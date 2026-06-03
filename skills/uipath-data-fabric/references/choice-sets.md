# Choice Sets Reference

Reusable picklists that back `CHOICE_SET_SINGLE` and `CHOICE_SET_MULTIPLE` entity fields. Full CRUD via CLI — sets and their values.

## Commands

| Command | Use |
|---------|-----|
| `uip df choice-sets list --output json` | Find an existing choice set's `Id` |
| `uip df choice-sets list-values <choice-set-id> --output json` | Page through values; pagination `{ Items, TotalCount, HasNextPage, … }` (use `--limit` / `--cursor` / `--offset`) |
| `uip df choice-sets create <name> [--display-name <…>] [--description <…>] --output json` | Create a choice set; response `Code: ChoiceSetCreated`, `Data.Id` |
| `uip df choice-sets update <choice-set-id> [--display-name <…>] [--description <…>] --output json` | Rename / re-describe the set |
| `uip df choice-sets delete <choice-set-id> --confirm --reason "<why>" --output json` | Irreversible — `--confirm` and `--reason` are required |
| `uip df choice-set-values create <choice-set-id> <name> [--display-name <…>] --output json` | Add a value; server assigns `NumberId` (0-based, monotonic by creation order) |
| `uip df choice-set-values update <choice-set-id> <value-id> "<new display name>" --output json` | Display-name only — `Name` and `NumberId` are immutable |
| `uip df choice-set-values delete <choice-set-id> --ids <value-id>[,<value-id>…] --confirm --reason "<why>" --output json` | Irreversible — same gating as `choice-sets delete` |

## Use the IDs

- `Id` from `list` → `choiceSetId` on the field definition.
- `NumberId` from `list-values` → the record value (integer for `_SINGLE`, integer array for `_MULTIPLE`). **0-based, set by creation order.**
- `Name` / `DisplayName` are human display — never write these on a record.

## Add a choice-set field to an entity

```bash
# 1. Get or create the choice set, then add values
uip df choice-sets list --output json
# (or)  uip df choice-sets create "ExpenseTypes" --display-name "Expense Types" --output json
uip df choice-set-values create <choice-set-id> travel --display-name "Travel" --output json
uip df choice-set-values create <choice-set-id> meals  --display-name "Meals"  --output json

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

Record value = integer `NumberId` (single) or integer array (multi); reads echo the same shape. Filter operator semantics — especially `CHOICE_SET_MULTIPLE` (`contains` vs `=`) — are in [`filter-platform-contract.md`](filter-platform-contract.md#operator-support-by-field-type).

```bash
uip df records insert <entity-id> --body '{"amount":250,"category":1,"tags":[1,2]}' --output json
```

Passing a display label (`"category":"Travel"`) is rejected — resolve to `NumberId` first.

## Decision: is this field a choice set?

- Finite, reused list of named options → choice set. Single value → `_SINGLE`; multiple → `_MULTIPLE`.
- Link to a *row* in another entity → `RELATIONSHIP` (see [`entity-schema.md` → Relationship Fields](entity-schema.md#relationship-fields)).

## Pick-or-create flow

When the user's request needs a choice set but they didn't name one (or the name they gave doesn't exist):

1. Run `choice-sets list --output json`.
2. Surface every existing choice set to the user with its `Name` and `DisplayName` — don't pre-filter. The user is the judge of relevance.
3. For each plausibly-matching set, run `choice-sets list-values <id>` and show its values so the user can confirm fit.
4. Ask explicitly: *"Use one of these, or create a new choice set named `<X>`?"*
5. Only `choice-sets create` + `choice-set-values create` after explicit approval, using the user's chosen name and values.

Never fall back to `STRING`. Never auto-create without confirming the values.

## Deleting a choice set

```bash
uip df choice-sets delete <choice-set-id> --confirm --reason "<why>" --output json
```

Irreversible. Before invoking, run `entities list --output json` and find every entity whose `Fields[].ChoiceSetId == <choice-set-id>`. Surface those entities to the user and ask: *"This choice set is used by `<entity>.<field>` — delete it anyway (those fields will break), pick a replacement choice set, or stop?"* Apply only what the user confirms.
