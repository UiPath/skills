# Registry workflow

Every `uipath:*` payload in a Maestro `.bpmn` comes from the registry — never
from prose, never hand-written. This file is the loop for turning user intent
into registry-backed XML.

## 1. Sync and discover

```bash
uip maestro bpmn registry pull            # sync + cache (login for connectors/processes)
uip maestro bpmn registry list --limit -1 --output json   # all extension types
uip maestro bpmn registry search <keyword> --output json  # find a type by intent
uip is connections list --output json     # live Integration Service connections
```

Map the user's intent to an extension type from the list. Confirm the choice
with the user (and the specific connection / process / queue) before authoring.
**Never fabricate an identifier** — see [cli-conventions.md](cli-conventions.md).

`registry list` returns three buckets in `Data`: `ExtensionTypes` (the OOTB
extension types, always available), `Connectors` and `Processes` (only after
`uip login`). Each extension-type row carries `ExtensionType`, `Label`,
`BpmnElement` (the host BPMN element), `ExtensionTag`, and
`RequiresDiscovery` (`Yes` means you must resolve a concrete resource — process,
queue, connection — before the node is runnable).

## 2. Get the template for each chosen type

```bash
uip maestro bpmn registry get <extensionType> --output json
```

`Data.ExtensionType` contains everything needed to author the node:

| Field | Use |
| --- | --- |
| `xmlTemplate` | The literal node XML with `{placeholder}` slots. **Author from this; fill placeholders only.** |
| `bpmnElement` | The host BPMN element the template uses (e.g. `bpmn:ServiceTask`). |
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

## 3. Connector (`Intsvc.*`) enrichment

For connector types (`requiresDiscovery: Yes`, e.g.
`Intsvc.ActivityExecution`, `Intsvc.WaitForEvent`, `Intsvc.EventTrigger`),
resolve a live connection and object, then enrich:

```bash
uip is connections list --output json     # pick a connection id + its connector
uip maestro bpmn registry get Intsvc.ActivityExecution \
    --connection-id <id> --object-name <object> --output json
```

The response adds an `ISEnrichment` block with the live field metadata. Write
the activity's `body` input (`target="body"`) and `context` (`connectorKey`,
`objectName`) from that enrichment — do not hand-author connector schemas. The
connection is referenced through a connection binding, `=bindings.<bindingId>`
(see §4).

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

Declare all bindings in a single process-level `<uipath:bindings version="v1">`
block. Each `<uipath:binding>` carries `id`, `resource`, `propertyAttribute`,
and a `default` value (the resolved key/id).

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
5. Generate the `bpmndi:BPMNDiagram` (shape per node, edge per flow).
6. Validate (see [structural-bpmn.md#validation](structural-bpmn.md#validation)).

## OOTB extension types (29, login-free)

These are the built-in types `registry pull` returns without login. Discover the
exact template for any of them with `registry get <type>`.

| Extension type | Host element | Tag |
| --- | --- | --- |
| `Actions.HITL` | `bpmn:UserTask` | activity |
| `Orchestrator.StartJob` | `bpmn:ServiceTask` | activity |
| `Orchestrator.StartAgentJob` | `bpmn:ServiceTask` | activity |
| `Orchestrator.BusinessRules` | `bpmn:BusinessRuleTask` | activity |
| `Orchestrator.ExecuteApiWorkflowAsync` | `bpmn:ServiceTask` | activity |
| `Orchestrator.CreateQueueItem` | `bpmn:SendTask` | activity |
| `Orchestrator.CreateAndWaitForQueueItem` | `bpmn:ServiceTask` | activity |
| `Orchestrator.StartAgenticProcess[Async]` | `bpmn:CallActivity` | activity |
| `Orchestrator.StartCaseMgmtProcess[Async]` | `bpmn:CallActivity` | activity |
| `Intsvc.ActivityExecution` | `bpmn:SendTask` | event/activity |
| `Intsvc.HttpExecution` / `Intsvc.UnifiedHttpRequest` | `bpmn:SendTask` | activity |
| `Intsvc.WaitForEvent` | `bpmn:ReceiveTask` | event |
| `Intsvc.EventTrigger` | `bpmn:StartEvent` | event |
| `Intsvc.TimerTrigger` | `bpmn:StartEvent` | activity |
| `Intsvc.{Async,SyncAgent,AsyncAgent,SyncWorkflow,AsyncWorkflow}Execution` | `bpmn:ServiceTask` | activity |
| `A2A.AgentExecution` | `bpmn:ServiceTask` | activity |
| `BPMN.Variables` | `bpmn:Task` | mapping |
| `BPMN.ScriptTask` | `bpmn:ScriptTask` | mapping |
| `Maestro.ReceiveMessageEvent` | `bpmn:IntermediateCatchEvent` | event |
| `Maestro.SendMessageEvent` | `bpmn:IntermediateThrowEvent` | event |
| `Maestro.CaseRulesEvaluator` / `Maestro.CaseManagerGuardrails` | `bpmn:ServiceTask` | activity |

This table is a discovery aid, not a substitute for `registry get` — always pull
the live template before authoring.
