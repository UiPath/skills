---
confidence: high
signatures:
  - kind: http-status
    value: "429"
    note: "Autopilot for Maestro apply-failure — backend/LLM Gateway rate limiting; Microsoft Graph 429 on an O365 activity → request-throttled.md (o365-activities)"
  - kind: message
    value: "Failed to apply"
    note: "Autopilot for Maestro surface — backend/LLM Gateway rate limiting"
---

# Autopilot 429 Too Many Requests

## Context

What this looks like:
- "Failed to apply" error in Autopilot for Maestro
- HTTP 429 error

What can cause it:
- Rate limiting on the Maestro backend or LLM Gateway side when using Autopilot features

## Investigation

1. Confirm the error is HTTP 429
2. Check if the issue is intermittent or persistent

## Resolution

- Retry after a short wait
- No permanent fix available yet
