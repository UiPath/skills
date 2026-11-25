# Evaluate — evaluators, eval sets, simulations, runs

Evaluators, eval sets, data points, and simulations are project assets managed by `uip maestro bpmn eval`; authoring `<Name>.bpmn.ts` does not create them. Use this for evaluation assets or evaluating a BPMN process.

Every `eval` command takes `--path <path>`: a Maestro BPMN project directory (`<Project>`, written by `init`), or a solution directory containing exactly one BPMN project; it defaults to `.`.

<!--skill-flavor:eval-host:start-->
**Local `add` / `list` / `remove` edit project files and need no login.** Every `run` verb (`start`, `status`, `results`, `list`, `compare`) needs `uip login`; `run start` also deploys (see [Running a set deploys your solution](#running-a-set-deploys-your-solution--know-what-it-overwrites)).
<!--skill-flavor:eval-host:end-->

**Spellings.** `--help` lists plural groups and `create` / `delete` (`evaluators create`, `sets delete`, `simulations create`, `runs start`). The singular and `add` / `remove` aliases below are equivalent; use them as written. Probe the installed CLI once, then let it write the JSON formats and generated file references rather than hand-authoring them:

```bash
uip maestro bpmn eval --help --output json
```

## Before the first eval command

Eval commands read the compiled project, not source. Bring `<Project>/<Name>.bpmn` up to date with the [validation loop](../SKILL.md#validation-loop): compile and `format` a new process, or `merge` an existing one, so `refresh` and `validate` have run. `refresh` writes `entry-points.json`, supplying the entry point and declared inputs and outputs. A simulation target must already be an element of that compiled `.bpmn`.

## Evaluators — how an output is scored

```bash
uip maestro bpmn eval evaluator add response-quality \
  --type llm-judge-output \
  --model gpt-4.1-2025-04-14 \
  --description "Score the response against the expected result" \
  --target-key '*' \
  --path <Project> --output json

uip maestro bpmn eval evaluator list        --path <Project> --output json
uip maestro bpmn eval evaluator remove <id> --path <Project> --output json
```

`--type` takes `exact-match`, `json-similarity`, `contains`, `llm-judge-output`, `llm-judge-strict-json`, `llm-judge-trajectory` or `llm-judge-trajectory-simulation`. Types and stored `evaluatorTypeId`s are shared with Flow; `llm-judge-output` produces `uipath-llm-judge-output-semantic-similarity`. Always pin an LLM-judge model; prefer `exact-match`, `json-similarity`, or `contains` for deterministic values.

## Evals and eval sets

```bash
uip maestro bpmn eval set add "Smoke Tests" \
  --entry-point Event_start \
  --path <Project> --output json

uip maestro bpmn eval add "basic case" \
  --set "Smoke Tests" \
  --inputs '{"request":"hello"}' \
  --expected '{"reply":"hello"}' \
  --path <Project> --output json

uip maestro bpmn eval list            --set "Smoke Tests" --path <Project> --output json
uip maestro bpmn eval remove <id>     --set "Smoke Tests" --path <Project> --output json
uip maestro bpmn eval set list        --path <Project> --output json
uip maestro bpmn eval set remove <id> --path <Project> --output json
```

Address almost everything **through its set**. `--set` is required on `eval list`, `eval remove`, all three `simulation` commands, and every `run` verb including `status` and `results`; only `set` and evaluator commands omit it.

Use the generated evaluator id or filename when explicitly passing `--evaluators`; display names are unstable and Studio Web cannot resolve them. Omitting `--evaluators` on `eval set add` links all current evaluators; later ones are **not** linked retroactively.

`--entry-point` is a **start-event id**: the id passed to `.startEvent(id)` in `<Name>.bpmn.ts` (`Event_start` for an `init` stub). It is stored as `selectedEntrypoint`, is not a path, and values containing `/` or `#` are rejected (`The entry point is a start event id from the .bpmn file, not a path.`), as are values absent from the process's derivable start events. Omit it for the default start event (`isDefault`, otherwise the first derivable entry point); override it per run with `run start --entry-point`.

**Node-scoped (agent-node) and document eval sets are not authorable through the CLI yet**: the CLI creates only `flow`-scoped sets, and `set add` / `set list` output that `Scope`; create the others in Studio Web. This differs from Flow.

A data point's input and output keys are validated against the entry point's declared schema in the project's **`entry-points.json`**, by the names a caller uses, not the ids in the `.bpmn`. An undeclared key fails with `Input "<name>" is not a declared input of the BPMN process. Declared inputs: …`. Declare the contract with `.input()` / `.output()` (see [Process contract](bpmn-runtime.md#variables-and-the-process-contract)), rerun the [validation loop](../SKILL.md#validation-loop), then `eval add` again. Validation is best-effort: with no declared inputs or outputs, it skips rather than rejecting keys. Build expected outputs from real records; an invented key matches no record and scores a fault.

## Simulations — stop an eval from really sending

A simulation stands in for a component during a run, keyed by its `.bpmn` element id (the id passed to the builder, such as `sendEmail` for `.connector('sendEmail', …)`) or an agent tool name. It is scoped to one **data point inside one set**; all three commands require `--set` and `--data-point`. `add` also requires `--strategy` and exact, case-sensitive `--component-type`: `agent`, `connector`, `hitl`, `process`, or `Node` (the Studio Web value). A `uip` with cli#5928 rejects other values such as `subprocess`, with exit 3; older versions accepted any text.

`--mock-value` is the element's raw `result`; top-level keys must match outputs reading `=result.<key>`. For example, `=result.response.ok` requires `{"response":{"ok":true}}`, and an `Actions.HITL` output reading `=result.Action` requires `{"Action":"<outcome name>", "<fieldId>": <value>}`.

Always run the BPMN simulation commands below, **never `maestro flow eval`** on a BPMN project: the flow verb skips the `--output-schema` requirement and lets a Flow-style `Llm` simulation silently bypass BPMN correctness.

```bash
# Static — returns --mock-value verbatim
uip maestro bpmn eval simulation add <component-id> \
  --set "Smoke Tests" --data-point <id> \
  --strategy Static --component-type connector --mock-value '{"response":{"ok":true}}' \
  --path <Project> --output json

# Llm — generates from instructions; --output-schema is REQUIRED
uip maestro bpmn eval simulation add <component-id> \
  --set "Smoke Tests" --data-point <id> \
  --strategy Llm --component-type connector \
  --simulation-instructions "Pretend to send the email and return success." \
  --output-schema '{"type":"object","properties":{"status":{"type":"string"}}}' \
  --path <Project> --output json

uip maestro bpmn eval simulation list \
  --set "Smoke Tests" --data-point <id> --path <Project> --output json
uip maestro bpmn eval simulation remove <component-id> \
  --set "Smoke Tests" --data-point <id> --path <Project> --output json
```

**`--output-schema` is required for every `Llm` simulation, the key divergence from Flow.** Flow resolves output schema from `.flow`; the BPMN CLI does not, so omission fails fast with `--output-schema is required for the Llm strategy (BPMN cannot auto-resolve the component's output schema)`. The id is checked against `.bpmn`; a missing one fails with `Component "<id>" not found in the BPMN process`.

Child tool simulations on an agent node (`--parent`) are **not supported for Maestro BPMN yet**: the CLI rejects `--parent` with "not supported for Maestro BPMN yet". Simulate the agent node itself with plain `--component-type agent`; Flow supports `--parent`, a BPMN divergence.

Simulate every side-effecting component before running a set more than once. An unsimulated connector really sends once per data point per run.

## Running a set

```bash
uip maestro bpmn eval run start   --set "Smoke Tests" --path <Project> --output json
uip maestro bpmn eval run status  <evalSetRunId> --set "Smoke Tests" --path <Project> --output json
uip maestro bpmn eval run results <evalSetRunId> --set "Smoke Tests" --path <Project> --output json
uip maestro bpmn eval run list    --set "Smoke Tests" --path <Project> --output json
uip maestro bpmn eval run compare <evalSetRunId> --compare-to <evalSetRunId> \
  --set "Smoke Tests" --path <Project> --output json
```

`run start` returns `evalSetRunId` and does not block. Poll `run status` until settled, then read `run results`. `run list` reads records written by this checkout; on a fresh checkout or another machine it fails (`No local run records for eval set ... and no --project-id given`) unless passed `--project-id <workloadId>`, printed by `run start`.

`run start` resolves workload/project id and solution from the parent `.uipx` or `SolutionStorage.json` and deploys from there. A scaffold created with `--skip-solution-registration` has neither and refuses with `No solution to package` unless both ids are passed. Pass both `--solution-id` and `--project-id` to run an already provisioned Studio Web solution, skipping package and upload; pass `--folder-key` outside the personal workspace and `--entry-point` to override the set's pinned start event.

`--wait` polls to a terminal state (`--timeout`, default 600 seconds) and prints one JSON envelope on stdout (`Code: BpmnEvalRunCompleted`), with per-data-point rows in `Data.Results`, directly `JSON.parse`-able in CI. Unlike `uip maestro flow eval`, it does not emit separate Started, Completed, and Results envelopes. Terminal `Failed` or `WorkloadFailed` emits one same-shaped failure envelope, with results still in `Data.Results`, and a **non-zero exit**; CI must not treat it as success. `WorkloadFailed` is a process runtime fault; triage it with [Diagnose](diagnose.md), not as an evaluator problem. Low evaluator scores on a completed run still mean the eval succeeded.

`run results` accepts `--only-failed`, `--verbose` (judge justifications), and `--export-format json|csv` (writes `bpmn-eval-results-<timestamp>.{json,csv}` to the working directory). `run compare` compares via `--compare-to`, aligning data points by stable snapshot id to show whether a prompt or process change helped.

## Running a set deploys your solution — know what it overwrites

`eval run start` is a deploy, not just a trigger: it packages local state and **uploads it to Studio Web, creating or overwriting the solution matching local `.uipx` `SolutionId`**, then provisions execution. The backend runs *deployed* resources; there is no separate upload or overwrite prompt. This mirrors `uip maestro bpmn debug`, which also deploys before running.

It has the same risks as manual `uip solution upload` when: (1) iterating locally before publishing, because work in progress reaches teammates and triggers; (2) changing a solution downloaded with `uip solution download`, because partial local state overwrites other changes; or (3) local and Studio Web diverge, because the remote side is discarded rather than merged.

The overwrite is recorded as a restorable version unless uploaded with `--no-snapshot`; recovery is browser-only and after the fact. Treat `eval run start` like an upload and confirm the local solution is intended for publication. To avoid overwriting, pass **both** `--solution-id` and `--project-id` for an already provisioned cloud solution; this skips package and upload. Never run `uip solution upload` for the user without asking: the same rule as [Operate](operate.md).

## Confirm what was written

After authoring, list the evaluator and eval set and read generated JSON. Confirm the evaluator has the requested `evaluatorTypeId`, the set contains its generated file reference, `Scope` is `flow`, and the entry point matches a `.bpmn` start event.

## Evidence boundary

A score is evidence about this process's output on these inputs under these evaluators—not proof of correctness. An `llm-judge-output` score includes model variance; movement of one or two points is noise. Compare runs rather than one result, and name the eval set and evaluator behind every reported number.
