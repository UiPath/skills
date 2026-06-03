# Final Resolution

---

**Root Cause:** The robot account `RobotUser1` running the
`AssetRobotAuthFailure` process **cannot authenticate its Orchestrator
API calls**. The robot is licensed (`IsLicensed: true`,
`LicenseType: Unattended`) and connected, so the job dispatches and
starts executing, but the first Orchestrator REST call the workflow
makes — the `Get Credential` asset read — is rejected with HTTP 401 /
"You are not authenticated! Error code: 0". The failing layer is robot
**identity / token**, not the asset, the folder, permissions, or
licensing.

**What went wrong:** The `AssetRobotAuthFailure` job (started
2026-05-13T13:24:17Z) reached the `Get Credential` activity and faulted
~1 second later with an authentication error. The job *did* run — it
acquired a runtime and began executing `Main.xaml` — which already
rules out a licensing problem: an unlicensed robot never starts a job
at all. The fault is the robot's Orchestrator access token being
rejected at the activity's HTTP call.

**Why:** The workflow's `GetRobotCredential` activity targets
`AssetName="myHiddenAsset"` and `FolderPath="Remote Debugging"`. Every
configuration layer checks out:

- The asset list shows `myHiddenAsset` present in `Remote Debugging`
  with the correct type (`Credential`, `Global`).
- The folder `Remote Debugging` exists.
- The robot account holds the necessary roles (Robot + Asset
  Administrator) — so this is **not** a permission gap.
- The robot is **licensed and connected** (`IsLicensed: true`,
  `LicenseType: Unattended`, `ConnectionState: Connected`) — so this is
  **not** a licensing gap.

With asset, folder, type, permissions, and license all correct, the
only remaining layer is the robot's authentication to Orchestrator. The
error phrasing "not **authenticated**" (HTTP 401) — distinct from "not
**authorized**" (HTTP 403, which is the permission-denied playbook,
even though both share `Error code: 0`) — localizes the fault to the
robot's identity/token, not RBAC. The robot can connect and start jobs,
but its API token is rejected when an activity calls the Orchestrator
REST API.

Per the `get-asset-robot-not-authenticated` playbook, a 401 "not
authenticated" from a *running* job's Orchestrator HTTP activity points
to one of these (in order of likelihood for this evidence):

1. **Machine key / client-credential mismatch** — the robot connected
   with a key Orchestrator no longer accepts (e.g. the machine key was
   regenerated, or the robot was provisioned against a different
   machine template). Dispatch can still succeed from a cached session
   while fresh API token requests get 401.
2. **Robot key authentication disabled in tenant security** — if
   "Allow both user authentication and robot key authentication" is
   off, an unattended robot that authenticated via machine key has its
   API token rejected.
3. **`UiPath.System.Activities` auth regression** — if the failure
   began right after a package upgrade, a known regression in the
   System.Activities Orchestrator HTTP client can produce this 401.

The available evidence (everything else correct, robot healthy and
connected) does not single out one of the three — so the resolution
covers the ranked checklist rather than asserting a single sub-cause.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: AssetRobotAuthFailure — Faulted at 2026-05-13T13:24:18.602Z, after running ~1.0 seconds (started 2026-05-13T13:24:17.510Z). The job started and executed — proof the robot is licensed and able to launch.
- Job type: Unattended, triggered manually under robot account `RobotUser1` on machine MOCK-HOST
- Folder: Remote Debugging (key `3e6f9b4c-1a2d-4f7e-8c5d-9b3a4c5d6e7f`) — folder exists
- Robot account: `RobotUser1` — `IsLicensed: true`, `LicenseType: Unattended`, `ConnectionState: Connected` (licensed and connected — licensing is NOT the cause)

### System Activities (Root Cause)
- Activity (from `Main.xaml`): `GetRobotCredential` (DisplayName: "Get Credential") — correct activity for the Credential asset
- AssetName (from `Main.xaml`): `myHiddenAsset` (correctly spelled, present in folder asset list)
- FolderPath (from `Main.xaml`): `Remote Debugging`
- Asset configuration in Orchestrator: `myHiddenAsset` exists with `ValueType: "Credential"`, `ValueScope: "Global"` — fully compatible with the activity
- Executing robot: `RobotUser1` (from `OrchestratorUserIdentity` in the job details), holds roles Robot + Asset Administrator
- Error at 2026-05-13T13:24:18.580Z: `[Get Credential] Status code: 401 (Unauthorized). Orchestrator response: You are not authenticated! Error code: 0`
- The error phrasing "not authenticated" (HTTP 401) — not "not authorized" (HTTP 403) — rules out the permission-denied playbook even though both share error code 0, and the running job rules out licensing. The fault is at the robot identity / API-token layer.

