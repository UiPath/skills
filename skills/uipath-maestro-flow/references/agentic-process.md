# Agentic Process

*Exact signatures, fields, and defaults: `agenticProcess()`.*

Invoke a deployed Maestro agentic process.

Signature: `agenticProcess({ key, name, folderPath?, location?, projectId?, inputs?, returns? })`
`folderPath` is required for a published process; a sibling project of the same solution takes `location: 'in-solution'` and `projectId` instead ([below](#in-solution-sibling)).

```ts
.step('intake',
  agenticProcess({
    key: 'BAADF00D-BAAD-F00D-BAAD-F00DBAADF00D',
    name: 'ProcurementProcess',
    folderPath: 'Shared',
    inputs: { productId: 1 },
    returns: { status: 'boolean' }
  }))
```

See [Orchestrator Processes](or-processes.md) and use the `ProcessOrchestration`, `CaseManagement`, and/or `Flow` process types to locate an agentic process and determine its contract.

## At a glance

Run a deployed Maestro agentic process synchronously.

Signature: `agenticProcess({ key, name, folderPath?, location?, projectId?, inputs?, returns?, form?, completion? })`.

```ts
.step('intake', agenticProcess({ key: processKey,
  name: 'ProcurementProcess', folderPath: 'Shared',
  inputs: { productId: 1 }, returns: { status: 'boolean' } }))
```

Confirm identity and argument names live; declared outputs may still be null;
`.onError(...)` is supported. `form: 'bpmn' | 'flow' | 'case'` picks the published
form; `completion: 'fire-and-forget'` waits for nothing — details below.

**Finding the key: [`or-processes.md`](or-processes.md)**

## General

- Declared outputs can be returned as `null`

## Forms and fire-and-forget completion

One `agenticProcess()` covers all three published forms; `form` selects the
wire identity: `'bpmn'` (default — Maestro BPMN process orchestration),
`'flow'` (published Maestro Flow), `'case'` (Case Management process).

`completion: 'fire-and-forget'` dispatches the process and continues
immediately: `returns` is forbidden, the step publishes no output (reading
`$vars.<step>.output` is a check error), and only dispatch failures route
through `.onError(...)`. Local replay treats it as dispatch-only.

```ts
.step('launchReview', agenticProcess({ key: reviewKey, name: 'ClaimsReview',
  folderPath: 'Shared', form: 'flow', completion: 'fire-and-forget',
  inputs: { claimId: input('claimId') } }))
```

## In-solution sibling

To call a sibling project of the SAME solution — for example another Flow,
with `form: 'flow'` — set `location: 'in-solution'` and `projectId`, and omit
`folderPath`:

```ts
.step('notify', agenticProcess({ key: localResourceKey, name: 'Notifier',
  form: 'flow', location: 'in-solution', projectId: localProjectKey,
  inputs: { message: input('who') }, returns: { echoed: 'string' } }))
```

- **Or name the sibling by project** (an SDK that ships builder-sdk#2028):
  `agenticProcess({ form: 'flow', location: 'in-solution', project: '<Project>', inputs })`. `compile` and `check` read `key` and `projectId` from
  `resources/solution_folder/process/flow/<Project>.json` (and `returns`
  from its `entry-points.json` when you declare none), so you copy neither id.
  They refuse a project the solution lacks (`IN_SOLUTION_PROJECT_NOT_FOUND`,
  with the nearest name) and the wrong builder for its type
  (`IN_SOLUTION_WRONG_BUILDER`, which names the right call). Refresh the
  solution's resources first.
- **Where the two ids come from.**
<!--skill-flavor:agentic-sibling-register:start-->
  Register the sibling and refresh resources
  (`uip solution projects add`, then `uip solution resources refresh`), then
<!--skill-flavor:agentic-sibling-register:end-->
  run `uip maestro flow registry list --local --output json` from the Flow
  project directory. The generated
  `resources/solution_folder/process/<type>/<Project>.json` carries the same
  pair: `resource.key` → `key`, `resource.projectKey` → `projectId`. Glob for
  the file (`process/*/<Project>.json`) rather than guessing `<type>`, and
  never invent either id; the full recipe is in
  [agent.md](agent.md#task-created-in-solution-coded-agent).
- **No `folderPath`.** The sibling has no folder until the solution is
  deployed.
- **Inputs and returns are yours to declare**, using the sibling's own
  argument names and casing; `uip maestro flow registry get --local` shows
  them when the sibling's manifest lists them.

`check` warns on `AGENTIC_LOCAL_NO_PROJECT_ID` (no `projectId`; the call
resolves by `key`, so a decompiled step without one is fine as is) and refuses
`AGENTIC_LOCAL_PROJECT_ID_NOT_GUID` (`projectId` is not the
project GUID), `AGENTIC_LOCAL_HAS_FOLDER` (`folderPath` set as well; drop it,
or drop `location` to call the published copy). `AGENTIC_NO_FOLDER` applies to
published steps only. If `check` reports `AGENTIC_LOCAL_NO_PROJECT_ID` as an error (an older SDK),
add `projectId` from `resource.projectKey`.
Still set `projectId` on a step you author: Studio Web's Run node reads it
to deploy the sibling first.
