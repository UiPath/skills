# Test Manager — full lifecycle e2e

`full_lifecycle_e2e.yaml` drives **one** Test Manager project through its
entire life in a single agent run, touching every `uip tm` subject in one
connected thread:

```
create  → project + test cases + requirement (+link) + TWO test sets
          (Automated Suite + Manual Suite) the cases are split across
metadata→ object label + custom field (value + label rows) + attachments
automate→ discover pre-published automation → link entry points to the
          Automated Suite's cases
run     → run the Automated Suite automated on a robot → wait → stats +
          logs + result (expect a pass/fail mix)
manual  → run the Manual Suite manually → testcase logs (Passed + Failed)
          → screenshot
explore → read-sweep across subjects (project/testcases/testsets/
          requirements/objectlabel/customfield/executions list, user get,
          requirement export + traceability) → report → summary file
cleanup → unlink automation → delete project
```

The agent self-seeds a uniquely-named project (so reruns never collide) and
deletes it at the end, so the tenant is left as it was found.

## Why one file (not several)

coder_eval runs each task as an **isolated agent run with no cross-task
state** — there is no `depends_on` and no way for one task to operate on a
project another task created. A genuinely *sequential, connected* lifecycle
(one project threaded through every phase) is only possible inside a single
task. Serial `make` scheduling alone would not connect separate files.

## Prerequisites

This is the heaviest task in the suite. It needs:

| Requirement | Why | How it's provided |
|---|---|---|
| **A published test automation (created once, outside the test)** | the automated run needs a real automation with a test entry point to link to — the test does **not** build a `.xaml` per run | a minimal one is provided at [`fixtures/tm-smoke-automation/`](fixtures/tm-smoke-automation/) (one test case that just "opens" the Test Manager page); build + publish it once to the folder in `$E2E_TM_FOLDER` (see that fixture's README), then the task discovers its entry point via `list-automations` and links it |
| **A serverless robot/machine (created once, outside the test)** | the automated execution must run somewhere real | create the serverless machine as a one-time admin step, then pass its key + target folder via the CI secrets below |

> **Robot: one-time creation vs. per-run assignment.** Creating the serverless
> machine is a one-time admin activity done *outside* this task (it needs org
> licensing and doesn't change between runs). The test itself does the
> per-run wiring: it **assigns** that machine to the target folder
> (`uip or machines assign <machine-key> --folder-path <folder>`) and then
> **runs** the automated execution. So the env vars below carry an
> already-created machine; the task handles assignment + execution.

CI secrets the task reads: `E2E_TM_FOLDER`, `E2E_TM_ROBOT_KEY`,
`E2E_TM_MACHINE_KEY` (same pattern as `E2E_PROCESS_KEY` in
`tests/fixtures/packages/README.md`). One-time creation recipe:

```bash
# one-time, outside the test (admin): create/find a serverless machine
SERVERLESS=$(uip or machines list --output json \
  | jq -r '.Data[]|select(.Scope=="Serverless")|.Key' | head -1)
# then expose $SERVERLESS as the E2E_TM_MACHINE_KEY secret.
# The test assigns it to $E2E_TM_FOLDER and runs the execution itself.
```
| **Live tenant auth** | every `uip tm` call hits the tenant | the runner's standard auth env (the suite targets `codereval / DefaultTenant`) |

> **Why the automate/run leg needs both fixtures:** the agent links an
> already-published automation and runs it — it does not build a `.xaml`, so
> there's no Studio/Windows dependency and the task runs on Linux. But the
> automation must already exist in `$E2E_TM_FOLDER` and a robot must be
> assignable to that folder; without both, `link-automation` / `testcases run`
> have nothing real to bind to or execute on. The create → metadata → manual →
> explore legs run regardless; only the automated-run leg needs the fixtures.

## Cleanup

The agent deletes its project in step 7. As a safety net, step 1 records the
project key to `./project-key.txt`, and a `post_run` block deletes that project
after the verdict — so an interrupted run (timeout, max_turns, crash) never
leaks the self-seeded project onto the shared tenant. `post_run` does not affect
pass/fail.

## Scoring shape

Criteria are weighted per leg so coverage is **legible and robust**:

- create / metadata / manual / explore legs each score on their own
  (`1.0`–`2.0`), so they still report green when only the automated leg is
  blocked.
- the **automated-run** trigger carries the top weight (`3.0`) — it's the
  faithful "run it automatically from Test Manager" behavior — followed by
  `link-automation` (`2.5`) and the machine-assign + entry-point discovery
  steps (`1.5`–`2.0`).

So a run on an environment **without** the automation fixture or an
assignable robot loses the single `3.0` automated-trigger criterion (and the
downstream stats/logs/result checks that depend on a real execution) rather
than failing the whole lifecycle. With the fixtures in place it scores the
full end-to-end.
