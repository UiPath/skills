---
name: uipath-maestro-flow-eval
description: "UiPath Maestro Flow evaluations — design, run, inspect Flow eval sets via `uip maestro flow eval` CLI. CRUD on data points, 7 evaluator types (exact-match, json-similarity, contains, llm-judge-output/strict-json/trajectory/trajectory-simulation), Studio Web run start/status/results/list/compare. For agent (agent.json) evals→uipath-agents. For BPMN/.flow authoring→uipath-maestro-flow."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
user-invocable: true
---

# UiPath Maestro Flow Evaluations

Design test data, configure evaluators, and run evaluations against deployed Maestro Flow projects using the `uip maestro flow eval` CLI.

## When to Use This Skill

- Add or remove data points (test cases) on a Flow eval set
- Create evaluators (exact-match, json-similarity, contains, llm-judge-* types) for a Flow project
- Create or remove eval sets, link them to evaluators, pin entry points
- Start an eval run on Studio Web, poll its status, fetch detailed results
- Compare two eval runs to verify a change improved scores without regressions

For Flow authoring (`.flow` editing, node/edge CRUD, validate, debug, ship) read the `uipath-maestro-flow` skill. For agent (`agent.json`) evaluations read the `uipath-agents` skill. For BPMN evaluations the same `uip maestro` family exposes `uip maestro bpmn eval` — this skill covers Flow only.

## Critical Rules

1. **Never run `uip solution upload` automatically.** The eval run requires the Flow solution to already exist in Studio Web, but uploading from the local working tree clobbers whatever is on Studio Web. If the project was pulled from Studio Web (`uip agent pull`), edited locally in VS Code, or scaffolded on disk and never uploaded, an unprompted upload will overwrite or push unintended state. **Ask the user explicitly before any `uip solution upload`** — see [references/upload-safety.md](references/upload-safety.md).
2. **Always use `--output json`** on every `uip maestro flow eval` command. Output is parsed downstream and table format truncates UUIDs.
3. **`--path` accepts a Flow project directory OR a solution directory containing exactly one Flow project.** If the solution holds multiple Flow projects, point `--path` at the specific project directory.
4. **Local CRUD does not require login.** `add`, `remove`, `list` (data points / eval sets / evaluators) edit JSON on disk. Only `uip maestro flow eval run *` requires `uip login` and an existing Studio Web solution.
5. **Pin a model on every LLM-judge evaluator.** Empty/missing `model` produces a cryptic 500 from the LLM gateway after retries. Pass `--model <name>` on `evaluator add` or set `model` in the JSON.
6. **Reference evaluators by `id` (UUID), never by filename.** Eval sets store `evaluatorRefs: [<uuid>...]`. Renaming or copy-pasting evaluator JSON across projects without regenerating UUIDs silently breaks resolution.
7. **Pre-empt timeouts on `run start --wait`.** The CLI blocks until the run reaches a terminal state or `--timeout` elapses. `--timeout` only stops local blocking — the run continues server-side; query progress with `eval run status <run_id>`.
8. **Do not invoke this skill for `uip maestro bpmn eval` or `uip maestro flow` (non-eval) commands.** Surface scope is `uip maestro flow eval *` only.

## Quick Start

Standard workflow: scaffold evaluators → create eval set → add data points → ensure project is in Studio Web → run.

```bash
# 1. Add an evaluator (local; no login required)
uip maestro flow eval evaluator add greeting-quality \
  --type llm-judge-output \
  --model gpt-4.1-2025-04-14 \
  --path ./MySolution/MyFlow --output json

# 2. Create an eval set, pin the agent's entry point and the evaluator(s)
uip maestro flow eval set add "Smoke Tests" \
  --evaluators greeting-quality \
  --entry-point /Main.bpmn#start \
  --path ./MySolution/MyFlow --output json

# 3. Add data points (test cases)
uip maestro flow eval add hello-test \
  --set "Smoke Tests" \
  --inputs '{"message":"hello"}' \
  --expected '{"reply":"Hello! How can I help you?"}' \
  --path ./MySolution/MyFlow --output json

# 4. Confirm the solution is in Studio Web
#    DO NOT auto-run `uip solution upload`. Ask the user. See upload-safety.md.

# 5. Start the run and wait
uip maestro flow eval run start \
  --set "Smoke Tests" \
  --path ./MySolution/MyFlow \
  --wait --timeout 600 --output json

# 6. Inspect failures
uip maestro flow eval run results <eval_set_run_id> \
  --set "Smoke Tests" \
  --only-failed --verbose \
  --path ./MySolution/MyFlow --output json
```

## Reference Navigation

| Read when... | File |
|---|---|
| Looking up any `uip maestro flow eval` subcommand syntax, flags, or output | [references/commands-reference.md](references/commands-reference.md) |
| Choosing among the 7 evaluator types, writing custom prompts, hand-writing evaluator JSON | [references/evaluators-guide.md](references/evaluators-guide.md) |
| Creating eval sets, adding data points, mapping `--inputs`/`--expected`/`--criteria` to evaluator types, attaching files | [references/eval-sets-guide.md](references/eval-sets-guide.md) |
| Starting a Studio Web run, polling status, reading results, exporting CSV/JSON, comparing two runs | [references/running-guide.md](references/running-guide.md) |
| Deciding whether to call `uip solution upload` (almost always: don't auto-run; ask first) | [references/upload-safety.md](references/upload-safety.md) |

## Anti-patterns

- **Don't auto-run `uip solution upload`.** Even when an eval run errors with "solution not found in Studio Web", stop and ask the user — see [references/upload-safety.md](references/upload-safety.md). The local project may be ahead of, or diverged from, Studio Web.
- **Don't reference an evaluator by filename in `evaluatorRefs`.** Use the `id` UUID. Filenames are informational.
- **Don't pass `--type` in PascalCase.** Only kebab-case is accepted: `exact-match`, `json-similarity`, `contains`, `llm-judge-output`, `llm-judge-strict-json`, `llm-judge-trajectory`, `llm-judge-trajectory-simulation`.
- **Don't depend on a specific `--wait` polling cadence.** Treat `--wait` as a black-box block; if you need precise progress, omit it and call `eval run status` yourself.
- **Don't compare runs from different eval sets.** `eval run compare` aligns by data-point name within the set; cross-set deltas are meaningless.
- **Don't omit `--model` on LLM-judge evaluators.** The cloud worker fail-fasts before calling the LLM gateway.
- **Don't run evals during `flow debug`.** `debug` is a separate Studio Web session; evals run against the deployed/published solution. Mixing them produces confusing run IDs.

## Completion Output

After a run completes, report:

1. **Eval set run ID** and aggregate score (from `run status`)
2. **Failed data points** (from `run results --only-failed --verbose`)
3. **Comparison delta** vs the previous run (`run compare`) if one exists
4. **Suggested next step** — fix the agent/flow, re-run, or accept the result. Do NOT suggest `uip solution upload` unless the user has explicitly asked to publish edits.
