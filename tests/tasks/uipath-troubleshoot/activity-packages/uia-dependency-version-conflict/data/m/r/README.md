# UIAutomationNext Failure - MissingMethodException / Dependency Version Conflict

This scenario reproduces a **design-time / validation** failure of a
UIAutomationNext (`NClick` / modern Click) project: opening or validating the
process throws `System.MissingMethodException` — "Method not found: 'Void
UiPath.UIAutomationNext.Activities...'" — because `project.json` pins
`UiPath.UIAutomation.Activities` out of step with `UiPath.System.Activities`
and the installed Studio. The process has **never run** — there are no
Orchestrator jobs.

## What this scenario uncovers

**Root Cause:** `project.json` pins `UiPath.UIAutomation.Activities [24.10.9]`
against `UiPath.System.Activities [22.4.4]` and `studioVersion 22.4.3.0`. The
UI Automation package was bumped in isolation; the resolved
`UiPath.UIAutomationNext(.Activities)` runtime is older than the package
expects, so the activities' method lookup fails at bind time and Studio
throws `MissingMethodException`. The diagnosis comes from the **project
source (the mismatched dependency set)**, not job evidence.

This maps to:
`references/activity-packages/ui-automation/playbooks/dependency-version-conflict.md`
(**Signature A** — Method not found / MissingMethodException).

The correct agent behavior is to reason from `project.json` (the version skew
across UI Automation vs System.Activities vs Studio) rather than chasing
Orchestrator jobs, match the dependency-version-conflict playbook, and
recommend aligning **all** foundational packages to a mutually compatible
line via Manage Packages — explicitly NOT the **Signature B** runtime
"Could not load file or assembly" fix (clean `%userprofile%\.nuget\packages`
/ republish), which does not apply because the assembly loads and the failure
reproduces in Studio at design time.

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` dispatcher | shared from `../../_shared/mock_template/` |
| `process/` | hand-authored UIAutomationNext project (`NApplicationCard` + `NClick`) pinning `UiPath.UIAutomation.Activities [24.10.9]` vs `UiPath.System.Activities [22.4.4]` with `studioVersion 22.4.3.0` |
| `data/m/r/*.json` | folders list + **empty** job lists (the process never ran) |
| `data/m/r/manifest.json` | dispatch table (folders, empty jobs, `docsai ask` passthrough, permissive `[]` fallback) |

> **Note on fixtures.** Like the Word `replace-text-version-mismatch`
> scenario, this has **no faulted job** by design — it is a design-time
> validation error, so `or jobs list` returns empty and the agent must
> diagnose from `project.json` + the Studio version in the prompt. It tests
> whether the agent correctly distinguishes an in-project version conflict
> (Signature A) from the robot-side assembly-load failure (Signature B).

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `dependency-version-conflict.md` (Signature A)
- Agent identified a UIAutomationNext dependency version conflict inside
  `project.json` (UI Automation package bumped out of step with
  System.Activities / Studio 2022.4) as the design-time cause, reasoning from
  the project source, and recommended aligning all foundational packages to a
  compatible line via Manage Packages — without confusing it with the
  Signature B runtime "cannot load assembly" cache/republish fix or
  fabricating actions
