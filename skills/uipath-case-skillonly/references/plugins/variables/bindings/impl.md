# Bindings — Implementation

Bindings link tasks to their published resources (processes, agents, apps). Every standard-IO and action task requires two bindings: one for `name` and one for `folderPath`.

## Where Bindings Live

All bindings are declared in `root.data.uipath.bindings` — a flat array shared by all tasks. Tasks reference them via `=bindings.<id>`.

## Declaring a Binding Pair

For each process / agent / rpa / api-workflow / case-management task:

```json
{
  "id": "b<8chars>",
  "name": "name",
  "type": "string",
  "resource": "process",
  "propertyAttribute": "name",
  "resourceKey": "Shared/[CM] Insurance.BookAppraisal",
  "default": "BookAppraisal"
},
{
  "id": "b<8chars>",
  "name": "folderPath",
  "type": "string",
  "resource": "process",
  "propertyAttribute": "folderPath",
  "resourceKey": "Shared/[CM] Insurance.BookAppraisal",
  "default": "Shared/[CM] Insurance"
}
```

For action tasks, use `"resource": "app"`:

```json
{
  "id": "b<8chars>",
  "name": "name",
  "type": "string",
  "resource": "app",
  "propertyAttribute": "name",
  "resourceKey": "Shared/Claims.ApprovalApp",
  "default": "ApprovalApp"
},
{
  "id": "b<8chars>",
  "name": "folderPath",
  "type": "string",
  "resource": "app",
  "propertyAttribute": "folderPath",
  "resourceKey": "Shared/Claims.ApprovalApp",
  "default": "Shared/Claims"
}
```

## Referencing in Task Data

```json
"data": {
  "name": "=bindings.bCiT7IgAE",
  "folderPath": "=bindings.bbXi98qr7"
}
```

For Integration Service connector tasks (and any task wired to an external connector), use `"resource": "Connection"`. Connection bindings come in pairs: `ConnectionId` + `folderKey`. Declare one pair per distinct connector used by the case:

```json
{
  "id": "b<8chars>",
  "name": "uipath-microsoft-outlook365 connection",
  "type": "string",
  "resource": "Connection",
  "propertyAttribute": "ConnectionId",
  "resourceKey": "<connection-uuid>",
  "default": "<connection-uuid>"
},
{
  "id": "b<8chars>",
  "name": "FolderKey",
  "type": "string",
  "resource": "Connection",
  "propertyAttribute": "folderKey",
  "resourceKey": "<connection-uuid>",
  "default": "<folder-uuid>"
}
```

The `resourceKey` for Connection bindings is the connection UUID (NOT a `folder/project.process` string). The `default` for `ConnectionId` is the connection UUID; for `folderKey` it is the orchestrator folder UUID where the connection lives. Both bindings share the same `resourceKey` (the connection UUID) so the runtime can pair them.

Resolve `<connection-uuid>` and `<folder-uuid>` via `uip case registry get-connection --type <typecache-activities|typecache-triggers> --activity-type-id <id> --output json`.

## Resource vs App vs Connection

| Task type | `resource` value | Pair propertyAttributes |
|---|---|---|
| `process`, `agent`, `rpa`, `api-workflow`, `case-management` | `"process"` | `name` + `folderPath` |
| `action` | `"app"` | `name` + `folderPath` |
| `execute-connector-activity`, `wait-for-connector`, connector triggers | `"Connection"` | `ConnectionId` + `folderKey` |

## resourceSubType (Optional)

For `resource: "process"`, the `resourceSubType` field indicates the specific process category. This is informational and helps the FE display the correct icon/label:

| Task type | `resourceSubType` |
|---|---|
| `rpa` (classic RPA process) | omit (no subtype) |
| `api-workflow` | `"Api"` |
| `agent` | `"Agent"` |
| `process` (agentic process / process orchestration) | `"ProcessOrchestration"` |
| `case-management` | omit (no subtype) |

Example with `resourceSubType`:

```json
{
  "id": "bDZHokoQJ",
  "name": "folderPath",
  "type": "string",
  "resource": "process",
  "resourceKey": "Lookup policy & historical claims",
  "default": "",
  "propertyAttribute": "folderPath",
  "resourceSubType": "Api"
},
{
  "id": "bjrd8GPnB",
  "name": "name",
  "type": "string",
  "resource": "process",
  "resourceKey": "Lookup policy & historical claims",
  "default": "Lookup policy & historical claims",
  "propertyAttribute": "name",
  "resourceSubType": "Api"
}
```

The `resourceSubType` should be included on **both** bindings in the pair (name and folderPath). Omit the field entirely for classic RPA processes — don't set it to `null` or empty string.

## resourceKey Format

`"<FolderPath>/<ProjectName>.<ProcessName>"`

Use `uip case registry search "<keyword>"` to find the exact resourceKey from the tenant registry.

## One Binding Pair Per Resource — Deduplicate Across Tasks

Bindings are **shared across tasks**. When multiple tasks reference the same underlying resource, declare exactly **one** binding pair and have every task reference the same `=bindings.<id>`. Production cases routinely share a single binding pair across 2–4 tasks (e.g., a "Coverage check" process called from 4 different stages — 1 binding pair, not 4).

### Dedup key

A binding is uniquely identified by **`(resource, resourceKey, propertyAttribute)`**. Two tasks that point to the same resourceKey with the same `propertyAttribute` share the same binding entry.

| If two tasks share | Then they share | And declare |
|---|---|---|
| Same `resourceKey` (same process / app / connection) | The same `name` binding AND the same `folderPath` binding | Just **one** pair total |
| Different `resourceKey` (different processes) | Nothing | Separate pairs each |

### Build procedure

When constructing `caseplan.json`:

1. Enumerate every task and collect the set of distinct `(resource, resourceKey)` tuples.
2. For each tuple, generate **one** binding pair (one `name` + one `folderPath`, or `ConnectionId` + `folderKey` for Connections). Store the binding IDs in a map keyed by `resourceKey`.
3. When writing each task, look up its `resourceKey` in the map and reference the existing binding IDs via `=bindings.<id>`.

Following this rule, a case with 17 process-type tasks calling 13 distinct processes will have 13 binding pairs (26 entries), not 17 pairs (34 entries) — matching the FE's emission.
