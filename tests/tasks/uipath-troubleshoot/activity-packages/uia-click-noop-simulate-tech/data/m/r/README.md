# Uia Click No-Op (Simulate on Java) — Synthetic Scenario

A modern Click (`NClick`) with `InteractionMode=Simulate` targets a **Java**
desktop app, where Simulate is unsupported. The click reports Successful while
the button is never actuated: the job ends `Successful` with zero Error logs and
the claim status stays `Draft`. This is the no-signature counterpart to the
Verify-Execution-failure case (nothing threw because no Verify was configured).

This exercises the new
`skills/uipath-troubleshoot/references/activity-packages/ui-automation/playbooks/click-silent-no-op.md`
playbook and the no-signature routing path.

## What the agent must uncover

**Root Cause:** `InteractionMode=Simulate` on a Java target is a documented
silent no-op; with no Verify Execution, the miss never faults. **Fix:** switch
the Click's input method to Hardware Events (and add a real Verify target to
harden). See `RESOLUTION.md`.

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` + `m/uip.cmd` | shared from `../../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `process/` | frozen snapshot of the failing UiPath project (Java scope, Simulate Click, no Verify) |
| `data/m/r/*.json` | canned `uip` CLI stdout: folders, jobs list/get, Error logs (empty), Info logs (status still Draft) |
| `data/m/r/manifest.json` | dispatch table mapping each command pattern to its fixture; `docsai ask` proxies to the real CLI (passthrough) |

Synthetic (not a faithful replay): fixtures are hand-authored so the root cause
is confirmable from runtime evidence (status still Draft) plus the workflow
source (Simulate input on a Java target). The agent-visible surface
(`process/` + `data/`) carries no diagnosis hints — the input-method/target-tech
knowledge lives in the skill's playbook, not in a planted fixture.

## Success criteria

Scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill (`skill_triggered`).
- Agent reached the same root cause + fix as `RESOLUTION.md` (`llm_judge`, threshold 0.7).

## Running

```bash
SKILLS_REPO_PATH="C:\\Work\\UiPath" .venv/Scripts/coder-eval.exe run \
  tasks/uipath-troubleshoot/activity-packages/uia-click-noop-simulate-tech/task.yaml \
  -e experiments/default.yaml --repeats 3 -j 3 -v
```

Requires `SKILLS_REPO_PATH` and a tilde-free `TMPDIR/TEMP/TMP` (e.g. `C:/cetmp`)
on Windows.
