/**
 * CAPABILITY: a `hitl` human task, and routing on WHICH BUTTON was pressed.
 *
 * A human task shows the reviewer some fields and collects others, then leaves
 * on one port (`completed`) whatever outcome was chosen — so per-outcome routing
 * is a `.branch` DOWNSTREAM reading `out('<task>', 'Action')` (the outcome name).
 *
 *   fields[]:  direction: 'input'  → shown to the reviewer (bind to a value)
 *              direction: 'output' → the reviewer fills it in (read by id)
 *   outcomes[]: the buttons; the chosen one is `out('<task>', 'Action')`
 *
 * Generic scenario (an art-gallery submission going to a curator) so it teaches
 * the human-task shape rather than a task answer.
 */
import { flow, hitl, script, input, out, js, types } from '@uipath/flow-sdk';

export default flow('gallery-submission')
  .name('GallerySubmission')
  .version('1.0.0')
  .input({ title: types.string, medium: types.string, widthCm: types.number, heightCm: types.number })
  .output({ outcome: types.string, note: types.string })

  // A derived fact for the curator to judge by, rather than raw dimensions.
  .step('wallSpace', script({
    code: 'return Math.round(($vars.start.output.widthCm * $vars.start.output.heightCm) / 100) + " dm2 of wall";',
  }))

  .step('curate', hitl({
    title: 'Curate submission',
    priority: 'Medium',
    fields: [
      { id: 'pieceTitle', label: 'Title', type: 'text', direction: 'input', value: input('title') },
      { id: 'medium', label: 'Medium', type: 'text', direction: 'input', value: input('medium') },
      { id: 'wall', label: 'Wall space', type: 'text', direction: 'input', value: out('wallSpace') },
      { id: 'note', label: 'Curator note', type: 'text', direction: 'output' },
    ],
    outcomes: ['Accept', 'Decline'],
  }))

  // Route on the button. `out('curate', 'Action')` holds the outcome's NAME.
  .branch(
    'wasAccepted',
    js`${out('curate', 'Action')} === "Accept"`,
    (yes) =>
      yes
        .step('hang', script({ code: 'return "accepted for the spring wall: " + $vars.curate.output.note;' }))
        .return({ outcome: out('curate', 'Action'), note: out('hang') }),
    (no) =>
      no
        .step('returnPiece', script({ code: 'return "returned to artist: " + $vars.curate.output.note;' }))
        .return({ outcome: out('curate', 'Action'), note: out('returnPiece') }),
  )

  .build();
