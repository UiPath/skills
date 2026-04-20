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

### Get Document (download original file)

```bash
uip ixp document get <owner> <comment-uid> -o /tmp/ixp_doc.png --output json
```

Downloads the original document file (image/PDF). Then use the **Read tool** to view it visually. This is the primary way to read a document for extraction.

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

Download the original document image and its OCR text:

```bash
# Download the document image
uip ixp document get <owner> <comment-uid> -o /tmp/ixp_doc.png --output json

# Get the OCR text (uses the attachment ref from document list)
uip ixp document text <attachment-ref> --output json
```

Then use the **Read tool** to view the image:

```
Read /tmp/ixp_doc.png
```

Use the **image** to understand the document layout and locate fields visually. Use the **OCR text** as the source of exact character values to submit — this ensures the `formatted_value` strings match exactly what IXP sees.

### Step 4 — Extract Field Values

Using the document image and OCR text from Step 3, and the taxonomy from Step 2, extract values for every field:
- Use the **image** to understand the document layout and identify which fields are present
- Use the **OCR text** to get the exact character values — every `formatted_value` you submit MUST be a substring of the OCR text, character-for-character
- Do NOT "fix" OCR characters (e.g., `Ó` → `O`, `l` → `1`) — use exactly what the OCR returned
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

### Step 1 — Get Current Metrics and Diagnose Fields

```bash
uip ixp project metrics <owner> <dataset-name> --output json
```

Use the **actual F1 scores from the API** — do NOT calculate F1 manually. Identify field groups with F1 < 0.7 as targets for improvement.

**Diagnose each low-scoring field** using the per-field Precision, Recall, and Documents values from the metrics:

1. **Classify the action** for each field:
   - `Documents = 0` AND `F1 = 0` → **SKIP** (no predictions — nothing to learn from)
   - `Documents < 1` → **SKIP** (insufficient data for meaningful refinement)
   - Otherwise → **REFINE**

2. **Diagnose the problem type** for fields marked REFINE:
   - `Precision < 0.5` AND `Recall >= 0.8` → **PRECISION** problem — model finds the field but extracts wrong values
   - `Recall < 0.5` AND `Precision >= 0.8` → **RECALL** problem — model misses the field entirely
   - `Precision < 0.5` AND `Recall < 0.5` → **BOTH** problem — model both misses fields and extracts wrong values
   - Otherwise → **MIXED** problem

Print a diagnosis summary to the user showing each field's score, action, problem type, and precision/recall before proceeding. Only continue with fields marked REFINE.

### Step 2 — Get Current Taxonomy with Instructions

```bash
uip ixp project taxonomy <owner> <dataset-name> --output json
```

From the response, find the `EntityDefs` with their current `instructions`. Note which entity_defs correspond to the low-scoring field groups (match via `moon_form[].kind` → entity_def `name`).

### Step 3 — Read Sample Documents

Pick 2-3 documents and view them as images to understand document structure:

```bash
uip ixp document list <owner> <dataset-name> --output json
uip ixp document get <owner> <comment-uid> -o /tmp/ixp_sample.png --output json
```

Then use the **Read tool** to view the image. This gives Claude visual context about where fields appear in the document, which is critical for writing location-aware instructions (especially for RECALL problems).

### Step 4 — Write Improved Instructions (Diagnosis-Driven)

For each field marked REFINE in Step 1, rewrite its `instructions` using the diagnosis from Step 1 and the document context from Step 3.

**First, audit the current instruction quality.** Check whether the existing instruction has:
- **Location hint** — any of: "page", "top of", "section", "header", "signature block", "end of the document", "boxed", "table", "bottom", "labeled"
- **Example value** — "example" or "e.g."
- **Format guidance** — "format" or "pattern"
- **Sufficient length** — at least 50 characters

Note which quality gaps exist — the rewrite must fill them.

**Then, apply diagnosis-specific fixes:**

- **PRECISION problem** → The model finds the field but extracts wrong values. Be more specific about **WHAT** value to extract and what **NOT** to extract. Clarify ambiguous cases (e.g., "Use the billing address, not the shipping address"). Add negative examples if helpful.
- **RECALL problem** → The model misses the field. Better describe **WHERE** to find it using section headings, labels, or document structure (e.g., "Found in the header area, near the company logo" or "In the table labeled 'Payment Details'").
- **BOTH problem** → Both precision and recall are failing. Rewrite the instruction entirely — describe what the field is, where it appears, what format to expect, and what to avoid.
- **MIXED problem** → Address whichever quality gaps were identified in the audit above.

**Instruction rules:**
1. **NEVER reference specific page numbers** (e.g., "page 28", "page 7"). Use section headings, labels, or content descriptions instead — page numbers vary between documents.
2. Include **format guidance** (e.g., "Format: NNN-NN-NNNN") and a **realistic example** when possible.
3. Keep instructions **2-4 sentences**. Be direct and specific.
4. The instruction goes on the **field group label** (the parent that contains the sub-fields). Write it to guide extraction of ALL fields in that group, not just one.
5. Fill all identified quality gaps: add location hints if missing, add examples if missing, add format guidance if missing.

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
| `uip ixp document get <owner> <comment-uid> -o <path>` | Download original document file for viewing |
| `uip ixp document text <attachment-ref>` | Get OCR text for exact character values |
| `uip ixp document image <attachment-ref> --page <n> -o <path>` | Download page image |
| `uip ixp labelling confirm <owner> <dataset>` | Confirm IXP predictions as-is |
| `uip ixp labelling label <owner> <dataset> <uid> --extractions <json>` | Submit Claude extractions |

## Reference Navigation

- [Labelling API details](references/labelling-guide.md)
