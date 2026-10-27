# Evaluate — evaluators, eval sets, simulations, runs

Evaluators, eval sets, data points and simulations are project assets managed by
`uip maestro bpmn eval`; authoring an agent or task in the `.bpmn` does not
create them. Use this when the request asks for evaluation assets, or for a BPMN
process to be evaluated.

Every `eval` command takes `--path <path>` — a Maestro BPMN project directory,
or a solution directory with exactly one BPMN project. It defaults to `.`.

**Local `add` / `list` / `remove` edit project files and need no login.**
Starting a run does — `uip login` first, and it needs a matching BPMN solution
already in Studio Web.

Probe the installed CLI once, then let it write the JSON formats and generated
file references rather than hand-authoring them:

```bash
uip maestro bpmn eval --help --output json
```

## Evaluators — how an output is scored

```bash
uip maestro bpmn eval evaluator add response-quality \
  --type llm-judge-output \
  --model gpt-4.1-2025-04-14 \
  --description "Score the response against the expected result" \
  --target-key '*' \
  --path ./MySolution/MyBpmn --output json

uip maestro bpmn eval evaluator list        --path ./MySolution/MyBpmn --output json
uip maestro bpmn eval evaluator remove <id> --path ./MySolution/MyBpmn --output json
```

The evaluator types and their stored `evaluatorTypeId`s are the shared eval
engine, identical to Flow — `llm-judge-output` produces
`uipath-llm-judge-output-semantic-similarity`. Always pin a model for an LLM
judge. For deterministic values prefer `exact-match`, `json-similarity`, or
`contains` — a judge on a value that can simply be compared is variance for
nothing.

## Evals and eval sets

```bash
uip maestro bpmn eval set add "Smoke Tests" \
  --entry-point Event_start \
  --path ./MySolution/MyBpmn --output json

uip maestro bpmn eval add "basic case" \
  --set "Smoke Tests" \
  --inputs '{"request":"hello"}' \
  --expected '{"reply":"hello"}' \
  --path ./MySolution/MyBpmn --output json

uip maestro bpmn eval list            --set "Smoke Tests" --path ./MySolution/MyBpmn --output json
uip maestro bpmn eval remove <id>     --set "Smoke Tests" --path ./MySolution/MyBpmn --output json
uip maestro bpmn eval set list        --path ./MySolution/MyBpmn --output json
uip maestro bpmn eval set remove <id> --path ./MySolution/MyBpmn --output json
```

Almost everything is addressed **through its set**. `--set` is required on `eval
list` and `eval remove`, on all three `simulation` commands, and on every `run`
verb including `status` and `results`. Only the `set` commands themselves and
the evaluator commands do without it.

Use the generated evaluator id or filename when explicitly passing
`--evaluators`; a display name alone is not a stable reference and a Studio Web
run cannot resolve it. Omitting the flag on `eval set add` links all evaluators
that currently exist, and evaluators added later are **not** linked
retroactively.

`--entry-point` is a BPMN **start-event id** from the `.bpmn` (e.g.
`Event_start`), stored as the set's `selectedEntrypoint`. It is not a path: a
value containing `/` or `#` is rejected (`The entry point is a start event id
from the .bpmn file, not a path.`), as is a value that is not one of the
process's derivable start events. **Node-scoped (agent-node) and document eval
sets are not authorable via the CLI yet** — the CLI only creates `flow`-scoped
sets, and the `set add`/`set list` output reports that `Scope` (create them in
Studio Web instead). This differs from Flow. Omit `--entry-point` to use the
process's default start event — the one flagged `isDefault`, else the first
derivable entry point. Override it per run with `run start --entry-point`.

A data point's input and output keys are validated against the entry point's
declared schema in the project's **`entry-points.json`** (the `.bpmn`'s
`<uipath:input>` carries internal ids, not the user-facing names). An undeclared
key fails with `Input "<name>" is not a declared input of the BPMN process.
Declared inputs: …`. Declare the missing variable through BPMN authoring and
regenerate project metadata (see [structural-bpmn.md](structural-bpmn.md) and
[shared/local-metadata-regeneration-guide.md](shared/local-metadata-regeneration-guide.md)),
then re-run `eval add`. Validation is best-effort: when the entry point declares
no inputs/outputs it is skipped rather than rejecting keys. Build expected
outputs from real records, not invented ones — an invented key matches no record
and the eval scores a fault instead of an answer.

## Simulations — stop an eval from really sending

A simulation stands in for a component during a run, keyed by component id: the
element id from the `.bpmn`, or the tool name for an agent's tool. A simulation
is scoped to one **data point inside one set**, so all three commands require
`--set` and `--data-point`. `add` also requires `--strategy` and
`--component-type` (`connector`, `agent`, `subprocess`), unless `--parent
<agent-id>` adds a child tool simulation, which defaults `--component-type` to
`Node`.

