# HITL AppTask Node — Direct JSON Reference

The AppTask variant uses a deployed coded app (Studio Web) as the task form. Node type: `uipath.human-in-the-loop.coded-action-app`. It has QuickForm's `input` and `completed` handles; `inputs.app` references a deployed app instead of an inline schema.

## App Lookup and Solution Registration

Before writing node JSON, resolve the app and register it with the solution. Run API calls with auth from the stored login session (`uip login`).

### 1. Resolve context and credentials

Run:

```bash
source "$HOME/.uipath/.auth"
```

Map `UIPATH_ACCESS_TOKEN`, `UIPATH_URL`, `UIPATH_ORGANIZATION_NAME`, `UIPATH_ORGANIZATION_ID`, `UIPATH_TENANT_NAME`, `UIPATH_TENANT_ID`, and `UIPATH_PROJECT_ID` to `ACCESS_TOKEN`, `BASE_URL`, `ORG_NAME`, `ORG_ID`, and `TENANT_ID`. Derive `USER_ID` from the `sub` claim by base64url-decoding the middle `ACCESS_TOKEN` segment, parsing its JSON, and reading `sub`.

Find the `.uipx` file in the flow file's directory and parse it as JSON:

```json
{
  "SolutionId": "<SOLUTION_ID>",
  "Projects": [
    { "Id": "<PROJECT_KEY>", "ProjectRelativePath": "<ProjectName>/<ProjectName>.uiproj" }
  ]
}
```

Set `SOLUTION_ID` from `SolutionId`. Select the `Projects[]` entry whose directory matches the flow file's directory and set `PROJECT_KEY` from `Id`. If none matches, run `uip solution projects add` first because the project is not registered.

### 2. Search for apps

Run:

```
GET {BASE_URL}/{ORG_NAME}/studio_/backend/api/resourcebuilder/solutions/{SOLUTION_ID}/resources/search
  ?kind=app
  &pageSize=25
  &projectKey={PROJECT_KEY}
  &includeSolutionResources=true
  &types=VB%20Action
  &types=Workflow%20Action
  &types=Coded%20Action
  &types=CodedAction
  &searchTerm={APP_NAME}
```

Send `Authorization: Bearer {ACCESS_TOKEN}`, `Accept: application/json`, and `x-uipath-tenantid: {TENANT_ID}`. Flatten `solutionResources` and `availableResources`; follow `nextPageCursor` when present. For each folder group retain each item's `key`, `name`, `type`, `kind`, and parent `fullyQualifiedName`, `path`, and `folderKey`.

If the request returns 401, upload the solution `.uipx` file first by just using the solution-tool cli upload command; do not bundle the solution.

Apply these selection rules:

- Exactly one match: use it and continue.
- Multiple matches: never block. Prefer an exact case-insensitive name match in a `Shared` folder; otherwise use the first result. State the selected app and alternatives so the user can correct it. Fetch more pages when truncated.
- Zero matches: never block. Fall back to QuickForm per SKILL.md Step 3's fallback rule and continue. State: `No deployed app named <APP_NAME> was found, so I used QuickForm instead. Verify the name and that the app is deployed, then ask me to swap it in.`

### 3. Retrieve configuration

Run:

```
POST {BASE_URL}/{ORG_NAME}/studio_/backend/api/resourcebuilder/solutions/{SOLUTION_ID}/resources/retrieve-configuration
```

Send `Content-Type: application/json`, `Authorization: Bearer {ACCESS_TOKEN}`, `Accept: application/json`, and `x-uipath-tenantid: {TENANT_ID}`. Use:

```json
{
  "key": "<selectedApp.key>",
  "name": "<selectedApp.name>",
  "kind": "app",
  "type": "<selectedApp.type>",
  "folder": <selectedApp.folder>
}
```

From the response set:

- `APP_SYSTEM_NAME` = `spec.appSystemName`
- `APP_VERSION_REF` = `spec.appVersionRef` (`{ key, name }`)
- `VERSION` = `spec.version`, default `"1.0.0"`
- `inputSchema` = parsed JSON-string `spec.actionSchema`, then `.inputs`
- `inOutSchema` = parsed JSON-string `spec.actionSchema`, then `.inOuts`
- `folder` = `raw.folder.fullyQualifiedName`, `.path`, and `.folderKey`, falling back to selected-app folder values

If retrieval fails, warn and continue with empty `inputSchema` and `inOutSchema`. For node `outputSchema`, parse `spec.actionSchema` and read `.outputs`.

### 4. Write solution resource files

Create directories as needed. Paths are relative to `<solutionDir>`, the directory containing `.uipx`.

