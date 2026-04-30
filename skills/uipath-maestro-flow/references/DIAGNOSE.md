# Diagnose — Investigate failed or misbehaving flow runs

Capability index for postmortem on a failed `flow debug` or deployed process run. Diagnose owns the diagnostic priority ladder (incidents → runtime variables → flow correlation → traces) and the catalog of known recurring failure modes (MST-9107, MST-9061, HITL-stuck, reused reference IDs, single-nested layout). Requires `uip login`.

> **Phase 1a scaffold** — this index is a placeholder. Subsequent phases populate the sections below by moving today's `troubleshooting-guide.md` into `diagnose/` and extracting failure-mode patterns from SKILL.md anti-patterns.

## When to use this capability

- Triage a failed `flow debug` or deployed process run
- Read incidents to identify the error category, message, and faulting element
- Inspect runtime variable state at the time of failure
- Map a faulting element ID back to a node in the `.flow` file
- Stream verbose traces for execution timeline
- Recognize known failure modes (MST-9107 missing `=js:`, MST-9061 tidy skipped, etc.)

## Critical rules

> Populated in Phase 3. Diagnose-scoped rules likely include "always investigate in priority order — incidents → variables → flow → traces" and "always include `--folder-key` on `instance` and `incident get` commands."

## Workflow

> Populated in Phase 3. Planned journey docs (links activate when files land):
>
> - Triage a failed run (priority ladder) → `diagnose/troubleshooting-guide.md`
> - Look up a known failure mode → `diagnose/failure-modes.md`

## Common tasks

> Populated in Phase 3.

## Anti-patterns

> Populated in Phase 3. Likely candidates:
>
> - Never start with traces — they are verbose and last-resort
> - Never call the underlying APIs directly; always use `uip` CLI commands
> - Never assume the local `.flow` matches the deployed BPMN — fetch `instance asset` if there's any doubt

## References

> Populated in Phase 3 as files are moved/added under [diagnose/](diagnose/):
>
> - `diagnose/troubleshooting-guide.md` — diagnostic priority ladder
> - `diagnose/failure-modes.md` — pattern catalog for known recurring failures
>
> Cross-capability references in [shared/](shared/):
>
> - `shared/commands.md` — `uip maestro flow instance` / `incident` / `job` subcommands
> - `shared/cli-conventions.md` — FOLDER_KEY requirement, login state
> - `shared/file-format.md` — to correlate faulting element IDs back to `.flow` nodes
> - `shared/node-output-wiring.md` — referenced from MST-9107 failure mode
