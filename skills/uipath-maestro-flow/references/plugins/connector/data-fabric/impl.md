# Data Fabric Activity Nodes — Implementation

Step-by-step guide for building Data Fabric connector nodes in a `.flow` file.

- For activity selection, entity discovery: [planning.md](planning.md)
- For the standard IS connector workflow: [connector/impl.md](../impl.md)

---

## Step 1 — Resolve the Connection

```bash
uip is connections list --output json
# Filter: ConnectorKey = "uipath-uipath-dataservice", State = "Enabled"
```

Capture `Id` (→ `<connectionId>`), `FolderKey` (→ `<folderKey>`), and `Name` (→ `<IS connection Name>`).

If no enabled connection exists, tell the user to create one in Integration Service before proceeding.

---

## Step 2 — Resolve the Entity Name

```bash
uip df entities list --native-only --output json
```

Use the exact CamelCase `Name` (e.g. `BankDetails`). For Create/Update, also run `uip df entities get <entity-id> --output json` for field names — skip system fields (`Id`, `CreatedBy`, `CreateTime`, `UpdatedBy`, `UpdateTime`, `RecordOwner`).

---

## Step 3 — Set Up the Flow File

Add these to your `.flow` file:

**1. `runtime: "maestro"` at the flow root** — required or the flow will not execute.

**2. `bindings[]`** — use the actual IS connection display name (e.g. `"aditi.goyal@uipath.com"`), not a connector-key placeholder:

```json
"bindings": [
  {
    "id": "bDFConn",
    "name": "<IS connection Name>",
    "type": "string",
    "resource": "Connection",
    "resourceKey": "<connectionId>",
    "default": "<connectionId>",
    "propertyAttribute": "ConnectionId"
  },
  {
    "id": "bDFFolder",
    "name": "FolderKey",
    "type": "string",
    "resource": "Connection",
    "resourceKey": "<connectionId>",
    "default": "<folderKey>",
    "propertyAttribute": "FolderKey"
  }
]
```

**3. `definitions[]`** — include `sortOrder: 515`, the full icon URL, and the `form` block. Use the templates in the Node JSON Templates section — copy the `definitions` entry from each template wholesale.

---

## Step 4 — Create `bindings_v2.json`

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

`uip maestro flow node add` fails for `uipath.connector.*` types — write nodes directly into the `.flow` JSON using the templates below.

For each node:
- Set `connectionId`, `connectionResourceId` (same value), `connectionFolderKey`, `pathParameters.entityName`, and `bodyParameters`/`queryParameters` as needed.
- Set `model.bindings.resourceKey` to `<connectionId>` — required for connection correlation.
- Set `model.context[].connection` to `"<bindings.<IS connection Name>>"` — must match the `bindings[].name` exactly.
- Copy the `configuration` string verbatim from the templates, replacing only `<EntityName>`.

### Setting Field Values

 see Global md file

**Data Fabric quick reference:**

| Value type | Example |
|---|---|
| Static string | `"BankName": "HDFC Bank"` |
| Previous node output (single record) | `"recordId": "=js:$vars.<sourceNodeId>.output.Id"` |
| Array element (query result) | `"recordId": "=js:$vars.<sourceNodeId>.output[0].Id"` |
| CEQL filter | `"queryExpression": "<FilterExpression>"` (e.g. `"FieldName = 'value' AND OtherField > 10"`) |

`expansionLevel` is always string `"3"`. Static values and CEQL expressions do not use `=js:`. Variable references always do.


## Step 7 — Run `node configure` and Restore Configuration

After writing all nodes, run `node configure` on each connector node from inside the solution directory:

```bash
uip maestro flow node configure <ProjectName>/<ProjectName>.flow <nodeId> \
  --detail '{"connectionId":"<id>","folderKey":"<key>","method":"<METHOD>","endpoint":"<endpoint>","pathParameters":{"entityName":"<EntityName>"},"queryParameters":{...}}' \
  --output json
```

