# Data Fabric

*Exact signatures, fields, and defaults: `dataFabricRead()`, `dataFabricCreate()`, `dataFabricUpdate()` and `dataFabricDelete()` for native CRUD, and `connector()` for the operations the native family still does not cover.*

## One product, two surfaces

"Data Fabric" and "Data Service" are **the same product under two names**: the
tenant lists connector key `uipath-uipath-dataservice` with the display name
**UiPath Data Fabric**, and `uip df entities` manages the entities both surfaces
read.

The native `core.datafabric.*` family covers all four CRUD verbs, so **CRUD on
one entity is native work** — one surface, no connection binding, no `prepare`
step.
Reach for the connector when the flow needs something the family does not have.

| Operation | Surface |
| --- | --- |
| Query records, with filters, limit, paging and sort | `dataFabricRead({ entity, filters, resultMode, limit, skip, sort, fields })` |
| Create a record | `dataFabricCreate({ entity, values })` |
| Update a record | `dataFabricUpdate({ entity, record, set })` |
| Delete a record | `dataFabricDelete({ entity, record })` |
| Get a record by id | `dataFabricRead({ entity, filters: [{ field: 'Id', value: … }] })` |
| Upload / download / delete a file record field | `connector('uipath-uipath-dataservice', '…-file-…-record-field', …)` |
| Record Created / Record Updated events | `onEvent(…)` on the same connector |

Only the bottom two are connector work. A flow that needs one of them straddles
both surfaces — a connection binding, a second payload shape, two things to
debug — so when that is the shape of the work, route the whole entity through
the connector instead of mixing.

