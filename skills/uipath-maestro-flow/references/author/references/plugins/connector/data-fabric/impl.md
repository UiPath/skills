# Data Fabric Activity Nodes

Data Fabric connector nodes (`uipath-uipath-dataservice`) give a Flow direct read/write access to UiPath Data Fabric entities via an Integration Service connection. For the standard IS connector workflow, see [parent connector impl.md](../impl.md).

---

## Activity Selection

| User says | Activity | Node type suffix |
|---|---|---|
| "query" / "list" / "search" / "find records" | Query Entity Records | `query-entity-records` |
| "create" / "insert" / "add a record" | Create Entity Record | `create-entity-record` |
| "update" / "modify" / "edit field" | Update Entity Record | `update-entity-record` |
| "delete" / "remove" | Delete Entity Record | `delete-entity-record` |
| "get by id" / "fetch one record" | Get Entity Record by ID | `get-entity-record-by-id` |

"Get all records matching X" → Query. "Get the record with ID Y" → Get by ID.

---

## Pre-Build Checklist

**1. Entity name** — `uip df entities list --native-only`. Use the exact CamelCase `Name` (e.g. `BankDetails`). For Create/Update, also `uip df entities get <entity-ID>` for field names — skip system fields (`Id`, `CreatedBy`, `CreateTime`, `UpdatedBy`, `UpdateTime`, `RecordOwner`).

