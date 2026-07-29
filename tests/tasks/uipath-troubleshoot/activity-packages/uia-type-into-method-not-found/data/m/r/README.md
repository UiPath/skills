# Type Into (NTypeInto) — Method Not Found / Package Version Skew (Runtime)

Runtime troubleshooting scenario for `UiPath.UIAutomationNext.Activities` `NTypeInto` (modern
`Type Into`).

## What this scenario exercises

An unattended job faults immediately with `Method not found: 'Void
UiPath.UIAutomationNext.Activities.NTypeInto...'` (a `MissingMethodException`), while the same project
runs fine in Studio Debug on the developer machine. The agent must recognize this as
**`UiPath.UIAutomation.Activities` package version skew** — the robot restored a different package
version than the project was built against, so the compiled `NTypeInto` binds to a method signature the
runtime assembly does not expose — and prescribe aligning the package version across all environments
(pin + restore/republish). It must NOT diagnose a selector/targeting failure, a timeout, or corrupt
XAML.

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` | shared manifest-driven mock dispatcher from `../../_shared/mock_template/` |
| `process/` | crafted VB project source: `Main.xaml` with an `NTypeInto` typing `invoiceNumber` into a Chromium portal field; `project.json` pins `UiPath.UIAutomation.Activities: [24.10.3]` |
| `data/m/r/` | canned `Faulted` job with `JobError.Type = System.MissingMethodException`; `job-logs-error.json` / `job-logs.json` carry the `Method not found: 'Void UiPath.UIAutomationNext.Activities.NTypeInto.set_DelayBetweenKeys(...)'` message; `docsai ask` passthrough |

The diagnosis is not leaked in any agent-visible name: the project is `InvoicePortalSubmit`, the
activity is `Enter invoice number`. The prompt states the observed symptom (the pasted error string and
"works in Debug, faults on the robot"); the cause (version skew) is not named — the agent derives it
from the `MissingMethodException` signature plus the pinned dependency.

## Success criteria

Scores the **conclusion**, not the trajectory (`skill_triggered` + `llm_judge` against `RESOLUTION.md`):

- Agent invoked the `uipath-troubleshoot` skill.
- Agent identified the `UiPath.UIAutomation.Activities` version skew between the build/debug environment
  and the robot as the cause, and the fix (align/pin the package version across environments and
  restore/republish) — not a selector, timeout, or corrupt-XAML misdiagnosis.

Playbook: `references/activity-packages/ui-automation/playbooks/type-into-input-failed.md` § (B).
