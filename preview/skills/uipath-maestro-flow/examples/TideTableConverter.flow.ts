/**
 * CAPABILITY: run a deployed Orchestrator FUNCTION as one step.
 *
 * A function is a small unit of code published as its own resource. `key`
 * becomes part of the node type (`uipath.core.function.<key>`); `name` and
 * `folderPath` locate the deployment. `returns` declares the fields the
 * function hands back so downstream steps can read them.
 *
 * A function is usually deployed into a folder of its OWN name, and the
 * binding's `resourceKey` is `<folderPath>.<name>` — read the folder from the
 * tenant rather than assuming `'Shared'`.
 *
 * Generic scenario: convert a tide height between measurement systems.
 */
import { flow, publishedFunction, script, input, out, types } from '@uipath/flow-sdk';

export default flow('tide-table-converter')
  .name('TideTableConverter')
  .version('1.0.0')
  .input({ heightFeet: types.number })
  .output({ reading: types.string })
  .step('toMetres', publishedFunction({
    key: 'd41f60c8-27b5-4e19-8a3d-6f0be9147c52',
    name: 'tide-convert',
    folderPath: 'Shared/tide-convert',
    inputs: { feet: input('heightFeet') },
    returns: { metres: 'number' },
  }))
  .step('formatReading', script({
    code:
      'return String($vars.start.output.heightFeet) + " ft = "'
      + ' + String($vars.toMetres.output.metres) + " m";',
  }))
  .return({ reading: out('formatReading') })
  .build();
