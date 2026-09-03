# Data Fabric Entity Nodes — Planning

The Data Fabric entity nodes read and write **records inside a UiPath Data Fabric entity** natively — no Integration Service connection, no HTTP call. They live in the **Data Fabric** section of the add-node panel. Four nodes cover the CRUD surface, and they share one entity picker, one filter grammar, and one `inputs.entityConfig` container.

Use them whenever the flow's own data lives in Data Fabric: a case record, a lookup table, a status the flow advances, an audit row the flow appends.

## Node Types

| Node Type | Canvas label | Does |
| --- | --- | --- |
| `core.datafabric.read` | Read entity records | Read one record, or a filtered list of records |
| `core.datafabric.create` | Create entity record | Insert one record and return the stored row |
| `core.datafabric.update` | Update entity record | Patch named columns on one record |
| `core.datafabric.delete` | Delete entity record | Delete one record (no output) |

These are fixed OOTB node types — no registry suffix, no connector key. Each is gated by its own tenant feature flag, so a tenant can have Read without Create:

| Node Type | Tenant flag |
| --- | --- |
| `core.datafabric.read` | `canvas.nodes.read-entity` |
| `core.datafabric.create` | `canvas.nodes.create-entity` |
| `core.datafabric.update` | `canvas.nodes.update-entity` |
| `core.datafabric.delete` | `canvas.nodes.delete-entity` |

