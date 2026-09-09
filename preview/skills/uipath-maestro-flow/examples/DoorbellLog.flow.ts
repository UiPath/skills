/**
 * CAPABILITY: a flow that STARTS on a connector event (`onEvent` trigger).
 *
 *     .trigger(onEvent({
 *       connector: 'uipath-http-webhook',
 *       event: 'http-webhook',
 *       connection: 'bWebhook', folder: 'bWebhookFolder',   // bindings.json ids
 *     }))
 *
 * There is no manual start: the event IS the start, and its payload arrives on
 * `$vars.start.output`. For the HTTP Webhook connector the CONNECTION is the
 * subscription's scope (each connection has its own URL), so there are no event
 * parameters and no `where` — binding the connection is what points the flow at
 * a URL at all. A local run subscribes to nothing; a start trigger's payload is
 * supplied AS FLOW INPUT for the dry run.
 *
 * Generic scenario: a smart doorbell posts to a webhook; the flow logs who rang.
 */
import { flow, script, onEvent, out, types } from '@uipath/flow-sdk';

export default flow('doorbell-log')
  .name('DoorbellLog')
  .version('1.0.0')
  .output({ entry: types.string })

  .trigger(onEvent({
    connector: 'uipath-http-webhook',
    event: 'http-webhook',
    connection: 'bWebhook',
    folder: 'bWebhookFolder',
  }))

  // `request_body` is TEXT — parse it, and handle a body that is not JSON, since
  // a webhook's body is whatever the caller sent.
  .step('readPing', script({
    code: `
      var raw = $vars.start.output.request_body;
      var who = "unknown";
      try { who = JSON.parse(raw).visitor || "unknown"; } catch (e) { who = "unparseable"; }
      return { entry: "doorbell: " + who + " rang" };
    `,
  }))
  .return({ entry: out('readPing', 'entry') })

  .build();
