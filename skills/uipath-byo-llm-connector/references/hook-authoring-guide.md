# Hook Authoring Guide

Hooks are where a BYO LLM connector does its work: the **preRequest** hook turns the flavor's request into the vendor's, the **postRequest** hook turns the vendor's answer back into the flavor's response. This guide covers what is specific to LLM traffic; the builder's own help (`uip is connectors builder activity hook create --help`) lists every variable.

## Runtime

- Hooks run in Integration Service's sandboxed JavaScript engine: modern syntax (`const`, arrow functions, `?.`, `??`, destructuring, spread) and `async`/`await` work, and `require()` loads a small fixed set (`axios`, `crypto`, `url`, `querystring`, `buffer`, `lodash`, …).
- Every code path ends in `done()` or `done({...})` — a hook returns through it, not through `return`. Put `return;` after a `done()` that is not the last statement.
- Keep the resource hooks synchronous and free of secondary HTTP calls: they sit on the hot path of every product call. Do token work in the token-exchange resources instead (§"Custom token exchange").
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
| `request_vendor_path` | write | Vendor path; **a value starting with `http` replaces the whole URL** |
| `request_vendor_parameters`, `request_vendor_method` | write | Vendor query and method |
| `continue`, `response_body`, `response_status_code`, `response_error_message` | done()-only | Answer without calling the vendor (`continue: false`) — for a request the vendor cannot serve |

**postRequest**

| Variable | Access | Use |
|---|---|---|
| `response_body` | read/write | The vendor's answer (object, or a string — parse defensively) |
| `response_iserror` | read | `true` unless the vendor returned 200–207 |
| `response_status_code`, `response_headers` | read/write | Correct a status the vendor got wrong |
| `configuration` | read/write | Writable here: persist a token or a derived value with `done({ configuration: {...} })` |
| `request_*` | read | What was sent to the vendor |

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

Use the builder's `oauth2ClientCredentials` auth type when the vendor's token endpoint is standard. When it is not (extra body fields, an unusual response), use `auth set --auth-type custom`, add `onProvision` (and, for expiring tokens, `onRefresh`) system resources, and hang a hook pair on each:

```javascript
// preRequest on onProvision / onRefresh — credentials in a header and the form body, never in the URL
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

```javascript
// postRequest on onProvision / onRefresh — persist the token on THIS connection
if (response_iserror) {
    done();
} else {
    done({
        configuration: {
            accessToken: response_body?.access_token,
            expires_in: response_body?.expires_in ?? 3600,
            'authentication.time': Date.now(),
        },
    });
}
```

The resource preRequest hook then sends `Authorization: Bearer ${configuration['accessToken']}`. `clientId` / `clientSecret` / `tokenUrl` are `pre` config entries the user fills in (the secret encrypted, as `PASSWORD`); `accessToken`, `expires_in` and `authentication.time` are hidden entries with **no** `configScreenType`.

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
- Do not switch a streamed call to `"stream": false` in the preRequest hook: the caller expects an event stream and gets a JSON body.

## Testing a hook offline

There is no hook log. Before publishing, run the hook against a sample body with a small harness (write it to a scratch directory, not into the connector). It needs a full Node.js runtime; where there is none, skip it and let the probe test the hooks:

```javascript
// run-hook.mjs — node run-hook.mjs <hook.js> <vars.json>
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
const [hookFile, varsFile] = process.argv.slice(2);
const vars = JSON.parse(readFileSync(varsFile, 'utf8'));
let result;
const context = vm.createContext({ ...vars, btoa, atob, done: (out = {}) => { result = out; } });
vm.runInContext(`(function () {\n${readFileSync(hookFile, 'utf8')}\n})();`, context);
if (result === undefined) { console.error('done() was not called'); process.exit(1); }
console.log(JSON.stringify(result, null, 2));
```

`vars.json` holds the variables the hook reads, for example `{"request_body_map": {...}, "request_path_variables": {}, "configuration": {"base.url": "https://llm.example.com"}}` for a preRequest hook, or `{"response_iserror": false, "response_body": {...}}` for a postRequest hook. Feed it a realistic flavor body (messages with a system prompt, a tool definition, an image part) and check the output against [format-mapping-guide.md](format-mapping-guide.md). Use made-up content and no real credentials.
