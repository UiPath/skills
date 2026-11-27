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
  const query = { types, exclude_archived: "true", limit: 200 };

  const listed = await intsvc.http({ method: "GET", url: "/conversations.list", query });
  if (listed.status !== 200 || !listed.body?.ok) throw new Error(`conversations.list failed: ${listed.status} ${listed.body?.error ?? ""}`);

  // A fresh result, so no vendor header is stored with the cached answer.
  return { ok: true, status: 200, body: (listed.body.channels ?? []).map((c) => ({ id: c.id, name: c.name, is_private: c.is_private })) };
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

`ttl` is a positive number of seconds. Default cap 48 h (`172800`). Pick it from how
stale the data may be, not from how expensive the call is:

| data | TTL |
|---|---|
| object and field schemas | 6-24 h (`21600`-`86400`) |
| people, channels, groups, projects | 15 min-1 h (`900`-`3600`) |

Use the table for a new connector. Slack's 48 h below is the one exception: it matches how
long v3 kept the same lists, so a migrated action behaves as before.

`cache` is allowed on a GET, HEAD or OPTIONS, and on a POST marked `read: true` (a
query API with no side effect). On any other call it is `script_invalid`. `cache:
cond ? { ttl } : undefined` is accepted by the runtime and by CACHE-001; the call is
uncached when `cond` is false.

## What is never cached

- An answer that is not a 200, 203 or 204.
- An answer whose `ok` is not `true` (see *The answer carries `ok`*).
- A write. A run that made any call that is not a read is write-tainted: its answer is
  not stored, and a Layer A read after the write goes live.
- A run that threw, or ended in a `script_*` error. Nothing from it is stored.
- A whole answer from a run in which any `intsvc.http` call threw or came back non-2xx,
  even if the script caught it and returned a 200.
- A whole answer from a run that saved a connection setting (`intsvc.connectionConfig.set`),
  or whose answer the runtime had to scrub of a withheld config value.
- A streamed, download or oversized body (default cap 8 MiB), and a request that uploads
  files.
- A vendor answer with `Cache-Control: no-store` or `private`, or a `Vary` of `*`; `ttl`
  cannot override it. The runtime never infers caching from the vendor's headers.

Throw on every vendor-reported failure, as Slack's `ok: false` above. Catching the throw
and returning anyway still keeps the answer out of the cache, so a partial answer is
never served from it.

## The answer carries `ok`

Every script's `execute()` answer carries a boolean `ok`, cached or not; CACHE-009
fails a script that provably lacks it. Nothing from a run is stored, in either layer,
unless the answer's `ok` is `true`: `false`, missing or not a boolean is handled as if
the script threw. The caller still gets the answer unchanged, and `ok` never reaches its
envelope.

