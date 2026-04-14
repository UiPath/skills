# HITL AppTask Node — Direct JSON Reference

The AppTask variant uses a deployed coded app (Studio Web) as the task form. Same node type as QuickForm (`uipath.human-in-the-loop`), same three output handles. Difference: `inputs.type = "custom"` and `inputs.app` points to the deployed app.

---

## App Lookup and Solution Registration

Before writing the node JSON, resolve the app and register it with the solution. All API calls use auth from the stored login session (`uip login`).

### Step 1 — Resolve solution context and credentials

**Read credentials from the active `uip` session:**

```bash
source "$HOME/.uipath/.auth"
# Variables now available:
# UIPATH_ACCESS_TOKEN       — bearer token
# UIPATH_URL                — e.g. https://alpha.uipath.com
# UIPATH_ORGANIZATION_NAME  — org name (slug)
# UIPATH_ORGANIZATION_ID    — org UUID
# UIPATH_TENANT_NAME
# UIPATH_TENANT_ID
# UIPATH_PROJECT_ID
```

Map to working variables:

| Variable | Source |
|---|---|
| `BASE_URL` | `$UIPATH_URL` |
| `ORG_NAME` | `$UIPATH_ORGANIZATION_NAME` |
| `ORG_ID` | `$UIPATH_ORGANIZATION_ID` |
| `TENANT_ID` | `$UIPATH_TENANT_ID` |
| `ACCESS_TOKEN` | `$UIPATH_ACCESS_TOKEN` |
| `USER_ID` | `sub` claim — base64url-decode the middle segment of `ACCESS_TOKEN`, parse JSON, read `sub` |

**Resolve solution context:**

Find the `.uipx` file: look in the flow file's directory first, then its parent directory.

Parse it as JSON:

```json
{
  "SolutionId": "<SOLUTION_ID>",
  "Projects": [
    { "Id": "<PROJECT_KEY>", "ProjectRelativePath": "<ProjectName>/<ProjectName>.uiproj" }
  ]
}
```

Extract `SolutionId` → `SOLUTION_ID`. Find the entry in `Projects[]` whose directory matches the flow file's directory → its `Id` is `PROJECT_KEY`.

> If no project entry matches, the project is not registered. Run `uip solution project add` first.

### Step 2 — Search for apps

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

Headers: `Authorization: Bearer {ACCESS_TOKEN}`, `Accept: application/json`, `x-uipath-tenantid: {TENANT_ID}`

Response:

```json
{
  "solutionResources": [
    {
      "fullyQualifiedName": "Shared",
      "path": "Shared",
      "key": "<folderKey>",
      "resources": [
        { "key": "<appKey>", "name": "Invoice Approval", "type": "Coded Action", "kind": "app" }
      ]
    }
  ],
  "availableResources": [...],
  "nextPageCursor": null
}
```

If this returns 401, upload the solution uipx file first by just using the solution-tool cli upload command, do not bundle the solution.

Flatten both `solutionResources` and `availableResources` folder groups into a single list. Each item carries: `key`, `name`, `type`, `kind`, and its parent `folder` (`fullyQualifiedName`, `path`, `folderKey`).

**Selection rules:**

- **Exactly one match** → use it, proceed to Step 3.
- **Multiple matches** → present a numbered list to the user and wait for their choice before proceeding:

  > I found multiple apps matching that name. Which one should I use?
  > 1. **Invoice Approval** — Shared / Coded Action
  > 2. **Invoice Approval** — Finance / VB Action
  >
  > Reply with the number of the app you want.

  Use `nextPageCursor` to fetch additional pages if the list is truncated. Do not proceed until the user selects.

- **Zero matches** → stop and tell the user: "No deployed app named `<APP_NAME>` was found. Verify the name and that the app is deployed, then try again."

### Step 3 — Retrieve app configuration

```
POST {BASE_URL}/{ORG_NAME}/studio_/backend/api/resourcebuilder/solutions/{SOLUTION_ID}/resources/retrieve-configuration
Content-Type: application/json

{
  "key": "<selectedApp.key>",
  "name": "<selectedApp.name>",
  "kind": "app",
  "type": "<selectedApp.type>",
  "folder": <selectedApp.folder>
}
```

Headers: `Authorization: Bearer {ACCESS_TOKEN}`, `Content-Type: application/json`, `Accept: application/json`, `x-uipath-tenantid: {TENANT_ID}`

The response is a resource object. Key extractions from `spec`:

| Extract | Field | Notes |
|---|---|---|
| `APP_SYSTEM_NAME` | `spec.appSystemName` | |
| `APP_VERSION_REF` | `spec.appVersionRef` | object `{ key, name }` |
| `VERSION` | `spec.version` | default `"1.0.0"` if absent |
| `inputSchema` | parsed from `spec.actionSchema` → `.inputs` | `spec.actionSchema` is a **JSON string** — parse it first |
| `inOutSchema` | parsed from `spec.actionSchema` → `.inOuts` | |
| `folder` | `raw.folder.fullyQualifiedName`, `.path`, `.folderKey` | fall back to `selectedApp.folder` values |

> If this call fails, warn and continue with empty `inputSchema`/`inOutSchema`.

