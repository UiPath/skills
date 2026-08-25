# BYO LLM Product Configurations

Register tenant-owned LLM keys against UiPath products via the `uip llm-configuration byo-connections` family of CLI commands. The user supplies an Integration Service connection (carrying the vendor credentials), a connections folder, and a product / feature / model triple; the CLI builds the configuration, validates it server-side, and saves it.

> **Preview** — CLI surface may still change.

---

## Subcommand Surface

Six verbs under `uip llm-configuration byo-connections`:

| Command | Purpose |
|---------|---------|
| `list` | List BYO product configurations for the current tenant. `--include-connection-details` resolves connector metadata (slower; calls Integration Service). |
| `get <id>` | Fetch one configuration by UUID. `--force-refresh` re-resolves connection details from Integration Service. |
| `create` | Create a configuration. Two input shapes (single-mapping shorthand, or repeated `--mapping` for multi-model features). Validates server-side before saving. |
| `update <id>` | PUT a fresh wrapper for an existing configuration. Identity fields (product, feature) are locked; every mapping must be re-supplied. |
| `delete <id> --force` | Permanently delete. `--force` is mandatory — the command refuses without it. |
| `list-product-configs` | Discover what's allowed: products, features, models, api-flavors, connectors. Returns one row per (product, feature) with nested per-model and per-alternative allow-lists. |

## Prerequisites

- **Logged in**: `uip login` with an account that has the **OrganizationAdmin** role for AI Trust Layer in the target tenant.
- **An Integration Service connection** for the LLM vendor whose key you want to register. Discover with `uip is connections list --output json`. The connection's UUID is what `--connection-id` takes. If none exists for the target vendor, ask the user before proceeding — create one with `uip is connections create "<connector-key>"` per [Connections](../integration-service/connections.md). Translate `--connector-type` to the right IS connector key using the **Connector-Type ↔ IS Connector Key** table below. Do not fabricate a UUID.
- **A target connections folder** exists. Discover with `uip or folders list --output json`. Its UUID is what `--folder-key` takes. **Ignore folders with `Type: Personal`** — pick a Standard (shared) folder instead.

## Connector-Type ↔ IS Connector Key

`--connector-type` (used on `byo-connections create` / `update`) is the gateway-side enum. `uip is connections create "<connector-key>"` takes the **IS connector key** — a different identifier. Use this table to translate before creating an Integration Service connection.

| `--connector-type` | Vendor | IS connector key for `is connections create` | Covers api-flavors |
|---|---|---|---|
| `OpenAi` | OpenAI direct | `uipath-openai-openai` | `OpenAiChatCompletions`, `OpenAiResponses`, `OpenAiEmbeddings` |
| `AzureOpenAi` | Azure OpenAI | `uipath-microsoft-azureopenai` | `OpenAiChatCompletions`, `OpenAiResponses`, `OpenAiEmbeddings` |
| `AmazonWebServices` | AWS Bedrock | `uipath-aws-bedrock` | `AwsBedrockInvoke`, `AwsBedrockConverse` |
| `OpenAiV1Compatible` | OpenAI-compatible vendors | `uipath-openai-openaiv1compliant` | `OpenAiChatCompletions`, `OpenAiResponses`, `OpenAiEmbeddings` |
| `GoogleVertex` | Google Vertex AI | `uipath-google-vertex` | `GeminiGenerateContent`, `GeminiEmbeddings` |

Always confirm the exact key on the target tenant before creating a connection — connector keys can vary by environment. Verify with:

```bash
uip is connectors list --output json
```

If the expected key is not in the list, retry once with `--refresh`. If still missing, the connector is not enabled on this tenant — stop and tell the user.

## Two Input Shapes for `create` and `update`

The `create` and `update` commands accept either:

- **Single-mapping shorthand** — one inner config — using flags like `--llm-name`, `--llm-identifier`, `--connector-type`, `--api-flavor`, `--connection-id`. Use this for `AnyModelWithOwnAdditions` features (the typical case where the customer is replacing one model).
- **Multi-mapping form** — `--mapping 'k=v,...'` repeatable, one per catalog model. **Required** for `AllModels` and `AnyModel` features (every catalog model must be mapped). Each mapping uses comma-separated key=value pairs: `llm-name`, `llm-identifier`, `connector-type`, `api-flavor`, `connection-id`, optional `default-model`.

The two shapes are mutually exclusive on a single invocation.

