---
description: Run the first-pass vendor enrichment over all vendors in 01-inputs/vendors-raw.xlsx
---

Run the first-pass vendor classification.

1. Confirm `01-inputs/vendors-raw.xlsx` exists. If not, tell me and stop.
2. Confirm `ANTHROPIC_API_KEY` is set in the environment. If not, tell me how to set it and stop.
3. Run: `python 03-scripts/analyze_vendors.py`
4. Report the summary line (Terminate/Consolidate/Optimize counts + low-confidence count).
5. If more than 10% of vendors came back with confidence < 0.6, surface that as a concern — those rows need closer review.
