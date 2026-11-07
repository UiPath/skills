/**
 * The coder-eval task `skill-case-single-http-request` (UiPath/skills
 * tests/tasks/uipath-maestro-case/single_node/http_request) done with the SDK:
 * its SDD's one manual-mode http-request task, with the `Body -> echoResponse`
 * output row.
 */
import { casePlan, rule } from '@uipath/maestro-builder-sdk/case';

export default casePlan('HttpRequestSingleCase')
  .name('HttpRequestSingleCase')
  .description('Single-node case that posts an invoice number to an echo service and keeps the echoed body.')
  .identifier('HRC')
  .sla({ count: 1, unit: 'd' })
  .var('echoResponse', 'object', '{}')
  .stage('Notify', (s) =>
    s
      .required()
      .description('Post the invoice number to the echo service.')
      .entryWhen(rule('case-entered'))
      .exitWhen(rule('required-tasks-completed'), { marksStageComplete: true })
      .task('Post Invoice', (t) =>
        t
          .httpRequest({
            method: 'POST',
            url: 'https://postman-echo.com/post',
            headers: { Accept: 'application/json' },
            query: { source: 'skills-case-eval' },
            body: { invoiceNumber: 'INV-1042', probe: 'skills-case-http-7f3a' },
          })
          .outputs({ echoResponse: '=response.body' })
          .description('POST the invoice number to the echo service and keep the response body.')
          .required()
          .runOnReEntry()
          .entryWhen(rule('current-stage-entered')),
      ),
  )
  .completeWhen(rule('required-stages-completed'))
  .build();
