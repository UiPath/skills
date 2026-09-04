# Improve Prompts Guide

Iteratively improve extraction quality on an existing IXP project for up to the requested iterations (default: 3). Retrain after changes and roll back regressions.

## What Prompts CAN and CANNOT Fix

Prompts can fix wrong values (precision), missed values (recall), and ambiguous candidate selection through clearer instructions, location hints, negative examples, and disambiguation.

Prompts and reviewing cannot fix:

- **OCR quality issues** — if OCR consistently garbles a field, correct OCR-mangled predictions during review with `labelling confirm --corrections` (keeps the reference, fixes the text). If many fields across documents are affected, report a data-quality issue instead of using iterations.
- **Missing fields** — instructions cannot create a value absent from documents.

## How Prompt Updates Work

Run these separate commands:

- `uip ixp fields update-prompts <project> --updates <json>` — per-field instructions matched by field name.
- `uip ixp groups update-prompts <project> --updates <json>` — label_def/group instructions matched by label_def name.

Each command makes one server-side call and preserves definitions omitted from the update. Run both back-to-back when changing fields and groups. Keep group and field instructions consistent: each label_def has its own `instructions` shown alongside field instructions. If they conflict, update the parent group with `groups update-prompts` too.

## Before Starting

Track baseline metrics and `ModelVersion` from `get-metrics`, previous-iteration metrics and `ModelVersion`, and previous instructions for rollback.

A trained version's metrics can be reread with `--model-version <N>`; retaining the version is sufficient. Do NOT reread taxonomy or sample documents between iterations. Reread only metrics after each update/retrain cycle. If the user reports web-UI changes, refetch taxonomy and document list before continuing.

## What `get-metrics` Returns and Which Values Decide

| Value | Level | Role |
|---|---|---|
| `F1` | field, group | Decision variable for targeting (2a), regression, and stopping (2f). |
| `Precision` | field, group | Decision variable for precision/recall diagnosis (2a). |
| `Recall` | field, group | Decision variable for diagnosis and the `< 0.5` labelling-gap probe (2a-check). |
| `Annotations` | field | Reviewed **extractions**, not documents; sets that field's regression threshold (2f). |
| `Documents` | field, group | Reviewed documents for that field/group, not project total. `0` → SKIP (2a). Below `ValidatedDocuments` → some reviewed documents carry no label for the field (2f). |
| `ProjectScore` | project | Report only. Averages per-field `F1`; never gate on it. |
| `ValidatedDocuments` | project | Decision variable: labelled documents used for metrics and the ceiling for per-field `Documents`. If below total document count, unlabelled documents exist (1e). |
| `ModelVersion` | project | Decision variable for retrain completion. |
| `ErrorRate` | field, group | Report only and independent of `Precision`: wrong extractions count once, and misses count even when they do not lower `Precision`. Report manual-correction burden; diagnose direction with `Precision`/`Recall`. |
| `Quality` | field | Ignore. It is a coarse scale inconsistent with `ProjectScoreQuality`; never gate or report it per field. If asked, explain that the scales differ. |
| `ProjectScoreQuality` | project | Report only on the project line, using the UI's project label. |
| `FieldGroup`, `FieldId`, `Name` | field | Identity. Compare on `FieldId` (stable); report on `Name` (current display name — `null` for a deleted field, fall back to `FieldId`; see 1a). |

## Waiting for Retrain

Every input change—labellings, instructions, document upload/delete, or taxonomy edits—triggers a full retrain. Never compare metrics read mid-retrain.

1. Record `ModelVersion` from the last metrics read **before** the change.
2. Wait 2 minutes, then run `uip ixp projects get-metrics <project-name> --output json`.
3. If `ModelVersion` is greater than the recorded value, proceed. Any increment counts; queued changes can skip versions.
4. Otherwise repeat step 2 with 2 minutes between checks, for 5 checks total (10 minutes). Do not use one long sleep, shorten the interval, or escalate.
5. If unchanged after the fifth check, stop polling and report that retraining did not complete. Mark carried-forward metrics as pre-change; never present them as post-change or roll back against them.

