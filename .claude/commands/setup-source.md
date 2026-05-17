---
description: Download the source Vendor Spend Strategy Google Sheet from Drive into 01-inputs/vendors-raw.xlsx
---

Fetch the source spreadsheet from Google Drive via the Drive MCP.

**Prereq:** the Google Drive MCP must be connected. If not, tell the user to run `claude mcp add --transport http google-drive https://drivemcp.googleapis.com/mcp/v1`, then `/mcp` to authenticate, then come back.

Steps:

1. Default source file ID is `1YaimnCR6OUGKbQ9BTegmwnS4kMA7izmayjjXHs19cqo` — this is the assessment template "A - TEMPLATE - RWA - Vendor Spend Strategy (NAME)" owned by heather.lother@crossover.com. If the user passes a different file ID as an argument, use that instead.

2. Call the Drive MCP tool `download_file_content` with:
   - `fileId`: <id from step 1>
   - `exportMimeType`: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

3. The response is JSON shaped `{content: <base64>, id, mimeType, title}`. Write that response (as JSON) to `/tmp/drive_source.json` using the Write tool.

4. Run: `python 03-scripts/save_source_from_drive.py /tmp/drive_source.json`. This decodes the base64 and writes `01-inputs/vendors-raw.xlsx`.

5. Verify with `python 03-scripts/profile_data.py`. Confirm the vendor count and total spend match expectations (386 vendors, ~$7.88M total spend, Salesforce as largest).

6. If the verify step shows different numbers, the source may have been updated since the analysis was designed — surface this to the user before they proceed.

7. Report success and tell the user they can now run `python 03-scripts/smoke_test.py` (verify API key) followed by `/analyze-batch`.
