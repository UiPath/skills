# IXP Labelling Guide

## Overview

All IXP operations use `uip ixp` CLI commands. Do NOT use curl or direct API calls.

## Submitting Extractions for a Single Document

```bash
cat > /tmp/ixp_extractions.json << 'EOF'
[
  {
    "label": "Invoice > Company Information",
    "fields": [
      { "field_id": "e8a39a45177cdd72", "formatted_value": "Acme Corp" },
      { "field_id": "a2298dc0c3fa32d9", "formatted_value": "123 Main St, City" }
    ]
  }
]
EOF

uip ixp labelling label <project-name> <comment-uid> \
  --extractions "$(cat /tmp/ixp_extractions.json)" --output json
```

The command handles parent labels, sentiment, spans, and dismissed format automatically.

## Confirming IXP Predictions As-Is

```bash
uip ixp labelling confirm <project-name> --output json
```

## Getting Document Data

### List All Documents

```bash
uip ixp document list <project-name> --output json
```

Returns `{ Uid, AttachmentRef }` for each document.

### Get Document (download original file)

```bash
uip ixp document get <project-name> <comment-uid> -o /tmp/ixp_doc.png --output json
```

Downloads the original document file. Then use the **Read tool** to view it visually.

## Getting the Taxonomy

```bash
uip ixp project taxonomy <project-name> --output json
```

Returns `EntityDefs` and `LabelGroups`. From these:
- Each `label_def` with `moon_form` entries defines a field group
- Each `moon_form` entry's `kind` matches an entity_def `name`, and `field_id` is what you submit
- The entity_def `name` gives you the human-readable field name

## Getting Metrics

```bash
uip ixp project metrics <project-name> --output json
```

Returns project score, quality rating, and per-field-group F1/precision/recall.

## Updating Prompts/Instructions

```bash
cat > /tmp/ixp_entity_defs.json << 'EOF'
[
  {
    "id": "<existing_id>",
    "name": "<existing_name>",
    "title": "<existing_title>",
    "inherits_from": [],
    "trainable": true,
    "instructions": "<new improved instructions>"
  }
]
EOF

uip ixp project update-prompts <project-name> \
  --entity-defs "$(cat /tmp/ixp_entity_defs.json)" \
  --label-instructions "<new top-level instructions>" \
  --output json
```

> **Important:** Include ALL entity_defs in the update, not just changed ones. Omitting one may delete it.

## Extractions JSON Format

Each extraction has:
- `label` — the field group name (e.g. `"Invoice > Company Information"`)
- `fields[]` — array of `{ "field_id": "<hex id>", "formatted_value": "<value>" }`

Only include fields with non-empty `formatted_value`. The CLI handles:
- Parent label injection for hierarchical labels
- Setting `sentiment: "positive"`
- Adding `spans: []` to each field
- Formatting `dismissed` as an object
