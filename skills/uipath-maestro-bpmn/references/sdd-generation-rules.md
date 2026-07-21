# BPMN SDD generation rules

Use these rules only for the portable BPMN Solution Design Document. The SDD is
a semantic contract between process design and BPMN authoring. The SDD does not include registry XML; it does not include BPMNDI. Registry templates,
resource identifiers, and diagram coordinates are later implementation inputs.

## 1. Establish stable logical IDs

- Give the process, every node, every sequence flow, every variable, and every
  resource intent a stable, human-readable logical ID.
- Keep display names separate from IDs. Renaming a label must not force a graph
  identity change.
- Use node IDs in flow endpoints, variable producers/consumers, event
  attachments, and resource intent ownership.

## 2. Translate confirmed behavior into a graph

- Start from the confirmed trigger and identify every business outcome.
- Add a node for each observable activity, decision, event, subprocess, loop,
  or end state. Do not hide a decision inside a task description.
- Add one sequence flow for every transition. Name flows so a reviewer can
  trace conditions through gateways without inferring direction.
- Write a condition for every conditional gateway path and mark exactly one
  default path when the business design requires fallback behavior. A default
  flow is unconditional (`Always`); never mark a conditional flow as default.

### Graph integrity

The graph has integrity only when it has a declared start, reachable outcomes,
valid flow endpoints, no orphan node, and no gateway path whose condition or
default behavior is ambiguous.

## 3. Preserve data lineage

- Declare trigger inputs and process variables with compatible types.
- For each consumed variable, record the trigger or node that produces it.
- For each output, record every downstream node, event, flow condition, or end
  outcome that consumes it. A flow ID is the consumer when its condition reads
  the variable.
- State transformations and decision inputs explicitly. A gateway condition
  cannot rely on an undeclared value.

## 4. Capture resources as intent, not implementation

- Attach a resource-intent ID to every node that needs a registry-owned
  extension type, connection, process, app, agent, or queue.
- Preserve the known intended name and folder/connection hint. Mark unknown
  fields `UNRESOLVED`; do not invent an identifier or select a look-alike.
- Mark each intent `Required` or `No`. A required unresolved resource can be
  reviewed in the SDD, but blocks executable BPMN until discovery resolves it.
- Do not promote a discovered candidate to resolved status unless it matches
  the SDD intent and is confirmed where the normal registry workflow requires
  confirmation.

## 5. Describe non-linear behavior explicitly

- Record boundary events, event subprocesses, and errors with their attachment,
  trigger, interrupting behavior, and return or terminal route.
- Record subprocess parentage and loop collection, cardinality, completion, or
  retry rules. Do not imply a loop from plural wording.
- Keep exception paths visible in the flow table and name their end behavior.

## 6. Set readiness honestly

The SDD is ready for review when its graph and data lineage are complete, even
if resource discovery is pending. It is ready for executable authoring only
when every required resource intent is resolved. The next skill stage resolves
resources with the existing registry workflow, authors structural BPMN and
BPMNDI, then runs the bundled validator.
