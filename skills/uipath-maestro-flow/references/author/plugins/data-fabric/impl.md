# Data Fabric Entity Nodes — Implementation

Four OOTB nodes that read and write records in a UiPath Data Fabric entity: `core.datafabric.read`, `core.datafabric.create`, `core.datafabric.update`, `core.datafabric.delete`. Each is a `bpmn:Task` host — the serializer attaches a `<uipath:output>` carrying a `=datafabric...` target, and the BPMN engine's activity postprocessor performs the query or write after the task runs. There is no Integration Service connection and no connector binding.

Shared action-node boilerplate — skeleton, ports, error port, add/edit mechanics — is in [shared/action-nodes.md](../../../shared/action-nodes.md). This file covers only what is specific to the entity nodes.

## Registry validation

Run `registry get` for each node type you intend to use:

```bash
uip maestro flow registry get core.datafabric.read --output json
uip maestro flow registry get core.datafabric.create --output json
uip maestro flow registry get core.datafabric.update --output json
uip maestro flow registry get core.datafabric.delete --output json
```

Confirm on `Data.Node`:

- `handleConfiguration` — input port `input`, output port `output`. All four share this shape.
- `model.type` — `bpmn:Task` (**not** `bpmn:ServiceTask`; these nodes carry no `serviceType`).
- `inputDefinition.properties.entityConfig` — the single input container.
- `outputDefinition.output.source` — `=response`, with `type: "jsonSchema"`. **Delete has no `outputDefinition` at all** — that absence is the contract, not an omission.
- `runtimeConstraints.exclude` — contains `api-function`.
- `version` — copy it verbatim into the instance's `typeVersion`. Read and Create are ahead of Update and Delete; do not assume one version across the family.

If `registry get` reports **"Node not found"**, the node is not available to you. Run `uip tools update`, then `uip maestro flow registry pull --force`, and retry. If it still fails, the tenant feature flag is off — `canvas.nodes.read-entity`, `canvas.nodes.update-entity`, `canvas.nodes.delete-entity`, or `canvas.nodes.create-entity` respectively. Confirm with the UiPath admin.

