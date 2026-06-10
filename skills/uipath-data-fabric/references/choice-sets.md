# Choice Sets Reference

Reusable picklists that back `CHOICE_SET_SINGLE` and `CHOICE_SET_MULTIPLE` entity fields. Full CRUD via CLI — sets and their values.

> **Preview-then-confirm gate (SKILL.md Rule 14).** Before invoking `choice-sets create` or `choice-set-values create`, show the full proposed set — name, displayName, description, and every value (`Name` + `DisplayName`) in creation order — and wait for explicit user approval. Value order matters: `NumberId` is assigned 0-based by creation order and is immutable.

## Commands

| Command | Use |
|---------|-----|
| `uip df choice-sets list --output json` | Find an existing choice set's `Id` |
| `uip df choice-sets list-values <choice-set-id> --output json` | Page through values; pagination `{ Items, TotalCount, HasNextPage, … }` (use `--limit` / `--cursor` / `--offset`) |
| `uip df choice-sets create <name> [--display-name <…>] [--description <…>] --output json` | Create a choice set; response `Code: ChoiceSetCreated`, `Data.Id` |
| `uip df choice-sets update <choice-set-id> [--display-name <…>] [--description <…>] --output json` | Rename / re-describe the set |
| `uip df choice-sets delete <choice-set-id> --yes --reason "<why>" --output json` | Irreversible — `--yes` and `--reason` are required |
| `uip df choice-set-values create <choice-set-id> <name> [--display-name <…>] --output json` | Add a value; server assigns `NumberId` (0-based, monotonic by creation order) |
| `uip df choice-set-values update <choice-set-id> <value-id> "<new display name>" --output json` | Display-name only — `Name` and `NumberId` are immutable |
| `uip df choice-set-values delete <choice-set-id> --ids <value-id>[,<value-id>…] --yes --reason "<why>" --output json` | Irreversible — same gating as `choice-sets delete` |

## Use the IDs

- `Id` from `list` → `choiceSetId` on the field definition.
- `NumberId` from `list-values` → the record value (integer for `_SINGLE`, integer array for `_MULTIPLE`). **0-based, set by creation order.**
- `Name` / `DisplayName` are human display — never write these on a record.

## Value `Name` validation

A choice-set value's `Name` must be alphanumeric, start with a letter, and avoid SQL / C# / VB reserved keywords — same rule as entity / field names (**SKILL.md Rule 4**). Domain words that commonly collide: `internal`, `public`, `private`, `class`, `case`, `new`, `default`, `static`, `void`, `event`, `lock`, `object`, `string`, `int`.

When a desired label is reserved, namespace the system `Name` and leave `DisplayName` unchanged: `Name: "internal_audit"` with `DisplayName: "Internal"`. The dropdown shows "Internal"; the validator sees `internal_audit`.

## Sourcing `NumberId` after batch value creates

`NumberId` is assigned 0-based by creation order and is immutable, but the server does not always reserve a slot for a rejected `choice-set-values create` — a subsequent successful create can take the `NumberId` the failed one was meant to occupy. Treat the announced creation order as a proposal, not the authoritative mapping.

Two rules for any script that batch-creates values:

1. Fail loud on each `choice-set-values create`. Never redirect stderr to `/dev/null` or strip non-zero exits inside the loop — a silenced rejection shifts every later `NumberId` without surfacing why.
2. After the batch, re-read with `choice-sets list-values <id>` and persist the actual `{Name → NumberId}` map to a side file. Read record-write payloads from that file — never from the announced order.

## Add a choice-set field to an entity

### Step 1 — Get or create the choice set

**Contract:**

```
uip df choice-sets create <name> [--display-name "<label>"] [--description "<…>"] --output json
```

| Arg | Required | Notes |
|---|---|---|
| `<name>` | yes | System name. Alphanumeric, starts with a letter, not a C#/VB/SQL reserved keyword. |
| `--display-name "<label>"` | no | User-facing label in dropdowns. Defaults to `<name>` when omitted. |
| `--description "<…>"` | no | Free text. |

**Example:**

```bash
uip df choice-sets list --output json                                                          # check for an existing match first
uip df choice-sets create ExpenseTypes --display-name "Expense Types" --output json            # create when none matches
```

### Step 2 — Add each value to the set

**Contract:**

```
uip df choice-set-values create <choice-set-id> <name> [--display-name "<label>"] --output json
```

| Arg | Required | Notes |
|---|---|---|
| `<choice-set-id>` | yes | UUID from `choice-sets list` / `create`. |
| `<name>` | yes | System name. Same alphanumeric + no-reserved-keyword rule as `<name>` above (see [Value `Name` validation](#value-name-validation)). |
| `--display-name "<label>"` | no | User-facing label. Defaults to `<name>` when omitted. |

`NumberId` is assigned 0-based by creation order — order matters. See [Sourcing `NumberId` after batch value creates](#sourcing-numberid-after-batch-value-creates) for the per-value error handling rule.

**Example — `travel` and `meals` on the ExpenseTypes set:**

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

```bash
uip df choice-sets delete <choice-set-id> --yes --reason "<why>" --output json
```

Irreversible. Before invoking, run `entities list --output json` and find every entity whose `Fields[].ChoiceSetId == <choice-set-id>`. Surface those entities to the user and ask: *"This choice set is used by `<entity>.<field>` — delete it anyway (those fields will break), pick a replacement choice set, or stop?"* Apply only what the user confirms.
