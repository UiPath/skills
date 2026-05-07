# RPA Job Implementation

This document defines the implementation boundary for RPA job tasks.

## Model-owned implementation

The model may edit:

- `bpmn:serviceTask` wrapper for RPA job execution.
- Documented `Orchestrator.StartJob` `uipath:activity` shell.
- Input CDATA for job arguments using declared variables.
- Output mappings for job ID, status, outputs, and exception fields.
- Retry, timeout, and boundary error paths.

## CLI or operator-owned implementation

The CLI or operator must resolve:

- Real process, release, folder, robot, and binding metadata.
- Generated package resources and argument schemas.
- Creation or update of the RPA automation itself.

## Validation expectations

- Process binding expression resolves.
- Argument names match the resolved process contract.
- Wait and timeout behavior is explicit.
- Outputs map to declared writable variables.
- No release keys, folder IDs, robot names, or exported private metadata are committed.
