# Choice Sets Reference

Reusable picklists for `CHOICE_SET_SINGLE` and `CHOICE_SET_MULTIPLE` fields. Full CRUD is available via CLI.

> **Preview-then-confirm gate (data-fabric.md Rule 14).** Before invoking `choice-sets create` or `choice-set-values create`, show the full proposed set—name, displayName, description, and every value (`Name` + `DisplayName`) in creation order—and wait for explicit user approval. Value order matters: `NumberId` is assigned 0-based by creation order and is immutable.

## Commands, scope, and IDs

Pass `--folder-key <GUID>` on writes against folder-scoped sets and on reads when appropriate. `list` accepts either `--folder-key` or `--include-folders`, not both.

- Run `uip df choice-sets list [--folder-key <…> \| --include-folders] --output json` to find an existing choice set's `Id`. No flags lists tenant-only sets; `--folder-key` lists that folder only; `--include-folders` lists the tenant and every visible folder. Each row carries `FolderId`.
- Run `uip df choice-sets list-values <choice-set-id> [--folder-key <…>] --output json` to page through values. The response is `{ Items, TotalCount, HasNextPage, … }`; use `--limit`, `--cursor`, or `--offset`.
- Run `uip df choice-sets create <name> [--folder-key <…>] [--display-name <…>] [--description <…>] --output json` to create a set. The response is `Code: ChoiceSetCreated`, `Data.Id`. Pass `--folder-key` for folder scope; omit it for tenant scope.
- Run `uip df choice-sets update <choice-set-id> [--folder-key <…>] --display-name <…> --description <…> --output json` to rename or re-describe a set. Pass both options every time, reading and resending the unchanged value with `choice-sets list`. Only `--description` returns *"DisplayName is required."*; only `--display-name` returns `Internal Server Error`.
- Run `uip df choice-sets delete <choice-set-id> [--folder-key <…>] --yes --reason "<why>" --output json` to irreversibly delete a set; `--yes` and `--reason` are required (`--confirm` is a deprecated alias).
- Run `uip df choice-set-values create <choice-set-id> <name> [--folder-key <…>] [--display-name <…>] --output json` to add a value. The server assigns `NumberId` (0-based, monotonic by creation order).
- Run `uip df choice-set-values update <choice-set-id> <value-id> "<new display name>" [--folder-key <…>] --output json` to update only the display name; `Name` and `NumberId` are immutable.
- Run `uip df choice-set-values delete <choice-set-id> --ids <value-id>[,<value-id>…] [--folder-key <…>] --yes --reason "<why>" --output json` to irreversibly delete values, using the same gate as `choice-sets delete`.

Apply this scope matrix:

| Goal | Flags |
|---|---|
| List only tenant-level choice sets | (none) — default |
| List a single folder's choice sets | `--folder-key <folder-guid>` |
| List tenant + every folder you can see | `--include-folders` |
| Create/update/delete a folder-scoped set or value | `--folder-key <folder-guid>` (required) |
| Read or operate on a tenant-scoped set | `--folder-key` is harmless when passed; the server resolves by UUID |

