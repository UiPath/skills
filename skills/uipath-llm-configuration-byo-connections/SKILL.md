---
name: uipath-llm-configuration-byo-connections
description: "Manage Bring-Your-Own (BYO) LLM product configurations in the UiPath LLM Gateway via `uip llm-configuration byo-connections`. Use when the user mentions BYO LLM, custom AI provider, bringing their own OpenAI / Azure OpenAI / Bedrock / Anthropic / Google Vertex key, registering an external LLM, or wiring a tenant-owned API key into UiPath products. The CLI wraps the product-level llm-configurations endpoints on the LLM Gateway. For tenant-wide AI governance (allowed providers, blocked models) → uipath-gov-aops-policy."
allowed-tools: Bash, Read
---

# UiPath BYO LLM Product Configurations

> **Preview** — skill is under active development; the underlying CLI surface may change.

Skill for registering tenant-owned LLM keys against UiPath products via the `uip llm-configuration byo-connections` family of CLI commands. The user supplies:

- An Integration Service connection (carrying the vendor credentials),
- A connections folder,
- A product / feature / model triple,

and the CLI builds the configuration, validates it server-side, and saves it.

## When to Use This Skill

Activate when the user asks to:

- **Register a tenant-owned LLM key** with UiPath: "I want to use my own OpenAI key for agents", "wire my Azure OpenAI deployment into the assistant", "swap the default model for Anthropic Claude in agenthub".
- **Configure a model substitution** for a specific UiPath product feature (`agents-design-eval-deploy`, `agenthub-llm-call`, `jarvis-natural-language-query`, etc.).
- **Inspect / list / update / delete** existing BYO configurations for the tenant.
- **Discover what's allowed**: which products, features, models, connectors, and api-flavors can be configured.

Do **NOT** activate (redirect to `uipath-gov-aops-policy` instead) when the user asks about:

- Tenant-wide vendor allowlists ("allow only Anthropic for my tenant").
- Blocking specific models or providers.
- Other AI Trust Layer governance policy concerns.

## Subcommand Surface

Six verbs under `uip llm-configuration byo-connections`:

| Command | Purpose |
|---------|---------|
| `list` | List BYO product configurations for the current tenant. `--include-connection-details` resolves connector metadata (slower; calls Integration Service). |
| `get <id>` | Fetch one configuration by UUID. `--force-refresh` re-resolves connection details from Integration Service. |
| `add` | Create a configuration. Two input shapes (single-mapping shorthand, or repeated `--mapping` for multi-model features). Validates server-side before saving. |
| `update <id>` | PUT a fresh wrapper for an existing configuration. Identity fields (product, feature) are locked; every mapping must be re-supplied. |
| `delete <id> --force` | Permanently delete. `--force` is mandatory — the command refuses without it. |
| `list-product-configs` | Discover what's allowed: products, features, models, api-flavors, connectors. Returns one row per (product, feature) with nested per-model and per-alternative allow-lists. |

## Prerequisites

- **Logged in**: `uip login` with an account that has the **OrganizationAdmin** role for AI Trust Layer in the target tenant.
- **An Integration Service connection** for the LLM vendor whose key you want to register. Discover with `uip is connections list --output json`. The connection's UUID is what `--connection-id` takes. **If none exists for the target vendor, ASK the user before proceeding** — connection creation is handled by the `uipath-platform` skill via `uip is connections create "<connector-key>"`. Translate `--connector-type` to the right IS connector key using the **Connector-Type ↔ IS Connector Key** table below. Do not fabricate a UUID.
- **A target connections folder** exists. Discover with `uip or folders list --output json`. Its UUID is what `--folder-id` takes.

## Connector-Type ↔ IS Connector Key

`--connector-type` (used on `byo-connections add` / `update`) is the gateway-side enum. `uip is connections create "<connector-key>"` (used by the `uipath-platform` skill) takes the **IS connector key** — a different identifier. Use this table to translate before asking `uipath-platform` to create a connection.

