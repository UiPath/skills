# Hook Authoring Guide

Hooks are where a BYO LLM connector does its work: the **preRequest** hook turns the flavor's request into the vendor's, the **postRequest** hook turns the vendor's answer back into the flavor's response. This guide covers what is specific to LLM traffic; the builder's own help (`uip is connectors builder activity hook create --help`) lists every variable.

## Runtime

- Hooks run in Integration Service's sandboxed JavaScript engine: modern syntax (`const`, arrow functions, `?.`, `??`, destructuring, spread) and `async`/`await` work, and `require()` loads a small fixed set (`axios`, `crypto`, `url`, `querystring`, `buffer`, `lodash`, …).
- Every code path ends in `done()` or `done({...})` — a hook returns through it, not through `return`. Put `return;` after a `done()` that is not the last statement.
- Keep the resource hooks synchronous and free of secondary HTTP calls: they sit on the hot path of every product call. Do token work in the token-exchange resources instead (§"Custom token exchange"), and chain them when the exchange takes several calls (§"Chained token exchange").
- No `console.log`, ever — there is no logger and the output can leak into responses. Never place prompts, completions, headers or tokens in `response_error_message`, `response_body` errors, or `connection_identity`.
- Register each file with `uip is connectors builder activity hook create --resource-name <NAME> --method POST --hook-type preRequest|postRequest --custom-code-file <FILE>`. The builder stores it under `app/element/hooks/` and derives the `contextParams` allow-list from the variables your code reads — a variable not referenced is not injected. Re-run the command after editing the file.

## Variables you will use

**preRequest**

