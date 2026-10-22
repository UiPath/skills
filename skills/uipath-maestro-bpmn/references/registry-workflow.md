# Registry workflow

Every `uipath:*` payload in a Maestro `.bpmn` comes from the registry, never prose or hand-written XML. Turn intent into registry-backed XML as follows.

## 1. Sync and discover

Run:

```bash
uip maestro bpmn registry pull            # sync + cache (login for connectors/processes)
uip maestro bpmn registry list --limit -1 --output json   # all extension types
uip maestro bpmn registry search <keyword> --output json  # find a type by intent
uip is connections list --all-folders --output json   # live IS connections (all folders)
uip rules list --all-folders --output json            # deployed business rules (all folders)
```

Map intent to the best-evidenced extension type, connection, process, and queue; summarize the selections and any ties, and ask only under SKILL.md Rule 4. Never fabricate identifiers; see [cli-conventions.md](cli-conventions.md).

**Connection discovery must be exhaustive.** Always pass `--all-folders`. A missing flag, guessed brand-name connector key, truncated listing, or otherwise unmatched result is a **false negative**. Search the registry for the real connector key, list all folders, and do not conclude that no connection exists or ask the user to create one until then. Select rows by fields, never position; lower-case `Data` keys first because casing is not fixed:

```bash
uip is connections list --all-folders --output json | jq '.Data[] | with_entries(.key |= ascii_downcase) | select(.connectorkey=="<connectorKey>" and .state=="Enabled")'
```

`registry list` returns `Data.ExtensionTypes` (login-free OOTB types), `Connectors` and `Processes` (after `uip login`), and `ProcessesByType` (each process type, including zero counts). Each extension row has `ExtensionType`, `Label`, `BpmnElement`, `ExtensionTag`, and `RequiresDiscovery`; `Yes` requires a concrete process, queue, or connection before the node is runnable.

In temp/smoke sandboxes, valid JSON may be only a failure envelope such as `"Result": "Failure"`. For discovery-only work, preserve that output in the transcript or `registry-evidence/cli-error.txt`, then replace final raw evidence JSON with matching entries from `validator/bpmn-spec.json`. Saved evidence must literally contain requested types such as `Orchestrator.StartJob` and `Maestro.ReceiveMessageEvent`, not only the envelope.

## 2. Get the template for each chosen type

Run:

```bash
uip maestro bpmn registry get <extensionType> --output json
```

`Data.ExtensionType` supplies:

| Field | Use |
| --- | --- |
| `xmlTemplate` | Literal node XML with `{placeholder}` slots; author from it and fill placeholders only, except SKILL.md rules 6 and 18. |
| `bpmnElement` | PascalCase host model type; normalize this and the template host tag to lower-camel when serializing (`<bpmn:serviceTask>`). 27 of 29 bundled templates use PascalCase tags. |
| `extensionTag` | `uipath:activity`, `uipath:event`, or `uipath:mapping`. |
| `contextFields[]` | `uipath:context` inputs, each possibly with `bindingInfo`. |
| `bindingInfo` | Resource-binding shape; see §4. |
| `inputPattern` / `inputName` / `inputTarget` | Request-body shape. |
| `requiresDiscovery` / `isDynamic` | Whether to resolve a concrete resource first. |

Fill `{id}`, `{name}`, `{incomingEdge}`, `{outgoingEdge}`, `{varId}`, per-context placeholders (`{releaseKey}`, `{queueName}`, `{appId}`, …), and body CDATA. Wire structural placeholders to the sequence-flow IDs from [structural-bpmn.md](structural-bpmn.md).

Treat each template and process variable as one contract. Replace `{varId}` with a stable ID and declare task-scoped `uipath:inputOutput` with the template output's exact `type` and `elementId="<node-id>"`, including opaque `custom` and product-specific `Actions.HITL`; never coerce them to `string`, `object`, or `jsonSchema`. Enrichment supplies concrete typed rows later.

For a dynamic unresolved node (SKILL.md step 1: draft/placeholders requested or no candidate pings `Enabled`), use escaped public placeholders `&lt;TENANT_URL&gt;`, `&lt;FOLDER_KEY&gt;`, and `&lt;CONNECTION_NAME&gt;` in resource identity slots; retain retrieved context/output shape and only user-supplied body/configurable-context values. Report **draft** and name the CLI-owned blocker literally, including `connection binding` when applicable. Do not inspect sibling skills, fixtures, or generated packages to invent live schema.

