# Wait and Trigger Implementation

This document defines the implementation boundary for waits and triggers.

## Model-owned implementation

The model may edit:

- Timer, message, signal, conditional, and boundary event definitions.
- Receive-task or event-based-gateway structures.
- Entry point metadata for runnable starts.
- Public-safe correlation variable names and mappings.
- Non-Integration-Service message event shells when documented.

Do not duplicate message-event concepts:

- Plain BPMN message events describe process semantics.
- `Maestro.ReceiveMessageEvent` and `Maestro.SendMessageEvent` are model-owned UiPath message-event shells.
- Connector-backed waits and triggers use `Intsvc.WaitForEvent` or `Intsvc.EventTrigger` and require CLI enrichment.

## CLI-owned or operator-owned implementation

The CLI or operator must provide:

- Integration Service trigger/wait context and schemas.
- Schedule resource details when they are cloud-owned.
- Real correlation identifiers, subscriptions, and binding resources.
- Generated package files for executable triggers.

## Validation expectations

- Start triggers are valid entry points.
- Intermediate waits have a path to resume or time out.
- Boundary timers attach to valid activities.
- Event schemas and output mappings resolve.
- Connector-backed waits are enriched before upload/run.
