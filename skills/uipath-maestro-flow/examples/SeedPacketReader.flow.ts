/**
 * CAPABILITY: classify a document, then extract fields against an INLINE taxonomy.
 *
 * `documentClassify` (`uipath.document.classify`) names the document's type.
 * `dynamicExtract` (`uipath.ixp.extract-document-builder`, the Extract document
 * node) extracts against the taxonomy it carries instead of a published IxP
 * project's trained fields.
 *
 * This is the SOURCE route for that node, and it carries two requirements the
 * node itself does not (references/document-pipeline.md explains both): the
 * `model` block is the factory's — copy a real pair from the tenant, never
 * construct one — and the taxonomy's stable ids are written by hand, because
 * the factory emits `schema` verbatim and nothing mints them. The default route
 * is the CLI (references/extract-document-node.md), which needs neither.
 *
 * Generic scenario: read the sowing details off a scanned seed packet.
 */
import { flow, documentClassify, dynamicExtract, script, out, types } from '@uipath/maestro-builder-sdk';

const sowingTaxonomy = {
  prompt: 'Extract the sowing details printed on the seed packet. Values are on the packet; do not infer missing ones.',
  outputSchema: {
    type: 'object',
    additionalProperties: false,
    required: ['Sowing Details'],
    properties: {
      'Sowing Details': {
        type: ['object', 'null'],
        description: 'The sowing table printed on the back of the packet.',
        additionalProperties: false,
        required: ['Variety', 'Sow Depth Mm', 'Days To Germinate'],
        'x-uipath-field-group-id': '0b6f2e5e-8d1a-4a53-9b2e-6a4a1c2d7f31',
        properties: {
          'Variety': {
            $ref: '#/$defs/ft-exact-text',
            description: 'The variety name as printed on the front.',
            'x-uipath-field-id': '6a1d9c0a-2f4b-4e3c-8a7d-5b9e0c1f2a43',
          },
          'Sow Depth Mm': {
            $ref: '#/$defs/ft-number',
            description: 'The sowing depth in millimetres.',
            'x-uipath-field-id': '9c3b7a51-4d2e-4f60-b18a-7e5d2c0b9f64',
          },
          'Days To Germinate': {
            $ref: '#/$defs/ft-number',
            description: 'How many days germination takes; the upper bound where a range is printed.',
            'x-uipath-field-id': '2e8f4b63-7c1d-4a95-8d02-1a6b3e9c5d87',
          },
        },
      },
    },
    $defs: {
      'ft-exact-text': { title: 'Exact Text', type: ['string', 'null'], format: 'verbatim' },
      'ft-number': { title: 'Number', type: ['string', 'null'], format: 'decimal' },
    },
  },
};

export default flow('seed-packet-reader')
  .name('SeedPacketReader')
  .version('1.0.0')
  .input({ packetScan: types.file })
  .output({ summary: types.string })
  .step('classifyPacket', documentClassify({
    fileRef: out('start', 'packetScan'),
    splitPages: false,
  }))
  .step('extractSowing', dynamicExtract({
    fileRef: out('start', 'packetScan'),
    schema: sowingTaxonomy,
    model: {
      modelName: 'seedpackets-9c41e7b2-ixp',
      folderKey: '4c9d1f70-6b2e-4a58-9f13-2ad5c8e0b741',
    },
  }))
  .step('summarize', script({
    code:
      'const extracted = $vars.extractSowing.output;\n'
      + 'return "type:" + String($vars.classifyPacket.output.ClassificationResult ?? "?")\n'
      + '  + " extracted:" + Object.keys(extracted ?? {}).length;',
  }))
  .return({ summary: out('summarize') })
  .build();
