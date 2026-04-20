---
name: uipath-ixp
description: "UiPath IXP (Document Understanding) — extract fields from documents using uip ixp CLI, review/correct extractions with Claude, confirm labellings. For Orchestrator/deploy→uipath-platform."
---

# UiPath IXP Document Extraction Assistant

Skill for working with UiPath IXP (Intelligent eXtraction Platform) projects — creating projects, uploading documents, reviewing extractions, and confirming labellings using Claude as an extraction reviewer.

## When to Use This Skill

- User wants to **label documents in an IXP project** (this is the most common case — run the full labelling workflow automatically)
- User wants to **improve extraction scores / prompts** for an IXP project
- User wants to **create an IXP project** and upload documents
- User wants to **list or inspect IXP projects**
- User asks about IXP extraction, taxonomy, or labellings
- User mentions `uip ixp` commands

## Critical Rules

1. **ONLY use `uip ixp` CLI commands as documented in this skill** — do NOT use curl, do NOT source `~/.uipath/.auth`, do NOT load auth tokens, do NOT call REST APIs directly, do NOT grep/read source code, do NOT explore the codebase, do NOT run `--help` to discover options. All commands, flags, and their usage are fully documented below.
2. **When the user asks to label a project, run the FULL labelling workflow automatically** — do NOT ask the user to do individual steps. Execute Steps 1-6 from the "Label an Existing Project" section below end-to-end.
3. **When the user asks to improve scores/prompts, run the FULL improve workflow automatically** — execute Steps 1-6 from the "Improve Extraction Prompts" section end-to-end.
4. **Always use `--output json`** when parsing CLI output programmatically
5. **Always use temp files for JSON payloads** — when passing JSON to `--extractions` or `--entity-defs`, write to a temp file first (`cat > /tmp/ixp_payload.json << 'EOF' ... EOF`) then use `"$(cat /tmp/ixp_payload.json)"`. Field values can contain quotes, newlines, and special characters that break shell expansion.
6. **Never use `UID` as a variable name** — it is a readonly shell variable. Use `DOC_UID`, `COMMENT_UID`, etc.
7. **Confirm labellings one document at a time** — each document needs its own extraction review and labelling confirmation
8. **Max 8 documents for taxonomy suggestion** — the suggest-taxonomy endpoint accepts at most 8 attachment references
9. **IXP projects require tenant admin** — the `project create` command will fail without admin access

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

### Get Taxonomy

```bash
uip ixp project taxonomy <owner> <dataset-name> --output json
```

Returns `EntityDefs` (with `id`, `name`, `title`, `trainable`, `instructions`) and `LabelGroups`.

### Get Metrics

```bash
uip ixp project metrics <owner> <dataset-name> --output json
```

Returns `ProjectScore`, `ProjectScoreQuality`, and per-field-group `F1`, `Precision`, `Recall`, `ErrorRate`, `Documents`.

### Update Prompts / Instructions

Updates extraction instructions on entity_defs. The `--entity-defs` flag takes a JSON array of ALL entity_defs (not just changed ones — omitting one may delete it). Each entry must have `id`, `name`, `title`, `inherits_from`, `trainable`, and the new `instructions`.

```bash
uip ixp project update-prompts <owner> <dataset-name> \
  --entity-defs '<json array of all entity_defs>' \
  --label-instructions '<optional top-level instructions>' \
  --output json
```

Flags:
- `-e, --entity-defs <json>` (required) — JSON array of entity_defs with updated instructions
- `-i, --label-instructions <text>` (optional) — default label group instructions
- `-t, --tenant <tenant-name>` (optional)

### List Documents

```bash
uip ixp document list <owner> <dataset-name> --output json
```

Returns `[{ Uid, AttachmentRef }]` for each document.

### Get Document Text (OCR)

```bash
uip ixp document text <attachment-ref> --output json
```

### Get Document Selections (OCR words with bounding polygons)

```bash
uip ixp document pages <attachment-ref> --output json
uip ixp document selections <attachment-ref> --page <n> --output json
```

### Download Document Page Image

```bash
uip ixp document image <attachment-ref> --page <n> --output /tmp/ixp_page.png --output json
```

Then use the **Read tool** to view the image.

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

### Step 1 — Get All Documents

```bash
uip ixp document list <owner> <dataset-name> --output json
```

