/**
 * CAPABILITY: a scheduled flow that creates an Orchestrator queue item.
 *
 * A scheduled trigger has no caller, so the specimen record is part of the
 * flow. The queue step hands that record to a separately managed worker.
 *
 * Generic scenario: send one preserved plant specimen to a daily cataloguing
 * queue. This demonstrates the timer and queue surfaces without mirroring an
 * eval task's business process.
 */
import { flow, scheduled, queueItem, script, out, types } from '@uipath/flow-sdk';

const CATALOG_QUEUE = 'HerbariumCatalog';
const CATALOG_FOLDER = 'Shared';
const CATALOG_KEY = '6a09e667-bb67-4e3c-8d3d-20e5b6f14a21';

export default flow('herbarium-dispatch')
  .name('HerbariumDispatch')
  .version('1.0.0')
  .output({ receipt: types.string })
  .trigger(scheduled({ every: 'R/P1D' }))
  .step('catalogSpecimen', queueItem({
    queue: CATALOG_QUEUE,
    folderPath: CATALOG_FOLDER,
    key: CATALOG_KEY,
    item: { SpecimenId: 'HERB-204', Family: 'Polypodiaceae', Cabinet: 'Ferns' },
    reference: 'HERB-204',
    priority: 'Normal',
  }))
  .step('recordDispatch', script({
    code: 'return "catalogued specimen HERB-204";',
  }))
  .return({ receipt: out('recordDispatch') })
  .build();
