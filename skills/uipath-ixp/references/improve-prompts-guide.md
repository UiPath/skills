# Improve Prompts Guide

Iteratively improve extraction quality on an existing IXP project for up to the requested iterations (default 3), retraining and rolling back regressions.

## What Prompts CAN and CANNOT Fix

Prompts can fix wrong values (precision), missed values (recall, with location hints), and ambiguous candidate selection (disambiguation and closed vocabularies). They cannot fix OCR or create fields absent from documents: OCR-garbled predictions are NOT CONFIRMED, remain unannotated, and every such field must be reported as a data-quality issue without iterating on it.

## How prompt updates work

Run `uip ixp projects update-prompt <project> --prompt "<text>"` to overwrite the full project **Overall extraction instructions** seen for every field; always submit the full text. Run `uip ixp groups update-prompts <project> --updates-file <path>` for label_def/group instructions, matching by label_def name. Run `uip ixp fields update-prompts <project> --updates-file <path>` for field instructions, matching by field group name + field name and failing if either is absent. Group and field updates change only supplied entries and preserve the rest; run commands back-to-back for multiple levels. Store the full project prompt used in each iteration for rollback.

## Before Starting

Track baseline metrics and `ModelVersion`, the previous successful iteration's complete metrics and version, and previous successful per-field, group, and project instructions. A trained version can be reread with `--model-version <N>`; preserve its number. Use [What `get-metrics` returns](#what-get-metrics-returns-and-which-values-decide). Do not reread taxonomy or sample documents between iterations; reread only metrics after update + retrain. If the user reports web-UI taxonomy or document changes, refetch taxonomy and document list first.

## What `get-metrics` returns, and which values decide

