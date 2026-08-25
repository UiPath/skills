# Hooks Reference

Hooks are JavaScript files that transform requests before they hit the vendor
(`preRequest`) or transform responses before returning to the caller (`postRequest`).

## Decide first: hook or built-in?

A hook is JS you maintain forever, run in a sandboxed JS engine. **Reach for one only when no
declarative feature does the job** — across shipped connectors the largest category of hooks
(static headers, constant query params, one-line response unwraps) is avoidable. Check this
table first:

| You want to… | Use this built-in (NO hook) | Write a hook ONLY when… |
|---|---|---|
| Add a constant/credential header (`Authorization: Bearer`, `Accept`) | `type:"value"` param + `${configuration.<key>}`, or `type:"configuration"` for a 1:1 map — [element-json.md](element-json.md) §"Value interpolation" | the value is *computed* (a signature, JWT-derived id, conditional on input) |
| Send a constant query param (`api-version`, `format=json`) | `type:"value"` query param — [element-json.md](element-json.md) §"Static / constant query parameters" | the param's presence/value depends on input |
| Per-connection host / region / instance in a URL | `{placeholder}` in the URL + auto-seeded config — [configuration.md](configuration.md) §"Templated (per-instance / per-region / per-workspace) hosts" | the host must be *derived* from a token/response and validated |
| Return the inner list from a wrapper (`{data:[…]}`, `{value:[…]}`) | `rootKey` (`activity create --root-key`) — [element-json.md](element-json.md) §resources[] | the reshape flattens, computes, or joins fields |
| Wrap the request body (`{…}` → `{"contact":…}`) | `requestBodyRoot` — no builder flag; see [element-json.md](element-json.md) §Expressions | the body is restructured by input value |
| Rename a list/filter/page param (or any param) to the vendor's name | `--filter-param` / `--page-size-param` / `--offset-param` (generated list params), else `activity param create --vendor-name` — [element-json.md](element-json.md) §resources[] | the value must be transformed, not just renamed |
| Standard offset / cursor / page pagination | pagination preset ([configuration.md](configuration.md) §"Pagination keys") + `activity create --pagination-type` / `--next-page-key` (`paginatorVersion` is top-level — [element-json.md](element-json.md)) | the cursor is derived from the payload with stateful logic |
| Verify credentials at connect time | `provisionAuthValidation` system resource — [system-resources.md](system-resources.md) §provisionAuthValidation | only to ADD a postRequest hook for a *computed* `connection_identity` or a custom vendor-error message — never to replace the check |
| Show a connection's display name from a plain response/config field | `connection.identity.lookup.key` config = the field's path (in the base preset; add via `state patch` if absent) — no hook | the identity must be *computed/combined* from several values |

If the third column applies — or your need is in the next list — a hook is the correct tool.

## Hooks that earn their keep

These genuinely need JS — no declarative feature expresses them (request-side → `preRequest`,
response-side → `postRequest`). Each is a real shipped pattern:

- **Delimited-string ↔ JSON** — CSV recipients → `[{emailAddress}]`, `name:value;` pairs → arrays, a comma list → a typed object (often with input validation).
- **Query-language assembly** — build JQL / SOQL / CEQL / OData `$filter` (or dialect SQL) from several typed params.
- **Conditional body reshape by value** — enum label → vendor code, `field` → `field@odata.bind`, flat fields → nested arrays.
- **Multipart / upload-session / MIME assembly** — create-upload-session then hand off the URL; file-vs-`urlSource` dual mode.
- **Multi-call orchestration** — a secondary call via `require('axios')`, a thread→run→poll state machine, read-modify-write. Chains via `request_previous_response`.
- **Object-discovery metadata synthesis** — vendor field schema → typed UiPath field metadata (`type`/`format`/`mask`/`enum`) at runtime.
- **Connection facts derived from a token/response** — instance/base URL, org/cloud/tenant id (JWT decode), validated and persisted. Recipe below.
- **`connection_identity` (computed)** — `done({connection_identity: name})` when the display name must be built/combined; a plain field uses the `connection.identity.lookup.key` config (no hook).
- **Context-dependent error rewriting** — a raw 4xx → actionable guidance ("wrong region — verify .com/.in/.eu"), or eventual-consistency → retry. (NOT a bare pass-through.)
- **Conditional status-code mapping** — 304→empty 200, 409→200, a 202 async callback.
- **Stateful polling cursors** — per-entity token maps, delta-link self-healing, last-id cursors. Beyond the pagination preset.
- **Vendor quirks no flag covers** — empty-body / strip `Content-Type`, path `decodeURIComponent`, custom date formats, dynamic signatures (RS256 JWT), deeply-nested array→object hoist (find-by-attribute), chunked/streamed response reassembly.

