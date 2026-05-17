# Vendor Analysis Assessment — Claude Code Runbook

**Candidate:** Ojas Shah
**Role:** AI-First VP of Operations
**Assessment:** Acquisition due diligence — analyze ~400 vendors, identify savings opportunities, brief the CEO/CFO.

This repository is a complete Claude Code project. You can see the methodology, tools used and prompts below. Anyone with access to the Anthropic API and the Claude Code CLI can reproduce the entire analysis by following the steps in the Quick start section.

**METHODOLOGY**

**1\. SETUP**  
Used Claude Opus 4.7 to build a Claude Code project based on the assessment's instructions.  
Prompt used: *\#Task: Review the expectation from the below assessment summary for an AI-First VP of Operations position. Design the best way for me to use Claude Code to complete this assessment. The approach should ensure that you have the right skills to help me complete this assessment. \#Context: \<Full text of assessment instructions\>*

**2\. PROJECT**  
The output included CLAUDE.md, .claude/agents, .claude/commands, versioned prompts in 02-prompts/, scripts in 03-scripts/. Every prompt used in the analysis is checked into the project so the work is auditable.

**3\. DATA SOURCE**  
The input data from Google Sheets was fetched directly from Google Drive via MCP using the /setup-source slash command. The command is re-usable, and can be used with any Google Sheet containing similar data.

**4\. FIRST-PASS ENRICHMENT**  
Used batch processing to process the 386 vendors in batches of 25 using analyze\_vendors.py, calling Claude with the prompt at 02-prompts/01-first-pass-prompt.md.This returned a structured JSON with department, description, recommendation, reasoning, and a self-reported confidence score.

**5\. INDEPENDENT QC PASS**  
qc\_validate.py re-classified every vendor using a different prompt (02-prompts/02-qc-pass-prompt.md) that biases toward conservatism. Crucially, the QC pass did NOT see the first pass's output — independence is the whole point of validation.

**6\. RECONCILIATION**  
reconcile.py compared the two passes line by line. Where they agreed, the answer was accepted (with averaged confidence). Where they disagreed, a tiebreaker prompt (03-reconciliation-prompt.md) saw both reasonings and made the final call. The full disagreement log is in 05-validation/qc-report.md — every vendor that needed a tiebreaker is listed there with both analyses and the resolution reasoning.

**7\. HUMAN-IN-THE-LOOP**  
qc-reviewer.md scrutinized the 20 highest-spend vendors providing any surfaced issues for human judgement. Allows for manual overrides in case there are any exceptions required.

**8\. STRATEGIC SYNTHESIS**  
top\_opportunities.py rolled vendors up by department and function, then prompted Claude with the spend-weighted view to identify the three highest-impact opportunities. Output is constrained to be specific (named vendors), financially justified (current spend → projected savings %), and realistic (effort \+ risk assessment).

**9\. EXECUTIVE MEMO**  
The /exec-memo slash command produced a 1-page CFO/CEO memo as markdown. The /publish-to-drive slash command then uploaded it to Google Drive as a native Google Doc (Drive auto-converted from text/plain).

**10\. PUBLISH**  
The /publish-to-drive slash command also uploaded this completed spreadsheet to the user's Google Drive via the Drive MCP. The Recommendations tab contains a link to the published Google Doc memo.

**11\. FINAL HUMAN REVIEW**  
Completed a final review of the full analysis, made updates as needed and cleaned up formatting.

**TOOLS USED:** Claude Opus 4.7, Claude Code CLI, Anthropic Python SDK (claude-sonnet-4-6 model), Anthropic Google Drive MCP (read source \+ publish deliverables), openpyxl.

**PROMPTS:** All prompts live as versioned markdown files in 02-prompts/. The full project is available at the GitHub repo provided with this submission. 


---

## Quick start (the 60-second version)

```bash
# 1. Install Claude Code (one-time)
npm install -g @anthropic-ai/claude-code

# 2. Set your API key (one-time)
export ANTHROPIC_API_KEY=sk-ant-...

# 3. Install Python deps (one-time)
cd Vendor-Analysis-Assessment
pip install -r 03-scripts/requirements.txt

# 4. Smoke test ($0.005, verifies auth works)
python 03-scripts/smoke_test.py

# 5. Connect Google Drive MCP (required — kit reads/writes Drive directly)
claude mcp add --transport http google-drive https://drivemcp.googleapis.com/mcp/v1

# 6. Launch Claude Code and run the pipeline
claude
/mcp                  # one-time: authenticate the google-drive server
/setup-source         # fetch source from Drive → 01-inputs/vendors-raw.xlsx
/analyze-batch        # first-pass classification
/qc-pass              # independent QC + reconciliation
/top3                 # top 3 strategic opportunities
/exec-memo            # draft + build local xlsx
/publish-to-drive     # upload memo as Google Doc + xlsx as Google Sheet
```

