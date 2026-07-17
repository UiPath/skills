# Label Documents Guide

Reusable workflow for labelling documents in an IXP project. Used by:

- [Project Setup](project-setup-guide.md) — initial labelling after creating a project
- [Improve Prompts](improve-prompts-guide.md) — reviewing predictions during optimization

You act as a **reviewer** — IXP generates predictions, you validate them field-by-field against the document. Only fields that are correct get confirmed. Fields that are wrong are left unannotated. Fields where the prediction found the right location but the value is OCR-mangled get corrected.

## Step 1 — Get Documents and Taxonomy

```bash
mkdir -p /tmp/ixp/<project-name>/{docs,text,taxonomies,prompts}
uip ixp documents list <project-name> --output json
uip ixp projects get-taxonomy <project-name> --output json
```

Save the taxonomy to `/tmp/ixp/<project-name>/taxonomies/v1.json` (increment the version on each re-fetch).

From the taxonomy (raw snake_case: field groups/fields under `Data.dataset.label_groups`, types under `Data.dataset.entity_defs`), review the field groups and field types so you understand what each predicted field represents. Use the field type when judging equivalence: normalized output for a Monetary Quantity does not need to reproduce the page's literal formatting.

## Step 2 — Process Each Document

For each document from the list, process one at a time: get predictions, download image/text, review, confirm.

### 2a. Get predictions for this document

```bash
uip ixp labellings get-predictions <project-name> <document-id> --output json
```

This returns `Data: { ProjectName, TotalDocuments, DocumentsWithPredictions, Predictions[] }`. Each `Predictions[]` entry is `{ DocumentId, Labels[] }` (for a single-document call, `Predictions[0]`). Each label is `{ Name, Occurrence, Fields[] }`, and each field has `FieldId`, `FieldName`, `FormattedValue`. `Occurrence` is the explicit 0-based index used for `--occurrence`/`--updates`.

### 2b. Download the document file

- **If the file already exists** in `/tmp/ixp/<project-name>/docs/` from a previous session, reuse it — do NOT re-download.
- **Otherwise, download:**

```bash
uip ixp documents download <project-name> <document-id> -o /tmp/ixp/<project-name>/docs/<document-id> --output json
```

Use the document ID as the filename. Pass `-o` **without an extension** — the CLI detects the actual format (PDF, PNG, JPG, …) from the file content and appends the correct extension. Read the resolved `Path` from the response and use that for the next step. Files persist across sessions — check for existing files before downloading.

### 2c. Review predictions field-by-field

Use the **Read tool** to view the document file (read the whole document in one call, no `pages` parameter — a full Read returns text + image natively for digital and scanned PDF/PNG/JPG docs; no PDF tools to install), then review each predicted field against the document:

1. **Look at the document** to understand the layout and where field values appear.
2. **For each predicted field**, assign one of four verdicts:
   - **CONFIRMED** — the predicted value matches what is in the document, either literally or according to the field type's valid normalization. Minor OCR-level differences (capitalization, whitespace) are acceptable. For Monetary Quantity fields, equivalent precision, locale separators, currency placement, and canonical currency notation are acceptable when the numeric amount and currency are supported by the document.
   - **CORRECTED** — **OCR-mangled values only.** The prediction found the right field in the right location, the bytes-on-page are correct, but the text was garbled in transcription (e.g., `MSIÓÓÓ601020/` instead of `MSI0601020`, `lNGRAM` instead of `INGRAM`, or `1S.00 RON` instead of `15.00 RON`). The reference is correct, only the literal characters need fixing. Do NOT use CORRECTED to add/remove trailing zeros, separators, a currency code, or other valid normalized formatting. Do NOT use CORRECTED for booleans that came back with the wrong answer, inferred/computed values that came back wrong, or any case where IXP picked the wrong source on the page — those are NOT CONFIRMED.
   - **MISSING** — IXP predicted **no value** (empty `FormattedValue`) AND the field is genuinely absent from the document. Both conditions must hold. If IXP predicted a value but the field isn't actually in the document, that's NOT CONFIRMED, not MISSING — Critical Rule 12 forbids overriding a non-empty prediction with "missing".
   - **NOT CONFIRMED** — the prediction is wrong for any reason other than OCR mangling. Covers: wrong literal value on the right field, wrong-source extraction, hallucinated value, boolean came back with the wrong answer, inferred/computed value came back wrong, predicted a value the document doesn't contain. Left unannotated. Do NOT try to "fix" these with `--corrections` — `--corrections` is OCR-only (see Critical Rule 8). Improve the prompt instead.

