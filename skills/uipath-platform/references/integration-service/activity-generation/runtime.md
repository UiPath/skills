# The action runtime: what a script can do, and how it is run

A generated action is an **intsvc/2 script** — a flat `execute(context)` module.
It never talks to a vendor, or to Integration Service, directly. It is handed to
`uip is resources scripts execute`, which runs it in a sandbox and brokers every
vendor call on its behalf.

There is no client/transport layer and no runner. A client layer (`interface/` +
`impl/` with plain-fetch, SDK and `uip` clients) and a `runner.ts` existed only
because the CLI route did not; execution is one command now.

## The path

```
<actionName>.js      async function execute(context) — no imports, no class, no TS
   ▲ shipped as source
uip is resources     reads the file, resolves the caller's identity from
  scripts execute    `uip login`, and runs it (step 4)
   │
runtime              compiles the script in a QuickJS-WASM sandbox, calls
   │ brokers         execute(context), and brokers every intsvc.http call:
   ▼ each call       egress guard + credential injection + metering, per call
vendor
```

All of a script's `intsvc.http` calls happen within ONE run and share one budget.
**The credential never reaches the script** — it is injected at the transport
edge, outside the sandbox.

## The `context` a script receives

```js
context = {
  request: { body, query, headers },  // the INBOUND call — data to read
  connectionConfiguration,            // the connection's NON-SECRET config (base.url, …)
  connectionId, connectorKey,
}
```

Inputs arrive on `context.request.body`, already decoded. There is no typed input
parameter and `context.request` carries **no `method`/`url`** — the script names
its own vendor target. Connection settings are read off
`context.connectionConfiguration?.['key']`; secrets are stripped before the
script sees them.

## The `intsvc` surface

| capability | kind | what it does |
|---|---|---|
| `intsvc.http(request)` | brokered egress | one credential-injected, egress-guarded vendor call. Costs one of the 4 per-request calls |
| `intsvc.decodePageToken(headers)` | pure | decodes an inbound `elements-next-page-token` into the query params to merge. `undefined` on page one |
| `intsvc.handlePagination(response, tokenKeyPath, pageParamName)` | pure | stamps the outgoing `elements-next-page-token`, keyed by the VENDOR's paging parameter. Returns the response unchanged when there is no next page |

The two pagination helpers cost no budget and reach nothing. They are
host-provided rather than something a script writes because the sandbox has **no
base64 primitive at all** — no `Buffer`, no `btoa`/`atob`, no `TextEncoder` — so
a guest cannot encode or decode the token envelope.

### `intsvc.http` — request and response

```js
intsvc.http({ method, url, query?, headers?, body? })   // → { status, headers, body }
```

| field | rule |
|---|---|
| `url` | a RELATIVE url resolves UNDER the connection's `base.url`, **its path included** — Slack's `base.url` `https://slack.com/api` means `"/users.list"` hits `…/api/users.list` |
| `query` | `{ k: v }` — serialized for you; prefer it over hand-encoding |
| `headers` | `{ name: value }` or `[{ name, value }]` (ordered, duplicates preserved) |
| `body` | an object is sent as JSON; a string is sent as its UTF-8 bytes |

| response field | rule |
|---|---|
| `status` | the VENDOR's status, verbatim — **a 4xx/5xx is a NORMAL RETURN, not a throw** |
| `headers` | `[{ name, value }]` — index with `.find(h => h.name.toLowerCase() === "x")` |
| `body` | the VENDOR's own body, envelope and all — nothing is unwrapped for you |

**The vendor payload is `resp.body`, not `resp`.**

### The pagination contract

**One invocation = one page.** The token rides the `elements-next-page-token`
header in and out; the CONSUMER loops by echoing it back, and a response with no
such header means the list is exhausted. A script that walks the cursor itself
breaks that contract, hides pagination from the surfaces, and exhausts the
4-call budget on a large tenant.

The envelope is keyed by the vendor's own paging parameter (`{"cursor":"…"}`,
`{"offset":200}`) rather than a generic `nextPageToken`, which is what makes the
inbound step a plain `Object.assign(query, … ?? {})` with no per-vendor
branching. Omitting the parameter name falls back to the generic key, preserving
the older udon wire format.

One consequence worth knowing: stamping a header MUTATES the response, so the
runtime re-encodes it instead of relaying the vendor's bytes byte-verbatim. That is
unavoidable — the header is the payload — and it is detected correctly, so the
header is never silently dropped.

## Reading the response

The command answers with the **vendor's own response**, decoded into `Data`:

