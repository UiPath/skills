# Queue Implementation

This document defines the implementation boundary for queue task recipes. See [task-recipes/queue.md](../../task-recipes/queue.md).

## Model-owned implementation

The model may edit:

- `bpmn:sendTask` wrapper for `Orchestrator.CreateQueueItem`.
- `bpmn:serviceTask` wrapper for `Orchestrator.CreateAndWaitForQueueItem`.
- Documented queue `uipath:activity` shell.
- Input CDATA for item payload, reference, priority, deadline, and transaction data.
- Output mappings for queue item ID, status, or correlation fields.
- Boundary error handling.

## CLI or operator-owned implementation

The CLI or operator must resolve:

- Real queue binding, folder scope, and generated package resources.
- Tenant-specific queue names, IDs, or folder keys.
- Queue schema or downstream callback contracts when required.

## Validation expectations

- Queue binding expression resolves.
- Payload fields come from declared variables through `vars.<variableId>` or literals.
- Outputs map to declared writable variables.
- Duplicate reference and unavailable-resource paths are modeled when required.
