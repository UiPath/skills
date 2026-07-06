---
confidence: medium
---

# Response Mapping Mismatch (DAP-RT-1005 / DAP-RT-1155 / DAP-RT-1156)

> **Fault bucket: 🛠 B1 — IS platform / connector defect (escalate to owner team).** The provider returned data but the connector's declared output schema no longer matches it (connector schema drift). No provider error status — the mapping fails inside IS after a successful call. The customer cannot fix connector metadata; updating the activity package to a matching version is the only customer-side mitigation. Lead with: "This is a connector schema-drift issue on the service side — update the activity package if a matching version exists, otherwise contact the owner team (Integration Service)." See [dap-error-codes-reference.md](../dap-error-codes-reference.md#fault-ownership--the-two-bucket-decision).

## Context

What this looks like — the provider call succeeded but IS could not map the response into the activity's output type:

| Code | Name | Specific cause |
|---|---|---|
| `DAP-RT-1005` | ApiResponseMismatch | Response shape doesn't match the activity's output type — connector schema drift |
| `DAP-RT-1155` | DataTableFieldTypeMismatch | A response field's type doesn't match the expected TypedDataTable column |
| `DAP-RT-1156` | TypedDataTableNotConstructedProperly | Output could not be assembled into the expected TypedDataTable |

What can cause it:
- The connector's response schema changed (provider API version drift) but the workflow's activity package is older
- The activity's declared output type no longer matches what the provider returns
- A field returned as a different type than the TypedDataTable column expects (e.g. string where a number is mapped)

Concrete scenario (`DAP-RT-1005`): a workflow was published months ago with a Salesforce activity package whose "Get Record" output declares `AnnualRevenue` as a number. The vendor (or a connector schema update) now returns that field as a string, or renames/removes it. Every run since: the provider call itself succeeds (HTTP 200, data returned), but IS fails to deserialize the payload into the activity's generated output type — the job faults at the mapping step with no provider error. Nothing changed in the workflow; the schema drifted underneath it. The same shape triggers `1155`/`1156` when the drifted field feeds a TypedDataTable column.

What to look for:
- No provider error status — the failure is IS-side mapping, not a provider error (the call returned data)
- The activity package version vs the current connector schema (drift is the usual cause of `1005`)
- `ProviderErrorMessage` is typically absent — the provider returned 200; mapping failed afterward

## Investigation

1. **Confirm it is a mapping failure, not a provider error** — there should be no `ProviderErrorCode` / provider status. If a provider status is present, use [request-failed.md](./request-failed.md).
2. **Read the connection resource file** — identify the connector and connection (see "Connection Resource File" in [overview.md](../overview.md)).
3. `uip is resources describe <connector-key> <object-name>` — get the current field definitions and compare against the activity's declared output type.
4. `uip is activities list <connector-key>` — check whether the activity/package version in the project lags the current connector schema.

## Resolution

- **`DAP-RT-1005` — schema drift:** update the connector activity package in the project to the version that matches the current response schema, then re-map the output and republish.
- **`DAP-RT-1155` — field type mismatch:** correct the TypedDataTable column type to match the field returned by `uip is resources describe`, or transform the field before mapping.
- **`DAP-RT-1156`:** re-create the output mapping from the current schema so the TypedDataTable is constructed from valid columns.
- If the provider genuinely changed its contract, align the activity configuration to the new schema rather than forcing the old mapping.
