# Connector Contract Guide

What the LLM Gateway expects from a BYO LLM custom connector: the paths it calls, the body it sends, how the connector is recognised, and how credentials reach the vendor.

## How the gateway calls the connector

For a configuration with `connectorType: Custom`, the gateway sends the product's request — already in the configuration's API flavor — to the Integration Service connection:

```text
POST <IS>/v3/element/instances/<CONNECTION_ID><FLAVOR_PATH>
     Accept: text/event-stream        (only when the caller streams)
     body: the flavor's own request JSON
```

Integration Service matches `<FLAVOR_PATH>` against the connector's resource `path` (not the vendor path), runs the resource's preRequest hook, calls `base.url` + `vendorPath` (or the full URL the hook sets), runs the postRequest hook, and returns the result. The vendor never sees `<FLAVOR_PATH>` unless the connector forwards it.

## Flavor contract (connector template `CustomAiGateway`)

One row per API flavor. The model the vendor should serve is the configuration's `--llm-identifier`; on path-variable flavors it arrives in the path, otherwise in the body's `model` field.

| API flavor | Resource path(s) to expose (all `POST`) | Streaming | Model arrives in | Tag for `element-metadata.json:tags` |
|---|---|---|---|---|
| `OpenAiChatCompletions` | `/v1/chat/completions` | same path, `"stream": true` | body `model` | `aigateway-openai-chat-completions` |
| `OpenAiResponses` | `/v1/responses` | same path, `"stream": true` | body `model` | `aigateway-openai-responses` |
| `OpenAiEmbeddings` | `/v1/embeddings` | — | body `model` | `aigateway-openai-embeddings` |
| `GeminiGenerateContent` | `/models/{model_id}:generateContent`, `/models/{model_id}:streamGenerateContent` | stream path, query `alt=sse` | path `model_id` | `aigateway-gemini-generatecontent` |
| `GeminiEmbeddings` | `/models/{model_id}:predict` | — | path `model_id` | `aigateway-gemini-embeddings` |
| `AwsBedrockInvoke` | `/model/{modelId}/invoke`, `/model/{modelId}/invoke-with-response-stream` | stream path | path `modelId` | `aigateway-aws-bedrock-invoke-model` |
| `AwsBedrockConverse` | `/model/{modelId}/converse`, `/model/{modelId}/converse-stream` | stream path | path `modelId` | `aigateway-aws-bedrock-converse` |
| `AnthropicMessages` | `/v1/messages` | same path, `"stream": true` | body `model` | `aigateway-anthropic-messages` |

Set the tags string to `custom, <tag>` (comma-separated, as the templates do). A connector serving several flavors lists every tag and exposes every row's paths; one configuration still names one flavor.

Expose the streaming path even when you cannot translate the stream: a product that streams calls it, and a 404 there reads as an outage. Whether the stream is *usable* depends on the vendor (see [hook-authoring-guide.md](hook-authoring-guide.md) §"Streaming").

### Other connector templates

A connector cloned from one of the vendor templates in the Integration Service connector builder registers with that template's name, and the gateway treats it as that vendor (Azure OpenAI deployment paths with `api-version`, Vertex `:generateContent`, and so on):

| `--connector-template` | Tag |
|---|---|
| `OpenAiV1Compliant` | `openai-v1-compliant` |
| `AzureOpenAi` | `azure-openai` |
| `GoogleVertexAi` | `google-vertexai` |
| `AmazonBedrock` | `amazon-web-services` |
| `Anthropic` | `anthropic-claude` |

Keep such a clone's resource paths exactly as the template has them. Prefer the built-in BYO connector for those vendors (no custom connector at all); a vendor template is for that vendor's API behind something the built-in connector cannot handle. Everything else — the usual case — is `CustomAiGateway` and the flavor table above.

## Authentication

Pick the builder auth type that matches the vendor; the builder writes the config fields, the encrypted secret entries and the header parameter, and the user fills them in on the connection page.

