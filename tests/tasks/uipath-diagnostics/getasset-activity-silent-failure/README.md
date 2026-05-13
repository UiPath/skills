# Get Asset Failure — Activity Bug / Silent Failure (UiPath.System.Activities 22.10.x)

This scenario reproduces a runtime `Get Credential` failure that is
**silent** at the activity layer — the activity itself completes
without throwing an exception, but its output variables remain `null`.
The downstream `LogMessage` activity then throws
`NullReferenceException` consuming the null outputs. The job logs do
NOT show any error from `Get Credential` itself — only the downstream
NRE.

This is the documented `UiPath.System.Activities` **22.10.x** bug
where variables bound via `Ctrl+K` in the activity's property grid
do not receive output values at runtime.

## What this scenario uncovers

**Root Cause:** The project targets `UiPath.System.Activities: [22.10.5]`.
That version has a documented bug where the `Get Credential`,
`Get Asset`, and `Get Orchestrator Asset` activities silently fail to
populate output variables when those variables were created via
`Ctrl+K` during activity configuration. The fix is to upgrade the
package, or pre-create the output variables in the Variables panel
BEFORE wiring them into the activity.

This maps to:
`references/activity-packages/system-activities/playbooks/get-asset-activity-bug-silent-failure.md`
(medium-confidence playbook).

> **Why this is harder than other GetAsset scenarios:** every other
> playbook in the family is keyed off a distinctive runtime error
> from the Get Credential / Get Asset activity itself. This one is
> keyed off the **absence** of such an error combined with a
> downstream null-consumer fault AND the package version. The agent
> has to (a) trace backward from the downstream NRE to find the
> silent activity, and (b) inspect `project.json` to connect the
> pattern to the package bug.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | synthesized UiPath project pinned to `UiPath.System.Activities: [22.10.5]` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

The decisive evidence:

1. **Job logs** show `NullReferenceException` at `LogMessage "Log Message"` — NOT at `GetRobotCredential "Get Credential"`. There is no error log entry naming Get Credential.
2. **`project.json`** lists `UiPath.System.Activities: [22.10.5]` — the version with the documented Ctrl+K output-binding bug.
3. **Asset list** shows `myHiddenAsset` is present, correctly typed, with `ValueScope: "Global"` — the asset and folder are fine; the failure isn't at the asset layer.
4. **`users list`** shows `RobotUser1` has the right roles and a valid license — rules out permission / authentication / licensing issues.

## How this differs from sibling scenarios

| Dimension | Other GetAsset scenarios | `activity-silent-failure` (this) |
|---|---|---|
| Get Credential activity throws an error log entry? | yes | **no — completes silently** |
| Where the error log entry comes from | the Get Credential activity itself | a **downstream** activity (LogMessage) |
| Decisive evidence in `project.json`? | no | **yes — package version 22.10.x** |
| Asset layer healthy? | varies | **yes** |
| Robot / role / license healthy? | varies | **yes** |
| Matched playbook | one of get-asset-{not-found, folder-scope-mismatch, permission-denied, wrong-activity-type, per-robot-no-value, robot-not-authenticated, external-vault-failure} | `get-asset-activity-bug-silent-failure.md` |

This is the only scenario in the family where the agent has to
diagnose **backward** from a non-asset-shaped error (NRE at
LogMessage) AND inspect `project.json` to find a package-version
anchor.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-diagnostics` skill
- Agent matched the correct playbook AND reached the same root cause as `RESOLUTION.md`
- Conclusion must (a) recognize that Get Credential completed silently, (b) name the package version `UiPath.System.Activities: 22.10.x`, and (c) recommend either upgrading the package or pre-creating output variables before activity configuration

## Regenerating from a real session

```bash
python tests/tasks/uipath-diagnostics/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.local/investigations> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name getasset-activity-silent-failure --apply
```
