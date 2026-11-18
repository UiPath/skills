# Evaluate — evaluators, eval sets, simulations, runs

Manage evaluators, eval sets, data points, and simulations with `uip maestro flow eval`; defining an `inlineAgent(...)` node does not create them. Every `eval` command takes `--path <project-dir>`, the directory containing `project.uiproj`.

<!--skill-flavor:eval-login:start-->
**Local `add` / `list` / `remove` edit project files and need no login.** Starting a run does — run `uip login` first, and it needs a matching solution in Studio Web.
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

`llm-judge-output` produces `evaluatorTypeId: "uipath-llm-judge-output-semantic-similarity"`; always pin its model. Prefer `exact-match`, `json-similarity`, or `contains` for deterministic values.

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

Most resources are addressed through their set. `--set` is required on `eval list`, `eval remove`, all three `simulation` commands, and every `run` verb including `status` and `results`; omission fails before execution with `required option '--set <name>' not specified`. Only `set` and evaluator commands omit it.

For `--evaluators`, use the generated evaluator id or filename, not its display name. Omitting `--evaluators` on `eval set add` links all existing evaluators.

Data-point input keys must match declared flow inputs. Declare them with `.input({ … })` in source and compile before `eval add`; the command reads the compiled `.flow` and fails with `Input "<name>" is not declared as an input variable in the flow` when missing. Do not use `uip maestro flow variable add`: the next `compile -o` rewrites the `.flow`, making the edit disappear or collide with `Variable '<name>' already exists`. Inspect declarations in the `.flow`; `variable` takes no `--path`:

```bash
uip maestro flow variable list ./MySolution/MyFlow/MyFlow.flow --output json
```

Build expected outputs from real records; invented keys match no record and score a fault instead of an answer.

## Simulations — stop an eval from really sending

A simulation stands in for a component, keyed by component id: its source step id, or the tool name for an inline agent's tool. It is scoped to one data point in one set; all three commands require `--set` and `--data-point`. `add` also requires `--strategy`: `Static` returns `--mock-value` verbatim, while `Llm` generates from `--simulation-instructions`. `add` also requires `--component-type` (`connector`, `agent`, `hitl`, or `Node`) unless `--parent <agent-id>` adds a child-tool simulation, which defaults to `Node`.

```bash
uip maestro flow eval simulation add <component-id> \
  --set "Smoke Tests" --data-point <id> \
  --strategy Static --component-type connector --mock-value '{"response":{"ok":true}}' \
  --path ./MySolution/MyFlow --output json

uip maestro flow eval simulation list \
  --set "Smoke Tests" --data-point <id> --path ./MySolution/MyFlow --output json
uip maestro flow eval simulation remove <component-id> \
  --set "Smoke Tests" --data-point <id> --path ./MySolution/MyFlow --output json
```

`--mock-value` is the component's raw `result`; its top-level keys are the ones the node's `outputs` read as `=result.<key>`; open the node and match them:

- Connector and inline-agent nodes read `=result.response`; pass `{"response": <value>}`.
- A `hitl` quick form maps `output` to `=result` and `status` to `=result.Action`; pass `{"Action":"<outcome name>", "<fieldId>": <value>}`. `Action` is the outcome's `name`, not its id.

`{"status":"Approve","output":{…}}` is wrong for a quick form: both `status` and `output` return null.

Before running a set more than once, simulate every side-effecting component. An unsimulated connector really sends once per eval, every run.

## Running a set

```bash
uip maestro flow eval run start   --set "Smoke Tests" --path ./MySolution/MyFlow --output json
uip maestro flow eval run status  <evalSetRunId> --set "Smoke Tests" --path ./MySolution/MyFlow --output json
uip maestro flow eval run results <evalSetRunId> --set "Smoke Tests" --path ./MySolution/MyFlow --output json
uip maestro flow eval run list    --set "Smoke Tests" --path ./MySolution/MyFlow --output json
uip maestro flow eval run compare <evalSetRunId> --compare-to <evalSetRunId> \
  --set "Smoke Tests" --path ./MySolution/MyFlow --output json
```

`run start` returns `evalSetRunId` and does not block. Poll `run status` until settled, then read `run results`. `run compare` takes both ids—the subject and `--compare-to`—to show whether a prompt or guidance change helped.

## Never upload as part of an eval workflow

<!--skill-flavor:eval-no-upload:start-->
**Never run `uip solution upload` automatically here. Always ask first.**

`eval run start` needs the solution in Studio Web. If it cannot resolve one, it fails with `solution-id could not be resolved` or a variant; never treat that as permission to upload. `eval run start` itself re-uploads and overwrites the matching Studio Web solution unless `--solution-id` and `--project-id` are passed, so ask before it too. If Studio Web assigns another id, `eval run start` and `flow debug` repoint local `.uipx` `SolutionId` and report `Data.LocalSolutionIdUpdated` (`Path`, `From`, `To`); keep and commit that change, or the next upload creates a second solution.

`uip solution upload` writes to Studio Web, creating or **overwriting** the solution matching local `.uipx` `SolutionId`; it needs no flag and raises no prompt. It can push work in progress to where teammates and triggers pick it up, send partial local state from a `uip solution download` back over whatever else moved, or discard divergent remote state. The overwrite is restorable only through the browser and only if `--no-snapshot` was not passed; recovery is after the fact, by the user, and does not undo work in progress already pushed to teammates and triggers.

Ask and offer either upload now with the user's acknowledgement, or pass `--solution-id` and `--project-id` for an existing Studio Web solution and plumb them through to `eval run start`.
<!--skill-flavor:eval-no-upload:end-->

## Confirm what was written

After authoring, list the evaluator and eval set and read the generated JSON. Confirm the evaluator has the requested `evaluatorTypeId`, the set contains its generated file reference, and the entry point matches the flow.

## Evidence boundary

A score is evidence about this flow's output on these inputs under these evaluators, not evidence that the flow is correct. An `llm-judge-output` score has model variance; one run moving a point or two is noise. Compare runs rather than reading one, and name the eval set and evaluator behind every reported number.
