---
confidence: medium
---

# Integration Services 400 — Bad Request to Connector

## Context

What this looks like:
- HTTP 400 from an Integration Service call
- Error message: `Request to Integration Services failed with status code '400'`
- Often paired with a connector-side error body (multipart parse failure, schema mismatch, etc.)

What can cause it:
- Malformed or invalid request body for the connector action
- Connector update changed expected `Content-Type` (e.g., Outlook moved from `application/json` to `multipart/form-data` for attachments) breaking already-published activities — historical bug `ENGCE-46376`
- A previously-bound variable was removed but the connector activity still references it, sending an empty string `""` instead of `null` (Office 365 Send Email historical issue, `PLT-77820`)
- Mismatched connector input schema after a connector version bump
- Bad connection state (token, scopes) — connection should be re-provisioned

What to look for:
- Connector name / action from `errorDetails` and element executions
- Whether the failure started after a connector update or Maestro publish
- Whether the same action works against a freshly-recreated connector activity

## Investigation

> Substitute `<type>` with `bpmn`, `flow`, or `case` per the [Maestro investigation guide](../investigation_guide.md) § Determine the Maestro process type.


1. Get the incident: `uip maestro <type> instance incidents <instance-id> -f <folder-key> --output json` — capture upstream connector error body
2. Identify the failing connector activity and connection: `uip maestro <type> instance element-executions <instance-id> -f <folder-key> --output json`
3. Pull the activity inputs: `uip maestro <type> instance variables <instance-id> -f <folder-key> --parent-element-id <element-id> --output json` — look for empty strings where nulls are expected, missing required fields, or wrong types
4. Check the connection's health in Orchestrator UI → **Integration Service > Connections** — re-authenticate if expired
5. Look up the connector version and compare against the version when the workflow was last published

## Resolution

- **If empty string from removed variable:** delete and re-add the connector step so it stops referencing the orphaned variable
- **If `Content-Type` / multipart mismatch after connector update:** delete and re-add the activity to pick up the new schema
- **If schema bump:** update the inputs to match the new schema or pin to the prior connector version where supported
- **If connection in bad state:** re-provision the connection, then re-publish or rebind the activity
- **If genuinely malformed payload:** validate the input JSON against the connector spec

## Notes

- This error is **Not Troubleshootable** from PIMS API alone — incident lacks the actual HTTP request that went to IS and the connector configuration details. Plan to log a connector telemetry ask if this becomes common in your investigation

## References

- [Docs: Connections Troubleshooting](https://docs.uipath.com/integration-service/automation-cloud/latest/user-guide/connections-troubleshooting)
