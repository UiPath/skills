# Evaluate — Design and run Flow evaluations

Capability index for `uip maestro flow eval` — evaluator CRUD (7 types), eval-set CRUD with entry-point pinning, data-point management with file attachments, and Studio Web run start/status/results/list/compare. Local CRUD is offline; runs require `uip login` and a Flow solution that already exists in Studio Web.

> **Where you came from / where to go next.** Evaluate is downstream of Operate (ship the flow → evaluate it on Studio Web) and feeds back into Author (failing eval → fix the `.flow` → re-ship → re-evaluate). Build/edit lives in [author/CAPABILITY.md](../author/CAPABILITY.md); publish/deploy lives in [operate/CAPABILITY.md](../operate/CAPABILITY.md); fault triage on a debug or process run lives in [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md).
>
> **Inherits universal rules from [SKILL.md](../../SKILL.md)** — `--output json` + prefer `--output-filter` for extraction, no `flow debug` without consent, never invoke other skills automatically, dropdown question pattern, **plain-English narration + granular progress list (opt-in — silent by default; engage when the user asks for verbosity)**. The rules below apply on top.

## When to use this capability

- Add/remove Flow eval-set data points, including file attachments and simulations.
- Create/remove evaluators (`exact-match`, `json-similarity`, `contains`, `llm-judge-*`), eval sets, and evaluator links; pin entry points.
- Start, poll, inspect, list, and compare Studio Web eval runs.

For agent (`agent.json`) evaluations read the `uipath-agents` skill. For BPMN evaluations read the `uipath-maestro-bpmn` skill — this capability covers Flow only.

## Critical rules

1. **Check Flow eval CLI availability once.** Run `uip maestro flow eval --help --output json` before using eval commands. If it returns `unknown command 'eval'`, the installed CLI does not expose Flow eval yet. Stop, report that the user needs a CLI/tool version with Flow eval support, and do not spend turns searching npm packages or source bundles.
<!--skill-flavor:upload-safety-critical-rule:start-->
2. **Never run `uip solution upload` automatically as part of an eval workflow.** The eval run requires the Flow solution to already exist in Studio Web, but uploading from the local working tree clobbers whatever is on Studio Web. If the project was pulled from Studio Web (`uip solution download`), edited locally in VS Code, or scaffolded on disk and never uploaded, an unprompted upload will overwrite or push unintended state. Ask the user explicitly before any `uip solution upload` — see [upload-safety.md](upload-safety.md).
<!--skill-flavor:upload-safety-critical-rule:end-->
3. **`--path` accepts a Flow project directory OR a solution directory containing exactly one Flow project.** If the solution holds multiple Flow projects, point `--path` at the specific project directory.
4. **Local CRUD does not require login.** `add`, `remove`, `list` (data points / eval sets / evaluators) edit JSON on disk. Only `uip maestro flow eval run *` requires `uip login` and an existing Studio Web solution.
5. **Pin a model on every LLM-judge evaluator.** Empty/missing `model` produces a cryptic 500 from the LLM gateway after retries. Pass `--model <name>` on `evaluator add` or set `model` in the JSON.
6. **Declare input variables before adding data points with `--inputs`.** `eval add` validates input keys against the Flow's declared input variables and fails fast on unknown keys. Add missing input variables first (for example, `uip maestro flow variable add My.flow name --direction in --type string --output json`) or change the data point input JSON to match the Flow schema.
7. **Let the CLI manage evaluator references.** Eval sets store `evaluatorRefs` as the evaluator file refs produced by `evaluator add` (for example, `greeting-match-1234abcd.json`). If the set should use every evaluator that already exists, omit `--evaluators` so the CLI writes those generated file refs. If you must pass `--evaluators`, pass the evaluator id or generated file base/ref from `evaluator add/list` — never the display name alone (`greeting-match`), because Studio Web does not resolve display-name refs.
8. **Pre-empt timeouts on `run start --wait`.** The CLI blocks until the run reaches a terminal state or `--timeout` elapses. `--timeout` only stops local blocking — the run continues server-side; query progress with `eval run status <run_id>`.

## Quick Start

Run this workflow: add an evaluator, create and populate an eval set, confirm the solution is in Studio Web, then run it.

```bash
# Add an evaluator (local; no login required)
uip maestro flow eval evaluator add greeting-quality \
  --type llm-judge-output \
  --model gpt-4.1-2025-04-14 \
  --path ./MySolution/MyFlow --output json

# Create an eval set, pin the entry point, and attach all current evaluators
uip maestro flow eval set add "Smoke Tests" \
  --entry-point /Main.bpmn#start \
  --path ./MySolution/MyFlow --output json

# Add a data point; message must be a declared Flow input variable
uip maestro flow eval add hello-test \
  --set "Smoke Tests" \
  --inputs '{"message":"hello"}' \
  --expected '{"reply":"Hello! How can I help you?"}' \
  --path ./MySolution/MyFlow --output json

<!--skill-flavor:upload-safety-workflow-comment:start-->
# Confirm the solution is in Studio Web.
# DO NOT auto-run `uip solution upload`. Ask the user. See upload-safety.md.
<!--skill-flavor:upload-safety-workflow-comment:end-->

# Start the run and wait
uip maestro flow eval run start \
  --set "Smoke Tests" \
  --path ./MySolution/MyFlow \
  --wait --timeout 600 --output json

# Inspect failures
uip maestro flow eval run results <eval_set_run_id> \
  --set "Smoke Tests" \
  --only-failed --verbose \
  --path ./MySolution/MyFlow --output json
```