`node configure` resets `customFieldsRequestDetails` to `null` in the `configuration` string. After running it, restore the correct `configuration` string on all nodes except Delete using the exact strings from the Configuration Strings section. Delete is the only node where `customFieldsRequestDetails: null` is correct.

---

## Step 8 — Validate and Upload

```bash
uip maestro flow validate <ProjectName>.flow --output json
uip maestro flow tidy <ProjectName>.flow --output json
uip solution upload <path-to-solution-dir> --output json
```

---

## `inputs.detail` — Field Reference

| Field | Notes |
|---|---|
| `connector` | Always `"uipath-uipath-dataservice"` |
| `connectionId` | UUID from `uip is connections list` |
| `connectionResourceId` | Same UUID as `connectionId` — both required |
| `connectionFolderKey` | Folder UUID from `uip is connections list` |
| `method` | HTTP method — see activity table below |
| `endpoint` | API path — see activity table below |
| `pathParameters` | `{ "entityName": "<CamelCaseEntityName>" }` |
| `queryParameters` | Activity-specific — `expansionLevel` is always string `"3"`, not number |
| `bodyParameters` | Required for Create/Update; omit for Query/Delete/GetById |
| `uiPathActivityTypeId` | Fixed UUID per activity — see table below |
| `errorState` | Always `{ "issues": [] }` |
| `telemetryData` | Connector telemetry object — see table below |
| `configuration` | `=jsonString:{...}` — see Configuration Strings section below |

### Activity Reference

| Activity | Method | Endpoint | `uiPathActivityTypeId` | `operationType` | `objectName` |
|---|---|---|---|---|---|
| Query Entity Records | `POST` | `/v2/{entityName}/qer` | `703065b9-a310-33b8-9d4d-12df0a6f520b` | `list` | `QueryEntityRecordsCurated` |
| Create Entity Record | `POST` | `/v2/{entityName}/CreateEntityRecord` | `dfd2bc7a-ca4b-3316-8a1f-57c9e106dfbf` | `create` | `CreateEntityRecordCurated` |
| Update Entity Record | `PUT` | `/v2/{entityName}/UpdateEntityRecord` | `718fdc36-73a8-3607-8604-ddef95bb9967` | `replace` | `UpdateEntityRecordV2` |
| Delete Entity Record | `POST` | `/v2/{entityName}/DeleteEntityRecord` | `9c8029ee-ff5f-3b82-92cc-34cee15e9f1d` | `delete` | `DeleteEntityRecordCurated` |
| Get Entity Record by ID | `GET` | `/v2/{entityName}/GetEntityRecord` | `81291b95-ff0c-3822-bdaa-3065391c1997` | `retrieve` | `GetEntityRecordByIdCurated` |

`telemetryData` structure (same for all activities):
```json
{
  "connectorKey": "uipath-uipath-dataservice",
  "connectorName": "Data Fabric",
  "operationType": "<see table>",
  "objectName": "<see table>",
  "objectDisplayName": "<Activity Display Name>",
  "primaryKeyName": ""
}
```

---

## Configuration Strings

Use these exact strings. Replace only `<EntityName>` with the CamelCase entity name.

> **`connectorVersion`** is set by the IS connector at the time `node configure` is run — it reflects the connector package version deployed in your tenant. If needed, run `node configure` on a test node and read the generated `configuration` string to get the current value for your environment.

**Query Entity Records Example:**
```
=jsonString:{"essentialConfiguration":{"connectorVersion":"<connectorVersion>","customFieldsRequestDetails":{"objectActionName":"GenerateSchema","parameterValues":[["entityName","<EntityName>"]]},"instanceParameters":{"connectorKey":"uipath-uipath-dataservice","objectName":"QueryEntityRecordsCurated","httpMethod":"POST","activityType":"Curated","version":"1.0.0","supportsStreaming":false,"subType":"standard"},"objectName":"QueryEntityRecordsCurated","operation":"list","packageVersion":"1.0.0","httpMethod":"POST","path":"/v2/{entityName}/qer","unifiedTypesCompatible":true}}
```