Data Fabric **events** (Record Created / Record Updated on an entity) are
Integration Service connector events on `uipath-uipath-dataservice`, not this
node family: `onEvent(RecordCreated, { object: '<Entity>', … })`, with the
entity named through `object`. See
[`event-trigger.md`](event-trigger.md#generic-events-name-the-object).

## The four verbs

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

A filter row is `{ field, operator?, value, or? }`. `operator` defaults to `'='`
and is one of exactly ten spellings — `=` `!=` `>` `>=` `<` `<=` `contains`
`starts with` `ends with` `in`. There is deliberately no `not in`, no
`not contains`, and no null check: the serializer cannot emit them, and a filter
it cannot emit takes the WHOLE query down rather than dropping one row.
`in` is honoured only when `resultMode` is `'multiple'`.

**The query model is disjunctive**, so `or: true` SPLITS the list rather than
joining one row to the one before it. The whole query is `alt1 OR alt2 OR …`,
and each alternative is an AND of its own rows; `or: true` opens a new
alternative (and is ignored on the first row, which has nothing to split from):

```ts
filters: [
  { field: 'Status', value: 'Open' },
  { field: 'Priority', value: 'High', or: true },   // Status
  { field: 'Region', value: 'EU' },                 //   OR (Priority AND Region)
]
```

To express `(A OR B) AND C`, write it out as `(A AND C) OR (B AND C)` — the
model has no other way to say it.

A filter value must not be blank and must not reference `$self`: either one makes
the serializer refuse the entire query, which leaves the step publishing nothing
and strands every downstream `$vars` read of it. `check` rejects both.

A filter on a choice-set column compares against the choice's numeric
`numberId`, never its label — a label matches nothing, silently.

`record` names the target row on **update and delete alike**, and takes exactly
ONE of:

- `{ byId: '<record id>' }` — a known record id, literal or expression;
- `{ fromRead: '<step name>' }` — the record a preceding `dataFabricRead`
  step returned. It must be a genuinely SINGLE-record read: a multi-record query
  is refused as a write target, and the refusal is a no-op task, not an error —
  the flow validates, runs green, and writes nothing. `check` rejects a
  `fromRead` that names no read step (`DATAFABRIC_FROMREAD_UNKNOWN`) or names a
  `resultMode: 'multiple'` one (`DATAFABRIC_FROMREAD_MULTIPLE`).

`set` (update) and `values` (create) map field names to values, literals or
expressions.
Both are rejected when empty, and `values` is rejected when every value is BLANK:
a blank is omitted from an insert so the column default applies, so an all-blank
create writes nothing and runs green. Fix that with a real value, never a
placeholder to satisfy the rule.

**System columns are never writable.** `Id`, `CreateTime`, `CreatedBy`,
`UpdateTime`, `UpdatedBy` are assigned by Data Fabric; a write to one is rejected
and the rejection is only logged, so the row comes back unchanged and the run
goes green. `check` refuses them (`DATAFABRIC_SYSTEM_COLUMN`).

A blank value means different things by verb: on create it is omitted so the
default applies; on update it writes an explicit `null`, which a non-nullable
column rejects. Check nullability with `uip df entities get`.

## Query-many needs `resultMode`, and `resultMode` needs 1.4

`core.datafabric.read` started as read-ONE ("Read entity") and became
read-one-or-query-many at **1.4** ("Query entity records").
`resultMode: 'single'` publishes one record as the step's `output`;
`resultMode: 'multiple'` publishes the matching records under `output.results`.

The SDK still pins **1.0** as the version a plain `dataFabricRead()` emits, the
same way every family here keeps its older default — so passing `resultMode` is
what selects 1.4, exactly as a Quartz `every` selects the scheduled trigger's
1.2. Nothing else changes, and a read that wants one record can ignore all of
this.

```ts
.step('open', dataFabricRead({ entity: 'Invoices',
  filters: [{ field: 'Status', value: 'Open' }],
  resultMode: 'multiple' }))          // → core.datafabric.read@1.4
.loop('each', js`$vars.open.output.results`, (b) => b./* … */)
```

`dataFabricRead({ resultMode }, { version: '1.0' })` is refused at compile time
rather than emitting an input the 1.0 definition does not declare.

## Paging a list query

`limit` is always applied — omitting it resolves to **100** — and **1000 is a
hard ceiling**: a larger value truncates silently rather than erroring. Cover a
bigger entity by paging with `skip`, and pair any limit with `sort` or the slice
is arbitrary.

```ts
.step('page1', dataFabricRead({ entity: 'Invoices', resultMode: 'multiple',
  limit: 1000, skip: 0, sort: { field: 'CreateTime', direction: 'desc' },
  fields: ['Id', 'Status'] }))
```

The real audit columns are `Id`, `CreateTime`, `CreatedBy`, `UpdateTime`,
`UpdatedBy` — there is no `CreatedAt`, and a sort on a column that does not exist
is not caught by `validate`.
`limit`, `skip`, `sort` and `fields` are list-query options: `check` refuses them
on a single-record read.

## A folder-scoped entity needs its bindings

A **tenant-scoped** entity needs nothing but `entity` — it serializes as a dotted
literal.

A **folder-scoped** one needs `folderKey` AND `resourceKey` together. With only
the folder key the entity serializes as a source-org literal: it validates, it
runs in this org, and it breaks on deploy to another. `check` refuses either half
alone (`DATAFABRIC_FOLDER_NO_RESOURCE_KEY`).

```ts
.step('read', dataFabricRead({ entity: 'Orders',
  folderKey: '<the entity\'s folderId>', resourceKey: '<solution resource key>' }))
```

Supplying both emits the two `resource: 'Entity'` binding rows the platform
matches on `propertyAttribute` (`name` and `folderKey` — never `folderPath`).
Resolve the keys from the tenant:

```bash
uip df entities list --include-folders --output json   # folderId per entity
uip solution resources list --kind Entity --output json # the resource key
```

Nothing mints a resource key for a hand-authored flow. If you cannot resolve one,
keep the entity tenant-scoped and omit both — a half-authored folder scope is
worse than none.

## A delete publishes nothing

`core.datafabric.delete` is the one verb of the family whose definition declares
no outputs — the record is gone, so there is nothing to hand downstream.
`$vars.<delete>.output` is undefined at run time, and `check` rejects the read
(`DATAFABRIC_DELETE_HAS_NO_OUTPUT`).
Take what the flow needs off the `dataFabricRead` step that FOUND the record,
before the delete runs.

## The connector path, end to end

For the operations still on the connector, an entity operation's body fields come
from the entity, so the static library cannot carry them — `compile` refuses them
as unknown inputs until you resolve the schema once:

```bash
uip maestro registry prepare uipath-uipath-dataservice get-entity-record-by-id \
  -f entityName=ContractRegistry
# → connectors-local/ + bindings.json, with the entity's own fields as inputs
```

```ts
.step('byId', connector('uipath-uipath-dataservice', 'get-entity-record-by-id',
  { entityName: 'ContractRegistry', recordId: input('id') },
  { connection: 'dataservice', folder: 'shared' }))
```

Full rules, including the parent-field (`GenerateSchema` over `entityName`)
shape these operations use: [`connector-params.md`](connector-params.md).

**Read the operation's own doc before guessing anything.** The connector library
ships a Markdown page per operation, and an environment that stages a library
points `$FLOW_SDK_LIBRARY_MD` at it (`uip maestro registry path --library-md --output plain`
otherwise):

```bash
sed -n '1,60p' "$FLOW_SDK_LIBRARY_MD/uipath-uipath-dataservice/create-entity-record@1.0.0.md"
```

That page names the connector *UiPath Data Fabric*, gives the HTTP route
(`POST /v2/{entityName}/CreateEntityRecord`), and prints the exact
`prepare-connector … -f entityName=<value>` line to run — before any of it has to
be inferred.

## Evidence boundary

The entity name and field names are tenant data — copy them from the scenario
or the tenant, never invent them.

**Entity and column names are case-sensitive, and an unmatched column is dropped
rather than rejected** — a wrong name yields a node that validates green and
writes nothing. Nothing offline can tell a real column from a typo, so resolve
them first:

```bash
uip df entities list --native-only --include-folders --output json  # writes need a NATIVE entity
uip df entities get <entity-id> --output json                       # exact column names and types
```

Two query options are documented by the platform but not applied by the
converter the local engine runs: `limit`/`skip`/`sort` reach the file as
`_recordLimit`/`_skip`/`_sort` and are read at run time, so `flow-debug` is not
evidence either way for them.

Offline `validate` proves only the emitted `entityConfig` SHAPE. It does not
check whether a column exists, is writable, or has the type the value implies;
whether the entity is native or federated; or whether a `byId` id matches
anything. Every one of those validates clean and fails silently at run time, so
green is not evidence here — the tenant is.

A typed column also needs the canvas's `_outputSchema` snapshot to coerce
values, and a dotted related path needs `_entityFields`. The SDK authors neither,
so keep from-scratch nodes on the entity's own columns with string or expression
values, and let the designer fill the snapshots in on first open.
