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
  <bpmn:process id="Process_1" isExecutable="false">
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

This is the whole shape — variables, an entry point, one node, a branch, and
the diagram — in one valid file. Author from this skeleton plus the registry
templates for your nodes. **Do not reverse-engineer the pattern from full
example BPMN files** — it is the main reason authoring runs out of time. Swap
the `scriptTask` payload for the registry `xmlTemplate` of whatever node you
need.

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
  <bpmn:process id="Process_1" isExecutable="false">
    <bpmn:extensionElements>
      <uipath:migrationVersion version="15" />
      <uipath:variables version="v1">
        <uipath:input id="input_Var_Amount" name="Amount" type="number" elementId="Start_1" />
        <uipath:inputOutput id="Var_Amount" name="Amount" type="number" elementId="Start_1" />
        <uipath:output id="output_Var_Tier" name="Tier" type="string" elementId="End_1" />
        <uipath:inputOutput id="Var_Tier" name="Tier" type="string" elementId="Task_Tier" />
        <uipath:inputOutput id="Var_ScriptResponse" name="scriptResponse" type="string" elementId="Task_Tier" />
        <uipath:inputOutput id="Var_ScriptError" name="Error" type="jsonSchema" elementId="Task_Tier">{"type":"object","properties":{"code":{"type":"string"},"message":{"type":"string"},"detail":{"type":"string"},"category":{"type":"string"},"status":{"type":"number"},"element":{"type":"string"}}}</uipath:inputOutput>
      </uipath:variables>
    </bpmn:extensionElements>
    <bpmn:startEvent id="Start_1" name="Start">
      <bpmn:extensionElements>
        <uipath:mapping version="v1">
          <uipath:type value="BPMN.Variables" version="v1" />
          <uipath:output name="Amount" type="number" var="Var_Amount" source="=vars.input_Var_Amount" />
        </uipath:mapping>
      </bpmn:extensionElements>
      <bpmn:outgoing>Flow_1</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:scriptTask id="Task_Tier" name="Classify" scriptFormat="JavaScript">
      <bpmn:extensionElements>
        <uipath:mapping version="v1">
          <uipath:type value="BPMN.Variables" version="v1" />
          <uipath:context>
            <uipath:inputSchema type="jsonSchema">{"$schema":"http://json-schema.org/draft-07/schema#","type":"object","properties":{"vars":{"type":"object"},"metadata":{"type":"object"}},"required":[]}</uipath:inputSchema>
          </uipath:context>
          <uipath:input name="args" type="json" target="bodyField" value="{&quot;vars&quot;:&quot;=vars&quot;,&quot;metadata&quot;:&quot;=metadata&quot;}" />
          <uipath:output name="scriptResponse" type="string" var="Var_ScriptResponse" source="=result.response" />
          <uipath:output name="Error" type="jsonSchema" var="Var_ScriptError" source="=Error" />
          <uipath:output name="Tier" type="string" var="Var_Tier" source="=vars.Var_ScriptResponse" custom="true" />
        </uipath:mapping>
        <uipath:scriptVersion value="v3" />
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing>
      <bpmn:script>return vars.Var_Amount &gt; 1000 ? "high" : "low";</bpmn:script>
    </bpmn:scriptTask>
    <bpmn:exclusiveGateway id="Gw_1" name="Tier?" default="Flow_Low">
      <bpmn:incoming>Flow_2</bpmn:incoming>
      <bpmn:outgoing>Flow_High</bpmn:outgoing><bpmn:outgoing>Flow_Low</bpmn:outgoing>
    </bpmn:exclusiveGateway>
    <bpmn:exclusiveGateway id="Gw_Merge">
      <bpmn:incoming>Flow_High</bpmn:incoming><bpmn:incoming>Flow_Low</bpmn:incoming>
      <bpmn:outgoing>Flow_End</bpmn:outgoing>
    </bpmn:exclusiveGateway>
    <bpmn:endEvent id="End_1" name="Complete">
      <bpmn:extensionElements>
        <uipath:mapping version="v1">
          <uipath:type value="BPMN.Variables" version="v1" />
          <uipath:output name="Tier" type="string" var="output_Var_Tier" source="=vars.Var_Tier" />
        </uipath:mapping>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_End</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_1" sourceRef="Start_1" targetRef="Task_Tier" />
    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_Tier" targetRef="Gw_1" />
    <bpmn:sequenceFlow id="Flow_High" sourceRef="Gw_1" targetRef="Gw_Merge">
      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">=vars.Var_Tier == "high"</bpmn:conditionExpression>
    </bpmn:sequenceFlow>
    <bpmn:sequenceFlow id="Flow_Low" sourceRef="Gw_1" targetRef="Gw_Merge" />
    <bpmn:sequenceFlow id="Flow_End" sourceRef="Gw_Merge" targetRef="End_1" />
  </bpmn:process>
  <bpmndi:BPMNDiagram id="Diagram_1">
    <bpmndi:BPMNPlane id="Plane_1" bpmnElement="Process_1">
      <bpmndi:BPMNShape id="S_Start" bpmnElement="Start_1"><dc:Bounds x="160" y="100" width="36" height="36" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="S_Task" bpmnElement="Task_Tier"><dc:Bounds x="250" y="78" width="100" height="80" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="S_Gw" bpmnElement="Gw_1"><dc:Bounds x="410" y="93" width="50" height="50" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="S_Merge" bpmnElement="Gw_Merge"><dc:Bounds x="540" y="93" width="50" height="50" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="S_End" bpmnElement="End_1"><dc:Bounds x="660" y="100" width="36" height="36" /></bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="E_1" bpmnElement="Flow_1"><di:waypoint x="196" y="118" /><di:waypoint x="250" y="118" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="E_2" bpmnElement="Flow_2"><di:waypoint x="350" y="118" /><di:waypoint x="410" y="118" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="E_High" bpmnElement="Flow_High"><di:waypoint x="435" y="93" /><di:waypoint x="565" y="93" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="E_Low" bpmnElement="Flow_Low"><di:waypoint x="435" y="143" /><di:waypoint x="565" y="143" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="E_End" bpmnElement="Flow_End"><di:waypoint x="590" y="118" /><di:waypoint x="660" y="118" /></bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
