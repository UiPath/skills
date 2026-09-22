# Evaluate — evaluators, eval sets, simulations, runs

Evaluators, eval sets, data points and simulations are project assets managed by
`uip maestro flow eval`; defining an `inlineAgent(...)` node does not create
them. Use this when the request asks for evaluation assets, or for a flow to be
evaluated.

Every command takes `--path <project-dir>` — the directory holding
`project.uiproj`.

**Local `add` / `list` / `remove` edit project files and need no login.**
Starting a run does — `uip login` first, and it needs a matching solution in
Studio Web.

Probe the installed CLI once, then let it write the JSON formats and generated
file references rather than hand-authoring them:

```bash
uip maestro flow eval --help --output json
```

## Evaluators — how an output is scored

```bash
uip maestro flow eval evaluator add response-quality \
  --type llm-judge-output \
  --model gpt-4.1-2025-04-14 \
  --description "Score the response against the expected result" \
  --target-key '*' \
  --path ./MySolution/MyFlow --output json

uip maestro flow eval evaluator list        --path ./MySolution/MyFlow --output json
uip maestro flow eval evaluator remove <id> --path ./MySolution/MyFlow --output json
```

`llm-judge-output` produces
`evaluatorTypeId: "uipath-llm-judge-output-semantic-similarity"`. Always pin a
model for an LLM judge. For deterministic values prefer `exact-match`,
`json-similarity`, or `contains` — a judge on a value that can simply be
compared is variance for nothing.

## Evals and eval sets

```bash
uip maestro flow eval set add "Smoke Tests" \
  --entry-point start \
  --path ./MySolution/MyFlow --output json

uip maestro flow eval add "basic case" \
  --set "Smoke Tests" \
  --inputs '{"request":"hello"}' \
  --expected '{"reply":"hello"}' \
  --path ./MySolution/MyFlow --output json

uip maestro flow eval list           --path ./MySolution/MyFlow --output json
uip maestro flow eval remove <id>    --path ./MySolution/MyFlow --output json
uip maestro flow eval set list       --path ./MySolution/MyFlow --output json
uip maestro flow eval set remove <id> --path ./MySolution/MyFlow --output json
```

Use the generated evaluator id or filename when explicitly passing
`--evaluators`; a display name alone is not a stable reference. Omitting the
flag on `eval set add` links all evaluators that currently exist.

A data point's input keys must match the flow's declared inputs — `.input({ … })`
in the source, or:

```bash
uip maestro flow variable list --path ./MySolution/MyFlow --output json
uip maestro flow variable add  --path ./MySolution/MyFlow --output json
```

Build expected outputs from real records rather than invented ones, for the same
reason a debug run needs real inputs: an invented key matches no record, and the
eval scores a fault instead of an answer.

## Simulations — stop an eval from really sending

A simulation stands in for a component during a run, keyed by component id: the
step id from the source, or the tool name for an inline agent's tool.

```bash
uip maestro flow eval simulation add <component-id>    --path ./MySolution/MyFlow --output json
uip maestro flow eval simulation list                  --path ./MySolution/MyFlow --output json
uip maestro flow eval simulation remove <component-id> --path ./MySolution/MyFlow --output json
```

Simulate every side-effecting component before running a set more than once. An
unsimulated connector step really sends — once per eval, every run.

## Running a set

```bash
uip maestro flow eval run start   --set "<name>"  --path ./MySolution/MyFlow --output json
uip maestro flow eval run status  <evalSetRunId>  --path ./MySolution/MyFlow --output json
uip maestro flow eval run results <evalSetRunId>  --path ./MySolution/MyFlow --output json
uip maestro flow eval run list    --set "<name>"  --path ./MySolution/MyFlow --output json
uip maestro flow eval run compare <evalSetRunId>  --path ./MySolution/MyFlow --output json
```

`run start` returns an `evalSetRunId` and does not block. Poll `run status`
until it settles, then read `run results`. `run compare` puts a run against a
previous one, which is how a prompt or guidance change is shown to have helped
rather than asserted to have.

## Never upload as part of an eval workflow

**Never run `uip solution upload` automatically here. Always ask first.**

`eval run start` needs the solution in Studio Web, and when it cannot resolve
one it fails with `solution-id could not be resolved` or a variant. That error
is not licence to upload.

`uip solution upload` writes to Studio Web: it creates, or **overwrites**, the
solution matching the local `.uipx` `SolutionId`. No flag is needed and no
prompt is raised. Three ways that costs someone real work:

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
Studio Web solution and plumb them through to `eval run start`.

## Confirm what was written

After authoring, list the evaluator and the eval set and read the generated
JSON. Confirm the evaluator carries the requested `evaluatorTypeId`, the set
contains its generated file reference, and the entry point matches the flow.

## Evidence boundary

A score is evidence about this flow's output on these inputs under these
evaluators. It is not evidence the flow is correct, and an `llm-judge-output`
score carries a model's variance — one run moving a point or two is noise.
Compare runs rather than reading one, and name the eval set and the evaluator
behind any number reported.
