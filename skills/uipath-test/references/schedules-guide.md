# Test set schedules (`uip tm schedules`)

A test set can run on a cadence. `uip tm schedules` is the whole surface:
`create`, `update`, `list`, `next-runs`, `enable`, `disable`, `delete`.

Everything here is project-scoped: pass `--project-key <PROJECT_KEY>` (or
`--project-id <UUID>`) to every verb, and `--output json` per Critical Rule 2.

## The cadence is not Unix cron

`--cron` takes **6 or 7 fields, starting with seconds**. A five-field Unix
expression is not a cadence Test Manager can run, and the server does not
reject it — one of its two validators only int-parses the first field, and the
other describes five parts as standard cron and returns a plausible sentence.
The bad value passes validation and then fails inside the scheduler as an
opaque 500. The CLI refuses it first, naming the flag.

Exactly one of day-of-month / day-of-week must be `?`.

| Cadence | `--cron` |
|---|---|
| Daily at 02:00 | `0 0 2 1/1 * ? *` |
| Daily at 15:30 | `0 30 15 1/1 * ? *` |
| Every 2 days at 02:00 | `0 0 2 1/2 * ? *` |
| Once, 12 Oct 2030 06:30 | `0 30 6 12 10 ? 2030` |

## `--cron-details` is required, and must be a JSON object

It is the recurrence JSON the UI sends, not a label, and it is required for
**every** recurrence type including `single`. The column is `NOT NULL` and
nothing server-side defaults it, so omitting it is a 500. It must be a JSON
object on every type, because the UI reads the field back with an unguarded
`JSON.parse` to rehydrate its recurrence editor — a scalar or an empty string
stores a schedule nobody can open in the product. Over 255 characters is also
a 500. The CLI refuses all three before the request.

| Cadence | `--cron-details` |
|---|---|
| Daily at 02:00 | `{"type":4,"daily":{"atHour":2,"atMinute":0,"frequencyIndays":1}}` |
| One-off | `{"type":1}` |

With `--recurrence recurrence` (the default) and `type` 4, the server requires
`daily.frequencyIndays` to be `1`.

## Times are wall-clock, not instants

`--start-time` and `--disable-time` are `YYYY-MM-DDTHH:mm` — **no seconds, no
offset, no `Z`**. The server parses that format exactly, so the ISO-looking
`2030-01-01T00:00:00Z` is a guaranteed refusal. The moment comes from
`--timezone` (an IANA name such as `Europe/Bucharest`).

`create` refuses a start time in the past once `--timezone` is applied, and
refuses `--disable-time` before `--start-time`. Equal is a valid window.

## `update` replaces, it does not patch

The body is the whole schedule. Anything omitted reverts to its default, so
pass every flag you want kept. There is **no get by id** — `schedules list` is
the only read, so it is where you recover the current values before an update.

One exception: the enabled state is preserved server-side whatever the request
carries, so `update` cannot switch a schedule on or off. Use `enable` /
`disable`.

## `list` — two things the filter cannot do

`uip tm schedules list --project-key <PROJECT_KEY>` takes `--enabled` /
`--disabled` (mutually exclusive), `--recurrence`, `--search`, `--sort-by`,
`--limit` / `--offset`.

- **There is no test set filter.** The request has no field for it, so
  `--test-set-id` narrows the returned page client-side. Widen `--limit` if a
  match seems missing.
- **`--search` is a prefix match** on the name **or** the description, not a
  substring: `nightly` does not match `Run nightly regression`.

## `next-runs` — pass schedule ids, never cache the other id

`uip tm schedules next-runs --project-key <PROJECT_KEY> --schedule-ids <UUID...>`

Pass the ids `schedules list` prints. The endpoint underneath is keyed by
`BackgroundTaskScheduleId`, a different GUID, and answers `200` with an empty
list if handed schedule ids — a silent wrong answer rather than an error. The
CLI resolves each id through the list so you never have to know that.

Do not hand-assemble that call from a stored `BackgroundTaskScheduleId`: the
list is the only thing that pairs the two id spaces, and getting it wrong looks
like "no runs scheduled" rather than like a mistake.

Each output row carries `ScheduleId`, `BackgroundTaskScheduleId`, `NextRun` and
`Outcome`:

| `Outcome` | Meaning |
|---|---|
| `Scheduled` | `NextRun` holds the next fire time |
| `NoNextRun` | The schedule exists but has no queued run |
| `NotFound` | No schedule in this project has that id |

Rows come back in the order asked for, and an unresolved id stays in the list,
so the output is safe to zip against the request. At most 100 ids per call.

## `enable`, `disable`, `delete` — all-or-nothing on a batch

Each takes `--schedule-ids <UUID...>`, or `--all` for every schedule in the
project. `delete` always needs `--yes`; `--all` needs `--yes` on every verb.

With several ids the request is a single bulk call. **It answers `204` with no
body**, so the reply carries one verdict — `ScheduleIds`, `Count`, `Action` —
and not a per-id status; there is no per-id detail to report.

What an unknown id does to the rest of the batch is **not guaranteed**: the
server has been observed both refusing the whole call and accepting it. So
after a bulk `enable`, `disable` or `delete` over ids you are not certain of,
**re-read with `schedules list`** rather than trusting the verdict to mean
every id moved.

Repeated ids are dropped before the request. Sending the same id twice would
otherwise fail the batch even though it exists, because the server counts the
ids against the rows it loads.

Switching a schedule to the state it is already in is a no-op success, not an
error.

An empty `--all` reports `Action: NoSchedules` and calls nothing.

## Permissions

Writes need the Test Manager automated-execution permission. `list` needs
test-set read. Check with
`uip tm project permissions get --project-key <PROJECT_KEY>`.

## What this does not tell you

Whether a schedule actually fires, and what it produces. That is Orchestrator
dispatch. Read the resulting runs with `uip tm executions list`.
