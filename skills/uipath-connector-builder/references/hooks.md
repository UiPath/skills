# Hooks Reference

Hooks are JavaScript files that transform requests before they hit the vendor
(`preRequest`) or transform responses before returning to the caller (`postRequest`).

## Authoring a hook

Use `uip is connectors builder activity hook create` (NOT a standalone `hook create`).
It writes the `.js` file under `hooks/` and registers the reference in element.json unless
`--no-auto-register`.

```bash
# resource-scoped post hook (unwrap a response array)
uip is connectors builder activity hook create --resource-name Account --method GET \
  --hook-type postRequest --wrap-array

# global pre hook from a JS file
uip is connectors builder activity hook create --hook-type preRequest --global \
  --custom-code-file ./my-hook.js
```
Key flags: `--resource-name` + `--method` (omit both with `--global`); `--hook-type
preRequest|postRequest`; `--custom-code <js>` or `--custom-code-file <path>` (raw body,
overrides the template); `--description`; `--context-params <list>`; scaffold helpers
`--transform-path` / `--transform-params` / `--transform-headers` (preRequest),
`--transform-body` (either), `--wrap-array` (postRequest); `--no-auto-register`; `--global`.

## Where they live

Files in `app/element/hooks/*.js`; registered in element.json `resources[].hooks[]`
(resource-level) or the top-level `hooks[]` (`--global`). Run in Udon's **Denali** JS engine.

## Execution order

1. Global preRequest → 2. Resource preRequest → [vendor call] → 3. Resource postRequest
→ 4. Global postRequest. Global hooks always run, even when resource hooks exist.

## Hook reference object

```json
{"type": "preRequest", "mimeType": "application/javascript", "ref": "resource-Account-GET-preRequest.js", "contextParams": "request_vendor_body"}
```
`type` (`preRequest` / `postRequest`), `mimeType` (always `application/javascript`),
`ref` (filename in `hooks/` — the canonical link), `contextParams` (comma-separated
context vars), `isLegacy` (false).

## Naming

`activity hook create` derives the filename. Resource:
`resource-{Resource}-{METHOD}-{preRequest|postRequest}.js`; global:
`global-preRequest.js` / `global-postRequest.js`. **One hook file per
resource+method+phase** — duplicate logic rather than sharing a file.

## ES5/ES6 (Denali) constraints

Denali is ES5/ES6 only. NO optional chaining (`?.`), nullish coalescing (`??`),
arrow-only constructs you rely on for `this`, spread in calls, or `async`/`await`. Use
plain `var`/`function`, `&&`/`||` guards, and explicit `done()`.

## PreRequest context vars

`request_vendor_parameters`, `request_vendor_path`, `request_vendor_body`,
`request_vendor_body_map` (curated input via `input[0]`), `request_vendor_headers`,
`request_parameters` (includes `nextPage`, `pageSize`), `configuration` (all config
keys), `multipart_hook_context_items`. Return changed keys via `done({...})`; bare
`done()` passes everything through.

## PostRequest context vars

`response_body`, `response_headers`, `response_iserror`, `response_status_code`,
`request_previous_response`, `configuration`. Return via
`done({ response_body, response_status_code, response_error_message })`.

## Common patterns

```javascript
// preRequest — paginate to next page
if (request_parameters.nextPage) request_vendor_path = request_parameters.nextPage;
done({ request_vendor_path: request_vendor_path });

// postRequest — unwrap array (ES5-safe: no optional chaining)
done({ response_body: (response_body && (response_body.data || response_body.items)) || [] });

// postRequest — error pass-through
if (response_iserror) { done(); return; }

// preRequest — auth header from config
request_vendor_headers['Authorization'] = 'Bearer ' + configuration['oauth.user.token'];
done({ request_vendor_headers: request_vendor_headers });
```

## Pattern: base URL from a token-exchange response (skill-guided)

Some vendors return the instance/base URL only in the token response (e.g. Salesforce
`instance_url`). There is NO vendor-specific base-url CLI flag — only the static
`init --base-url`. To capture a dynamic one, compose a **postRequest hook on the
token-exchange/onProvision step** that reads the field, VALIDATES it, then persist it with
`state patch`. NEVER log the token or any secret.

```javascript
// postRequest on the token exchange — extract + validate instance_url, never log the token
var url = response_body && response_body.instance_url;     // do NOT log response_body (holds the token)
var ok = false;
if (url && url.indexOf('https://') === 0) {                 // require https
    var host = url.replace('https://', '').split('/')[0];
    var allowed = ['my.salesforce.com', 'force.com'];        // host allowlist
    for (var i = 0; i < allowed.length; i++) {
        if (host && host.indexOf(allowed[i]) !== -1) { ok = true; break; }
    }
}
if (!ok) { done({ response_error_message: 'invalid instance_url' }); return; }
done({ response_body: { base_url: url } });                 // pass only the validated URL onward
```
Then write the validated value into config (no secrets in the command):
```bash
uip is connectors builder state query element.json/configuration/base.url --output json
uip is connectors builder state patch element.json/configuration/base.url \
  --value '<full entry from the query, defaultValue set to the validated instance URL>'
```
Always require `https://` and a non-empty host from an allowlist before use — reject
anything else. Keep secrets out of logs, output, and example commands (see SKILL.md secret rules).

## See also
- [element-json.md](element-json.md), [debugging.md](debugging.md), [system-resources.md](system-resources.md)
