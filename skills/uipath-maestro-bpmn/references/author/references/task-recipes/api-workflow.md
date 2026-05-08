# API Workflow Recipe

Use `bpmn:serviceTask` with `Orchestrator.ExecuteApiWorkflowAsync` for API workflow invocation.

The model may draft:

- Service task wrapper and BPMN DI.
- Request variables, response variables, status/error variables, and mappings.
- Public-safe request body examples and boundary error paths.

CLI or operator must resolve:

- API workflow resource identity, folder binding, and generated package resources.
- Dynamic request and response schemas.
- Fire-and-forget versus wait behavior when the product contract exposes that choice.

Stop before Operate when workflow binding, schema, or wait behavior is unresolved.
