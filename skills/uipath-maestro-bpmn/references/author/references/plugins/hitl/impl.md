# HITL Implementation

This document defines the implementation boundary for HITL tasks.

## Model-owned implementation

The model may edit:

- `bpmn:serviceTask` wrapper for human work.
- Documented `Actions.HITL` `uipath:activity` shell.
- Input body CDATA using synthetic payload fields.
- Output mappings for action result, completed fields, comments, and decision values.
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
