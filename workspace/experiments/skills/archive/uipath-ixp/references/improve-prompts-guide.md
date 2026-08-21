# Improve Prompts Guide

Iterative optimization loop for improving extraction quality on an existing IXP project. Runs multiple iterations automatically, rolling back if scores regress.

## What Prompts CAN and CANNOT Fix

Before starting, understand the limits of prompt iteration:

**Prompts CAN fix:**

- Fields where the model extracts the wrong value (precision problems) — better instructions clarify what to extract
- Fields where the model misses the value entirely (recall problems) — location hints help the model find the field
- Ambiguous fields where the model picks the wrong candidate — negative examples and disambiguation rules help

**Neither prompts nor reviewing can fix:**

- **OCR quality issues** — if the OCR consistently garbles a field's text, no instruction will fix it. However, during the review step, OCR-mangled predictions can be corrected using `labelling confirm --corrections` (keeps the reference, fixes the text). If many fields are OCR-mangled across multiple documents, report this to the user as a data quality issue rather than burning prompt iterations.
- **Missing fields** — if a field simply doesn't exist in the documents, no instruction will conjure it.

## How prompt updates work

Prompts live at two levels and are edited by two separate commands:

- **`uip ixp fields update-prompts <project> --updates <json>`** — per-field instructions (e.g., "Invoice Number", "Invoice Date"). Match by field name.
- **`uip ixp groups update-prompts <project> --updates <json>`** — field group (label_def) instructions (e.g., "Invoice", "Line Items"). Match by label_def name.

Each command sends one server-side call; the server matches by name and writes per affected label_def, preserving every definition you didn't change. To update both field and group instructions in the same iteration, run the two commands back-to-back.

**Aligning group and field instructions.** Each label_def (e.g., "Invoice") has its OWN `instructions` field that the model sees alongside per-field instructions. If the group instruction says "Extract only fields visible on the first page" but a per-field instruction says "Found in the summary table on page 2", the model gets contradictory signals. When updating field instructions, also update the parent group instruction with `groups update-prompts` if it contradicts.

## Before Starting

The user may specify a max number of iterations (default: 3). Track:

- **Baseline metrics** — the per-field F1 scores before any changes
- **Previous iteration metrics** — the per-field F1 scores from the last successful iteration
- **Previous instructions** — the per-field (field) instructions from the last successful iteration (for rollback)

Do NOT re-read the taxonomy or sample documents between iterations — use what you already have. Only re-read metrics after each instruction update + retrain cycle. This assumes no one modifies the taxonomy or documents externally during the loop. If the user mentions changes were made in the web UI, re-fetch the taxonomy and document list before continuing.

## Step 1 — Setup (once, before the loop)

### 1a. Get baseline metrics

If documents were just labelled (or uploaded, or the taxonomy was edited), wait ~2 minutes for the resulting retrain to complete before reading metrics. Reading mid-retrain captures *pre*-change scores and corrupts every downstream comparison.

```bash
mkdir -p /tmp/ixp/<project-name>/{docs,taxonomies,prompts}
uip ixp projects get-metrics  <project-name> --output json > /tmp/ixp/<project-name>/metrics_baseline.json
uip ixp projects get-taxonomy <project-name> --output json > /tmp/ixp/<project-name>/taxonomies/v1.json
```

Note the `ModelVersion` from the baseline — later iterations check that it advances after each `fields update-prompts` / `groups update-prompts` (see step 2e). If the value looks identical to a known pre-labelling version, the retrain may still be in flight; wait another 60 seconds and re-fetch.

(For a validated model, get-metrics Data is flat — `Fields`/`FieldGroups`/`ValidatedDocuments` are top-level. An unvalidated model returns `Data: { Metrics: null }` instead — wait for retrain and re-fetch.)

### 1b. Check model configuration

If many fields have low scores across the board, the model configuration may be wrong (e.g., no table pre-processing for table-heavy documents). View sample documents and check if the current config matches the document type. If not, reconfigure:

```bash
uip ixp projects configure-model <project-name> \
  --model gemini_2_5_flash \
  --preprocessing <none|table_mini|table> \
  --output json
```

See the [Project Setup Guide](project-setup-guide.md) Step 2 for the decision table.

### 1c. Get taxonomy

```bash
uip ixp projects get-taxonomy <project-name> --output json
```

