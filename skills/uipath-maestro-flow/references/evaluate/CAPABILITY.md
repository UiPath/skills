# Evaluate — Design and run Flow evaluations

Capability index for `uip maestro flow eval` — evaluator CRUD (7 types), eval set CRUD with entry-point pinning, data point management with file attachments, and Studio Web run start/status/results/list/compare. Local CRUD is offline; runs require `uip login` and a Flow solution that already exists in Studio Web.

> **Where you came from / where to go next.** Evaluate is downstream of Operate (ship the flow → evaluate it on Studio Web) and feeds back into Author (failing eval → fix the `.flow` → re-ship → re-evaluate). Build/edit lives in [author/CAPABILITY.md](../author/CAPABILITY.md); publish/deploy lives in [operate/CAPABILITY.md](../operate/CAPABILITY.md); fault triage on a debug or process run lives in [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md).
>
> **Inherits universal rules from [SKILL.md](../../SKILL.md)** — `--output json` + prefer `--output-filter` for extraction, no `flow debug` without consent, never invoke other skills automatically, AskUserQuestion dropdown pattern, **plain-English narration + granular `TodoWrite` (opt-in — silent by default; engage when the user asks for verbosity)**. The rules below are evaluate-scoped and apply on top.

## When to use this capability

- Add or remove data points (test cases) on a Flow eval set
- Create evaluators (`exact-match`, `json-similarity`, `contains`, `llm-judge-*` types) for a Flow project
- Create or remove eval sets, link them to evaluators, pin entry points
- Add, list, or remove simulations on data points (`uip maestro flow eval simulation`)
- Start an eval run on Studio Web, poll its status, fetch detailed results
- Compare two eval runs to verify a change improved scores without regressions

For agent (`agent.json`) evaluations read the `uipath-agents` skill. For BPMN evaluations read the `uipath-maestro-bpmn` skill — this capability covers Flow only.

## Critical rules

1. **Check Flow eval CLI availability once.** Run `uip maestro flow eval --help --output json` before using eval commands. If it returns `unknown command 'eval'`, the installed CLI does not expose Flow eval yet. Stop, report that the user needs a CLI/tool version with Flow eval support, and do not spend turns searching npm packages or source bundles.
2. **Never run `uip solution upload` automatically as part of an eval workflow.** The eval run requires the Flow solution to already exist in Studio Web, but uploading from the local working tree clobbers whatever is on Studio Web. If the project was pulled from Studio Web (`uip agent pull`), edited locally in VS Code, or scaffolded on disk and never uploaded, an unprompted upload will overwrite or push unintended state. Ask the user explicitly before any `uip solution upload` — see [upload-safety.md](references/upload-safety.md).
3. **`--path` accepts a Flow project directory OR a solution directory containing exactly one Flow project.** If the solution holds multiple Flow projects, point `--path` at the specific project directory.
4. **Local CRUD does not require login.** `add`, `remove`, `list` (data points / eval sets / evaluators) edit JSON on disk. Only `uip maestro flow eval run *` requires `uip login` and an existing Studio Web solution.
5. **Pin a model on every LLM-judge evaluator.** Empty/missing `model` produces a cryptic 500 from the LLM gateway after retries. Pass `--model <name>` on `evaluator add` or set `model` in the JSON.
6. **Declare input variables before adding data points with `--inputs`.** `eval add` validates input keys against the Flow's declared input variables and fails fast on unknown keys. Add missing input variables first (for example, `uip maestro flow variable add My.flow name --direction in --type string --output json`) or change the data point input JSON to match the Flow schema.
7. **Let the CLI manage evaluator references.** Eval sets store `evaluatorRefs` as the evaluator file refs produced by `evaluator add` (for example, `greeting-match-1234abcd.json`). Use `set add --evaluators <id_or_file_base>` or the default "all current evaluators" behavior instead of hand-writing refs.
8. **Pre-empt timeouts on `run start --wait`.** The CLI blocks until the run reaches a terminal state or `--timeout` elapses. `--timeout` only stops local blocking — the run continues server-side; query progress with `eval run status <run_id>`.

## Quick Start

Standard workflow: scaffold evaluators → create eval set → add data points → confirm project is in Studio Web → run.