`registry search` is not a substitute for `registry get` here. A flag-gated node can still appear in search with `AvailableOnTenant: false` while `registry get` refuses it — and without `registry get` you cannot source the `definitions[]` entry, which must never be hand-written ([Author capability, rule 6](../../CAPABILITY.md#critical-rules)). Treat `AvailableOnTenant: false` as unavailable and stop.

## Add or edit the node

These are OOTB nodes and therefore **user-owned**: author them with `Edit` / `Write` directly against the `.flow` file. `inputs.entityConfig` is a plain JSON object, not a `=jsonString:` envelope, so none of the CLI-owned node rules apply. See [Author capability — Node ownership](../../CAPABILITY.md#node-ownership--who-authors-the-node) and [editing-operations.md](../../editing-operations.md).

Every node type still needs its `definitions[]` entry copied verbatim from `registry get`.

## Resolving the entity and its columns

Entity and column names are **case-sensitive**, and an unmatched column is silently dropped rather than rejected — a wrong name yields a node that validates green and writes nothing. Resolve both from the tenant before authoring:

```bash
uip df entities list --output json
uip df entities get <entity-id> --output json
```

`entities list` gives the entity `Name` (what `entityName` takes) and its id; `entities get` gives the exact column names for `_filters`, `fieldValues`, `fieldUpdates`, and `_selectedFieldNames`.

When a step needs a real record id or a sample row — for a `byId` selector, or to sanity-check a filter — read one rather than inventing it:

```bash
uip df records list <entity-id> --output json
uip df records query <entity-id> --body '{"filterGroup":{...}}' --output json
```

An invented id or column matches no record: every lookup returns empty and the run faults on empty data.

## JSON structure

Node instances carry `inputs` only. Do **not** hand-write an `outputs` block, a `model` block, or a `ui` block — `flow format` owns layout, the definition owns the BPMN model, and the manifest's `outputDefinition` plus the `variables.nodes[]` entry that `flow format` regenerates own the output contract ([Author capability, rules 13–15](../../CAPABILITY.md#critical-rules)).

### Read — single record

```json
{
  "id": "readOrder",
  "type": "core.datafabric.read",
  "typeVersion": "<from registry get>",
  "display": { "label": "Read order" },
  "inputs": {
    "entityConfig": {
      "entityName": "Orders",
      "resultMode": "single",
      "_filters": {
        "logicalOperator": "AND",
        "rows": [
          { "field": "OrderNumber", "operator": "=", "value": "=js:$vars.start.output.orderNumber" }
        ],
        "groups": []
      }
    }
  }
}
```

### Read — multiple records

```json
{
  "id": "listOpenOrders",
  "type": "core.datafabric.read",
  "typeVersion": "<from registry get>",
  "display": { "label": "List open orders" },
  "inputs": {
    "entityConfig": {
      "entityName": "Orders",
      "resultMode": "multiple",
      "_recordLimit": 100,
      "_skip": 0,
      "_sort": { "field": "CreatedAt", "direction": "desc" },
      "_selectedFieldNames": ["Id", "OrderNumber", "Status"],
      "_filters": {
        "logicalOperator": "AND",
        "rows": [{ "field": "Status", "operator": "=", "value": "Open" }],
        "groups": []
      }
    }
  }
}
```

The rows land at `$vars.listOpenOrders.output.results`, not `$vars.listOpenOrders.output`.

Write `_recordLimit` explicitly, as the canvas does. Omitting it does not mean "no cap" — the engine applies its own default, which differs by the entity's composite shape, so the row count silently depends on the entity rather than on the flow. A `_sort` matters for the same reason: a limit without an order returns an arbitrary slice.

### Create

```json
{
  "id": "createOrder",
  "type": "core.datafabric.create",
  "typeVersion": "<from registry get>",
  "display": { "label": "Create order" },
  "inputs": {
    "entityConfig": {
      "entityName": "Orders",
      "fieldValues": [
        { "field": "OrderNumber", "value": "=js:$vars.start.output.orderNumber" },
        { "field": "Status", "value": "Open" }
      ]
    }
  }
}
```

At least one row must carry a non-blank `value`. A blank value is **omitted** from the insert so the column default applies — so an all-blank `fieldValues` serializes to an empty body, emits no output, and runs green having inserted nothing. The validator rejects that case; do not work around it by adding a placeholder value.

### Update

```json
{
  "id": "markShipped",
  "type": "core.datafabric.update",
  "typeVersion": "<from registry get>",
  "display": { "label": "Mark shipped" },
  "inputs": {
    "entityConfig": {
      "entityName": "Orders",
      "recordSource": "fromRead",
      "readEntityNodeId": "readOrder",
      "fieldUpdates": [
        { "field": "Status", "value": "Shipped" },
        { "field": "ShippedAt", "value": "=js:new Date().toISOString()" }
      ]
    }
  }
}
```

An empty `value` in `fieldUpdates` is a **real write** that clears the column — unlike Create, it is never treated as "leave unset".

### Delete

```json
{
  "id": "removeDraft",
  "type": "core.datafabric.delete",
  "typeVersion": "<from registry get>",
  "display": { "label": "Remove draft" },
  "inputs": {
    "entityConfig": {
      "entityName": "Orders",
      "recordSource": "byId",
      "recordId": "=js:$vars.start.output.orderId"
    }
  }
}
```

`recordSource` is **required** on Delete (unlike Update, which tolerates its absence on legacy configs). Without it both selector guards go inert, the serializer resolves no record, and a destructive node publishes and runs green having deleted nothing.

## Filters

`_filters` uses a grouped query model:

```json
{
  "logicalOperator": "AND",
  "rows": [{ "field": "Status", "operator": "=", "value": "Open" }],
  "groups": [
    {
      "logicalOperator": "OR",
      "rows": [
        { "field": "Priority", "operator": "=", "value": "High" },
        { "field": "Amount", "operator": ">", "value": "1000" }
      ]
    }
  ]
}
```

Rows at the root and each group's rows join by that level's own `logicalOperator`. A bare array of rows is the legacy form and is still read, but author the grouped object.

**Supported operators**, exactly as spelled in the file:

`=` · `!=` · `>` · `>=` · `<` · `<=` · `contains` · `starts with` · `ends with` · `in`

`in` takes a comma-separated `value` and is honoured **only** when `resultMode` is `"multiple"`. There is deliberately no `not in`, `not contains`, or null check — the serializer cannot emit them. `is any of` is the legacy spelling of `in` and is still read.

Filter values may be literals or `=js:` expressions. Two rules the serializer enforces by refusing the **entire** query — which leaves the node with no output and breaks every downstream reference:

- **A filter value cannot reference `$self`,** and cannot use a value the engine's query bracket cannot carry. A query cannot wait on the record it is being run to fetch.
- **An expression switched on and left blank is refused,** rather than dropped. Dropping it would silently widen the read past what was written.

Keep filters narrow. A `multiple` read whose filters all compile away returns an arbitrary page, not an error.

## Record selection

Update and Delete name one record through `recordSource`:

| `recordSource` | Required key | Resolves to |
| --- | --- | --- |
| `"byId"` | `recordId` | The record with that `Id`. A literal, or a `=js:` reference such as `=js:$vars.createOrder.output.Id` |
| `"fromRead"` | `readEntityNodeId` | The record the named Read node's query identifies — the query is recompiled, with `Id` forced into the selected fields |

Both selectors are validated as **non-blank after trimming**, because the serializer trims before deciding a selector is usable. A whitespace-only `recordId` is not "empty enough" to be an obvious mistake but is exactly as inert.

A `fromRead` pointing at a Read that matches more than one record faults the element at runtime — that over-match throw is the safety net, so do not disable it by widening the read.

## Folder-scoped entities and bindings

A **tenant-scoped** entity needs nothing beyond `entityName`; the target serializes as `=datafabric.<EntityName>`.

A **folder-scoped** entity carries `_folderKey` (the folder GUID). Its presence switches the emitted target to the folder-qualified form, and for the flow to survive export to another org the entity's name and folder must serialize as binding tokens rather than source-org literals. That requires:

1. `_resourceKey` (preferred) or `_entityKey` on the `entityConfig`, and
2. two top-level `bindings[]` rows for that key, with `resource: "Entity"` and `propertyAttribute` of `name` and `folderKey`.

```json
"bindings": [
  { "id": "<bindingId1>", "resource": "Entity", "resourceKey": "<resourceKey>", "propertyAttribute": "name",      "name": "Orders" },
  { "id": "<bindingId2>", "resource": "Entity", "resourceKey": "<resourceKey>", "propertyAttribute": "folderKey", "name": "<folder GUID>" }
]
```

The folder token must come from the **`folderKey`** attribute, not `folderPath`: the platform's deploy-time override rewrites `folderPath` with the Orchestrator FQN, which breaks the query even in the source org.

When `_folderKey` is set but a binding is missing, serialization still succeeds — it falls back to a source-org literal and logs a warning. That partial state (name token + literal folder GUID) looks portable and breaks on cross-org deploy, so treat the warning as a defect rather than noise.

The entity picker writes these bindings automatically. When hand-authoring a folder-scoped entity, add them yourself or leave the entity tenant-scoped.

## Output wiring

Reference the output through `=js:$vars.<nodeId>.output` per the canonical rule ([node-output-wiring.md](../../../shared/node-output-wiring.md)):

```json
{
  "id": "end",
  "type": "core.control.end",
  "typeVersion": "<from registry get>",
  "outputs": {
    "status":   { "source": "=js:$vars.readOrder.output.Status" },
    "orderId":  { "source": "=js:$vars.createOrder.output.Id" },
    "openRows": { "source": "=js:$vars.listOpenOrders.output.results" }
  }
}
```

Run `uip maestro flow format <ProjectName>.flow` after adding nodes. Format regenerates `variables.nodes[]`, which is what makes `$vars.<nodeId>.output` resolve at runtime; skipping it produces a flow that validates but resolves the reference to `undefined` ([Author capability, rule 14](../../CAPABILITY.md#critical-rules)).

Two wiring constraints unique to these nodes:

- **Delete produces nothing.** There is no `$vars.<deleteNodeId>.output`.
- **An Update node's output cannot feed a collection.** Each downstream reference is rewritten into its own re-read of the written record; [Loop](../loop/impl.md) and data-transform collections are excluded from that rewriting and have no snapshot to fall back on. Wire the Read node's output into the collection instead.

## Validate

```bash
uip maestro flow validate <ProjectName>.flow --output json
```

The validator enforces the "green but inert" cases specifically, because for a write they are worse than a hard failure:

| Message | Means |
| --- | --- |
| `An entity must be selected` | `entityName` missing or empty |
| `Set a value for at least one field` | Create's `fieldValues` has no row with a non-blank value |
| `Select a field to update` | Update's `fieldUpdates` has no row naming a field |
| `A record ID is required` | `recordSource: "byId"` with a blank or whitespace-only `recordId` |
| `Select a Read entity records node` | `recordSource: "fromRead"` with no `readEntityNodeId` |
| `Choose how to identify the record` | Delete with `recordSource` missing or not one of `byId` / `fromRead` |

It does **not** check that a column name exists — that is what `uip df entities get <entity-id>` is for.

## Debug

| Symptom | Cause | Fix |
| --- | --- | --- |
| `Node not found: core.datafabric.*` on `registry get` | Tenant flag off, or CLI predates the node | `uip tools update`, then `uip maestro flow registry pull --force`; then confirm the matching `canvas.nodes.*-entity` flag with the admin |
| Node runs green, nothing written | An inert selector or an all-blank write body | Re-run `flow validate` — every inert case above has a message. A node that validates clean but still no-ops is a folder/binding problem, not a selector one |
| Create runs, but `output.Id` is empty and the row was updated instead of inserted | Runtime engine older than `1.923.0` — `GetDataFabricAction()` falls back to `update` | Upgrade the engine, or turn `canvas.nodes.create-entity` off until it is upgraded |
| Downstream `$vars.<id>.output` is `undefined` | `variables.nodes[]` missing | Run `uip maestro flow format` |
| A Loop over a multi-record read iterates nothing | Wired `output` instead of `output.results` | Use `=js:$vars.<readId>.output.results` |
| `404 Entity <name> does not exist` | Folder-scoped entity queried without folder qualification, or a related-field join | Set `_folderKey` and its bindings. Joins across a folder-scoped entity are not supported — the join request carries a bare name with no folder qualifier |
| Read returns every record | Filters compiled away — a blank expression row, or an `in` row in `single` mode | Check each row against [Filters](#filters); the validator's `entityQueryExpressionRule` blocks the publishable cases |
| Console warning `… has no name/folderKey binding — serializing a non-portable literal` | Folder-scoped entity missing a `bindings[]` row | Add both rows — see [Folder-scoped entities and bindings](#folder-scoped-entities-and-bindings) |

## What not to do

- **Do not hand-write `definitions[]`** — copy verbatim from `registry get`. A flag-gated node you cannot `registry get` is a node you cannot author.
- **Do not put a `model` block on the instance.** `bpmn:Task` and the debug runtime live in the definition.
- **Do not add an instance `outputs` block.** The canvas writes none for these nodes; the manifest `outputDefinition` plus `flow format`'s `variables.nodes[]` carry the contract.
- **Do not treat `AvailableOnTenant: false` as usable** because search returned the node.
- **Do not use a Data Fabric node in an API workflow** — all four exclude the `api-function` runtime.
- **Do not reference `$self` in a filter value,** and do not leave a filter expression blank — either refuses the whole query and strands every downstream reference.
- **Do not add a placeholder value to satisfy Create's "at least one value" rule.** The rule exists because a blank-only insert writes nothing; a junk value writes junk.
- **Do not point `folderPath` at the folder token** for a folder-scoped entity — use `folderKey`.
- **Do not wire an `error` edge back into the happy path.** A failed write that reaches the success End node reports `Completed` with success-shaped outputs ([Author capability, rule 16](../../CAPABILITY.md#critical-rules)).