#### Monetary Quantity decision test

Before using `--corrections` on a Monetary Quantity:

1. Parse the predicted numeric value and currency.
2. Parse the visible document value using the document's locale and currency evidence.
3. Normalize harmless representation differences: trailing zeros, thousands/decimal separators, currency placement, symbols/codes, and canonical currency names.
4. If the normalized amount and currency match, mark **CONFIRMED** and submit the prediction unchanged.
5. If the source characters were genuinely misread but the field and location are correct, mark **CORRECTED**.
6. If the amount, currency, or source row differs, mark **NOT CONFIRMED**.

Examples:

| Prediction | Document | Verdict | Reason |
|---|---|---|---|
| `15.00 RON` | `15 LEI` | CONFIRMED | Same amount and canonical currency; precision differs only in display. |
| `USD 15.00` | `$15` | CONFIRMED | Same amount and currency with different placement/notation. |
| `1,234.50 EUR` | `1.234,50 EUR` | CONFIRMED | Same value under the document's locale. |
| `1S.00 RON` | `15.00 RON` | CORRECTED | OCR confused `S` with `5` at the correct source location. |
| `15.00 USD` | `15.00 RON` | NOT CONFIRMED | Currency differs. |
| `15.00 RON` | `150.00 RON` | NOT CONFIRMED | Numeric amount differs. |
| `15.00 RON` | `15.00` with no currency evidence | NOT CONFIRMED | The prediction added an unsupported currency. |

3. **Report your verdict for every field.** Print a table per document:

```text
Document: <document-id>

Field                    | Verdict       | Reason
-------------------------|---------------|-----------------------------------------------
Invoice Number           | CORRECTED     | OCR mangled "MSIÓÓÓ601020/" → "MSI0601020", top-right of page 1
Invoice Date             | CONFIRMED     | Predicted "2018-02-28" matches document
Vendor Address           | NOT CONFIRMED | Predicted "123 Main St" but actual is "456 Oak Ave", top-left of page 1
Has Signature            | NOT CONFIRMED | Predicted "false" but signature visible bottom-right (boolean came back wrong — NOT CORRECTED)
Total After Tax          | NOT CONFIRMED | Predicted "$1100.00" but Subtotal+Tax = "$1210.00" (inferred value wrong — NOT CORRECTED)
Terms of Payment         | MISSING       | IXP predicted no value AND field not visible in document
Discount                 | MISSING       | IXP predicted no value AND no discount section on the page
Line Items > Description | CONFIRMED     | Predicted "Widget A" matches row 1 in the table
```

**Repeatable field groups produce one extraction per row.** `get-predictions` returns one label per row, each with an explicit 0-based `Occurrence` — `Line Items` on a multi-line invoice has N entries indexed 0..N-1 (read `Occurrence` directly; it equals document order). When validation differs across rows, give per-occurrence verdicts:

```text
Line Items > Description (occurrence 0) | CONFIRMED     | "Widget A" matches line 1
Line Items > Description (occurrence 1) | CONFIRMED     | "Widget B" matches line 2
Line Items > Description (occurrence 3) | NOT CONFIRMED | Predicted "Widget D" but line 4 shows "Widget Z"
```

