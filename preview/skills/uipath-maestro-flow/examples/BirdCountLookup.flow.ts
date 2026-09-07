/**
 * CAPABILITY: run a deployed API workflow as one flow step.
 *
 * The workflow key selects the published node; name and folder locate the
 * deployment. Declared returns make its response readable and typed.
 *
 * Generic scenario: look up the latest bird count for a nature reserve.
 */
import { flow, apiWorkflow, input, out, types } from '@uipath/flow-sdk';

export default flow('bird-count-lookup')
  .name('BirdCountLookup')
  .version('1.0.0')
  .input({ reserve: types.string })
  .output({ count: types.number })
  .step('lookupCount', apiWorkflow({
    key: '3a6f4d22-8388-41c7-9f6a-6e4ea9154c32',
    name: 'Reserve Bird Count',
    folderPath: 'Shared/nature-observations',
    inputs: { reserve: input('reserve') },
    returns: { ObservedBirds: 'integer' },
  }))
  .return({ count: out('lookupCount', 'ObservedBirds') })
  .build();
