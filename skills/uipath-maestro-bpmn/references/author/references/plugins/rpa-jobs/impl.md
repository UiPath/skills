# RPA Job Implementation

This document defines the implementation boundary for RPA job task recipes. RPA jobs are implemented as `bpmn:serviceTask`; see [task-recipes/rpa-job.md](../../task-recipes/rpa-job.md).

Use the canonical shell from
[shared/wrapper-shells.md](../../../../shared/wrapper-shells.md): a
`bpmn:serviceTask` containing `uipath:activity version="v1"` and nested
`uipath:type value="Orchestrator.StartJob" version="v1"`, with job arguments
and outputs as direct `uipath:activity` children.

## Model-owned implementation

The model may edit:

- `bpmn:serviceTask` wrapper for RPA job execution.
- Documented `Orchestrator.StartJob` `uipath:activity` shell.
- Input CDATA for job arguments in `uipath:activity` using `vars.<variableId>` references.
- `uipath:activity` outputs for job result, status, outputs, and exception fields.
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
- Outputs map to declared writable variable ids.
- No release keys, folder IDs, robot names, or exported private metadata are committed.
