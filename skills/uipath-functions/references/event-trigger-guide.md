# Connector Event Triggers

Function started by an Integration Service connector event (mail received, Data Fabric record created or updated) declares that start in its bindings file: `bindings_v2.json` (JS/TS) or `bindings.json` (Python). No CLI command writes these entries; write them by hand.

## Rules

1. **Take every value from connector discovery** ([Where values come from](#where-values-come-from)), never from another trigger. Operation and object names are connector-specific (`EMAIL_RECEIVED`, `UPDATED_V3`): never write a generic `CREATED` unless discovery returns it.
2. **Bind the trigger to the function it starts**: `value.EntryPointUniqueId.defaultValue` is the function's `uniqueId` in `entry-points.json`, `displayName` its `filePath`. Without the field Orchestrator binds a Python project's trigger to the first entry point in `entry-points.json`, with no warning, so omit it only when the project has one. Python `init` gives every entry point a new `uniqueId` on each run; copy the new one into the field after every run, since a stale one fails the deploy (`Cannot set entry point. The entry point with path '' was not found`).
3. **Declare the event inputs.** Event starts the function with eight string inputs: `UiPathEventConnector`, `UiPathEvent`, `UiPathEventObjectType`, `UiPathEventObjectId` (the record's or item's id), `UiPathTime`, `UiPathCorrelationId`, `UiPathAdditionalEventData`, `UiPathTriggerActionId`. JS/TS: declare all eight as optional strings — the input contract rejects undeclared properties, and the job faults with `Input validation failed … must NOT have additional properties` before the handler runs. Python: undeclared inputs are ignored; declare the ones the code reads, as `str` defaulting to `""`.
4. **A clean gate proves nothing.** A trigger with a wrong `Operation`, or none, packs, publishes, deploys and pushes clean; function never starts. After deploy, raise one real event and confirm it starts a job that succeeds: `uip or jobs list --folder-key <DEPLOYMENT_FOLDER_KEY> --output json` lists it with `Source: IntegrationTrigger` and `State: Successful` (`uip or triggers list` does not show event triggers).
   - Only a solution deploy creates the trigger; publishing the package and creating its process, with triggers auto-created, creates none.
   - The deploy config gives each event trigger `runtimeType: Unattended`, which never starts a function. Fetch the config with `uip solution deploy config get <SOLUTION_PACKAGE> -d <CONFIG_FILE>`, set the trigger with `uip solution deploy config set <CONFIG_FILE> "<TRIGGER_RESOURCE_NAME>" runtimeType Serverless` (the `kind: trigger` resource's `name` in the file, like `my-function_EventTrigger-Record Created`), and pass `--config-file <CONFIG_FILE>` to `deploy run`, or to `deploy upgrade` for an existing deployment.
   - A Data Fabric entity event fires only on the entity copy the deployment installs in its folder; raise the test event there.

## Binding entries

One `EventTrigger`, plus one `Property` keyed to it when the event takes parameters. Entries in `resources[]`:

```json
[
  {
    "resource": "EventTrigger",
    "key": "<TRIGGER_KEY>",
    "value": {
      "ConnectionId": { "defaultValue": "<CONNECTION_ID>", "isExpression": false, "displayName": "Connection" },
      "EntryPointUniqueId": { "defaultValue": "<ENTRY_POINT_UNIQUE_ID>", "isExpression": false, "displayName": "<ENTRY_POINT_FILE_PATH>" }
    },
    "metadata": {
      "ActivityName": "<EVENT_DISPLAY_NAME>",
      "BindingsVersion": "2.2",
      "Connector": "<CONNECTOR_KEY>",
      "ObjectName": "<OBJECT_NAME>",
      "Operation": "<OPERATION>",
      "FilterExpression": "<FILTER_EXPRESSION>"
    }
  },
  {
    "resource": "Property",
    "key": "<OPERATION>_EventTrigger.<TRIGGER_KEY>",
    "value": {
      "<EVENT_PARAMETER>": { "defaultValue": "<PARAMETER_VALUE>", "isExpression": false, "displayName": "<EVENT_PARAMETER>" }
    },
    "metadata": {
      "ActivityName": "<EVENT_DISPLAY_NAME>",
      "BindingsVersion": "2.2",
      "ObjectName": "<OBJECT_NAME>",
      "ParentResourceKey": "EventTrigger.<TRIGGER_KEY>",
      "TriggerCreateParameters": "<EVENT_PARAMETER_NAMES>",
      "DebugQueryParameters": "<EVENT_PARAMETER_NAMES>"
    }
  }
]
```

- `key`: name unique among the project's triggers. `Property` names its trigger in `metadata.ParentResourceKey` as `EventTrigger.<TRIGGER_KEY>`.
- `TriggerCreateParameters`, `DebugQueryParameters`: the `value` keys, comma-separated.
- `ConnectionId.defaultValue`: connection's id.
- `displayName` on every `value` entry: push of a Python project fails without it (`validation errors for Bindings … displayName Field required`).
- `FilterExpression`: optional ([Filter expression](#filter-expression)).

Data Fabric entity event scopes its `Property` to the entity and adds an `entity` resource that `Property` references in `FieldReferences`:

```json
[
  {
    "resource": "entity",
    "key": "<ENTITY_NAME>",
    "activityDisplayName": "Connector",
    "value": {
      "name": { "defaultValue": "<ENTITY_NAME>", "isExpression": false, "displayName": "Entity" },
      "folderKey": { "defaultValue": "", "isExpression": false, "displayName": "folderKey" }
    },
    "metadata": {
      "ActivityName": "<EVENT_DISPLAY_NAME>",
      "BindingsVersion": "2.2",
      "NameFieldPath": "queryParameters.folderEntityName",
      "Scope": "Folder",
      "FolderFieldPath": "queryParameters.folderEntityName_folderKey"
    }
  },
  {
    "resource": "Property",
    "key": "<OPERATION>_EventTrigger.<TRIGGER_KEY>",
    "id": "Property_<OPERATION>_<TRIGGER_KEY>",
    "activityDisplayName": "Connector",
    "value": {
      "entityScope": { "defaultValue": "folder", "isExpression": false, "displayName": "entityScope" },
      "folderEntityName": { "defaultValue": "<ENTITY_NAME>", "isExpression": false, "displayName": "folderEntityName" },
      "folderEntityName_folderKey": { "defaultValue": "", "isExpression": false, "displayName": "folderEntityName_folderKey" }
    },
    "metadata": {
      "ActivityName": "<EVENT_DISPLAY_NAME>",
      "BindingsVersion": "2.2",
      "ObjectName": "<OBJECT_NAME>",
      "ParentResourceKey": "EventTrigger.<TRIGGER_KEY>",
      "TriggerCreateParameters": "entityScope,folderEntityName,folderEntityName_folderKey",
      "DebugQueryParameters": "entityScope,folderEntityName,folderEntityName_folderKey",
      "FieldReferences": "{\"folderEntityName\": {\"resourceKey\": \"Entity.<ENTITY_NAME>\", \"field\": \"name\"}, \"folderEntityName_folderKey\": {\"resourceKey\": \"Entity.<ENTITY_NAME>\", \"field\": \"folderKey\"}}"
    }
  }
]
```

## Where values come from

| Binding value | Discovery |
|---|---|
| `Connector` | connector key: `uip is connectors list --filter "<CONNECTOR_NAME>" --output json` |
| `ConnectionId.defaultValue` | `Id` from `uip is connections list <CONNECTOR_KEY> --all-folders --output json`; check it with `uip is connections ping <CONNECTION_ID> --output json` |
| `Operation`, `ActivityName` | the event's `Name` (its `Operation` column reads `N/A`) and `DisplayName` from `uip is activities list <CONNECTOR_KEY> --triggers --output json` |
| `ObjectName` | the event's `ObjectName`. A generic `CREATED` / `UPDATED` / `DELETED` event names none: take `Name` from `uip is triggers objects <CONNECTOR_KEY> <OPERATION> --connection-id <CONNECTION_ID> --output json` |
| `Property` `value` keys | event parameters: `EventParameters` from `uip is triggers describe <CONNECTOR_KEY> <OPERATION> <OBJECT_NAME> --connection-id <CONNECTION_ID> --output json`, plus the object's `Parameters[].Name` from `triggers objects` |
| Filter field names | `FilterFields` from the same `describe`. For a Data Fabric entity event it lists only `Id`: take the entity's field `Name`s from `uip df entities get <ENTITY_ID> --folder-key <FOLDER_KEY> --output json` |
| Choice-set value in a filter | `NumberId` from `uip df choice-sets list-values <CHOICE_SET_ID> --output json` |

## Filter expression

`FilterExpression` narrows which events start the function; omit it only when every event on the object should. JMESPath: each condition in parentheses, conditions joined by `&&`.

- String: single quotes, `(<FIELD>=='<VALUE>')`. Boolean or number: backtick literal, ``(<FIELD>==`true`)``. Double quotes are JMESPath identifiers, not strings.
- Choice-set field: ``contains(`[<NUMBER_ID>]`, <FIELD>)``, with the option's `NumberId`, not its position in a list.

Example: ``(contains(`[<NUMBER_ID>]`, <CHOICE_FIELD>))&&(<FIELD>=='<VALUE>')``.
