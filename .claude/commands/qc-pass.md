---
description: Run the independent QC second pass and reconcile against the first pass
---

Run the QC validation pipeline.

1. Confirm `04-outputs/pass1.jsonl` exists. If not, tell me to run `/analyze-batch` first.
2. Run: `python 03-scripts/qc_validate.py` — this is the independent second pass.
3. When that finishes, run: `python 03-scripts/reconcile.py` — this compares pass 1 and pass 2 and tiebreaks disagreements.
4. Read `05-validation/qc-report.md` and summarize: how many vendors agreed, how many needed a tiebreaker, which high-spend vendors had disagreements (sort by spend, top 5).
5. Recommend whether to spot-check anything manually before moving on to `/top3`.
