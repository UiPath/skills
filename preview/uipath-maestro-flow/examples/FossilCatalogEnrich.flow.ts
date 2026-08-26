/**
 * CAPABILITY: append AI-generated columns to an uploaded CSV with batch transform.
 *
 * The service receives a file attachment and returns a new file handle. Each
 * output column declares both the CSV header and the instruction for its cells.
 *
 * Generic scenario: add era and material labels to a fossil catalog export.
 */
import { flow, batchTransform, out, types } from '@uipath/flow-sdk';

export default flow('fossil-catalog-enrich')
  .name('FossilCatalogEnrich')
  .version('1.0.0')
  .input({ catalogFile: types.file })
  .output({ result: types.file })
  .step('labelSpecimens', batchTransform({
    attachment: out('start', 'catalogFile'),
    prompt: 'Classify each specimen from the catalog description.',
    outputColumns: [
      { name: 'Era', description: 'The geological era most consistent with the row' },
      { name: 'Material', description: 'The preserved material described by the row' },
    ],
    enableWebSearchGrounding: false,
  }))
  .return({ result: out('labelSpecimens') })
  .build();
