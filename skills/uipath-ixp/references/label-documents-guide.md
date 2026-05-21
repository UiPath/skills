# Label Documents Guide

Reusable workflow for labelling documents in an IXP project. Used by:

- [Project Setup](project-setup-guide.md) — initial labelling after creating a project
- [Improve Prompts](improve-prompts-guide.md) — reviewing predictions during optimization

Claude acts as a **reviewer** — IXP generates predictions, Claude validates them field-by-field against the document. Only fields that are correct get confirmed. Fields that are wrong are left unannotated. Fields where the prediction found the right location but the value is OCR-mangled get corrected.

## Step 1 — Get Documents and Taxonomy

```bash
mkdir -p /tmp/ixp/<project-name>/{docs,text,taxonomies,prompts}
uip ixp documents list <project-name> --output json
uip ixp projects get-taxonomy <project-name> --output json
```

Save the taxonomy to `/tmp/ixp/<project-name>/taxonomies/v1.json` (increment the version on each re-fetch).

From the taxonomy, review the field groups and field types so you understand what each predicted field represents.

## Step 2 — Process Each Document

For each document from the list, process one at a time: get predictions, download image/text, review, confirm.

### 2a. Get predictions for this document

```bash
uip ixp labellings get-predictions <project-name> <document-id> --output json
```

This returns the document's predicted `Labels` (grouped by field group name), each containing `Fields` with `FieldId`, `FieldName`, and `FormattedValue`.

### 2b. Download the document file

- **If the file already exists** in `/tmp/ixp/<project-name>/docs/` from a previous session, reuse it — do NOT re-download.
- **Otherwise, download:**

```bash
uip ixp documents download <project-name> <document-id> -o /tmp/ixp/<project-name>/docs/<document-id> --output json
```

Use the document ID as the filename. Pass `-o` **without an extension** — the CLI detects the actual format (PDF, PNG, JPG, …) from the file content and appends the correct extension. Read the resolved `Path` from the response and use that for the next step. Files persist across sessions — check for existing files before downloading.

### 2c. Review predictions field-by-field

Use the **Read tool** to view the document file (the Read tool handles PDF, PNG, JPG, etc. natively), then review each predicted field against the document:

1. **Look at the document** to understand the layout and where field values appear.
2. **For each predicted field**, assign one of four verdicts:
   - **CONFIRMED** — the predicted value matches what is in the document. Minor OCR-level differences (capitalization, whitespace) are acceptable.
   - **CORRECTED** — the prediction found the right field in the right location, but the value is OCR-mangled (e.g., `MSIÓÓÓ601020/` instead of `MSI0601020`). The reference is correct but the text needs fixing.
   - **MISSING** — IXP predicted **no value** (empty `FormattedValue`) AND the field is genuinely absent from the document. Both conditions must hold. If IXP predicted a value but the field isn't actually in the document, that's NOT CONFIRMED, not MISSING — Critical Rule 12 forbids overriding a non-empty prediction with "missing".
   - **NOT CONFIRMED** — the predicted value is wrong, the field is misassigned, or IXP predicted a value the document doesn't contain. Left unannotated.
3. **Report your verdict for every field.** Print a table per document:

```text
Document: <document-id>

Field                    | Verdict       | Reason
-------------------------|---------------|-----------------------------------------------
Invoice Number           | CORRECTED     | OCR mangled "MSIÓÓÓ601020/" → "MSI0601020", top-right of page 1
Invoice Date             | CONFIRMED     | Predicted "2018-02-28" matches document
Vendor Address           | NOT CONFIRMED | Predicted "123 Main St" but actual is "456 Oak Ave", top-left of page 1
Terms of Payment         | MISSING       | IXP predicted no value AND field not visible in document
Discount                 | MISSING       | IXP predicted no value AND no discount section on the page
Line Items > Description | CONFIRMED     | Predicted "Widget A" matches row 1 in the table
```

For **CORRECTED** fields: state the mangled predicted value, the corrected value, and where it appears.
For **MISSING** fields: state that the prediction was empty AND describe how you verified the field is absent (e.g., "no payment-terms section anywhere in the document").
For **NOT CONFIRMED** fields: state the predicted value, the actual value (if visible) and location, or that IXP predicted something the document doesn't contain.

4. **Build three lists from the table:**
   - **Confirmed field IDs** — all CONFIRMED + CORRECTED fields
   - **Corrections JSON** — only CORRECTED fields: `[{"field_id":"...","value":"corrected text"}]`
   - **Missing field IDs** — all MISSING fields

### 2d. Confirm and correct

Submit confirmed and corrected fields for this document.

**If there are corrections:**

```bash
uip ixp labellings confirm <project-name> <document-id> \
  --fields "<all_confirmed_and_corrected_ids>" \
  --corrections '[{"field_id":"<id>","value":"<corrected_value>"}]' \
  --output json
```

The `--fields` list includes both CONFIRMED and CORRECTED field IDs. The `--corrections` JSON overrides the predicted value for corrected fields while keeping their document references (bounding boxes).

**If there are no corrections (all approved fields are exact matches):**

```bash
uip ixp labellings confirm <project-name> <document-id> \
  --fields "<field_id_1>,<field_id_2>,<field_id_3>" --output json
```

If ALL predicted fields for a document are correct with no corrections needed, you can omit `--fields` to confirm everything:

```bash
uip ixp labellings confirm <project-name> <document-id> --output json
```

**If there are missing fields**, submit them AFTER the `confirm` call above:

```bash
uip ixp labellings mark-missing <project-name> <document-id> \
  --fields "<missing_field_id_1>,<missing_field_id_2>" --output json
```

Order matters: `confirm` runs first (it doesn't carry empty annotations forward), then `mark-missing` writes the empty markers while carrying the just-confirmed annotations forward. If you have no MISSING fields, skip this call.

### 2e. Move to the next document

Repeat steps 2a–2d for all documents in the list.

### Removing a document from the project

If a document is unusable (wrong document type, corrupted, duplicate), delete it instead of confirming or skipping:

```bash
uip ixp documents delete <project-name> <document-id> --output json
```

`<document-id>` is the `DocumentId` from `documents list` (e.g., `3453547f3538febd.1fc885607f2aac621f8f2d3ef1847f22`). Pass it whole. Do NOT pass the AttachmentRef or the Filename.

**Finding the DocumentId:**

| You have | How to get the DocumentId |
|----------|---------------------------|
| Filename (e.g., `invoice-001.pdf`) | `uip ixp documents list <project-name> --output json --output-filter "[?Filename=='invoice-001.pdf'].DocumentId \| [0]" --output plain` |
| A distinctive predicted field value (e.g., Invoice Number `MSI0601020`) | Run `uip ixp labellings get-predictions <project-name> --output json`, find the document whose `Labels[].Fields[].FormattedValue` matches, take its `DocumentId` |
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
