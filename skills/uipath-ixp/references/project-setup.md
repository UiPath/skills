# Project Setup Guide

Complete workflow for creating a new IXP project, labelling all documents, and getting initial metrics. Run all steps end-to-end automatically.

## Step 1 — Create the Project

```bash
mkdir -p /tmp/ixp
uip ixp project create "<name>" <folder-path> --description "<what to extract>" --output json
```

Use the `ProjectName` from the output for all subsequent commands. This is the lowercase slug with UUID and `-ixp` suffix (e.g., `cezara_invoices4-f1afa9ef-ixp`), NOT the Title.

## Step 2 — Get All Documents, Images, and OCR Text

List all documents and get the taxonomy:

```bash
uip ixp document list <project-name> --output json
uip ixp project taxonomy <project-name> --output json
```

Then, for **every document** in the list, get the image and OCR text:

- **If you just created the project in this same session** and already know the local file paths from the `project create` command, use those files directly — do NOT download or search for them.
- **Otherwise, always download** each document image:

```bash
uip ixp document get <project-name> <comment-uid> -o /tmp/ixp/doc_1.png --output json
```

Do NOT search the filesystem for document files. Either you already have the paths from project creation in this session, or you download them.

**Always fetch the OCR text** (it's not available locally — it comes from IXP's OCR engine):

```bash
uip ixp document text <project-name> <comment-uid> --output json
```

Store the OCR text for each document alongside its image path and UID. **Get ALL documents before starting extraction.**

From the taxonomy:

- Each `label_def` with `moon_form` entries defines a field group to extract
- Each `moon_form` entry's `field_id` is what you submit in the labelling
- The `label_def.name` (e.g., `"Invoice Details"`, `"Line Items"`) is the label you use in the extractions JSON — **use the flat name, NEVER prefix with parent names** like `"Invoice > Details"`
- Check each entity_def's `inherits_from` to identify typed fields (Date, Monetary Quantity) — these require specific value formats (see System Type Formats in the main skill)

## Step 3 — For Each Document: Extract Field Values

For each document, use the **Read tool** to view the image:

```
Read /tmp/ixp/doc_1.png
```

Then extract fields using this process:

1. **Look at the image** to understand the document layout and identify where each field's value appears visually.
2. **Find that same value in the OCR text.** The OCR text is a space-separated sequence of words — look for a contiguous substring that matches what you see in the image.
3. **Copy the value from the OCR text when it's accurate.** If the OCR is clearly garbled (e.g., `INGRAM NTCRO INC` instead of `INGRAM MICRO INC`), use the clean value from the image instead — the API does not enforce verbatim OCR.

**Rules:**

- Prefer OCR-verbatim values when they match the document
- If OCR is garbled, use the clean value you read from the image
- For **typed fields** (Date, Monetary Quantity), submit the value **as-written in the document** — same rule as all other fields. If the document says `02/28/2018`, submit `02/28/2018`. If it says `$17,000.00`, submit `$17,000.00`. The model predicts in the document's own format.
- If a field is not visible in the document, skip it (do NOT include it with empty value)

**Label rules:**

- Use the **flat `label_def.name`** from taxonomy as the `"label"` — never prefix with parent names
- **Non-repeating labels** (e.g., "Invoice Details") → one entry with all fields
- **Repeating/table labels** (e.g., "Line Items") → one entry per row, each with the same label name

## Step 4 — Submit the Labelling

```bash
cat > /tmp/ixp/extractions.json << 'EXTRACTIONS_EOF'
[
  {
    "label": "Invoice Details",
    "fields": [
      { "field_id": "dba783c9b74f805b", "formatted_value": "INV-001" },
      { "field_id": "98d17d6b0e8dadc8", "formatted_value": "2024-03-15" }
    ]
  },
  {
    "label": "Line Items",
    "fields": [
      { "field_id": "c573d9279a570e2d", "formatted_value": "Widget A" },
      { "field_id": "c7dcfaaaba8aa867", "formatted_value": "10" }
    ]
  },
  {
    "label": "Line Items",
    "fields": [
      { "field_id": "c573d9279a570e2d", "formatted_value": "Widget B" },
      { "field_id": "c7dcfaaaba8aa867", "formatted_value": "5" }
    ]
  }
]
EXTRACTIONS_EOF

uip ixp labelling label <project-name> <comment-uid> \
  --extractions "$(cat /tmp/ixp/extractions.json)" --output json
```

Submit labellings in **serial** — do not parallelize.

## Step 5 — Loop Steps 3-4 for All Documents

Process all documents. Track progress and errors:

- Do NOT stop on the first error — continue with remaining documents
- If `document get` or `document text` fails for a document, skip it and note the failure
- If `labelling label` fails, log the error and the document UID, then continue with the next document
- At the end, report a summary: how many succeeded, how many failed, and which UIDs failed

**Time estimate:** Budget ~15 seconds per document for downloads + ~5 seconds per submission.

## Step 6 — Show Metrics

After all documents are labelled, wait ~2 minutes for server-side retraining, then:

```bash
uip ixp project metrics <project-name> --output json
```

Check that `ModelVersion` has advanced. If not, wait another 60 seconds and retry — retraining can take longer on staging.

Report project score, quality rating, and per-field F1/precision/recall. Highlight:

- Fields with F1 < 0.5 that need prompt improvement
- Typed fields (Date, Monetary Quantity) at F1 = 0 — likely a format mismatch. Re-label using the value as-written in the document.

If the user wants to improve scores, follow the [Improve Prompts Guide](improve-prompts.md).
