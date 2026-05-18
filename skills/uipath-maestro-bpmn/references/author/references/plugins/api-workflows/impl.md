# API Workflow Implementation

This document defines the implementation boundary for API workflow task recipes. API workflows are implemented as `bpmn:serviceTask`; see [task-recipes/api-workflow.md](../../task-recipes/api-workflow.md).

Use the canonical shell from
[shared/wrapper-shells.md](../../../../shared/wrapper-shells.md): a
`bpmn:serviceTask` containing `uipath:activity version="v1"` and nested
`uipath:type value="Orchestrator.ExecuteApiWorkflowAsync" version="v1"`,
with request and result movement in sibling `uipath:mapping`.
Do not author new API workflow XML with legacy
`<uipath:activity type="Orchestrator.ExecuteApiWorkflowAsync">` shorthand.

## Model-owned implementation

The model may edit:

- `bpmn:serviceTask` wrapper for API workflow execution.
- Documented `Orchestrator.ExecuteApiWorkflowAsync` `uipath:activity` shell.
- Request input CDATA in `uipath:mapping` using declared variables.
- `uipath:mapping` outputs for invocation ID, status, result, and errors.
- Retry and boundary error metadata when specified.

## CLI or operator-owned implementation

The CLI or operator must resolve:

- Real API workflow resource identity and folder binding.
- Dynamic request and response schemas.
- Generated binding resources and package metadata.

## Validation expectations

- Workflow binding resolves before upload/run.
- Request body matches the resolved schema.
- Output mappings target declared variables.
- Fire-and-forget versus wait behavior is explicit.
- No private endpoint URLs, resource IDs, or exported payloads are committed.