---

**Immediate fix:**

### Orchestrator / Robot (Root Cause)
1. Reconnect `RobotUser1` to Orchestrator with the current machine key.
   - **Why:** A 401 "not authenticated" from a running job's Orchestrator HTTP call means the robot's API token is being rejected. The most common cause is a machine key the robot still holds but Orchestrator no longer accepts.
   - **Where:** Orchestrator UI → Tenant → Machines → open the machine for `MOCK-HOST` → copy the current Machine Key → re-enter it in the UiPath Assistant / Robot connection settings, then reconnect. Confirm the robot returns to `Connected, Licensed`.
   - **Who:** Tenant admin / RPA operator
   - **Source:** `system-activities/playbooks/get-asset-robot-not-authenticated.md` ("machine key mismatch" branch)
2. Confirm robot key authentication is enabled for the tenant.
   - **Why:** If "Allow both user authentication and robot key authentication" is disabled, an unattended robot's machine-key token is rejected at the API call → 401 "not authenticated".
   - **Where:** Orchestrator UI → Tenant → Settings → Security → enable "Allow both user authentication and robot key authentication".
   - **Who:** Tenant admin
   - **Source:** `system-activities/playbooks/get-asset-robot-not-authenticated.md` ("interactive sign-in not enabled" branch)
3. If the failure began right after a package upgrade, check `UiPath.System.Activities`.
   - **Why:** A System.Activities version with the documented Orchestrator-HTTP auth regression produces this exact 401.
   - **Where:** `project.json` dependencies → roll back to the last known-good `UiPath.System.Activities` (or update to the latest stable), republish, rerun.
   - **Who:** RPA developer
   - **Source:** `system-activities/playbooks/get-asset-robot-not-authenticated.md` ("package regression" branch)

---

**Preventive fix:**

1. **Orchestrator** — Configure an alert subscription for robot connection / authentication failures.
   - **Why:** A robot whose key is rotated or whose auth mode changes will fail silently the next time it's invoked. An alert at the failure point prevents repeated production faults.
   - **Where:** Orchestrator UI → Alerts → severity "Error" + component filter for robot connection / authentication events.
   - **Who:** Admin or platform team
   - **Source:** https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/alerts

2. **Onboarding / key-rotation runbook** — Add a "reconnect the robot after any machine-key rotation" step.
   - **Why:** Rotating a machine key in Orchestrator without re-entering it on the robot leaves the robot connected but unable to authenticate API calls — exactly this failure.
   - **Where:** Update the team's runbook to include a "verify robot is Connected, Licensed and run a smoke job" check after any key change.
   - **Who:** Tenant admin / platform team

3. **Studio** — Wrap `Get Credential` / `Get Asset` activities in a Try/Catch that surfaces robot-identity errors distinctly from asset-level errors.
   - **Why:** A raw 401 / "not authenticated" message is easy to mistake for a permission issue, leading to wasted triage time. A wrapped exception that includes the robot account name and points at auth/token state speeds up the next incident.
   - **Where:** `Main.xaml` → wrap the `GetRobotCredential` activity in Try/Catch → catch `UiPath.Core.Activities.OrchestratorCommunicationException`, inspect the HTTP code, and throw a meaningful application exception.
   - **Who:** RPA developer

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Robot account `RobotUser1` cannot authenticate its Orchestrator API calls (token rejected at the activity's HTTP call) | Medium-High | Confirmed | Yes | Error "You are not authenticated! Error code: 0" (HTTP 401) thrown *inside* a running job at `GetRobotCredential` + asset/folder/type/permission/license all verified correct + robot `Connected, Licensed` | Reconnect the robot with the current machine key; confirm robot-key auth is enabled; check System.Activities for the auth regression if it started after an upgrade |

---

Would you like help applying the fix — walking through the Orchestrator UI path to copy the machine key and reconnect the robot, or checking the tenant security setting? I can also clean up the `.local/investigations/` folder if you no longer need it.
