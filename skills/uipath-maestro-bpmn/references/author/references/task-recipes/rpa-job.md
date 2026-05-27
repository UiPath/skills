# RPA Job Recipe

The current supported implementation wrapper for confirmed RPA process
execution is `bpmn:serviceTask` with `Orchestrator.StartJob`.

Use a complete `StartJob` context: process key, folder key, folder ID, folder
path, and process name. Resolve these values from process and folder discovery
before execution; keep examples public-safe.

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