## Workflow and references

| Need | Read |
| --- | --- |
| Any `uip maestro flow eval` syntax, flags, defaults, or output codes | [commands-reference.md](commands-reference.md) |
| Evaluator types, custom prompts, or evaluator JSON | [evaluators-guide.md](evaluators-guide.md) |
| Eval sets, data points, `--inputs`/`--expected`/`--criteria`, or attachments | [eval-sets-guide.md](eval-sets-guide.md) |
| Simulations | [eval-sets-guide.md — Simulations](eval-sets-guide.md#simulations-on-data-points) + [commands-reference.md — Simulations](commands-reference.md#simulations) |
| Start, poll, inspect, export, list, or compare runs | [running-guide.md](running-guide.md) |
<!--skill-flavor:upload-safety-workflow-row:start-->
| Decide whether to call `uip solution upload` (almost always: don't auto-run; ask first) | [upload-safety.md](upload-safety.md) |
<!--skill-flavor:upload-safety-workflow-row:end-->

### Common tasks

- **Add an evaluator:** [evaluators-guide.md](evaluators-guide.md) + [commands-reference.md — Evaluators](commands-reference.md#evaluators)
- **Pick an evaluator type:** [evaluators-guide.md — When to Pick Each Type](evaluators-guide.md#when-to-pick-each-type)
- **Create an eval set and pin an entry point:** [eval-sets-guide.md — Eval Set Lifecycle](eval-sets-guide.md#eval-set-lifecycle)
- **Add a data point with file attachments:** [eval-sets-guide.md — `--input-file`](eval-sets-guide.md#--input-file-keypath)
- **Set trajectory criteria:** [eval-sets-guide.md — `--criteria`](eval-sets-guide.md#--criteria)
- **Start a run:** [running-guide.md — Start a Run](running-guide.md#start-a-run)
- **Poll without `--wait`:** [running-guide.md — Check Status](running-guide.md#check-status)
- **Inspect failed points:** [running-guide.md — Detailed Results](running-guide.md#detailed-results) (`--only-failed --verbose`)
- **Compare runs:** [running-guide.md — Compare Two Runs](running-guide.md#compare-two-runs)
<!--skill-flavor:upload-safety-task-row:start-->
- **Decide whether to call `uip solution upload`:** [upload-safety.md](upload-safety.md)
<!--skill-flavor:upload-safety-task-row:end-->
- **Diagnose a failed eval:** [running-guide.md — Failure Detection](running-guide.md#failure-detection); for flow-level faults [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md)

## Anti-patterns

<!--skill-flavor:upload-safety-antipattern:start-->
- **Don't auto-run `uip solution upload`.** Even when an eval run errors with "solution not found in Studio Web", stop and ask the user — see [upload-safety.md](upload-safety.md). The local project may be ahead of, or diverged from, Studio Web.
<!--skill-flavor:upload-safety-antipattern:end-->
- **Don't hand-write `evaluatorRefs` unless repairing an eval set.** Prefer default all-evaluators behavior so the CLI writes generated file refs, or pass generated evaluator ids/file refs explicitly. Never pass evaluator display names to `--evaluators`.
- **Don't pass `--type` in PascalCase.** Use only `exact-match`, `json-similarity`, `contains`, `llm-judge-output`, `llm-judge-strict-json`, `llm-judge-trajectory`, or `llm-judge-trajectory-simulation`.
- **Don't depend on a specific `--wait` polling cadence.** Treat `--wait` as a black-box block; for precise progress, omit it and call `eval run status` yourself.
- **Don't compare runs from different eval sets.** `eval run compare` aligns by data-point name within the set; cross-set deltas are meaningless.
- **Don't omit `--model` on LLM-judge evaluators.** The cloud worker fail-fasts before calling the LLM gateway.
- **Don't run evals during `flow debug`.** `debug` is a separate Studio Web session; evals run against the deployed/published solution. Mixing them produces confusing run IDs.

## Completion Output

After a run completes, report:

1. **Eval set run ID** and aggregate score (from `run status`)
2. **Failed data points** (from `run results --only-failed --verbose`)
3. **Comparison delta** vs the previous run (`run compare`) if one exists
<!--skill-flavor:upload-safety-next-step:start-->
4. **Suggested next step** — fix the agent/flow, re-run, or accept the result. Do NOT suggest `uip solution upload` unless the user has explicitly asked to publish edits.
<!--skill-flavor:upload-safety-next-step:end-->

## References

### Evaluate-scoped

- [commands-reference.md](commands-reference.md) — every `uip maestro flow eval` subcommand, flags, defaults, output `Code` enum
- [evaluators-guide.md](evaluators-guide.md) — 7 evaluator types mapped to internal `uipath-*` IDs, JSON shapes, template variables
- [eval-sets-guide.md](eval-sets-guide.md) — eval set + data point CRUD, `--inputs`/`--expected`/`--criteria`/`--input-file`/`--search-text`, simulations
- [running-guide.md](running-guide.md) — run start/status/results/list/compare, JMESPath `--output-filter`, failure detection
<!--skill-flavor:upload-safety-reference-entry:start-->
- [upload-safety.md](upload-safety.md) — the `solution upload` rule
<!--skill-flavor:upload-safety-reference-entry:end-->

### Cross-capability (shared)

- [shared/cli-commands.md](../shared/cli-commands.md) — flat CLI lookup including `eval` subcommands
- [shared/cli-conventions.md](../shared/cli-conventions.md) — login states, `--output json`, JSON output shape