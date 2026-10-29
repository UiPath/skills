# Caching vendor reads in a generated script

A script can keep a computed value and serve the next call from it, with
`intsvc.cache.remember`:

```js
const fields = await intsvc.cache.remember(`describe:${name}`, { ttl: 86400 }, async () => {
  const res = await intsvc.http({ method: "GET", url: `/services/data/v62.0/sobjects/${name}/describe` });
  if (res.status !== 200) throw new Error(`describe ${name} failed: ${res.status}`);
  return res.body.fields.map(({ name, type, label, nillable, referenceTo }) => ({ name, type, label, nillable, referenceTo }));
});
```

```js
const page = await intsvc.cache.remember(
  `users.list:${cursor ?? ""}:${limit}`, { ttl: 900, perScript: true },
  async () => {
    const res = await intsvc.http({ method: "GET", url: "/users.list", query: { limit, cursor } });
    if (res.status !== 200 || res.body.ok === false) throw new Error(`users.list failed: ${res.status} ${res.body.error ?? ""}`);
    return { members: res.body.members.map(({ id, name }) => ({ id, name })), next: res.body.response_metadata?.next_cursor };
  },
);
```

`remember(name, { ttl, perScript?, replay?, refresh? }, fill)`. A hit returns the
stored value: no vendor call, and nothing charged to the script's call/egress
budget. A miss runs `fill`, stores what it returns (JSON, at most 8 MiB) and
returns it. The runtime proxy's `docs/intsvc-sdk.md` is the live contract for the
options and limits; follow it where this page differs.

## What goes in `fill`

- **Throw on every vendor failure**, including a 2xx body that reports one (Slack's
  `ok: false`). A throw stores nothing; a return is stored, whatever it holds.
- **Everything that shapes the value goes inside `fill`**: API version, URL,
  projection. The entry is keyed on `fill`'s source, not on the values it closes
  over, so an outer value (a variable, `context`) that `fill` reads and `name` does
  not carry is invisible to the key: two callers with different values share one
  entry. Read outer values only when `name` carries them (`name` in the describe
  example), and nothing else.
- **Writes stay outside `fill`.** A `fill` that made a PUT, PATCH or DELETE, or a
  POST not marked `read: true` on `intsvc.http`, is not stored (except `replay`
  below). Mark a POST `read: true` only when it is a query API with no side effect.
- **Return the projection, not the raw body.** Keep the fields the script uses;
  the entry is the stored value.

## Shared or per script

| | shared (default) | `perScript: true` |
|---|---|---|
| key | connection + revision + hash of `fill` source + `name` | the same, plus this script version's digest |
| who reads it | every script on the connection whose `fill` source is identical | this script version only; editing the script ends it |
| use for | data several scripts reuse: Salesforce `describe:{object}` for metadata discovery, record lists and record writes | a whole answer: one page of a list, the object list, metadata discovery output |

Inline scripts (`--inline-script`) cache too, in their own namespace: an inline script
never reads or overwrites a published script's entries, and the reverse. Inline
scripts share with each other by identical `fill` text, and `perScript` is keyed by
the inline source's digest.

Editing `fill` starts a new entry by itself, so no version suffix is needed in
`name`; a new name is still fine for a deliberate cut-over. Editing or
re-authenticating the connection also starts fresh entries.

**`name`** carries every input that changes the value: object name, cursor, limit,
team, types, normalized email. At most 512 characters. A missing input in the name
serves one caller another caller's answer.

## When to cache

Cache what changes slowly and callers repeat: the list behind a lookup field
(channels, users, projects), and object or field discovery. Do not cache live data
(record lists, search results) as a whole; cache the lookups inside them, such as
the field schema the list needs. Do not cache anything a user edits and reads back.

`ttl` is required, in seconds, capped at 48 h (`172800`). Pick it from how stale the
data may be, not from how expensive the call is:

| data | TTL |
|---|---|
| object and field schemas | 6-24 h (`21600`-`86400`) |
| people, channels, groups, projects | 15 min-1 h (`900`-`3600`) |

## What the caller controls

| input | CLI flag | effect |
|---|---|---|
| `cache_data=uncache` on the inbound request | `--refresh` | every `remember` in the run skips the read and replaces its entry |
| `cache_data=bypass` on the inbound request | `--no-cache` | every `remember` in the run just runs `fill`: no read, no write |
| `cache_key=<value>` | `--cache-key <value>` | reaches the script on `context.request.query` |

`refresh: true` on one call does the same for that call alone.

`replay: true` (requires `perScript`) is for one case: an invoke that writes and
must not repeat under the same caller `cache_key` (Agent2Agent `/invokeAgent`,
Power Automate `/run_flow`). Build `name` from the caller's `cache_key` and use
`ttl: 172800`; a repeat returns the first answer without sending again. Take
`cache_key` out of any query sent to the vendor.

```js
const { cache_key: cacheKey, ...query } = context.request.query ?? {};
const invoke = () => intsvc.cache.remember(`invoke:${cacheKey}`, { ttl: 172800, perScript: true, replay: true }, async () => {
  const res = await intsvc.http({ method: "POST", url: "/v1/message:send", query, body: context.request.body });
  if (res.status >= 400) throw new Error(`message:send failed: ${res.status}`);
  return { status: res.status, body: res.body };
});
```

Never return the raw `intsvc.http` result from `fill`: the stored value is replayed to
every caller for the TTL, vendor headers (`Set-Cookie`, rate-limit counters, request
ids) included. Build `{ status, body }`, plus pagination headers for a list.

Use it only when `cache_key` is present; without one, send the write plainly.

## Testing

- **While iterating, run with `--no-cache`** (`cache_data=bypass`) so nothing
  work-in-progress is stored. `--refresh` is not a substitute: it still replaces the
  entry with the new value.
- **Once the script is right, test the caching** with `--inline-script` or
  `--script-ref`: run the same call twice (the second is a hit), then once with
  `--refresh`.
- **Only a miss costs budget**: its `fill`'s `intsvc.http` calls count against the
  4-call run budget; a hit costs none.
- **Say in the report** which values are cached, with `name`, `ttl`, and whether
  `perScript` or `replay`.
