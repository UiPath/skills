# UiPath Data Fabric (`uip df`)

Data Fabric is UiPath's structured data store. Entities are typed schemas; records are rows; file fields store binary attachments.

All operations go through `uip df <subject> <verb> --output json`.

> For Flow connector nodes (Query / Create / Update / Delete / Get Entity Record by ID inside a `.flow`), use the `uipath-maestro-flow` skill — it owns the node JSON, `bindings_v2.json`, connection-resource layout, and `node configure` mechanics. Use this reference for entity discovery and record seeding from the CLI.

---

## When to Use

- Creating or modifying entity schemas (add fields, update metadata)
- Reading, inserting, updating, or deleting records
- Filtering records with complex predicates
- Computing aggregate metrics for dashboards / KPIs (counts, sums, averages, group-by) — see [records-query.md](records-query.md#aggregates-server-side)
- Importing bulk data from CSV files
- Uploading or downloading file attachments on records

## When NOT to Use — Hand Off to Another Skill

Embedding Data Fabric reads/writes **inside a `.flow` file** as connector activity nodes (Query / Create / Update / Delete / Get Entity Record by ID) is owned by `uipath-maestro-flow`. That skill knows the node JSON, `bindings_v2.json`, connection-resource layout, and `node configure` mechanics.

Use this reference (`uipath-platform` → Data Fabric) for entity discovery and record seeding from the CLI; hand off to `uipath-maestro-flow` for in-flow node authoring.

| Task | Skill |
|------|-------|
| Discover entities, list/describe fields before authoring a flow node | `uipath-platform` Data Fabric (`uip df entities list`/`get`) |
| Seed test records the flow will read | `uipath-platform` Data Fabric (`uip df records insert` / `import`) |
| Add a Query/Create/Update/Delete/GetById node to a `.flow` | `uipath-maestro-flow` |
| Resolve the IS `uipath-uipath-dataservice` connection for binding | `uipath-maestro-flow` (in-flow binding) or `uipath-platform` Integration Service (general IS connection management) |

---

## Not Supported — Never Attempt These

Respond that the operation is not supported. Do not try to work around it.

| Operation | Response |
|-----------|----------|
| Change a field's data type | Not supported; type is fixed at creation |
| Create a federated entity | Not supported via CLI or UiPath portal |
| Write records to a federated entity | Federated entities are read-only |
| Name a field with a SQL / language reserved keyword | API rejects with `RESERVED_LANGUAGE_KEYWORDS` — pick a domain-specific name (see Rule 4) |
| Write a `FILE` value through `records insert` / `records update` | Not supported — `FILE` columns are written exclusively through `files upload`. Insert the row without the FILE column, then `files upload <entity-id> <record-id> <field-name> --file <path>`. See Rule 6. |
| Write a `FILE` value through `records import` (CSV) | Not supported. CSV `records import` does not accept `FILE` columns — see Rule 20. Switch to `records insert` (no FILE column) + `files upload`. |

---

## Critical Rules

1. **Install the tool first.** If `uip df` returns "unknown command": `uip tools install @uipath/data-fabric-tool`. See *Tool Version Requirements* below for the floor needed per feature.

2. **Verify login and tenant first.** Run `uip login status --output json`. Switch with `uip login tenant set <tenant>` if needed. For full login/environment setup, see the parent `uipath-platform` skill.

3. **Always resolve entity ID first.** Use `entities list` before any operation. Never assume an entity ID.

4. **Entity and field names must pass validation**: start with a letter, contain only letters/digits/underscores (`[a-zA-Z0-9_]`), 3–100 characters. No hyphens or spaces. Reserved field names that will error: `Id`, `CreatedBy`, `CreateTime`, `UpdatedBy`, `UpdateTime`. Also never use **SQL, C#, or VB reserved keywords** — common rejections: `Case`, `Class`, `If`, `Then`, `Else`, `New`, `Object`, `Public`, `Return`, `Select`, `From`, `Where`, `Table`, `Order`, `Group`, `Index`, `Key`, `User`, `Role`, `Type`, `Status`. The API surfaces these as *"cannot be a reserved word in C# or VB"* (or `RESERVED_LANGUAGE_KEYWORDS`). Pick domain-specific names: `Case` → `WorkItem`; `Status` → `OrderStatus`; `Order` → `PurchaseOrder`; `Key` → `ItemKey`.

5. **All updates require `Id` in the body.** The CLI routes single vs batch by whether the body is a JSON object (1 record) or array (multiple). Both require `"Id"` in the record. Use `records list` or `records query` to retrieve record IDs before updating.

6. **Never put a FILE-typed key in `records insert` / `records update` / `records import` payloads.** Expected behavior: the platform silently strips FILE values — paths, base64, filenames, UUIDs, and `null` are all dropped server-side, the CLI returns `Result: Success`, no error. Do not interpret Success as "the file was changed." `records update receipt:null` does **not** clear the file. `records update receipt:"<uuid>"` does **not** swap the file. CSV import drops FILE columns too (Rule 20). Required path: `files upload <entity-id> <record-id> <field-name> --file <path>` to attach or replace, `files delete` to clear, `files download` to retrieve. Sequence to seed a file on a new row: (1) `records insert` without the FILE column; (2) `files upload` against the returned `Data.Id`. Full surface in [`file-attachments.md`](file-attachments.md).

7. **CSV headers must match exact field names** (case-sensitive). Use `entities get` to discover field names before importing.

8. **Never create duplicate entities.** Always `entities list` first; reuse if it already exists.

9. **Only work with native entities.** When listing entities before a write, use `entities list --native-only` to filter out federated entities. Never write to federated entities.

10. **Entity delete is irreversible — surface dependents first.** `entities delete <id> --yes --reason "<why>"` deletes the entity and every record in it. Before invoking, scan for dependents and list them to the user one by one: (a) other entities that reference this one (run `entities list --output json` and pull every entry whose `Fields[].ReferenceEntity.Id == <id>` — these will have broken FKs after the delete); (b) choice sets used by this entity's fields (`Fields[].ChoiceSetId` from `entities get`) — those choice sets are shared and may still be in use elsewhere. Ask the user explicitly for each dependent: delete it too, leave it, or stop. Apply only the choices the user confirms — never cascade silently.

11. **Field delete is irreversible — surface impact first.** `entities update <id> --body '{"removeFields":[{"fieldName":"<name>"}]}' --yes --reason "<why>"` drops the field and every record's value in it. Note `removeFields` takes `{"fieldName": "..."}` (NOT `{"id": "..."}` like `updateFields`). Before invoking: (a) if it's a RELATIONSHIP / FILE field, identify any code or flows that read its value; (b) if it's a CHOICE_SET field, note the choice set itself is unaffected (still shared). Ask the user explicitly: confirm the field name, confirm the loss is intentional, supply a reason for the audit log. Apply only after explicit confirmation.

12. **Complex field types need extra config and lookups, just like `DECIMAL` needs `decimalPrecision`.** `CHOICE_SET_SINGLE` / `CHOICE_SET_MULTIPLE` require `choiceSetId` (UUID, from `choice-sets list`); `RELATIONSHIP` and `FILE` require `referenceEntityId` (target entity UUID — from `entities list`) + `referenceFieldId` (target field UUID — from `entities get <target-id>`). The target entity must exist first. When the user describes a link to another row ("each order has a Customer", "each report has a Supplier"), the field type is `RELATIONSHIP` — never substitute `STRING` or `UUID` for it. Full shape in [`entity-schema.md`](entity-schema.md).

13. **Pick-or-create flow for choice sets and relationship targets.** When the user's request needs a choice set or a relationship target entity that they didn't name (or the name they gave doesn't exist), do NOT auto-create and do NOT fall back to `STRING`. Run `choice-sets list` / `entities list --native-only`, present the matching candidates by `Name` / `DisplayName`, and ask: *pick from these, or create new?* Create only with explicit user approval, using their chosen name and values. Choice-set authoring uses `choice-sets create` / `update` / `delete` + `choice-set-values create` / `update` / `delete`; surface in [`choice-sets.md`](choice-sets.md).

14. **Preview the proposed schema and get explicit approval before any create or schema-altering update.** Applies to `entities create`, `entities update` with `addFields` / `updateFields` / `removeFields`, `choice-sets create`, and `choice-set-values create`. Sequence: (1) compose the full proposal — entity / choice-set name, `displayName`, `description`, and every field with its `fieldName`, normalized UPPERCASE `type`, and all extras (`isRequired`, `isUnique`, `lengthLimit`, `maxValue` / `minValue`, `decimalPrecision`, `defaultValue`, `choiceSetId`, `referenceEntityId` / `referenceFieldId`); (2) render it as a readable table or formatted JSON block (NOT a raw CLI command); (3) ask the user to confirm or revise — wait for an explicit *yes / approved / proceed* before invoking the CLI; (4) apply revisions exactly as requested — never silently add, drop, rename, or retype fields the user didn't approve; re-show the revised proposal and ask again. Show the proposal **once per round** — don't re-show an unchanged schema after every minor question.

15. **Choice / relationship record values use lookup tokens, not labels.** Choice value → integer `NumberId` (single) or array of `NumberId`s (multi), from `choice-sets list-values`. Relationship value → target record's UUID `Id` regardless of which field was bound as `referenceFieldId`. Filter / `groupBy` use the same tokens; `CHOICE_SET_MULTIPLE` filtering has special operator semantics — see [`records-query.md`](records-query.md#filtering-on-choice-set-fields).

16. **Answer with `records query`, not from memory.** Counts, sums, filters, lookups — issue a fresh `records query` (or `records list`) and use the server's response. Do not reuse cached insert responses, IDs you generated earlier, or values from previous tool results. Exception: the `Id` returned by the same `records insert` you just made.

17. **`records query` filters.** Body shape, operators, per-type support, response, and unsupported-operator handling are in the [filter contract](filter-platform-contract.md). Symbol-form operators only (`==`/`Equals`/`like` → 400). On an unsupported operator/type or a missing value, don't run it — ask the user (Rule 18). **Return all fields by default** — omit `selectedFields` unless a subset is requested. **Aggregate aliases are PascalCased in the response** — `alias: "total"` comes back as key `"Total"` on each row of `Data.Items`; parse by the PascalCase key, not the alias you sent.

18. **When a request isn't supported OR the upstream system returns an error, stop and confirm with the user — never silently substitute.** Triggers (not exhaustive): a filter operator unsupported for the field type / not in the symbol list / missing a value (see [filter contract → Unsupported operator](filter-platform-contract.md#unsupported-operator-or-missing-value)); an unknown `fieldName`; a nonexistent or federated entity; a missing CLI verb (`removeFields`, … — see *Not Supported*); cross-entity joins or value forms the API can't serve; ANY 4xx/5xx, validation error, `RESERVED_LANGUAGE_KEYWORDS`, constraint-violation, or quota response from the API.
    Sequence: (1) surface the full upstream message verbatim — never swallow it; (2) state precisely what isn't supported or what failed (cite the rule / schema / error code); (3) propose a concrete next step keyed to the error — e.g. unknown `fieldName` → list the entity's real same-type fields from `entities get` and ask which; `RESERVED_LANGUAGE_KEYWORDS` → suggest a domain-specific rename; constraint violation → show the allowed range; missing dependency → list candidates via `entities list` / `choice-sets list` and offer pick-or-create (Rule 13); (4) apply **only** what the user approves, never your own fallback. If nothing works, error out and recommend the right sibling skill (`uipath-maestro-flow` / `uipath-rpa` / `uipath-agents` / `uipath-test`) — don't fabricate or return a degraded result.

19. **Resolve folder scope up front; pass `--folder-key` on folder-scoped targets.** Data Fabric entities and choice sets live either at the tenant level or inside an Orchestrator folder. Every `uip df` command that touches a row accepts `--folder-key <GUID>`; `entities list` and `choice-sets list` also accept `--include-folders` (mutually exclusive with `--folder-key`). See [Folder Scope](#folder-scope) for the matrix. Required on folder-scoped writes (entity/record/file/choice-set create/update/delete) and recommended on folder-scoped reads. Lists default to **tenant-only** — pass `--folder-key` or `--include-folders` to see folder rows.

    **Mandatory scope-prompt flow.** If the user requests any `entities` / `records` / `files` / `choice-sets` / `choice-set-values` operation (create / update / delete / get / list / insert / upload / download / import / query) and has **not** specified the scope in this conversation, stop. Do not guess, do not default to personal workspace, do not default to tenant. Ask via `AskUserQuestion` with two dropdown questions:

    1. **Scope** — options: `Tenant level (no --folder-key)` · `Folder-scoped`.
    2. **If folder-scoped**, pre-fetch `uip or folders list --output json` first, then render the accessible folders as a single-select dropdown — label each option `<Name> — <Path>`, stash the `Key` as the option payload, and use that as `--folder-key` for every subsequent call this turn. If more than 4 folders return, narrow first — ask whether the user wants Personal / Shared / Solution / Standard folders, or accept a free-text name filter, then re-prompt with the filtered list. Never render the raw folder list as plain markdown — always a selectable dropdown.

    Cache the folder list within the turn to avoid refetching. Echo the chosen scope back in the next message before any irreversible call. Scope persists across follow-up turns unless the user switches. Tenant prompting is rarely needed — `uip login status` shows the active tenant; only call `uip login tenant set <tenant>` after the user explicitly asks for a different one.

    **Bypass clauses — skip the AskUserQuestion flow when ANY of these hold.** The agent must still announce the chosen scope (one line) in the response so the user can correct.
    - The prompt explicitly says some variant of *"do not ask"*, *"do not pause"*, *"no approval / confirmation / feedback needed"*, or *"proceed without confirmation"* — proceed at **tenant level** unless folder context is mentioned inline.
    - The prompt names a folder inline (*"in the Shared folder"*, *"in folder X"*, *"--folder-key <guid>"*, *"in personal workspace"*) — proceed with that folder; do **not** ask which folder.
    - The prompt explicitly states tenant scope (*"tenant level"*, *"do NOT pass any folder flag"*, *"no folder"*, *"at the root"*) — proceed at tenant level.
    - The prompt provides a folder GUID, a `folder_a_id`/`folder_b_id` variable, or instructions to derive folder IDs from another command — proceed using the derived folder; if none is available, fall through to tenant.
    - The request is a pure tenant-wide discovery read (`entities list` / `choice-sets list` with no specific entity ID in mind) — default to `--include-folders` and announce. Asking adds no value for a survey.

    When a bypass triggers, write one sentence at the top of the response stating which scope you picked and why (*"Proceeding at tenant level — prompt said 'do not pause'."* / *"Using folder Shared (key c4359cde-…) — prompt referenced it."*). The user can redirect in the next turn.

20. **`records import` does not support complex field types — surface this to the user before invoking.** `records import` accepts Basic types only — `CHOICE_SET_SINGLE`, `CHOICE_SET_MULTIPLE`, `RELATIONSHIP`, `FILE`, and `AUTO_NUMBER` are **not supported**. The CSV header is accepted but the column values are ignored (no error, no `ErrorFileLink` entry — `null` in every row, or row failure if the field is `isRequired` without a `defaultValue`). Sequence: (1) run `entities get <entity-id>` and list every field whose type is in the unsupported set above; (2) tell the user verbatim which columns are not supported by import and why; (3) offer the alternative — `records insert --file <json>` with a JSON-array body handles all types except `FILE` (use `files upload` for those — Rule 6). See [`records-query.md` → Writing choice-set and relationship values](records-query.md#writing-choice-set-and-relationship-values) for the value form; (4) only invoke `records import` after the user confirms they accept the unsupported columns being skipped OR want to switch to `records insert`. This is platform behavior, not a bug — do not attempt to work around it.

---

## Tool Version Requirements

| Feature | Required `@uipath/data-fabric-tool` |
|---------|--------------------------------------|
| `entities` / `records` CRUD, `query` with filters/sort, `records import`, `files` | `0.9.0+` |
| Server-side `aggregates` and `groupBy` on `records query` | `1.0.1+` |
| `--folder-key` threaded through every entity/record/file/choice-set command + `--include-folders` on `entities list` / `choice-sets list` | `1.197.0+` (currently on `alpha` dist-tag; falls into `latest` once promoted — install with `uip tools install @uipath/data-fabric-tool@alpha` until then) |

Upgrade with `uip tools install @uipath/data-fabric-tool@latest` when a feature appears to silently no-op (e.g. aggregate body keys returning raw record lists).

---

## Quick Start

```bash
# List entities (use --native-only before any write)
uip df entities list --native-only --output json

# Get entity schema (field names and types)
uip df entities get <entity-id> --output json

# List records (first page)
uip df records list <entity-id> --limit 50 --output json

# Insert one record
uip df records insert <entity-id> --body '{"Name":"Alice","Score":95}' --output json

# Query with a filter
uip df records query <entity-id> \
  --body '{"filterGroup":{"logicalOperator":0,"queryFilters":[{"fieldName":"Status","operator":"=","value":"active"}]}}' \
  --output json

# Aggregate query — count of records per Status (server-side groupBy)
uip df records query <entity-id> \
  --body '{"selectedFields":["Status"],"groupBy":["Status"],"aggregates":[{"function":"COUNT","field":"Id","alias":"total"}]}' \
  --output json
```

For Complex types field shapes and value formats, see [`entity-schema.md`](entity-schema.md#supported-field-types) and [`records-query.md`](records-query.md#filtering-on-choice-set-fields).

### `records query` body schema — exact keys (agents commonly mis-guess)

The CLI accepts a strict schema. These are the four most-missed keys:

| Position | Correct | Common wrong guess |
|---|---|---|
| Entity ID | positional: `uip df records query <entity-id>` | `--entity-id <id>` (no such flag) |
| Wrap object | `filterGroup` | `filter`, `where`, `query` |
| Boolean operator | `logicalOperator: 0` (AND) or `1` (OR) — **integer** | `"AND"` / `"OR"` (string) |
| Filter list | `queryFilters: [...]` | `filters`, `conditions` |
| Per-filter field key | `fieldName: "..."` | `field`, `name`, `column` |

`CHOICE_SET_MULTIPLE` value forms:
- `contains` / `not contains` → bare-NumberId **string** (`"1"`, not `"[1]"`)
- `=` / `!=` → JSON-array **string** (`"[1,3]"`, not bare `"1"`)

Full per-type operator support matrix: [`filter-platform-contract.md`](filter-platform-contract.md).

---

## Folder Scope

Entities and choice sets are either tenant-level or folder-scoped. Records and files inherit the parent entity's scope.

**Flags (CLI ≥ `1.197.0`):**

- `--folder-key <GUID>` — scope the call to that folder. Pass the Orchestrator folder key (`uip or folder list --output json` → `Key`), NOT the folder display name.
- `--include-folders` — on `entities list` / `choice-sets list` only. Returns tenant + every folder the caller can see, in one response. **Mutually exclusive with `--folder-key`** — passing both errors out.

**Per-command behavior:**

| Command(s) | `--folder-key` effect |
|---|---|
| `entities list`, `choice-sets list` | Filter mode: omit both flags → tenant only (default); `--folder-key <key>` → that folder only; `--include-folders` → tenant + all visible folders. Each returned row carries `folderId` / `FolderId` — keep it for follow-up calls. |
| `entities create`, `choice-sets create` | **Scope-bound** — required for folder placement. Omit to create at tenant level. The created row's `folderId` matches. |
| `entities get / update / delete`, `records *`, `files *`, `choice-sets list-values / update / delete`, `choice-set-values create / update / delete` | Forwarded as `X-UIPATH-FolderKey`. Required on folder-scoped targets; tenant-scoped targets accept any key (server resolves by UUID). Pass it defensively on every destructive op. |

**Cross-folder references on RELATIONSHIP / FILE / CHOICE_SET_\* fields:** the parent entity's `--folder-key` doesn't have to equal the target's folder. Add `referenceFolderKey` per-field when the target lives elsewhere — see [`entity-schema.md` → Cross-folder references](entity-schema.md#cross-folder-references).

If a verb returns `unknown option '--folder-key'`, the installed tool is older than `1.197.0` — see *Tool Version Requirements* above.

---

## Task Navigation

| Task | Commands to use |
|------|----------------|
| Explore what entities exist (tenant) | `entities list` → `entities get <id>` |
| Explore entities in a specific folder | `entities list --folder-key <folder-guid>` |
| Explore tenant + every folder's entities in one shot | `entities list --include-folders` |
| Explore only native entities | `entities list --native-only` |
| Manage choice sets | `choice-sets list [--folder-key <…> \| --include-folders]` / `list-values <id> [--folder-key <…>]` / `create [--folder-key <…>]` / `update [--folder-key <…>]` / `delete [--folder-key <…>]`; values via `choice-set-values create` / `update` / `delete` (all accept `--folder-key`) — full surface in [`choice-sets.md`](choice-sets.md) |
| Create a new entity | `entities create <name> [--folder-key <folder-guid>] --body '{"fields":[{"fieldName":"Title","type":"STRING"}]}'` — omit `--folder-key` for tenant scope. For complex field types (`CHOICE_SET_*`, `RELATIONSHIP`) and their required extras (including cross-folder `referenceFolderKey`), see [`entity-schema.md`](entity-schema.md#supported-field-types) |
| Update entity / add fields | `entities update <id> --body '{"addFields":[{"fieldName":"NewField","type":"STRING"}]}'` |
| Update existing field metadata | `entities update <id> --body '{"updateFields":[{"id":"<field-uuid>","displayName":"New Label","isRequired":true}]}'` — body uses `id` (lowercase); the response key is `Id` (different case, same value) |
| Update entity metadata | `entities update <id> --body '{"displayName":"New Name","description":"desc"}'` |
| Delete an entity (irreversible — list dependents first) | `entities delete <id> [--folder-key <…>] --yes --reason "<why>"` — pass `--folder-key` on folder-scoped entities. See Rule 10 for the dependent-discovery flow |
| Delete a field (irreversible — confirm impact first) | `entities update <id> --body '{"removeFields":[{"fieldName":"<name>"}]}' --yes --reason "<why>"` — note `removeFields` uses `fieldName`, NOT `id` like `updateFields`. See Rule 11 |
| Read records (first page) | `records list <entity-id> --limit 50` |
| Read records (next page) | `records list <entity-id> --cursor <NextCursor.Value>` — extract the inner `Value` from the previous response's `Data.NextCursor` object; passing the whole object errors |
| Get one record | `records get <entity-id> <record-id>` |
| Insert one record | `records insert <entity-id> --body '{...}'` (or `--file`). Choice / relationship value formats: see [`records-query.md`](records-query.md#writing-choice-set-and-relationship-values) |
| Batch insert | `records insert <entity-id> --body '[{...},{...}]'` |
| Update one record | `records update <entity-id> --body '{"Id":"<record-id>","field":"val"}'` |
| Batch update | `records update <entity-id> --body '[{"Id":"<id1>","field":"val"},{"Id":"<id2>","field":"val"}]'` |
| Delete records (irreversible — `--yes --reason` required) | `records delete <entity-id> <id1> <id2> [--folder-key <…>] --yes --reason "<why>"` — IDs are positional varargs (separate args, NOT space-joined in one quoted string) |
| Filter/search records | `records query <entity-id> --body '{...}'`. Choice / relationship filter operators: see [`records-query.md`](records-query.md#filtering-on-choice-set-fields) |
| Aggregate / group-by metrics | `records query <entity-id> --body '{"aggregates":[{"function":"COUNT","field":"Id","alias":"total"}],"groupBy":["FieldName"]}'` |
| Bulk import from CSV (Basic field types only — `CHOICE_SET_*`, `RELATIONSHIP`, `FILE`, and `AUTO_NUMBER` are **not supported** by `records import`; **surface this to the user before invoking — Rule 20**) | `records import <entity-id> --file data.csv [--folder-key <…>]` |
| Bulk seed records that include complex fields | `records insert <entity-id> --file records.json` with a JSON array body |
| Upload file to record | `files upload <entity-id> <record-id> <field-name> --file path` |
| Download file | `files download <entity-id> <record-id> <field-name> --destination path` |
| Delete file (irreversible — `--yes --reason` required) | `files delete <entity-id> <record-id> <field-name> [--folder-key <…>] --yes --reason "<why>"` |

---

## Field Types

Pass the exact `EntityFieldDataType` string — the CLI is case-sensitive. Common types: `STRING`, `INTEGER`, `DECIMAL`, `BOOLEAN`, `DATE`, `DATETIME`, `UUID`, `FILE`, plus `AUTO_NUMBER` and the complex types (`CHOICE_SET_*` / `RELATIONSHIP` / `FILE`) whose required extras are covered in Rule 12. Full table with SQL backing types and value semantics in [`entity-schema.md`](entity-schema.md).

**Normalize user input to UPPERCASE before invoking.** Users typically say `boolean`, `string`, `decimal`, `datetime` in their prompts. The CLI rejects lowercase / mixed-case variants with `Cannot read properties of undefined (reading 'sqlTypeName')`. Case-fold to the enum value: `boolean` → `BOOLEAN`, `String` → `STRING`, `Decimal` → `DECIMAL`, etc. Synonyms that don't map 1:1 (e.g. `number` → `INTEGER` or `DECIMAL`; `text` → `STRING` or `MULTILINE_TEXT`) need disambiguation — see [`entity-schema.md` → Normalizing user-facing type names](entity-schema.md#normalizing-user-facing-type-names).

### Advanced Field Constraints

Optional per-type constraints on create/update — `lengthLimit` (STRING, MULTILINE_TEXT), `maxValue` / `minValue` (INTEGER, BIG_INTEGER, DECIMAL, FLOAT, DOUBLE), `decimalPrecision` (DECIMAL, FLOAT, DOUBLE). See [`entity-schema.md`](entity-schema.md) for ranges and examples.

---

## Workflow: Discover → Act → Verify

1. **Discover** — list entities, get schema, check existing records
2. **Act** — create/insert/update
3. **Verify** — re-read to confirm the operation succeeded

```bash
uip df entities list --native-only --output json
uip df entities get <entity-id> --output json
uip df records insert <entity-id> --body '{"Name":"Alice","Score":95}' --output json
uip df records list <entity-id> --limit 50 --output json
# Records live in Data.Items (NOT Data.Records). Stop when Data.HasNextPage is false.
# NextCursor is an object — unwrap Data.NextCursor.Value and pass that to --cursor.
uip df records list <entity-id> --cursor <NextCursor.Value> --output json
```

---

## Query Request Format

Pass the query body via `--body` or `--file`; pagination uses `--limit` / `--cursor` / `--offset` CLI flags, never body keys (see [Pagination](#pagination) below). The body shape, operators, per-type support, and response shape live in [`filter-platform-contract.md`](filter-platform-contract.md); query-only extras (`selectedFields`, `sortOptions`) are documented in [`records-query.md`](records-query.md).

## Pagination

`records list` / `records query` paginate via `--limit`, `--cursor`, `--offset`. See [`records-query.md`](records-query.md).

---

## Troubleshooting

> **Any error not in this table → Rule 18.** (Surface verbatim, propose options keyed to the error, apply only what the user confirms.)

| Error | Cause | Fix |
|-------|-------|-----|
| `unknown command: df` | Tool not installed | `uip tools install @uipath/data-fabric-tool` |
| `Not logged in` | Auth expired | `uip login` |
| `HTTP 401` | Invalid token | Re-login; ensure `DataServiceApiUserAccess` scope is present |
| `HTTP 403` | Permission denied | Ensure account has Data Fabric permissions |
| `Entity not found` | Wrong entity ID | Run `entities list` to get correct ID |
| `Record must include 'Id'` | Update body missing Id | Every record passed to `records update` must include `"Id": "<record-id>"` — both single and batch |
| `Each field must include a 'fieldName' string` | Invalid field in `entities create` | Use `{"fieldName":"myfield"}` not `{"name":"myfield"}` |
| `Entity name resolution failed` | Query/import with bad ID | Verify entity exists with `entities list` |
| Import errors in CSV | Header mismatch | Run `entities get` and check exact field names (case-sensitive) |
| `records import` succeeded but choice / relationship / file / auto-number column is `null` on every row | Complex field types are **not supported** by `records import` (Basic types only) — current Data Fabric platform behavior | Re-seed those columns via `records insert` with a JSON body (FILE fields additionally require `files upload` — Rule 6). Surface the limitation **before** invoking import next time — see Rule 20 and [`bulk-import.md`](bulk-import.md) |
| Write to federated entity | Entity is read-only | Use `--native-only`; federated entities cannot be written to |
| `cannot be a reserved word in C# or VB` (alias: `RESERVED_LANGUAGE_KEYWORDS`) | Entity or field name collides with a C# / VB / SQL reserved keyword (e.g. `Case`, `Class`, `Status`, `Order`) | Surface the rejected name + the error to the user. Offer concrete renames: `Case` → `WorkItem` / `Matter`; `Status` → `OrderStatus` / `ItemStatus`; `Order` → `RecordOrder` / `PurchaseOrder`; `Key` → `ItemKey`. Apply only the user-confirmed rename. See Rule 4. |
| `Choiceset member name must only contain alphanumeric characters, start with alphabetic characters and not be C# keyword` | Choice-set value `Name` violates the keyword rule that also gates entity / field names (Rule 4) | Namespace the system `Name` and keep `DisplayName` unchanged. Full rule + the related `NumberId`-ordering caveat for batch creates: [`choice-sets.md` → Value `Name` validation](choice-sets.md#value-name-validation). |
| Constraint violation (`"outside of allowed range"`, `"exceeds lengthLimit"`, etc.) | Write value broke `minValue` / `maxValue` / `lengthLimit` / `decimalPrecision` | Surface the full error to the user, show the allowed range from `entities get`, and ask what value to use — never silently clamp. See Rule 18. |
| `referenceEntityId` missing on RELATIONSHIP/FILE field | Field defined with names instead of UUIDs | Pass `referenceEntityId` + `referenceFieldId` (UUIDs from `entities list` / `entities get`). See Rule 12. |
| `Cannot read properties of undefined (reading 'sqlTypeName')` | Field `type` value didn't match a known `EntityFieldDataType` enum — almost always lowercase / mixed-case (e.g. `"boolean"` instead of `"BOOLEAN"`) | Case-fold to the UPPERCASE enum from the type table — see [`entity-schema.md` → Normalizing user-facing type names](entity-schema.md#normalizing-user-facing-type-names) |
| `Each field in removeFields must include a non-empty 'fieldName' string` | `removeFields` was called with `{"id": "..."}` (the shape `updateFields` uses) instead of `{"fieldName": "..."}` | Re-emit with `{"fieldName": "<exact field name>"}` — see Rule 11 |
| `unknown option '--folder-key'` or `unknown option '--include-folders'` | Installed `@uipath/data-fabric-tool` predates `1.197.0` (folder-key fan-out) | Upgrade: `uip tools install @uipath/data-fabric-tool@alpha` until `1.197.0+` is promoted to `latest`. See *Tool Version Requirements* |
| `--folder-key and --include-folders are mutually exclusive` | Both flags passed on `entities list` / `choice-sets list` | Pick one: `--folder-key <key>` for a single folder, OR `--include-folders` for tenant + every folder you can see |
| Entity / choice set just created via `--folder-key <X>` doesn't appear in `entities list` / `choice-sets list` | Lists default to tenant-only | Re-run with `--folder-key <X>` (same key) or `--include-folders` |

---

## References

- [`entity-schema.md`](entity-schema.md) — Field definitions, supported types, schema update patterns, choice-set + relationship field shapes
- [`choice-sets.md`](choice-sets.md) — Full choice-set CRUD (`list`/`list-values`/`create`/`update`/`delete` plus `choice-set-values create`/`update`/`delete`), look up `NumberId`s, add CHOICE_SET fields to entities, write choice values on records
- [`records-query.md`](records-query.md) — Query filter syntax, pagination, sorting, choice/relationship semantics on read & write
- [`filter-platform-contract.md`](filter-platform-contract.md) — Filter body structure, per-type operator support matrix, and what to do when a request needs an unsupported operator
- [`file-attachments.md`](file-attachments.md) — File field upload/download/delete file
- [`bulk-import.md`](bulk-import.md) — CSV format requirements and the Basic-fields-only limitation (complex types — `CHOICE_SET_*`, `RELATIONSHIP`, `FILE`, `AUTO_NUMBER` — are **not supported** by `records import`; use `records insert` with a JSON body, plus `files upload` for FILE)
