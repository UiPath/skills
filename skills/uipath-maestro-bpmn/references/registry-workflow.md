# Registry workflow

Every `uipath:*` payload in a Maestro `.bpmn` comes from the registry — never
from prose, never hand-written. This file is the loop for turning user intent
into registry-backed XML.

## 1. Sync and discover

```bash
uip maestro bpmn registry pull            # sync + cache (login for connectors/processes)
uip maestro bpmn registry list --limit -1 --output json   # all extension types
uip maestro bpmn registry search <keyword> --output json  # find a type by intent
uip is connections list --all-folders --output json   # live IS connections (all folders)
```

Map the user's intent to an extension type from the list. Confirm the choice
with the user (and the specific connection / process / queue) before authoring.
**Never fabricate an identifier** — see [cli-conventions.md](cli-conventions.md).

**Connection discovery must be exhaustive.** Always pass `--all-folders` to
`uip is connections list` — connections live in many folders and a folder-scoped
listing silently misses them. An empty or unmatched result from a missing
`--all-folders`, or from a connector key guessed from a brand name rather than
found via `registry search`, is a **false negative** — never conclude "no
connection exists" or ask the user to create one until you have searched the
registry for the real connector key and listed across all folders.

`registry list` returns three buckets in `Data`: `ExtensionTypes` (the OOTB
extension types, always available), `Connectors` and `Processes` (only after
`uip login`). Each extension-type row carries `ExtensionType`, `Label`,
`BpmnElement` (the host BPMN element), `ExtensionTag`, and
`RequiresDiscovery` (`Yes` means you must resolve a concrete resource — process,
queue, connection — before the node is runnable).

In temp/smoke sandboxes, a CLI/tooling mismatch can produce valid JSON that is
only a failure envelope (for example `"Result": "Failure"`) instead of registry
content. For discovery-only tasks, keep that failed output in the transcript or
`registry-evidence/cli-error.txt`, then replace the final raw evidence JSON with
the matching entries from `validator/bpmn-spec.json`. The final saved evidence
must literally contain the requested extension type strings, such as
`Orchestrator.StartJob` and `Maestro.ReceiveMessageEvent`, not just the failure
envelope.

## 2. Get the template for each chosen type

```bash
uip maestro bpmn registry get <extensionType> --output json
```

`Data.ExtensionType` contains everything needed to author the node:

| Field | Use |
| --- | --- |
| `xmlTemplate` | The literal node XML with `{placeholder}` slots. **Author from this; fill placeholders only.** |
| `bpmnElement` | The host element's PascalCase model type (`bpmn:ServiceTask`). Normalize both this field and the `xmlTemplate` host tag to lower-camel when serializing (`<bpmn:serviceTask>`) — 27 of the 29 bundled templates carry the PascalCase tag. |
| `extensionTag` | `uipath:activity`, `uipath:event`, or `uipath:mapping`. |
| `contextFields[]` | The `uipath:context` inputs; each may carry its own `bindingInfo`. |
| `bindingInfo` | How the node binds to a resource (see §4). |
| `inputPattern` / `inputName` / `inputTarget` | How the request body input is shaped. |
| `requiresDiscovery` / `isDynamic` | Whether a concrete resource must be resolved first. |

The placeholders you fill are the obvious ones: `{id}`, `{name}`,
`{incomingEdge}`, `{outgoingEdge}`, `{varId}` (the output variable id), plus the
per-context-field placeholders (`{releaseKey}`, `{queueName}`, `{appId}`, …) and
the body CDATA. Leave the structural placeholders (`{incomingEdge}` /
`{outgoingEdge}`) wired to the sequence-flow ids you create in
[structural-bpmn.md](structural-bpmn.md).

Treat each template output and its process variable as one contract. Replace
`{varId}` with a stable id and declare a task-scoped `uipath:inputOutput` with
the template output's exact `type` and `elementId="<node-id>"`. This includes
opaque types such as `custom` and product-specific types such as
`Actions.HITL`; do not search examples for a guessed schema or coerce the type
to `string`, `object`, or `jsonSchema`. Leave the opaque type in place; live
enrichment replaces it with concrete typed rows later, so do not pre-empt it.

