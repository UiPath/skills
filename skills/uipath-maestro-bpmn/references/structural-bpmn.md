# Structural BPMN (what the registry does not emit)

The registry's `xmlTemplate`s give you the `uipath:*` payload for each node
(see [registry-workflow.md](registry-workflow.md)). They do **not** give you the
structural BPMN that holds those nodes together. This file is the ground truth
for everything you author by hand around the templates.

Two sources define the contract:

- the registry spec `bpmn-spec.json` — enumerates which BPMN element types and
  event definitions exist, via its `bpmnElements` section;
- the Studio Web canvas serializer
  (`PO.Frontend/src/services/serialization/`) — defines how that XML must be
  shaped to import and round-trip.

Where the registry stops, the canvas serializer is authoritative. Each
gap below is labelled **REGISTRY GAP** — the registry exposes no template for
it, so author it from this reference.

## The document scaffold (REGISTRY GAP)

The registry emits no `<bpmn:definitions>` / `<bpmn:process>` root and no
namespace declarations. Author this shell yourself. The canvas import detector
(`exporter.ts`) requires: a root `<…:definitions>` carrying a BPMN-spec
namespace, at least one `<bpmn:process>`, and (to render) a
`<bpmndi:BPMNDiagram>`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions
    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
    xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
    xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
    xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:uipath="http://uipath.org/schema/bpmn"
    id="Definitions_1" targetNamespace="http://bpmn.io/schema/bpmn"
    exporter="UiPath (https://bpmn.uipath.com)" exporterVersion="1.0">
  <bpmn:process id="Process_1" isExecutable="true">
    <!-- variables, flow nodes, sequence flows -->
  </bpmn:process>
  <bpmndi:BPMNDiagram id="Diagram_1">
    <bpmndi:BPMNPlane id="Plane_1" bpmnElement="Process_1">
      <!-- one BPMNShape per node, one BPMNEdge per flow -->
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
```

The `uipath:` namespace URI is exactly `http://uipath.org/schema/bpmn`. All
`uipath:*` tags inside `extensionElements` are lower-camelCase
(`uipath:activity`, `uipath:variables`, `uipath:loopCharacteristics`, …).

## Variables (`BPMN.Variables`)

Declare root variables with the `BPMN.Variables` registry template attached to
the process via `extensionElements`, or use the canvas `<uipath:variables>`
block directly. Variable bodies are CDATA. Reference variables in expressions as
`vars.<id>` — see [expression-authoring.md](expression-authoring.md).
Sub-process-scoped variables go in that sub-process's own `<uipath:variables>`.

## Sequence flows, conditions, and gateway defaults (REGISTRY GAP)

The registry never emits `<bpmn:sequenceFlow>`, conditions, or the gateway
`default` attribute. Author all of them.

- A flow: `<bpmn:sequenceFlow id="Flow_1" sourceRef="A" targetRef="B" />`. The
  source/target nodes must also list `<bpmn:incoming>`/`<bpmn:outgoing>`
  (the registry templates leave `{incomingEdge}`/`{outgoingEdge}` placeholders
  for exactly these).
- Conditional flow body: `<bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=vars.Var_X == "approved"</bpmn:conditionExpression>`.
  The canvas normalizes the body to start with `=` — always lead with `=`.
- Gateway default flow: set `default="Flow_else"` on the gateway element, and
  give that flow no condition.

## Gateways

All gateway types in `bpmnElements.gateways` are supported by the canvas:
`bpmn:ExclusiveGateway`, `bpmn:ParallelGateway`, `bpmn:InclusiveGateway`,
`bpmn:EventBasedGateway`, `bpmn:ComplexGateway`.

- **Exclusive (XOR)**: each non-default outgoing flow needs a
  `conditionExpression`; exactly one outgoing flow is the `default`. (Validator
  rule `MISSING_CONDITION_EXPRESSION`.)
- **Parallel (AND)**: fork = one in, many out; join = many in, one out. No
  conditions.
- **Inclusive (OR)**: conditions on outgoing flows; multiple may be taken.
- **Event-based**: routes to the first of several catch events / receive tasks
  to fire; its outgoing flows target intermediate catch events or receive tasks.
- A gateway with exactly one incoming and one outgoing flow is rejected
  (`SUPERFLUOUS_GATEWAY`). Activities/events must not have more than one
  incoming flow — join with a gateway, not a "fake join" (`FAKE_JOIN`).

## Events and the event-definition matrix