```

## Variables (`BPMN.Variables`)

Declare root variables with the `BPMN.Variables` registry template attached to
the process via `extensionElements`, or use the canvas `<uipath:variables>`
block directly. Variable schema bodies are JSON text or CDATA. Reference
variables in expressions as `vars.<id>` — see
[expression-authoring.md](expression-authoring.md).

Public entry-point variables have a two-layer runtime contract:

- Declare a public `uipath:input` bound to the root StartEvent and a mutable
  internal `uipath:inputOutput` with the stable id used by process expressions.
  Map `=vars.<public-input-id>` to the internal id on the StartEvent.
- Declare a mutable internal `uipath:inputOutput`, plus a public
  `uipath:output` bound to the root completion EndEvent. Map the internal value
  to the public output id on that EndEvent.

Do not route directly on a public input declaration or assume an internal
variable automatically becomes an entry-point output. Alpha can accept and
complete such a file while downstream decisions see empty values or the caller
receives null outputs.

Sub-process-scoped variables go in that sub-process's own `<uipath:variables>`.
Map values needed by the parent explicitly on the `bpmn:subProcess` using a
`BPMN.Variables` output mapping; otherwise the parent/root value can remain
unset even though the inner assignment completed.

## Script tasks — Jint runtime contract

`bpmn:scriptTask scriptFormat="JavaScript"` runs under **Jint**, not Node.js or
a browser. The current Studio serializer uses a `BPMN.Variables` mapping on the
ScriptTask. Some CLI registry versions still return the older
`BPMN.ScriptTask`/empty-args template; that stale shape validates locally but
does not provide the runtime arguments. Use the current runtime contract:

- Only these helpers exist: `uipath.aggregate`, `uipath._aggregate`,
  `uipath._pipe`, and a no-op `console`. No npm packages, filesystem, network,
  browser globals, or long-running async behavior. Execution envelope is ~64 MB
  / 30 s.
- Set `uipath:scriptVersion value="v3"` for new scripts; preserve an imported
  `value="v2"`. For v2+ the script returns JSON under `response`.
- Add an input schema context for `vars` and `metadata`; add `iterator` when
  the ScriptTask itself owns a multi-instance marker. Pass the objects in
  `args` as
  `{"vars":"=vars","metadata":"=metadata"}` (plus
  `"iterator":"=iterator"` for a marker).
- Encode the `args` JSON as CDATA or as the parser-equivalent `value`
  attribute. Ordinary child text is ignored by the engine mapping parser.
- Read process variables as `vars.<stable-id>` in the script. A ScriptTask
  marker reads the current item as `iterator.item`. A ScriptTask nested in a
  multi-instance subprocess receives `=iterator[0].item` through a typed named
  argument and reads that argument; the whole `iterator` global can be null in
  the nested script runtime.
- Declare and map the standard `scriptResponse` and typed `Error` outputs.
  The Error declaration must use `name="Error"`, `type="jsonSchema"`, and
  `elementId="<script-task-id>"`. Give each script its own Error variable id
  and map by that id when several scripts create same-named scoped Error
  declarations.
- For typed object arguments and responses, declare every property that the
  script reads or downstream expressions dereference. Put each guaranteed
  property in the enclosing schema's `required` array; `properties` alone
  still permits the field to be absent.
- Map the returned object's property back through `source="=result.response"`
  (the conventional scalar property) or `source="=result.response.<field>"`
  (another object field); `var` points at a declared variable id (do not put the
  target id in `name`).
- Return the intended response directly (`return 42;` or
  `return { normalized: value };`). The runtime exposes that return under
  `result.response`; do not add another `{ response: ... }` wrapper.
- Map `scriptResponse` from `=result.response`, then map any individual process
  variables from the declared response variable. Also map `Error` from
  `=Error`.
- Do not mutate `Globals.*`, `vars.*`, or process variables inside the script
  body. The supported path is: return a value from the script, then use a
  `uipath:output` mapping to write it to the declared variable. Direct mutation
  is not applied to the runtime, so the variable reads empty afterward.

```xml
<bpmn:scriptTask id="Task_RiskScore" name="Risk Score" scriptFormat="JavaScript">
  <bpmn:extensionElements>
    <uipath:mapping version="v1">
      <uipath:type value="BPMN.Variables" version="v1" />
      <uipath:context>
        <uipath:inputSchema type="jsonSchema">{"$schema":"http://json-schema.org/draft-07/schema#","type":"object","properties":{"vars":{"type":"object"},"metadata":{"type":"object"}},"required":[]}</uipath:inputSchema>
      </uipath:context>
      <uipath:input name="args" type="json" target="bodyField" value="{&quot;vars&quot;:&quot;=vars&quot;,&quot;metadata&quot;:&quot;=metadata&quot;}" />
      <uipath:output name="scriptResponse" type="number" var="Var_ScriptResponse" source="=result.response" />
      <uipath:output name="Error" type="jsonSchema" var="Var_ScriptError" source="=Error" />
      <uipath:output name="riskScore" type="number" var="Var_RiskScore" source="=vars.Var_ScriptResponse" custom="true" />
    </uipath:mapping>
    <uipath:scriptVersion value="v3" />
  </bpmn:extensionElements>
  <bpmn:script>