| Vendor auth | Builder flags |
|---|---|
| API key in a header (`Authorization: Bearer <key>`, `api-key`, `x-api-key`) | `init --auth customApiKey --api-key-param-name <HEADER> [--api-key-prefix 'Bearer ']` |
| Several static headers (key + tenant id) | `auth set --auth-type customApiKey …` plus `--secret-auth-header <CONFIG>=<HEADER>` / `--auth-header <CONFIG>=<HEADER>` |
| Standard OAuth2 client credentials | `auth set --auth-type oauth2ClientCredentials --token-url <TOKEN_URL> --scope '<SCOPES>'` |
| AWS SigV4 (Bedrock-compatible endpoint) | `auth set --auth-type awsv4` |
| A non-standard token exchange (custom body, extra fields, returned host) | `auth set --auth-type custom` + an `onProvision` system resource whose hooks fetch the token — recipe in [hook-authoring-guide.md](hook-authoring-guide.md) §"Custom token exchange" |
| No auth (private network endpoint) | `init --auth none` |

Rules that hold for every type:

- Secrets are config entries with `encrypt: true` (usually `PASSWORD`). Never give one a `defaultValue`.
- A value the user must type has `configScreenType: "pre"` (or `"pre-optional"`) and a `hintText` with an example. A value a hook writes back (`accessToken`, `expires_in`, `authentication.time`) has **no** `configScreenType` at all — any value, even `"post"`, puts it on a form.
- Credentials travel in headers or a form-encoded token body only. Never as a `vendorType: "query"` or `"path"` parameter, never in `request_vendor_path` — full request URLs are written to telemetry in clear text. Query parameters are fine for non-secrets (`api-version`, `alt`).
- Add a `provisionAuthValidation` system resource when the vendor has a cheap authenticated `GET` (for example `/models`), so a wrong key fails on the connection page instead of in the probe: `uip is connectors builder auth system create --type provisionAuthValidation --vendor-path /models --method GET`.

## Per-connection values

A per-connection host part (region, workspace, deployment name) is one config templated into the base URL: `init --base-url 'https://{workspace}.llm.example.com'` seeds a single `{workspace}` field. Add other fixed-set options with `state patch element.json/configuration/<KEY> --value-file <entry.json>` (a complete entry: `name`, `key`, `type`, `required`, `configScreenType`, `hide`, `displayOrder`, `hintText`, and `options` for a `COMBO`). Hooks read them as `configuration['<KEY>']`.

## Porting from a template or zip

When the user supplies a zip, or names an AI Gateway template to start from, use it as reference material for a fresh scaffold:

1. Extract it into its own directory **outside** the work directory (never `init` inside it).
2. Read `app/element/element.json` (`resources[]`, `configuration[]`, `parameters[]`, `hooks[]`) and every `standard-resources/*.json`. Hook code may be inline (`hooks[].body`, a JSON string — unescape it) or in `app/element/hooks/*.js`.
3. In the fresh scaffold: one `activity create` per resource path you need, then `activity hook create` per hook body (saved as a `.js` file first), then `state patch element.json/configuration/<KEY>` per non-auth config entry the hooks read. Re-create auth with `auth set` rather than copying auth config entries.
4. Copy `element-metadata.json:tags` into the new metadata.

Do not import the reference itself: AI Gateway templates share one key (`design-entity-customaigatewaybyomtemplate`), and an old zip carries its owner's key — importing either updates a connector that is not yours. Do not rename the key by hand either; `init` derives it from your login. A template also fails `builder validate` as shipped (its standard-resource file names do not match its resource names, its parameters lack `source`), which is one more reason to rebuild instead.

## Pre-publish checklist

Run after `builder validate` passes, before `import`:

1. **Paths** — every path in the flavor's row exists as a resource `path` with method `POST` (`builder inspect --output json`, `ResourceSummary`). No vendor-only path was used as the resource path.
2. **Tag** — `element-metadata.json:tags` contains the flavor's tag.
3. **Version** — `element-metadata.json:latestVersion` is higher than the last published version (first publish: `1.0.0`).
4. **Hooks** — every hook passes `node --check`, ends every path in `done(...)`, passes a vendor error through with its status, and contains no `console.log`.
5. **No credentials in URLs** — no credential is a `query`/`path` parameter or part of a URL a hook builds.
6. **No secret defaults** — no encrypted or `PASSWORD` config entry has a `defaultValue`; `base.url` holds the vendor host, not a placeholder such as `https://example.com`.
7. **Hook-written config** — every config entry a hook writes back has no `configScreenType`.
