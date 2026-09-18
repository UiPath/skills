# The action runtime: what a script can do, and how it is run

A generated action is an **intsvc/2 script** — a flat `execute(context)` module.
It never talks to a vendor, or to Integration Service, directly. It is handed to
`uip is resources run script`, which runs it in a sandbox and brokers every
vendor call on its behalf.

There is no client/transport layer and no runner. A client layer (`interface/` +
`impl/` with plain-fetch, SDK and `uip` clients) and a `runner.ts` existed only
because the CLI route did not; execution is one command now.

## The path

```
<actionName>.js      async function execute(context) — no imports, no class, no TS
   ▲ shipped as source
uip is resources     reads the file, resolves the caller's identity from
  run script         `uip login`, and runs it (step 4)
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

`intsvc.http` is the whole surface. There are no pagination helpers: the runtime
carries no page token in or out.

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

### One page per invocation

A list script returns **one page** — the page the vendor answers with for the
query it was given. Pagination is not handled by the runtime: no token travels in
or out, and nothing concatenates pages. If a caller needs a later page, the
script has to accept the vendor's own paging parameter (`cursor`, `offset`,
`page`) as an input and pass it through in `query`. A script that walks the
cursor itself in a loop exhausts the 4-call budget on a large tenant, so do not.

## Reading the response

The command answers with the **vendor's own response**, decoded into `Data`:

```jsonc
{ "Result": "Success", "Code": "ScriptExecuted",
  "Data": { "Status": 400,         // the VENDOR's status, verbatim
            "Headers": { … },
            "Body": { "ok": false, … } } }   // the vendor's JSON, parsed
```

`Data.Body` is the vendor's payload, parsed — an array for a `list_*` script.
A **runtime refusal** (the request never reached the vendor) is relayed the same
way: `Data.Status` is then the runtime's own status and `Data.Body` its raw body
as a string, so a string body on a non-2xx status means the runtime, not the
vendor, is talking.

**The command exits 0 for any vendor answer, whatever the status.** A vendor 400
is a normal result, not a command failure. It exits 1 only when the request never
got an answer (network, login), and 3 on a bad argument — so `set -e` will not
stop you on a vendor rejection; branch on `Data.Status` and `Data.Body` yourself.

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

A runtime refusal comes back with the runtime's status and a string `Data.Body`
naming the cause. What can go wrong, and whose fix it is:

| what went wrong | fix |
|---|---|
| not a valid module / no top-level `execute` / TypeScript | the script — it must be a plain `.js` module with `execute(context)` |
| `--script-ref` unresolved or unauthorized, or `--connector-key` mismatch | the reference — check the published name and the connector key |
| credential could not be resolved (connection not Enabled, token 401) | the connection — `uip is connections list <key> --all-folders` |
| your script threw (including your own `!body.ok` guard) | read the thrown message; it is the vendor's answer, quoted |
| call/egress budget exceeded | the script — fewer `intsvc.http` calls, no paging loops |
| egress guard refused the target | the URL — it must be on the connection's allowed origin |
| CPU / wall-clock deadline | the script |
| sandbox / engine failure | not yours to fix — retry, then report |

## What the sandbox does NOT have

The generated file IS what the sandbox runs, so it obeys the sandbox's rules. It
is not TypeScript and not a class:

- **One top-level function literally named `execute`.** Nothing else is looked
  up. A class, a nested declaration, or `export { run as execute }` is refused
  by the runtime — *"script does not define an execute(context) entrypoint"*.
- **No imports.** There is no module resolution in the sandbox.
- **No TypeScript.** QuickJS rejects it outright: *"script failed to compile:
  invalid export syntax"*. Types live in the Standard resource, not the script.

No module resolution (so no `import`), no TypeScript, and no Node globals —
`Buffer`, `btoa`/`atob`, `TextEncoder`/`TextDecoder` are all absent. `JSON` and
`Uint8Array` are present. Anything needing base64 cannot be written in a script.

## What this skill does NOT ship

There is no IS client and no runner. Connections come from
`uip is connections list <key> --all-folders`; execution is
`uip is resources run script`.
