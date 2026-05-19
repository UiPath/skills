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

For a new draft HITL node, do not add an orphan root `uipath:bindings` entry
just to represent an unresolved Action Center form or app. Keep unresolved
Action Center resources in the project notes until the operator or CLI supplies
a concrete binding contract. If a binding is authored, it must be referenced by
the task and backed by generated package metadata before Operate.

## Validation expectations

- Task inputs and outputs reference declared variables.
- Outcome gateway conditions match possible result values.
- Timeout paths do not discard required process state.
- Binding references are placeholders or resolved generated resources, and no
  unreferenced HITL binding is left in root metadata.
- No personal names, emails, tenant URLs, or exported form payloads are committed.