For an unresolved portable dynamic node, fill resource identity slots with the
escaped public placeholders SKILL.md defines (`&lt;TENANT_URL&gt;`,
`&lt;FOLDER_KEY&gt;`, `&lt;CONNECTION_NAME&gt;`), keep the retrieved
context/output shape, and use only user-supplied values in the body or
configurable context fields. Report the node as **draft** and name the
CLI-owned blocker literally, including the exact phrase `connection binding` where
that is what is missing. Do not inspect sibling skills, test fixtures, or
generated packages to invent the missing live schema.

## 3. Connector (`Intsvc.*`) enrichment

For connector types (`requiresDiscovery: Yes`, e.g.
`Intsvc.ActivityExecution`, `Intsvc.WaitForEvent`, `Intsvc.EventTrigger`),
resolve a live connection and object, then enrich:

```bash
uip is connections list --all-folders --output json   # pick a connection id + its connector (search all folders)
uip maestro bpmn registry get Intsvc.ActivityExecution \
    --connection-id <id> --object-name <object> --output json
```

The response adds an `IsEnrichment` block with the live field metadata (the
CLI builds it as `ISEnrichment`; the output formatter normalizes the key, so
`--output json` emits `IsEnrichment` — read that one). Write
the activity's `body` input (`target="body"`) and `context` (`connectorKey`,
`objectName`) from that enrichment — do not hand-author connector schemas. The
connection is referenced through a connection binding, `=bindings.<bindingId>`
(see §4).

### Body shape: hand-authored files need ONE `target="body"` input

The manifest declares `inputPattern: separateInputs` with `inputTarget: body`,
and its `InputNotes` tell you to add each request field as its own
`uipath:input`. Studio Web's canvas does emit that shape. **The runtime does
not consume it:** several `target="body"` inputs do not merge — each claims to
be the entire body, the last one wins, and the provider receives that single
value as a bare scalar. Integration Service answers `500 Internal failure`, or
the provider reports the other fields missing (Slack:
`missing required field: channel`). Measured on live Alpha against both the
Atlassian Jira and Slack connectors.

So when you hand-author the XML, emit exactly one `target="body"` input holding
the complete request object as JSON element content, nested the way the
provider's API nests it:

```xml
<uipath:input name="body" type="json" target="body"><![CDATA[{"fields":{"project":{"key":"=vars.Var_ProjectKey"},"issuetype":{"id":"=vars.Var_IssueTypeId"},"summary":"=js:'[' + vars.Var_Severity + '] ' + vars.Var_CorrelationId}}]]></uipath:input>
```

`=vars.<id>` and `=js:` resolve inside that CDATA, so build the body from
variables rather than literals. In an XML *attribute* a `=js:` expression must
escape the XML metacharacters — `&amp;&amp;` for `&&`, and `&lt;` for `<` — or
the file is not well-formed; `>` needs no escaping in an attribute value, and
inside CDATA nothing does.

This single-input form **is** the canonical shape, and it round-trips. Studio
Web's own design schema for this type sets `isSplitInputs: false` with one
`jsonBody` at `target="body"`
(`origin/develop:src/services/serialization/design-schema/intsvc.activityExecution.beta.design-schema.json`),
and the canvas's round-trip fixture for a Jira `curated_create_issue` node is
exactly one nested `target="body"` CDATA asserted parse→serialize identical
(`origin/develop:src/services/serialization/xml-serialization.test.ts:706`).
The serializer *preserves* separate inputs if a file already has them rather
than merging, but it never generates them.

The outlier is the CLI manifest: `Intsvc.ActivityExecution` still declares
`inputPattern: separateInputs` with `inputTarget: body`, and its `InputNotes`
still tell authors to add one `uipath:input` per request field. That contradicts
both the canvas and the runtime, so treat the manifest's InputNotes as stale
here rather than as the contract.

