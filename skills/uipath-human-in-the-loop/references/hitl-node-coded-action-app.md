# HITL Coded Action App (Inline) — Project Scaffold and Node Reference

Create a new coded action app project inside the solution using the user's own source code, then wire the HITL node to reference it.

Use this path when the user selects **New Coded Action App** in Step 3.

---

## Overview

| Step | Action |
|---|---|
| 1 | Generate keys |
| 2 | Create project folder and copy source code (excluding `node_modules`) |
| 3 | Add project to solution via CLI |
| 4 | Write solution resource files |
| 5 | Write HITL node into the `.flow` file |

---

## Step 1 — Generate Keys

Generate three UUIDs before writing any files. All three are used across multiple files — generate them once and reuse.

```bash
node -e "
const { randomUUID: r } = require('crypto');
console.log('APP_KEY=' + r());
console.log('PACKAGE_KEY=' + r());
console.log('PROJECT_KEY=' + r());
"
```

| Variable | Used in |
|---|---|
| `APP_KEY` | Resource file key, HITL node `inputs.app.key` |
| `PACKAGE_KEY` | Package resource key, app resource `spec.package.key` |
| `PROJECT_KEY` | `projectKey` in both resource files |

---

## Step 2 — Create Project Folder and Copy Source Code

Create this structure relative to `<SOLUTION_DIR>` (the directory containing the `.uipx` file):

```
<SOLUTION_DIR>/
└── <APP_NAME>/
    ├── project.uiproj
    ├── webAppManifest.json
    └── source/          ← contents copied from <SOURCE_PATH> provided by the user
```

### `<APP_NAME>/project.uiproj`

```json
{
  "ProjectType": "AppV2",
  "WebAppSettings": {
    "AppId": null,
    "IsCoreProject": false
  },
  "Name": "<APP_NAME>",
  "Description": null,
  "MainFile": null
}
```

### `<APP_NAME>/webAppManifest.json`

```json
{
  "type": "Coded",
  "solutionResourceSubType": "CodedAction",
  "config": {
    "isCompiled": true,
    "isActionApp": true,
    "bundlePath": "source/dist"
  }
}
```

### Copy source code

The source path provided by the user must already contain the built `dist/` folder. Copy its contents into `<APP_NAME>/source/`, skipping `node_modules`:

```bash
rsync -a --exclude='node_modules' "<SOURCE_PATH>/" "<SOLUTION_DIR>/<APP_NAME>/source/"
```

> The `dist/` folder must exist inside `<SOURCE_PATH>` before copying — it is the compiled output that the solution packages. If it is missing, ask the user to run their build first.

---

## Step 3 — Add Project to Solution

```bash
uip solution project add --project-path "<APP_NAME>/project.uiproj" --solution-path "<SOLUTION_DIR>"
```

This updates `<SOLUTION_DIR>/SolutionStorage.json` with a new `Projects` entry for the app.

> If the command reports the project is already registered, read `SolutionStorage.json` to confirm and skip this step.

---

## Step 4 — Write Solution Resource Files

Create directories as needed. All paths are relative to `<SOLUTION_DIR>`.

### 4a — Read and transform `action-schema.json`

Read `<SOURCE_PATH>/action-schema.json`. The file has this top-level shape:

```json
{
  "inputs":   { "type": "object", "properties": { ... } },
  "outputs":  { "type": "object", "properties": { ... } },
  "inOuts":   { "type": "object", "properties": { ... } },
  "outcomes": { "type": "object", "properties": { ... } }
}
```

Transform it into a `ParsedActionSchema` object using the algorithm below. This object is used in two places: JSON-stringified into `spec.actionSchema` in the resource file, and directly as `inputSchema`/`inOutSchema` arrays in the HITL node.

**Transform each property in `inputs.properties`, `outputs.properties`, and `inOuts.properties`:**

For each `{ propertyKey: propDef }` entry:

```json
{
  "name": "<propertyKey>",
  "key": "<new UUID>",
  "required": "<propDef.required ?? false>",
  "version": 0,
  "typeNamespace": "system",
  "isList": "<propDef.type === 'array'>",
  "collectionDataType": "<'Array' if array, else null>",
  "type": "<mapped .NET type — see table>",
  "properties": "<[] for scalars; recurse for object/array-of-object>"
}
```

For arrays (`propDef.type === "array"`): use `propDef.items.type` and `propDef.items.format` to determine the .NET type; recurse on `propDef.items.properties` if the item type is `"object"`.
For objects (`propDef.type === "object"`): recurse on `propDef.properties`.

**Type mapping** (`itemType` = `propDef.type` for scalars, `propDef.items.type` for arrays; `itemFormat` = `propDef.format` or `propDef.items.format`):

| Condition | .NET type |
|---|---|
| `itemFormat === "uuid"` | `System.Guid` |
| `itemFormat === "date"` | `System.DateOnly` |
| `itemType === "string"` | `System.String` |
| `itemType === "integer"` | `System.Int64` |
| `itemType === "number"` | `System.Decimal` |
| `itemType === "boolean"` | `System.Boolean` |
| `itemType === "object"` | `System.Object` |
| `itemType === "file"` | `UiPath.Platform.ResourceHandling.IResource` |

**Transform each property in `outcomes.properties`:**

```json
{
  "name": "<propertyKey>",
  "key": "<new UUID>",
  "required": false,
  "type": "System.String",
  "typeNamespace": "system",
  "isList": false,
  "collectionDataType": null,
  "properties": [],
  "version": 0
}
```

