/**
 * CAPABILITY: a `.parallel` fan-out and its join — the builder's only non-linear
 * shape.
 *
 *     .parallel('mergeName', [
 *       (a) => a.step(…).step(…),   // an arm can be a CHAIN
 *       (b) => b.step(…),
 *       (c) => c.step(…),
 *     ])
 *     .step('after', …)   // continues from the Merge, so it sees every arm
 *
 * The name passed to `.parallel` is the MERGE, not a fork — reading its own
 * output is an error (`PARALLEL_HAS_NO_OUTPUT`); read the arms' steps instead.
 * Locally the arms run sequentially, so a green run proves the fork/join graph
 * is right and every arm ran — not that they ran at the same instant. Use it for
 * genuinely independent work.
 *
 * Generic scenario: three independent pre-show checks at a concert. No `.input`:
 * the data is variable defaults so the example is self-contained.
 */
import { flow, script, out, types } from '@uipath/flow-sdk';

export default flow('concert-soundcheck')
  .name('ConcertSoundcheck')
  .version('1.0.0')
  .output({ verdict: types.string })

  .var('mics', types.object, { live: 6, expected: 6 })
  .var('monitors', types.object, { working: 4, total: 4 })
  .var('lightingCues', types.number, 18)

  // Three checks with nothing to say to each other → they fan out.
  .parallel('checksDone', [
    // An arm can be a CHAIN: count, then phrase it.
    (a) => a
      .step('micCount', script({
        code: 'return $vars.mics.live === $vars.mics.expected ? "all mics live" : ($vars.mics.expected - $vars.mics.live) + " mic(s) dead";',
      }))
      .step('micLine', script({
        code: 'return "mics: " + $vars.micCount.output;',
      })),

    (b) => b.step('monitorLine', script({
      code: 'return "monitors: " + ($vars.monitors.working === $vars.monitors.total ? "all good" : $vars.monitors.working + "/" + $vars.monitors.total);',
    })),

    (c) => c.step('lightingLine', script({
      code: 'return "lighting: " + ($vars.lightingCues > 0 ? $vars.lightingCues + " cues loaded" : "no cues");',
    })),
  ])

  // Runs after the join, so all three arms' outputs are readable here.
  .step('verdict', script({
    code: 'return [$vars.micLine.output, $vars.monitorLine.output, $vars.lightingLine.output].join("; ");',
  }))

  .return({ verdict: out('verdict') })

  .build();
