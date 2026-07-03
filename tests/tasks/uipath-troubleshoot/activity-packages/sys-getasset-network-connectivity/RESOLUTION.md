# Final Resolution

---

**Root Cause:** The robot host running the `AssetNetworkConnectivity`
job (`RobotUser1` on `MOCK-HOST`) cannot reach the Orchestrator URL.
The HTTP call from the `Get Credential` activity to Orchestrator times
out. Orchestrator's runtime surfaces this as "Orchestrator information
is not available." The asset, folder, permissions, license, and
activity type are all correctly configured — the failing layer is
robot-to-Orchestrator connectivity.

The exact sub-cause within the connectivity family is one of the
following per the playbook; without runtime access to the robot host
we cannot narrow it further from the troubleshooting evidence alone:

- UiPath Robot Windows service not running on the robot host
- Robot host cannot reach the Orchestrator URL (firewall, DNS, proxy)
- Authenticated proxy in the network path (UiPath Robot supports only unauthenticated proxies)
- SSL certificate expired or not trusted by the robot machine
- TLS Extended Master Secret (EMS) incompatibility (~1 in 256 intermittent failures)
- Orchestrator auth session expired in a long-running process

**What went wrong:** The `AssetNetworkConnectivity` job (started
2026-05-13T19:18:42Z) faulted ~31 seconds after launch — the time
it took the HTTP client to give up on the Orchestrator connection.

**Why:** The workflow's `GetRobotCredential` activity targets
`AssetName="myHiddenAsset"` in folder `Remote Debugging` — a correctly
configured asset with `ValueType: "Credential"`, `ValueScope: "Global"`.
The robot account `RobotUser1` is `IsLicensed: true`,
`LicenseType: "Unattended"`, with the `Asset Administrator` role.
Every asset-side, folder-side, role-side, and license-side layer
checks out. When the activity ran, however, the HTTP call from the
robot host to Orchestrator timed out, and Orchestrator's client SDK
surfaced this as "Orchestrator information is not available." The
asymmetric signal is that the CLI commands (`uip orch folders list`,
`uip orch jobs get`, `uip orch assets list`) all succeed from the
developer's session — proving Orchestrator is up and reachable from
SOME network paths. The failure is specific to the robot host's
network path or its local SDK configuration.

---

**Evidence:**

### Orchestrator (Propagation — but from CLI session, not robot)
- Job: AssetNetworkConnectivity — Faulted at 2026-05-13T19:19:13.812Z (ran for ~31 seconds — typical HTTP-timeout duration)
- Folder: Remote Debugging (key `6b9d2c5e-3a4f-4b8c-9d1e-2f3a4b5c6d7e`) — folder exists when queried from the CLI session
- Executing robot: `RobotUser1` (Connected, Licensed, has Asset Administrator role)

### System Activities (Root Cause — connectivity layer)
- Activity (from `Main.xaml`): `GetRobotCredential` (DisplayName: "Get Credential")
- AssetName: `myHiddenAsset` (correctly configured; asset list confirms presence with correct type and scope)
- FolderPath: `Remote Debugging` (folder exists)
- Error at 2026-05-13T19:19:13.781Z: `[Get Credential] Orchestrator information is not available. Connection timed out connecting to https://cloud.uipath.com after 30000 ms. Inner exception: System.Net.WebException: The operation has timed out.`
- The error signature ("Orchestrator information is not available" + connection timeout) is unique to the network-connectivity playbook.
- The asymmetry is the key: CLI queries from the developer's session reach Orchestrator successfully (folders, jobs, assets, users all return data), but the robot host's in-job HTTP call does not. The failure is on the robot's network path or local SDK configuration.

---

**Immediate fix:**

### System Activities (Root Cause) — the playbook lists 6+ sub-causes; check in this order on the robot host

1. **Verify the UiPath Robot Windows service is running on the robot host.**
   - **Why:** A stopped or crashed `UiPath Robot` service produces "Orchestrator information is not available" immediately. Easiest check, fixes the issue in many cases.
   - **Where:** On the robot host (`MOCK-HOST`): `Get-Service "UiPath Robot*" | Where-Object Status -ne 'Running'`. Start any stopped service.
   - **Who:** Robot machine admin

