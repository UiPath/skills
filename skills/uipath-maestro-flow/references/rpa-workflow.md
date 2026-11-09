# RPA Workflow

*Exact signatures, fields, and defaults: `rpaWorkflow()`.*

Run a published robotic process and wait for its output arguments.

Signature: `rpaWorkflow({ key, name, folderPath?, location?, projectId?, inputs?, returns? })`.
Published processes require `folderPath`; a sibling project in the same solution uses `location: 'in-solution'` and `projectId` instead ([below](#in-solution-sibling)).

```ts
.step('title', rpaWorkflow({ key: releaseKey,
  name: 'RPA Workflow', folderPath: 'Shared',
  inputs: { problemId: 123 }, returns: { title: 'string' } }))
```

## At a glance

Run a deployed robotic process and wait for its job result. Confirm its identity and exact argument names against the same deployed tenant resource.

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
  Register the sibling and refresh resources (`uip solution projects add`, then `uip solution resources refresh`), then
<!--skill-flavor:rpa-sibling-register:end-->
  run `uip maestro flow registry list --local --output json` from the Flow project directory. The generated `resources/solution_folder/process/process/<RpaProject>.json` maps `resource.key` to `key` and `resource.projectKey` to `projectId`. Never invent either; see [agent.md](agent.md#task-created-in-solution-coded-agent).
- **No `folderPath`.** The sibling has no folder until the solution is deployed.
- **Inputs and returns are yours to declare.** The local sibling manifest may list no arguments; use the RPA project's own argument names and casing.

`check` refuses wrong shapes: `RPA_LOCAL_NO_PROJECT_ID` (no `projectId`), `RPA_LOCAL_PROJECT_ID_NOT_GUID` (`projectId` is not the project GUID—often a key or name), `RPA_LOCAL_HAS_FOLDER` (`folderPath` also set; drop it, or drop `location` to call the published copy). `RPA_NO_FOLDER` applies only to published steps.

## Tenant contract

The release key, name, and folder must identify the same deployed process. Use that process's exact input and return argument names and casing; the offline SDK cannot discover them. Inspect the registry/process listing and deployed contract, not another folder's values.

## Where the job runs

The step starts an Orchestrator job on a robot in the process's folder. The project's target framework, fixed at creation, determines eligible robots: a serverless cloud robot runs only background, cross-platform processes ([Serverless robots](https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/executing-unattended-automations-with-serverless-robots)). Create a Flow-started process as cross-platform unless the folder's robots are known to be Windows.

A process intended for Studio Web editing beside the Flow must be XAML with VB expressions. Studio Web does not open projects containing coded workflows or C# expressions, and lists such a process with errors `20042` and `20021`.

## Evidence boundary

Replay proves the graph with synthesized job output. Live evidence should show a real Orchestrator job, intended input arguments, completion, and returned values; correct UI/business work is separate from job completion.

A headless `flow debug` cannot provide this evidence: it starts the step as a debug job of the solution's own project, not the deployed process, and fails at start with exit code `0x33` (`Signalr agent missing protocol versions`) when no Studio Web debugger attaches. Run the deployed flow ([operate.md](operate.md#trigger-a-deployed-process)) to prove the step.
