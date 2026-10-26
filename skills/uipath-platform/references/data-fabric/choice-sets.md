# Choice Sets Reference

Reusable picklists for `CHOICE_SET_SINGLE` and `CHOICE_SET_MULTIPLE`; full CRUD is available through the CLI.

> **Preview-then-confirm gate (data-fabric.md Rule 14).** Before invoking `choice-sets create` or `choice-set-values create`, show the full proposed set—name, displayName, description, and every value (`Name` + `DisplayName`) in creation order—and wait for explicit user approval. Creation order assigns immutable, 0-based `NumberId`s.

## Commands

All commands accept `--folder-key <GUID>` for folder-scoped sets; it is required for writes against them and recommended for reads. `list` also accepts mutually exclusive `--include-folders` and `--folder-key`. See [Folder scope](#folder-scope).

| Command | Use |
|---|---|
| `uip df choice-sets list [--folder-key <…> \| --include-folders] --output json` | Find a set's `Id`: no flags lists tenant sets; `--folder-key` lists that folder; `--include-folders` lists tenant plus every visible folder. Rows include `FolderId`. |
| `uip df choice-sets list-values <choice-set-id> [--folder-key <…>] --output json` | Page values. Pagination is `{ Items, TotalCount, HasNextPage, … }` and supports `--limit` / `--cursor` / `--offset`. |
| `uip df choice-sets create <name> [--folder-key <…>] [--display-name <…>] [--description <…>] --output json` | Create a set; response is `Code: ChoiceSetCreated`, `Data.Id`. Include `--folder-key` for folder scope; omit it for tenant scope. |
| `uip df choice-sets update <choice-set-id> [--folder-key <…>] --display-name <…> --description <…> --output json` | Rename/re-describe. Both flags are required: only `--description` returns *"DisplayName is required."*; only `--display-name` returns `Internal Server Error`. Run `choice-sets list` and resend the current other value. |
| `uip df choice-sets delete <choice-set-id> [--folder-key <…>] --yes --reason "<why>" --output json` | Irreversible; requires `--yes` and `--reason` (`--confirm` is a deprecated alias). |
| `uip df choice-set-values create <choice-set-id> <name> [--folder-key <…>] [--display-name <…>] --output json` | Add a value; the server assigns a 0-based, creation-order `NumberId`. |
| `uip df choice-set-values update <choice-set-id> <value-id> "<new display name>" [--folder-key <…>] --output json` | Change display name only; `Name` and `NumberId` are immutable. |
| `uip df choice-set-values delete <choice-set-id> --ids <value-id>[,<value-id>…] [--folder-key <…>] --yes --reason "<why>" --output json` | Irreversible; uses the same gate as `choice-sets delete`. |

## Folder scope

Sets are tenant-level or folder-scoped:

| Goal | Flags |
|---|---|
| List tenant-level sets | (none), the default |
| List one folder's sets | `--folder-key <folder-guid>` |
| List tenant plus every visible folder | `--include-folders` |
| Create/update/delete a folder-scoped set or value | `--folder-key <folder-guid>` (required) |
| Read or operate on a tenant-scoped set | `--folder-key` is harmless; the server resolves by UUID |

Bind a folder-scoped set to an entity in another folder by passing only `choiceSetId`; the server resolves its folder from that UUID. Do NOT pass `referenceFolderKey` on `CHOICE_SET_*` fields. Tenant ↔ folder boundaries still apply: a folder parent cannot bind a tenant-level set, and vice versa. See [`entity-schema.md` → Cross-folder references](entity-schema.md#cross-folder-references).

## Use the IDs

- `list` `Id` → field `choiceSetId`.
- `list-values` `NumberId` → record integer for `_SINGLE`, integer array for `_MULTIPLE`; it is 0-based and assigned by creation order.
- `Name` and `DisplayName` are human-facing; never write them on a record.

## Value `Name` validation

`Name` must start with a letter, contain only letters and digits, and be at most 250 characters; underscores are rejected. `DisplayName` is limited to 500 characters. C#/VB reserved keywords are rejected with *"Choiceset member name must … not be C# keyword"*. This is separate from the entity/field-name validator (data-fabric.md Rule 4):

| Aspect | Entity / field name (Rule 4) | Choice-set value `Name` |
|---|---|---|
| Case match | **case-insensitive** (`Class`, `class`, `CLASS` all rejected) | **case-sensitive** (`class` rejected; `Class` may pass—`New` accepted while `new` would be rejected) |
| Keyword list | Full C#/VB reserved list, including `Select`, `Return`, `New`, `Internal`, … | Partial list; empirically `select` is not rejected, but `Select` is rejected as a field name |

Do not infer legality across contexts. Use a descriptive alphanumeric token that is not a language keyword and put the human label in `DisplayName`, e.g. `Name: "internalAudit"` with `DisplayName: "Internal"`. Lowercase tokens rejected by the choice-value validator include `internal`, `public`, `private`, `class`, `case`, `new`, `default`, `static`, `void`, `event`, `lock`, `object`, `string`, and `int`.

## Sourcing `NumberId` after batch value creates

A rejected `choice-set-values create` does not always reserve a slot; a later success may take its intended `NumberId`, so announced order is only a proposal. For every batch script:

1. Fail loud on each `choice-set-values create`; never redirect stderr to `/dev/null` or strip non-zero exits inside the loop.
2. After the batch, re-read with `choice-sets list-values <id>` and persist the actual `{Name → NumberId}` map to a side file. Read record-write payloads from that file, never announced order.

## Add a choice-set field to an entity

1. List sets and let the user reuse one or approve a new one.
2. For a new set, create it, then create each value separately in the approved order. `choice-set-values create` takes the set ID and value name as positional arguments; it does not accept a batch `--body`.
3. Re-list values to obtain assigned `NumberId`s.
4. Bind it with `{"name":"<field>","type":"CHOICE_SET_SINGLE","choiceSetId":"<id>"}` or `CHOICE_SET_MULTIPLE` in `entities create` or `entities update`.

## Write / read / filter record values

A record value is an integer `NumberId` (single) or integer array (multi), and reads echo that shape. Filter semantics—including `CHOICE_SET_MULTIPLE` (`contains` versus `=`)—are in [`filter-platform-contract.md`](filter-platform-contract.md#operator-support-by-field-type).

```bash
uip df records insert <entity-id> --body '{"amount":250,"category":1,"tags":[1,2]}' --output json
```

Passing a display label such as `"category":"Travel"` is rejected; resolve `NumberId` first.

## Decision: is this field a choice set?

- A finite, reused list of named options is a choice set: use `_SINGLE` for one value and `_MULTIPLE` for several.
- A link to a row in another entity is `RELATIONSHIP` (see [`entity-schema.md` → Relationship Fields](entity-schema.md#relationship-fields)).

## Pick-or-create flow

When the request needs a choice set but names none or names a nonexistent one:

1. Run `choice-sets list --output json`.
2. Show every existing set with `Name` and `DisplayName`; do not pre-filter.
3. For each plausibly matching set, run `choice-sets list-values <id>` and show its values.
4. Ask explicitly: *"Use one of these, or create a new choice set named `<X>`?"*
5. Only after explicit approval run `choice-sets create` and `choice-set-values create`, using the chosen name and values.

Never fall back to `STRING` or auto-create without confirming values.

## Deleting a choice set

```bash
uip df choice-sets delete <choice-set-id> [--folder-key <…>] --yes --reason "<why>" --output json
```

This is irreversible. Before invoking it, run `entities list --output json`; find every entity whose `Fields[].ChoiceSetId == <choice-set-id>`, surface those entities, and ask: *"This choice set is used by `<entity>.<field>` — delete it anyway (those fields will break), pick a replacement choice set, or stop?"* Apply only what the user confirms.