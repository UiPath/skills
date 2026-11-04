# RPA Workflow

*Exact signatures, fields, and defaults: `rpaWorkflow()`.*

Run a published robotic process and wait for its output arguments.

Signature: `rpaWorkflow({ key, name, folderPath?, location?, projectId?, inputs?, returns? })`.
`folderPath` is required for a published process; a sibling project of the same solution takes `location: 'in-solution'` and `projectId` instead ([below](#in-solution-sibling)).

```ts
.step('title', rpaWorkflow({ key: releaseKey,
  name: 'RPA Workflow', folderPath: 'Shared',
  inputs: { problemId: 123 }, returns: { title: 'string' } }))
```

## At a glance

Run a deployed robotic process and wait for its job result.

Confirm identity and argument names against the same deployed tenant resource.

**Finding the key: [`or-processes.md`](or-processes.md)**

## In-solution sibling

To call an RPA project that sits in the SAME solution as the Flow (not a
deployed process), set `location: 'in-solution'` and `projectId`, and omit
`folderPath`:

```ts
.step('title', rpaWorkflow({ key: localResourceKey, name: '<RpaProject>',
  location: 'in-solution', projectId: localProjectKey,
  inputs: { problemId: 123 }, returns: { title: 'string' } }))
```

- **Where the two ids come from.**
<!--skill-flavor:rpa-sibling-register:start-->
  Register the sibling and refresh resources
  (`uip solution projects add`, then `uip solution resources refresh`), then
<!--skill-flavor:rpa-sibling-register:end-->
  run `uip maestro flow registry list --local --output json` from the Flow
  project directory. The generated
  `resources/solution_folder/process/process/<RpaProject>.json` carries the
  same pair: `resource.key` → `key`, `resource.projectKey` → `projectId`.
  Never invent either; the full recipe is in
  [agent.md](agent.md#task-created-in-solution-coded-agent).
- **No `folderPath`.** The sibling has no folder until the solution is
  deployed.
- **Inputs and returns are yours to declare.** The local manifest of an RPA
  sibling may list no arguments, so write the names and casing the RPA
  project's own arguments use.

`check` refuses the wrong shapes: `RPA_LOCAL_NO_PROJECT_ID` (no `projectId`),
`RPA_LOCAL_PROJECT_ID_NOT_GUID` (`projectId` is not the project GUID — often
the key or the name pasted by mistake), `RPA_LOCAL_HAS_FOLDER` (`folderPath`
set as well; drop it, or drop `location` to call the published copy).
`RPA_NO_FOLDER` applies to published steps only.

## Tenant contract

The release key, name, and folder must identify the same deployed process.
Inputs and returns are that process's own argument names and exact casing; the
offline SDK cannot discover their truth. Inspect the registry/process listing
and the deployed contract rather than copying values from a different folder.

## Where the job runs

The step starts an Orchestrator job on a robot of the process's folder, and the
project's target framework, fixed when the project is created, decides which
robots can take it: a serverless cloud robot runs only background,
cross-platform processes
([Serverless robots](https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/executing-unattended-automations-with-serverless-robots)).
So create a process a Flow starts as cross-platform unless the folder's robots
are known to be Windows. A process meant to be edited in Studio Web beside the
Flow is also XAML with VB expressions: Studio Web opens no project holding coded
workflows or C# expressions, and lists such a process with errors `20042` and
`20021` instead.

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