`target="bodyField"` is **not** an option here. It is the target of the single
merged *arguments* payload on `mergedBody` / `scriptArgs` types —
`JobArguments` for the `Orchestrator.*` process starts, `HitlTaskArguments` for
`Actions.HITL`, `args` for `BPMN.ScriptTask` — and no `Intsvc.*` type uses it.
The validator enforces that: any other direct input name is rejected with
`does not support input payload "<name>"`. Dotted Integration Service field
names are also nested into objects on the way out, not sent as literal flat
keys, so a flat `fields.project.key` leaves the provider never seeing
`fields.project`.

Take `operation` from the `Operation.Name` reported by
`uip is resources describe` (for example `Create`); `path` and `objectName`
come from the same described object. The template's `DiscoveryNotes` say "set
operation from Name", which reads as the catalogue's per-activity `Name`
(`CreateIssue`) — that value draws a provider `400` at runtime. `--operation`
takes the same value, so pass `--operation Create`.

### Required `Parameters` are separate from the body — emit every one

`uip is resources describe` reports `Parameters` alongside `RequestFields`.
Each parameter is its own input, targeted by its `Type` (`query`, `path`, or
`file`) — never folded into the body. Emit an input for every parameter marked
`Required: true`, using its `DefaultValue` when the request has no better
value:

```xml
<uipath:input target="query" name="send_as" type="string" value="bot" />
```

