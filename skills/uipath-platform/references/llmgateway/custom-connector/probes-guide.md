# Probes Guide

The product's compatibility probes are the acceptance test for a BYO LLM connector. They are the same requests the product's own features depend on — a plain completion, tool calling, a forced tool choice, several choices, an image, an embedding — chosen per product, feature and API flavor by the gateway. They run when the configuration is saved, on the published connector's runtime connection. Before that, the unpublished draft gets the same requests, with the same checks, through Integration Service (below).

## The probe requests (`assets/probes/`)

The gateway's probes are fixed requests with fixed checks. `assets/probes/` holds them as one JSON file per request, and `scripts/run-probes.sh` sends them to any connection (custom-connector-guide.md steps 1 and 7), so the draft meets the same requests and checks before it is published. There are three kinds of folder:

| Folder | What it holds | When each runs |
|---|---|---|
| `default/` | Every product's probes: the gateway's base probe for the flavor (`base-chat`, one per chat flavor; `base-responses`; `base-embeddings`), and the basic payloads any product's configuration can list (the `*_basic_probe`s, `"optIn": true`) | A base probe always, unless a product's code-built probe takes its place; a basic payload only when named with `--probe <ProbeId>` |
| `<product>/` | One product's own: the probe the gateway's code builds for it (`agents/agents-tool-call.*`, Agents' forced `tool2` call on every feature but `agents-autopilot`; `uia/uia-screenplay.*`, UIA on its computer-use model), and the payloads only that product lists, each with a validator of its own in the gateway (`uipath-ecs/`: ECS's tool-calling, multimodal, several-choices, embeddings and grounding probes, `"optIn": true`) | A code-built probe automatically for that product, in place of the base probe it `replaces`; a listed payload only when named with `--probe <ProbeId>` |
| `autopilot/` | Autopilot's tool-result round trips, one per flavor (`autopilot_*_stream_roundtrip_probe`, `"optIn": true`, `"roundTrip": true`): two streamed calls with values drawn for the run (§"Round-trip probes") | Only when named with `--probe <ProbeId>` |

A file marked `"optIn": true` is a payload a product's Model Hub configuration lists for a feature, and it is opt in. This guide holds no product's list of them: the list is the product's own configuration, and it varies by feature, model and environment. A product comes with its probes — ask the user or the product team which `ProbeId`s the feature lists, and pass each with `--probe`. With none, the default and any code-built probe run, which is what the gateway runs for a feature that lists none. A named probe written for another flavor is reported as skipped: the gateway runs only those of the configuration's flavor.

### Which files run

