# Caching in a generated script

The runtime caches in two layers. Both build their own keys; a script author writes
at most two things:

```js
// Layer 1: keep one vendor read for a day. Every script on the connection shares it.
const describe = await intsvc.http({ method: "GET", url: `/sobjects/${name}/describe`, cacheFor: 86400 });
```

```js
// Layer 2: keep this activity's whole answer for an hour. A repeat call never runs the script.
export const cache = { ttl: 3600 };

export async function execute(context) { /* … */ }
```

Both need a runtime with UiPath/IPE-Runtime-Proxy#165 deployed. Behaviour on a runtime
without #165 is undefined; deploy after it.

Never name entries, version them, list inputs, or clear anything. The runtime derives
the keys and Udon clears entries when the connection or connector changes.

## When to cache

| Cache this | With |
|---|---|
| a lookup (a user by email, a channel, a project) | `cacheFor` on the call |
| a describe, or object and field discovery, including the describe a record list or a write needs | `cacheFor` on the call |
| a read activity that is called repeatedly with the same inputs (a dropdown list, object discovery, metadata discovery) | `export const cache` |

Do not cache:

- **Write activities.** A run that makes a write call is never stored, so `export const
  cache` on a write does nothing. Cache the reads inside it with `cacheFor`.
- **Data a user edits and reads back within the TTL.** They would read the old value.
- **Anything that depends on inbound headers, the time or randomness.** Those are not
  part of the key, so one caller would be served another's answer.

Live data as a whole (record lists, search results) is not a fit for `export const
cache`; cache the lookups inside it with `cacheFor` instead.

## `cacheFor` on `intsvc.http`

`cacheFor` is the maximum age in **seconds**. A cached response is served only while it
is no older than that, so two scripts asking for 1 h and 24 h share one entry and each
gets the age it asked for. Absent or `0` means not cached.

| Rule | |
|---|---|
| eligible calls | GET, HEAD, OPTIONS, and a POST marked `read: true` (a query API with no side effect) |
| `cacheFor` on any other call | rejected as `script_invalid` (`cache_for_not_read`) |
| stored when | the vendor answers 2xx with a normal body (not streamed, not a download, no attachment), up to 8 MiB, and the run then completes successfully (a script that throws stores nothing) |
| never stored when | the vendor's response says `Cache-Control: no-store` or `private`; `cacheFor` cannot override it |
| shared with | every script on the connection that makes the same request: method, URL with its query, the headers that change an answer (`accept`, `accept-language`, `content-type`, `prefer`, any `x-*` header the script sets) and the body |
| not in the key | the script, and the credential, which is injected after the key is built |
| longest life | 48 h, whatever `cacheFor` says |
| a hit | no vendor call and no call-budget charge (the response bytes still count) |
| after a write in the run | later `cacheFor` reads in that run go to the vendor, so a read after a write is fresh |

The runtime does not infer caching from the vendor's `Cache-Control`; it only lets a
`no-store` or `private` header switch caching off.

Pick the TTL from how stale the data may be, not from how expensive the call is:

| data | `cacheFor` |
|---|---|
| object and field schemas | 6-24 h (`21600`-`86400`) |
| a user looked up by email or id | up to 24 h (`86400`) |
| people, channels, groups, projects | 15 min-1 h (`900`-`3600`) |