var score = vars.Var_Amount * 0.01 + vars.Var_DaysOverdue * 2;
return score;
  </bpmn:script>
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
  Plain conditions use the BPMN expression grammar (`==`, `!=`, `>=`, `<=`).
  Prefix JavaScript syntax with `=js:`; for example, strict equality must be
  `=js:vars.Var_X === "approved"`, never `=vars.Var_X === "approved"`.
- A condition expression is read-only and cannot assign variables. When a
  branch must set route, failure, or other outputs, place a registry-derived
  `BPMN.Variables` task on that branch and map the outputs there before the
  paths converge.
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
  conditions. An AND join waits for a token on every active incoming path. If
  one workstream contains mutually exclusive alternatives, merge those
  alternatives with an XOR gateway inside that workstream, then connect one
  flow from that merge to the AND join. Do not connect every alternative
  directly to the AND join: only one alternative can produce a token, so the
  join deadlocks. A three-workstream fork should therefore normally have three
  incoming flows at its matching join, one from each completed workstream.
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
- An error end is abnormal termination. For an embedded subprocess, its normal
  output mapping runs only on normal completion; it does not copy child-local
  values when an error end is caught by a parent boundary. The boundary also
  cannot read the terminated child scope. Re-establish any required downstream
  business values on the parent boundary path from parent-visible state, with
  explicit gateways and Variables tasks when the recovery has business policy.

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
        inputCollection="=vars.Var_Items" version="v1" />
  </bpmn:extensionElements>
