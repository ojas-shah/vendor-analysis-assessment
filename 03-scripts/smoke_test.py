"""Smoke test — verify auth, model availability, and prompt formatting BEFORE
running the full 5-minute pipeline.

Costs about $0.005 to run. Always run this once before /analyze-batch.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
    MODEL,
    call_claude,
    load_source_vendors,
    parse_json_response,
    render_prompt,
)


def main() -> None:
    print(f"Model: {MODEL}")
    print("Loading source vendors...")
    vendors = load_source_vendors()
    sample = vendors[:3]
    print(f"  Sample (first 3): {[v['name'] for v in sample]}")

    print("Rendering first-pass prompt...")
    system = render_prompt("01-first-pass-prompt.md")

    print(f"Calling Claude ({MODEL}) with 3-vendor sample...")
    import json
    user_msg = json.dumps([
        {
            "name": v["name"],
            "spend": round(v["spend"], 2),
            "peer_vendors": [w["name"] for w in sample if w["name"] != v["name"]],
        }
        for v in sample
    ])
    response = call_claude(system=system, user=user_msg)
    parsed = parse_json_response(response)

    print()
    print("=== Result ===")
    for row in parsed:
        print(f"  {row['name']}")
        print(f"    dept={row['department']!r}  rec={row['recommendation']!r}  conf={row['confidence']}")
        print(f"    desc: {row['description']}")
        print(f"    why: {row['reasoning'][:120]}")
        print()

    print("OK. Auth works, model responds, JSON parses. Safe to run /analyze-batch.")


if __name__ == "__main__":
    main()
