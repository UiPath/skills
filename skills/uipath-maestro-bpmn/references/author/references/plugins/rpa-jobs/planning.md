# RPA Job Planning

Use this reference when planning Orchestrator RPA process execution from BPMN.

## When to use

- Starting an unattended or attended process job.
- Passing BPMN variables into an RPA process.
- Waiting for job result or routing by status.
- Handling job faults, timeouts, and business exceptions.

## Planning steps

1. Identify process, folder/resource scope, input arguments, output arguments, and wait behavior.
2. Decide if the BPMN path should continue after starting the job or wait for completion.
3. Plan job ID, status, output, and error variables.
4. Add boundary timeout/error behavior and retry intent.
5. Use placeholder-safe bindings unless the operator provides public-safe resource references.
6. Hand missing RPA project creation or editing to the RPA skill; do not create it here.

## Model may draft

- Service task wrapper with documented `Orchestrator.StartJob` shell.
- Input/output mappings and error paths.
- Public-safe binding placeholders and diagram geometry.

## Stop conditions

Stop before Operate when process identity, folder binding, argument schema, or wait semantics are unresolved.
