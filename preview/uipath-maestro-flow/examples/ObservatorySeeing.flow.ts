/**
 * CAPABILITY: an ERROR PORT — a failed step routes to a handler instead of
 * killing the run.
 *
 *     .step('fetch', http({ url: …, managed: true, returns: { … } }))
 *     .onError((h) => h.return({ … err('fetch', 'message') … }))
 *     .step('onSuccess', …)   // everything after .onError is the SUCCESS path
 *
 * `.onError()` handles the step BEFORE it; its handler is a path of its own.
 * `managed: true` is load-bearing: on the plain HTTP node a 4xx/5xx is a SUCCESS
 * carrying `statusCode`, so the handler would never run (`check` rejects that).
 * The managed node throws on non-2xx, so the failure reaches the port — and it
 * hands back a PARSED body. Read the failure with `err('<step>', '<field>')`
 * (siblings of `out`): `code` (a string), `message`, `detail`, `category`,
 * `status`.
 *
 * Generic scenario: an observatory asks a public sun API when tonight's viewing
 * can start, and states a fallback for when the service is unreachable.
 */
import { flow, http, script, err, out, input, lit, tmpl, types } from '@uipath/flow-sdk';

export default flow('observatory-seeing')
  .name('ObservatorySeeing')
  .version('1.0.0')
  .input({ lat: types.number, lng: types.number })
  .output({ viewingFrom: types.string, source: types.string })

  // Somebody else's uptime, so the call has to ROUTE on failure.
  .step('fetchSun', http({
    url: tmpl`https://api.sunrise-sunset.org/json?lat=${input('lat')}&lng=${input('lng')}&formatted=0`,
    managed: true,
    // Declare what we read, or the read is refused.
    returns: { results: 'object' },
  }))
  // Service down / rate-limited / unknown coordinates: carry on with a stated
  // fallback rather than faulting the whole run.
  .onError((h) => h.return({
    viewingFrom: lit('sunset unknown — check a local almanac'),
    source: tmpl`fallback (${err('fetchSun', 'code')}): ${err('fetchSun', 'message')}`,
  }))

  // Success path — reached only when the call actually succeeded.
  .step('describe', script({
    // Read the DECLARED field (`body.results`) and index it in JS; reading
    // `body.results.sunset` through $vars would not resolve (declaration stops at
    // `results`).
    code: 'const r = $vars.fetchSun.output.body.results || {};\nreturn { line: "best viewing after " + (r.sunset || "sunset") };',
  }))
  .return({ viewingFrom: out('describe', 'line'), source: lit('live') })

  .build();
