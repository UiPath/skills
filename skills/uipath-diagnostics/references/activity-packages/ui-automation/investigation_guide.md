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
