# LighthouseSignal.flow.ts

The code block is the exact content of `LighthouseSignal.flow.ts`. To copy `LighthouseSignal.flow.ts`, write only the block's contents; never copy this Markdown file.

```ts
/**
 * CAPABILITY: an HTTP call followed by a delay.
 *
 * A delay publishes nothing; the next step reads the HTTP result, not the
 * timer.
 *
 * Generic scenario: read a lighthouse signal and pause before recording it.
 */
import { flow, http, delay, script, input, out, tmpl, types, type FlowVars } from '@uipath/maestro-builder-sdk';

export default flow('lighthouse-signal')
  .name('LighthouseSignal')
  .version('1.0.0')
  .input({ station: types.string })
  .output({ report: types.string })
  .step('readSignal', http({
    method: 'GET',
    url: tmpl`https://signals.example.com/stations/${input('station')}`,
    managed: true,
    returns: { signal: 'string' },
  }))
  .step('cooldown', delay({ duration: 'PT2S' }))
  .step('recordSignal', script(recordSignal))
  .return({ report: out('recordSignal') })
  .build();

function recordSignal($vars: FlowVars) {
  return "station " + $vars.start.output.station + ": " + String($vars.readSignal.output.body.signal || "unknown");
}
```
