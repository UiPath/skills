# Business Rules Evaluate Guide

A rule's tests are evaluation sets of data points, each scored by exact match against the rule's decisions. `uip rules eval` writes them under `<PROJECT_DIR>/evals/rule/`, the folder Studio Web's Evaluate tab reads, so sets move both ways between the CLI and the tab.

## Critical Rules

1. **Exact match only.** `--type exact-match` is the only evaluator type; the CLI refuses every other one. When the user asks for an LLM judge, similarity, or contains scoring, say business rules are scored by exact match only, create an exact-match evaluator, and narrow what it compares with `--target-key`.
2. **Take each expected output from what the reviewed table returns for those inputs.** Never copy a value from an existing data point without checking it against the table. Key it by decision, then output: `{"<DECISION_NAME>":{"<OUTPUT_NAME>":<VALUE>}}`. `<DECISION_NAME>` is the `<decision>` element's `name` attribute, not its `label`. Any decision may be expected, intermediate ones included. A decision with one unnamed output, or a literal expression, is keyed by the decision's name twice.
3. **Write eval files only through `uip rules eval`.** Never hand-edit `evals/rule/**`. Each data point keeps a copy of its expected output per evaluator (`evaluationCriterias`); a hand edit to `expectedOutput` leaves those copies stale, and the run scores against them. The CLI also checks inputs and expected outputs against the `.dmn` before it saves.
4. **Ask before `uip rules eval runs start`.** It uploads the solution and overwrites the Studio Web solution with no prompt; Studio Web edits made since the last upload are lost. Name that in the question and run only after the user approves. When told not to ask, or no one can answer, stop after the local files and give the user the `runs start` command to run.
5. **One `.dmn` per project.** Every `uip rules eval` command refuses a project with more than one.

## Workflow

`--path` takes the rules project directory (the one holding `project.uiproj`) or a solution folder holding exactly one rules project. It defaults to the current directory.

### 1. Evaluator

```bash
uip rules eval evaluators list --path <PROJECT_DIR> --output json
uip rules eval evaluators create <EVALUATOR_NAME> --type exact-match --path <PROJECT_DIR> --output json
```

Reuse an existing exact-match evaluator when one fits. `--target-key` picks what the evaluator compares:

| `--target-key` | Compares |
|---|---|
| `*` (default) | Every decision and output the data point expects |
| `<DECISION_NAME>` | One decision's outputs |
| `<DECISION_NAME>.<OUTPUT_NAME>` | One output |

### 2. Set

```bash
uip rules eval sets list --path <PROJECT_DIR> --output json
uip rules eval sets create <SET_NAME> --evaluators <EVALUATOR_REF> [<EVALUATOR_REF>...] --path <PROJECT_DIR> --output json
```

`--evaluators` takes evaluator ids or names, space-separated; without it, the set links every evaluator in the project. A name two evaluators share is refused: pass the id. A set's evaluators are fixed at creation; to change them, create a new set.

### 3. Data points

```bash
uip rules eval create <DATA_POINT_NAME> --set <SET_NAME> --inputs '<INPUTS_JSON>' --expected '<EXPECTED_JSON>' --path <PROJECT_DIR> --output json
uip rules eval list --set <SET_NAME> --path <PROJECT_DIR> --output json
uip rules eval delete <DATA_POINT_REF> --set <SET_NAME> --path <PROJECT_DIR> --output json
```

- Add one data point per row of the review table, named after the row's Annotation, plus one per boundary the policy names (e.g. `579`, `580`, `700` for `< 580` and `[580..700)`).
- `--inputs` is keyed by input-argument name. Give each value the JSON type of its DMN type: `number` → number, `boolean` → `true`/`false`, `string`, `date`, `time`, `date and time` and durations → string.
- `--expected` is required and must give at least one output a non-null, non-empty value; exact match has nothing to compare otherwise.
- There is no update command. To change a data point, `delete` it and `create` it again.

After authoring, run `uip rules eval list` and compare every row with the table.

### 4. Run (after the user approves)

```bash
uip rules eval runs start --set <SET_NAME> --wait --path <PROJECT_DIR> --output json
```

`--wait` polls until the run ends (default 600 seconds; `--timeout <SECONDS>`, at most 3600) and prints one envelope with `Code: RulesEvalRunCompleted` and each data point's result in `Data.Results`.
<!--skill-flavor:run-target:start-->
Without a folder flag the rule is evaluated in the personal workspace, which needs a user login (`uip login`); pass `--folder-path` or `--folder-key` (never both) for another folder. `runs start` needs the project inside its solution folder, as `uip rules init` creates it.
<!--skill-flavor:run-target:end-->

### 5. Read results

```bash
uip rules eval runs results <RUN_ID> --only-failed --verbose --path <PROJECT_DIR> --output json
uip rules eval runs status <RUN_ID> --path <PROJECT_DIR> --output json
uip rules eval runs list --set <SET_NAME> --path <PROJECT_DIR> --output json
uip rules eval runs compare <RUN_ID> --compare-to <OTHER_RUN_ID> --path <PROJECT_DIR> --output json
```

`<RUN_ID>` is `Data.EvalSetRunId` from `runs start`. The read commands find the run from a record `runs start` keeps on this machine; elsewhere, pass `--project-id <PROJECT_ID>` (`Data.ProjectId` from `runs start`). When the `--compare-to` run was started under another project (a re-imported solution), also pass `--compare-to-project-id <OTHER_PROJECT_ID>`.

A failing data point means the table or the expected output is wrong. Check the row the inputs should hit against the policy, fix the table (then `refresh` and `validate`) or recreate the data point, and run again. Stop after 3 rounds and show the user the table and the failing data points.

## Failures

| Error | Fix |
|---|---|
| `--type` other than `exact-match` refused | Use `--type exact-match` (Critical Rule 1) |
| `Input "<NAME>" is not an input of the rule` | Key `--inputs` by the `.dmn`'s input names; the message lists them |
| `Input "<NAME>" must be of type <TYPE>` | Give the value the JSON type in step 3 |
| `"<NAME>" is not a decision of the rule` / `is not an output of decision` | Key `--expected` by decision `name`, then output; the message lists both |
| `The expected output gives no decision an output value` | Give at least one output a non-null, non-empty value |
| Removing a set's last exact-match evaluator refused | Create and link another exact-match evaluator first |
| `Evaluator name "<NAME>" matches 2 evaluators` | Pass the evaluator id |
| `holds 2 .dmn files` | Keep one `.dmn` per project |
| `runs start`: `has no data points` / `links no evaluators` / `expects nothing` | Fix the set locally; `runs start` refuses it before login or upload |
<!--skill-flavor:personal-workspace-row:start-->
| `runs start`: `permission_denied` on the personal workspace | Log in as a user with `uip login`, or pass `--folder-path` |
<!--skill-flavor:personal-workspace-row:end-->
| `runs start --wait`: `Result: TimeoutError`, exit 4 | The run is still going; check it with the `runs status` command in `Instructions`, or wait longer with `--timeout` |
| `runs start --wait`: `Evaluation run finished with status "workloadFailed"` | The rule did not run. Read each data point's error in `Data.Results`; run `uip rules refresh` so decision names match the `.dmn` |
| `No local record of eval run` (`not_found`) | Pass `--project-id <PROJECT_ID>` |
| `Business Rules is not available on tenant` / `is a preview feature and is not enabled` | Stop and relay the CLI's instruction (SKILL.md Critical Rule 8) |
