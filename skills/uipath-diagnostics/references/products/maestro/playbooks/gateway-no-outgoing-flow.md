---
confidence: high
---

# No Outgoing Flow Condition Met (400001)

## Context

What this looks like:
- HTTP 400, Maestro error code `400001` (`NoOutgoingFlow`)
- Error message: `No condition for an outgoing flow was met. At least one outgoing flow condition needs to evaluate to true or have a default flow.`
- Always raised by an Exclusive or Inclusive Gateway

What can cause it:
- All outgoing sequence flow conditions evaluated to `false` and no default flow was configured
- Variable ID mismatch — designer-side bug where renaming a variable leaves expressions bound to the old variable ID, so they read the wrong value
- Boolean variable populated via Actionable Messages (email approval) arriving in an unexpected shape
- Condition expressions reference a variable that is uninitialized on some execution paths

What to look for:
- The gateway name in `errorDetails` and the variables it depends on
- Whether a default flow is configured on the gateway in the BPMN XML
- Whether any variable was renamed recently in Studio Web

## Investigation

1. Get the incident: `uip maestro instance incidents <instance-id> -f <folder-key> --output json`
2. **If `IncludeGatewayDebugInfoInIncidents` is enabled** ([PO.BpmnEngine PR #3092](https://github.com/UiPath/PO.BpmnEngine/pull/3092)): `errorDetails` already lists each outgoing flow's condition expression, the default flow config, and variable values at evaluation time — no further data gathering needed
3. **If the flag is not enabled:** pull the BPMN XML to read gateway conditions: `uip maestro instance asset <instance-id> -f <folder-key> --output json`
4. Pull the variables snapshot just before the gateway element: `uip maestro instance variables <instance-id> -f <folder-key> --parent-element-id <gateway-id> --output json`
5. Walk element executions to confirm which gateway: `uip maestro instance element-executions <instance-id> -f <folder-key> --output json`

## Resolution

- **If no default flow:** add a default flow on the gateway in the BPMN modeler — set one outgoing sequence flow as the default; this path is taken when no conditions match
- **If conditions are not exhaustive:** broaden the conditions to cover all possible runtime values
- **If variable ID mismatch after rename:** open the gateway in Studio Web and **re-select** the correct variable in each condition expression; do not just retype the name
- **If variable is uninitialized on some paths:** assign a default earlier in the flow so the variable is always defined before reaching the gateway
- **If actionable messages payload:** verify the boolean comes back in the expected shape; consider routing through Action Center if Actionable Messages keeps yielding unexpected values

## Notes

- Pre-PR #3092: this error is **Not Diagnosable** from PIMS API alone — agents had to ask the user for the `.bpmn` and walk variables manually
- Post-PR #3092 with the targeted feature flag enabled: this error is **Fully Diagnosable** — incident `errorDetails` contains everything needed
- Variable values in enriched `errorDetails` are truncated to 200 chars per variable

## References

- [PR #3092 — Enrich NoOutgoingFlow incident with gateway debug info](https://github.com/UiPath/PO.BpmnEngine/pull/3092)
- [Docs: Gateways and Flow Logic](https://docs.uipath.com/maestro/automation-cloud/latest/user-guide/gateways-flow-logic)
- [Docs: Gateways](https://docs.uipath.com/maestro/automation-cloud/latest/user-guide/gateways)
