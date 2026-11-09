# Data Fabric

*Exact signatures, fields, and defaults: `dataFabricRead()`, `dataFabricCreate()`, `dataFabricUpdate()` and `dataFabricDelete()` for native CRUD; use `connector()` for operations the native family does not cover.*

## At a glance

```ts
.step('open', dataFabricRead({ entity: 'Invoices', resultMode: 'multiple',
  filters: [{ field: 'Status', value: 'Open' }], limit: 200, sort: { field: 'CreateTime' } }))
```

`resultMode: 'multiple'` publishes matches at `output.results` and selects read 1.4; plain `dataFabricRead()` remains 1.0 and reads one record. Wrong columns are dropped **SILENTLY**; `validate` proves nothing. Resolve columns with `uip df entities get` first. Delete publishes nothing. System columns (`Id`, `CreateTime`, `CreatedBy`, `UpdateTime`, `UpdatedBy`) are never writable. `fromRead` requires a single-record read. Folder-scoped entities use `entity: { name, folder: '<folder path>' }`; `check` prints the one `prepare` that records its keys ([below](#a-folder-scoped-entity-name-it-and-its-folder)).

Whole long-text values (native reads return a 10,000-character preview; [see below](#long-text-queries-return-a-10000-character-preview)), file record fields, and Record Created/Updated events remain connector-only. Use `connector('uipath-uipath-dataservice', …)` plus `registry prepare -f entityName=<Entity>`.

## One product, two surfaces

“Data Fabric” and “Data Service” are the same product. The tenant connector key is `uipath-uipath-dataservice` (**UiPath Data Fabric**); `uip df entities` manages both. Native `core.datafabric.*` covers all four CRUD verbs without connection binding or `prepare`; use the connector only for unsupported operations.

| Operation | Surface |
| --- | --- |
| Query records, filters, limit, paging, sort | `dataFabricRead({ entity, filters, resultMode, limit, skip, sort, fields })` |
| Create | `dataFabricCreate({ entity, values })` |
| Update | `dataFabricUpdate({ entity, record, set })` |
| Delete | `dataFabricDelete({ entity, record })` |
| Get by id, whole field values | `connector('uipath-uipath-dataservice', 'get-entity-record-by-id', …)` ([Long text](#long-text-queries-return-a-10000-character-preview)) |
| Upload/download/delete a file record field | `connector('uipath-uipath-dataservice', 'upload-file-to-record-field' / 'download-file-from-record-field' / 'delete-file-from-record-field', …)` ([example](#a-file-field-connector-example)) |
| Record Created/Updated events | `onEvent(…)` on the same connector |

Only the bottom three are connector work. If a flow needs one, route the whole entity through the connector instead of mixing surfaces: connector work requires a connection binding and a second payload shape. Data Fabric entity events are Integration Service connector events: `onEvent(RecordCreated, { object: '<Entity>', … })`, with the entity in `object`; see [`event-trigger.md`](event-trigger.md#generic-events-name-the-object).

## Long text: queries return a 10,000-character preview

`dataFabricRead` is always a query, including a read-one with an `Id` filter. It returns the first 10,000 characters of `MULTILINE_MAX` plus `...[Truncated]`; nothing flags it, and `check`, `validate`, the run, and downstream steps still pass. `dataFabricCreate` has the same preview. Never write that preview through `dataFabricUpdate`: it stores the truncated value, including `...[Truncated]`; omit the field from `set`.

For a 15,551-character value, all native paths return 10,014 characters:

| Read path | Characters |
| --- | --- |
| `$vars.<create step>.output.<field>` | 10,014 (preview) |
| `dataFabricRead({ resultMode: 'multiple' })` → `output.results[i].<field>` | 10,014 (preview) |
| `dataFabricRead({ filters: [{ field: 'Id', value: … }] })` → `output.<field>` | 10,014 (preview) |
| `connector('uipath-uipath-dataservice', 'get-entity-record-by-id', …)` → `output.<field>` | 15,551 (whole) |

Read potentially long fields with connector `get-entity-record-by-id` ([The connector path](#the-connector-path-end-to-end)); short fields are whole through every path.

## The four verbs

- `dataFabricRead({ entity, filters?, resultMode?, limit?, skip?, sort?, fields? })`
- `dataFabricCreate({ entity, values })`
- `dataFabricUpdate({ entity, record, set })`
- `dataFabricDelete({ entity, record })`

```ts
.step('lookup', dataFabricRead({ entity: 'Invoices',
  filters: [
    { field: 'InvoiceId', value: input('invoiceId') },
    { field: 'Status', operator: '!=', value: 'Paid', or: true },
  ] }))
.step('markPaid', dataFabricUpdate({ entity: 'Invoices',
  record: { fromRead: 'lookup' },
  set: { Status: 'Paid', PaidBy: js`$vars.lookup.output.Approver` } }))
.step('logIt', dataFabricCreate({ entity: 'PaymentLog',
  values: { InvoiceId: input('invoiceId'), PaidOn: js`new Date().toISOString()` } }))
.step('purge', dataFabricDelete({ entity: 'Drafts', record: { byId: input('draftId') } }))
```

## Filters and targeting

A filter is `{ field, operator?, value, or? }`. `operator` defaults to `'='` and must be exactly one of `=` `!=` `>` `>=` `<` `<=` `contains` `starts with` `ends with` `in`. There is no `not in`, `not contains`, or null check; unsupported serialization takes down the whole query rather than dropping a row. `in` works only with `resultMode: 'multiple'`.

The query is disjunctive: `or: true` starts an alternative (ignored on the first row), so the list is `alt1 OR alt2 OR …`, with AND within each alternative:

```ts
filters: [
  { field: 'Status', value: 'Open' },
  { field: 'Priority', value: 'High', or: true },   // Status
  { field: 'Region', value: 'EU' },                 //   OR (Priority AND Region)
]
```

For `(A OR B) AND C`, write `(A AND C) OR (B AND C)`.

Filter values must be nonblank and must not reference `$self`; either makes the serializer refuse the whole query, publish nothing, and strand downstream `$vars` reads. `check` rejects both. Choice-set filters require numeric `numberId`, not the label; labels silently match nothing.

`record` targets update/delete and takes exactly one of `{ byId: '<record id>' }` (literal or expression) or `{ fromRead: '<step name>' }` (a preceding genuinely single-record `dataFabricRead`). A multi-record query is refused as a write target as a no-op, so validation and the run stay green while nothing is written. `check` reports `DATAFABRIC_FROMREAD_UNKNOWN` for a nonexistent read step and `DATAFABRIC_FROMREAD_MULTIPLE` for `resultMode: 'multiple'`.

`set` and `values` map fields to literals or expressions and reject empty maps. `values` also rejects an all-BLANK map. Blank create values are omitted so defaults apply; an all-blank create writes nothing and stays green. Supply a real value, not a placeholder.

**Type each flow input by its field.** Run `uip df entities get <id> --output json`; the type is at `Data.Fields[].FieldDataType.Name`, and use the resulting `input('<name>')`:

| Field type | Flow input |
| --- | --- |
| `STRING`, `MULTILINE_TEXT`, `UUID`, `DATE`, `DATETIME` | `types.string` |
| `DECIMAL`, `INTEGER` | `types.number` |
| `BOOLEAN` | `types.boolean` |
| `FILE` | none — declare `types.file` and upload with connector `upload-file-to-record-field` ([example](#a-file-field-connector-example)) |

System columns are never writable. Writes to `Id`, `CreateTime`, `CreatedBy`, `UpdateTime`, or `UpdatedBy` are rejected and only logged; the row stays unchanged and the run stays green. `check` reports `DATAFABRIC_SYSTEM_COLUMN`. Blank creates are omitted; blank updates write explicit `null`, which non-nullable columns reject. Check nullability with `uip df entities get`.

## Query-many needs `resultMode`, and `resultMode` needs 1.4

`core.datafabric.read` began as read-one (“Read entity”) and became read-one/query-many at **1.4** (“Query entity records”). `resultMode: 'single'` publishes `output`; `resultMode: 'multiple'` publishes `output.results`. Plain `dataFabricRead()` emits SDK-pinned **1.0**; passing `resultMode` selects 1.4. `dataFabricRead({ resultMode }, { version: '1.0' })` is refused at compile time.

```ts
.step('open', dataFabricRead({ entity: 'Invoices', resultMode: 'multiple',
  filters: [{ field: 'Status', value: 'Open' }] })) // core.datafabric.read@1.4
.loop('each', js`$vars.open.output.results`, (b) => b./* … */)
```

## Paging a list query

`limit` always applies; omission resolves to **100**. **1000 is the hard ceiling**; larger values truncate silently. Use `skip` to page, and pair limits with `sort` or the slice is arbitrary.

```ts
.step('page1', dataFabricRead({ entity: 'Invoices', resultMode: 'multiple',
  limit: 1000, skip: 0, sort: { field: 'CreateTime', direction: 'desc' },
  fields: ['Id', 'Status'] }))
```

`limit`, `skip`, `sort`, and `fields` are list-query options; `check` refuses them on single-record reads.

Audit columns are `Id`, `CreateTime`, `CreatedBy`, `UpdateTime`, `UpdatedBy`; there is no `CreatedAt`. Invalid sort columns are not caught by `validate`.

## A folder-scoped entity: name it and its folder

Tenant-scoped entities use `entity: '<Name>'`; folder-scoped entities use the name and Orchestrator folder **path**, never keys:

```ts
.step('read', dataFabricRead({ entity: { name: 'Orders', folder: 'Finance/Prod' }, resultMode: 'multiple' }))
```

Requires `@uipath/maestro-builder-sdk` 6.73.0 or later. Older SDKs refuse `{ name, folder }` and lack key-less `prepare`.
<!--skill-flavor:data-fabric-entity-ref-sdk:start-->
Upgrade by running `npm install -g @uipath/maestro-builder-sdk@latest`. If `uip maestro registry prepare --entity …` reports `missing required argument 'connector-key'`, run the same command with `npx flow-sdk registry prepare --entity …`.
<!--skill-flavor:data-fabric-entity-ref-sdk:end-->

`check` reports `RESOURCE_UNRESOLVED` and prints the command recording keys; run it, then run `check` again:

```bash
uip maestro registry prepare --entity Orders --folder-path Finance/Prod
# Entity    Orders   (Finance/Prod, remote)
# Recorded  ./.flow-sdk/resources.json
```

`compile` writes the folder/resource keys, two `resource: 'Entity'` binding rows, and the entity row in `bindings_v2.json`, allowing `uip solution resources refresh` to declare it. Do not type keys; `compile` refuses an unrecorded entity.

Run `prepare` from the directory used for `check` and `compile`, normally `<Solution>/<Name>/`; it records `./.flow-sdk/resources.json` there. In a solution (a `.uipx` in that folder or above), it searches the solution before the tenant.

`prepare` lists and stops; it never selects:

- Without `folder`, it searches every folder. One match is recorded and names the folder to pin; multiple matches list each `folder:`—write the intended one and run `prepare` again.
- A tenant-level match needs no `prepare`; write `entity: '<Name>'` as output says.
- Names match exactly, including case; folder paths ignore case and leading/trailing slash. A folder with no matching entity reports `RESOURCE_NOT_IN_FOLDER` and lists folders containing it.
- No match lists near misses and listings. If none is intended, ask the user; never create an entity independently. Creation in the requested scope follows [/uipath:uipath-platform — local-entities.md](../../uipath-platform/references/data-fabric/local-entities.md), then run `prepare` again.
- A recorded row older than a day counts as missing; `check` asks for `prepare` again.

### An entity the solution authors itself

An entity created with `uip df entities create <Name> --local` exists only in the solution until deployment and resolves the same way. Write `{ name: '<Name>' }` and run the `prepare` printed by `check` from the Flow project folder. It reads the solution, records the entity in placeholder folder `99999999-9999-9999-9999-999999999999` (which `flow debug` and `solution deploy` replace with the provisioned folder), and names the folder to pin: `folder: 'solution_folder'`.

Do not look it up on the tenant. Omitting keys makes it tenant-scoped; runtime fails with `Entity <Name> does not exist`, while `flow validate` reports `INLINE_ENTITY_UNBOUND`. Although its message suggests `uip maestro flow node configure` (which edits compiled `.flow`), fix `.flow.ts` in a builder-SDK project or the next `compile` reverts it. Creating/modeling belongs to [/uipath:uipath-platform — local-entities.md](../../uipath-platform/references/data-fabric/local-entities.md).

A decompiled flow uses `folderKey` and `resourceKey`; leave that form unless the entity changes.

**Debugging:** `uip maestro flow debug` works only the first time for a solution with a local entity; later runs overwrite the same Studio Web solution, which Studio Web cannot do for one holding an Entity project. Tell the user up front and recommend the UiPath extension for VS Code for repeated debugging. `pack` / `publish` / `deploy run` are unaffected.

## A delete publishes nothing

`core.datafabric.delete` declares no outputs. `$vars.<delete>.output` is undefined at runtime, and `check` reports `DATAFABRIC_DELETE_HAS_NO_OUTPUT`. Read needed values from the `dataFabricRead` that found the record before deleting.

## The connector path, end to end

For connector operations, entity body fields cannot be carried by the static library; resolve the schema once or `compile` refuses unknown inputs:

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

For full rules, including the parent-field (`GenerateSchema` over `entityName`) shape, see [`connector-params.md`](connector-params.md).

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

`entityName` is a LOOKUP: use `lookup(...).byDisplayName(...)`, never a system name. The FILE column is `_fieldName` (leading underscore required); `fieldName` fails `check`. Debug CLI uploads with `--attachment doc=<path>` ([`operate.md` § types.file](operate.md)); download publishes the file reference at `output.Response`. Delete has the same shape with only the action name changed.

`file:` accepts any upstream file reference, including `out('fetch', 'Response')`. Chain the download's `output.Response` straight into another upload — same shape as the Slack upload example ([`connector-params.md` § file uploads](connector-params.md#file-uploads-are-multipart-flow-inputs)):

```ts
.step('mirror', connector(UploadFileToRecordField, {
  entityName: lookup(UploadFileToRecordField, 'entityName').byDisplayName('LoanApplication'),
  recordId: input('mirrorId'),
  _fieldName: 'Contract',
  file: out('fetch', 'Response'),   // from the download step above
}, BIND))
```

The same source rule applies to `documentClassify`, `dynamicExtract`, `ixpExtract`, `summarize`, and `batchTransform`: the file field accepts `types.file` input, `out('<step>', '<fileField>')`, or any step whose declared output is a file. Runtime values are file references, never bytes.

<!--skill-flavor:operation-doc:start-->
**Read the operation's own doc before guessing anything.** The connector library ships one Markdown page per operation. An environment-staged library sets `$FLOW_SDK_LIBRARY_MD`; otherwise run `uip maestro registry path --library-md --output plain`:

```bash
sed -n '1,60p' "$FLOW_SDK_LIBRARY_MD/uipath-uipath-dataservice/create-entity-record@1.0.0.md"
```

The page names connector *UiPath Data Fabric*, gives `POST /v2/{entityName}/CreateEntityRecord`, and prints the exact `prepare-connector … -f entityName=<value>` command to run.
<!--skill-flavor:operation-doc:end-->

## Evidence boundary

Entity and field names are tenant data: copy them from the scenario or tenant; never invent them. Names are case-sensitive, and unmatched columns are dropped rather than rejected, so resolve first:

```bash
uip df entities list --native-only --include-folders --output json  # writes need a NATIVE entity
uip df entities get <entity-id> --output json                       # exact column names and types
```

Two query options are documented by the platform but not applied by the
converter the local engine runs: `limit`/`skip`/`sort` reach the file as
`_recordLimit`/`_skip`/`_sort` and are read at run time, so `flow-debug` is not
evidence either way for them.

Offline `validate` checks only `entityConfig` shape—not column existence, writability, value type, native versus federated status, or whether a `byId` id exists. Each can validate green and fail silently; the tenant is authoritative.

A typed column also needs the canvas's `_outputSchema` snapshot to coerce
values, and a dotted related path needs `_entityFields`. The SDK authors neither,
so keep from-scratch nodes on the entity's own columns with string or expression values, and let the designer populate snapshots on first open.