| Value | Level | Role |
|---|---|---|
| `F1` | field, group | **Decision:** targeting (2a), regression and stopping (2f). |
| `Precision` | field, group | **Decision:** split low `F1` into PRECISION vs RECALL (2a), selecting the rewrite. |
| `Recall` | field, group | **Decision:** same split and `< 0.5` labelling-gap probe (2a-check). |
| `Annotations` | field | **Decision:** reviewed **extractions**, not documents; sample `F1` is computed over these and they set that field's regression threshold (2f). |
| `Documents` | field, group | **Decision:** reviewed documents for that field/group, not project total. `0` → SKIP (2a); below `ValidatedDocuments` means some reviewed documents have no label for that field (2f). |
| `ProjectScore` | project | **Report only:** average of per-field `F1`; never gate on it. |
| `ValidatedDocuments` | project | **Decision:** labelled documents used for metrics and ceiling for each per-field `Documents`. Below total document count means unlabelled documents exist; label them before looping (1e). |
| `ModelVersion` | project | **Decision:** retrain completion ([Waiting for retrain](#waiting-for-retrain)). |
| `ErrorRate` | field, group | **Report, independent of `Precision`:** wrong extractions over `Annotations`; a wrong value counts once, not as false positive + false miss, and a miss counts even though it cannot lower `Precision`. Thus `Precision` 1.00 may have `ErrorRate` 0.20. Report manual-correction burden; diagnose direction with `Precision`/`Recall`. |
| `Quality` | field | **Ignore:** coarse scale differs from `ProjectScoreQuality`; never gate or report per field. If asked about the UI label, explain the scales differ. |
| `ProjectScoreQuality` | project | Report only on the project line, beside the score; its scale differs from field `Quality`. |
| `FieldGroup`, `FieldId`, `Name` | field | Identity — SKILL.md Critical Rule 21. |

## Waiting for retrain

Every model-input change—labellings, instructions, document upload/delete, or taxonomy edit—triggers a full retrain. Never read metrics mid-retrain:

1. Record `ModelVersion` from the last metrics read **before** the change.
2. Wait 2 minutes, then run `uip ixp projects get-metrics <project-name> --output json`.
3. If `ModelVersion` is greater than the recorded value, proceed; any increment counts. Do not wait for a specific number because queued changes may skip versions.
4. Otherwise repeat step 2, with 2 minutes between checks and 5 checks total (10 minutes). Do not use one long sleep, escalate, shorten the interval, loop, or chain commands; issue one `uip` call per command because bundled checks time out.
5. If unchanged after check 5, stop polling and report incomplete retraining. Carried metrics predate the change: label them as pre-change, never present them as post-change, and never roll back against them.

A failed read consumes a check and does not restart the budget.

**No confirmed labellings yet** (a new project, before its first labelling): `get-metrics` stays `{ Metrics: null }` even after training finishes, so it cannot show completion. Run the same checks with `uip ixp projects list-models <project-name> --output json` instead: training is done once `Models[]` has a model whose `TrainedTime` is later than your change, whatever its `Version` number (even `0`).

## Step 1 — Setup (once, before the loop)

### 1a. Get baseline metrics

If recent labelling, upload, or taxonomy edits triggered retraining, apply [Waiting for retrain](#waiting-for-retrain) first.

```bash
mkdir -p /tmp/ixp/<project-name>/{docs,taxonomies,payloads}
uip ixp projects get-metrics <project-name> --model-version latest --output json
```

`--model-version latest` deliberately selects the latest trained version, not the `live` tag (Critical Rule 20: the version follows the question). Save its `ModelVersion`; later iterations require advancement after `fields update-prompts`, `groups update-prompts`, or `projects update-prompt` (2e). If it matches a known pre-labelling version, refetch under bounded wait and use the result.

Save the complete top-level `Fields` array as `baseline_metrics`. For a validated model, `Fields`/`FieldGroups`/`ValidatedDocuments` are top-level; an unvalidated model returns `Data: { Metrics: null }`, so refetch under bounded wait. Compare fields by `FieldId`, report by `Name`, and qualify shared names by `FieldGroup` — SKILL.md Critical Rule 21.

### 1b. Check model configuration

If many fields are low, inspect sample documents and determine whether configuration fits the document type (for example, table preprocessing for table-heavy documents). If not, run:

```bash
uip ixp projects configure-model <project-name> \
  --model gemini_2_5_flash \
  --preprocessing <none|table_mini|table> \
  --output json
```

See [Project Setup Guide](project-setup-guide.md) Step 2 for the decision table.

### 1c. Get taxonomy

```bash
uip ixp projects get-taxonomy <project-name> --output json
```

Save the raw snake_case response (`{ status, dataset: { entity_defs, label_groups } }`) to `/tmp/ixp/<project-name>/taxonomies/v1.json`; increment the version after each prompt update. `dataset.label_groups[]` contains `label_defs`, their fields, and current `instructions`. Pass the parent `label_def` name as `group` and field `name` as `name` to `fields update-prompts`.

### 1d. Read sample documents (2-3 documents)

```bash
uip ixp documents list <project-name> --output json

# For each sample document:
uip ixp documents download <project-name> <document-id> -o /tmp/ixp/<project-name>/docs/<document-id> --output json
```

`download` appends the server content-type extension; read the resolved `Path`. Use the **Read tool**, one full Read per document, with **no `pages` parameter** (PDF/PNG/JPG returns text + image natively). Check existing files before downloading; they persist across sessions.

### 1e. Check for unlabelled documents

Compare the document list with metrics. If `ValidatedDocuments` is below total document count, review and label unlabelled documents using [Label Documents Guide](label-documents-guide.md), then refetch metrics under [Waiting for retrain](#waiting-for-retrain) before looping.

## Step 2 — Optimization Loop

Repeat through the user's maximum iterations.

### 2a. Diagnose fields and field groups

Use baseline metrics on iteration 1 and post-relabel metrics thereafter. Inspect `FieldGroups` first: a low-F1 whole group may require `groups update-prompts`; then inspect `Fields`. Target every field with `F1 < 0.7`:

1. `Documents = 0` → **SKIP**; otherwise → **REFINE**.
2. Classify from `Precision`/`Recall`: `Precision < Recall` significantly → **PRECISION** (wrong values); `Recall < Precision` significantly → **RECALL** (misses); otherwise → **BOTH** (full rewrite).
3. Record `Annotations`; it does not alter classification but controls believable delta and threshold in 2f.

Print one row per field with name, `F1`, `Precision`, `Recall`, `ErrorRate`, `Annotations`, `Documents`, and diagnosis; include group rows and project line (`ProjectScore` / `ProjectScoreQuality` / `ValidatedDocuments` / `ModelVersion`). Ignore `Quality` labels as specified in [What `get-metrics` returns](#what-get-metrics-returns-and-which-values-decide). If no fields need REFINE, stop.

### 2a-check. Check for labelling gaps (before writing instructions)

For each REFINE field with `Recall < 0.5`, inspect existing sample images and determine whether its value is visible. If visible, predictions may have been correct but unconfirmed: refetch predictions and review those fields. If not visible, treat it as a prompt/recall issue. Confirm previously skipped correct predictions for the specific documents and fields with `labellings confirm --fields`, then refetch metrics under [Waiting for retrain](#waiting-for-retrain). If no gap exists, write instructions.

### 2b. Write improved instructions

Rewrite each REFINE field: **PRECISION** specifies WHAT; **RECALL** specifies WHERE; **BOTH** rewrites what and where. Instructions must:

- focus on what/where, not format (entity_def already handles format);
- be at least 120 characters (field instructions) and at most 4096 at every level — field, group, project (trim before submission; longer values are rejected and nothing saves);
- give a location (section, header, table, near a label; e.g. keywords "section", "header", "table", "top of", "labeled", "near");
- include an actual document value when visible (for example, `Example: '2106732'` or `Example: 'SINV0077023'`); for fields not visible, use a generic instruction with no example: "Extract [what] from this document, as it appears on the page.";
- identify the target by label, role, and location; do not name an incorrect candidate or write "Do NOT return [value]";
- use a closed vocabulary only when the complete set is explicit in taxonomy, business rules, or an authoritative reference; never infer it from samples;
- contain no format patterns such as "Format: MM/DD/YYYY"; and
- target one field only.

**Good instruction** (145 chars):
> "The unique invoice identifier, found in the header area near the top-right, labeled 'Invoice #' or 'Invoice Number'. Example: '2106732'."

**Bad instruction** (25 chars):
> "Extract the invoice number"

For visible fields include location and a real document example. Never reference specific page numbers; use headings or labels. On iteration 2+, do not repeat the failed instruction; change wording, location hints, or vocabulary. Keep project, group, and field prompts consistent: if a project/group rule contradicts a field, update the conflicting level too. Rules not true for every covered field belong at field or group level.

### 2c. Update instructions

Use the exact parent field-group name and field name in field objects, and label_def/group name in group objects:

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

Group and project commands are optional; skip each level needing no change. Save the full project prompt with each iteration's prompt files. Rollback must resubmit the prior saved prompt.

After updating, refetch and save taxonomy, then verify unchanged field counts per label_def:

```bash
uip ixp projects get-taxonomy <project-name> --output json > /tmp/ixp/<project-name>/taxonomies/v<N>.json
```

If any updated label_def loses fields, **STOP immediately** and report taxonomy corruption for manual restoration; the previous taxonomy version preserves old instructions for rollback.

### 2d. Review and confirm predictions for all documents

Apply [Label Documents Guide](label-documents-guide.md) after waiting for instruction-triggered retraining under [Waiting for retrain](#waiting-for-retrain). Review every document against actual content and confirm correct predictions; skip incorrect predictions so old labels remain.

### 2e. Wait and get new metrics

Wait for labelling-triggered retraining under [Waiting for retrain](#waiting-for-retrain), then run:

```bash
uip ixp projects get-metrics <project-name> --model-version latest --output json
```

If `ModelVersion` has not advanced, reread under the same bounded budget. When it expires, record available metrics and proceed to 2f; do not stall for a version bump.

### 2f. Compare and decide

Compare complete new metrics with the previous iteration for touched fields and the whole project.

#### Regression noise floor

With few `Annotations`, `F1` moves in jumps: one annotation flipping by chance looks like a worse instruction. For every field:

```text
regression_threshold = max(0.1, 1 / Annotations)
```

Thus `Annotations = 5` gives 0.2 and `Annotations = 10` gives 0.1. Different annotation counts intentionally have different thresholds. A sub-threshold change is **not measurable yet**, neither an improvement nor "no change." Repeated sub-threshold movement with few annotations cannot evaluate a rewrite; report the remedy based on sample cause.

`Annotations` counts reviewed **extractions**, not documents; one document may contribute several, so do not compare it directly to document count. Compare field `Documents` with project `ValidatedDocuments`:

- equal → tag final report **UPLOAD** (field has evidence on every labelled document; sample is data-limited);
- below → tag **REVIEW** (some labelled documents have no field evidence, either unreviewed or skipped; use [Label Documents Guide](label-documents-guide.md) to identify them). The `Recall < 0.5` gate does not replace this review.

UPLOAD and REVIEW are final-report tags, not loop actions: continue normally — never pause mid-run to ask for documents or to review — and report that the tagged field cannot improve until its sample grows. `Annotations / Documents` is average extractions per document (about 1 for a single-value field, higher for a repeatable group).

For each field updated this iteration, compare its F1 drop with its own threshold. Roll back only fields dropping **greater than** threshold; keep improved/unchanged fields:

```bash
# Only include the regressed fields, not the whole iteration
cat > /tmp/ixp/<project-name>/payloads/rollback.json << 'FIELDS_EOF'
[{"group": "Invoice", "name": "Vendor Address", "instructions": "previous instruction for this field only"}]
FIELDS_EOF

uip ixp fields update-prompts <project-name> \
  --updates-file /tmp/ixp/<project-name>/payloads/rollback.json \
  --output json
```

Also diff every field, not `ProjectScore`: it is the unweighted mean of field `F1` and can hide regressions. Group edits affect all fields in that label_def; project edits affect all fields. For each unedited field beyond its own threshold, report name and delta. Roll it back only when it shares a field group with a `groups update-prompts` edit you made this iteration, or when you edited the project prompt this iteration (roll back the project prompt); otherwise keep the iteration and recheck next round, since two reads cannot prove causation. Wait for rollback retraining under [Waiting for retrain](#waiting-for-retrain), then on the next iteration use a different approach for regressed fields only (different wording, shorter instruction, fewer examples). Rollback retraining may provide only partial recovery; prefer small-scope iterations.

If no regression, accept the iteration and replace `previous_metrics` with the complete output and `previous_instructions` with new values. Stop when all fields meet the user target F1 (default 0.7), max iterations are reached, or no field improves by more than its own threshold for 2 consecutive iterations. A run of sub-threshold moves is not progress.

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

`ErrorRate` is remaining manual-correction burden; `Annotations` distinguishes a real plateau from an unmeasurable one. If fields need more work, suggest another round with more iterations. For every too-few-`Annotations` field, state that its score cannot rise until its sample grows and identify the remedy: **UPLOAD** (more documents) or **REVIEW** (documents where it carries no label).
