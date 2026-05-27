# Choice Sets Reference

Reusable picklists that back `CHOICE_SET_SINGLE` and `CHOICE_SET_MULTIPLE` entity fields. **CLI is read-only — `list` and `get` only**; author / edit / delete in the Data Fabric web UI. If a needed choice set doesn't exist, stop and ask — do not fall back to `STRING`.

## Commands

| Command | Use |
|---------|-----|
| `uip df choice-sets list --output json` | Find a choice set's `ID` (pass as `choiceSetId` on the field) |
| `uip df choice-sets get <choice-set-id> --output json` | Get each value's `NumberId` (pass as record value); `--limit` / `--cursor` / `--offset` for pagination |

## Response shapes

```json
// list
{ "Data": [{ "ID": "<choice-set-id>", "Name": "ExpenseTypes", "DisplayName": "Expense Types", ... }] }

// get
{ "Data": { "Values": [{ "Id": "<value-uuid>", "Name": "travel", "DisplayName": "Travel", "NumberId": 1 }, ...] } }
```

- `ID` from `list` → `choiceSetId` on the field definition
- `NumberId` from `get` → record value (integer for `_SINGLE`, integer array for `_MULTIPLE`)
- `Name` / `DisplayName` → human display only; never write these on a record

## Add a choice-set field to an entity

```bash
# 1. Discover ID (and confirm values)
uip df choice-sets list --output json
uip df choice-sets get <choice-set-id> --output json

# 2a. New entity
uip df entities create "Expense" --body '{
  "fields":[
    {"fieldName":"amount",   "type":"DECIMAL", "isRequired": true},
    {"fieldName":"category", "type":"CHOICE_SET_SINGLE",   "choiceSetId":"<choice-set-id>"},
    {"fieldName":"tags",     "type":"CHOICE_SET_MULTIPLE", "choiceSetId":"<choice-set-id>"}
  ]
}' --output json

# 2b. Existing entity
uip df entities update <entity-id> --body '{
  "addFields":[{"fieldName":"category","type":"CHOICE_SET_SINGLE","choiceSetId":"<choice-set-id>"}]
}' --output json
```

## Write / read / filter record values

Record value is the integer `NumberId` (single) or integer array (multi). Records read back in the same shape — resolve to display labels client-side via `choice-sets get` if needed.

```bash
uip df records insert <entity-id> --body '{"amount":250,"category":1,"tags":[1,2]}' --output json
```

Passing a display label (`"category":"Travel"`) is rejected. Filter operator semantics — especially `CHOICE_SET_MULTIPLE` (`contains` vs `=`) — are in [`records-query.md`](records-query.md#filtering-on-choice-set-fields).

## Decision: is this field a choice set?

- Finite, reused list of named options → choice set. Single value → `_SINGLE`; multiple → `_MULTIPLE`.
- Link to a *row* in another entity → `RELATIONSHIP` (see [`entity-schema.md`](entity-schema.md#relationship-fields)), not a choice set.
- No matching choice set exists → stop and ask the user to author it in the web UI; do not fall back to `STRING`.
