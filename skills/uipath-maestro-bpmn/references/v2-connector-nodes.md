# V2 connector nodes

Studio Web saves every new BPMN workflow with the V2 (Unified Build)
connector component: the process carries
`<uipath:intsvcActivityConfig version="v2" />` and each connector node
`activityConfigurationVersion: v2`. The V2 properties panel reads only the V2
shape, so a node authored from the V1 registry template opens in the designer
with no activity selected and its instance parameters missing, even when it
runs.

**Author a connector node as V2 whenever a live connection is available.** The
CLI builds the whole element from the connector's design-time configuration,
so nothing in it is hand-written. Keep the V1 template (the rest of
[registry-workflow.md](registry-workflow.md)) only for an offline draft that
hands enrichment to the CLI.

| Type | V2 element | Notes |
| --- | --- | --- |
| `Intsvc.ActivityExecution` | `bpmn:sendTask` | Connector activities, including a connector's own HTTP request object. |
| `Intsvc.EventTrigger` | `bpmn:startEvent` | Its own entry point (`uipath:entryPointId`). |
| `Intsvc.WaitForEvent` | `bpmn:receiveTask` | Move the `uipath:event` block onto an `intermediateCatchEvent` or `boundaryEvent` host if the process needs one, with a bare `<bpmn:messageEventDefinition />` after the flows. |

Not V2 connector elements: `Intsvc.UnifiedHttpRequest` and
`Intsvc.HttpExecution` (connectionless manual HTTP), `Intsvc.TimerTrigger` (no
connection), and the agent and workflow execution types. `registry get`
refuses V2 options for them (`<type> has no V2 connector element`).

## 1. Get the element

Find the connection and the object exactly as for a V1 node
([§3](registry-workflow.md#3-connector-intsvc-enrichment) for activities,
[Integration Service triggers](registry-workflow.md#integration-service-triggers)
for triggers and waits). Then ask for the V2 element:

```bash
uip maestro bpmn registry get Intsvc.ActivityExecution \
    --connection-id <id> --object-name <ObjectName> \
    --input-details '{"bodyParameters":{"name":"=vars.Var_Name"},"queryParameters":{"entityScope":"folder","folderEntityName":"<entity>"}}' \
    --solution-folder <solution-dir> --output json

uip maestro bpmn registry get Intsvc.EventTrigger \
    --connection-id <id> --object-name <ObjectName> --operation <OPERATION> \
    --input-details '{"queryParameters":{"entityScope":"folder","folderEntityName":"<entity>"}}' \
    --solution-folder <solution-dir> --output json
```

- `--input-details` takes the node's values, as JSON or `@file.json`:
  activities `{bodyParameters, queryParameters, pathParameters, filter}`,
  triggers and waits `{eventParameters, queryParameters, pathParameters,
  filter}`. Pass `{}` when there is nothing to set. The field names come from
  `uip is resources describe` (activities) or `uip is triggers describe`
  (triggers, waits), with `-f` for any picker, as for Flow and Case.
- A **resource picker** (a Data Fabric folder entity on `folderEntityName`)
  takes the resource's name. On Data Fabric the folder-entity picker is on
  the `*_V3` objects (`CreateEntityRecord_V3`, `GetEntityRecord_V3`,
  `QueryEntityRecords_V3`, `UpdateEntityRecord_V3`, `DeleteEntityRecord_V3`,
  the `*Experimental_V3` objects, and the `EntityTriggers_V3` trigger), which
  `uip is resources list` labels `(Preview)` or `(Experimental)`; the
  `<EntityName>` objects are tenant entities and have no picker. Use the
  `*_V3` objects for a folder entity even though the V1 table below says to
  skip `(Preview)` objects. The CLI finds it in the solution or on the
  tenant, binds it into `--solution-folder`, and reads it through root
  bindings. When the name is in several folders the command fails
  `invalid_argument`, `A resource picker in --input-details did not resolve`,
  and lists each folder key; add `"<field>_folderKey": "<FolderKey>"` next to
  the name and run it again.
- The activity type is looked up from the Studio Web catalog by object (and
  operation for triggers). When an object carries several activities the
  command lists them; pass `--activity-type-id <id>` with the one you mean.

`Data.V2` carries `ActivityTypeId`, `ElementXml`, `RootBindings`,
`Variables` and `Instructions`.

## 2. Paste it

1. Put `ElementXml` in the process and replace its tokens: `{id}`, `{name}`,
   `{incomingEdge}`, `{outgoingEdge}` (a trigger has no incoming edge),
   `{varId}` and `{errorVarId}`.
2. Add each `RootBindings` line to the process's `<uipath:bindings>`. Binding
   ids are derived from what they bind, so two nodes on the same connection or
   entity return identical lines; add each line once.
3. Add each `Variables` line to `<uipath:variables>`, with the same `{varId}`
   / `{errorVarId}` / `{id}` replacements.
4. Add `<uipath:intsvcActivityConfig version="v2" />` once to the process's
   `extensionElements`.

Do not edit the element's `uipath:context` or its `metadata`: they are the
connector's design-time configuration, and the designer reads them back as
they are. To change a value, run `registry get` again with new
`--input-details`. A body value that reads a variable (`"=vars.<id>"`) goes in
`bodyParameters`, never into the pasted XML.

V2 differs from the V1 template in ways that matter at run time, so never mix
the two shapes in one node:

| | V1 template | V2 element |
| --- | --- | --- |
| Trigger and wait connection | `connectionId`, plus `folderId` / `folderPath` | `connection`, `resourceKey`, `folderKey` |
| Trigger and wait parameters | `body.queryParams` | `body.parameters` |
| Activity query and path fields | one input per field, `target="query"` / `"path"` | one JSON input each, `target="queryParameters"` / `"pathParameters"` |
| `metadata` | `{}` | design-time configuration, catalog entry, telemetry and the node's picker bindings |

A V1 trigger context under V2 faults with `Value cannot be null (Parameter
'Connection')`; V1 trigger parameters under V2 fault with `searchParams value
'{entityScope},folder'`.

## 3. Refresh, validate, debug

```bash
uip maestro bpmn format <file.bpmn>
uip maestro bpmn refresh <project-path>
uip maestro bpmn validate <file.bpmn>
```

`refresh` writes what Studio Web writes on save: the Connection resource for
every connector node, an `EventTrigger` resource and its `Property` resource
for each trigger start (without them a deployed process never gets its
trigger), and one resource for each solution resource a picker bound. A V2
trigger start is an entry point of its own, so a process whose only start is a
connector trigger refreshes and packs without a manual start.

To debug from the trigger, name its start event. A trigger debug replays a
recent event rather than waiting for one, so cause the event (create or
update a record in the picked entity) **just before** you start; with none
the run faults `102003 DebugTriggerNoMatches`:

```bash
uip maestro bpmn debug <project-path> --entry-point <trigger-start-event-id>
```

Without `--entry-point` the debug starts at the first entry point, which is
the manual start when there is one. A wait is debugged from the manual start,
and its event has to happen while the wait is in progress. Debug's own
progress lines can lag behind the run, so read where the instance is with
`uip maestro bpmn debug-instance variables-all <instance-id>` (the instance id
is in the debug log: `--log-level debug --log-file <file>`), and cause the
event once the wait element shows as running.

These need a CLI that has `registry get --input-details` and
`bpmn debug --entry-point`. On an older CLI (`unknown option
'--input-details'`), author the V1 template and say in the notes that the
node is V1.