Save to `/tmp/ixp/<project-name>/taxonomies/v1.json`. Output is `{ status, dataset: { entity_defs, label_groups } }` (raw snake_case); each `dataset.label_groups[]` holds `label_defs` with their fields and current `instructions`. These per-field instructions are what you'll be iterating on. Increment the version after each prompt update (v2, v3, …).

The field `name` (e.g., `"Invoice Number"`, `"Description"`) is what you pass to `fields update-prompts --updates`.

### 1d. Read sample documents (2-3 documents)

```bash
uip ixp documents list <project-name> --output json

# For each sample document:
uip ixp documents download <project-name> <document-id> -o /tmp/ixp/<project-name>/docs/sample --output json
```

The `download` command auto-detects format and appends the correct extension — read the resolved `Path` from the response. View the document with the **Read tool** — one full Read per document, **no `pages` parameter** (returns text + image natively for PDF/PNG/JPG). Files persist across sessions — check for existing files before downloading.

### 1e. Check for unlabelled documents

Compare the document list against the metrics. If the metrics show fewer `ValidatedDocuments` than the total document count, some documents have no confirmed labellings (e.g., newly added documents). Review and label them first using the [Label Documents Guide](label-documents-guide.md), then wait ~2 minutes for retrain and re-fetch metrics before starting the loop.

---

## Step 2 — Optimization Loop

Repeat the following for each iteration (up to max iterations):

### 2a. Diagnose fields and field groups

Run `diagnose_fields.py` (see SKILL.md § Scripts) on the current metrics file and taxonomy:

```bash
# First iteration: use baseline. Subsequent iterations: use the latest metrics file.
python3 scripts/diagnose_fields.py \
  --metrics /tmp/ixp/<project-name>/metrics_baseline.json \
  --taxonomy /tmp/ixp/<project-name>/taxonomies/v1.json
```

The script prints field group scores and per-field rows with action (SKIP / OK / REFINE) and problem type (PRECISION / RECALL / BOTH). If no fields are REFINE, stop — the project is already at target quality.

**Interpreting the output (your judgment):**
- PRECISION problem → model extracts wrong values; tighten what to extract and what NOT to
- RECALL problem → model misses the field; add location hints describing WHERE it appears
- BOTH → full rewrite: what, where, what to avoid

### 2a-check. Check for labelling gaps (before writing instructions)

For each REFINE field with **Recall < 0.5**, check whether the problem is a bad prompt or a missing label:

1. Look at the sample document images you already have from Step 1d
2. For each low-recall field, check: **can you see this field's value in the document?**
   - If yes, the model may have predicted it correctly but it wasn't confirmed in a previous round → re-fetch predictions and review those fields again
   - If the field is genuinely not visible in the document → it's a prompt/recall issue, handle with instruction changes

**If you find previously skipped predictions that are actually correct**, confirm them now using `labelling confirm --fields` for those specific documents and fields. Wait ~2 minutes for retrain and re-fetch metrics before continuing.

**If no labelling gaps are found**, proceed directly to writing instructions.

### 2b. Write improved instructions

For each field marked REFINE, rewrite its `instructions`:

- **PRECISION** → Be more specific about WHAT to extract and what NOT to extract
- **RECALL** → Better describe WHERE to find the field
- **BOTH** → Full rewrite — what, where, what to avoid

**Instruction quality standards:**

Focus on **what** to extract and **where** to find it. Do NOT specify format — the entity_def (field type) already handles that.

- **Minimum length**: 120+ characters. Short instructions like "Extract the date" are too vague.
- **Location hint**: describe WHERE in the document (section, header area, table, near a label). Keywords: "section", "header", "table", "top of", "labeled", "near".
- **Real example**: include an actual value from the documents (e.g., "Example: '2106732'", "Example: 'SINV0077023'").
- **Disambiguation**: if similar fields exist, clarify what NOT to extract (e.g., "Do NOT confuse with PO Number").
- **No format patterns**: do NOT include "Format: MM/DD/YYYY" or similar — the entity_def type (Date, Monetary, Text) already defines the format. Adding format in instructions creates conflicting signals.

**Good instruction** (145 chars):
> "The unique invoice identifier, found in the header area near the top-right, labeled 'Invoice #' or 'Invoice Number'. Example: '2106732'."

**Bad instruction** (25 chars):
> "Extract the invoice number"

**For fields visible in documents** — include location and a real example from the actual documents.
**For fields NOT visible** — use a generic instruction with no example: "Extract [what] from this document, as it appears on the page."

**Additional rules:**

