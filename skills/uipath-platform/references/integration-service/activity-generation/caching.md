# Caching vendor reads in a generated script

A script can keep a computed value and serve the next call from it, with
`intsvc.cache.remember`:

```js
const fields = await intsvc.cache.remember(`describe@1:${name}`, { ttl: 86400 }, async () => {
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
- **Writes stay outside `fill`.** A `fill` that made a PUT, PATCH or DELETE, or a
  POST not marked `read: true` on `intsvc.http`, is not stored (except `replay`
  below). Mark a POST `read: true` only when it is a query API with no side effect.
- **Return the projection, not the raw body.** Keep the fields the script uses;
  the entry is the stored value.

## Shared or per script

| | shared (default) | `perScript: true` |
|---|---|---|
| key | connection + revision + `name` | the same, plus this script version's digest |
| who reads it | every published script on the connection that uses the same `name` | this script version only; editing the script ends it |
| name | versioned: `describe@1:${object}` | no version needed |
| use for | data several scripts reuse: Salesforce `describe@1:{object}` for metadata discovery, a user looked up by email | a whole answer: one page of a list, the object list, metadata discovery output |

A shared entry is keyed on `name` alone, never on the `fill` code, so the name is the
contract:

- **Put a version in a shared name** (`describe@1:${object}`, `user-by-email@1:${email}`)
  and bump it whenever the stored value's shape changes. Editing `fill` does not start
  a new entry; an old-shape entry lives until its TTL.
- **Use a descriptive prefix.** Any published script on the connection that uses the
  same name shares the entry and can overwrite it, so a generic `list` collides.
- **Every input that changes the value goes in the name.** `fill` copies in different
  scripts need not be identical, but each must store the same shape under that name.

A script that lives in a connector repo (`app/element/v4/scripts/*.js`) is checked at
design time by `uip is connectors builder validate --connector-dir <dir>`, check
`script-cache-names`. `perScript` calls are ignored; every shared name must:

- **Start with `<base>@<version>:`** (`` `user-by-email@1:${email}` ``). A name without
  one is an error.
- **Use a base no other script uses, unless declared.** Intentional sharing goes in
  `app/element/v4/cache-names.json`, listing exactly the scripts that use the base
  (file names without `.js`): `{ "user-by-email": ["GetUserByEmail", "SendMessageToUser"] }`.
  An undeclared shared base is an error; a declaration naming a script that no longer
  uses it, or a base used by one script or none, is a warning.
- **Carry one version across its scripts.** When the stored shape changes, bump the
  version in every script that shares the base, together; mixed versions are an error.

Fix `script-cache-names` errors before publishing the connector.

Inline scripts (`--inline-script`) cache in their own namespace and per caller: an
inline script never sees a published script's entries, nor another caller's inline
entries. With no caller identity the cache is off for that run.

Editing or re-authenticating the connection starts fresh entries.

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
| `cache_key=<value>` | `--query cache_key=<value>` | reaches the script on `context.request.query`; only a script that builds a name from it uses it |

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
