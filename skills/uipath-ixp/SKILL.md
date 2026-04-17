---
name: uipath-ixp
description: "UiPath IXP (Document Understanding) — extract fields from documents using uip ixp CLI, review/correct extractions with Claude, confirm labellings. For Orchestrator/deploy→uipath-platform."
---

# UiPath IXP Document Extraction Assistant

Skill for working with UiPath IXP (Intelligent eXtraction Platform) projects — creating projects, uploading documents, reviewing extractions, and confirming labellings using Claude as an extraction reviewer.

## When to Use This Skill

- User wants to **label documents in an IXP project** (this is the most common case — run the full labelling workflow automatically)
- User wants to **create an IXP project** and upload documents
- User wants to **list or inspect IXP projects**
- User asks about IXP extraction, taxonomy, or labellings
- User mentions `uip ixp` commands

## Critical Rules

1. **When the user asks to label a project, run the FULL labelling workflow automatically** — do NOT ask the user to do individual steps. Execute Steps 1-6 from the "Label an Existing Project" section below end-to-end.
2. **Always use `--output json`** when parsing CLI output programmatically
3. **Always use temp files for curl payloads** — never pass JSON inline with `-d '...'`. Write to a temp file first (`echo "$VAR" > /tmp/ixp_payload.json`) then use `-d @/tmp/ixp_payload.json`. Field values can contain quotes, newlines, and special characters that break shell expansion.
4. **Never use `UID` as a variable name** — it is a readonly shell variable. Use `DOC_UID`, `COMMENT_UID`, etc.
5. **Confirm labellings one document at a time** — each document needs its own extraction review and labelling confirmation
6. **Max 8 documents for taxonomy suggestion** — the suggest-taxonomy endpoint accepts at most 8 attachment references
7. **IXP projects require tenant admin** — the `project create` command will fail without admin access

## Available CLI Commands

### List IXP Projects

```bash
uip ixp project list --output json
```

### Get a Project

```bash
uip ixp project get <project-name> --output json
```

### Create a Project

Creates an IXP dataset, uploads all documents from a folder, suggests a taxonomy, and imports it.

```bash
uip ixp project create "<name>" <folder-path> --description "<what to extract>" --output json
```

The `Owner` and `Name` values from the output are needed for subsequent commands.

### Confirm IXP Predictions

Fetches IXP-generated predictions and confirms them as-is for all documents.

```bash
uip ixp labelling confirm <owner> <dataset-name> --output json
```

### Label a Single Document (Claude extractions)

Submit Claude-generated extractions for one document. This is the command the skill calls per document during the labelling workflow.

```bash
uip ixp labelling label <owner> <dataset-name> <comment-uid> \
  --extractions '[{"label":"Invoice > Details","fields":[{"field_id":"abc123","formatted_value":"INV-001"}]}]' \
  --output json
```

The `--extractions` flag takes a JSON array. Each entry has:
- `label` — the field group name (e.g. `"Invoice > Company Information"`)
- `fields[]` — array of `{ "field_id": "<hex id>", "formatted_value": "<extracted value>" }`

The command handles parent label injection, sentiment, spans, and dismissed format automatically.

## Label an Existing Project

**This is the primary workflow.** When the user asks to "label a project", run ALL of these steps automatically without asking.

### Setup — Read Auth and Build Base URL

```bash
source ~/.uipath/.auth
BASE="${UIPATH_URL}/${UIPATH_ORGANIZATION_ID}/${UIPATH_TENANT_NAME}/reinfer_/api"
```

All subsequent API calls use `Authorization: Bearer ${UIPATH_ACCESS_TOKEN}`.

### Step 1 — Find the Design Source

```bash
OWNER="<owner>"
DATASET="<dataset-name>"
DESIGN_SOURCE=$(curl -s -H "Authorization: Bearer ${UIPATH_ACCESS_TOKEN}" \
  "${BASE}/v1/sources/${OWNER}" | jq -r '.sources[] | select(._kind == "ixp_design") | .id')
```

### Step 2 — Get All Documents

```bash
cat > /tmp/ixp_query.json << EOF
{"filter": {"sources": ["${DESIGN_SOURCE}"]}, "order": {"kind": "recent"}, "limit": 50}
EOF
curl -s -X POST -H "Authorization: Bearer ${UIPATH_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  "${BASE}/_private/datasets/${OWNER}/${DATASET}/query" \
  -d @/tmp/ixp_query.json
```

