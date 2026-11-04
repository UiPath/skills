# Probes Guide

The product's compatibility probes are the acceptance test for a BYO LLM connector. They are the same requests the product's own features depend on — a plain completion, tool calling, a forced tool choice, several choices, an image, an embedding — chosen per product, feature and API flavor by the gateway. They run when the configuration is saved, on the published connector's runtime connection. Before that, the unpublished draft gets the same kinds of requests through Integration Service.

## Test calls on the draft

SKILL.md step 7 sends these to the draft's test connection at the flavor's path, the call the gateway makes. The bodies below are for `OpenAiChatCompletions`. For another flavor, send the same request in that flavor's own format ([format-mapping-guide.md](format-mapping-guide.md)) to its path ([connector-contract-guide.md](connector-contract-guide.md)), with the model in the path where the flavor puts it there (`/models/<VENDOR_MODEL_ID>:generateContent`).

| Call | Send it when | Body | Passes when |
|---|---|---|---|
| `basic` | Always | `{"model": "<VENDOR_MODEL_ID>", "messages": [{"role": "user", "content": "Give me the first capital letter of the English alphabet and this letter only"}]}` | 200; exactly one choice, `message.role` `assistant`, content `A`; `usage` with token counts |
| `tools` | The product calls tools (Agents always does) | `model`, a user message that needs the tool, one function in `tools` with a small JSON-schema `parameters`, `"tool_choice": "required"`, `"parallel_tool_calls": false` | Exactly one `tool_calls` entry naming that function, its `arguments` a JSON **string** that parses |
| `choices` | The product asks for several choices | `tools` plus `"n": 2` | Exactly 2 choices |
| `image` | The product sends images | A user message whose `content` holds a `text` part and an `image_url` part with a small `data:image/png;base64,…` URL | 200 with an answer |
| `stream` | The product streams | `basic` plus `"stream": true`, sent with `-N -H 'Accept: text/event-stream'` | `text/event-stream` in the flavor's own event format, ending as the flavor's stream ends (`data: [DONE]` for chat completions) |
| `embeddings` | The flavor is an embeddings flavor (in place of the calls above) | `{"model": "<VENDOR_MODEL_ID>", "input": ["first text", "second text"]}` | One embedding per input |

A call the vendor cannot serve, refused by the hook's own `continue: false`, fails the matching probe too. Do not work around it: tell the user which product feature needs it (SKILL.md step 1).

The test calls do not replace the probes, which use the product's own requests and checks. A connector that passes every call can still fail a probe; read its reason below.

## How the probes run

`uip llm-configuration byo-connections create` and `update` always:

1. run a client-side preflight (connector type, model in the catalog, flavor allowed for the model), exiting 1 offline on a mistake;
2. for a `Custom` mapping, read the connector template from the connection's connector tags (below);
3. send the configuration to the gateway's validate endpoint, which runs every probe for each mapped model through the connection — the real path: gateway → Integration Service → your hooks → vendor;
4. save the configuration only if every model passes. There is no validate-only command and no skip flag.

So probing means creating (first time) or updating (after a fix) a configuration, on the runtime connection of the published connector (SKILL.md step 9). Create with `--no-enabled`; enable with `update … --enabled` once the user says the product should use it.

```bash
uip llm-configuration byo-connections create --product <PRODUCT> --feature <FEATURE> \
  --folder-key <SHARED_FOLDER_KEY> --name '<CONFIG_NAME>' --no-enabled \
  --connector-type Custom --connection-id <RUNTIME_CONNECTION_ID> --api-flavor <API_FLAVOR> \
  --llm-name <CATALOG_MODEL> --llm-identifier <VENDOR_MODEL_ID> --output json
```

A failed `create` saves nothing — re-run `create` after the fix. A failed `update` leaves the saved record as it was — re-run the same `update`.

## Before the probes: the connector template

The CLI stops a `Custom` mapping, before any probe, when it cannot read the template:

| CLI message | Meaning | Fix |
|---|---|---|
| `Integration Service has no connection '<id>' you can read` | The connection is a builder test connection (never listed), sits in a folder you cannot see, or the id is wrong | Use the runtime connection on the published connector (`uip is connections list <PUBLISHED_KEY> --all-folders --refresh`) |
| `connector '<key>' of connection '<id>' has no tag naming its template` | `element-metadata.json:tags` lacks the flavor's tag | Add it ([connector-contract-guide.md](connector-contract-guide.md)), bump `latestVersion`, `import`, `publish --wait`, run the command again |

## Reading the verdict

The verdict is keyed by catalog model (`validation.<model>` on success; in the failure message otherwise):

| Field | Meaning |
|---|---|
| `isAvailable` | The probe reached a working endpoint. `false` → connection, Integration Service, auth, path, or vendor failure (`unavailabilityReason`) |
| `isCompatible` | The answer had the shape and content the product needs. `false` with `isAvailable: true` → your hooks' output is wrong (`incompatibilityReason`) |
| `isModelNameSimilar` | Advisory only: `--llm-identifier` looks very different from the catalog model. Confirm with the user that the mapping is intended |
| `vendorRawResponse` | The upstream answer on an unavailability — read it before changing anything; never paste it to the user if it may contain their prompt |

