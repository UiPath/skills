/**
 * CAPABILITY: start a flow from a submitted FORM (`core.trigger.form`).
 *
 * `formTrigger()` takes no arguments. The form's fields are derived from
 * `.input()` — one field per input, required unless the input has a default —
 * so the submitted values ARE the flow's inputs and are read from
 * `$vars.start.output.<name>` exactly like a manual trigger's.
 *
 * Generic scenario: accept an entry into a village bake-off.
 *
 * No local rung renders a form; supply the values with `--input` when running.
 */
import { flow, formTrigger, script, out, types } from '@uipath/flow-sdk';

export default flow('bake-off-entry-form')
  .name('BakeOffEntryForm')
  .version('1.0.0')
  .input({ bakerName: types.string, category: types.string, servings: types.number })
  .output({ confirmation: types.string })
  .trigger(formTrigger())
  .step('confirmEntry', script({
    code:
      'return $vars.start.output.bakerName + " entered " + $vars.start.output.category'
      + ' + " with " + String($vars.start.output.servings) + " servings";',
  }))
  .return({ confirmation: out('confirmEntry') })
  .build();
