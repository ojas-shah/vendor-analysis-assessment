# Vendor Analysis Assessment — Project Context

You are assisting the VP of Operations with an acquisition-due-diligence vendor analysis. This file is auto-loaded by Claude Code at session start.

## Mission

Analyze vendors representing the trailing-twelve-months spend of a newly acquired company. For each vendor:

1. Assign a **Department** (use the taxonomy in `01-inputs/department-taxonomy.md` — derived from the source spreadsheet's reference tab).
2. Write a **one-line description** of what the vendor does.
3. Recommend an **action**: `Terminate`, `Consolidate`, or `Optimize`.

Then identify the **Top 3 highest-impact savings opportunities** (spend-weighted, financially justified), document the **methodology**, and write a **1-page executive memo** for the CEO/CFO.

## How this project is organized

```
01-inputs/         ← Source data, taxonomy, any provided files
02-prompts/        ← Every LLM prompt used, versioned and reusable
03-scripts/        ← Python automation (uses Anthropic SDK)
04-outputs/        ← Final deliverables (xlsx + docx + pdf)
05-validation/     ← QC reports, audit trail
.claude/agents/    ← Custom subagents for QC and categorization
.claude/commands/  ← Custom slash commands for each pipeline phase
```

## Working principles

- **Reproducibility first.** Every prompt lives in `02-prompts/` as a markdown file. Never run a prompt that isn't checked in there.
- **QC is non-negotiable.** Every first-pass classification gets an independent second pass. Disagreements get reconciled with a tiebreaker prompt that sees both reasonings. Audit trail lives in `05-validation/qc-report.md`.
- **Spend-weighted reasoning.** Top 3 opportunities must be justified in dollars, not vendor counts. The single $200K vendor matters more than ten $2K vendors.
- **Consolidation requires evidence.** Never mark something `Consolidate` without naming the peer vendors that justify it.
- **Conservative on Terminate.** `Terminate` on a high-spend vendor should be flagged for human review, not auto-applied.

## Pipeline order

1. `/setup-source` slash command — pull source Google Sheet via Drive MCP into `01-inputs/vendors-raw.xlsx`
2. `python 03-scripts/smoke_test.py` — verify auth works (~$0.005)
3. `python 03-scripts/analyze_vendors.py` — first-pass enrichment (~5 min)
4. `python 03-scripts/qc_validate.py` — independent second pass (~5 min)
5. `python 03-scripts/reconcile.py` — resolve disagreements (~1 min)
6. `python 03-scripts/top_opportunities.py` — derive Top 3 opportunities
7. `python 03-scripts/generate_memo.py` — produce executive memo (markdown only)
8. `python 03-scripts/build_deliverable.py` — assemble local xlsx
9. `/publish-to-drive` slash command — upload memo as Google Doc, xlsx as Google Sheet, then re-build xlsx with the Doc URL embedded in the Recommendations tab

The slash commands `/setup-source`, `/analyze-batch`, `/qc-pass`, `/top3`, `/exec-memo`, `/publish-to-drive` orchestrate these in sequence inside Claude Code.

## Google Drive MCP integration

This project relies on the Anthropic Google Drive MCP (`https://drivemcp.googleapis.com/mcp/v1`) for both input and output:

- **Input** — `/setup-source` uses `download_file_content` to fetch the source spreadsheet from the user's Drive as xlsx, decodes the base64 via `save_source_from_drive.py`, and writes `01-inputs/vendors-raw.xlsx` for the pipeline to consume.
- **Output** — `/publish-to-drive` uses `create_file` to upload the executive memo (as `text/plain`, which Drive auto-converts to a native Google Doc) and the final spreadsheet (as xlsx, which Drive converts to Google Sheets format on upload). The Google Doc URL is embedded back into the Recommendations tab of the spreadsheet before the second upload.

Available Drive MCP tools: `create_file`, `download_file_content`, `read_file_content`, `search_files`, `get_file_metadata`, `get_file_permissions`, `list_recent_files`, `copy_file`. Note: there is no permissions-update tool — sharing must be set manually in the Drive UI (one click per file).

## When the user asks for help

Default to suggesting they use the scripts and slash commands here rather than ad-hoc prompts — that's the point of the project. If something needs improvement, edit the prompt file in `02-prompts/`, not the inline tool call.
