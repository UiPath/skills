# Label Documents Guide

Reusable workflow for labelling documents in an IXP project. Used by:

- [Project Setup](project-setup.md) — initial labelling after creating a project
- [Improve Prompts](improve-prompts.md) — reviewing predictions during optimization

Claude acts as a **reviewer** — IXP generates predictions, Claude validates them field-by-field against the document. Only fields that are correct get confirmed. Fields that are wrong are left unannotated.

## Step 1 — Get Documents and Taxonomy

```bash
mkdir -p /tmp/ixp/docs /tmp/ixp/text /tmp/ixp/taxonomies /tmp/ixp/prompts
uip ixp document list <project-name> --output json
uip ixp project taxonomy <project-name> --output json
```

Save the taxonomy to `/tmp/ixp/taxonomies/v1.json` (increment the version on each re-fetch).

From the taxonomy, review the field groups and field types so you understand what each predicted field represents.

## Step 2 — Get Predictions

Fetch IXP's model predictions for all documents:

```bash
uip ixp labelling predictions <project-name> --output json
```

This returns each document's `CommentUid` with predicted `Labels` (grouped by field group name), each containing `Fields` with `FieldId`, `FieldName`, and `FormattedValue`.

## Step 3 — Download Images and OCR Text

For each document that has predictions, get the image and OCR text:

- **If you just created the project in this same session** and already know the local file paths, use those files directly — do NOT download or search for them.
- **Otherwise, download** each document image:

```bash
uip ixp document get <project-name> <comment-uid> -o /tmp/ixp/docs/doc_1.png --output json
```

Do NOT search the filesystem for document files. Either you already have the paths from project creation in this session, or you download them.

**Always fetch the OCR text:**

```bash
uip ixp document text <project-name> <comment-uid> --output json
```

Save OCR output to `/tmp/ixp/text/doc_1.json`. Use unique filenames per document (e.g., `doc_1`, `doc_2`). Download ALL documents before starting review. These files are reused across steps — do not re-download.

## Step 4 — Review Predictions Field-by-Field

For each document, use the **Read tool** to view the image, then review each predicted field against the document:

1. **Look at the image** to understand the document layout and where field values appear.
2. **For each predicted field**, check:
   - Does the predicted value match what is actually written in the document?
   - Is the value assigned to the correct field? (e.g., an invoice number is not in a date field)
   - Minor OCR-level differences (capitalization, whitespace) are acceptable — the value is correct if it identifies the right content
3. **Build a list of approved field IDs** — the `FieldId` values for fields whose predictions are correct.
4. **Skip fields whose predictions are wrong** — wrong value, missing value, or misassigned field. Do NOT attempt to correct them manually.

## Step 5 — Confirm Approved Fields

For each document, confirm only the fields that passed review:

```bash
uip ixp labelling confirm <project-name> <comment-uid> \
  --fields "<field_id_1>,<field_id_2>,<field_id_3>" --output json
```

Pass the comma-separated list of approved `FieldId` values. Only those fields are labelled. Unapproved fields are left unannotated.

If ALL predicted fields for a document are correct, you can omit `--fields` to confirm everything:

```bash
uip ixp labelling confirm <project-name> <comment-uid> --output json
```

Submit confirmations in **serial** — do not parallelize.

## Step 6 — Loop Steps 4-5 for All Documents

Process all documents with predictions. Track progress and errors:

- Do NOT stop on the first error — continue with remaining documents
- If a download or text fetch fails, skip the document and note the failure
- If confirmation fails, log the error and UID, then continue
- At the end, report a summary: how many documents processed, how many fields confirmed vs skipped, and which UIDs failed
