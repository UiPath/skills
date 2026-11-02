# Test set schedules (`uip tm schedules`)

A test set can run on a cadence. The surface is `create`, `update`, `list`,
`next-runs`, `enable`, `disable`, `delete` — run each with `--help` for its
flags. Everything is project-scoped (`--project-key`/`--project-id`) and takes
`--output json` (Critical Rule 2). You already know how to write cron; this
guide covers only what `--help` cannot and what Unix-cron instinct gets wrong.

## The cron is Quartz, not Unix

`--cron` is **6 or 7 fields starting with SECONDS**, and exactly one of
day-of-month / day-of-week must be `?` (the other carries the value). A
five-field Unix expression is not a cadence Test Manager can run: the server
accepts it (its validators only int-parse the first field) and then fails
inside the scheduler as an opaque 500, so the CLI refuses it first. So a daily
run is `… 1/1 * ? *` and a weekly run puts the days in day-of-week with `?` in
day-of-month (e.g. `0 0 9 ? * MON,THU *`).

## `--cron-details` is a required JSON object, matched to the cron

Not a label — a JSON **object** ≤255 chars, required for **every** recurrence
type (the column is `NOT NULL`; omitting it is a 500). The UI rehydrates it with
an unguarded `JSON.parse`, so a scalar or empty string stores a schedule nobody
can open in the product. The object's `type` enum must agree with the cron:

- **`type` 1** — one-off: `{"type":1}`.
- **`type` 3** — weekly: `weekly.days` takes full English day names
  (`["Monday","Thursday"]`), and those same days appear in the cron's
  day-of-week field as 3-letter codes.
- **`type` 4** — daily: `daily.frequencyIndays` must be `1`
  (`{"type":4,"daily":{"atHour":2,"atMinute":0,"frequencyIndays":1}}`).

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
