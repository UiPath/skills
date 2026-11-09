# HTTP

*Exact signatures, fields, and defaults: `http()`.*

Always author `http({ managed: true, ... })`; non-2xx responses take the error
path. `managed: false` (`core.action.http`) no longer runs: the tenant answers 500
`No handler registered for extension type 'Intsvc.HttpExecution'`, even though
`check` only warns (`HTTP_V1_RETIRED`). A `managed: false` step you edit gets
the same switch, and every read of its `statusCode` becomes an `.onError()`
handler ([error-handling.md](error-handling.md)); leave an untouched one alone.
An older SDK's `HTTP_V1_RETIRED` text saying to "keep managed: false" for a URL without a connection is outdated; still use `managed: true`.

Signature:
`http({ method?, url, managed, connection?, folder?, targetConnector?, headers?, query?, body?, contentType?, timeout?, retryCount?, returns?, branches? })`.

Live product evidence shows that the node exposes an `application/json` body as
a parsed value.
Connector auth needs both `connection` and `folder` from `.flow-sdk/bindings.json`; omit both bindings for manual/implicit mode.
A `branch-<name>` side exit uses `.stepToList`.

```ts
.step('getPolicy', http({ method: 'GET', url: policyUrl,
  managed: true, returns: { limit: 'number' } }))
.onError((h) => h.return({ status: err('getPolicy', 'status') }))
.step('limit', script({ code: 'return $vars.getPolicy.output.body.limit;' }))
```

## At a glance

Managed HTTP routes non-2xx responses through its error port and exposes a JSON
response body as a parsed value. A status check is an `.onError()` handler reading
`err(step, 'status')`, not a `branches` condition on `statusCode`.

Declare response top-level fields with `returns` and read them directly; never apply `JSON.parse` to a body declared by `returns`. Non-JSON bodies remain opaque unless their live media type establishes a scalar contract. Offline local runs do not establish the product-CLI contract: follow the task's named evidence mode and use live debug for product response shape.

Definitions default `timeout` to `PT15M` and `retryCount` to `0`; override only when required by the scenario.

## Choosing the node

Use managed for every request. A scenario that says “standalone” or
`core.action.http` still gets `managed: true`.

## Managed authentication

Managed HTTP supports manual/implicit and connection modes. Omit `connection` and `folder` for
manual/implicit mode, which a URL that needs no connection uses. Implicit managed
HTTP goes out through Integration Service's shared egress, which public APIs may
rate-limit (429 `Daily API request limit exceeded`); that is infrastructure, not
a reason to switch to `managed: false`. CLI builds before cli#5384 also refuse
implicit managed HTTP in `uip maestro flow debug` (`Connection ImplicitConnection
not found in Resource Catalog`).

To reuse an Integration Service HTTP connection, provide both symbolic names from `bindings.json`; the compiler resolves them into the node detail and the emitted flow's resource bindings:

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

Connection mode emits `authentication: "connector"`, targets `uipath-uipath-http`, and treats `url` as relative to the connection's configured base URL. Supplying only one of `connection` or `folder` is an error.

Put secrets such as header tokens or basic credentials in the connection. The builder cannot read an Orchestrator asset or credential; a token in `headers` is plain text in flow source.

For an HTTP fallback authenticated by another connector, set its key as `targetConnector`. The node remains the managed HTTP wrapper and the proxied request reuses that connector's authentication:

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

`branches: [{ name, condition }]` declares extra response exits. Each becomes a `branch-<name>` source port routed with `.stepToList('branch-<name>', …)`; the main path continues from the default port. Conditions are expressions (e.g.
``js`$vars.fetch.output.body.limit > 100` ``), typically reading the step's
own declared `returns`. A non-2xx never reaches a branch; handle it with
`.onError()`. Names must be unique; `check` rejects constant conditions.

## Evidence

Offline replay proves the graph and chosen response shape. A live request proves endpoint reachability, response media type, authentication, and actual service status/body behavior.

The node defaults to `timeout: 'PT15M'` and `retryCount: 0` when omitted.
It deserializes the response body, so read `out('fetch', 'body.items')`
and let `returns` declare the body's top-level fields.
