---
description: Spawn the qc-reviewer subagent to scrutinize the top 20 highest-spend vendors
---

Run a focused review of the highest-spend vendors.

1. Read `04-outputs/reconciled.jsonl` and identify the top 20 vendors by spend.
2. Spawn the `qc-reviewer` subagent and ask it to independently re-classify those 20 vendors and flag any disagreements with the reconciled output.
3. Compile its findings into a short report. Pay special attention to:
   - Any vendor where the reviewer disagrees on `recommendation`
   - Any vendor with confidence < 0.7 in reconciled.jsonl
   - Any Consolidate call whose named peers aren't in the portfolio
4. Recommend changes I should make manually before regenerating the deliverable.
