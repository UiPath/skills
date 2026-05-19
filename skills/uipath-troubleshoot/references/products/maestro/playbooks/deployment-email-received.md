---
confidence: high
---

# Deployment Error — EMAIL_RECEIVED

## Context

What this looks like:
- Deployment fails with error code 4006
- Error: "No package resource with type 'Property' and key 'EMAIL_RECEIVED' was found"

What can cause it:
- Integration Service component exposed a new property on the Outlook email received trigger that was out of sync with the packaging component

## Investigation

1. Confirm the error code is 4006 and the message references "EMAIL_RECEIVED"

## Resolution

- Open the email received trigger configuration in Studio Web and republish the solution
- Verify deployment succeeds and the trigger fires correctly in the target environment
