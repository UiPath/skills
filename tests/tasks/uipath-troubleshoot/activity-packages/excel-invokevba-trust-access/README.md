# Invoke VBA Failure - Trust Access to VBA Project Denied

This scenario reproduces a runtime `Invoke VBA` failure caused by Excel's
**"Trust access to the VBA project object model"** Trust Center setting
being disabled on the robot machine. The activity throws
`Programmatic access to Visual Basic Project is not trusted` synchronously
when it attempts to inject the macro module into the workbook.

## What this scenario uncovers

**Root Cause:** Excel's "Trust access to the VBA project object model"
setting is disabled under the Windows user the robot runs as. The
`Invoke VBA` activity in `Main.xaml` cannot call
`Workbook.VBProject.VBComponents.Add` to inject the macro module, so the
job faults before any macro logic executes.

This maps to:
`references/activity-packages/excel-activities/playbooks/invoke-vba-trust-access.md`

The user is framed as **off-host**, so the correct agent behavior is to
recommend the Trust Center toggle the next time the user is at the
machine - not to try host-side commands.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `process/` | hand-authored UiPath project with a minimal Excel Process Scope containing an Invoke VBA activity, plus the external `macro.txt` it references |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session. Before treating this test's score as
> a regression signal, replay against a real failed job and regenerate
> via `_shared/scripts/generate_scenario.py` - see
> `tests/tasks/uipath-troubleshoot/CLAUDE.md`.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `invoke-vba-trust-access.md`
- Agent recommended enabling the Trust Center toggle on the robot
  machine, without fabricating host-side actions it could not perform
