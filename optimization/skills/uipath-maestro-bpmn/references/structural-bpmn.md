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

Every `uipath:activity` / `uipath:event` / `uipath:mapping` carries its node
type as a **child** element — `<uipath:type value="<Type>" version="v1" />` —
never as a `type=` attribute on the wrapper. This holds both for templated nodes
and for any shell you author or preserve by hand.

XML comments must not contain `--` (double-hyphen): it is invalid XML and the
file will fail to parse. Never paste CLI commands or flags
(`--output`, `--connection-id`) into `<!-- … -->`. Keep comments minimal.

## A complete minimal file (author from this, not from fixtures)

This is the whole shape — variables, an entry point, one node, a branch, and
the diagram — in one valid file. Author from this skeleton plus the registry
templates for your nodes. **Do not read the validator's `test/fixtures/` to
infer the pattern**; those are validator test data, and reading them is the
main reason authoring runs out of time. Swap the `scriptTask` payload for the
registry `xmlTemplate` of whatever node you need.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions
    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
    xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
    xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
    xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
    xmlns:uipath="http://uipath.org/schema/bpmn"
    id="Definitions_1" targetNamespace="http://bpmn.io/schema/bpmn"
    exporter="UiPath (https://bpmn.uipath.com)" exporterVersion="1.0">
  <bpmn:process id="Process_1" isExecutable="true">
    <bpmn:extensionElements>
      <uipath:migrationVersion version="11.5" />
      <uipath:variables version="v1">
        <uipath:inputOutput id="Var_Amount" name="Amount" type="number" />
        <uipath:inputOutput id="Var_Tier" name="Tier" type="string" />
      </uipath:variables>
    </bpmn:extensionElements>
    <bpmn:startEvent id="Start_1" name="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent>
    <bpmn:scriptTask id="Task_Tier" name="Classify" scriptFormat="JavaScript">
      <bpmn:extensionElements>
        <uipath:scriptVersion value="v3" />
        <uipath:mapping version="v1">
          <uipath:type value="BPMN.ScriptTask" version="v1" />
          <uipath:input name="args"><![CDATA[{"amount":"=vars.Var_Amount"}]]></uipath:input>
          <uipath:output name="tier" type="string" var="Var_Tier" source="=result.response" />
        </uipath:mapping>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing>
      <bpmn:script><![CDATA[return { response: amount > 1000 ? "high" : "low" };]]></bpmn:script>
    </bpmn:scriptTask>
    <bpmn:exclusiveGateway id="Gw_1" name="Tier?" default="Flow_Low">
      <bpmn:incoming>Flow_2</bpmn:incoming>
      <bpmn:outgoing>Flow_High</bpmn:outgoing><bpmn:outgoing>Flow_Low</bpmn:outgoing>
    </bpmn:exclusiveGateway>
    <bpmn:endEvent id="End_High" name="High"><bpmn:incoming>Flow_High</bpmn:incoming></bpmn:endEvent>
    <bpmn:endEvent id="End_Low" name="Low"><bpmn:incoming>Flow_Low</bpmn:incoming></bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_1" sourceRef="Start_1" targetRef="Task_Tier" />
    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_Tier" targetRef="Gw_1" />
    <bpmn:sequenceFlow id="Flow_High" sourceRef="Gw_1" targetRef="End_High">
      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">=vars.Var_Tier == "high"</bpmn:conditionExpression>
    </bpmn:sequenceFlow>
    <bpmn:sequenceFlow id="Flow_Low" sourceRef="Gw_1" targetRef="End_Low" />
  </bpmn:process>
  <bpmndi:BPMNDiagram id="Diagram_1">
    <bpmndi:BPMNPlane id="Plane_1" bpmnElement="Process_1">
      <bpmndi:BPMNShape id="S_Start" bpmnElement="Start_1"><dc:Bounds x="160" y="100" width="36" height="36" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="S_Task" bpmnElement="Task_Tier"><dc:Bounds x="250" y="78" width="100" height="80" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="S_Gw" bpmnElement="Gw_1"><dc:Bounds x="410" y="93" width="50" height="50" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="S_High" bpmnElement="End_High"><dc:Bounds x="520" y="40" width="36" height="36" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="S_Low" bpmnElement="End_Low"><dc:Bounds x="520" y="160" width="36" height="36" /></bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="E_1" bpmnElement="Flow_1"><di:waypoint x="196" y="118" /><di:waypoint x="250" y="118" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="E_2" bpmnElement="Flow_2"><di:waypoint x="350" y="118" /><di:waypoint x="410" y="118" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="E_High" bpmnElement="Flow_High"><di:waypoint x="435" y="93" /><di:waypoint x="435" y="58" /><di:waypoint x="520" y="58" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="E_Low" bpmnElement="Flow_Low"><di:waypoint x="435" y="143" /><di:waypoint x="435" y="178" /><di:waypoint x="520" y="178" /></bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
