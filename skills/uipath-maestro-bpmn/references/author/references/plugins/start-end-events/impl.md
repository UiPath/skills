# Start, End, and Event Implementation

This document defines the implementation boundary for BPMN events.

## Model-owned implementation

The model may edit:

- `bpmn:startEvent`, `bpmn:endEvent`, `bpmn:intermediateCatchEvent`, `bpmn:intermediateThrowEvent`, and `bpmn:boundaryEvent`.
- Standard event definitions such as timer, message, error, and terminate end events where supported.
- Event IDs, names, `attachedToRef`, `cancelActivity`, incoming/outgoing flows, and BPMN DI.
- Root `uipath:entryPointId` values for root starts.
- `uipath:mapping` entries for event input/output movement.
- Documented non-Integration-Service `uipath:event` shells such as Maestro message events.

Message event boundaries:

- Use `Maestro.ReceiveMessageEvent` for model-owned message starts, intermediate catches, and boundary waits when the message name and payload contract are known.
- Use `Maestro.SendMessageEvent` for model-owned message throws and message end events when the message name and payload contract are known.
- Use `Intsvc.EventTrigger` and `Intsvc.WaitForEvent` only through CLI enrichment because connector event metadata, bindings, trigger properties, and schemas are registry-backed.

Boundary event flow rules:

- A boundary event has no incoming flow.
- A boundary event lists each exception/timeout sequence flow as its own
  `bpmn:outgoing` child.
- The attached activity lists only its normal incoming and outgoing flows. Do
  not add boundary-event exception flows as normal activity incoming or
  outgoing flows.
- The exception sequence flow uses `sourceRef` equal to the boundary event ID
  and `targetRef` equal to the recovery or review target.
- Error boundary events must reference a declared root `bpmn:error`.
- Add BPMN DI for the boundary event shape and for each outgoing exception
  sequence flow.

## CLI-owned or externally resolved implementation

The CLI or operator must resolve:

- Integration Service trigger and wait metadata.
- Trigger property bindings and generated schemas.
- Real connection, folder, queue, or external-system identifiers.
- Cloud-side subscription, schedule, or correlation resources.

## Validation expectations

- Root runnable starts have unique entry point IDs.
- Entry point variables reference the owning start event.
- Event subprocesses have exactly one valid start event.
- Boundary events attach to an activity in the same scope.
- Boundary events have outgoing sequence flow children for their exception
  paths, and the attached activity does not list those exception flows as
  normal incoming/outgoing activity flows.
- Message and error references resolve.
- Every visible event and event flow has diagram geometry.

Excluded event definitions from
[supported-elements.md](../../supported-elements.md#current-generation-exclusions)
are preserve-only for imported files.