1. NEVER reference specific page numbers — use section headings or labels
2. Each instruction targets one specific field (e.g., "Invoice Number", "Invoice Date")
3. On iteration 2+, do NOT repeat the same instruction that failed last time — try a different approach (different wording, different location hints, add negative examples)

### 2c. Update instructions

Validate instructions first, then send to the API:

```bash
# Validate before sending (hard rules: min 120 chars, location-hint keyword)
python3 scripts/validate_instructions.py \
  --updates /tmp/ixp/<project-name>/prompts/field_updates.json
# Fix all ERRORs before continuing. WARNs are advisory.

# Send to API
uip ixp fields update-prompts <project-name> \
  --updates "$(cat /tmp/ixp/<project-name>/prompts/field_updates.json)" \
  --output json

# If group instructions also need updating, run a second command.
uip ixp groups update-prompts <project-name> \
  --updates "$(cat /tmp/ixp/<project-name>/prompts/group_updates.json)" \
  --output json
```

The group update is optional — skip it if the group instructions don't need changing.

**Post-update verification:** Re-fetch the taxonomy and run `check_taxonomy_delta.py`. If any fields are missing, STOP immediately — the taxonomy was corrupted and needs manual restoration.

```bash
uip ixp projects get-taxonomy <project-name> --output json > /tmp/ixp/<project-name>/taxonomies/v<N>.json

python3 scripts/check_taxonomy_delta.py \
  --old /tmp/ixp/<project-name>/taxonomies/v<N-1>.json \
  --new /tmp/ixp/<project-name>/taxonomies/v<N>.json
# Exit 0 → proceed. Exit 1 → STOP, restore from previous version.
```

### 2d. Review and confirm predictions for all documents

Wait ~2 minutes for the model to retrain with the updated instructions, then review predictions for all documents using the [Label Documents Guide](label-documents-guide.md). The updated prompts should produce better predictions — review each document's predictions against the actual content and confirm the correct ones. Documents with incorrect predictions are skipped (their old labels remain).

### 2e. Wait and get new metrics

Wait ~2 minutes for the model to retrain with the new labellings, then:

```bash
uip ixp projects get-metrics <project-name> --output json > /tmp/ixp/<project-name>/metrics_iter<N>.json
```

If `ModelVersion` hasn't advanced since the last check, wait another 60 seconds and retry.

### 2f. Compare and decide

Run `compare_metrics.py` to detect regressions and build the iteration summary:

```bash
python3 scripts/compare_metrics.py \
  --baseline /tmp/ixp/<project-name>/metrics_iter<N-1>.json \
  --current  /tmp/ixp/<project-name>/metrics_iter<N>.json \
  --taxonomy /tmp/ixp/<project-name>/taxonomies/v1.json \
  --out      /tmp/ixp/<project-name>/delta_iter<N>.json
```

Exit 0 → no regressions; accept the iteration and continue.
Exit 1 → some fields regressed (F1 drop > 0.1); roll back only those fields.

**Selective rollback (your judgment):** For each regressed field shown, restore its previous instructions. Keep improved fields as-is.

```bash
cat > /tmp/ixp/<project-name>/prompts/rollback.json << 'FIELDS_EOF'
[{"name": "Vendor Address", "instructions": "previous instruction for this field only"}]
FIELDS_EOF

uip ixp fields update-prompts <project-name> \
  --updates "$(cat /tmp/ixp/<project-name>/prompts/rollback.json)" \
  --output json
```

Wait ~2 minutes for retrain. On the next iteration, try a different approach for regressed fields (different wording, shorter instruction, fewer examples).

**Rollback caveat:** Rollback restores the previous instructions but the model retrains from scratch. Expect only partial recovery — prefer small-scope iterations (few fields at a time).

**Stopping criteria — stop the loop if:**

- All fields meet the user's target F1 (default: 0.7)
- Max iterations reached
- No fields improved in the last 2 consecutive iterations (diminishing returns)

---

## Step 3 — Final Report

Run `compare_metrics.py` one final time against baseline to produce the full summary:

```bash
python3 scripts/compare_metrics.py \
  --baseline /tmp/ixp/<project-name>/metrics_baseline.json \
  --current  /tmp/ixp/<project-name>/metrics_iter<N>.json \
  --taxonomy /tmp/ixp/<project-name>/taxonomies/v1.json
```

Add a header and footer with iteration count, rollback count, any fields still below target, and any labelling gaps fixed in step 2a-check. If fields still need work, suggest the user run another round with more iterations.