**Create Entity Record Example:**
```
=jsonString:{"essentialConfiguration":{"connectorVersion":"<connectorVersion>","customFieldsRequestDetails":{"objectActionName":"GenerateSchema","parameterValues":[["entityName","<EntityName>"]]},"instanceParameters":{"connectorKey":"uipath-uipath-dataservice","objectName":"CreateEntityRecordCurated","httpMethod":"POST","activityType":"Curated","version":"1.0.0","supportsStreaming":false,"subType":"standard"},"objectName":"CreateEntityRecordCurated","operation":"create","packageVersion":"1.0.0","httpMethod":"POST","path":"/v2/{entityName}/CreateEntityRecord","unifiedTypesCompatible":true,"savedJitInputFieldId":"in_CreateEntityRecordCurated"}}
```

**Update Entity Record:**
```
=jsonString:{"essentialConfiguration":{"connectorVersion":<connectorVersion>","customFieldsRequestDetails":{"objectActionName":"GenerateSchema","parameterValues":[["entityName","<EntityName>"]]},"instanceParameters":{"connectorKey":"uipath-uipath-dataservice","objectName":"UpdateEntityRecordV2","httpMethod":"PUT","activityType":"Curated","version":"1.0.0","supportsStreaming":false,"subType":"standard"},"objectName":"UpdateEntityRecordV2","operation":"replace","packageVersion":"1.0.0","httpMethod":"PUT","path":"/v2/{entityName}/UpdateEntityRecord","unifiedTypesCompatible":true,"savedJitInputFieldId":"in_UpdateEntityRecordV2"}}
```

**Get Entity Record by ID:**
```
=jsonString:{"essentialConfiguration":{"connectorVersion":"connectorVersion","customFieldsRequestDetails":{"objectActionName":"GenerateSchema","parameterValues":[["entityName","<EntityName>"]]},"instanceParameters":{"connectorKey":"uipath-uipath-dataservice","objectName":"GetEntityRecordByIdCurated","httpMethod":"GET","activityType":"Curated","version":"1.0.0","supportsStreaming":false,"subType":"standard"},"objectName":"GetEntityRecordByIdCurated","operation":"retrieve","packageVersion":"1.0.0","httpMethod":"GET","path":"/v2/{entityName}/GetEntityRecord","unifiedTypesCompatible":true,"savedJitInputFieldId":"in_GetEntityRecordByIdCurated"}}
```

**Delete Entity Record:**
```
=jsonString:{"essentialConfiguration":{"connectorVersion":"connectorVersion","customFieldsRequestDetails":null,"instanceParameters":{"connectorKey":"uipath-uipath-dataservice","objectName":"DeleteEntityRecordCurated","httpMethod":"POST","activityType":"Curated","version":"1.0.0","supportsStreaming":false,"subType":"standard"},"objectName":"DeleteEntityRecordCurated","operation":"delete","packageVersion":"1.0.0","httpMethod":"POST","path":"/v2/{entityName}/DeleteEntityRecord","unifiedTypesCompatible":true}}
```

> Delete is the only activity where `customFieldsRequestDetails` is `null` — do not restore it after `node configure`.

---

## `definitions[].form` — Required for Studio Web Node Panel

The `form.connectorDetail.configuration` uses **flat JSON** (no `=jsonString:` prefix, no `essentialConfiguration` wrapper):