</bpmn:multiInstanceLoopCharacteristics>
```

- `isSequential="true"` = one at a time; `false` = parallel.
- The collection/item binding lives in the `uipath:loopCharacteristics`
  extension (`inputCollection`, `inputElement`), **not** in `loopCardinality`
  (the canvas never reads `loopCardinality`).
- For a root task marker, the Studio/engine contract can omit `inputElement`;
  pass `iterator` into a ScriptTask and read `iterator.item`. For a
  multi-instance **subprocess** body, bind `inputElement="iterator[0]"` on
  `uipath:loopCharacteristics` and pass the current item into body activities
  with `=iterator[0].item`. For a ScriptTask in that body, map the expression
  into its args under a typed name, for example
  `{"currentItem":"=iterator[0].item"}`, then read `currentItem` in JavaScript.
  Do not pass `{"iterator":"=iterator"}` into that nested script: live Alpha
  can bind it as null.
- Task-marker results are recorded per iteration. Do not assume that mapping a
  custom task output to an array variable creates a process-level aggregate;
  live runtime may leave that variable null. If a post-loop ScriptTask only
  needs a deterministic reduction such as the final processed item, run it
  after the sequential marker and reduce the original input collection. The
  completed marker proves every item was processed before that reducer runs.
- A subprocess marker can explicitly aggregate a custom subprocess output into
  a scoped `Collection{T}` variable. Use that canonical shape when the
  per-iteration result itself must be observed or reduced in order: map one
  scalar from the subprocess body, target the collection variable from the
  subprocess mapping, then read the completed collection after the marker.
  All of `type="Collection{T}"`, `elementId="<subprocess-id>"`, and
  `custom="true"` belong on the variable, while `custom="true"` also belongs
  on the subprocess output:

  ```xml
  <uipath:inputOutput
      id="Var_ProcessedNames"
      name="processedNames"
      type="Collection{string}"
      elementId="SubProcess_CopyItems"
      custom="true" />
  ```

  ```xml
  <uipath:output
      name="itemName"
      type="string"
      var="Var_ProcessedNames"
      source="=vars.Var_ItemResult.itemName"
      custom="true" />
  ```

  A plain `type="array"` declaration is not the marker aggregate contract.
- Inside direct body mappings, read the current item with the `iterator`
  namespace; inside nested ScriptTask code, read the mapped argument — see
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

Validate with the CLI — it runs the full PO.Frontend canvas rule set offline
(the same Node/Edge/CanvasState reconstruction and every canvas rule), plus the
deploy-readiness checks:

```bash
uip maestro bpmn validate <file.bpmn> --output json
```

Exit 0 means the document passes all rules. Exit 1 lists the blocking errors,
each with its rule code (gateway/condition, fake-join, superfluous-gateway,
error end/boundary event, timer-duration/required-field, single-blank-start,
single-conditional-outgoing-flow, variable-reference, method-parentheses,
input-type, event-object, and IS-connector checks). Warnings are reported but do
not block. If `validate` is unknown or runs only deploy-readiness checks, update
the CLI — see [cli-conventions.md](cli-conventions.md#discovery-commands-read-only-authoring-safe).

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
