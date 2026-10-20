/**
 * CAPABILITY: a `quick-form` human task with shown and answered fields, routed
 * per outcome.
 *
 * A shown field has `direction: 'input'` and a value from the flow. An answered
 * field has `direction: 'output'` and is read by its id after the reviewer picks
 * an outcome. The explicit variant emits the quick-form node family, which has
 * one exit per outcome (`outcome-approve`, `outcome-revise`): `.stepSwitch`
 * gives each one its own arm. A plain `.step()` after the task would instead
 * continue every outcome to that one next step.
 *
 * Generic scenario: a coordinator reviews a proposed field-trip destination.
 */
import { flow, hitl, input, lit, out, types } from '@uipath/maestro-builder-sdk';

export default flow('field-trip-quick-form')
  .name('FieldTripQuickForm')
  .version('1.0.0')
  .input({ destination: types.string })
  .output({ outcome: types.string, note: types.string })
  .stepSwitch('review', hitl({
    variant: 'quick-form',
    title: 'Review field trip',
    priority: 'Medium',
    fields: [
      {
        id: 'destination',
        label: 'Destination',
        type: 'text',
        direction: 'input',
        value: input('destination'),
      },
      {
        id: 'note',
        label: 'Coordinator note',
        type: 'text',
        direction: 'output',
      },
    ],
    outcomes: ['Approve', 'Revise'],
  }), [
    { value: 'Approve', body: (b) => b.return({ outcome: lit('approved'), note: out('review', 'note') }) },
    { value: 'Revise', body: (b) => b.return({ outcome: lit('sent back for revision'), note: out('review', 'note') }) },
  ])
  .build();
