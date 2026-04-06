---
confidence: high
---

# Integration Service Failure (404)

## Context

What this looks like:
- HTTP 404 during an Integration Service call
- Resource or endpoint not found

What can cause it:
- Incorrect or outdated endpoint URL in the connection configuration
- Target resource does not exist or is misconfigured in the external service

## Investigation

1. Verify the endpoint URL in the Integration Service connection configuration
2. Check if the target resource exists in the external service

## Resolution

- Update endpoint URLs in the connection configuration
- Ensure target resources are available and correctly named in the external service
- Coordinate with integration service owners for API changes
