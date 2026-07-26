# Final Resolution

Investigation complete. Here is the resolution:

---

**Root Cause:** **Persistence is not supported in the current runtime.** The invoked workflow
`SubmitForApproval.xaml` contains a `Run Job` activity in **Suspend** mode (`ExecutionMode="Suspend"`),
which suspends the workflow and therefore requires persistence — but the process has
`runtimeOptions.supportsPersistence: false` in `project.json`. When the invoked workflow reaches the
suspend point on the robot, the runtime cannot persist and the job faults.

**What went wrong:** Job `8d2c5f91-4a06-4e73-9b18-3c7f0a2e6d45` (process **OrderApproval**, folder
**Shared**, robot **MOCK-HOST**, unattended) faulted with `System.NotSupportedException` — the workflow
requires persistence, which is not enabled/supported. The `Run Job` (Suspend) activity inside the
invoked workflow needs a persistence-capable runtime that the process is not configured for.

**Why:**
- Job Info/logs: "Persistence is not supported in the current runtime. The workflow attempted to
  suspend (Run Job in Suspend mode), which requires persistence…" →
  `System.NotSupportedException … Set supportsPersistence to true in project.json`. Stack:
  `UiPath.Core.Activities.RunJob` inside `SubmitForApproval.xaml`, reached through
  `InvokeWorkflowFile "Invoke SubmitForApproval"`.
- `process/SubmitForApproval.xaml` — `<uca:RunJob ProcessName="ApprovalRoutingJob"
  ExecutionMode="Suspend" …>`. `Suspend` mode suspends the workflow (persistence required).
- `process/project.json` — `runtimeOptions.supportsPersistence: false`. The process is not configured
  for persistence, so the suspend cannot happen at run time.
- `process/Main.xaml` — the `Invoke Workflow File` relays the fault; the invoke itself is fine.

**Evidence:**
- Error: `System.NotSupportedException` — persistence required but not supported; message points to
  `supportsPersistence`.
- Source: `RunJob` `ExecutionMode="Suspend"` in the invoked workflow + `supportsPersistence: false` in
  `project.json`.
- Fault at `RunJob` inside `SubmitForApproval.xaml`, propagated through the invoke.
- Job identity: Key `8d2c5f91-…`, `ReleaseName` OrderApproval, `EntryPointPath` Main.xaml, `State`
  Faulted, `ErrorCode` Robot, folder **Shared** (`e5f19c42-…`), robot **MOCK-HOST**, unattended.

**Immediate fix:**
1. Enable persistence for the process: set `runtimeOptions.supportsPersistence: true` in `project.json`
   (in Studio: project settings → **Supports Persistence**), and run the process on a
   persistence-capable runtime (a persistence-enabled Orchestrator/robot).
   - Where: `project.json` → `runtimeOptions.supportsPersistence` → `true`.
2. If suspending is not actually needed, change the `Run Job` `ExecutionMode` from `Suspend` to `Busy`
   (Wait for job completion) so no persistence is required.
   - Where: `SubmitForApproval.xaml` RunJob_1 `ExecutionMode`.

**Preventive fix:**
- When any invoked workflow uses a suspending / `…AndResume` / `Run Job` (Suspend) activity, ensure the
  process (and every process that invokes it) has `supportsPersistence: true` and runs on a
  persistence-capable runtime.

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The invoked `SubmitForApproval.xaml` runs `Run Job` in Suspend mode (persistence required), but `project.json` has `supportsPersistence: false`, so the runtime cannot persist and the job faults with `NotSupportedException`. | high | confirmed | Yes | Error names persistence/`supportsPersistence`; `RunJob ExecutionMode="Suspend"` in the child; `supportsPersistence: false` in project.json; fault at RunJob through the invoke. | Set `supportsPersistence: true` (and use a persistence-capable runtime), or switch RunJob to `Busy`. |
| H2 | The Invoke Workflow File is misconfigured (bad path/arguments/session). | low | eliminated | No | The invoke resolves the child and the fault is a persistence `NotSupportedException` raised at the child's RunJob, not at the invoke's binding/validation. | N/A. |
