# BYO LLM Product Configurations

Register tenant-owned LLM keys against UiPath products with `uip llm-configuration byo-connections`. The user supplies an Integration Service connection, a shared connections folder, and a product/feature/model mapping; the CLI validates server-side and saves it.

> **Preview** — CLI surface may still change.

## Command surface

| Command | Purpose |
|---|---|
| `list` | List tenant BYO configurations. `--include-connection-details` resolves Integration Service metadata and is slower. |
| `get <id>` | Fetch one configuration. `--force-refresh` re-resolves connection details. |
| `create` | Create and validate using single-mapping shorthand or repeated `--mapping`. |
| `update <id>` | Full PUT; product and feature identity are locked and every desired mapping must be supplied. |
| `delete <id> --force` | Permanently delete; `--force` is mandatory. |
| `list-product-configs` | Discover products, features, models, api-flavors, connectors, and alternatives. |

## Prerequisites

- Log in with `uip login` using an account with the **OrganizationAdmin** role for AI Trust Layer in the target tenant.
- Run `uip is connections list --output json`. Use a suitable real connection UUID as `--connection-id`; never fabricate one. If none exists, ask whether to create one with `uip is connections create "<connector-key>"` per [Connections](../integration-service/connections.md), and do not proceed without a real ID.
- Run `uip or folders list --output json`. Choose a Standard folder and ignore `Type: Personal`. If only Personal folders exist, ask the user to provide or create a non-personal folder.
- Run `uip is connectors list --output json`. If the expected key is absent, retry once with `--refresh`; if still absent, stop and report that the connector is not enabled on the tenant.

### Connector-Type ↔ IS Connector Key

`--connector-type` is the gateway enum; `uip is connections create "<connector-key>"` requires the IS connector key. Translate with this table and verify the exact key on the target tenant:

| `--connector-type` | Vendor | IS connector key | Covers api-flavors |
|---|---|---|---|
| `OpenAi` | OpenAI direct | `uipath-openai-openai` | `OpenAiChatCompletions`, `OpenAiResponses`, `OpenAiEmbeddings` |
| `AzureOpenAi` | Azure OpenAI | `uipath-microsoft-azureopenai` | `OpenAiChatCompletions`, `OpenAiResponses`, `OpenAiEmbeddings` |
| `AmazonWebServices` | AWS Bedrock | `uipath-aws-bedrock` | `AwsBedrockInvoke`, `AwsBedrockConverse` |
| `OpenAiV1Compatible` | OpenAI-compatible vendors | `uipath-openai-openaiv1compliant` | `OpenAiChatCompletions`, `OpenAiResponses`, `OpenAiEmbeddings` |
| `GoogleVertex` | Google Vertex AI | `uipath-google-vertex` | `GeminiGenerateContent`, `GeminiEmbeddings` |

## Input shapes and defaults

`create` and `update` accept exactly one form:

- **Single-mapping shorthand**: `--llm-name`, `--llm-identifier`, `--connector-type`, `--api-flavor`, and `--connection-id`; use for `AnyModelWithOwnAdditions`.
- **Multi-mapping**: repeat `--mapping 'k=v,...'` once per catalog model; required for `AllModels` and `AnyModel`. Keys are `llm-name`, `llm-identifier`, `connector-type`, `api-flavor`, `connection-id`, and optional `default-model`.

Optional `create` flags are `--default-model`, `--name`, `--enabled` / `--no-enabled`, and `--tenant <name>`. Defaults are `defaultModel` = `--llm-name`, `configurationType` = `SelfServe`, auto-generated `name` = `feature-unix-millis`, and `organizationId` / `tenantId` from login context.

Run one of these generic forms:

```bash
uip llm-configuration byo-connections create --product <product> --feature <feature> --folder-key <folder-uuid> --llm-name <model> --llm-identifier <identifier> --connector-type <type> --api-flavor <flavor> --connection-id <connection-id> --output json
```

```bash
uip llm-configuration byo-connections create --product <product> --feature <feature> --folder-key <folder-uuid> --mapping 'llm-name=<model>,llm-identifier=<identifier>,connector-type=<type>,api-flavor=<flavor>,connection-id=<connection-id>' --output json
```

`--default-model` selects the primary model for an operation group with alternatives; otherwise it defaults to `--llm-name`.

## Discovery and validation

Run:

```bash
uip llm-configuration byo-connections list-product-configs --product <product> --feature <feature> --output json
```

Each row represents `(product, feature)` and may contain `modelsConfigurationOption`: `AllModels`, `AnyModel`, or `AnyModelWithOwnAdditions`; `addYourOwn`: connector → api-flavors, present only for `AnyModelWithOwnAdditions`; and `models[]` entries with `model`, `allowedApiFlavors`, `allowedConnectors`, and optional `alternatives[]`.

Supported flags are `--product <name>`, `--feature <name>`, and `--models-only`. `--models-only` removes per-model and per-alternative `allowedApiFlavors` / `allowedConnectors`, while retaining `addYourOwn` and the synthetic generic-alternative entry.

