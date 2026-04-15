# System Activities Playbooks

**Investigation guide:** [investigation_guide.md](./investigation_guide.md) — data correlation rules and testing prerequisites for System Activities investigations

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Get Asset — Wrong Activity for Asset Type | High | `Get Asset` used on a Credential or `Get Credential` used on a Text/Integer/Boolean asset | [get-asset-wrong-activity-type.md](./playbooks/get-asset-wrong-activity-type.md) |
| Get Asset — Asset Does Not Exist | High | Asset not found in the Orchestrator folder where the job runs (error code 1002) | [get-asset-not-found.md](./playbooks/get-asset-not-found.md) |
| Get Asset — Permission Denied | High | Robot account lacks View permission on Assets (HTTP 403, error code 0) | [get-asset-permission-denied.md](./playbooks/get-asset-permission-denied.md) |
| Get Asset — Folder Scope Mismatch | High | Wrong `OrchestratorFolderPath` or classic/modern folder incompatibility (error codes 1100, 1101) | [get-asset-folder-scope-mismatch.md](./playbooks/get-asset-folder-scope-mismatch.md) |
| Get Asset — Per-Robot Asset Has No Value | High | Per-robot asset has no value entry for the executing robot | [get-asset-per-robot-no-value.md](./playbooks/get-asset-per-robot-no-value.md) |
| Get Asset — Robot Not Authenticated or Unlicensed | Medium | Robot not authenticated or not licensed against Orchestrator (error code 0, package regressions) | [get-asset-robot-not-authenticated.md](./playbooks/get-asset-robot-not-authenticated.md) |
| Get Asset — External Credential Store Failure | Medium | External vault (CyberArk, Azure Key Vault, Thycotic) unreachable or misconfigured (error codes 2303, 2304) | [get-asset-external-vault-failure.md](./playbooks/get-asset-external-vault-failure.md) |
| Get Asset — Activity Bug / Silent Failure | Medium | Activity completes without exception but output is null/zero/empty (copy-paste or package 22.10.x bug) | [get-asset-activity-bug-silent-failure.md](./playbooks/get-asset-activity-bug-silent-failure.md) |
| Get Asset — Network or Connectivity Issue | Low | Network, TLS, proxy, or session expiry between robot and Orchestrator | [get-asset-network-connectivity.md](./playbooks/get-asset-network-connectivity.md) |
