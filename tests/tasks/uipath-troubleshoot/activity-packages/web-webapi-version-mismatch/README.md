# Web Activities — MissingMethodException / Package-Studio Version Mismatch (design-time)

This scenario reproduces a **design-time / validation** failure of a Web
Activities project: opening or validating the process, or clicking Configure
on the **HTTP Request wizard**, throws `System.MissingMethodException` —
"Method not found: 'Void UiPath.Web.Activities...'" — because `project.json`
pins `UiPath.WebAPI.Activities` at a version incompatible with the installed
Studio (and out of step with `UiPath.System.Activities`). The process has
**never run** — there are no Orchestrator jobs.

## What this scenario uncovers

**Root Cause:** `project.json` pins `UiPath.WebAPI.Activities [1.16.2]` against
`UiPath.System.Activities [21.10.5]` and `studioVersion 21.10.5.0` (Studio
2021.10). The WebAPI package build requires a newer Studio than the one
installed; its assembly loads but a member the wizard/activity was compiled
against is absent, so Studio throws `MissingMethodException` at design time.
The diagnosis comes from the **project source (the WebAPI package vs the
installed Studio)**, not job evidence.

This maps to:
`references/activity-packages/web-activities/playbooks/package-version-mismatch.md`.

The correct agent behavior is to reason from `project.json` (WebAPI version vs
Studio 2021.10 vs System.Activities) rather than chase Orchestrator jobs,
match the package-version-mismatch playbook, and recommend aligning the
packages to a Studio-compatible line via Manage Packages — explicitly NOT the
runtime "Could not load file or assembly" fix (clean
`%userprofile%\.nuget\packages` / republish), which does not apply because the
assembly loads and the failure reproduces in Studio at design time.

## How this test reproduces it

| Layer | Source |
|---|---|
| `process/` | hand-authored Web Activities project (`HttpClient` / HTTP Request) pinning `UiPath.WebAPI.Activities [1.16.2]` vs `UiPath.System.Activities [21.10.5]` with `studioVersion 21.10.5.0` |

> **Note on fixtures.** Like the `uia-dependency-version-conflict` and Word
> `replace-text-version-mismatch` scenarios, this has **no faulted job** by
> design — it is a design-time validation error, so `or jobs list` returns
> empty and the agent must diagnose from `project.json` + the Studio version
> in the prompt. It tests whether the agent distinguishes an in-project
> package/Studio version mismatch (design-time `MissingMethodException`) from
> the robot-side assembly-load failure ("Could not load file or assembly").

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `package-version-mismatch.md`
- Agent identified the `UiPath.WebAPI.Activities` version as incompatible with
  the installed Studio 2021.10 (and skewed vs `UiPath.System.Activities`) as
  the design-time cause, reasoning from the project source, and recommended
  aligning the packages to a Studio-compatible line via Manage Packages —
  without confusing it with the runtime "cannot load assembly"
  cache/republish fix or fabricating actions

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's host-side protected mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
