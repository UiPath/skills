# API Workflow Planning

Use this reference when planning API workflow execution from BPMN.

## When to use

- Calling an Orchestrator API workflow asynchronously.
- Passing structured request data to an API workflow.
- Routing based on workflow status or structured response.
- Combining API workflows with connector, agent, RPA, or HITL steps.

## Planning steps

1. Identify API workflow resource, input schema, output schema, timeout, and error behavior.
2. Decide whether execution is fire-and-forget or waits for completion.
3. Plan request variables, response variables, job/status variables, and mapping.
4. Add retries or boundary errors for transient failures.
5. Use placeholders until the API workflow binding and schemas are resolved.

## Model may draft

- Service task wrapper with documented `Orchestrator.ExecuteApiWorkflowAsync` shell.
- Input/output mappings and public-safe request examples.
- Boundary error paths and gateways.

## Stop conditions

Stop before Operate when workflow identity, schema, binding, or wait semantics are unresolved.
