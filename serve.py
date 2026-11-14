#!/usr/bin/env python3
"""
FitFindr over HTTP. ← UNIT 9

    python serve.py                       run it on your machine
    gunicorn serve:app                    run it the way a host runs it

Everything else in this repo exits after one command. A host has nothing to
keep running, so a command line cannot be deployed. This file is the smallest
thing that can: it starts a web server, waits, and hands each request to the
same `run_agent()` your CLI calls. **No new agent logic lives here.** If your
loop works from `python app.py ask`, it works from here; if it doesn't, fix it
there, not in this file.

Two routes:

    POST /ask       {"query": "vintage graphic tee under $30",
                     "wardrobe": {...}}     ← wardrobe is optional
    GET  /health    is it awake?

`/ask` returns the session dict from `run_agent()` as JSON, unchanged — the
same keys you print from the command line, including `error`. Read
`session["error"]` first, exactly as you do everywhere else.

It runs **one request at a time**, and one route is deliberately slower than a
web server has to be. The reason is worth reading before you deploy: see the
note above `_one_at_a_time` below — it also decides which gunicorn worker you
can use.

Capstone (unit 9): every /ask request now appends one JSON record to
logs/requests.jsonl (timestamp, query, status, outcome, model calls, tokens,
duration). Bad input gets a 400 and a model outage gets a 503, both with a
sentence instead of a Python exception.
"""

import json
import os
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

# config first, and before anything that talks to the model: it loads your .env
# and fixes the Windows console encoding for every module that imports it.
import config  # noqa: F401

from flask import Flask, jsonify, request

from agent import run_agent
import generate
from generate import ModelUnavailable
from utils.data_loader import get_example_wardrobe

app = Flask(__name__)


# ── one request at a time ─────────────────────────────────────────────────────
# Here's why this exists.
#
# A web server will happily run two requests at once. Two things in this repo
# assume otherwise:
#
#   • If you moved a tool onto MCP in unit 4, `mcp_client.call_tool` starts
#     `mcp_server.py` as a separate process over stdio, one per call. Two
#     overlapping requests means two extra Python interpreters, and the free
#     tier you're deploying to has 512 MB for all of it. That is the reason
#     that would still be here even if everything else were perfect.
#   • `generate.py`'s pacing window and its call counter are plain module
#     globals — deliberately, because that file is teaching pacing and quota,
#     not locking. Two threads sharing them means the per-minute limiter is
#     counting something that isn't true.
#
# What the lock covers is exactly the agent run: the part that spawns
# processes and calls the model. Reading the request, rejecting a bad one, and
# turning the answer into JSON all happen outside it — so a request with a
# malformed body comes straight back with a 400 instead of queueing behind
# somebody else's agent.
#
# Serialising the runs costs you nothing here — this is one user asking one
# question — and it keeps the deployed behaviour identical to the CLI's. When
# that stops being an acceptable trade, the fix is a real queue, not a bigger
# lock.
#
# The same constraint decides your start command, and this is the part that
# bites in deployment rather than on your machine. `mcp_client.call_tool`
# wraps `asyncio.run()`, and `asyncio.run()` refuses to start when an event
# loop is already running. An async worker always has one running. So under
# `gunicorn -k gevent` (or `-k eventlet`, or `serve:app` wrapped for an ASGI
# server like uvicorn) EVERY MCP call fails with "asyncio.run() cannot be
# called from a running event loop" — not some of them under load, all of
# them, every time, in a place your laptop never showed you.
#
#     gunicorn serve:app              ← right: the DEFAULT sync worker
#     gunicorn -k gevent serve:app    ← breaks every MCP call you make

_one_at_a_time = threading.Lock()


# ── structured log (capstone) ─────────────────────────────────────────────────
# One JSON object per line, one line per /ask request — successes, 400s, 503s
# and 500s alike. A failure that only shows up as a missing line can't be found.

LOG_PATH = Path(os.getenv("FITFINDR_LOG", Path(__file__).parent / "logs" / "requests.jsonl"))


def _log(record: dict) -> None:
    """Append one record. Logging must never break the request it describes."""
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as exc:  # noqa: BLE001
        print(f"  [serve] couldn't write the log: {exc}", file=sys.stderr, flush=True)


def _short(value, limit=160):
    """Keep log lines readable: long text is cut, non-text is shown as its repr."""
    if value is None:
        return None
    text = value if isinstance(value, str) else repr(value)
    return text if len(text) <= limit else text[:limit] + "…"


# ── input validation (capstone) ───────────────────────────────────────────────

MAX_WARDROBE_ITEMS = 50   # the whole wardrobe goes into suggest_outfit's prompt


def _validate(payload):
    """
    Check a request body before anything runs.

    Returns (query, wardrobe, problem). `problem` is None when the request is
    fine, otherwise one sentence that names the field to fix.
    """
    example = '{"query": "vintage graphic tee under $30"}'
    if not isinstance(payload, dict):
        return None, None, f"The body must be a JSON object, e.g. {example}"

    query = payload.get("query")
    if query is None:
        return None, None, f"Missing 'query'. Send JSON like {example}"
    if not isinstance(query, str):
        return None, None, f"'query' must be text, not {type(query).__name__}."
    query = query.strip()
    if not query:
        return None, None, "'query' is empty. Say what you're looking for."

    wardrobe = payload.get("wardrobe")
    if wardrobe is None:
        return query, get_example_wardrobe(), None
    if not isinstance(wardrobe, dict) or not isinstance(wardrobe.get("items"), list):
        return None, None, "'wardrobe' must be an object with an 'items' list, e.g. {\"items\": []}"
    items = wardrobe["items"]
    if len(items) > MAX_WARDROBE_ITEMS:
        return None, None, (f"'wardrobe' has {len(items)} items; the limit is "
                            f"{MAX_WARDROBE_ITEMS}.")
    if not all(isinstance(i, dict) for i in items):
        return None, None, "Every item in 'wardrobe.items' must be an object with a 'name'."
    return query, wardrobe, None


