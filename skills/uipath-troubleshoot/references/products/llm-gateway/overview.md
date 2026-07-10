# LLM Gateway

The LLM Gateway is the UiPath service that routes agent / product LLM calls to a model — either the platform default or a tenant-owned (BYO) provider key. It exposes a single CLI surface for configuration management: `uip llm-configuration byo-connections`. There is **no first-class CLI for per-request gateway logs** — diagnosis is current-state + trace-evidence only.

A BYO LLM product configuration is the record that says: "for product `P` and feature `F`, route LLM calls through Integration Service connection `C` to model `M` via vendor `V`". When agent calls fail with model / provider errors, the BYO record is one of three places to look — the others are the underlying IS connection and tenant-wide AI Trust Layer policy.

## Organization Model

```
Tenant
  └── BYO LLM Product Configuration       ← one per (product, operationGroupName)
        ├── product                       ← e.g. agents, agenthub, jarvis, ixp, uipath-ecs
        ├── operationGroupName (feature)  ← e.g. agenthub-llm-call, agents-design-eval-deploy
        ├── enabled                       ← gates whether this record is honored
        ├── llmConfigurations[]           ← model mappings
        │     ├── llmName / llmIdentifier  ← what the customer registered
        │     ├── connectorType            ← OpenAi / AzureOpenAi / AmazonWebServices / GoogleVertex / OpenAiV1Compatible
        │     ├── apiFlavor                ← OpenAiResponses / OpenAiChatCompletions / AwsBedrockInvoke / ...
        │     └── connectionId             ← Integration Service connection UUID (the credentials)
        └── validation (server-side probes, last write)
              └── modelName: {isAvailable, isCompatible, isModelNameSimilar}
```

## Dependencies

- **Integration Service** — every BYO configuration points at an IS connection (`connectionId`) for credentials. If the IS connection is disabled, revoked, or rotated, the BYO config's runtime calls fail. See [Integration Service playbooks](../integration-service/summary.md).
- **AI Trust Layer (Governance)** — tenant-wide policies on allowed providers / blocked models can override BYO routing at runtime. See `uip gov aops-policy` and [`uipath-governance`](/uipath:uipath-governance).
- **Agent / product runtime** — the consumer of the LLM call (agents, agenthub, jarvis, IXP). The agent's trace spans are the only per-request evidence available.
- **LLM Observability traces** — `uip traces spans get <trace-id>` returns spans with the model + provider that was actually invoked. Owned by `uipath-agents` / this skill, not the LLM Gateway CLI itself.

## Features

- **BYO LLM product configurations** — register tenant-owned LLM keys against UiPath product features. Six verbs: `list`, `get`, `create`, `update`, `delete`, `list-product-configs`.
- **Server-side validation probes** — `create` and `update` always run `POST .../validate`. The probe summary is keyed by model and reports `isAvailable` / `isCompatible` / `isModelNameSimilar`. This is **mandatory and the only diagnostic exposed at write time**.
- **Connection-detail resolution** — `get --force-refresh` and `list --include-connection-details` re-resolve the underlying IS connection state. This is the primary read-time diagnostic.

## CLI

```
uip llm-configuration byo-connections list                          — list all BYO configs for the tenant
uip llm-configuration byo-connections list --include-connection-details  — list with IS connection state resolved
uip llm-configuration byo-connections get <id> --force-refresh      — fetch one config and re-resolve connection details
uip llm-configuration byo-connections list-product-configs          — discover allowed (product, feature, model, connector, api-flavor) combinations
uip llm-configuration byo-connections create / update / delete      — mutate (write-time validation is mandatory)
```

Key commands for troubleshooting:

- `uip llm-configuration byo-connections get <id> --force-refresh --output json` — re-resolve the underlying connection state for a single BYO config
- `uip llm-configuration byo-connections list --include-connection-details --output json` — tenant audit: every BYO config + the live state of its IS connection
- `uip llm-configuration byo-connections list-product-configs --product <p> --feature <f> --output json` — confirm the saved mapping still matches the product's current allowed-model catalog
- `uip llm-configuration byo-connections update <id> --<same-fields>` — idempotent re-write that forces a fresh server-side probe; surfaces current `isAvailable` / `isCompatible`
- `uip gov aops-policy deployed-policy resolve --product AITrustLayer ... --output json` — resolve the tenant-effective AI Trust Layer policy when calls are blocked by governance
- `uip traces spans get <trace-id> --output json` — read the actual model + provider invoked on a failing agent call

## What the CLI does NOT expose

There is **no** `uip llm-configuration logs`, **no** per-request gateway invocation history, **no** time-series probe results, and **no** vendor-side error history without re-probing. If a runtime issue cannot be explained by current state or trace evidence, the next step is a support ticket with the trace ID — not further CLI investigation.

## See Also

- Configuration reference (Build / Operate / Diagnose flows): [`uipath-platform` → `references/llmgateway/byo-connections.md`](/uipath:uipath-platform)
- AI Trust Layer policy authoring + `deployed-policy resolve` diagnostics: [`uipath-governance`](/uipath:uipath-governance)
- Trace inspection for the consuming agent: [`uipath-agents`](/uipath:uipath-agents)
