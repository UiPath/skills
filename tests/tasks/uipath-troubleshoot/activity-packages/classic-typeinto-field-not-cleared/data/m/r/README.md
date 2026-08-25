# classic-typeinto-field-not-cleared

Faithful-replay scenario for the `uipath-troubleshoot` skill.

## What this scenario covers

A scheduled unattended `VendorOnboarding` job finishes **Successful** with zero Error logs, but the
bank account number written to the Vendor Master form is wrong: `00008891245` instead of the intended
`8891245`. The classic `Type Into 'Account Number'` (`UiPath.Core.Activities.TypeInto`) has
`EmptyField = False` and no clear-field step, so the intended text was **appended** to the field's
pre-existing value (`0000`) rather than replacing it. Classic `Type Into` has no post-write
verification, so the wrong value never faulted.

This is the Type-Into-specific **wrong/incomplete/appended text** family — distinct from a pure silent
no-op (text DID land, just concatenated) and from the throwing paths (no `SelectorNotFoundException` /
`ElementOperationException` / `ActivityTimeoutException`). It is a **no-signature** case: the agent
routes via the top-level `summary.md` no-signature table ("Successful but the output is wrong") to
`classic-activities/playbooks/type-into-wrong-or-incomplete-text.md`.

The correct diagnosis names the append caused by `EmptyField=False` on a pre-filled field, and the fix
`EmptyField=True` (or an explicit clear) plus a read-back verification. Wrong turns to avoid:
concluding a silent no-op, an element-not-found, or a SimulateType character drop.

## Evidence layout

- `data/m/r/10fold.json` — `or folders list` (Finance folder key)
- `data/m/r/20jobs.json` — `or jobs list` (the Successful job)
- `data/m/r/30jobg.json` — `or jobs get` (State Successful, Unattended, MOCK-HOST)
- `data/m/r/40errl.json` — `or jobs logs --level Error` (empty — confirms no-signature)
- `data/m/r/50infl.json` — `or jobs logs` (Info logs: `0000` before, `00008891245` after)
- `process/` — the failing project source (classic `Type Into` with `EmptyField="False"`)

Ground truth for the judge: [`RESOLUTION.md`](./RESOLUTION.md).
