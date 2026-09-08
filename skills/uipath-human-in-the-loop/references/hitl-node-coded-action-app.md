# HITL Coded Action App (Inline) — Project Scaffold and Node Reference

Create a coded action app project inside the solution from the user's source code and wire the HITL node to reference it. Use this path when the user selects **New Coded Action App** in Step 3.

## Overview

1. Generate keys.
2. Create `<APP_NAME>` and copy source code, excluding `node_modules`.
3. Add the project to the solution via CLI.
4. Write solution resources.
5. Write the HITL node in the `.flow` file.

## Step 1 — Generate Keys

Generate three UUIDs before writing files and reuse them everywhere:

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

## Step 2 — Create Project Folder and Copy Source Code

Create this structure relative to `<SOLUTION_DIR>`, the directory containing the `.uipx` file:

```
<SOLUTION_DIR>/
└── <APP_NAME>/
    ├── project.uiproj
    ├── webAppManifest.json
    └── source/          ← contents copied from <SOURCE_PATH>
```

Write `<APP_NAME>/project.uiproj`:

```json
{
  "ProjectType": "AppV2",
  "WebAppSettings": { "AppId": null, "IsCoreProject": false },
  "Name": "<APP_NAME>",
  "Description": null,
  "MainFile": null
}
```

Write `<APP_NAME>/webAppManifest.json`:

```json
{
  "type": "Coded",
  "solutionResourceSubType": "CodedAction",
  "config": { "isCompiled": true, "isActionApp": true, "bundlePath": "source/dist" }
}
```

Run:

```bash
rsync -a --exclude='node_modules' "<SOURCE_PATH>/" "<SOLUTION_DIR>/<APP_NAME>/source/"
```

Require `<SOURCE_PATH>/dist/`, the compiled output packaged by the solution. If it is missing, never wait for a build: fall back to QuickForm per SKILL.md Step 3's fallback rule, proceed, and state that you did so; the user can request a Coded Action App after it is built.

## Step 3 — Add Project to Solution

Run:

```bash
uip solution projects add --project-path "<APP_NAME>/project.uiproj" --solution-path "<SOLUTION_DIR>"
```

If the command reports that the project is already registered, read `SolutionStorage.json` to confirm and skip the command.

## Step 4 — Write Solution Resource Files

Create directories as needed. Paths are relative to `<SOLUTION_DIR>`.

### 4a — Transform `action-schema.json`

Read `<SOURCE_PATH>/action-schema.json`, shaped as:

```json
{
  "inputs": { "type": "object", "properties": { ... } },
  "outputs": { "type": "object", "properties": { ... } },
  "inOuts": { "type": "object", "properties": { ... } },
  "outcomes": { "type": "object", "properties": { ... } }
}
```

Build one `ParsedActionSchema` and reuse it in `spec.actionSchema` and directly for the HITL node's `inputSchema`/`inOutSchema`.

For every property in `inputs.properties`, `outputs.properties`, and `inOuts.properties`, recursively create:

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

For arrays, use `propDef.items.type` and `propDef.items.format`; recurse through `propDef.items.properties` for item type `object`. For objects, recurse through `propDef.properties`. Use `itemType = propDef.type` for scalars or `propDef.items.type` for arrays, and `itemFormat = propDef.format` or `propDef.items.format`:

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

Transform each `outcomes.properties` entry to:

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

Assemble:

```json
{
  "key": "<new UUID>",
  "version": 0,
  "description": "Action Schema",
  "id": "ID<new UUID with dashes removed>",
  "name": "ActionSchema",
  "inputs": [ /* transformed inputs */ ],
  "outputs": [ /* transformed outputs */ ],
  "inOuts": [ /* transformed inOuts */ ],
  "outcomes": [ /* transformed outcomes */ ]
}
```

Set `ACTION_SCHEMA_JSON_STRING = JSON.stringify(parsedSchema)`.

### 4b — Read `externalClientId` and write resources

Read `<SOURCE_PATH>/uipath.json` and use its `clientId` as `externalClientId`. Create `resources/solution_folder/app/codedAction/<APP_NAME>.json`:

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
    "dependencies": [{ "name": "<APP_NAME>", "kind": "package" }],
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

`appSystemName` is `null` for a new app; the platform populates it on first deployment.

Create `resources/solution_folder/package/<APP_NAME>.json`:

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

## Step 5 — Write the HITL Node

Reuse the same `ParsedActionSchema` objects and UUIDs; do not regenerate them:

- `inputs.app.inputSchema` = `ParsedActionSchema.inputs`
- `inputs.app.inOutSchema` = `ParsedActionSchema.inOuts`
- `schema.outcomes` = `{ "name": outcome.name, "type": "string" }` for each parsed outcome

```json
{
  "id": "<NODE_ID>",
  "type": "uipath.human-in-the-loop.coded-action-app",
  "typeVersion": "1.0.0",
  "display": { "label": "<LABEL>" },
  "ui": { "position": { "x": 474, "y": 144 } },
  "inputs": {
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

Use one of these `inputs.recipient` forms:

```json
// Action Center, unassigned (default)
"recipient": { "channels": ["ActionCenter"], "connections": {}, "assignee": { "type": "group" } }

// Specific user by email
"recipient": { "channels": ["Email"], "assignee": { "type": "user", "value": "user@company.com" } }

// Named group
"recipient": { "channels": ["ActionCenter"], "assignee": { "type": "group", "value": "Finance Team" } }
```

Add one definition entry to `workflow.definitions`, deduplicated by `nodeType`, using `nodeType: "uipath.human-in-the-loop.coded-action-app"`—not the QuickForm nodeType. See [hitl-node-apptask.md](hitl-node-apptask.md#definition-entry) for the full definition block.

Wire the `completed` handle only; it is the only handle available in v1.0. See [hitl-node-quickform.md](hitl-node-quickform.md) for edge format.

Add `output` and `status` entries for the new node to `variables.nodes`, then replace the entire array. See [hitl-node-quickform.md](hitl-node-quickform.md) for the regeneration algorithm.

## Runtime Variables

| Variable | Contents |
|---|---|
| `$vars.<nodeId>.output` | Outputs the human filled in via the app form |
| `$vars.<nodeId>.status` | Selected outcome's action value (`"Continue"` or `"End"`) |