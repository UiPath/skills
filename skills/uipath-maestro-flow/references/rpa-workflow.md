# RPA Workflow

*Exact signatures, fields, and defaults: `rpaWorkflow()`.*

Run a published robotic process and wait for its output arguments.

Signature: `rpaWorkflow({ key?, name, folderPath?, location?, projectId?, inputs?, inputSchema?, returns? })`.
`folderPath` is required for a published process; a sibling project of the same solution takes `location: 'in-solution'` and `projectId` instead ([below](#in-solution-sibling)).
For a published process, leave `key` out: `check` prints the `registry prepare --kind Process` command that records it, and `compile` fills it in ([Orchestrator Processes](or-processes.md#getting-the-inputs-and-outputs)). An in-solution sibling still takes `key`.
Keep `returns` for every output you read: Orchestrator usually leaves an RPA process's `ArgumentsV2` blank, so `prepare` prints `Arguments not recorded` and `compile` does not fill `returns`. Without it a read of the output is `RPA_READ_WITHOUT_RETURNS`.

```ts
.step('title', rpaWorkflow({ name: 'RPA Workflow', folderPath: 'Shared',
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

- **Or name the sibling by project** (`@uipath/maestro-builder-sdk` 6.108.0 or later): `rpaWorkflow({ location: 'in-solution', project: '<RpaProject>', inputs, returns })`. See
  [agent.md](agent.md#name-an-in-solution-sibling-by-project) for what it
  fills in, what it refuses, and when to fall back to the ids below.
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

`check` warns on `RPA_LOCAL_NO_PROJECT_ID` (no `projectId`; the call resolves by
`key`, so a decompiled step without one is fine as is) and refuses
`RPA_LOCAL_PROJECT_ID_NOT_GUID` (`projectId` is not the project GUID — often
the key or the name pasted by mistake), `RPA_LOCAL_HAS_FOLDER` (`folderPath`
set as well; drop it, or drop `location` to call the published copy).
`RPA_NO_FOLDER` applies to published steps only. If `check` reports `RPA_LOCAL_NO_PROJECT_ID` as an error (an older SDK),
add `projectId` from `resource.projectKey`.
Still set `projectId` on a step you author: Studio Web's Run node reads it
to deploy the sibling first.

## Tenant contract

The release key, name, and folder must identify the same deployed process.
Inputs and returns are that process's own argument names and exact casing; the
offline SDK cannot discover their truth. Inspect the registry/process listing
and the deployed contract rather than copying values from a different folder.

To type an argument differently from its value (for example an object filled
from an expression), add `inputSchema`; keep one a decompiled step carries. See
[Orchestrator Processes](or-processes.md#argument-types-inputschema).

## Which entry point runs

The step starts a job of the process it names, and the job runs that
process's entry point: the workflow set as main in Studio, unless another was
picked for the process
([Managing processes](https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/managing-processes)).
No `rpaWorkflow()` field passes another. When the flow calls an entry point
other than main, or several entry points of one RPA project:

1. **Published process:** create one Orchestrator process per entry point and
   write each step with its own process's `name` and `folderPath`, leaving
   `key` out as for any published process
   ([Orchestrator Processes](or-processes.md#getting-the-inputs-and-outputs)).
   Take `<ENTRY_POINT_PATH>` from the `Path` of each entry point the package
   lists:

   ```bash
   uip or packages entry-points "<PACKAGE_ID>:<VERSION>" --output json
   uip or processes create --name "<PROCESS_NAME>" --package-key "<PACKAGE_ID>" \
     --package-version "<VERSION>" --folder-path "<FOLDER_PATH>" \
     --entry-point "<ENTRY_POINT_PATH>" --output json
   ```

2. **In-solution sibling:** the solution holds one process per project, and its
   entry-point fields are read-only: `uip solution resources edit` skips them
   and still reports success. The deployed process runs the project's main
   workflow: for one entry point, set it as main. For several, split them into
   one project each, so each keeps the typed `returns` that `check` verifies.
   Only when they must stay in one project, make main a dispatcher that invokes
   the entry point a step input names; each step then passes and returns the
   dispatcher's arguments, not the entry point's.

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
