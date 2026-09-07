# Label Documents Guide

Reusable workflow for labelling documents in an IXP project. Used by:

- [Project Setup](project-setup-guide.md) — initial labelling after creating a project
- [Improve Prompts](improve-prompts-guide.md) — reviewing predictions during optimization

Act as a **reviewer**: IXP generates predictions; validate them field-by-field against the document. Confirm only correct fields. Leave wrong fields unannotated. Correct only OCR-mangled values when IXP found the right location.

## Step 1 — Get Documents and Taxonomy

Run:

```bash
mkdir -p /tmp/ixp/<project-name>/{docs,text,taxonomies,prompts}
uip ixp documents list <project-name> --output json
uip ixp projects get-taxonomy <project-name> --output json
```

Save the taxonomy as `/tmp/ixp/<project-name>/taxonomies/v1.json`; increment the version on each re-fetch. Review raw snake_case field groups and fields under `Data.dataset.label_groups`, and types under `Data.dataset.entity_defs`.

## Step 2 — Process Each Document

Process documents one at a time: get predictions, download or reuse the file, review every field, and confirm only approved fields.

### 2a. Get predictions

Run:

```bash
uip ixp labellings get-predictions <project-name> <document-id> --output json
```

Read `Data: { ProjectName, TotalDocuments, DocumentsWithPredictions, Predictions[] }`. Each `Predictions[]` entry is `{ DocumentId, Labels[] }` (for a single-document call, `Predictions[0]`). Each label is `{ Name, Occurrence, Fields[] }`; each field has `FieldId`, `FieldName`, `FormattedValue`.

