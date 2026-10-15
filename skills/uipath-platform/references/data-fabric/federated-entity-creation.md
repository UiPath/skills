# Federated Entity Creation (from connectors)

Create a Data Fabric **federated** entity — a read-only view over an external system reached through an **Integration Service (IS) connection**, or over another existing DF entity. Data lives in the source; the entity mirrors it. The exact set of supported connectors is tenant-driven — never hard-coded here; always resolve it live from `uip df connectors list` (Rule 5).

## When this applies (triggers)

Route here when the user wants an entity **backed by an external source**, e.g.:
- "create an entity from `<connector>` `<object>`" (e.g. "from Salesforce Account", "from ServiceNow incident", "from Data hub `<object>`") — the connector must be on the tenant's federated allow-list (Rule 5); if it isn't, stop and offer the supported list rather than guessing.
- "make a **federated** entity", "a read-only view over `<external object>`"
- "create a **virtual data object**", "a **zero-copy** entity / view over `<source>`" — "virtual data object" and "zero-copy" are UiPath product terms for a federated entity; treat them as synonyms and route here.
- "pull `<object>` from `<connector>` into Data Fabric as an entity"
- an entity sourced from an **existing DF entity** (native source).

For a plain **native** entity (columns stored in UiPath, no connector) → [`entity-schema.md`](entity-schema.md). For inserting/querying records → [`records-query.md`](records-query.md).

## The CLI builds the payload — you pass only the choices

**Pass only the body described below; the CLI builds the API payload.** It reads Integration Service itself and derives every piece of metadata. You pass only what a caller must *choose*; the CLI fills the rest.