| Activity | `configuration` value | `uiPathActivityTypeId` |
|---|---|---|
| Query Entity Records | `{"connectorKey":"uipath-uipath-dataservice","objectName":"QueryEntityRecordsCurated","httpMethod":"POST","activityType":"Curated","version":"1.0.0","supportsStreaming":false,"subType":"standard"}` | `703065b9-a310-33b8-9d4d-12df0a6f520b` |
| Create Entity Record | `{"connectorKey":"uipath-uipath-dataservice","objectName":"CreateEntityRecordCurated","httpMethod":"POST","activityType":"Curated","version":"1.0.0","supportsStreaming":false,"subType":"standard"}` | `dfd2bc7a-ca4b-3316-8a1f-57c9e106dfbf` |
| Update Entity Record | `{"connectorKey":"uipath-uipath-dataservice","objectName":"UpdateEntityRecordV2","httpMethod":"PUT","activityType":"Curated","version":"1.0.0","supportsStreaming":false,"subType":"standard"}` | `718fdc36-73a8-3607-8604-ddef95bb9967` |
| Delete Entity Record | `{"connectorKey":"uipath-uipath-dataservice","objectName":"DeleteEntityRecordCurated","httpMethod":"POST","activityType":"Curated","version":"1.0.0","supportsStreaming":false,"subType":"standard"}` | `9c8029ee-ff5f-3b82-92cc-34cee15e9f1d` |
| Get Entity Record by ID | `{"connectorKey":"uipath-uipath-dataservice","objectName":"GetEntityRecordByIdCurated","httpMethod":"GET","activityType":"Curated","version":"1.0.0","supportsStreaming":false,"subType":"standard"}` | `81291b95-ff0c-3822-bdaa-3065391c1997` |

`form` template:
```json
"form": {
  "id": "connector-properties",
  "title": "Connector configuration",
  "sections": [{
    "id": "connector",
    "title": "Connector",
    "collapsible": true,
    "defaultExpanded": true,
    "fields": [{
      "label": "",
      "name": "inputs.detail",
      "type": "custom",
      "component": "dap-config",
      "componentProps": {
        "connectorDetail": {
          "isAppActivity": false,
          "packageId": 196550,
          "svgIconUrl": "icons/98381fa079bbcf73264f551006d6ef7580fb53992f3d9f94361eb5d9e06040cb.svg",
          "displayName": "<Activity Display Name>",
          "assemblyQualifiedName": "UiPath.IntegrationService.Activities.Runtime.Activities.ConnectorActivity, UiPath.IntegrationService.Activities.Runtime, Version=1.26.0.0, Culture=neutral, PublicKeyToken=null",
          "description": "<Activity description>",
          "activityColor": "#E56D5C",
          "configuration": "<flat JSON string from table above>",
          "uiPathActivityTypeId": "<UUID from table above>",
          "isExperimental": true,
          "helpUrlTemplate": "https://docs.uipath.com/{0}/activities/other/latest/integration-service/uipath-uipath-dataservice-<activity-slug>",
          "isEnabled": true,
          "targetPlatform": "CrossPlatform",
          "isAdvanced": false,
          "isRestricted": false,
          "tags": []
        }
      }
    }]
  }]
}
```

---

## Node JSON Templates

Substitute `<EntityName>`, `<connectionId>`, `<folderKey>`, and `<IS connection Name>` with actual values.

> **`display.icon`** uses an environment-specific URL (`<cloud_host>/<org_id>/studio_/typecache/icons/<hash>.svg`). Replace `<cloud_host>/<org_id>` with your tenant's base URL prefix (e.g. `alpha.uipath.com/<your-org-id>`). The icon hash is stable for the Data Fabric connector: `98381fa079bbcf73264f551006d6ef7580fb53992f3d9f94361eb5d9e06040cb.svg`. Alternatively, retrieve the correct URL from `uip maestro flow registry get uipath.connector.uipath-uipath-dataservice.query-entity-records --output json`.

### Query Entity Records

