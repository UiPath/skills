# LLM Gateway - BYO Routing Bypassed by AI Trust Layer Policy

Faithful-replay scenario for the `uipath-troubleshoot` skill. It covers a BYO
LLM routing investigation where the BYO product configuration is enabled and
the Integration Service connection is healthy, but the effective AI Trust Layer
policy blocks the BYO provider/model.

## What this exercises

The scenario locks in the current governance command shape:

```bash
uip gov aops-policy deployed-policy get NoLicense AITrustLayer 00000000-0000-4000-8000-000000000100 --output json
```

This guards against reverting to the removed flag-based `resolve` command.

## Mock surface

| Command | Fixture |
|---|---|
| `traces spans get <trace-id>` | `trace-byo-default-model.json` |
| `llm-configuration byo-connections list --include-connection-details` | `byo-connections-list.json` |
| `llm-configuration byo-connections list-product-configs` | `product-configs.json` |
| `gov aops-policy deployed-policy get NoLicense AITrustLayer <tenant-id>` | `deployed-policy-get.json` |
