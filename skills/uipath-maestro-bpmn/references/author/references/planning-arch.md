# Planning Architecture

Use this reference for pass 1 of BPMN authoring: create a standard BPMN skeleton that the operator can understand and confirm before execution-specific UiPath XML is filled.

## Pass 1 goal

Pass 1 produces a reviewable process shape:

- Root process or collaboration choice.
- Start events and intended entry points.
- Tasks, subprocesses, gateways, events, error boundaries, and end states.
- Sequence flows, conditions in plain process terms, and default routes.
- Diagram plane, shapes, bounds, edges, and waypoints.
- Placeholder labels or annotations for external resources that need pass 2 or CLI enrichment.

Pass 1 does not need runnable UiPath service metadata. It should be valid enough to inspect as BPMN, but it may intentionally leave executable service details unresolved.

## Intake checklist

Before drafting the skeleton, identify:

- Process trigger: manual start, schedule, message, Integration Service trigger, timer, or another process.
- Happy path steps and the owner of each step: human, BPMN script, Orchestrator process, agent, API workflow, queue, business rule, message, or connector.
- Branching conditions and whether each gateway needs a default route.
- Parallel work and join behavior.
- Subprocess boundaries and whether nested content must render in Studio Web.
- Retry and error-handling intent: boundary error, event subprocess, terminate end, or normal compensation path.
- Variables crossing entry points, subprocesses, service tasks, and end events.
- Resources that already exist versus placeholders that need discovery or CLI enrichment.

## Skeleton authoring rules

- Use one executable root `bpmn:process` by default.
- Use collaboration and pools only when the user explicitly requests cross-participant modeling.
- Prefer stable, readable IDs such as `Start_RequestReceived`, `Task_CheckEligibility`, `Gateway_Approved`, and `Flow_Check_To_Approve`.
- Keep labels public-safe and user-readable.
- Create BPMN DI while creating elements; do not leave layout as a later afterthought.
- Put conditions on outgoing sequence flows from exclusive or inclusive gateway splits.
- Keep pass 1 conditions in business-readable terms. Do not use
  Maestro runtime expressions such as `=vars.<variableId>` until pass 2 has
  declared the variables and mappings those expressions reference.
- Keep script tasks structural in pass 1. A pass 1 `bpmn:scriptTask` may have a
  readable name or documentation, but executable script bodies and
  UiPath script mappings belong in pass 2.
- Set a `default` sequence flow when the business process has a fallthrough route.
- Model errors with boundary events or event subprocesses instead of unlabeled failure branches when the runtime should handle failures structurally.
- Keep sequence flows inside their owning process or subprocess scope.

## Operator confirmation

After pass 1, summarize the shape in business terms and wait for confirmation when the change is non-trivial.

Confirmation should cover:

- Entry points and trigger type.
- Step order and major branches.
- Join semantics for parallel branches.
- Subprocess boundaries.
- Error and timeout behavior.
- Which placeholders represent Integration Service, Orchestrator, HITL, agent, queue, API workflow, or other resources.
- Any intentionally unresolved resource selection.

For small edits, confirmation can be a concise statement such as: "I changed only the timeout branch from Task_A to Event_Timeout and kept all existing variables and service metadata unchanged."

## Integration Service placeholders

When a connector activity or trigger is needed in pass 1:

- Add the surrounding BPMN element with a stable ID and public-safe label.
- Record connector intent: connector, operation/event, object, filters, required parameters, and desired outputs.
- Do not author `Intsvc.*` context, connection binding IDs, connector metadata, dynamic schemas, or generated outputs by hand.
- Mark enrichment as required before upload, debug, publish, or deploy.

For plain connectionless HTTP where the workflow owns the URL, method, payload,
and parsing, record the node as a plain HTTP candidate in pass 1 instead of
treating it as connector enrichment. After the operator confirms the skeleton,
use [task-recipes/http-request.md](task-recipes/http-request.md) only for the
pass-2 executable wrapper.

## Done state

Pass 1 is done when the operator can review the BPMN diagram and answer: "Is this the process shape we want?" without needing to inspect UiPath extension XML.
