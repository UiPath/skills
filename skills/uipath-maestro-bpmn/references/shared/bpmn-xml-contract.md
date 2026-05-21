# BPMN XML Contract

This document summarizes the public-safe authoring boundary for Maestro BPMN XML. It intentionally avoids raw exported BPMN, tenant data, connection identifiers, private names, URLs, or local paths.

## Baseline document

Generated BPMN must be valid BPMN 2.0 with the UiPath extension namespace.

- `bpmn:definitions` includes standard BPMN, BPMNDI, DI, DC, and the UiPath namespace.
- The UiPath namespace URI is `http://uipath.org/schema/bpmn` and the preferred prefix is `uipath`.
- Do not declare `uipath` as `http://schemas.uipath.com/workflow/activities` in
  Maestro BPMN files.
- Use one executable root process by default. Use collaboration/pools only when the user explicitly asks for that model.
- Studio Web import requires at least one valid `bpmndi:BPMNDiagram` with a `bpmndi:BPMNPlane`.
- Every visible flow node should have a `bpmndi:BPMNShape` with bounds.
- Every visible edge should have a `bpmndi:BPMNEdge` with waypoints.
- Conditions and scripts should use a leading `=` where Maestro expects expressions.
- UiPath extension expressions should read BPMN variables through `vars.<variableId>`,
  for example `=vars.Var_RequestId`, rather than bare names.
- For lint-sensitive expression details, see [expression-authoring.md](expression-authoring.md).
- CDATA is the expected representation for JSON bodies, schemas, scripts, variable schemas, custom output bodies, and case-management payload bodies.
- XML comments must remain parseable. Do not put `--` inside comments, and do
  not use dashed decorative separator lines in BPMN XML comments.

## Supported model-authored BPMN

For the supported element map and UiPath extension wrapper table, see [author/supported-elements.md](../author/references/supported-elements.md).

