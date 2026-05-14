---
confidence: low
---

# Generic Error_400 — Bad Request With No Details

## Context

What this looks like:
- Error code: `400`, error name: `Error_400` (no specific name)
- Incident `errorDetails` is empty or non-actionable
- API data alone is not enough to root-cause — must inspect upstream response body

What can cause it:
- Malformed JSON payload
- Request headers too long (HA setups with mismatched token-signing certs)
- Invalid `Content-Type` (must be `application/json`)
- Expired auth token
- Maestro frontend bug — historically `MST-4535` "actionable messages" feature surfaced as generic 400 when a new app version was available

What to look for:
- Whether actionable messages toggle is enabled on the failing app — if yes, this is the known frontend bug
- Whether the workflow uses a custom HTTP request task with hand-crafted headers/body
- Whether the issue is tied to a specific HA tenant

## Investigation

1. Get the incident: `uip maestro instance incidents <instance-id> -f <folder-key> --output json` — capture any HTTP body returned upstream
2. Pull the activity inputs to see what was actually sent: `uip maestro instance variables <instance-id> -f <folder-key> --output json`
3. If the failing element is an Action App task with actionable messages enabled, jump straight to the `MST-4535` resolution
4. For HA setups, request platform logs from the Maestro service — generic 400 here often points to token-signing certificate mismatch across nodes

## Resolution

- **If actionable messages bug (`MST-4535`):** turn OFF the "Enable actionable messages" toggle on the Action App task. Frontend fix is deployed to disable by default — re-publish to pick it up
- **If malformed JSON:** validate the payload structure
- **If Content-Type:** set `application/json`
- **If expired token:** rotate the auth token and retry
- **If HA token-signing mismatch:** sync the token-signing certificates across all nodes (platform/infra owner)

## Notes

- This error is **Not Troubleshootable** from PIMS API alone — full root cause typically requires ADX logs or Temporal history
- When the incident gives nothing useful, ask the user for the failing element name and whether they recently re-published the app

## References

- [Forum: 400 Bad Request](https://forum.uipath.com/t/400-bad-request/506399)
