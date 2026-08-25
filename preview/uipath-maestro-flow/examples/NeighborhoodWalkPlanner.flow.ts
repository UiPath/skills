/**
 * CAPABILITY: call a published agentic process and wait for its output.
 *
 * An agentic process is a deployed orchestration rather than an inline model.
 * Its declared output fields become readable after the synchronous step.
 *
 * Generic scenario: ask a community-planning process for a neighborhood walk.
 */
import { flow, agenticProcess, script, input, out, types } from '@uipath/flow-sdk';

export default flow('neighborhood-walk-planner')
  .name('NeighborhoodWalkPlanner')
  .version('1.0.0')
  .input({ district: types.string })
  .output({ route: types.string })
  .step('planWalk', agenticProcess({
    key: '510e527f-ade6-4c92-a860-9f17657dc821',
    name: 'Neighborhood Walk Planner',
    folderPath: 'Shared/community-planning',
    inputs: { District: input('district') },
    returns: { RouteName: 'string' },
  }))
  .step('recordRoute', script({
    code: 'return "route: " + String($vars.planWalk.output.RouteName);',
  }))
  .return({ route: out('recordRoute') })
  .build();
