# Resolution — the trigger is healthy; the filter is doing its job

## Root cause

Nothing is broken. The trigger polled every five minutes for the whole window,
every cycle returned `Outcome: Success`, and the cycles that matched an event
dispatched it and started a job.

The reporter's expectation is what is wrong: they are watching issues that the
trigger's filter excludes. The filter is `(project == 'SUP')`, and the cycles
show `EventsFetched: 2` with `EventsMatched: 1` — the second record is in
`result.nonMatches` on every cycle, rejected because its project is not `SUP`.

## Evidence that settles it

- `is trigger-traces list` — 12 traces in the window, all `Success`, six with
  `EventsMatched: 1` and `Notified: true`.
- `traces spans get` on a matching trace — the `UserFilters - 1` span carries
  `result.filter` = `(project == 'SUP')`, `result.matches` holding `ISS-4821`,
  and `result.nonMatches` holding `ISS-4820`.
- `is correlated-jobs list` — the matched event produced job `251503171` with
  `DispatchStatus: 0`.

## What NOT to conclude

The connection is `Enabled` and `IsConnected`, and `or triggers history` is
empty. Neither is evidence of anything here: a healthy connection and an empty
fire log are the normal state of a working trigger. Checking them *before*
reading the traces answers a question nobody asked and finds nothing, because
the trigger ran fine.

## Fix

Widen the trigger's filter in Integration Service, or raise the issues in the
`SUP` project. Quote the expression and the rejected record id to the reporter
rather than describing the filter in the abstract.