### `create` — single-mapping example

```bash
uip llm-configuration byo-connections create --product agenthub --feature agenthub-llm-call --folder-key <folder-uuid> --connector-type AmazonWebServices --connection-id <connection-id> --llm-name anthropic.claude-sonnet-4-20250514-v1:0 --llm-identifier eu.anthropic.claude-sonnet-4-20250514-v1:0 --api-flavor AwsBedrockInvoke --output json
```

### `create` — multi-mapping example (AllModels feature)

```bash
uip llm-configuration byo-connections create --product uipath-ecs --feature uipath-ecs-batch-transform-web-search --folder-key <folder-uuid> --mapping 'llm-name=gemini-2.5-flash,llm-identifier=gemini-2.5-flash,connector-type=GoogleVertex,api-flavor=GeminiGenerateContent,connection-id=<connection-id>' --mapping 'llm-name=gemini-2.5-flash-lite,llm-identifier=gemini-2.5-flash,connector-type=GoogleVertex,api-flavor=GeminiGenerateContent,connection-id=<connection-id>' --output json
```

### Optional `create` flags

- `--default-model` — primary model for an operation group with alternatives. Defaults to `--llm-name`.
- `--name` — override the auto-generated wrapper name (default: `feature-unix-millis`).
- `--enabled` / `--no-enabled` — default true.
- `--tenant <name>` — target a tenant other than the logged-in one.

The CLI auto-derives `name` (from feature + epoch ms when omitted), `defaultModel` (equals `--llm-name` when omitted), `configurationType` (always `SelfServe`), and `organizationId` / `tenantId` (from login context).

## `update` — full PUT, no merge

`update` rebuilds the wrapper from scratch on every invocation. The command reads the existing record only to recover its locked identity fields (product, operationGroupName) and to default `--folder-key` / `--name` to the existing values; it then PUTs a wrapper containing exactly the mappings supplied.

Implication: every model mapping the user wants in the resulting record must be in this invocation, either via single-mapping shorthand flags or via repeated `--mapping`. There is no "patch one field" mode.

```bash
# Replace the model on a single-mapping config
uip llm-configuration byo-connections update <id> --llm-name gpt-5-2025-08-07 --llm-identifier gpt-5 --connector-type OpenAi --connection-id <connection-id> --api-flavor OpenAiResponses --output json
```

```bash
# Re-supply every mapping for a multi-mapping AllModels config
uip llm-configuration byo-connections update <id> --mapping 'llm-name=gemini-2.5-flash,llm-identifier=gemini-2.5-flash,connector-type=GoogleVertex,api-flavor=GeminiGenerateContent,connection-id=<connection-id>' --mapping 'llm-name=gemini-2.5-flash-lite,llm-identifier=gemini-2.5-flash,connector-type=GoogleVertex,api-flavor=GeminiGenerateContent,connection-id=<connection-id>' --output json
```

To move a configuration to a different `(product, feature)` pair, use `delete` + `create` — those identity fields are immutable on `update`.

## Discovery: `list-product-configs`

Returns one row per (product, feature). Each row has the model list with per-model allowed api-flavors and connectors, plus optional per-feature fields:

- `modelsConfigurationOption` — `AllModels`, `AnyModel`, or `AnyModelWithOwnAdditions`. Tells you whether you need the multi-mapping form.
- `addYourOwn` — connector → api-flavors map. Present only on `AnyModelWithOwnAdditions` features. Lists, per connector, which api-flavors are valid when adding a customer model not in the catalog `models[]`.
- `models[]` — each entry has `model`, `allowedApiFlavors`, `allowedConnectors`, and optional `alternatives[]` for features whose primaries declare alternatives.

Flags:

- `--product <name>` — filter to one product.
- `--feature <name>` — filter to one operation group within `--product`.
- `--models-only` — strip per-model and per-alternative `allowedApiFlavors` / `allowedConnectors`. Keeps `addYourOwn` and the synthetic generic-alternative entry untouched. Handy when you only want the model list.

```bash
uip llm-configuration byo-connections list-product-configs --product agents --feature agents-design-eval-deploy --output json
```

```bash
uip llm-configuration byo-connections list-product-configs --product jarvis --feature jarvis-natural-language-query --output json
```

## Validation: mandatory before save