## Recognizing an avoidable hook

Patterns shipped connectors hand-wrote when a built-in (table above) would do — delete or never add:

- **Anything in the decision table's left column** — plain response unwrap (`response_body.value`/`.data`, the biggest cluster), static/credential header, constant query param, host templating, body wrap, param rename.
- **Constant body fields** (`enableAutoReply:false`) → a `type:"value"` param with `vendorType:"bodyField"`.
- **Bare error pass-through** (`if(response_iserror){done();return;}` with nothing after) — delete it; the runtime already surfaces vendor errors.
- **The same response transform copied across resources** (e.g. de-prefixing Graph `@odata.*` keys — itself hook-only: the builder has no declarative response-key rename) — make it one `--global` hook (see §Naming).

## Authoring a hook

Use `uip is connectors builder activity hook create` (NOT a standalone `hook create`). It writes
the `.js` under `hooks/` and registers it in element.json unless `--no-auto-register`.

**You write the hook body; the CLI just places and registers it** — there are no per-shape
scaffold flags. Author the `.js` (the decision table above + `activity hook create --help`, which
lists the in-scope vars and the `done()` contract, give you everything), then attach it:

```bash
# resource hook from an agent-written JS file
uip is connectors builder activity hook create --resource-name accounts --method GET \
  --hook-type postRequest --custom-code-file ./accounts-postRequest.js

# global hook
uip is connectors builder activity hook create --hook-type preRequest --global \
  --custom-code-file ./global-pre.js
```
Scope with `--resource-name` + `--method`, or `--global`; `--hook-type preRequest|postRequest`;
supply the body with `--custom-code-file <path>` (or `--custom-code <js>`). With no body it writes
a minimal editable stub. Run `activity hook create --help` for the rest (`--context-params`, `--no-auto-register`).

## Where they live

Files in `app/element/hooks/*.js`; registered in element.json `resources[].hooks[]`
(resource-level) or the top-level `hooks[]` (`--global`).

## Execution order

1. Global preRequest → 2. Resource preRequest → [vendor call] → 3. Resource postRequest
→ 4. Global postRequest. Global hooks always run, even when resource hooks exist.

## Hook reference object

```json
{"mimeType": "application/javascript", "type": "preRequest", "bodyOrRef": true, "ref": "resource-accounts-GET-preRequest.js", "contextParams": "request_vendor_body,configuration"}
```
`mimeType` (always `application/javascript`), `type` (`preRequest` / `postRequest`),
`bodyOrRef` (always `true` — the hook body lives in the referenced file, not inline), `ref`
(filename in `hooks/` — the canonical link), `contextParams` (comma-separated context vars).

**`contextParams` is the runtime binding allow-list** — a variable is injected only if it is listed,
so a wrong list means the vars your code reads come back `undefined` (a silent break). **You don't
manage it:** `activity hook create` derives it from your hook body, binding exactly the variables the
code references. Pass `--context-params` only as an escape hatch — to add `multipart_hook_context_items`
(opt-in; never auto-injected) or to deliberately override the derived set.

## Naming

`activity hook create` derives the filename. Resource:
`resource-{Resource}-{METHOD}-{preRequest|postRequest}.js`; global:
`global-preRequest.js` / `global-postRequest.js`. Each resource+method+phase maps to its own
file — you cannot point two resources at one shared file, so when two resources need the same
logic you copy it. When ONE transform should apply to every request/response (and is safe to run
on all of them — else guard it inside the hook), write it once as a `--global` hook instead of copying.

## JS engine (Denali)

Hooks run in Udon's **Denali** engine, which supports modern JS — shipped hooks freely use
optional chaining (`?.`), nullish coalescing (`??`), `async`/`await`, and `require()` for a small
module set: `axios` (secondary HTTP calls — the basis of multi-call orchestration), `crypto`, `url`,
`querystring`, `util`, `buffer`, `zlib`, `lodash`, `jmespath`, `moment` (the full menu prints in
`activity hook create --help`). Match the surrounding connector's style. **Every code path MUST end
with an explicit `done()`** (or `done({...})`) — a hook returns through that call, not via `return`.

## Context vars (what's in scope)

A hook reads a fixed set of variables and returns via `done({...})` — never `return`, on **every**
path. *read* = readable input; *read/write* = readable AND returnable via `done()`; *done()-only* =
NOT injected (you can't read it; it only has meaning when returned, and needs no `contextParams`
entry). The full per-variable contract is in `activity hook create --help`; the commonly used set:

