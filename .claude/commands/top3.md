---
description: Generate the Top 3 strategic savings opportunities from the reconciled data
---

Generate the Top 3 opportunities.

1. Confirm `04-outputs/reconciled.jsonl` exists. If not, run `/qc-pass` first.
2. Run: `python 03-scripts/top_opportunities.py`
3. Read `04-outputs/top3.json` and present each opportunity in a short paragraph for me to review.
4. For each opportunity, sanity-check the math: does `current_annual_spend * projected_savings_pct` equal `projected_annual_savings`? Call out any discrepancies.
5. Verify each opportunity names specific vendors and that those vendor names appear in `04-outputs/reconciled.jsonl`.
6. Ask me if I want any adjustments before generating the executive memo.
