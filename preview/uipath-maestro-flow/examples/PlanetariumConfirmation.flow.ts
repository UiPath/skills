/**
 * CAPABILITY: pause mid-flow until a filtered connector event arrives.
 *
 * `waitForEvent` is an action, not a start trigger. The injected event resumes
 * the existing run, and its payload is readable from the wait step's output.
 *
 * Generic scenario: wait for the email confirming a planetarium reservation.
 */
import { flow, waitForEvent, script, out, types } from '@uipath/flow-sdk';

const CONFIRMATIONS_FOLDER =
  'AQMkAGU5ZGFmM2QyLWY4OTEtNDAzNi04MGU2LWRjNzE2OWM0NTllMA==';

export default flow('planetarium-confirmation')
  .name('PlanetariumConfirmation')
  .version('1.0.0')
  .input({ reservationCode: types.string })
  .output({ confirmation: types.string })
  .step('awaitConfirmation', waitForEvent({
    connector: 'uipath-microsoft-outlook365',
    event: 'email-received',
    where: { parentFolderId: CONFIRMATIONS_FOLDER },
    filters: [{ field: 'subject', contains: 'PLANETARIUM' }],
  }))
  .step('recordConfirmation', script({
    code:
      'return "confirmed " + $vars.start.output.reservationCode + ": "'
      + ' + $vars.awaitConfirmation.output.subject;',
  }))
  .return({ confirmation: out('recordConfirmation') })
  .build();