**Assemble the final `ParsedActionSchema`:**

```json
{
  "key": "<new UUID>",
  "version": 0,
  "description": "Action Schema",
  "id": "ID<new UUID with dashes removed>",
  "name": "ActionSchema",
  "inputs":   [ /* transformed inputs */ ],
  "outputs":  [ /* transformed outputs */ ],
  "inOuts":   [ /* transformed inOuts */ ],
  "outcomes": [ /* transformed outcomes */ ]
}
```

Set `ACTION_SCHEMA_JSON_STRING = JSON.stringify(parsedSchema)`.

### 4b — Read `externalClientId` from `uipath.json`

Read `<SOURCE_PATH>/uipath.json`. Use its `clientId` field as `externalClientId` in the resource file below.

### File: `resources/solution_folder/app/codedAction/<APP_NAME>.json`

```json
{
  "docVersion": "1.0.0",
  "resource": {
    "name": "<APP_NAME>",
    "kind": "app",
    "type": "codedAction",
    "apiVersion": "apps.uipath.com/v1",
    "projectKey": "<PROJECT_KEY>",
    "isOverridable": true,
    "dependencies": [
      { "name": "<APP_NAME>", "kind": "package" }
    ],
    "runtimeDependencies": [],
    "files": [],
    "folders": [{ "fullyQualifiedName": "solution_folder" }],
    "spec": {
      "name": "<APP_NAME>",
      "description": null,
      "version": "1.0.0",
      "routingName": null,
      "appSystemName": null,
      "package": { "key": "<PACKAGE_KEY>" },
      "externalClientId": "<clientId from uipath.json>",
      "actionSchema": "<ACTION_SCHEMA_JSON_STRING>"
    },
    "locks": [],
    "key": "<APP_KEY>"
  }
}
```

> `appSystemName` is `null` for a new app; the platform populates it on first deployment.

### File: `resources/solution_folder/package/<APP_NAME>.json`

```json
{
  "docVersion": "1.0.0",
  "resource": {
    "name": "<APP_NAME>",
    "kind": "package",
    "apiVersion": "orchestrator.uipath.com/v1",
    "projectKey": "<PROJECT_KEY>",
    "isOverridable": true,
    "dependencies": [],
    "runtimeDependencies": [],
    "files": [],
    "folders": [{ "fullyQualifiedName": "solution_folder" }],
    "spec": {
      "fileName": null,
      "fileReference": null,
      "name": "<APP_NAME>",
      "description": null
    },
    "locks": [],
    "key": "<PACKAGE_KEY>"
  }
}
```

---

## Step 5 — Write the HITL Node

All values below come directly from the `ParsedActionSchema` assembled in Step 4a — reuse the same objects and UUIDs, do not regenerate them.

- `inputs.app.inputSchema` = the `inputs` array from `ParsedActionSchema`
- `inputs.app.inOutSchema` = the `inOuts` array from `ParsedActionSchema`
- `schema.outcomes` = for each entry in `ParsedActionSchema.outcomes`: `{ "name": outcome.name, "type": "string" }`

### Full Node JSON

```json
{
  "id": "<NODE_ID>",
  "type": "uipath.human-in-the-loop",
  "typeVersion": "1.0.0",
  "display": { "label": "<LABEL>" },
  "ui": { "position": { "x": 474, "y": 144 } },
  "inputs": {
    "type": "custom",
    "channels": [],
    "recipient": {
      "channels": ["ActionCenter"],
      "connections": {},
      "assignee": { "type": "group" }
    },
    "app": {
      "name": "<APP_NAME>",
      "key": "<APP_KEY>",
      "folderPath": "solution_folder",
      "inputSchema": [ /* ParsedActionSchema.inputs */ ],
      "inOutSchema": [ /* ParsedActionSchema.inOuts */ ],
      "appSystemName": null,
      "appVersionRef": null
    },
    "schema": {
      "inputs": [],
      "outputs": [],
      "inOuts": [],
      "outcomes": [ /* { name, type: "string" } for each ParsedActionSchema.outcomes entry */ ]
    }
  },
  "model": { "type": "bpmn:UserTask", "serviceType": "Actions.HITL" }
}
```

**`inputs.recipient` options** — same as AppTask:

```json
// Action Center, unassigned (default)
"recipient": { "channels": ["ActionCenter"], "connections": {}, "assignee": { "type": "group" } }

// Specific user by email
"recipient": { "channels": ["Email"], "assignee": { "type": "user", "value": "user@company.com" } }

// Named group
"recipient": { "channels": ["ActionCenter"], "assignee": { "type": "group", "value": "Finance Team" } }
```

**Definition entry** — same as QuickForm. See [hitl-node-quickform.md](hitl-node-quickform.md) for the full definition block. Add once to `workflow.definitions`, deduplicated by `nodeType`.

**Edge wiring** — wire `completed`, `cancelled`, `timeout`. See [hitl-node-quickform.md](hitl-node-quickform.md) for edge format.

**`variables.nodes` regeneration** — add `result` and `status` entries for the new node, then replace the entire array. See [hitl-node-quickform.md](hitl-node-quickform.md) for the regeneration algorithm.

---

## Runtime Variables

| Variable | Contents |
|---|---|
| `$vars.<nodeId>.result` | Outputs the human filled in via the app form |
| `$vars.<nodeId>.status` | `"completed"`, `"cancelled"`, or `"timeout"` |