```json
{
  "id": "queryEntityRecords1",
  "type": "uipath.connector.uipath-uipath-dataservice.query-entity-records",
  "typeVersion": "1.0.0",
  "display": { "label": "Query <EntityName>", "description": "(Data Fabric) Retrieves a list of records for the selected Entity from Data Fabric, according to specified filters.", "icon": "https://alpha.uipath.com/f4b9d127-5680-40ff-a562-f76fbdb50ca7/studio_/typecache/icons/98381fa079bbcf73264f551006d6ef7580fb53992f3d9f94361eb5d9e06040cb.svg", "subLabel": "" },
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
      "configuration": "=jsonString:{\"essentialConfiguration\":{\"connectorVersion\":\"connectorVersion\",\"customFieldsRequestDetails\":{\"objectActionName\":\"GenerateSchema\",\"parameterValues\":[[\"entityName\",\"<EntityName>\"]]},\"instanceParameters\":{\"connectorKey\":\"uipath-uipath-dataservice\",\"objectName\":\"QueryEntityRecordsCurated\",\"httpMethod\":\"POST\",\"activityType\":\"Curated\",\"version\":\"1.0.0\",\"supportsStreaming\":false,\"subType\":\"standard\"},\"objectName\":\"QueryEntityRecordsCurated\",\"operation\":\"list\",\"packageVersion\":\"1.0.0\",\"httpMethod\":\"POST\",\"path\":\"/v2/{entityName}/qer\",\"unifiedTypesCompatible\":true}}"
    }
  },
  "outputs": {
    "output": { "type": "object", "description": "The return value of the connector.", "source": "=result.response", "var": "output" },
    "error":  { "type": "object", "description": "Error information if the node fails", "source": "=Error", "var": "error" }
  },
  "model": {
    "type": "bpmn:SendTask",
    "serviceType": "Intsvc.ActivityExecution",
    "debug": { "runtime": "bpmnEngine" },
    "bindings": { "resourceKey": "<connectionId>" },
    "context": [
      { "name": "connectorKey", "type": "string", "value": "uipath-uipath-dataservice" },
      { "name": "operation",    "type": "string" },
      { "name": "objectName",   "type": "string", "value": "QueryEntityRecordsCurated" },
      { "name": "method",       "type": "string", "value": "POST" },
      { "name": "connection",   "type": "string", "value": "<bindings.<IS connection Name>>" },
      { "name": "folderKey",    "type": "string", "value": "<bindings.FolderKey>" },
      { "name": "activityConfigurationVersion", "type": "string", "value": "v1" },
      { "name": "metadata", "body": { "telemetryData": { "connectorKey": "uipath-uipath-dataservice", "connectorName": "Query Entity Records" }, "inputMetadata": {}, "errorState": { "hasError": true } }, "type": "json" }
    ]
  }
}
```

**With CEQL filter** — add to `queryParameters`: `"queryExpression": "<FilterExpression>"` where `<FilterExpression>` is the CEQL expression the user specifies (e.g. `"FieldName = 'value' AND OtherField > 10"`).

**Output:** `<nodeId>.output` — array of records. Access fields as `=js:$vars.<nodeId>.output[0].<FieldName>`. The node ID is whatever `"id"` value you set on this node.

---

### Create Entity Record

