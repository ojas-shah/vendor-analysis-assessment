"""Reconcile pass1 and pass2.

For each vendor:
- If pass1 and pass2 agree on department + recommendation → take pass1 (with
  averaged confidence) and mark agree=True.
- If they disagree → call the tiebreaker prompt with both passes' reasoning,
  let it pick or propose a new answer, log to qc-report.md.

Reads:  04-outputs/pass1.jsonl, 04-outputs/pass2.jsonl
Writes: 04-outputs/reconciled.jsonl, 05-validation/qc-report.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
    OUTPUTS_DIR,
    VALIDATION_DIR,
    call_claude,
    parse_json_response,
    read_jsonl,
    render_prompt,
    write_jsonl,
)


def tiebreaker(vendor: dict, p1: dict, p2: dict, disagree_fields: list[str]) -> dict:
    system = render_prompt("03-reconciliation-prompt.md")
    user_payload = {
        "vendor": {"name": vendor["name"], "spend": vendor.get("spend", 0)},
        "pass1": {k: p1.get(k) for k in ["department", "description", "recommendation", "reasoning", "confidence"]},
        "pass2": {k: p2.get(k) for k in ["department", "description", "recommendation", "reasoning", "confidence"]},
        "disagreement_fields": disagree_fields,
    }
    response = call_claude(system=system, user=json.dumps(user_payload, ensure_ascii=False))
    return parse_json_response(response)


def main() -> None:
    pass1 = {row["name"]: row for row in read_jsonl(OUTPUTS_DIR / "pass1.jsonl")}
    pass2 = {row["name"]: row for row in read_jsonl(OUTPUTS_DIR / "pass2.jsonl")}

    all_names = sorted(set(pass1.keys()) | set(pass2.keys()), key=lambda n: -(pass1.get(n, {}).get("spend") or pass2.get(n, {}).get("spend") or 0))

    print(f"Reconciling {len(all_names)} vendors...")

    reconciled: list[dict] = []
    audit_lines: list[str] = []
    audit_lines.append("# QC Reconciliation Report\n")
    audit_lines.append(
        "Every vendor where the first-pass and QC-pass analyses disagreed is listed here, "
        "along with the tiebreaker's resolution and reasoning. Sorted by spend (highest first) "
        "because higher-spend disagreements matter more.\n"
    )

    agree_count = 0
    disagree_count = 0
    disagree_log: list[dict] = []

    for name in all_names:
        p1 = pass1.get(name)
        p2 = pass2.get(name)
        if not p1 or not p2:
            chosen = p1 or p2
            chosen["_origin"] = "single_pass_only"
            reconciled.append(chosen)
            continue

        disagree_fields = []
        if p1.get("department") != p2.get("department"):
            disagree_fields.append("department")
        if p1.get("recommendation") != p2.get("recommendation"):
            disagree_fields.append("recommendation")

        if not disagree_fields:
            merged = dict(p1)
            merged["confidence"] = round(
                (p1.get("confidence", 0.5) + p2.get("confidence", 0.5)) / 2, 2
            )
            merged["_origin"] = "agreed"
            reconciled.append(merged)
            agree_count += 1
        else:
            print(f"  Tiebreak: {name} (disagree on {disagree_fields})")
            result = tiebreaker(p1, p1, p2, disagree_fields)
            result["spend"] = p1.get("spend", 0)
            result["_origin"] = "tiebroken"
            reconciled.append(result)
            disagree_count += 1
            disagree_log.append({"name": name, "p1": p1, "p2": p2, "result": result})

    disagree_log.sort(key=lambda d: -(d["p1"].get("spend") or 0))
    for d in disagree_log:
        name = d["name"]
        spend = d["p1"].get("spend", 0)
        audit_lines.append(f"\n## {name} — ${spend:,.2f}\n")
        audit_lines.append(f"- **Pass 1:** dept=`{d['p1'].get('department')}` rec=`{d['p1'].get('recommendation')}` conf=`{d['p1'].get('confidence')}`")
        audit_lines.append(f"  > {d['p1'].get('reasoning', '')}\n")
        audit_lines.append(f"- **Pass 2:** dept=`{d['p2'].get('department')}` rec=`{d['p2'].get('recommendation')}` conf=`{d['p2'].get('confidence')}`")
        audit_lines.append(f"  > {d['p2'].get('reasoning', '')}\n")
        audit_lines.append(f"- **Tiebreaker chose:** `{d['result'].get('chose')}` → dept=`{d['result'].get('department')}` rec=`{d['result'].get('recommendation')}`")
        audit_lines.append(f"  > {d['result'].get('tiebreaker_reasoning', '')}\n")

    write_jsonl(OUTPUTS_DIR / "reconciled.jsonl", reconciled)
    (VALIDATION_DIR / "qc-report.md").write_text("\n".join(audit_lines), encoding="utf-8")

    print(f"\nAgree: {agree_count} | Disagree (tiebroken): {disagree_count}")
    print(f"Wrote 04-outputs/reconciled.jsonl")
    print(f"Wrote 05-validation/qc-report.md")


if __name__ == "__main__":
    main()