Collect from the response:
- `results[].comment.uid` — the comment UID (use variable name `DOC_UID`, never `UID`)
- `results[].comment.attachments[0].attachment_reference` — for document retrieval

### Step 3 — Get the Taxonomy

Fetch the dataset to get the full taxonomy (entity_defs + label_groups):

```bash
curl -s -H "Authorization: Bearer ${UIPATH_ACCESS_TOKEN}" \
  "${BASE}/v1/datasets/${OWNER}/${DATASET}"
```

From the response, extract:
- `dataset.entity_defs[]` — each has `id` (hex), `name` (field type name), `title`, `trainable`
- `dataset.label_groups[]` — each has `name` (field group name), `label_defs[]` which contain:
  - `label_defs[].name` — the label/field group name (may be hierarchical like `"Invoice > Details"`)
  - `label_defs[].moon_form[]` — each entry has `kind` (matching an entity_def name) and `field_id`

The taxonomy maps label groups → labels → fields → entity_defs. For extraction:
- Each `label_def` with `moon_form` entries defines a field group to extract
- Each `moon_form` entry's `kind` tells you the field type name, and `field_id` is what you submit in the labelling
- The entity_def `name` matching `moon_form.kind` gives you the human-readable field name

If `GET /v1/datasets/...` returns 401, fall back to learning taxonomy from predictions:

```bash
curl -s -H "Authorization: Bearer ${UIPATH_ACCESS_TOKEN}" \
  "${BASE}/_private/datasets/${OWNER}/${DATASET}/labellings?id=<any_comment_uid>&compute_moon_predictions=true"
```

From `results[0].moon_forms[0].predicted`:
- `label.name` → field group name
- `captures[].fields[].field_id` → the hex field ID
- `captures[].fields[].name` → human-readable field name

### Step 4 — For Each Document: Read the Document

There are two modes. **Use DOM mode by default.** Only use Vision mode if the user explicitly asks for it (e.g. "use images", "use vision").

#### DOM Mode (default)

Fetch structured OCR selections (words with bounding polygons) for each page:

```bash
# Get page count
PAGE_COUNT=$(curl -s -H "Authorization: Bearer ${UIPATH_ACCESS_TOKEN}" \
  "${BASE}/_private/attachments/${ATTACHMENT_REF}/render" | jq '.page_metadata | length')

# Get selections for each page (0-indexed)
for i in $(seq 0 $((PAGE_COUNT - 1))); do
  curl -s -H "Authorization: Bearer ${UIPATH_ACCESS_TOKEN}" \
    "${BASE}/_private/attachments/${ATTACHMENT_REF}/selections/pages/${i}"
done
```

Each page returns `selections[]` where each selection has:
- `kind`: `"word"`
- `text`: the word text
- `polygon.vertices[]`: bounding box with `{x, y}` coordinates (normalized 0-1)
- `parent`: index of parent selection (for grouping words into lines/blocks)

Use the spatial layout to understand document structure:
- **Tables**: words at similar x coordinates form columns, similar y form rows
- **Key-value pairs**: label on the left, value on the right at similar y
- **Reading order**: sort by y then x to reconstruct natural reading order

#### Vision Mode (only when user explicitly requests images/vision)

Download page images and view them directly:

```bash
PAGE_COUNT=$(curl -s -H "Authorization: Bearer ${UIPATH_ACCESS_TOKEN}" \
  "${BASE}/_private/attachments/${ATTACHMENT_REF}/render" | jq '.page_metadata | length')

for i in $(seq 0 $((PAGE_COUNT - 1))); do
  curl -s -H "Authorization: Bearer ${UIPATH_ACCESS_TOKEN}" \
    "${BASE}/_private/attachments/${ATTACHMENT_REF}/thumbnail/pages/${i}" \
    -o "/tmp/ixp_page_${i}.png"
done
```

Then use the **Read tool** to view each image (`Read /tmp/ixp_page_0.png`, etc.).

### Step 5 — Extract Field Values

Using the document data from Step 4 and the taxonomy from Step 3, extract values for every field:
- Match labels to their values based on spatial proximity
- Read tables by tracking column alignment
- Parse amounts, dates, names in their natural format
- If a field is not found in the document, skip it (do NOT include it with empty value)

### Step 6 — Submit the Labelling

Write the extractions JSON to a temp file, then pass it to the CLI:

```bash
cat > /tmp/ixp_extractions.json << 'EXTRACTIONS_EOF'
[
  {
    "label": "Invoice > Company Information",
    "fields": [
      { "field_id": "e8a39a45177cdd72", "formatted_value": "Acme Corp" },
      { "field_id": "a2298dc0c3fa32d9", "formatted_value": "123 Main St" }
    ]
  }
]
EXTRACTIONS_EOF

uip ixp labelling label "${OWNER}" "${DATASET}" "${DOC_UID}" \
  --extractions "$(cat /tmp/ixp_extractions.json)" --output json
```

The command handles parent labels, sentiment, spans, and dismissed format automatically — just provide the label names, field IDs, and extracted values.

### Batch Loop Pattern

Process all documents by looping Steps 4-6. Track progress and errors:

```bash
SUCCEEDED=0
FAILED=0
TOTAL=<number of documents>

for each document (DOC_UID, ATTACHMENT_REF) from Step 2:
    # Step 4 — Read the document (DOM or Vision)
    # Step 5 — Extract field values
    # Step 6 — Submit labelling

    if labelling succeeded:
        SUCCEEDED=$((SUCCEEDED + 1))
    else:
        FAILED=$((FAILED + 1))
    fi

    echo "Progress: $((SUCCEEDED + FAILED))/${TOTAL} (${SUCCEEDED} ok, ${FAILED} failed)"
done

echo "Done: ${SUCCEEDED}/${TOTAL} labelled, ${FAILED} failed"
```

Do NOT stop on the first error — continue with the remaining documents and report the summary at the end.

## New Project Workflow

To create a fresh project, upload documents, and generate a taxonomy:

```bash
uip ixp project create "<name>" <folder-path> --description "<what to extract>" --output json
```

Then follow "Label an Existing Project" above using the Owner and Name from the output.

## Labelling JSON Format

The labelling POST body must follow this exact structure:

```json
{
  "moon_forms": [{
    "group": "default",
    "assigned": [
      {
        "label": { "name": "<field group name>", "sentiment": "positive" },
        "captures": [{
          "fields": [
            {
              "field_id": "<field_id>",
              "formatted_value": "<extracted value>",
              "spans": []
            }
          ]
        }]
      }
    ],
    "dismissed": { "captures": [] }
  }],
  "entities": { "assigned": [], "dismissed": [] }
}
```

### Format Rules (MUST follow — the API rejects invalid payloads)

1. **`sentiment`** must be the string `"positive"` — not a number
2. **`dismissed`** must be an object `{ "captures": [] }` — not an array `[]`
3. **`spans: []`** is required on every field — even when empty
4. **Parent labels are required** — hierarchical label `"Invoice > Details"` requires a separate entry for `"Invoice"` with empty captures:
   ```json
   { "label": { "name": "Invoice", "sentiment": "positive" }, "captures": [{ "fields": [] }] }
   ```
5. **Omit empty fields** — do NOT include fields with `formatted_value: ""`
6. **`group`** must be `"default"`

## API Endpoints Reference

| Action | Method | Endpoint |
|--------|--------|----------|
| List projects | GET | `/_private/projects` |
| Get project | GET | `/_private/projects/<name>` |
| Create IXP dataset | PUT | `/_private/ixp/datasets` |
| Get dataset (taxonomy) | GET | `/v1/datasets/<owner>/<dataset_name>` |
| List sources in project | GET | `/v1/sources/<owner>` |
| Upload document | PUT | `/_private/sources/id:<source_id>/documents` |
| Suggest taxonomy | POST | `/_private/ixp/projects/<owner>/<dataset>/suggest-taxonomy` |
| Import taxonomy | POST | `/_private/ixp/projects/<owner>/<dataset>/import-taxonomy` |
| Query comments | POST | `/_private/datasets/<owner>/<dataset>/query` |
| Get page metadata | GET | `/_private/attachments/<ref>/render` |
| Get page image | GET | `/_private/attachments/<ref>/thumbnail/pages/<index>` |
| Get OCR selections | GET | `/_private/attachments/<ref>/selections/pages/<index>` |
| Get labellings | GET | `/_private/datasets/<owner>/<dataset>/labellings?id=<uid>&compute_moon_predictions=true` |
| Confirm labelling | POST | `/_private/datasets/<owner>/<dataset>/labellings/<comment_uid>` |

## Reference Navigation

- [Labelling API details](references/labelling-guide.md)