```json
{
  "id": "createEntityRecord1",
  "type": "uipath.connector.uipath-uipath-dataservice.create-entity-record",
  "typeVersion": "1.0.0",
  "display": { "label": "Create <EntityName>", "description": "(Data Fabric) Creates a new record for the selected Entity in Data Fabric", "icon": "https://alpha.uipath.com/f4b9d127-5680-40ff-a562-f76fbdb50ca7/studio_/typecache/icons/98381fa079bbcf73264f551006d6ef7580fb53992f3d9f94361eb5d9e06040cb.svg", "subLabel": "" },
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
      "configuration": "=jsonString:{\"essentialConfiguration\":{\"connectorVersion\":\"connectorVersion\",\"customFieldsRequestDetails\":{\"objectActionName\":\"GenerateSchema\",\"parameterValues\":[[\"entityName\",\"<EntityName>\"]]},\"instanceParameters\":{\"connectorKey\":\"uipath-uipath-dataservice\",\"objectName\":\"CreateEntityRecordCurated\",\"httpMethod\":\"POST\",\"activityType\":\"Curated\",\"version\":\"1.0.0\",\"supportsStreaming\":false,\"subType\":\"standard\"},\"objectName\":\"CreateEntityRecordCurated\",\"operation\":\"create\",\"packageVersion\":\"1.0.0\",\"httpMethod\":\"POST\",\"path\":\"/v2/{entityName}/CreateEntityRecord\",\"unifiedTypesCompatible\":true,\"savedJitInputFieldId\":\"in_CreateEntityRecordCurated\"}}"
    }
  },
  "outputs": {
    "output": { "type": "object", "description": "The return value of the connector.", "source": "=result.response", "var": "output" },
    "error":  { "type": "object", "description": "Error information if the node fails", "source": "=Error", "var": "error" }
  },
  "model": {
    "type": "bpmn:SendTask",
    "serviceType": "Intsvc.ActivityExecution",
    "debug": { "runtime": "bpmnEngine" },
    "bindings": { "resourceKey": "<connectionId>" },
    "context": [
      { "name": "connectorKey", "type": "string", "value": "uipath-uipath-dataservice" },
      { "name": "operation",    "type": "string" },
      { "name": "objectName",   "type": "string", "value": "CreateEntityRecordCurated" },
      { "name": "method",       "type": "string", "value": "POST" },
      { "name": "connection",   "type": "string", "value": "<bindings.<IS connection Name>>" },
      { "name": "folderKey",    "type": "string", "value": "<bindings.FolderKey>" },
      { "name": "activityConfigurationVersion", "type": "string", "value": "v1" },
      { "name": "metadata", "body": { "telemetryData": { "connectorKey": "uipath-uipath-dataservice", "connectorName": "Create Entity Record" }, "inputMetadata": {}, "errorState": { "hasError": true } }, "type": "json" }
    ]
  }
}
```

**Using a value from a previous node:** `"bodyParameters": { "<FieldName>": "=js:$vars.<sourceNodeId>.output[0].<FieldName>" }` — replace `<sourceNodeId>` with the ID of the node whose output you are reading, and `<FieldName>` with the exact field name from that node's output.

**Output:** `<nodeId>.output` — the newly created record object (includes `Id`). The node ID is whatever `"id"` value you set on this node.

---

### Update Entity Record

```json
{
  "id": "updateEntityRecord1",
  "type": "uipath.connector.uipath-uipath-dataservice.update-entity-record",
  "typeVersion": "1.0.0",
  "display": { "label": "Update <EntityName>", "description": "(Data Fabric) Updates an existing record in a Data Fabric entity", "icon": "https://alpha.uipath.com/f4b9d127-5680-40ff-a562-f76fbdb50ca7/studio_/typecache/icons/98381fa079bbcf73264f551006d6ef7580fb53992f3d9f94361eb5d9e06040cb.svg", "subLabel": "" },
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
      "configuration": "=jsonString:{\"essentialConfiguration\":{\"connectorVersion\":\"connectorVersion\",\"customFieldsRequestDetails\":{\"objectActionName\":\"GenerateSchema\",\"parameterValues\":[[\"entityName\",\"<EntityName>\"]]},\"instanceParameters\":{\"connectorKey\":\"uipath-uipath-dataservice\",\"objectName\":\"UpdateEntityRecordV2\",\"httpMethod\":\"PUT\",\"activityType\":\"Curated\",\"version\":\"1.0.0\",\"supportsStreaming\":false,\"subType\":\"standard\"},\"objectName\":\"UpdateEntityRecordV2\",\"operation\":\"replace\",\"packageVersion\":\"1.0.0\",\"httpMethod\":\"PUT\",\"path\":\"/v2/{entityName}/UpdateEntityRecord\",\"unifiedTypesCompatible\":true,\"savedJitInputFieldId\":\"in_UpdateEntityRecordV2\"}}"
    }
  },
  "outputs": {
    "output": { "type": "object", "description": "The return value of the connector.", "source": "=result.response", "var": "output" },
    "error":  { "type": "object", "description": "Error information if the node fails", "source": "=Error", "var": "error" }
  },
  "model": {
    "type": "bpmn:SendTask",
    "serviceType": "Intsvc.ActivityExecution",
    "debug": { "runtime": "bpmnEngine" },
    "bindings": { "resourceKey": "<connectionId>" },
    "context": [
      { "name": "connectorKey", "type": "string", "value": "uipath-uipath-dataservice" },
      { "name": "operation",    "type": "string" },
      { "name": "objectName",   "type": "string", "value": "UpdateEntityRecordV2" },
      { "name": "method",       "type": "string", "value": "PUT" },
      { "name": "connection",   "type": "string", "value": "<bindings.<IS connection Name>>" },
      { "name": "folderKey",    "type": "string", "value": "<bindings.FolderKey>" },
      { "name": "activityConfigurationVersion", "type": "string", "value": "v1" },
      { "name": "metadata", "body": { "telemetryData": { "connectorKey": "uipath-uipath-dataservice", "connectorName": "Update Entity Record" }, "inputMetadata": {}, "errorState": { "hasError": true } }, "type": "json" }
    ]
  }
}
```


