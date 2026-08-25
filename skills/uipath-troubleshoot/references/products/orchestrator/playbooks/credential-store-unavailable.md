---
confidence: medium
---

# Credential Store Unavailable — Cannot Retrieve Robot Credential

## Context

A job fails to start because Orchestrator cannot **retrieve** the robot credential from its credential store — the store backend itself is unreachable or misconfigured. This is distinct from a wrong/expired password (see `robot-credentials.md` / `job-faulted-logon-failure.md`): here the credential is never obtained at all, so no Windows logon is even attempted.

What this looks like:
- `Unable to retrieve credentials from Orchestrator Database credential store. Please check your connection settings and ensure the Orchestrator Database service is running.`
- Or, for an external store: errors naming CyberArk / Azure Key Vault / HashiCorp Vault (vault unreachable, secret not found, or access denied)
- Job faults at/near start with a credential-**retrieval** error, not a `Logon failed` / `0x0000052E` code
- Often affects **every** robot/asset bound to the same store simultaneously (store-wide, not one user)

What can cause it (branches):
1. **Orchestrator Database store unreachable** — the Orchestrator SQL database (which backs the default "Orchestrator Database" credential store) is down, or the connection string / network path to it is broken.
2. **External vault unreachable / misconfigured** — the CyberArk / Azure Key Vault / HashiCorp store's endpoint, credentials, or network path is wrong or the vault is down.
3. **Secret missing / access denied in the store** — the credential record was deleted/renamed in the store, or Orchestrator's service principal lost read permission.
4. **Store misconfiguration** — the credential store definition in Orchestrator points at the wrong instance/path after a migration or config change.

## Investigation

1. Get the failing job and confirm the signature (retrieval, not logon):
   `uip or jobs get <job-key> --output json` — `Info` names the credential store / retrieval, with no `Logon failed` code.
2. Read logs for the store-side error detail:
   `uip or jobs logs <job-key> --level Error --output json` — which store (Orchestrator DB vs external vault), and the underlying reason (connection, not-found, access-denied).
3. Establish scope — is it store-wide?
   `uip or jobs list --state Faulted --output json` — if many robots/processes bound to the same store fail at once, the store backend is the problem (branch 1/2), not one credential.
4. Identify which credential store the robot/asset uses (Orchestrator → Credentials/Assets → the robot user or credential asset → Credential Store). Confirm the store type (Orchestrator Database vs CyberArk/AKV/HashiCorp).

## Resolution

- **Branch 1 — Orchestrator Database store unreachable:** verify the Orchestrator SQL database service is running and reachable from Orchestrator (connection string, network, firewall). Restore DB connectivity, then rerun. (This is an Orchestrator-infrastructure dependency — see `overview.md` § Dependencies.)
- **Branch 2 — external vault unreachable/misconfigured:** check the credential store definition (endpoint URL, app/credential, network reachability) and that the vault service is up. Use Orchestrator's **Test** on the credential store to confirm connectivity, fix the config, rerun.
- **Branch 3 — secret missing / access denied:** confirm the credential exists in the store under the expected name and that Orchestrator's identity has read permission; re-create/re-grant as needed.
- **Branch 4 — store misconfiguration after a change:** repoint the credential store to the correct instance/path; re-test.

Prevention:
- Monitor the credential store backend (SQL DB / vault) health and alert on retrieval failures — store outages are store-wide.
- After any store or DB migration, run the store's **Test** and a canary job before re-enabling triggers.
