# HTTP

*Exact signatures, fields, and defaults: `http()`.*

The factory selects two product nodes:

- standalone: `http({ managed: false, ... })`; non-2xx responses remain on success with `statusCode`.
- managed: `http({ managed: true, ... })`; non-2xx responses take the error path.

Signature:
`http({ method?, url, managed, connection?, folder?, targetConnector?, headers?, query?, body?, contentType?, timeout?, retryCount?, returns?, branches? })`.

Both nodes parse `application/json` response bodies as values. Match `managed` to the scenario's named node: “Managed HTTP Request,” “HTTP Request node,” and `core.action.http.v2` mean managed; “standalone” and `core.action.http` mean standalone. Authentication needs and error handlers do not override that choice. Connector auth requires both `connection` and `folder` from `.flow-sdk/bindings.json`; omit both for manual/implicit mode. A `branch-<name>` side exit uses `.stepToList`.

```ts
.step('getPolicy', http({ method: 'GET', url: policyUrl,
  managed: true, returns: { limit: 'number' },
  branches: [{ name: 'throttled', condition: js`$vars.getPolicy.output.statusCode === 429` }] }))
.stepToList('branch-throttled', (b) => b.return({}))
.step('limit', script({ code: 'return $vars.getPolicy.output.body.limit;' }))
```

## At a glance

Declare response top-level fields with `returns` and read them directly; never apply `JSON.parse` to a body declared by `returns`. Non-JSON bodies remain opaque unless their live media type establishes a scalar contract. Offline local runs do not establish the product-CLI contract: follow the task's named evidence mode and use live debug for product response shape.

Definitions default `timeout` to `PT15M` and `retryCount` to `0`; override only when required by the scenario.

## Choosing the node

Set `managed: false` or `managed: true` according to the scenario. Standalone keeps non-2xx responses on success; managed routes them to its error port.

## Managed authentication

Managed HTTP supports manual/implicit and connection modes. Omit `connection` and `folder` for manual/implicit mode. For a URL needing no connection, prefer standalone (`managed: false`) unless the scenario names managed: implicit managed HTTP uses Integration Service shared egress, which public APIs often rate-limit. Standalone emits an `HTTP_V1_RETIRED` warning from `check`; that is expected. CLI builds before cli#5384 also refuse implicit managed HTTP in `uip maestro flow debug` (`Connection ImplicitConnection not found in Resource Catalog`).

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

`targetConnector` requires both bindings and is invalid on standalone HTTP.

## Response branches

`branches: [{ name, condition }]` declares extra response exits. Each becomes a `branch-<name>` source port routed with `.stepToList('branch-<name>', …)`; the main path continues from the default port. Conditions typically read declared `returns`, such as ``js`$vars.fetch.output.statusCode === 429` ``. Names must be unique; `check` rejects constant conditions.

## Evidence

Offline replay proves the graph and chosen response shape. A live request proves endpoint reachability, response media type, authentication, and actual service status/body behavior.

The managed node deserializes the response body; read `out('fetch', 'body.items')` and let `returns` declare the body's top-level fields.
