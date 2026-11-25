# Caching vendor reads in a generated script

Two layers, one spec shape: `{ ttl }`, seconds. Pick by who reuses the data.

| | vendor read (Layer A) | whole answer (Layer B) |
|---|---|---|
| declare | `cache: { ttl }` on `intsvc.http` | `export const cache = { ttl }` at the top of the script |
| caches | one vendor response | the script's final answer, served before it runs |
| use when | the **same read** is made by more than one script of the connector | one script's answer is worth caching and no other script makes the read |

```js
// Layer A: Salesforce describe, made by every script that needs the field schema
const describe = await intsvc.http({
  method: "GET",
  url: `/services/data/v62.0/sobjects/${name}/describe`,
  cache: { ttl: 86400 },
});
if (describe.status !== 200) throw new Error(`describe ${name} failed: ${describe.status}`);
```

```js
// Layer B: one script's whole answer
export const cache = { ttl: 900 };

async function execute(context) {
  const { types = "public_channel" } = context.request?.query ?? {};
  const page = intsvc.decodePageToken(context.request?.query?.nextPage) ?? {};
  const pageSize = Number(page.pageSize ?? 200);
  const cursor = page.next;

  const query = { types, exclude_archived: "true", limit: pageSize };
  if (cursor) query.cursor = cursor;

  const listed = await intsvc.http({ method: "GET", url: "/conversations.list", query });
  if (listed.status !== 200 || !listed.body?.ok) throw new Error(`conversations.list failed: ${listed.status} ${listed.body?.error ?? ""}`);

  const next = listed.body.response_metadata?.next_cursor || "";
  // A fresh result, so no vendor header is stored with the cached page.
  const result = { status: 200, body: (listed.body.channels ?? []).map((c) => ({ id: c.id, name: c.name, is_private: c.is_private })) };
  intsvc.setPaginationHeaders(result, { current: cursor, next, pageSize, hasMore: next !== "" });
  return result;
}
```

A Layer A hit makes no vendor call, but it still counts as one of the script's calls (the
4-call run budget) and its response bytes still count. A Layer B hit does not run the
script at all.

## Which layer

1. Is the same read (method + URL) made by two or more scripts of the connector?
   Yes: `cache` on that `intsvc.http` call, in **every** script that makes it, with the
   same method and url template. A describe or user lookup several actions share.
2. Otherwise, does the script's answer depend only on its inbound query and body (and the
   connection), and make no write? Yes: `export const cache`. A lookup list that changes
   slowly (users, channels, the object list), one page per entry.
3. Otherwise do not cache. Live data (record lists, search results, anything a user
   edits and reads back) stays uncached; cache the shared lookups inside them with
   Layer A.

Both can coexist in one script. A Layer B entry expires with the earliest of the Layer A
entries it was built from.

`ttl` is a positive number of seconds. The runtime stores for at most 48 h (`172800`) by
default; the host can change that cap (`IPE_SCRIPT_CACHE_MAX_TTL_MS`). Pick it from how
stale the data may be, not from how expensive the call is:

| data | TTL |
|---|---|
| object and field schemas | 6-24 h (`21600`-`86400`) |
| people, channels, groups, projects | 15 min-1 h (`900`-`3600`) |

Use the table for a new connector. Slack's 48 h below is the one exception: it matches how
long v3 kept the same lists, so a migrated action behaves as before.

`cache` is allowed on a GET, HEAD or OPTIONS, and on a POST marked `read: true` (a
query API with no side effect). On any other call it is `script_invalid`. `cache:
cond ? { ttl } : undefined` leaves the call uncached.

## What is never cached

- An answer that is not a 200, 203 or 204. A 202, 206 or other 2xx is not stored either.
- A write. A run that made any call that is not a read is write-tainted: its answer is
  not stored, and a Layer A read after the write goes live.
- A run that threw, or ended in a `script_*` error. Nothing from it is stored.
- A whole answer from a run in which any `intsvc.http` call threw or came back non-2xx,
  even if the script caught it and returned a 200.
- A whole answer from a run that saved a connection setting (`intsvc.connectionConfig.set`),
  or whose answer the runtime had to scrub of a withheld config value.
- A streamed, download or oversized body (over 8 MiB by default,
  `IPE_SCRIPT_CACHE_MAX_ENTRY_BYTES`), and a request that uploads files.
- A vendor answer with `Cache-Control: no-store` or `private`, or a `Vary` of `*`; `ttl`
  cannot override it. The runtime never infers caching from the vendor's headers.

**A returned `ok: false` body is cached**, because the run completed and the answer was
200. Throw on every vendor-reported failure, as Slack's `ok: false` above, so it is not
stored. Catching the throw and carrying on does not help: the run is still not stored.

## What the key holds

A Layer A key is the tenant, connection, method, URL (query merged and sorted), **every
header the script sets**, and a digest of the request body. Anything that changes the answer must be in the URL, the query
or a header; a header you set but do not mean to vary on splits the cache, so leave it
off. A call carrying `authorization`, `cookie`, `range` or a conditional header is not
cached.

A Layer B key is the tenant, connection, the script's digest (a hash of its source), the
object name, and the inbound query (without `cache_data`) and body. The method and path
are not in it; each script has its own digest. Each page has its own entry, because the page
token is in the query. A publish that changes the script changes its digest, so its old
entries are never read again; there is nothing to version. The key does **not** include inbound headers, so a script
with `export const cache` gets no `context.request.headers`: do not write one that varies
on them.