```bash
# 1. Add an evaluator (local; no login required)
uip maestro flow eval evaluator add greeting-quality \
  --type llm-judge-output \
  --model gpt-4.1-2025-04-14 \
  --path ./MySolution/MyFlow --output json

# 2. Create an eval set, pin the entry point and the evaluator(s)
uip maestro flow eval set add "Smoke Tests" \
  --evaluators greeting-quality \
  --entry-point /Main.bpmn#start \
  --path ./MySolution/MyFlow --output json

# 3. Add data points (test cases)
#    The `message` key must already be declared as a Flow input variable.
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

## Workflow

| Journey | Read |
| --- | --- |
| Look up any `uip maestro flow eval` subcommand syntax, flags, defaults, output codes | [commands-reference.md](references/commands-reference.md) |
| Choose among the 7 evaluator types, write custom prompts, hand-write evaluator JSON | [evaluators-guide.md](references/evaluators-guide.md) |
| Create eval sets, add data points, map `--inputs`/`--expected`/`--criteria` to evaluator types, attach files | [eval-sets-guide.md](references/eval-sets-guide.md) |
| Start a Studio Web run, poll status, read results, export CSV/JSON, compare two runs | [running-guide.md](references/running-guide.md) |
| Decide whether to call `uip solution upload` (almost always: don't auto-run; ask first) | [upload-safety.md](references/upload-safety.md) |

## Common tasks

| I need to... | Read these |
| --- | --- |
| **Add an evaluator** | [evaluators-guide.md](references/evaluators-guide.md) + [commands-reference.md — Evaluators](references/commands-reference.md#evaluators) |
| **Pick the right evaluator type** | [evaluators-guide.md — When to Pick Each Type](references/evaluators-guide.md#when-to-pick-each-type) |
| **Create an eval set and pin an entry point** | [eval-sets-guide.md — Eval Set Lifecycle](references/eval-sets-guide.md#eval-set-lifecycle) |
| **Add a data point with file attachments** | [eval-sets-guide.md — `--input-file`](references/eval-sets-guide.md#--input-file-keypath) |
| **Set per-data-point criteria for trajectory evaluators** | [eval-sets-guide.md — `--criteria`](references/eval-sets-guide.md#--criteria) |
| **Add a simulation to a data point** | [eval-sets-guide.md — Simulations](references/eval-sets-guide.md#simulations-on-data-points) + [commands-reference.md — Simulations](references/commands-reference.md#simulations) |
| **Start a Studio Web eval run** | [running-guide.md — Start a Run](references/running-guide.md#start-a-run) |
| **Poll run status without `--wait`** | [running-guide.md — Check Status](references/running-guide.md#check-status) |
| **Inspect only failed data points** | [running-guide.md — Detailed Results](references/running-guide.md#detailed-results) (`--only-failed --verbose`) |
| **Compare two runs side-by-side** | [running-guide.md — Compare Two Runs](references/running-guide.md#compare-two-runs) |
| **Decide whether to call `uip solution upload`** | [upload-safety.md](references/upload-safety.md) |
| **Look up the `eval` subcommand tree, flags, defaults, output codes** | [commands-reference.md](references/commands-reference.md) |
| **My eval run failed** | [running-guide.md — Failure Detection](references/running-guide.md#failure-detection); for flow-level faults [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md) |

## Anti-patterns

- **Don't auto-run `uip solution upload`.** Even when an eval run errors with "solution not found in Studio Web", stop and ask the user — see [upload-safety.md](references/upload-safety.md). The local project may be ahead of, or diverged from, Studio Web.
- **Don't hand-write `evaluatorRefs` unless you are repairing an eval set.** Prefer `uip maestro flow eval set add --evaluators ...` or the default all-evaluators behavior so the CLI writes the correct refs.
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

## References

### Evaluate-scoped

- [commands-reference.md](references/commands-reference.md) — every `uip maestro flow eval` subcommand, flags, defaults, output `Code` enum
- [evaluators-guide.md](references/evaluators-guide.md) — 7 evaluator types mapped to internal `uipath-*` IDs, JSON shapes, template variables
- [eval-sets-guide.md](references/eval-sets-guide.md) — eval set + data point CRUD, `--inputs`/`--expected`/`--criteria`/`--input-file`/`--search-text`, simulations
- [running-guide.md](references/running-guide.md) — run start/status/results/list/compare, JMESPath `--output-filter`, failure detection
- [upload-safety.md](references/upload-safety.md) — the `solution upload` rule

### Cross-capability (shared)

- [shared/cli-commands.md](../shared/cli-commands.md) — flat CLI lookup including `eval` subcommands
- [shared/cli-conventions.md](../shared/cli-conventions.md) — login states, `--output json`, JSON output shape
