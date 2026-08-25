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

BPMN XML element names are case-sensitive. Use the exact lower-camel BPMN tag
names the serializer emits, such as `<bpmn:startEvent>`,
`<bpmn:intermediateCatchEvent>`, `<bpmn:scriptTask>`, and `<bpmn:endEvent>`.
Do not use PascalCase variants like `<bpmn:IntermediateCatchEvent>`; XML accepts
them syntactically, but BPMN tools do not treat them as the same elements.

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
  <bpmn:process id="Process_1">
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

## A complete minimal file (author from this, not from examples)

This is a minimal CLI-compatible authoring scaffold with a runnable
entry-point contract: one public input, mutable process variables, one
registry-derived `BPMN.Variables` task, one public output, and complete diagram
interchange. The CLI initializer omits `isExecutable`; preserve that shape. If
existing source includes the equivalent default `isExecutable="false"`,
preserve it. Do not force `isExecutable="true"`. Author structural nodes from
this skeleton and replace the middle task with retrieved templates for the
nodes the process needs. **Do not reverse-engineer the pattern from full example
BPMN files** — it is the main reason authoring runs out of time.

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
  <bpmn:process id="Process_1">
    <bpmn:extensionElements>
      <uipath:variables version="v1">
        <uipath:input id="input_Var_Amount" name="Amount" type="double" elementId="Start_1" />
        <uipath:inputOutput id="Var_Amount" name="Amount" type="double" />
        <uipath:output id="output_Var_Echo" name="Echo" type="double" elementId="End_1" />
        <uipath:inputOutput id="Var_Echo" name="Echo" type="double" />
      </uipath:variables>
      <uipath:bindings version="v1" />
    </bpmn:extensionElements>
    <bpmn:startEvent id="Start_1" name="Start">
      <bpmn:extensionElements>
        <uipath:entryPointId value="00000000-0000-4000-8000-000000000001" />
        <uipath:mapping version="v1">
          <uipath:type value="BPMN.Variables" version="v1" />
          <uipath:output name="Amount" type="double" var="Var_Amount" source="=vars.input_Var_Amount" />
        </uipath:mapping>
      </bpmn:extensionElements>
      <bpmn:outgoing>Flow_1</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:task id="Task_Copy" name="Copy amount">
      <bpmn:extensionElements>
        <uipath:mapping version="v1">
          <uipath:type value="BPMN.Variables" version="v1" />
          <uipath:output name="Echo" type="double" var="Var_Echo" source="=vars.Var_Amount" custom="true" />
        </uipath:mapping>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_1</bpmn:incoming>
      <bpmn:outgoing>Flow_2</bpmn:outgoing>
    </bpmn:task>
    <bpmn:endEvent id="End_1" name="Complete">
      <bpmn:extensionElements>
        <uipath:mapping version="v1">
          <uipath:type value="BPMN.Variables" version="v1" />
          <uipath:output name="Echo" type="double" var="output_Var_Echo" source="=vars.Var_Echo" />
        </uipath:mapping>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_2</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_1" sourceRef="Start_1" targetRef="Task_Copy" />
    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_Copy" targetRef="End_1" />
  </bpmn:process>
  <bpmndi:BPMNDiagram id="Diagram_1">
    <bpmndi:BPMNPlane id="Plane_1" bpmnElement="Process_1">
      <bpmndi:BPMNShape id="S_Start" bpmnElement="Start_1"><dc:Bounds x="160" y="100" width="36" height="36" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="S_Task" bpmnElement="Task_Copy"><dc:Bounds x="250" y="78" width="100" height="80" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="S_End" bpmnElement="End_1"><dc:Bounds x="430" y="100" width="36" height="36" /></bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="E_1" bpmnElement="Flow_1"><di:waypoint x="196" y="118" /><di:waypoint x="250" y="118" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="E_2" bpmnElement="Flow_2"><di:waypoint x="350" y="118" /><di:waypoint x="430" y="118" /></bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
```

## Variables (`BPMN.Variables`)

Declare root variables with the `BPMN.Variables` registry template attached to
the process via `extensionElements`, or use the canvas `<uipath:variables>`
block directly. Every declaration needs a stable, unique `id`, a non-empty
user-facing `name`, and its documented `type`; do not use the name as a
substitute for the id. Expressions reference the id as `vars.<id>`. Public or
node-scoped declarations also carry the owning node's `elementId`. Variable
schema bodies are JSON text or CDATA.

```xml
<uipath:variables version="v1">
  <uipath:input id="input_ExpenseId" name="expenseId" type="string" elementId="Start_1" />
  <uipath:inputOutput id="Var_Decision" name="decision" type="string" />
