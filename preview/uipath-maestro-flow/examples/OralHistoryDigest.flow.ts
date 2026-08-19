/**
 * CAPABILITY: summarize an uploaded file with the platform Summarize node.
 *
 * The input is the complete file attachment. The result uses the node's
 * PascalCase `content.Text` and `content.Citations` contract.
 *
 * Generic scenario: condense a community oral-history interview for an archive.
 */
import { flow, summarize, out, err, tmpl, types } from '@uipath/flow-sdk';

export default flow('oral-history-digest')
  .name('OralHistoryDigest')
  .version('1.0.0')
  .input({ interviewFile: types.file })
  .output({ summary: types.string, citations: types.array })
  .step('summarizeInterview', summarize({
    attachment: out('start', 'interviewFile'),
    prompt: 'Summarize the places, people, dates, and traditions mentioned in this interview.',
    returnCitations: true,
  }))
  .onError((handler) => handler.return({
    summary: tmpl`could not summarize interview: ${err('summarizeInterview', 'detail')}`,
    citations: out('summarizeInterview', 'content.Citations'),
  }))
  .return({
    summary: out('summarizeInterview', 'content.Text'),
    citations: out('summarizeInterview', 'content.Citations'),
  })
  .build();
