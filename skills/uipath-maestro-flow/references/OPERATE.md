# Operate — Ship, run, and manage deployed flows

Capability index for the lifecycle of a flow as a deployed asset. Operate owns everything that touches the cloud — `solution resource refresh`, Studio Web upload, Orchestrator deploy, `flow debug`, `process run`, `job status/traces`, and `instance` lifecycle (pause, resume, cancel, retry). Requires `uip login`.

> **Phase 1a scaffold** — this index is a placeholder. Subsequent phases populate the sections below by extracting content from SKILL.md Steps 7 & 8 and from `commands.md`.

## When to use this capability

- Push a flow to Studio Web (`uip solution upload`)
- Deploy a flow to Orchestrator (`uip maestro flow pack` + `uip solution publish`)
- Run a flow end-to-end via `uip maestro flow debug` (cloud round-trip with real side effects)
- Trigger a deployed process via `uip maestro flow process run`
- Check job status or stream traces with `uip maestro flow job status` / `job traces`
- Manage a running instance — pause, resume, cancel, or retry
- Refresh solution resources after binding changes (`uip solution resource refresh`)

## Critical rules

> Populated in Phase 4. Inherits universal rules from SKILL.md (rules 4, 9, 14, 15, 19, 20). Operate-scoped rules to be added — likely include "always run `solution resource refresh` before upload or debug" and "always confirm consent before `flow debug`."

## Workflow

> Populated in Phase 4. Planned journey docs (links activate when files land):
>
> - Publish a flow to Studio Web or Orchestrator → `operate/ship.md`
> - Run a flow on demand or check progress → `operate/run.md`
> - Intervene in a running instance → `operate/manage.md`

## Common tasks

> Populated in Phase 4.

## Anti-patterns

> Populated in Phase 4. Likely candidates:
>
> - Never run `flow debug` without explicit user consent
> - Never run `solution upload` without first running `solution resource refresh`
> - Never deploy to Orchestrator when the user said "publish" — default to Studio Web
> - Never run `flow debug` as a validation step

## References

> Populated in Phase 4 as files are added to [operate/](operate/):
>
> - `operate/ship.md` — Studio Web upload + Orchestrator deploy
> - `operate/run.md` — debug, process run, job status/traces
> - `operate/manage.md` — instance lifecycle (pause, resume, cancel, retry)
>
> Cross-capability references in [shared/](shared/):
>
> - `shared/commands.md` — flat CLI lookup
> - `shared/cli-conventions.md` — login states, FOLDER_KEY, UIPCLI_LOG_LEVEL, JSON shape
> - `shared/variables-and-expressions.md` — `--inputs` JSON for `flow debug`

For Orchestrator deployment via `uip solution publish`, see [/uipath:uipath-platform](/uipath:uipath-platform).
