# Test case logs (`uip tm testcaselog`)

One test case log is one test case's outcome inside one execution — the surface
for reading logs and their evidence, correcting a result, and giving a failure
an owner. Every verb is project-scoped (`--project-key` or `--project-id`) and
takes `--output json`. Discover flags with `--help`; only the non-obvious rules
are below.

## Reading (`list`, `get`, `latest`)

- **No date or execution filter on `list`.** Narrow by run with
  `uip tm executions testcaselogs list --execution-id`; by period with
  `uip tm executions list-filtered --execution-finished-interval`.
- **`--search` is a prefix match** on name/objKey: `checkout` misses
  `Guest checkout flow`. **`--labels` is any-match on whole names** — not
  all-of, not a prefix.
- **`latest` and `assign` take at most 100 ids per call.** Split larger sets.
- **`--statuses` is asymmetric:** input tokens lowercase, rows return `Status`
  in PascalCase (`Finished`). **`--results Restricted` is filtered
  client-side**, so a row asked as `Passed` can come back `Restricted`.
- `get --include-assertions` returns no assertions when `Result` is
  `Restricted` (the caller isn't entitled).

## `Result` vs `OriginalResult`

`Result` is what the log reports **now**; `OriginalResult` is what the run
recorded. A result is **overridden only when both are populated and they
differ** — there is no separate flag. A null/empty `OriginalResult` means the
log was **not** overridden, whatever `Result` says. Never report `Result` as a
run's outcome without this check.

## Evidence

`list-assertions` (structured rows), `render-assertions` (markdown for a
defect), and `get-robot-logs` (expiring link, or `--output-file` to save) read
a log's evidence. A log with no robot logs is **not an error** —
`get-robot-logs` answers `Action: "NoLogs"` and writes nothing; do not retry.
That link is a TM API path, so fetching it yourself needs a token with the
`TM.Attachments` scope (the command itself does not).

## Overriding a result

`override create --test-case-log-id <UUID> --result <...> --reason "<why>"` —
**both `--result` and `--reason` are required.** The output carries the override
`Id` that `update`/`delete` need. `override get` reads it (and returns a **404
when there is none — treat as "not overridden"**, not an error).

Three things that bite:

1. **A log carries at most one override.** A second `create` fails on a unique
   constraint; use `override update` instead.
2. **`create` is not atomic.** `Result` is written *before* the override row, so
   a failed `create` can still have moved it. Re-read after any `create` error.
3. **An override is destroyed** when the log is finished, re-imported, or
   touched by an Orchestrator job event — a correction on a settled run, not
   durable.

## Assigning an owner

`assign --test-case-log-ids <UUID...> --assignee-email <EMAIL>` — prefer
`--assignee-email`, which the CLI resolves to the identity-provider id. The
alternative `--assignee-id` is a **UUID, never a name or email** (from
`uip tm user get` → `IdentityProviderId`, or `project owners list` →
`Identifier`). `--due-date` is ISO `YYYY-MM-DD`; omitting it on a reassignment
clears any existing due date.

- **Assignment is stored per test case per execution, not per log.** One
  variation's log id reassigns every variation and run of that case in that
  execution.
- **An id that resolves to nothing is dropped silently.** `Assigned` means the
  request was accepted, not that every id was written — re-read to confirm.

## Recording a manual result

`start` opens a log on an execution, `finish` closes it. **`start` needs an
existing `--execution-id`** — there is no `executions create`; open one with
`uip tm testcases run ... --execution-type manual` (execution under `Data.Id`)
or `uip tm testsets run ... --execution-type manual`. A manual run already opens
each case log, so `start` returns that same log, not a duplicate.

`finish` requires **all three** of `--result`, `--has-error`, and
`--executed-by` — omit any and it fails with a `ValidationError`/exit 3 and an
**empty error message**, not a usage hint. **`--executed-by` is an email** — not a
user/IdP UUID (unlike `assign --assignee-id`); wrong type is a `ValidationError`/exit
3, not a 400. It is validated non-empty then discarded: the log records the
authenticated caller regardless, so when no executor is named pass your own login
email (`uip login status` → `Data.UserEmail`). `finish` destroys any override on the
log.

Reads need test-case-log read permission; override and assign need the matching
write permissions (`uip tm project permissions get --project-key`).