`bpmn-spec.json` `bpmnElements.events` enumerates which event definitions each
event element accepts. The canvas serializer
(`event-definition.ts`) reads/writes the payload of Timer, Message, Error,
Signal, and Escalation definitions; Conditional/Link/Compensate/Terminate
round-trip structurally but carry no special payload.

| Event element | Accepted event definitions |
| --- | --- |
| `bpmn:StartEvent` | none, Message, Timer, Conditional, Signal |
| `bpmn:IntermediateThrowEvent` | none, Message, Escalation, Signal, Link, Compensate |
| `bpmn:IntermediateCatchEvent` | Message, Timer, Escalation, Signal, Conditional, Link, Compensate |
| `bpmn:EndEvent` | none, Message, Escalation, Error, Compensate, Signal, Terminate |
| `bpmn:BoundaryEvent` | Message, Timer, Escalation, Conditional, Error, Signal, Compensate |

Payload shapes the canvas serializes:

- **Timer**: `<bpmn:timerEventDefinition><bpmn:timeDuration xsi:type="bpmn:tFormalExpression">PT30M</bpmn:timeDuration></bpmn:timerEventDefinition>`
  (or `timeDate` / `timeCycle`). Static durations must be valid ISO-8601;
  week designators (`PnW`) are unsupported. Expression-mode (`=…`) is allowed.
- **Message**: `<bpmn:messageEventDefinition messageRef="Message_1" />` with a
  `<bpmn:message id="Message_1" name="…"/>` declared at definitions level. The
  Maestro internal-message events (`Maestro.ReceiveMessageEvent` /
  `Maestro.SendMessageEvent`) carry the `uipath:event` payload **and** a bare
  `<bpmn:messageEventDefinition />` (see their registry templates).
- **Error**: `<bpmn:errorEventDefinition errorRef="Error_1" />` with a
  `<bpmn:error id="Error_1" name="…" errorCode="…"/>` at definitions level. An
  error end event with no `errorRef` fails to parse at runtime
  (`ERROR_END_EVENT_MISSING_EXCEPTION`); an error referenced by a boundary event
  must declare an `errorCode` (`ERROR_BOUNDARY_EVENT_REQUIRES_ERROR_CODE`).
- **Signal**: `<bpmn:signalEventDefinition signalRef="Signal_1" />` with a
  definitions-level `<bpmn:signal/>`.
- **Escalation**: `<bpmn:escalationEventDefinition escalationRef="Escalation_1" />`.
- **Conditional / Link / Compensate / Terminate**: emit the bare definition
  element (e.g. `<bpmn:terminateEventDefinition />`); the canvas round-trips it.

### Boundary events (REGISTRY GAP for `attachedToRef` / `cancelActivity`)

A boundary event attaches to an activity and catches an event on it. The
registry exposes no boundary template; author it:

```xml
<bpmn:boundaryEvent id="Boundary_Timeout" attachedToRef="Task_DoWork" cancelActivity="true">
  <bpmn:timerEventDefinition>
    <bpmn:timeDuration xsi:type="bpmn:tFormalExpression">PT15M</bpmn:timeDuration>
  </bpmn:timerEventDefinition>
  <bpmn:outgoing>Flow_OnTimeout</bpmn:outgoing>
</bpmn:boundaryEvent>
```

- `attachedToRef` = id of the activity it sits on. The boundary event and that
  activity must be `flowElements` of the same parent scope.
- `cancelActivity="true"` = interrupting (default); `cancelActivity="false"` =
  non-interrupting. Per the spec, non-interrupting is available for
  Message/Timer/Escalation/Conditional/Signal — **not** Error or Compensate.
- Only one catch-all (no `errorRef`) error boundary event per task, and no two
  error boundary events with the same error code on one task
  (`MULTIPLE_CATCH_ALL_BOUNDARY_EVENTS_ON_TASK`,
  `DUPLICATE_ERROR_BOUNDARY_EVENT_ON_TASK`).

## Subprocess, call activity, event subprocess (REGISTRY GAP for structure)

- **SubProcess** (`bpmn:SubProcess`): a container with its own nested
  `flowElements` (start event, nodes, end event) and its own scoped
  `<uipath:variables>`. Variants: `collapsed`, `expanded`, `eventSubprocess`.
  The shape carries `isExpanded` for the collapsed/expanded distinction.
- **Event subprocess**: a `bpmn:SubProcess` with `triggeredByEvent="true"`. Its
  start event carries an event definition and an `isInterrupting` flag.
