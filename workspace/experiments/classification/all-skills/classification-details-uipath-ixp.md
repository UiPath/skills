# Classification Details — uipath-ixp

**Classification: Strong**

---

## What the Skill Teaches

UiPath IXP (Document Understanding) skill covering project creation, document upload, taxonomy authoring, prediction review, prompt improvement, model publishing, and metrics retrieval via `uip ixp`.

| # | Area | Codifiable? | Notes |
|---|------|-------------|-------|
| 1 | **Task navigation (request → CLI command mapping)** | **Yes — LOOKUP/REFERENCE-TABLE** | Lines 69–97 are a complete mapping table: every user intent resolves to an exact `uip ixp` command |
| 2 | **Project setup pipeline** | **Yes — TRANSFORM-PIPELINE** | Fixed sequence: list → create → upload → label → improve → publish |
| 3 | **Prediction review and confirmation** | **Yes — VALIDATE/CHECK** | Rules 8–15 define exact confirm/mark-missing/unconfirm logic with per-field and per-occurrence targeting |
| 4 | **Normalization validation** | **Yes — VALIDATE/CHECK** | Rule 8 specifies the exact normalization table (Date, Monetary Quantity formats) to confirm/reject predictions |
| 5 | Taxonomy authoring (add fields, groups, data types) | No | Requires judgment about field names, instructions, data types — design decisions |
| 6 | Prompt improvement loop | No | F1-driven iteration: determining *what* to improve in prompts requires judgment |
| 7 | **Metrics extraction and reporting** | **Yes — EXTRACT** | Deterministic command sequence: `get-metrics` → parse ProjectScore, FieldGroups[], Fields[] sorted lowest-F1 first |

---

## Codifiable Procedures (not yet scripted)

### 1. Task Navigation — LOOKUP/REFERENCE-TABLE

**Source:** `skills/uipath-ixp/SKILL.md` §Task Navigation

**What it does:** Maps a user's natural-language request to the exact `uip ixp` subcommand, flags, and arguments required. Inputs are user intent strings; outputs are copy-paste ready CLI commands. The table is exhaustive — every documented operation (publish, rollback, unpublish, untag, metrics, upload, delete, rename, move, label, unconfirm, mark-missing) has a dedicated row. Line 69: `"| User request | Action |"` opens a 28-row routing table where every row resolves intent to exact CLI syntax.

**Why it's mechanical:** Each row is a deterministic mapping from a recognized intent string to a single command invocation — no branching logic or user-specific judgment.

**Turn savings:** Without a lookup script the agent reads the full table on every request; a lookup function can resolve the command in one call.

---

### 2. Prediction Confirmation Workflow — VALIDATE/CHECK

**Source:** `skills/uipath-ixp/SKILL.md` §Critical Rules 8–15

**What it does:** For each document, fetches `get-predictions`, evaluates each predicted value against the normalization table (Date → `YYYY-MM-DDTHH:MM:SSZ`, Monetary Quantity → `<amount> <ISO-4217>`), decides confirm / mark-missing / leave-unannotated, and calls the appropriate `labellings` command. OCR garble is detected by the magnitude-preservation test (same value, different character rendering → `--corrections`; wrong answer → unannotated). Line 45: `"Decision test before every --corrections: is the predicted value the correct answer, merely mis-typed? If NO — a boolean that should flip, a wrong inferred/computed number, a normalized date or amount you want back in the page's format, or any value where the prediction picked the wrong answer — then --corrections is FORBIDDEN."` 

**Why it's mechanical:** The normalization mapping and the OCR-garble decision rule are fully specified; no judgment about business meaning is needed once the normalization table is applied.

**Turn savings:** Currently the agent applies normalization rules manually for each field across multiple turns; a script checks all fields in one pass and returns a structured confirm/skip/corrections payload.

---

### 3. Metrics Extraction and Report — EXTRACT + AGGREGATE/STATS

**Source:** `skills/uipath-ixp/SKILL.md` §Task Navigation, row "Show metrics / What are the scores?"

**What it does:** Runs `get-metrics` and `list-models`, parses the `Data` envelope, extracts live/published version tags from `Tags[]` and `Models[]`, reads `ProjectScore`/`ProjectScoreQuality`, and sorts `Fields[]` by ascending F1. Line 96: `"State numbers plainly; no 'good enough' judgement unless asked; route low scores to Improve Prompts Guide."` Output is a structured report: published version + overall score + per-group scores + per-field scores sorted lowest-F1 first.

**Why it's mechanical:** Field ordering (lowest-F1 first), version tag resolution, and envelope parsing are deterministic given the API response.

**Turn savings:** The agent currently reads and formats metrics manually across 2–3 turns; a script does it in one.

---

## Justification for Classification

**Strong** — not Partial, not None.

**Why not Partial:** The task navigation table (28 rows) combined with the validation loop (Critical Rules 8–15) and the metrics extraction workflow account for the majority of what the skill teaches. Even the taxonomy authoring actions (add-field, add-group, add-data-type) are routed through the same LOOKUP/REFERENCE-TABLE. The one judgment-heavy area — choosing what to change in prompts — is explicitly bounded by the metrics output (lowest-F1 first), making even that step partially mechanical.

**Why not None:** Three independent codifiable procedures exist: a LOOKUP/REFERENCE-TABLE (task navigation), a VALIDATE/CHECK (prediction review with normalization rules), and an EXTRACT + AGGREGATE/STATS (metrics report).

**Evidence locations:**
- LOOKUP/REFERENCE-TABLE: `SKILL.md` §Task Navigation (lines 69–97)
- VALIDATE/CHECK normalization rules: `SKILL.md` Critical Rule 8 (line 45)
- VALIDATE/CHECK confirm/mark-missing/unconfirm logic: `SKILL.md` Critical Rules 12–15 (lines 49–55)
- EXTRACT sorting rule: `SKILL.md` §Task Navigation row "Show metrics" (line 96)
