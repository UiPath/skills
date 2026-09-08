/**
 * CAPABILITY: invoke a published agent resource.
 *
 * Published coded and low-code agents share the same node family. The release
 * key, name, folder, inputs, and declared returns close the deployed contract.
 *
 * Generic scenario: ask a botany advisor for a plant's common name.
 */
import { flow, agent, script, input, out, types } from '@uipath/flow-sdk';

export default flow('plant-name-advisor')
  .name('PlantNameAdvisor')
  .version('1.0.0')
  .input({ description: types.string })
  .output({ answer: types.string })
  .step('identifyPlant', agent({
    key: '9b05688c-2b3e-4b69-86e6-f1f923a264d8',
    name: 'Plant Name Advisor',
    folderPath: 'Shared/botany',
    flavour: 'lowcode',
    inputs: { description: input('description') },
    returns: { commonName: 'string' },
  }))
  .step('recordName', script({
    code: 'return "plant: " + String($vars.identifyPlant.output.commonName);',
  }))
  .return({ answer: out('recordName') })
  .build();