Omitting one is accepted by local validation and by `pack`, then fails only at
runtime with `400` and `Value for required parameter '<name>' not found`. A
`Parameters` list can be empty (Jira's `curated_create_issue`) or carry a
required entry (Slack's `send_message_to_channel_v2` requires `send_as`), so
check it per activity rather than assuming.

## 4. Bindings — from `bindingInfo`, never invented

A node that targets a cloud resource carries a binding. The `bindingInfo` on the
extension type tells you the binding shape; the concrete value comes from
discovery or the user.

- **Resource bindings** (`bindingInfo.resource` = `process` / `queue` /
  `businessRule`): the context field named by `bindingInfo.contextField`
  (e.g. `releaseKey`, `queueName`) holds the resource key
  (`bindingInfo.propertyAttribute`, usually `Key`). Resolve the real key with
  `registry search` / discovered `Processes` / `Queues`; never guess a GUID.
- **Connection bindings** (`Intsvc.*`): the context references a connection via
  `=bindings.<bindingId>`, and a `<uipath:binding>` of `resource="Connection"`
  with `propertyAttribute="ConnectionId"` in the process-level
  `<uipath:bindings>` holds the live connection id from `uip is connections list`.
  The context field that carries the reference differs by node kind: activities
  (`Intsvc.ActivityExecution`) use `connection`; connector **triggers and waits**
  (`Intsvc.EventTrigger`, `Intsvc.WaitForEvent`) use `connectionId`. Either way
  `uip maestro bpmn refresh` (and `pack`) materialize that binding into a
  `Connection` resource in `bindings_v2.json` — without it the process passes
  `validate` but faults at runtime with `102010 IntSvcArgumentsError -
  Integration Services invalid value in input` (the connection resolves to null).

Declare all bindings in a single process-level `<uipath:bindings version="v1">`
block. Each `<uipath:binding>` carries `id`, `resource`, `propertyAttribute`,
`resourceKey`, and a `default` value. **`resourceKey` is required** — omitting
it fails `validate` with `Integration Service activity connection binding
"<id>" is missing resourceKey`.

A folder-scoped connector activity needs TWO bindings that share one
`resourceKey` (the connection id) and differ in `propertyAttribute`: the
connection binding's `default` is the connection id, the folder binding's
`default` is the folder key.

```xml
<uipath:bindings version="v1">
  <uipath:binding id="Binding_JiraConn"   resource="Connection" propertyAttribute="ConnectionId" resourceKey="<connection-id>" default="<connection-id>" />
  <uipath:binding id="Binding_JiraFolder" resource="Connection" propertyAttribute="folderKey"    resourceKey="<connection-id>" default="<folder-key>" />
</uipath:bindings>
```

## Agent wrapper selection — pick by `processType`, not the label

When a node invokes an agent, choose the wrapper by the resource's
**`processType`** (from `uip or processes list --all-fields`), not its display
label:

- Coded Python agents publish as `processType: "Function"` — use the
  `Orchestrator.StartJob` process contract, **not** `StartAgentJob`.
- Agent Builder (low-code) publishes as `processType: "Agent"` →
  `Orchestrator.StartAgentJob`.
- External A2A agent addressed by URL / skillId → `A2A.AgentExecution`.
- Integration Service external agent → `Intsvc.*AgentExecution`.

Gotcha: `A2A.AgentExecution` renders as an external A2A node and **disables the
Action dropdown** in Studio Web. Do not use it for a folder-deployed agent — the
canvas treats the task as misconfigured. Use `StartAgentJob`/`StartJob` for
folder-deployed resources.

## API workflow — wait vs fire-and-forget

Pick the wrapper by whether downstream needs the invocation result:
`Orchestrator.ExecuteApiWorkflow` **waits** for completion (result available to
later nodes); `Orchestrator.ExecuteApiWorkflowAsync` **returns immediately**
(fire-and-forget). Both are `bpmn:serviceTask` activities. Resolve `ReleaseKey`
(process GUID), `FolderKey`/`FolderPath`, and the request/response schemas before
the node is runnable — make the wait-versus-async choice explicit in the model.

When the caller asks for API workflow invocation/status/result fields, map those
fields as `uipath:output` rows on the API workflow `bpmn:serviceTask` itself
using the discovered output names/types and `source` expressions, for example
`source="=invocation"`, `source="=status"`, and `source="=result"` (or the exact
schema fields returned by discovery). Do not add a downstream script task solely
to split the API workflow service-task result into variables; that hides the
requested service-task output contract from the model.

## Integration Service triggers

`Intsvc.TimerTrigger` is portable: its registry entry has
`RequiresDiscovery=false`, no binding, context, or input fields, and needs only
the exact `registry get Intsvc.TimerTrigger` template. It does not require a
live connection or schema enrichment.

`Intsvc.EventTrigger` and connector waits such as `Intsvc.WaitForEvent` do need
their **trigger properties** enriched/bound through the CLI — the same
enrichment path as `Intsvc.*` activities (§3). A hand-authored connector
trigger shell stays **draft** until the CLI supplies the concrete trigger
properties, connection binding, and schemas.

For `Intsvc.EventTrigger` / `Intsvc.WaitForEvent` the connection is referenced
from the node context as **`connectionId`** = `=bindings.<bindingId>` (activities
use `connection`); the timer trigger binds no connection. After authoring the
connection binding, run `uip maestro bpmn refresh <project>` so the binding is
materialized into a `Connection` resource in `bindings_v2.json` — a trigger whose
connection is not materialized passes `validate` but faults at runtime with a
null connection (error 102010). Use `refresh`, not the deprecated
`update-metadata`, which does not materialize connection bindings.

## Connectionless vs connector HTTP

- **Connector activity** (`Intsvc.ActivityExecution` / a connector-authenticated
  operation): use when the call goes through a tenant connection, a dynamic
  connector schema, or a connector object operation. Keep the node **draft**
  until enriched. The CLI-owned enrichment blockers — the ones that must be
  resolved before upload or run, and that boundary notes should name explicitly
  — are **connection binding**, **dynamic schemas**, generated **package
  metadata** (`bindings_v2.json`, `entry-points.json`, `operate.json`,
  `package-descriptor.json`). Do not hand-author any of these (§3).
- **Connectionless / manual HTTP** (`Intsvc.HttpExecution`, or
  `Intsvc.UnifiedHttpRequest` when current tooling exposes the unified shape):
  use when the workflow itself owns the URL, method, payload, and response
  parsing (no connection). Author `mode="manual"`, `method`, `url`, `headers`,
  `parameters`, `body` directly from the registry template.

Status vocabulary for an IS node in a summary: **executable** (activity, inputs,
output variable, and downstream mappings present, runtime-verified if a run was
done), **draft** (BPMN shape/intent present but enrichment missing), **mock**
(returns fixed sample data instead of calling out), **blocked** (a required URL,
auth, schema, or enrichment decision is missing).

## 5. Assemble

1. Build the document scaffold and process (see
   [structural-bpmn.md](structural-bpmn.md)).
2. Declare the process's variables (`<uipath:variables>`, each with an
   `elementId`) and the `<uipath:bindings>` block.
3. For each node, paste its `registry get` `xmlTemplate`, fill placeholders, and
   wire `{incomingEdge}`/`{outgoingEdge}` to your sequence flows.
4. Author the structural BPMN the registry does not emit: sequence flows,
   gateway conditions/defaults, event definitions, boundary events,
   subprocess/call-activity containers, multi-instance markers.
5. Generate the `bpmndi:BPMNDiagram`: `uip maestro bpmn format <file.bpmn>`
6. Validate (see [structural-bpmn.md#validation](structural-bpmn.md#validation)).

## OOTB extension types (29, login-free)

These are the built-in types `registry pull` returns without login. Discover the
exact template for any of them with `registry get <type>`.

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
| `Intsvc.HttpExecution` / `Intsvc.UnifiedHttpRequest` | `bpmn:sendTask` | activity |
| `Intsvc.WaitForEvent` | `bpmn:receiveTask` | event |
| `Intsvc.EventTrigger` | `bpmn:startEvent` | event |
| `Intsvc.TimerTrigger` | `bpmn:startEvent` | activity |
| `Intsvc.{Async,SyncAgent,AsyncAgent,SyncWorkflow,AsyncWorkflow}Execution` | `bpmn:serviceTask` | activity |
| `A2A.AgentExecution` | `bpmn:serviceTask` | activity |
| `BPMN.Variables` | `bpmn:task` | mapping |
| `BPMN.ScriptTask` | `bpmn:scriptTask` | mapping |
| `Maestro.ReceiveMessageEvent` | `bpmn:intermediateCatchEvent` | event |
| `Maestro.SendMessageEvent` | `bpmn:intermediateThrowEvent` | event |
| `Maestro.CaseRulesEvaluator` / `Maestro.CaseManagerGuardrails` | `bpmn:serviceTask` | activity |

This table is a discovery aid, not a substitute for `registry get` — always pull
the live template before authoring.

If a registry `xmlTemplate` returns a PascalCase BPMN host tag such as
`bpmn:SendTask` or `bpmn:ReceiveTask`, normalize only the BPMN host element
names to the serializer's lower-camel form (`bpmn:sendTask`,
`bpmn:receiveTask`) when inserting it into a source file. Keep the
`uipath:*` payload and its `uipath:type` value unchanged.

Event types stay event-wrapped even when you place them on task-like BPMN
hosts: `Intsvc.WaitForEvent`, `Intsvc.EventTrigger`,
`Maestro.ReceiveMessageEvent`, and `Maestro.SendMessageEvent` use
`uipath:event`, not `uipath:activity`.

## Registry-evidence-only tasks

- Create `registry-evidence/` before anything else.
- Run the registry command forms the user asked for. For RPA job + internal
  message discovery, use `uip maestro bpmn registry list --limit -1 --output
  json`, `uip maestro bpmn registry get Orchestrator.StartJob --output json`,
  and `uip maestro bpmn registry get Maestro.ReceiveMessageEvent --output json`.
- If `uip` is unavailable in a temp/smoke sandbox, or if it writes a valid JSON
  failure object such as `"Result": "Failure"` instead of registry content, do
  not search the repo for a replacement CLI or inspect test fixtures. Still
  issue the required `list` and `get` command forms once each with output
  redirected to their evidence files (allowing failure with `|| true`), so the
  transcript shows the discovery loop:
  `uip maestro bpmn registry list --limit -1 --output json` and
  `uip maestro bpmn registry get <type> --output json`. Record the failed CLI
  attempts in `registry-evidence/cli-error.txt`, then overwrite any failure JSON
  in the expected `registry-evidence/*.json` files with valid JSON evidence from
  `skills/uipath-maestro-bpmn/validator/bpmn-spec.json` containing the same
  extension types and stop. The final evidence files must literally contain the
  discovered type names, for example `Orchestrator.StartJob` and
  `Maestro.ReceiveMessageEvent`.
