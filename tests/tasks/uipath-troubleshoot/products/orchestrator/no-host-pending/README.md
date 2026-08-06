# No Host Pending — Genuine No-Available-Host

This scenario replays a UiPath troubleshooting investigation where a job is
stuck in `Pending` because **no host is connected to the folder's machine
template** — a genuine no-available-host condition.

## What the scenario covers

A user reports their last job in the Shared folder is stuck in `Pending` and
never started. The agent discovers exactly one Pending job there
(process `NewBlankTask`, Unattended) whose `PendingReasons.ErrorCodes` is the
host-family (`TemplateNoHostsAvailable`, `DynamicJobConnectedMachinesInvalid`,
`DynamicJobConnectedMachinesWindowsRobotVersionInvalid`) with the error text
*"…there is none connected to this folder"*.

The evidence confirms a real no-host condition:

- `machines list --all-fields`: the only Default-scope template **DanLaptopNew**
  has `robotVersions: []` — **no runtime is connected to it**. (The other
  templates are Serverless / PersonalWorkspace scope, not eligible for this
  Default-scope folder job.)
- `licenses info`: Unattended `Allowed=1`, `Used=0` — the slot is **free**, so
  license is not the blocker.
- `JobHistory`: a single Pending entry — the job never started because nothing
  could accept it.

So no machine is available to run the job. The fix is to **connect/assign a
machine to the folder's template** (sign a robot into a machine on DanLaptopNew,
or assign a template that has a connected host). Re-triggering does **not** help
while no host is connected — a fresh dispatch finds the same empty template.

This is the *paired counterpart* to `no-login-pending/` (a
`RobotNoMatchingUsernames` credentials case). Together the two tests verify the
skill routes correctly between `job-pending-no-host.md`, `robot-credentials.md`,
and `job-pending-stale-dispatch.md` based on the actual evidence (here: no
connected runtime), not on superficial wording.

## How this test reproduces it

| Layer | Source |
|---|---|

(No `process/` snapshot — this investigation is purely CLI-driven; no project
source was read.)

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill.
- The agent's presented resolution names the **no available host** (no runtime
  connected to the folder's template) as the root cause and recommends
  **connecting/assigning a machine to the folder**, without falling for the
  stale-dispatch/re-trigger, license-exhaustion, or credential-mismatch
  misreads.

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's UID/GID-isolated mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
