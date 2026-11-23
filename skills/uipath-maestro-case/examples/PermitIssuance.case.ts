/**
 * PermitIssuance — task-set grouping for parallel-after-predecessor execution.
 *
 * Stage "Issuing Permit" has four tasks in three sequential sets:
 *   Set 0: [Collect Fees]              — predecessor, runs first.
 *   Set 1: [Wait For Payment Confirmation, Track Payment Deadline]
 *           — siblings that start together AFTER set 0 completes.
 *   Set 2: [Generate Permit]           — downstream, runs after set 1.
 *
 * All tasks use `runs-sequentially` as their entry rule. The `lane` option
 * on `.task()` controls which set a task joins: tasks on the same lane share
 * a set and start together; tasks on different lanes run one set after another.
 *
 * A task without `runs-sequentially` gets its own set regardless of `lane`;
 * `lane` only groups sequential tasks. Do not use `selected-tasks-completed`
 * gates to chain siblings — use task-set grouping instead.
 */
import { casePlan, rule } from '@uipath/maestro-builder-sdk/case';

export default casePlan('permit-issuance')
  .name('PermitIssuance')
  .identifier('PI')
  .stage('Issuing Permit', (s) =>
    s
      .required()
      .description('Collect payment, confirm and track in parallel, then generate.')
      .entryWhen(rule('case-entered'))
      .exitWhen(rule('required-tasks-completed'), { marksStageComplete: true })
      .task('Collect Fees', (t) =>
        t
          .action({ title: 'Collect permit fees', priority: 'Normal', recipient: 'cashier@city.gov' })
          .required()
          .entryWhen(rule('runs-sequentially')),
      { lane: 0 })
      .task('Wait For Payment Confirmation', (t) =>
        t
          .action({ title: 'Confirm payment received', priority: 'Normal', recipient: 'finance@city.gov' })
          .required()
          .entryWhen(rule('runs-sequentially')),
      { lane: 1 })
      .task('Track Payment Deadline', (t) =>
        t
          .action({ title: 'Track payment deadline', priority: 'Normal', recipient: 'finance@city.gov' })
          .required()
          .entryWhen(rule('runs-sequentially')),
      { lane: 1 })
      .task('Generate Permit', (t) =>
        t
          .action({ title: 'Generate the permit document', priority: 'Normal', recipient: 'permits@city.gov' })
          .required()
          .entryWhen(rule('runs-sequentially')),
      { lane: 2 }),
  )
  .completeWhen(rule('required-stages-completed'))
  .build();
