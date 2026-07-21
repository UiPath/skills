---
confidence: high
---

# Autopilot 429 Too Many Requests

## Context

What this looks like:
- "Failed to apply" error in Autopilot for Maestro (design-time, in the designer)
- HTTP 429 Too Many Requests

What can cause it:
- Rate limiting on the Maestro backend or LLM Gateway side when using Autopilot features

Not this playbook:
- 429 at runtime on an Integration Service connector activity (error code `DAP-RT-1101`, `ProviderErrorCode` 429) - underlying fault is provider-side rate limiting → [request-failed](../../integration-service/playbooks/request-failed.md). Discriminator: a `DAP-RT-1101`/`ProviderErrorCode` is present and the 429 hits a running instance, not the Autopilot designer

## Investigation

1. Confirm the error is HTTP 429 and comes from an Autopilot action in the designer (no `DAP-RT-1101` code, no running instance involved)
2. Check if the issue is intermittent or persistent

## Resolution

- Retry after a short wait
- No permanent fix available yet