</uipath:variables>
```

If a migration marker is present, its supported shape is
`<uipath:migrationVersion version="11.5" />`; the attribute is `version`, not
`value`. The CLI initializer may omit that optional marker.

Public entry-point variables have a two-layer runtime contract:

- Give each root StartEvent used as an entry point a stable unique UUID in
  `uipath:entryPointId` (generate a fresh value; do not reuse the example UUID).
  Declare each public `uipath:input` with `elementId` bound to its intended
  StartEvent and a mutable internal `uipath:inputOutput` with the stable id used
  by process expressions. Map `=vars.<public-input-id>` to the internal id on
  that StartEvent.
- Declare a mutable internal `uipath:inputOutput`, plus a public
  `uipath:output` bound with `elementId` to the root EndEvent that returns it.
  Map the internal value to the public output id on that EndEvent. If one
  public result must be returned on several normal routes, converge those
  routes on that completion event.

Do not route directly on a public input declaration or assume an internal
variable automatically becomes an entry-point output. A deployment can
complete while downstream decisions see empty values or the caller receives
null outputs.

See [expression-authoring.md](expression-authoring.md) for expression rules.
Sub-process-scoped variables go in that sub-process's own
`<uipath:variables>`.

## Script tasks — Jint authoring contract

`bpmn:scriptTask scriptFormat="JavaScript"` runs under **Jint**, not Node.js or
a browser. Discover it with registry key `BPMN.ScriptTask` and preserve the
retrieved result as evidence. When that result contains the recognized older
`<uipath:type value="BPMN.ScriptTask">` mapping, author the new node from the
bundled `extensionTypes["BPMN.ScriptTask"].xmlTemplate` in
`validator/bpmn-spec.json`. That compatibility fallback is only for the known
older built-in shape; do not use it to override an unfamiliar newer registry
template or to rewrite an existing ScriptTask.

When applying the compatibility template, keep its lookup key and serialized
discriminator distinct: retrieve `BPMN.ScriptTask`, but serialize
`<uipath:type value="BPMN.Variables" version="v1" />`. Local validation can
accept the older discriminator, so it does not prove this new-node mapping is
correct.

The following rules describe newly authored tasks using that compatibility
template. In brownfield BPMN, preserve the existing mapping discriminator and
`uipath:scriptVersion`. Preserve arguments and outputs except where the
requested edit requires a surgical change, and make that change using the
node's existing contract. Migration to a different contract requires explicit
confirmation. If runtime evidence establishes an incompatibility, present that
evidence and obtain confirmation before migrating it.

- Keep the selected template's `uipath:scriptVersion` marker on a new task.
  Treat it as a serialized field, not as the name of the overall authoring
  contract or a reason to migrate existing tasks.
- Declare a task-scoped mutable `scriptResponse` variable and a task-scoped
  mutable `Error` variable. `Error` uses `type="jsonSchema"`, the standard
  error schema, and `elementId="<script-task-id>"`.
- Add a `uipath:context/uipath:inputSchema` of type `jsonSchema` that declares
  `vars` and `metadata` as objects.
- Add `uipath:input name="args" type="json" target="bodyField"` with
  `{"vars":"=vars","metadata":"=metadata"}` in CDATA.
- Read process data in JavaScript through `vars.<stable-variable-id>`.
- Return the intended scalar or object directly. Map the standard
  `scriptResponse` output from `=result.response` and `Error` from `=Error`.
  Fill `{scriptResponseType}` with the declared response variable's exact BPMN
  type so the mapping and returned value agree.
  Downstream nodes and the completion EndEvent can read the declared
  `scriptResponse` variable directly. Only when a distinct business variable
  is needed, add a custom output that reads `=vars.<script-response-id>` and
  writes that variable.
- In BPMN variable and mapping attributes, a JSON Schema `number` result uses
  `type="double"` and an `integer` result uses `type="integer"`. Keep JSON
  Schema names inside schema bodies; structured object or array results use a
  declared `jsonSchema`. Do not use `number` or `long` as BPMN primitive
  mapping types.
- Do not add an extra `{ response: ... }` wrapper around the script return; the
  runtime already exposes the direct return beneath `result.response`.
- Do not mutate `Globals.*`, `vars.*`, or process variables in the script.
  Return a value and let output mappings write declared variables.
- Only the documented Jint helpers are available (`uipath.aggregate`,
  `uipath._aggregate`, `uipath._pipe`, and a no-op `console`). Do not use npm
  packages, filesystem, network, browser globals, timers, or long-running async
  work. The execution envelope is approximately 64 MB / 30 seconds.

```xml
<uipath:inputOutput id="Var_ScriptResponse" name="scriptResponse"
  type="double" elementId="Task_RiskScore" />
