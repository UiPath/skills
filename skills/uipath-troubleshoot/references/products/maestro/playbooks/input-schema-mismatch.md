---
confidence: high
---

# Input Does Not Conform to Schema (400)

## Context

What this looks like:
- HTTP 400 at workflow/agent start
- Error message: `Input does not conform to schema` or `Agent.InputArgumentsSchema` error
- Variants: `"Value is 'null' but should be 'object'"` when an optional file/attachment is null
- Used to work, suddenly fails after a new version was published

What can cause it:
- Provided inputs do not match the JSON schema declared on the process/agent: wrong types, missing required fields, extra fields, or unsupported types
- For queue transactions: `DateTime` must be passed as string; arrays are not supported
- Optional file/attachment parameters passed as `null` — schema rejects `null` where it expects an `object`
- Newly published version added a required parameter (e.g., `modelName` on GenAI activities) that older callers don't pass
- Stale agent metadata from a previous publish — Maestro still references the old `InputArgumentsSchema`

What to look for:
- Compare the actual payload (Variables API) against the agent's/process's declared input schema (`inputDefinitions`)
- Confirm whether the failure started after a new package version was deployed

## Investigation

> Substitute `<type>` with `bpmn`, `flow`, or `case` per the [Maestro investigation guide](../investigation_guide.md) § Determine the Maestro process type.


1. Get the incident: `uip maestro <type> instance incidents <instance-id> -f <folder-key> --output json`
2. Pull the actual inputs and the schema: `uip maestro <type> instance variables <instance-id> -f <folder-key> --output json` — compare values vs `inputDefinitions`
3. Identify the failing parameter from `errorDetails` — the schema validator names the offending field/type
4. Check the package version that introduced the breaking change — list releases and diff schemas

## Resolution

- **If type/field mismatch:** correct the payload to match the schema exactly (types, required fields, no extras)
- **If null optional file/attachment:** either omit the field entirely or pass a valid empty-shaped object the schema accepts
- **If queue payload:** convert `DateTime` to string; flatten arrays
- **If new required parameter added:** make it optional with a default value, or update all callers
- **If stale agent metadata:** delete the deployed agent and let the next solution publish re-create it (last-resort workaround)

## References

- [Docs: About Input and Output Arguments](https://docs.uipath.com/orchestrator/standalone/2023.4/user-guide/about-input-and-output-arguments)
- [Docs: About Queues and Transactions](https://docs.uipath.com/orchestrator/standalone/2024.10/user-guide/about-queues-and-transactions)
