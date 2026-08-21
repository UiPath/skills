/**
 * CAPABILITY: extract structured fields with a published IxP project.
 *
 * The registry supplies the complete project node type. Extraction results use
 * the nested `ExtractionResult.ResultsDocument.Fields[]` schema.
 *
 * Generic scenario: read the catalog fields on a scanned archive card.
 */
import { flow, ixpExtract, script, out, err, tmpl, types } from '@uipath/flow-sdk';

const PROJECT =
  'uipath.ixp.archive-cards.2f6e5c18-43ac-4d6a-91d5-c7b1240e8a36-74a4b14d-8ef5-4f24-a6aa-0d6f52a08c11';

export default flow('archive-card-extract')
  .name('ArchiveCardExtract')
  .version('1.0.0')
  .input({ cardFile: types.file })
  .output({ result: types.string })
  .step('extractCard', ixpExtract({
    project: PROJECT,
    modelName: 'Archive Cards',
    name: 'Archive Cards',
    folderName: 'Shared',
    fileRef: out('start', 'cardFile'),
  }))
  .onError((handler) => handler.return({
    result: tmpl`could not extract archive card: ${err('extractCard', 'detail')}`,
  }))
  .step('readCard', script({
    code: `const doc = $vars.extractCard.output.ExtractionResult.ResultsDocument || {};
const fields = Array.isArray(doc.Fields) ? doc.Fields : [];
const first = fields.length ? fields[0] : {};
return 'type:' + (doc.DocumentTypeName || '?')
  + ' fields:' + fields.length
  + ' first:' + (first.FieldName || '-') + '=' + ((first.Values || [])[0] ?? '-');`,
  }))
  .return({ result: out('readCard') })
  .build();
