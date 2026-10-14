# Caching vendor calls in a generated script

A script can ask the runtime to keep a vendor answer and serve the next identical
call from it, per `intsvc.http` call, with a `cache` option:

```js
const resp = await intsvc.http({
  method: 'GET',
  url: '/conversations.list',
  query: { types: 'public_channel', limit: 200, cursor },
  cache: { ttl: 900 },
});
```

A runtime without the cache ignores the option and calls the vendor, so passing it
is always safe.

## When to cache

Cache a read whose answer changes slowly and that callers repeat: the list behind
a lookup field (channels, users, projects), and object or field discovery
(Salesforce `GET /sobjects`, `GET /sobjects/{name}/describe`). Do not cache a read
the caller expects to be live (a record they just changed, a status they are
polling for).

Never cache a write. Passing `cache` on a POST tells the runtime the call is a read,
such as a query API; it cannot tell otherwise. A cached write is not sent again
until the entry expires.

Pick the TTL from how stale the data may be, not from how expensive the call is:

| data | TTL |
|---|---|
| object and field schemas | 6–24 h (`21600`–`86400`) |
| people, channels, groups, projects | 15 min–1 h (`900`–`3600`) |
| anything a user edits and then reads back | do not cache |

The runtime caps every TTL at 48 h.

## The `cache` option

| field | rule |
|---|---|
| `ttl` | seconds; required |
| `key` | names the entry instead of the request, so two different calls share it. Up to 512 characters |
| `keyHeaders` | request header names whose values change the answer (at most 16). Ignored with `key` |
| `refresh` | `true` skips the read, calls the vendor, and replaces the entry |

The runtime builds the key, scoped to the tenant and the connection. Without `key`,
the entry is the request itself: method, full URL with its query, the named
`keyHeaders`, and for a POST the `Content-Type` and body. So:

- **a list's cursor or offset belongs in `query`**: each page is its own entry,
  which is what one-page-per-invocation wants;
- **a header that changes the answer** (`Accept-Language`, an API-version header)
  goes in `keyHeaders`, or two variants share one entry.

Not stored: a non-2xx answer, a `Set-Cookie` or `Cache-Control: no-store`
response, a streamed download, a body over 8 MiB. A POST body over 64 KiB, or one
streamed from an attachment, is not cached without a `key`. PUT, PATCH and DELETE
never are.

## What the caller controls

Two inbound query parameters, which the CLI sets with flags:

| parameter | CLI flag | effect |
|---|---|---|
| `cache_data=uncache` | `--refresh` | every cached call in the run skips the read and replaces its entry. The runtime removes it before the script sees `context.request.query` |
| `cache_key=<value>` | `--cache-key <value>` | reaches the script on `context.request.query`. A script that supports it passes it as `cache.key` |

Support `cache_key` only when two different calls must share an answer, such as an
invoke and the poll that reads its result. Pass the value unchanged, and take it
out of any query you send to the vendor:

```js
const { cache_key: cacheKey, ...query } = context.request.query ?? {};
const resp = await intsvc.http({
  method: 'GET', url: `/tasks/${context.request.body.id}`, query,
  cache: { ttl: 3600, ...(cacheKey ? { key: cacheKey } : {}) },
});
```

## Testing

- **`--inline-script` runs never use the cache.** They prove the script, not the
  caching. Check caching against the published script with `--script-ref`: run the
  same call twice, then once with `--refresh`.
- **A hit still costs one of the 4 calls** in the run's budget.
- **Say in the report** which calls are cached and with what TTL.
