/**
 * CAPABILITY: a standalone HTTP call followed by a delay.
 *
 * `managed: false` emits the plain HTTP node, where response status and body
 * remain ordinary outputs. A delay publishes nothing; the next step reads the
 * HTTP result, not the timer.
 *
 * Generic scenario: read a lighthouse signal and pause before recording it.
 */
import { flow, http, delay, script, input, out, tmpl, types } from '@uipath/flow-sdk';

export default flow('lighthouse-signal')
  .name('LighthouseSignal')
  .version('1.0.0')
  .input({ station: types.string })
  .output({ report: types.string })
  .step('readSignal', http({
    method: 'GET',
    url: tmpl`https://signals.example.com/stations/${input('station')}`,
    managed: false,
    returns: { signal: 'string' },
  }))
  .step('cooldown', delay({ duration: 'PT2S' }))
  .step('recordSignal', script({
    code:
      'return "station " + $vars.start.output.station + ": "'
      + ' + String($vars.readSignal.output.body.signal || "unknown");',
  }))
  .return({ report: out('recordSignal') })
  .build();
