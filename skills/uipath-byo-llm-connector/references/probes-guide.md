# Probes Guide

The product's compatibility probes are the acceptance test for a BYO LLM connector. They are the same requests the product's own features depend on — a plain completion, tool calling, a forced tool choice, several choices, an image, an embedding — chosen per product, feature and API flavor by the gateway.

## How to run them

`uip llm-configuration byo-connections create` and `update` always:

1. run a client-side preflight (connector type, connector template, model in the catalog, flavor allowed for the model), exiting 1 offline on a mistake;
2. send the configuration to the gateway's validate endpoint, which runs every probe for each mapped model through the connection — the real path: gateway → Integration Service → your hooks → vendor;
3. save the configuration only if every model passes. There is no validate-only command and no skip flag.

So probing means creating (first time) or updating (after a fix) a configuration. Use `--no-enabled` while iterating; switch to `--enabled` only on the runtime connection.

```bash
uip llm-configuration byo-connections create --product <PRODUCT> --feature <FEATURE> \
  --folder-key <SHARED_FOLDER_KEY> --name '<TEST_CONFIG_NAME>' --no-enabled \
  --connector-type Custom --connector-template CustomAiGateway \
  --connection-id <CONNECTION_ID> --api-flavor <API_FLAVOR> \
  --llm-name <CATALOG_MODEL> --llm-identifier <VENDOR_MODEL_ID> --output json
```

A failed `create` saves nothing — re-run `create` after the fix. A failed `update` leaves the saved record as it was — re-run the same `update`.

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
| `IntegrationServiceConfigurationNotFound` | Wrong connection id; deleted connection; connection in a Personal workspace; `--folder-key` is not the connection's folder | Re-list the connection; move it to the shared folder ([connections-guide.md](connections-guide.md)) |
| `IntegrationServiceConfigurationNotEnabled` | Connection disabled or its authorization expired | `uip is connections edit <ID>` and re-enter the fields |
| `IntegrationServiceMissingAttributes` | The connection lacks a required field | Re-create the connection with every `pre` field filled |
| `IntegrationServiceUnreachable` | Integration Service error, or the connector version is not published | `publish-status`, then retry |
| `VendorAuthFailed` (401) | Wrong key, wrong header name, missing `Bearer ` prefix, expired token | Fix the auth config or the token-exchange hooks; re-enter the key |
| `VendorPermissionDenied` (403) | Key valid but not allowed this model or endpoint | The customer grants access; nothing to fix in the connector |
| `VendorModelNotFound` (404) | **The resource path does not match the flavor** (Integration Service answers 404 for an unknown path) — or the vendor does not know `--llm-identifier` | Check the paths against [connector-contract-guide.md](connector-contract-guide.md) first, then the model id and the hook's model mapping |
| `VendorInvalidRequest` (400) | The preRequest hook sends a body the vendor rejects (unknown field, wrong types, missing required field such as Anthropic `max_tokens`) | Read `vendorRawResponse`; fix the request mapping; test it with the harness |
| `VendorRateLimitExceeded` (429) | Vendor quota | Wait and re-probe; not a connector defect |
| `VendorInternalFailure`, `VendorGatewayFailure`, `VendorServiceUnavailable`, `VendorDefault5xxFailure` | Vendor outage — or a hook that throws (an exception in a hook surfaces as a 5xx) | Run both hooks through the harness on the probe's body shape; then retry |
| `VendorDefault4xxFailure` | Another 4xx from the vendor | Read `vendorRawResponse` |
| *(no reason)* | The gateway failed before calling out — most often a Custom mapping without `--connector-template`, or an unparseable answer | Check the mapping flags; check the postRequest output is valid JSON |

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

1. Change one thing — the hook or config entry the reason points at. Re-run the harness.
2. Bump `element-metadata.json:latestVersion`.
3. `uip is connectors builder validate --output json`, then `import`, then `publish --wait` (must reach `SUCCESS`).
4. Re-probe: the same `update <CONFIG_ID>` (or `create` if nothing was saved).
5. Three failures on the same reason → stop and show the user the verdict and the hook.

A product can add probes over time. A configuration that passed once can fail on a later `update`; read the new reason the same way.
