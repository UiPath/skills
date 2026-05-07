# Queue Implementation

This document defines the implementation boundary for queue tasks.

## Model-owned implementation

The model may edit:

- Service task wrapper for queue item creation.
- Documented `Orchestrator.CreateQueueItem` `uipath:activity` shell.
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
- Payload fields come from declared variables or literals.
- Outputs map to declared writable variables.
- Duplicate reference and unavailable-resource paths are modeled when required.