```

## Variables (`BPMN.Variables`)

Declare root variables with the `BPMN.Variables` registry template attached to
the process via `extensionElements`, or use the canvas `<uipath:variables>`
block directly. Variable bodies are CDATA. Reference variables in expressions as
`vars.<id>` — see [expression-authoring.md](expression-authoring.md).
Sub-process-scoped variables go in that sub-process's own `<uipath:variables>`.

## Script tasks (`BPMN.ScriptTask`) — Jint runtime contract

`bpmn:scriptTask scriptFormat="JavaScript"` runs under **Jint**, not Node.js or
a browser. The mapping payload comes from the `BPMN.ScriptTask` registry
template, but the runtime contract is fixed:

- Only these helpers exist: `uipath.aggregate`, `uipath._aggregate`,
  `uipath._pipe`, and a no-op `console`. No npm packages, filesystem, network,
  browser globals, or long-running async behavior. Execution envelope is ~64 MB
  / 30 s.
- Set `uipath:scriptVersion value="v3"` for new scripts; preserve an imported
  `value="v2"`. For v2+ the script returns JSON under `response`.
- Mapped `args` fields are read as **top-level identifiers** in the script body
  (`amount`, not `args.amount`); the input mapping itself stays `name="args"`
  and maps each field by variable id (`=vars.Var_Amount`).
- Map the return back through `source="=result.response"` (scalar) or
  `source="=result.response.<field>"` (object field); `var` points at a declared
  variable id (do not put the target id in `name`).
- Do not mutate `Globals.*`, `vars.*`, or process variables inside the script
  body. The supported path is: return a value from the script, then use a
  `uipath:output` mapping to write it to the declared variable. Direct mutation
  is not applied to the runtime, so the variable reads empty afterward.

```xml
<bpmn:scriptTask id="Task_RiskScore" name="Risk Score" scriptFormat="JavaScript">
  <bpmn:extensionElements>
    <uipath:scriptVersion value="v3" />
    <uipath:mapping version="v1">
      <uipath:type value="BPMN.ScriptTask" version="v1" />
      <uipath:input name="args"><![CDATA[{"amount":"=vars.Var_Amount","daysOverdue":"=vars.Var_DaysOverdue"}]]></uipath:input>
      <uipath:output name="riskScore" type="number" var="Var_RiskScore" source="=result.response" />
    </uipath:mapping>
  </bpmn:extensionElements>
  <bpmn:script><![CDATA[
var score = amount * 0.01 + daysOverdue * 2;
return { response: score };
]]></bpmn:script>
</bpmn:scriptTask>
```

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

Author these gateway types for new BPMN: `bpmn:ExclusiveGateway`,
`bpmn:ParallelGateway`, `bpmn:InclusiveGateway`, `bpmn:EventBasedGateway`.
`bpmn:ComplexGateway` round-trips structurally but is **preserve-only** — do not
generate it for new authoring (see [Do not generate for new
authoring](#do-not-generate-for-new-authoring-preserve-on-round-trip-only)).

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
event element can carry on **round-trip**. For **new authoring**, only the
**none**, **Message**, **Timer**, **Error** (on end + boundary), and
**Terminate** (on end events only) definitions are generated. Conditional,
Signal, Escalation, Compensate, Cancel, Link, multiple, and parallel-multiple
definitions are **preserve-only** — keep them when imported, but do not generate
them for new BPMN (see [Do not generate for new
authoring](#do-not-generate-for-new-authoring-preserve-on-round-trip-only)).

The matrix below is the round-trip acceptance per element; **preserve-only**
marks definitions that the skill keeps but does not author for new files.

| Event element | Authorable | Preserve-only (round-trip) |
| --- | --- | --- |
| `bpmn:StartEvent` | none, Message, Timer | Conditional, Signal |
| `bpmn:IntermediateThrowEvent` | none, Message | Escalation, Signal, Link, Compensate |
| `bpmn:IntermediateCatchEvent` | Message, Timer | Escalation, Signal, Conditional, Link, Compensate |
| `bpmn:EndEvent` | none, Message, Error, Terminate | Escalation, Compensate, Signal |
| `bpmn:BoundaryEvent` | Message, Timer, Error | Escalation, Conditional, Signal, Compensate |

Payload shapes the canvas serializes:

- **Timer**: `<bpmn:timerEventDefinition><bpmn:timeDuration xsi:type="bpmn:tFormalExpression">PT30M</bpmn:timeDuration></bpmn:timerEventDefinition>`
  (or `timeDate` / `timeCycle`). Static durations must be valid ISO-8601;
  week designators (`PnW`) are unsupported. Expression-mode is allowed and
  accepts either prefix — `=…` or `@…`.
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
- **Terminate** (end events only): emit the bare
  `<bpmn:terminateEventDefinition />`.

Preserve-only payloads — keep these when imported, but do not author them for
new files:

- **Signal**: `<bpmn:signalEventDefinition signalRef="Signal_1" />` with a
  definitions-level `<bpmn:signal/>`.
- **Escalation**: `<bpmn:escalationEventDefinition escalationRef="Escalation_1" />`
  with a `<bpmn:escalation id="Escalation_1" name="…" escalationCode="…"/>`
  declared at definitions level (parallel to message/error/signal).
- **Conditional / Link / Compensate**: the bare definition element; the canvas
  round-trips it.

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

### Retry and error mapping (REGISTRY GAP)

UiPath-specific retry and error-mapping metadata live inside an activity's
`extensionElements`. The error **code** lives on the declared
`bpmn:error errorCode="…"`; `uipath:*` elements reference it through `errorRef`.

```xml
<uipath:retry maxRetryCount="2" retryBackoff="PT30S" retryBackoffType="exponential"
              maxDuration="PT5M" exponentialBase="2" retryAllErrors="false">
  <uipath:errorDefinition errorRef="Error_ServiceUnavailable" />
