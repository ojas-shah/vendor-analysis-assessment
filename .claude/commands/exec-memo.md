---
description: Draft the 1-page CEO/CFO executive memo and produce the final deliverable xlsx
---

Generate the executive memo and assemble the final deliverable.

1. Confirm `04-outputs/top3.json` exists. If not, run `/top3` first.
2. Run: `python 03-scripts/generate_memo.py` — produces `04-outputs/executive-memo.md`.
3. Show me the memo (read `04-outputs/executive-memo.md`) and ask if I want any edits before assembly.
4. After I approve, run: `python 03-scripts/build_deliverable.py` — builds `04-outputs/Vendor Analysis Assessment - Ojas Shah.xlsx` with all four tabs populated.
5. List the deliverable files in `04-outputs/` and remind me the next step is `/publish-to-drive` to upload to Google Drive as a Sheet + Doc.