### Delete Entity Record

```json
{
  "id": "deleteEntityRecord1",
  "type": "uipath.connector.uipath-uipath-dataservice.delete-entity-record",
  "typeVersion": "1.0.0",
  "display": { "label": "Delete <EntityName>", "description": "(Data Fabric) Deletes an existing record for the selected entity from Data Fabric", "icon": "https://alpha.uipath.com/f4b9d127-5680-40ff-a562-f76fbdb50ca7/studio_/typecache/icons/98381fa079bbcf73264f551006d6ef7580fb53992f3d9f94361eb5d9e06040cb.svg", "subLabel": "" },
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
      "configuration": "=jsonString:{\"essentialConfiguration\":{\"connectorVersion\":\"connectorVersion\",\"customFieldsRequestDetails\":null,\"instanceParameters\":{\"connectorKey\":\"uipath-uipath-dataservice\",\"objectName\":\"DeleteEntityRecordCurated\",\"httpMethod\":\"POST\",\"activityType\":\"Curated\",\"version\":\"1.0.0\",\"supportsStreaming\":false,\"subType\":\"standard\"},\"objectName\":\"DeleteEntityRecordCurated\",\"operation\":\"delete\",\"packageVersion\":\"1.0.0\",\"httpMethod\":\"POST\",\"path\":\"/v2/{entityName}/DeleteEntityRecord\",\"unifiedTypesCompatible\":true}}"
    }
  },
  "outputs": {
    "output": { "type": "object", "description": "The return value of the connector.", "source": "=result.response", "var": "output" },
    "error":  { "type": "object", "description": "Error information if the node fails", "source": "=Error", "var": "error" }
  },
  "model": {
    "type": "bpmn:SendTask",
    "serviceType": "Intsvc.ActivityExecution",
    "debug": { "runtime": "bpmnEngine" },
    "bindings": { "resourceKey": "<connectionId>" },
    "context": [
      { "name": "connectorKey", "type": "string", "value": "uipath-uipath-dataservice" },
      { "name": "operation",    "type": "string" },
      { "name": "objectName",   "type": "string", "value": "DeleteEntityRecordCurated" },
      { "name": "method",       "type": "string", "value": "POST" },
      { "name": "connection",   "type": "string", "value": "<bindings.<IS connection Name>>" },
      { "name": "folderKey",    "type": "string", "value": "<bindings.FolderKey>" },
      { "name": "activityConfigurationVersion", "type": "string", "value": "v1" },
      { "name": "metadata", "body": { "telemetryData": { "connectorKey": "uipath-uipath-dataservice", "connectorName": "Delete Entity Record" }, "inputMetadata": {}, "errorState": { "hasError": true } }, "type": "json" }
    ]
  }
}
```

