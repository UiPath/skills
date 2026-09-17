/**
 * CAPABILITY: a `hitl` human task, and routing on WHICH BUTTON was pressed.
 *
 * More than one outcome routes PER OUTCOME by default: the task leaves on an
 * `outcome-<slug>` exit, one per button, and `.stepSwitch` gives each of them an
 * arm. There is no tacit next step and no decision node in the middle — an arm
 * that does not `.return()` converges, which is why a flow VARIABLE plus one
 * `.return()` beats returning separately from every arm.
 *
 *   fields[]:  direction: 'input'  → shown to the reviewer (bind to a value)
 *              direction: 'output' → the reviewer fills it in (read by id)
 *   outcomes[]: the buttons; each one gets an arm
 *
 * Generic scenario (an art-gallery submission going to a curator) so it teaches
 * the human-task shape rather than a task answer.
 */
import { flow, hitl, script, input, out, v, lit, types } from '@uipath/maestro-builder-sdk';

export default flow('gallery-submission')
  .name('GallerySubmission')
  .version('1.0.0')
  .input({ title: types.string, medium: types.string, widthCm: types.number, heightCm: types.number })
  .output({ outcome: types.string, note: types.string })
  .var('outcome', types.string)
  .var('note', types.string)

  // A derived fact for the curator to judge by, rather than raw dimensions.
  .step('wallSpace', script({
    code: 'return Math.round(($vars.start.output.widthCm * $vars.start.output.heightCm) / 100) + " dm2 of wall";',
  }))

  // One arm per button. Each assigns the shared variables; the single return reads them.
  .stepSwitch('curate', hitl({
    title: 'Curate submission',
    priority: 'Medium',
    fields: [
      { id: 'pieceTitle', label: 'Title', type: 'text', direction: 'input', value: input('title') },
      { id: 'medium', label: 'Medium', type: 'text', direction: 'input', value: input('medium') },
      { id: 'wall', label: 'Wall space', type: 'text', direction: 'input', value: out('wallSpace') },
      { id: 'note', label: 'Curator note', type: 'text', direction: 'output' },
    ],
    outcomes: ['Accept', 'Decline'],
  }), [
    {
      value: 'Accept',
      body: (b) => b.step(
        'hang',
        script({ code: 'return "accepted for the spring wall: " + $vars.curate.output.note;' }),
        { updates: { outcome: lit('Accept'), note: out('hang') } },
      ),
    },
    {
      value: 'Decline',
      body: (b) => b.step(
        'returnPiece',
        script({ code: 'return "returned to artist: " + $vars.curate.output.note;' }),
        { updates: { outcome: lit('Decline'), note: out('returnPiece') } },
      ),
    },
  ])

  .return({ outcome: v('outcome'), note: v('note') })

  .build();
