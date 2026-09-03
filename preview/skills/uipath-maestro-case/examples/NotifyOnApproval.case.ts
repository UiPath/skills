/**
 * NotifyOnApproval — a Case plan that posts a Slack message via an Integration
 * Service connector once a human approval completes.
 *
 * Two required stages:
 *   Approve  — a human `action` task (Action Center approval).
 *   Notify   — a `connector` task that runs Slack `send-message-to-user` after
 *              Approve completes.
 *
 * The connector task needs a `bindings.json` alongside this file (see
 * examples/bindings.json) mapping the symbolic `slack` / `shared` names to a
 * real connection + folder. Compile with the connector library on
 * `$FLOW_SDK_LIBRARY_JSON` or `uip maestro case compile --library` supplies it.
 */
import { casePlan, rule } from '@uipath/flow-sdk/case';

export default casePlan('notify-on-approval')
  .name('NotifyOnApproval')
  .identifier('NOA')
  .stage('Approve', (s) =>
    s
      .required()
      .entryWhen(rule('case-entered'))
      .exitWhen(rule('required-tasks-completed'), { marksStageComplete: true })
      .task('Manager approval', (t) =>
        t
          .action({ title: 'Approve the request', priority: 'High', recipient: 'manager@corp.com' })
          .required()
          .entryWhen(rule('current-stage-entered')),
      ),
  )
  .stage('Notify', (s) =>
    s
      .required()
      .entryWhen(rule('selected-stage-completed', { stage: 'Approve' }))
      .exitWhen(rule('required-tasks-completed'), { marksStageComplete: true })
      .task('Post to Slack', (t) =>
        t
          .connector(
            'uipath-salesforce-slack',
            'send-message-to-user',
            // Connector inputs are the op's fields by name (discover them in the
            // markdown library at $FLOW_SDK_LIBRARY_MD). `send_as` is a query
            // parameter; `channel` / `messageToSend` are body fields.
            { channel: '@requester', messageToSend: 'Your request was approved.', send_as: 'bot' },
            { connection: 'slack', folder: 'shared' },
          )
          .required()
          .entryWhen(rule('current-stage-entered')),
      ),
  )
  .completeWhen(rule('required-stages-completed'))
  .build();