A node whose flag is off is filtered out of the manifest entirely: `registry search` may still list it with `AvailableOnTenant: false`, but `registry get` answers **"Node not found"** and you cannot source its `definitions[]` entry. Confirm availability before planning around one — see [impl.md — Registry validation](impl.md#registry-validation).

## Writes require a native entity

Create, Update and Delete work only against **native** Data Fabric entities. A federated entity (one projecting an external system) can be read but never written through these nodes.

Nothing enforces this outside the canvas: the three write panels filter their picker to native entities, but there is **no validation rule**. A hand-authored write against a federated entity passes `flow validate`, serializes, is rejected by Data Fabric, and the rejection is swallowed — a green run that changed nothing. Reads against the same entity keep working, which makes it read like a write bug rather than an entity-class one.

Resolve the class up front with `uip df entities list --native-only --output json` and plan writes only against entities in that list.

## When to Use

Use these nodes when the record lives in **Data Fabric** and the flow itself is the thing reading or writing it.

### Selection Heuristics

| Situation | Use a Data Fabric entity node? |
| --- | --- |
| Look up a record by key to drive a decision or fill a downstream input | Yes — Read, `resultMode: "single"` |
| Fetch a filtered set of rows to iterate over | Yes — Read, `resultMode: "multiple"`, then [Loop](../loop/planning.md) |
| Advance a status, stamp a result, write back an outcome | Yes — Update (native entity) |
| Append a new row (case, audit entry, request) | Yes — Create (native entity) |
| Remove a row the flow has finished with | Yes — Delete (native entity) |
| Write to a federated entity | No — these nodes cannot; use [connector](../connector/planning.md) or [http](../http/planning.md) |
| React to a record being created/updated **elsewhere** | No — that is a trigger; use [connector-trigger](../connector-trigger/planning.md) (`uipath.connector.trigger.uipath-uipath-dataservice.record-created` / `record-updated`) |
| Aggregate, group, or reshape rows already in memory | No — use [Transform](../transform/planning.md) |
| Bulk-load a CSV into an entity | No — that is a data-loading job, not a flow step; use `uip df records import` out of band |
| Read a record from a non-UiPath system | No — use [connector](../connector/planning.md) or [http](../http/planning.md) |

### Native node vs Data Service connector — pick the native node

The `uipath-uipath-dataservice` Integration Service connector also exposes entity operations (`QueryEntityRecordsCurated`, `CreateEntityRecordCurated`, …), and `registry search` surfaces both. **Prefer the native `core.datafabric.*` node**, because it:

- needs **no Integration Service connection** — nothing to create, bind, or keep healthy, and no `bindings[]` connection row;
- is **user-owned** — author it with `Edit`/`Write` instead of the CLI's `node add` + `node configure` envelope (see [Author capability — Node ownership](../../CAPABILITY.md#node-ownership--who-authors-the-node));
- gives downstream expressions the **record shape** (`$vars.readOrder1.output.Status`) with autocomplete, because the picked entity's schema is merged into the node's output definition;
- carries **portable entity bindings**, so a folder-scoped entity survives export to another org.

Choose the connector when the native node is unavailable (flag off), when the entity is federated, or when you need an operation the native nodes do not cover. Record that choice in **Open Questions** rather than making it silently.

### Anti-Patterns

- **Do not use Delete to "clear" a field.** Delete removes the whole record. To blank a column, use Update with an empty `value` — but see the nullability caveat in [impl.md — Write bodies](impl.md#write-bodies).
- **Do not chain Read → Update by re-typing the record id.** Use `recordSource: "fromRead"` and point at the Read node; it reuses that node's query, so the two can never drift apart.
- **Do not read a whole entity to find one row.** Push the constraint into `_filters` — a `resultMode: "multiple"` read with no filter returns the first 100 rows in arbitrary order, not "everything".
- **Do not use these nodes inside an API workflow runtime.** All four declare `runtimeConstraints.exclude: ["api-function"]`; the read/write is dispatched by the BPMN engine, which no other runtime implements.
- **Do not feed an Update node's output into a [Loop](../loop/planning.md) collection or a [Transform](../transform/planning.md).** That output is re-read per consumer, and collection consumers are excluded from the rewriting — see [Output Variables](#output-variables).

## Ports

| Node Type | Input | Output |
| --- | --- | --- |
| `core.datafabric.read` | `input` | `output` |
| `core.datafabric.create` | `input` | `output` |
| `core.datafabric.update` | `input` | `output` |
| `core.datafabric.delete` | `input` | `output` |

**These four nodes have no `error` port.** Unlike most action nodes, none of them declares `supportsErrorHandling`, so no error handle is ever injected and the properties panel offers no error-handling toggle. Do not set `inputs.errorHandlingEnabled` and do not add an edge with `sourcePort: "error"` — the serializer will still emit a boundary event for it, but with no error mapping, and the canvas shows no handle the author can see or remove. Plan failure handling upstream or downstream instead.

Delete's `output` port exists for **sequencing only** — it carries no data (see below).

## Output Variables

| Node Type | `$vars.{nodeId}.output` |
| --- | --- |
| `core.datafabric.read` (`single`) | The record itself — address columns directly: `$vars.readOrder1.output.Status` |
| `core.datafabric.read` (`multiple`) | `{ results: [...] }` — the rows are under `output.results`, never `output` itself |
| `core.datafabric.create` | The **stored** record, including the generated `Id` and server-applied defaults |
| `core.datafabric.update` | The record **after** the write |
| `core.datafabric.delete` | Nothing — the node declares no output definition |

Three consequences worth planning around:

- **A multi-record read is not an array.** `=js:$vars.listOrders1.output` is an object; the collection is `=js:$vars.listOrders1.output.results`. Wiring the former into a Loop iterates nothing.
- **Update's output is a re-read, not the write's response.** The engine discards the write response; the serializer rewrites each downstream `$vars.<updateId>.output` reference into its own query for the record just written. That is why it cannot be consumed as a Loop or Transform collection — those are excluded from the rewriting and have no snapshot to fall back on.
- **A read that matches nothing does not fault.** Only an *over*-match faults a single-record read. Zero matches completes normally and leaves `$vars.<readId>.output` unresolved, so a downstream Decision silently takes its falsy branch. If "not found" is a real business case, branch on it explicitly.

Delete has no output at all, so plan any post-delete signalling (a count, a status) as a separate [Script](../script/planning.md) or End-node mapping.

## Key Inputs

Every node takes exactly one input object, `inputs.entityConfig`. Its contents differ per node.

### Shared by all four

| Key | Required | Description |
| --- | --- | --- |
| `entityName` | Yes | The entity's technical name. Resolve it with `uip df entities list` — never invent it |
| `_folderKey` | Folder-scoped entities only | The entity's `folderId`. Its presence switches the emitted target to the folder-qualified form and makes `bindings[]` entries necessary for portability — see [impl.md — Folder-scoped entities](impl.md#folder-scoped-entities-and-bindings) |
| `_resourceKey` / `_entityKey` | With `_folderKey` | Key the entity's `bindings[]` rows are scoped to |

The canvas also persists schema snapshots (`_entityFields`, `_relatedFields`, `_outputSchema`, `_choiceSets`). They are not decoration — see [impl.md — Schema snapshots](impl.md#schema-snapshots) for when authoring without them silently breaks.

### `core.datafabric.read`

| Key | Required | Description |
| --- | --- | --- |
| `resultMode` | No | `"single"` (default) or `"multiple"` |
| `_filters` | No | The query. Grouped filter model — see [impl.md — Filters](impl.md#filters) |
| `_selectedFieldNames` | No | Columns to return. Omit for all |
| `_recordLimit` | `multiple` only | Row cap, clamped 1–1000. Omitted resolves to **100** — the emitted query always carries an explicit limit |
| `_skip` | `multiple` only | Rows to pass over first. The only way past the 1000-row ceiling |
| `_sort` | `multiple` only | `{ field, direction: "asc" \| "desc" }`. A limit without an order returns an arbitrary slice |

### `core.datafabric.create`

| Key | Required | Description |
| --- | --- | --- |
| `fieldValues` | Yes | `[{ field, value }]`. **At least one row must carry a non-blank `value`** — blank values are omitted so the column default applies, so an all-blank config inserts nothing and still runs green |

### `core.datafabric.update`

| Key | Required | Description |
| --- | --- | --- |
| `recordSource` | Yes | `"byId"` or `"fromRead"` — how the target record is identified |
| `recordId` | `byId` | The record's `Id` — a literal or a `=js:` reference |
| `readEntityNodeId` | `fromRead` | The upstream Read node whose query identifies the record |
| `fieldUpdates` | Yes | `[{ field, value }]`. An **empty `value` writes an explicit null**, which a non-nullable column rejects |

### `core.datafabric.delete`

| Key | Required | Description |
| --- | --- | --- |
| `recordSource` | Yes | `"byId"` or `"fromRead"`. The validator requires it — but do not read its absence as "inert" ([impl.md — Record selection](impl.md#record-selection)) |
| `recordId` | `byId` | The record's `Id` |
| `readEntityNodeId` | `fromRead` | The upstream Read node identifying the record |

## Record selection — `byId` vs `fromRead`

Update and Delete both need to name exactly one record, and offer the same two ways:

| Mode | Use when | Cost of getting it wrong |
| --- | --- | --- |
| `byId` | The id is already in hand — a trigger payload, a Create node's `output.Id`, a flow input | A blank or whitespace-only id resolves to nothing; the node runs green having written nothing |
| `fromRead` | An upstream Read already located the record by business key | The write is **skipped silently** if the read matches more than one record, names a node that does not exist, or is itself multi-record |

Prefer `fromRead` when a Read node is already there — it reuses that node's compiled query, so a later change to the filter automatically follows through to the write. But note the asymmetry: on the **read** path an over-match faults the element, while on the **write** path the engine swallows that same over-match and skips the write. A `fromRead` target must therefore be a genuinely single-record read; there is no runtime safety net telling you it was not.

## Common Pattern — read, branch, write back

```text
Trigger -> Read entity records (single, filter by business key)
        -> Decision (on a column)
             -> true:  Update entity record (fromRead) -> End
             -> false: Create entity record            -> End
```

The Decision is doing real work here: a read that matches nothing completes with an unresolved output, so the false branch is also the not-found branch.

## Planning Annotation

In the architectural plan:

- `datafabric: <verb> <EntityName> — <one-line purpose>`, naming the entity and, for a read, whether it is single or multiple.
- Name the **selector** for every Update and Delete (`byId` from `<source>`, or `fromRead` from `<readNodeId>`). An unnamed selector is the single most common way these nodes ship silently doing nothing.
- Record the entity's **class and scope** — native vs federated, tenant vs folder — because writes need native, and a folder-scoped entity needs `_folderKey` plus bindings.
- Put the entity in **Open Questions** when the requirements name a business concept ("the order", "the case") but no entity is confirmed by `uip df entities list`. Do not guess an entity or column name — they are case-sensitive and unmatched names are dropped rather than rejected.
