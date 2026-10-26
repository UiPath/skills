# BYO LLM Product Configurations

Register tenant-owned LLM keys against UiPath products with the `uip llm-configuration byo-connections` CLI family. Supply an Integration Service connection, a shared connections folder, and a product / feature / model triple; the CLI validates server-side and saves the configuration.

> **Preview** — CLI surface may still change.

## Subcommand Surface

Six verbs are available under `uip llm-configuration byo-connections`:

| Command | Purpose |
|---|---|
| `list` | List the current tenant's BYO configurations. `--include-connection-details` resolves connector metadata through Integration Service. |
| `get <id>` | Fetch one configuration by UUID. `--force-refresh` re-resolves connection details. |
| `create` | Create and server-validate a configuration using single-mapping shorthand or repeated `--mapping`. |
| `update <id>` | PUT a fresh wrapper; product and feature are locked and every mapping must be supplied again. |
| `delete <id> --force` | Permanently delete; `--force` is mandatory. |
| `list-product-configs` | Discover products, features, models, api-flavors, and connectors, with per-model and per-alternative allow-lists. |

## Prerequisites

- Log in with `uip login` using an account with the **OrganizationAdmin** role for AI Trust Layer in the target tenant.
- Obtain an Integration Service connection for the target LLM vendor. Run `uip is connections list --output json`; pass its UUID to `--connection-id`. If no suitable connection exists, ask the user before proceeding and create one with `uip is connections create "<connector-key>"` per [Connections](../integration-service/connections.md). Do not fabricate a UUID. Translate `--connector-type` with the table below.
- Obtain a target folder with `uip or folders list --output json`; pass its UUID to `--folder-key`. Ignore folders with `Type: Personal`; use a Standard/shared folder.

## Connector-Type ↔ IS Connector Key

`--connector-type` is the gateway enum used by `byo-connections create` / `update`; `uip is connections create "<connector-key>"` requires the distinct IS connector key.

| `--connector-type` | Vendor | IS connector key for `is connections create` | Covers api-flavors |
|---|---|---|---|
| `OpenAi` | OpenAI direct | `uipath-openai-openai` | `OpenAiChatCompletions`, `OpenAiResponses`, `OpenAiEmbeddings` |
| `AzureOpenAi` | Azure OpenAI | `uipath-microsoft-azureopenai` | `OpenAiChatCompletions`, `OpenAiResponses`, `OpenAiEmbeddings` |
| `AmazonWebServices` | AWS Bedrock | `uipath-aws-bedrock` | `AwsBedrockInvoke`, `AwsBedrockConverse` |
| `OpenAiV1Compatible` | OpenAI-compatible vendors | `uipath-openai-openaiv1compliant` | `OpenAiChatCompletions`, `OpenAiResponses`, `OpenAiEmbeddings` |
| `GoogleVertex` | Google Vertex AI | `uipath-google-vertex` | `GeminiGenerateContent`, `GeminiEmbeddings` |

Always confirm the exact key on the target tenant before creating a connection; keys can vary by environment. Run:

```bash
uip is connectors list --output json
```

If the expected key is absent, retry once with `--refresh`. If still absent, the connector is not enabled on the tenant; stop and tell the user.

## Two Input Shapes for `create` and `update`

The shapes are mutually exclusive:

- **Single-mapping shorthand:** flags `--llm-name`, `--llm-identifier`, `--connector-type`, `--api-flavor`, and `--connection-id`. Use for `AnyModelWithOwnAdditions`, typically when replacing one model.
- **Multi-mapping:** repeat `--mapping 'k=v,...'` once per catalog model. Required for `AllModels` and `AnyModel`, where every catalog model must be mapped. Keys are `llm-name`, `llm-identifier`, `connector-type`, `api-flavor`, `connection-id`, and optional `default-model`.

### `create` — single-mapping example

```bash
uip llm-configuration byo-connections create --product agenthub --feature agenthub-llm-call --folder-key <folder-uuid> --connector-type AmazonWebServices --connection-id <connection-id> --llm-name anthropic.claude-sonnet-4-20250514-v1:0 --llm-identifier eu.anthropic.claude-sonnet-4-20250514-v1:0 --api-flavor AwsBedrockInvoke --output json
```

### `create` — multi-mapping example (AllModels feature)

```bash
uip llm-configuration byo-connections create --product uipath-ecs --feature uipath-ecs-batch-transform-web-search --folder-key <folder-uuid> --mapping 'llm-name=gemini-2.5-flash,llm-identifier=gemini-2.5-flash,connector-type=GoogleVertex,api-flavor=GeminiGenerateContent,connection-id=<connection-id>' --mapping 'llm-name=gemini-2.5-flash-lite,llm-identifier=gemini-2.5-flash,connector-type=GoogleVertex,api-flavor=GeminiGenerateContent,connection-id=<connection-id>' --output json
```

Optional `create` flags:

- `--default-model` — primary model for an operation group with alternatives; defaults to `--llm-name`.
- `--name` — wrapper name override; default `feature-unix-millis`.
- `--enabled` / `--no-enabled` — default true.
- `--tenant <name>` — target a tenant other than the logged-in tenant.

The CLI derives `name` from feature plus epoch ms when omitted, `defaultModel` from `--llm-name` when omitted, `configurationType` as `SelfServe`, and `organizationId` / `tenantId` from login context.

## `update` — full PUT, no merge

`update` rebuilds the wrapper on every invocation. It reads the existing record only to recover locked `product` and `operationGroupName`, and to default `--folder-key` / `--name` from existing values; it then PUTs exactly the supplied mappings. Re-supply every desired mapping: there is no patch mode.

