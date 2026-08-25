# HTTP

*Exact signatures, fields, and defaults: [`http()`](api.md#http-function).*

The one factory selects two distinct product nodes:

- standalone: `http({ managed: false, ... })`, non-2xx responses stay on the
  success output with `statusCode`;
- managed: `http({ managed: true, ... })`, non-2xx responses take the error
  path.

Signature:
`http({ method?, url, managed, connection?, folder?, headers?, query?, body?, contentType?, timeout?, retryCount?, returns? })`.

```ts
.step('policy', http({ method: 'GET', url: policyUrl,
  managed: true, returns: { limit: 'number' } }))
.step('read', script({
  code: 'return $vars.policy.output.body.limit;' }))
```

## Choosing the node

Match the product node named by the scenario. “Managed HTTP Request,” “HTTP
Request node,” and `core.action.http.v2` select managed; “standalone” and
`core.action.http` select standalone. Authentication needs or the desire for an
error handler are not substitutes for that intent.

Live product evidence shows that both nodes expose an `application/json` body as
a parsed value. Declare its top-level fields with `returns` and read them
directly; do not apply `JSON.parse` to a body declared by `returns`. A non-JSON
body remains opaque unless its live media type establishes a scalar contract. An
offline local run is not evidence for the product-CLI contract either way: follow
the task's named evidence mode and use live debug for product response shape.

The definitions default `timeout` to `PT15M` and `retryCount` to `0`. Override
them only when the scenario calls for different operational behavior.

## Managed authentication

Managed HTTP has two authentication modes. Omit `connection` and `folder` for
manual/implicit mode. To reuse an Integration Service HTTP connection, provide
both symbolic names from `bindings.json`; the compiler resolves them into the
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
