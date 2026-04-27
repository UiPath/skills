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

## How update-prompts Works

`update-prompts` supports two levels of instruction updates:

- **`--fields`** (required): per-field instructions (moon_form fields like "Invoice Number", "Invoice Date"). Match by field name.
- **`--groups`** (optional): field group instructions (label_defs like "Invoice", "Line Items"). Match by label_def name.

Both can be used together in a single call. The CLI fetches the taxonomy, merges changes, and sends updates per label_def — preserving all fields and definitions you didn't change.

Omitting `--label-instructions` preserves the existing project-level prompt — it is NOT wiped.

**Aligning group and field instructions.** Each label_def (e.g., "Invoice") has its OWN `instructions` field that the model also sees alongside per-field instructions. If the group instruction says "Monetary fields: decimal format, no currency symbol" but a per-field instruction says "submit as-written with commas", the model gets contradictory signals. When updating field instructions, also update the parent group instruction with `--groups` if it contradicts.

## Before Starting

The user may specify a max number of iterations (default: 3). Track:

- **Baseline metrics** — the per-field F1 scores before any changes
- **Previous iteration metrics** — the per-field F1 scores from the last successful iteration
- **Previous instructions** — the per-field (moon_form) instructions from the last successful iteration (for rollback)

Do NOT re-read the taxonomy or sample documents between iterations — use what you already have. Only re-read metrics after each instruction update + retrain cycle.

## Step 1 — Setup (once, before the loop)

### 1a. Get baseline metrics

```bash
mkdir -p /tmp/ixp/<project-name>/{docs,text,taxonomies,prompts}
uip ixp project metrics <project-name> --output json
```

Save the full per-field `Fields` array as `baseline_metrics`. This is the starting point you compare against.

**Correlating metrics to field names:** The metrics `Fields` array returns `FieldId` but not the field name. To map them, join against the taxonomy's `moon_form` entries:

- For each metric entry: `FieldGroup` = label_def name, `FieldId` = moon_form `field_id`
- Find the matching `moon_form` entry in the taxonomy where `field_id == FieldId` — its `name` is the human-readable field name

Build this mapping once and reuse it throughout the loop.

### 1b. Check model configuration

If many fields have low scores across the board, the model configuration may be wrong (e.g., no table pre-processing for table-heavy documents). View sample documents and check if the current config matches the document type. If not, reconfigure:

```bash
uip ixp project configure-model <project-name> \
  --model gemini_2_5_flash \
  --preprocessing <none|table_mini|table> \
  --attribution model \
  --output json
```

See the [Project Setup Guide](project-setup.md) Step 2 for the decision table.

### 1c. Get taxonomy

```bash
uip ixp project taxonomy <project-name> --output json
```

Save to `/tmp/ixp/<project-name>/taxonomies/v1.json`. This includes `label_defs` → `moon_form` fields with their current `instructions`. These per-field instructions are what you'll be iterating on. Increment the version after each `update-prompts` (v2, v3, …).

The `moon_form` field `name` (e.g., `"Invoice Number"`, `"Description"`) is what you pass to `update-prompts --fields`.

### 1d. Read sample documents (2-3 documents)

```bash
uip ixp document list <project-name> --output json

# For each sample document:
uip ixp document get <project-name> <comment-uid> -o /tmp/ixp/<project-name>/docs/sample.png --output json
uip ixp document text <project-name> <comment-uid> --output json
```

Save OCR output to `/tmp/ixp/<project-name>/text/sample.json`. View the images with the **Read tool** and review the OCR text. These files persist across sessions — check for existing files before downloading.

### 1e. Check for unlabelled documents

Compare the document list against the metrics. If the metrics show fewer `ValidatedDocuments` than the total document count, some documents have no confirmed labellings (e.g., newly added documents). Review and label them first using the [Label Documents Guide](label-documents.md), then wait ~2 minutes for retrain and re-fetch metrics before starting the loop.

---

## Step 2 — Optimization Loop

Repeat the following for each iteration (up to max iterations):

### 2a. Diagnose fields

Use the current metrics (baseline on first iteration, post-relabel metrics on subsequent iterations).

Identify individual fields with F1 < 0.7 as targets. Diagnose each:

1. **Classify the action:**
   - `Documents = 0` AND `F1 = 0` → **SKIP**
   - `Documents < 1` → **SKIP**
   - Otherwise → **REFINE**

2. **Diagnose the problem type** (use F1 as primary signal with few documents):
   - `Precision < Recall` significantly → **PRECISION** — model extracts wrong values
   - `Recall < Precision` significantly → **RECALL** — model misses the field
   - Both low → **BOTH** — rewrite entirely
   - Otherwise → **MIXED** — improve generally

Print a diagnosis summary showing each field's name, F1, precision/recall, and diagnosis.

If no fields need REFINE, stop — the project is already at target quality.

### 2a-check. Check for labelling gaps (before writing instructions)

For each REFINE field with **Recall < 0.5**, check whether the problem is a bad prompt or a missing label:

1. Look at the sample document images you already have from Step 1d
2. For each low-recall field, check: **can you see this field's value in the document?**
   - If yes, the model may have predicted it correctly but it wasn't confirmed in a previous round → re-fetch predictions and review those fields again
   - If the field is genuinely not visible in the document → it's a prompt/recall issue, handle with instruction changes

**If you find previously skipped predictions that are actually correct**, confirm them now using `labelling confirm --fields` for those specific documents and fields. Wait ~2 minutes for retrain and re-fetch metrics before continuing.