```bash
# Replace the model on a single-mapping config
uip llm-configuration byo-connections update <id> --llm-name gpt-5-2025-08-07 --llm-identifier gpt-5 --connector-type OpenAi --connection-id <connection-id> --api-flavor OpenAiResponses --output json
```

```bash
# Re-supply every mapping for a multi-mapping AllModels config
uip llm-configuration byo-connections update <id> --mapping 'llm-name=gemini-2.5-flash,llm-identifier=gemini-2.5-flash,connector-type=GoogleVertex,api-flavor=GeminiGenerateContent,connection-id=<connection-id>' --mapping 'llm-name=gemini-2.5-flash-lite,llm-identifier=gemini-2.5-flash,connector-type=GoogleVertex,api-flavor=GeminiGenerateContent,connection-id=<connection-id>' --output json
```

To change a `(product, feature)` pair, run `delete` + `create`; those identity fields are immutable on `update`.

## Discovery: `list-product-configs`

Returns one row per (product, feature), with `models[]` and per-model allowed api-flavors/connectors, alternatives where applicable, and optional feature fields:

- `modelsConfigurationOption` — `AllModels`, `AnyModel`, or `AnyModelWithOwnAdditions`; determines the required input shape.
- `addYourOwn` — connector → api-flavors map, present only for `AnyModelWithOwnAdditions`; valid for custom models absent from catalog `models[]`.
- `models[]` — entries contain `model`, `allowedApiFlavors`, `allowedConnectors`, and optional `alternatives[]`.

Flags: `--product <name>` filters a product; `--feature <name>` filters an operation group within `--product`; `--models-only` removes per-model and per-alternative `allowedApiFlavors` / `allowedConnectors` but retains `addYourOwn` and the synthetic generic-alternative entry.

Run:

```bash
uip llm-configuration byo-connections list-product-configs --product agents --feature agents-design-eval-deploy --output json
uip llm-configuration byo-connections list-product-configs --product jarvis --feature jarvis-natural-language-query --output json
```

## Validation: mandatory before save

`create` and `update` always run `POST .../validate` before saving. The probe summary is keyed by model name; multi-mapping results contain one verdict per model. If any model has `isAvailable: false` or `isCompatible: false`, saving aborts and the command exits 1.

Client-side preflight also runs before validate:

1. `--connector-type` must be one of: `OpenAi`, `AzureOpenAi`, `AwsBedrock`, `AmazonWebServices`, `GoogleVertex`, `OpenAiV1Compatible`.
2. `--llm-name` must be in the operation group's declared `models[]`, unless the group is `AnyModelWithOwnAdditions`, the only mode accepting custom additions.
3. `--api-flavor` must match the model's per-model probes when present, or the intersection of feature probes with the vendor catalog otherwise.

There is no skip flag. Fix the mapping and retry.

## Diagnostics

When a BYO configuration is failing, the gateway exposes no per-request CLI logs. Re-probe the configuration and its underlying Integration Service connection.

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

`list --include-connection-details` resolves the underlying IS connection for every BYO record in one pass. Filter for configs whose `connectionState` is not `Enabled`:

```bash
uip llm-configuration byo-connections list \
  --include-connection-details --output json \
  --output-filter "[?ConnectionState!='Enabled'].{id: Id, product: Product, feature: OperationGroupName, connectionState: ConnectionState}"
```

### Cross-checking with trace evidence

When an agent / product run failed and you have a trace ID, fetch spans and cross-reference the BYO configuration:

```bash
uip traces spans get <trace-id> --output json
```

Spans expose the model and provider actually invoked. A mismatch with the BYO config—wrong vendor or fallback to platform default—means the BYO record was not selected. Common causes: `modelsConfigurationOption` is `AllModels` but only some models were mapped; `enabled: false`; or AI Trust Layer policy overrode routing.

### What the CLI does NOT expose

There is no `uip llm-configuration logs`, per-request gateway invocation history, or historical probe-result query. Diagnose current state through `get` / `list` / `update` re-probe and trace evidence owned by `uipath-agents` / `uipath-troubleshoot`. For runtime issues requiring per-call routing history, raise a support ticket with the trace ID.

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
|---|---|---|
| `AiByoConnectionsList` | `list` | Array of wrapper records, each with `llmConfigurations[]`; empty `[]` is valid. |
| `AiByoConnectionsGet` | `get <id>` | One wrapper record. |
| `AiByoConnectionsCreated` | `create` | `{ configuration, validation: { modelName: { isAvailable, isCompatible, isModelNameSimilar } } }`; every multi-mapping model has an entry. |
| `AiByoConnectionsUpdated` | `update <id>` | Same shape as `create`. |
| `AiByoConnectionsDeleted` | `delete <id>` | `{ id }`. |
| `AiByoProductConfigs` | `list-product-configs` | Array of (product, feature) rows. |

A non-zero exit code indicates client-side preflight failure, server-side validation failure (probe summary attached to the error message), or an HTTP / API error. The error path always emits `Result: Failure` with a `Message` and `Instructions`.

## Common Pitfalls

- `AllModels` / `AnyModel` features require one `--mapping` per catalog model in `models[]`; shorthand fails preflight.
- `update` is full-replace, not partial. Supply every desired mapping; only `--folder-key` and `--name` default from the existing record when omitted.
- `delete` without `--force` is a no-op failure; re-run with `--force`.
- `--connection-id` must already exist in Integration Service; credentials resolve lazily and missing connections cause validation failure.
- Validation is mandatory in `create` / `update`; there is no skip flag and any failed probe aborts saving.
- `--product` and `--feature` are case-sensitive; use exact `list-product-configs` values.
- Lists are unpaginated; there are no `--limit` / `--offset` flags.