## Unavailable (`isAvailable: false`)

| `unavailabilityReason` | Likely cause | Fix |
|---|---|---|
| `IntegrationServiceConfigurationNotFound` | Wrong connection id, or a deleted connection | Re-list it with `uip is connections list <PUBLISHED_KEY> --all-folders --refresh` and use its id ([connections-guide.md](connections-guide.md)) |
| `IntegrationServiceConfigurationNotEnabled` | Connection disabled or its authorization expired | `uip is connections edit <ID>` and re-enter the fields |
| `IntegrationServiceMissingAttributes` | The connection lacks a required field | Re-create the connection with every `pre` field filled |
| `IntegrationServiceUnreachable` | Integration Service error; on the runtime connection, a version that is not published yet | `publish-status`, then retry |
| `VendorAuthFailed` (401) | Wrong key, wrong header name, missing `Bearer ` prefix, expired token | Fix the auth config or the token-exchange hooks; re-enter the key |
| `VendorPermissionDenied` (403) | Key valid but not allowed this model or endpoint | The customer grants access; nothing to fix in the connector |
| `VendorModelNotFound` (404) | **The resource path does not match the flavor** (Integration Service answers 404 for an unknown path) — or the vendor does not know `--llm-identifier` | Check the paths against [connector-contract-guide.md](connector-contract-guide.md) first, then the model id and the hook's model mapping |
| `VendorInvalidRequest` (400) | The preRequest hook sends a body the vendor rejects (unknown field, wrong types, missing required field such as Anthropic `max_tokens`) — or the hook's own `continue: false` refusal of a feature the vendor lacks | Read `vendorRawResponse`; fix the request mapping; test it with the harness or a test call. If it is the hook's own refusal, the connector cannot fix it: stop and tell the user which probe needs the feature (SKILL.md step 1) |
| `VendorRateLimitExceeded` (429) | Vendor quota | Wait and re-probe; not a connector defect |
| `VendorInternalFailure`, `VendorGatewayFailure`, `VendorServiceUnavailable`, `VendorDefault5xxFailure` | Vendor outage — or a hook that throws (an exception in a hook surfaces as a 5xx) | Run both hooks through the harness, or a test call, on the probe's body shape; then retry |
| `VendorDefault4xxFailure` | Another 4xx from the vendor | Read `vendorRawResponse` |
| *(no reason)* | The gateway failed before calling out — most often a CLI too old to send the connector template (SKILL.md Rule 2), or an unparseable answer | Check `byo-connections create --help` (SKILL.md Rule 2); check the postRequest output is valid JSON |

## Incompatible (`isAvailable: true`, `isCompatible: false`)

| `incompatibilityReason` | Likely cause | Fix |
|---|---|---|
| `MALFORMED_RESPONSE` | The postRequest output is not the flavor's response shape: missing `choices` / `candidates` / `content` / `output`, a string where an object belongs, no `message.role` | Rebuild the response per [format-mapping-guide.md](format-mapping-guide.md) |
| `INCORRECT_RESPONSE` | Shape is right but the content is not the model's answer (empty text, a wrapper object, the request echoed back) | Return the vendor's generated text, not its envelope |
| `MULTIPLE_RESPONSES` | More choices, candidates or embeddings than requested | Return exactly `n` (default 1) |
| `MISSING_TOOL_CALL` | `tools` / `tool_choice` dropped on the way to the vendor, or the vendor's call not mapped back | Map the tool definitions and choice both ways |
| `INCORRECT_TOOL_CALL` | Wrong function name, or `arguments` not a JSON **string** (OpenAI) / not an object (Anthropic, Gemini, Converse) | Fix the call mapping |
| `MULTIPLE_TOOL_CALLS_WHEN_PARALLEL_TOOL_CALLS_NOT_ALLOWED` | `parallel_tool_calls: false` not honoured | Map it (Anthropic `disable_parallel_tool_use`) or keep only the first call |
| `EXPECTED_MAX_COMPLETION_TOKENS` | The vendor wants `max_completion_tokens`; the gateway retries with it once automatically | If it persists, map `max_tokens` → `max_completion_tokens` in the preRequest hook |

## The fix loop

1. Change one thing — the hook or config entry the reason points at. Reproduce the failing request as a test call on the draft's test connection (it runs what was last imported); `builder validate` and `import` until that call passes.
2. Bump `latestVersion`, `import`, `publish --wait`: the runtime connection runs only the published version.
3. Re-probe: the same `update <CONFIG_ID>` (or `create` if nothing was saved).
4. Three failures on the same reason → stop and show the user the verdict and the hook.

A product can add probes over time. A configuration that passed once can fail on a later `update`; read the new reason the same way.