Returns a list of `{ Uid, AttachmentRef }` for each document.

### Step 2 — Get the Taxonomy

```bash
uip ixp project taxonomy <owner> <dataset-name> --output json
```

Returns `EntityDefs` and `LabelGroups`. From these:
- Each `label_def` with `moon_form` entries defines a field group to extract
- Each `moon_form` entry's `kind` tells you the field type name, and `field_id` is what you submit in the labelling
- The entity_def `name` matching `moon_form.kind` gives you the human-readable field name

### Step 3 — For Each Document: Read the Document

There are two modes. **Use DOM mode by default.** Only use Vision mode if the user explicitly asks for it (e.g. "use images", "use vision").

#### DOM Mode (default)

Get OCR selections (words with bounding polygons) for each page:

```bash
# Get page count
uip ixp document pages <attachment-ref> --output json

# Get selections for a page (0-based index)
uip ixp document selections <attachment-ref> --page 0 --output json
```

Each selection has:
- `kind`: `"word"`
- `text`: the word text
- `polygon.vertices[]`: bounding box with `{x, y}` coordinates (normalized 0-1)

Use the spatial layout to understand document structure:
- **Tables**: words at similar x coordinates form columns, similar y form rows
- **Key-value pairs**: label on the left, value on the right at similar y
- **Reading order**: sort by y then x to reconstruct natural reading order

Or get the full text directly:

```bash
uip ixp document text <attachment-ref> --output json
```

#### Vision Mode (only when user explicitly requests images/vision)

Download page images and view them:

```bash
uip ixp document image <attachment-ref> --page 0 --output /tmp/ixp_page_0.png --output json
```

Then use the **Read tool** to view each image (`Read /tmp/ixp_page_0.png`, etc.).

### Step 4 — Extract Field Values

Using the document data from Step 3 and the taxonomy from Step 2, extract values for every field:
- Match labels to their values based on spatial proximity
- Read tables by tracking column alignment
- Parse amounts, dates, names in their natural format
- If a field is not found in the document, skip it (do NOT include it with empty value)

### Step 5 — Submit the Labelling

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

uip ixp labelling label <owner> <dataset-name> <comment-uid> \
  --extractions "$(cat /tmp/ixp_extractions.json)" --output json
```

### Batch Loop Pattern

Process all documents by looping Steps 3-5. Track progress and errors. Do NOT stop on the first error — continue with remaining documents and report the summary at the end.

### Step 6 — Show Metrics

After all documents are labelled:

```bash
uip ixp project metrics <owner> <dataset-name> --output json
```

Report project score, quality rating, and per-field-group F1/precision/recall. Highlight any fields with low F1 scores (< 0.5).

## Improve Extraction Prompts

**When the user asks to improve scores/prompts, run this workflow automatically.** This reads the current metrics and taxonomy, identifies weak fields, writes better instructions, and updates them.

### Step 1 — Get Current Metrics

```bash
uip ixp project metrics <owner> <dataset-name> --output json
```

Use the **actual F1 scores from the API** — do NOT calculate F1 manually. Identify field groups with F1 < 0.7 as targets for improvement.

### Step 2 — Get Current Taxonomy with Instructions

```bash
uip ixp project taxonomy <owner> <dataset-name> --output json
```

From the response, find the `EntityDefs` with their current `instructions`. Note which entity_defs correspond to the low-scoring field groups (match via `moon_form[].kind` → entity_def `name`).

### Step 3 — Read Sample Documents

Pick 2-3 documents and read them (DOM or Vision, per Step 3 of the labelling workflow):

```bash
uip ixp document list <owner> <dataset-name> --output json
uip ixp document text <attachment-ref> --output json
```

This gives Claude context about what the actual documents look like, so it can write better instructions.

### Step 4 — Write Improved Instructions

For each low-scoring entity_def, write a better `instructions` string. Good instructions should:
- **Be specific about what the field contains** — e.g. "The invoice number, typically formatted as INV-XXXX or #XXXX, found near the top of the document"
- **Describe where to find it** — e.g. "Usually in the top-right corner, near the date"
- **Include format examples** — e.g. "Dates should be in MM/DD/YYYY format"
- **Clarify ambiguous cases** — e.g. "If multiple addresses are present, use the billing address, not the shipping address"
- **Mention what it is NOT** — e.g. "Do not confuse with the PO number, which starts with PO-"

Also update `_default_label_group_instructions` with general guidance about the document type.

### Step 5 — Update the Dataset

Write the entity_defs JSON to a temp file and pass it to the CLI:

```bash
cat > /tmp/ixp_entity_defs.json << 'ENTITY_DEFS_EOF'
[
  {
    "id": "<existing_entity_def_id>",
    "name": "<existing_name>",
    "title": "<existing_title>",
    "inherits_from": [],
    "trainable": true,
    "instructions": "<new improved instructions>"
  }
]
ENTITY_DEFS_EOF

