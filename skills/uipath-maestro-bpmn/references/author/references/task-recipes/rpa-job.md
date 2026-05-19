# RPA Job Recipe

Use this pass-2 recipe for confirmed RPA process execution. In pass 1, model
the automation step as process intent in the BPMN skeleton; apply this recipe
after the skeleton is chosen and the RPA node should receive UiPath metadata.

The current supported implementation wrapper is `bpmn:serviceTask` with
`Orchestrator.StartJob`.

The model may draft:

- Stable service task ID, display name, incoming/outgoing flows, and BPMN DI.
- Root variables for process inputs, job status, output arguments, and errors.
- Public-safe `uipath:activity` shell only when the required context/input/output contract is known.
- Boundary error or timeout paths and post-job gateways.

CLI or operator must resolve:

- Real process identity, release/folder binding, robot/runtime scope, and generated binding resources.
- Input/output argument schemas.
- Whether the task waits for completion or only starts the job.

Stop before Operate if process binding, folder scope, argument schema, or wait semantics are unresolved.
