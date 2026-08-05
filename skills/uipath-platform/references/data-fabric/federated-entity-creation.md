# Federated Entity Creation (from connectors)

Create a Data Fabric **federated** entity — a read-only view over an external system reached through an **Integration Service (IS) connection** (Salesforce, HubSpot, Zendesk, ServiceNow, Data hub, …), or over another existing DF entity. Data lives in the source; the entity mirrors it.

## When this applies (triggers)

Route here when the user wants an entity **backed by an external source**, e.g.:
- "create an entity from **Salesforce** Account" / "from the **HubSpot** contacts" / "from **Data hub** / **ServiceNow** / `<connector>`"
- "make a **federated** entity", "a read-only view over `<external object>`"
- "create a **virtual data object** / **VDO**", "a **zero-copy** entity / view over `<source>`" — "virtual data object", "VDO", and "zero-copy" are UiPath product terms for a federated entity; treat them as synonyms and route here.
- "pull `<object>` from `<connector>` into Data Fabric as an entity"
- an entity sourced from an **existing DF entity** (native source).

For a plain **native** entity (columns stored in UiPath, no connector) → [`entity-schema.md`](entity-schema.md). For inserting/querying records → [`records-query.md`](records-query.md).

## Critical rules

1. **`entityClass: "Federated"`** on the create body. Native `fields` is not required for a federated entity — its schema comes from `externalFields`.
2. **`directionType` is numeric** — `0` = read-only, `1` = read/write. The string `"ReadOnly"` is rejected (500).
3. **Each field mapping (`externalFieldMappingDetail`) must be complete** — `externalFieldName`, `externalFieldType`, `directionType`, `searchability`, `isRequiredForRead`, `sortable`. A bare mapping (only name + direction) → **500**.
4. **`externalObjectDetail.method` is required for a *functional* (queryable) entity — and its internal casing is consumed at read time, so it must be the canonical lowercase shape.** It is the connector's operations catalog, sourced from `is resources describe`. Two traps:
   - **Create does NOT validate `method`.** Create is *accepted* with a wrong or absent `method` (returns `Success`) — the entity is built with correct schema/fields/join. The failure surfaces only at **read** time: `records list` returns a generic `"An internal error occurred"` because the query engine can't parse the catalog. Never treat create-`Success` as proof the entity works — always follow with a `records list` (Verify step).
   - **Get `method` from `uip is resources describe … --operation List --output json`** — it returns the catalog under a top-level `Method` key as a **ready canonical JSON string** (uppercase verb keys `{GET, GETBYID, PATCH, POST, DELETE}`, each with lowercase props: `operation`, `description`, `method`, `path`, `operationId`, `hasCEQL`, `parameters[{name, description, type, dataType, required, displayName, curated, design}]`). **Copy that string verbatim** into `externalObjectDetail.method` — do not re-serialize, re-case, or hand-build it. The casing is load-bearing at read time, and the CLI already emits it in the correct shape (only the `--operation` form carries `Method`; the bare `describe` does not).
