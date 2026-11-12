# Improve Prompts Guide

Iteratively improve extraction quality in an existing IXP project: run iterations, measure, and roll back regressions.

## What Prompts CAN and CANNOT Fix

Prompts can fix wrong values (precision), missed values through location hints (recall), and ambiguous candidate selection (disambiguation and closed vocabularies). Prompts and review cannot fix OCR-garbled text or absent fields. OCR-garbled predictions are **NOT CONFIRMED**, remain unannotated, and must all be reported as data-quality issues, even one; do not iterate on them. Missing fields cannot be conjured.

## How prompt updates work

- Run `uip ixp projects update-prompt <project> --prompt "<text>"` for overall instructions seen by every field; it overwrites the entire project prompt, so submit the full text.
- Run `uip ixp groups update-prompts <project> --updates-file <path>` for field-group (`label_def`) instructions matched by `label_def` name.
- Run `uip ixp fields update-prompts <project> --updates-file <path>` for field instructions matched by field-group name plus field name; it fails if either combination is absent.

Group and field updates modify only supplied entries and preserve the rest. Run commands back-to-back to update multiple levels in one iteration.

## Before Starting

The user may set max iterations (default `3`). Track baseline metrics and `ModelVersion`, previous successful-iteration metrics, and previous successful per-field, group, and project instructions. A trained version can be reread with `--model-version <N>`; retaining the version is sufficient for recovery.

Do not reread taxonomy or sample documents between iterations; reread metrics only after each update/retrain cycle, assuming no external taxonomy/document changes. If the user reports web-UI changes, refetch taxonomy and document list before continuing.

## What `get-metrics` returns, and which values decide

Use values exactly as follows:

