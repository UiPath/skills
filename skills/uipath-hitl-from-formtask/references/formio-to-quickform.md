# Formio Component → QuickForm Field Type Map

Complete reference for converting every Formio component type to a HITL QuickForm field.

## Core Type Mappings

| Formio `type` | Formio usage | QuickForm `type` | Notes |
|---|---|---|---|
| `textfield` | Single-line text | `text` | |
| `textarea` | Multi-line text | `text` | QuickForm has no multiline distinction |
| `email` | Email address | `text` | No email-specific validation in QuickForm |
| `phoneNumber` | Phone number | `text` | |
| `url` | URL string | `text` | |
| `number` | Numeric value | `number` | |
| `currency` | Money amount | `number` | Strip currency symbol/formatting |
| `checkbox` | True/false toggle | `boolean` | |
| `radio` | Two-option select | `boolean` | Only if options map to true/false; otherwise use `text` |
| `datetime` | Date and time | `date` | QuickForm `date` accepts ISO strings |
| `day` | Date only | `date` | |
| `select` | Dropdown | `text` | No enum support; append options to label as hint: "Status (Open/Closed/Pending)" |
| `selectboxes` | Multi-select checkboxes | `text` | No multi-value type; note limitation to user |
| `signature` | Signature pad | `text` | Not supported; collect as text note instead; warn user |
| `file` | File upload | **skip** | File upload not supported in QuickForm; inform user |
| `password` | Password input | `text` | Caution: stored as plain text in flow variables |

## Container Types (Never Emit a Field)

| Formio `type` | Action |
|---|---|
| `panel` | Recurse into `components[]` |
| `well` | Recurse into `components[]` |
| `fieldset` | Recurse into `components[]` |
| `columns` | Recurse into each column's `components[]` |
| `tabs` | Recurse into each tab's `components[]` |
| `form` | Recurse into `components[]` |

## Unsupported / Complex Types

| Formio `type` | Action |
|---|---|
| `datagrid` | **Unsupported** — Inform user; suggest flattening into individual fields or collecting as a text summary field |
| `editgrid` | **Unsupported** — Same as datagrid |
| `tree` | **Unsupported** — Skip; note to user |
| `button` | → Outcome (see outcome table below) |
| `content` | Display-only HTML — Skip |
| `htmlelement` | Display-only HTML — Skip |
| `hidden` | Hidden value → `text`, direction `input` (pre-populated, not shown) |
| `survey` | Multi-question survey — Skip; note to user |

## Direction Rules

Apply in order — first matching rule wins:

1. `type === "hidden"` → `input`
2. `disabled === true` → `input`
3. `calculateValue` is set (non-empty string/object) → `input`
4. `readonly === true` → `input`
5. Has a known upstream binding (from Orchestrator process variable) → `inOut`
6. Default → `output`

When migrating without knowing the upstream flow context, use `inOut` for all non-disabled fields so the human can see the current value AND edit it.

## Outcome Mapping

| Formio button `action` / label | QuickForm outcome |
|---|---|
| `action: "submit"` or label "Submit" | Primary outcome; `isPrimary: true`, `action: "Continue"` |
| `action: "reset"` | Skip — no equivalent |
| `action: "event"` | Secondary outcome; `isPrimary: false`, `action: "End"` |
| Any other button | Secondary outcome |

**Button label normalization:**
- "Submit" → keep as "Submit" (or rename to "Approve" if user confirms)
- "Approve" / "Reject" → keep as-is
- "Yes" / "No" → keep as-is
- Buttons with empty label → skip

**`buttonNamesList` takes precedence** over `button`-type components when both are present. Always check `buttonNamesList` first.

## Field Name / Key Normalization

Formio `key` is a camelCase or snake_case identifier used internally. QuickForm uses:
- `name` (for schema input) = human-readable label from Formio `label`
- `id` (generated internally) = slugified, lowercase version of `name` (spaces → empty, special chars stripped)

Do NOT use the Formio `key` as the QuickForm `name` — use `label` for readability.

## Required Fields

- If Formio `validate.required === true` → set `required: true` on the QuickForm output/inOut field
- If no `validate` object → omit `required` (defaults to false)

## Edge Cases

### select with boolean values
```json
{"type":"select","label":"Approved","key":"approved","data":{"values":[{"label":"Yes","value":true},{"label":"No","value":false}]}}
```
→ Map to `boolean` since values are true/false. Name field "Approved".

### radio with exactly two options
If options map to a yes/no or true/false semantic → `boolean`. Otherwise → `text`.

### Nested panel with a label
The panel's `label` becomes a comment, not a field. If the panel contains fields, emit them at the top level with their own labels intact.

### datagrid migration strategy
If the user must preserve datagrid structure, suggest one of:
1. Add one `text` output field per column (flatten the grid)
2. Add a single `text` output field for the whole grid (user types a JSON or CSV summary)
3. Keep the FormTask for this step and use an AppTask node instead of QuickForm
