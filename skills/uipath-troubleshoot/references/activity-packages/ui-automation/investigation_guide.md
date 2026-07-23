# UI Automation Investigation Guide

## Data Correlation

Before using any fetched data, verify it matches the user's reported problem:

- **Activity** — the faulted activity namespace and name match the reported failure
- **Selector** — the selector in evidence corresponds to the actual target element the user described
- **Application** — the target application (name, version, technology) matches the user's environment
- **Workflow** — the error originates from the correct workflow file / activity in the project
- **Timestamp** — the failure occurred during the time window the user reported

If the data doesn't match: **discard it**. Do NOT use unrelated data as a proxy. Report the mismatch and ask for clarification.

## Testing Prerequisites

When testing hypotheses for UI Automation issues, gather and verify these before drawing conclusions:

1. **Activity type and namespace** — identify the exact activity that faulted (e.g., `UiPath.UIAutomationNext.Activities.NClick` vs `UiPath.Core.Activities.Click`)
2. **Selector definition** — read the actual selector from the workflow source or error details; don't rely on summaries
3. **Target application state** — verify the application was running and the expected screen/page was visible at time of failure
4. **Healing Agent status** — if relevant, check whether Healing Agent is enabled, whether recovery data exists
5. **Execution context** — check if running attended vs unattended, screen resolution, RDP session state — these affect UI element visibility
6. **Package version** — confirm `UiPath.UIAutomation.Activities` package version; behavior differs across versions
7. **Enclosing scope container configuration** — for activities inside a scope container (`NApplicationCard`, `NBrowser`, `Use Application/Browser`, `NWindow`, `Attach Window`, `Attach Browser`, etc.), open the workflow XAML and capture the container's `AttachMode`, `OpenMode` (defaults to `IfNotOpen` when absent), and `TargetApp.{Selector,Url}` values. The scope container determines which application instance/page the inner selector resolves against — a misconfigured scope makes a structurally correct selector fail (e.g., card attaches to an unintended existing tab via `AttachMode=ByInstance` + default `OpenMode=IfNotOpen` + a loose `TargetApp.Selector`). Do not confirm a selector-failure hypothesis before naming the scope container's configuration.
8. **Silent no-op check** — if a UI activity completed `Successful` but its effect did not occur (e.g. the click never happened), check **Verify Execution** on that activity. An absent or target-less Verify (`VerifyOptions` with a Mode but no verification target) lets a wrong-target / wrong-page no-op pass without faulting — so a "succeeded but did nothing" report is usually a missing Verify, not a missing exception. Dedicated playbook: [playbooks/click-silent-no-op.md](./playbooks/click-silent-no-op.md) (covers input-method/target-tech mismatch, overlay intercept, wrong target, lost focus, DOM race — and closing the detection gap). See also [playbooks/scope-container-wrong-page.md](./playbooks/scope-container-wrong-page.md) for the wrong-page miss variant.
