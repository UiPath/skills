# Replace Text Failure - TargetInvocationException / Studio Crash on Drop

This scenario reproduces a **design-time** Studio crash: dropping the
`Replace Text` activity (or opening the workflow) throws
`System.Reflection.TargetInvocationException` because the project pins a
`UiPath.Word.Activities` version newer than the installed Studio (2021.10)
can construct. The process has **never run** — there are no Orchestrator
jobs.

## What this scenario uncovers

**Root Cause:** `project.json` pins `UiPath.Word.Activities [2.0.0]` against
`studioVersion 21.10.5.0`. Studio 2021.10 cannot construct the newer
package's activity designer, so the reflection call crashes at design time.
The diagnosis comes from the **project source + the stated Studio version**,
not job evidence.

This maps to:
`references/activity-packages/word-activities/playbooks/replace-text-version-mismatch.md`

The correct agent behavior is to reason from `project.json` (package vs
Studio version) rather than chasing Orchestrator jobs, match the
version-mismatch playbook, and recommend aligning versions via Manage
Packages — explicitly NOT the runtime `Cannot create unknown type` package
restore fix.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project pinning `UiPath.Word.Activities [2.0.0]` with `studioVersion 21.10.5.0` |
| `fixtures/mocks/responses/*.json` | folders list + **empty** job lists (the process never ran) |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** This is the one Word scenario with **no faulted
> job** by design — it is a design-time Studio crash, so `or jobs list`
> returns empty and the agent must diagnose from `project.json` + the
> Studio version in the prompt. It tests whether the agent correctly
> distinguishes a design-time version mismatch from the runtime
> `cannot-create-unknown-type` package gap.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `replace-text-version-mismatch.md`
- Agent identified a Studio↔`UiPath.Word.Activities` version mismatch (newer
  package vs older Studio 2021.10) as the design-time cause, reasoning from
  the project source, and recommended aligning versions via Manage Packages
  (downgrade the package or upgrade Studio) — without confusing it with the
  runtime `cannot-create-unknown-type` fault or fabricating actions
