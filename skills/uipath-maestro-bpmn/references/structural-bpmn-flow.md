# Structural BPMN: flows, gateways, events

## Sequence flows, conditions, and gateway defaults (REGISTRY GAP)

The registry never emits `<bpmn:sequenceFlow>`, conditions, or the gateway
`default` attribute. Author all of them.

- A flow: `<bpmn:sequenceFlow id="Flow_1" sourceRef="A" targetRef="B" />`. The
  source/target nodes must also list `<bpmn:incoming>`/`<bpmn:outgoing>`
  (the registry templates leave `{incomingEdge}`/`{outgoingEdge}` placeholders
  for exactly these).
- Conditional flow body: `<bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=vars.Var_X == "approved"</bpmn:conditionExpression>`.
  The canvas normalizes the body to start with `=` — always lead with `=`.
- `xsi:type` needs `xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"` on
  `bpmn:definitions`. The `init` scaffold does not declare it, and `validate`,
  `format` and `refresh` accept the unbound prefix, so only a real XML parser
  catches it: run the `ET.parse` check in [Validation](structural-bpmn-validation.md#validation).
- Gateway default flow: set `default="Flow_else"` on the gateway element, and
  give that flow no condition.

## Gateways

Author these gateway types for new BPMN: `bpmn:exclusiveGateway`,
`bpmn:parallelGateway`, `bpmn:inclusiveGateway`, `bpmn:eventBasedGateway`.
`bpmn:complexGateway` round-trips structurally but is **preserve-only** — do not
generate it for new authoring (see [Do not generate for new
authoring](structural-bpmn-round-trip.md#do-not-generate-for-new-authoring-preserve-on-round-trip-only)).

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
  incoming flow — join with a gateway, not a "fake join" (`FAKE_JOIN`). A
  join gateway is two or more in, one out; it needs no `conditionExpression`
  and no `default`, and it does not trip `SUPERFLUOUS_GATEWAY`. **`validate`
  does not report `FAKE_JOIN`** (CLI 1.204.0), so a clean run is not evidence
  that a multi-inbound activity is legal. Author the join gateway anyway.
  When a CLI starts reporting the rule, delete this caveat and the one in
  validation checklist item 5.

## Events and the event-definition matrix

Author only the definitions in the Authorable column. Keep a **preserve-only**
one when it arrives in an imported file; never generate it (see [Do not
generate for new
authoring](structural-bpmn-round-trip.md#do-not-generate-for-new-authoring-preserve-on-round-trip-only)).

| Event element | Authorable | Preserve-only (round-trip) |
| --- | --- | --- |
| `bpmn:StartEvent` | none, Message, Timer | Conditional, Signal |
| `bpmn:IntermediateThrowEvent` | none, Message | Escalation, Signal, Link, Compensate |
| `bpmn:IntermediateCatchEvent` | Message, Timer | Escalation, Signal, Conditional, Link, Compensate |
| `bpmn:EndEvent` | none, Message, Error, Terminate | Escalation, Compensate, Signal |
| `bpmn:BoundaryEvent` | Message, Timer, Error | Escalation, Conditional, Signal, Compensate |

Those rows name the spec's model types, as `bpmn-spec.json` keys them. Write the
lower-camel tag: `<bpmn:startEvent>`, `<bpmn:boundaryEvent>`, and so on.

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
  A mid-process `Maestro.ReceiveMessageEvent` wait is a
  `<bpmn:intermediateCatchEvent>` with incoming and outgoing sequence flows,
  the registry-provided payload under `bpmn:extensionElements`, and a sibling
  `<bpmn:messageEventDefinition />`. Do not model it as `bpmn:receiveTask`,
  `bpmn:serviceTask`, a start event, or the PascalCase
  `bpmn:IntermediateCatchEvent`. A connector event wait is
  `Intsvc.WaitForEvent`; hosts in
  [registry-workflow-discover.md](registry-workflow-discover.md#ootb-extension-types-29-login-free).
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
                priority="1" condition="=vars.Error.code == &quot;SERVICE_UNAVAILABLE&quot;"
                detail="Service unavailable" retryable="true" />
</uipath:errorMapping>
```

- `uipath:retry` attributes: `maxRetryCount`, `retryBackoff`, `retryBackoffType`,
  `maxDuration`, `exponentialBase`, `retryAllErrors`. Do not use stale aliases
  (`maxAttempts`, `interval`). `retryAllErrors="false"` with no
  `uipath:errorDefinition` children retries nothing at all.
- `uipath:error` (mapping) fields: `id`, `errorRef`, `priority`, `condition`,
  `detail`, `retryable` (`true`/`false`). Conditions read the runtime error via
  `vars.Error` (capital `E`, lowercase fields — see
  [expression-authoring.md](expression-authoring.md#stored-expression-shape))
  and contain no assignments. Do not put `code=` on `uipath:error`;
  model the code on `bpmn:error errorCode` and reference via `errorRef`.

### Choosing an error-handling construct

Three constructs catch failures at different scopes. A failure tries them in
order, so pick by intent:

- **`uipath:retry` on the activity** — transient failures, resolved in place.
- **Error boundary event on the activity** — recover and continue. The token
  leaves the failed step onto a branch that rejoins the main path.
- **Error event subprocess in the container** — escalate and terminate.
  Code-specific nets match before a catch-all.

Unhandled failures propagate outward container by container, so one net at
process level covers every nested subprocess. Do not author a net per
container — except inside a multi-instance iteration or a queue performer,
where per-item failures need per-item handling. There the process-level net
would end the whole instance on the first bad item, so the iteration gets its
own net, placed directly in it. An error boundary event is not a substitute:
it resumes the main path rather than ending that item. See
[composing-guide.md](patterns/composing-guide.md#scoping-the-failure-net).