5. **`primaryKey`, per-field `searchable`/`searchableOperators`, and field types come from `is resources describe`** (`--operation List`). The CLI surfaces them in the resource summary. **`externalObjectDetail.primaryKey` is required on every source** — the primary connector source and each native/related source alike (a native source's primary key is its own `Id`).
6. **External vs native source, per `externalFields[]` entry:** an external connector source uses `externalConnectionDetail`; a source backed by another UiPath entity uses `nativeConnectionDetail: { entityId, folderKey }` instead.
7. **Multi-source joins** go in `sourceJoinConditionDetails`. Omit for a single source. Each condition MUST carry BOTH connection ids, a `joinType`, and the **external** (source) field names — get any of these wrong and create fails with `external sources join conditions not making a connected dependency or having a cyclic dependency`:
   - **`sourceObjectConnectionId` + `relatedSourceObjectConnectionId` are mandatory.** The join graph matches each source by its **connection id, NOT by name**; without them the referenced source is unresolvable and the graph reads as disconnected. For a **connector** source the id is its IS `connectionId`; for a **native** source (`nativeConnectionDetail`) the id is the **entity id** (the same GUID as `entityId`).
   - **`joinType`** — send `"LeftJoin"`. The server also accepts the numeric enum `0` (same left join); both create and read identically.
   - **`sourceJoinField` / `relatedSourceJoinField` use the EXTERNAL source field name** (e.g. `Id`), NOT the renamed internal column (`IdField` per Rule 11). Reserved names still get renamed on the internal `field.name`, but the join maps by source spelling.
   - `sourceObjectName` / `relatedSourceObjectName` = each source's `externalObjectName`.
   - **Both join fields MUST be mapped columns on their sources.** A join field is part of the schema — it is not implied by the join. Each of `sourceJoinField` and `relatedSourceJoinField` must appear as a mapped `field` in that source's `fields[]` (matched by `externalFieldMappingDetail.externalFieldName`). When you add a second source with a join, include the related join key in that new source's `fields`; and confirm the left/existing source already maps the field it joins on (add it if not). A join on an unmapped field builds but fails at read — the column isn't in the entity's schema.
8. **Federated entities are read-only, but reads work through both `records list` and `records query`.** Never `records insert/update/delete` — writes silently fail; write at the source. `records query` works on a federated entity for **`filterGroup` filtering, `selectedFields` projection, and `sortOptions`** — same body shape and operators as a native query (see [filter contract](filter-platform-contract.md), data-fabric.md Rule 17). Two federated-only limits: **`aggregates` / `groupBy` are silently ignored** (server returns raw rows, no counts — aggregate the listed rows client-side), and **multi-entity `joins` are rejected with a 400** (`Multi-entity joins (req.Joins) are not supported on the v3 query endpoint`). Plain reads still work with `records list` (`--limit` / `--cursor` / `--offset`) — no need to push a filter to the source just to read a subset.
9. **Confirm before creating or updating.** Before `entities create` **or** a federated `entities update`, render the **complete** join graph (see [Join graph](#join-graph-render-in-the-cli)) — every source and **every** join in the *resulting* state — alongside the full proposed schema (sources, fields, mappings, joins, connection) as a readable table/JSON, then wait for explicit approval; never auto-create/update. On an **update** the graph is the existing joins (from a projected `get`, Rule 13) **plus** the delta — not just the added join. Draw **one diagram per join condition** with the shared left box repeated, **stacked vertically — never a single star** with multiple arrows out of one box.
10. **List federated entities** with `entities list --federated-only` (mutually exclusive with `--native-only`; omit both for all).
11. **Every internal `field.name` must clear the shared field Name Validation — check it before create, not by hitting the API.** Each mapping's `field.name` becomes a native Data Fabric column, so it is bound by the same rules as any native field: **[`entity-schema.md` → Name Validation](entity-schema.md#name-validation)** (which defers to [`data-fabric.md` Rule 4](data-fabric.md#critical-rules) for the reserved-name and C#/VB-keyword lists). Federated creation MUST run every internal field name through that same validation up front — do not build column names blindly from connector field names. Common collision: connector primary keys are almost always named **`Id`**, a reserved column name, so the naive `field.name == externalFieldName` mapping fails on the first field. Rename the internal column (e.g. `Id` → `IdField`) while keeping `externalFieldMappingDetail.externalFieldName`, `externalObjectDetail.primaryKey`, **and any `sourceJoinConditionDetails` join field** (Rule 7) on the source name `Id` — only the internal `field.name` changes; every reference to the *source* field keeps the source spelling. Reflect any rename in the Rule 9 preview; skipping the check fails create with the misleading `Required parameter 'Id' was not found in GET(List) parameters`.
12. **Federated create is an `entities create` — it inherits every native entity-create validation.** Rule 11 (names) is only the one that bites first; the rest apply identically to the federated payload. Run these checks up front — do not discover them through API errors. A connector's `dataType` is a *source* type only; it never exempts the internal column from these rules.

    | Native validation | Where it applies in the federated body | Reference |
    |---|---|---|
    | Name rules (reserved names, C#/VB keywords, charset, length) | internal `field.name`, entity `<Name>` | Rule 11 · [`entity-schema.md` → Name Validation](entity-schema.md#name-validation) |
    | UI-compatible field types only — no `INTEGER` / `BIG_INTEGER` / `FLOAT` / `DOUBLE` / `UUID` / `DATETIME`; substitute per the table | internal `field.type` (e.g. connector `integer` → `DECIMAL` precision 0, `number` → `DECIMAL` precision 2) | [`data-fabric.md` Rule 12b](data-fabric.md#critical-rules) · [`entity-schema.md` → UI-broken types](entity-schema.md#ui-broken-types--do-not-use) |
    | No duplicate entity | `entities list` before create; reuse if it already exists | [`data-fabric.md` Rule 8](data-fabric.md#critical-rules) |
    | Folder-scope resolution (list accessible folders via `uip or folders list` — same as native, never hardcode) + preview-then-confirm | `--folder-key` placement; the Rule 9 preview | [`data-fabric.md` Rule 19](data-fabric.md#critical-rules) · flow step 2 · Rule 9 |

13. **Entity `list`/`get` responses are large — always project with `--output-filter`, never dump.** `entities list` returns every entity with its full field arrays (thousands of lines); a federated `entities get` embeds each source's `method` catalog (multi-KB per source) plus every mapping; a native entity with many fields is likewise big. Reading the raw payload can exceed output/context limits and fail. Use `--output-filter` (JMESPath, PascalCase keys) to filter + project at the CLI before it prints. **The expression is applied to the `Data` field directly — do NOT prefix it with `Data`.** When `Data` is an array (a `list`) start the expression with `[]` or `[?…]`; when `Data` is an object (a `get`) start with a key (`Fields[]`, `Name`). Writing `Data[].…` looks for a `Data` key *inside* `Data`, matches nothing, and **silently returns empty** — a false negative that reads as "no results" even though the raw response is huge. Recipes:
    - **Resolve a native source by name AND get its fields in one call** (returns just the match, not the whole tenant): `uip df entities list --include-folders --output-filter "[?Name=='<name>'].{Id:Id,Name:Name,FolderId:FolderId,Fields:Fields[].Name}" --output json`. The list response already carries each entity's `Fields`, so project them here — **do not follow with a separate `entities get` to re-fetch field names**. `--include-folders` covers folder-scoped entities; disambiguate with the user if the name matches zero or several (Rule 9). `Id` is the native source's `entityId`, `FolderId` its `nativeConnectionDetail.folderKey`, and `Fields` the mappable column names.
    - **Inspect the current federated schema before an update** (a `get`, not a list): `uip df entities get <id> [--folder-key <key>] --output-filter "{name:Name, sources:ExternalFields[].ExternalObjectDetail.ExternalObjectName, fields:ExternalFields[].Fields[].FieldMetaData.Name, joins:SourceJoinCriterias}" --output json`

    You never need the `method` catalogs to inspect — they're opaque strings copied verbatim from `is resources describe` at build time (Rule 4). For the update flow this is enough: pass only the delta and the SDK re-reads/merges the full definition itself.

14. **The mapped field set is the user's choice — ask; never default it.** When the user names a source but not its columns (e.g. "add a Salesforce Contact"), you MUST ask which fields to map *before* building the payload: present that object's fields from `is resources describe` (`ResponseFields[]`) via `AskUserQuestion` and let the user pick (flow step 4). Do **not** infer a "sensible" set (PK + a few common columns) and fold it into the preview. The Rule 9 preview is a backstop to catch mistakes — it is **not** the ask; surfacing a defaulted set for a veto still defaults a decision that was the user's. This applies **per source**, including a second or later-added source. Skip the ask only when the user already enumerated the columns, or explicitly said "all of them" / "you choose".

15. **Never silently pick a connection — ask when there's a choice.** A connection is *which account / org* the entity reads from, so it's the user's decision. From `uip is connections list <connectorKey> --all-folders --refresh`, **auto-select only when exactly one connection is `Enabled`** (and announce which one). If more than one connection matches — or more than one is `Enabled` — you MUST raise an `AskUserQuestion` (label each option by `Name` + `State`, payload = `Id`) and let the user pick. Do **not** default to the first row, a "default," or the most-recently-used.

## End-to-end flow

1. **Detect** the connector / external object / source entity from the prompt. Users name the *integration* ("Salesforce", "SAP", "HubSpot"), not the `connectorKey` — you must resolve the key.
2. **Clarify** in one round what's missing: connector, connection, object (or source entity name), and **folder scope**.

   **Resolve the `connectorKey` from the friendly name** — never hardcode or guess it (it is not simply `uipath-<name>`; e.g. Salesforce = `uipath-salesforce-sfdc`, SAP S/4HANA = `uipath-sap-s4hanacloud`):
   - `uip is connectors list --filter <name> --output json` → returns `{Name, Key}` rows. Match by `Name`, use its `Key`.
   - **`--filter` is a substring match on BOTH name and key, so it returns false positives** — `salesforce` also returns Quip / Slack (keys contain `salesforce`); `sap` also returns WhatsApp Business (`what`**`sap`**`p`). Do not assume the first row. When more than one row's `Name` plausibly matches, raise an `AskUserQuestion` dropdown labeled by `Name` (payload = `Key`) and let the user pick.
   - Confirm the chosen key with `uip is connectors get <connectorKey> --output json`.

   **Resolve folder scope** exactly as native entity creation does — this is an `entities create`, so follow [`data-fabric.md` Rule 19](data-fabric.md#critical-rules) *Mandatory scope-prompt flow* verbatim, **fetching nothing until it's actually needed**:
   - **First** ask (`AskUserQuestion`) with **literally two options and nothing else: `Tenant level (no --folder-key)` and `Folder-scoped`.** Do **not** add, rename, replace, or pre-fill either option with a folder *type* (`Shared` / `Personal` / …), a folder *name*, or a folder *GUID* — **including one discovered from a source entity, a connection, or `is connections list`.** Knowing where the sources live never justifies surfacing that folder here; a specific folder is offered only in the *second* question, after the user picks `Folder-scoped`.
     - ❌ Wrong: options `Shared folder (a8150f57…)` · `Tenant level` — substitutes a discovered folder for `Folder-scoped`.
     - ✅ Right: options `Tenant level (no --folder-key)` · `Folder-scoped` — ask *which* folder only after `Folder-scoped` is chosen.
   - **Only if** the user picks `Folder-scoped`, ask a second dropdown `Provide folder GUID` vs `List accessible folders`.
   - **Only if** they pick `List accessible folders`, run `uip or folders list --output json` — **once** — and render each folder `<Name> — <FullyQualifiedName>`, payload `Key` (narrow if >4 return). **Do not pre-fetch folders before the scope question, and never run `or folders list` twice** — it's a lazy, single call on this branch only.
   - Do not hardcode the folder set or default silently (Rule 19 bypass clauses excepted). **Resolve the new entity's scope ONLY from the user's answer — never pre-fill, default, or infer it from a source's folder.** The IS connection's own `FolderKey` (from `is connections list`) **and** a native source's `folderKey` scope the *source*, not the new entity, and are independent of it: a source that happens to live in a `Shared` folder does **not** make the new entity folder-scoped or "Shared." The chosen `Key` becomes `--folder-key` on `entities create` and every follow-up `entities get` / `records list`.
3. **Resolve the IS source** (with the `connectorKey` from step 2):
   - `uip is connections list <connectorKey> --all-folders --refresh --output json` — resolve the connection (Rule 15): **auto-pick only if exactly one is `Enabled`** (announce it); if more than one matches or is `Enabled`, **ask** via `AskUserQuestion` (label `Name` + `State`, payload `Id`) — never take a default. Gives `Id` (connectionId), `FolderKey`, `ConnectorKey`, `ConnectorName`, `Name` (connectionName), **and `ElementInstanceId`** — all from this one row.
   - **`--refresh` is mandatory here — it's the reason `ElementInstanceId` is present.** The connections-list cache drops `ElementInstanceId` (a warm-cache read returns it empty; it's populated only on a cache-bypassing fetch), so a plain list shows it blank. `--refresh` on the single resolution call above fixes this — **do not issue a second folder-scoped list to get it.** **A blank/absent `elementInstanceId` in the create body builds a valid-looking entity that returns 0 rows at read time — silently (no error).**
   - `uip is resources list <connectorKey> --connection-id <id> --output json` — list objects.
   - `uip is resources describe <connectorKey> <Object> --connection-id <id> --operation List --output json` — one call returns both the per-field schema under `ResponseFields[]` (`Name`, `Type`, `Searchable`, `SearchableOperators`, `PrimaryKey`) and the operations catalog under top-level `Method` as a **ready canonical JSON string**. Copy `Method` **verbatim** into `externalObjectDetail.method` (Rule 4) — no re-casing needed.
   - **Native DF-entity source** (not a connector — Rule 6): there is no `is connections` / `resources describe` / `method`. Get its columns from the projected `entities list` (Rule 13 → `{Id, Name, FolderId, Fields}`) or `uip df entities get <id> --output-filter "Fields[].Name" --output json`, **drop the system fields** (`Id`, `CreatedBy`, `CreatedTime`, `UpdatedBy`, `UpdatedTime`), and feed the remaining columns into the same field picker (step 4). `Id` is the source's `entityId`, `FolderId` its `nativeConnectionDetail.folderKey`.
4. **Field picker (mandatory — Rule 14).** Present the source's fields from step 3 — a connector's `ResponseFields[]`, **or a native source's `Fields` (minus system fields)** — and let the user choose which to map (`AskUserQuestion`). If the user didn't enumerate the columns, **ask — do not default a set** — and repeat this for every source, including a second/added one.
5. **(Optional) more sources + joins** — repeat step 3 per source; define joins.
6. **Preview → confirm** (Rule 9) — render the join graph (see [Join graph](#join-graph-render-in-the-cli)) + the schema table/JSON, then wait for explicit approval.
7. **Check for a duplicate, then create.** Before creating, confirm no entity with that name already exists in the target scope — projected so it's one cheap call (Rule 13): `uip df entities list [--folder-key <key>] --output-filter "[?Name=='<Name>'].{Id:Id,Name:Name}" --output json`. If it returns a row, **stop and tell the user it already exists** (give its `Id`) — offer to update it (see [Updating a federated entity](#updating-a-federated-entity)) or pick a different name; never silently create a duplicate (Rule 12). Otherwise create: `uip df entities create <Name> --file <schema.json> [--folder-key <key>] --output json`.
8. **Verify:** `uip df entities get <id> --output json` (`EntityClass` = `Federated`), then a small `records list` (or `records query`) to confirm the entity reads — a bad `method` fails here, not at create (Rule 4 / Rule 8).

## Create body (`--file` / `--body`)

Connector-agnostic — the same shape works for any IS connector (Salesforce, SAP, HubSpot, ServiceNow, …). Only the resolved values differ (`<connectorKey>`, `<objectName>`, field names, operator sets). Replace every `<…>` placeholder with values resolved in the End-to-end flow.

```json
{
  "displayName": "<Entity Display Name>",
  "entityClass": "Federated",
  "externalFields": [
    {
      "externalConnectionDetail": {
        "connectionId": "<connectionId from `is connections list`>",
        "elementInstanceId": "<ElementInstanceId — from the folder-scoped connections list, step 3>",
        "folderKey": "<connection FolderKey>",
        "connectorKey": "<connectorKey resolved in flow step 2>",
        "connectorName": "<ConnectorName from same row>",
        "connectionName": "<Name from same row>"
      },
      "externalObjectDetail": {
        "externalObjectName": "<objectName, e.g. Account>",
        "primaryKey": "<PK field name from `is resources describe`>",
        "isPrimarySource": true,
        "method": "<the `Method` string from `is resources describe --operation List`, verbatim — see Rule 4>"
      },
      "fields": [
        {
          "field": { "name": "<internal column — rename if reserved, Rule 11>", "type": "STRING" },
          "externalFieldMappingDetail": {
            "externalFieldName": "<source field name — keeps source spelling>",
            "externalFieldType": "<source dataType: string|integer|number|boolean|date|datetime>",
            "directionType": 0,
            "searchability": { "searchable": true, "supportsOperators": { "searchableOperators": ["=", "in", "LIKE"] } },
            "isRequiredForRead": false,
            "sortable": true
          }
        }
      ]
    }
  ],
  "sourceJoinConditionDetails": []
}
```

- `field` is the internal column — same shape as a native field (`name` + friendly `type`; the SDK builds the SQL type). `externalFieldName` is the source field it maps to. The internal `name` is bound by the shared Name Validation (Rule 11) — rename reserved source names like `Id` to `IdField`; `externalFieldName` keeps the source spelling.
- `searchableOperators` are per-field and per-connector — copy them from that field's `SearchableOperators` in `is resources describe` (they vary: a `string` field may allow `["LIKE","in","="]`, a `number`/`date` field `["<=","<","=",">",">="]`). Do not hardcode the example set.
- `isPrimarySource` designates the root source of the join graph. Set `true` on exactly one source (single-source: the only source). Multi-source: mark one, the others `false`.
- For a **native source** entry (another DF entity as a source), replace `externalConnectionDetail` with `"nativeConnectionDetail": { "entityId": "<df-entity-id>", "folderKey": "<key>" }`, keep `primaryKey` in its `externalObjectDetail` (the native entity's own primary key, `Id`), and omit `method` (native sources have no connector operations catalog). `nativeConnectionDetail.folderKey` must be the folder where that native entity actually lives (resolve it via `entities list --include-folders`) — it is **independent of the new federated entity's own scope**. The federated entity can be created at **any scope** regardless of where its sources live: tenant-level (no `--folder-key`) or in any folder (`--folder-key <key>`), and the sources may sit in a different folder — every split (tenant↔folder, folder↔folder) is accepted and reads correctly. The only requirement is that the source-folder keys in `externalConnectionDetail`/`nativeConnectionDetail` point at where each source actually lives.

### Multi-source join — worked example (connector ⋈ native entity)

Two sources — a connector object and a native DF entity — joined on `<primaryObject>.<primaryJoinField> = <relatedObject>.<relatedJoinField>`. Note the **connection ids on the join** (Rule 7): the connector source by its `connectionId`, the native source by its **entity id**:

```json
"sourceJoinConditionDetails": [
  {
    "sourceObjectName": "<primaryObject>",
    "sourceJoinField": "<primary external field>",
    "sourceObjectConnectionId": "<primary source connectionId>",
    "joinType": "LeftJoin",
    "relatedSourceObjectName": "<relatedObject>",
    "relatedSourceJoinField": "<related external field>",
    "relatedSourceObjectConnectionId": "<related source connectionId — for a native source, its DF entity id>"
  }
]
```

- `sourceJoinField` / `relatedSourceJoinField` are the **external** source field names, even when the internal columns are renamed (Rule 11). `joinType` is `"LeftJoin"` (the numeric enum `0` works too).
- For a connector ⋈ connector join, both `*ConnectionId`s are IS `connectionId`s. For connector ⋈ native, the native side's id is the DF entity id (from `entities list`).

## Join graph (render in the CLI)

MANDATORY before every `entities create` (Rule 9). Render as ASCII in a monospace fenced code block — never an artifact or hosted page. Derive it from `sourceJoinConditionDetails` + each source's `fields[]`. Match the template below exactly.

Graph rules:
- Two boxes per join condition — primary source left, related source right; box header = `externalObjectName`.
- List every mapped field (`field.name`), one per line; mark the primary key `[PK]`.
- One arrow from the primary's join-key row to the related join key; list the related join key as its first field row so it aligns.
- **Multi-join → one diagram per condition, left box identical across all; never a star.** Stack vertically.

Single join (`<PrimarySource>` ⋈ `<RelatedSource>`):

```text
   +-----------------------------+              +-----------------------------+
   |  <PrimarySource>            |              |  <RelatedSource>            |
   +-----------------------------+              +-----------------------------+
   |  <keyField>       [PK]      |------------> |  <relatedKey>               |
   |  <fieldA>                   |              |  <fieldC>                   |
   |  <fieldB>                   |              +-----------------------------+
   |  <fieldC>                   |
   +-----------------------------+
```

Multiple joins — one diagram each, same left box:

```text
   +-----------------------------+              +-----------------------------+
   |  <PrimarySource>            |              |  <RelatedSourceA>           |
   +-----------------------------+              +-----------------------------+
   |  <keyField>       [PK]      |------------> |  <keyA>                     |
   |  <fieldA>                   |              |  <fieldA1>                  |
   |  <fieldB>                   |              +-----------------------------+
   +-----------------------------+

   +-----------------------------+              +-----------------------------+
   |  <PrimarySource>            |              |  <RelatedSourceB>           |
   +-----------------------------+              +-----------------------------+
   |  <keyField>       [PK]      |------------> |  <keyB>                     |
   |  <fieldA>                   |              |  <fieldB1>                  |
   |  <fieldB>                   |              +-----------------------------+
   +-----------------------------+
```

## Internal column: types & options

Each mapping's `field` is a real native column, so its `type` follows the same [`entity-schema.md` → Supported Field Types](entity-schema.md#supported-field-types) table and the UI-broken-type ban (Rule 12). Map the connector's `externalFieldType` (the `dataType` from `is resources describe`) to a UI-compatible DF type:

| Connector `dataType` | Internal `field.type` | Notes |
|---|---|---|
| `string` | `STRING` | Most connectors also return **date/datetime values as `string`** (e.g. Salesforce `CreatedDate` is `string`, with range operators) — keep `STRING` unless the connector explicitly types the field `date`/`datetime`. |
| `integer` | `DECIMAL`, `decimalPrecision: 0` | `INTEGER` is UI-broken (Rule 12) |
| `number` | `DECIMAL`, `decimalPrecision: 2` | pick precision for the data; confirm in the Rule 9 preview |
| `boolean` | `BOOLEAN` | |
| `date` | `DATE` | only when the connector types it `date` |
| `datetime` | `DATETIME_WITH_TZ` | `DATETIME` (no TZ) is UI-broken (Rule 12) |

**Field options on a read-only column.** The internal `field` accepts the native field-option keys, but a federated view never inserts rows — insert-time options are inert. Express read semantics through the **mapping**, not the column:

| Native option | On a federated internal field |
|---|---|
| `displayName`, `description`, `lengthLimit` (STRING) | Apply as native (cosmetic label / length) |
| `isRequired`, `isUnique`, `defaultValue` | **Inert** — no record writes occur here. Use `externalFieldMappingDetail.isRequiredForRead`, `searchability`, and `sortable` instead. |

## Updating a federated entity

`entities update <id>` edits the sources, fields, and joins of an existing federated entity. Pass **only the change** (a delta) — the SDK reads the current definition, merges the delta, and reposts the whole thing. **Never hand-author the full definition** (you'd drop everything you omit). To see current sources/fields/joins before building the delta, inspect with a **projected** `entities get` (`--output-filter`, Rule 13) — a full federated GET is large. Preview the change (Rule 9) — render the **full resulting** join graph (the existing joins from the projected `get` **plus** the delta, one diagram per condition, never a star — not just the join you're adding) — then re-verify with a projected `entities get` + a `records list` afterward (a bad mapping/`method` fails at read time, not update — Rule 4 / Rule 8).

Delta keys (in the `--body` / `--file` JSON):

| Goal | Delta | Notes |
|---|---|---|
| Add a field to a source | `addFieldsToSource: [{ sourceObjectName, fields: [{ field, externalFieldMappingDetail }] }]` | Maps a field that **already exists** on the source (a native column or a connector field) — it does not create the underlying field. Same `field` + full `externalFieldMappingDetail` shape as create (Rules 2, 3, 11). Works the same on native- and connector-backed sources. |
| Remove a mapped field | `removeFieldsFromSource: [{ sourceObjectName, fieldNames: [...] }]` | Destructive → `--yes --reason` (Rule 10 gate). |
| Change a field's mapping | `updateExternalFieldMapping: [{ sourceObjectName, fieldName, mapping: { searchable?, sortable?, directionType? } }]` | Merges into the existing mapping. |
| Add a source + join it in | `addExternalSources: [ <source, same shape as create> ]` **and** `addSourceJoins: [ <join> ]` | A new non-primary source **must** be joined to the graph in the same update, or the upsert fails ("not a connected dependency"). Supply `method` on connector sources. **Map the join key in the new source's `fields`** (and confirm the left source maps its side) — the join field is part of the schema, not implied by the join (Rules 7, 13). |
| Change an existing join | `updateSourceJoin: [{ sourceObjectName, relatedSourceObjectName, sourceJoinField?, relatedSourceJoinField?, joinType? }]` | Edits the join in place (identified by the two object names). Only supplied fields change. |
| Remove a source | `removeExternalSources: ["<objectName>"]` | Destructive → `--yes --reason`. **Its joins are removed automatically** (a join can't outlive its source) — there is no standalone remove-join. |

Rules that differ from create:
- You supply object **names** (not connection ids) for `updateSourceJoin` / `removeExternalSources` — the SDK resolves connection ids from the current definition. For `addSourceJoins` on a brand-new source, still pass `sourceObjectConnectionId` / `relatedSourceObjectConnectionId` (connector → `connectionId`, native → entity id) as in create (Rule 7).
- `joinType` accepts `"LeftJoin"` (string) or `0`.
- Entity metadata (`displayName`, `description`) updates as native: `entities update <id> --body '{"displayName":"…"}'`.

## Deleting a federated entity

`entities delete <id> [--folder-key <key>] --yes --reason "<why>"`. Inherits the destructive-op gate + dependent discovery of [`data-fabric.md` Rule 10](data-fabric.md#critical-rules) / [`entity-schema.md` → Deleting an Entity](entity-schema.md#deleting-an-entity): confirm explicitly, list inbound references first. Deleting removes the **view**, not the source data.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `500 Internal Server Error` on create | `directionType` sent as string, OR a bare `externalFieldMappingDetail` | Use numeric `directionType` (0/1) and include the full mapping metadata (Rules 2, 3) |
| `Required parameter 'Id' was not found in GET(List) parameters` on create | internal `field.name` uses a reserved column name — typically `Id`, the connector PK mapped 1:1 | Rename the internal column (`Id` → `IdField`); keep `externalFieldName` / `primaryKey` = `Id`. Validate all internal names against the shared Name Validation first (Rule 11) |
| Create succeeds but `records list` fails with `An internal error occurred` | `method` omitted or wrong — create does not validate it (Rule 4) | Set `externalObjectDetail.method` to the `Method` string from `is resources describe --operation List`, **verbatim**. To fix an existing entity, re-add the source with the correct `method` (`removeExternalSources` then `addExternalSources` + `addSourceJoins`) — there is no in-place `method` edit |
| Create succeeds but `records list`/`query` returns **0 rows with no error** (structure looks correct) | `externalConnectionDetail.elementInstanceId` was built empty — the connections-list cache dropped it (warm-cache CLI bug, flow step 3) | Re-fetch the connection with `uip is connections list <connectorKey> --folder-key <fk> --refresh --output json`, take `ElementInstanceId`, and rebuild the connector source with it (`removeExternalSources` then `addExternalSources` + `addSourceJoins`) |
| `external sources join conditions not making a connected dependency or having a cyclic dependency` on create | a join condition is missing `sourceObjectConnectionId` / `relatedSourceObjectConnectionId`, so the graph can't resolve that source by connection id | Add both connection ids to every `sourceJoinConditionDetails` entry (connector → `connectionId`, native → entity id); use a valid `joinType` (`"LeftJoin"`) and external field names — Rule 7 |
| Federated entity not in `entities list` | listing filtered to native | Use `--federated-only` or omit both class flags (Rule 10) |
| `records query` returns `400: Multi-entity joins (req.Joins) are not supported…` | cross-entity `joins` aren't supported on federated query | Drop `joins`; filter/sort/project work. A federated entity already merges its own sources — to combine it with another entity, add that as a source in the entity definition (Rule 7) rather than a query-time join |
| `records query` with `aggregates`/`groupBy` returns raw rows, no counts | aggregates are silently ignored on federated query | Aggregate the listed rows client-side (Rule 8) |
| Writes to the entity silently fail | federated entities are read-only | Read/query only; write at the source (Rule 8) |
