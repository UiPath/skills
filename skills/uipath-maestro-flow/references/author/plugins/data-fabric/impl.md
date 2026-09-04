# Data Fabric Entity Nodes — Implementation

Four OOTB nodes that read and write records in a UiPath Data Fabric entity: `core.datafabric.read`, `core.datafabric.create`, `core.datafabric.update`, `core.datafabric.delete`. Each is a `bpmn:Task` host with no `serviceType`, and the BPMN engine does the actual work — but by two different mechanisms:

- **Read** emits its compiled query as a `<uipath:input>`. The engine's **input preprocessor** resolves it *before* the task runs.
- **Create / Update / Delete** emit a `<uipath:output>` carrying a `=datafabric...` target. The engine's **activity postprocessor** performs the write *after* the task runs.

That split matters when reading generated BPMN: a Read node with no `<uipath:output>` action target is correct, not a serialization failure.

Shared action-node boilerplate — skeleton, ports, add/edit mechanics — is in [shared/action-nodes.md](../../../shared/action-nodes.md), which these nodes diverge from in **two** ways, both recorded in its Exceptions note: they have no `error` port (see [No error port](#no-error-port)), and they carry no instance `outputs` block at all (see [JSON structure](#json-structure)). This file covers only what is specific to the entity nodes.

## Registry validation

Run `registry get` for each node type you intend to use:

```bash
uip maestro flow registry get core.datafabric.read --output json
uip maestro flow registry get core.datafabric.create --output json
uip maestro flow registry get core.datafabric.update --output json
uip maestro flow registry get core.datafabric.delete --output json
```

Confirm on `Data.Node`:

- `handleConfiguration` — input port `input`, output port `output`. All four share this shape, and none has an `error` handle.
- `model.type` — `bpmn:Task` (**not** `bpmn:ServiceTask`; these nodes carry no `serviceType`).
- `inputDefinition.properties.entityConfig` — the single input container.
- `outputDefinition.output.source` — `=response`, with `type: "jsonSchema"`. **Delete has no `outputDefinition` at all** — that absence is the contract, not an omission.
- `runtimeConstraints.exclude` — contains `api-function`.
- `version` — copy it verbatim into the instance's `typeVersion`. The four are versioned independently; do not assume one version across the family.

If `registry get` reports **"Node not found"**, the node is not available to you. Run `uip tools update`, then `uip maestro flow registry pull --force`, and retry. If it still fails, that node's tenant feature flag is off:

| Node type | Flag to ask the admin about |
| --- | --- |
| `core.datafabric.read` | `canvas.nodes.read-entity` |
| `core.datafabric.create` | `canvas.nodes.create-entity` |
| `core.datafabric.update` | `canvas.nodes.update-entity` |
| `core.datafabric.delete` | `canvas.nodes.delete-entity` |

`registry search` is not a substitute for `registry get` here. A flag-gated node can still appear in search with `AvailableOnTenant: false` while `registry get` refuses it — and without `registry get` you cannot source the `definitions[]` entry, which must never be hand-written ([Author capability, rule 6](../../CAPABILITY.md#critical-rules)).

**When the node is unavailable, switch to the connector and stop.** `AvailableOnTenant: false` is a decision, not an obstacle: build the flow with the `uipath-uipath-dataservice` activities ([connector/impl.md](../connector/impl.md)) and say in the final report that the native nodes were unavailable. Do not retry `registry get`, do not run `uip tools update` hoping for a newer manifest, and above all **do not hand-author a `definitions[]` entry from this doc's field list to stand in for the missing one** — a hand-written definition carries the wrong port schema, passes `flow validate`, and fails at runtime.

## Add or edit the node

These are OOTB nodes and therefore **user-owned**: author them with `Edit` / `Write` directly against the `.flow` file. `inputs.entityConfig` is a plain JSON object, not a `=jsonString:` envelope, so none of the CLI-owned node rules apply. See [Author capability — Node ownership](../../CAPABILITY.md#node-ownership--who-authors-the-node) and [editing-operations.md](../../editing-operations.md).

Every node type still needs its `definitions[]` entry copied verbatim from `registry get`.

## No error port

These four nodes are the exception to the implicit-error-port rule in [shared/action-nodes.md](../../../shared/action-nodes.md). None of them declares `supportsErrorHandling`, so the canvas never injects an `error` handle and the properties panel offers no error-handling toggle.

Do not set `inputs.errorHandlingEnabled`, and do not add an edge with `sourcePort: "error"`. Such an edge still serializes a boundary event — keyed purely on the handle name — but the node has no `outputDefinition.error` to map, so it emits with no error mapping and shows no handle the author can see or remove. Handle failure upstream (validate inputs before the node) or downstream (branch on the result), not with an error edge.

## Resolving the entity, its scope, and its columns

Entity and column names are **case-sensitive**, and an unmatched column is silently dropped rather than rejected — a wrong name yields a node that validates green and writes nothing. Resolve everything from the tenant before authoring.

`uip df entities list` shows **tenant-level entities only** by default. A folder-scoped entity will not appear until you widen the scope:

```bash
# Tenant-level only (default)
uip df entities list --output json

# Tenant + every folder you can see
uip df entities list --include-folders --output json

# One folder (mutually exclusive with --include-folders)
uip df entities list --folder-key <folder-uuid> --output json

# Writable entities only — Create/Update/Delete need a native entity
uip df entities list --native-only --include-folders --output json
```

Each listed entity carries its `folderId`. That value is both the `--folder-key` for follow-up commands and the `_folderKey` you put on a folder-scoped `entityConfig`.

Column names and a live record follow the same scoping rule — a folder-scoped entity needs `--folder-key` on each:

```bash
uip df entities get <entity-id> [--folder-key <folder-uuid>] --output json
uip df records list <entity-id> [--folder-key <folder-uuid>] --output json
```

`entities get` gives the exact column names for `_filters`, `fieldValues`, `fieldUpdates`, and `_selectedFieldNames`, plus each column's type, nullability, and whether it is a system field. Read a real record before writing a `byId` selector — an invented id matches nothing, and a read that matches nothing does not fault.

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

A single-record read faults only on an **over**-match. Zero matches completes normally, leaving `$vars.readOrder.output` unresolved — so treat "not found" as a branch, not an error.

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
      "_sort": { "field": "CreateTime", "direction": "desc" },
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

The emitted query **always** carries an explicit `limit`: omitting `_recordLimit` resolves to **100**, and any value is clamped to 1–1000. 1000 is a hard ceiling, so the only way to cover a larger entity is to page with `_skip` — raising `_recordLimit` past 1000 silently truncates. Pair any limit with `_sort`, or the slice is arbitrary.

`CreateTime` above is the real server-managed audit column. The audit columns are `Id`, `CreateTime`, `CreatedBy`, `UpdateTime`, `UpdatedBy` — there is no `CreatedAt`, and a sort on a non-existent column is not caught by `flow validate`.

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
        { "field": "Notes", "value": "Created by flow" }
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
        { "field": "Notes", "value": "Shipped by flow" },
        { "field": "ShippedAt", "value": "=js:$vars.start.output.shippedAt" }
      ]
    }
  }
}
```

`readEntityNodeId` must match the Read node's `id` exactly — see [Record selection](#record-selection) for what happens when it does not.

Timestamps come in as ISO 8601 strings from a variable or an upstream [Script](../script/impl.md) node, as above. Do not reach for `new Date()` in a `=js:` value — the Jint runtime's `Date` support is limited ([variables-and-expressions.md](../../../shared/variables-and-expressions.md)), and here a value the serializer cannot coerce is rejected by Data Fabric and the rejection is swallowed, so the column simply stays unchanged.

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

## Write bodies

Both write editors take `[{ field, value }]` rows, but what a value means differs by verb and by column type. The serializer coerces each value using the column's declared type from the `_outputSchema` snapshot; a value it cannot coerce is passed through as a string for the API to reject, **and that rejection is only logged** — it surfaces as an unchanged row, not a failed run.

| Column kind | What the row's `value` must be |
| --- | --- |
| String | The text itself |
| Integer / number | A clean numeric literal. `42.5` in an integer column is not coerced and is rejected |
| Boolean | `true` or `false` |
| **Choice set (single)** | The choice's numeric **`numberId`**, not its label — the column's SQL type is `INT` |
| **Choice set (multi)** | A JSON array of those numeric ids, as a **string**: `{ "field": "Tags", "value": "[1,2]" }`. The column is `NVARCHAR`, so the text is written through uncoerced and Data Fabric parses the array itself — not a real JSON array in the `value` slot |
| **System columns** | Never writable — see below |
| **Attachment columns** | Never writable |

**System columns are `Id`, `CreateTime`, `CreatedBy`, `UpdateTime`, `UpdatedBy`.** Data Fabric assigns them. The canvas hides them from both write editors, but the serializer has no guard: a hand-authored `{ field: "Id", … }` or `{ field: "UpdatedBy", … }` satisfies the validator's "at least one field" rule, ships in the body, and is rejected and swallowed.

**Blank values differ by verb.** On Create a blank value is omitted, letting the column default apply. On Update a blank value writes an explicit `null`, which **a non-nullable column rejects** — so "clear the column" only works on a nullable one. Nullability is not carried in the node's snapshot, so check it with `uip df entities get`.

## Schema snapshots

The entity panels persist snapshots of the picked entity onto `entityConfig`: `_entityFields`, `_relatedFields`, `_outputSchema`, `_choiceSets`, `_entityDisplayName`. When editing a node the canvas created, **preserve every one you are not deliberately changing.**

They are not decoration, and two of them are load-bearing when authoring from scratch:

- **`_entityFields` is mandatory for any dotted related path.** A filter on `customer.Name` resolves its first segment against this snapshot; without it the path is unresolvable, and the serializer refuses **the whole query** — the node emits nothing and every downstream `$vars` reference breaks. Related paths are capped at 3 segments, and a 3-segment path's last segment must literally be `Id`.
- **`_outputSchema` is the only input to write-body type coercion.** Without it nothing is coerced: `{ field: "Quantity", value: "5" }` serializes as the string `"5"` on an integer column, is rejected, and is swallowed.

So a from-scratch node is safe with plain scalar filters and string columns, and needs these snapshots as soon as it touches a related path, a typed column, or a choice set. When you cannot produce them, keep the config to columns on the entity itself and let the canvas fill the rest in on first open.

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

A filter on a choice-set column compares against the numeric `numberId`, exactly as a write does — comparing against the label matches nothing.

Filter values may be literals or `=js:` expressions. Two rules the serializer enforces by refusing the **entire** query — which leaves the node with no output and breaks every downstream reference:

- **A filter value cannot reference `$self`,** and cannot use a value the engine's query bracket cannot carry. A query cannot wait on the record it is being run to fetch.
- **An expression switched on and left blank is refused,** rather than dropped. Dropping it would silently widen the read past what was written.

## Record selection

Update and Delete name one record through `recordSource`:

| `recordSource` | Required key | Resolves to |
| --- | --- | --- |
| `"byId"` | `recordId` | The record with that `Id`. A literal, or a `=js:` reference such as `=js:$vars.createOrder.output.Id` |
| `"fromRead"` | `readEntityNodeId` | The record the named Read node's query identifies — the query is recompiled, with `Id` forced into the selected fields |

Both selectors are validated as **non-blank after trimming**, because the serializer trims before deciding a selector is usable. A whitespace-only `recordId` is not "empty enough" to be an obvious mistake but is exactly as inert.

> **An absent `recordSource` does not mean the node is inert.** The validator requires the key, but the *serializer* infers the mode from whichever selector field is populated — `readEntityNodeId` wins, otherwise a non-blank `recordId` means `byId`. So a legacy or hand-edited config carrying `{ entityName, recordId }` and no `recordSource` compiles a **real** delete or update. Never read a missing `recordSource` in an existing file as dead code; resolve it explicitly.

A `fromRead` target fails **silently** in three ways, none of which any validation rule catches, because each makes the serializer emit a plain no-op task:

1. `readEntityNodeId` names a node that does not exist (a typo, or a node id that changed).
2. The named Read is `resultMode: "multiple"` — a multi-record read is refused as a write target.
3. The named Read's filters do not all compile.

And at runtime, if the read matches more than one record, the engine re-runs the query as a single-record fetch and **swallows** the resulting over-match — the write is skipped and the run goes green. (The same over-match faults an ordinary read; only the write path swallows it.) A `fromRead` target must therefore be a genuinely single-record read, verified by you rather than by the runtime.

## Folder-scoped entities and bindings

A **tenant-scoped** entity needs nothing beyond `entityName`; the target serializes as `=datafabric.<EntityName>`.

A **folder-scoped** entity carries `_folderKey` (the entity's `folderId`). Its presence switches the emitted target to the folder-qualified form, and for the flow to survive export to another org the entity's name and folder must serialize as binding tokens rather than source-org literals. That requires:

1. `_resourceKey` (preferred) or `_entityKey` on the `entityConfig`, and
2. two top-level `bindings[]` rows for that key, with `resource: "Entity"` and `propertyAttribute` of `name` and `folderKey`.

```json
"bindings": [
  {
    "id": "bOrdersEntityName",
    "name": "Orders",
    "type": "string",
    "resource": "Entity",
    "resourceKey": "<resourceKey>",
    "default": "Orders",
    "propertyAttribute": "name"
  },
  {
    "id": "bOrdersEntityFolder",
    "name": "OrdersFolder",
    "type": "string",
    "resource": "Entity",
    "resourceKey": "<resourceKey>",
    "default": "<folder GUID>",
    "propertyAttribute": "folderKey"
  }
]
```

**Where `_resourceKey` comes from.** It is the key the entity's reference is registered under in the solution, written by the canvas entity picker when it registers the entity (`_entityKey`, the Data Fabric entity id from `uip df entities list`, is the older fallback and is only used when `_resourceKey` is absent). A registered entity reference surfaces under `uip solution resources list --kind Entity --output json`, but there is no CLI that mints one for a flow you are hand-authoring. **If you cannot resolve a `_resourceKey`, do not hand-author the folder-scoped form** — keep the entity tenant-scoped, or add the node and let the picker write `_folderKey`, `_resourceKey` and both binding rows on first open. A half-authored folder scope is worse than none: it serializes, and it breaks on deploy.

Two values are easy to get wrong, and both are things you type by hand:

- **`resource` is the capitalized `"Entity"`.** The BPMN engine matches case-insensitively, but packaging requires the capital form; a lowercase row never becomes a binding resource, so the deploy side gets no override at all.
- **`propertyAttribute` is `name` and `folderKey`** — never `folderPath`, and it is what the serializer matches on rather than the row's `name`.

Entity bindings differ from the Orchestrator-resource form in several other ways — what `name` holds, the matching key, the absent `resourceSubType`. Those are tabulated once in [file-format.md — Bindings — Data Fabric entity bindings](../../../shared/file-format.md#bindings--data-fabric-entity-bindings); read it before hand-authoring a pair.

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

The validator enforces the "green but inert" cases it can see structurally:

| Message | Means |
| --- | --- |
| `An entity must be selected` | `entityName` missing or empty |
| `Set a value for at least one field` | Create's `fieldValues` has no row with a non-blank value |
| `Select a field to update` | Update's `fieldUpdates` has no row naming a field |
| `A record ID is required` | `recordSource: "byId"` with a blank or whitespace-only `recordId` |
| `Select a Read entity records node` | `recordSource: "fromRead"` with no `readEntityNodeId` |
| `Choose how to identify the record` | Delete with `recordSource` missing or not one of `byId` / `fromRead` |

A separate rule refuses a query whose filter value the engine cannot carry, or whose related path cannot resolve.

What it does **not** check — every one of these validates clean and fails silently at runtime:

- whether a column name exists, or is writable, or has the type the value implies;
- whether the entity is native (writes) or federated (write is rejected and swallowed);
- whether an **Update** names a `recordSource` — only Delete's is in the required list, so an Update without one validates clean and the serializer infers the mode from whichever selector is populated;
- whether `readEntityNodeId` names a real node, or names a multi-record read;
- whether a `byId` record id matches any record.

Use `uip df entities get` and `uip df records list` to close that gap before shipping.

## Debug

| Symptom | Cause | Fix |
| --- | --- | --- |
| `Node not found: core.datafabric.*` on `registry get` | Tenant flag off, or CLI predates the node | `uip tools update`, then `uip maestro flow registry pull --force`; then confirm that node's flag with the admin (see the table above) |
| Node validates clean, runs green, nothing written | Most often a **selector** problem, not a binding one: `readEntityNodeId` names a missing node or a multi-record read, the read's filters do not compile, or the `fromRead` read matched more than one record at runtime | Check the Read node's `id` matches exactly and its `resultMode` is `single`; confirm the filter identifies exactly one record with `uip df records list` |
| Write runs green, row unchanged | The body was rejected and the rejection swallowed — a federated entity, a system or attachment column, a choice-set label instead of its numeric id, an uncoercible value, or a null into a non-nullable column | Re-check the entity is native and each column against `uip df entities get` |
| Downstream `$vars.<id>.output` is `undefined` | `variables.nodes[]` missing, or the read matched nothing | Run `uip maestro flow format`; if it persists, verify the filter matches a real record |
| A Loop over a multi-record read iterates nothing | Wired `output` instead of `output.results` | Use `=js:$vars.<readId>.output.results` |
| Multi-record read returns only some rows | The limit is always explicit and capped at 1000 | Page with `_skip`; raising `_recordLimit` past 1000 truncates silently |
| `404 Entity <name> does not exist` | Folder-scoped entity queried without folder qualification, or a related-field join | Set `_folderKey` and its bindings. Joins across a folder-scoped entity are not supported — the join request carries a bare name with no folder qualifier |
| Read returns every record | Filters compiled away — a blank expression row, or an `in` row in `single` mode | Check each row against [Filters](#filters) |
| Console warning `… has no name/folderKey binding — serializing a non-portable literal` | Folder-scoped entity missing a `bindings[]` row | Add both rows — see [Folder-scoped entities and bindings](#folder-scoped-entities-and-bindings) |

## What not to do

- **Do not hand-write `definitions[]`** — copy verbatim from `registry get`. A flag-gated node you cannot `registry get` is a node you cannot author.
- **Do not put a `model` block on the instance.** `bpmn:Task` and the debug runtime live in the definition.
- **Do not add an instance `outputs` block.** The canvas writes none for these nodes; the manifest `outputDefinition` plus `flow format`'s `variables.nodes[]` carry the contract.
- **Do not wire an `error` edge or set `errorHandlingEnabled`** — these four nodes have no error port. See [No error port](#no-error-port).
- **Do not write to a federated entity.** Create, Update and Delete require a native entity; the rejection is swallowed, so the run looks successful.
- **Do not write a system column** (`Id`, `CreateTime`, `CreatedBy`, `UpdateTime`, `UpdatedBy`) or an attachment column.
- **Do not put a choice-set label in a value or a filter** — use the numeric `numberId`.
- **Do not treat `AvailableOnTenant: false` as usable** because search returned the node.
- **Do not use a Data Fabric node in an API workflow** — all four exclude the `api-function` runtime.
- **Do not reference `$self` in a filter value,** and do not leave a filter expression blank — either refuses the whole query and strands every downstream reference.
- **Do not add a placeholder value to satisfy Create's "at least one value" rule.** The rule exists because a blank-only insert writes nothing; a junk value writes junk.
- **Do not strip `_entityFields` / `_outputSchema` / `_choiceSets` from an existing node** — related paths stop resolving and typed values stop coercing, both silently.
- **Do not point `folderPath` at the folder token** for a folder-scoped entity — use `folderKey`.
