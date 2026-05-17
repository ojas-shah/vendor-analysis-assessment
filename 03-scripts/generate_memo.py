"""Generate the executive memo from the reconciled data + top3 opportunities.

Writes:
  - 04-outputs/executive-memo.md (the source-of-truth memo content)

The /publish-to-drive slash command uploads this markdown as a Google Doc.
Drive auto-converts text/plain content into a Google Doc on upload.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
    OUTPUTS_DIR,
    VALIDATION_DIR,
    call_claude,
    read_jsonl,
    render_prompt,
)


def main() -> None:
    reconciled = read_jsonl(OUTPUTS_DIR / "reconciled.jsonl")
    top3 = json.loads((OUTPUTS_DIR / "top3.json").read_text(encoding="utf-8"))
    qc_report = (VALIDATION_DIR / "qc-report.md").read_text(encoding="utf-8")
    qc_summary = qc_report[:2000]

    total_spend = sum(v.get("spend", 0) for v in reconciled)
    today = datetime.now().strftime("%B %d, %Y")

    system = render_prompt("05-executive-memo-prompt.md", TODAY=today)
    user_payload = {
        "total_vendors": len(reconciled),
        "total_annual_spend": round(total_spend, 2),
        "top3": top3,
        "qc_summary_excerpt": qc_summary,
    }
    print("Calling Claude for executive memo draft...")
    memo_md = call_claude(
        system=system,
        user=json.dumps(user_payload, ensure_ascii=False),
        max_tokens=2000,
    ).strip()

    (OUTPUTS_DIR / "executive-memo.md").write_text(memo_md, encoding="utf-8")
    print("Wrote 04-outputs/executive-memo.md")
    print()
    print("Next step: run /publish-to-drive to upload as a Google Doc.")


if __name__ == "__main__":
    main()