Run validation automatically through `create` and `update`; there is no skip flag. Multi-mapping results contain a probe verdict per model. Abort and fix the mapping if any model has `isAvailable: false` or `isCompatible: false`.

Apply these client preflight checks:

1. `--connector-type` must be one of `OpenAi`, `AzureOpenAi`, `AwsBedrock`, `AmazonWebServices`, `GoogleVertex`, or `OpenAiV1Compatible`.
2. `--llm-name` must be in the feature’s `models[]`, except that `AnyModelWithOwnAdditions` permits custom additions.
3. `--api-flavor` must match the model’s probes when present, or the intersection of feature probes and the vendor catalog otherwise.

## Update semantics

`update` is full replacement, not merge. It reads the existing record only to recover locked `product` and `operationGroupName` and to default `--folder-key` and `--name`; the PUT contains exactly the supplied mappings. Re-supply every mapping wanted in the result. To change a `(product, feature)` pair, run `delete <id> --force`, then run `create`.

## Typical flow

1. Run `list-product-configs --product P --feature F --output json`; use `modelsConfigurationOption` to select single- or multi-mapping.
2. Ask which connector/vendor to register unless already specified. Offer only connector types allowed by `addYourOwn` / `allowedConnectors`; do not infer intent from an existing connection.
3. Run `uip is connections list --output json`; use the chosen vendor connection UUID. If none exists, ask whether to run `uip is connections create "<connector-key>"` using the table above. Do not proceed without a real connection ID.
4. Run `uip or folders list --output json`; choose a non-`Personal` folder.
5. Present catalog models whose `allowedConnectors` include the selected connector. For `AnyModelWithOwnAdditions`, also offer a custom model and validate its flavor against `addYourOwn[<connector-type>]`.
6. Ask whether the vendor identifier equals the model name. Use a different `--llm-identifier` when required for deployments, inference profiles, or aliases; skip only when both values were supplied.
7. Run `byo-connections create` with the correct input shape; validation runs automatically.
8. Run `byo-connections list --output json` and confirm the record.
9. Run `byo-connections get <id> --output json` and inspect resolved connection details.

## Diagnostics

The gateway exposes no per-request logs through CLI. Diagnose current state with `get`, `list`, and an idempotent `update` re-probe; use traces for routing evidence.

For a previously working configuration:

1. Run `uip llm-configuration byo-connections get <id> --force-refresh --output json` and inspect `connectionState` / `enabled`.
2. Run an idempotent `update` with the same `--llm-name`, `--llm-identifier`, `--connector-type`, `--api-flavor`, and `--connection-id` to force fresh validation.
3. Run `uip llm-configuration byo-connections list-product-configs --product <product> --feature <feature> --output json`; compare current `models[]` and `addYourOwn[<connector-type>]` with saved `llmName` and `apiFlavor`.
4. For policy-shaped gateway errors, run `uip gov aops-policy deployed-policy resolve --product AITrustLayer --license-type <type> --tenant <name> --output json`. See [uipath-governance](/uipath:uipath-governance).

For a tenant audit, run:

```bash
uip llm-configuration byo-connections list --include-connection-details --output json --output-filter "Data[?connectionState!='Enabled'].{id: id, product: product, feature: operationGroupName, connectionState: connectionState}"
```

With a trace ID, run:

```bash
uip traces spans get <trace-id> --output json
```

Compare the invoked model and provider with the BYO record. A mismatch indicates that the record was not selected; common causes are incomplete `AllModels` mappings, `enabled: false`, or AI Trust Layer policy override.

The CLI does not expose `uip llm-configuration logs`, per-request gateway history, or historical probe-result queries. Runtime issues requiring routing history need a support ticket with the trace ID; traces are owned by `uipath-agents` / `uipath-troubleshoot`.

## Expected output

| Code | Command | Data |
|---|---|---|
| `AiByoConnectionsList` | `list` | Array of wrapper records containing `llmConfigurations[]`; `[]` is valid. |
| `AiByoConnectionsGet` | `get <id>` | One wrapper record. |
| `AiByoConnectionsCreated` | `create` | `{ configuration, validation: { modelName: { isAvailable, isCompatible, isModelNameSimilar } } }`; multi-mapping has one entry per model. |
| `AiByoConnectionsUpdated` | `update <id>` | Same shape as `create`. |
| `AiByoConnectionsDeleted` | `delete <id>` | `{ id }`. |
| `AiByoProductConfigs` | `list-product-configs` | Array of `(product, feature)` rows. |

A non-zero exit code indicates client preflight failure, server validation failure with a probe summary, or an HTTP/API error. The error path emits `Result: Failure` with `Message` and `Instructions`.

## Common pitfalls

- `AllModels` and `AnyModel` require one `--mapping` per catalog model in `models[]`.
- `update` replaces the entire mapping set; omitted mappings are removed. Only `--folder-key` and `--name` default from the existing record.
- `delete` without `--force` fails by design.
- `--connection-id` must already exist in Integration Service; credentials resolve lazily.
- Validation cannot be skipped, and saving aborts when any model fails.
- `--product` and `--feature` are case-sensitive; use values from `list-product-configs`.
- These lists are unpaginated; there are no `--limit` / `--offset` flags.