The model may directly author standard BPMN structure when user intent is clear.
Anything listed in
[Current generation exclusions](../author/references/supported-elements.md#current-generation-exclusions)
is preserve-only for imported files and must not be generated in new source.

- Events: start, end, boundary, intermediate catch, and intermediate throw events.
- Event definitions: none, timer, message, error, and terminate end events where supported by the runtime path.
- Gateways: exclusive, inclusive, parallel, and event-based gateways.
- Tasks and activities: task, service task, send task, receive task, user task, business rule task, script task, and call activity.
- Containers: subprocess and supported event subprocesses. Expanded subprocesses need a second diagram when nested content must render in Studio Web.
- Flow and annotation elements: sequence flow, message flow, association, data input/output association, group, text annotation, categories, messages, errors, data stores, item definitions, and resources.
- Loop markers: documented multi-instance parallel or sequential loop metadata. UiPath collection/element metadata belongs under the loop characteristic extension elements.

Conservative defaults:

- Start with one root process and one blank start event unless the process needs a trigger entry point.
- Use sequence flows for routing inside one process.
- Put gateway conditions on outgoing sequence flows and set a default flow where appropriate.
- Attach boundary error events to activities and reference valid error definitions.
- Give event subprocesses exactly one start event.
- Avoid sequence flows that cross subprocess scope or pool boundaries.

## Two-pass authoring boundary

For non-trivial authoring, split generation into two passes:

- **Pass 1: BPMN skeleton** - author standard BPMN process structure, event definitions, gateway conditions, subprocess scopes, sequence/message flows, annotations, and BPMN DI. Use placeholder labels or annotations for resource intent. Keep gateway conditions business-readable; do not use Maestro runtime expressions such as `=vars.<variableId>` until pass 2 declares those variables. Preserve existing extension XML in brownfield files.
- **Operator confirmation** - confirm the process shape before filling execution-specific XML.
- **Pass 2: model-owned UiPath XML** - add root variables, entry point IDs, mappings, documented bindings, script metadata, retry/error metadata, loop metadata, and documented service shells from [wrapper-shells.md](wrapper-shells.md).
- **CLI enrichment** - generate or enrich Integration Service activity/trigger payloads, connector bindings, dynamic schemas, and generated package files.

Do not combine connector selection, connection binding, dynamic schema generation, and topology rewrites in one opaque edit.

## Executable contract boundary

The current confirmed generation boundary is preserve/model-shell only for areas whose runtime contract depends on tenant state, registry metadata, or non-BPMN subscriptions. Do not add generation guidance that creates executable payloads for those areas until the contract is fixture-backed and CLI-validated.

- Signals: do not generate new signal definitions or signal event definitions.
  Preserve imported signal XML and report it as unsupported for regeneration
  unless a current product contract and local validation prove support.
- Plain connectionless HTTP: after skeleton confirmation, model authors may use
  the documented [HTTP request recipe](../author/references/task-recipes/http-request.md)
  when the workflow owns the URL, method, payload, and parsing, and no
  connector connection or dynamic connector schema is needed.
- Integration Service: model authors may create the surrounding BPMN node and
  document connector intent. They may also create a non-executable draft
  `Intsvc.*` shell with `uipath:type value="Intsvc.<Variant>"` and placeholder
  strings. Except for the documented pass-2 plain connectionless HTTP recipe,
  executable `Intsvc.*` activity/event XML, connection bindings, connector
  metadata, trigger property bindings, filters, parameters, and dynamic schemas
  require live registry-backed CLI enrichment for the target tenant before
  upload, debug, publish, or deploy.
- Brownfield files: preserve imported signal or Integration Service extension XML unless the user explicitly asks for normalization and the CLI can validate the replacement.

## UiPath extensions the model may write

Use lower-case XML aliases in examples and authoring guidance:

- Root `uipath:variables version="v1"` with input, input/output, and output variables.
- Root `uipath:bindings version="v1"` for placeholder-safe resource bindings when the binding contract is documented.
- Root-level start event `uipath:entryPointId value="..."` for runnable entry points.
- `uipath:mapping version="v1"` for `BPMN.Variables` mappings.
- `uipath:scriptVersion value="..."` for script task metadata. Prefer `v3` for new script tasks; preserve imported `v2` metadata unless the user explicitly migrates it.
- `uipath:migrationVersion version="..."` as import migration metadata to preserve, including numeric values such as `5`, `11`, and `11.5`.
- `uipath:loopCharacteristics inputCollection="..." inputElement="..."` under loop characteristic extensions.
- `uipath:retry`, `uipath:errorMapping`, and `uipath:tags` when the user gives explicit public-safe metadata. For retry, boundary errors, event subprocesses, and error mapping shapes, see [error-handling.md](error-handling.md).
- `uipath:activity` and `uipath:event` shells for documented non-Integration-Service service types.

New authored `uipath:activity` and `uipath:event` shells use the canonical
nested type element:

```xml
<uipath:activity version="v1">
  <uipath:type value="Orchestrator.StartJob" version="v1" />
</uipath:activity>
```

Do not use legacy shorthand such as `<uipath:activity type="...">` in new XML.
For task payloads, keep the wrapper type and resource context in
`uipath:activity`; put variable inputs and outputs in a sibling
`uipath:mapping version="v1"` element whose `var` attributes target declared
variable ids.

For new root variables, use `uipath:input`, `uipath:inputOutput`, and
`uipath:output` children. Do not author generic `uipath:variable
direction="..."` entries in new source; preserve imported instances only when
normalizing the file is out of scope.

Do not invent `uipath:caseManagement` payloads without a dedicated case-management contract. Preserve imported `uipath:caseManagement` and unknown generic `uipath:Activity` payloads unless the edit explicitly normalizes them.

## Non-Integration-Service task shells

> Copyable minimal XML shell per wrapper: [wrapper-shells.md](wrapper-shells.md).

The model may author placeholder-safe shells for documented non-Integration-Service task types when it has enough user intent and no private identifiers are embedded. Choose the BPMN wrapper first:

- `BPMN.Variables`
- `BPMN.ScriptTask` as `bpmn:scriptTask` with script CDATA, `uipath:scriptVersion`, and mapping metadata.
- `Actions.HITL` as `bpmn:userTask`.
- `Orchestrator.StartJob`, `Orchestrator.StartAgentJob`, `Orchestrator.ExecuteApiWorkflowAsync`, `Orchestrator.CreateAndWaitForQueueItem`, and `A2A.AgentExecution` as `bpmn:serviceTask`.
- `Orchestrator.CreateQueueItem` as `bpmn:sendTask`.
- `Orchestrator.BusinessRules` as `bpmn:businessRuleTask`.
- `Orchestrator.StartAgenticProcess`, `Orchestrator.StartAgenticProcessAsync`, `Orchestrator.StartCaseMgmtProcess`, and `Orchestrator.StartCaseMgmtProcessAsync` as `bpmn:callActivity`.
- `Maestro.ReceiveMessageEvent` and `Maestro.SendMessageEvent` as message event wrappers.
- `Maestro.CasePlanScheduler` only when a dedicated case-management contract is available; otherwise preserve imported XML.

Keep resource identity fields synthetic or placeholder-based until CLI or user-provided public-safe data resolves them.

For copyable minimal XML shells, read [wrapper-shells.md](wrapper-shells.md)
before authoring a task wrapper.

### Script-task body rule

A `<bpmn:script>` body on `bpmn:scriptTask` is only valid when the task also
carries UiPath script metadata. `uip maestro bpmn validate` accepts the body
when **at least one** of these extension elements is present inside
`<bpmn:extensionElements>`:

- `<uipath:scriptVersion value="v3" />` (preferred for new tasks; `v2` is
  preserve-only on imports)
- `<uipath:mapping>` containing `<uipath:type value="BPMN.ScriptTask" version="v1" />`
- `<uipath:mapping>` containing `<uipath:type value="BPMN.Variables" version="v1" />`

Without one of those, the validator rejects the body. If the task does not
need to execute JavaScript, drop the `<bpmn:script>` and express the logic as
a `BPMN.Variables` output mapping on a generic `bpmn:task`, or as a condition
on a downstream gateway.

## CLI-owned or CLI-enriched areas

The CLI must generate, enrich, or validate these before upload, debug, publish, or deploy:

- Integration Service activity operation metadata.
- Integration Service trigger metadata and trigger property bindings.
- Connection binding resources and connector metadata.
- Dynamic input/output schemas for connectors, event triggers, unified HTTP, external agents, external workflows, API workflows, and generated outputs.
- `bindings_v2.json`, including deduped resources and metadata.
- `entry-points.json`, including schema extraction from root variables and entry point file wiring.
- `operate.json`, including project ID, main file, content type, target framework, and runtime options.
- `package-descriptor.json`, including manifest entries for BPMN and generated JSON.
- Package identifiers and final package paths.
- XML parse validation with the UiPath moddle descriptor.
- Maestro validation parity for connections, gateways, start events, subprocess crossing, boundary errors, required fields, assignment-free expressions, variables, and resource references.
- Project scaffolding and canonical BPMN filename selection.

## Validation expectations

Validation should report:

- XML parse errors.
- Missing or orphaned BPMN diagrams.
- Missing shape/edge geometry for rendered elements.
- Invalid root variables, bindings, migration metadata, or UiPath transaction-root markers.
- Duplicate or invalid entry point IDs.
- Entry point variables whose `elementId` does not match the start event.
- Context binding expressions that do not resolve to root bindings.
- Missing required service-type context/input fields.
- Illegal sequence-flow or message-flow connections.
- Gateway split/default-flow issues.
- Multiple blank starts in a single scope.
- Invalid event subprocess starts.
- Invalid or duplicate error references.
- Expressions with assignment operators in fields that require read-only expression evaluation.
- Output references that do not match root or scoped variables.
- Unresolved solution resources when validating inside a solution context.

## Migration behavior

Prefer current extension shapes instead of relying on import migrations. Preserve existing `uipath:migrationVersion` values, including numeric values like `5`, `11`, and `11.5`, and preserve unknown extension payloads such as generic `uipath:Activity`. Warn on old or unknown migrations unless the file cannot be interpreted.
