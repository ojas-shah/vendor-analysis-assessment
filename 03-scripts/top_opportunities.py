"""Roll up reconciled vendors and identify the Top 3 savings opportunities.

Reads:  04-outputs/reconciled.jsonl
Writes: 04-outputs/top3.json

Sends a CURATED summary to Claude, not the full 386-row firehose, to stay
under low-tier 30K-input-tokens/minute rate limits even when reconcile.py
just finished a burst of tiebreaker calls.

Payload (~3K tokens total):
  - Top 40 vendors by spend (covers ~95% of total spend)
  - Department-level rollups
  - Consolidation candidates: top 5 vendors per dept group
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
    OUTPUTS_DIR,
    call_claude,
    parse_json_response,
    read_jsonl,
    render_prompt,
)

TOP_N_BY_SPEND = 40
MAX_VENDORS_PER_CONSOLIDATE_GROUP = 5


def slim(row):
    return {
        "name": row.get("name"),
        "spend": round(row.get("spend", 0), 2),
        "department": row.get("department"),
        "recommendation": row.get("recommendation"),
        "description": (row.get("description") or "")[:80],
    }


def main():
    reconciled = read_jsonl(OUTPUTS_DIR / "reconciled.jsonl")
    total_spend = sum(v.get("spend", 0) for v in reconciled)

    top_by_spend = sorted(reconciled, key=lambda x: -x.get("spend", 0))[:TOP_N_BY_SPEND]
    top_slim = [slim(v) for v in top_by_spend]

    dept_rollup = defaultdict(lambda: {"count": 0, "total_spend": 0.0})
    for v in reconciled:
        key = (v.get("department", "Unclassified"), v.get("recommendation", "Unknown"))
        dept_rollup[key]["count"] += 1
        dept_rollup[key]["total_spend"] += v.get("spend", 0)

    dept_summary = []
    for (dept, rec), stats in sorted(dept_rollup.items(), key=lambda x: -x[1]["total_spend"]):
        dept_summary.append({
            "department": dept,
            "recommendation": rec,
            "vendor_count": stats["count"],
            "total_spend": round(stats["total_spend"], 2),
        })

    consolidate_groups = defaultdict(list)
    for v in reconciled:
        if v.get("recommendation") == "Consolidate":
            consolidate_groups[v.get("department", "Unclassified")].append(slim(v))

    consolidate_summary = []
    for dept, vendors in sorted(consolidate_groups.items(), key=lambda x: -sum(v["spend"] for v in x[1])):
        sorted_vendors = sorted(vendors, key=lambda x: -x["spend"])
        consolidate_summary.append({
            "department": dept,
            "total_vendor_count": len(sorted_vendors),
            "total_spend": round(sum(x["spend"] for x in sorted_vendors), 2),
            "top_vendors": sorted_vendors[:MAX_VENDORS_PER_CONSOLIDATE_GROUP],
        })

    long_tail_threshold = top_by_spend[-1]["spend"] if top_by_spend else 0

    payload = {
        "total_vendors": len(reconciled),
        "total_annual_spend": round(total_spend, 2),
        "departments_by_spend": dept_summary,
        "top_vendors_by_spend": top_slim,
        "consolidation_candidates_by_department": consolidate_summary,
        "_note_to_model": (
            "Long tail of " + str(len(reconciled) - len(top_by_spend)) +
            " smaller vendors (each under $" + format(long_tail_threshold, ',.0f') +
            ") is omitted - represents <5% of spend, doesn't move Top 3. " +
            "Within each consolidation group, only top " +
            str(MAX_VENDORS_PER_CONSOLIDATE_GROUP) + " by spend shown."
        ),
    }

    user_msg = json.dumps(payload, ensure_ascii=False)
    print("Payload size: ~" + format(len(user_msg), ',') + " chars (~" + format(len(user_msg) // 4, ',') + " tokens)")

    system = render_prompt("04-top3-prompt.md")
    print("Calling Claude for Top 3 opportunity synthesis...")
    response = call_claude(system=system, user=user_msg, max_tokens=3000)
    result = parse_json_response(response)

    (OUTPUTS_DIR / "top3.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("Wrote 04-outputs/top3.json")
    print()
    for opp in result.get("opportunities", []):
        savings = opp.get("projected_annual_savings", 0)
        pct = opp.get("projected_savings_pct", 0) * 100
        cur = opp.get("current_annual_spend", 0)
        print(
            "  #" + str(opp.get("rank", "?")) + " " + opp.get("title", "") + ": " +
            "$" + format(savings, ',.0f') + " (" + format(pct, '.0f') + "% of $" + format(cur, ',.0f') + ")"
        )
    print("\nTotal projected savings: $" + format(result.get('total_projected_savings', 0), ',.0f'))


if __name__ == "__main__":
    main()
