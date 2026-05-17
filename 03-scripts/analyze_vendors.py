"""First-pass enrichment: department, description, recommendation, confidence.

Reads:  01-inputs/vendors-raw.xlsx
Writes: 04-outputs/pass1.jsonl  (one JSON line per vendor, appended per batch)

RESUMABLE: if pass1.jsonl already has some vendors, those are skipped on
re-run. Each batch is appended immediately, so a timeout never loses more
than one in-flight batch of work.

Knobs (via env vars):
  VENDOR_BATCH_SIZE      vendors per API call (default 25, safe 10-40)
  VENDOR_ANALYSIS_MODEL  Anthropic model name (default claude-sonnet-4-5)
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
    OUTPUTS_DIR,
    batched,
    call_claude,
    load_source_vendors,
    parse_json_response,
    read_jsonl,
    render_prompt,
)

BATCH_SIZE = int(os.getenv("VENDOR_BATCH_SIZE", "25"))
OUTPUT_FILE = OUTPUTS_DIR / "pass1.jsonl"


def _print_summary() -> None:
    rows = read_jsonl(OUTPUT_FILE)
    low_conf = sum(1 for r in rows if r.get("confidence", 1) < 0.6)
    counts: dict[str, int] = {}
    for r in rows:
        rec = r.get("recommendation", "?")
        counts[rec] = counts.get(rec, 0) + 1
    summary = " | ".join(f"{k}: {v}" for k, v in sorted(counts.items()))
    print(f"  {summary} | Low confidence (<0.6): {low_conf}")


def main() -> None:
    vendors = load_source_vendors()

    already_done: set[str] = set()
    if OUTPUT_FILE.exists():
        existing = read_jsonl(OUTPUT_FILE)
        already_done = {r["name"] for r in existing if r.get("name")}
        if already_done:
            print(f"Found {len(already_done)} vendors already classified - resuming.")

    todo = [v for v in vendors if v["name"] not in already_done]
    if not todo:
        print(f"All {len(vendors)} vendors already classified. Nothing to do.")
        _print_summary()
        return

    total_batches = (len(todo) + BATCH_SIZE - 1) // BATCH_SIZE
    print(
        f"Loaded {len(vendors)} vendors total. "
        f"Processing {len(todo)} remaining in {total_batches} batch(es) of {BATCH_SIZE}."
    )

    system = render_prompt("01-first-pass-prompt.md")

    for i, batch in enumerate(batched(todo, BATCH_SIZE), start=1):
        peer_names = [v["name"] for v in batch]
        user_payload = [
            {
                "name": v["name"],
                "spend": round(v["spend"], 2),
                "peer_vendors": [n for n in peer_names if n != v["name"]],
            }
            for v in batch
        ]
        user_msg = json.dumps(user_payload, ensure_ascii=False)

        print(f"  Batch {i}/{total_batches}: {len(batch)} vendors... ", end="", flush=True)
        response_text = call_claude(system=system, user=user_msg)
        try:
            parsed = parse_json_response(response_text)
        except Exception as exc:
            print(f"PARSE ERROR - {exc}")
            print(f"    Raw response head: {response_text[:200]!r}")
            print(f"    Progress saved. Re-run the script to resume from here.")
            raise

        # Re-attach authoritative spend from source
        spend_by_name = {v["name"]: v["spend"] for v in batch}
        for row in parsed:
            row["spend"] = spend_by_name.get(row["name"], 0.0)

        # Append immediately so a timeout doesn't lose this batch
        with OUTPUT_FILE.open("a", encoding="utf-8") as f:
            for row in parsed:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

        print(f"done ({len(parsed)} saved)")

    print(f"\nAll batches complete. Output at {OUTPUT_FILE}.")
    _print_summary()


if __name__ == "__main__":
    main()
