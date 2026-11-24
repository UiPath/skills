# Data Fabric

*Exact signatures, fields, and defaults: `dataFabricRead()`, `dataFabricCreate()`, `dataFabricUpdate()` and `dataFabricDelete()` for native CRUD, and `connector()` for operations the native family does not cover.*

## At a glance

```ts
.step('open', dataFabricRead({ entity: 'Invoices', resultMode: 'multiple',
  filters: [{ field: 'Status', value: 'Open' }], limit: 200, sort: { field: 'CreateTime' } }))
```

`resultMode: 'multiple'` publishes matches under `output.results` and selects read 1.4; plain `dataFabricRead()` reads one record on SDK-pinned 1.0. Wrong columns are dropped **SILENTLY**; `validate` passing is not evidence, so resolve columns with `uip df entities get` first. Delete publishes nothing. `Id`, `CreateTime`, `CreatedBy`, `UpdateTime`, and `UpdatedBy` are never writable. `fromRead` requires a single-record read. Folder-scoped entities use `entity: { name, folder: '<folder path>' }`; `check` prints the `prepare` command that records their keys ([below](#a-folder-scoped-entity-name-it-and-its-folder)).

Still connector-only: get-by-id when the whole long-text value is needed (native reads return a 10,000-character preview, [see below](#long-text-queries-return-a-10000-character-preview)), file record fields, and Record Created/Updated events. Use `connector('uipath-uipath-dataservice', …)` plus `registry prepare -f entityName=<Entity>`.

## One product, two surfaces

"Data Fabric" and "Data Service" are the same product: the tenant lists connector key `uipath-uipath-dataservice` as **UiPath Data Fabric**, and `uip df entities` manages both. Native `core.datafabric.*` covers all four CRUD verbs and needs neither connection binding nor `prepare`; use the connector only for unsupported operations.

| Operation | Surface |
| --- | --- |
| Query records, filters, limit, paging, sort | `dataFabricRead({ entity, filters, resultMode, limit, skip, sort, fields })` |
| Create | `dataFabricCreate({ entity, values })` |
| Update | `dataFabricUpdate({ entity, record, set })` |
| Delete | `dataFabricDelete({ entity, record })` |
| Get by id, whole field values | `connector('uipath-uipath-dataservice', 'get-entity-record-by-id', …)` ([Long text](#long-text-queries-return-a-10000-character-preview)) |
| File record field upload/download/delete | `connector('uipath-uipath-dataservice', 'upload-file-to-record-field' / 'download-file-from-record-field' / 'delete-file-from-record-field', …)` ([example](#a-file-field-connector-example)) |
| Record Created/Updated events | `onEvent(…)` on the same connector |

Only the bottom three are connector work. Route an entity needing one through the connector rather than mixing surfaces: mixing requires connection binding, a second payload shape, and separate debugging.

Data Fabric **events** (Record Created / Record Updated on an entity) are
Integration Service connector events on `uipath-uipath-dataservice`, not this
node family. They are curated events with the object built in, so do not pass
`object`: the registry serves them as `record-created-preview-` and
`record-updated-preview-`. Name the entity with `entity`, not `where`:
`onEvent({ connector: 'uipath-uipath-dataservice', event: 'record-created-preview-', connection, folder, entity: 'Invoices' })`
for a tenant entity, `entity: { name: 'Movie', folder: '<folder path>' }` for a
folder entity. A folder entity compiles to the picker Studio Web saves, so
packaging declares the entity in the solution and a deploy re-points it to the
copy it provisions in the deployment folder; `where: { folderEntityName }` writes
no picker and does neither. `check` reports `RESOURCE_UNRESOLVED` with the
`uip maestro registry prepare --entity <name> --folder-path <path>` that records
its keys; run it, then `check` again. `waitForEvent` takes `entity` the same way.
Needs `@uipath/maestro-builder-sdk` <NEXT_SDK_VERSION> or later; an older SDK has
no `entity` on an event (`check` reports `TS2353`),
<!--skill-flavor:event-entity-sdk-upgrade:start-->
so upgrade the copy `uip` resolves, local copy first, then global. From the
directory you run `uip` in (the workspace root), run
`node -e "console.log(require.resolve('@uipath/maestro-builder-sdk/package.json',{paths:[process.cwd()]}))"`.
When it prints a path, that `node_modules` (possibly in a parent directory) owns
the copy: run `npm install --save-dev @uipath/maestro-builder-sdk@latest` in the
directory holding it when a `package.json` sits beside it; otherwise tell the
user the path, and never create a `package.json`. On error, run
`npm install -g @uipath/maestro-builder-sdk@latest`. Then run `check` again.
<!--skill-flavor:event-entity-sdk-upgrade:end-->
See
[`event-trigger.md`](event-trigger.md#tenant-discovery--check-names-it-prepare-does-it).

## Long text: queries return a 10,000-character preview

`dataFabricRead` is a query, including read-one with an `Id` filter. For `MULTILINE_MAX`, it returns the first 10,000 characters plus `...[Truncated]`; nothing flags this, and `check`, `validate`, the run, and downstream steps succeed on cut text. `dataFabricCreate`'s `output` is also the preview. Never write that preview through `dataFabricUpdate`; omit the field from `set`, or the stored value becomes truncated and includes `...[Truncated]`.

For a 15,551-character value:

| Read path | Characters |
| --- | --- |
| `$vars.<create step>.output.<field>` | 10,014 (preview) |
| `dataFabricRead({ resultMode: 'multiple' })` → `output.results[i].<field>` | 10,014 (preview) |
| `dataFabricRead({ filters: [{ field: 'Id', value: … }] })` → `output.<field>` | 10,014 (preview) |
| `connector('uipath-uipath-dataservice', 'get-entity-record-by-id', …)` → `output.<field>` | 15,551 (whole) |

Read potentially long fields with connector `get-entity-record-by-id` ([The connector path](#the-connector-path-end-to-end)); short fields are whole through every path.

## The four verbs

```ts
.step('lookup', dataFabricRead({ entity: 'Invoices', filters: [
  { field: 'InvoiceId', value: input('invoiceId') },
  { field: 'Status', operator: '!=', value: 'Paid', or: true }, ] }))
.step('markPaid', dataFabricUpdate({ entity: 'Invoices',
  record: { fromRead: 'lookup' }, set: { Status: 'Paid', PaidBy: js`$vars.lookup.output.Approver` } }))
.step('logIt', dataFabricCreate({ entity: 'PaymentLog', values: { InvoiceId: input('invoiceId'), PaidOn: js`new Date().toISOString()` } }))
.step('purge', dataFabricDelete({ entity: 'Drafts', record: { byId: input('draftId') } }))
```

## Filters and targeting

A filter is `{ field, operator?, value, or? }`; `operator` defaults to `'='` and must be exactly one of `=` `!=` `>` `>=` `<` `<=` `contains` `starts with` `ends with` `in`. There is no `not in`, `not contains`, or null check; unsupported serialization takes down the whole query. `in` works only with `resultMode: 'multiple'`.

The query is disjunctive: `or: true` starts an alternative rather than joining one row to the one before it (ignored on the first row), each alternative ANDs its rows, and results are `alt1 OR alt2 OR …`. Express `(A OR B) AND C` as `(A AND C) OR (B AND C)`. Filter values cannot be blank or reference `$self`; either makes serialization refuse the whole query, publishes nothing, and strands downstream `$vars` reads; `check` rejects both. Choice-set filters require numeric `numberId`, never the label; labels silently match nothing.

`record` targets update and delete and takes exactly one of `{ byId: '<record id>' }` (literal or expression) or `{ fromRead: '<step name>' }` (the preceding single-record `dataFabricRead` result). A multiple-record query is refused as a write target as a no-op: validation and run are green, but nothing writes. `check` reports `DATAFABRIC_FROMREAD_UNKNOWN` for a nonexistent read step and `DATAFABRIC_FROMREAD_MULTIPLE` for a multiple read.

`set` and `values` map fields to literals or expressions and are rejected when empty. `values` is also rejected when every value is BLANK. Blank create values are omitted so defaults apply; an all-blank create writes nothing and runs green. Use a real value, not a placeholder.

Type each flow input by its destination field. Run `uip df entities get <id> --output json`; types are at `Data.Fields[].FieldDataType.Name`, and use `input('<name>')`:

| Field type | Flow input |
| --- | --- |
| `STRING`, `MULTILINE_TEXT`, `UUID`, `DATE`, `DATETIME` | `types.string` |
| `DECIMAL`, `INTEGER` | `types.number` |
| `BOOLEAN` | `types.boolean` |
| `FILE` | none — declare `types.file` and upload with connector `upload-file-to-record-field` ([example](#a-file-field-connector-example)) |

System columns `Id`, `CreateTime`, `CreatedBy`, `UpdateTime`, and `UpdatedBy` are never writable. Writes to them are rejected, logged only, leave the row unchanged, and run green; `check` reports `DATAFABRIC_SYSTEM_COLUMN`. Blank create values are omitted; blank update values write explicit `null`, which non-nullable columns reject. Check nullability with `uip df entities get`.

## Query-many needs `resultMode`, and `resultMode` needs 1.4

`core.datafabric.read` began as read-one ("Read entity") and became read-one-or-many at **1.4** ("Query entity records"). `resultMode: 'single'` publishes one record under `output`; `resultMode: 'multiple'` publishes records under `output.results`. Plain `dataFabricRead()` emits SDK-pinned 1.0; passing `resultMode` selects 1.4. `dataFabricRead({ resultMode }, { version: '1.0' })` is refused at compile time.

```ts
.step('open', dataFabricRead({ entity: 'Invoices', resultMode: 'multiple',
  filters: [{ field: 'Status', value: 'Open' }] })) // → core.datafabric.read@1.4
.loop('each', js`$vars.open.output.results`, (b) => b./* … */)
```

## Paging a list query

`limit` is always applied — omitting it resolves to **100** — and **1000 is a
hard ceiling**: `check` refuses a larger value (`DATAFABRIC_LIMIT_RANGE`),
because the run would silently return only 1000. Cover a bigger entity by
paging with `skip`, and pair any limit with `sort` or the slice is arbitrary.

`limit`, `skip`, `sort`, and `fields` are list-query options; `check` refuses them on single-record reads.

```ts
.step('page1', dataFabricRead({ entity: 'Invoices', resultMode: 'multiple',
  limit: 1000, skip: 0, sort: { field: 'CreateTime', direction: 'desc' },
  fields: ['Id', 'Status'] }))
```

Audit columns are `Id`, `CreateTime`, `CreatedBy`, `UpdateTime`, `UpdatedBy`; there is no `CreatedAt`. `validate` does not catch a nonexistent sort column.

## A folder-scoped entity: name it and its folder

Tenant-scoped entities use `entity: '<Name>'`; folder-scoped entities use the Orchestrator folder **path**, never keys:

```ts
.step('read', dataFabricRead({ entity: { name: 'Orders', folder: 'Finance/Prod' }, resultMode: 'multiple' }))
```

SDK 6.73.0 or later is required. An older SDK refuses `{ name, folder }` and has no key-less `prepare`,
<!--skill-flavor:data-fabric-entity-ref-sdk:start-->
so upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
If `uip maestro registry prepare --entity …` says `missing required argument 'connector-key'`, run the same command as `npx flow-sdk registry prepare --entity …`.
<!--skill-flavor:data-fabric-entity-ref-sdk:end-->

`check` reports `RESOURCE_UNRESOLVED` and prints the command recording keys. Run it, then run `check` again:

```bash
uip maestro registry prepare --entity Orders --folder-path Finance/Prod
# Entity    Orders   (Finance/Prod, remote)
# Recorded  ./.flow-sdk/resources.json
```

`compile` writes the folder key, resource key, two `resource: 'Entity'` binding rows, and the entity row in `bindings_v2.json`; `uip solution resources refresh` then declares it in the solution. Do not type keys; compile refuses an unrecorded entity.

Run `prepare` from the directory used for `check` and `compile`, normally `<Solution>/<Name>/`; it records `./.flow-sdk/resources.json`. Within a solution (a `.uipx` in that folder or above), it searches the solution before the tenant.

`prepare` lists and stops; it never picks:

- **No `folder`:** it searches every folder. One match records the folder and names it to pin in source. Multiple matches list each `folder:`; write the intended one and run `prepare` again.
- **Tenant-level match:** no `prepare`; write `entity: '<Name>'` as output says.
- **Matching:** a name matches exactly, case included; a `folder` path ignores case and a leading or trailing slash. A folder without that entity returns `RESOURCE_NOT_IN_FOLDER` and lists folders containing it.
- **No match:** it lists near misses and listings to check. If none is intended, ask the user; never create an entity unless the user asks. Creating one in the requested scope follows [/uipath:uipath-platform — local-entities.md](../../uipath-platform/references/data-fabric/local-entities.md), then run `prepare` again.
- **Recorded row older than a day:** it counts as missing; `check` asks for `prepare` again.

### An entity the solution authors itself

An entity from `uip df entities create <Name> --local` exists only in the solution until deployment and resolves the same way. Write `{ name: '<Name>' }`; from the Flow project folder, run the `prepare` printed by `check`. It reads the solution, records the entity in placeholder folder `99999999-9999-9999-9999-999999999999` (replaced by `flow debug` and `solution deploy`), and names `folder: 'solution_folder'` to pin.

Do not look it up on the tenant before deploy. Skipping that `prepare` leaves the keys out and makes it tenant-scoped; the run fails with `Entity <Name> does not exist`, naming an entity that does exist, and `flow validate` reports `INLINE_ENTITY_UNBOUND`. Although its message suggests `uip maestro flow node configure` (which edits compiled `.flow`), fix `.flow.ts` in a builder-SDK project or the next `compile` reverts it. Creating and modelling follows [/uipath:uipath-platform — local-entities.md](../../uipath-platform/references/data-fabric/local-entities.md).

A decompiled flow uses `folderKey` and `resourceKey`; leave that form unless the entity changes.

**Debugging:** `uip maestro flow debug` works once for a solution with a local entity and fails from the second run because each later run overwrites the same Studio Web solution, which Studio Web cannot do for one holding an Entity project. Tell the user up front and recommend the UiPath extension for VS Code for repeated debugging. `pack` / `publish` / `deploy run` are unaffected.

## A delete publishes nothing

`core.datafabric.delete` declares no outputs. `$vars.<delete>.output` is undefined, and `check` rejects that read with `DATAFABRIC_DELETE_HAS_NO_OUTPUT`. Take needed data from the `dataFabricRead` step that found the record, before deletion.

## The connector path, end to end

Connector entity-operation body fields come from the entity, so the static library cannot carry them. Resolve the schema once; otherwise `compile` refuses unknown inputs:

```bash
uip maestro registry prepare uipath-uipath-dataservice --action get-entity-record-by-id \
  -f entityName=ContractRegistry
# → .flow-sdk/connectors-local/ + .flow-sdk/bindings.json, with the entity's own fields as inputs
```

```ts
.step('byId', connector('uipath-uipath-dataservice', 'get-entity-record-by-id',
  { entityName: 'ContractRegistry', recordId: input('id') },
  { connection: 'dataservice', folder: 'shared' }))
```

Full rules, including parent-field (`GenerateSchema` over `entityName`) shapes: [`connector-params.md`](connector-params.md).

### A file field: connector example

File-record-field operations take a Flow file input ([`connector-params.md` § file uploads](connector-params.md#file-uploads-are-multipart-flow-inputs)):

```bash
uip maestro registry prepare uipath-uipath-dataservice \
  --action upload-file-to-record-field \
  --resolve entityName:displayName=LoanApplication
# → .flow-sdk/connectors-local/uipath-uipath-dataservice.ts with typed descriptors
```

```ts
import { UploadFileToRecordField, DownloadFileFromRecordField }
  from './connectors-local/uipath-uipath-dataservice.ts';
const BIND = { connection: 'dataservice', folder: 'shared' } as const;

.input({ recordId: types.string, doc: types.file })
.step('attach', connector(UploadFileToRecordField, {
  entityName: lookup(UploadFileToRecordField, 'entityName').byDisplayName('LoanApplication'),
  recordId: input('recordId'), _fieldName: 'Contract', file: input('doc'),
}, BIND))
.step('fetch', connector(DownloadFileFromRecordField, {
  entityName: lookup(DownloadFileFromRecordField, 'entityName').byDisplayName('LoanApplication'),
  recordId: input('recordId'), _fieldName: 'Contract',
}, BIND))
```

`entityName` is a LOOKUP through `lookup(...).byDisplayName(...)`; do not paste a system name. The FILE column is `_fieldName` (leading underscore required); `fieldName` fails `check`. Debug CLI uploads with `--attachment doc=<path>` ([`operate.md` § types.file](operate.md)); download publishes the file reference under `output.Response`. Delete has the same shape with only the action name changed.

`file:` accepts any upstream file reference, including `out('fetch', 'Response')`:

```ts
.step('mirror', connector(UploadFileToRecordField, {
  entityName: lookup(UploadFileToRecordField, 'entityName').byDisplayName('LoanApplication'),
  recordId: input('mirrorId'), _fieldName: 'Contract', file: out('fetch', 'Response'),
}, BIND))
```

The same source rule applies to `documentClassify`, `dynamicExtract`, `ixpExtract`, `summarize`, and `batchTransform`: the file field accepts a `types.file` input, `out('<step>', '<fileField>')`, or any step whose declared output is a file. Runtime values are file references, never bytes.

<!--skill-flavor:operation-doc:start-->
**Read the operation's own doc before guessing anything.**
Run:
```bash
uip maestro registry describe uipath.connector.uipath-uipath-dataservice.create-entity-record
```
It prints the connector page (UiPath Data Fabric), HTTP route `POST /v2/{entityName}/CreateEntityRecord`, and exact `prepare-connector … -f entityName=<value>` line before anything is inferred.
<!--skill-flavor:operation-doc:end-->

## Evidence boundary

Entity and field names are tenant data: copy them from the scenario or tenant, never invent them. Names are case-sensitive; unmatched columns are dropped rather than rejected, so a wrong name validates green and writes nothing. Resolve first:

```bash
uip df entities list --native-only --include-folders --output json  # writes need a NATIVE entity
uip df entities get <entity-id> --output json                       # exact column names and types
```

The platform documents `limit`/`skip`/`sort`, but the local engine's converter does not apply them; they reach the file as `_recordLimit`/`_skip`/`_sort` and are read at run time, so `flow-debug` is not evidence either way.

Offline `validate` proves only emitted `entityConfig` shape. It does not verify column existence, writability, value type, native versus federated entity, or whether a `byId` id matches; all validate clean and can fail silently at runtime. The tenant is evidence.

Typed columns also need the canvas `_outputSchema` snapshot for coercion, and dotted related paths need `_entityFields`. SDK authors provide neither: keep from-scratch nodes to the entity's own columns with string or expression values, and let the designer populate snapshots on first open.