**`recordId` from a previous node:** `"queryParameters": { "recordId": "=js:$vars.<sourceNodeId>.output[0].Id" }` — replace `<sourceNodeId>` with the ID of the node that produced the record (e.g. a Query node result or a Create node output via `.output.Id`).

---

### Get Entity Record by ID

```json
{
  "id": "getEntityRecord1",
  "type": "uipath.connector.uipath-uipath-dataservice.get-entity-record-by-id",
  "typeVersion": "1.0.0",
  "display": { "label": "Get <EntityName> By Id", "description": "(Data Fabric) Reads an existing record for the selected entity from Data Fabric", "icon": "https://alpha.uipath.com/f4b9d127-5680-40ff-a562-f76fbdb50ca7/studio_/typecache/icons/98381fa079bbcf73264f551006d6ef7580fb53992f3d9f94361eb5d9e06040cb.svg", "subLabel": "" },
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
      "configuration": "=jsonString:{\"essentialConfiguration\":{\"connectorVersion\":\"connectorVersion\",\"customFieldsRequestDetails\":{\"objectActionName\":\"GenerateSchema\",\"parameterValues\":[[\"entityName\",\"<EntityName>\"]]},\"instanceParameters\":{\"connectorKey\":\"uipath-uipath-dataservice\",\"objectName\":\"GetEntityRecordByIdCurated\",\"httpMethod\":\"GET\",\"activityType\":\"Curated\",\"version\":\"1.0.0\",\"supportsStreaming\":false,\"subType\":\"standard\"},\"objectName\":\"GetEntityRecordByIdCurated\",\"operation\":\"retrieve\",\"packageVersion\":\"1.0.0\",\"httpMethod\":\"GET\",\"path\":\"/v2/{entityName}/GetEntityRecord\",\"unifiedTypesCompatible\":true,\"savedJitInputFieldId\":\"in_GetEntityRecordByIdCurated\"}}"
    }
  },
  "outputs": {
    "output": { "type": "object", "description": "The return value of the connector.", "source": "=result.response", "var": "output" },
    "error":  { "type": "object", "description": "Error information if the node fails", "source": "=Error", "var": "error" }
  },
  "model": {
    "type": "bpmn:SendTask",
    "serviceType": "Intsvc.ActivityExecution",
    "debug": { "runtime": "bpmnEngine" },
    "bindings": { "resourceKey": "<connectionId>" },
    "context": [
      { "name": "connectorKey", "type": "string", "value": "uipath-uipath-dataservice" },
      { "name": "operation",    "type": "string" },
      { "name": "objectName",   "type": "string", "value": "GetEntityRecordByIdCurated" },
      { "name": "method",       "type": "string", "value": "GET" },
      { "name": "connection",   "type": "string", "value": "<bindings.<IS connection Name>>" },
      { "name": "folderKey",    "type": "string", "value": "<bindings.FolderKey>" },
      { "name": "activityConfigurationVersion", "type": "string", "value": "v1" },
      { "name": "metadata", "body": { "telemetryData": { "connectorKey": "uipath-uipath-dataservice", "connectorName": "Get Entity Record by ID" }, "inputMetadata": {}, "errorState": { "hasError": true } }, "type": "json" }
    ]
  }
}
```

**Output:** `<nodeId>.output` — single entity record object. The node ID is whatever `"id"` value you set on this node.

---

## Script Nodes That Consume Query Results

When writing a script node that reads query output, guard against empty results:

```javascript
/** @type {any[]} */
const results = $vars.<queryNodeId>.output;  // replace <queryNodeId> with the ID of your Query node
if (!results || results.length === 0) {
  return { skipped: true, reason: 'No matching records.' };
}
/** @type {any} */
const record = results[0];
```

Studio Web types `$vars.<nodeId>.output` as `unknown` — use a JSDoc cast (`/** @type {any} */`) to suppress TypeScript property warnings. These are design-time warnings only and do not affect runtime.
