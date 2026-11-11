# script task — Implementation

> **Phase split.** Written in Phase 2 by `uip maestro case sdd convert`. See [`../../../phased-execution.md`](../../../phased-execution.md).

## Convert writes this task

`sdd convert` emits every `script` task in the shape the Case Designer saves: `type: "script"`, `data.script` holding the fenced body behind a leading `=` (the stored form; the Designer's BPMN writer strips it again), the two system inputs `vars` (`=vars`) and `metadata` (`=metadata`), and the two outputs `scriptResponse` (`source: "=result.response"`) and `Error` (`source: "=Error"`).

1. **Never hand-write `data.script`, the inputs or the outputs.** Fix the SDD's fenced body and re-run convert instead. A hand-written body without the leading `=` is a shape Studio Web rewrites on its first save.
2. **When convert cannot write the task, write a [placeholder](../../../placeholder-tasks.md).** That is a CLI whose `uip maestro case task-types list --output json` does not list `script` under `Authorable`, and every brownfield add, which runs no convert. Tell the user to write the script in Studio Web, or to upgrade the CLI and rebuild; never improvise the shape.
3. **Work the `Data.Unresolved[]` entries for the task** — `task-script` (no ```` ```js ```` fence), `task-io-table` (an Inputs row), and an Outputs row other than `scriptResponse`/`Error` — by fixing the SDD and re-running convert. Report any left to the user in `build-issues.md`.

## Post-Write Verification

- `type: "script"`, and `data.script` is a non-empty string starting with `=`.
- `uip maestro case validate --strict` reports no `STRICT_SCRIPT_SYNTAX` for the task. If it fires, the body does not parse as a function body: fix the SDD's fence and re-run convert.
- `data.inputs` is exactly `vars` and `metadata`; `data.outputs` is `scriptResponse` and `Error`, with `var` numbered apart from other tasks' outputs and from the case's own variable names, unless an arrow row bound `scriptResponse` to a case variable.
- `scriptResponse._jsonSchema` is absent; the Designer infers it from the body's return on first save. That is expected, not a defect.
- The body carries no credential ([planning.md § Rules](planning.md#rules), first item).

<!-- END: impl-json.md -->
