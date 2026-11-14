#!/usr/bin/env python3
"""
The capstone test. ← CAPSTONE, MILESTONE 5

    python capstone_eval.py --label before --trial 1

One trial = every request the five criteria in criteria.md (C1–C5) need:

    1. starts serve.py on port 5055 with the real key and the cache off
    2. C1: sends the six malformed requests
    3. C4/C5: sends 'vintage graphic tee under $30' five times
    4. stops it, starts serve.py again with an INVALID key (cache off)
    5. C2: sends five different matching queries
    6. C3: reads the log lines those 16 requests wrote

Both servers append to the same logs/requests.jsonl, which is what C3 checks.
Scoring follows the wording of each criterion; nothing is judged by eye.
Writes results/capstone_<label>_trial<N>.md with the raw responses and log lines.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
LOG = ROOT / "logs" / "requests.jsonl"
PORT = 5055
BASE = f"http://localhost:{PORT}"

BAD_REQUESTS = [  # C1: (label, raw body bytes, word the error must contain)
    ("body is not JSON", b"hello", "JSON"),
    ("no query", b"{}", "query"),
    ("whitespace query", json.dumps({"query": "   "}).encode(), "query"),
    ("query is a number", json.dumps({"query": 123}).encode(), "query"),
    ("wardrobe items not a list",
     json.dumps({"query": "tee", "wardrobe": {"items": "abc"}}).encode(), "wardrobe"),
    ("wardrobe over 50 items",
     json.dumps({"query": "tee", "wardrobe": {"items": [{"name": f"shirt {i}"} for i in range(51)]}}).encode(),
     "wardrobe"),
]
HAPPY_QUERY = "vintage graphic tee under $30"            # C4 / C5
OUTAGE_QUERIES = [                                       # C2
    "vintage graphic tee under $30",
    "denim jacket under $50",
    "silk slip dress",
    "suede chelsea boots",
    "corduroy wide-leg pants",
]
LEAKS = re.compile(r"Error:|Exception|Traceback|ModelUnavailable|\.env|GEMINI_API_KEY")


def post(body: bytes):
    req = urllib.request.Request(f"{BASE}/ask", data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            status, text = resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        status, text = exc.code, exc.read().decode("utf-8")
    seconds = time.perf_counter() - started
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = {"_raw": text}
    return status, data, seconds


def start_server(env_overrides: dict, out_path: Path):
    env = {**os.environ, "PORT": str(PORT), "AI201_CACHE": "0", **env_overrides}
    out = out_path.open("a", encoding="utf-8")
    proc = subprocess.Popen([sys.executable, "serve.py"], cwd=ROOT, env=env,
                            stdout=out, stderr=subprocess.STDOUT)
    for _ in range(60):
        try:
            urllib.request.urlopen(f"{BASE}/health", timeout=2)
            return proc, out
        except Exception:  # noqa: BLE001
            time.sleep(0.5)
    proc.kill()
    raise SystemExit("serve.py never answered /health")


def stop_server(proc, out):
    proc.terminate()
    proc.wait(timeout=10)
    out.close()


def log_lines() -> list[str]:
    return LOG.read_text(encoding="utf-8").splitlines() if LOG.exists() else []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--trial", type=int, required=True)
    args = parser.parse_args()

    results_dir = ROOT / "results"
    results_dir.mkdir(exist_ok=True)
    server_out = results_dir / f"capstone_{args.label}_trial{args.trial}_server.txt"
    server_out.write_text("", encoding="utf-8")
    log_before = len(log_lines())
    sent = []  # (criterion, label, status, data, seconds)

    # ── working server: C1, then C4/C5 ───────────────────────────────────────
    proc, out = start_server({}, server_out)
    try:
        for label, body, _ in BAD_REQUESTS:
            sent.append(("C1", label, *post(body)))
        for i in range(5):
            sent.append(("C4/C5", f"happy {i + 1}", *post(json.dumps({"query": HAPPY_QUERY}).encode())))
    finally:
        stop_server(proc, out)

    # ── invalid key: C2 ──────────────────────────────────────────────────────
    proc, out = start_server({"GEMINI_API_KEY": "AIzaInvalidKeyForCapstoneTest000000000"}, server_out)
    try:
        for q in OUTAGE_QUERIES:
            sent.append(("C2", q, *post(json.dumps({"query": q}).encode())))
    finally:
        stop_server(proc, out)

    new_lines = log_lines()[log_before:]
    records = []
    for line in new_lines:
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            records.append(None)

    # ── scoring ──────────────────────────────────────────────────────────────
    rows = {}

    c1 = []
    for idx, (label, _, word) in enumerate(BAD_REQUESTS):
        _, _, status, data, _ = sent[idx]
        rec = records[idx] if idx < len(records) else None
        ok = (status == 400 and word in str(data.get("error", ""))
              and rec is not None and rec.get("model_calls") == 0)
        c1.append(ok)
    rows["C1"] = (sum(c1), 6)

    happy = [s for s in sent if s[0] == "C4/C5"]
    happy_recs = records[6:11]
    c4 = [s[2] == 200 and s[3].get("error") is None and bool(s[3].get("fit_card"))
          and f"${(s[3].get('selected_item') or {}).get('price', 0):.0f}" in s[3]["fit_card"]
          for s in happy]
    rows["C4"] = (sum(c4), 5)
    c5 = [r is not None and r.get("duration_ms") is not None and r["duration_ms"] < 10_000
          for r in happy_recs]
    rows["C5"] = (sum(c5), 5)

    outage = [s for s in sent if s[0] == "C2"]
    c2 = [s[2] == 503 and s[4] < 10 and not LEAKS.search(json.dumps(s[3])) for s in outage]
    rows["C2"] = (sum(c2), 5)

    c3_ok = 0
    for idx, s in enumerate(sent):
        rec = records[idx] if idx < len(records) else None
        if (rec is not None and all(rec.get(k) is not None for k in ("ts", "status", "outcome", "duration_ms"))
                and rec["status"] == s[2]):
            c3_ok += 1
    if len(records) != len(sent):   # a missing or extra line fails the whole trial's count
        c3_ok = min(c3_ok, len(records)) if len(records) < len(sent) else 0
    rows["C3"] = (c3_ok, len(sent))

    # ── write it up ──────────────────────────────────────────────────────────
    report = results_dir / f"capstone_{args.label}_trial{args.trial}.md"
    with report.open("w", encoding="utf-8") as f:
        f.write(f"# Capstone {args.label}, trial {args.trial}\n\n")
        f.write(f"Run {datetime.now().isoformat(timespec='seconds')} by `capstone_eval.py`. "
                f"{len(sent)} requests sent, {len(new_lines)} new log lines.\n\n")
        f.write("| Criterion | Passed |\n|---|---|\n")
        for k in ("C1", "C2", "C3", "C4", "C5"):
            f.write(f"| {k} | {rows[k][0]}/{rows[k][1]} |\n")
        f.write("\n## Every request\n\n| # | For | Request | HTTP | Client s | Pass | Body (first 220 chars) |\n|---|---|---|---|---|---|---|\n")
        passes = {"C1": iter(c1), "C2": iter(c2), "C4/C5": iter(zip(c4, c5))}
        for n, (crit, label, status, data, secs) in enumerate(sent, 1):
            p = next(passes[crit])
            p = f"C4 {'PASS' if p[0] else 'FAIL'}, C5 {'PASS' if p[1] else 'FAIL'}" if isinstance(p, tuple) else ("PASS" if p else "FAIL")
            body = json.dumps(data.get("error") if data.get("error") else {"fit_card": data.get("fit_card")}, ensure_ascii=False)
            body = body[:220].replace("|", "\\|")
            f.write(f"| {n} | {crit} | {label} | {status} | {secs:.2f} | {p} | {body} |\n")
        f.write("\n## New log lines (logs/requests.jsonl)\n\n```\n")
        f.write("\n".join(new_lines))
        f.write("\n```\n")
    print(f"Wrote {report.relative_to(ROOT)}")
    for k in ("C1", "C2", "C3", "C4", "C5"):
        print(f"  {k}: {rows[k][0]}/{rows[k][1]}")


if __name__ == "__main__":
    main()
