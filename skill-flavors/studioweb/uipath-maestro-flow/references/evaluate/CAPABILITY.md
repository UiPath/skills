<!--skill-flavor:sw-eval-intro:start-->
Capability index for `uip maestro flow eval` — evaluator CRUD (7 types), eval set CRUD with entry-point pinning, data point management with file attachments, and run start/status/results/list/compare against the open solution. Local CRUD is offline and writes under `/solution/<Project>/evals/` (a fresh project has no `evals/` folder; the CLI creates it on first use, and the host adds one itself after the first debug); runs require `uip login`. `eval run *` works from the Studio Web shell only when both ids are passed explicitly (`--solution-id <CurrentSolution.SolutionId> --project-id <CurrentProject.ProjectId>`; there is no `.uipx`/`SolutionStorage.json` to resolve them from) and it can hang on first use: call it with `timeoutSeconds: 120`, never with `--wait`, and if the call times out (exit 124) hand the run to the user via the Studio Web Evaluations panel instead of retrying in a loop.
<!--skill-flavor:sw-eval-intro:end-->

<!--skill-flavor:sw-eval-orientation:start-->
> **Where you came from / where to go next.** Evaluate follows Author (save the `.flow` → validate → evaluate it) and feeds back into Author (failing eval → fix the `.flow` → save + validate → re-evaluate). Build/edit lives in [author/CAPABILITY.md](../author/CAPABILITY.md); publish and run management live in [operate/CAPABILITY.md](../operate/CAPABILITY.md); fault triage on a debug or process run lives in [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md).
<!--skill-flavor:sw-eval-orientation:end-->

<!--skill-flavor:sw-eval-when-to-use:start-->
- Start an eval run on the open solution (ids from the context), poll its status, fetch detailed results — or hand the run to the user's Evaluations panel when the shell call times out
<!--skill-flavor:sw-eval-when-to-use:end-->

<!--skill-flavor:sw-eval-cli-availability:start-->
1. **Flow eval ships in Studio Web.** `uip maestro flow eval` is part of the host's `uip` bundle — never probe for it with `--help`, `--version`, or by searching packages. If an eval command is rejected as unknown, report it as a host capability gap and stop.
<!--skill-flavor:sw-eval-cli-availability:end-->

<!--skill-flavor:upload-safety-critical-rule:start-->
2. **Studio Web owns the solution.** The eval run targets the open solution — there is nothing to upload, download, or register first. Never try `uip solution upload`/`download` to satisfy a run prerequisite; the host refuses them.
<!--skill-flavor:upload-safety-critical-rule:end-->

<!--skill-flavor:sw-eval-path-login-rules:start-->
3. **Always pass `--path /solution/<Project>`.** Every eval command needs the Flow project directory (`CurrentProject.AbsolutePath`). The shell starts in `/solution`, which is the solution root and not a project — never use `--path .` or `--path /solution`.
4. **Local CRUD does not require login.** `add`, `remove`, `list` (data points / eval sets / evaluators / simulations) edit JSON under `/solution/<Project>/evals/`. Only `uip maestro flow eval run *` requires `uip login`, plus `--solution-id <CurrentSolution.SolutionId> --project-id <CurrentProject.ProjectId>` from the context.
<!--skill-flavor:sw-eval-path-login-rules:end-->

<!--skill-flavor:sw-eval-variable-add-rule:start-->
6. **Declare input variables before adding data points with `--inputs`.** `eval add` validates input keys against the Flow's declared input variables and fails fast on unknown keys. Add missing input variables first (for example, `uip maestro flow variable add /solution/<Project>/new.flow name --direction in --type string --output json`) or change the data point input JSON to match the Flow schema.
<!--skill-flavor:sw-eval-variable-add-rule:end-->

<!--skill-flavor:sw-eval-run-rule:start-->
8. **Never `--wait`; budget 120 s per run call.** `--wait`'s 600 s default is the shell tool's maximum and past its 180 s default, so a blocked start is cut off before the run finishes. Start without `--wait`, call every `eval run *` command with `timeoutSeconds: 120`, and poll `eval run status <run_id>` for progress (the run continues server-side). `eval run *` can hang on first use: if a call times out (exit 124), do not retry in a loop — ask the user to run the evaluation from the Studio Web Evaluations panel and report the result back.
<!--skill-flavor:sw-eval-run-rule:end-->

<!--skill-flavor:sw-eval-quick-start:start-->
Standard workflow: scaffold evaluators → create eval set → add data points → run against the open solution. Every command takes `--path /solution/<Project>`; run commands also take the ids from the context (`CurrentSolution.SolutionId`, `CurrentProject.ProjectId`).