</uipath:retry>
<uipath:errorMapping version="v1">
  <uipath:error id="Mapped_ServiceUnavailable" errorRef="Error_ServiceUnavailable"
                priority="1" condition="=vars.error.code == &quot;SERVICE_UNAVAILABLE&quot;"
                detail="Service unavailable" retryable="true" />
</uipath:errorMapping>
```

- `uipath:retry` attributes: `maxRetryCount`, `retryBackoff`, `retryBackoffType`,
  `maxDuration`, `exponentialBase`, `retryAllErrors`. Do not use stale aliases
  (`maxAttempts`, `interval`).
- `uipath:error` (mapping) fields: `id`, `errorRef`, `priority`, `condition`,
  `detail`, `retryable` (`true`/`false`). Conditions read the runtime error via
  `vars.error` and contain no assignments. Do not put `code=` on `uipath:error`;
  model the code on `bpmn:error errorCode` and reference via `errorRef`.

## Subprocess, call activity, event subprocess (REGISTRY GAP for structure)

- **SubProcess** (`bpmn:SubProcess`): a container with its own nested
  `flowElements` (start event, nodes, end event) and its own scoped
  `<uipath:variables>`. Variants: `collapsed`, `expanded`, `eventSubprocess`.
  The shape carries `isExpanded` for the collapsed/expanded distinction.
- **Event subprocess**: a `bpmn:SubProcess` with `triggeredByEvent="true"`. It
  must have **exactly one** start event, and that start event **must carry an
  event definition** (with `isInterrupting`) — a blank start event is invalid for
  an event subprocess.
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
    <uipath:loopCharacteristics
        inputCollection="=vars.Var_Items" inputElement="item" />
  </bpmn:extensionElements>
</bpmn:multiInstanceLoopCharacteristics>
```

- `isSequential="true"` = one at a time; `false` = parallel.
- The collection/item binding lives in the `uipath:loopCharacteristics`
  extension (`inputCollection`, `inputElement`), **not** in `loopCardinality`
  (the canvas never reads `loopCardinality`).
- The loop element **must declare `inputElement`** — do not rely on reading a
  bare `iterator`/`iterator.item` downstream without it. For a multi-instance
  **subprocess** body, bind `inputElement="iterator[0]"` on
  `uipath:loopCharacteristics` and pass the current item into body activities
  with `=iterator[0].item`. Do not assume a bare alias such as `=currentItem` is
  in scope inside a marker subprocess body unless the file already uses it.
- Inside the body, read the current item with the `iterator` namespace — see
  [expression-authoring.md](expression-authoring.md).
- `bpmn:standardLoopCharacteristics` is also recognized (no uipath extension).

Because the registry exposes no template for this, treat it as a documented
authoring path backed by the canvas serializer, and tell the user it is a
registry gap if they ask why no `registry get` covers it.

## Do not generate for new authoring (preserve on round-trip only)

These structures are **not** authored for new Maestro BPMN. If they appear in an
imported or brownfield file, preserve them and report that the skill cannot
safely regenerate or normalize them. Planned / preview / TBD statuses count as
unsupported for generation until current tooling confirms them.

- Gateway: `bpmn:complexGateway`.
- Tasks / containers: `bpmn:manualTask`, `bpmn:adHocSubProcess`,
  `bpmn:transaction`.
- Event definitions: `conditionalEventDefinition`, `signalEventDefinition`,
  `escalationEventDefinition`, `compensateEventDefinition`,
  `cancelEventDefinition`, `linkEventDefinition`, multiple, and
  parallel-multiple event definitions.
