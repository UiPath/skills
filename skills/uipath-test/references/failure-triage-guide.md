# Failure Triage — from a red run to a root cause

Diagnose in order: **what failed**, **why**, and **defect or flake**. Run every command with `--output json` (Critical Rule #2), and paginate every `list` with `--limit` / `--offset`.

## When to use this

Use for a red test set run, a broken or flaky test question, a release decision needing evidence, or a CI failure with only the execution ID. For a persona-tailored stakeholder report, use [test-result-report-guide.md](test-result-report-guide.md); this guide diagnoses failures.

## Triage ladder

Run rungs in order and stop when one answers the question.

| Rung | Command | Answers |
|---|---|---|
| 1. Execution totals | `uip tm executions get-stats --execution-id <UUID> --project-key <KEY>` | Pass/fail/skip counts as reported |
| 2. Failed cases | `uip tm executions testcaselogs list --execution-id <UUID> --project-key <KEY> --only-failed` | Which cases failed |
| 3. Failed assertion | `uip tm testcaselog list-assertions --project-key <KEY> --test-case-log-id <UUID>` | Which assertion broke |
| 4. Step detail | `uip tm teststeplog list --project-key <KEY> --test-case-log-id <UUID>` | Which step broke |
| 5. Evidence | `uip tm attachment download --execution-id <UUID> --only-failed --result-path <DIR>` | Screenshots/logs |

At rung 2, use `--only-failed` instead of retrieving all logs and filtering client-side (Critical Rule #8). Get the `test-case-log-id` for rungs 3–4 from `testcaselogs list`; do not guess it.

## Defect or flaky test?

One red run is not enough. Check failure history:

```bash
uip tm testcases list-result-history --project-key <KEY> --test-case-id <UUID> --only-failed --output json
```

| History | Interpretation |
|---|---|
| Fails every run since a known date | Real regression; bisect what changed then |
| Intermittently fails at the same assertion | Flaky test: environment, timing, or test data, not product code |
| Intermittently fails at different assertions | Unstable environment or shared-state contention between tests |
| First failure ever | Could be a new regression or flake; one data point is not a pattern, so re-run before concluding |

Keep `--only-failed` to narrow to failures; drop it when you need the pass/fail *ratio*.

## Narrowing across executions

Use `executions list` for common queries; use `list-filtered` only when `list` cannot express the query:

```bash
uip tm executions list-filtered --project-key <KEY> \
  --status finished --execution-type automated \
  --labels <Label1> <Label2> --sort-by <expr> --output json
```

Use `list-filtered` for label filtering, `--updated-by <userId>`, multi-execution lookup via `--test-execution-ids`, or custom ordering. Labels and execution IDs are **space-separated** variadics. `executions testcaselogs list` also accepts `--results <results...>`, `--statuses <statuses...>`, and `--duration-period <period>` (e.g. `last7Days`); prefer these over post-filtering a wide list.

## Evidence capture

Run:

```bash
uip tm attachment download --execution-id <UUID> --only-failed --result-path ./evidence --output json
```

Use `--test-case-name <name>` to narrow to one case (case-insensitive), or `--test-set-key` instead of `--project-key` if you only have the set. Attach downloaded evidence to the defect; do not merely describe it.

## Symptom → first command

| Symptom | Start here |
|---|---|
| “The nightly run failed” | Rung 1, then rung 2 |
| “This one test keeps breaking” | `list-result-history --only-failed` |
| “Which step does it die on?” | Rung 2 → rung 4 |
| “Prove it to me” | Rung 5 |
| “Did anyone re-run it?” | `executions list-filtered --updated-by` |
| “Is the whole suite degrading?” | `executions list-filtered --status finished --sort-by`; compare `get-stats` across runs |

## Anti-patterns

- **Do NOT report a count as a diagnosis.** `get-stats` gives counts, not causes; descend the ladder.
- **Do NOT call one red run a regression.** Check `list-result-history` first; misreporting a flaky test as a defect wastes a developer’s day.
- **Do NOT list every test case log and filter locally.** Use `--only-failed`, `--results`, `--statuses`, and `--duration-period`; client-side filtering misses paginated rows.
- **Do NOT guess a `--test-case-log-id`.** Get it from `testcaselogs list`; a fabricated UUID returns an error the retry cap will burn through (Critical Rule #3).
- **Do NOT skip evidence on a defect you are filing.** Run `attachment download --only-failed`; it is one call.