A hit returns the response the vendor sent, so check the vendor's success signal on it as
you would on a live call ([runtime.md](runtime.md)). **Throw on every vendor failure,
including a 2xx whose body reports an error** (Slack's `ok: false`): a cached read is
committed only when the run completes successfully, so a script that throws on the
response stores nothing.

## `export const cache` on an activity

```js
export const cache = { ttl: 3600 };
```

Top level of the script, an object literal, `ttl` a positive number of seconds. Anything
else is rejected as `script_invalid` (`cache_declaration_invalid`). On a repeat request
the runtime answers before it fetches the script or starts a worker.

| Rule | |
|---|---|
| keyed on | the connection, the connector and its version, the script's own source, and the whole inbound request: the query (without `cache_data`) and the body |
| pagination | nothing to do: the page token is in the query, so each page has its own entry |
| stored when | the run made no write call, returned 2xx with a normal body, had no attachments, and is under 8 MiB |
| age | `min(ttl, the remaining age of the cached reads it used)`; never older than the data it was built from |
| `context.request.headers` | **absent** in a script that declares `cache`, so it cannot read what is not in its key |
| changing the script | ends its entries; there is nothing to version |

Use it on a read activity whose answer depends only on the query and body. It is safe to
add by mistake to a write (nothing is stored) but pointless.

## Both together: Slack

**List channels.** Both layers apply. The whole answer is kept for an hour; the Slack call
inside it is kept for 15 minutes and shared with any other script that lists channels.

```js
export const cache = { ttl: 3600 };

export async function execute(context) {
  const { pageSize: qPageSize, nextPage, types = "public_channel" } = context.request?.query ?? {};
  const page = intsvc.decodePageToken(nextPage) ?? {};
  const pageSize = Number(page.pageSize ?? qPageSize ?? 200);
  const cursor = page.next;

  const query = { types, exclude_archived: "true", limit: pageSize };
  if (cursor) query.cursor = cursor;

  const listed = await intsvc.http({ method: "GET", url: "/conversations.list", query, cacheFor: 900 });
  if (!listed.body?.ok) throw new Error("conversations.list failed: " + listed.body?.error);

  const channels = (listed.body.channels ?? []).map((c) => ({ id: c.id, name: c.name, is_private: c.is_private }));
  const next = listed.body.response_metadata?.next_cursor || "";

  listed.body = channels;
  intsvc.setPaginationHeaders(listed, { current: cursor, next, pageSize, hasMore: next !== "" });
  listed.headers["elements-returned-count"] = String(channels.length);
  return listed;
}
```

**Send a message to a user by email.** A write, so no `export const cache`. The email
lookup is cached for a day and shared with every other script that looks users up by email.

```js
export async function execute(context) {
  const { email, text } = context.request?.body ?? {};
  if (!email || !text) throw new Error("email and text are required");

  const user = await intsvc.http({ method: "GET", url: "/users.lookupByEmail", query: { email }, cacheFor: 86400 });
  if (!user.body?.ok) throw new Error("users.lookupByEmail failed: " + user.body?.error);

  const dm = await intsvc.http({ method: "POST", url: "/conversations.open", body: { users: user.body.user.id } });
  if (!dm.body?.ok) throw new Error("conversations.open failed: " + dm.body?.error);

  const sent = await intsvc.http({ method: "POST", url: "/chat.postMessage", body: { channel: dm.body.channel.id, text } });
  if (!sent.body?.ok) throw new Error("chat.postMessage failed: " + sent.body?.error);

  sent.body = { channel: sent.body.channel, ts: sent.body.ts, user: user.body.user.id };
  return sent;
}
```

| Call | Whole answer | Vendor read | Vendor calls made |
|---|---|---|---|
| ListChannels, page 1, first time | miss, script runs | miss | 1 |
| The same call within the hour | hit, script does not run | not reached | 0 |
| The same call with `types=private_channel` | miss, different query | miss, different URL | 1 |
| Any call after Udon invalidates the connection | miss | miss | 1 |
| SendMessageToUser to Alice, first time | not declared | lookup miss | 3 |
| SendMessageToUser to Alice again | not declared | lookup hit | 2 |
| AddUserToChannel for Alice, a different script | not declared | lookup hit, same entry | one fewer |

Salesforce follows the same pattern: `cacheFor` on the describe inside lists, writes and
metadata discovery; `export const cache` on object discovery and metadata discovery.

## Invalidation

Nothing to do. When Udon edits, re-authenticates or deletes a connection, or publishes a
connector, it tells the runtime, and the entries for that connection or connector stop
being served. If that call is lost, entries still end at their TTL (48 h at most). A token
refresh, a rename or an enable and disable clears nothing, because none of them changes an
answer.

## What the caller controls

| input | CLI flag | effect |
|---|---|---|
| `cache_data=uncache` on the inbound request | `--refresh` | both layers skip their reads and store fresh values |
| `cache_data=bypass` on the inbound request | `--no-cache` | both layers are off for the run: nothing read, nothing stored |

The runtime removes `cache_data` from the query before the script sees it.

## Warnings from `uip is connectors builder validate`

In a connector repo, `uip is connectors builder validate --connector-dir <dir>` warns on:

- `cacheFor` on a non-read method;
- `export const cache` in a script whose source contains a write;
- a cached script that reads `context.request.headers`, `Date.now`, `new Date` or `Math.random`;
- a `ttl` above the 48 h cap.

Fix them before publishing. The runtime makes the likely mistakes harmless (a run that
writes is never stored, headers are unavailable, the cap is enforced), but a warning
means the cache is not doing what the script says.

## Testing

- **While iterating, run with `--no-cache`** so nothing from a work-in-progress script is
  stored. `--refresh` is not a substitute: it still stores the new result.
- **Once the script is right, test the caching** with `--inline-script` or
  `--script-ref`: run the same call twice with no flag. The second run should make no
  vendor call (for a `cacheFor` read, one fewer). Confirm it from the vendor's own request
  count, not from the response, which looks the same.
  Then run once with `--refresh` and expect the vendor to be called again.
- **A `cacheFor` hit costs no call budget**, so a script near the 4-call limit has more
  room once its reads are cached; a miss still counts.
- **Say in the report** what is cached: each `cacheFor` call with its seconds, and each
  `export const cache` with its `ttl`.
