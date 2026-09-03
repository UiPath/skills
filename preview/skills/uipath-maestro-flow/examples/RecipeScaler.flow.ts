/**
 * CAPABILITY: `subflow` — a flow that runs OTHER flows.
 *
 * A `subflow` step hands work to a CHILD flow and reads back what the child
 * returns. Two scopes, one door: the child sees nothing of its caller — inputs
 * arrive through the `subflow(child, { … })` map (keyed by the child's own input
 * names) and results leave through the child's `.return()`.
 *
 *   - A child is declared as a `flow(...)` WITHOUT `.build()`, ABOVE its callers.
 *   - Read a subflow's output BY NAME: `out('step', 'field')`, never bare
 *     `out('step')` (a subflow publishes an OBJECT of its declared outputs).
 *   - Children nest: a child may itself run a subflow.
 *
 * Generic scenario: scale a recipe's ingredients by a factor, with a nested
 * child that phrases one line. No `.input`: variable defaults keep it
 * self-contained.
 */
import { flow, script, subflow, v, out, input, types } from '@uipath/flow-sdk';

/** A leaf child: scale one quantity. Declared ABOVE the flows that run it. */
const scaleIngredient = flow('scale-ingredient')
  .name('ScaleIngredient')
  .input({ grams: types.number, factor: types.number })
  .output({ scaled: types.number })
  .step('scale', script({ code: 'return Math.round($vars.start.output.grams * $vars.start.output.factor);' }))
  .return({ scaled: out('scale') });

/** A child that itself runs a subflow — the nesting case. */
const describeBatch = flow('describe-batch')
  .name('DescribeBatch')
  .input({ grams: types.number, factor: types.number, label: types.string })
  .output({ line: types.string })
  .step('scaleLabelled', subflow(scaleIngredient, { grams: input('grams'), factor: input('factor') }))
  .step('phrase', script({
    code: 'return $vars.start.output.label + ": " + $vars.scaleLabelled.output.scaled + " g";',
  }))
  .return({ line: out('phrase') });

export default flow('recipe-scaler')
  .name('RecipeScaler')
  .version('1.0.0')
  .output({ flour: types.number, sugar: types.number, headline: types.string })

  .var('factor', types.number, 2.5)
  .var('flourBase', types.number, 200)
  .var('sugarBase', types.number, 120)
  .var('flourLabel', types.string, 'flour')

  // The same child, twice — nothing shared but its definition.
  .step('scaleFlour', subflow(scaleIngredient, { grams: v('flourBase'), factor: v('factor') }))
  .step('scaleSugar', subflow(scaleIngredient, { grams: v('sugarBase'), factor: v('factor') }))

  // A child that nests one level deeper.
  .step('headline', subflow(describeBatch, { grams: v('flourBase'), factor: v('factor'), label: v('flourLabel') }))

  .return({
    flour: out('scaleFlour', 'scaled'),
    sugar: out('scaleSugar', 'scaled'),
    headline: out('headline', 'line'),
  })

  .build();
