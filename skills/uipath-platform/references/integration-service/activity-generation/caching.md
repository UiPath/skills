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
  listed.body = (listed.body.channels ?? []).map((c) => ({ id: c.id, name: c.name, is_private: c.is_private }));
  intsvc.setPaginationHeaders(listed, { current: cursor, next, pageSize, hasMore: next !== "" });
  return listed;
}
```

A Layer A hit makes no vendor call and costs nothing against the script's call or egress
budget (response bytes still count). A Layer B hit does not run the script at all. The runtime proxy's `docs/intsvc-sdk.md` §3a is the live contract for limits and
metrics; follow it where this page differs.

## Which layer

1. Is the same read (method + URL) made by two or more scripts of the connector?
   Yes: `cache` on that `intsvc.http` call, in **every** script that makes it, with the
   same method and url template. A describe or user lookup several actions share.
2. Otherwise, does the script's answer depend only on its inbound query and body (and the
   connection), and make no write? Yes: `export const cache`. One page of a list, the object list.
3. Otherwise do not cache. Live data (record lists, search results, anything a user
   edits and reads back) stays uncached; cache the shared lookups inside them with
   Layer A.

Both can coexist in one script. A Layer B entry expires with the earliest of the Layer A
entries it was built from.

`ttl` is a positive number of seconds, capped at 48 h (`172800`). Pick it from how stale
the data may be, not from how expensive the call is:

| data | TTL |
|---|---|
| object and field schemas | 6-24 h (`21600`-`86400`) |
| people, channels, groups, projects | 15 min-1 h (`900`-`3600`) |

`cache` is allowed on a GET, HEAD or OPTIONS, and on a POST marked `read: true` (a
query API with no side effect). On any other call it is `script_invalid`. `cache:
cond ? { ttl } : undefined` leaves the call uncached.

## What is never cached

- A non-2xx answer.
- A write. A run that made any call that is not a read is write-tainted: its answer is
  not stored, and a Layer A read after the write goes live.
- A run that threw, or ended in a `script_*` error. Nothing from it is stored.
- A streamed, download or oversized (over 8 MiB) body.
- A vendor answer with `Cache-Control: no-store` or `private`; `ttl` cannot override it.
  The runtime never infers caching from the vendor's headers.

**A returned `ok: false` body is cached**, because the run completed and the answer was
2xx. Throw on every vendor-reported failure, as Slack's `ok: false` above, so it is not
stored.

## What the key holds

A Layer A key is the tenant, connection, method, URL (query merged and sorted), **every
header the script sets**, and a digest of the request body. Anything that changes the answer must be in the URL, the query
or a header; a header you set but do not mean to vary on splits the cache, so leave it
off. A call carrying `authorization`, `cookie`, `range` or a conditional header is not
cached.

A Layer B key is the tenant, connection, the script's digest (a hash of its source), and the
inbound query (without `cache_data`) and body. The method and path are not in it; each
script has its own digest. Each page has its own entry, because the page
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
vendor. Only a published script (`--script-ref`) is cached.

## Checked before you publish

Cache declarations are checked before a connector ships. The runtime cannot tell whether a vendor read is shared across scripts, so these rules run on the scripts themselves.

**Errors** fail the check:

| Rule | Fails when | Fix |
|---|---|---|
| `cache-shape` | `cache` is not `{ ttl: <seconds> }`: an extra key, a missing ttl, or a ttl that is not a positive number | Write `cache: { ttl: 3600 }` |
| `cache-on-write` | `cache` is on a call that changes data (anything but GET, HEAD, OPTIONS, or POST with `read: true`) | Remove `cache`, or mark a query-only POST `read: true` |
| `cache-not-shared` | a vendor call has `cache` but no other script makes the same call with `cache` | Cache the script's whole answer with `export const cache = { ttl }` instead |
| `script-parse` | a script is not valid JavaScript, so it cannot be checked | Fix the syntax error |

Two calls count as the same when the method and URL match, ignoring the query string and treating every `${…}` in the URL as a placeholder; a URL built at runtime cannot be compared and fails `cache-not-shared`.

**Warnings** print but never fail:

| Warning | Means |
|---|---|
| `answer-cache-on-write` | `export const cache` on a script that writes; its answers are never stored |
| `answer-cache-reads-headers` | the script reads `context.request.headers`, which a cached script does not get |
| `cache-ttl-capped` | the ttl is above 48 h; the runtime stores for at most 48 h |

**How it is enforced**

- **Locally:** `uip is connectors builder validate`. Errors fail validation, and warnings are listed.
- **Connector repos, CI:** the unit tests step in periodic-workflows, which a connector repo gets with `./scripts/build`. Errors fail the PR check, and warnings are printed.
- Both print `<file>:<line>:<col> <rule> <message>`, and there is no ignore list.

## Worked example: Slack

Slack's v4 connector caches its three lookup lists the way v3 did: **ListUsers**,
**ListChannels** and **ListPublicChannels** each declare `export const cache = { ttl: 172800 }`
(48 h). Each list is made by one script only, so none of their `intsvc.http` calls carries
`cache`, and each page is its own entry.

**Send a message to a user by email** is a write, so it has no `export const cache`. Its
`users.lookupByEmail` read is also made by Get User by Email, so it could take `cache` in
both scripts; Slack leaves it uncached because v3 never cached it. Had it been cached, it
would read:

```js
const user = await intsvc.http({ method: "GET", url: "/users.lookupByEmail", query: { email }, cache: { ttl: 3600 } });
if (!user.body?.ok) throw new Error(`users.lookupByEmail failed: ${user.body?.error}`);
```

in **both** scripts, with the same method and url, or `validate` fails it with `cache-not-shared`.

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
  inline script, so every run is live and `--refresh` is not needed.
- **Once the script is published, test the caching** with `--script-ref`: run the same call twice (the second is a hit), then once with
  `--refresh`. Confirm a hit from the vendor's own request count, not from the
  response, which looks the same.
- **Only a miss costs budget**: its `intsvc.http` calls count against the 4-call run
  budget; a hit costs none.
- **Say in the report** which reads or answers are cached, with the layer and `ttl`.