Treat `Occurrence` as the explicit 0-based index for `--occurrence`/`--updates`, valid **for this read only**; see [Occurrence numbers are read-scoped](#occurrence-numbers-are-read-scoped). Record `ModelVersion` and pass it to every `confirm --model-version` call so a retrain cannot silently change reviewed values.

### 2b. Download the document

If the file exists in `/tmp/ixp/<project-name>/docs/`, reuse it and do NOT re-download. Otherwise run:

```bash
uip ixp documents download <project-name> <document-id> -o /tmp/ixp/<project-name>/docs/<document-id> --output json
```

Pass `-o` without an extension. Read the response's resolved `Path` and use it next; the CLI detects the content format and appends the correct extension. Files persist across sessions.

### 2c. Review every predicted field

Use the **Read tool** once on the whole file with no `pages` parameter. A full Read returns text + image natively for digital and scanned PDF/PNG/JPG documents; do not install PDF tools. Understand the layout, then evaluate every predicted field.

Use exactly one verdict per field:

- **CONFIRMED** — the value matches literally or in the data type's normalized form. Capitalization, whitespace, and type normalization are acceptable. For example, a `Date` may read back as `2022-06-21T00:00:00Z` for `21-JUN-22`, and a `Monetary Quantity` as `114.91 AUD`. Compare by reading; do not write a conversion/checking script. See [CLI Reference § Normalized output formats](cli-reference.md#normalized-output-formats).
- **CORRECTED** — OCR mangling only: the prediction found the right field and location, the bytes-on-page are correct, and only the transcription is garbled. A magnitude difference is OCR garble, never type normalization (Rule 8). Do not correct formatting, wrong booleans, wrong inferred/computed values, or wrong source selection.
- **MISSING** — IXP predicted an empty `FormattedValue` **and** the field is genuinely absent. Both conditions are required. A non-empty prediction for an absent field is NOT CONFIRMED, never MISSING (Critical Rule 12).
- **NOT CONFIRMED** — every other error: wrong literal value, wrong source, hallucination, wrong boolean, wrong inferred/computed value, or a value not present in the document. Leave it unannotated and do not use `--corrections`; improve the prompt instead. `--corrections` is OCR-only (Critical Rule 8).

Report every field in a table per document:

```text
Document: <document-id>

Field                    | Verdict       | Reason
-------------------------|---------------|-----------------------------------------------
<field>                  | <verdict>     | <comparison, correction, or absence evidence>
```

For CORRECTED, state the mangled value, corrected value, and location; the error must be character-level in the same field and location. For MISSING, state that the prediction was empty and how absence was verified. For NOT CONFIRMED, state the predicted value, actual value if visible, and location.

Repeatable field groups produce one extraction per row. `get-predictions` returns one label per row with a 0-based `Occurrence`; read it directly, but match rows to the document by values, not index. On an unlabelled document it matches document order; after partial confirmation it may not. Report differing rows separately.

Build:

- **Submit field IDs**: all CONFIRMED, CORRECTED, and MISSING fields in one combined list.
- **Corrections JSON**: CORRECTED fields only, `[{'field_id':'...','value':'corrected text'}]` (use valid JSON with double quotes in the command).

### 2d. Confirm and correct

Pass the reviewed `ModelVersion` as `-m <model_version>` to every `confirm` call, including narrowed `--occurrence`/`--updates` calls. If confirmation returns `PredictionVersionChangedError`, run 2a again, re-review, and confirm again.

With corrections, run:

```bash
uip ixp labellings confirm <project-name> <document-id> \
  --fields "<all_submitted_ids>" \
  --corrections '[{"field_id":"<id>","value":"<corrected_value>"}]' \
  -m <model_version> \
  --output json
```

Without corrections, run:

```bash
uip ixp labellings confirm <project-name> <document-id> \
  --fields "<field_id_1>,<field_id_2>,<field_id_3>" -m <model_version> --output json
```

`--fields` may contain CONFIRMED, CORRECTED, and MISSING IDs. The CLI confirms content, applies a correction override while retaining document references/bounding boxes, or writes a missing marker when the prediction is empty. If every reviewed prediction is correct, run the per-document form:

```bash
uip ixp labellings confirm <project-name> <document-id> -m <model_version> --output json
```

Never run `confirm` without `<document-id>`: that confirms every project document without review. Wrong labels can make F1 report 1.00, so F1 alone is never evidence of correctness.

Include a MISSING field only when `get-predictions` shows no value (Critical Rule 12). For mixed approved fields, run:

```bash
uip ixp labellings confirm <project-name> <document-id> \
  --fields "<confirmed_id>,<corrected_id>,<missing_id_1>,<missing_id_2>" \
  --corrections '[{"field_id":"<corrected_id>","value":"<corrected_value>"}]' \
  -m <model_version> \
  --output json
```

Run this when a missing marker must be written directly, including when `confirm --fields` cannot reach a field with a prior annotation:

```bash
uip ixp labellings mark-missing <project-name> <document-id> --fields <ids>
```

Use it only when IXP predicted no value; never override a wrong prediction.

For repeatable groups with differing verdicts, do not use unscoped `--fields`; it applies to every occurrence. Target occurrences by index:

```bash
# All predicted fields in occurrence 0:
uip ixp labellings confirm <project-name> <document-id> \
  --group "Line Items" --occurrence 0 -m <model_version> --output json

# Just Quantity in occurrence 2:
uip ixp labellings confirm <project-name> <document-id> \
  --group "Line Items" --occurrence 2 --fields c4e1907a3b8f25d6 -m <model_version> --output json
```

Confirm all correct rows in one `--updates` call, not separate `--occurrence` calls:

```bash
uip ixp labellings confirm <project-name> <document-id> \
  --group "Line Items" --updates '[{"occurrence":0},{"occurrence":2,"fields":["c4e1907a3b8f25d6"]}]' \
  -m <model_version> \
  --output json
```

Every index in one call resolves against the same read. See [CLI Reference § Labellings](cli-reference.md#labellings) and Critical Rule 13.

Run `unconfirm` with the same `--group`/`--occurrence`/`--updates` scope to roll back an incorrect confirmation. Unscoped `unconfirm --fields a7c3e9105f2b4d86` affects that field in every occurrence; scope it to one or several occurrences to limit the rollback. Without `--fields`, roll back every annotated field in the target occurrence(s). Use a fresh `get-predictions` index because partial confirmation can reorder occurrences. See Critical Rule 14.

```bash
# Roll back only occurrence 2 of Line Items (every field in that line):
uip ixp labellings unconfirm <project-name> <document-id> \
  --group "Line Items" --occurrence 2 --output json
```

### 2e. Move to the next document

Repeat steps 2a–2d for every document in the list.

### Occurrence numbers are read-scoped

`get-predictions` lists matched annotation/prediction pairs first, then unmatched predictions. Confirmed rows therefore move to the front, as in the IXP UI; values and page locations are retained. Only a group with no annotations or with every row annotated reads in document order.

An `Occurrence` is valid only for the read that produced it, and any write invalidates it:

- put all target occurrences in one `--updates` call;
- if sequential calls are unavoidable, run `get-predictions` between them and re-locate rows by field values;
- never reuse an index after a write;
- report rows by value, not as a row number.

### Removing a document from the project

For a wrong type, corruption, or duplicate, run deletion instead of confirming or skipping:

```bash
uip ixp documents delete <project-name> <document-id> -y --output json
```

`-y/--yes` is required. Use the whole `DocumentId` from `documents list`, not AttachmentRef or Filename. Deletion is irreversible and triggers model retraining; do not delete merely to skip labelling.

Find the `DocumentId` as follows:

| You have | How to get the DocumentId |
|----------|---------------------------|
| Filename | Run `uip ixp documents list <project-name> --output json --output-filter "Documents[?Filename=='invoice-001.pdf'].DocumentId \| [0]" --output plain` (rows are under `Documents` in a paged envelope). |
| A distinctive predicted field value | Run `uip ixp documents list <project-name> --output json`, then run `uip ixp labellings get-predictions <project-name> <document-id> --output json` per ID until `Labels[].Fields[].FormattedValue` matches; stop at the first match. |
| Nothing — need to find by content | Run `uip ixp documents list <project-name> --output json`, download candidates with `documents download`, and read them with the Read tool. |

`documents list` returns `Filename` with `DocumentId`; it may be the original upload filename or `null`. If filenames are not unique, review all IDs returned before deleting.

## Step 3 — Summary

Do not stop at the first error. Continue with remaining documents. If download or text fetch fails, skip the document and record the failure. If confirmation fails, log the error and UID, then continue.

Report:

```text
Labelling complete.

Documents: N processed, M confirmed, K skipped (no predictions)
Fields: X confirmed, Y corrected, W marked missing, Z not confirmed

OCR Corrections Applied:
  Doc <uid-1>: <field> "<mangled>" → "<corrected>"
  Doc <uid-3>: <field> "<mangled>" → "<corrected>"

Marked Missing (IXP predicted empty AND field absent from document):
  Doc <uid-2>: <field>
  Doc <uid-4>: <field>

Not Confirmed (skipped):
  Doc <uid-3>: <field> — predicted "<value>" but actual is "<value>" (<location>)
  Doc <uid-5>: <field> — predicted "<value>" but actual is "<value>"
```