**2. Connection** — Per [parent planning.md § Check Connector Connections](../planning.md#check-connector-connections), filter by `ConnectorKey = "uipath-uipath-dataservice"`. Capture `Id` (→ `connectionId`), `FolderKey`, and `Name` (→ binding name).

**3. Project name** — use what the user specifies; suggest `<EntityName>Flow` if they don't provide one.

---

## Activity Parameter Defaults

| Activity | Defaults |
|---|---|
| Query Entity Records | `start=0`, `limit=100`, `expansionLevel="3"`, `isAscending=false` |
| Create / Update / GetById | `expansionLevel="3"` |
| Delete | _(none)_ |

No body fields provided for Create → ask the user (field names are entity-specific). `expansionLevel` is always a **string** `"3"`, not a number.

**Paging:** To retrieve more than `limit=100` records, increment `start` by `limit` on each pass (e.g. `start=0`, then `start=100`, etc.) and repeat the Query node until the result count is less than `limit`. Use a Script node to accumulate results across pages.

---

## CEQL Filter Reference

Data Fabric Query passes a **raw CEQL string** under `queryParameters.queryExpression` — not the structured filter tree used by other connectors. For full operator syntax (`=`, `>`, `LIKE`, `IS NULL`, `AND` / `OR`), see [uipath-platform — Filter Trees (CEQL)](../../../../../../../uipath-platform/references/integration-service/activities.md#filter-trees-ceql).

| Pattern | Example |
|---|---|
| Equality | `AccountNumber = '788'` |
| AND / Compare | `BankName = 'HDFC' AND Amount > 1000` |
| Contains | `AccountHolderName LIKE '%Kumar%'` |

---

## Step 1 — Resolve the Connection

Per [parent impl.md § Step 1](../impl.md#step-1--fetch-and-bind-a-connection), filter by `ConnectorKey = "uipath-uipath-dataservice"`. Capture `Id` (→ `<connectionId>`), `FolderKey` (→ `<folderKey>`), and `Name` (→ `<IS connection Name>`).

---

## Step 2 — Resolve the Entity Name

```bash
uip df entities list --native-only --output json
```

Use the exact CamelCase `Name` (e.g. `BankDetails`). For Create/Update, also run `uip df entities get <entity-id> --output json` for field names — skip system fields (`Id`, `CreatedBy`, `CreateTime`, `UpdatedBy`, `UpdateTime`, `RecordOwner`).

---

## Step 3 — Set Up the Flow File

Author the standard top-level `bindings[]` pair (`ConnectionId` + `FolderKey`) per [parent impl.md § Authoring top-level `bindings[]`](../impl.md#authoring-top-level-bindings). Data Fabric specifics:

- Connection binding `name` = the IS connection display name (not the `<CONNECTOR_KEY> connection` placeholder), since `node configure` is run with this value pre-resolved.
- Both bindings share the same `resourceKey` = `<connectionId>`.

Add one `definitions[]` entry per activity type used — copy the complete entry from the Definitions Templates section below. The `form` block is required ([parent impl.md § Critical: Connector Definition Must Include `form`](../impl.md#critical-connector-definition-must-include-form)).

---

## Step 4 — Create `bindings_v2.json`

> **Data Fabric exception to [parent impl.md § Bindings](../impl.md#bindings--top-level-flow-bindings).** The parent guide says `bindings_v2.json` is regenerated from top-level `bindings[]` and must never be hand-edited. For Data Fabric Maestro Flow projects this regeneration does not happen — Studio Web returns 500 on designer load if `bindings_v2.json` is missing or shaped differently from the block below. Author it by hand using the exact format here.

Create this file manually alongside the `.flow` file.

```json
{
  "version": "2.0",
  "resources": [{
    "resource": "Connection",
    "key": "<connectionId>",
    "id": "Connection<connectionId>",
    "value": { "ConnectionId": { "defaultValue": "<connectionId>", "isExpression": false, "displayName": "<IS connection Name>" } },
    "metadata": { "ActivityName": "<first connector node label>", "BindingsVersion": "2.2", "DisplayLabel": "<IS connection Name>", "UseConnectionService": "true", "Connector": "uipath-uipath-dataservice" }
  }]
}
```

---

## Step 5 — Create the Connection Resource File

Create `resources/solution_folder/connection/uipath-uipath-dataservice/<IS connection Name>.json` manually in the solution directory.

```json
{
  "docVersion": "1.0.0",
  "resource": {
    "name": "<IS connection Name>", "kind": "connection", "type": "uipath-uipath-dataservice",
    "apiVersion": "integrationservice.uipath.com/v1", "isOverridable": true,
    "dependencies": [], "runtimeDependencies": [],
    "folders": [{ "fullyQualifiedName": "solution_folder" }],
    "spec": { "connectorName": "Data Fabric", "name": "<IS connection Name>", "authenticationType": "AuthenticateAfterDeployment", "connectorVersion": "<IS Connector version>", "connectorKey": "uipath-uipath-dataservice", "pollingInterval": 5 },
    "locks": [], "key": "<connectionId>", "files": []
  }
}
```

---

## Step 6 — Write Connector Nodes

Write nodes directly into the `.flow` JSON using the templates below — `uip maestro flow node add` does not support `uipath.connector.*` types.

For each node, set `connectionId`, `connectionResourceId` (same value), `connectionFolderKey`, `pathParameters.entityName`, and `bodyParameters`/`queryParameters` as needed. Copy the `configuration` string verbatim from the templates, replacing only `<EntityName>`.

For wiring upstream node outputs (`=js:$vars.<sourceNodeId>.output.<field>`), see [parent impl.md § Step 5b](../impl.md#step-5b--wire-outputs-from-previous-nodes). Data Fabric specifics:

- `expansionLevel` is always string `"3"`, never a number.
- `queryExpression` is a raw CEQL string — no `=js:` prefix (e.g., `"queryExpression": "FieldName = 'value' AND OtherField > 10"`).

---

## Step 7 — Run `node configure` and Restore Configuration

Run `uip maestro flow node configure` on each connector node per [parent impl.md § Step 6](../impl.md#step-6--configure-the-node). Use `method` and `endpoint` from the Activity Reference table below; pass `pathParameters.entityName` and any activity-specific `queryParameters`/`bodyParameters` in `--detail`.

> **Data Fabric quirk — restore `configuration` after configure.** `node configure` resets `customFieldsRequestDetails` to `null` in the `configuration` string. Restore the correct `configuration` string on **every node except Delete** using the exact strings from the Configuration Strings section below. Delete is the only activity where `customFieldsRequestDetails: null` is correct.

---

## `inputs.detail` — Data Fabric Specifics

For the full set of `inputs.detail` fields populated by `node configure`, see [parent impl.md § How Connector Nodes Differ from OOTB](../impl.md#how-connector-nodes-differ-from-ootb). Data Fabric–specific values:

| Field | Value |
|---|---|
| `connector` | Always `"uipath-uipath-dataservice"` |
| `connectionResourceId` | Same UUID as `connectionId` — both required (Data Fabric requires both) |
| `pathParameters` | `{ "entityName": "<CamelCaseEntityName>" }` — every Data Fabric activity uses this |
| `bodyParameters` | Required for Create/Update; omit for Query/Delete/GetById |
| `method` / `endpoint` / `uiPathActivityTypeId` / `telemetryData` | Per-activity values — see Activity Reference table below |
| `configuration` | `=jsonString:{...}` — see Configuration Strings section below |

### Activity Reference

| Activity | Method | Endpoint | `uiPathActivityTypeId` | `operationType` | `objectName` |
|---|---|---|---|---|---|
| Query Entity Records | `POST` | `/v2/{entityName}/qer` | `703065b9-a310-33b8-9d4d-12df0a6f520b` | `list` | `QueryEntityRecordsCurated` |
| Create Entity Record | `POST` | `/v2/{entityName}/CreateEntityRecord` | `dfd2bc7a-ca4b-3316-8a1f-57c9e106dfbf` | `create` | `CreateEntityRecordCurated` |
| Update Entity Record | `PUT` | `/v2/{entityName}/UpdateEntityRecord` | `718fdc36-73a8-3607-8604-ddef95bb9967` | `replace` | `UpdateEntityRecordV2` |
| Delete Entity Record | `POST` | `/v2/{entityName}/DeleteEntityRecord` | `9c8029ee-ff5f-3b82-92cc-34cee15e9f1d` | `delete` | `DeleteEntityRecordCurated` |
| Get Entity Record by ID | `GET` | `/v2/{entityName}/GetEntityRecord` | `81291b95-ff0c-3822-bdaa-3065391c1997` | `retrieve` | `GetEntityRecordByIdCurated` |

---

## Configuration Strings

`<activityVersion>` is the `version` field inside the definition's `connectorDetail.configuration` JSON string — currently `"1.0.0"` for all Data Fabric activities. `connectorVersion` is set by `node configure` at run time.

**Query Entity Records:**
```
=jsonString:{"essentialConfiguration":{"connectorVersion":"<connectorVersion>","customFieldsRequestDetails":{"objectActionName":"GenerateSchema","parameterValues":[["entityName","<EntityName>"]]},"instanceParameters":{"connectorKey":"uipath-uipath-dataservice","objectName":"QueryEntityRecordsCurated","httpMethod":"POST","activityType":"Curated","version":"<activityVersion>","supportsStreaming":false,"subType":"standard"},"objectName":"QueryEntityRecordsCurated","operation":"list","packageVersion":"<activityVersion>","httpMethod":"POST","path":"/v2/{entityName}/qer","unifiedTypesCompatible":true}}
```

**Create Entity Record:**
```
=jsonString:{"essentialConfiguration":{"connectorVersion":"<connectorVersion>","customFieldsRequestDetails":{"objectActionName":"GenerateSchema","parameterValues":[["entityName","<EntityName>"]]},"instanceParameters":{"connectorKey":"uipath-uipath-dataservice","objectName":"CreateEntityRecordCurated","httpMethod":"POST","activityType":"Curated","version":"<activityVersion>","supportsStreaming":false,"subType":"standard"},"objectName":"CreateEntityRecordCurated","operation":"create","packageVersion":"<activityVersion>","httpMethod":"POST","path":"/v2/{entityName}/CreateEntityRecord","unifiedTypesCompatible":true,"savedJitInputFieldId":"in_CreateEntityRecordCurated"}}
```

**Update Entity Record:**
```
=jsonString:{"essentialConfiguration":{"connectorVersion":"<connectorVersion>","customFieldsRequestDetails":{"objectActionName":"GenerateSchema","parameterValues":[["entityName","<EntityName>"]]},"instanceParameters":{"connectorKey":"uipath-uipath-dataservice","objectName":"UpdateEntityRecordV2","httpMethod":"PUT","activityType":"Curated","version":"<activityVersion>","supportsStreaming":false,"subType":"standard"},"objectName":"UpdateEntityRecordV2","operation":"replace","packageVersion":"<activityVersion>","httpMethod":"PUT","path":"/v2/{entityName}/UpdateEntityRecord","unifiedTypesCompatible":true,"savedJitInputFieldId":"in_UpdateEntityRecordV2"}}
```

**Get Entity Record by ID:**
```
=jsonString:{"essentialConfiguration":{"connectorVersion":"<connectorVersion>","customFieldsRequestDetails":{"objectActionName":"GenerateSchema","parameterValues":[["entityName","<EntityName>"]]},"instanceParameters":{"connectorKey":"uipath-uipath-dataservice","objectName":"GetEntityRecordByIdCurated","httpMethod":"GET","activityType":"Curated","version":"<activityVersion>","supportsStreaming":false,"subType":"standard"},"objectName":"GetEntityRecordByIdCurated","operation":"retrieve","packageVersion":"<activityVersion>","httpMethod":"GET","path":"/v2/{entityName}/GetEntityRecord","unifiedTypesCompatible":true,"savedJitInputFieldId":"in_GetEntityRecordByIdCurated"}}
```

**Delete Entity Record:**
```
=jsonString:{"essentialConfiguration":{"connectorVersion":"<connectorVersion>","customFieldsRequestDetails":null,"instanceParameters":{"connectorKey":"uipath-uipath-dataservice","objectName":"DeleteEntityRecordCurated","httpMethod":"POST","activityType":"Curated","version":"<activityVersion>","supportsStreaming":false,"subType":"standard"},"objectName":"DeleteEntityRecordCurated","operation":"delete","packageVersion":"<activityVersion>","httpMethod":"POST","path":"/v2/{entityName}/DeleteEntityRecord","unifiedTypesCompatible":true}}
```

> Delete is the only activity where `customFieldsRequestDetails` is `null` — do not restore it after `node configure`.

---

## Definitions Templates

Add one entry per activity type used to `definitions[]` in the `.flow` file (sibling of `nodes`/`edges`/`bindings`). Replace `<cloud_host>/<org_id>` in `display.icon` with your tenant URL prefix. The icon hash is stable across tenants.

> The `assemblyQualifiedName` version (`1.26.0.0`) reflects the IS connector package at time of authoring. If stale, fetch the current value: `uip maestro flow registry get uipath.connector.uipath-uipath-dataservice.query-entity-records --connection-id <connectionId> --output json` and read `Data.Node.form.sections[0].fields[0].componentProps.connectorDetail.assemblyQualifiedName`.

> `definitions[]` must be present before running `node configure` — without it, configure fails with `No instanceParameters found in definition`.

### Query Entity Records

```json
{
  "nodeType": "uipath.connector.uipath-uipath-dataservice.query-entity-records",
  "version": "1.0.0",
  "description": "(Data Fabric) Retrieves a list of records for the selected Entity from Data Fabric, according to specified filters.",
  "category": "connector.196550",
  "tags": ["connector", "activity"],
  "sortOrder": 515,
  "display": {
    "label": "Query Entity Records",
    "description": "(Data Fabric) Retrieves a list of records for the selected Entity from Data Fabric, according to specified filters.",
    "icon": "https://<cloud_host>/<org_id>/studio_/typecache/icons/98381fa079bbcf73264f551006d6ef7580fb53992f3d9f94361eb5d9e06040cb.svg",
    "iconBackground": "linear-gradient(225deg, #FAFAFB 0%, #ECEDEF 100%)",
    "iconBackgroundDark": "linear-gradient(225deg, #526069 0%, rgba(50, 60, 66, 0.6) 100%)"
  },
  "handleConfiguration": [
    { "position": "left",  "handles": [{ "id": "input",  "type": "target", "handleType": "input",  "label": "" }] },
    { "position": "right", "handles": [{ "id": "output", "type": "source", "handleType": "output", "label": "" }] }
  ],
  "inputDefaults": {},
  "inputDefinition": {},
  "outputDefinition": {
    "output": { "type": "object", "description": "The return value of the connector.", "source": "=result.response", "var": "output" },
    "error":  { "type": "object", "description": "Error information if the node fails",   "source": "=Error",           "var": "error" }
  },
  "debug": { "runtime": "bpmnEngine" },
  "model": {
    "type": "bpmn:SendTask",
    "serviceType": "Intsvc.ActivityExecution",
    "debug": { "runtime": "bpmnEngine" },
    "context": [
      { "name": "connectorKey", "type": "string", "value": "uipath-uipath-dataservice" },
      { "name": "operation",    "type": "string" },
      { "name": "objectName",   "type": "string", "value": "QueryEntityRecordsCurated" },
      { "name": "method",       "type": "string", "value": "POST" },
      { "name": "connection",   "type": "string", "value": "<bindings.<IS connection Name>>" },
      { "name": "folderKey",    "type": "string", "value": "<bindings.FolderKey>" },
      { "name": "activityConfigurationVersion", "type": "string", "value": "v1" },
      { "name": "metadata", "type": "json", "body": { "telemetryData": { "connectorKey": "uipath-uipath-dataservice", "connectorName": "Query Entity Records" }, "inputMetadata": {}, "errorState": { "hasError": false } } }
    ]
  },
  "form": {
    "id": "connector-properties", "title": "Connector configuration",
    "sections": [{ "id": "connector", "title": "Connector", "collapsible": true, "defaultExpanded": true, "fields": [{
      "label": "", "name": "inputs.detail", "type": "custom", "component": "dap-config",
      "componentProps": { "connectorDetail": {
        "isAppActivity": false, "packageId": 196550,
        "svgIconUrl": "icons/98381fa079bbcf73264f551006d6ef7580fb53992f3d9f94361eb5d9e06040cb.svg",
        "displayName": "Query Entity Records",
        "assemblyQualifiedName": "UiPath.IntegrationService.Activities.Runtime.Activities.ConnectorActivity, UiPath.IntegrationService.Activities.Runtime, Version=1.26.0.0, Culture=neutral, PublicKeyToken=null",
        "description": "(Data Fabric) Retrieves a list of records for the selected Entity from Data Fabric, according to specified filters.",
        "activityColor": "#E56D5C",
        "configuration": "{\"connectorKey\":\"uipath-uipath-dataservice\",\"objectName\":\"QueryEntityRecordsCurated\",\"httpMethod\":\"POST\",\"activityType\":\"Curated\",\"version\":\"1.0.0\",\"supportsStreaming\":false,\"subType\":\"standard\"}",
        "uiPathActivityTypeId": "703065b9-a310-33b8-9d4d-12df0a6f520b",
        "isExperimental": true,
        "helpUrlTemplate": "https://docs.uipath.com/{0}/activities/other/latest/integration-service/uipath-uipath-dataservice-Query-Entity-Records",
        "isEnabled": true, "targetPlatform": "CrossPlatform", "isAdvanced": false, "isRestricted": false, "tags": []
      }}
    }]}]
  }
}
```

### Create Entity Record

```json
{
  "nodeType": "uipath.connector.uipath-uipath-dataservice.create-entity-record",
  "version": "1.0.0",
  "description": "(Data Fabric) Creates a new record for the selected Entity in Data Fabric",
  "category": "connector.196550",
  "tags": ["connector", "activity"],
  "sortOrder": 515,
  "display": {
    "label": "Create Entity Record",
    "description": "(Data Fabric) Creates a new record for the selected Entity in Data Fabric",
    "icon": "https://<cloud_host>/<org_id>/studio_/typecache/icons/98381fa079bbcf73264f551006d6ef7580fb53992f3d9f94361eb5d9e06040cb.svg",
    "iconBackground": "linear-gradient(225deg, #FAFAFB 0%, #ECEDEF 100%)",
    "iconBackgroundDark": "linear-gradient(225deg, #526069 0%, rgba(50, 60, 66, 0.6) 100%)"
  },
  "handleConfiguration": [
    { "position": "left",  "handles": [{ "id": "input",  "type": "target", "handleType": "input",  "label": "" }] },
    { "position": "right", "handles": [{ "id": "output", "type": "source", "handleType": "output", "label": "" }] }
  ],
  "inputDefaults": {},
  "inputDefinition": {},
  "outputDefinition": {
    "output": { "type": "object", "description": "The return value of the connector.", "source": "=result.response", "var": "output" },
    "error":  { "type": "object", "description": "Error information if the node fails",   "source": "=Error",           "var": "error" }
  },
  "debug": { "runtime": "bpmnEngine" },
  "model": {
    "type": "bpmn:SendTask",
    "serviceType": "Intsvc.ActivityExecution",
    "debug": { "runtime": "bpmnEngine" },
    "context": [
      { "name": "connectorKey", "type": "string", "value": "uipath-uipath-dataservice" },
      { "name": "operation",    "type": "string" },
      { "name": "objectName",   "type": "string", "value": "CreateEntityRecordCurated" },
      { "name": "method",       "type": "string", "value": "POST" },
      { "name": "connection",   "type": "string", "value": "<bindings.<IS connection Name>>" },
      { "name": "folderKey",    "type": "string", "value": "<bindings.FolderKey>" },
      { "name": "activityConfigurationVersion", "type": "string", "value": "v1" },
      { "name": "metadata", "type": "json", "body": { "telemetryData": { "connectorKey": "uipath-uipath-dataservice", "connectorName": "Create Entity Record" }, "inputMetadata": {}, "errorState": { "hasError": false } } }
    ]
  },
  "form": {
    "id": "connector-properties", "title": "Connector configuration",
    "sections": [{ "id": "connector", "title": "Connector", "collapsible": true, "defaultExpanded": true, "fields": [{
      "label": "", "name": "inputs.detail", "type": "custom", "component": "dap-config",
      "componentProps": { "connectorDetail": {
        "isAppActivity": false, "packageId": 196550,
        "svgIconUrl": "icons/98381fa079bbcf73264f551006d6ef7580fb53992f3d9f94361eb5d9e06040cb.svg",
        "displayName": "Create Entity Record",
        "assemblyQualifiedName": "UiPath.IntegrationService.Activities.Runtime.Activities.ConnectorActivity, UiPath.IntegrationService.Activities.Runtime, Version=1.26.0.0, Culture=neutral, PublicKeyToken=null",
        "description": "(Data Fabric) Creates a new record for the selected Entity in Data Fabric",
        "activityColor": "#E56D5C",
        "configuration": "{\"connectorKey\":\"uipath-uipath-dataservice\",\"objectName\":\"CreateEntityRecordCurated\",\"httpMethod\":\"POST\",\"activityType\":\"Curated\",\"version\":\"1.0.0\",\"supportsStreaming\":false,\"subType\":\"standard\"}",
        "uiPathActivityTypeId": "dfd2bc7a-ca4b-3316-8a1f-57c9e106dfbf",
        "isExperimental": true,
        "helpUrlTemplate": "https://docs.uipath.com/{0}/activities/other/latest/integration-service/uipath-uipath-dataservice-Create-Entity-Record",
        "isEnabled": true, "targetPlatform": "CrossPlatform", "isAdvanced": false, "isRestricted": false, "tags": []
      }}
    }]}]
  }
}
```

### Update Entity Record

```json
{
  "nodeType": "uipath.connector.uipath-uipath-dataservice.update-entity-record",
  "version": "1.0.0",
  "description": "(Data Fabric) Updates an existing record in a Data Fabric entity",
  "category": "connector.196550",
  "tags": ["connector", "activity"],
  "sortOrder": 515,
  "display": {
    "label": "Update Entity Record",
    "description": "(Data Fabric) Updates an existing record in a Data Fabric entity",
    "icon": "https://<cloud_host>/<org_id>/studio_/typecache/icons/98381fa079bbcf73264f551006d6ef7580fb53992f3d9f94361eb5d9e06040cb.svg",
    "iconBackground": "linear-gradient(225deg, #FAFAFB 0%, #ECEDEF 100%)",
    "iconBackgroundDark": "linear-gradient(225deg, #526069 0%, rgba(50, 60, 66, 0.6) 100%)"
  },
  "handleConfiguration": [
    { "position": "left",  "handles": [{ "id": "input",  "type": "target", "handleType": "input",  "label": "" }] },
    { "position": "right", "handles": [{ "id": "output", "type": "source", "handleType": "output", "label": "" }] }
  ],
  "inputDefaults": {},
  "inputDefinition": {},
  "outputDefinition": {
    "output": { "type": "object", "description": "The return value of the connector.", "source": "=result.response", "var": "output" },
    "error":  { "type": "object", "description": "Error information if the node fails",   "source": "=Error",           "var": "error" }
  },
  "debug": { "runtime": "bpmnEngine" },
  "model": {
    "type": "bpmn:SendTask",
    "serviceType": "Intsvc.ActivityExecution",
    "debug": { "runtime": "bpmnEngine" },
    "context": [
      { "name": "connectorKey", "type": "string", "value": "uipath-uipath-dataservice" },
      { "name": "operation",    "type": "string" },
      { "name": "objectName",   "type": "string", "value": "UpdateEntityRecordV2" },
      { "name": "method",       "type": "string", "value": "PUT" },
      { "name": "connection",   "type": "string", "value": "<bindings.<IS connection Name>>" },
      { "name": "folderKey",    "type": "string", "value": "<bindings.FolderKey>" },
      { "name": "activityConfigurationVersion", "type": "string", "value": "v1" },
      { "name": "metadata", "type": "json", "body": { "telemetryData": { "connectorKey": "uipath-uipath-dataservice", "connectorName": "Update Entity Record" }, "inputMetadata": {}, "errorState": { "hasError": false } } }
    ]
  },
  "form": {
    "id": "connector-properties", "title": "Connector configuration",
    "sections": [{ "id": "connector", "title": "Connector", "collapsible": true, "defaultExpanded": true, "fields": [{
      "label": "", "name": "inputs.detail", "type": "custom", "component": "dap-config",
      "componentProps": { "connectorDetail": {
        "isAppActivity": false, "packageId": 196550,
        "svgIconUrl": "icons/98381fa079bbcf73264f551006d6ef7580fb53992f3d9f94361eb5d9e06040cb.svg",
        "displayName": "Update Entity Record",
        "assemblyQualifiedName": "UiPath.IntegrationService.Activities.Runtime.Activities.ConnectorActivity, UiPath.IntegrationService.Activities.Runtime, Version=1.26.0.0, Culture=neutral, PublicKeyToken=null",
        "description": "(Data Fabric) Updates an existing record in a Data Fabric entity",
        "activityColor": "#E56D5C",
        "configuration": "{\"connectorKey\":\"uipath-uipath-dataservice\",\"objectName\":\"UpdateEntityRecordV2\",\"httpMethod\":\"PUT\",\"activityType\":\"Curated\",\"version\":\"1.0.0\",\"supportsStreaming\":false,\"subType\":\"standard\"}",
        "uiPathActivityTypeId": "718fdc36-73a8-3607-8604-ddef95bb9967",
        "isExperimental": true,
        "helpUrlTemplate": "https://docs.uipath.com/{0}/activities/other/latest/integration-service/uipath-uipath-dataservice-Update-Entity-Record",
        "isEnabled": true, "targetPlatform": "CrossPlatform", "isAdvanced": false, "isRestricted": false, "tags": []
      }}
    }]}]
  }
}
```

### Delete Entity Record

```json
{
  "nodeType": "uipath.connector.uipath-uipath-dataservice.delete-entity-record",
  "version": "1.0.0",
  "description": "(Data Fabric) Deletes an existing record for the selected entity from Data Fabric",
  "category": "connector.196550",
  "tags": ["connector", "activity"],
  "sortOrder": 515,
  "display": {
    "label": "Delete Entity Record",
    "description": "(Data Fabric) Deletes an existing record for the selected entity from Data Fabric",
    "icon": "https://<cloud_host>/<org_id>/studio_/typecache/icons/98381fa079bbcf73264f551006d6ef7580fb53992f3d9f94361eb5d9e06040cb.svg",
    "iconBackground": "linear-gradient(225deg, #FAFAFB 0%, #ECEDEF 100%)",
    "iconBackgroundDark": "linear-gradient(225deg, #526069 0%, rgba(50, 60, 66, 0.6) 100%)"
  },
  "handleConfiguration": [
    { "position": "left",  "handles": [{ "id": "input",  "type": "target", "handleType": "input",  "label": "" }] },
    { "position": "right", "handles": [{ "id": "output", "type": "source", "handleType": "output", "label": "" }] }
  ],
  "inputDefaults": {},
  "inputDefinition": {},
  "outputDefinition": {
    "output": { "type": "object", "description": "The return value of the connector.", "source": "=result.response", "var": "output" },
    "error":  { "type": "object", "description": "Error information if the node fails",   "source": "=Error",           "var": "error" }
  },
  "debug": { "runtime": "bpmnEngine" },
  "model": {
    "type": "bpmn:SendTask",
    "serviceType": "Intsvc.ActivityExecution",
    "debug": { "runtime": "bpmnEngine" },
    "context": [
      { "name": "connectorKey", "type": "string", "value": "uipath-uipath-dataservice" },
      { "name": "operation",    "type": "string" },
      { "name": "objectName",   "type": "string", "value": "DeleteEntityRecordCurated" },
      { "name": "method",       "type": "string", "value": "POST" },
      { "name": "connection",   "type": "string", "value": "<bindings.<IS connection Name>>" },
      { "name": "folderKey",    "type": "string", "value": "<bindings.FolderKey>" },
      { "name": "activityConfigurationVersion", "type": "string", "value": "v1" },
      { "name": "metadata", "type": "json", "body": { "telemetryData": { "connectorKey": "uipath-uipath-dataservice", "connectorName": "Delete Entity Record" }, "inputMetadata": {}, "errorState": { "hasError": false } } }
    ]
  },
  "form": {
    "id": "connector-properties", "title": "Connector configuration",
    "sections": [{ "id": "connector", "title": "Connector", "collapsible": true, "defaultExpanded": true, "fields": [{
      "label": "", "name": "inputs.detail", "type": "custom", "component": "dap-config",
      "componentProps": { "connectorDetail": {
        "isAppActivity": false, "packageId": 196550,
        "svgIconUrl": "icons/98381fa079bbcf73264f551006d6ef7580fb53992f3d9f94361eb5d9e06040cb.svg",
        "displayName": "Delete Entity Record",
        "assemblyQualifiedName": "UiPath.IntegrationService.Activities.Runtime.Activities.ConnectorActivity, UiPath.IntegrationService.Activities.Runtime, Version=1.26.0.0, Culture=neutral, PublicKeyToken=null",
        "description": "(Data Fabric) Deletes an existing record for the selected entity from Data Fabric",
        "activityColor": "#E56D5C",
        "configuration": "{\"connectorKey\":\"uipath-uipath-dataservice\",\"objectName\":\"DeleteEntityRecordCurated\",\"httpMethod\":\"POST\",\"activityType\":\"Curated\",\"version\":\"1.0.0\",\"supportsStreaming\":false,\"subType\":\"standard\"}",
        "uiPathActivityTypeId": "9c8029ee-ff5f-3b82-92cc-34cee15e9f1d",
        "isExperimental": true,
        "helpUrlTemplate": "https://docs.uipath.com/{0}/activities/other/latest/integration-service/uipath-uipath-dataservice-Delete-Entity-Record",
        "isEnabled": true, "targetPlatform": "CrossPlatform", "isAdvanced": false, "isRestricted": false, "tags": []
      }}
    }]}]
  }
}
```

### Get Entity Record by ID

```json
{
  "nodeType": "uipath.connector.uipath-uipath-dataservice.get-entity-record-by-id",
  "version": "1.0.0",
  "description": "(Data Fabric) Reads an existing record for the selected entity from Data Fabric",
  "category": "connector.196550",
  "tags": ["connector", "activity"],
  "sortOrder": 515,
  "display": {
    "label": "Get Entity Record by ID",
    "description": "(Data Fabric) Reads an existing record for the selected entity from Data Fabric",
    "icon": "https://<cloud_host>/<org_id>/studio_/typecache/icons/98381fa079bbcf73264f551006d6ef7580fb53992f3d9f94361eb5d9e06040cb.svg",
    "iconBackground": "linear-gradient(225deg, #FAFAFB 0%, #ECEDEF 100%)",
    "iconBackgroundDark": "linear-gradient(225deg, #526069 0%, rgba(50, 60, 66, 0.6) 100%)"
  },
  "handleConfiguration": [
    { "position": "left",  "handles": [{ "id": "input",  "type": "target", "handleType": "input",  "label": "" }] },
    { "position": "right", "handles": [{ "id": "output", "type": "source", "handleType": "output", "label": "" }] }
  ],
  "inputDefaults": {},
  "inputDefinition": {},
  "outputDefinition": {
    "output": { "type": "object", "description": "The return value of the connector.", "source": "=result.response", "var": "output" },
    "error":  { "type": "object", "description": "Error information if the node fails",   "source": "=Error",           "var": "error" }
  },
  "debug": { "runtime": "bpmnEngine" },
  "model": {
    "type": "bpmn:SendTask",
    "serviceType": "Intsvc.ActivityExecution",
    "debug": { "runtime": "bpmnEngine" },
    "context": [
      { "name": "connectorKey", "type": "string", "value": "uipath-uipath-dataservice" },
      { "name": "operation",    "type": "string" },
      { "name": "objectName",   "type": "string", "value": "GetEntityRecordByIdCurated" },
      { "name": "method",       "type": "string", "value": "GET" },
      { "name": "connection",   "type": "string", "value": "<bindings.<IS connection Name>>" },
      { "name": "folderKey",    "type": "string", "value": "<bindings.FolderKey>" },
      { "name": "activityConfigurationVersion", "type": "string", "value": "v1" },
      { "name": "metadata", "type": "json", "body": { "telemetryData": { "connectorKey": "uipath-uipath-dataservice", "connectorName": "Get Entity Record by ID" }, "inputMetadata": {}, "errorState": { "hasError": false } } }
    ]
  },
  "form": {
    "id": "connector-properties", "title": "Connector configuration",
    "sections": [{ "id": "connector", "title": "Connector", "collapsible": true, "defaultExpanded": true, "fields": [{
      "label": "", "name": "inputs.detail", "type": "custom", "component": "dap-config",
      "componentProps": { "connectorDetail": {
        "isAppActivity": false, "packageId": 196550,
        "svgIconUrl": "icons/98381fa079bbcf73264f551006d6ef7580fb53992f3d9f94361eb5d9e06040cb.svg",
        "displayName": "Get Entity Record by ID",
        "assemblyQualifiedName": "UiPath.IntegrationService.Activities.Runtime.Activities.ConnectorActivity, UiPath.IntegrationService.Activities.Runtime, Version=1.26.0.0, Culture=neutral, PublicKeyToken=null",
        "description": "(Data Fabric) Reads an existing record for the selected entity from Data Fabric",
        "activityColor": "#E56D5C",
        "configuration": "{\"connectorKey\":\"uipath-uipath-dataservice\",\"objectName\":\"GetEntityRecordByIdCurated\",\"httpMethod\":\"GET\",\"activityType\":\"Curated\",\"version\":\"1.0.0\",\"supportsStreaming\":false,\"subType\":\"standard\"}",
        "uiPathActivityTypeId": "81291b95-ff0c-3822-bdaa-3065391c1997",
        "isExperimental": true,
        "helpUrlTemplate": "https://docs.uipath.com/{0}/activities/other/latest/integration-service/uipath-uipath-dataservice-Get-Entity-Record-by-ID",
        "isEnabled": true, "targetPlatform": "CrossPlatform", "isAdvanced": false, "isRestricted": false, "tags": []
      }}
    }]}]
  }
}
```

---

## Node JSON Templates

Substitute `<EntityName>`, `<connectionId>`, `<folderKey>`, and `<IS connection Name>` with actual values. Use the same tenant URL prefix for `display.icon` as in the Definitions Templates above.

### Query Entity Records

```json
{
  "id": "queryEntityRecords1",
  "type": "uipath.connector.uipath-uipath-dataservice.query-entity-records",
  "typeVersion": "1.0.0",
  "display": { "label": "Query <EntityName>", "icon": "https://<cloud_host>/<org_id>/studio_/typecache/icons/98381fa079bbcf73264f551006d6ef7580fb53992f3d9f94361eb5d9e06040cb.svg", "subLabel": "" },
  "inputs": {
    "detail": {
      "connector": "uipath-uipath-dataservice",
      "connectionId": "<connectionId>",
      "connectionResourceId": "<connectionId>",
      "connectionFolderKey": "<folderKey>",
      "method": "POST",
      "endpoint": "/v2/{entityName}/qer",
      "pathParameters": { "entityName": "<EntityName>" },
      "queryParameters": { "start": 0, "limit": 100, "expansionLevel": "3", "isAscending": false },
      "uiPathActivityTypeId": "703065b9-a310-33b8-9d4d-12df0a6f520b",
      "errorState": { "issues": [] },
      "telemetryData": { "connectorKey": "uipath-uipath-dataservice", "connectorName": "Data Fabric", "operationType": "list", "objectName": "QueryEntityRecordsCurated", "objectDisplayName": "Query Entity Records", "primaryKeyName": "" },
      "configuration": "=jsonString:{\"essentialConfiguration\":{\"connectorVersion\":\"<connectorVersion>\",\"customFieldsRequestDetails\":{\"objectActionName\":\"GenerateSchema\",\"parameterValues\":[[\"entityName\",\"<EntityName>\"]]},\"instanceParameters\":{\"connectorKey\":\"uipath-uipath-dataservice\",\"objectName\":\"QueryEntityRecordsCurated\",\"httpMethod\":\"POST\",\"activityType\":\"Curated\",\"version\":\"<activityVersion>\",\"supportsStreaming\":false,\"subType\":\"standard\"},\"objectName\":\"QueryEntityRecordsCurated\",\"operation\":\"list\",\"packageVersion\":\"<activityVersion>\",\"httpMethod\":\"POST\",\"path\":\"/v2/{entityName}/qer\",\"unifiedTypesCompatible\":true}}"
    }
  },
  "outputs": {
    "output": { "type": "object", "description": "The return value of the connector.", "source": "=result.response", "var": "output" },
    "error":  { "type": "object", "description": "Error information if the node fails", "source": "=Error", "var": "error" }
  }
}
```

**Pagination defaults** — `start`, `limit`, and `isAscending` are adjustable. Use `queryExpression` to filter: `"queryExpression": "<FilterExpression>"` (e.g. `"FieldName = 'value' AND OtherField > 10"`).

**Output:** `<nodeId>.output` — array of records. Access fields as `=js:$vars.<nodeId>.output[0].<FieldName>`.

---

### Create Entity Record

```json
{
  "id": "createEntityRecord1",
  "type": "uipath.connector.uipath-uipath-dataservice.create-entity-record",
  "typeVersion": "1.0.0",
  "display": { "label": "Create <EntityName>", "icon": "https://<cloud_host>/<org_id>/studio_/typecache/icons/98381fa079bbcf73264f551006d6ef7580fb53992f3d9f94361eb5d9e06040cb.svg", "subLabel": "" },
  "inputs": {
    "detail": {
      "connector": "uipath-uipath-dataservice",
      "connectionId": "<connectionId>",
      "connectionResourceId": "<connectionId>",
      "connectionFolderKey": "<folderKey>",
      "method": "POST",
      "endpoint": "/v2/{entityName}/CreateEntityRecord",
      "pathParameters": { "entityName": "<EntityName>" },
      "queryParameters": { "expansionLevel": "3" },
      "bodyParameters": { "FieldName1": "<value1>", "FieldName2": "<value2>" },
      "uiPathActivityTypeId": "dfd2bc7a-ca4b-3316-8a1f-57c9e106dfbf",
      "errorState": { "issues": [] },
      "telemetryData": { "connectorKey": "uipath-uipath-dataservice", "connectorName": "Data Fabric", "operationType": "create", "objectName": "CreateEntityRecordCurated", "objectDisplayName": "Create Entity Record", "primaryKeyName": "" },
      "configuration": "=jsonString:{\"essentialConfiguration\":{\"connectorVersion\":\"<connectorVersion>\",\"customFieldsRequestDetails\":{\"objectActionName\":\"GenerateSchema\",\"parameterValues\":[[\"entityName\",\"<EntityName>\"]]},\"instanceParameters\":{\"connectorKey\":\"uipath-uipath-dataservice\",\"objectName\":\"CreateEntityRecordCurated\",\"httpMethod\":\"POST\",\"activityType\":\"Curated\",\"version\":\"<activityVersion>\",\"supportsStreaming\":false,\"subType\":\"standard\"},\"objectName\":\"CreateEntityRecordCurated\",\"operation\":\"create\",\"packageVersion\":\"<activityVersion>\",\"httpMethod\":\"POST\",\"path\":\"/v2/{entityName}/CreateEntityRecord\",\"unifiedTypesCompatible\":true,\"savedJitInputFieldId\":\"in_CreateEntityRecordCurated\"}}"
    }
  },
  "outputs": {
    "output": { "type": "object", "description": "The return value of the connector.", "source": "=result.response", "var": "output" },
    "error":  { "type": "object", "description": "Error information if the node fails", "source": "=Error", "var": "error" }
  }
}
```

**Output:** `<nodeId>.output` — the newly created record object (includes `Id`).

---

### Update Entity Record

```json
{
  "id": "updateEntityRecord1",
  "type": "uipath.connector.uipath-uipath-dataservice.update-entity-record",
  "typeVersion": "1.0.0",
  "display": { "label": "Update <EntityName>", "icon": "https://<cloud_host>/<org_id>/studio_/typecache/icons/98381fa079bbcf73264f551006d6ef7580fb53992f3d9f94361eb5d9e06040cb.svg", "subLabel": "" },
  "inputs": {
    "detail": {
      "connector": "uipath-uipath-dataservice",
      "connectionId": "<connectionId>",
      "connectionResourceId": "<connectionId>",
      "connectionFolderKey": "<folderKey>",
      "method": "PUT",
      "endpoint": "/v2/{entityName}/UpdateEntityRecord",
      "pathParameters": { "entityName": "<EntityName>" },
      "queryParameters": { "recordId": "=js:$vars.<sourceNodeId>.output.Id", "expansionLevel": "3" },
      "bodyParameters": { "FieldToUpdate": "<newValue>" },
      "uiPathActivityTypeId": "718fdc36-73a8-3607-8604-ddef95bb9967",
      "errorState": { "issues": [] },
      "telemetryData": { "connectorKey": "uipath-uipath-dataservice", "connectorName": "Data Fabric", "operationType": "replace", "objectName": "UpdateEntityRecordV2", "objectDisplayName": "Update Entity Record", "primaryKeyName": "" },
      "configuration": "=jsonString:{\"essentialConfiguration\":{\"connectorVersion\":\"<connectorVersion>\",\"customFieldsRequestDetails\":{\"objectActionName\":\"GenerateSchema\",\"parameterValues\":[[\"entityName\",\"<EntityName>\"]]},\"instanceParameters\":{\"connectorKey\":\"uipath-uipath-dataservice\",\"objectName\":\"UpdateEntityRecordV2\",\"httpMethod\":\"PUT\",\"activityType\":\"Curated\",\"version\":\"<activityVersion>\",\"supportsStreaming\":false,\"subType\":\"standard\"},\"objectName\":\"UpdateEntityRecordV2\",\"operation\":\"replace\",\"packageVersion\":\"<activityVersion>\",\"httpMethod\":\"PUT\",\"path\":\"/v2/{entityName}/UpdateEntityRecord\",\"unifiedTypesCompatible\":true,\"savedJitInputFieldId\":\"in_UpdateEntityRecordV2\"}}"
    }
  },
  "outputs": {
    "output": { "type": "object", "description": "The return value of the connector.", "source": "=result.response", "var": "output" },
    "error":  { "type": "object", "description": "Error information if the node fails", "source": "=Error", "var": "error" }
  }
}
```

---

### Delete Entity Record

```json
{
  "id": "deleteEntityRecord1",
  "type": "uipath.connector.uipath-uipath-dataservice.delete-entity-record",
  "typeVersion": "1.0.0",
  "display": { "label": "Delete <EntityName>", "icon": "https://<cloud_host>/<org_id>/studio_/typecache/icons/98381fa079bbcf73264f551006d6ef7580fb53992f3d9f94361eb5d9e06040cb.svg", "subLabel": "" },
  "inputs": {
    "detail": {
      "connector": "uipath-uipath-dataservice",
      "connectionId": "<connectionId>",
      "connectionResourceId": "<connectionId>",
      "connectionFolderKey": "<folderKey>",
      "method": "POST",
      "endpoint": "/v2/{entityName}/DeleteEntityRecord",
      "pathParameters": { "entityName": "<EntityName>" },
      "queryParameters": { "recordId": "=js:$vars.<sourceNodeId>.output.Id" },
      "uiPathActivityTypeId": "9c8029ee-ff5f-3b82-92cc-34cee15e9f1d",
      "errorState": { "issues": [] },
      "telemetryData": { "connectorKey": "uipath-uipath-dataservice", "connectorName": "Data Fabric", "operationType": "delete", "objectName": "DeleteEntityRecordCurated", "objectDisplayName": "Delete Entity Record", "primaryKeyName": "" },
      "configuration": "=jsonString:{\"essentialConfiguration\":{\"connectorVersion\":\"<connectorVersion>\",\"customFieldsRequestDetails\":null,\"instanceParameters\":{\"connectorKey\":\"uipath-uipath-dataservice\",\"objectName\":\"DeleteEntityRecordCurated\",\"httpMethod\":\"POST\",\"activityType\":\"Curated\",\"version\":\"<activityVersion>\",\"supportsStreaming\":false,\"subType\":\"standard\"},\"objectName\":\"DeleteEntityRecordCurated\",\"operation\":\"delete\",\"packageVersion\":\"<activityVersion>\",\"httpMethod\":\"POST\",\"path\":\"/v2/{entityName}/DeleteEntityRecord\",\"unifiedTypesCompatible\":true}}"
    }
  },
  "outputs": {
    "output": { "type": "object", "description": "The return value of the connector.", "source": "=result.response", "var": "output" },
    "error":  { "type": "object", "description": "Error information if the node fails", "source": "=Error", "var": "error" }
  }
}
```

---

### Get Entity Record by ID

```json
{
  "id": "getEntityRecord1",
  "type": "uipath.connector.uipath-uipath-dataservice.get-entity-record-by-id",
  "typeVersion": "1.0.0",
  "display": { "label": "Get <EntityName> By Id", "icon": "https://<cloud_host>/<org_id>/studio_/typecache/icons/98381fa079bbcf73264f551006d6ef7580fb53992f3d9f94361eb5d9e06040cb.svg", "subLabel": "" },
  "inputs": {
    "detail": {
      "connector": "uipath-uipath-dataservice",
      "connectionId": "<connectionId>",
      "connectionResourceId": "<connectionId>",
      "connectionFolderKey": "<folderKey>",
      "method": "GET",
      "endpoint": "/v2/{entityName}/GetEntityRecord",
      "pathParameters": { "entityName": "<EntityName>" },
      "queryParameters": { "recordId": "=js:$vars.<sourceNodeId>.output.Id", "expansionLevel": "3" },
      "uiPathActivityTypeId": "81291b95-ff0c-3822-bdaa-3065391c1997",
      "errorState": { "issues": [] },
      "telemetryData": { "connectorKey": "uipath-uipath-dataservice", "connectorName": "Data Fabric", "operationType": "retrieve", "objectName": "GetEntityRecordByIdCurated", "objectDisplayName": "Get Entity Record by ID", "primaryKeyName": "" },
      "configuration": "=jsonString:{\"essentialConfiguration\":{\"connectorVersion\":\"<connectorVersion>\",\"customFieldsRequestDetails\":{\"objectActionName\":\"GenerateSchema\",\"parameterValues\":[[\"entityName\",\"<EntityName>\"]]},\"instanceParameters\":{\"connectorKey\":\"uipath-uipath-dataservice\",\"objectName\":\"GetEntityRecordByIdCurated\",\"httpMethod\":\"GET\",\"activityType\":\"Curated\",\"version\":\"<activityVersion>\",\"supportsStreaming\":false,\"subType\":\"standard\"},\"objectName\":\"GetEntityRecordByIdCurated\",\"operation\":\"retrieve\",\"packageVersion\":\"<activityVersion>\",\"httpMethod\":\"GET\",\"path\":\"/v2/{entityName}/GetEntityRecord\",\"unifiedTypesCompatible\":true,\"savedJitInputFieldId\":\"in_GetEntityRecordByIdCurated\"}}"
    }
  },
  "outputs": {
    "output": { "type": "object", "description": "The return value of the connector.", "source": "=result.response", "var": "output" },
    "error":  { "type": "object", "description": "Error information if the node fails", "source": "=Error", "var": "error" }
  }
}
```

---

## Script Nodes That Consume Query Results

When writing a script node that reads query output, guard against empty results:

```javascript
/** @type {any[]} */
const results = $vars.<queryNodeId>.output;
if (!results || results.length === 0) {
  return { skipped: true, reason: 'No matching records.' };
}
/** @type {any} */
const record = results[0];
```

Studio Web types `$vars.<nodeId>.output` as `unknown` — use a JSDoc cast (`/** @type {any} */`) to suppress TypeScript property warnings. These are design-time warnings only and do not affect runtime.
