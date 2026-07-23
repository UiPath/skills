# rpa-is-connection-not-authorized-cns

Reproduces the #3 Connection Service error by production volume: a connector
activity faults because the Integration Service connection is **no longer in
an authorized state** — the provider rejected token refresh with
`invalid_grant` — surfaced as `CNS1008` (HTTP 400) inside the activity's
`DAP-GE-3000` wrapper. The connection shows `State: Failed` and `ping` fails
with the same code.

Fixtures are hand-authored from the production error signature (Connection
Service traces `StatusCode: BadRequest, ErrorCode: "CNS1008"`); shapes mirror
the sibling `rpa-is-*-dap` scenarios.

## Playbook coverage

This replay covers the connector-key router and the Salesforce-specific
authentication branch in
`playbooks/connectors/uipath-salesforce-sfdc.md`. The mocked connection exposes
the exact `uipath-salesforce-sfdc` key, and the evidence distinguishes a revoked
or expired Salesforce OAuth grant from app approval, API permission, folder
access, connection state, and workflow-input causes.

## How this test reproduces it

| Layer | Simulation |
|---|---|
| Faulted job | `or jobs list/get/logs`: `LeadImport` unattended run faulted at "Create Contact" with the `CNS1008` message embedding the provider's `invalid_grant` |
| Connection state | `is connections list` shows the Salesforce connection in **Failed** state; `ping` fails with HTTP 400 / `CNS1008` and re-authenticate instructions |
| Temporal signature | "Worked for weeks, broke this morning, nothing changed" — the token-expiry/revocation pattern |

## Success criteria

- `skill_triggered` — the uipath-troubleshoot skill actually ran
- `llm_judge` vs [RESOLUTION.md](./RESOLUTION.md) — the diagnosis quotes the
  Salesforce cause contract, identifies the expired/revoked OAuth grant, and
  reauthorizes the existing connection without recreating it or changing
  unrelated permissions
