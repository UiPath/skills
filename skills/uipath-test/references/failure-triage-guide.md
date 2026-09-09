# Failure Triage — from a red run to a root cause

Diagnose workflow for a Test Manager execution that failed. Answers three questions in order: **what failed**, **why it failed**, **is it a real defect or a flaky test**.

All commands take `--output json` (Critical Rule #3). Every `list` below is paginated — `--limit` / `--offset`.

## When to use this

- A test set run came back red and you need the cause, not the count
- Someone asks "is this test actually broken, or just flaky?"
- A release decision needs evidence attached, not a summary
- CI reported a failure and you have only the execution ID

For a persona-tailored written report, use [test-result-report-guide.md](test-result-report-guide.md) instead — that answers "what do I tell stakeholders", this answers "what is wrong".

## The triage ladder

Walk down. Each rung narrows the blast radius; stop at the rung that answers the question.

| Rung | Command | Answers |
|---|---|---|
| 1. Execution totals | `uip tm executions get-stats --execution-id <UUID> --project-key <KEY>` | How bad? Pass/fail/skip counts as the run reports them |
| 2. Failed cases only | `uip tm executions testcaselogs list --execution-id <UUID> --project-key <KEY> --only-failed` | Which test cases failed |
| 3. Failed assertion | `uip tm testcaselog list-assertions --project-key <KEY> --test-case-log-id <UUID>` | Which assertion inside the case broke |
| 4. Step detail | `uip tm teststeplog list --project-key <KEY> --test-case-log-id <UUID>` | Which step it broke on |
| 5. Evidence | `uip tm attachment download --execution-id <UUID> --only-failed --result-path <DIR>` | Screenshots / logs for the failures |

`--only-failed` on rung 2 is the difference between reading 4 rows and reading 400. Use it — do not pull every log and filter client-side (Critical Rule #9).

IDs chain downward: `testcaselogs list` returns the `test-case-log-id` that rungs 3 and 4 need. Do not guess it.

## Real defect, or flaky test?

A single red run cannot tell you. Ask the test case's own history:

```bash
uip tm testcases list-result-history --project-key <KEY> --test-case-id <UUID> --only-failed --output json
```

Read the pattern:

| History | Read |
|---|---|
| Fails every run since a known date | Real regression — bisect to what changed at that date |
| Fails intermittently, same assertion | Flaky test — environment, timing, or test data, not product code |
| Fails intermittently, different assertions | Unstable environment or shared-state contention between tests |
| First failure ever | Either a new regression or a new flake — one data point is not a pattern; re-run before concluding |

`--only-failed` here narrows to the failures; drop it when you need the pass/fail *ratio* rather than the failure list.

## Narrowing across many executions

`executions list` covers the common case. Reach for `list-filtered` only when you need what `list` cannot express:

```bash
uip tm executions list-filtered --project-key <KEY> \
  --status finished --execution-type automated \
  --labels <Label1> <Label2> --sort-by <expr> --output json
```

Use it for label filtering, `--updated-by <userId>`, multi-execution lookup via `--test-execution-ids`, or custom ordering. Labels and execution IDs are **space-separated** variadics.

`executions testcaselogs list` additionally accepts `--results <results...>`, `--statuses <statuses...>` and `--duration-period <period>` (e.g. `last7Days`) — prefer these over post-filtering a wide list.

## Evidence capture

```bash
uip tm attachment download --execution-id <UUID> --only-failed --result-path ./evidence --output json
```

`--test-case-name <name>` narrows to one case (case-insensitive). `--test-set-key` can stand in for `--project-key` when you only have the set. Attach what you downloaded to the defect rather than describing it.

## Symptom → first command

| Symptom | Start here |
|---|---|
| "The nightly run failed" | Rung 1, then rung 2 |
| "This one test keeps breaking" | `list-result-history --only-failed` |
| "Which step does it die on?" | Rung 2 → rung 4 |
| "Prove it to me" | Rung 5 |
| "Did anyone re-run it?" | `executions list-filtered --updated-by` |
| "Is the whole suite degrading?" | `executions list-filtered --status finished --sort-by`, compare `get-stats` across runs |

## Anti-patterns

- **Do NOT report a count as a diagnosis.** `get-stats` says how many failed, never why. Descend the ladder.
- **Do NOT call one red run a regression.** Check `list-result-history` first; a flaky test misreported as a defect burns a developer's day.
- **Do NOT list every test case log and filter locally.** `--only-failed`, `--results`, `--statuses` and `--duration-period` exist; client-side filtering misses paginated rows entirely.
- **Do NOT guess a `--test-case-log-id`.** It comes from `testcaselogs list`; a fabricated UUID returns an error the retry cap will burn through (Critical Rule #4).
- **Do NOT skip evidence on a defect you are filing.** `attachment download --only-failed` is one call.
