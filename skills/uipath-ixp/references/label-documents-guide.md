# Label Documents Guide

Reusable workflow for labelling documents in an IXP project. Used by:

- [Project Setup](project-setup-guide.md) — initial labelling after creating a project
- [Improve Prompts](improve-prompts-guide.md) — reviewing predictions during optimization

Claude acts as a **reviewer** — IXP generates predictions, Claude validates them field-by-field against the document. Only fields that are correct get confirmed. Fields that are wrong are left unannotated. Fields where the prediction found the right location but the value is OCR-mangled get corrected.

## Step 1 — Get Documents and Taxonomy

```bash
mkdir -p /tmp/ixp/<project-name>/{docs,text,taxonomies,prompts}
uip ixp document list <project-name> --output json
uip ixp project taxonomy <project-name> --output json
```

Save the taxonomy to `/tmp/ixp/<project-name>/taxonomies/v1.json` (increment the version on each re-fetch).

From the taxonomy, review the field groups and field types so you understand what each predicted field represents.

## Step 2 — Process Each Document

For each document from the list, process one at a time: get predictions, download image/text, review, confirm.

### 2a. Get predictions for this document

```bash
uip ixp labelling predictions <project-name> <document-id> --output json
```

This returns the document's predicted `Labels` (grouped by field group name), each containing `Fields` with `FieldId`, `FieldName`, and `FormattedValue`.

### 2b. Download image and OCR text

- **If files already exist** in `/tmp/ixp/<project-name>/docs/` from a previous session, reuse them — do NOT re-download.
- **Otherwise, download** the document image and OCR text:

```bash
uip ixp document image <project-name> <document-id> -o /tmp/ixp/<project-name>/docs/<document-id>.png --output json
uip ixp document text <project-name> <document-id> -o /tmp/ixp/<project-name>/text/<document-id>.txt --output json
```

Use the document ID as the filename — it's unique and lets you match files to documents without tracking a counter. These files persist across sessions — check for existing files before downloading.

### 2c. Review predictions field-by-field

Use the **Read tool** to view the image, then review each predicted field against the document:

1. **Look at the image** to understand the document layout and where field values appear.
2. **For each predicted field**, assign one of three verdicts:
   - **CONFIRMED** — the predicted value matches what is in the document. Minor OCR-level differences (capitalization, whitespace) are acceptable.
   - **CORRECTED** — the prediction found the right field in the right location, but the value is OCR-mangled (e.g., `MSIÓÓÓ601020/` instead of `MSI0601020`). The reference is correct but the text needs fixing.
   - **NOT CONFIRMED** — the predicted value is wrong, the field is misassigned, or the field is not visible in the document. Left unannotated.
3. **Report your verdict for every field.** Print a table per document:

```text
Document: <document-id>

Field                    | Verdict       | Reason
-------------------------|---------------|-----------------------------------------------
Invoice Number           | CORRECTED     | OCR mangled "MSIÓÓÓ601020/" → "MSI0601020", top-right of page 1
Invoice Date             | CONFIRMED     | Predicted "2018-02-28" matches document
Vendor Address           | NOT CONFIRMED | Predicted "123 Main St" but actual is "456 Oak Ave", top-left of page 1
Terms of Payment         | NOT CONFIRMED | Field not visible in document, prediction appears hallucinated
Line Items > Description | CONFIRMED     | Predicted "Widget A" matches row 1 in the table
```

For **CORRECTED** fields: state the mangled predicted value, the corrected value, and where it appears.
For **NOT CONFIRMED** fields: state the predicted value, the actual value (if visible) and location, or that the field is not visible.

4. **Build two lists from the table:**
   - **Confirmed field IDs** — all CONFIRMED + CORRECTED fields
   - **Corrections JSON** — only CORRECTED fields: `[{"field_id":"...","value":"corrected text"}]`

### 2d. Confirm and correct

Submit confirmed and corrected fields for this document.

**If there are corrections:**

```bash
uip ixp labelling confirm <project-name> <document-id> \
  --fields "<all_confirmed_and_corrected_ids>" \
  --corrections '[{"field_id":"<id>","value":"<corrected_value>"}]' \
  --output json
```

The `--fields` list includes both CONFIRMED and CORRECTED field IDs. The `--corrections` JSON overrides the predicted value for corrected fields while keeping their document references (bounding boxes).

**If there are no corrections (all approved fields are exact matches):**

```bash
uip ixp labelling confirm <project-name> <document-id> \
  --fields "<field_id_1>,<field_id_2>,<field_id_3>" --output json
```

If ALL predicted fields for a document are correct with no corrections needed, you can omit `--fields` to confirm everything:

```bash
uip ixp labelling confirm <project-name> <document-id> --output json
```

### 2e. Move to the next document

Repeat steps 2a–2d for all documents in the list.

## Step 3 — Summary

After processing all documents, track progress and errors:

- Do NOT stop on the first error — continue with remaining documents
- If a download or text fetch fails, skip the document and note the failure
- If confirmation fails, log the error and UID, then continue

At the end, report a full summary:

```text
Labelling complete.

Documents: N processed, M confirmed, K skipped (no predictions)
Fields: X confirmed, Y corrected, Z not confirmed

OCR Corrections Applied:
  Doc <uid-1>: Invoice Number "MSIÓÓÓ601020/" → "MSI0601020"
  Doc <uid-1>: Vendor Name "INGRAM NTCRO INC" → "INGRAM MICRO INC"
  Doc <uid-3>: Bill-To Address "123 Mam St" → "123 Main St"

Not Confirmed (skipped):
  Doc <uid-2>: Terms of Payment — field not visible in document
  Doc <uid-3>: Total Amount — predicted "500.00" but actual is "5000.00" (bottom-right, page 1)
```