For `--flavor X [--product P] [--feature F] [--llm-name M] [--probe ID]…` the runner reads `default/*.json`, `P/*.json` and, for each `--probe ID`, the one `"optIn": true` file named `ID.json` in any folder (a `ProbeId` is unique across the gateway, so a product may list another product's), and keeps a file when:

- its `apiFlavor` is `X`;
- it is not `"optIn": true`, or `--probe` names it;
- it has no `match`, or one `match` entry fits: `feature` is `F` and `llmName` is `M`; a key left out fits anything;
- `F` is not in its `excludeFeatures`.

A kept file's `replaces` then drops the kept files with those ids: Agents' `agents-tool-call` replaces `default/`'s `base-chat`, as the gateway's code does. The rest run in `order` (listed payloads `10`, base and code-built probes `90`), and every one is reported. The gateway stops at the first failure; the runner goes on so you see them all.

### File format

```json
{
  "id": "agents-tool-call",
  "description": "What the probe sends and wants, in a sentence.",
  "source": "Where the gateway defines it (class or payload file).",
  "apiFlavor": "OpenAiChatCompletions",
  "match": [{"feature": "…", "llmName": "…"}],
  "excludeFeatures": ["agents-autopilot"],
  "replaces": ["base-chat"],
  "order": 90,
  "path": "/v1/chat/completions",
  "body": {"model": "{{model}}", "messages": [{"role": "user", "content": "…"}]},
  "retries": [{"status": 400, "ifBodyContains": ["…"], "edit": ".tool_choice = \"auto\"", "why": "…"}],
  "checks": [{"reason": "MISSING_TOOL_CALL", "says": "the answer calls a tool", "jq": ".choices[0].message.tool_calls != null"}]
}
```

- `path` and `body` are what the gateway sends to the connection. `{{model}}` anywhere in either becomes `--model`, the vendor's model id: the gateway puts it in the body for the OpenAI and Anthropic flavors and in the path for Gemini and Bedrock.
- `checks` run in order on the answer to a 2xx call, each a jq condition that is true when the answer is fine. The first false one is the verdict, with the gateway's reason. With no checks, any 2xx passes; with checks, an answer that is not JSON is `MALFORMED_RESPONSE`. A non-2xx answer is `UNAVAILABLE`.
- `retries`: when the answer has that status and contains every string listed, the runner applies the jq `edit` to the body and sends it once more, as the gateway does (`max_completion_tokens` instead of `max_tokens`; tool choice `auto` when a model refuses a forced one).
- `optIn: true` marks a payload a product's configuration lists: it runs only when named with `--probe`, and its file is named `<ProbeId>.json`. The base and code-built probes leave it out.
- `roundTrip: true` marks a tool-result round trip (below): `path` is the flavor's streaming path, `body` is the first turn's request with `{{order_id}}` and `{{customer_id}}` where the prompt names the run's ids, and the file has no `checks` — the runner's are the validator's own.
- `id`, `apiFlavor`, `path`, `body` are required; the rest are optional.

### Round-trip probes (`autopilot/`)

Autopilot's `autopilot_*_stream_roundtrip_probe`s — one per flavor Autopilot uses: chat completions, Responses, Anthropic Messages, Bedrock Invoke, Gemini — are not one request with fixed checks. Each run makes two streamed calls with values drawn fresh for it, so a stub, a cache or a replayed answer cannot pass:

1. **Tool calls.** The prompt names an order id and a customer id. The stream must reassemble into calls to `lookup_order` / `lookup_customer` whose `order_id` / `customer_id` are exactly those ids. One call passes; two is what the prompt asks for.
2. **Tool results.** The same request goes back with the assistant's calls and a result for each, in the form the flavor's clients use: `tool_calls` and `tool` messages for chat completions; `function_call` and `function_call_output` items for Responses; the first turn's `thinking` blocks, then `tool_use`, and `tool_result` blocks for Anthropic and Bedrock; `functionCall` with its `thoughtSignature`, and `functionResponse`, for Gemini. The streamed answer must quote the status and tier codes that exist only in those results.

`run-probes.sh` makes both calls with `Accept: text/event-stream` and reads each stream as the gateway does. The files are `"optIn": true` like every listed payload: name the one of the configuration's flavor with `--probe`. `autopilot/` is named for the probes' owner, not for a `--product` key, so they are found only by id.

Both turns stream, and Integration Service relays a streamed answer raw (custom-connector-guide.md Rule 4): the vendor itself must stream the flavor's events. For chat completions that means `delta.tool_calls` fragments carrying an `index`, the call's `id` and `function.name` sent once, and `arguments` in pieces. A vendor whose stream differs cannot pass, whatever the hooks do; say so to the user in step 1.

### Adding a probe

Only a probe the gateway itself has — never a request of this guide's own:

- **code-built** (a class under the gateway's `CompatibilityProbes/ProgrammaticProbes/`): `<product>/<id>.<flavor-slug>.json`, one per flavor the gateway's mappers send it in, with `replaces` naming the default it takes the place of and the `match` / `excludeFeatures` the class selects by;
- **a payload a product lists** (under the gateway's `CompatibilityProbes/ProductDefinedProbes/Payloads/`, with its validator): `default/<ProbeId>.json` when any product can list it, `<product>/<ProbeId>.json` when the payload and its validator are that product's own; `"optIn": true`, the payload as `body`, the validator's checks in order, and no `match`: it runs when named.
- **a round trip** (a payload whose validator makes more than one call, such as `AutopilotStreamRoundTripProbeValidator`): the first turn's payload as `body`, `"optIn": true`, `"roundTrip": true`, the streaming `path`, and no `checks`. A new flavor or a new scenario also needs its reader and its tool-result form in `scripts/run-probes.sh`.

Set `path` to the flavor's resource path ([connector-contract-guide.md](connector-contract-guide.md)), add `model: "{{model}}"` to the body for the OpenAI and Anthropic flavors, and check the selection offline with `--list`.

The files mirror the gateway's probes (each file's `source` names the class or payload file it comes from) and carry the request the flags in production select: Agents sends `tool2` and accepts one or two calls. When a probe's verdict in step 9 names a request the runner did not send, the feature lists a probe you did not name: get its `ProbeId` and run it with `--probe`.

A call the vendor cannot serve, refused by the hook's own `continue: false`, fails the matching probe too. Do not work around it: tell the user which product feature needs it (custom-connector-guide.md step 1).

## How the probes run

`uip llm-configuration byo-connections create` and `update` always:

1. run a client-side preflight (connector type, model in the catalog, flavor allowed for the model), exiting 1 offline on a mistake;
2. for a `Custom` mapping, read the connector template from the connection's connector tags (below);
3. send the configuration to the gateway's validate endpoint, which runs every probe for each mapped model through the connection — the real path: gateway → Integration Service → your hooks → vendor;
4. save the configuration only if every model passes. There is no validate-only command and no skip flag.

So probing means creating (first time) or updating (after a fix) a configuration, on the runtime connection of the published connector: the command, and when to pass `--enabled`, are in custom-connector-guide.md step 9 and Rule 10.

A failed `create` saves nothing — re-run `create` after the fix. A failed `update` leaves the saved record as it was — re-run the same `update`.

## Before the probes: the connector template

The CLI stops a `Custom` mapping, before any probe, when it cannot read the template:

| CLI message | Meaning | Fix |
|---|---|---|
| `Integration Service has no connection '<id>' you can read` | The connection is a builder test connection (never listed), sits in a folder you cannot see, or the id is wrong | Use the runtime connection on the published connector (`uip is connections list <PUBLISHED_KEY> --all-folders --refresh`) |
| `connector '<key>' of connection '<id>' has no tag naming its template` | `element-metadata.json:tags` lacks the flavor's tag | Add it ([connector-contract-guide.md](connector-contract-guide.md)), bump `latestVersion`, `import`, `publish --wait`, run the command again |

## Reading the verdict

The verdict is keyed by catalog model, and its casing depends on where you read it:

- **On success**, the CLI's envelope: `Data.Validation.<Model>`, the model name PascalCased (`gemini-3.8-flash` → `Gemini3.8Flash`), with PascalCase fields `IsAvailable`, `IsCompatible`, `IsModelNameSimilar`.
- **On failure**, the CLI's `Message`, which quotes the gateway's own answer: `isAvailable`, `isCompatible`, `unavailabilityReason`, `incompatibilityReason`, `vendorRawResponse`. Read these names without regard to case (in jq, compare `ascii_downcase` keys); do not rely on one casing.

The table and the sections below use the gateway's camelCase names; on success, read the PascalCase twin:

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
| `VendorInvalidRequest` (400) | The preRequest hook sends a body the vendor rejects (unknown field, wrong types, missing required field such as Anthropic `max_tokens`) — or the hook's own `continue: false` refusal of a feature the vendor lacks | Read `vendorRawResponse`; fix the request mapping; test it with the harness or a test call. If it is the hook's own refusal, the connector cannot fix it: stop and tell the user which probe needs the feature (custom-connector-guide.md step 1) |
| `VendorRateLimitExceeded` (429) | Vendor quota | Wait and re-probe; not a connector defect |
| `VendorInternalFailure`, `VendorGatewayFailure`, `VendorServiceUnavailable`, `VendorDefault5xxFailure` | Vendor outage — or a hook that throws (an exception in a hook surfaces as a 5xx) | Run both hooks through the harness, or a test call, on the probe's body shape; then retry |
| `VendorDefault4xxFailure` | Another 4xx from the vendor | Read `vendorRawResponse` |
| *(no reason)* | The gateway failed before calling out — most often a CLI too old to send the connector template (custom-connector-guide.md Rule 2), or an unparseable answer | Check `byo-connections create --help` (custom-connector-guide.md Rule 2); check the postRequest output is valid JSON |

## Incompatible (`isAvailable: true`, `isCompatible: false`)

| `incompatibilityReason` | Likely cause | Fix |
|---|---|---|
| `MALFORMED_RESPONSE` | The postRequest output is not the flavor's response shape: missing `choices` / `candidates` / `content` / `output`, a string where an object belongs, no `message.role` | Rebuild the response per [format-mapping-guide.md](format-mapping-guide.md) |
| `INCORRECT_RESPONSE` | Shape is right but the content is not the model's answer (empty text, a wrapper object, the request echoed back) | Return the vendor's generated text, not its envelope |
| `MULTIPLE_RESPONSES` | More choices, candidates or embeddings than requested | Return exactly `n` (default 1) |
| `MISSING_TOOL_CALL` | `tools` / `tool_choice` dropped on the way to the vendor, or the vendor's call not mapped back | Map the tool definitions and choice both ways |
| `TOOL_RESULT_IGNORED` | A round-trip probe's second turn: the answer is empty, is another tool call, or does not quote the codes the tool results carry — the results were dropped or reshaped on the way to the vendor, or the model did not read them | Map the assistant's tool calls and the tool results in the preRequest hook (matching ids, the result's content as sent); read `<name>.turn2.request.json` and `<name>.turn2.stream.txt` from the runner |
| `INCORRECT_TOOL_CALL` | Wrong function name, or `arguments` not a JSON **string** (OpenAI) / not an object (Anthropic, Gemini, Converse) | Fix the call mapping |
| `MULTIPLE_TOOL_CALLS_WHEN_PARALLEL_TOOL_CALLS_NOT_ALLOWED` | `parallel_tool_calls: false` not honoured | Map it (Anthropic `disable_parallel_tool_use`) or keep only the first call |
| `EXPECTED_MAX_COMPLETION_TOKENS` | The vendor wants `max_completion_tokens`; the gateway retries with it once automatically | If it persists, map `max_tokens` → `max_completion_tokens` in the preRequest hook |

## The fix loop

1. Change one thing — the hook or config entry the reason points at. Run `run-probes.sh` on the draft's test connection (it runs what was last imported) to reproduce it; `builder validate` and `import` until that probe passes.
2. Bump `latestVersion`, `import`, `publish --wait`: the runtime connection runs only the published version.
3. Re-probe: the same `update <CONFIG_ID>` (or `create` if nothing was saved).
4. Three failures on the same reason → stop and show the user the verdict and the hook.

A product can add probes over time. A configuration that passed once can fail on a later `update`; read the new reason the same way.
