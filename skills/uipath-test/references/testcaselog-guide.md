# Test case logs (`uip tm testcaselog`)

One test case log is one test case's outcome inside one execution. This is the
surface for reading them, reading their evidence, correcting a result, and
giving a failure an owner.

Every verb is project-scoped — pass `--project-key <PROJECT_KEY>` (or
`--project-id <UUID>`) — and takes `--output json` per Critical Rule 2.

## Reading

- `uip tm testcaselog list --project-key <PROJECT_KEY>` — every log the filter
  matches across the project. Filters: `--results`, `--statuses`, `--labels`,
  `--assignees`, `--search`, `--sort-by`, `--limit` / `--offset`.
- `uip tm testcaselog get --project-key <PROJECT_KEY> --test-case-log-id <UUID>`
  — one log; add `--include-assertions` to get its assertions in the same call.
- `uip tm testcaselog latest --project-key <PROJECT_KEY> --test-case-ids <UUID...>`
  — the newest log for each of several test cases, in one call.

**There is no date or execution filter on `list`.** To narrow by run use
`uip tm executions testcaselogs list --execution-id <UUID>`; to narrow by
period use `uip tm executions list-filtered --execution-finished-interval`.

**`--search` is a prefix match** on the test case name or objKey: `checkout`
does not match `Guest checkout flow`.

**`--labels` is an any-match on whole names**, not all-of and not a prefix.

**`latest` and `assign` take at most 100 ids per call.** Split larger sets.

**`--results Restricted` is applied after the query**, not by the server, so a
row asked for as `Passed` can come back reading `Restricted`.

**`--statuses` is asymmetric:** the accepted input tokens are lowercase, and
rows come back with `Status` in PascalCase (`Finished`, `Running`).

## `Result` vs `OriginalResult`

`Result` is what the log reports **now**. `OriginalResult` is what the run
recorded. **The two differing is exactly what "this result was overridden"
means** — there is no separate flag to read. Never report `Result` as the
outcome of a run without checking `OriginalResult` first.

`--include-assertions` returns nothing when `Result` is `Restricted`: the
server drops assertions for a caller not entitled to the result.

## Evidence

- `uip tm testcaselog list-assertions --project-key <PROJECT_KEY> --test-case-log-id <UUID>`
  — the structured assertion rows.
- `uip tm testcaselog assertions --project-key <PROJECT_KEY> --test-case-log-id <UUID>`
  — the same assertions rendered as markdown, ready to paste into a defect.
- `uip tm testcaselog robot-logs --project-key <PROJECT_KEY> --test-case-log-id <UUID>`
  — an expiring download link and its size, or with `--output-file <PATH>` the
  downloaded file.

A log with no robot logs is **not an error**: both forms answer
`Action: "NoLogs"` and write nothing. Do not retry it. The returned link is a
Test Manager API path, so fetching it yourself needs a bearer token carrying
the `TM.Attachments` scope, which the command itself does not require.

## Overriding a result

```
uip tm testcaselog override set --project-key <KEY> --test-case-log-id <UUID> \
  --result <Passed|Failed|...> --reason "<why>"
```

`--reason` is required. The output carries the override id that `update` and
`clear` need.

- `override get --test-case-log-id <UUID>` — read it. **A log with no override
  is a 404**, not an empty result. Treat that as "not overridden".
- `override update --test-case-log-id <UUID> --override-id <UUID> --result … --reason …`
  — replace an existing one; both fields are required.
- `override clear --test-case-log-id <UUID> --override-id <UUID>` — remove it,
  so the log reports what the run recorded again.

Three things that bite:

1. **A log carries at most one override.** A second `set` fails on a unique
   constraint. Use `override update` to change one that already exists.
2. **`set` is not atomic.** The log's reported result is written *before* the
   override row, so a failed second `set` can still have moved the result. If a
   `set` errors, re-read the log before deciding what happened.
3. **An override is destroyed** whenever the log is finished, re-imported, or
   updated by an Orchestrator job event. It is a correction on a settled run,
   not a durable property — re-running the test wipes it.

## Assigning an owner

```
uip tm testcaselog assign --project-key <KEY> --test-case-log-ids <UUID...> \
  --assignee-id <IDENTITY_PROVIDER_UUID> [--due-date 2026-10-01]
```

**`--assignee-id` is an identity-provider UUID, never a name or an email.**
Get one from `uip tm user get` (`IdentityProviderId`, your own) or
`uip tm project owners list` (`Identifier`, a project owner). Do not guess it.

Two behaviours to plan around:

- **Assignment is stored per test case per execution, not per log.** Passing
  one variation's log id reassigns every variation and run of that test case in
  that execution.
- **An id that resolves to nothing is dropped silently.** `Assigned` means the
  request was accepted, not that every id was written — re-read a log to
  confirm.

`uip tm testcaselog delete-defect --project-key <KEY> --test-case-log-id <UUID> --defect-id <UUID>`
unlinks a defect from a log. It refuses if the log does not carry that defect.

## Recording a manual result

`testcaselog start` opens a log on an execution and `finish` closes it:

```
uip tm testcaselog start  --project-key <KEY> --execution-id <UUID> --test-case-id <UUID>
uip tm testcaselog finish --project-key <KEY> --execution-id <UUID> --test-case-id <UUID> \
  --result <None|Passed|Failed|Restricted> --has-error <true|false> \
  --executed-by <EMAIL>
```

`finish` requires **all three** of `--result`, `--has-error` and
`--executed-by`, and `--executed-by` is an **email address**, not a user id or
an identity-provider UUID — unlike `assign --assignee-id`, which is the UUID.
Getting that one wrong is a `ValidationError` and exit 3, not a 400.

Optionally `--run-id`, `--detail-link`, `--is-post-condition-met`,
`--step-logs` / `--step-logs-file` (mutually exclusive). Remember that
`finish` destroys any override on the log.

## Permissions

Reads need test-case-log read; overriding and assigning need the matching write
permissions. Check with
`uip tm project permissions get --project-key <PROJECT_KEY>`.
