/**
 * CAPABILITY: invoke a deployed RPA workflow and declare its returned fields.
 *
 * The process key selects the node type; name and folder locate the deployed
 * automation. `returns` makes the robot's output readable downstream.
 *
 * Generic scenario: ask a robot to count missing tools in a shared workshop.
 */
import { flow, rpaWorkflow, script, input, out, types } from '@uipath/flow-sdk';

export default flow('workshop-inventory')
  .name('WorkshopInventory')
  .version('1.0.0')
  .input({ zone: types.string })
  .output({ report: types.string })
  .step('countTools', rpaWorkflow({
    key: 'bb67ae85-84ca-4b2c-9f37-ac52c57f9d18',
    name: 'Workshop Tool Count',
    folderPath: 'Shared/community-workshop',
    inputs: { zone: input('zone') },
    returns: { missingTools: 'integer' },
  }))
  .step('formatCount', script({
    code: 'return "missing tools: " + String($vars.countTools.output.missingTools);',
  }))
  .return({ report: out('formatCount') })
  .build();
