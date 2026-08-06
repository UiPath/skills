# Classic Click No-Op (SimulateClick on Java) — Synthetic Scenario

A classic `Click` (`UiPath.Core.Activities.Click`) with `SimulateClick=True`
targets a **Java** desktop app, where SimulateClick is unsupported — so the
click reports `Successful` while the Submit button is never actuated: job
`Successful`, zero Error logs, claim status still `Draft`. Classic Click has no
Verify Execution, so the miss is silent by design.

Exercises the
`skills/uipath-troubleshoot/references/activity-packages/classic-activities/playbooks/click-silent-no-op.md`
playbook and the no-signature routing path.

## What the agent must uncover

**Root Cause:** `SimulateClick=True` on a Java target is a documented silent
no-op; classic Click has no Verify Execution to catch it. **Fix:** disable
SimulateClick (use Default / hardware events) and add an explicit post-click
check. See `RESOLUTION.md`.

## How this test reproduces it

| Layer | Source |
|---|---|
| `process/` | frozen snapshot of the failing project (classic `Click`, `SimulateClick=True`, Java selector) |

Synthetic (not a faithful replay): fixtures are hand-authored so the root cause
is confirmable from runtime evidence (status still Draft) plus the workflow
source (SimulateClick on a Java target). The agent-visible surface
(`process/` + `data/`) carries no diagnosis hints — the input-method/target-tech
knowledge lives in the skill's playbook, not in a planted fixture.

## Success criteria

Scores the **conclusion**, not the trajectory (suite two-criteria convention):

- Agent invoked the `uipath-troubleshoot` skill (`skill_triggered`).
- Agent reached the same root cause + fix as `RESOLUTION.md` (`llm_judge`, threshold 0.7).

## Running

```bash
SKILLS_REPO_PATH="C:\\Work\\UiPath" .venv/Scripts/coder-eval.exe run \
  tasks/uipath-troubleshoot/activity-packages/classic-click-noop-simulate/task.yaml \
  -e experiments/default.yaml --repeats 3 -j 3 -v
```

Requires `SKILLS_REPO_PATH` and a tilde-free `TMPDIR/TEMP/TMP` (e.g. `C:/cetmp`)
on Windows.

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's host-side protected mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
