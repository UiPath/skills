/**
 * CAPABILITY: classify a document, then extract fields against an INLINE schema.
 *
 * `documentClassify` (`uipath.document.classify`) names the document's type.
 * `dynamicExtract` (`uipath.ixp.extract-document-builder`) is the other half of
 * the pair: it carries its own `schema` instead of a published IxP project's
 * trained fields, which is what makes it "dynamic".
 *
 * Dynamic Extract still needs a model DEPLOYMENT identity. `modelName` and
 * `folderKey` below are placeholders in the shape the tenant serves — copy the
 * real pair from the tenant; never construct them.
 *
 * Generic scenario: read the sowing details off a scanned seed packet.
 */
import { flow, documentClassify, dynamicExtract, script, out, types } from '@uipath/flow-sdk';

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
    schema: {
      type: 'object',
      properties: {
        variety: { type: 'string' },
        sowDepthMm: { type: 'string' },
        daysToGerminate: { type: 'string' },
      },
    },
    model: {
      modelName: 'seedpackets-9c41e7b2-ixp',
      folderKey: '4c9d1f70-6b2e-4a58-9f13-2ad5c8e0b741',
    },
  }))
  .step('summarize', script({
    code:
      'const sowing = $vars.extractSowing.output || {};\n'
      + 'return "type:" + ($vars.classifyPacket.output.DocumentTypeName || "?")\n'
      + '  + " variety:" + (sowing.variety || "-")\n'
      + '  + " depth:" + (sowing.sowDepthMm || "-");',
  }))
  .return({ summary: out('summarize') })
  .build();
