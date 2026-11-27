# Label Documents Guide

Reusable document-labelling workflow for IXP projects, used by [Project Setup](project-setup-guide.md) and [Improve Prompts](improve-prompts-guide.md).

Act as a **reviewer**: IXP generates predictions; validate every field against the document. Confirm only correct fields; leave wrong fields unannotated.

## Step 1 — Get Documents and Taxonomy

Run:

```bash
mkdir -p /tmp/ixp/<project-name>/{docs,taxonomies,payloads}
uip ixp documents list <project-name> --output json
uip ixp projects get-taxonomy <project-name> --output json
```

Save the taxonomy as `/tmp/ixp/<project-name>/taxonomies/v1.json`, incrementing the version on each re-fetch. Review raw snake_case groups/fields under `Data.dataset.label_groups` and types under `Data.dataset.entity_defs`.

## Step 2 — Process Each Document

Process one document at a time: get predictions, download, review, then confirm.

### 2a. Get predictions for this document

Run:

```bash
uip ixp labellings get-predictions <project-name> <document-id> --output json
```

The response is `Data: { ProjectName, TotalDocuments, DocumentsWithPredictions, Predictions[] }`; each `Predictions[]` entry is `{ DocumentId, Labels[] }` (use `Predictions[0]` for a single-document call), each label is `{ Name, Occurrence, Fields[] }`, and each field is `{ FieldId, FieldName, FormattedValue }`. `Occurrence` is the explicit 0-based index for `--occurrence`/`--updates-file`, valid **for this read only**; see [Occurrence numbers are read-scoped](#occurrence-numbers-are-read-scoped).

Record `ModelVersion` and pass it to `confirm --model-version` in step 2d so retraining cannot silently change reviewed values.

### 2b. Download the document file

Reuse an existing file in `/tmp/ixp/<project-name>/docs/`; do **not** re-download it. Otherwise run:

```bash
uip ixp documents download <project-name> <document-id> -o /tmp/ixp/<project-name>/docs/<document-id> --output json
```

Pass `-o` without an extension; the CLI appends the server content-type extension (PDF, PNG, JPG, …). Read the response `Path` and use it. No extension means unknown content type (see [CLI Reference § Documents](cli-reference.md#documents)). Files persist across sessions.

### 2c. Review predictions field-by-field

Use the **Read tool** once on the whole file, with no `pages` parameter. Full Read returns text and image natively for digital/scanned PDF/PNG/JPG documents; do not install or use PDF tools.

1. **Look at the document** to understand the layout and where field values appear.
2. **For each predicted field**, assign exactly one verdict:
   - **CONFIRMED**: the value matches literally or in the type's normalized form. Capitalization/whitespace and type normalization are acceptable. Read and compare values; do not script conversion or format checks. See [CLI Reference § Normalized output formats](cli-reference.md#normalized-output-formats).
   - **MISSING**: `FormattedValue` is empty **and** the field is genuinely absent. Both conditions are required. A non-empty wrong prediction is NOT CONFIRMED, never MISSING (Critical Rule 11).
   - **NOT CONFIRMED**: any mismatch, including wrong literal/source, garbled OCR, misread digit (page `£7,300.00` predicted as `£730.00`), hallucinated/absent value, wrong boolean, or wrong inferred/computed value. A magnitude difference is never type normalization (Rule 8). Leave every NOT CONFIRMED field unannotated (Critical Rule 8) and improve the prompt so IXP predicts it correctly. Report OCR errors (garbled characters, a misread digit) as data-quality issues; do not iterate prompts for them.

3. **Report your verdict for every field** in a table per document with predicted value, actual value/location where applicable, and reason:

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

For MISSING, state both the empty prediction and how absence was verified (e.g., "no payment-terms section anywhere in the document"). For NOT CONFIRMED, state the predicted value, visible actual value, and location; begin an OCR reason with `OCR:`.

Repeatable groups return one extraction per row with explicit 0-based `Occurrence` values. Match rows by field values, not index, because annotated rows reorder (see [Occurrence numbers are read-scoped](#occurrence-numbers-are-read-scoped)). Report differing rows per occurrence:

```text
Line Items > Description (occurrence 0) | CONFIRMED     | "Widget A" matches line 1
Line Items > Description (occurrence 1) | CONFIRMED     | "Widget B" matches line 2
Line Items > Description (occurrence 3) | NOT CONFIRMED | Predicted "Widget D" but line 4 shows "Widget Z"
```

4. **Build the submit list from the table:** all CONFIRMED and MISSING field IDs together; the CLI applies the correct semantic.

### 2d. Confirm

Submit all confirmed and missing fields for a document in one call. Add `-m <model_version>` (the `ModelVersion` from step 2a) to **every** `confirm` call, including narrowed `--occurrence`/`--updates-file` forms:

```bash
uip ixp labellings confirm <project-name> <document-id> \
  --fields "<confirmed_id_1>,<confirmed_id_2>,<missing_id>" -m <model_version> --output json
```

`--fields` combines CONFIRMED and MISSING IDs: predicted content is confirmed; empty prediction gets a missing marker. List MISSING only when IXP predicted nothing (Critical Rule 11); omit wrong non-empty predictions. If retraining causes `PredictionVersionChangedError`, rerun 2a, re-review, and confirm again.

After reviewing every predicted field and finding all correct, you can omit `--fields` to confirm every predicted field:

```bash
uip ixp labellings confirm <project-name> <document-id> -m <model_version> --output json
```

Never run `confirm` without `<document-id>`: that confirms every project document without review. Wrong labels can make F1 report `1.00`; F1 alone never proves correctness (Critical Rule 14).

Run `labellings mark-missing <project-name> <document-id> --fields <ids>` to mark genuinely missing fields directly, including a field with a prior annotation that the current prediction no longer includes and for which `confirm` no-ops. Use it only when `get-predictions` shows no value; never override a wrong prediction.

**Per-occurrence confirm for repeatable groups.** When verdicts differ by occurrence, do not use unscoped `confirm --fields a7c3e9105f2b4d86`: it confirms that field in every occurrence. Target correct occurrences:

```bash
# All predicted fields in occurrence 0:
uip ixp labellings confirm <project-name> <document-id> \
  --group "Line Items" --occurrence 0 -m <model_version> --output json

# Just Quantity in occurrence 2:
uip ixp labellings confirm <project-name> <document-id> \
  --group "Line Items" --occurrence 2 --fields c4e1907a3b8f25d6 -m <model_version> --output json
```

Untargeted occurrences retain existing annotations, so wrong untouched predictions remain unannotated. Confirm correct rows in one `--updates-file` call, not sequential `--occurrence` calls ([Occurrence numbers are read-scoped](#occurrence-numbers-are-read-scoped)):

```bash
cat > /tmp/ixp/<project-name>/payloads/confirm_updates.json << 'EOF'
[{"occurrence":0},{"occurrence":2,"fields":["c4e1907a3b8f25d6"]}]
EOF

uip ixp labellings confirm <project-name> <document-id> \
  --group "Line Items" --updates-file /tmp/ixp/<project-name>/payloads/confirm_updates.json \
  -m <model_version> \
  --output json
```

All indices in one call resolve against the same read. See [CLI Reference § Labellings](cli-reference.md#labellings) and Critical Rule 12.

**Per-occurrence unconfirm.** `unconfirm` accepts the same `--group`/`--occurrence`/`--updates-file` flags. Unscoped `unconfirm --fields a7c3e9105f2b4d86` removes that field from every occurrence; scope one with `--group "Line Items" --occurrence 2`, or several with `--group "Line Items" --updates-file <path>`. Without `--fields`, roll back every annotated field in targeted occurrences; with it, only those fields. See Critical Rule 13.

```bash
# Roll back only occurrence 2 of Line Items (every field in that line):
uip ixp labellings unconfirm <project-name> <document-id> \
  --group "Line Items" --occurrence 2 --output json
```

Take indices from a **fresh** `get-predictions`; on a partly confirmed group, a confirming index usually differs from its rollback index.

### 2e. Move to the next document

Repeat 2a–2d for every document in the list.

### Occurrence numbers are read-scoped

`get-predictions` lists annotated occurrences first, then unannotated ones. Confirming the third row of four therefore makes it `Occurrence` 0 and shifts the rest; the UI does the same. Values and page locations remain attached to rows. Only an entirely unannotated or entirely annotated group reads in document order.

An occurrence is valid only for its producing read, and any group write invalidates it:

- Put all occurrences to confirm/unconfirm in one `--updates-file` call.
- If sequential calls are unavoidable, rerun `get-predictions` between them and relocate each row by field values.
- Never reuse an index across a write; report rows by value, not "row 3".

### Removing a document from the project

Delete unusable (wrong type, corrupted, or duplicate) documents instead of confirming or skipping:

```bash
uip ixp documents delete <project-name> <document-id> -y --output json
```

`-y/--yes` is required; the CLI never prompts. Use the whole `DocumentId` from `documents list` (e.g., `3453547f3538febd.1fc885607f2aac621f8f2d3ef1847f22`), not AttachmentRef or Filename. Deletion is irreversible and triggers model retraining. Do not delete merely to skip labelling; leave such documents unconfirmed.

**Finding the DocumentId:**

| You have | How to get the DocumentId |
|----------|---------------------------|
| Filename (e.g., `invoice-001.pdf`) | `uip ixp documents list <project-name> --limit 10000 --output-filter "Documents[?Filename=='invoice-001.pdf'].DocumentId \| [0]" --output plain` (rows are under `Documents`; the list is paged, so `--output-filter` needs explicit `--limit`) |
| A distinctive predicted field value (e.g., Invoice Number `MSI0601020`) | Run `uip ixp documents list <project-name> --output json`, then run `uip ixp labellings get-predictions <project-name> <document-id> --output json` per ID until `Labels[].Fields[].FormattedValue` matches; stop at the first match. |
| Nothing — need to find by content | Run `uip ixp documents list <project-name> --output json`, download candidates with `documents download`, and read them with the Read tool. |

`documents list` returns `Filename` with `DocumentId` (original upload filename, or `null`). Non-unique filenames can yield multiple IDs; review them with `documents download` before deleting.

## Step 3 — Summary

Continue after errors; do not stop at the first error. If download fails, skip and note the document. If confirmation fails, log the error and document ID, then continue. Report:

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
