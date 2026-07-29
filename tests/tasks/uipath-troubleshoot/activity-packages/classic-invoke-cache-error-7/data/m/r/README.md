# Classic Invoke Workflow File — Cache Mechanism Error / Code 7 (Design-Time)

Design-time (Studio build) troubleshooting scenario for `UiPath.Core.Activities.InvokeWorkflowFile`.

## What this scenario exercises

Studio reports `Invoked workflows are missing` + `Cache Mechanism Error (Error code: 7)` at build/debug
time, even though the invoked child `.xaml` files are present in the project. The agent must recognize
this as **project cache corruption** (not a real missing dependency) and prescribe clearing the cache.

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` | shared manifest-driven mock dispatcher from `../../_shared/mock_template/` |
| `process/` | crafted project source: `Main.xaml` invoking two children, both `ValidateOrder.xaml` and `PostOrder.xaml` present, plus a stale `obj/` build artifact |
| `data/m/r/manifest.json` | `docsai ask` passthrough + permissive empty `unmocked_default` — no job/trace exists for a build-time error |

## Success criteria

Scores the **conclusion**, not the trajectory (`skill_triggered` + `llm_judge` against `RESOLUTION.md`):

- Agent invoked the `uipath-troubleshoot` skill.
- Agent identified cache corruption and the fix (close Studio, delete `.local`/`bin`/`obj`, reopen).

Playbook: `references/activity-packages/classic-activities/playbooks/invoke-workflow-file-design-time-errors.md`.