- Markers: standard-loop and compensation markers (use only documented
  multi-instance parallel/sequential metadata for new loops).
- Terminate is supported **only** on end events — not on start, boundary,
  intermediate-catch, or intermediate-throw events.
- Preserve-only `uipath:*` extension payloads: keep these when imported, and when
  a file legitimately needs one, reproduce the shape (with synthetic, public-safe
  contents) rather than inventing a new one.
  - **Typed activity/event shells always use the lowercase `<uipath:activity>` /
    `<uipath:event>` wrapper with a `<uipath:type value="<Type>" version="v1" />`
    child** — including types not served by the live registry (e.g.
    `Maestro.CasePlanScheduler`, `Maestro.CaseManagerGuardrails`,
    `Maestro.CaseRulesEvaluator`). Do **not** substitute the capital-`A`
    `<uipath:Activity>` element for a typed shell.
  - The capital-`A` `<uipath:Activity>` element is a **separate** generic
    preserve-only payload (its own element, not a wrapper for typed shells).
  - `uipath:caseManagement` is a versioned body-string element —
    `<uipath:caseManagement version="v1">…synthetic payload…</uipath:caseManagement>`.
  - `<uipath:scriptVersion value="v2" />` is legacy: author `v3` for new scripts,
    preserve `v2` where it already exists.

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

## Editing operations

Safe, surgical edits on an existing `.bpmn` (preserve content you did not author
— see [SKILL.md](../SKILL.md#editing-an-existing-bpmn-preserve-what-you-did-not-author)):

- **Add / delete / reconnect a node**: add the element with a stable id and its
  `<bpmn:incoming>`/`<bpmn:outgoing>` refs, add the sequence-flow elements in the
  owning scope, and add/update its `BPMNShape` and edge waypoints. On delete,
  remove orphaned flows and DI edges and recheck entry-point variables, output
  mappings, and binding references.
- **Insert a gateway**: split the existing sequence flow into an incoming and an
  outgoing flow, add conditions to the outgoing flows plus one `default`, add a
  matching join only if branches actually need synchronization, then re-waypoint
  the diagram (gateway shape + all edges).
- **Move logic into a subprocess**: move only elements that share a valid scope,
  re-scope their variables, recreate legal subprocess flow boundaries, and add a
  second diagram plane for the subprocess so nested content renders.
- **Add an entry point**: use a root-level start event, add a stable unique
  `uipath:entryPointId`, and declare input/output variables whose `elementId`
  matches that start event.

Do not patch generated JSON to fix source behavior — change the `.bpmn` and
regenerate. For `Intsvc.*` activities/triggers, hand editing to CLI enrichment.

### Edit red-flags

Re-check after any edit:

- A diagram plane references a missing process, collaboration, or subprocess.
- A rendered element lacks a shape or its flow lacks an edge/waypoint.
- An entry-point variable points at the wrong start event.
- A `uipath:context` value references a missing binding.
- A topology edit rewrote unrelated `uipath:*` extension XML.
- An Integration Service element carries hand-authored connection details.

## Validation

There is **no** `uip maestro bpmn validate` CLI command. The skill ships its own
offline validator that reconstructs the PO.Frontend Node/Edge/CanvasState model
from the parsed BPMN and runs **every** canvas validation rule — run it as the
primary check:

```bash
cd skills/uipath-maestro-bpmn/validator && npm install --silent
node validate-bpmn.mjs <file.bpmn>   # prints VALID and exits 0, or prints errors and exits 1
```

`VALID` / exit 0 means the document passes all rules. Any other output lists the
blocking errors (gateway/condition, fake-join, superfluous-gateway, error
end/boundary event, timer-duration, single-blank-start, variable-reference, and
IS-connector checks). See [validator/README.md](../validator/README.md).

If Node is unavailable, fall back to a well-formed-XML parse plus the structural
checklist below — it mirrors the same blocking rules:

```bash
python3 -c "import xml.etree.ElementTree as ET; ET.parse('<file.bpmn>')"
```

Then walk the structural checklist:

1. Root is `<…:definitions>` with the BPMN + `uipath` namespaces.
2. Exactly one `<bpmndi:BPMNDiagram>` with a shape per node and an edge per flow.
3. Every `sourceRef`/`targetRef`/`attachedToRef`/`*Ref` resolves to a declared id.
4. Each XOR gateway: non-default flows have conditions; exactly one default.
5. No activity/event has more than one incoming flow.
6. Each event subprocess has exactly one start event, and it carries an event
   definition (with `isInterrupting`).
7. Every `vars.<id>` reference resolves to a declared variable.
8. Each `uipath:*` payload was produced from a `registry get` template, not
   hand-written.
