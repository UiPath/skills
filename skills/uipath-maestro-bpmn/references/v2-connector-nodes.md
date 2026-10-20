# V2 connector nodes

**Every new connector node is a V2 element**, built with `registry get
--input-details` (below), in every workflow:

- **New workflow.** A workflow Studio Web or `uip maestro bpmn init` creates
  carries `<uipath:intsvcActivityConfig version="v2" />` in its process
  `extensionElements`.
- **Existing workflow without the marker.** Still build the new node as V2.
  The node's own `activityConfigurationVersion` `v2` decides how Studio Web
  opens it, whatever the workflow says, and the runtime runs V2 activities,
  triggers, waits and HTTP requests in an unmarked workflow. **Never add the
  marker to an existing workflow**: its V1 nodes do not declare a version,
  so the marker would make Studio Web read them as V2. Leave existing V1
  nodes as they are unless the task asks to change them.
- **An existing V1 trigger or wait does not run.** The runtime runs it as V2
  and faults with `Value cannot be null. (Parameter 'Connection')`, Studio
  Web's own V1 save included. `uip maestro bpmn validate` warns about one in
  an unmarked workflow and fails one in a V2 workflow. When a task touches
  such a trigger or wait, rebuild it as V2 with the same object, operation
  and parameters, and say so in your summary.

A workflow with no connection yet keeps the registry template shell as a
draft (the SKILL.md draft rule); do not fill it in as a configured V1 node.
That shell is V1-shaped (`activityConfigurationVersion` `v1`), so the draft
notes say so, and once a connection exists it is replaced by the element
`registry get --input-details` builds. In a V2 workflow `validate` fails a V1
trigger or wait shell until then.