uip ixp project update-prompts <owner> <dataset-name> \
  --entity-defs "$(cat /tmp/ixp_entity_defs.json)" \
  --label-instructions "<new top-level instructions>" \
  --output json
```

> **Important:** Include ALL entity_defs in the update (not just changed ones), preserving existing `id`, `name`, `title`, `trainable`, and `inherits_from` values. Only change the `instructions` field. Omitting an entity_def from the array may delete it.

### Step 6 — Re-label All Documents

`update-prompts` alone does NOT change the F1 scores. The stored `ProjectScore` and field-group F1 reflect the last trained `ModelVersion`, which is validated against the existing ground-truth labellings — not against the new prompts. To make the new prompts take effect, you MUST re-label every document using Steps 1-5 of the "Label an Existing Project" workflow. This overwrites the stored labellings with Claude's new extractions produced under the new prompts, triggering server-side retraining.

### Step 7 — Wait ~60 seconds, Then Re-check Metrics

IXP retrains server-side after labellings are submitted. After re-labelling all documents, wait ~60 seconds before checking metrics:

```bash
uip ixp project metrics <owner> <dataset-name> --output json
```

Compare the new `ModelVersion` against the previous one:
- If `ModelVersion` has advanced, report the new F1 scores vs the prior baseline
- If `ModelVersion` is unchanged, wait another ~60 seconds and re-check (retraining occasionally takes longer)
- Do NOT poll faster than once per 60 seconds — retraining is not instant, and faster polling wastes calls

Report which fields improved and which still need work.

## New Project Workflow

To create a fresh project, upload documents, and generate a taxonomy:

```bash
uip ixp project create "<name>" <folder-path> --description "<what to extract>" --output json
```

Then follow "Label an Existing Project" above using the Owner and Name from the output.

## Extractions JSON Format

The `--extractions` flag on `uip ixp labelling label` takes a JSON array:

```json
[
  {
    "label": "Invoice > Company Information",
    "fields": [
      { "field_id": "e8a39a45177cdd72", "formatted_value": "Acme Corp" },
      { "field_id": "a2298dc0c3fa32d9", "formatted_value": "123 Main St" }
    ]
  }
]
```

- Only include fields with non-empty `formatted_value`
- The CLI handles parent labels, sentiment, spans, and dismissed format automatically

## CLI Commands Reference

| Command | Description |
|---------|-------------|
| `uip ixp project list` | List IXP projects |
| `uip ixp project get <name>` | Get a project |
| `uip ixp project create <name> <folder> -d <desc>` | Create project, upload docs, suggest+import taxonomy |
| `uip ixp project taxonomy <owner> <dataset>` | Get taxonomy (entity_defs + label_groups) |
| `uip ixp project metrics <owner> <dataset>` | Get validation metrics (F1, precision, recall) |
| `uip ixp project update-prompts <owner> <dataset> --entity-defs <json>` | Update field instructions |
| `uip ixp document list <owner> <dataset>` | List documents (UIDs + attachment refs) |
| `uip ixp document text <attachment-ref>` | Get full OCR text |
| `uip ixp document selections <attachment-ref> --page <n>` | Get OCR words with bounding polygons |
| `uip ixp document pages <attachment-ref>` | Get page count |
| `uip ixp document image <attachment-ref> --page <n> -o <path>` | Download page image |
| `uip ixp labelling confirm <owner> <dataset>` | Confirm IXP predictions as-is |
| `uip ixp labelling label <owner> <dataset> <uid> --extractions <json>` | Submit Claude extractions |

## Reference Navigation

- [Labelling API details](references/labelling-guide.md)
