# Test set schedules (`uip tm schedules`)

A test set can run on a cadence. The surface is `create`, `update`, `list`,
`next-runs`, `enable`, `disable`, `delete` — run each with `--help` for its
flags. Everything is project-scoped (`--project-key`/`--project-id`) and takes
`--output json` (Critical Rule 2). This guide covers only what `--help` cannot:
the cron/recurrence translation and the cross-call gotchas.

## The cron is not Unix cron — translate it

`--cron` is **6 or 7 fields starting with seconds**, and exactly one of
day-of-month / day-of-week must be `?`. A five-field Unix expression is not a
cadence Test Manager can run: the server accepts it (its validators only
int-parse the first field) and then fails inside the scheduler as an opaque
500, so the CLI refuses it first.

| Cadence | `--cron` |
|---|---|
| Daily at 02:00 | `0 0 2 1/1 * ? *` |
| Daily at 15:30 | `0 30 15 1/1 * ? *` |
| Every 2 days at 02:00 | `0 0 2 1/2 * ? *` |
| Weekly, Mon & Thu at 09:00 | `0 0 9 ? * MON,THU *` |
| Once, 12 Oct 2030 06:30 | `0 30 6 12 10 ? 2030` |

## `--cron-details` is a JSON object, matched to the cron

Required for **every** recurrence type (the column is `NOT NULL`; omitting it is
a 500). It must be a JSON object ≤255 chars — the UI rehydrates it with an
unguarded `JSON.parse`, so a scalar or empty string stores a schedule nobody can
open in the product.

| Cadence | `--cron-details` |
|---|---|
| Daily at 02:00 | `{"type":4,"daily":{"atHour":2,"atMinute":0,"frequencyIndays":1}}` |
| One-off | `{"type":1}` |
| Weekly (Mon & Thu) | `{"type":3,"weekly":{"atHour":9,"atMinute":0,"days":["Monday","Thursday"]}}` |

`type` 4 (daily) requires `daily.frequencyIndays` to be `1`. **Weekly is
`type` 3**: `weekly.days` takes full English day names, and the cron's
day-of-week field carries the same days as 3-letter codes (`MON,THU`) with `?`
in day-of-month.

## Times are wall-clock, not instants

`--start-time`/`--disable-time` are `YYYY-MM-DDTHH:mm` — **no seconds, no `Z`,
no offset** — read in `--timezone` (an IANA name such as `Europe/Bucharest`).
The ISO-looking `2030-01-01T00:00:00Z` is a guaranteed refusal.

## `update` replaces, it does not patch

The body is the whole schedule; anything omitted reverts to its default. There
is **no get by id**, so recover the current values with `schedules list` and
pass back every flag you want kept. `update` cannot switch a schedule on or off
— the enabled state is preserved server-side whatever the request carries, so
use `enable` / `disable`.

## `next-runs` — pass schedule ids, never the other id

Pass the ids `schedules list` prints. The endpoint underneath is keyed by
`BackgroundTaskScheduleId`, a **different GUID**, and answers `200` with an
empty list if handed schedule ids — a silent wrong answer, not an error. The CLI
resolves each id through the list, so never hand-assemble the call from a stored
`BackgroundTaskScheduleId`. `Outcome` is `Scheduled` (`NextRun` is set),
`NoNextRun` (no queued run) or `NotFound` (no schedule here has that id);
`NextRun` is a UTC instant. At most 100 ids per call.

## What this does not tell you

Whether a schedule actually fires, and what it produces — that is Orchestrator
dispatch. Read the resulting runs with `uip tm executions list`.
