#!/usr/bin/env python3
"""
Measure what one FitFindr run costs. ← CAPSTONE, MILESTONE 3

    python serve.py                      (terminal 1, with AI201_CACHE=0)
    python measure_cost.py               (terminal 2)

Sends ten matching queries to the running server, one after another, then
reads the records those requests wrote to logs/requests.jsonl and averages
model calls, tokens and duration. The numbers come from the service's own
token counts (generate.token_counts), not from a pricing page.

Start the server with the cache OFF, or repeated prompts cost nothing and the
average is wrong:

    PowerShell:  $env:AI201_CACHE='0'; python serve.py
    bash:        AI201_CACHE=0 python serve.py
"""

import argparse
import json
import statistics
import urllib.request
from pathlib import Path

QUERIES = [
    "vintage graphic tee under $30",
    "denim jacket under $50",
    "silk slip dress",
    "suede chelsea boots",
    "corduroy wide-leg pants",
    "platform sneakers size 8",
    "90s track jacket in size M",
    "cargo pants under $40",
    "crossbody bag",
    "oversized crewneck sweatshirt",
]

LOG = Path(__file__).parent / "logs" / "requests.jsonl"


def post(url: str, body: dict) -> int:
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:5000/ask")
    args = parser.parse_args()

    before = LOG.read_text(encoding="utf-8").splitlines() if LOG.exists() else []
    for q in QUERIES:
        print(f"{post(args.url, {'query': q})}  {q}")
    after = LOG.read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in after[len(before):]]
    ok = [r for r in records if r["outcome"] == "ok"]

    if not ok:
        print("No successful runs to average.")
        return
    calls = [r["model_calls"] for r in ok]
    p_tok = [r["prompt_tokens"] for r in ok]
    o_tok = [r["output_tokens"] for r in ok]
    secs = [r["duration_ms"] / 1000 for r in ok]
    print(f"\n{len(ok)} of {len(records)} runs ended 'ok' (averages are over those)")
    print(f"model calls per run:   {statistics.mean(calls):.1f}")
    print(f"prompt tokens per run: {statistics.mean(p_tok):.0f}  (min {min(p_tok)}, max {max(p_tok)})")
    print(f"output tokens per run: {statistics.mean(o_tok):.0f}  (min {min(o_tok)}, max {max(o_tok)})")
    print(f"total tokens per run:  {statistics.mean(p + o for p, o in zip(p_tok, o_tok)):.0f}")
    print(f"seconds per run:       {statistics.mean(secs):.2f}  (min {min(secs):.2f}, max {max(secs):.2f})")


if __name__ == "__main__":
    main()