- **Call activity** (`bpmn:CallActivity`): invokes a *separate* Maestro
  instance. The registry provides the `uipath:activity` payload for the
  Orchestrator agentic/case-management call-activity types
  (`Orchestrator.StartAgenticProcess[Async]`, `…CaseMgmtProcess[Async]`). A
  plain BPMN `calledElement` round-trips but is not specially authored by the
  canvas layer.
- Each scope (process or sub-process) may have at most one blank (untyped) start
  event (`MULTIPLE_BLANK_START_EVENTS`).

> SubProcess scopes operations *within the same instance*; CallActivity invokes
> a *separate* Maestro instance. Do not conflate them.

## Multi-instance / loop characteristics (REGISTRY GAP — canvas supports it)

The registry spec enumerates **no** multi-instance or loop markers
(`grep` for `multiInstance`/`loopCharacteristics` in `bpmn-spec.json` returns
nothing). This is a genuine registry gap. The Studio Web canvas, however, **does**
serialize them (`elements/nodes.ts`), so author them from the canvas contract:

```xml
<bpmn:multiInstanceLoopCharacteristics isSequential="true">
  <bpmn:completionCondition xsi:type="bpmn:tFormalExpression">=vars.Var_Done</bpmn:completionCondition>
  <bpmn:extensionElements>
    <uipath:loopCharacteristics version="v1"
        inputCollection="=vars.Var_Items" inputElement="item" />
  </bpmn:extensionElements>
</bpmn:multiInstanceLoopCharacteristics>
```

- `isSequential="true"` = one at a time; `false` = parallel.
- The collection/item binding lives in the `uipath:loopCharacteristics`
  extension (`inputCollection`, `inputElement`), **not** in `loopCardinality`
  (the canvas never reads `loopCardinality`).
- Inside the body, read the current item with the `iterator` namespace — see
  [expression-authoring.md](expression-authoring.md).
- `bpmn:standardLoopCharacteristics` is also recognized (no uipath extension).

Because the registry exposes no template for this, treat it as a documented
authoring path backed by the canvas serializer, and tell the user it is a
registry gap if they ask why no `registry get` covers it.

## Diagram interchange — `bpmndi` (REGISTRY GAP — always generated)

The registry emits no diagram. Import is **diagram-driven**: the canvas builds
nodes from `BPMNShape`s and edges from `BPMNEdge`s, not by walking
`flowElements`. **A node with no shape is invisible; a flow with no edge is
dropped.** You must generate the full `BPMNDiagram` yourself.

- One `<bpmndi:BPMNShape id="S_<nodeId>" bpmnElement="<nodeId>">` per node, with
  `<dc:Bounds x= y= width= height= />`. SubProcess shapes carry `isExpanded`.
- One `<bpmndi:BPMNEdge id="BPMNEdge_<flowId>" bpmnElement="<flowId>">` per
  sequence flow, with `<di:waypoint x= y= />` points.
- Lay nodes out left-to-right with non-overlapping bounds. Typical sizes: tasks
  100×80, events 36×36, gateways 50×50.

Example:

```xml
<bpmndi:BPMNShape id="S_StartEvent_1" bpmnElement="StartEvent_1">
  <dc:Bounds x="160" y="100" width="36" height="36" />
</bpmndi:BPMNShape>
<bpmndi:BPMNEdge id="BPMNEdge_Flow_1" bpmnElement="Flow_1">
  <di:waypoint x="196" y="118" />
  <di:waypoint x="260" y="118" />
</bpmndi:BPMNEdge>
```

## Validation

There is **no** `uip maestro bpmn validate` CLI command. Validate with a
well-formed-XML parse plus the structural checklist below. The checklist mirrors
the canvas serializer's blocking rules (gateway/condition, fake-join,
superfluous-gateway, error end/boundary event, timer-duration,
single-blank-start, variable-reference, and IS-connector checks referenced
above).

Parse for well-formedness first:

```bash
python3 -c "import xml.etree.ElementTree as ET; ET.parse('<file.bpmn>')"
```

Then walk the structural checklist:

1. Root is `<…:definitions>` with the BPMN + `uipath` namespaces.
2. Exactly one `<bpmndi:BPMNDiagram>` with a shape per node and an edge per flow.
3. Every `sourceRef`/`targetRef`/`attachedToRef`/`*Ref` resolves to a declared id.
4. Each XOR gateway: non-default flows have conditions; exactly one default.
5. No activity/event has more than one incoming flow.
6. Every `vars.<id>` reference resolves to a declared variable.
7. Each `uipath:*` payload was produced from a `registry get` template, not
   hand-written.
