/**
 * CAPABILITY: `.doWhile` — run a body, then repeat WHILE a condition holds.
 *
 * The condition is checked AFTER each pass, so the body always runs at least
 * once (`core.logic.dowhile`). That is the difference from `.loop()`, which
 * iterates a collection it already has.
 *
 * The container publishes NO data output. Carry results out through a `.var()`
 * written from inside the body with `{ updates }` — here `page` advances the
 * cursor and doubles as the loop's own state. `limit` caps iterations (1–10,000;
 * blank means the platform default of 10,000), and `body.break()` works exactly
 * as it does in `.loop()`.
 *
 * Generic scenario: page through a meteor-shower sightings feed until it ends.
 */
import { flow, http, script, js, tmpl, v, out, types } from '@uipath/flow-sdk';

export default flow('meteor-shower-pages')
  .name('MeteorShowerPages')
  .version('1.0.0')
  .output({ pagesRead: types.string })
  .var('page', types.number, 1)
  .doWhile(
    'paginate',
    js`$vars.fetchPage.output.body.hasNextPage === true`,
    (body) => body
      .step('fetchPage', http({
        method: 'GET',
        url: tmpl`https://sightings.example.com/meteors?page=${v('page')}`,
        managed: false,
        returns: { hasNextPage: 'boolean' },
      }), { updates: { page: js`$vars.page + 1` } }),
    { limit: 50 },
  )
  .step('reportPages', script({
    code: 'return "read " + String($vars.page - 1) + " page(s) of sightings";',
  }))
  .return({ pagesRead: out('reportPages') })
  .build();