| Value | Level | Use |
|---|---|---|
| `F1` | field, group | **Decision variable.** Targeting (2a), regression, and stopping (2f). |
| `Precision` | field, group | **Decision variable.** With `Recall`, selects PRECISION vs RECALL rewrite (2a). |
| `Recall` | field, group | **Decision variable.** Same split; also triggers the `< 0.5` labelling-gap probe (2a-check). |
| `Annotations` | field | **Decision variable.** Reviewed **extractions**, not documents; sets that field's regression threshold (2f). |
| `Documents` | field, group | **Decision variable.** Reviewed documents for that field/group, not project total. `0` means SKIP (2a). Below `ValidatedDocuments` means some reviewed documents have no label for the field (2f). |
| `ProjectScore` | project | Report only; average of per-field `F1`; never gate on it. |
| `ValidatedDocuments` | project | **Decision variable.** Labelled documents used for metrics and ceiling for per-field `Documents`. Below total document count means unlabelled documents exist; label them before looping (1e). |
| `ModelVersion` | project | **Decision variable.** Retrain completion ([Waiting for retrain](#waiting-for-retrain)). |
| `ErrorRate` | field, group | Report independently of `Precision`: wrong extractions over `Annotations`, counted once; misses count even though they do not lower `Precision`. Thus `Precision` 1.00 can have `ErrorRate` 0.20. Report manual-correction burden and diagnose direction from precision/recall. |
| `Quality` | field | Ignore; its coarse scale differs from `ProjectScoreQuality` (an `F1` of 1.00 still reads `good` while a `ProjectScore` of 0.91 reads `excellent`). Never gate or report it per field; explain differing UI scales if asked. |
| `ProjectScoreQuality` | project | Report only on the project line; it is the UI label beside the project score and uses a different scale from field `Quality`. |
| `FieldGroup`, `FieldId`, `Name` | field | Identity — SKILL.md Critical Rule 21. |

## Waiting for retrain

Every model-input change (labellings, instructions, document upload/delete, taxonomy edits) triggers full retraining. Never read metrics mid-retrain.

**Bounded wait. Poll on a fixed interval; never poll indefinitely:**

1. Record `ModelVersion` from the last metrics read before the change.
2. Wait 2 minutes, then run `uip ixp projects get-metrics <project-name> --output json`.
3. If `ModelVersion` is greater than the recorded value, proceed. Any increment counts; do not wait for exactly `N`+1 because queued changes may skip versions.
4. Otherwise repeat step 2, with 2 minutes between checks and 5 checks total (10 minutes). Do not use one long sleep, escalate, shorten the interval, loop, or chain commands; issue one `uip` call per command because bundled checks time out.
5. If unchanged after check 5, stop polling and report incomplete retraining. Carry metrics as pre-change, label them as such, never present them as post-change, and never roll back instructions based on them.

A failed read consumes a check and never restarts the budget.

## Step 1 — Setup (once, before the loop)

### 1a. Get baseline metrics

If documents were labelled, uploaded, or taxonomy-edited, wait using [Waiting for retrain](#waiting-for-retrain), then run:

```bash
mkdir -p /tmp/ixp/<project-name>/{docs,taxonomies,payloads}
uip ixp projects get-metrics <project-name> --model-version latest --output json
```

`--model-version latest` is deliberate: use the latest trained version, not the `live` tag (Critical Rule 20: the version follows the question). Record `ModelVersion`; if it matches a known pre-labelling version, the retrain may still be in flight; refetch under the bounded wait, then proceed with whatever it returns. Save the complete top-level `Fields` array as `baseline_metrics`.

Validated output is flat (`Fields`/`FieldGroups`/`ValidatedDocuments` top-level); an unvalidated model returns `Data: { Metrics: null }`, so refetch under the bounded wait. Compare fields by `FieldId`, report by `Name`, and qualify shared names with `FieldGroup` — SKILL.md Critical Rule 21.

### 1b. Check model configuration

If many fields score poorly, inspect sample documents and verify configuration, including table preprocessing for table-heavy documents. If wrong, run:

```bash
uip ixp projects configure-model <project-name> \
  --model gemini_2_5_flash \
  --preprocessing <none|table_mini|table> \
  --output json
```

See the [Project Setup Guide](project-setup-guide.md) Step 2 decision table.

### 1c. Get taxonomy

```bash
uip ixp projects get-taxonomy <project-name> --output json
```

Save the raw-snake-case response `{ status, dataset: { entity_defs, label_groups } }` to `/tmp/ixp/<project-name>/taxonomies/v1.json`. `dataset.label_groups[]` contains `label_defs`, fields, and current `instructions`; iterate field instructions and increment versions after updates (`v2`, `v3`, …). Pass parent `label_def.name` as `group` and field `name` as `name` in field updates.

### 1d. Read sample documents (2-3 documents)

```bash
uip ixp documents list <project-name> --output json

# For each sample document:
uip ixp documents download <project-name> <document-id> -o /tmp/ixp/<project-name>/docs/<document-id> --output json
```

`download` appends the server content-type extension; read the resolved response `Path`. Use the **Read tool**, one full Read per document, with **no `pages` parameter** (PDF/PNG/JPG returns text and image natively). Check for existing files before downloading; files persist across sessions.

### 1e. Check for unlabelled documents

Compare the document list with metrics. If `ValidatedDocuments` is below total documents, review and label unlabelled documents using the [Label Documents Guide](label-documents-guide.md), then refetch metrics under [Waiting for retrain](#waiting-for-retrain) before looping.

## Step 2 — Optimization Loop

Run each iteration up to the maximum.

### 2a. Diagnose fields and field groups

Use baseline metrics on iteration 1 and post-relabel metrics thereafter. Inspect `FieldGroups` first: a low group score may require `groups update-prompts` rather than individual fixes. Target each field with `F1 < 0.7`:

1. `Documents = 0` → **SKIP**; otherwise → **REFINE**.
2. Split precision and recall: `Precision < Recall` significantly → **PRECISION**; `Recall < Precision` significantly → **RECALL**; otherwise → **BOTH**. `F1` measures severity; the split selects the rewrite.
3. Record `Annotations`; it does not change classification but determines measurable delta in 2f.

Print one row per field containing name, `F1`, `Precision`, `Recall`, `ErrorRate`, `Annotations`, `Documents`, and diagnosis; include group rows and project `ProjectScore` / `ProjectScoreQuality` / `ValidatedDocuments` / `ModelVersion`. Ignore field `Quality`. If no field needs REFINE, stop.

### 2a-check. Check for labelling gaps (before writing instructions)

For every REFINE field with `Recall < 0.5`, inspect Step 1d images and determine whether the value is visible. If visible, refetch predictions and review again because a prior correct prediction may not have been confirmed. If genuinely absent, treat it as prompt/recall work.

If skipped predictions are correct, confirm only those documents/fields with `labellings confirm --fields`, then refetch metrics under [Waiting for retrain](#waiting-for-retrain). If no gaps exist, write instructions.

### 2b. Write improved instructions

Rewrite every REFINE field:

- **PRECISION:** specify more precisely what to extract.
- **RECALL:** describe where to find it.
- **BOTH:** rewrite what and where.

Focus on what and where; the entity_def supplies format. Field instructions: 120+ characters (short ones like "Extract the date" are too vague). Every level (field, field group, overall project prompt): at most 4096 characters; trim before submission because longer values are rejected and nothing is saved. Include a document location (section, header, table, top, label, or nearby text) and, for visible fields, an actual document value (e.g., "Example: '2106732'", "Example: 'SINV0077023'"). For invisible fields, use a generic instruction with no example: `Extract [what] from this document, as it appears on the page.`

**Good instruction** (145 chars):
> "The unique invoice identifier, found in the header area near the top-right, labeled 'Invoice #' or 'Invoice Number'. Example: '2106732'."

**Bad instruction** (25 chars):
> "Extract the invoice number"

Identify the target by label, role, and location; do not name an incorrect candidate or write `Do NOT return [value]`. Use a closed vocabulary only when its complete set is explicit in taxonomy, business rules, or an authoritative reference; never infer it from samples. Do not specify format patterns such as `Format: MM/DD/YYYY`; Date, Monetary, and Text entity types already define format.

Keep project, group, and field prompts consistent. If the project or a group prompt says "Extract only values on the first page", but a per-field instruction says "Found in the summary table on page 2", the model gets contradictory signals — also update the parent group instruction with `groups update-prompts` and the project prompt with `projects update-prompt` if either contradicts; a rule not true for every covered field belongs at field or group level. Each instruction addresses one field. Never reference specific page numbers; use headings or labels. From iteration 2 onward, do not repeat the same failed instruction; use different wording, location hints, vocabulary, or examples.

### 2c. Update instructions

Use the parent field-group name and exact field name in field objects, and `label_def`/group name in group objects:

```bash
cat > /tmp/ixp/<project-name>/payloads/field_updates.json << 'FIELDS_EOF'
[
  {"group": "Invoice", "name": "Invoice Number", "instructions": "The unique document identifier, found in the header area top-right. Example: 2106732, QC006."},
  {"group": "Invoice", "name": "Invoice Date", "instructions": "The date the invoice was issued. Found near the invoice number."}
]
FIELDS_EOF

uip ixp fields update-prompts <project-name> \
  --updates-file /tmp/ixp/<project-name>/payloads/field_updates.json \
  --output json

# If group instructions also need updating, run a second command.
cat > /tmp/ixp/<project-name>/payloads/group_updates.json << 'GROUPS_EOF'
[
  {"name": "Invoice", "instructions": "General invoice header fields including number, dates, payment terms, and totals."}
]
GROUPS_EOF

uip ixp groups update-prompts <project-name> \
  --updates-file /tmp/ixp/<project-name>/payloads/group_updates.json \
  --output json

# Only if the project prompt needs changing
uip ixp projects update-prompt <project-name> --prompt "<FULL_PROMPT_TEXT>" --output json
```

Group/project calls are optional; skip each unnecessary level. Save the full project prompt for each iteration; rollback must resubmit the previous saved prompt.

After updating, refetch and version the taxonomy, verifying field counts per updated `label_def`:

```bash
uip ixp projects get-taxonomy <project-name> --output json > /tmp/ixp/<project-name>/taxonomies/v<N>.json
```

If any updated `label_def` loses fields, **STOP immediately** and report corruption for manual restoration. The previous taxonomy version has the old instructions for rollback.

### 2d. Review and confirm predictions for all documents

Wait for the instruction-triggered retrain using [Waiting for retrain](#waiting-for-retrain). Using the [Label Documents Guide](label-documents-guide.md), review every document against actual content and confirm correct predictions. Skip incorrect predictions; old labels remain.

### 2e. Wait and get new metrics

Wait for the labelling-triggered retrain using [Waiting for retrain](#waiting-for-retrain), then run:

```bash
uip ixp projects get-metrics <project-name> --model-version latest --output json
```

If `ModelVersion` has not advanced, reread under that same bounded budget. When it expires, record available metrics and continue to 2f; do not stall for a version bump.

### 2f. Compare and decide

Compare complete new output with the previous iteration for touched fields and the whole project. For each field:

```text
regression_threshold = max(0.1, 1 / Annotations)
```

A field with 5 annotations therefore has threshold 0.2; thresholds are flat 0.1 from 10 annotations upward. Use each field's own threshold. A move below threshold is **not measurable**, not “no change”. Do not report a sub-threshold move as an improvement either; repeated sub-threshold movement with few annotations cannot evaluate a rewrite.

`Annotations` counts reviewed extractions, not documents (one document may contribute several); `Annotations / Documents` is average extractions per document. Compare field `Documents` with project `ValidatedDocuments`:

- Equal → tag final report **UPLOAD**: evidence covers every labelled document and the sample cannot grow without more documents.
- Below → tag **REVIEW**: some labelled documents lack field evidence; the [Label Documents Guide](label-documents-guide.md) identifies whether they were unreviewed or skipped. This is a report tag, not a loop action.

Continue normally; do not pause to request documents or review. State that the tagged field cannot rise until its sample grows and report the remedy.

For every field updated this iteration, roll back only fields whose `F1` drop exceeds their own threshold; keep improved or unchanged fields. Diff every untouched field too: group edits affect every field in that group and project edits affect every project field. An untouched field beyond its threshold is collateral damage. Report its name and delta; roll back only when it shares a field group with a `groups update-prompts` edit made this iteration (roll back that group edit), or when the project prompt was edited this iteration (roll back the project prompt). Otherwise keep the iteration and recheck next round because two reads cannot establish causation.

Do not gate on `ProjectScore`; it is the unweighted mean of field `F1` and can hide a field regression.

If fields regressed, selectively roll back:

```bash
# Only include the regressed fields, not the whole iteration
cat > /tmp/ixp/<project-name>/payloads/rollback.json << 'FIELDS_EOF'
[{"group": "Invoice", "name": "Vendor Address", "instructions": "previous instruction for this field only"}]
FIELDS_EOF

uip ixp fields update-prompts <project-name> \
  --updates-file /tmp/ixp/<project-name>/payloads/rollback.json \
  --output json
```

Wait for retraining. On the next iteration use a different approach for regressed fields only (different wording, shorter instruction, or fewer examples). Rollback restores instructions but requires retraining and may recover only partially; prefer small-scope iterations.

With no regression, accept the iteration and replace `previous_metrics` with the complete output and `previous_instructions` with new values.

Stop when all fields meet the user's target F1 (default `0.7`), max iterations is reached, or no field improves by more than its own threshold for 2 consecutive iterations.

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

`ErrorRate` is remaining manual-correction burden; `Annotations` distinguishes a real plateau from an unmeasurable one. If fields remain below target, suggest another round with more iterations. For every too-few-`Annotations` field, state that its score cannot rise until the sample grows and identify **UPLOAD** (more documents) or **REVIEW** (documents where it has no label).