/**
 * CAPABILITY: an N-way `.switch` — the many-armed sibling of `.branch`.
 *
 * A case matches when `<discriminant> === <case value>`, compared STRICTLY, so
 * the value's type counts (the ranks below are strings, so the cases are
 * strings). The optional last function is the DEFAULT arm, taken when nothing
 * matched. Each arm ends in its own `.return()`.
 *
 * Generic scenario (a dojo belt rank → what its next grading needs) so it reads
 * as "here is the switch shape", not as any task's expected output.
 */
import { flow, script, input, out, types } from '@uipath/flow-sdk';

export default flow('belt-progression')
  .name('BeltProgression')
  .version('1.0.0')
  .input({ rank: types.string })
  .output({ nextGrading: types.string })

  .switch(
    'byRank',
    input('rank'),
    [
      {
        value: 'white',
        body: (b) =>
          b
            .step('whiteNext', script({ code: 'return "yellow: 8 basic forms";' }))
            .return({ nextGrading: out('whiteNext') }),
      },
      {
        value: 'yellow',
        body: (b) =>
          b
            .step('yellowNext', script({ code: 'return "green: 12 forms plus one spar";' }))
            .return({ nextGrading: out('yellowNext') }),
      },
      {
        value: 'green',
        body: (b) =>
          b
            .step('greenNext', script({ code: 'return "brown: 20 forms plus board break";' }))
            .return({ nextGrading: out('greenNext') }),
      },
    ],
    // Default arm — any rank not listed above.
    (other) =>
      other
        .step('unknownRank', script({ code: 'return "see the head instructor";' }))
        .return({ nextGrading: out('unknownRank') }),
  )

  .build();