| `--connector-type` | Vendor | IS connector key for `is connections create` | Covers api-flavors |
|---|---|---|---|
| `OpenAi` | OpenAI direct | `uipath-openai-openai` | `OpenAiChatCompletions`, `OpenAiResponses`, `OpenAiEmbeddings` |
| `AzureOpenAi` | Azure OpenAI | `uipath-microsoft-azureopenai` | `OpenAiChatCompletions`, `OpenAiResponses`, `OpenAiEmbeddings` |
| `AmazonWebServices` | AWS Bedrock | `uipath-aws-bedrock` | `AwsBedrockInvoke`, `AwsBedrockConverse` |
| `OpenAiV1Compatible` | OpenAI-compatible vendors | `uipath-openai-openaiv1compliant` | `OpenAiChatCompletions`, `OpenAiResponses`, `OpenAiEmbeddings` |
| `GoogleVertex` | Google Vertex AI | `uipath-google-vertex` | `GeminiGenerateContent`, `GeminiEmbeddings` |

Always confirm the exact key on the target tenant before handing off — connector keys can vary by environment. Verify with:

```bash
uip is connectors list --output json
```

If the expected key is not in the list, retry once with `--refresh`. If still missing, the connector is not enabled on this tenant — stop and tell the user.

## Two Input Shapes for `add` and `update`

The `add` and `update` commands accept either:

- **Single-mapping shorthand** — one inner config — using flags like `--llm-name`, `--llm-identifier`, `--connector-type`, `--api-flavor`, `--connection-id`. Use this for `AnyModelWithOwnAdditions` features (the typical case where the customer is replacing one model).
- **Multi-mapping form** — `--mapping 'k=v,...'` repeatable, one per catalog model. **Required** for `AllModels` and `AnyModel` features (every catalog model must be mapped). Each mapping uses comma-separated key=value pairs: `llm-name`, `llm-identifier`, `connector-type`, `api-flavor`, `connection-id`, optional `default-model`.

The two shapes are mutually exclusive on a single invocation.

### `add` — single-mapping example

```bash
uip llm-configuration byo-connections add --product agenthub --feature agenthub-llm-call --folder-id <folder-id> --connector-type AmazonWebServices --connection-id <connection-id> --llm-name anthropic.claude-sonnet-4-20250514-v1:0 --llm-identifier eu.anthropic.claude-sonnet-4-20250514-v1:0 --api-flavor AwsBedrockInvoke --output json
```

### `add` — multi-mapping example (AllModels feature)

```bash
uip llm-configuration byo-connections add --product uipath-ecs --feature uipath-ecs-batch-transform-web-search --folder-id <folder-id> --mapping 'llm-name=gemini-2.5-flash,llm-identifier=gemini-2.5-flash,connector-type=GoogleVertex,api-flavor=GeminiGenerateContent,connection-id=<connection-id>' --mapping 'llm-name=gemini-2.5-flash-lite,llm-identifier=gemini-2.5-flash,connector-type=GoogleVertex,api-flavor=GeminiGenerateContent,connection-id=<connection-id>' --output json
```

### Optional `add` flags

- `--default-model` — primary model for an operation group with alternatives. Defaults to `--llm-name`.
- `--name` — override the auto-generated wrapper name (default: `feature-unix-millis`).
- `--enabled` / `--no-enabled` — default true.
- `--tenant <name>` — target a tenant other than the logged-in one.

The CLI auto-derives `name` (from feature + epoch ms when omitted), `defaultModel` (equals `--llm-name` when omitted), `configurationType` (always `SelfServe`), and `organizationId` / `tenantId` (from login context).

## `update` — full PUT, no merge

`update` rebuilds the wrapper from scratch on every invocation. The command reads the existing record only to recover its locked identity fields (product, operationGroupName) and to default `--folder-id` / `--name` to the existing values; it then PUTs a wrapper containing exactly the mappings supplied.

Implication: every model mapping the user wants in the resulting record must be in this invocation, either via single-mapping shorthand flags or via repeated `--mapping`. There is no "patch one field" mode.

```bash
# Replace the model on a single-mapping config
uip llm-configuration byo-connections update <id> --llm-name gpt-5-2025-08-07 --llm-identifier gpt-5 --connector-type OpenAi --connection-id <connection-id> --api-flavor OpenAiResponses --output json
```

```bash
# Re-supply every mapping for a multi-mapping AllModels config
uip llm-configuration byo-connections update <id> --mapping 'llm-name=gemini-2.5-flash,llm-identifier=gemini-2.5-flash,connector-type=GoogleVertex,api-flavor=GeminiGenerateContent,connection-id=<connection-id>' --mapping 'llm-name=gemini-2.5-flash-lite,llm-identifier=gemini-2.5-flash,connector-type=GoogleVertex,api-flavor=GeminiGenerateContent,connection-id=<connection-id>' --output json
```