```bash
# Static — returns --mock-value verbatim
uip maestro bpmn eval simulation add <component-id> \
  --set "Smoke Tests" --data-point <id> \
  --strategy Static --component-type connector --mock-value '{"ok":true}' \
  --path ./MySolution/MyBpmn --output json

# Llm — generates from instructions; --output-schema is REQUIRED
uip maestro bpmn eval simulation add <component-id> \
  --set "Smoke Tests" --data-point <id> \
  --strategy Llm --component-type connector \
  --simulation-instructions "Pretend to send the email and return success." \
  --output-schema '{"type":"object","properties":{"status":{"type":"string"}}}' \
  --path ./MySolution/MyBpmn --output json

uip maestro bpmn eval simulation list \
  --set "Smoke Tests" --data-point <id> --path ./MySolution/MyBpmn --output json
uip maestro bpmn eval simulation remove <component-id> \
  --set "Smoke Tests" --data-point <id> --path ./MySolution/MyBpmn --output json
```

**`--output-schema` is required for every `Llm` simulation — the key divergence
from Flow.** Flow auto-resolves a component's output schema from the `.flow`;
the BPMN CLI does not, so an `Llm` simulation without it fails fast with
`--output-schema is required for the Llm strategy (BPMN cannot auto-resolve the
component's output schema)`. A consequence worth knowing: because the schema is
always supplied, BPMN never consults the process to resolve it, so an `Llm`
simulation does **not** require the simulated (or parent agent) node to already
exist in the `.bpmn` the way Flow's does.

To simulate one tool inside an agent, pass `--parent <agent-node-id>`; the
child's `<component-id>` is the tool's runtime name. A `Static` child tool
simulation needs only `--mock-value`; since BPMN can't resolve the tool's schema
to check the mock keys, the CLI writes it with a `Mock value key validation was
skipped` warning in `Data.Warning`. An `Llm` child tool simulation still
requires `--output-schema`. Adding `--parent` and `list`/`remove` with
`--parent` act on the agent node's child simulations.

Simulate every side-effecting component before running a set more than once. An
unsimulated connector step really sends — once per data point, every run.

## Running a set

```bash
uip maestro bpmn eval run start   --set "Smoke Tests" --path ./MySolution/MyBpmn --output json
uip maestro bpmn eval run status  <evalSetRunId> --set "Smoke Tests" --path ./MySolution/MyBpmn --output json
uip maestro bpmn eval run results <evalSetRunId> --set "Smoke Tests" --path ./MySolution/MyBpmn --output json
uip maestro bpmn eval run list    --set "Smoke Tests" --path ./MySolution/MyBpmn --output json
uip maestro bpmn eval run compare <evalSetRunId> --compare-to <evalSetRunId> \
  --set "Smoke Tests" --path ./MySolution/MyBpmn --output json
```

`run start` returns an `evalSetRunId` and does not block. Poll `run status`
until it settles, then read `run results`. `run start` resolves the BPMN project
(workload) id and solution from the parent `.uipx` or `SolutionStorage.json`;
pass `--solution-id` / `--project-id` only when the working tree does not carry
them, `--folder-key` to run outside the personal workspace, and `--entry-point`
to override the set's pinned start event for one run.

`--wait` polls to a terminal state (default 600s) and then prints results. A
terminal `Failed` or `WorkloadFailed` set-run prints the per-data-point results,
then a failure envelope and a **non-zero exit** — so `--wait` in CI does not
read a failed workload as success. `WorkloadFailed` means the process itself
failed to execute; triage it as a runtime fault via
[diagnose/CAPABILITY.md](diagnose/CAPABILITY.md), not an evaluator problem. A
completed run whose evaluators merely scored low is still a success: the eval
ran. `run results` takes `--only-failed`, `--verbose` (judge justifications),
and `--export-format json|csv` (writes `bpmn-eval-results-<timestamp>.{json,csv}`
to the working directory). `run compare` puts one run against another by
`--compare-to`, aligning data points by their stable snapshot id — which is how
a prompt or process change is shown to have helped rather than asserted to have.

## Never upload as part of an eval workflow

**Never run `uip solution upload` automatically here. Always ask first.**

`eval run start` needs the BPMN solution in Studio Web, and when it cannot
resolve one it fails. That error is not licence to upload. `uip solution upload`
writes to Studio Web: it creates, or **overwrites**, the solution matching the
local `.uipx` `SolutionId`, with no flag and no prompt. Three ways that costs
someone real work:

1. The user is iterating locally and meant to test *before* publishing. Upload
   pushes work in progress to where teammates and triggers pick it up.
2. The user pulled the solution with `uip solution download` to change one
   piece. Upload sends partial local state back over whatever else moved.
3. Local and Studio Web have diverged. Upload discards the remote side —
   nothing is merged.

The overwrite is recorded as a restorable version unless `--no-snapshot` was
passed, but recovery is browser-only, after the fact, by the user, and it does
not undo case 1. Ask, and offer the two real options: upload now with the user's
acknowledgement, or pass `--solution-id` and `--project-id` for an existing
Studio Web solution and plumb them through to `eval run start`. (Same rule as
Operate's `solution upload`.)

## Confirm what was written

After authoring, list the evaluator and the eval set and read the generated
JSON. Confirm the evaluator carries the requested `evaluatorTypeId`, the set
contains its generated file reference, that `Scope` is `flow`, and the entry
point matches a start event in the `.bpmn`.

## Evidence boundary

A score is evidence about this process's output on these inputs under these
evaluators. It is not evidence the process is correct, and an `llm-judge-output`
score carries a model's variance — one run moving a point or two is noise.
Compare runs rather than reading one, and name the eval set and the evaluator
behind any number reported.
