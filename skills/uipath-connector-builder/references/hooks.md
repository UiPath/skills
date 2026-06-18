# Hooks Reference

Hooks are JavaScript files that transform requests before they hit the vendor
(preRequest) or transform responses before returning to the caller (postRequest).

## Where they live
Files in `app/element/hooks/*.js` (extracted from element.json by `scripts/build`);
registered in element.json `resources[].hooks[]` (resource-level) or top-level
`hooks[]` (global). Run in Udon's **Denali** JS engine (ES5/ES6).

## Execution order
1. Global preRequest → 2. Resource preRequest → [vendor call] → 3. Resource postRequest
→ 4. Global postRequest. Global hooks always run, even when resource hooks exist.

## Hook reference object
```json
{"type": "preRequest", "mimeType": "application/javascript", "ref": "resource-accounts-GET-preRequest.js", "contextParams": "request_vendor_body"}
```
`type` (`preRequest`/`postRequest`), `mimeType` (always `application/javascript`),
`ref` (filename in `hooks/` — the canonical link), `bodyOrRef` (legacy alternative),
`contextParams` (comma-separated context vars), `isLegacy` (false).

## Naming
`{scope}-{resource-path}-{METHOD}-{hookType}.js`. Resource: `resource-{path}-{METHOD}-{preRequest|postRequest}.js`.
Global: `global-preRequest.js`, `global-postRequest.js`. Path derived by stripping
`/hubs/{hub}/` and joining segments with `-`. **One hook file per
resource+method+phase** — duplicate logic rather than sharing a file.

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

// postRequest — wrap object in array
done({ response_body: [response_body] });
```

## See also
- [element-json.md](element-json.md), [debugging.md](debugging.md)
