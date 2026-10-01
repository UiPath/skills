# Registry workflow: discover and get templates

## 1. Sync and discover

```bash
uip maestro bpmn registry pull            # sync + cache (login for connectors/processes)
uip maestro bpmn registry list --limit -1 --output json   # all extension types
uip maestro bpmn registry search <keyword> --output json  # find a type by intent
uip is connections list --all-folders --output json   # live IS connections (all folders)
```

Map the user's intent to an extension type from the list. Pick the
best-evidenced type, connection, process and queue and say in your summary
which you used and which others tied; ask only under SKILL.md Rule 4.
**Never fabricate an identifier** — see [cli-conventions.md](cli-conventions.md).

**Connection discovery must be exhaustive.** Always pass `--all-folders` to
`uip is connections list` — connections live in many folders and a folder-scoped
listing silently misses them. An empty or unmatched result from a missing
`--all-folders`, or from a connector key guessed from a brand name rather than
found via `registry search`, is a **false negative** — never conclude "no
connection exists" or ask the user to create one until you have searched the
registry for the real connector key and listed across all folders.
Select rows by field, never by position, lower-casing `Data` keys first
(their casing is not fixed): `uip is connections list --all-folders --output json
| jq '.Data[] | with_entries(.key |= ascii_downcase)
| select(.connectorkey=="<connectorKey>" and .state=="Enabled")'`.
A truncated listing is also a false negative; see
[cli-conventions.md](cli-conventions.md).

`registry list` returns four buckets in `Data`: `ExtensionTypes` (the OOTB
extension types, always available), `Connectors` and `Processes` (only after
`uip login`), and `ProcessesByType` (`Processes` counted per `processType`,
every type present even at 0). Each extension-type row carries
`ExtensionType`, `Label`, `BpmnElement` (the host BPMN element),
`ExtensionTag`, and `RequiresDiscovery` (`Yes` means you must resolve a
concrete resource — process, queue, connection — before the node is runnable).

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
| `bindingInfo` | How the node binds to a resource (see [§4](registry-workflow-bindings.md#4-bindings--from-bindinginfo-never-invented)). |
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

For a dynamic node left unresolved (SKILL.md step 1: the user asked for a
draft or placeholders, or no candidate pings `Enabled`), fill resource
identity slots with the escaped public placeholders SKILL.md defines (`&lt;TENANT_URL&gt;`,
`&lt;FOLDER_KEY&gt;`, `&lt;CONNECTION_NAME&gt;`), keep the retrieved
context/output shape, and use only user-supplied values in the body or
configurable context fields. Report the node as **draft** and name the
CLI-owned blocker literally, including the exact phrase `connection binding` where
that is what is missing. Do not inspect sibling skills, test fixtures, or
generated packages to invent the missing live schema.

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
| `Intsvc.WaitForEvent` | `bpmn:receiveTask`; or its `uipath:event` block on a `bpmn:intermediateCatchEvent` (incoming + outgoing) or a `bpmn:boundaryEvent` (`attachedToRef`, outgoing only), with a bare `<bpmn:messageEventDefinition />` after the flows | event |
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
