"""Independent QC second pass.

Reads:  01-inputs/vendors-raw.xlsx
Writes: 04-outputs/pass2.jsonl

Does NOT see pass1.jsonl. Independence is the whole point.

RESUMABLE - same as analyze_vendors.py. Appends per batch, skips already-done.

Knobs:
  VENDOR_BATCH_SIZE  vendors per API call (default 25)
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
OUTPUT_FILE = OUTPUTS_DIR / "pass2.jsonl"


def main() -> None:
    vendors = load_source_vendors()

    already_done: set = set()
    if OUTPUT_FILE.exists():
        existing = read_jsonl(OUTPUT_FILE)
        already_done = {r["name"] for r in existing if r.get("name")}
        if already_done:
            print(f"Found {len(already_done)} vendors already QC'd - resuming.")

    todo = [v for v in vendors if v["name"] not in already_done]
    if not todo:
        print(f"All {len(vendors)} vendors already QC'd. Nothing to do.")
        return

    total_batches = (len(todo) + BATCH_SIZE - 1) // BATCH_SIZE
    print(
        f"Loaded {len(vendors)} vendors total. "
        f"Processing {len(todo)} remaining in {total_batches} batch(es) of {BATCH_SIZE}."
    )

    system = render_prompt("02-qc-pass-prompt.md")

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
        print(f"  Batch {i}/{total_batches}: {len(batch)} vendors... ", end="", flush=True)
        response_text = call_claude(
            system=system, user=json.dumps(user_payload, ensure_ascii=False)
        )
        parsed = parse_json_response(response_text)

        spend_by_name = {v["name"]: v["spend"] for v in batch}
        for row in parsed:
            row["spend"] = spend_by_name.get(row["name"], 0.0)

        with OUTPUT_FILE.open("a", encoding="utf-8") as f:
            for row in parsed:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

        print("done")

    print(f"\nAll batches complete. Output at {OUTPUT_FILE}.")


if __name__ == "__main__":
    main()
