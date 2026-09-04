# Data Fabric

*Exact signatures, fields, and defaults: [`dataFabricRead()`](api.md#datafabricread-function), [`dataFabricUpdate()`](api.md#datafabricupdate-function), and — for every other entity operation — [`connector()`](api.md#connector-function).*

## Two surfaces, one product — choose by the verb

"Data Fabric" and "Data Service" are **the same product under two names**: the
tenant lists connector key `uipath-uipath-dataservice` with the display name
**UiPath Data Fabric**, and `uip df entities` manages the entities that
connector reads. What differs is the authoring surface, and the surfaces are not
interchangeable, because the native one has exactly two verbs:

| Operation | Surface |
| --- | --- |
| Read ONE record (optionally filtered) | `dataFabricRead()` → `core.datafabric.read` |
| Update ONE record | `dataFabricUpdate()` → `core.datafabric.update` |
| Create a record | `connector('uipath-uipath-dataservice', 'create-entity-record', …)` |
| Get a record by id | `connector(…, 'get-entity-record-by-id', …)` |
| Query MANY records / a row limit | `connector(…, 'query-entity-records', …)` |
| Delete a record | `connector(…, 'delete-entity-record', …)` |
| Upload / download / delete a file record field | `connector(…, '…-file-…-record-field', …)` |
| Record Created / Record Updated events | `onEvent(…)` on the same connector |

**So a task can say "Data Fabric" and still be a connector task.** Route on the
operation you need, never on which of the two names the scenario used. Reaching
for a `dataFabricCreate()` is the predictable dead end — there is no such node in
`core.datafabric.*` and none is coming; the create verb has always lived on the
connector.

`core.datafabric.*` also declares **no output schema**, so a step that must map
declared outputs downstream is a connector step for that reason alone.

### The connector path, end to end

An entity operation's body fields come from the entity, so the static library
cannot carry them — `compile` refuses them as unknown inputs until you resolve
the schema once:

```bash
npx flow-sdk registry prepare uipath-uipath-dataservice create-entity-record \
  -f entityName=ContractRegistry
# → connectors-local/ + bindings.json, with the entity's own fields as inputs
```

```ts
.step('create', connector('uipath-uipath-dataservice', 'create-entity-record',
  { entityName: 'ContractRegistry', contractTitle: 'Q3 renewal', status: 'Draft' },
  { connection: 'dataservice', folder: 'shared' }))
```

Full rules, including the parent-field (`GenerateSchema` over `entityName`)
shape these operations use: [`connector-params.md`](connector-params.md).

**Read the operation's own doc before guessing anything.** The connector library
ships a Markdown page per operation, and an environment that stages a library
points `$FLOW_SDK_LIBRARY_MD` at it (`uip maestro registry path --library-md`
otherwise):

```bash
sed -n '1,60p' "$FLOW_SDK_LIBRARY_MD/uipath-uipath-dataservice/create-entity-record@1.0.0.md"
```

That page names the connector *UiPath Data Fabric*, gives the HTTP route
(`POST /v2/{entityName}/CreateEntityRecord`), and prints the exact
`prepare-connector … -f entityName=<value>` line to run — before any of it has to
be inferred.

## The native two-verb family

Read one entity record with filters (`core.datafabric.read`) and write fields
back to one record (`core.datafabric.update`).

Data Fabric **events** (Record Created / Record Updated on an entity) are
Integration Service connector events on `uipath-uipath-dataservice`, not this
node family: `onEvent(RecordCreated, { object: '<Entity>', … })`, with the
entity named through `object`. See
[`event-trigger.md`](event-trigger.md#generic-events-name-the-object).

Signatures: `dataFabricRead({ entity, filters? })`;
`dataFabricUpdate({ entity, record, set })`.

```ts
.step('lookup', dataFabricRead({ entity: 'Invoices',
  filters: [
    { field: 'InvoiceId', value: input('invoiceId') },
    { field: 'Status', operator: '!=', value: 'Paid', or: true },
  ] }))
.step('markPaid', dataFabricUpdate({ entity: 'Invoices',
  record: { fromRead: 'lookup' },
  set: { Status: 'Paid', PaidBy: js`$vars.lookup.output.Approver` } }))
```

## Filters and targeting

A filter row is `{ field, operator?, value, or? }` — `operator` defaults to
`'='`; `or: true` joins that row to the previous with OR instead of AND.
Values may be literals or expressions.

`record` names the target row and takes exactly ONE of:

- `{ byId: '<record id>' }` — a known record id, literal or expression;
- `{ fromRead: '<step name>' }` — the record a preceding `dataFabricRead`
  step returned. `check` rejects a `fromRead` that names no read step.

`set` maps field names to new values (literals or expressions); an empty `set`
is rejected — the node would write nothing.

## Evidence boundary

The entity name and field names are tenant data — copy them from the scenario
or the tenant, never invent them. No local rung reads a real entity: offline
`validate` proves the emitted `entityConfig` shape (entity, filter rows,
record targeting, field updates); actual reads and writes are platform-side.
