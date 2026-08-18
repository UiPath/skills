/**
 * CAPABILITY: a `quick-form` human task with shown and answered fields.
 *
 * A shown field has `direction: 'input'` and a value from the flow. An answered
 * field has `direction: 'output'` and is read by its id after the reviewer picks
 * an outcome. The explicit variant emits the quick-form node family.
 *
 * Generic scenario: a coordinator reviews a proposed field-trip destination.
 */
import { flow, hitl, input, out, types } from '@uipath/flow-sdk';

export default flow('field-trip-quick-form')
  .name('FieldTripQuickForm')
  .version('1.0.0')
  .input({ destination: types.string })
  .output({ outcome: types.string, note: types.string })
  .step('review', hitl({
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
  }))
  .return({
    outcome: out('review', 'Action'),
    note: out('review', 'note'),
  })
  .build();
