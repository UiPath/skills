# classic-triggerscope-split-in-parallel

Faithful-replay scenario for the `uipath-troubleshoot` skill.

## What this scenario covers

An attended `OrderEntryAssistant` automation (folder `Operations`) faults ~3 seconds after start,
before it handles any shortcut. `Main.xaml` places **two separate `Trigger Scope` blocks inside one
`Parallel`** (`Monitor Shortcuts`): `Watch Save Shortcut` (Ctrl+S) and `Watch Submit Shortcut`
(Ctrl+Shift+Enter). The local robot service allows only **one** active trigger-monitoring session per
execution, so when the `Parallel` starts both branches concurrently, the second `Trigger Scope`
throws `System.InvalidOperationException` ("A trigger monitoring session is already active") the
instant it tries to register its hook — the job faults immediately.

This is a **signature** case (Faulted job with an Error log). The agent routes via
`classic-activities/summary.md` to
`classic-activities/playbooks/trigger-scope-and-local-triggers-failed.md`.

The correct diagnosis names the split `Trigger Scope`s under `Parallel` as the cause, and the fix
**consolidate both hotkey triggers into a single shared `Trigger Scope`** (drop the `Parallel`). Wrong
turns to avoid: blaming a hotkey the OS already owns (no key-conflict error present), a missing
`.local\generated\Triggers.Generated.xaml` (no `Run Local Triggers`, no generated-file error), or a
legacy `UiPath.Core.Activities` package conflict (dependencies are the modern split).

## Evidence layout

- `data/m/r/10fold.json` — `or folders list` (Operations folder key)
- `data/m/r/20jobs.json` — `or jobs list` (the Faulted job)
- `data/m/r/30jobg.json` — `or jobs get` (State Faulted, Attended, MOCK-HOST, ~3s)
- `data/m/r/40errl.json` — `or jobs logs --level Error` (the TriggerScope InvalidOperationException; `Parallel` on the stack)
- `data/m/r/50infl.json` — `or jobs logs` (Info/Trace: first scope registered, then Parallel faulted)
- `process/` — the failing project source (`Parallel` → two `ui:TriggerScope` blocks)

Ground truth for the judge: [`RESOLUTION.md`](./RESOLUTION.md).