| Type | V2 element | Notes |
| --- | --- | --- |
| `Intsvc.ActivityExecution` | `bpmn:sendTask` | Connector activities. |
| `Intsvc.UnifiedHttpRequest` | `bpmn:sendTask` | **Every new HTTP request**, manual or through a connector's connection — see [HTTP requests](#http-requests). |
| `Intsvc.EventTrigger` | `bpmn:startEvent` | Its own entry point (`uipath:entryPointId`). |
| `Intsvc.WaitForEvent` | `bpmn:receiveTask` | Move the `uipath:event` block onto an `intermediateCatchEvent` or `boundaryEvent` host if the process needs one, with a bare `<bpmn:messageEventDefinition />` after the flows. |
| `Intsvc.AsyncExecution` (external agent) | `bpmn:serviceTask` | Saved as `Intsvc.SyncAgentExecution` or `Intsvc.AsyncAgentExecution`, whichever the connector reports — see [External agents and automations](#external-agents-and-automations). |
| `Intsvc.AsyncWorkflowExecution` (external automation) | `bpmn:serviceTask` | Saved as `Intsvc.SyncWorkflowExecution` or `Intsvc.AsyncWorkflowExecution`. |

Never author `Intsvc.HttpExecution` (legacy HTTP) or a connector's own
`httpRequest` object for a new node; keep one only where an existing workflow
already has it. `Intsvc.TimerTrigger` binds no connection and is authored from
its template.

**A value that reads a variable is `=js:<expression>`** — `"=js:vars.Var_Name"`,
`"=js:'Hello ' + vars.Var_Name"`. Studio Web's V2 component shows `=vars.x` as
plain text instead of a variable; `registry get` rewrites `=vars.x` to
`=js:vars.x`, but write `=js:` yourself. `=bindings.<id>` references stay as
they are.

## 1. Get the element

Find the connection and the object exactly as for a V1 node
([§3](registry-workflow.md#3-connector-intsvc-enrichment) for activities,
[Integration Service triggers](registry-workflow.md#integration-service-triggers)
for triggers and waits). Then ask for the V2 element:

```bash
uip maestro bpmn registry get Intsvc.ActivityExecution \
    --connection-id <id> --object-name <ObjectName> \
    --input-details '{"bodyParameters":{"name":"=js:vars.Var_Name"},"queryParameters":{"entityScope":"folder","folderEntityName":"<entity>"}}' \
    --solution-folder <solution-dir> --output json

uip maestro bpmn registry get Intsvc.EventTrigger \
    --connection-id <id> --object-name <ObjectName> --operation <OPERATION> \
    --input-details '{"queryParameters":{"entityScope":"folder","folderEntityName":"<entity>"}}' \
    --solution-folder <solution-dir> --output json
```

- `--input-details` takes the node's values, as JSON or `@file.json` — the
  same contract as `uip maestro case spec --input-details`
  ([shape reference](#--input-details-reference)):
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

### HTTP requests

```bash
# Authenticates itself: no connection
uip maestro bpmn registry get Intsvc.UnifiedHttpRequest \
    --input-details '{"authentication":"manual","method":"GET","url":"https://api.example.com/items","headers":{"Authorization":"=js:\"Bearer \" + vars.Var_Token"},"query":{"limit":"10"}}' \
    --output json

# Through a connector's connection: --connection-id names it, the endpoint is relative
uip maestro bpmn registry get Intsvc.UnifiedHttpRequest --connection-id <connection-id> \
    --input-details '{"authentication":"connector","method":"GET","url":"/conversations.list","query":{"limit":"5"}}' \
    --output json
```

`--input-details` is the request: `authentication` (`manual` or `connector`),
`method`, `url`, and optional `headers` and `query` objects and a `body`
(sent for `POST`, `PUT` and `PATCH`). In connector mode the command takes the
target connector and folder from the connection. The element binds Studio
Web's implicit connection for a manual request and the target connection for a
connector one. Its outputs are `code`, `headers` and `body`, plus `Error`.

When `registry get` says an object has no activity in the catalog
(`Cannot identify the V2 element`, e.g. Slack's `emoji_list_GET`), the
endpoint is not a catalog activity: send it as a connector-mode HTTP request
through the same connection. Never fall back to the V1 template for it; the
V1 node neither opens nor packs the way Studio Web needs.

A service with no Integration Service connector of its own (Spotify, an
internal API) goes through a connection of the generic HTTP connector,
`uipath-uipath-http`, which holds the service's base URL and auth: connector
mode with `--connection-id` of that connection and a relative `url`
(`"/me"`). Use manual mode only when no such connection exists and the
request carries its own auth.

### External agents and automations

An external agent (CrewAI, Snowflake Cortex, Azure AI Foundry, Salesforce
Agentforce, Google Vertex, Databricks…) or automation (Power Automate,
Salesforce flows) is an activity of its connector, listed in Studio Web's
external-agent and external-automation catalogs:

```bash
uip maestro bpmn registry get Intsvc.AsyncExecution \
    --connection-id <id> --object-name <ObjectName> \
    --input-details '{"bodyParameters":{"prompt":"=js:vars.Var_Question"}}' \
    --solution-folder <solution-dir> --output json
```

The connection must be the agent connector's own: Execute Salesforce Agent
is `uipath-salesforce-agent`, not a `uipath-salesforce-sfdc` connection. Find
it with `uip is connections list <connector-key> --all-folders`; the command
refuses a connection of another connector.

Use `Intsvc.AsyncWorkflowExecution` for an automation. `Data.V2.ExtensionType`
is the type the node is saved as: the connector's `executionType` decides sync
or async, and an async one also carries the event it answers with
(`operation`, `eventMode`). Take the fields from `uip is resources describe
<connector> <ObjectName> --connection-id <id> --operation Create`.

### Files: download, upload, attach

A download (OneDrive or Google Drive Download File, Outlook Download Email)
outputs a file: its `response` output is `type="file"` with
`target="=orchestrator.JobAttachments"`. An upload, or Send Email with an
attachment, takes the file under its file parameter in `bodyParameters`
(usually `file`), read from the download's variable:

```bash
uip maestro bpmn registry get Intsvc.ActivityExecution \
    --connection-id <onedrive-connection> --object-name FileUploadV2 \
    --input-details '{"queryParameters":{"referenceID":"<drive-id> - <folder-item-id>"},"bodyParameters":{"file":"=js:vars.<download-var>"}}' \
    --solution-folder <solution-dir> --output json
```

The rest of `bodyParameters` is the request body. Outlook's
`message.toRecipients` is a comma-separated string, not a Graph array.

A bare item id as `referenceID` fails with `400 ... drive id appears to be malformed`. List a
folder's files, each with `FullName`, `Type` and `ReferenceID`, with
`uip is resources run list uipath-microsoft-onedrive CuratedFileAndFolder
--connection-id <id> --query "id=<folder-item-id>" --output json`; the
`CuratedFolder` list gives the folders. Other query keys are ignored and
return the drive root.

## 2. Paste it

Follow `Data.V2.Instructions` (tokens, `RootBindings`, `Variables`, the
marker). Beyond it:

- An output other than `response` / `Error` writes `{{VAR_ID}}_<name>` (an
  HTTP request's `code`, `headers`, `body`). A trigger has no
  `{{INCOMING_EDGE}}`.
- If `Data.V2.MissingRequired` lists inputs (e.g. `bodyParameters.prompt`),
  run `registry get` again with them in `--input-details` before pasting.
- Do not edit the element's `uipath:context` or its `metadata`. To change a
  value, run `registry get` again with new `--input-details`. A body value
  that reads a variable (`"=js:vars.<id>"`) goes in `bodyParameters`, never
  into the pasted XML.

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

<!--skill-flavor:v2-solution-resources-refresh:start-->
Then sync the solution so each connection becomes a solution resource. The
V2 properties panel shows a connection that is not one as "The selected
connection is not part of the solution":

```bash
uip solution resources refresh --solution-folder <solution-dir>
```
<!--skill-flavor:v2-solution-resources-refresh:end-->

To debug from the trigger, name its start event. A trigger debug replays a
recent event rather than waiting for one, so cause the event (create or
update a record in the picked entity) **just before** you start; with none
the run faults `102003 DebugTriggerNoMatches`:

```bash
uip maestro bpmn debug <project-path> --entry-point <trigger-start-event-id>
```

Without `--entry-point` the debug starts at the first entry in
`entry-points.json`, the first start event in the `.bpmn` file (not the
topmost on the canvas), which can be the trigger; pass `--entry-point <manual-start-id>` to
debug from the manual start. A wait is debugged from the manual start,
and its event has to happen while the wait is in progress. Debug's own
progress lines can lag behind the run, so read where the instance is with
`uip maestro bpmn debug-instance variables-all <instance-id>` (the instance id
is in the debug log: `--log-level debug --log-file <file>`), and cause the
event once the wait element shows as running.

### A CLI without V2 nodes

When a `registry get` with `--input-details` fails with an error that names
`--input-details`, or succeeds without a `Data.V2` (or `bpmn debug` rejects
`--entry-point`), the CLI predates V2 nodes, or that node type's V2 build:

- **Triggers, waits, HTTP requests and external agents or automations:**
  stop. Their V1 template faults at run time or has no allowed form. Tell the
  user to update `uip` and leave the node out.
- **Plain activities** (`Intsvc.ActivityExecution`): fill the V1 template by
  [registry-workflow.md §3](registry-workflow.md#3-connector-intsvc-enrichment)
  in full — one `target="body"` input holding the whole body — and say in the
  notes that the node is V1.

## `--input-details` reference

The contract is shared with `uip maestro case spec`:

| Key | Activities | Triggers and waits | Lands in |
| --- | --- | --- | --- |
| `bodyParameters` | yes | — | the one `target="body"` input; dotted keys nest (`message.subject`) |
| `queryParameters` | yes | yes | the `queryParameters` input (activity) or `body.parameters` (trigger, wait) |
| `pathParameters` | yes | yes | the `pathParameters` input, or `body.parameters` |
| `eventParameters` | — | yes | `body.queryParams` |
| `filter` | yes | yes | a FilterTree the design-time client compiles into the connector's filter field (activity) or `body.filters.expression` (trigger, wait) |

A FilterTree is `{"groupOperator":"And","filters":[{"id":"<field>","operator":"<operator>","value":{"isLiteral":true,"rawString":"\"x\"","value":"x"}}],"groups":[]}`;
take the field names and operators from the spec's `filter.fields`, emit
`"And"` even for one condition, and never put a raw CEQL or JMESPath string in
`queryParameters` for a field the connector filters with (`where`,
`queryExpression`) — the designer re-renders the filter only from the tree.
A `filter` of `{}` is refused. Connection identity (`connectionId`, `folderKey`, method,
path) never goes in `--input-details`; it comes from `--connection-id` and the
catalog, except for an HTTP request (above).
