---
confidence: high
---

# Get Asset Failed

## Context

A `Get Asset`, `Get Robot Asset`, `Get Orchestrator Asset`, or `Get Credential` activity failed at runtime.

What this looks like:
- Job fails with an exception from a Get Asset or Get Credential activity
- Process succeeds in Studio/attended mode but fails in unattended Orchestrator jobs
- Activity returns null, zero, or empty with no exception thrown
- Failures are intermittent — the same process and asset succeed on some runs

What can cause it:
- Asset does not exist in the folder where the job runs, or the name does not match
- Wrong activity used for the asset type (Get Asset on a Credential, or vice versa)
- Robot account lacks View permission on Assets in the target folder
- Robot is not authenticated, not licensed, or not connected to Orchestrator
- Folder scope mismatch between the job context and the asset location
- Per-robot or per-account asset has no value assigned for the executing robot
- External credential store (CyberArk, Azure Key Vault, Thycotic) is unreachable or misconfigured
- Package version bug in `UiPath.System.Activities`
- Network, TLS, or proxy issue between the robot and Orchestrator

What to look for:
- Exact exception message and error code from job traces
- Whether the failure is consistent or intermittent
- Whether the failure is environment-specific (attended vs. unattended, one folder vs. another)
- Execution identity (which robot account and folder the job runs under)

For the full error code reference and root cause taxonomy, see [get-asset-failure-causes.md](../../../products/orchestrator/get-asset-failure-causes.md).

---

### Scenario: wrong-activity-for-credential-asset

**Trigger:** Error message contains `"does not work with assets of type Credential"` or `"Invalid asset type"`.

**Investigation:**
1. Identify the asset name from the faulted activity.
2. Verify the asset type in Orchestrator — navigate to the folder > Assets and inspect the Type column.
3. Confirm the workflow uses `Get Orchestrator Asset` instead of `Get Orchestrator Credential`.

**Resolution:**
- Replace the `Get Orchestrator Asset` activity with `Get Orchestrator Credential`.
- `Get Credential` returns a `SecureString` for the password and a `String` for the username — update downstream variable types accordingly.
- The reverse also applies: `Get Credential` on a Text/Integer/Boolean asset fails; use `Get Asset` instead.

---

### Scenario: asset-does-not-exist

**Trigger:** Error message contains `"Could not find an asset with this name"` or `"Could not find the asset"` (Error code: 1002).

**Investigation:**
1. Get the exact asset name from the activity's AssetName property (check XAML or job traces).
2. Confirm the folder the job runs in (check the job details in Orchestrator > Jobs).
3. List assets in that folder and verify an asset with that exact name exists.
4. Check for case or spacing differences — asset names are not case-sensitive but spelling must match exactly.
5. If the asset is missing, check whether it exists in a different folder or was recently renamed/deleted.

**Resolution:**
- If the asset does not exist in the job folder: create it there, or run the job in the folder where the asset is defined.
- If the name does not match: fix the AssetName property in the workflow to match the Orchestrator asset name exactly.
- If the asset was deleted: recreate it with the correct name, type, and value.

---

### Scenario: permission-denied

**Trigger:** Error message contains `"does not have the required permissions"`, `"You are not authorized!"`, or HTTP 403 `"Forbidden"` (Error code: 0).

**Investigation:**
1. Identify the robot account running the job (check job details in Orchestrator).
2. In Orchestrator, navigate to the folder > Manage > Accounts & Groups and check the robot account's assigned role.
3. Verify the role includes the **View** permission on Assets.
4. If using folder inheritance, check parent folder permissions as well.

**Resolution:**
- Grant the robot account a role that includes "View Assets" permission in the folder where the asset lives.
- Common roles with this permission: Automation User, Automation Developer, Administrator.
- If the Windows user running the process differs from the registered robot account, align them or reassign the robot.

---

### Scenario: robot-not-authenticated-or-unlicensed

**Trigger:** Error message contains `"You are not authenticated! Error code: 0"`, or robot shows as `Connected, Unlicensed`.

**Investigation:**
1. Check the UiPath Robot tray icon — verify it shows "Connected, Licensed".
2. If unlicensed, check the license assignment in Orchestrator > Tenant > Licenses.
3. Verify the robot's machine key or client credentials match what is configured in Orchestrator.
4. Check whether the issue started after a `UiPath.System.Activities` package upgrade — versions 20.10.1+ and 2021.10.5 introduced authentication regressions.
5. If only Background Process template jobs fail (not RE-Framework), the cause is likely a package version conflict.

**Resolution:**
- If unlicensed: assign a Runtime license to the robot in Orchestrator.
- If machine key mismatch: reconnect the robot using the correct key from Orchestrator > Machines.
- If package regression: downgrade `UiPath.System.Activities` to v20.4.x as a workaround, or update to the latest stable version.
- If interactive sign-in is not enabled for the tenant: enable "Allow both user authentication and robot key authentication" in Tenant Settings > Security.

