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
  const { limit, cursor } = context.request.body ?? {};
  const listed = await intsvc.http({ method: "GET", url: "/users.list", query: { limit, cursor } });
  if (listed.status !== 200 || listed.body.ok === false) throw new Error(`users.list failed: ${listed.status} ${listed.body.error ?? ""}`);
  listed.body = listed.body.members;
  return listed;
}
```

A hit makes no vendor call and costs nothing against the script's call or egress budget.
The runtime proxy's `docs/intsvc-sdk.md` §3a is the live contract for limits and
metrics; follow it where this page differs.

## Which layer

1. Is the same read (method + URL) made by two or more scripts of the connector?
   Yes: `cache` on that `intsvc.http` call, in **every** script that makes it, with the
   same method and url template. A describe or user lookup several actions share.
2. Otherwise, does the script's answer depend only on its method, path, query and body,
   and make no write? Yes: `export const cache`. One page of a list, the object list.
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

**A returned `ok: false` body is cached**, because the run completed and the answer was
2xx. Throw on every vendor-reported failure, as Slack's `ok: false` above, so it is not
stored.

## What the key holds

A Layer A key is the tenant, connection, method, URL (query merged and sorted) and **every
header the script sets**. Anything that changes the answer must be in the URL, the query
or a header; a header you set but do not mean to vary on splits the cache, so leave it
off. A call carrying `authorization`, `cookie`, `range` or a conditional header is not
cached.

A Layer B key is the connection, the script and connector versions, and the inbound
method, path, query and body. It does **not** include inbound headers, so a script with
`export const cache` gets no `context.request.headers`: do not write one that varies on
them.

Nothing about the credential is in either key, so the connection's cache is dropped when
Udon invalidates it on re-auth, edit or delete. Correctness after a re-auth depends on
that call being deployed; until it is, an entry can outlive a re-auth for its TTL.

## What the caller controls

| input | CLI flag | effect |
|---|---|---|
| `cache_data=uncache` on the inbound request | `--refresh` | skips the read in both layers and stores the new answer |
| `cache_data=bypass` on the inbound request | `--no-cache` | neither reads nor stores, in both layers |

`cache_data` is removed before the script sees `context.request.query`. Inline scripts
(`--inline-script`) cache like published ones, in their own namespace per caller; with
no caller identity the cache is off for that run.

## Checked before you publish

In a connector repo (`app/element/v4/scripts/**/*.js`), `uip is connectors builder
validate --connector-dir <dir>` and the periodic-workflows pre-merge check apply the
same rules. Every finding fails; there is no ignore list.

| rule | fails when |
|---|---|
| `cache-for-removed` | an `intsvc.http` call still uses the old per-call cache option; use `cache: { ttl }` |
| `cache-shape` | `cache` has a key other than `ttl`, no `ttl`, or a literal `ttl` that is not a positive number; `export const cache` is not an object literal |
| `cache-on-write` | `cache` on a method other than GET, HEAD, OPTIONS, or a POST with `read: true` |
| `cache-not-shared` | a call with `cache` has a non-literal `method`, a `url` that is not a literal or template, or its method + url template is cached in fewer than two script files |
| `script-parse` | a v4 script does not parse, so its cache use cannot be checked |

If `cache-not-shared` fires, either add `cache` to the other scripts that make the read,
or cache this script's answer with `export const cache = { ttl }`.

## Testing

- **While iterating, run with `--no-cache`** so nothing work-in-progress is stored.
  `--refresh` is not a substitute: it still replaces the entry with the new answer.
- **Once the script is right, test the caching** with `--inline-script` or
  `--script-ref`: run the same call twice (the second is a hit), then once with
  `--refresh`.
- **Only a miss costs budget**: its `intsvc.http` calls count against the 4-call run
  budget; a hit costs none.
- **Say in the report** which reads or answers are cached, with the layer and `ttl`.