Write `resources/solution_folder/app/<app.type>/<AppName>.json`:

```json
{
  "docVersion": "1.0.0",
  "resource": {
    "name": "<app.name>",
    "kind": "app",
    "type": "<app.type>",
    "apiVersion": "apps.uipath.com/v1",
    "isOverridable": true,
    "dependencies": [{ "name": "<app.name>", "kind": "appVersion" }],
    "runtimeDependencies": [],
    "files": [],
    "folders": [{ "fullyQualifiedName": "solution_folder" }],
    "spec": {
      "name": "<app.name>",
      "description": "<spec.description or null>",
      "type": "<spec.type or 'Regular'>",
      "appSystemName": "<APP_SYSTEM_NAME or app.key>",
      "version": "<VERSION or '1.0.0'>",
      "appVersionRef": "<APP_VERSION_REF or { name: app.name, key: app.key }>",
      "actionSchema": "<raw spec.actionSchema string — do not re-serialize>"
    },
    "locks": [],
    "key": "<app.key>"
  }
}
```

Write `resources/solution_folder/appVersion/<AppName>.json`; skip it if `APP_SYSTEM_NAME` or `APP_VERSION_REF` is absent:

```json
{
  "docVersion": "1.0.0",
  "resource": {
    "name": "<app.name>",
    "kind": "appVersion",
    "apiVersion": "apps.uipath.com/v1",
    "isOverridable": true,
    "dependencies": [],
    "runtimeDependencies": [],
    "files": [
      {
        "name": "<app.name>.uiapp",
        "kind": "appVersion",
        "url": "<BASE_URL>/<ORG_ID>/apps_/default/api/v1/default/models/<APP_SYSTEM_NAME>/publish/versions/<MAJOR_VERSION>/package",
        "key": "<APP_VERSION_REF.key>"
      }
    ],
    "folders": [],
    "spec": {
      "name": "<app.name>",
      "description": "",
      "appSystemName": "<APP_SYSTEM_NAME>",
      "version": "<VERSION or '1.0.0'>",
      "isAppPublic": false,
      "expressionLanguage": null,
      "publishNote": null,
      "uiappFile": "<APP_VERSION_REF.key>",
      "uiappFileName": "<app.name>.uiapp",
      "isUnifiedProject": null
    },
    "locks": [],
    "key": "<APP_VERSION_REF.key>"
  }
}
```

Set `MAJOR_VERSION` to the first `VERSION` segment (for example, `"2.0.1"` becomes `"2"`). Write `spec.actionSchema` verbatim from the API response; do not re-serialize it because changed unicode escapes or quote representation breaks schema matching.

### 5. Register the app reference

Run:

```
POST {BASE_URL}/{ORG_NAME}/studio_/backend/api/resourcebuilder/solutions/{SOLUTION_ID}/resources/reference?api-version=2&forceUpdate=true
```

Send `Content-Type: application/json`, `Authorization: Bearer {ACCESS_TOKEN}`, `Accept: application/json`, and `x-uipath-tenantid: {TENANT_ID}`. Use:

```json
{
  "kind": "app",
  "type": "<app.type>",
  "key": "<app.key>",
  "folder": {
    "fullyQualifiedName": "<folder.fullyQualifiedName>",
    "path": "<folder.path>",
    "folderKey": "<folder.folderKey>"
  }
}
```

If registration fails, warn and continue.

### 6. Write debug overwrites

Read `<solutionDir>/userProfile/<USER_ID>/debug_overwrites.json` if it exists and merge the app entry without overwriting unrelated entries:

```json
{
  "docVersion": "1.0.0",
  "tenants": [
    {
      "tenantKey": "<TENANT_ID>",
      "resources": [
        {
          "solutionResourceKey": "<app.key>",
          "reprovisioningIndex": 0,
          "overwrite": {
            "resourceKey": "<app.key>",
            "resourceName": "<app.name>",
            "folderKey": "<folder.folderKey>",
            "folderFullyQualifiedName": "<folder.fullyQualifiedName>",
            "folderPath": "<folder.path>",
            "type": "Reference",
            "kind": "app"
          }
        }
      ]
    }
  ]
}
```

If the tenant exists, replace the resource matching `solutionResourceKey` or append it; otherwise add a tenant object. If writing fails, warn and continue.

## Full Node JSON

