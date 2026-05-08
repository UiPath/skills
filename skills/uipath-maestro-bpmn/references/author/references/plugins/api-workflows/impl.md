# API Workflow Implementation

This document defines the implementation boundary for API workflow task recipes. API workflows are implemented as `bpmn:serviceTask`; see [task-recipes/api-workflow.md](../../task-recipes/api-workflow.md).

## Model-owned implementation

The model may edit:

- `bpmn:serviceTask` wrapper for API workflow execution.
- Documented `Orchestrator.ExecuteApiWorkflowAsync` `uipath:activity` shell.
- Request input CDATA using declared variables.
- Output mappings for invocation ID, status, result, and errors.
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