```bash
# 1. Add an evaluator (local; no login required — the CLI creates /solution/<Project>/evals/ on first use)
uip maestro flow eval evaluator add greeting-quality \
  --type llm-judge-output \
  --model gpt-4.1-2025-04-14 \
  --path /solution/<Project> --output json

# 2. Create an eval set and let the CLI attach all current evaluators
#    by generated file ref. Omit --entry-point when the flow has one
#    trigger; otherwise pass the trigger node id from new.flow.
uip maestro flow eval set add "Smoke Tests" \
  --path /solution/<Project> --output json

# 3. Add data points (test cases)
#    The `message` key must already be declared as a Flow input variable.
uip maestro flow eval add hello-test \
  --set "Smoke Tests" \
  --inputs '{"message":"hello"}' \
  --expected '{"reply":"Hello! How can I help you?"}' \
  --path /solution/<Project> --output json

# 4. Start the run — no --wait; call with timeoutSeconds: 120
uip maestro flow eval run start \
  --set "Smoke Tests" \
  --path /solution/<Project> \
  --solution-id <CurrentSolution.SolutionId> --project-id <CurrentProject.ProjectId> \
  --output json

# 5. Poll until Status is Completed or Failed (separate calls, timeoutSeconds: 120)
uip maestro flow eval run status <eval_set_run_id> \
  --set "Smoke Tests" \
  --path /solution/<Project> \
  --solution-id <CurrentSolution.SolutionId> --project-id <CurrentProject.ProjectId> \
  --output json

# 6. Inspect failures
uip maestro flow eval run results <eval_set_run_id> \
  --set "Smoke Tests" \
  --only-failed --verbose \
  --path /solution/<Project> \
  --solution-id <CurrentSolution.SolutionId> --project-id <CurrentProject.ProjectId> \
  --output json
```

If a run call times out (exit 124), hand the run to the user — "Open the Evaluations panel, run 'Smoke Tests', and paste the result here" — instead of retrying in a loop.
<!--skill-flavor:sw-eval-quick-start:end-->

<!--skill-flavor:sw-eval-workflow-table:start-->
| Start a run with the context ids, poll status, read results, compare two runs, fall back to the Evaluations panel on a time-out | [running-guide.md](running-guide.md) |
<!--skill-flavor:sw-eval-workflow-table:end-->

<!--skill-flavor:sw-eval-common-tasks-table:start-->
| **Start an eval run (ids from the context)** | [running-guide.md — Start a Run](running-guide.md#start-a-run) |
| **Poll run status (never `--wait`)** | [running-guide.md — Check Status](running-guide.md#check-status) |
| **Inspect only failed data points** | [running-guide.md — Detailed Results](running-guide.md#detailed-results) (`--only-failed --verbose`) |
| **Compare two runs side-by-side** | [running-guide.md — Compare Two Runs](running-guide.md#compare-two-runs) |
| **Look up the `eval` subcommand tree, flags, defaults, output codes** | [commands-reference.md](commands-reference.md) |
| **My eval run failed or the call timed out** | [running-guide.md — Failure Detection](running-guide.md#failure-detection); for flow-level faults [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md) |
<!--skill-flavor:sw-eval-common-tasks-table:end-->

<!--skill-flavor:upload-safety-antipattern:start-->
<!--skill-flavor:upload-safety-antipattern:end-->

<!--skill-flavor:sw-eval-antipatterns:start-->
- **Don't use `--wait` or retry a timed-out run call in a loop.** Start without `--wait`, poll `eval run status`, and on exit 124 hand the run to the user's Evaluations panel.
- **Don't compare runs from different eval sets.** `eval run compare` aligns by data-point name within the set; cross-set deltas are meaningless.
- **Don't omit `--model` on LLM-judge evaluators.** The cloud worker fail-fasts before calling the LLM gateway.
- **Don't start an eval while a `uip flow debug` is in flight.** Debug runs the saved project through the host's debug session; an eval run is a separate server-side run of the same project. Let the debug call return before `eval run start`, and keep the run ids apart when reporting.
<!--skill-flavor:sw-eval-antipatterns:end-->

<!--skill-flavor:sw-eval-completion-report:start-->
After a run completes (from `run status`, or from the result the user pasted back from the Evaluations panel), report:
<!--skill-flavor:sw-eval-completion-report:end-->

<!--skill-flavor:upload-safety-next-step:start-->
4. **Suggested next step** — fix the agent/flow, re-run, or accept the result.
<!--skill-flavor:upload-safety-next-step:end-->

<!--skill-flavor:upload-safety-reference-entry:start-->
<!--skill-flavor:upload-safety-reference-entry:end-->