That's the headline. The rest of this README explains each step in detail.

---

## Part 1 — Setting up Claude Code (Optional if you have it set up already)

### Install

**macOS / Linux:**
```bash
npm install -g @anthropic-ai/claude-code
# or, via Homebrew:
brew install anthropic/claude/claude-code
```

**Windows (PowerShell):**
```powershell
npm install -g @anthropic-ai/claude-code
```

Verify the install:
```bash
claude --version
```

### Authenticate

You have two options:

**Option A — API key (recommended for scripting):**
```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
# Persist in ~/.zshrc or ~/.bashrc so scripts inherit it
```

**Option B — Interactive login:**
```bash
claude
# Then run /login inside the session
```

For this assessment, **use Option A** because the Python scripts in `03-scripts/` need the env var.

### Install Python dependencies

```bash
cd Vendor-Analysis-Assessment
pip install -r 03-scripts/requirements.txt
```

---

## Part 2 — The pipeline, step by step

The analysis is a 6-step pipeline. Each step is reproducible, has a saved prompt, and writes its output to disk so the next step can pick it up.

### Step 0 — Get the source data + verify auth

Use the slash command /setup-source followed by the Google Sheet id. This populates an xlsx at `01-inputs/vendors-raw.xlsx` and the canonical taxonomy is at `01-inputs/department-taxonomy.md` (auto-derived from the Config tab of the source spreadsheet).
```
/setup-source <Google Sheet id>
```

Optional if you have it set up already: Before doing anything else, run the smoke test to verify your API key works:

```bash
python 03-scripts/smoke_test.py
```

Expected output: three vendors classified with reasonable departments and recommendations. Costs ~$0.005. If this fails, fix it before continuing — don't burn the full $0.50 of the pipeline on broken auth.

Optional: run `python 03-scripts/profile_data.py` to inspect spend distribution before the analysis.

### Step 1 — First-pass enrichment

```bash
python 03-scripts/analyze_vendors.py
```

What it does: reads `01-inputs/vendors-raw.xlsx`, sends each vendor (in batches of 25) to Claude with the prompt at `02-prompts/01-first-pass-prompt.md`, and writes structured output to `04-outputs/pass1.jsonl`. Each line is one vendor with `{name, spend, department, description, recommendation, reasoning, confidence}`.

Inside Claude Code, you can also run this as a slash command:
```
/analyze-batch
```

### Step 2 — Independent QC pass

```bash
python 03-scripts/qc_validate.py
```

What it does: re-classifies every vendor using a **different prompt** (`02-prompts/02-qc-pass-prompt.md`) that does NOT see the first pass's answers. Writes to `04-outputs/pass2.jsonl`. This is the rigorous validation layer — the same vendor scored independently by two prompts.

Or in Claude Code:
```
/qc-pass
```

### Step 3 — Reconciliation

```bash
python 03-scripts/reconcile.py
```

What it does: compares pass1 and pass2 line-by-line. Where they agree → high-confidence final answer. Where they disagree → tiebreaker prompt (`02-prompts/03-reconciliation-prompt.md`) that sees both reasonings and decides. All disagreements and resolutions are logged to `05-validation/qc-report.md` — this audit trail is the strongest signal to the hiring manager that QC was real, not theater.

### Step 4 — Top 3 opportunities

```bash
python 03-scripts/top_opportunities.py
```

What it does: rolls up reconciled vendors by `(department, function)`. Spend-weighted. Identifies the three highest-impact opportunities with named vendors, current spend, estimated savings, and confidence. Writes to `04-outputs/top3.json`.

Or in Claude Code:
```
/top3
```

### Step 5 — Build the final spreadsheet

```bash
python 03-scripts/build_deliverable.py
```

Produces `04-outputs/Vendor Analysis Assessment - Ojas Shah.xlsx` with four tabs:
- **Vendor Analysis** — the 400-row enriched table
- **Top 3 Opportunities** — the rollup
- **Methodology** — how the analysis was done, prompts used, validation
- **Recommendations** — the executive memo