### Step 4 — Write solution resource files

Create directories as needed. All paths are relative to `<solutionDir>` (the directory containing the `.uipx` file).

**File 1: `resources/solution_folder/app/<app.type>/<AppName>.json`**

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

> Write `spec.actionSchema` verbatim from the API response. Re-serializing it changes unicode escapes vs. plain quotes and will break schema matching.

**File 2: `resources/solution_folder/appVersion/<AppName>.json`** *(skip if `APP_SYSTEM_NAME` or `APP_VERSION_REF` are absent)*

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

`MAJOR_VERSION` = first segment of `VERSION` (e.g. `"2.0.1"` → `"2"`).

### Step 5 — Register app reference

```
POST {BASE_URL}/{ORG_NAME}/studio_/backend/api/resourcebuilder/solutions/{SOLUTION_ID}/resources/reference?api-version=2&forceUpdate=true
Content-Type: application/json

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

> If this call fails, warn and continue.

### Step 6 — Write debug overwrites

Read `<solutionDir>/userProfile/<USER_ID>/debug_overwrites.json` if it exists. Merge in the new entry — do not overwrite unrelated entries.

Structure:

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

Merge rules:
- Tenant entry for `TENANT_ID` exists → find resource by `solutionResourceKey` and replace, or append if not found.
- No tenant entry → add a new tenant object.

> If this write fails, warn and continue.

---

## Full Node JSON

```json
{
  "id": "invoiceReview1",
  "type": "uipath.human-in-the-loop",
  "typeVersion": "1.0.0",
  "display": { "label": "Invoice Review" },
  "ui": { "position": { "x": 474, "y": 144 } },
  "inputs": {
    "type": "custom",
    "channels": [],
    "recipient": {
      "channels": ["Email"],
      "assignee": { "type": "user", "value": "reviewer@company.com" }
    },
    "app": {
      "name": "Invoice Approval",
      "key": "c0ba97df-8a30-4fe0-b4b4-4611a631d77b",
      "folderPath": "Shared",
      "inputSchema": [],
      "inOutSchema": [],
      "appSystemName": "invoice-approval",
      "appVersionRef": { "key": "<APP_VERSION_REF.key>", "name": "Invoice Approval" }
    },
    "schema": {
      "inputs": [],
      "outputs": [],
      "inOuts": [],
      "outcomes": [{ "name": "Submit", "type": "string" }]
    }
  },
  "model": { "type": "bpmn:UserTask", "serviceType": "Actions.HITL" }
}
```

### `inputs.app` field mapping

| Field | Source | Example |
|---|---|---|
| `name` | `selectedApp.name` from search | `"Invoice Approval"` |
| `key` | `selectedApp.key` from search | `"c0ba97df-8a30-4fe0-b4b4-4611a631d77b"` |
| `folderPath` | `selectedApp.folder.fullyQualifiedName` from search | `"Shared"` |
| `inputSchema` | `config.inputSchema` from retrieve-configuration | `[]` |
| `inOutSchema` | `config.inOutSchema` from retrieve-configuration | `[]` |
| `appSystemName` | `config.appSystemName` from retrieve-configuration | `"invoice-approval"` |
| `appVersionRef` | `config.appVersionRef` from retrieve-configuration | `{ "key": "...", "name": "Invoice Approval" }` |

### `inputs.recipient` options

```json
// Action Center (default — no specific assignee)
"recipient": { "channels": ["ActionCenter"], "connections": {}, "assignee": { "type": "group" } }

// Specific user by email
"recipient": { "channels": ["Email"], "assignee": { "type": "user", "value": "user@company.com" } }

// Everyone in a group
"recipient": { "channels": ["ActionCenter"], "assignee": { "type": "group", "value": "Finance Team" } }
```

---

## Definition Entry

Same definition as QuickForm — see [hitl-node-quickform.md](hitl-node-quickform.md) for the full definition block. Add it once to `workflow.definitions`, deduplicated by `nodeType`.

---

## Edge Wiring

Identical to QuickForm. Wire `completed`, `cancelled`, `timeout`:

```json
{ "id": "invoiceReview1-completed-nextNode1-input", "sourceNodeId": "invoiceReview1", "sourcePort": "completed", "targetNodeId": "nextNode1", "targetPort": "input" },
{ "id": "invoiceReview1-cancelled-end1-input",      "sourceNodeId": "invoiceReview1", "sourcePort": "cancelled", "targetNodeId": "end1",      "targetPort": "input" },
{ "id": "invoiceReview1-timeout-end2-input",        "sourceNodeId": "invoiceReview1", "sourcePort": "timeout",   "targetNodeId": "end2",      "targetPort": "input" }
```

---

## `variables.nodes` — Regenerate After Adding

Same rule as QuickForm — add `result` and `status` entries for the new node, then replace the entire `variables.nodes` array. See [hitl-node-quickform.md](hitl-node-quickform.md) for the regeneration algorithm.

---

## Runtime Variables

Same as QuickForm:

| Variable | What it contains |
|---|---|
| `$vars.<nodeId>.result` | Outputs the human filled in via the app |
| `$vars.<nodeId>.status` | `"completed"`, `"cancelled"`, or `"timeout"` |