| Variable | Access | Use |
|---|---|---|
| `request_body_map` | read | The flavor's request as an object (may be `null` — fall back to `JSON.parse(request_body)`) |
| `request_body` | read | The same request as a string |
| `request_path_variables` | read | Path tokens, e.g. `request_path_variables['modelId']`, `['model_id']` |
| `request_parameters`, `request_headers` | read | Incoming query and headers (`alt=sse` on a Gemini stream) |
| `configuration` | read | Connection values: `configuration['base.url']`, your own config keys. Read-only here |
| `request_vendor_body` | write | The body sent to the vendor (object or string) |
| `request_vendor_headers` | write | Headers sent to the vendor (merged over the connector's header parameters) |
| `request_vendor_path` | write | Vendor path, appended to `base.url` (path prefix included); **a value starting with `http` replaces the whole URL** |
| `request_vendor_parameters`, `request_vendor_method` | write | Vendor query and method |
| `continue`, `response_body`, `response_status_code`, `response_error_message` | done()-only | Answer without calling the vendor (`continue: false`) — for a request the vendor cannot serve. The builder leaves `continue` out of `contextParams` on purpose: it is never injected. The postRequest hook **still runs** on that answer: make it pass a body it did not get from the vendor through unchanged |

**postRequest**

| Variable | Access | Use |
|---|---|---|
| `response_body` | read/write | The vendor's answer (object, or a string — parse defensively). `response_body_map` and `response_body_raw_map` hold it too, read-only; read one name consistently |
| `response_iserror` | read | `true` unless the vendor returned 200–207 |
| `response_status_code`, `response_headers` | read/write | Correct a status the vendor got wrong |
| `configuration` | read/write | Writable here: persist a token or a derived value with `done({ configuration: {...configuration, …} })` |
| `request_body`, `request_body_map` | read | The body **sent to the vendor** (what the preRequest hook wrote), not the caller's |
| `request_body_raw` | read | The caller's original request, as a string — parse it to read what the caller asked for (`model`, `parallel_tool_calls`, `logprobs`, `n`) |

## Recipes

### Same format, different endpoint

When the vendor already speaks the flavor's format, the preRequest hook only points the call at the vendor and names the model the vendor expects; there is no postRequest hook.

```javascript
const body = request_body_map ?? JSON.parse(request_body || '{}');
const deployment = configuration['acme.deployment'] || body.model;
done({
    request_vendor_path: `/openai/deployments/${encodeURIComponent(deployment)}/chat/completions`,
    request_vendor_body: { ...body, model: deployment },
});
```

### Translate the request and the response

```javascript
// preRequest — flavor → vendor
const body = request_body_map ?? JSON.parse(request_body || '{}');
const system = (body.messages ?? []).filter(m => m.role === 'system').map(m => m.content).join('\n');
done({
    request_vendor_body: {
        model: body.model,
        system: system || undefined,
        messages: (body.messages ?? []).filter(m => m.role !== 'system'),
        max_tokens: body.max_completion_tokens ?? body.max_tokens ?? 1024,
        temperature: body.temperature,
    },
});
```

```javascript
// postRequest — vendor → flavor; leave errors to the error recipe below
if (response_iserror) {
    done();
} else {
    const r = typeof response_body === 'string' ? JSON.parse(response_body) : response_body;
    done({
        response_body: {
            id: r.id,
            object: 'chat.completion',
            created: Math.floor(Date.now() / 1000),
            model: r.model,
            choices: [{ index: 0, message: { role: 'assistant', content: r.text ?? '' }, finish_reason: 'stop' }],
            usage: { prompt_tokens: r.usage?.input ?? 0, completion_tokens: r.usage?.output ?? 0, total_tokens: (r.usage?.input ?? 0) + (r.usage?.output ?? 0) },
        },
    });
}
```

Field-by-field mappings between the formats: [format-mapping-guide.md](format-mapping-guide.md). Always map `usage` — the gateway meters tokens from the response, and a missing usage block records the call as zero tokens.

When the answer depends on what the caller asked for (the request's `model`, one tool call when `parallel_tool_calls` is `false`, `logprobs`), read it from `request_body_raw`: in a postRequest hook `request_body_map` is the body the preRequest hook sent to the vendor.

```javascript
let caller = {};
try { caller = JSON.parse(request_body_raw || '{}') ?? {}; } catch (e) { caller = {}; }
const oneCall = caller.parallel_tool_calls === false;
```

### Errors: keep the vendor's status

The gateway turns the status code into the probe's verdict (401 → auth failed, 404 → model not found, 429 → rate limited). Pass a vendor error through unchanged (`if (response_iserror) { done(); }`), and fix a vendor that reports an error with HTTP 200:

```javascript
const r = typeof response_body === 'string' ? JSON.parse(response_body) : response_body;
if (!response_iserror && r?.error) {
    const status = r.error.code === 'unauthorized' ? 401 : r.error.code === 'model_not_found' ? 404 : 502;
    done({ response_status_code: status, response_error_message: 'Vendor returned an error' });
} else {
    done(); // or the translation from the previous recipe
}
```

Never copy the vendor's message into `response_error_message` if it can echo the prompt.

### Custom token exchange

Use the builder's `oauth2ClientCredentials` auth type when the vendor's token endpoint is standard. When it is not (extra body fields, a JSON body, an unusual response), use `auth set --auth-type custom` and two lifecycle resources that run the exchange:

| Resource | When Integration Service runs it | Entry it must be |
|---|---|---|
| `onProvision` | Once, when a connection is created | `"path": "/onProvision", "method": "GET", "vendorMethod": "POST"` |
| `onRefresh` | On the first call after `expires_in` seconds have passed since `authentication.time`, before that call | `"path": "/onRefresh", "method": "POST", "vendorMethod": "POST"` |

The builder does not write either of those: `auth system create --type onProvision` writes the method you pass for the vendor method too, and `--type onRefresh` insists on `/on-refresh`. Create both, then patch them, **before** registering their hooks (a hook file is named after the resource's method and path):

```bash
uip is connectors builder auth system create --type onProvision --method GET --vendor-path <TOKEN_PATH> --output json
uip is connectors builder auth system create --type onRefresh --method POST --vendor-path <TOKEN_PATH> --output json
uip is connectors builder state query 'element.json/resources/GET/%2FonProvision' --output json \
  | jq '.Data.Value | .vendorMethod = "POST"' > provision.json
uip is connectors builder state patch 'element.json/resources/GET/%2FonProvision' --value-file provision.json --output json
uip is connectors builder state query 'element.json/resources/POST/%2Fon-refresh' --output json \
  | jq '.Data.Value | .path = "/onRefresh"' > refresh.json
uip is connectors builder state patch 'element.json/resources/POST/%2Fon-refresh' --op remove --output json
uip is connectors builder state patch 'element.json/resources/POST/%2FonRefresh' --value-file refresh.json --output json
```

Then register the same hook pair on each: `activity hook create --resource-name onProvision --method GET --path /onProvision …` and `--resource-name onRefresh --method POST --path /onRefresh …`.

- **No `provisionAuthValidation`.** Integration Service runs it before `onProvision`, so it reaches the vendor without a token and every connection fails with the vendor's 401. The exchange already rejects wrong credentials; `builder validate` then warns that the resource is missing, which is expected here.
- **`custom.auth.header`.** `auth set --auth-type custom` adds this example entry as a required `pre` field defaulting to `Bearer mytoken`, and `validate` fails without it. If the vendor does not use it, keep the key and make it hidden: `required: false`, empty `defaultValue`, no `configScreenType`.
- **Lifetime.** Write `expires_in` a few minutes below the token's real lifetime, so the refresh lands before the vendor starts answering 401. To test refresh on the draft, write a short one (`'120'`), make a call after it has passed, and check it succeeds on a new token; restore the real value before publishing.

```javascript
// preRequest on onProvision / onRefresh — credentials in a header or the body, never in the URL
const { clientId, clientSecret, tokenUrl } = configuration;
done({
    request_vendor_method: 'POST',
    request_vendor_path: tokenUrl,
    request_vendor_headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        Authorization: `Basic ${btoa(`${clientId}:${clientSecret}`)}`,
    },
    request_vendor_body: { grant_type: 'client_credentials' },
});
```

A token service that takes JSON gets `'Content-Type': 'application/json'` and an object body with the credentials in it — still never the URL.

```javascript
// postRequest on onProvision / onRefresh — persist the token on THIS connection, keeping every other value
if (response_iserror) {
    done();
    return;
}
const r = typeof response_body === 'string' ? JSON.parse(response_body || '{}') : (response_body ?? {});
if (!r.access_token) {
    done({ response_status_code: 502, response_error_message: 'The token service returned no token.' });
    return;
}
done({
    configuration: {
        ...configuration,
        accessToken: r.access_token,
        expires_in: String(Math.max(60, (Number(r.expires_in) || 3600) - 300)),
        'authentication.time': String(Date.now()),
    },
});
```

The resource preRequest hook then sends `Authorization: Bearer ${configuration['accessToken']}` (or the vendor's own token header). `clientId` / `clientSecret` / `tokenUrl` are `pre` config entries the user fills in (the secret encrypted, as `PASSWORD`); `accessToken` (encrypted), `expires_in` and `authentication.time` are hidden entries with **no** `configScreenType`.

### Chained token exchange (request chaining)

Some vendors need several calls before the first token exists, each using what the previous one returned. Apple's OIDC sign-in is one: authenticate the account (password plus a TOTP code) to get a corporate JWT, then trade that JWT at the OAuth token endpoint for the access token Endor takes. Integration Service runs such a sequence itself, through **request chaining**: a resource names the resource to run after it, and that resource's hooks read the previous call's answer. The calls still run only when the connection is provisioned or refreshed, never on the product's hot path, so this is the way to do a multi-call exchange, not `axios` inside the flavor resource's hook.

| Piece | What it is |
|---|---|
| `nextResource` on a resource | `"<METHOD>:<path>"` of the resource Integration Service runs after this one, for example `"POST:/oidcToken"`. Set it with `--next-resource 'POST:/oidcToken'` on `auth system create` or `activity create`, or patch the field into the entry |
| `request_previous_response` | Readable in the next resource's hooks: the previous call's response body (map or list; `null` when the resource was not reached through a chain). `request_previous_response_headers` holds its headers |
| The step resource | An ordinary `api` resource made with `activity create` (its own `standard-resources` file, like `Auth2.json` in Apple's OIDC + A3 connector), with the next token service as its vendor URL |

Shape, as in Apple's OIDC + A3 connector: `onProvision` and `onRefresh` both carry `"nextResource": "POST:/<step>"`. Their preRequest hook sends the first call (authenticate) and they have no postRequest hook. The step resource's preRequest hook reads `request_previous_response` and sends the second call, and its postRequest hook persists the token and its lifetime on the connection. Create the step resource first, then the lifecycle resources with `--next-resource` pointing at it. Keep `nextResource` when you re-create `onRefresh` at `/onRefresh` (Rule 13's patch): the queried entry already has it, or add it in the same `jq`:

```bash
uip is connectors builder activity create --name oidc_token --display-name 'OIDC token' \
  --resource-path /oidcToken --vendor-path /auth/oauth2/token --methods POST --no-curate --output json
uip is connectors builder auth system create --type onProvision --method GET \
  --vendor-path /service/authservice/authenticate --next-resource 'POST:/oidcToken' --output json
uip is connectors builder auth system create --type onRefresh --method POST \
  --vendor-path /service/authservice/authenticate --next-resource 'POST:/oidcToken' --output json
# then the Rule 13 patches; on the onRefresh entry: jq '.Data.Value | .path = "/onRefresh" | .nextResource = "POST:/oidcToken"'
```

```javascript
// preRequest on the step resource (/oidcToken): trade the previous call's JWT for the access token
const prev = request_previous_response;
if (!prev || !prev.corpJwt) {
    // Reached directly, not through the chain, or the first call returned no JWT: never call the token service
    done({ continue: false, response_status_code: 502, response_body: { error: { message: 'The sign-in step returned no token.' } } });
    return;
}
done({
    request_vendor_method: 'POST',
    request_vendor_path: `${String(configuration['oidc.token.service.url']).replace(/\/+$/, '')}/auth/oauth2/token`,
    request_vendor_headers: { 'Content-Type': 'application/json' },
    request_vendor_body: {
        client_id: configuration['oidc.client.id'],
        client_secret: configuration['oidc.client.secret'],
        grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
        assertion: prev.corpJwt,
        scope: 'default',
    },
});
```

The step's postRequest hook is the token-exchange postRequest above, writing the token it receives (`userToken` there). Rules on top of §"Custom token exchange":

- **The last step persists.** Write `configuration` in the postRequest hook of the step that has the final token, and carry earlier values forward through `request_previous_response`, not through `configuration`: an earlier step's `configuration` write is not shown to reach a later step.
- **Guard the step resource.** It is an ordinary resource, so anyone who can call the connection can call its path directly, with `request_previous_response` `null`. Refuse that before any vendor call (as above), and give the postRequest hook `if (response_iserror) { done(); return; }`: without the `return`, an error falls through and overwrites the stored token with `undefined`. Name its path so it never collides with a flavor path.
- **Every host is a field.** Each token service the chain calls is its own `pre` config entry (Apple: the IdMS authenticate host, the OAuth token host, the A3 host), never a URL written into the hook. One host left at a value the cloud cannot reach fails the connection with "Failed to execute API … during provisioning", naming that host.
- **Every secret is encrypted.** Each password, client secret and TOTP seed is a `PASSWORD` entry with `encrypt: true`. Apple's OIDC + A3 template ships them with `encrypt: false`: fix that when porting it. Stored tokens are hidden entries with `encrypt: true` too.
- **Independent tokens.** A vendor that needs two unrelated tokens (Apple: the OIDC access token and the A3 app token, sent together as `X-Apple-OIDC-Access-Token` and `X-Apple-IDMS-A3-Token`) needs both persisted. The template shows only one hop (`onProvision`/`onRefresh` → one step); its `Auth3` (A3) resource is defined but nothing chains to it, so `a3Token` stays empty. Whether a step resource's own `nextResource` runs a third call, and whether a write made in one step survives the next, are not verified. Check both on the draft before relying on them: after connecting the test connection, a call that needs both tokens must pass, and again after a refresh (short `expires_in`, as above).

### Model in the path

Flavors such as Bedrock and Gemini put the model in the path. Read it from `request_path_variables` and move it where the vendor wants it:

```javascript
const model = decodeURIComponent(request_path_variables['modelId'] ?? '');
const body = request_body_map ?? JSON.parse(request_body || '{}');
done({ request_vendor_path: '/v2/generate', request_vendor_body: { ...body, model } });
```

`builder validate` then warns that `modelId` has no slot in the vendor path — expected for this recipe.

## Streaming

On a streaming call (`"stream": true`, or a stream path such as `:streamGenerateContent` / `converse-stream`) Integration Service runs the **preRequest hook only** and relays the vendor's response bytes as they arrive. The postRequest hook does not run, even when the vendor answers with plain JSON.

- The preRequest hook can still rewrite the URL, headers, model and body — so a vendor that streams **in the flavor's own event format** works.
- A vendor that streams in a different format, or cannot stream, cannot be fixed in the connector. Tell the user which product calls will not work, and prefer a flavor the vendor streams natively.
- Do not switch a streamed call to `"stream": false` in the preRequest hook: the caller expects an event stream and gets a JSON body. For a vendor that cannot stream in the flavor's format, refuse the streamed call instead, so it never reaches the vendor: `done({ continue: false, response_status_code: 400, response_body: { error: { message: 'Streaming is not supported by this connector.' } } })`.
- That refusal reaches only a caller that did not ask for an event stream. On a streamed call (`Accept: text/event-stream`, which the gateway sends with every stream) Integration Service drops it and answers `404` `{"message":"Published Connector not found with key <CONNECTOR_KEY>"}` itself, on the draft and on the published connector alike, still without calling the vendor. Tell the user that a streamed call fails with that 404, not with your message. To see the refusal itself, send the same call with `Accept: application/json`: it answers your `400`, its body flattened into `providerMessage`.

## Testing a hook offline

There is no hook log. Before publishing, run the hook against a sample body with a small harness (write it to a scratch directory, not into the connector). It needs a full Node.js runtime; where there is none, skip it and let the test calls in custom-connector-guide.md step 7 test the hooks:

```javascript
// run-hook.mjs — node run-hook.mjs <hook.js> <vars.json>
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
const [hookFile, varsFile] = process.argv.slice(2);
const vars = JSON.parse(readFileSync(varsFile, 'utf8'));
let result;
// Every documented variable exists in Integration Service, so a hook may read one vars.json leaves out.
const declared = Object.fromEntries(['request_body', 'request_body_map', 'request_body_raw', 'request_path_variables', 'request_parameters',
    'request_headers', 'configuration', 'response_body', 'response_body_map', 'response_body_raw_map',
    'response_iserror', 'response_status_code', 'response_headers'].map((name) => [name, undefined]));
const context = vm.createContext({ ...declared, ...vars, btoa, atob, done: (out = {}) => { result = out; } });
vm.runInContext(`(function () {\n${readFileSync(hookFile, 'utf8')}\n})();`, context);
if (result === undefined) { console.error('done() was not called'); process.exit(1); }
console.log(JSON.stringify(result, null, 2));
```

`vars.json` holds the variables the hook reads, for example `{"request_body_map": {...}, "request_path_variables": {}, "configuration": {"base.url": "https://llm.example.com"}}` for a preRequest hook, or `{"response_iserror": false, "response_body": {...}, "request_body_raw": "<the caller's request as a JSON string>", "request_body_map": {<the body sent to the vendor>}}` for a postRequest hook. Feed it a realistic flavor body (messages with a system prompt, a tool definition, an image part) and check the output against [format-mapping-guide.md](format-mapping-guide.md). Use made-up content and no real credentials.
