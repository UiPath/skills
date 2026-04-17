# IXP Labelling API Guide

## Overview

The labelling API confirms (or corrects) extractions for documents in an IXP project. This guide covers the exact format and rules for submitting labellings.

## Confirming Predictions for a Single Document

**Endpoint:** `POST /_private/datasets/<owner>/<dataset_name>/labellings/<comment_uid>`

**Auth:** User token via `Authorization: Bearer <token>` header. Requires `DATASETS_REVIEW` permission on the project.

### Request Body Structure

```json
{
  "moon_forms": [{
    "group": "default",
    "assigned": [ ...capture groups... ],
    "dismissed": { "captures": [] }
  }],
  "entities": { "assigned": [], "dismissed": [] }
}
```

### Capture Group Structure

Each capture group represents one field group (label) with its extracted fields:

```json
{
  "label": {
    "name": "Invoice > Company Information",
    "sentiment": "positive"
  },
  "captures": [{
    "fields": [
      {
        "field_id": "e8a39a45177cdd72",
        "formatted_value": "Acme Corp",
        "spans": []
      },
      {
        "field_id": "a2298dc0c3fa32d9",
        "formatted_value": "123 Main St, City",
        "spans": []
      }
    ]
  }]
}
```

### Hierarchical Labels

When a label has hierarchy (uses ` > ` separator), ALL ancestor labels must also be in the `assigned` array:

For label `"Invoice > Company Information"`:
- Must also include `"Invoice"` as a separate capture group with empty captures

```json
{
  "label": { "name": "Invoice", "sentiment": "positive" },
  "captures": [{ "fields": [] }]
}
```

### Field Rules

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `field_id` | string | Yes | Hex ID from the taxonomy |
| `formatted_value` | string | Yes | The extracted text value |
| `spans` | array | Yes | Pass `[]` when no text span positions available |
| `document_spans` | array | No | Polygon coordinates on the document page |

### Validation Rules

1. `sentiment` must be `"positive"` or `"negative"` (string, not number)
2. `dismissed` in `moon_forms` must be an **object** `{ "captures": [] }`, not an array
3. Each field must have either `span` or `spans` (pass `spans: []` to satisfy this)
4. Only include fields that have a non-empty `formatted_value`
5. `group` must be `"default"`

## Getting Document Data

### Query Comments in a Source

```
POST /_private/datasets/<owner>/<dataset_name>/query
{
  "filter": { "sources": ["<source_id>"] },
  "order": { "kind": "recent" },
  "limit": 50
}
```

Returns comments with `uid` and `attachments[].attachment_reference`.

### Get OCR Text for a Document

1. Get page count:
   ```
   GET /_private/attachments/<attachment_reference>/render
   ```
   Returns `page_metadata` array (one entry per page).

2. Get words per page:
   ```
   GET /_private/attachments/<attachment_reference>/selections/pages/<page_index>
   ```
   Returns `selections` array with `{ kind: "word", text: "..." }` entries.

3. Join all words with spaces, pages with double newlines.

### Get Taxonomy from Labellings

```
GET /_private/datasets/<owner>/<dataset_name>/labellings?id=<comment_uid>&compute_moon_predictions=true
```

The response includes `moon_forms[].predicted` capture groups which contain:
- `label.name` — the field group name
- `captures[].fields[].field_id` — the field ID
- `captures[].fields[].name` — the field name
- `captures[].fields[].formatted_value` — the IXP-predicted value

Use these to build the taxonomy schema for Claude's extraction prompt.

## Finding the Design Source

The design source is where uploaded documents live. To find it:

```
GET /v1/sources/<owner>
```

Filter sources by `_kind === "ixp_design"` and use its `id`.
