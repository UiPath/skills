# RPA Workflow

*Exact signatures, fields, and defaults: `rpaWorkflow()`.*

Run a published robotic process and wait for its output arguments.

Signature: `rpaWorkflow({ key, name, folderPath, inputs?, returns? })`.

```ts
.step('title', rpaWorkflow({ key: releaseKey,
  name: 'RPA Workflow', folderPath: 'Shared',
  inputs: { problemId: 123 }, returns: { title: 'string' } }))
```

## Tenant contract

The release key, name, and folder must identify the same deployed process.
Inputs and returns are that process's own argument names and exact casing; the
offline SDK cannot discover their truth. Inspect the registry/process listing
and the deployed contract rather than copying values from a different folder.

## Where the job runs

The step starts an Orchestrator job, and the robot that takes it decides the
project type: serverless cloud robots run only background, cross-platform
projects (vendor documentation), and jobs a Flow starts have run on them even
where the folder also had an unattended Windows robot. So a process a Flow
starts targets the cross-platform framework unless the folder's robots are
known to be Windows. A process meant to be edited in Studio Web beside the Flow
is also XAML with VB expressions: Studio Web opens no project holding coded
workflows or C# expressions, and lists such a process with errors `20042` and
`20021` instead. A `types.file` input passed to it arrives as a job
attachment reference (`ID`, `FullName`, `MimeType`, `Metadata`), the shape the
process's file argument takes.

## Evidence boundary

Replay proves the graph with synthesized job output. Live evidence should show
a real Orchestrator job, the intended input arguments, completion, and the
returned values. Whether the robot performed the right UI/business work is a
separate assertion from job completion.

A headless `flow debug` cannot give that evidence: it starts the step as a debug
job of the solution's own project, not the deployed process, and that job fails
at start with exit code `0x33` (`Signalr agent missing protocol versions`) when
no Studio Web debugger attaches. Run the deployed flow
([operate.md](operate.md#trigger-a-deployed-process)) to prove the step.