```json
{
  "id": "<nodeId>",
  "type": "uipath.human-in-the-loop.coded-action-app",
  "typeVersion": "1.0",
  "display": { "label": "<label>" },
  "inputs": {
    "recipient": {
      "channels": ["ActionCenter"],
      "connections": {},
      "assignee": { "type": "group" }
    },
    "app": {
      "displayName": "<app.name>",
      "name": "<app.name>",
      "key": "<app.key>",
      "folderPath": "<folder.fullyQualifiedName>",
      "inputSchema": {
        "type": "object",
        "properties": { "<param>": { "type": "string" } }
      },
      "outputSchema": {
        "type": "object",
        "properties": { "<param>": { "type": "string" } }
      }
    },
    "appInputBindings": {
      "<parameter>": "=vars.<nodeId>.output.<field>"
    },
    "schema": {
      "fields": [],
      "outcomes": [{ "id": "submit", "name": "Submit", "type": "string", "isPrimary": true, "action": "Continue" }]
    }
  },
  "outputs": {
    "output": {
      "type": "object",
      "description": "Task result data",
      "source": "=result",
      "var": "output",
      "properties": {
        "Action": { "type": "string", "enum": ["Submit"], "default": "Submit" }
      }
    },
    "status": {
      "type": "string",
      "description": "Task completion status",
      "source": "=result.Action",
      "var": "status",
      "enum": ["Submit"],
      "default": "Submit"
    }
  }
}
```

### `inputs.app` mapping

- `displayName`, `name`: `selectedApp.name`
- `key`: `selectedApp.key`
- `folderPath`: `selectedApp.folder.fullyQualifiedName`
- `inputSchema`: JSON Schema object from parsed `config.actionSchema.inputs`
- `outputSchema`: JSON Schema object from parsed `config.actionSchema.outputs`

Both schemas must be `{ "type": "object", "properties": { ... } }`, not arrays. Parse `spec.actionSchema`, which is a JSON string, before extracting `inputs` and `outputs`.

### `inputs.appInputBindings`

Map app parameter names to expressions with an `=` prefix and no `js:`:

```json
"appInputBindings": {
  "<parameter>": "=vars.<path>"
}
```

### `inputs.recipient`

```json
// Action Center, default; no specific assignee
"recipient": { "channels": ["ActionCenter"], "connections": {}, "assignee": { "type": "group" } }

// Specific user by email
"recipient": { "channels": ["Email"], "assignee": { "type": "user", "value": "<user@company.com>" } }

// Everyone in a group
"recipient": { "channels": ["ActionCenter"], "assignee": { "type": "group", "value": "<group>" } }
```

## Definition Entry

Add exactly one definition entry to `workflow.definitions`, deduplicated by `nodeType`, using `nodeType` `"uipath.human-in-the-loop.coded-action-app"`, not `"uipath.human-in-the-loop.quick-form"`:

```json
{
  "nodeType": "uipath.human-in-the-loop.coded-action-app",
  "version": "1.0",
  "category": "human-task",
  "description": "App-based human task using a deployed coded action app",
  "tags": ["human-task", "hitl", "human-in-the-loop", "coded-action-app", "approval"],
  "sortOrder": 28,
  "display": { "label": "App Task", "icon": "users", "shape": "square" },
  "handleConfiguration": [
    {
      "position": "left",
      "handles": [{ "id": "input", "type": "target", "handleType": "input" }],
      "visible": true
    },
    {
      "position": "right",
      "handles": [{ "id": "completed", "type": "source", "handleType": "output", "showButton": true, "constraints": { "forbiddenTargetCategories": ["trigger"] } }],
      "visible": true
    }
  ],
  "model": { "type": "bpmn:UserTask", "serviceType": "Actions.HITL" },
  "outputDefinition": {
    "output": { "type": "object", "description": "Task result data", "source": "=result", "var": "output" },
    "status": { "type": "string", "description": "Task completion status", "source": "=result.Action", "var": "status" }
  }
}
```

## Edge Wiring

Wire only `completed`; v1.0 has no `cancelled` or `timeout` handles:

```json
{ "id": "<nodeId>-completed-<targetNodeId>-input", "sourceNodeId": "<nodeId>", "sourcePort": "completed", "targetNodeId": "<targetNodeId>", "targetPort": "input" }
```

## `variables.nodes` — Regenerate After Adding

Use the same rule as QuickForm: add `output` and `status` entries for the new node, then replace the entire `variables.nodes` array. See [hitl-node-quickform.md](hitl-node-quickform.md) for the regeneration algorithm.

## Runtime Variables

| Variable | Contents |
|---|---|
| `$vars.<nodeId>.output` | Outputs the human filled in via the app |
| `$vars.<nodeId>.status` | Selected outcome's action value (`"Continue"` or `"End"`) |