@app.get("/health")
def health():
    """Is the server awake? A host pings something like this to find out."""
    return jsonify({"status": "ok"})


@app.post("/ask")
def ask():
    """
    Run the agent on one query.

    In:   {"query": "...", "wardrobe": {...}}   wardrobe optional — leave it
                                                out and you get the same
                                                example wardrobe the CLI uses.
    Out:  the session dict from run_agent(), as JSON.
    """
    started = time.perf_counter()
    payload = request.get_json(silent=True)
    record = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "request_id": uuid.uuid4().hex[:8],
        "query": _short(payload.get("query") if isinstance(payload, dict) else payload),
        "wardrobe_items": None,
        "status": None,
        "outcome": None,
        "selected_item": None,
        "price": None,
        "fit_card": None,
        "error": None,
        "detail": None,
        "model_calls": 0,
        "prompt_tokens": 0,
        "output_tokens": 0,
        "duration_ms": None,
    }

    def finish(body, status, outcome):
        record["status"] = status
        record["outcome"] = outcome
        record["duration_ms"] = round((time.perf_counter() - started) * 1000)
        _log(record)
        return jsonify(body), status

    # Capstone: every bad input is caught here, before the agent (and the
    # model) runs, and comes back as a 400 that names the field to fix.
    query, wardrobe, problem = _validate(payload)
    if problem:
        record["error"] = problem
        return finish({"error": problem}, 400, "bad_request")
    record["wardrobe_items"] = len(wardrobe.get("items") or [])

    # A queued request should look like a queued request. Without this the
    # second caller just sits there, and "slow" and "waiting its turn" are
    # indistinguishable from the outside — which is how people conclude the
    # deployment is broken when it is behaving exactly as designed.
    if _one_at_a_time.locked():
        print(
            "  [serve] another request is still running. This one is waiting "
            "its turn — serve.py handles one at a time, on purpose.",
            file=sys.stderr,
            flush=True,
        )

    # Capstone: sort failures by who can fix them. A model outage or a rate
    # limit is temporary (503, "try again"); anything else is our bug (500).
    # Either way the caller gets a sentence, never a Python exception name —
    # the exception itself goes in the log's "detail" field instead.
    failure = None
    status = 200
    session = None
    with _one_at_a_time:
        calls_before = generate.call_count()
        tokens_before = generate.token_counts()
        try:
            session = run_agent(query, wardrobe)
        except ModelUnavailable as exc:
            status, failure = 503, f"The styling model is unavailable right now: {exc}"
            record["detail"] = _short(f"{type(exc).__name__}: {exc}")
        except RuntimeError as exc:
            record["detail"] = _short(f"{type(exc).__name__}: {exc}")
            if "rate limited" in str(exc).lower():
                status, failure = 503, ("The styling model is busy (rate limited). "
                                        "Wait a minute and try again.")
            else:
                status, failure = 500, "Something went wrong on our side. Try again."
        except Exception as exc:  # noqa: BLE001 — a 500 with a sentence beats a hang
            status, failure = 500, "Something went wrong on our side. Try again."
            record["detail"] = _short(f"{type(exc).__name__}: {exc}")
        tokens_after = generate.token_counts()
        record["model_calls"] = generate.call_count() - calls_before
        record["prompt_tokens"] = tokens_after["prompt"] - tokens_before["prompt"]
        record["output_tokens"] = tokens_after["output"] - tokens_before["output"]

    # Outside the lock: building a response is not work the next caller should
    # be waiting on.
    if failure is not None:
        record["error"] = failure
        outcome = "model_unavailable" if status == 503 else "server_error"
        return finish({"error": failure}, status, outcome)

    item = session.get("selected_item") or {}
    record["selected_item"] = item.get("title")
    record["price"] = item.get("price")
    record["fit_card"] = _short(session.get("fit_card"))
    record["error"] = session.get("error")
    return finish(session, 200, "no_match" if session.get("error") else "ok")


if __name__ == "__main__":
    # PORT and 0.0.0.0 are not decoration. A host tells you which port to
    # listen on through PORT, and it reaches your process from outside the
    # container — bind 127.0.0.1 and nothing but the container itself can
    # connect, which looks exactly like a broken app from the browser.
    port = int(os.getenv("PORT", "5000"))

    # Never on by default. Flask's debugger executes code typed into a browser,
    # and a deployed app with it on is a stranger's shell. Set AI201_DEBUG=1 in
    # your own terminal when you want the reloader.
    debug = os.getenv("AI201_DEBUG", "0") == "1"

    print(f"\nFitFindr is listening on http://localhost:{port}")
    print("It runs one request at a time — a second one waits for the first.")
    print("Ask it something (single quotes, as always):\n")
    print(
        f"  curl -X POST http://localhost:{port}/ask \\\n"
        f"    -H 'Content-Type: application/json' \\\n"
        f"    -d '{{\"query\": \"vintage graphic tee under $30\"}}'\n"
    )
    print("Ctrl-C to stop.\n")

    app.run(host="0.0.0.0", port=port, debug=debug)
