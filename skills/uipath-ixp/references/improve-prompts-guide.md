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

- **Baseline metrics** — the **complete** `get-metrics` payload before any changes: the whole `Fields[]` array (all nine values per field, not just `F1`), the whole `FieldGroups[]` array, and the project block (`ProjectScore`, `ProjectScoreQuality`, `ValidatedDocuments`, `ModelVersion`). Store the response verbatim — every field below drives a decision or a report line, and re-fetching a discarded one costs a retrain wait.
- **Previous iteration metrics** — the same complete payload from the last successful iteration
- **Previous instructions** — the per-field (field) instructions from the last successful iteration (for rollback)

Do NOT re-read the taxonomy or sample documents between iterations — use what you already have. Only re-read metrics after each instruction update + retrain cycle. This assumes no one modifies the taxonomy or documents externally during the loop. If the user mentions changes were made in the web UI, re-fetch the taxonomy and document list before continuing.

## What `get-metrics` returns, and which values decide

`get-metrics` returns nine values per field, six per group, and four project-level. They are not independent, and they are not interchangeable — using the wrong one silently changes the loop's behaviour.

| Value | Level | Role in this loop |
|-------|-------|-------------------|
| `F1` | field, group | **Decision variable.** Targeting (2a), regression (2f), stopping (2f). |
| `Precision` | field, group | **Decision variable.** Splits a low `F1` into PRECISION vs RECALL (2a) — that split picks which rewrite to attempt. |
| `Recall` | field, group | **Decision variable.** Same split, plus the `< 0.5` labelling-gap probe (2a-check). |
| `Annotations` | field | **Decision variable.** Sample size behind that field's `F1` — sets the noise floor for the regression check (2f). |
| `Documents` | field, group | **Decision variable.** `0` → SKIP (2a): no evidence, so no instruction rewrite can be evaluated. |
| `ProjectScore` | project | **Decision variable.** Whole-project regression guard across iterations (2f) — catches damage in fields you did not touch. |
| `ValidatedDocuments` | project | **Decision variable.** Below the document count → unlabelled documents exist; label them before looping (1e). |
| `ModelVersion` | project | **Decision variable.** Retrain completion ([Waiting for retrain](#waiting-for-retrain)). |
| `ErrorRate` | field, group | **Report only — carries no independent signal.** It is exactly `1 - Precision` (verified across every field and group of a real project at two model versions). Never treat it as a second opinion on `Precision`, and never threshold on both. |
| `Quality` | field | **Report only — never gate on it.** A coarse label (`average`, `good`, …). It does **not** share a scale with `ProjectScoreQuality`: an `F1` of 1.00 still reads `good` at field level while a `ProjectScore` of 0.91 reads `excellent`. Report it beside the number; make every decision on the number. |
| `ProjectScoreQuality` | project | **Report only.** IXP's label for `ProjectScore` — different scale from field `Quality` (above). |
| `FieldGroup`, `FieldId` | field | Identity. `FieldId` needs the taxonomy join for a human-readable name (see 1a). |

Two consequences worth stating outright:

1. **`F1` alone is not enough to act on.** A field at `F1` 0.60 with `Precision` 0.45 / `Recall` 0.95 needs the opposite rewrite from one at `F1` 0.60 with `Precision` 0.95 / `Recall` 0.45. Always read the triple.
2. **`F1` is a ratio over `Annotations`, so small `Annotations` means coarse `F1`.** With 5 annotations the achievable values near the top are 1.00, 0.889, 0.80 — adjacent steps of ~0.11. See [Regression noise floor](#regression-noise-floor) in 2f before rolling anything back on a delta that small.

## Waiting for retrain

Every change to model inputs — labellings, instructions, document upload/delete, taxonomy edits — triggers a full retrain. Metrics read mid-retrain are *pre*-change scores and corrupt every downstream comparison, so wait before each metrics read.

**Bounded wait. Poll on a fixed interval; never poll indefinitely:**

1. Record `ModelVersion` from the last metrics read BEFORE the change.
2. Wait 2 minutes, then read `uip ixp projects get-metrics <project-name> --output json`.
3. `ModelVersion` **greater than** the recorded value → retrain is done, proceed. Any increment counts. Do NOT wait for a specific number: queued input changes can bump the version by more than one, so waiting for exactly *N*+1 polls until the budget dies when the server jumps straight to *N*+2.
4. Otherwise repeat step 2 — **2 minutes between checks, 5 checks in total** (10 minutes). Do NOT use a single long sleep, and do NOT escalate or shorten the interval between checks.
5. Still unchanged after the 5th check → **stop polling** and report that the retrain did not complete. Metrics you carry forward predate the change: label them as such, never present them as the post-change measurement, and never roll back instructions on a comparison against them.

A read that fails counts against the budget like any other attempt, and never restarts it.

## Step 1 — Setup (once, before the loop)

### 1a. Get baseline metrics

If documents were just labelled (or uploaded, or the taxonomy was edited), wait out the resulting retrain before reading metrics — apply the bounded wait in [Waiting for retrain](#waiting-for-retrain).

```bash
mkdir -p /tmp/ixp/<project-name>/{docs,text,taxonomies,prompts}
uip ixp projects get-metrics <project-name> --output json
```

Note the `ModelVersion` from this baseline read — later iterations check that it advances after each `fields update-prompts` / `groups update-prompts` (see step 2e). If the value here looks identical to a known pre-labelling version, the retrain may still be in flight; re-fetch under the bounded wait in [Waiting for retrain](#waiting-for-retrain), then proceed with whatever it returns.

Save the full per-field `Fields` array as `baseline_metrics`. This is the starting point you compare against. (For a validated model, get-metrics Data is flat — `Fields`/`FieldGroups`/`ValidatedDocuments` are top-level. An unvalidated model returns `Data: { Metrics: null }` instead — re-fetch under the bounded wait above.)

**Correlating metrics to field names:** The metrics `Fields` array returns `FieldId` but not the field name. To map them, join against the taxonomy's `field` entries:

- For each metric entry: `FieldGroup` = label_def name, `FieldId` = the field's `field_id`
- Find the matching field entry in the taxonomy where `field_id == FieldId` — its `name` is the human-readable field name

Build this mapping once and reuse it throughout the loop.

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

Compare the document list against the metrics. If the metrics show fewer `ValidatedDocuments` than the total document count, some documents have no confirmed labellings (e.g., newly added documents). Review and label them first using the [Label Documents Guide](label-documents-guide.md), then re-fetch metrics under the bounded wait in [Waiting for retrain](#waiting-for-retrain) before starting the loop.

---

## Step 2 — Optimization Loop

Repeat the following for each iteration (up to max iterations):

### 2a. Diagnose fields and field groups

Use the current metrics (baseline on first iteration, post-relabel metrics on subsequent iterations). The metrics include both `FieldGroups` (per-group scores) and `Fields` (per-field scores).

**Field group diagnosis:** Check `FieldGroups` first. If an entire group has low F1, the group-level instructions may need updating with `--groups` rather than fixing individual fields.

**Per-field diagnosis:** Identify individual fields with F1 < 0.7 as targets. Diagnose each:

1. **Classify the action:**
   - `Documents = 0` AND `F1 = 0` → **SKIP**
   - `Documents < 1` → **SKIP**
   - Otherwise → **REFINE**

2. **Diagnose the problem type** from the `Precision`/`Recall` split — `F1` says *how bad*, the split says *what to write*:
   - `Precision < Recall` significantly → **PRECISION** — model extracts wrong values
   - `Recall < Precision` significantly → **RECALL** — model misses the field
   - Otherwise → **BOTH** — rewrite entirely

3. **Record the field's `Annotations` count** next to the diagnosis. It does not change the classification, but it sets how much of the following delta you are entitled to believe (2f), so carry it forward rather than re-fetching it later.

Print a diagnosis summary with one row per field — name, `F1`, `Precision`, `Recall`, `Annotations`, `Documents`, `Quality`, diagnosis — plus the group rows and the project line (`ProjectScore` / `ProjectScoreQuality` / `ValidatedDocuments` / `ModelVersion`). Report `Quality` as the label IXP returned; do not convert it to a threshold or compare it against `ProjectScoreQuality` (different scales — see [What `get-metrics` returns](#what-get-metrics-returns-and-which-values-decide)). Omit `ErrorRate`: it is `1 - Precision` and adds a column of nothing.

If no fields need REFINE, stop — the project is already at target quality.

### 2a-check. Check for labelling gaps (before writing instructions)

For each REFINE field with **Recall < 0.5**, check whether the problem is a bad prompt or a missing label:

1. Look at the sample document images you already have from Step 1d
2. For each low-recall field, check: **can you see this field's value in the document?**
   - If yes, the model may have predicted it correctly but it wasn't confirmed in a previous round → re-fetch predictions and review those fields again
   - If the field is genuinely not visible in the document → it's a prompt/recall issue, handle with instruction changes

**If you find previously skipped predictions that are actually correct**, confirm them now using `labelling confirm --fields` for those specific documents and fields, then re-fetch metrics under the bounded wait in [Waiting for retrain](#waiting-for-retrain) before continuing.

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

Use **field names** for `--fields` and **label_def names** for `--groups`:

```bash
cat > /tmp/ixp/<project-name>/prompts/field_updates.json << 'FIELDS_EOF'
[
  {"name": "Invoice Number", "instructions": "The unique document identifier, found in the header area top-right. Example: 2106732, QC006."},
  {"name": "Invoice Date", "instructions": "The date the invoice was issued. Use the exact format as written in the document. Found near the invoice number."}
]
FIELDS_EOF

uip ixp fields update-prompts <project-name> \
  --updates "$(cat /tmp/ixp/<project-name>/prompts/field_updates.json)" \
  --output json

# If group instructions also need updating, run a second command.
cat > /tmp/ixp/<project-name>/prompts/group_updates.json << 'GROUPS_EOF'
[
  {"name": "Invoice", "instructions": "General invoice header fields including number, dates, payment terms, and totals."}
]
GROUPS_EOF

uip ixp groups update-prompts <project-name> \
  --updates "$(cat /tmp/ixp/<project-name>/prompts/group_updates.json)" \
  --output json
```

The second call is optional — skip it if the group instructions don't need changing.

**Post-update verification:** After the update, re-fetch the taxonomy, save it as the next version, and verify that field counts per label_def are unchanged:

```bash
uip ixp projects get-taxonomy <project-name> --output json > /tmp/ixp/<project-name>/taxonomies/v<N>.json
```

Compare the number of fields in each updated label_def against the previous version. If any fields are missing, **STOP the workflow immediately** and report to the user — the taxonomy was corrupted and needs manual restoration. The previous taxonomy version has the old instructions for rollback.

### 2d. Review and confirm predictions for all documents

Wait out the retrain triggered by the updated instructions ([Waiting for retrain](#waiting-for-retrain)), then review predictions for all documents using the [Label Documents Guide](label-documents-guide.md). The updated prompts should produce better predictions — review each document's predictions against the actual content and confirm the correct ones. Documents with incorrect predictions are skipped (their old labels remain).

### 2e. Wait and get new metrics

Wait out the retrain triggered by the new labellings ([Waiting for retrain](#waiting-for-retrain)), then:

```bash
uip ixp projects get-metrics <project-name> --output json
```

If `ModelVersion` hasn't advanced since the last check, keep re-reading under that same bounded budget. When the budget runs out, record the metrics you have and move on to step 2f — do NOT stall the iteration waiting for a version bump.

### 2f. Compare and decide

Compare the new metrics against the **previous iteration** at both levels — the fields you touched, and the project as a whole.

#### Regression noise floor

`F1` is a ratio over that field's `Annotations`, so it cannot move in arbitrarily small steps. With `Annotations` = 5 the reachable values near the top are 1.00, 0.889, 0.80 — **adjacent steps of ~0.11**. A flat "rolled back if it dropped more than 0.1" therefore fires on the smallest change the metric is capable of expressing: one annotation flipping is indistinguishable from a genuinely worse instruction, and the loop rolls back a change that did nothing measurable.

Set the threshold from the sample size instead:

```text
noise_floor = 1 / Annotations        # smallest F1 step this field can express
regression_threshold = max(0.1, 2 x noise_floor)
```

At `Annotations` = 5 that is 0.4 — a drop must exceed two of the smallest possible steps before it counts as evidence. At `Annotations` = 40 it collapses back to the flat 0.1. Fields whose `Annotations` differ get different thresholds in the same iteration; that is intended, not an inconsistency.

**Below the threshold is not "no change" — it is "not measurable yet".** Do not report a sub-threshold move as an improvement either. If a field keeps drifting sub-threshold across iterations and its `Annotations` is small, the fix is more labelled documents, not more prompt rewrites — say so in the final report.

**Selective regression check:** For each field you updated this iteration, compare its `F1` drop against **that field's** `regression_threshold`:

- **Regressed fields** (drop > their threshold): roll back ONLY those fields' instructions to the previous iteration's version. Keep the improved instructions for fields that gained or held steady.
- **Improved/unchanged fields**: keep their new instructions.

**Project-level guard (fields you did NOT touch):** per-field checks only cover the fields you edited, but instructions interact — a sharper rule on one field can pull the model off another, and group instructions affect every field under them. So also compare `ProjectScore` against the previous iteration:

- `ProjectScore` dropped **and** no edited field regressed → the damage is in a field you did not edit. Diff the full `Fields[]` array against the previous iteration to find it, then roll back this iteration's edits that could plausibly have caused it (same group first). Do not accept the iteration on the strength of the edited fields alone.
- `ProjectScore` held or rose while one edited field regressed → roll back that field only, as above; the iteration is otherwise sound.

If any fields regressed, do a selective rollback:

```bash
# Only include the regressed fields, not the whole iteration
cat > /tmp/ixp/<project-name>/prompts/rollback.json << 'FIELDS_EOF'
[{"name": "Vendor Address", "instructions": "previous instruction for this field only"}]
FIELDS_EOF

uip ixp fields update-prompts <project-name> \
  --updates "$(cat /tmp/ixp/<project-name>/prompts/rollback.json)" \
  --output json
```

Wait out the retrain ([Waiting for retrain](#waiting-for-retrain)). On the next iteration, try a **different approach** for the regressed fields only (different wording, shorter instruction, fewer examples).

**Rollback caveat:** Rollback restores the previous instructions but the model needs to retrain. Expect only **partial recovery** — prefer small-scope iterations (few fields at a time).

**No regression:** Accept the iteration. Update `previous_metrics` (the complete payload again, not just F1) and `previous_instructions` with the new values.

**Stopping criteria — stop the loop if:**

- All fields meet the user's target F1 (default: 0.7)
- Max iterations reached
- No fields improved by more than their own noise floor in the last 2 consecutive iterations (diminishing returns — a run of sub-threshold moves is not progress)

---

## Step 3 — Final Report

After the loop ends, print a summary:

```text
Optimization complete after N iterations. Model version V1 -> V2.

Field           | Base F1 | Final F1 | Change    | Prec  | Rec   | Ann | Quality
----------------|---------|----------|-----------|-------|-------|-----|--------
Invoice Number  | 0.450   | 0.820    | +0.370    | 0.850 | 0.790 |  40 | good
Description     | 0.300   | 0.650    | +0.350    | 0.700 | 0.610 |  38 | average
Bill-To Name    | 0.900   | 0.900    | unchanged | 0.900 | 0.900 |  40 | good
Vendor Address  | 0.600   | 0.400    | -0.200 (rolled back) | 0.410 | 0.390 | 40 | average
Freight Charge  | 1.000   | 0.889    | -0.111 (within noise floor, kept) | 0.800 | 1.000 | 5 | good

Project score:   X.XX (Quality) -> Y.YY (Quality)   ValidatedDocuments: D
Iterations: N total, M with rollbacks
Fields still below target (F1 < 0.7): [list]
Fields whose Annotations are too few to measure progress (noise floor > 0.1): [list]
Labelling gaps fixed: [list any fields re-labelled in 2a-check]
```

Report `Precision`/`Recall` alongside `F1` — they say whether a field that is still short is over-extracting or under-extracting, which is what the user needs to decide the next move. Report `Annotations` so a reader can tell a real plateau from an unmeasurable one. Report `Quality` verbatim as IXP's own label. Do **not** add an `ErrorRate` column (it is `1 - Precision`).

If fields still need work, suggest the user run another round with more iterations. If any field appears in the *too-few-`Annotations`* list, say plainly that more labelled documents — not more prompt rewrites — is what will move it.
