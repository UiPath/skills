# LLM Gateway Playbooks

**Overview:** [overview.md](./overview.md) — service model, dependencies, CLI surface, and what the CLI does **not** expose.

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| BYO LLM Call Failing (underlying IS connection dead) | High | Agent / product LLM call used to work and now fails with auth / provider errors — the IS connection behind the BYO config has been revoked, disabled, or had credentials rotated | [byo-connection-dead.md](./playbooks/byo-connection-dead.md) |
| BYO LLM Validation Probe Failing | Medium | `create` / `update` aborts with `isAvailable: false` or `isCompatible: false` — the model is not reachable through the chosen vendor key + api-flavor, or the catalog drifted since the config was created | [validation-probe-failed.md](./playbooks/validation-probe-failed.md) |
| BYO LLM Routing Bypassed (call hit platform default) | Medium | Trace spans show the platform default model / provider was used despite an active BYO config — the record is disabled, the feature requires multi-mapping and some models were unmapped, or AI Trust Layer policy overrode the routing | [byo-routing-bypassed.md](./playbooks/byo-routing-bypassed.md) |
