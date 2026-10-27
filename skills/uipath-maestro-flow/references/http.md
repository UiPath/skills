# HTTP

*Exact signatures, fields, and defaults: `http()`.*

Always author `http({ managed: true, ... })`; non-2xx responses take the error
path. `managed: false` (`core.action.http`) no longer runs: the tenant answers 500
`No handler registered for extension type 'Intsvc.HttpExecution'`, even though
`check` only warns (`HTTP_V1_RETIRED`).

Signature:
`http({ method?, url, managed, connection?, folder?, targetConnector?, headers?, query?, body?, contentType?, timeout?, retryCount?, returns? })`.

```ts
.step('policy', http({ method: 'GET', url: policyUrl,
  managed: true, returns: { limit: 'number' } }))
.step('read', script({
  code: 'return $vars.policy.output.body.limit;' }))
```

## At a glance

Managed HTTP routes non-2xx responses through its error port and exposes a JSON
response body as a parsed value. A status check is an `.onError()` handler reading
`err(step, 'status')`, not a `branches` condition on `statusCode`.

Signature: `http({ method?, url, managed, connection?, folder?, targetConnector?, headers?, query?, body?, contentType?, timeout?, retryCount?, returns?, branches? })`.

```ts
.step('getPolicy', http({ method: 'GET', url: policyUrl,
  managed: true, returns: { limit: 'number' } }))
.onError((h) => h.return({ status: err('getPolicy', 'status') }))
.step('limit', script({ code: 'return $vars.getPolicy.output.body.limit;' }))
```

Connector auth needs both `connection` and `folder` from `.flow-sdk/bindings.json`; omit both bindings for manual/implicit mode.
A `branch-<name>` side exit uses `.stepToList`.

## Choosing the node

Use managed for every request. A scenario that says “standalone” or
`core.action.http` still gets `managed: true`.

Live product evidence shows that the node exposes an `application/json` body as
a parsed value. Declare its top-level fields with `returns` and read them
directly; do not apply `JSON.parse` to a body declared by `returns`. A non-JSON
body remains opaque unless its live media type establishes a scalar contract. An
offline local run is not evidence for the product-CLI contract either way: follow
the task's named evidence mode and use live debug for product response shape.

The definitions default `timeout` to `PT15M` and `retryCount` to `0`. Override
them only when the scenario calls for different operational behavior.

## Managed authentication

Managed HTTP has two authentication modes. Omit `connection` and `folder` for
manual/implicit mode, which a URL that needs no connection uses. Implicit managed
HTTP goes out through Integration Service's shared egress, which public APIs may
rate-limit (429 `Daily API request limit exceeded`); that is infrastructure, not
a reason to switch to `managed: false`. CLI builds before cli#5384 also refuse
implicit managed HTTP in `uip maestro flow debug` (`Connection ImplicitConnection
not found in Resource Catalog`).

To reuse an Integration Service HTTP connection, provide both symbolic names
from `bindings.json`; the compiler resolves them into the
node detail and the emitted flow's resource bindings:

```ts
.step('profile', http({
  managed: true,
  method: 'GET',
  url: '/me',
  connection: 'spotifyHttp',
  folder: 'shared',
  returns: { display_name: 'string' },
}))
```

```json
{
  "bindings": [
    { "name": "spotifyHttp", "resourceKey": "<uipath-uipath-http connection id>" },
    { "name": "shared", "resourceKey": "<folder key>" }
  ]
}
```

Connection mode emits `authentication: "connector"`, targets
`uipath-uipath-http`, and treats `url` as a path relative to the connection's
configured base URL. Supplying only one of `connection` or `folder` is an error.

A secret the call needs, such as a header token or basic credentials, belongs in
that connection. The builder has no node that reads an Orchestrator asset or
credential, so a token written into `headers` sits in the flow source as plain
text.

For an HTTP fallback authenticated by another connector, set its connector key
as `targetConnector`. The node remains the managed HTTP wrapper, while the
proxied request reuses that connector's authentication:

```ts
.step('emoji', http({
  managed: true,
  method: 'GET',
  url: '/emoji.list',
  connection: 'slack',
  folder: 'shared',
  targetConnector: 'uipath-salesforce-slack',
}))
```

`targetConnector` requires both bindings.

## Response branches

`branches: [{ name, condition }]` declares extra exits evaluated against the
response — each becomes a `branch-<name>` source port routed with
`.stepToList('branch-<name>', …)`, while the main path continues from the
default port. Conditions are expressions (e.g.
``js`$vars.fetch.output.statusCode === 429` ``), typically reading the step's
own declared `returns`. Names must be unique and constant conditions are
rejected by `check`.

## Evidence

An offline replay proves the graph and chosen response shape. A live request is
the evidence for endpoint reachability, response media type, authentication,
and the service's actual status/body behavior.

Both HTTP types default to `timeout: 'PT15M'` and `retryCount: 0` when omitted.
The managed node deserializes the response body, so read `out('fetch', 'body.items')`
and let `returns` declare the body's top-level fields.