| the script returns | `ok` |
|---|---|
| an `intsvc.http` result untouched (`return res`), or with its body swapped (`{ ...res, body }`, `res.body = …; return res`) | already set: true for a 2xx status |
| an answer it builds | set it: `{ ok: true, status: 200, body }` |
| a vendor that reports an error in the body of a 200 (Slack's `{ "ok": false }`) | throw, or set it from the body: `ok: res.body?.ok === true` |
| a failure it answers on purpose | `ok: false`; assigning `res.ok = false` on a result is honoured |

This is the answer's `ok`, not the vendor body's: Jira has no body `ok`, and its answers
still carry one.

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

Nothing about the credential is in either key, so Udon drops the connection's cache on
re-auth, edit or delete. When a change must take effect at once, run with `--refresh`.

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

Cache declarations are checked before a connector ships. The runtime cannot tell whether a vendor read is shared across scripts, so the connector rule engine's `script-cache` rules (CACHE-001 to CACHE-010) run on the scripts themselves. CACHE-009 and CACHE-010 check every v4 script, cached or not.

**Errors** fail the check:

| Code | Fails when | Fix |
|---|---|---|
| CACHE-001 (`cache-shape`) | `cache` is not `{ ttl: <seconds> }`: an extra key, a missing ttl, or a ttl that is not a positive finite number (`0`, `Infinity`, `1e999`, `NaN`, `undefined`). `export const cache`, `export { cache }`, `export { x as cache }` and `export function cache` are all checked | Write `cache: { ttl: 3600 }` |
| CACHE-002 (`cache-on-write`) | `cache` is on a call that changes data (anything but GET, HEAD, OPTIONS, or POST with `read: true`), or on a call whose options have a spread | Remove `cache`, or mark a query-only POST `read: true` |
| CACHE-003 (`cache-not-shared`) | a vendor call has `cache` but no other script makes the same call with `cache` | Cache the script's whole answer with `export const cache = { ttl }` instead |
| CACHE-004 (`script-parse`) | a script is not valid JavaScript, so it cannot be checked | Fix the syntax error |
| CACHE-009 (`answer-ok-missing`) | a return of `execute()` provably lacks `ok`: an object literal with no `ok` and no spread of an `intsvc.http` result, a bare `return;`, a primitive or an array; or `execute()` can end without returning | Return the `intsvc.http` result (`return await intsvc.http(…)` is accepted), or set `ok` |

Two calls count as the same when the method and URL match, ignoring the query string and treating every `${…}` in the URL as a placeholder. A URL built at runtime (`byId ? "/a" : "/b"`) cannot be compared and fails CACHE-003. Only the scripts present in the repo count, so a read cached in one script fails until a second script that makes it is in the repo too.

Where the checker cannot see a value it assumes the worst. A call whose `method` is missing or not a literal fails CACHE-003, and one whose options object has a spread fails CACHE-002, since neither can be proven a read. `intsvc.http(options)` with a non-literal options object counts as a possible write for CACHE-005.

**Warnings and info** never fail the check:

| Code | Means |
|---|---|
| CACHE-005 (`answer-cache-on-write`) | `export const cache` on a script that writes; its answers are never stored |
| CACHE-006 (`answer-cache-reads-headers`) | the script reads `context.request.headers`, which a cached script does not get |
| CACHE-007 (`cache-ttl-capped`) | the ttl is above 48 h, the runtime's default cap |
| CACHE-008 (`script-skipped`, info) | a `.ts` script is not parsed, so its cache declarations are not checked |
| CACHE-010 (`answer-ok-unknown`) | a return the checker cannot classify, such as a helper's call result; make sure it carries `ok`, or return the object inline |

**How it is enforced**

- `uip is connectors builder validate`, with `--checks legacy` (the default) or `--checks rules`. Errors fail validation, and warnings are listed.
- Each finding prints as `CODE severity file message`. A script finding has no JSON pointer, and its message starts `line L, col C: `.

## Worked example: Slack

Slack's v4 connector caches its three lookup lists the way v3 did: **ListUsers**,
**ListChannels** and **ListPublicChannels** each declare `export const cache = { ttl: 172800 }`
(48 h, v3's lifetime). Each list is made by one script only, so none of their `intsvc.http` calls carries
`cache`, and each page is its own entry. Each builds its answer with `ok: true`, after
throwing on Slack's `ok: false`.

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
| ListChannels with another `types` | miss, different key | 1 |
| ListChannels with `--refresh` | skipped, answer re-stored | 1 |
| SendMessageToUser | not declared (a write) | every call |

For Salesforce the split is the same: `cache` on the object describe that several scripts
make, and `export const cache` on a list that only one script makes.

## Testing

- **While editing a script**, run it with `--inline-script` (never cached, see *What the
  caller controls*); re-check a script that reads headers once it is published.
- **Once the script is published, test the caching** with `--script-ref`: run the same
  call twice, then once with `--refresh`. The CLI shows no hit or miss and the answer
  looks the same, so compare run times: a hit is much faster than the miss, and a
  `--refresh` run takes miss time. A change made at the vendor between runs shows up
  only after `--refresh`. If those do not separate hit from miss, report the cache as
  untested.
- **Say in the report** which reads or answers are cached, with the layer and `ttl`.
