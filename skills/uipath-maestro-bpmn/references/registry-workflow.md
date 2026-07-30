# Registry workflow

Registry-listed node execution payloads come from the registry — never from
prose or hand-written approximations. Structural BPMN and serializer-owned
scaffold metadata follow the structural/canvas contract. This file is the loop
for turning user intent into registry-backed node XML.

## 1. Choose draft or live mode, then discover the node type

Choose the mode from the request before tenant-dependent discovery:

- **Portable draft:** for synthetic, local-only, structural, or explicitly
  draft work, default to a known login-free built-in template without adding an
  authenticated pull or tenant-resource listing, and preserve unresolved
  placeholders. An explicit request for raw `registry pull`, `list`, or
  `search` evidence still authorizes those read-only registry forms without a
  profile; it does not authorize tenant-resource inventory. If the type cannot
  be identified without the live catalog, ask before crossing that boundary:

  ```bash
  uip maestro bpmn registry get <known-built-in-type> --output json
  ```

- **Live/runnable:** when the user asks for a real, current, tenant-bound, or
  runnable resource, verify the active context and follow
  [live-resource-resolution-guide.md](live-resource-resolution-guide.md):

  ```bash
  uip login status --profile <name> --output json
  uip maestro bpmn registry pull --profile <name> --output json
  uip maestro bpmn registry list --profile <name> --limit -1 --output json
  uip maestro bpmn registry search <keyword> --profile <name> --output json
  uip maestro bpmn registry get <extensionType> --profile <name> --output json
  ```

- **Unclear:** ask before tenant inventory when live versus portable would
  materially change the result.

`RequiresDiscovery` means a concrete resource is needed to make the node
runnable; it does not authorize live discovery. An unknown resource adapter
blocks a runnable claim, not a structural draft.

Map intent to an extension type and inspect the full contract from `registry
get`. `registry list` is a coarse discovery view. When authenticated, it can
also include live `Connectors` and `Processes`; use those only in live mode.

In temp/smoke sandboxes, a CLI/tooling mismatch can produce a valid JSON failure
envelope instead of registry content. The bundled `validator/bpmn-spec.json`
fallback is allowed only for login-free built-in-template evidence. It must
never stand in for a live process, queue, connector, connection, operation,
object, schema, or runnable-node claim. For a live-resource failure, stop and
report the node as blocked.

## 2. Get the template for each chosen type

For a portable built-in, use:

```bash
uip maestro bpmn registry get <extensionType> --output json
```

For a live lookup under a named profile, repeat the profile on this command too:

```bash
uip maestro bpmn registry get <extensionType> --profile <name> --output json
```

`Data.ExtensionType` contains everything needed to author the node:

| Field | Use |
| --- | --- |
| `XmlTemplate` | The literal node XML with `{placeholder}` slots. **Author from this; fill placeholders only.** |
| `BpmnElement` | The host BPMN element the template uses (for source files, normalize to lower-camel such as `bpmn:serviceTask`). |
| `ExtensionTag` | `uipath:activity`, `uipath:event`, or `uipath:mapping`. |
| `ContextFields[]` | The `uipath:context` inputs; each may carry its own `BindingInfo`. |
| `BindingPattern` / `BindingInfo` | Whether and how the node binds to a resource; for live mode, use [live-resource-resolution-guide.md](live-resource-resolution-guide.md). |
| `InputPattern` / `InputName` / `InputTarget` | How the request body input is shaped. |
| `RequiresDiscovery` / `IsDynamic` | Whether a concrete resource must be resolved first. |

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
to `string`, `object`, or `jsonSchema`. Live enrichment can replace an opaque
dynamic output with concrete typed output rows later.

For an unresolved portable dynamic node, fill resource identity slots with
escaped public placeholders, keep the retrieved context/output shape, and use
only user-supplied values in the body or configurable context fields. Label the
node non-runnable. Do not inspect sibling skills, test fixtures, or generated
packages to invent the missing live schema.

## 3. Resolve live resources only when requested

For live mode, use the full-contract adapters, exact identity/folder/lifecycle
rules, ambiguity handling, bounded refresh, and binding boundary in
[live-resource-resolution-guide.md](live-resource-resolution-guide.md). For portable draft
mode, keep placeholders unresolved and label the node non-runnable; do not
substitute bundled or stale data for live proof.

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
their **trigger properties** enriched/bound through the CLI — follow the same
live contract boundary as `Intsvc.*` activities in
[live-resource-resolution-guide.md](live-resource-resolution-guide.md). A hand-authored
trigger shell stays **draft** until the CLI supplies the concrete trigger
properties, connection binding, and schemas.

## Connectionless vs connector HTTP

- **Connector activity** (`Intsvc.ActivityExecution` / a connector-authenticated
  operation): use when the call goes through a tenant connection, a dynamic
  connector schema, or a connector object operation. Keep the node **draft**
  until enriched. The CLI-owned enrichment blockers — the ones that must be
  resolved before upload or run, and that boundary notes should name explicitly
  — are **connection binding**, **dynamic schemas**, generated **package
  metadata** (`bindings_v2.json`, `entry-points.json`, `operate.json`,
  `package-descriptor.json`). Do not hand-author any of these; follow the
  [live binding boundary](live-resource-resolution-guide.md#5-preserve-the-binding-boundary).
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
2. Declare root variables (`BPMN.Variables` template) and the
   `<uipath:bindings>` block.
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

This table is a discovery aid, not a substitute for `registry get` — always
retrieve the exact template before authoring.

If a registry `xmlTemplate` returns a PascalCase BPMN host tag such as
`bpmn:SendTask` or `bpmn:ReceiveTask`, normalize only the BPMN host element
names to the serializer's lower-camel form (`bpmn:sendTask`,
`bpmn:receiveTask`) when inserting it into a source file. Keep the
`uipath:*` payload and its `uipath:type` value unchanged.

Event types stay event-wrapped even when you place them on task-like BPMN
hosts: `Intsvc.WaitForEvent`, `Intsvc.EventTrigger`,
`Maestro.ReceiveMessageEvent`, and `Maestro.SendMessageEvent` use
`uipath:event`, not `uipath:activity`.
