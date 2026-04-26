# Label Documents Guide

Reusable workflow for labelling documents in an IXP project. Used by:

- [Project Setup](project-setup.md) — initial labelling after creating a project
- [Improve Prompts](improve-prompts.md) — reviewing predictions during optimization

Claude acts as a **reviewer** — IXP generates predictions, Claude validates them field-by-field against the document. Only fields that are correct get confirmed. Fields that are wrong are left unannotated. Fields where the prediction found the right location but the value is OCR-mangled get corrected.

## Step 1 — Get Documents and Taxonomy

```bash
mkdir -p /tmp/ixp/<project-name>/{docs,text,taxonomies,prompts}
uip ixp document list <project-name> --output json
uip ixp project taxonomy <project-name> --output json
```

Save the taxonomy to `/tmp/ixp/<project-name>/taxonomies/v1.json` (increment the version on each re-fetch).

From the taxonomy, review the field groups and field types so you understand what each predicted field represents.

## Step 2 — Get Predictions

Fetch IXP's model predictions for all documents:

```bash
uip ixp labelling predictions <project-name> --output json
```

This returns each document's `CommentUid` with predicted `Labels` (grouped by field group name), each containing `Fields` with `FieldId`, `FieldName`, and `FormattedValue`.

## Step 3 — Download Images and OCR Text

For each document that has predictions, get the image and OCR text:

- **If files already exist** in `/tmp/ixp/<project-name>/docs/` from a previous session, reuse them — do NOT re-download.
- **Otherwise, download** each document image:

```bash
uip ixp document get <project-name> <comment-uid> -o /tmp/ixp/<project-name>/docs/doc_1.png --output json
```

**Always fetch the OCR text** (unless already saved from a previous session):

```bash
uip ixp document text <project-name> <comment-uid> --output json
```

Save OCR output to `/tmp/ixp/<project-name>/text/doc_1.json`. Use unique filenames per document (e.g., `doc_1`, `doc_2`). These files persist across sessions — check for existing files before downloading.

## Step 4 — Review Predictions Field-by-Field

For each document, use the **Read tool** to view the image, then review each predicted field against the document:

1. **Look at the image** to understand the document layout and where field values appear.
2. **For each predicted field**, assign one of three verdicts:
   - **CONFIRMED** — the predicted value matches what is in the document. Minor OCR-level differences (capitalization, whitespace) are acceptable.
   - **CORRECTED** — the prediction found the right field in the right location, but the value is OCR-mangled (e.g., `MSIÓÓÓ601020/` instead of `MSI0601020`). The reference is correct but the text needs fixing.
   - **NOT CONFIRMED** — the predicted value is wrong, the field is misassigned, or the field is not visible in the document. Left unannotated.
3. **Report your verdict for every field.** Print a table per document:

```text
Document: <comment-uid>

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

## Step 5 — Confirm and Correct

For each document, submit confirmed and corrected fields together.

**If there are corrections:**

```bash
uip ixp labelling confirm <project-name> <comment-uid> \
  --fields "<all_confirmed_and_corrected_ids>" \
  --corrections '[{"field_id":"<id>","value":"<corrected_value>"}]' \
  --output json
```

The `--fields` list includes both CONFIRMED and CORRECTED field IDs. The `--corrections` JSON overrides the predicted value for corrected fields while keeping their document references (bounding boxes).

**If there are no corrections (all approved fields are exact matches):**

```bash
uip ixp labelling confirm <project-name> <comment-uid> \
  --fields "<field_id_1>,<field_id_2>,<field_id_3>" --output json
```

If ALL predicted fields for a document are correct with no corrections needed, you can omit `--fields` to confirm everything:

```bash
uip ixp labelling confirm <project-name> <comment-uid> --output json
```

Submit confirmations in **serial** — do not parallelize.

## Step 6 — Loop Steps 4-5 for All Documents

Process all documents with predictions. Track progress and errors:

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
