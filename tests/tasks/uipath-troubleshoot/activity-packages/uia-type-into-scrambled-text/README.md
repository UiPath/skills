# Type Into (NTypeInto) — Scrambled / Dropped Text (Runtime)

Runtime troubleshooting scenario for `UiPath.UIAutomationNext.Activities` `NTypeInto` (modern
`Type Into`).

## What this scenario exercises

A scheduled unattended job ends `Successful`, but the account number it entered into a web portal came
out corrupted — characters missing and out of order. There is **no exception and no Error log**; the
fault is silent text corruption. The agent must recognize that `NTypeInto` ran with
`InteractionMode = HardwareEvents` and `DelayBetweenKeys = 0` and typed faster than the field accepted,
dropping/reordering keystrokes — and prescribe raising `DelayBetweenKeys` or switching the input method
to `Simulate` / `ChromiumAPI`. It must NOT diagnose a selector/targeting failure, a timeout, or a pure
silent no-op (text DID land, just wrong).

## How this test reproduces it

| Layer | Source |
|---|---|
| `process/` | crafted VB project source: `Main.xaml` with an `NTypeInto` (`HardwareEvents`, `DelayBetweenKeys=0`) typing `accountNumber` into a Chromium portal field, followed by an `NGetText` read-back and Log Messages |

The diagnosis is not leaked in any agent-visible name: the project is `AccountPortalEntry`, the activity
is `Enter account number`, and the prompt states only the symptom (entered value wrong). The cause lives
only in the `NTypeInto` properties and the corrupted read-back value.

## Success criteria

Scores the **conclusion**, not the trajectory (`skill_triggered` + `llm_judge` against `RESOLUTION.md`):

- Agent invoked the `uipath-troubleshoot` skill.
- Agent identified the `HardwareEvents` + zero `DelayBetweenKeys` keystroke race as the cause of the
  corrupted value, and the fix (increase `DelayBetweenKeys` / switch input method to
  `Simulate`/`ChromiumAPI`) — not a selector, timeout, or no-op misdiagnosis.

Playbook: `references/activity-packages/ui-automation/playbooks/type-into-input-failed.md` § (A).

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's host-side protected mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
