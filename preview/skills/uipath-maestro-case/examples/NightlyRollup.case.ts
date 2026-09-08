/**
 * NightlyRollup — a Case plan started by MULTIPLE triggers: a manual entry point
 * plus two schedules. All three fire the single Run stage via its `case-entered`
 * entry (there are no edges — the trigger nodes just subscribe the start signal).
 *
 *   manual                              — someone kicks it off on demand.
 *   timer R/PT1H                        — every hour, unbounded.
 *   timer R5/2026-04-26T09:00:00Z/P1D   — 5 times, daily at 09:00 UTC from that date.
 *
 * A manual trigger emits a `case-management:Trigger` node with no `data.uipath`; a
 * timer adds `data.uipath = { serviceType:'Intsvc.TimerTrigger', timerType:
 * 'timeCycle', timeCycle }`. Compile also syncs the sibling `entry-points.json`.
 * No bindings or connector library — compile with `uip maestro case compile`,
 * check source with `uip maestro case check`, then run `uip maestro case validate`.
 */
import { casePlan, rule, manualTrigger, timerTrigger } from '@uipath/flow-sdk/case';

export default casePlan('nightly-rollup')
  .name('NightlyRollup')
  .identifier('NR')
  .trigger(manualTrigger({ name: 'Manual start' }))
  .trigger(timerTrigger({ every: 'R/PT1H', name: 'Hourly' }))
  .trigger(timerTrigger({ every: 'R5/2026-04-26T09:00:00.000Z/P1D', name: 'Daily 09:00 (5×)' }))
  .stage('Run', (s) =>
    s
      .required()
      .entryWhen(rule('case-entered'))
      .exitWhen(rule('required-tasks-completed'), { marksStageComplete: true })
      .task('Roll up', (t) =>
        t.rpa('RollupWorker', { folder: 'Shared' }).required().entryWhen(rule('current-stage-entered')),
      ),
  )
  .completeWhen(rule('required-stages-completed'))
  .build();