**If no labelling gaps are found**, proceed directly to writing instructions.

### 2b. Write improved instructions

For each field marked REFINE, rewrite its moon_form field `instructions`:

- **PRECISION** → Be more specific about WHAT to extract and what NOT to extract
- **RECALL** → Better describe WHERE to find the field
- **BOTH** → Full rewrite — what, where, format, what to avoid
- **MIXED** → Fill quality gaps (location hints, examples, format guidance)

**Rules** (see also "Instruction Quality Standards" in the main skill):

1. NEVER reference specific page numbers — use section headings or labels
2. Each instruction must be **120+ characters** with location hint, format pattern, and real example from the documents
3. For fields visible in the sample documents, use the real data you observed (location, label on page, format, example value)
4. For fields NOT visible in the sample documents, use a generic instruction with no example
5. Each instruction targets one specific field (e.g., "Invoice Number", "Invoice Date")
6. On iteration 2+, do NOT repeat the same instruction that failed last time — try a different approach (different wording, different location hints, add negative examples)

Save the current field instructions before updating (for rollback).

### 2c. Update instructions

Use **field names** for `--fields` and **label_def names** for `--groups`:

```bash
cat > /tmp/ixp/<project-name>/prompts/field_updates.json << 'FIELDS_EOF'
[
  {"name": "Invoice Number", "instructions": "The unique document identifier, found in the header area top-right. Example: 2106732, QC006."},
  {"name": "Invoice Date", "instructions": "The date the invoice was issued. Use the exact format as written in the document. Found near the invoice number."}
]
FIELDS_EOF

cat > /tmp/ixp/<project-name>/prompts/group_updates.json << 'GROUPS_EOF'
[
  {"name": "Invoice", "instructions": "General invoice header fields including number, dates, payment terms, and totals."}
]
GROUPS_EOF

uip ixp project update-prompts <project-name> \
  --fields "$(cat /tmp/ixp/<project-name>/prompts/field_updates.json)" \
  --groups "$(cat /tmp/ixp/<project-name>/prompts/group_updates.json)" \
  --output json
```

`--groups` is optional — omit it if the group instructions don't need changing.

**Post-update verification:** After `update-prompts`, re-fetch the taxonomy and verify that `moon_form` field counts per label_def are unchanged:

```bash
uip ixp project taxonomy <project-name> --output json
```

Compare the number of `moon_form` entries in each updated label_def against what you saved in Step 1c. If any fields are missing, **STOP the workflow immediately** and report to the user — the taxonomy was corrupted and needs manual restoration.

### 2d. Review and confirm predictions for all documents

After updating instructions, review predictions for all documents using the [Label Documents Guide](label-documents.md). The updated prompts should produce better predictions — review each document's predictions against the actual content and confirm the ones that are correct. Documents with incorrect predictions are skipped (their old labels remain).

### 2e. Wait and get new metrics

Wait ~2 minutes for server-side retraining, then:

```bash
uip ixp project metrics <project-name> --output json
```

If `ModelVersion` hasn't advanced, wait another 60 seconds and retry. **What triggers retrain:** Any change to model inputs — labellings OR instructions — triggers a full model retrain. Even changing 1 field's instruction retrains the whole model. Retrain typically takes ~2 minutes. If no advance after 5 minutes, stop polling.

### 2f. Compare and decide

Compare the new per-field F1 scores against the **previous iteration** scores.

**Selective regression check:** For each field you updated this iteration, check if F1 dropped by more than 0.1:

- **Regressed fields** (F1 dropped >0.1): roll back ONLY those fields' instructions to the previous iteration's version. Keep the improved instructions for fields that gained or held steady.
- **Improved/unchanged fields**: keep their new instructions.

If any fields regressed, do a selective rollback:

```bash
# Only include the regressed fields, not the whole iteration
cat > /tmp/ixp/<project-name>/prompts/rollback.json << 'FIELDS_EOF'
[{"name": "Vendor Address", "instructions": "previous instruction for this field only"}]
FIELDS_EOF

uip ixp project update-prompts <project-name> \
  --fields "$(cat /tmp/ixp/<project-name>/prompts/rollback.json)" \
  --output json
```

Wait ~2 minutes for retrain. On the next iteration, try a **different approach** for the regressed fields only (different wording, shorter instruction, fewer examples).

**Rollback caveat:** Rollback restores the previous instructions but the model needs to retrain. Expect only **partial recovery** — prefer small-scope iterations (few fields at a time).

**No regression:** Accept the iteration. Update `previous_metrics` and `previous_instructions` with the new values.

**Stopping criteria — stop the loop if:**

- All fields have F1 >= 0.7 (target reached)
- Max iterations reached
- No fields improved in the last iteration (diminishing returns)

---

## Step 3 — Final Report

After the loop ends, print a summary:

```text
Optimization complete after N iterations.

Field               | Baseline F1 | Final F1 | Change
--------------------|-------------|----------|-------
Invoice Number      | 0.450       | 0.820    | +0.370
Description         | 0.300       | 0.650    | +0.350
Bill-To Name        | 0.900       | 0.900    | (unchanged)
Vendor Address      | 0.600       | 0.400    | -0.200 (rolled back)

Overall project score: X.XX → Y.YY
Iterations: N total, M with rollbacks
Fields still below target (F1 < 0.7): [list]
Labelling gaps fixed: [list any fields re-labelled in 2a-check]
```

If fields still need work, suggest the user run another round with more iterations.