Both `create` and `update` always run `POST .../validate` server-side before saving. The probe summary is keyed by model name — for multi-mapping configs you get a per-model verdict. If any model reports `isAvailable: false` or `isCompatible: false`, the save is aborted and the command exits 1.

The CLI also runs **client-side preflight** before sending validate, catching the most common errors offline:

1. `--connector-type` must be one of: `OpenAi`, `AzureOpenAi`, `AwsBedrock`, `AmazonWebServices`, `GoogleVertex`, `OpenAiV1Compatible`.
2. `--llm-name` must be in the operation group's declared `models[]`, **unless** the group is `AnyModelWithOwnAdditions` (the only mode that accepts custom additions).
3. `--api-flavor` must match the model's per-model probes (when present) or the intersection of feature probes with the vendor catalog (otherwise).

There is no skip flag. Fix the offending mapping and retry.

## Diagnostics

When a BYO LLM configuration is in place but agent / product calls are failing or behaving unexpectedly, the gateway does not expose per-request logs via CLI. Diagnose by re-probing the configuration and its underlying Integration Service connection.

### "This config was working yesterday, now LLM calls fail"

1. **Re-resolve the underlying IS connection.** `--force-refresh` bypasses cached connection details and re-queries Integration Service. If the connection has been disabled, revoked, or rotated, the resolved `connectionState` / `enabled` field will flip.

   ```bash
   uip llm-configuration byo-connections get <id> --force-refresh --output json
   ```

2. **Re-run server-side validation by issuing an idempotent `update`.** `update` always re-runs `POST .../validate`. Re-sending the same mapping forces a fresh probe of the vendor key against the catalog model and surfaces `isAvailable: false` / `isCompatible: false` with a current reason.

   ```bash
   uip llm-configuration byo-connections update <id> \
     --llm-name <same> --llm-identifier <same> \
     --connector-type <same> --api-flavor <same> \
     --connection-id <same> --output json
   ```

3. **Check whether the product's allowed-model catalog drifted.** A model may have been removed from the feature's `models[]` since you registered the config, which makes the saved `--llm-name` invalid against current preflight rules.

   ```bash
   uip llm-configuration byo-connections list-product-configs \
     --product <product> --feature <feature> --output json
   ```

   Compare the returned `models[]` and `addYourOwn[<connector-type>]` against the saved configuration's `llmName` and `apiFlavor`.

4. **If the call is being rejected at the gateway with a policy-shaped error (vendor blocked, model not allowed), check tenant-wide AI Trust Layer policy.** BYO records what the customer asked for; AI Trust Layer governance can still override at runtime.

   ```bash
   uip gov aops-policy deployed-policy resolve \
     --product AITrustLayer --license-type <type> --tenant <name> --output json
   ```

   See [uipath-governance](/uipath:uipath-governance) for full AOps policy diagnostics.

### Tenant audit — "which BYO configs are pointing at dead connections?"

`list --include-connection-details` resolves the underlying IS connection for every BYO record in one pass. Filter the output for configs whose `connectionState` is not `Enabled`.

```bash
uip llm-configuration byo-connections list \
  --include-connection-details --output json \
  --output-filter "Data[?connectionState!='Enabled'].{id: id, product: product, feature: operationGroupName, connectionState: connectionState}"
```

### Cross-checking with trace evidence

When an agent / product run failed and you have a trace ID, fetch the spans and cross-reference the BYO config the call should have routed through:

```bash
uip traces spans get <trace-id> --output json
```

Spans expose the model + provider that was actually invoked. A mismatch with the BYO config — wrong vendor, fallback to platform default — is the diagnostic signal: the BYO record was not selected. Common causes: the feature's `modelsConfigurationOption` is `AllModels` but only some models were mapped; the config is `enabled: false`; AI Trust Layer policy overrode the routing.

### What the CLI does NOT expose

There is no `uip llm-configuration logs`, no per-request gateway invocation history, and no historical probe-result query. Diagnose is limited to **current state** (via `get` / `list` / `update` re-probe) and **trace evidence** (which is owned by `uipath-agents` / `uipath-troubleshoot`). For runtime issues that require per-call routing history, raise a support ticket with the trace ID.

## Typical Flow