### Step 6 — Executive memo

```
/exec-memo
```

This slash command takes the reconciled data and Top 3 output and drafts a 1-page memo for CEO/CFO. Reviewed by you, saved as `executive-memo.md` and pasted into the Recommendations tab of the xlsx. The `/publish-to-drive` slash command then uploads the markdown to Google Drive where it becomes a native Google Doc.

---

## Part 3 — How this kit demonstrates AI-First operating

The hiring manager grades on (1) Claude Code fluency, (2) AI-driven QC, (3) structured methodology. Here's how this kit maps to each:

**Claude Code fluency** is demonstrated by:
- `CLAUDE.md` — project context Claude Code auto-loads
- `.claude/agents/` — custom subagents for specialized tasks
- `.claude/commands/` — reusable slash commands for the pipeline
- Scripts that use the Anthropic SDK directly when batch throughput matters

**AI-driven QC** is demonstrated by:
- Two independent enrichment passes with different prompts
- A reconciliation prompt that resolves disagreements with explicit reasoning
- The `qc-report.md` audit trail that shows every disagreement and how it was decided

**Structured methodology** is demonstrated by:
- Every prompt versioned in `02-prompts/`
- The Methodology tab in the final spreadsheet
- This README

---

## Project structure reference

```
Vendor-Analysis-Assessment/
├── README.md                          ← You are here
├── CLAUDE.md                          ← Auto-loaded project context
├── .claude/
│   ├── agents/
│   │   ├── vendor-categorizer.md      ← Subagent for first-pass enrichment
│   │   └── qc-reviewer.md             ← Subagent for independent QC
│   └── commands/
│       ├── analyze-batch.md           ← /analyze-batch
│       ├── qc-pass.md                 ← /qc-pass
│       ├── top3.md                    ← /top3
│       └── exec-memo.md               ← /exec-memo
├── 01-inputs/
│   ├── vendors-raw.xlsx               ← Source data (you provide)
│   └── department-taxonomy.md         ← Canonical department list
├── 02-prompts/
│   ├── 01-first-pass-prompt.md
│   ├── 02-qc-pass-prompt.md
│   ├── 03-reconciliation-prompt.md
│   ├── 04-top3-prompt.md
│   └── 05-executive-memo-prompt.md
├── 03-scripts/
│   ├── _common.py                     ← Shared helpers (prompt loader, API client, JSONL IO)
│   ├── smoke_test.py                  ← $0.005 auth check before running the full pipeline
│   ├── profile_data.py                ← Inspect the source file before analysis
│   ├── analyze_vendors.py             ← First-pass enrichment
│   ├── qc_validate.py                 ← Independent QC second pass
│   ├── reconcile.py                   ← Tiebreak disagreements
│   ├── top_opportunities.py           ← Spend-weighted Top 3
│   ├── generate_memo.py               ← Executive memo as markdown
│   ├── build_deliverable.py           ← Assemble final xlsx (supports --memo-url)
│   ├── save_source_from_drive.py      ← Decode Drive MCP response → vendors-raw.xlsx
│   └── requirements.txt
├── 04-outputs/
│   ├── pass1.jsonl                    ← Generated
│   ├── pass2.jsonl                    ← Generated
│   ├── reconciled.jsonl               ← Generated
│   ├── top3.json                      ← Generated
│   ├── Vendor Analysis Assessment - Ojas Shah.xlsx  ← Final
│   └── (no docx — memo lives in Drive as a Google Doc)
└── 05-validation/
    └── qc-report.md                   ← Generated audit trail
```

---

## Troubleshooting

**"ANTHROPIC_API_KEY not set"** — `export ANTHROPIC_API_KEY=sk-ant-...` and restart your shell.

**"Rate limit exceeded"** — The scripts respect rate limits with retries, but if you have a low-tier key, edit `BATCH_SIZE` in the scripts down to 10.

**"File not found: 01-inputs/vendors-raw.xlsx"** — Download the Google Sheet as `.xlsx` from File → Download → Microsoft Excel and place it there.

**Output looks off** — Read `05-validation/qc-report.md`. The disagreements between passes are usually the most informative signal about where the analysis is uncertain. If you want to override a categorization, edit `04-outputs/reconciled.jsonl` manually and re-run `build_deliverable.py`.
