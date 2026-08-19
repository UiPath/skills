/**
 * IntakeBinding — a Case plan whose inputs are BOUND to its triggers. Two
 * triggers (a manual entry point + an hourly timer); each In-arg names the
 * trigger it arrives with via `.input(shape, { from })`.
 *
 *   caseId    ← the manual trigger (supplied when a person starts the case)
 *   batchId   ← the manual trigger (a second arg on the same trigger)
 *   sweepId   ← the timer trigger (supplied when the schedule fires)
 *
 * A bound In-arg emits a formal slot (`variables.inputs[]`, `elementId` = the
 * trigger), a companion (`variables.inputOutputs[]`, readable as `=vars.<name>`),
 * and a bridge on the trigger node's `data.uipath.outputs[]` that copies the slot
 * into the companion at fire. Binding to the manual trigger gives it a
 * `data.uipath = { outputs }` with NO `serviceType` (still manual). No bindings or
 * connector library — compile with `uip maestro case compile` and check source
 * with `uip maestro case check`.
 */
import { casePlan, rule, manualTrigger, timerTrigger } from '@uipath/flow-sdk/case';

const manual = manualTrigger({ name: 'Manual start' });
const hourly = timerTrigger({ every: 'R/PT1H', name: 'Hourly sweep' });

export default casePlan('intake-binding')
  .name('IntakeBinding')
  .identifier('IB')
  .trigger(manual)
  .trigger(hourly)
  .input({ caseId: 'string' }, { from: manual })
  .input({ batchId: 'string' }, { from: manual })
  .input({ sweepId: 'string' }, { from: hourly })
  .stage('Handle', (s) =>
    s
      .required()
      .entryWhen(rule('case-entered'))
      .exitWhen(rule('required-tasks-completed'), { marksStageComplete: true })
      .task('Process', (t) =>
        t.rpa('Handler', { folder: 'Shared' }).required().entryWhen(rule('current-stage-entered')),
      ),
  )
  .completeWhen(rule('required-stages-completed'))
  .build();