**preRequest**

| var | use | notes |
|---|---|---|
| `request_body_map` | read | the curated request body **as a map** — read fields directly (`request_body_map.group`), no `input[0]` wrapper |
| `request_parameters`, `request_headers`, `request_path_variables` | read | the incoming call |
| `request_expression` | read | CEQL `where` → `[{attribute,value,operator}]` |
| `request_previous_response` | read | predecessor's response in a chained resource |
| `configuration` | read | instance config map — **read-only in preRequest** |
| `request_vendor_body` | read/write | what's sent to the vendor (string on read; list\|map\|string on write) |
| `request_vendor_parameters`, `request_vendor_headers`, `request_vendor_method` | read/write | what's sent to the vendor |
| `request_vendor_path` | read/write | what's sent; **a value starting with `http` becomes the full request URL** |
| `request_root_key`, `multipart_hook_context_items` | read/write | nest the body / multipart items |
| `continue: false` | done()-only | skip the vendor call — **the postRequest hook still runs** |
| `response_body` / `response_status_code` / `response_error_message` | done()-only | short-circuit a response without calling the vendor |

**postRequest**

| var | use | notes |
|---|---|---|
| `response_body` | read/write | the parsed vendor response — **read it here**, and return it to reshape |
| `response_iserror` | read | `true` unless HTTP **200–207**; read-only (returning it does nothing) |
| `response_body_raw`, `response_headers`, `response_status_code`, `response_root_key` | read/write | |
| `request_*`, `request_previous_response` | read | values as sent to the vendor |
| `configuration` | read/write | **writable here** — persist derived per-connection values (recipe below) |
| `multipart_hook_context_items` | read/write | |
| `response_error_message` | done()-only | converts the call to an error (status from `response_status_code`, else 400) |
| `connection_identity` | done()-only | set the connection's display name (honored in **both** phases) |
| `metadata_merge` / `merge_objects` | done()-only | object-discovery resources only |

`configuration` is the one var whose write-ability differs by phase (read-only pre, writable post): a
preRequest `configuration` write has no effect — persist derived per-connection values in a
postRequest hook (recipe below).

## Pattern: base URL (or any per-connection value) derived from a token response

Some vendors return the instance/base URL only in the token response (Salesforce
`instance_url`). There is NO vendor-specific base-url flag — `init --base-url` is static.
The default OAuth exchange isn't directly hookable, so author a system resource to hang the
hook on (`auth system create`): an `oauthOnTokenExchange` override (for a field in the token
response) or an `onProvision` resource (for a value fetched by a follow-up authenticated call) —
see [system-resources.md](system-resources.md). Its postRequest hook reads the value, VALIDATES
it (https + allowlisted host), then persists it into THIS connection's config with
`done({ configuration: {…} })` — the write-back shipped connectors use for tokens. Do **NOT**
`state patch` it: that edits the connector's static default at authoring time and bakes one
org's URL into every connection. NEVER log the token.

```javascript
// postRequest on the token exchange — extract + validate instance_url, never log response_body (holds the token)
var url = response_body && response_body.instance_url;
var ok = false;
if (typeof url === 'string' && url.indexOf('https://') === 0) {  // require https
    var host = url.replace('https://', '').split('/')[0].split(':')[0].toLowerCase();
    var allowed = ['.my.salesforce.com', '.force.com'];          // SUFFIX allowlist
    for (var i = 0; i < allowed.length; i++) {
        // anchor to the END of the host so 'my.salesforce.com.evil.com' can't pass
        if (host.length > allowed[i].length &&
            host.lastIndexOf(allowed[i]) === host.length - allowed[i].length) { ok = true; break; }
    }
}
if (!ok) { done({ response_status_code: 400, response_error_message: 'invalid instance_url' }); return; }
done({ configuration: { 'base.url': url } });               // persists to THIS connection only
```
Keep secrets out of logs, output, and example commands (SKILL.md Rule 9).

## Hook hygiene

- **No `console.log`** — Denali has no logger and stray output leaks into responses. Remove it before validating.
- **No dead hooks** — delete 0-byte / no-op hook files; an unused `ref` is a `validate` and review smell.
- **No time-bomb logic** — never hard-code an expiring credential or a "remove in 3 weeks" branch; fix the auth config instead.

## See also
- [element-json.md](element-json.md), [debugging.md](debugging.md), [system-resources.md](system-resources.md)
