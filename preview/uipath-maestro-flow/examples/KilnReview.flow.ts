/**
 * CAPABILITY: a human task whose form is supplied by a deployed Action App.
 *
 * The flow identifies the app and binds values to the app's own input names.
 * Outcomes still belong to the flow and are read through `Action`.
 *
 * Generic scenario: let a studio coordinator approve a pottery kiln firing.
 */
import { flow, hitl, script, input, out, types } from '@uipath/flow-sdk';

export default flow('kiln-review')
  .name('KilnReview')
  .version('1.0.0')
  .input({ pieceName: types.string, targetCelsius: types.number })
  .output({ decision: types.string })
  .step('reviewFiring', hitl({
    variant: 'action-app',
    title: 'Kiln firing review',
    priority: 'Medium',
    app: {
      name: 'Kiln Firing Review',
      key: '3c6ef372-fe94-4f82-aa0b-6d1f45c8b721',
      folderPath: 'Shared',
      inputs: {
        'Piece Name': input('pieceName'),
        'Target Celsius': input('targetCelsius'),
      },
    },
    outcomes: ['Fire', 'Hold'],
  }))
  .step('recordDecision', script({
    code: `const action = $vars.reviewFiring.output.Action;
return action === 'Fire'
  ? 'scheduled:' + $vars.start.output.pieceName
  : 'held:' + $vars.start.output.pieceName;`,
  }))
  .return({ decision: out('recordDecision') })
  .build();
