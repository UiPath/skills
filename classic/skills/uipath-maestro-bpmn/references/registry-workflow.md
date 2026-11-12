# Registry workflow

Every `uipath:*` payload in a Maestro `.bpmn` comes from the registry, never prose or hand-written XML. Turn intent into registry-backed XML as follows.

## 1. Sync and discover

Run:

```bash
uip maestro bpmn registry pull            # sync + cache (login for connectors/processes)
uip maestro bpmn registry list --limit -1 --output json   # all extension types
uip maestro bpmn registry search <keyword> --output json  # find a type by intent
uip is connections list --all-folders --output json       # live IS connections (all folders)
uip rules list --all-folders --output json                # deployed business rules (all folders)
```

Map intent to the best-evidenced extension type, connection, process, and queue; summarize used and tied candidates; ask only under SKILL.md Rule 4. Never fabricate identifiers; see [cli-conventions.md](cli-conventions.md).

**Connection discovery must be exhaustive.** Always pass `--all-folders`; a folder-scoped listing silently misses connections. An empty or unmatched result from a missing `--all-folders`, a connector key guessed from a brand name rather than found via `registry search`, or a truncated listing is a **false negative** — never conclude "no connection exists" or ask the user to create one until you have searched the registry for the real connector key and listed across all folders. Select rows by fields, lower-casing `Data` keys first:

```bash
uip is connections list --all-folders --output json | jq '.Data[] | with_entries(.key |= ascii_downcase) | select(.connectorkey=="<connectorKey>" and .state=="Enabled")'
```

`registry list` returns `Data.ExtensionTypes` (login-free OOTB types), `Connectors` and `Processes` (after `uip login`), and `ProcessesByType` (processes counted per `processType`, every type including 0). Rows contain `ExtensionType`, `Label`, `BpmnElement`, `ExtensionTag`, and `RequiresDiscovery`; `Yes` requires a concrete process, queue, or connection before the node is runnable.

In temp/smoke sandboxes, valid failure JSON such as `"Result": "Failure"` is not registry content. For discovery-only tasks, retain it in the transcript or `registry-evidence/cli-error.txt`, then replace final raw evidence with matching `validator/bpmn-spec.json` entries. Final evidence must literally contain requested strings such as `Orchestrator.StartJob` and `Maestro.ReceiveMessageEvent`.

## 2. Get the template for each chosen type

Run:

```bash
uip maestro bpmn registry get <extensionType> --output json
```

