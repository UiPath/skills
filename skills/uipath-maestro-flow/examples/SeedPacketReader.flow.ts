/**
 * CAPABILITY: classify a document, then extract fields against an INLINE taxonomy.
 *
 * `documentClassify` (`uipath.document.classify`) names the document's type.
 * `dynamicExtract` (`uipath.ixp.extract-document-builder`, the Extract document
 * node) extracts against the taxonomy it carries instead of a published IxP
 * project's trained fields.
 *
 * It takes no `model` argument: compile gives the step its IDP processor, named after the
 * step's label, and writes the processor's resource file into the solution
 * (references/document-pipeline.md). The taxonomy carries no ids: compile
 * gives every field group and field its stable id.
 *
 * Generic scenario: read the sowing details off a scanned seed packet.
 */
import { flow, documentClassify, dynamicExtract, script, out, types, type FlowVars } from '@uipath/maestro-builder-sdk';

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
        properties: {
          'Variety': {
            $ref: '#/$defs/ft-exact-text',
            description: 'The variety name as printed on the front.',
          },
          'Sow Depth Mm': {
            $ref: '#/$defs/ft-number',
            description: 'The sowing depth in millimetres.',
          },
          'Days To Germinate': {
            $ref: '#/$defs/ft-number',
            description: 'How many days germination takes; the upper bound where a range is printed.',
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
  }), { label: 'Extract sowing details' })
  .step('summarize', script(summarize))
  .return({ summary: out('summarize') })
  .build();

function summarize($vars: FlowVars) {
  const extracted = $vars.extractSowing.output;
  return "type:" + String($vars.classifyPacket.output.ClassificationResult ?? "?")
    + " extracted:" + Object.keys(extracted ?? {}).length;
}