```jsonc
{ "Result": "Success", "Code": "ScriptExecuted",
  "Data": { "Outcome": "vendor",   // `proxy_error` ⇒ it never reached the vendor
            "Status": 400,         // the VENDOR's status, verbatim
            "Headers": [ … ],
            "Body": "{\"ok\":false,…}",   // a STRING — parse it yourself
            "Diagnostics": { "VendorCallCount": 1, "ScriptCpuMs": 14,
                             "ScriptDigest": "sha256:…" } } }
```

**Read `Data.Outcome`, not the status** — a vendor 404 and an infrastructure
failure can both be 404. `Diagnostics` is your evidence the script actually ran,
and `ScriptDigest` identifies the exact source that ran, so it matches the file
you shipped.

**The command exits 0 for any vendor answer, whatever the status.** A vendor 400
is a normal result, not a command failure. It exits 1 only when the request never
reached the vendor, and 3 on a bad argument — so `set -e` will not stop you on a
vendor rejection.

Returning an `intsvc.http` result **untouched** relays the vendor's original
bytes verbatim (status, ordered/duplicate headers, body). Returning a fabricated
object re-encodes it — the right call for a list whose envelope is noise, the
wrong one when fidelity matters.

## Detecting vendor failure

A vendor error does not throw, so the script must check it — **using that
vendor's own success signal**, which differs by API:

| vendor convention | the check | who does this |
|---|---|---|
| status codes (the REST norm) | `if (resp.status >= 400)` | Jira, most REST APIs |
| in-band flag on HTTP 200 | `if (!resp?.body?.ok)` | Slack, Twitter-family |
| error object on the body | `if (resp?.body?.error)` | MS Graph (with a 4xx) |

```js
// Slack-family — fails with HTTP 200 + { ok: false }, so a status check MISSES it
if (!listed?.body?.ok) {
  throw new Error('Failed to retrieve users list' + JSON.stringify(listed?.body ?? listed?.raw));
}

// REST-conventional — Jira has NO `ok` field, so an `ok` check throws on SUCCESS
if (search.status >= 400) {
  throw new Error('Jira search failed: ' + search.status + ' ' + JSON.stringify(search?.body));
}
```

> **Do not copy the guard from an example written for another vendor.** It is the
> single easiest way to break a generated action: `!body.ok` against Jira throws
> on every successful call, and a bare status check against Slack treats
> `{ ok: false }` as success. Read the vendor's docs for how it reports failure,
> then write the matching check. When unsure, check **both** — a status guard
> plus an `ok`/`error` guard is always safe.

## Failure map

When `Data.Outcome` is `proxy_error` the command fails with an `ErrorCode`:

| what went wrong | `ErrorCode` |
|---|---|
| not a valid module / no top-level `execute` / TypeScript — **or inline source is not permitted** | `script_invalid` |
| `--script-ref` unresolved or unauthorized, or `--connector-key` mismatch | `script_artifact_missing` |
| credential could not be resolved (connection not Enabled, token 401) | `credential` |
| your script threw (including your own `!body.ok` guard) | `script_runtime` |
| call/egress budget exceeded | `script_quota` |
| egress guard refused the target | `guard_block` |
| CPU / wall-clock deadline | `script_deadline` |
| sandbox / engine failure | `script_infra` — the only one that is not yours to fix |

`script_invalid` has two very different causes, and the message does not always
separate them: a genuine syntax error, or a runtime that will not accept inline
source at all. If the script compiles locally, suspect the second.

## What the sandbox does NOT have

The generated file IS what the sandbox runs, so it obeys the sandbox's rules. It
is not TypeScript and not a class:

- **One top-level function literally named `execute`.** Nothing else is looked
  up. A class, a nested declaration, or `export { run as execute }` fails with
  `script_invalid` — *"script does not define an execute(context) entrypoint"*.
- **No imports.** There is no module resolution in the sandbox.
- **No TypeScript.** QuickJS rejects it outright: *"script failed to compile:
  invalid export syntax"*. Types live in the Standard resource, not the script.

No module resolution (so no `import`), no TypeScript, and no Node globals —
`Buffer`, `btoa`/`atob`, `TextEncoder`/`TextDecoder` are all absent. `JSON` and
`Uint8Array` are present. Anything needing base64 has to be provided by the host
as a capability, not written in the script — which is exactly why
`handlePagination` / `decodePageToken` exist above rather than living in each
generated action.

## What this skill does NOT ship

There is no IS client and no runner. Connections come from
`uip is connections list <key> --all-folders`; execution is
`uip is resources scripts execute`. Both halves of the pagination transport are
host-provided because the sandbox has no base64 primitive — see
[The pagination contract](#the-pagination-contract).
