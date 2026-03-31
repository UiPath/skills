---
confidence: medium
---

# Operation Failed

## Context

What this looks like:
- Integration Service activity returns an error during execution
- Maestro error codes: 102002 (IntSvcOperationFailed), 102003 (IntSvcBadRequest), 102004 (IntSvcMethodNotSupported), 102010 (IntSvcArgumentsError)
- The connection is active but the specific operation fails

What can cause it:
- Invalid or missing input parameters for the activity
- The external service API changed or deprecated the endpoint
- The operation requires fields or permissions not available with the current connection scope
- Rate limiting or quota exceeded on the external service
- Resource referenced in the operation does not exist in the external service

What to look for:
- The specific error code and message detail
- Whether the same operation worked before (regression vs misconfiguration)
- Whether other operations on the same connector succeed (isolates operation vs connection issue)

## Investigation

1. Identify the connector, activity, and input parameters from the error or binding
2. Run `uip is connections ping <connection-id>` to confirm the connection is healthy
3. Run `uip is activities list <connector-key>` to verify the activity exists and is supported
4. Run `uip is resources describe <connector-key> <object-name>` to check required fields and operations
5. Check if the external service API has changed or if rate limits apply

## Resolution

- **If bad request / invalid input:** fix the input parameters to match the activity's required schema (use `uip is resources describe` for field definitions)
- **If method not supported:** the connector may not support this operation — check connector documentation or use a different activity
- **If external service changed:** update the activity configuration to match the new API schema
- **If rate limited:** implement retry logic or reduce call frequency