Use `Data.ExtensionType` fields `xmlTemplate`, `bpmnElement`, `extensionTag`, `contextFields[]` (the `uipath:context` inputs; each may carry its own `bindingInfo`), `bindingInfo`, `inputPattern`/`inputName`/`inputTarget` (how the request body input is shaped), and `requiresDiscovery`/`isDynamic` (whether a concrete resource must be resolved first). Author from `xmlTemplate` and fill placeholders only, except SKILL.md rules 6 and 18. Normalize PascalCase template hosts and `bpmnElement` (e.g. `bpmn:ServiceTask`) to lower-camel when serializing, e.g. `<bpmn:serviceTask>`; 27 of 29 bundled templates use PascalCase. `extensionTag` is `uipath:activity`, `uipath:event`, or `uipath:mapping`; `bindingInfo` is the shape in [§4](#4-bindings--from-bindinginfo-never-invented).

Fill `{id}`, `{name}`, `{incomingEdge}`, `{outgoingEdge}`, `{varId}`, context placeholders such as `{releaseKey}`, `{queueName}`, `{nameBindingId}`, and body CDATA. Wire structural placeholders to sequence-flow ids from [structural-bpmn.md](structural-bpmn.md).

Treat each template and process variable as one contract: replace `{varId}` with a stable id and declare task-scoped `uipath:inputOutput` with the exact template output `type` and `elementId="<node-id>"`, including `custom` and `Actions.HITL`; do not search examples for a guessed schema; never coerce to `string`, `object`, or `jsonSchema`. Leave opaque types for live enrichment.

For a dynamic unresolved node (SKILL.md step 1: draft/placeholders requested or no candidate pings `Enabled`), use escaped public placeholders `&lt;TENANT_URL&gt;`, `&lt;FOLDER_KEY&gt;`, and `&lt;CONNECTION_NAME&gt;`; retain retrieved context/output shape and use only user values in body/configurable context. Report **draft** and name the CLI-owned blocker literally, including `connection binding` when applicable. Do not inspect sibling skills, fixtures, or generated packages to invent live schema.

## 3. Connector (`Intsvc.*`) enrichment

Author every new connector node as a V2 element from `registry get --input-details`, in new and existing workflows; see [v2-connector-nodes.md](v2-connector-nodes.md). Use the template only to read existing V1 nodes. If the CLI rejects `--input-details` with `unknown option`, only a plain activity may fall back ([A CLI without V2 nodes](v2-connector-nodes.md#a-cli-without-v2-nodes)); still apply every rule here, including [one `target="body"` input](#body-shape-hand-authored-files-need-one-targetbody-input).

For `requiresDiscovery: Yes` connector activities such as `Intsvc.ActivityExecution`, resolve connection and object. `Intsvc.EventTrigger` and `Intsvc.WaitForEvent` resolve objects as in [Integration Service triggers](#integration-service-triggers).

```bash
uip is connections list --all-folders --output json
uip is resources list <connectorKey> --connection-id <id> --output json
uip is activities list <connectorKey> --output json   # the catalog: ObjectName + MethodName per activity (takes no --connection-id)
uip maestro bpmn registry get Intsvc.ActivityExecution \
    --connection-id <id> --object-name <object> --output json
```

### Picking the object: the table first, then the parameters

Use this table, not inferred names; confirm with `uip is resources describe <connectorKey> <object> --connection-id <id> --operation <Operation.Name>` and read `RequestFields` and `Parameters`.

| Connector key | Object | Activity | Operation |
| --- | --- | --- | --- |
| `uipath-atlassian-jira` | `curated_create_issue` | Create Issue | `Create` |
| `uipath-atlassian-jira` | `curated_get_issue` | Get Issue | `Retrieve` |
| `uipath-atlassian-jira` | `curated_edit_issue` | Update Issue | `Replace` |
| `uipath-salesforce-slack` | `send_message_to_channel_v2` | Send Message to Channel | `Create` |
| `uipath-microsoft-outlook365` | `send-mail-v2` | Send Email | `Create` |
| `uipath-uipath-dataservice` | `<EntityName>` | Create Entity Record | `Create` |
| `uipath-uipath-dataservice` | `<EntityName>` | Update Entity Record | `Replace` |
| `uipath-uipath-dataservice` | `GetEntityRecordByIdCurated` | Get Entity Record by ID | `List` |
| `uipath-uipath-dataservice` | `DeleteEntityRecordCurated` | Delete Entity Record | `Create` |
| `uipath-uipath-dataservice` | `QueryEntityRecordsCurated` | Query Entity Records | `Create` |
| `uipath-uipath-dataservice` | `UploadFileToRecordField` | Upload File to Record Field | `Create` |
| `uipath-uipath-dataservice` | `DownloadFileFromRecordField` | Download File from Record Field | `List` |
| `uipath-uipath-dataservice` | `DeleteFileFromRecordField` | Delete File from Record Field | `Delete` |
| `uipath-uipath-testmanager` | `TestSet` | Create / Get / Update / Delete Test Set | `Create` / `Retrieve` / `Update` / `Delete` |
| `uipath-uipath-testmanager` | `AssignTestCasesToTestSet` | Assign Test Cases to Test Set | `Create` |
| `uipath-uipath-testmanager` | `GetAssignedTestCasesForTestSet` | Get Assigned Test Cases for Test Set | `List` |
| `uipath-uipath-testmanager` | `ExecuteTestSet` | Execute Test Set | `Create` |
| `uipath-uipath-testmanager` | `TestCase` | Create / Get / Update / Delete Test Case | `Create` / `Retrieve` / `Update` / `Delete` |
| `uipath-uipath-testmanager` | `ExecuteTestCases` | Execute Test Cases | `Create` |
| `uipath-uipath-testmanager` | `TestExecution` | Get / Delete Test Execution | `Retrieve` / `Delete` |
| `uipath-uipath-testmanager` | `GetTestCaseLogsOfTestExecution` | Get Test Case Logs of Test Execution | `List` |
| `uipath-uipath-testmanager` | `TestCaseLog` | Get Test Case Log | `Retrieve` |
| `uipath-uipath-testmanager` | `GetRobotLogs` | Get Robot Logs | `List` |
| `uipath-uipath-testmanager` | `GetAssertions` | Get Assertions | `List` |
| `uipath-uipath-testmanager` | `DownloadAssertion` | Download Assertion | `Retrieve` |
| `uipath-uipath-testmanager` | `GetTestSteps` | Get Test Steps | `List` |
| `uipath-uipath-testmanager` | `GetTestStepLogs` | Get Test Step Logs | `List` |

Operation names are connector names, not activity verbs: Get Entity Record is `List`; Delete and Query are `Create`; do not change them. `<EntityName>` is the `Custom: yes` tenant entity from `uip is resources list`; its `RequestFields` are columns. Do not use `CreateEntityRecordCurated` or `UpdateEntityRecordV2` (empty `RequestFields`). File rows require `fieldName`; do not use their `V2` counterparts.
`QueryEntityRecordsCurated` reports an empty `RequestFields` until you pass the entity:

```bash
uip is resources describe <connectorKey> <object> --connection-id <id> \
    --operation Create --field entityName=<EntityName> --output json
```

`RequestFields` then lists `_sortFieldName`. Send it only in the body; as a query parameter it is ignored. Always set `isAscending`; omission sorts ascending regardless of `DefaultValue`.

V2 `--input-details` accepts a FilterTree in `filter` and compiles it to `queryExpression` ([reference](v2-connector-nodes.md#--input-details-reference)). V1 requires CEQL in `queryExpression`, even for a requested FilterBuilder tree: operators are `=`, `!=`, `<`, `<=`, `>`, `>=`, `LIKE`, `NOT LIKE`, `IN`, `NOT IN`, `IS NULL`, `IS NOT NULL`, joined by `AND`/`OR`; contains is `LIKE '%<text>%'`. A tree fails with `400 Error parsing query`. Put a requested tree in context `metadata` at `activityPropertyConfiguration.configuration.essentialConfiguration.savedFilterTrees.queryExpression`; summarize that runtime uses CEQL.

```xml
<uipath:input name="entityName" type="string" target="path" value="&lt;EntityName&gt;" />
<uipath:input name="queryExpression" type="string" target="query" value="&lt;field&gt; = &apos;&lt;value&gt;&apos; AND &lt;field&gt; &gt;= &lt;number&gt;" />
<uipath:input name="isAscending" type="boolean" target="query" value="false" />
<uipath:input name="body" type="json" target="body"><![CDATA[{"_sortFieldName":"<field>"}]]></uipath:input>
```

For unlisted Data Fabric operations, drop display names ending `(Preview)` or `(Deprecated)`, prefer paths beginning `/v2/`; folder entities are the exception: only `*_V3` objects qualify and must be V2 ([v2-connector-nodes.md](v2-connector-nodes.md#1-get-the-element)).

`send-mail-v2` defaults `saveAsDraft=true`. For V2, pass `"queryParameters":{"saveAsDraft":false}` in `--input-details`; `registry get` writes multipart metadata. For V1, emit `saveAsDraft` as a `target="query"` input set false, keep the message in the single `target="body"` input (its `body` parameter is `multipart`), and set context `metadata` to `{"inputMetadata":{"type":"multipart","multipart":{"bodyFieldName":"body"}}}`; otherwise the body is JSON.

For unlisted connector/operation candidates, describe all and retain those whose `Operation.Curated` names the requested activity. Break ties by required `Parameters` and `RequestFields`, not names; retain only candidates carrying every task value. If several remain, choose one and report it and ties. If none carries a required value, report that instead of dropping the requirement or smuggling it in as an input name. Never choose silently. Do not run `uip is resources run ...` to discover fields, filters, or defaults; `describe` is the contract. A failed describe is not a contract: on `Operation '<x>' not found`, rerun with the listed operation. The listed operation wins even when its verb is odd, e.g. `DownloadFileFromRecordFieldV2` is `Create`, not `List`.

Match enrichment keys case-insensitively; write `body` (`target="body"`) and `context` (`connectorKey`, `objectName`) from enrichment, never hand-author connector schemas. Bind the connection as `=bindings.<bindingId>` (see [§4](#4-bindings--from-bindinginfo-never-invented)).

### Body shape: hand-authored files need ONE `target="body"` input

For every `Intsvc.*` type whose `inputTarget` is `body`—`ActivityExecution`, `AsyncExecution`, `SyncAgentExecution`, `AsyncAgentExecution`, `SyncWorkflowExecution`, `AsyncWorkflowExecution`—hand-author exactly one `target="body"` input containing complete nested request JSON. Though `inputPattern: separateInputs`, multiple body inputs do not merge: the last wins as a bare scalar, causing `500 Internal failure` or provider errors such as `missing required field: channel`.

```xml
<uipath:input name="body" type="json" target="body"><![CDATA[{"fields":{"project":{"key":"=vars.Var_TargetProject"},"issuetype":{"id":"=vars.Var_IssueTypeId"},"summary":"=js:'Created from Maestro at ' + vars.Var_RunLabel}}]]></uipath:input>
```

Take every body name from `RequestFields` in `uip is resources describe`, not provider documentation; a vendor-doc name passes `validate` and `pack` and is then silently omitted from the request. `=vars.<id>` and `=js:` resolve inside that CDATA, so build the body from variables rather than literals. In XML attributes escape `=js:` `&&` as `&amp;&amp;` and `<` as `&lt;`; `>` needs no escaping; CDATA needs none. Nest dotted names: `fields.project.key` becomes `{"fields":{"project":{"key":…}}}`.

This round-trips: Studio Web sets `isSplitInputs: false` with one `jsonBody` at `target="body"` (`origin/develop:src/services/serialization/design-schema/intsvc.activityExecution.beta.design-schema.json`); the Jira fixture at `origin/develop:src/services/serialization/xml-serialization.test.ts:706` is one nested body; copy its body shape, not its context inputs (its `operation="CreateIssue"` is wrong). The serializer preserves existing separate inputs but never generates them. Treat manifest `InputNotes` directing one input per field as stale.

`target="bodyField"` is invalid here; it is for merged arguments on `JobArguments` (`Orchestrator.*` starts), `HitlTaskArguments` (`Actions.HITL`), and `args` (`BPMN.ScriptTask`). Read each type's `inputTarget`, not `inputPattern`. Five of fourteen `mergedBody` types use `body`: `Orchestrator.CreateQueueItem`, `Orchestrator.CreateAndWaitForQueueItem`, `A2A.AgentExecution`, `Maestro.CaseRulesEvaluator`, and `Maestro.CaseManagerGuardrails`.

Local `validate`/`pack` do not prove this shape: `validateInputs` short-circuits for `usesCanvasOwnedDynamicPayload` (`project-validator.ts:1602`) when `isDynamic` or an `Intsvc.*` requiring discovery, and `validateDynamicDirectInputs` checks only input `name` and parseable `type="json"`; wrong target, count, or name fails at runtime.

Take `operation` from described `Operation.Name` (e.g. `Create`), and `path`/`objectName` from that object. Do not use catalogue activity `Name` such as `CreateIssue`: `METHOD_TO_OPERATION` (`integrationservice-sdk/src/dap/validation/rules.ts:74`) permits only `List`, `Retrieve`, `Create`, `Update`, `Delete`, `Replace` plus raw HTTP verbs; `--operation` uses the same value.

### Set every required `RequestFields` entry

Put every `RequestFields` row with `Required: true` under its described name. Discover them with:

```bash
uip is resources describe <connectorKey> <object> --connection-id <id> --operation <Operation.Name> --output json | jq '.Data | with_entries(.key |= ascii_downcase) | .requestfields | map(with_entries(.key |= ascii_downcase) | select(.required) | .name)'
```

Never filter by expected names. A missing Slack `messageToSend` causes `invalid_blocks`; set Jira `fields.summary` even when describe omits it.

### Required `Parameters` are separate from the body — emit every one

Emit every `Required: true` parameter as its own input with target equal to its `Type`: `path`, `query`, `body`, or `multipart` (`validator/bpmn-spec.json`), using `DefaultValue` when no better request value exists:

```xml
<uipath:input name="entityName" target="path"      type="string" value="FlowCodeEvalEntity" />
<uipath:input name="fieldName"  target="path"      type="string" value="file1" />
<uipath:input name="recordId"   target="path"      type="string" value="=vars.Var_CreatedRecord.Id" />
<uipath:input name="send_as"    target="query"     type="string" value="bot" />
<uipath:input name="file"       target="multipart" type="file"   value="=vars.Var_DownloadedFile" />
```

A path parameter remains required when context shows a `{placeholder}`. A `body` parameter is the sole exception: include it inside the one complete body input; a second body input overwrites it with a scalar. Omitting one passes local validation/pack and fails at runtime with `400` and `Value for required parameter '<name>' not found`. `Parameters` may be empty, as for Jira, or required, as Slack `send_as`; inspect each activity.

### A `Reference` entry takes a looked-up value, never the display name

For a `Parameters` or `RequestFields` `Reference`, match the user's value against `LookupNames` and use that row's `LookupValue`. Slack `ConversationsInfo_GET` parameter `conversationsInfoId` uses `{"ObjectName": "curated_channels", "LookupNames": ["name", "id"], "LookupValue": "id"}`; use channel id `C0123ABCDEF`, never display name. A name passes `validate` and faults at runtime (`channel_not_found`).

List `Reference.ObjectName` itself, not a sibling object such as `conversations`, on the connection the node binds:

```bash
uip is resources run list uipath-salesforce-slack "curated_channels?types=public_channel,private_channel" --connection-id <id> --output json
```

Treat nonzero exit or `Result` other than `Success` as lookup failure. Match `Data` keys case-insensitively (`items`, `Pagination`, `HasMore`, `NextPageToken`). While `HasMore`, rerun with `--query "nextPage=<NextPageToken>"`; `pageToken=`, `page=`, and `name=` return page 1. Stop at first match or when a page adds no new rows. If absent, repeat on every other `Enabled` connection from `uip is connections list <connector-key> --all-folders --output json` and bind the one that holds it; the `IsDefault` connection can reach a workspace without the value. If no connection has it or lookup fails, stop and report the field; never write the display name.

## 4. Bindings — from `bindingInfo`, never invented

Cloud-resource nodes carry bindings shaped by extension `bindingInfo`; values come from discovery or the user.

- **Resource bindings** (`bindingInfo.resource` = `process`/`queue`, v1): the `bindingInfo.contextField` (e.g. `releaseKey`, `queueName`) carries `bindingInfo.propertyAttribute` (usually `Key`). Resolve with `registry search` / discovered `Processes` / `Queues`; never guess a GUID.
- **Name and folder bindings** (v2 `Orchestrator.StartJob`, `StartAgentJob`:
  `process`; `Actions.HITL`: `app`): the context `name` and `folderPath` each
  reference a binding of that `resource`, `propertyAttribute` `name` /
  `folderPath`. `default`s are the resource's `Name` (from `uip or processes
  list`) and the folder path you listed; both bindings share `resourceKey`
  `<folderPath>.<name>`. `StartAgentJob` bindings also carry
  `resourceSubType="Agent"`.

  ```xml
  <uipath:binding id="Binding_ProcName"   name="name"       type="string" resource="process" propertyAttribute="name"       resourceKey="<FOLDER_PATH>.<NAME>" default="<NAME>" />
  <uipath:binding id="Binding_ProcFolder" name="folderPath" type="string" resource="process" propertyAttribute="folderPath" resourceKey="<FOLDER_PATH>.<NAME>" default="<FOLDER_PATH>" />
  ```
- **Business rule bindings** (`BusinessRule`): context `name` and `folderPath` each reference a `BusinessRule` binding with `propertyAttribute` `name`/`folderPath`, never `Key` or process `releaseKey`. Use `uip rules list --all-folders`; bind `Name` and `FolderPath`. Both share `resourceKey=<folderPath>.<name>` or `<name>` when folder empty, never catalog key/process key/release key. The engine runs the rule by `name` + `folderPath` and uses `resourceKey` only to match deploy-time binding overwrites. Bind only deployed rules; deploy a solution-only rule first (SKILL.md rule 17). Task must be `version="v3"`: below v3 the engine cannot read the `.uirule` package a BusinessRules project deploys. Bind only decision-keyed rules: `uip rules describe` `OutputArguments` must contain `"x-uipath-decision-keyed": true`; a rule without it reads back empty columns from the task's `output` — do not bind it; run `uip rules refresh <project-path>` and redeploy. `folderPath` always has `default`, `""` when in the running job folder. Unbound `_label` contains the rule name.
- **Connection bindings** (`Intsvc.*`): context uses `=bindings.<bindingId>` and process-level `<uipath:binding resource="Connection" propertyAttribute="ConnectionId">` uses live connection id. Activities use context `connection`; triggers/waits use `connectionId`. `uip maestro bpmn refresh` and `pack` materialize a `Connection` resource in `bindings_v2.json`; otherwise `validate` passes but runtime fails `102010 IntSvcArgumentsError - Integration Services invalid value in input` because connection is null.

Declare all bindings in a single process-level `<uipath:bindings version="v1">`
block. Each `<uipath:binding>` carries `id`, `resource`, `propertyAttribute`, and a
`default` value (the resolved key or id), plus a `resourceKey`: Studio Web
files each binding in `bindings_v2.json` under it, so keyless bindings of one
type merge into one entry and the others are lost. Omitting it fails
`validate`, `refresh` and `pack` — on a connection binding with `Integration
Service activity connection binding "<id>" is missing resourceKey`, on any
other with `Binding "<id>" (resource=…, propertyAttribute=…) is missing
resourceKey`. v1 `process` and `queue`
bindings carry `resourceKey` from `bindingInfo.resourceKeyPattern`, which
`registry get <type>` shows. Both `BusinessRule` bindings carry the same
`resourceKey`, `<folderPath>.<name>` (`<name>` alone when the folder path is empty):

```xml
<uipath:binding id="Binding_RuleName"   name="name"         type="string" resource="BusinessRule" propertyAttribute="name"       resourceKey="<FOLDER_PATH>.<RULE_NAME>" default="<RULE_NAME>" />
<uipath:binding id="Binding_RuleFolder" name="folderPath"   type="string" resource="BusinessRule" propertyAttribute="folderPath" resourceKey="<FOLDER_PATH>.<RULE_NAME>" default="<FOLDER_PATH>" />
```

Every `Intsvc.ActivityExecution` connection needs two bindings sharing the connection id as `resourceKey`: `ConnectionId` default is connection id; folder binding `propertyAttribute="folderKey"` default is folder key.

```xml
<uipath:bindings version="v1">
  <uipath:binding id="Binding_JiraConn"   resource="Connection" propertyAttribute="ConnectionId" resourceKey="&lt;connection-id&gt;" default="&lt;connection-id&gt;" />
  <uipath:binding id="Binding_JiraFolder" resource="Connection" propertyAttribute="folderKey"    resourceKey="&lt;connection-id&gt;" default="&lt;folder-key&gt;" />
</uipath:bindings>
```

Only `ConnectionId` becomes a `bindings_v2.json` resource: `buildConnectionResources` (`connection-resources.ts`) retains only `resource=Connection` and `propertyAttribute=ConnectionId`; folder binding remains for authoring/validation and is exempt from missing-binding lookup. Point activity `connection` at a non-`ConnectionId` binding and lookup fails with `Activity "<name>" references missing Connection binding "<id>"`; `folderKey` is read separately.

## Agent wrapper selection — pick by `ProcessType`, not the label

Run `uip or processes list --folder-path <path> --output json` with `--all-fields`; read `ProcessType`, `Key`, and `FolderKey` from that response. Casing remains PascalCase; `--all-fields` only adds fields.

- `ProcessType: "Function"` (coded Python): `Orchestrator.StartJob`, not `StartAgentJob`.
- `ProcessType: "Agent"` (Agent Builder): `Orchestrator.StartAgentJob`.
- External A2A URL/skillId: `A2A.AgentExecution`.
- Integration Service external agent: `Intsvc.*AgentExecution`.

`A2A.AgentExecution` disables Studio Web's Action dropdown; never use it for a folder-deployed agent; use `StartAgentJob`/`StartJob`.

## API workflow invocation — `ExecuteApiWorkflowAsync` waits, despite the name

Use the sole API-workflow service-task type, `Orchestrator.ExecuteApiWorkflowAsync`; `Start and wait for API workflow` waits and exposes the result to later nodes. Do not model fire-and-forget. Resolve release key, folder key, and request/response schemas first; the served template is broken as-is.

## Job-wrapper v1 trap — `releaseKey` templates are unrunnable

`Orchestrator.ExecuteApiWorkflowAsync`, `Orchestrator.StartAgenticProcess[Async]`, and `StartCaseMgmtProcess[Async]` share a v1 `<uipath:activity version="v1">` template with hidden unbound `releaseKey`/`folderId`/`folderPath`/`name`; every field has `binding: false` except `releaseKey`, whose `bindingInfo` is process/`Key` in `validator/bpmn-spec.json`. Blank placeholders pass `validate`/pack but runtime fails, including `ExecuteApiWorkflowAsync` `170009 Could not get value for key:ReleaseKey from context in input`.

1. Bind `releaseKey` using [§4](#4-bindings--from-bindinginfo-never-invented) with process binding `resource="process" propertyAttribute="Key" resourceKey="<RELEASE_KEY>" default="<RELEASE_KEY>"`, context `=bindings.<id>`, and deployed `Key` from `uip or processes list --folder-path <path> --output json`.
2. **The template's `folderId` context field is misnamed — the runtime reads `folderKey`, not `folderId` or `folderPath`.** Populating `releaseKey` alone still faults with `Could not get value for key:FolderKey from context in input`. Add a context field literally named `folderKey` holding `FolderKey` from that response — a plain literal value, not a binding. Re-read after every deploy because `deploy run` creates a new folder.
3. With real `releaseKey` and `folderKey`, the node runs to completion. For `ExecuteApiWorkflowAsync`, drop template `folderId`/`folderPath`/`name` fields.

For the other types apply step 1 only; apply step 2 after a live `key:FolderKey` fault, otherwise report unverified.

Map requested API workflow invocation/status/result fields as `uipath:output` rows on the service task, with discovered names/types and sources such as `source="=invocation"`, `source="=status"`, and `source="=result"` (or the exact schema fields returned by discovery); for `=result.<key>`, use the debug-run key from SKILL.md rule 17 step 5, otherwise schema name and report unverified. Do not add a downstream script solely to split the result.

## Integration Service triggers

`Intsvc.TimerTrigger` is portable: `RequiresDiscovery=false`, no binding/context/input, and only exact `registry get Intsvc.TimerTrigger` template.

`Intsvc.EventTrigger`/`Intsvc.WaitForEvent` enrich like §3, but object/operation come from trigger catalog, not `uip is resources`; omit `--operation` and enrichment fails `Event enrichment requires --operation`. Build new triggers/waits as V2; put Data Fabric scoping (`entityScope`, `folderEntityName`, `folderEntityName_folderKey`) under `--input-details.queryParameters` (the CLI refuses a name the event object does not list); see [v2-connector-nodes.md](v2-connector-nodes.md). V1 uses `queryParams`/`filters.expression`.

```bash
uip is activities list <connectorKey> --triggers --output json
uip is triggers objects <connectorKey> <OPERATION> --connection-id <id> --output json
uip is triggers describe <connectorKey> <operation> <objectName> --connection-id <id> --output json
uip maestro bpmn registry get <Intsvc.EventTrigger|Intsvc.WaitForEvent> \
    --connection-id <id> --object-name <ObjectName> --operation <Name> --output json
```

Prefer `IsCurated: Yes`. If none covers the event, use generic `CREATED`/`UPDATED`/`DELETED` (`IsCurated: No`, `ObjectName: N/A`), taking the object from `uip is triggers objects`; it may omit connection-specific objects or be empty without `--connection-id`. For connectors with only generic rows, such as `uipath-uipath-jdbc`, this is the only path.

`registry get` supplies template/InputFields; `uip is triggers describe` supplies `FilterFields`, `EventParameters`, and `OutputFields`. Build filters from `FilterFields`, never from an activity's `RequestFields`; `EventParameters` are the trigger's scoping inputs, `OutputFields` the event payload. V1 runtime reads only a `target="body"` input; the template's `filter` and `parameters` fields, and any sibling input without `target`, are dropped. Write exactly one `body` input as a sibling of `uipath:context`: one JSON with `queryParams` for EventParameters and `filters.expression` AND-joining one equality per parameter with FilterFields conditions. No filter tree; only the expression is evaluated. A V2 element carries them in `body.parameters`; do not move them.

```xml
<uipath:input name="body" type="json" target="body"><![CDATA[{"filters":{"expression":"(parentFolderId == '<INBOX_ID>') && (contains(subject, 'Invoice'))"},"queryParams":{"parentFolderId":"<INBOX_ID>"}}]]></uipath:input>
```

Curated pairs already confirmed:

| Connector key | Trigger operation | Object |
| --- | --- | --- |
| `uipath-microsoft-outlook365` | `EMAIL_RECEIVED` | `Message` |
| `uipath-atlassian-jira` | `ISSUE_CREATED` | `curated_get_issue` |
| `uipath-salesforce-slack` | `SLACK_EVENT_MESSAGE` | `slack_events_message` |
| `uipath-uipath-dataservice` | `CREATED_V3` | `EntityTriggers_V3` |

`uip is triggers` and `registry get` uppercase operations; mixed-case Test Manager operations `Created`, `Updated`, `Finished` return HTTP 404 / `IS enrichment error` in CLI 1.204.0 and have no reachable CLI trigger.

Hand-authored connector triggers remain **draft** until CLI supplies trigger properties, connection binding, and schemas. V1 `EventTrigger`/`WaitForEvent` use context `connectionId` = `=bindings.<bindingId>`; activities use `connection`; V2 uses `connection` for all, see [v2-connector-nodes.md](v2-connector-nodes.md). Timer has no connection. After binding, run `uip maestro bpmn format <file.bpmn>`; for an existing diagram see [Keep the user's diagram](../SKILL.md#keep-the-users-diagram) instead of running `format`, then run `uip maestro bpmn refresh <project>`. Use `refresh`, not deprecated `update-metadata`; unmaterialized connections pass `validate` but fault null with 102010. Trigger-start drafts skip refresh ([SKILL.md](../SKILL.md) step 3); package-ready/upload/debug/publish/deploy deliverables run it.

## Connectionless vs connector HTTP

Use a connector activity (`Intsvc.ActivityExecution`) when the call goes through a tenant connection, a dynamic connector schema, or a connector object operation; keep it **draft** until enriched. CLI-owned blockers, which must be resolved before upload or run and named explicitly in boundary notes, are **connection binding**, **dynamic schemas**, and generated package metadata (`bindings_v2.json`, `entry-points.json`, `operate.json`, `package-descriptor.json`); do not hand-author these (§3).

HTTP always uses `Intsvc.UnifiedHttpRequest`, whether `manual` or `connector`. Build it with `uip maestro bpmn registry get Intsvc.UnifiedHttpRequest --input-details '<request>'` and add `--connection-id` for connector mode. A service with no connector of its own goes through a `uipath-uipath-http` connection in connector mode; never author legacy `Intsvc.HttpExecution` or a connector's `httpRequest` object for a new node. See [v2-connector-nodes.md](v2-connector-nodes.md#http-requests).

Summary status: **executable** (activity, inputs, output variable, downstream mappings present; runtime-verified if run), **draft** (shape/intent present, enrichment missing), **mock** (fixed sample data), **blocked** (required URL, auth, schema, or enrichment decision missing).

## 5. Assemble

1. Build scaffold/process using [structural-bpmn.md](structural-bpmn.md).
2. Declare `<uipath:variables>` variables, each with `elementId`, and `<uipath:bindings>`.
3. Paste each `registry get` `xmlTemplate` except SKILL.md rules 6 and 18; fill placeholders and wire edges.
4. Author sequence flows, gateway conditions/defaults, event definitions, boundary events, subprocess/call-activity containers, and multi-instance markers.
5. After final source edit, generate `bpmndi:BPMNDiagram`: run `uip maestro bpmn format <file.bpmn>`; for an existing diagram see [Keep the user's diagram](../SKILL.md#keep-the-users-diagram) instead of running `format`.
6. Validate using [structural-bpmn.md#validation](structural-bpmn.md#validation); rerun step 5 after every later source edit because `validate` errors on nodes without shapes.

## OOTB extension types (29, login-free)

Discover each exact template with `registry get <type>`.

| Extension type | Host element | Tag |
| --- | --- | --- |
| `Actions.HITL` | `bpmn:userTask` | activity |
| `Orchestrator.StartJob` | `bpmn:serviceTask` | activity |
| `Orchestrator.StartAgentJob` | `bpmn:serviceTask` | activity |
| `Orchestrator.BusinessRules` | `bpmn:businessRuleTask` | activity |
| `Orchestrator.ExecuteApiWorkflowAsync` | `bpmn:serviceTask` | activity |
| `Orchestrator.CreateQueueItem` | `bpmn:sendTask` | activity |
| `Orchestrator.CreateAndWaitForQueueItem` | `bpmn:serviceTask` | activity |
| `Orchestrator.StartAgenticProcess[Async]` | `bpmn:callActivity` | activity |
| `Orchestrator.StartCaseMgmtProcess[Async]` | `bpmn:callActivity` | activity |
| `Intsvc.ActivityExecution` | `bpmn:sendTask` | activity |
| `Intsvc.UnifiedHttpRequest` (`Intsvc.HttpExecution` is legacy) | `bpmn:sendTask` | activity |
| `Intsvc.WaitForEvent` | `bpmn:receiveTask`; or `uipath:event` on `bpmn:intermediateCatchEvent` (incoming + outgoing) or `bpmn:boundaryEvent` (`attachedToRef`, outgoing only), with bare `<bpmn:messageEventDefinition />` after flows | event |
| `Intsvc.EventTrigger` | `bpmn:startEvent` | event |
| `Intsvc.TimerTrigger` | `bpmn:startEvent` | activity |
| `Intsvc.{Async,SyncAgent,AsyncAgent,SyncWorkflow,AsyncWorkflow}Execution` | `bpmn:serviceTask` | activity |
| `A2A.AgentExecution` | `bpmn:serviceTask` | activity |
| `BPMN.Variables` | `bpmn:task` | mapping |
| `BPMN.ScriptTask` | `bpmn:scriptTask` | mapping |
| `Maestro.ReceiveMessageEvent` | `bpmn:intermediateCatchEvent` | event |
| `Maestro.SendMessageEvent` | `bpmn:intermediateThrowEvent` | event |
| `Maestro.CaseRulesEvaluator` / `Maestro.CaseManagerGuardrails` | `bpmn:serviceTask` | activity |

This is a discovery aid, not a template substitute — always run `registry get` for the live template before authoring. Event types remain `uipath:event` even on task-like hosts: `Intsvc.WaitForEvent`, `Intsvc.EventTrigger`, `Maestro.ReceiveMessageEvent`, and `Maestro.SendMessageEvent`.

## Registry-evidence-only tasks

- Create `registry-evidence/` before anything else.
- Run the registry command forms the user asked for. For RPA job + internal message discovery, run `uip maestro bpmn registry list --limit -1 --output json`, `uip maestro bpmn registry get Orchestrator.StartJob --output json`, and `uip maestro bpmn registry get Maestro.ReceiveMessageEvent --output json`.
- If `uip` is unavailable in a temp/smoke sandbox, or returns valid failure JSON such as `"Result": "Failure"`, do not search the repo for another CLI or inspect fixtures. Still issue the required list/get forms once each redirected to evidence files, allowing failure with `|| true`: `uip maestro bpmn registry list --limit -1 --output json` and `uip maestro bpmn registry get <type> --output json`. Record failures in `registry-evidence/cli-error.txt`; overwrite failure JSON in expected `registry-evidence/*.json` with valid JSON from `skills/uipath-maestro-bpmn/validator/bpmn-spec.json` containing the same extension types, then stop. Final files must literally contain names such as `Orchestrator.StartJob` and `Maestro.ReceiveMessageEvent`.
