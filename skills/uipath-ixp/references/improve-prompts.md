# Improve Prompts Guide

Iterative optimization loop for improving extraction quality on an existing IXP project. Runs multiple iterations automatically, rolling back if scores regress.

## What Prompts CAN and CANNOT Fix

Before starting, understand the limits of prompt iteration:

**Prompts CAN fix:**

- Fields where the model extracts the wrong value (precision problems) — better instructions clarify what to extract
- Fields where the model misses the value entirely (recall problems) — location hints help the model find the field
- Ambiguous fields where the model picks the wrong candidate — negative examples and disambiguation rules help

**Prompts CANNOT fix (but re-labelling can):**

- **Typed field format mismatches** — if Date or Monetary Quantity fields score F1 = 0, the issue is value format, not instructions. Fix by re-labelling with the value **as-written in the document** (the model predicts in the document's own format). The optimization loop handles this automatically — fields are classified as FIX FORMAT and included in re-labelling.

**Neither prompts nor re-labelling can fix:**

- **OCR quality issues** — if the OCR consistently garbles a field's text, no instruction will make the model extract it correctly. Report to the user.
- **Missing fields** — if a field simply doesn't exist in the documents, no instruction will conjure it.

## How update-prompts Works

`update-prompts --fields` updates individual **field instructions** (moon_form fields like "Invoice Number", "Invoice Date"). Match by field name — the CLI fetches the taxonomy, finds which label_def contains each field, merges the instruction change, and sends all fields in that label_def back (preserving fields you didn't change).

Omitting `--label-instructions` preserves the existing project-level prompt — it is NOT wiped.

**Warning: label_def vs field instruction conflicts.** Each label_def (e.g., "Invoice") has its OWN `instructions` field that the model also sees. `update-prompts --fields` does NOT touch this. If the label_def instructions say "Monetary fields: decimal format, no currency symbol" but your per-field instruction says "submit as-written with commas", the model gets contradictory signals. Before iterating, read each label_def's `instructions` in the taxonomy and ensure they don't contradict the per-field instructions you're writing.

## Before Starting

The user may specify a max number of iterations (default: 3). Track:

- **Baseline metrics** — the per-field F1 scores before any changes
- **Previous iteration metrics** — the per-field F1 scores from the last successful iteration
- **Previous instructions** — the label_def instructions from the last successful iteration (for rollback)

Do NOT re-read the taxonomy or sample documents between iterations — use what you already have. Only re-read metrics after each re-label cycle.

## Step 1 — Setup (once, before the loop)

### 1a. Get baseline metrics

```bash
mkdir -p /tmp/ixp
uip ixp project metrics <project-name> --output json
```

Save the full per-field `Fields` array as `baseline_metrics`. This is the starting point you compare against.

**Check for format issues first.** If any typed fields (Date, Monetary Quantity) have F1 = 0, these are format mismatches — not prompt issues. Fix them BEFORE starting the optimization loop:
1. Re-label all documents using Steps 2-5 of the [Project Setup Guide](project-setup.md), submitting typed field values as-written in the document
2. Wait ~2 minutes for retrain
3. Re-fetch metrics — the typed fields should now have F1 > 0
4. Use these refreshed metrics as `baseline_metrics` for the loop

This ensures the optimization loop only targets fields that actually need prompt improvement.

### 1b. Get taxonomy

```bash
uip ixp project taxonomy <project-name> --output json
```

Save the full taxonomy including `label_defs` → `moon_form` fields with their current `instructions`. These per-field instructions are what you'll be iterating on.

The `moon_form` field `name` (e.g., `"Invoice Number"`, `"Description"`) is what you pass to `update-prompts --fields`.

### 1c. Read sample documents (2-3 documents)

```bash
uip ixp document list <project-name> --output json

# For each sample document:
uip ixp document get <project-name> <comment-uid> -o /tmp/ixp/sample.png --output json
uip ixp document text <project-name> <comment-uid> --output json
```

View the images with the **Read tool** and review the OCR text. This gives you visual and textual context for writing instructions. You will NOT re-read these in subsequent iterations.

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

### 2b. Write improved instructions

For each field marked REFINE, rewrite its label_def `instructions`:

- **PRECISION** → Be more specific about WHAT to extract and what NOT to extract
- **RECALL** → Better describe WHERE to find the field
- **BOTH** → Full rewrite — what, where, format, what to avoid
- **MIXED** → Fill quality gaps (location hints, examples, format guidance)

**Rules:**

1. NEVER reference specific page numbers — use section headings or labels
2. Include format guidance and a realistic example when possible
3. Keep instructions 2-4 sentences per field
4. Each instruction targets one specific field (e.g., "Invoice Number", "Invoice Date") — write it to describe that exact field
5. On iteration 2+, do NOT repeat the same instruction that failed last time — try a different approach (different wording, different location hints, add negative examples)

Save the current field instructions before updating (for rollback).

### 2c. Update instructions

Use the **field name** (e.g., "Invoice Number", "Invoice Date"), not the label_def name:

```bash
cat > /tmp/ixp/updates.json << 'FIELDS_EOF'
[
  {"name": "Invoice Number", "instructions": "The unique document identifier, found in the header area top-right. Example: 2106732, QC006."},
  {"name": "Invoice Date", "instructions": "The date the invoice was issued. Use the exact format as written in the document. Found near the invoice number."}
]
FIELDS_EOF

uip ixp project update-prompts <project-name> \
  --fields "$(cat /tmp/ixp/updates.json)" \
  --output json
```

**Post-update verification:** After `update-prompts`, re-fetch the taxonomy and verify that `moon_form` field counts per label_def are unchanged:

```bash
uip ixp project taxonomy <project-name> --output json
```

Compare the number of `moon_form` entries in each updated label_def against what you saved in Step 1b. If any fields are missing, **STOP the workflow immediately** and report to the user — the taxonomy was corrupted and needs manual restoration.

### 2d. Re-label all documents

Follow Steps 2-5 of the [Project Setup Guide](project-setup.md) to re-label all documents.

**CRITICAL: Do NOT change labelling values to match IXP's predictions.** Extract what you see in the document — the same way you did in the initial labelling. The goal of re-labelling is for IXP to retrain against your (correct) extractions with the new prompts. If a field's F1 is low, the fix is better prompts, not changing your labels to match the model. Only modify a labelling if you genuinely made an error the first time (missed a field, extracted the wrong value, used the wrong format).

### 2e. Wait and get new metrics

Wait ~2 minutes for server-side retraining, then:

```bash
uip ixp project metrics <project-name> --output json
```

If `ModelVersion` hasn't advanced, wait another 60 seconds and retry. **Important:** ModelVersion does NOT advance on identical re-submissions. If labellings didn't actually change (same values submitted), no retrain will occur. On changed labellings, retrain typically takes ~2 minutes. If no advance after 5 minutes, stop polling.

### 2f. Compare and decide

Compare the new per-field F1 scores against the **previous iteration** scores:

**Regression check:** If ANY field's F1 dropped by more than 0.1 compared to the previous iteration:

1. Report the regression to the user (which fields, old vs new scores)
2. **Roll back** — restore the previous iteration's instructions:

   ```bash
   cat > /tmp/ixp/rollback.json << 'FIELDS_EOF'
   [{"name": "...", "instructions": "previous instruction"}, ...]
   FIELDS_EOF

   uip ixp project update-prompts <project-name> \
     --fields "$(cat /tmp/ixp/rollback.json)" \
     --output json
   ```

3. Re-label all documents with the rolled-back instructions
4. Try a **different approach** for the regressed fields on the next iteration

**Rollback caveat:** Rollback is NOT atomic — the model has already retrained on the regressed labels, so re-submitting the previous iteration's values won't snap F1 back to exactly where it was. Expect only **partial recovery**. To minimize this risk: prefer small-scope iterations (few fields at a time), and keep the best-seen labellings around to re-submit if needed.

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
Invoice Details     | 0.450       | 0.820    | +0.370
Line Items          | 0.300       | 0.650    | +0.350
Bill-To-Party       | 0.900       | 0.900    | (unchanged)
Invoice Date        | 0.000       | 0.000    | (format issue — skipped)

Overall project score: X.XX → Y.YY
Rollbacks: N iterations were rolled back due to regression
Fields still below target: [list any with F1 < 0.7]
Format issues (not fixable by prompts): [list typed fields at F1 = 0]
```

If fields still need work, suggest the user run another round with more iterations.
If typed fields are at F1 = 0, advise fixing the labelling format and re-labelling.