2. **Verify the robot host can reach the Orchestrator URL.**
   - **Why:** Firewall, DNS, or proxy changes can block the robot's network path while leaving the developer's session intact.
   - **Where:** From the robot host: `Test-NetConnection cloud.uipath.com -Port 443` and `curl -I https://cloud.uipath.com`. Compare against the Orchestrator URL configured in the robot's settings.
   - **Who:** Network team / robot machine admin

3. **Inspect proxy and SSL/TLS configuration on the robot host.**
   - **Why:** UiPath Robot supports only **unauthenticated** proxies — an authenticated proxy in the path produces "Orchestrator information is not available." SSL certificate expiry, untrusted CA, or TLS EMS incompatibility produce the same symptom.
   - **Where:** Robot config: check `Proxy*` settings in `UiPath.Settings`. SSL: `[Net.ServicePointManager]::SecurityProtocol` on the robot host; verify the Orchestrator URL's certificate via `openssl s_client -connect cloud.uipath.com:443`.
   - **Who:** Robot machine admin

4. **For long-running processes only — check Orchestrator session expiry.**
   - **Why:** Orchestrator auth sessions for unattended robots can expire after ~2 hours, producing intermittent "Orchestrator information is not available" failures partway through long jobs.
   - **Where:** Confirm the job was short-running (<30 min) before this branch applies. If long-running, look at the timestamp of the failure relative to job start.
   - **Who:** Platform team
   - **Source:** `system-activities/playbooks/get-asset-network-connectivity.md` (session-expiry branch)

If none of these fixes resolve the issue, the playbook lists the **TLS Extended Master Secret (EMS)** incompatibility as a low-frequency cause (~1 in 256 connections failing on Windows hosts without the EMS update); apply the relevant Windows update to the robot host as a last resort.

---

**Preventive fix:**

1. **Monitoring** — Configure synthetic uptime probes from the robot host to the Orchestrator URL.
   - **Why:** Network/SSL changes on the robot side are invisible to Orchestrator-level alerts. A robot-side probe catches them at the layer where they actually fail.
   - **Where:** Schedule a no-op job that calls Orchestrator from each robot every N minutes; alert on failure.
   - **Who:** Platform / SRE team

2. **Studio** — Wrap `Get Credential` / `Get Asset` activities in Try/Catch to surface connectivity errors distinctly from asset-level errors.
   - **Why:** A raw "Orchestrator information is not available" is easy to misroute as an asset issue. A wrapped exception that surfaces the underlying timeout or SSL error speeds up the next incident.
   - **Where:** `Main.xaml` → wrap the `GetRobotCredential` activity in Try/Catch → catch `UiPath.Core.Activities.OrchestratorCommunicationException`, inspect the inner exception (`WebException`, `TimeoutException`, `AuthenticationException`), and throw a meaningful application exception.
   - **Who:** RPA developer

3. **Orchestrator** — Alert subscription for faulted jobs in the `Remote Debugging` folder.
   - **Why:** Robot-side connectivity outages produce silent automation regression. Folder-level alerts catch them at first occurrence.
   - **Where:** Orchestrator UI → Alerts → severity "Error" + folder filter for `Remote Debugging`.
   - **Who:** Admin or platform team

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Robot host cannot reach the Orchestrator URL (network/firewall/DNS/proxy/SSL/TLS/session-expiry) | Medium (family confidence high; sub-cause selection requires robot-host access we don't have from CLI) | Confirmed | Yes | Error message "Orchestrator information is not available. Connection timed out..." + CLI queries from developer's session reach Orchestrator successfully + asset/folder/role/license all verified healthy | Verify Robot service, network connectivity, proxy/SSL/TLS config from the robot host |

---

Would you like help applying the fix — checking the Robot service status, running connectivity probes from the robot host, or walking through SSL/proxy configuration? I can also clean up the `.local/investigations/` folder if you no longer need it.
