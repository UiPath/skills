---
confidence: medium
---

# Get Asset Failed — External Credential Store Failure

## Context

A `Get Credential` or `Get Orchestrator Credential` activity failed because the external credential store (CyberArk, Azure Key Vault, Thycotic, or other vault) is unreachable or misconfigured.

What this looks like:
- Error code 2303: `"Invalid Credential Store configuration"`
- Error code 2304: `"Failed to read from Credential Store type <X>"`

What can cause it:
- Vault endpoint unreachable from the Orchestrator server (firewall, network)
- CyberArk: FIPS mode enabled on Windows, 32/64-bit SDK mismatch, wrong web service name
- Azure Key Vault: Orchestrator IP not whitelisted, secret contains backslash, wrong key-pair format
- Thycotic: incorrect integration URL or credentials in Orchestrator settings
- Credential store plugin settings incomplete or incorrect (error 2303)

What to look for:
- Vault type from the error message
- Network connectivity between Orchestrator server and vault endpoint
- Credential store configuration in Orchestrator > Credential Stores

## Investigation

1. Identify the vault type from the error message.
2. Verify Orchestrator can reach the vault endpoint — check firewall/network rules from the Orchestrator server.
3. For **CyberArk**: check for FIPS mode on Windows (incompatible with CyberArk SDK), 32/64-bit SDK mismatch, and web service name in Orchestrator credential store settings. On Orchestrator 2020.10.8–2021.10.1, set `Plugins.SecureStores.CyberArk.UsePowerShellCLI=false` in configuration (fixed in 2022.4+).
4. For **Azure Key Vault**: verify the Orchestrator server IP is whitelisted in Key Vault network settings, the secret value does not contain a backslash (`\`), and the secret is in the expected key-pair format.
5. For **Thycotic**: verify integration settings (URL, credentials) in Orchestrator > Credential Stores.
6. For error 2303: check all credential store plugin settings (URL, application ID, credentials) for completeness and correctness.

## Resolution

- **If vault endpoint unreachable:** open network access from the Orchestrator server to the vault, then retest.
- **If vault configuration incorrect:** fix the specific misconfiguration identified above and re-test by running the job.
- **If secret format is wrong:** update the secret in the vault to match the expected format.
