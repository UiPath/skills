# Scheduled Trigger

*Exact signatures, fields, and defaults: `scheduled()`.*

A scheduled trigger asks the platform scheduler to start a Flow repeatedly.

Signature: `.trigger(scheduled({ every: string }))`.

```ts
export default flow('nightly')
  .trigger(scheduled({ every: 'R/P1D' }))
  .step('rollup', script({ code: 'return { ok: true };' }))
  .build();
```

## At a glance

A platform timer starts the flow on a recurring interval.

Signature: `.trigger(scheduled({ every: string }))`. `every` takes an ISO-8601
repeating interval or a Quartz cron expression (e.g. `'0 0 2 * * ?'`).

Prefer self-contained variables because there may be no caller supplying inputs.

## Authoring judgment

A timer usually has no caller, so prefer `.var(...)` defaults or tenant-backed
steps over required caller inputs unless the deployment supplies configured
values. Pick the interval from the business requirement rather than from what
is convenient to test.

`every` is the trigger's only field: there is no time-zone setting. When the
requirement ties the run to local hours, state that time zone in the final
response.

A cron expression taken from another scheduler is usually Unix cron: five
fields (some schedulers allow a leading seconds field), Sunday as 0 or 7.
Rewrite it in Quartz before passing it to `every`: add a seconds field in front
when it has none, write `?` in day-of-month when day-of-week is given
(Quartz takes only one of the two), and write weekdays as names (`MON-FRI`),
since Quartz numbers them 1–7 from Sunday ([Quartz CronTrigger
tutorial](https://www.quartz-scheduler.org/documentation/quartz-2.3.0/tutorials/crontrigger.html)).
`30 9 * * 1-5` becomes `0 30 9 ? * MON-FRI`. `check` and `validate` refuse the
five-field form, but neither refuses a missing `?`; only the deploy does, with
`[1600] … Invalid cron expression syntax`, and installs nothing.

## Evidence boundary

Local execution starts the graph directly. It proves the scheduled node was
emitted with the authored interval and that the downstream graph runs; it does
not prove the platform scheduler fired. The scheduling claim requires a
deployed run observed at the requested cadence.

`every` is an ISO-8601 repeating interval (`R/PT30M`, `R/PT1H`, `R/P1W`) or a
Quartz cron expression (`0 0 2 * * ?`, `0 30 9 ? * MON-FRI`). Cron and a
single-unit interval (`R/PT45M`, `R/P1D`) are written at the trigger's 1.2
definition, in `timerValue`. 1.2 takes one unit within its range, so an interval
such as `R/PT90M` or `R/P1DT12H` is written at 1.1. Pinning 1.2 with one is a
compile error (`SCHEDULE_INTERVAL_VERSION`), and so is pinning 1.1 with cron. A
decompiled node keeps its version.
