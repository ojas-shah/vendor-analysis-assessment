"""Shared helpers used by every pipeline script.

Loading prompts from disk (so prompts stay editable in 02-prompts/),
calling Claude with retries (including proper 60s wait on 429s), and
reading the taxonomy.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from anthropic import Anthropic

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUTS_DIR = PROJECT_ROOT / "01-inputs"
PROMPTS_DIR = PROJECT_ROOT / "02-prompts"
OUTPUTS_DIR = PROJECT_ROOT / "04-outputs"
VALIDATION_DIR = PROJECT_ROOT / "05-validation"

OUTPUTS_DIR.mkdir(exist_ok=True)
VALIDATION_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Model config
# ---------------------------------------------------------------------------

MODEL = os.getenv("VENDOR_ANALYSIS_MODEL", "claude-sonnet-4-5")
MAX_TOKENS = 4096

_client = None


def client():
    """Lazy-init the Anthropic client. Reads ANTHROPIC_API_KEY from env."""
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set. "
                "Run: export ANTHROPIC_API_KEY=sk-ant-..."
            )
        _client = Anthropic(api_key=api_key)
    return _client


# ---------------------------------------------------------------------------
# Prompt loading
# ---------------------------------------------------------------------------

def load_prompt(filename):
    """Read a prompt file from 02-prompts/. Returns raw text."""
    path = PROMPTS_DIR / filename
    return path.read_text(encoding="utf-8")


def load_taxonomy():
    """Read the canonical department taxonomy from 01-inputs/department-taxonomy.md."""
    text = (INPUTS_DIR / "department-taxonomy.md").read_text(encoding="utf-8")
    in_block = False
    departments = []
    for line in text.splitlines():
        if line.strip().startswith("## Canonical departments"):
            in_block = True
            continue
        if in_block:
            if line.strip().startswith("##"):
                break
            if line.strip().startswith("- "):
                departments.append(line.strip()[2:].strip())
    if not departments:
        raise RuntimeError(
            "No departments found in 01-inputs/department-taxonomy.md."
        )
    return departments


def render_prompt(filename, **kwargs):
    """Load a prompt and substitute {{PLACEHOLDERS}}."""
    text = load_prompt(filename)
    taxonomy = "\n".join(f"- {d}" for d in load_taxonomy())
    text = text.replace("{{DEPARTMENT_TAXONOMY}}", taxonomy)
    for k, v in kwargs.items():
        text = text.replace(f"{{{{{k}}}}}", str(v))
    return text


# ---------------------------------------------------------------------------
# Anthropic call with retry (proper 60s wait on rate limits)
# ---------------------------------------------------------------------------

def call_claude(system, user, max_tokens=MAX_TOKENS, max_retries=5):
    """Send a single-turn request to Claude. Returns the text response.

    On 429 rate-limit errors, waits ~65s (one minute bucket plus margin)
    before retrying. On other transient errors, uses exponential backoff.
    """
    import anthropic
    for attempt in range(max_retries):
        try:
            response = client().messages.create(
                model=MODEL,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return response.content[0].text
        except anthropic.RateLimitError as exc:
            if attempt == max_retries - 1:
                raise
            wait = 65
            print(f"  [rate limit] waiting {wait}s for bucket reset...")
            time.sleep(wait)
        except Exception as exc:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** attempt
            print(f"  [retry] {type(exc).__name__}: {exc} - sleeping {wait}s")
            time.sleep(wait)
    raise RuntimeError("unreachable")


def parse_json_response(text):
    """Strip code fences and parse JSON."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)
    return json.loads(text)


# ---------------------------------------------------------------------------
# JSONL helpers
# ---------------------------------------------------------------------------

def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path):
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


# ---------------------------------------------------------------------------
# Vendor source loader
# ---------------------------------------------------------------------------

def load_source_vendors():
    """Read vendors-raw.xlsx and return [{name, spend}, ...]."""
    import openpyxl

    wb = openpyxl.load_workbook(INPUTS_DIR / "vendors-raw.xlsx", data_only=True)
    ws = wb["Vendor Analysis Assessment"]
    vendors = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        name = row[0]
        spend = row[2]
        if not name:
            continue
        vendors.append({
            "name": str(name).strip(),
            "spend": float(spend) if spend is not None else 0.0,
        })
    return vendors


def batched(items, size):
    return [items[i:i + size] for i in range(0, len(items), size)]
