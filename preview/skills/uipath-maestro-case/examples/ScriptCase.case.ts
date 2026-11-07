/**
 * A Case script task authored as a TypeScript function (`.script(fn)`): the
 * body doubles a case variable and returns it with the instance id, and
 * `.outputs()` maps the whole return to the `scriptResult` variable. The function is
 * lowered to the body at compile, its parameters renamed, in order, to `vars` and
 * `metadata`.
 */
import { casePlan, rule } from '@uipath/maestro-builder-sdk/case';

function doubled(vars: { amount: number }, metadata: { InstanceId: string }) {
  const total = vars.amount * 2;
  return { total, note: metadata.InstanceId };
}

export default casePlan('ScriptCase')
  .name('ScriptCase')
  .identifier('SCR')
  .var('amount', 'double', '21')
  .var('scriptResult', 'object', '{}')
  .stage('Work', (s) =>
    s
      .required()
      .entryWhen(rule('case-entered'))
      .exitWhen(rule('required-tasks-completed'), { marksStageComplete: true })
      .task('Double', (t) =>
        t
          .script(doubled)
          .outputs({ scriptResult: '=result.response' })
          .required()
          .entryWhen(rule('current-stage-entered')),
      ),
  )
  .completeWhen(rule('required-stages-completed'))
  .build();
