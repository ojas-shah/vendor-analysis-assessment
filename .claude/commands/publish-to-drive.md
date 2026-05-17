---
description: Upload the executive memo as a Google Doc via Drive MCP. Tells user to manually drag-and-drop the xlsx (MCP binary uploads are broken).
---

Publish the executive memo to Google Drive as a native Google Doc.

**Prereq:** the Google Drive MCP must be connected and authenticated.

**Known issue:** the Drive MCP corrupts xlsx files when uploaded via `base64Content` — adds 9 bytes and mangles the ZIP central directory regardless of `contentMimeType` or `disableConversionToGoogleType`. The memo (text/plain) upload works fine. So this command handles the memo only; the user uploads the xlsx manually through Drive's web UI, which uses a different (working) conversion path.

**Step 1 — Upload the executive memo as a Google Doc**

1. Read `04-outputs/executive-memo.md`.
2. Call the Drive MCP `create_file` tool with:
   - `title`: "Vendor Analysis Memo - Ojas Shah"
   - `textContent`: the full markdown content of the memo
   - `contentMimeType`: `text/plain`
3. The response will have `mimeType: application/vnd.google-apps.document`. Capture the file `id` and construct the URL: `https://docs.google.com/document/d/<id>/edit`.

**Step 2 — Re-build the xlsx with the Google Doc URL embedded**

```bash
python 03-scripts/build_deliverable.py --memo-url "<the Google Doc URL>"
```

The Recommendations tab now points at the Doc.

**Step 3 — Tell the user how to upload the xlsx manually**

Don't try to upload via the MCP. Tell the user:

> The xlsx upload via MCP is broken — verified through three test variants (all corrupt the zip by 9 bytes). The reliable path is Drive's own web upload, which converts xlsx → Google Sheet during upload.
>
> 1. Open https://drive.google.com.
> 2. Drag `04-outputs/Vendor Analysis Assessment - Ojas Shah.xlsx` into the browser window.
> 3. Once it appears in Drive, right-click it → **Open with → Google Sheets**. A Google Sheets version is created in the same folder, preserving all four tabs.
> 4. Right-click both files (the Doc and the new Sheet) → Share → "Anyone with the link" → Viewer.
>
> Use the **Google Sheet URL** for submission, plus the Google Doc URL for the memo link.

**Step 4 — Report**

Print the Google Doc URL. Print the local path to the xlsx. Remind about manual upload + share. Estimate the manual work at ~60 seconds.
