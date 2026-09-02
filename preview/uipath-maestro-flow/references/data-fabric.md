# Data Fabric

*Exact signatures, fields, and defaults: [`dataFabricRead()`](api.md#datafabricread-function) and [`dataFabricUpdate()`](api.md#datafabricupdate-function).*

Data Fabric and Data Service are different authoring surfaces. Use this native
node family only when the scenario says **Data Fabric**. A **Data Service**
entity is reached through the Integration Service connector key
`uipath-uipath-dataservice`; follow
[`connector-params.md`](connector-params.md) and do not substitute
`dataFabricRead()` for that request.

Read entity records with filters (`core.datafabric.read`) and write fields back
to one record (`core.datafabric.update`).

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
