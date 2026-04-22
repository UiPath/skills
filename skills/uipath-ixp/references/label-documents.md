# Label Documents Guide

Reusable workflow for labelling documents in an IXP project. Used by:
- [Project Setup](project-setup.md) — initial labelling after creating a project
- [Improve Prompts](improve-prompts.md) — labelling new/unlabelled documents during optimization

## Step 1 — Get Documents and Taxonomy

```bash
mkdir -p /tmp/ixp
uip ixp document list <project-name> --output json
uip ixp project taxonomy <project-name> --output json
```

From the taxonomy:

- Each `label_def` with `moon_form` entries defines a field group to extract
- Each `moon_form` entry's `field_id` is what you submit in the labelling
- The `label_def.name` (e.g., `"Invoice Details"`, `"Line Items"`) is the label you use in the extractions JSON — **use the flat name, NEVER prefix with parent names**
- Check each entity_def's `inherits_from` to identify typed fields — see Field Types in the main skill

## Step 2 — Download Images and OCR Text

For each document to label, get the image and OCR text:

- **If you just created the project in this same session** and already know the local file paths, use those files directly — do NOT download or search for them.
- **Otherwise, download** each document image:

```bash
uip ixp document get <project-name> <comment-uid> -o /tmp/ixp/doc_1.png --output json
```

Do NOT search the filesystem for document files. Either you already have the paths from project creation in this session, or you download them.

**Always fetch the OCR text:**

```bash
uip ixp document text <project-name> <comment-uid> --output json
```

Use unique filenames per document (e.g., `/tmp/ixp/doc_1.png`, `/tmp/ixp/doc_2.png`). Download ALL documents before starting extraction.

## Step 3 — Extract Field Values

For each document, use the **Read tool** to view the image, then extract fields:

1. **Look at the image** to understand the document layout and identify where each field's value appears visually.
2. **Find that same value in the OCR text.** The OCR text is a space-separated sequence of words — look for a contiguous substring that matches what you see in the image.
3. **Copy the value from the OCR text when it's accurate.** If the OCR is garbled, use the clean value from the image — the API does not enforce verbatim OCR.

**Rules:**

- Prefer OCR-verbatim values when they match the document
- If OCR is garbled, use the clean value from the image
- For typed fields (Date, Monetary Quantity), submit as-written in the document first. See Field Types in the main skill for fallback formats.
- If a field is not visible in the document, skip it (do NOT include it with empty value)

**Label rules:**

- Use the **flat `label_def.name`** from taxonomy — never prefix with parent names
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
      { "field_id": "98d17d6b0e8dadc8", "formatted_value": "03/15/2024" }
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
- If a download or text fetch fails, skip the document and note the failure
- If labelling submission fails, log the error and UID, then continue
- At the end, report a summary: how many succeeded, how many failed, and which UIDs failed