For **CORRECTED** fields: state the mangled predicted value, the corrected value, and where it appears. The mistake must be at the character level — same field, same location, garbled bytes.
For **MISSING** fields: state that the prediction was empty AND describe how you verified the field is absent (e.g., "no payment-terms section anywhere in the document").
For **NOT CONFIRMED** fields: state the predicted value, the actual value (if visible) and location. Includes any non-OCR mistake — wrong source, wrong boolean, wrong inferred value, hallucination, value the document doesn't contain. **Do NOT use `--corrections` to fix these** — improve the field's prompt instructions instead.

4. **Build two lists from the table:**
   - **Submit field IDs** — all CONFIRMED + CORRECTED + MISSING fields (one combined list — the CLI applies the right semantic per field based on IXP's prediction)
   - **Corrections JSON** — only CORRECTED fields: `[{"field_id":"...","value":"corrected text"}]`

### 2d. Confirm and correct

Submit confirmed, corrected, and missing fields for this document — all in one `confirm` call.

**If there are corrections:**

```bash
uip ixp labellings confirm <project-name> <document-id> \
  --fields "<all_submitted_ids>" \
  --corrections '[{"field_id":"<id>","value":"<corrected_value>"}]' \
  --output json
```

The `--fields` list includes CONFIRMED, CORRECTED, and MISSING field IDs together — the CLI writes the right annotation per field based on IXP's prediction (content → confirm, content with override → correct, empty → missing marker). The `--corrections` JSON overrides the predicted value for corrected fields while keeping their document references (bounding boxes).

**If there are no corrections (all approved fields are exact matches):**

```bash
uip ixp labellings confirm <project-name> <document-id> \
  --fields "<field_id_1>,<field_id_2>,<field_id_3>" --output json
```

If ALL predicted fields for a document are correct with no corrections needed, you can omit `--fields` to confirm every predicted field on **that one document** in a single call:

```bash
uip ixp labellings confirm <project-name> <document-id> --output json
```

This per-document form is fine **once you've reviewed the document and every field is correct** (2c). What you must NOT do is run `confirm` **without a `<document-id>`** — that confirms every document in the project at once, bypassing the per-document review loop. Confirming unreviewed predictions bakes wrong values into the labels, and because F1 compares predictions against those labels, **the metric reports 1.00 even when the confirmed values are wrong**. F1 alone is never evidence the values are correct.

**If there are missing fields**, include their IDs in the same `--fields` list as the CONFIRMED and CORRECTED IDs. The `confirm` command applies one uniform rule per listed field: if IXP predicted content, the content is confirmed; if IXP predicted nothing, a missing marker is written. No separate call needed.

```bash
uip ixp labellings confirm <project-name> <document-id> \
  --fields "<confirmed_id>,<corrected_id>,<missing_id_1>,<missing_id_2>" \
  --corrections '[{"field_id":"<corrected_id>","value":"<corrected_value>"}]' \
  --output json
```

**Only include a field in the `--fields` list for the MISSING case when IXP itself predicted nothing for it** — see Critical Rule 12. If IXP predicted a wrong value, omit the field entirely (don't list it).

Use `labellings mark-missing <project-name> <document-id> --fields <ids>` to record a genuinely-missing field. It marks the listed fields directly, so it also handles the case where `confirm --fields` no-ops — a field with a prior annotation that the current prediction no longer includes (e.g., model behavior changed after a retrain), which `confirm` can't reach. Either records the missing marker; only do so when `get-predictions` shows IXP predicted no value for the field — never to override a wrong prediction.

**Per-occurrence confirm for repeatable groups.** When a repeatable group's verdicts differ across occurrences (some lines correct, some not), `confirm --fields a7c3e9105f2b4d86` is the wrong shape — it confirms `a7c3e9105f2b4d86` in **every** occurrence, including the wrong ones. Target each correct occurrence by index:

```bash
# All predicted fields in occurrence 0:
uip ixp labellings confirm <project-name> <document-id> \
  --group "Line Items" --occurrence 0 --output json

# Just Quantity in occurrence 2:
uip ixp labellings confirm <project-name> <document-id> \
  --group "Line Items" --occurrence 2 --fields c4e1907a3b8f25d6 --output json
```

Occurrences not targeted carry forward whatever annotation they already had (so wrong predictions in untouched occurrences stay unannotated). For batching many occurrences in one call, use `--updates '[…]'` — see [CLI Reference § Labellings](cli-reference.md#labellings). See Critical Rule 13.

**Per-occurrence unconfirm.** `unconfirm` takes the same `--group`/`--occurrence`/`--updates` flags, so a wrong confirmation can be rolled back at the same granularity. `unconfirm --fields a7c3e9105f2b4d86` (no `--group`) removes `a7c3e9105f2b4d86` from **every** occurrence; scope it to one line with `--group "Line Items" --occurrence 2`, or several at once with `--group "Line Items" --updates '[…]'`, using the same 0-based indices. Without `--fields`, every annotated field in the targeted occurrence(s) is rolled back; with `--fields`, only those. See Critical Rule 14.

```bash
# Roll back only occurrence 2 of Line Items (every field in that line):
uip ixp labellings unconfirm <project-name> <document-id> \
  --group "Line Items" --occurrence 2 --output json
```

### 2e. Move to the next document

Repeat steps 2a–2d for all documents in the list.

### Removing a document from the project

If a document is unusable (wrong document type, corrupted, duplicate), delete it instead of confirming or skipping:

```bash
uip ixp documents delete <project-name> <document-id> -y --output json
```

`-y/--yes` is required (the CLI never prompts). `<document-id>` is the `DocumentId` from `documents list` (e.g., `3453547f3538febd.1fc885607f2aac621f8f2d3ef1847f22`). Pass it whole. Do NOT pass the AttachmentRef or the Filename.

**Finding the DocumentId:**

| You have | How to get the DocumentId |
|----------|---------------------------|
| Filename (e.g., `invoice-001.pdf`) | `uip ixp documents list <project-name> --output json --output-filter "Documents[?Filename=='invoice-001.pdf'].DocumentId \| [0]" --output plain` (rows are under `Documents` — the list is a paged envelope) |
| A distinctive predicted field value (e.g., Invoice Number `MSI0601020`) | Run `uip ixp labellings get-predictions <project-name> --output json`, find the entry in `Predictions[]` whose `Labels[].Fields[].FormattedValue` matches, take its `DocumentId` |
| Nothing — need to find by content | `uip ixp documents list <project-name> --output json`, then `documents download` candidates and read with the Read tool |

`documents list` returns `Filename` alongside `DocumentId` (the original upload filename, or `null` if none was sent at upload time). When filenames aren't unique within the project, the JMESPath filter returns multiple IDs — review them with `documents download` before deleting.

Deletion is irreversible and triggers a model retrain. Do NOT use deletion to skip documents you simply don't want to label — leave those unconfirmed instead.

## Step 3 — Summary

After processing all documents, track progress and errors:

- Do NOT stop on the first error — continue with remaining documents
- If a download or text fetch fails, skip the document and note the failure
- If confirmation fails, log the error and UID, then continue

At the end, report a full summary:

```text
Labelling complete.

Documents: N processed, M confirmed, K skipped (no predictions)
Fields: X confirmed, Y corrected, W marked missing, Z not confirmed

OCR Corrections Applied:
  Doc <uid-1>: Invoice Number "MSIÓÓÓ601020/" → "MSI0601020"
  Doc <uid-1>: Vendor Name "INGRAM NTCRO INC" → "INGRAM MICRO INC"
  Doc <uid-3>: Bill-To Address "123 Mam St" → "123 Main St"

Marked Missing (IXP predicted empty AND field absent from document):
  Doc <uid-2>: Terms of Payment
  Doc <uid-4>: Discount

Not Confirmed (skipped):
  Doc <uid-3>: Total Amount — predicted "500.00" but actual is "5000.00" (bottom-right, page 1)
  Doc <uid-5>: Vendor Address — predicted "123 Main St" but actual is "456 Oak Ave"
```
