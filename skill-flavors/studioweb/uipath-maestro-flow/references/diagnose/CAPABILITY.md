<!--skill-flavor:single-nested-intro:start-->
Capability index for postmortem on a failed `flow debug` or deployed process run. Diagnose owns the diagnostic priority ladder (incidents → runtime variables → flow correlation → traces) and the catalog of known recurring failure modes (missing `=js:`, misshapen nodes, HITL-stuck, reused reference IDs).
<!--skill-flavor:single-nested-intro:end-->

<!--skill-flavor:diagnose-inherited-rules:start-->
> **Inherited rules:** use `--output json` and prefer `--output-filter` for extraction (bundle commands only — `uip flow debug` returns plain text); do not run `flow debug` without consent; never invoke other skills automatically; use the dropdown question pattern; provide plain-English narration and a granular progress list only when the user asks for verbosity, and remain silent by default. These rules apply in addition to the rules below.
<!--skill-flavor:diagnose-inherited-rules:end-->

<!--skill-flavor:single-nested-task-row:start-->
<!--skill-flavor:single-nested-task-row:end-->

<!--skill-flavor:single-nested-reference-entry:start-->
- [failure-modes.md](failure-modes.md) — pattern catalog for known recurring failures: missing `=js:`, misshapen nodes, HITL-stuck, reused reference IDs, "validate passes / debug faults"
<!--skill-flavor:single-nested-reference-entry:end-->

<!--skill-flavor:diagnose-conventions-reference-entry:start-->
- [shared/cli-conventions.md](../shared/cli-conventions.md) — `--folder-key` requirement, JSON output shape
<!--skill-flavor:diagnose-conventions-reference-entry:end-->