Nothing about the credential is in either key, so the connection's cache is dropped when
Udon invalidates it on re-auth, edit or delete. Correctness after a re-auth depends on
that call being deployed; until it is, an entry can outlive a re-auth for its TTL.

## What the caller controls

| input | CLI flag | effect |
|---|---|---|
| `cache_data=uncache` on the inbound request | `--refresh` | skips the read in both layers and stores the new answer |

`cache_data` is removed before the script sees `context.request.query`. **Inline scripts
(`--inline-script`) are never cached**: both layers skip them, so every run calls the
vendor. Only a published script (`--script-ref`) is cached. Because an inline run does not
read `export const cache`, it keeps `context.request.headers` and does not refuse a
malformed declaration; both change once the script is published.

## Checked before you publish

Cache declarations are checked before a connector ships. The runtime cannot tell whether a vendor read is shared across scripts, so the connector rule engine's `script-cache` rules (CACHE-001 to CACHE-008) run on the scripts themselves.

**Errors** fail the check:

| Code | Fails when | Fix |
|---|---|---|
| CACHE-001 (`cache-shape`) | `cache` is not `{ ttl: <seconds> }`: an extra key, a missing ttl, or a ttl that is not a positive finite number (`0`, `Infinity`, `1e999`, `NaN`, `undefined`). `export const cache`, `export { cache }`, `export { x as cache }` and `export function cache` are all checked | Write `cache: { ttl: 3600 }` |
| CACHE-002 (`cache-on-write`) | `cache` is on a call that changes data (anything but GET, HEAD, OPTIONS, or POST with `read: true`), or on a call whose options have a spread | Remove `cache`, or mark a query-only POST `read: true` |
| CACHE-003 (`cache-not-shared`) | a vendor call has `cache` but no other script makes the same call with `cache` | Cache the script's whole answer with `export const cache = { ttl }` instead |
| CACHE-004 (`script-parse`) | a script is not valid JavaScript, so it cannot be checked | Fix the syntax error |

Two calls count as the same when the method and URL match, ignoring the query string and treating every `${…}` in the URL as a placeholder. A URL built at runtime (`byId ? "/a" : "/b"`) cannot be compared and fails CACHE-003. Only the scripts present in the repo count, so a read cached in one script fails until a second script that makes it is in the repo too.

Where the checker cannot see a value it assumes the worst. A call whose `method` is missing or not a literal fails CACHE-003, and one whose options object has a spread fails CACHE-002, since neither can be proven a read. `intsvc.http(options)` with a non-literal options object counts as a possible write for CACHE-005.

**Warnings and info** never fail the check:

| Code | Means |
|---|---|
| CACHE-005 (`answer-cache-on-write`) | `export const cache` on a script that writes; its answers are never stored |
| CACHE-006 (`answer-cache-reads-headers`) | the script reads `context.request.headers`, which a cached script does not get |
| CACHE-007 (`cache-ttl-capped`) | the ttl is above 48 h, the runtime's default cap |
| CACHE-008 (`script-skipped`, info) | a `.ts` script is not parsed, so its cache declarations are not checked |

**How it is enforced**

- `uip is connectors builder validate`, with `--checks legacy` (the default) or `--checks rules`. Errors fail validation, and warnings are listed.
- Each finding prints as `CODE severity file message`. A script finding has no JSON pointer, and its message starts `line L, col C: `.

## Worked example: Slack

Slack's v4 connector caches its three lookup lists the way v3 did: **ListUsers**,
**ListChannels** and **ListPublicChannels** each declare `export const cache = { ttl: 172800 }`
(48 h, v3's lifetime). Each list is made by one script only, so none of their `intsvc.http` calls carries
`cache`, and each page is its own entry.

**Send a message to a user by email** is a write, so it has no `export const cache`. Its
`users.lookupByEmail` read is also made by Get User by Email, but neither script can cache it
today, and Slack would not anyway because v3 never did:

- Send message to user sets an `Authorization` header on the call, and a call carrying
  `authorization` is never cached.
- Get User by Email picks `/users.info` or `/users.lookupByEmail` at runtime, so its URL
  cannot be compared and `validate` fails it with CACHE-003. It also forwards
  `context.request.headers`, which would split the key from any other script's.

To share a read, every script that makes it needs a literal method and url template, no
`Authorization` header, the same set of headers, and at least two scripts carrying `cache`.

| call | answer cache | vendor calls |
|---|---|---|
| ListChannels, first time | miss, script runs | 1 |
| ListChannels again within 48 h | hit, script does not run | 0 |
| ListChannels with another `types` or `nextPage` | miss, different key | 1 |
| ListChannels with `--refresh` | skipped, answer re-stored | 1 |
| SendMessageToUser | not declared (a write) | every call |

For Salesforce the split is the same: `cache` on the object describe that several scripts
make, and `export const cache` on a list that only one script makes.

## Testing

- **While editing a script**, run it with `--inline-script`. Nothing is cached for an
  inline script, so every run is live and `--refresh` is not needed. An inline run also
  keeps `context.request.headers` and does not refuse a bad `export const cache`, so
  re-check a script that reads headers once it is published.
- **Once the script is published, test the caching** with `--script-ref`: run the same call twice (the second is a hit), then once with
  `--refresh`. Confirm a hit from the vendor's own request count, not from the
  response, which looks the same.
- **A Layer A hit still counts as one of the 4 calls** in the run budget, with its response
  bytes; it only saves the vendor call. A Layer B hit does not run the script, so it
  costs no budget.
- **Say in the report** which reads or answers are cached, with the layer and `ttl`.
