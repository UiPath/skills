# Choice Sets Reference

Reusable picklists that back `CHOICE_SET_SINGLE` and `CHOICE_SET_MULTIPLE` entity fields. Full CRUD via CLI — sets and their values.

> **Preview-then-confirm gate (data-fabric.md Rule 14).** Before invoking `choice-sets create` or `choice-set-values create`, show the full proposed set — name, displayName, description, and every value (`Name` + `DisplayName`) in creation order — and wait for explicit user approval. Value order matters: `NumberId` is assigned 0-based by creation order and is immutable.

## Commands + folder scope

Command syntax, flags, response shapes: [Data Fabric CLI docs → Common Commands](https://github.com/UiPath/cli/blob/main/docs/tools/data-fabric.md#common-commands). Folder-scope rules mirror entities — see data-fabric.md → Folder Scope.

Behavioral quirks the CLI can't self-document:

- **`choice-set-values update` is display-name only** — `Name` and `NumberId` are immutable once created.
- **Binding a `CHOICE_SET_*` field**: pass only `choiceSetId`; `referenceFolderKey` on `CHOICE_SET_*` is CLI-rejected. The tenant ↔ folder boundary still applies. See [`entity-schema.md` → Cross-folder references](entity-schema.md#cross-folder-references).

## Use the IDs

- `Id` from `list` → `choiceSetId` on the field definition.
- `NumberId` from `list-values` → the record value (integer for `_SINGLE`, integer array for `_MULTIPLE`). **0-based, set by creation order.**
- `Name` / `DisplayName` are human display — never write these on a record.

## Value `Name` validation

CLI-enforced from `@uipath/data-fabric-tool` `1.199.0+`. The choice-set-value validator is a separate code path from the entity/field-name one — **case-sensitive** and narrower — so a name legal in one slot may not be legal in the other. Full rule list and the recommended snake_case + `--display-name` pattern: [Data Fabric CLI docs → Client-side validation](https://github.com/UiPath/cli/blob/main/docs/tools/data-fabric.md#client-side-validation).

## Sourcing `NumberId` after batch value creates

`NumberId` is assigned 0-based by creation order and is immutable, but the server does not always reserve a slot for a rejected `choice-set-values create` — a subsequent successful create can take the `NumberId` the failed one was meant to occupy. Treat the announced creation order as a proposal, not the authoritative mapping.

Two rules for any script that batch-creates values:

1. Fail loud on each `choice-set-values create`. Never redirect stderr to `/dev/null` or strip non-zero exits inside the loop — a silenced rejection shifts every later `NumberId` without surfacing why.
2. After the batch, re-read with `choice-sets list-values <id>` and persist the actual `{Name → NumberId}` map to a side file. Read record-write payloads from that file — never from the announced order.

## Add a choice-set field to an entity

### Step 1 — Get or create the choice set

```bash
uip df choice-sets list --output json                                                 # look for an existing match first (Rule 13 pick-or-create)
uip df choice-sets create ExpenseTypes --display-name "Expense Types" --output json   # create when none matches
```

### Step 2 — Add each value to the set

`NumberId` is assigned 0-based by creation order — order matters ([Sourcing `NumberId` after batch value creates](#sourcing-numberid-after-batch-value-creates)).

```bash
uip df choice-set-values create <choice-set-id> travel --display-name "Travel" --output json
uip df choice-set-values create <choice-set-id> meals  --display-name "Meals"  --output json
```

### Step 3 — Bind the choice set to an entity field

```bash
# New entity
uip df entities create "Expense" --body '{
  "fields":[
    {"fieldName":"amount",   "type":"DECIMAL", "isRequired": true},
    {"fieldName":"category", "type":"CHOICE_SET_SINGLE",   "choiceSetId":"<choice-set-id>"},
    {"fieldName":"tags",     "type":"CHOICE_SET_MULTIPLE", "choiceSetId":"<choice-set-id>"}
  ]
}' --output json

# Existing entity
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

Irreversible. Before invoking `choice-sets delete`, run `entities list --output json` and find every entity whose `Fields[].ChoiceSetId == <choice-set-id>`. Surface those entities and ask: *"This choice set is used by `<entity>.<field>` — delete it anyway (those fields will break), pick a replacement, or stop?"* Apply only what the user confirms.