To move a configuration to a different `(product, feature)` pair, use `delete` + `add` — those identity fields are immutable on `update`.

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

Both `add` and `update` always run `POST .../validate` server-side before saving. The probe summary is keyed by model name — for multi-mapping configs you get a per-model verdict. If any model reports `isAvailable: false` or `isCompatible: false`, the save is aborted and the command exits 1.

The CLI also runs **client-side preflight** before sending validate, catching the most common errors offline:

1. `--connector-type` must be one of: `OpenAi`, `AzureOpenAi`, `AwsBedrock`, `AmazonWebServices`, `GoogleVertex`, `OpenAiV1Compatible`.
2. `--llm-name` must be in the operation group's declared `models[]`, **unless** the group is `AnyModelWithOwnAdditions` (the only mode that accepts custom additions).
3. `--api-flavor` must match the model's per-model probes (when present) or the intersection of feature probes with the vendor catalog (otherwise).

There is no skip flag. Fix the offending mapping and retry.

## Typical Flow

1. **Identify the feature shape**: run `list-product-configs --product P --feature F --output json` and read `modelsConfigurationOption`. If it's `AllModels` or `AnyModel`, you must use multi-mapping. If it's `AnyModelWithOwnAdditions`, use single-mapping.
2. **Get a connection id**: `uip is connections list --output json` — copy the vendor's connection UUID. If the list has no connection for the target vendor, STOP and ask the user: *"No Integration Service connection found for &lt;vendor&gt;. Want me to hand off to the `uipath-platform` skill to create one (`uip is connections create "<connector-key>"`)? I'll resume here once it's enabled."* Use the **Connector-Type ↔ IS Connector Key** table above to pick the right `<connector-key>` based on the `--connector-type` and api-flavor you intend to register. Do not invent a UUID and do not proceed without one — server-side validation will fail with an unavailability reason.
3. **Get the folder id**: `uip or folders list --output json` — pick the folder you want the configuration in.
4. **Create**: invoke `byo-connections add` with the right input shape (single-mapping or repeated `--mapping`). Server-side validation runs automatically.
5. **Confirm**: `byo-connections list --output json` — record appears.
6. **Inspect**: `byo-connections get <id> --output json` — resolved connection details.

## Expected Output

| Code | Command | Data |
|------|---------|------|
| `AiByoConnectionsList` | `list` | Array of wrapper records, each with `llmConfigurations[]`. Empty list `[]` is a valid result. |
| `AiByoConnectionsGet` | `get <id>` | One wrapper record. |
| `AiByoConnectionsAdded` | `add` | `{ configuration, validation: { modelName: { isAvailable, isCompatible, isModelNameSimilar } } }` — every model in the multi-mapping body gets its own validation entry. |
| `AiByoConnectionsUpdated` | `update <id>` | Same shape as `add`. |
| `AiByoConnectionsDeleted` | `delete <id>` | `{ id }`. |
| `AiByoProductConfigs` | `list-product-configs` | Array of (product, feature) rows. |

A non-zero exit code indicates either client-side preflight failure, server-side validation failure (probe summary attached to the error message), or an HTTP / API error. The error path always emits `Result: Failure` with a `Message` and `Instructions`.

## Common Pitfalls

- **`AllModels` / `AnyModel` features require one `--mapping` per catalog model in `models[]`.** Single-mapping shorthand will fail preflight on these features.
- **`update` is full-replace, not partial.** Every mapping you want in the resulting record must be supplied on the call. Flags you omit revert to defaults from the existing record only for `--folder-id` and `--name`.
- **`delete` without `--force` is a no-op failure** — by design. Re-run with `--force`.
- **`--connection-id` must exist in Integration Service first** — credentials are resolved lazily. If the connection is missing, server-side validation surfaces an unavailability reason and aborts.
- **Validation is mandatory in `add` / `update`** — no skip flag. The save is aborted if any model fails the probe.
- **`--product` and `--feature` are case-sensitive.** Use the exact values from `list-product-configs`.
- **Lists are unpaginated** — there are no `--limit` / `--skip` flags here.

## Out of Scope

- **Creating Integration Service connections** — delegate to the `uipath-platform` skill (`uip is connections create "<connector-key>"`). When the user has no connection for the target vendor, ask whether to hand off; resume this skill once an enabled connection exists.
- **Provisioning UiPath products** themselves — this skill assumes the product is already enabled for the tenant.
