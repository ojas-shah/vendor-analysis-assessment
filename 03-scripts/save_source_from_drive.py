"""Decode a Google Drive MCP download response into 01-inputs/vendors-raw.xlsx.

The Drive MCP's download_file_content tool returns JSON with the file content
base64-encoded. This script extracts that content and writes the xlsx locally
so the rest of the pipeline (which reads from 01-inputs/) doesn't need to change.

Usage: python save_source_from_drive.py <path-to-response.json>
"""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: save_source_from_drive.py <response.json>")

    response_path = Path(sys.argv[1])
    if not response_path.exists():
        sys.exit(f"File not found: {response_path}")

    payload = json.loads(response_path.read_text(encoding="utf-8"))
    content = payload.get("content")
    if not content:
        sys.exit("No 'content' field found in response JSON.")

    try:
        xlsx_bytes = base64.b64decode(content)
    except Exception as exc:
        sys.exit(f"Base64 decode failed: {exc}")

    project_root = Path(__file__).resolve().parent.parent
    out = project_root / "01-inputs" / "vendors-raw.xlsx"
    out.write_bytes(xlsx_bytes)

    print(f"Saved source xlsx to: {out}")
    print(f"  Size: {len(xlsx_bytes):,} bytes")
    print(f"  Original title: {payload.get('title', '?')}")
    print(f"  Original mimeType: {payload.get('mimeType', '?')}")
    print(f"  Source file ID: {payload.get('id', '?')}")


if __name__ == "__main__":
    main()