A failed read counts against the five-check budget and does not restart it.

## Step 1 — Setup (once)

### 1a. Get Baseline Metrics

If documents were labelled, uploaded, or the taxonomy was edited, wait using [Waiting for retrain](#waiting-for-retrain), then run:

```bash
mkdir -p /tmp/ixp/<project-name>/{docs,text,taxonomies,prompts}
uip ixp projects get-metrics <project-name> --model-version latest --output json
```

Use `--model-version latest`, not `live`: the baseline must be the latest trained version that instruction edits retrain (Critical Rule 21: the version follows the question). Record `ModelVersion` and save the complete per-field `Fields` array as `baseline_metrics`. If the result is unvalidated (`Data: { Metrics: null }`), refetch under the bounded wait. If it resembles a known pre-labelling version, refetch under the bounded wait and use the returned result.

**Field names:** each `Fields` entry carries both `FieldId` and `Name`, so report and compare straight from the metrics — do NOT fetch the taxonomy to build an id→name map. Three rules:

- **Compare on `FieldId`, report on `Name`.** `FieldId` is stable; `Name` reflects the current taxonomy, so a field renamed since an older version was scored reads back under its current name.
- **`Name` is `null`** when the service could not resolve it (e.g. the field was deleted after that version was scored). Fall back to `FieldId`; never skip the field.
- **When two fields share a `Name`, qualify it as `<FieldGroup> / <Name>`.** Display names are unique only within a group. This changes only how you print the row — the comparison still keys on `FieldId`.

### 1b. Check Model Configuration

If many fields score poorly, inspect sample documents and verify configuration, especially table preprocessing. If wrong, run:

```bash
uip ixp projects configure-model <project-name> \
  --model gemini_2_5_flash \
  --preprocessing <none|table_mini|table> \
  --output json
```

Use the decision table in [Project Setup Guide](project-setup-guide.md) Step 2.

### 1c. Get Taxonomy

Run:

```bash
uip ixp projects get-taxonomy <project-name> --output json
```

Save the raw snake_case response (`{ status, dataset: { entity_defs, label_groups } }`) to `/tmp/ixp/<project-name>/taxonomies/v1.json`. Each `dataset.label_groups[]` contains `label_defs`, fields, and current `instructions`. Increment the taxonomy version after each prompt update. Pass the field `name` to `fields update-prompts`.

### 1d. Read Sample Documents

Read 2–3 documents. Run:

```bash
uip ixp documents list <project-name> --output json

# For each sample document:
uip ixp documents download <project-name> <document-id> -o /tmp/ixp/<project-name>/docs/sample --output json
```

The download command detects format and appends the extension. Read the resolved `Path`; use the Read tool once per document, with no `pages` parameter, so PDF/PNG/JPG text and image are returned natively. Reuse existing files.

### 1e. Check for Unlabelled Documents

Compare the document list with metrics. If `ValidatedDocuments` is below the total document count, label unlabelled documents first using [Label Documents Guide](label-documents-guide.md), then wait and refetch metrics under [Waiting for retrain](#waiting-for-retrain).

## Step 2 — Optimization Loop

Repeat through the maximum iteration count.

### 2a. Diagnose Fields and Groups

Use baseline metrics on iteration 1 and post-relabel metrics thereafter. Check `FieldGroups` first; a low-scoring group may require `--groups`. Target fields with `F1 < 0.7`:

1. `Documents = 0` AND `F1 = 0` → **SKIP**.
2. `Documents < 1` → **SKIP**.
3. Otherwise → **REFINE**.
4. For REFINE fields, classify the `Precision`/`Recall` split:
   - `Precision < Recall` significantly → **PRECISION** (wrong values).
   - `Recall < Precision` significantly → **RECALL** (misses).
   - Otherwise → **BOTH** (full rewrite).
5. Record `Annotations`; it does not alter diagnosis but sets the field's regression threshold in 2f.

Print one row per field with name, `F1`, `Precision`, `Recall`, `ErrorRate`, `Annotations`, `Documents`, and diagnosis; include group rows and the project line (`ProjectScore` / `ProjectScoreQuality` / `ValidatedDocuments` / `ModelVersion`). Ignore field `Quality`. Stop if no fields need REFINE.

### 2a-check. Check Labelling Gaps

For every REFINE field with `Recall < 0.5`, inspect already-downloaded sample images and determine whether the value is visible. If visible, refetch predictions and review the field; a correct prediction may previously have been skipped. If not visible, treat it as a prompt/recall issue.

If skipped predictions are correct, confirm only those documents and fields with `labelling confirm --fields`, then wait and refetch metrics under [Waiting for retrain](#waiting-for-retrain) before writing instructions. If no gap exists, write instructions directly.

### 2b. Write Improved Instructions

Rewrite each REFINE field:

- **PRECISION**: specify what to extract and what not to extract.
- **RECALL**: describe where to find it.
- **BOTH**: rewrite what, where, and what to avoid.

Requirements:

- Focus on what and where; do not specify format because the entity_def type handles it.
- Use at least 120 characters.
- Include a location hint: section, header, table, top of, labeled, or near.
- Include a real document value when visible; use no example when not visible. For example: `Example: '2106732'`.
- Disambiguate similar fields, including what NOT to extract.
- Do NOT include format patterns such as `Format: MM/DD/YYYY`.
- Reference one field only.
- NEVER reference page numbers; use headings or labels.
- From iteration 2 onward, do not repeat a failed instruction; change wording, location hints, length, or negative examples.

### 2c. Update Instructions

Use field names with `--fields` and label_def names with `--groups`. Run:

```bash
cat > /tmp/ixp/<project-name>/prompts/field_updates.json << 'FIELDS_EOF'
[
  {"name": "Invoice Number", "instructions": "The unique document identifier, found in the header area top-right. Example: 2106732, QC006."},
  {"name": "Invoice Date", "instructions": "The date the invoice was issued. Found near the invoice number."}
]
FIELDS_EOF

uip ixp fields update-prompts <project-name> \
  --updates "$(cat /tmp/ixp/<project-name>/prompts/field_updates.json)" \
  --output json
```

If group instructions also need changing, run:

```bash
cat > /tmp/ixp/<project-name>/prompts/group_updates.json << 'GROUPS_EOF'
[
  {"name": "Invoice", "instructions": "General invoice header fields including number, dates, payment terms, and totals."}
]
GROUPS_EOF

uip ixp groups update-prompts <project-name> \
  --updates "$(cat /tmp/ixp/<project-name>/prompts/group_updates.json)" \
  --output json
```

After updating, wait as required, then run:

```bash
uip ixp projects get-taxonomy <project-name> --output json > /tmp/ixp/<project-name>/taxonomies/v<N>.json
```

Verify field counts in every updated label_def are unchanged from the previous version. If any field is missing, STOP immediately, report taxonomy corruption, and restore manually using the previous taxonomy version.

### 2d. Review and Confirm All Documents

Wait for the instruction-triggered retrain using [Waiting for retrain](#waiting-for-retrain). Review every document's predictions against its content using [Label Documents Guide](label-documents-guide.md), confirming correct predictions and skipping incorrect ones so old labels remain.

### 2e. Wait and Get Metrics

Wait for the labelling-triggered retrain using [Waiting for retrain](#waiting-for-retrain), then run:

```bash
uip ixp projects get-metrics <project-name> --output json
```

If `ModelVersion` has not advanced, continue under the same bounded budget. If the budget expires, record available metrics and proceed to 2f; do not stall.

### 2f. Compare and Decide

Compare the complete new payload with the previous iteration at touched-field and project-wide levels.

#### Regression Noise Floor

For each field:

```text
regression_threshold = max(0.1, 1 / Annotations)
```

A single annotation can move `F1` sharply. A move below the field's threshold is **not measurable**, not an improvement. If sub-threshold drift continues, report the appropriate remedy based on sample size.

`Annotations` counts reviewed extractions, not documents. Compare the field's `Documents` with project-level `ValidatedDocuments`:

- Equal → tag **UPLOAD**: evidence covers every labelled document, so the sample can grow only with more documents.
- Below → tag **REVIEW**: some labelled documents have no label for this field. Review them using [Label Documents Guide](label-documents-guide.md), whether or not new labels are found.

These are final-report tags, not loop actions. Continue normally and report that the score cannot rise until its sample grows. `Annotations / Documents` is the average extractions per document.

#### Selective Regression and Collateral Checks

For each field updated this iteration, compare its `F1` drop with its own threshold:

- Drop greater than threshold → roll back only that field.
- Improved or within threshold → keep it.

Diff every field, not `ProjectScore`, against its own threshold. For an unedited field that regresses beyond threshold, report its name and delta. Roll it back only if it shares a field group changed by `groups update-prompts` this iteration; otherwise keep the iteration and recheck next round because two reads cannot prove causation.

For selective rollback, run:

```bash
cat > /tmp/ixp/<project-name>/prompts/rollback.json << 'FIELDS_EOF'
[{"name": "Vendor Address", "instructions": "previous instruction for this field only"}]
FIELDS_EOF

uip ixp fields update-prompts <project-name> \
  --updates "$(cat /tmp/ixp/<project-name>/prompts/rollback.json)" \
  --output json
```

Wait for retrain. On the next iteration, use a different approach for regressed fields only. Rollback restores instructions, but retraining may yield only partial recovery; prefer small-scope iterations.

If no regression occurs, accept the iteration and update `previous_metrics` with the complete payload and `previous_instructions` with the new values.

Stop when:

- All fields meet the user's target F1 (default: 0.7).
- The maximum iteration count is reached.
- No field improves by more than its own `regression_threshold` for 2 consecutive iterations.

## Step 3 — Final Report

Print:

```text
Optimization complete after N iterations. Model version V1 -> V2.

Field           | Base F1 | Final F1 | Change    | Prec  | Rec   | Err   | Ann
----------------|---------|----------|-----------|-------|-------|-------|----
Invoice Number  | 0.450   | 0.820    | +0.370    | 0.850 | 0.790 | 0.200 |  40
Description     | 0.300   | 0.650    | +0.350    | 0.700 | 0.610 | 0.395 |  38
Bill-To Name    | 0.900   | 0.900    | unchanged | 0.900 | 0.900 | 0.100 |  40
Vendor Address  | 0.600   | 0.400    | -0.200 (rolled back) | 0.410 | 0.390 | 0.600 | 40
Freight Charge  | 1.000   | 0.889    | -0.111 (under its threshold, kept) | 1.000 | 0.800 | 0.200 | 5

Project score:   X.XX (Quality) -> Y.YY (Quality)   ValidatedDocuments: D
Iterations: N total, M with rollbacks
Fields still below target (F1 < 0.7): [list]
Fields whose regression_threshold sits above the flat 0.1 (too few Annotations to measure progress): [list, each tagged UPLOAD or REVIEW]
Labelling gaps fixed: [list any fields re-labelled in 2a-check]
```

Report `ErrorRate` as remaining manual-correction burden and `Annotations` as evidence of whether a plateau is measurable. If fields remain below target, suggest another round with more iterations. For each too-few-`Annotations` field, state that its score cannot rise until its sample grows and identify **UPLOAD** or **REVIEW** as the remedy.