Bind a folder-scoped choice set to an entity in another folder by passing only `choiceSetId`; the server resolves its folder from that UUID. Do **not** pass `referenceFolderKey` on `CHOICE_SET_*` fields. A folder parent cannot bind a tenant-level choice set, and vice versa. See [`entity-schema.md` → Cross-folder references](entity-schema.md#cross-folder-references).

Use `Id` from `list` as the field's `choiceSetId`. Use `NumberId` from `list-values` as the record value: an integer for `_SINGLE`, or an integer array for `_MULTIPLE`. It is 0-based and assigned by creation order. Treat `Name` and `DisplayName` as display metadata; never write them on a record.

## Names and values

Require each value `Name` to start with a letter, contain only letters and digits, and be at most 250 characters. Reject underscores. Limit `DisplayName` to 500 characters. The server rejects C# / VB reserved keywords with *"Choiceset member name must … not be C# keyword"*.

Do not apply the entity/field-name validator (data-fabric.md Rule 4) to choice values:

| Aspect | Entity / field name (Rule 4) | Choice-set value `Name` (here) |
|---|---|---|
| Case match | **case-insensitive** (`Class`, `class`, `CLASS` all rejected) | **case-sensitive** (`class` rejected, `Class` may pass — empirically verified: `New` accepted while `new` would be rejected) |
| Keyword list | full C#/VB reserved list — incl. `Select`, `Return`, `New`, `Internal`, … | partial list — some keywords missing (empirically `select` is NOT rejected as a choice-set value, but `Select` IS rejected as a field name) |

Use a descriptive alphanumeric token that is not a language keyword, such as `internalAudit`, `newLead`, or `classOption`, and put the human label in `DisplayName`: `Name: "internalAudit"` with `DisplayName: "Internal"`. Lowercase tokens rejected by the choice-value validator include `internal`, `public`, `private`, `class`, `case`, `new`, `default`, `static`, `void`, `event`, `lock`, `object`, `string`, and `int`.

## Batch creates and `NumberId`

The server does not always reserve a slot for a rejected `choice-set-values create`; a later successful create may take that failed slot. Treat announced order as a proposal, not the authoritative mapping.

For every batch script:

1. Fail loud on each `choice-set-values create`. Never redirect stderr to `/dev/null` or strip non-zero exits inside the loop; a silenced rejection shifts later `NumberId`s without explaining why.
2. After the batch, re-read with `choice-sets list-values <id>` and persist the actual `{Name → NumberId}` map to a side file. Read record-write payloads from that file, never from announced order.

## Add a choice-set field

1. Run `choice-sets list` and let the user reuse a set or approve a new one.
2. For a new set, create it, then create each value separately in the approved order. `choice-set-values create` takes the set ID and value name as positional arguments; it does not accept a batch `--body`.
3. Re-list values to obtain assigned `NumberId`s.
4. Bind the set with `{"name":"<field>","type":"CHOICE_SET_SINGLE","choiceSetId":"<id>"}` or `CHOICE_SET_MULTIPLE` in `entities create` or `entities update`.

## Record values and filters

Write an integer `NumberId` for a single value or an integer array for multiple values; reads echo the same shape. Resolve labels to `NumberId` first; passing a display label such as `"category":"Travel"` is rejected. Consult [`filter-platform-contract.md`](filter-platform-contract.md#operator-support-by-field-type) for filter operators, especially `CHOICE_SET_MULTIPLE` (`contains` versus `=`).

```bash
uip df records insert <entity-id> --body '{"amount":250,"category":1,"tags":[1,2]}' --output json
```

Use a choice set for a finite, reused list of named options; choose `_SINGLE` or `_MULTIPLE` as appropriate. Use `RELATIONSHIP` for a link to a row in another entity. See [`entity-schema.md` → Relationship Fields](entity-schema.md#relationship-fields).

## Pick-or-create flow

When a request needs a choice set but names none, or names a nonexistent set:

1. Run `choice-sets list --output json`.
2. Show every existing choice set with its `Name` and `DisplayName`; do not pre-filter.
3. For each plausibly matching set, run `choice-sets list-values <id>` and show its values.
4. Ask explicitly: *"Use one of these, or create a new choice set named `<X>`?"*
5. Invoke `choice-sets create` and `choice-set-values create` only after explicit approval, using the user's chosen name and values.

Never fall back to `STRING` or auto-create without confirming the values.

## Delete a choice set

Before invoking:

```bash
uip df choice-sets delete <choice-set-id> [--folder-key <…>] --yes --reason "<why>" --output json
```

Run `entities list --output json` and find every entity whose `Fields[].ChoiceSetId == <choice-set-id>`. Surface those entities and ask: *"This choice set is used by `<entity>.<field>` — delete it anyway (those fields will break), pick a replacement choice set, or stop?"* Apply only what the user confirms. Deletion is irreversible.