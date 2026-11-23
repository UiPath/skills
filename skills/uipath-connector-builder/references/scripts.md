# Scripts Reference (community route)

A script is one JavaScript file that makes the vendor call for a method or a lookup.
It replaces hooks on the community route. You write it; the CLI only links it.

- File: `app/element/v4/scripts/<name>.js`. The name (letters, digits, `-`, `_`) is the `scriptRef`.
- One top-level function named `execute`. No imports, no TypeScript.

```javascript
async function execute(context) {
  return await intsvc.http({ method: 'GET', url: '/v1/contacts', query: context.request?.query });
}
```

## Write a script

1. Take method, path, inputs and response shape from the vendor's API docs.
2. One script per method; one list script per lookup. Write lookups first.
3. Start from the matching pattern below.
4. Read inputs under the names the activity declares: query parameters from `query`, fields from `body`.
5. A path value (`/contacts/{id}`) is declared as a query parameter. Read it from `query` and send it the way the vendor accepts it — here, in the path.
6. Check failure with the vendor's own signal, and return the failed result.
7. For a list, return the records array and page.

## Lookups

A lookup fills a dropdown for an input that is a vendor ID (`ownerId`, `channel`): the user picks a name, the activity stores the ID.

- A lookup is a list script that returns the records array. It does no matching.
- The field or parameter names it: `reference: { scriptRef, lookupValue, lookupNames }`.
  - `scriptRef` — the list script's name
  - `lookupValue` — the record key stored as the value (`id`)
  - `lookupNames` — the record keys shown to the user (`name`)
- One list script can serve many fields, and can also be a list method's script.

## What is in scope

Use only what is listed here. Nothing else is available.

**`context` — the inbound call (read-only)**

| var | holds |
|---|---|
| `context.request.query` | parameters declared `type: query`. Values are strings |
| `context.request.body` | request fields, as the decoded JSON body |
| `context.request.headers` | inbound headers, lower-cased names. Credentials are removed |
| `context.attachments` | uploaded files, by part name: `{ name, size, contentType }`. `{}` when none |

**`intsvc` — what a script can call**

| call | use |
|---|---|
| `intsvc.http({ method, url, query?, headers?, body? })` | one vendor call, credential injected. Returns `{ status, headers, body }` |
| `intsvc.decodePageToken(text)` | reads the `nextPage` token → `{ next, pageSize }`, or `null` |
| `intsvc.setPaginationHeaders(result, { current, next, pageSize, hasMore })` | writes the paging headers onto `result` |

## `intsvc.http`

| field | rule |
|---|---|
| `url` | relative → resolved under the connection's base URL. Use the vendor's own path |
| `query` | `{ k: v }`. Never hand-encode it into `url` |
| `body` | object → JSON, string → text, an attachment → that file |
| `status` | the vendor's status. **A 4xx/5xx is returned, not thrown** |
| `headers` (response) | object, lower-cased names |
| `body` (response) | object for JSON, string for text, a download handle for a file |

Await every call. A run allows 4.

## Rules

1. **Check failure yourself, and return the failed result.**

   | vendor | failed when |
   |---|---|
   | REST status codes | `res.status >= 400` |
   | flag on HTTP 200 (Slack) | `!res.body?.ok` |
   | error object (Graph) | `res.body?.error` |

   On failure, `return res;` before any reshaping. The caller then gets the vendor's status and body.
   When the vendor's status is 200, set one first: `res.status = 400; return res;`.
   Never `throw` for a vendor failure: it becomes a 422 with the status lost and the message cut at 4 KiB.
2. **Return the `intsvc.http` result.** To reshape, change `result.body` and return `result`.
3. **A path value is a query input.** `id` arrives in `context.request.query`. Send it the way the vendor accepts it:

   | vendor takes | send |
   |---|---|
   | `/contacts/{id}` | in `url`: `` `/contacts/${encodeURIComponent(id)}` `` |
   | `/contacts.info?id=…` | in `query`: `{ id }` |
4. **Map names in the script.** Read our names, send the vendor's.

## Patterns

**By id** — `id` arrives in the query; the vendor takes it in the path
```javascript
async function execute(context) {
  const { id, ...query } = context.request?.query ?? {};
  const res = await intsvc.http({ method: 'GET', url: `/v1/contacts/${encodeURIComponent(id)}`, query });
  return res;
}
```

**Create**
```javascript
async function execute(context) {
  const res = await intsvc.http({ method: 'POST', url: '/v1/contacts', body: context.request?.body });
  return res;
}
```

**List — one page per call, records array as the body**
```javascript
async function execute(context) {
  const { pageSize: asked, nextPage, ...filters } = context.request?.query ?? {};
  const page = intsvc.decodePageToken(nextPage) ?? {};
  const pageSize = Number(page.pageSize ?? asked ?? 100);

  const res = await intsvc.http({
    method: 'GET',
    url: '/v1/contacts',
    query: { ...filters, limit: pageSize, cursor: page.next },
  });
  if (res.status >= 400) return res;

  const next = res.body.next_cursor || '';
  res.body = res.body.items ?? [];
  intsvc.setPaginationHeaders(res, { current: page.next, next, pageSize, hasMore: next !== '' });
  return res;
}
```
- The caller sends `pageSize` on the first call and `nextPage` after. Both arrive in the query.
- Read `next` before replacing `res.body`. Never loop over pages.
- No paging on the vendor side: unwrap the array and return, without the two helpers.
- A lookup script is this same list script ([Lookups](#lookups)).

**Upload** — the parameter is `type: multipart`, `dataType: file`
```javascript
async function execute(context) {
  const file = context.attachments?.file;
  return await intsvc.http({ method: 'POST', url: '/v1/files', body: file });
}
```
- You get the file's details, never its bytes.
- Use each file once, in the order sent, and use all of them.
- Do not set `content-length` or `transfer-encoding`.

**Download**
```javascript
async function execute(context) {
  const { id } = context.request?.query ?? {};
  return await intsvc.http({ method: 'GET', url: `/v1/files/${encodeURIComponent(id)}/content` });
}
```
- A file response gives `body` as a handle: `{ size, contentType }`. Return the result unchanged.
- To send it on, pass `res.body` as the `body` of the next call. Once only.

## Limits per run

| limit | value |
|---|---|
| `intsvc.http` calls | 4 |
| wall clock | 120 s |
| memory | 64 MiB |
| one request you send | 1 MiB |
| script file | 512 KiB |
| upload | 100 MiB per file, 4 files |

## Not available

`fetch`, `setTimeout`, `require`, `import`, `console`, `Buffer`, `btoa`/`atob`, `TextEncoder`.
Standard JavaScript is: `JSON`, `Map`, `Set`, `Promise`, `async`/`await`, `encodeURIComponent`.

## See also
- [v4-flow.md](v4-flow.md) — where scripts fit in the community route