<uipath:inputOutput id="Var_ScriptError" name="Error"
  type="jsonSchema" elementId="Task_RiskScore"><![CDATA[
{"type":"object","properties":{"code":{"type":"string"},"message":{"type":"string"},"detail":{"type":"string"},"category":{"type":"string"},"status":{"type":"number"},"element":{"type":"string"}}}
]]></uipath:inputOutput>

<bpmn:scriptTask id="Task_RiskScore" name="Risk Score" scriptFormat="JavaScript">
  <bpmn:extensionElements>
    <uipath:mapping version="v1">
      <uipath:type value="BPMN.Variables" version="v1" />
      <uipath:context>
        <uipath:inputSchema type="jsonSchema"><![CDATA[{"$schema":"http://json-schema.org/draft-07/schema#","type":"object","properties":{"vars":{"type":"object"},"metadata":{"type":"object"}},"required":[]}]]></uipath:inputSchema>
      </uipath:context>
      <uipath:input name="args" type="json" target="bodyField"><![CDATA[{"vars":"=vars","metadata":"=metadata"}]]></uipath:input>
      <uipath:output name="scriptResponse" type="double" var="Var_ScriptResponse" source="=result.response" />
      <uipath:output name="Error" type="jsonSchema" var="Var_ScriptError" source="=Error" />
    </uipath:mapping>
    <uipath:scriptVersion value="v3" />
  </bpmn:extensionElements>
  <bpmn:script><![CDATA[
var score = vars.Var_Amount * 0.01 + vars.Var_DaysOverdue * 2;
return score;
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

Every root-level `bpmn:startEvent` is an entry point, whether it is manual,
timer-triggered, or connector-triggered. Give it exactly one stable GUID in
`<uipath:entryPointId value="..." />`, declared as a direct child of that start
event's own `<bpmn:extensionElements>`. Subprocess start events do not carry an
entry-point id. When replacing the initializer's manual start with a timer or
connector start, move or create the entry-point id on the replacement and
remove the manual start; do not retain a second start event.

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
  A mid-flow wait for an inbound message is a
  `<bpmn:intermediateCatchEvent>` with incoming and outgoing sequence flows,
  the registry-provided `Maestro.ReceiveMessageEvent` payload under
  `bpmn:extensionElements`, and a sibling `<bpmn:messageEventDefinition />`.
  Do not model a mid-flow receive as `bpmn:receiveTask`, `bpmn:serviceTask`, a
  start event, or the PascalCase `bpmn:IntermediateCatchEvent`.
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
    preserve-only payload (its own element, not a wrapper for typed shells). If
    a prompt asks for a generic unsupported `uipath:Activity`, preserve that
    exact capitalized tag, for example:
    `<uipath:Activity version="v1"><uipath:type value="uipath:Activity" version="v1" /></uipath:Activity>`.
    Do not encode it as lowercase `<uipath:activity>` with
    `<uipath:type value="uipath:Activity" />`; that misses the preserve-only
    payload shape.
  - `uipath:caseManagement` is a versioned body-string element —
    `<uipath:caseManagement version="v1">…synthetic payload…</uipath:caseManagement>`.
    If a prompt asks for case-management contract variants, preserve-only
    case-management payloads, or case-plan/case-management wrappers, include an
    actual lowercase `uipath:caseManagement` element with synthetic content. A
    typed `Orchestrator.StartCaseMgmtProcess*` activity shell is not the same
    payload and does not satisfy that preserve-only case-management shape.
  - Preserve existing `uipath:scriptVersion` markers. For a new ScriptTask, use
    the marker supplied by the selected live or compatibility template.

## Diagram interchange — `bpmndi` (REGISTRY GAP — always generated)

The registry emits no diagram. Import is **diagram-driven**: the canvas builds
nodes from `BPMNShape`s and edges from `BPMNEdge`s, not by walking
`flowElements`. **A node with no shape is invisible; a flow with no edge is
dropped.** Generate the full `BPMNDiagram` with `uip maestro bpmn format <file.bpmn>`.

- One `<bpmndi:BPMNShape id="S_<nodeId>" bpmnElement="<nodeId>">` per node, with
  `<dc:Bounds x= y= width= height= />`. SubProcess shapes carry `isExpanded`.
- One `<bpmndi:BPMNEdge id="BPMNEdge_<flowId>" bpmnElement="<flowId>">` per
  sequence flow, with `<di:waypoint x= y= />` points.
- Lay nodes out left-to-right with non-overlapping bounds, using the canonical
  sizes below.

### Canonical shape dimensions

These are the `dc:Bounds` `width`/`height` values the Studio Web canvas
serializes. Match them exactly so a generated diagram renders identically to a
canvas-authored one; an off-size shape imports misaligned against its neighbors.

| Element | `width`×`height` |
|---------|------------------|
| Tasks and activities — `task`, `sendTask`, `receiveTask`, `scriptTask`, `userTask`, `manualTask`, `serviceTask`, `businessRuleTask`, `callActivity` | 100×80 |
| Events — `startEvent`, `endEvent`, `intermediateCatchEvent`, `intermediateThrowEvent`, `boundaryEvent` | 36×36 |
| Gateways — `exclusiveGateway`, `inclusiveGateway`, `parallelGateway`, `eventBasedGateway`, `complexGateway` | 50×50 |
| Collapsed `subProcess` (`isExpanded="false"`) | 100×80 |
| `textAnnotation` (default) | 100×80 |
| `dataObjectReference` | 36×50 |
| `dataStoreReference` | 50×50 |

Size these to fit their contents instead of a fixed box — the shape must
enclose every element it contains, or the canvas renders children outside their
container:

- Expanded `subProcess` (`isExpanded="true"`).
- `participant` and `lane`.
- `group`.
- `textAnnotation` whose text needs more room than the 100×80 default.

`uip maestro bpmn format <file.bpmn>` emits these sizes. Preserve them when
editing a shape by hand, and never resize a fixed-size element to fit a label.

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
  owning scope. On delete, remove orphaned flows and recheck entry-point variables,
  output mappings, and binding references. Then regenerate the diagram:
  `uip maestro bpmn format <file.bpmn>`. If CLI unavailable: add/update `BPMNShape`
  and edge waypoints manually.
- **Insert a gateway**: split the existing sequence flow into an incoming and an
  outgoing flow, add conditions to the outgoing flows plus one `default`, add a
  matching join only if branches actually need synchronization. Then regenerate the
  diagram: `uip maestro bpmn format <file.bpmn>`. If CLI unavailable: re-waypoint
  manually (gateway shape + all edges).
- **Move logic into a subprocess**: move only elements that share a valid scope,
  re-scope their variables, recreate legal subprocess flow boundaries, and add a
  second diagram plane for the subprocess so nested content renders.
- **Add an entry point**: use a root-level start event, generate a stable unique
  UUID for its serializer-owned `uipath:entryPointId`, and bind that entry
  point's public inputs to it. Bind each public output to its intended root end
  event; converge routes only when they must return the same result. Bridge
  both sides through mutable process variables. Do not copy the example UUID;
  this scaffold field is not a registry-owned node payload.

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

Generate the diagram with `uip maestro bpmn format <file.bpmn>`, then validate.
Do not hand-author the diagram when the command is available.

Validation is only meaningful once coherent diagram interchange exists:
complete `BPMNDiagram` coverage, a finite-bounds `BPMNShape` with positive
width and height for every rendered node, and a `BPMNEdge` with at least two
finite waypoints for every rendered sequence flow. A semantic-only validator
can return a successful result for a no-layout file without reconstructing the
DI-driven canvas. Do not invoke `validate` until DI is complete.

After DI is complete, validate with the CLI. It runs the canvas rules offline,
plus the deploy-readiness checks:

```bash
uip maestro bpmn validate <file.bpmn> --output json
```

Exit 0 means the post-layout document passes the reported rules. Exit 1 lists
the blocking errors, each with its rule code (gateway/condition, fake-join,
superfluous-gateway, error end/boundary event, timer-duration/required-field,
single-blank-start, single-conditional-outgoing-flow, variable-reference,
method-parentheses, input-type, event-object, and IS-connector checks). Warnings
are reported but do not block. If `validate` is unknown or runs only
deploy-readiness checks, update the CLI — see
[cli-conventions.md](cli-conventions.md#discovery-commands-read-only-authoring-safe).

If the CLI is unavailable, fall back to a well-formed-XML parse plus the
structural checklist below — it mirrors the same blocking rules:

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
