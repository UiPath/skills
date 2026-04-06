---
confidence: high
---

# Autopilot 429 Too Many Requests

## Context

What this looks like:
- "Failed to apply" error in Autopilot for Maestro
- HTTP 429 error

What can cause it:
- Rate limiting on the Maestro backend or LLM Gateway side when using Autopilot features (tracked via MST-7255)

## Investigation

1. Confirm the error is HTTP 429
2. Check if the issue is intermittent or persistent

## Resolution

- Retry after a short wait
- No permanent fix available yet (tracked via MST-7255)
