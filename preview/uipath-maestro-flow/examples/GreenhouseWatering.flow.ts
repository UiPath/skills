/**
 * CAPABILITY: a two-way `.branch` — run one of two paths on a boolean condition.
 *
 * The scenario is deliberately generic (a greenhouse sensor) so it shows the
 * SHAPE, not a task answer: a condition, a `yes` arm, a `no` arm, each ending in
 * its own `.return()`.
 *
 *     .branch(name, <js boolean>, (yes) => …, (no) => …)
 *
 * `js\`…\`` builds the condition from inputs/vars/step outputs; each arm is a
 * sub-builder exactly like the top-level flow. An arm that ends in `.return()`
 * is that path's End node — the two arms are independent endings, not a join.
 */
import { flow, script, input, out, js, types } from '@uipath/flow-sdk';

export default flow('greenhouse-watering')
  .name('GreenhouseWatering')
  .version('1.0.0')
  .input({ moisture: types.number, threshold: types.number })
  .output({ action: types.string })

  .branch(
    'needsWater',
    js`${input('moisture')} < ${input('threshold')}`,
    (yes) =>
      yes
        .step('water', script({
          code: 'return "watered: moisture " + $vars.start.output.moisture + " is below " + $vars.start.output.threshold;',
        }))
        .return({ action: out('water') }),
    (no) =>
      no
        .step('hold', script({
          code: 'return "held off: moisture " + $vars.start.output.moisture + " is at or above " + $vars.start.output.threshold;',
        }))
        .return({ action: out('hold') }),
  )

  .build();
