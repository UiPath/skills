# NeighborhoodWalkPlanner.flow.ts

The code block is the exact content of `NeighborhoodWalkPlanner.flow.ts`. To copy `NeighborhoodWalkPlanner.flow.ts`, write only the block's contents; never copy this Markdown file.

```ts
/**
 * CAPABILITY: call a published agentic process and wait for its output.
 *
 * An agentic process is a deployed orchestration rather than an inline model.
 * Its declared output fields become readable after the synchronous step.
 *
 * Generic scenario: ask a community-planning process for a neighborhood walk.
 */
import { flow, agenticProcess, script, input, out, types, type FlowVars } from '@uipath/maestro-builder-sdk';

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
  .step('recordRoute', script(recordRoute))
  .return({ route: out('recordRoute') })
  .build();

function recordRoute($vars: FlowVars) {
  return "route: " + String($vars.planWalk.output.RouteName);
}
```