| You provide (per source) | The CLI derives from IS |
|---|---|
| `connectionId` (connector) **or** `entityId` (native) | connection metadata: `elementInstanceId`, `connectorKey`, `connectorName`, `connectionName`, connection `folderKey` |
| `object` (connector — the table/object name) | `primaryKey`, the operations `method` catalog, per-field types, `searchable` + `searchableOperators` |
| `fields` (external field **names**) | internal column names (camelCase; reserved names like `Id` renamed to `IdField`), internal `type` (UI-safe mapping), `directionType` (`ReadOnly`), `isRequiredForRead`, `sortable`, `searchable` + `searchableOperators` (per-field, from the IS object's List-op metadata — override with `searchable` / `searchableOperators` on the field; non-searchable fields are indexed as `searchable: false`) |
| `joins` (`{source,relatedSource,sourceField,relatedField}` — names) | both join connection ids, `joinType` (`LeftJoin`), and auto-maps a join field onto a source that doesn't map it yet |

So the create/update body is small. The CLI also **validates client-side** before the API call — unknown field, missing primary key, reserved name, ambiguous source, non-array delta — and surfaces backend errors in the failure envelope's `Instructions`.

## Critical rules

1. **Minimal body.** Each source is `{ connectionId, object, fields }` (connector) or `{ entityId, fields }` (native). Optional top-level `joins`, `displayName`, `description`, `isRbacEnabled`. `entityClass` is inferred from a non-empty `externalFields` — don't set it (and never set it to anything but `Federated` when `externalFields` is present, or the CLI rejects it). **`isAnalyticsEnabled` is not valid for federated entities** — never include it in a federated create or update body.
   - **Primary source:** you don't set it. The backend derives it from the joins: it is the one source every join starts from. A multi-source entity needs `joins` ([Rule 7](#critical-rules)); the backend rejects one without them.
2. **`fields` entries are external field names**, or an object to override one column: `{ "source": "<external name>", "name"?, "type"?, "direction"?, "searchable"?, "sortable"?, "requiredForRead"? }` — only `source` is required. Override only when you must (e.g. force a `type`); otherwise pass the bare name and let the CLI derive everything.
3. **The mapped field set is the user's choice — ask; never default it.** When the user names a source but not its columns (e.g. "add a Salesforce Contact"), you MUST ask which fields to map *before* building the body: present that object's fields (`uip is resources describe <connectorKey> <Object> --connection-id <id> --operation List --output json` → `ResponseFields[].Name`; for a native source, its `Fields` minus system fields) and let the user pick. Use `AskUserQuestion` (dropdown) when your runtime offers it; otherwise print the numbered options and wait on a reply — never infer a "sensible" set. Repeat per source. Skip the ask only when the user enumerated columns or said "all"/"you choose".
4. **Never silently pick a connection — ask when there's a choice.** From `uip is connections list <connectorKey> --all-folders --refresh --output json`, **auto-select only when exactly one connection is `Enabled`** (announce it). If more than one matches or is `Enabled`, prompt the user (label `Name` + `State`, payload `Id`; use `AskUserQuestion` when available, else a numbered list). The `Id` is the `connectionId` you pass. This is the **dynamic** per-connection check — distinct from the static tenant allow-list in Rule 5.
5. **A connector can back a federated entity only if it's on the tenant's federated allow-list — gate on `uip df connectors list`, never the full IS catalog.** This is the **static** (tenant-level, feature-flag-driven) gate: `uip df connectors list --output json` hits the same `datafabric_/api/FeatureFlag/supportedConnectors` endpoint the UiPath Data Fabric UI uses, and returns `Data: [{ ConnectorKey }]` (PascalCase in `--output json`) — the tenant's `fqs-connectors-list` subset. Each `ConnectorKey` is a real IS connector key. Because this is the single source of truth, the list naturally reflects the tenant — e.g. a connector the tenant doesn't support will not appear and the picker won't surface it. Pair with Rule 4 (per-connection enabled check) for the full gate.
   - **User named no connector** → present the allow-list `ConnectorKey` values in a dropdown (payload = `ConnectorKey`; use `AskUserQuestion` when available, else a numbered list).
   - **User named a connector** → resolve its key, confirm it exact-matches a `ConnectorKey` in the list. **Not on it → stop** and offer the supported list.
   - **Empty list** ⇒ the flag is unset (not "none supported"): tell the user, skip the gate, resolve from the full catalog. (The backend is fail-open when the flag is unset.)
   - Applies to **connector** sources only; a **native** source (another DF entity) is not gated here.
6. **Native vs connector source.** A connector source needs `connectionId` + `object`; a native source (backed by another DF entity) needs `entityId` and, if that entity is folder-scoped, `folderKey`. A source with **both** `connectionId` and `entityId` is rejected. A native source's primary key is its own `Id` — the CLI keeps it available so you can join on it.
7. **Joins.** `joins: [{ source, relatedSource, sourceField, relatedField, sourceConnectionId, relatedConnectionId }]` — `source`/`relatedSource` are `object` names, `sourceField`/`relatedField` are the **external** source field names, and `sourceConnectionId`/`relatedConnectionId` are each side's connection id (a connector `connectionId`, or the `entityId` for a native source). **All six keys are required on every join** — you already have the ids from the sources, and an entity can hold two sources with the same object name on different connections, so the name alone can't identify a side. The CLI forces `LeftJoin` and auto-maps a join field onto a source that doesn't already map it. The join graph must follow these rules (N sources → N−1 joins):
   - **Same `source` in every join.** Every join starts from the same source (same object **and** connection id). That source is the primary; the backend derives it from the joins, so there is no primary to set.
   - **Every other source is joined exactly once, directly to the primary**, as `relatedSource`. No chaining (`A→B→C`), no join between two non-primary sources, no source left unjoined, and the primary is never a `relatedSource`.
   - **One field pair per source pair.** Composite/multi-field joins between the same two sources are rejected; use a single field pair.
   - **Join field types must be compatible.** The backend rejects e.g. a `string`↔`integer` join; pick fields of matching type.
8. **Confirm before creating or updating.** Render the **complete** join graph ([Join graph](#join-graph-render-in-the-cli)) — every source and **every** join in the *resulting* state — plus the fields per source, then wait for explicit approval. Never auto-create/update. On update, the graph is the existing joins (from a projected `get`, Rule 11) **plus** the delta. One diagram per join condition, stacked vertically.
9. **Federated entities are read-only.** Never `records insert/update/delete` — write at the source. Reads work through `records list` (`--limit`/`--cursor`/`--offset`) and `records query` (`filterGroup`, `selectedFields`, `sortOptions` — same shape as native, see [filter contract](filter-platform-contract.md)). Federated-only limits: `aggregates`/`groupBy` are silently ignored (aggregate client-side), and multi-entity `joins` are rejected `400` (combine sources in the entity definition instead).
10. **List federated entities** with `entities list --federated-only` (mutually exclusive with `--native-only`; omit both for all).
11. **`list`/`get` responses are large — project with `--output-filter`, never dump.** JMESPath, **PascalCase keys**, applied to `Data` directly (no `Data` prefix). Array (`list`) → start with `[]`/`[?…]`; object (`get`) → start with a key. Recipes:
    - **Resolve a native source by name + its fields in one call:** `uip df entities list --include-folders --output-filter "[?Name=='<name>'].{Id:Id,Name:Name,FolderId:FolderId,Fields:Fields[].Name}" --output json`. `Id` is the native source's `entityId`, `FolderId` its `folderKey`.
    - **Inspect a federated entity before update:** `uip df entities get <id> [--folder-key <key>] --output-filter "{name:Name, sources:ExternalFields[].ExternalObjectDetail.ExternalObjectName, fields:ExternalFields[].Fields[].{internal:FieldMetaData.Name, external:ExternalFieldMappingDetail.ExternalFieldName}, joins:SourceJoinCriterias}" --output json`
12. **Folder scope is the new entity's own choice — never inferred from a source.** Follow [`data-fabric.md` Rule 19](data-fabric.md#critical-rules) *Mandatory scope-prompt flow* verbatim: first ask **only** `Tenant level (no --folder-key)` vs `Folder-scoped`; only then, if folder-scoped, ask which folder (offer `List accessible folders` → `uip or folders list --output json`, once). A source's folder (connection `FolderKey` or a native source's `folderKey`) scopes the *source*, not the new entity. The chosen `Key` becomes `--folder-key` on `create` and every follow-up `get`/`records list`.
13. **Check for a duplicate before create** (Rule 12 of data-fabric): projected list `uip df entities list [--folder-key <key>] --output-filter "[?Name=='<Name>'].{Id:Id}" --output json`. If it returns a row, stop — offer to update it or pick another name.

## End-to-end flow

1. **Detect** the connector / object / source entity from the prompt. Users name the integration ("Salesforce"), not the `connectorKey`. If no connector/source is named, go straight to the allow-list picker (Rule 5).
2. **Gate on the allow-list (Rule 5)** — `uip df connectors list --output json`. No connector named → picker; named → resolve + confirm on the list; empty list → skip gate.
   **Resolve the `connectorKey` from the friendly name** — never guess (`uip is connectors list --filter <name> --output json` → match by `Name`, use its `Key`; `--filter` is a substring match on name AND key, so it returns false positives — ask when ambiguous).
   **Resolve folder scope** (Rule 12) — ask; do not infer from a source.
3. **Resolve the source:**
   - Connector: `uip is connections list <connectorKey> --all-folders --refresh --output json` → pick the connection (Rule 4), take its `Id`. `uip is resources list <connectorKey> --connection-id <id> --output json` → objects. `uip is resources describe <connectorKey> <Object> --connection-id <id> --operation List --output json` → `ResponseFields[].Name` **for the field picker only**.
   - Native: resolve the entity + its columns via the projected `entities list` (Rule 11), drop system fields (`Id`, `CreatedBy`, `CreateTime`, `UpdatedBy`, `UpdateTime`, `RecordOwner`, `Version`).
4. **Field picker (Rule 3)** — present the source's fields, let the user choose. Repeat per source.
5. **(Optional) more sources + joins** — repeat step 3 per source; define joins by name (Rule 7).
6. **Preview → confirm** (Rule 8) — join graph + fields per source, wait for approval.
7. **Duplicate check, then create** (Rule 13): `uip df entities create <Name> --file <body.json> [--folder-key <key>] --output json`.
8. **Verify:** `uip df entities get <id> --output-filter "{class:EntityClass, sources:ExternalFields[].ExternalObjectDetail.ExternalObjectName}" --output json` — `EntityClass` is `Federated`/`Native`/`Case` (the native-vs-federated field). **Do not use `EntityType`** — it's the object kind and returns the generic `"Entity"` for both native and federated. Then a small `records list` to confirm it reads.

## Create body (`--file` / `--body`)

Connector-agnostic — same shape for any IS connector. Replace `<…>` with values resolved above.

```json
{
  "displayName": "<Entity Display Name>",
  "externalFields": [
    { "connectionId": "<connectionId>", "object": "<objectName>", "fields": ["<field1>", "<field2>"] }
  ],
  "joins": []
}
```

- **Native source** entry: `{ "entityId": "<df-entity-id>", "fields": ["<col1>"] }` (add `"folderKey": "<key>"` if that entity is folder-scoped).
- **Per-field override** (only when needed): replace a field name string with `{ "source": "<external name>", "name": "<internal>", "type": "DECIMAL", "direction": "ReadAndWrite", "searchable": true, "sortable": false, "requiredForRead": true }`. Every key but `source` is optional and overrides the CLI's derived value.
- The CLI derives the primary key, operations catalog, connection metadata, internal names (renaming reserved ones), types, and searchability. You don't supply any of it.

### Multi-source join — worked example (connector ⋈ native entity)

```json
{
  "displayName": "Accounts with owner",
  "externalFields": [
    { "connectionId": "<sf-connectionId>", "object": "Account", "fields": ["Id", "Name", "OwnerId"] },
    { "entityId": "<users-entity-id>", "fields": ["Name", "Id"] }
  ],
  "joins": [
    { "source": "Account", "relatedSource": "<users-object-name>", "sourceField": "OwnerId", "relatedField": "Id", "sourceConnectionId": "<sf-connectionId>", "relatedConnectionId": "<users-entity-id>" }
  ]
}
```

- `sourceField`/`relatedField` are external source names. If a source doesn't already map its join field, the CLI adds it — but listing it in `fields` is clearer. Join field types must match (Rule 7).

## Join graph (render in the CLI)

MANDATORY before every `entities create`/`update` (Rule 8). ASCII in a monospace fenced block — never an artifact. Derive from `joins` + each source's `fields`.

- Two boxes per join condition — `source` left, `relatedSource` right; box header = object name.
- List every field, one per line; mark the primary key `[PK]`.
- One arrow from the source join field to the related join field.
- **Multi-join → one diagram per condition, left box identical.** Stack vertically.

```text
   +-----------------------------+              +-----------------------------+
   |  <source>                   |              |  <relatedSource>            |
   +-----------------------------+              +-----------------------------+
   |  <keyField>       [PK]      |------------> |  <relatedKey>               |
   |  <fieldA>                   |              |  <fieldC>                   |
   |  <fieldB>                   |              +-----------------------------+
   +-----------------------------+
```

## Field type overrides (optional)

The CLI maps the source type to a UI-safe DF type automatically. Override with a per-field `type` only when the derived one is wrong for your data:

| Source `dataType` | CLI-derived internal type | Notes |
|---|---|---|
| `string` | `STRING` | most connectors return date/datetime as `string` |
| `integer`, `int` | `DECIMAL` (precision 0) | `INTEGER` is UI-broken |
| `number`, `decimal`, `float`, `double` | `DECIMAL` (precision 2) | |
| `boolean` | `BOOLEAN` | |
| `date` | `DATE` | |
| `datetime` | `DATETIME_WITH_TZ` | `DATETIME` (no TZ) is UI-broken |

A native decimal source keeps its own precision. Only `INTEGER`/`FLOAT`/`DOUBLE`/`UUID`/`DATETIME` are UI-broken — avoid them in a `type` override ([`entity-schema.md` → UI-broken types](entity-schema.md#ui-broken-types--do-not-use)).

## Updating a federated entity

`entities update <id>` edits an existing federated entity. Pass **only the delta** — the CLI reads the current definition, derives metadata for the delta, merges, and reposts. Inspect first with a projected `get` (Rule 11). Preview the **full resulting** graph (Rule 8), then re-verify with a projected `get` + `records list`.

Delta keys (in `--body` / `--file` JSON). **Every reference to an existing source needs both `sourceObjectName` and `sourceConnectionId`** — a connector `connectionId`, or the `entityId` for a native source. An entity can hold two sources with the same object name on different connections, so the name alone is ambiguous.

| Goal | Delta | Notes |
|---|---|---|
| Add fields to an existing source | `addExternalFields: [{ sourceObjectName, sourceConnectionId, fields: ["<name>", …] }]` | `fields` are external names (or override objects, Rule 2). The field must exist on the source. |
| Add a source + join it in | `addExternalSources: [ { connectionId, object, fields } \| { entityId, fields } ]` **and** `joins: [ { source, relatedSource, sourceField, relatedField, sourceConnectionId, relatedConnectionId } ]` | Same source + join shape as create (join to the **primary**; all names and connection ids required). A new source must be joined into the graph in the same update. The CLI auto-maps join fields (including onto the existing source). |
| Remove a mapped field | `removeExternalFields: [{ sourceObjectName, sourceConnectionId, fieldNames: [...] }]` | Destructive → `--yes --reason`. `fieldNames` are the entity's column names. A source must keep at least one field (to swap all of them, remove and add in the same call). Joins that use a removed field are removed with it, so pass `replaceJoins` if that leaves a source unjoined. |
| Remove a source | `removeExternalSources: [{ sourceObjectName, sourceConnectionId }]` | Destructive → `--yes --reason`. Its joins are removed with it. Removing the primary source needs `replaceJoins` to re-join the rest. The entity must keep at least one source. |
| Change the join fields of an existing join | `updateSourceJoin: [{ sourceObjectName, sourceConnectionId, relatedSourceObjectName, relatedSourceConnectionId, sourceJoinField?, relatedSourceJoinField? }]` | Edits only the join fields, in place; identified by both sides' (object name, connection id); only supplied fields change. It cannot change which sources the join connects or its direction, and the join type is always a left join. To change the primary, use `replaceJoins`. |
| Change the primary source | `replaceJoins: [ { source, relatedSource, sourceField, relatedField, sourceConnectionId, relatedConnectionId } ]` | The **complete** new join set, in the same shape as `joins`. The primary is the source every join starts from, so root every join at the new primary; every other source is the related side of exactly one join. Destructive → `--yes --reason`. Cannot be combined with `joins` or `updateSourceJoin`. A join cannot be removed on its own: every source except the primary has to stay joined. |
| Replace a source's connection | `updateExternalConnection: [{ sourceObjectName, sourceConnectionId, newConnectionId }]` | `sourceConnectionId` is the **current** connection (identifies the source); `newConnectionId` is the one to switch to. The CLI checks that the new connection is a different one, is for the **same connector**, is **enabled**, and exposes the object, then looks up its element instance id, folder key and name itself. Keeps the source's object, fields, and joins. Connector sources only — not native. A mapped field the new connection lacks is **dropped**, along with any join that uses it. The CLI prints a warning naming the fields (also in `Data.Warnings`) — show it to the user — and, because it deletes columns, refuses to run without `--yes --reason` (destructive → confirm with the user first). If dropping leaves a source unjoined, pass `replaceJoins` in the same update. |
| Entity metadata | `{ "displayName": "…", "description": "…" }` | As native. `isAnalyticsEnabled` is not valid for federated entities — the CLI rejects it on create and update. |

You pass object **names**, connection/entity ids, and external field names — the CLI resolves the operations catalog and field metadata itself. `joins` on update becomes the added join(s) for a new source; use `updateSourceJoin` to change the fields of an existing join and `replaceJoins` to change the primary.

## Deleting a federated entity

`entities delete <id> [--folder-key <key>] --yes --reason "<why>"`. Inherits the destructive-op gate of [`data-fabric.md` Rule 10](data-fabric.md#critical-rules): confirm explicitly, list inbound references first. Deleting removes the **view**, not the source data.

## Troubleshooting

Only errors whose fix isn't clear from the message:

| Symptom | Cause | Fix |
|---|---|---|
| `Field '<x>' is not on object '<obj>'` (client-side) | field name typo, or a field not in the object's List response | Check the name against `is resources describe … ResponseFields[]`; or set an explicit `type` on the field to map it anyway |
| HTTP 404 `Connection [...] is invalid or you do not have access` | bad/again-scoped `connectionId` | Re-resolve via `is connections list <key> --all-folders --refresh` |
