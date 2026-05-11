# BPMN XML Contract

This document summarizes the public-safe authoring boundary for Maestro BPMN XML. It intentionally avoids raw exported BPMN, tenant data, connection identifiers, private names, URLs, or local paths.

## Baseline document

Generated BPMN must be valid BPMN 2.0 with the UiPath extension namespace.

- `bpmn:definitions` includes standard BPMN, BPMNDI, DI, DC, and the UiPath namespace.
- The UiPath namespace URI is `http://uipath.org/schema/bpmn` and the preferred prefix is `uipath`.
- Use one executable root process by default. Use collaboration/pools only when the user explicitly asks for that model.
- Studio Web import requires at least one valid `bpmndi:BPMNDiagram` with a `bpmndi:BPMNPlane`.
- Every visible flow node should have a `bpmndi:BPMNShape` with bounds.
- Every visible edge should have a `bpmndi:BPMNEdge` with waypoints.
- Conditions and scripts should use a leading `=` where Maestro expects expressions.
- UiPath extension expressions should read BPMN variables through `vars.<variableId>`,
  for example `=vars.Var_RequestId`, rather than bare names.
- CDATA is the expected representation for JSON bodies, schemas, scripts, variable schemas, custom output bodies, and case-management payload bodies.

## Supported model-authored BPMN

For the supported element map and UiPath extension wrapper table, see [author/supported-elements.md](../author/references/supported-elements.md).

The model may directly author standard BPMN structure when user intent is clear:

- Events: start, end, boundary, intermediate catch, and intermediate throw events.
- Event definitions: timer, message, signal, error, escalation, conditional, link, and terminate where supported by the runtime path.
- Gateways: exclusive, inclusive, parallel, event-based, and complex gateways.
- Tasks and activities: task, service task, send task, receive task, user task, manual task, business rule task, script task, and call activity.
- Containers: subprocess and event subprocess. Expanded subprocesses need a second diagram when nested content must render in Studio Web.
- Flow and annotation elements: sequence flow, message flow, association, data input/output association, group, text annotation, categories, messages, signals, errors, escalations, data stores, global tasks, item definitions, and resources.
- Loop markers: standard and multi-instance loop characteristics. UiPath collection/element metadata belongs under the loop characteristic extension elements.

Conservative defaults:

- Start with one root process and one blank start event unless the process needs a trigger entry point.
- Use sequence flows for routing inside one process.
- Put gateway conditions on outgoing sequence flows and set a default flow where appropriate.
- Attach boundary error events to activities and reference valid error definitions.
- Give event subprocesses exactly one start event.
- Avoid sequence flows that cross subprocess scope or pool boundaries.

## Two-pass authoring boundary

For non-trivial authoring, split generation into two passes:

- **Pass 1: BPMN skeleton** - author standard BPMN process structure, event definitions, gateway conditions, subprocess scopes, sequence/message flows, annotations, and BPMN DI. Use placeholder labels or annotations for resource intent. Preserve existing extension XML in brownfield files.
- **Operator confirmation** - confirm the process shape before filling execution-specific XML.
- **Pass 2: model-owned UiPath XML** - add root variables, entry point IDs, mappings, documented bindings, script metadata, retry/error metadata, loop metadata, and documented non-Integration-Service service shells.
- **CLI enrichment** - generate or enrich Integration Service activity/trigger payloads, connector bindings, dynamic schemas, and generated package files.

Do not combine connector selection, connection binding, dynamic schema generation, and topology rewrites in one opaque edit.

## Executable contract boundary

The current confirmed generation boundary is preserve/model-shell only for areas whose runtime contract depends on tenant state, registry metadata, or non-BPMN subscriptions. Do not add generation guidance that creates executable payloads for those areas until the contract is fixture-backed and CLI-validated.

- Signals: standard BPMN signal definitions and signal event references are model-owned XML. Runtime-executable cross-process signal subscriptions, correlation, payload schema contracts, and tenant/resource/channel bindings are outside the model-owned contract unless a dedicated CLI or operator-owned contract supplies them.
- Integration Service: model authors may create the surrounding BPMN node and document connector intent. Executable `Intsvc.*` activity/event XML, connection bindings, connector metadata, trigger property bindings, filters, parameters, and dynamic schemas require live registry-backed CLI enrichment for the target tenant before upload, debug, publish, or deploy.
- Brownfield files: preserve imported executable signal or Integration Service extension XML unless the user explicitly asks for normalization and the CLI can validate the replacement.

## UiPath extensions the model may write

Use lower-case XML aliases in examples and authoring guidance:

- Root `uipath:variables version="v1"` with input, input/output, and output variables.
- Root `uipath:bindings version="v1"` for placeholder-safe resource bindings when the binding contract is documented.
- Root-level start event `uipath:entryPointId value="..."` for runnable entry points.
- `uipath:mapping version="v1"` for `BPMN.Variables` mappings.
- `uipath:scriptVersion value="..."` for script task metadata. Prefer `v3` for new script tasks; preserve imported `v2` metadata unless the user explicitly migrates it.
- `uipath:migrationVersion version="..."` as import migration metadata to preserve, including numeric values such as `5`, `11`, and `11.5`.
- `uipath:loopCharacteristics inputCollection="..." inputElement="..."` under loop characteristic extensions.
- `uipath:retry`, `uipath:errorMapping`, and `uipath:tags` when the user gives explicit public-safe metadata.
- `uipath:activity` and `uipath:event` shells for documented non-Integration-Service service types.

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
- Invalid root variables, bindings, migration metadata, or transaction markers.
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
