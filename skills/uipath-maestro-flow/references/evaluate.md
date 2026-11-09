# Evaluate — evaluators, eval sets, simulations, runs

Manage evaluators, eval sets, data points, and simulations with `uip maestro flow eval`; defining an `inlineAgent(...)` node does not create them. Every `eval` command takes `--path <project-dir>` containing `project.uiproj`.
Use this when the request asks for evaluation assets, or for a flow to be evaluated.

<!--skill-flavor:eval-login:start-->
**Local `add` / `list` / `remove` edit project files and need no login.**
Starting a run does — `uip login` first, and it needs a matching solution in Studio Web.
<!--skill-flavor:eval-login:end-->

Probe the installed CLI once, then let it write the JSON formats and generated file references rather than hand-authoring them:

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

`llm-judge-output` produces `evaluatorTypeId: "uipath-llm-judge-output-semantic-similarity"`; always pin its model. Prefer deterministic `exact-match`, `json-similarity`, or `contains` for directly comparable values.

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

uip maestro flow eval list            --set "Smoke Tests" --path ./MySolution/MyFlow --output json
uip maestro flow eval remove <id>     --set "Smoke Tests" --path ./MySolution/MyFlow --output json
uip maestro flow eval set list        --path ./MySolution/MyFlow --output json
uip maestro flow eval set remove <id> --path ./MySolution/MyFlow --output json
```

Address almost everything through its set. `--set` is required on `eval list`, `eval remove`, all three `simulation` commands, and every `run` verb including `status` and `results`; omitting it fails before execution with `required option '--set <name>' not specified`. Only `set` and evaluator commands omit it.

For `--evaluators`, use the generated evaluator id or filename, not only a display name. Omitting it on `eval set add` links all existing evaluators.

Data-point input keys must match declared flow inputs. Declare them with `.input({ … })` in source and compile before `eval add`; it reads the compiled `.flow`, and a missing input fails with `Input "<name>" is not declared as an input variable in the flow`. Do not add inputs with `uip maestro flow variable add`: the next `compile -o` rewrites the `.flow`, so the edit disappears or collides with `Variable '<name>' already exists`. Inspect declarations by passing the `.flow` itself; `variable` takes no `--path`:

```bash
uip maestro flow variable list ./MySolution/MyFlow/MyFlow.flow --output json
```

Build expected outputs from real records, not invented ones; invented keys match no record and score a fault instead of an answer.

## Simulations — stop an eval from really sending

A simulation stands in for a component, keyed by its source step id or an inline agent tool name, and is scoped to one data point in one set. All three commands require `--set` and `--data-point`. `add` also requires `--strategy`: `Static` returns `--mock-value` verbatim; `Llm` generates from `--simulation-instructions`. It requires `--component-type` (`connector`, `agent`, or `subflow`) unless `--parent <agent-id>` adds a child-tool simulation, which defaults to `Node`.

```bash
uip maestro flow eval simulation add <component-id> \
  --set "Smoke Tests" --data-point <id> \
  --strategy Static --component-type connector --mock-value '{"ok":true}' \
  --path ./MySolution/MyFlow --output json

uip maestro flow eval simulation list \
  --set "Smoke Tests" --data-point <id> --path ./MySolution/MyFlow --output json
uip maestro flow eval simulation remove <component-id> \
  --set "Smoke Tests" --data-point <id> --path ./MySolution/MyFlow --output json
```

Simulate every side-effecting component before running a set more than once. An unsimulated connector step really sends once per eval, every run.

## Running a set

```bash
uip maestro flow eval run start   --set "Smoke Tests" --path ./MySolution/MyFlow --output json
uip maestro flow eval run status  <evalSetRunId> --set "Smoke Tests" --path ./MySolution/MyFlow --output json
uip maestro flow eval run results <evalSetRunId> --set "Smoke Tests" --path ./MySolution/MyFlow --output json
uip maestro flow eval run list    --set "Smoke Tests" --path ./MySolution/MyFlow --output json
uip maestro flow eval run compare <evalSetRunId> --compare-to <evalSetRunId> \
  --set "Smoke Tests" --path ./MySolution/MyFlow --output json
```

`run start` returns `evalSetRunId` without blocking. Poll `run status` until settled, then read `run results`. `run compare` takes both ids—the subject and `--compare-to`—to show that a prompt or guidance change helped rather than assert it.

## Never upload as part of an eval workflow

<!--skill-flavor:eval-no-upload:start-->
**Never run `uip solution upload` automatically here. Always ask first.**

`eval run start` needs the solution in Studio Web; if it cannot resolve one, it fails with `solution-id could not be resolved` or a variant. That error is not permission to upload.

`uip solution upload` writes to Studio Web, creating or **overwriting** the solution matching the local `.uipx` `SolutionId`; it needs no flag and raises no prompt. This can publish unfinished local work, overwrite unrelated remote changes after a download, or discard divergent remote state—nothing is merged.
Three ways that costs someone real work:

1. The user is iterating locally and meant to test *before* publishing. Upload
   pushes work in progress to where teammates and triggers pick it up.
2. The user pulled the solution with `uip solution download` to change one
   piece. Upload sends partial local state back over whatever else moved.
3. Local and Studio Web have diverged. Upload discards the remote side —
   nothing is merged.

The overwrite is recorded as a restorable version unless `--no-snapshot` was passed, but recovery is browser-only, after the fact, by the user, and does not undo publishing unfinished work (teammates or triggers may already have picked it up). Ask, and offer either uploading now with the user's acknowledgement or passing `--solution-id` and `--project-id` for an existing Studio Web solution and plumbing them through to `eval run start`.
<!--skill-flavor:eval-no-upload:end-->

## Confirm what was written

After authoring, list the evaluator and eval set and read the generated JSON. Confirm the evaluator has the requested `evaluatorTypeId`, the set contains its generated file reference, and the entry point matches the flow.

## Evidence boundary

A score is evidence about this flow's output on these inputs under these evaluators—not proof the flow is correct. An `llm-judge-output` score includes model variance; a one- or two-point movement is noise. Compare runs rather than reading one, and name the eval set and evaluator behind every reported number.