1. **Identify the feature shape**: run `list-product-configs --product P --feature F --output json` and read `modelsConfigurationOption`. If it's `AllModels` or `AnyModel`, you must use multi-mapping. If it's `AnyModelWithOwnAdditions`, use single-mapping.
2. **Ask the user which connector / vendor** to register, unless the user has already named it explicitly. Offer the supported `--connector-type` values relevant to the feature's `addYourOwn` / `allowedConnectors` (typically `OpenAi`, `AzureOpenAi`, `AmazonWebServices`, `GoogleVertex`, `OpenAiV1Compatible`). Do not assume the connector from whatever connection happens to exist — multiple vendor connections may be present, and the user's intent determines which one to use.
3. **Get a connection id**: `uip is connections list --output json` — copy the chosen vendor's connection UUID. If the list has no connection for the target vendor, stop and ask the user whether to create one: `uip is connections create "<connector-key>"` (see [Connections](../integration-service/connections.md)). Use the **Connector-Type ↔ IS Connector Key** table above to pick the right `<connector-key>` based on the `--connector-type` and api-flavor you intend to register. Do not invent a UUID and do not proceed without one — server-side validation will fail with an unavailability reason.
4. **Get the folder id**: `uip or folders list --output json` — pick the folder you want the configuration in. **Filter out folders whose `Type` is `Personal`** — BYO configurations belong in shared/standard folders, not in per-user personal workspaces. If only Personal folders are returned, stop and ask the user which non-personal folder to use (or to create one).
5. **Pick the model (`--llm-name`)**: present the feature's catalog `models[]` (filtered to those whose `allowedConnectors` include the chosen `--connector-type`). **If the feature's `modelsConfigurationOption` is `AnyModelWithOwnAdditions`, always offer an extra "Add a custom model" option** alongside the catalog choices — that mode is the only one that accepts non-catalog model names, and customers frequently want to register a model the catalog doesn't list yet. For a custom model, the user supplies the `--llm-name` freely; validate the chosen `--api-flavor` against the feature's `addYourOwn[<connector-type>]` list.
6. **Confirm the `--llm-identifier`**: by default the deployment/identifier sent to the vendor matches `--llm-name`, but they often differ — e.g. Azure OpenAI deployment names, AWS Bedrock region-prefixed inference profile IDs (`eu.anthropic.claude-...`), or OpenAI-compatible aliases. **Ask the user explicitly** whether the identifier the vendor expects matches the model name, or if a different value should be passed to `--llm-identifier`. Only skip the question if the user already provided both values.
7. **Create**: invoke `byo-connections create` with the right input shape (single-mapping or repeated `--mapping`). Server-side validation runs automatically.
8. **Confirm**: `byo-connections list --output json` — record appears.
9. **Inspect**: `byo-connections get <id> --output json` — resolved connection details.

## Expected Output

| Code | Command | Data |
|------|---------|------|
| `AiByoConnectionsList` | `list` | Array of wrapper records, each with `llmConfigurations[]`. Empty list `[]` is a valid result. |
| `AiByoConnectionsGet` | `get <id>` | One wrapper record. |
| `AiByoConnectionsCreated` | `create` | `{ configuration, validation: { modelName: { isAvailable, isCompatible, isModelNameSimilar } } }` — every model in the multi-mapping body gets its own validation entry. |
| `AiByoConnectionsUpdated` | `update <id>` | Same shape as `create`. |
| `AiByoConnectionsDeleted` | `delete <id>` | `{ id }`. |
| `AiByoProductConfigs` | `list-product-configs` | Array of (product, feature) rows. |

A non-zero exit code indicates either client-side preflight failure, server-side validation failure (probe summary attached to the error message), or an HTTP / API error. The error path always emits `Result: Failure` with a `Message` and `Instructions`.

## Common Pitfalls

- **`AllModels` / `AnyModel` features require one `--mapping` per catalog model in `models[]`.** Single-mapping shorthand will fail preflight on these features.
- **`update` is full-replace, not partial.** Every mapping you want in the resulting record must be supplied on the call. Flags you omit revert to defaults from the existing record only for `--folder-key` and `--name`.
- **`delete` without `--force` is a no-op failure** — by design. Re-run with `--force`.
- **`--connection-id` must exist in Integration Service first** — credentials are resolved lazily. If the connection is missing, server-side validation surfaces an unavailability reason and aborts.
- **Validation is mandatory in `create` / `update`** — no skip flag. The save is aborted if any model fails the probe.
- **`--product` and `--feature` are case-sensitive.** Use the exact values from `list-product-configs`.
- **Lists are unpaginated** — there are no `--limit` / `--offset` flags here.
