# Label Documents Guide

Reusable workflow for labelling documents in an IXP project, used by [Project Setup](project-setup-guide.md) and [Improve Prompts](improve-prompts-guide.md).

Act as a **reviewer**: IXP generates predictions; validate every field against the document. Confirm only correct fields; leave wrong fields unannotated.

## Step 1 — Get Documents and Taxonomy

Run:

```bash
mkdir -p /tmp/ixp/<project-name>/{docs,taxonomies,payloads}
uip ixp documents list <project-name> --output json
uip ixp projects get-taxonomy <project-name> --output json
```

Save the taxonomy as `/tmp/ixp/<project-name>/taxonomies/v1.json`, incrementing the version on each re-fetch. Review field groups and types from raw snake_case `Data.dataset.label_groups` and `Data.dataset.entity_defs`.

## Step 2 — Process Each Document

Process documents one at a time: get predictions, download, review, and confirm.

### 2a. Get predictions for this document

Run:

```bash
uip ixp labellings get-predictions <project-name> <document-id> --output json
```

The response is `Data: { ProjectName, TotalDocuments, DocumentsWithPredictions, Predictions[] }`; each `Predictions[]` entry is `{ DocumentId, Labels[] }` (use `Predictions[0]` for a single-document call), each label is `{ Name, Occurrence, Fields[] }`, and each field is `{ FieldId, FieldName, FormattedValue }`. `Occurrence` is the explicit 0-based index for `--occurrence`/`--updates-file`, valid **only for this read**; see [Occurrence numbers are read-scoped](#occurrence-numbers-are-read-scoped).

Record `ModelVersion` and pass it to every `confirm --model-version` operation below so retraining cannot silently change reviewed values.

### 2b. Download the document file

Reuse an existing file in `/tmp/ixp/<project-name>/docs/`; do NOT re-download it. Otherwise run:

```bash
uip ixp documents download <project-name> <document-id> -o /tmp/ixp/<project-name>/docs/<document-id> --output json
```

Use the document ID as the filename and pass `-o` without an extension; the CLI appends the server content-type extension (PDF, PNG, JPG, …). Read the response `Path` and use it next. A path without an extension means unknown content type; see [CLI Reference § Documents](cli-reference.md#documents). Files persist across sessions.

### 2c. Review predictions field-by-field

Use the **Read tool** once on the whole file, with no `pages` parameter. Full Read returns text and image natively for digital or scanned PDF/PNG/JPG documents; do not install or use PDF tools.

1. Inspect layout and field locations.
2. Assign every predicted field one verdict:
   - **CONFIRMED**: value matches literally or in the type's normalized form. Capitalization and whitespace OCR differences and type normalization are acceptable; e.g. `Date` may read `2022-06-21T00:00:00Z` for `21-JUN-22`, and `Monetary Quantity` may read `114.91 AUD` for `114.91`. Compare by reading; do not script conversions or checks. See [CLI Reference § Normalized output formats](cli-reference.md#normalized-output-formats).
   - **MISSING**: IXP returned an empty `FormattedValue` **and** the field is genuinely absent. Both conditions are required. A non-empty wrong prediction is NOT MISSING; Critical Rule 11 forbids overriding it.
   - **NOT CONFIRMED**: any mismatch, including wrong literal value or source, garbled characters (e.g., `MSIÓÓÓ601020/` instead of `MSI0601020`), misread digits (page `£7,300.00` predicted as `£730.00`), wrong boolean, wrong inferred/computed value, hallucination, or a value absent from the document. A number with different magnitude is never type normalization (Rule 8). Leave it unannotated (Critical Rule 8). OCR errors are data quality issues: report them and do not spend prompt iterations on them.
3. Report every field in a table per document:

```text
Document: <document-id>

Field                    | Verdict       | Reason
-------------------------|---------------|-----------------------------------------------
Invoice Number           | NOT CONFIRMED | OCR: predicted "MSIÓÓÓ601020/" but actual is "MSI0601020", top-right of page 1
Invoice Date             | CONFIRMED     | Predicted "2018-02-28T00:00:00Z" matches "28-Feb-2018" (normalized Date)
Vendor Address           | NOT CONFIRMED | Predicted "<ADDRESS_A>" but actual is "<ADDRESS_B>", top-left of page 1
Has Signature            | NOT CONFIRMED | Predicted "false" but signature visible bottom-right (boolean came back wrong)
Total After Tax          | NOT CONFIRMED | Predicted "$1100.00" but Subtotal+Tax = "$1210.00" (inferred value wrong)
Terms of Payment         | MISSING       | IXP predicted no value AND field not visible in document
Discount                 | MISSING       | IXP predicted no value AND no discount section on the page
Line Items > Description | CONFIRMED     | Predicted "Widget A" matches row 1 in the table
```

For **MISSING**, state that the prediction was empty and how absence was verified (e.g., "no payment-terms section anywhere in the document"). For **NOT CONFIRMED**, state predicted value, actual value if visible, and location; begin OCR reasons with `OCR:`.

Repeatable groups return one label per row, each with an explicit 0-based `Occurrence` (for example, `Line Items` rows are indexed `0..N-1`). Read the returned occurrence directly, but match rows by field values rather than index because confirmed rows reorder; see [Occurrence numbers are read-scoped](#occurrence-numbers-are-read-scoped). Report differing verdicts per occurrence:

```text
Line Items > Description (occurrence 0) | CONFIRMED     | "Widget A" matches line 1
Line Items > Description (occurrence 1) | CONFIRMED     | "Widget B" matches line 2
Line Items > Description (occurrence 3) | NOT CONFIRMED | Predicted "Widget D" but line 4 shows "Widget Z"
```

4. Build one submit list containing every CONFIRMED and MISSING field ID. The CLI applies the appropriate semantic.

### 2d. Confirm

Submit all confirmed and missing fields for the document in one call. Always add `-m <model_version>` using the `ModelVersion` from 2a, including narrowed `--occurrence` and `--updates-file` calls. If confirmation is rejected with `PredictionVersionChangedError`, rerun 2a, re-review, and confirm again.

Run:

```bash
uip ixp labellings confirm <project-name> <document-id> \
  --fields "<confirmed_id_1>,<confirmed_id_2>,<missing_id>" -m <model_version> --output json
```

`--fields` combines CONFIRMED and MISSING IDs. If IXP predicted content, it is confirmed; if it predicted nothing, a missing marker is written. Include a MISSING field only when IXP predicted nothing; omit wrong non-empty predictions (Critical Rule 11).

If every predicted field on this document was reviewed and is correct, run:

```bash
uip ixp labellings confirm <project-name> <document-id> -m <model_version> --output json
```

This confirms every prediction for that document only. Never omit `<document-id>`: that confirms every project document without review. Wrong labels can make F1 report `1.00`; F1 alone never proves correctness (Critical Rule 14).

To record a genuinely missing field directly, run:

```bash
uip ixp labellings mark-missing <project-name> <document-id> --fields <ids>
```

This also handles a prior annotation whose current prediction disappeared after retraining, which `confirm` cannot reach. Use it only when `get-predictions` shows no value; never override a wrong prediction.

**Per-occurrence confirm.** If verdicts differ across repeatable-group rows, unscoped `--fields` confirms that field in every occurrence, including wrong ones. Target rows by index:

```bash
# All predicted fields in occurrence 0:
uip ixp labellings confirm <project-name> <document-id> \
  --group "Line Items" --occurrence 0 -m <model_version> --output json

# Just Quantity in occurrence 2:
uip ixp labellings confirm <project-name> <document-id> \
  --group "Line Items" --occurrence 2 --fields c4e1907a3b8f25d6 -m <model_version> --output json
```

Untargeted occurrences retain existing annotations, so wrong predictions remain unannotated. Confirm all correct rows in one `--updates-file` call, not separate `--occurrence` calls; all indices then resolve against one read:

```bash
cat > /tmp/ixp/<project-name>/payloads/confirm_updates.json << 'EOF'
[{"occurrence":0},{"occurrence":2,"fields":["c4e1907a3b8f25d6"]}]
EOF

uip ixp labellings confirm <project-name> <document-id> \
  --group "Line Items" --updates-file /tmp/ixp/<project-name>/payloads/confirm_updates.json \
  -m <model_version> \
  --output json
```

See [CLI Reference § Labellings](cli-reference.md#labellings) and Critical Rule 12.

**Per-occurrence unconfirm.** `unconfirm` accepts the same `--group`/`--occurrence`/`--updates-file` flags. Without `--group`, `unconfirm --fields a7c3e9105f2b4d86` removes that field from every occurrence; scope one or several occurrences with `--group "Line Items" --occurrence 2` or `--group "Line Items" --updates-file <path>`. Without `--fields`, roll back every annotated field in targeted occurrences; with it, only those fields. See Critical Rule 13.

Run:

```bash
# Roll back only occurrence 2 of Line Items (every field in that line):
uip ixp labellings unconfirm <project-name> <document-id> \
  --group "Line Items" --occurrence 2 --output json
```

Take indices from a **fresh** `get-predictions`; after partial confirmation, the index that confirmed a row usually differs from the rollback index.

### 2e. Move to the next document

Repeat 2a–2d for every listed document.

### Occurrence numbers are read-scoped

`get-predictions` does not preserve repeatable-group order: annotated occurrences appear first, then unannotated ones. Thus confirming the third of four rows can return it as `Occurrence` 0, shifting others; the UI behaves the same. Values and page locations remain attached to their rows. Only an entirely unannotated or entirely annotated group reads in document order.

An `Occurrence` is valid only for the read that produced it; any write invalidates it. Therefore:

- Put all occurrences to confirm or unconfirm in one `--updates-file` call.
- If sequential calls are unavoidable, rerun `get-predictions` between them and relocate rows by field values.
- Never reuse an index after a write; report rows by value, not position.

### Removing a document from the project

Delete unusable documents (wrong type, corrupted, or duplicate) instead of confirming or skipping them. Run:

```bash
uip ixp documents delete <project-name> <document-id> -y --output json
```

`-y/--yes` is required; the CLI never prompts. Use the whole `DocumentId` from `documents list`, not AttachmentRef or Filename. Deletion is irreversible and triggers model retraining. Do not delete merely to skip labelling; leave such documents unconfirmed.

**Finding the DocumentId:**

| You have | How to get the DocumentId |
|----------|---------------------------|
| Filename (e.g., `invoice-001.pdf`) | Run `uip ixp documents list <project-name> --limit 10000 --output-filter "Documents[?Filename=='invoice-001.pdf'].DocumentId \| [0]" --output plain`; rows are under `Documents`, the list is a paged envelope, and `--output-filter` requires explicit `--limit`. |
| Distinctive predicted field value (e.g., Invoice Number `MSI0601020`) | Run `uip ixp documents list <project-name> --output json`, then run `uip ixp labellings get-predictions <project-name> <document-id> --output json` per ID until `Labels[].Fields[].FormattedValue` matches; stop at the first match. |
| Content only | Run `uip ixp documents list <project-name> --output json`, download candidates, and read them with the Read tool. |

`documents list` returns `Filename` with `DocumentId` (original upload filename, or `null`). If filenames are not unique, the JMESPath filter returns multiple IDs; review downloaded documents before deleting. Example IDs such as `3453547f3538febd.1fc885607f2aac621f8f2d3ef1847f22` must be passed whole.

## Step 3 — Summary

After all documents:

- Do NOT stop at the first error; continue with remaining documents.
- If download fails, skip the document and note the failure.
- If confirmation fails, log the error and document ID, then continue.

Report:

```text
Labelling complete.

Documents: N processed, M confirmed, K skipped (no predictions)
Fields: X confirmed, W marked missing, Z not confirmed

Marked Missing (IXP predicted empty AND field absent from document):
  Doc <uid-2>: Terms of Payment
  Doc <uid-4>: Discount

Not Confirmed (skipped):
  Doc <uid-1>: Invoice Number — OCR: predicted "MSIÓÓÓ601020/" but actual is "MSI0601020"
  Doc <uid-3>: Total Amount — predicted "500.00" but actual is "5000.00" (bottom-right, page 1)
  Doc <uid-5>: Vendor Address — predicted "<ADDRESS_A>" but actual is "<ADDRESS_B>"
```