## 3. Connector (`Intsvc.*`) enrichment

Author every new connector node as a V2 element from `registry get --input-details`, including existing workflows; see [v2-connector-nodes.md](v2-connector-nodes.md). Use the template to read existing V1 nodes. If the CLI rejects `--input-details` with `unknown option`, only a plain activity falls back to the template ([A CLI without V2 nodes](v2-connector-nodes.md#a-cli-without-v2-nodes)); apply every rule here, including [one `target="body"` input](#body-shape-hand-authored-files-need-one-targetbody-input) containing the entire request body.

For connector activity types (`requiresDiscovery: Yes`, e.g. `Intsvc.ActivityExecution`), resolve a live connection and object, then enrich. `Intsvc.EventTrigger` and `Intsvc.WaitForEvent` also require discovery but resolve objects as described in [Integration Service triggers](#integration-service-triggers).

```bash
uip is connections list --all-folders --output json   # pick a connection id + its connector (search all folders)
uip is resources list <connectorKey> --connection-id <id> --output json   # objects exposed by connector
uip is activities list <connectorKey> --output json   # ObjectName + MethodName; no --connection-id
uip maestro bpmn registry get Intsvc.ActivityExecution \
    --connection-id <id> --object-name <object> --output json
```

### Picking the object: the table first, then the parameters

Use this table, not display names or inferred object types: four Jira objects create an issue, and describe prints `Curated: "Create Issue"` for two of them because its summary drops the `curated.isHidden` flag that marks the live one. Confirm with `uip is resources describe <connectorKey> <object> --connection-id <id> --operation <Operation.Name>` and read `RequestFields` and `Parameters` from that call.

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

Operation names are the connector's, not the verb: Get Entity Record is `List`, Delete Entity Record and Query are `Create`; never substitute intuitive names.

For Data Service, `<EntityName>` is the tenant entity object (`Custom: yes`); its `RequestFields` are columns for Create/Update. Do not use `CreateEntityRecordCurated` or `UpdateEntityRecordV2` (empty `RequestFields`). File rows require `fieldName`; do not use their `V2` counterparts (no field parameter). Query requires:

```bash
uip is resources describe <connectorKey> <object> --connection-id <id> \
    --operation Create --field entityName=<EntityName> --output json
```

Then put `_sortFieldName` only in the body and always set `isAscending`; omitted means ascending regardless of `DefaultValue`. V2 compiles `--input-details` FilterTree `filter` into `queryExpression` ([reference](v2-connector-nodes.md#--input-details-reference)); V1 requires a CEQL string, even when the request specifies a FilterBuilder tree. Supported CEQL operators are `=`, `!=`, `<`, `<=`, `>`, `>=`, `LIKE`, `NOT LIKE`, `IN`, `NOT IN`, `IS NULL`, `IS NOT NULL`, joined by `AND` / `OR`; contains is `LIKE '%<text>%'`. A tree in `queryExpression` fails with `400 Error parsing query`. Put a requested tree in context `metadata` at `activityPropertyConfiguration.configuration.essentialConfiguration.savedFilterTrees.queryExpression` and summarize that runtime filtering uses CEQL.

```xml
<uipath:input name="entityName" type="string" target="path" value="&lt;EntityName&gt;" />
<uipath:input name="queryExpression" type="string" target="query" value="&lt;field&gt; = &apos;&lt;value&gt;&apos; AND &lt;field&gt; &gt;= &lt;number&gt;" />
<uipath:input name="isAscending" type="boolean" target="query" value="false" />
<uipath:input name="body" type="json" target="body"><![CDATA[{"_sortFieldName":"<field>"}]]></uipath:input>
```

For unlisted Data Fabric operations, drop display names ending `(Preview)` or `(Deprecated)` and prefer `/v2/`; folder entities are the exception: only `*_V3` objects qualify, authored as V2; see [v2-connector-nodes.md](v2-connector-nodes.md#1-get-the-element).

For `send-mail-v2`, default `saveAsDraft=true` would save rather than send. V2: pass `"queryParameters":{"saveAsDraft":false}` in `--input-details`; `registry get` writes multipart metadata. V1: add `target="query"` `saveAsDraft=false`, keep message in the single `target="body"` input (`body` parameter `multipart`), and set context `metadata` to `{"inputMetadata":{"type":"multipart","multipart":{"bodyFieldName":"body"}}}`.

For an unlisted connector/operation, describe every candidate and retain those whose `Operation.Curated` names the requested activity. Catalogs may expose plain, `V2`, `_V3`, and Jira's four variants. Break ties by `Parameters` and `RequestFields`: retain only candidates carrying every requested value. For example, only unsuffixed `UploadFileToRecordField` accepts `fieldName`; V2 accepts `entityName`, `recordId`, `file`, and `expansionLevel`. If several remain, pick one and report it and ties. If none exposes a required value, report that; do not drop it or smuggle it into an input name. Never pick silently.

`describe` is the contract. Never run `uip is resources run ...` to discover fields, filters, or defaults; it executes against the tenant. A failed describe is not a contract: if it says `Operation '<x>' not found`, use a listed operation and rerun. The listed operation wins even when odd (`DownloadFileFromRecordFieldV2` is `Create`, not `List`). Match enrichment keys case-insensitively. Write `body` (`target="body"`) and context (`connectorKey`, `objectName`) from enrichment; do not hand-author connector schemas. Reference the connection with `=bindings.<bindingId>`; see §4.

### Body shape: hand-authored files need ONE `target="body"` input

For every `Intsvc.*` type whose `inputTarget` is `body`—`ActivityExecution`, `AsyncExecution`, `SyncAgentExecution`, `AsyncAgentExecution`, `SyncWorkflowExecution`, `AsyncWorkflowExecution`—emit exactly one `target="body"` input containing the complete nested JSON request. Although `inputPattern: separateInputs` says one input per request field, multiple body inputs do not merge: the last wins as a bare scalar, causing `500 Internal failure` or missing-field errors such as Slack `missing required field: channel`.

```xml
<uipath:input name="body" type="json" target="body"><![CDATA[{"fields":{"project":{"key":"=vars.Var_TargetProject"},"issuetype":{"id":"=vars.Var_IssueTypeId"},"summary":"=js:'Created from Maestro at ' + vars.Var_RunLabel}}]]></uipath:input>
```

Use names from `RequestFields` in `uip is resources describe`, not provider docs. `=vars.<id>` and `=js:` resolve inside that CDATA at runtime, so build the body from variables rather than literals. In XML attributes escape `&&` as `&amp;&amp;` and `<` as `&lt;`; `>` need not be escaped; CDATA needs no such escaping. `target="bodyField"` is not valid here; it belongs to merged arguments on `JobArguments` (`Orchestrator.*` starts), `HitlTaskArguments` (`Actions.HITL`), and `args` (`BPMN.ScriptTask`). Read `inputTarget` per manifest type. Five of fourteen `mergedBody` types use `body`: `Orchestrator.CreateQueueItem`, `Orchestrator.CreateAndWaitForQueueItem`, `A2A.AgentExecution`, `Maestro.CaseRulesEvaluator`, and `Maestro.CaseManagerGuardrails`.

The single-input form is canonical: Studio Web sets `isSplitInputs:false` and one `jsonBody`; the Jira round-trip fixture asserts one nested body CDATA parse→serialize identity. The serializer preserves existing separate inputs but never generates them. Copy that fixture's body shape, not its context inputs; its `operation="CreateIssue"` is not authoritative. Treat the manifest's `InputNotes` as stale here rather than as the contract. Local `validateInputs` does not catch wrong targets/names/counts: `usesCanvasOwnedDynamicPayload` (`project-validator.ts:1602`) returns after `validateDynamicDirectInputs`, which checks only input names and parses `type="json"`; therefore `validate` and `pack` are not evidence of correct runtime shape.

Nest dotted names (`fields.project.key` → `{"fields":{"project":{"key":…}}}`), not a literal dotted key. Take `operation` from described `Operation.Name` (for example `Create`), and `path`/`objectName` from that object. The catalogue activity name such as `CreateIssue` cannot resolve: `METHOD_TO_OPERATION` (`integrationservice-sdk/src/dap/validation/rules.ts:74`) permits only `List`, `Retrieve`, `Create`, `Update`, `Delete`, `Replace` plus raw HTTP verbs. Use `--operation Create`.

### Set every required `RequestFields` entry

Put every `RequestFields` row with `Required: true` in the body under its described name. Discover them with:

```bash
jq '.Data | with_entries(.key |= ascii_downcase) | .requestfields | map(with_entries(.key |= ascii_downcase) | select(.required) | .name)'
```

Never filter by expected names. A missing Slack `messageToSend` causes `invalid_blocks`; set Jira `fields.summary` even when describe omits it.

### Required `Parameters` are separate from the body — emit every one

`Parameters` are alongside `RequestFields`; emit every `Required: true` parameter as its own input, with `target` equal to its `Type`: `path`, `query`, `body`, or `multipart` (`validator/bpmn-spec.json`). Use `DefaultValue` when no better value exists:

```xml
<uipath:input name="entityName" target="path"      type="string" value="FlowCodeEvalEntity" />
<uipath:input name="fieldName"  target="path"      type="string" value="file1" />
<uipath:input name="recordId"   target="path"      type="string" value="=vars.Var_CreatedRecord.Id" />
<uipath:input name="send_as"    target="query"     type="string" value="bot" />
<uipath:input name="file"       target="multipart" type="file"   value="=vars.Var_DownloadedFile" />
```

A path parameter is required even if context shows a `{placeholder}`. A `body` parameter is the exception: place it as a field in the one complete body input; a second body input loses the object. Omitting a required parameter passes local validation/pack and fails at runtime with `400` and `Value for required parameter '<name>' not found`. Check each activity; `Parameters` may be empty.

### A `Reference` entry takes a looked-up value, never the display name

For a `Parameters`/`RequestFields` `Reference`, match `LookupNames` to the user's value and use that row's `LookupValue`. Slack `conversationsInfoId` uses `{"ObjectName": "curated_channels", "LookupNames": ["name", "id"], "LookupValue": "id"}`; use channel ID (`C0123ABCDEF`), never its name. A name passes `validate` and faults at runtime (`channel_not_found`).

List `Reference.ObjectName` itself, not a sibling object such as `conversations`, on the bound connection:

```bash
uip is resources run list uipath-salesforce-slack "curated_channels?types=public_channel,private_channel" --connection-id <id> --output json
```

A nonzero exit or `Result` other than `Success` is lookup failure. Match `Data` keys case-insensitively (`items`, `Pagination`, `HasMore`, `NextPageToken`). While `HasMore` is true, rerun with `--query "nextPage=<NextPageToken>"`; `pageToken=`, `page=`, and `name=` return page 1 again. Stop at the first match or when a page adds no unseen rows. If no match, repeat on every other `Enabled` connection from `uip is connections list <connector-key> --all-folders --output json`; bind the one holding it. `IsDefault` may reach another workspace. If none holds it or lookup fails, stop and report the field; never write the display name.

## 4. Bindings — from `bindingInfo`, never invented

Cloud-resource nodes carry bindings whose shape comes from `bindingInfo` and whose values come from discovery/user input.

- **Resource bindings** (`bindingInfo.resource` = `process` / `queue`): the `bindingInfo.contextField` (`releaseKey`, `queueName`, etc.) holds `bindingInfo.propertyAttribute` (usually `Key`). Resolve with `registry search` / discovered `Processes` / `Queues`; never guess GUIDs.
- **Business rule bindings** (`BusinessRule`): context `name` and `folderPath` each use a `BusinessRule` binding with `propertyAttribute` `name` / `folderPath`, never a `Key` binding or a process `releaseKey`, even when `registry get` returns one. Find deployed rules using `uip rules list --all-folders`; use `Name` and `FolderPath`. Both use `resourceKey=<folderPath>.<name>` or `<name>` when folder is empty, never catalog entity key, process `Key`, or release key. Bind only deployed rules; deploy a solution-only rule first (SKILL.md rule 17). Task must be `version="v3"`. `OutputArguments` from `uip rules describe` must carry `"x-uipath-decision-keyed": true`; without it the task's `output` reads back empty columns; do not bind it — run `uip rules refresh <project-path>` on its project and redeploy it first. `folderPath` always has `default`, `""` when in the running job's folder. Unbound `_label` holds the rule name.
- **Connection bindings** (`Intsvc.*`): context uses `=bindings.<bindingId>`; process-level `<uipath:binding resource="Connection" propertyAttribute="ConnectionId">` contains the live connection ID. Activities use context `connection`; triggers/waits use `connectionId`. `uip maestro bpmn refresh` and `pack` materialize it in `bindings_v2.json`; without this, `validate` passes but runtime fails `102010 IntSvcArgumentsError - Integration Services invalid value in input`.

Declare one process-level `<uipath:bindings version="v1">`. Each binding has `id`, `resource`, `propertyAttribute`, and `default`; process/queue bindings also use `resourceKey` from `bindingInfo.resourceKeyPattern`; connections require `resourceKey` or `validate` fails with `Integration Service activity connection binding "<id>" is missing resourceKey`. BusinessRule bindings share the same resource key:

```xml
<uipath:binding id="Binding_RuleName"   name="name"         type="string" resource="BusinessRule" propertyAttribute="name"       resourceKey="<FOLDER_PATH>.<RULE_NAME>" default="<RULE_NAME>" />
<uipath:binding id="Binding_RuleFolder" name="folderPath"   type="string" resource="BusinessRule" propertyAttribute="folderPath" resourceKey="<FOLDER_PATH>.<RULE_NAME>" default="<FOLDER_PATH>" />
```

Every `Intsvc.ActivityExecution` connection needs two bindings sharing the connection ID as `resourceKey`: `ConnectionId` defaulting to the connection ID and `folderKey` defaulting to the folder key.

```xml
<uipath:bindings version="v1">
  <uipath:binding id="Binding_JiraConn"   resource="Connection" propertyAttribute="ConnectionId" resourceKey="&lt;connection-id&gt;" default="&lt;connection-id&gt;" />
  <uipath:binding id="Binding_JiraFolder" resource="Connection" propertyAttribute="folderKey"    resourceKey="&lt;connection-id&gt;" default="&lt;folder-key&gt;" />
</uipath:bindings>
```

Only `ConnectionId` becomes a `bindings_v2.json` resource: `buildConnectionResources` (`connection-resources.ts`) retains only `resource=Connection` and `propertyAttribute=ConnectionId`; the folder binding remains for authoring/validation. The activity's `connection` input must point to the `ConnectionId` binding; otherwise lookup misses and reports `Activity "<name>" references missing Connection binding "<id>"`. `folderKey` is read separately.

## Agent wrapper selection — pick by `ProcessType`, not the label

Choose by resource `ProcessType`, not display label. Run `uip or processes list --folder-path <path> --output json` with `--all-fields` and read `ProcessType`, `Key`, and `FolderKey` from the same response; casing remains PascalCase.

- `ProcessType: "Function"` (coded Python): `Orchestrator.StartJob`, not `StartAgentJob`.
- `ProcessType: "Agent"` (Agent Builder): `Orchestrator.StartAgentJob`.
- External A2A URL/skillId: `A2A.AgentExecution`.
- Integration Service external agent: `Intsvc.*AgentExecution`.

`A2A.AgentExecution` is an external A2A node and disables Studio Web's Action dropdown; never use it for a folder-deployed agent, which requires `StartAgentJob`/`StartJob`.

## API workflow invocation: `ExecuteApiWorkflowAsync` waits, despite the name

Use the sole API-workflow type, `Orchestrator.ExecuteApiWorkflowAsync`, on `bpmn:serviceTask`; its label `Start and wait for API workflow` means it waits and exposes the result to later nodes. Do not model fire-and-forget. Resolve release key, folder key, request schema, and response schema before runnable status; the served template is broken as described next.

## Job-wrapper v1 trap — `releaseKey` templates are unrunnable

`Orchestrator.StartJob`, `Orchestrator.ExecuteApiWorkflowAsync`, `Orchestrator.StartAgenticProcess[Async]`, and `StartCaseMgmtProcess[Async]` serve the same v1 template: `<uipath:activity version="v1">` with hidden unbound `releaseKey` / `folderId` / `folderPath` / `name`; all fields have `binding: false` except `releaseKey`, whose `bindingInfo` is process/Key in `validator/bpmn-spec.json`. Blank placeholders pass `validate`/pack but fail runtime; API workflow gives `170009 Could not get value for key:ReleaseKey from context in input`.

Fix, do not drop `releaseKey`:

1. Bind it using the documented resource mechanism (see [§4 Bindings](#4-bindings--from-bindinginfo-never-invented)) a process-kind `<uipath:binding resource="process" propertyAttribute="Key" resourceKey="<RELEASE_KEY>" default="<RELEASE_KEY>" />`, referenced from context as `=bindings.<id>`. Resolve `<RELEASE_KEY>` from `uip or processes list --folder-path <path> --output json` → deployed `Key`.
2. The template's `folderId` context field is misnamed — the runtime reads `folderKey`, not `folderId` or `folderPath`; `releaseKey` alone still faults `Could not get value for key:FolderKey from context in input`. Add a context field literally named `folderKey` containing the target `FolderKey` GUID from the same response; it is a literal, not a binding. Re-read after every deploy because `deploy run` creates a new folder.
3. With real `releaseKey` and `folderKey`, the node runs to completion. For `Orchestrator.ExecuteApiWorkflowAsync`, drop the template's own `folderId`/`folderPath`/`name` context fields.

For the other listed types apply step 1 only; apply step 2 after a live `key:FolderKey` fault, otherwise report unverified.

Map requested API workflow invocation/status/result fields as `uipath:output` rows on the service task, using discovered names/types and `source` expressions such as `=invocation`, `=status`, and `=result`; use exact schema fields. For `=result.<key>`, use a debug-run key when available (SKILL.md rule 17 step 5), otherwise schema name and report unverified. Do not add a downstream script solely to split the service-task result.

## Integration Service triggers

`Intsvc.TimerTrigger` is portable: `RequiresDiscovery=false`, no binding/context/input, and only exact `registry get Intsvc.TimerTrigger` template is needed. It needs no live connection/schema.

`Intsvc.EventTrigger` and `Intsvc.WaitForEvent` enrich like §3, but object/operation come from the trigger catalogue, not `uip is resources`; omit `--operation` and enrichment fails `Event enrichment requires --operation`.

Build new triggers/waits as V2; put Data Fabric scoping parameters (`entityScope`, `folderEntityName`, `folderEntityName_folderKey`) in `--input-details.queryParameters`; the CLI rejects unlisted names. See [v2-connector-nodes.md](v2-connector-nodes.md). V1 uses `queryParams`/`filters.expression`.

```bash
uip is activities list <connectorKey> --triggers --output json   # Name + ObjectName + IsCurated
uip is triggers objects <connectorKey> <OPERATION> --connection-id <id> --output json
uip is triggers describe <connectorKey> <operation> <objectName> --connection-id <id> --output json
uip maestro bpmn registry get <Intsvc.EventTrigger|Intsvc.WaitForEvent> \
    --connection-id <id> --object-name <ObjectName> --operation <Name> --output json
```

Prefer `IsCurated: Yes`. If absent, use generic `CREATED`/`UPDATED`/`DELETED` (`IsCurated: No`, `ObjectName: N/A`; the only path for generic-only connectors such as `uipath-uipath-jdbc`) and take its object from `uip is triggers objects`; it omits connection-specific objects and may be empty without `--connection-id`. `registry get` supplies template/InputFields only; use `uip is triggers describe` for `FilterFields`, `EventParameters`, and `OutputFields`: build the filter from `FilterFields`, never an activity's `RequestFields`; `EventParameters` are scoping inputs, `OutputFields` the event payload. The runtime reads only a `target="body"` input; the template's `filter` and `parameters` fields, and any sibling input without `target`, are dropped. In V1 emit one `target="body"` input as a sibling of `uipath:context`: `queryParams` contains EventParameters (a V2 element carries them in `body.parameters`; do not move them); `filters.expression` AND-joins equality clauses for each parameter with FilterFields. No filter tree is evaluated.

```xml
<uipath:input name="body" type="json" target="body"><![CDATA[{"filters":{"expression":"(parentFolderId == '<INBOX_ID>') && (contains(subject, 'Invoice'))"},"queryParams":{"parentFolderId":"<INBOX_ID>"}}]]></uipath:input>
```

`uip is triggers` and `registry get` uppercase operations; mixed-case Test Manager operations (`Created`, `Updated`, `Finished`) therefore return HTTP 404 / `IS enrichment error` and are unreachable in CLI 1.204.0.

| Connector key | Trigger operation | Object |
| --- | --- | --- |
| `uipath-microsoft-outlook365` | `EMAIL_RECEIVED` | `Message` |
| `uipath-atlassian-jira` | `ISSUE_CREATED` | `curated_get_issue` |
| `uipath-salesforce-slack` | `SLACK_EVENT_MESSAGE` | `slack_events_message` |
| `uipath-uipath-dataservice` | `CREATED_V3` | `EntityTriggers_V3` |

A hand-authored connector trigger is **draft** until CLI supplies trigger properties, connection binding, and schemas. In V1, context uses `connectionId = =bindings.<bindingId>`; activities use `connection`; V2 uses `connection` for all three; timer uses no connection. After authoring bindings, run `uip maestro bpmn format <file.bpmn>` then `uip maestro bpmn refresh <project>` so `bindings_v2.json` contains the connection. Use `refresh`, not deprecated `update-metadata`. An unmaterialized trigger passes `validate` but faults null connection with `102010`. Trigger-start drafts skip `refresh` ([SKILL.md](../SKILL.md) step 4c); package-ready/upload/debug/publish/deploy deliverables run it.

## Connectionless vs connector HTTP

- **Connector activity** (`Intsvc.ActivityExecution` or connector-authenticated operation): use for tenant connections, dynamic connector schemas, or connector objects; keep **draft** until enriched. Explicit CLI-owned blockers are **connection binding**, **dynamic schemas**, and generated package metadata (`bindings_v2.json`, `entry-points.json`, `operate.json`, `package-descriptor.json`); do not hand-author them (§3).
- **HTTP request**: always `Intsvc.UnifiedHttpRequest`, for both `manual` and `connector` modes. Build with `uip maestro bpmn registry get Intsvc.UnifiedHttpRequest --input-details '<request>'` and add `--connection-id` for connector mode; see [v2-connector-nodes.md](v2-connector-nodes.md#http-requests). A service with no connector of its own goes through a `uipath-uipath-http` connection in connector mode. Never author legacy `Intsvc.HttpExecution` or a connector's `httpRequest` object for a new node.

IS summary statuses: **executable** (activity, inputs, output variable, downstream mappings, and runtime verification if run), **draft** (shape/intent but enrichment missing), **mock** (fixed sample data), **blocked** (required URL, auth, schema, or enrichment decision missing).

## 5. Assemble

1. Build scaffold/process using [structural-bpmn.md](structural-bpmn.md).
2. Declare variables (`<uipath:variables>`, each with `elementId`) and process-level `<uipath:bindings>`.
3. For each node, paste `registry get` `xmlTemplate` (except SKILL.md rules 6 and 18), fill placeholders, and wire edges.
4. Author registry-omitted structure: sequence flows, gateway conditions/defaults, event definitions, boundary events, subprocess/call-activity containers, and multi-instance markers.
5. Generate `bpmndi:BPMNDiagram` after final source edit by running `uip maestro bpmn format <file.bpmn>`.
6. Validate using [structural-bpmn.md#validation](structural-bpmn.md#validation); rerun step 5 after every later source edit because `validate` errors on a node without shape.

## OOTB extension types (29, login-free)

`registry pull` returns these without login; always run `registry get <type>` before authoring.

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

This is a discovery aid, not a substitute for live `registry get`. Event types remain event-wrapped even on task-like hosts: `Intsvc.WaitForEvent`, `Intsvc.EventTrigger`, `Maestro.ReceiveMessageEvent`, and `Maestro.SendMessageEvent` use `uipath:event`, not `uipath:activity`.

## Registry-evidence-only tasks

- Create `registry-evidence/` before anything else.
- Run the registry command forms the user asked for. For RPA job + internal-message discovery, run `uip maestro bpmn registry list --limit -1 --output json`, `uip maestro bpmn registry get Orchestrator.StartJob --output json`, and `uip maestro bpmn registry get Maestro.ReceiveMessageEvent --output json`.
- If `uip` is unavailable in a temp/smoke sandbox, or returns valid failure JSON such as `"Result": "Failure"`, do not search the repository for another CLI or inspect fixtures. Still issue the required `list` and `get` forms once each, redirecting to evidence and allowing failure with `|| true`; record failed attempts in `registry-evidence/cli-error.txt`. Overwrite failure JSON in expected `registry-evidence/*.json` with valid JSON from `skills/uipath-maestro-bpmn/validator/bpmn-spec.json` containing the same types, then stop. Final evidence must literally contain the discovered type names, for example `Orchestrator.StartJob` and `Maestro.ReceiveMessageEvent`.
