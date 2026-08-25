/**
 * CAPABILITY: terminate the whole run from a guard branch.
 *
 * Unlike `return`, terminate publishes no flow output and leaves no outgoing
 * path. It is appropriate when continuing the run would be unsafe.
 *
 * Generic scenario: stop an aquarium maintenance round when oxygen is too low.
 */
import { flow, script, input, out, js, types } from '@uipath/flow-sdk';

export default flow('aquarium-safety-stop')
  .name('AquariumSafetyStop')
  .version('1.0.0')
  .input({ tank: types.string, oxygenMgL: types.number })
  .output({ status: types.string })
  .branch(
    'oxygenSafe',
    js`${input('oxygenMgL')} >= 6`,
    (safe) => safe
      .step('recordSafe', script({
        code: 'return "safe:" + $vars.start.output.tank + ":" + $vars.start.output.oxygenMgL;',
      }))
      .return({ status: out('recordSafe') }),
    (unsafe) => unsafe.terminate('stopRound', 'Oxygen below the safe maintenance threshold'),
  )
  .build();
