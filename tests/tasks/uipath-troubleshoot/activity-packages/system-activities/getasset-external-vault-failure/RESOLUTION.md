# Final Resolution

---

**Root Cause:** The Credential asset `MyCyberArkSecret` in the
`Remote Debugging` folder is backed by an external **CyberArk** vault
(`CredentialStoreId` references the "Production CyberArk Store"). The
CyberArk vault endpoint is currently unreachable / misconfigured from
the Orchestrator host, so the value cannot be retrieved. Orchestrator
returns error code 2304 / "Failed to read from Credential Store type
'CyberArk'." — the failing layer is the external vault, not the asset
itself.

**What went wrong:** The `AssetVaultFailure` job (started
2026-05-13T15:42:08Z) faulted ~1.4 seconds after launch because
Orchestrator could not read the credential value from the backing
CyberArk vault.

**Why:** The workflow's `GetRobotCredential` activity targets
`AssetName="MyCyberArkSecret"` with `FolderPath="Remote Debugging"`.
At every Orchestrator-side layer the configuration is correct: the
folder exists, the asset is present in the folder asset list with
`ValueType: "Credential"` and `ValueScope: "Global"`, the executing
robot (`RobotUser1`) has the necessary roles (`Robot` + `Asset
Administrator`) and a valid `Unattended` license. The asset record,
however, sets `CredentialStoreId` to the non-default
"Production CyberArk Store" — i.e., the credential's *value* is not
stored inside Orchestrator's database; it's stored in an external
CyberArk vault. When Orchestrator tried to fetch the value, the
CyberArk endpoint was unreachable (network, firewall, expired SDK
configuration, FIPS-mode mismatch, or similar). Orchestrator surfaced
this as error code 2304 with the vault type explicitly named.

This is **not** an asset-layer issue. The asset is fine; the external
vault that holds the asset's value is the failing component.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: AssetVaultFailure — Faulted at 2026-05-13T15:42:09.402Z (ran for ~1.4 seconds)
- Folder: Remote Debugging (key `4f7a9b3d-2e8c-4f6b-9d5a-1c2b3d4e5f6a`) — folder exists
- Executing robot: `RobotUser1` (Connected, Licensed, has Asset Administrator role)

### System Activities (Surface)
- Activity (from `Main.xaml`): `GetRobotCredential` (DisplayName: "Get Credential") — correct activity for a Credential asset
- AssetName (from `Main.xaml`): `MyCyberArkSecret`
- Asset record in Orchestrator: `ValueType: "Credential"`, `ValueScope: "Global"`, `CredentialStoreId: "a3e7b2c5-4d8f-49a1-b6c2-8e7d1f3a5b9c"` (NOT the default Orchestrator store)
- Error at 2026-05-13T15:42:09.380Z: `[Get Credential] Status code: 500 (Internal Server Error). Orchestrator response: Failed to read from Credential Store type 'CyberArk'. Error code: 2304`

### Credential Stores (Root Cause)
- Credential store referenced by the asset: "Production CyberArk Store" (id `a3e7b2c5-4d8f-49a1-b6c2-8e7d1f3a5b9c`), `Type: "CyberArk"`
- The Orchestrator side records the store as configured, but the read from the vault fails. The error code 2304 fires when Orchestrator successfully resolved the store binding but failed to fetch the value from the vault. Whether the vault endpoint is unreachable (network/firewall/DNS) or the store is misconfigured (wrong endpoint URL, web service name, FIPS/SDK mismatch) cannot be distinguished from Orchestrator-side evidence — both readings are acceptable, and the remediation checks below cover both.

---

**Immediate fix:**

The fix is **outside the asset and workflow layers** — it's on the
Orchestrator-to-CyberArk path.

### Credential Stores (Root Cause)

1. **Verify network connectivity between the Orchestrator host and the CyberArk vault endpoint.**
   - **Why:** Error code 2304 means Orchestrator resolved the credential store binding but couldn't reach the vault. Most common cause is firewall / DNS / proxy on the Orchestrator host.
   - **Where:** From the Orchestrator server, run `nslookup <vault-hostname>` and `Test-NetConnection <vault-hostname> -Port <port>` (or `curl -v https://<vault-hostname>/...`). Compare against the endpoint configured in Orchestrator → Tenant → Credential Stores → "Production CyberArk Store".
   - **Who:** Platform / network team

2. **Verify the CyberArk Credential Store configuration in Orchestrator.**
   - **Why:** Configuration drift on the Orchestrator side — incorrect web service name, FIPS mode toggled on Windows, 32/64-bit SDK mismatch — also produces 2304. The playbook's "CyberArk" branch enumerates these explicitly.
   - **Where:** Orchestrator UI → Tenant → Credential Stores → "Production CyberArk Store" → Edit. Verify: (a) the AppID, (b) the web service URL, (c) the platform's bitness matches the installed CyberArk SDK, (d) FIPS mode on Windows is not interfering with the SDK.
   - **Who:** Tenant admin

3. **If Orchestrator-side configuration is correct, contact the CyberArk vault administrator.**
   - **Why:** The vault itself may be down, the AppID may have been revoked, or the safe/object that holds this credential may have been moved or deleted on the CyberArk side.
   - **Where:** Verify with the vault admin that the AppID still resolves to the safe/object that stores `MyCyberArkSecret`'s value.
   - **Who:** CyberArk vault administrator
   - **Source:** `system-activities/playbooks/get-asset-external-vault-failure.md` ("Vault endpoint unreachable" / "CyberArk: FIPS mode / SDK mismatch" branches)

---

**Preventive fix:**

1. **Orchestrator** — Configure synthetic health checks for each credential store.
   - **Why:** External vault outages are common enough that proactive monitoring catches them before downstream jobs fault. A synthetic `Get Credential` against a sentinel asset, scheduled every N minutes, surfaces vault outages immediately.
   - **Where:** Schedule a no-op job that reads a sentinel credential per credential store; alert on failure via Orchestrator Alerts.
   - **Who:** Platform / SRE team

2. **Orchestrator** — Configure an alert subscription on credential-store errors.
   - **Why:** Job-level alerts catch downstream symptoms; a vault-level alert catches the cause sooner.
   - **Where:** Orchestrator UI → Alerts → component filter for credential-store errors, severity "Error".
   - **Who:** Tenant admin

3. **Studio** — For workflows that read external-vault-backed credentials, wrap `Get Credential` in a Try/Catch and surface vault errors distinctly from asset errors.
   - **Why:** A 2303 / 2304 mixed in with generic Orchestrator errors is easy to misroute. A wrapped exception that names the vault speeds up the next incident.
   - **Where:** `Main.xaml` → wrap the `GetRobotCredential` activity in Try/Catch → catch `UiPath.Core.Activities.OrchestratorCommunicationException`, inspect the error code, and throw a meaningful application exception.
   - **Who:** RPA developer

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The asset's external credential store (CyberArk) is unreachable / misconfigured from Orchestrator | High | Confirmed | Yes | Error code 2304 + asset's non-null `CredentialStoreId` points at a CyberArk-typed credential store + all asset/folder/permission/license layers verified correct | Verify network + Orchestrator credential-store config + vault availability |

---

Would you like help applying the fix — walking through the Orchestrator UI path to verify the CyberArk credential store configuration, or running connectivity checks from the Orchestrator host? I can also clean up the `.local/investigations/` folder if you no longer need it.
