# HITL Implementation

This document defines the implementation boundary for HITL task recipes. HITL is implemented as `bpmn:userTask`; see [task-recipes/hitl.md](../../task-recipes/hitl.md).

Use the canonical shell from
[shared/wrapper-shells.md](../../../../shared/wrapper-shells.md): a
`bpmn:userTask` containing `uipath:activity version="v1"` and nested
`uipath:type value="Actions.HITL" version="v1"`, with task data and result
movement in sibling `uipath:mapping`.

## Model-owned implementation

The model may edit:

- `bpmn:userTask` wrapper for human work.
- Documented `Actions.HITL` `uipath:activity` shell.
- Input body CDATA in `uipath:mapping` using synthetic payload fields.
- `uipath:mapping` outputs for action result, completed fields, comments, and decision values.
- Boundary timeout/error events and post-task gateways.

## Operator or CLI-owned implementation

The operator or tooling must resolve:

- Real Action Center app, form, folder, queue, group, or assignee references.
- Dynamic form schemas and generated resources.
- Tenant-specific routing and notification metadata.

## Validation expectations

- Task inputs and outputs reference declared variables.
- Outcome gateway conditions match possible result values.
- Timeout paths do not discard required process state.
- Binding references are placeholders or resolved generated resources.
- No personal names, emails, tenant URLs, or exported form payloads are committed.