---

### Scenario: folder-scope-mismatch

**Trigger:** Error code 1100 (`"Folder does not exist or the user does not have access to the folder"`) or error code 1101 (`"An organization unit is required"`).

**Investigation:**
1. Check the `OrchestratorFolderPath` property of the activity — an incorrect or missing value is the most common cause.
2. Confirm whether the asset is in a classic or modern folder, and whether the job runs in the same type.
3. If error is 1101, the activity was likely created before modern folders were introduced — it lacks the FolderPath property entirely.
4. Verify that the robot account is assigned to the folder containing the asset.

**Resolution:**
- If `OrchestratorFolderPath` is wrong: correct it or leave it blank to use the robot's connected folder.
- If error is 1101 (old XAML migration): delete the activity and re-add it from the Activities panel in the current Studio version to generate the FolderPath property.
- If classic/modern folder mismatch: recreate the asset in the correct folder type — cross-type access is not supported.
- Assets are **not** auto-migrated during classic-to-modern folder migration; recreate them manually.

---

### Scenario: per-robot-asset-no-value

**Trigger:** Error message contains `"The asset does not have a value associated with this robot"`.

**Investigation:**
1. Navigate to Orchestrator > folder > Assets and open the asset.
2. Confirm the asset is configured with "Per Robot" (or "Per Account/Machine") values.
3. Check whether the robot executing the job has a value entry assigned.

**Resolution:**
- Add a value entry for the executing robot in the asset's per-robot value table.
- If per-robot values are not required, switch the asset to a global value.

---

### Scenario: external-vault-failure

**Trigger:** Error code 2303 (`"Invalid Credential Store configuration"`) or error code 2304 (`"Failed to read from Credential Store type <X>"`). Applies to CyberArk, Azure Key Vault, Thycotic, and other external vaults.

**Investigation:**
1. Identify the vault type from the error message.
2. Verify Orchestrator can reach the vault endpoint — check firewall/network rules from the Orchestrator server.
3. For **CyberArk**: check for FIPS mode on Windows (incompatible with CyberArk SDK), 32/64-bit SDK mismatch, and web service name in Orchestrator credential store settings. On Orchestrator 2020.10.8–2021.10.1, set `Plugins.SecureStores.CyberArk.UsePowerShellCLI=false` in configuration (fixed in 2022.4+).
4. For **Azure Key Vault**: verify the Orchestrator server IP is whitelisted in Key Vault network settings, the secret value does not contain a backslash (`\`), and the secret is in the expected key-pair format.
5. For **Thycotic**: verify integration settings (URL, credentials) in Orchestrator > Credential Stores.
6. For error 2303: check all credential store plugin settings (URL, application ID, credentials) for completeness and correctness.

**Resolution:**
- Fix the specific misconfiguration identified above and re-test by running the job.
- If the vault endpoint is unreachable: open network access from the Orchestrator server to the vault, then retest.
- If vault is correctly configured but the secret format is wrong: update the secret in the vault to match the expected format.

---

### Scenario: network-or-connectivity-issue

**Trigger:** `"Orchestrator information is not available"`, timeout errors, SSL handshake failures, or intermittent failures with no consistent error code.

**Investigation:**
1. Confirm the UiPath Robot Windows service is running on the machine.
2. Verify the robot can reach the Orchestrator URL — test from the robot machine.
3. Check for proxy configuration: UiPath Robot supports only unauthenticated proxies.
4. For on-premises Orchestrator: verify the SSL certificate is valid and trusted by the robot machine's certificate store.
5. If failures appear intermittent (~1 in 256 attempts): investigate TLS Extended Master Secret (EMS) compatibility.
6. If failures occur after ~2 hours in long-running processes: the Orchestrator auth session has expired — implement retry logic around the Get Asset call.

**Resolution:**
- If Robot service is stopped: start it and re-run the job.
- If proxy is blocking: configure the proxy to allow unauthenticated pass-through, or exclude the Orchestrator URL.
- If SSL certificate is expired: renew it on the Orchestrator server and ensure the robot machine trusts it.
- If session expiry in long-running jobs: add retry handling (Retry Scope) around the Get Asset activity.

---

### Scenario: activity-bug-silent-failure

**Trigger:** Activity completes without exception but the output variable is null, zero, or empty.

**Investigation:**
1. Check whether the activity was copy-pasted from another sequence — copy-paste retains internal state from the original.
2. Check the Studio and `UiPath.System.Activities` package version — version 22.10.x has a bug where variables created with `Ctrl+K` do not receive output values.
3. Verify the output variable was created before the activity (not via `Ctrl+K` during activity configuration in the affected version).

**Resolution:**
- If copy-paste issue: delete the activity and re-drag a fresh one from the Activities panel.
- If `Ctrl+K` variable bug (System.Activities 22.10.x): update the package to ≥22.10.4, or pre-create the variable in the Variables panel before wiring it to the activity.
