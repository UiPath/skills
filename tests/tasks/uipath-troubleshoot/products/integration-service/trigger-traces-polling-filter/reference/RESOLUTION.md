# Resolution — the mail arrived and the filter rejected every message

## Root cause

The trigger polled normally: eight cycles in the window, all `Outcome: Success`,
each one `EventsFetched: 4`. Outlook returned the mail. The trigger's filter
then rejected all of it.

The filter is `(parentFolderName == 'Inbox')`. Every message the connector
fetched has `folder: "Archive"` — a rule is moving the mail out of the Inbox
before the trigger's next poll, so nothing ever satisfies the filter.

## Evidence that settles it

Read the filter span. On a **polling** trigger the keys are:

- `result.filter` — `(parentFolderName == 'Inbox')`
- `result.matches` — empty
- `result.nonMatches` — all four message ids, `AAMkAD-0001` … `AAMkAD-0004`

`result.nonMatches` is the direct answer: it names the exact messages that were
fetched and turned away.

## What NOT to conclude

**Do not report "no filter data".** A polling trigger records none of
`DataFilters.input.filter` or `DataFilters.output.matched` — those are the
webhook span keys. Their absence means the wrong shape is being read, not that
the trigger recorded nothing. Locate the filter span by shape: it is whichever
span carries a `filter` string, with the matched records beside it.

The connection is `Enabled` and `IsConnected`, and `correlated-jobs` is
correctly empty — the trace matched nothing, so there is nothing to correlate.
Neither is the cause.

## Fix

Either stop the rule that archives the mail before the poll, or change the
trigger's filter to the folder the mail actually lands in. Quote
`result.filter` and the rejected ids to the reporter.
