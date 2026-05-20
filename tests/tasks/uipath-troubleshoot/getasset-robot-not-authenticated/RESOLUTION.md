# Final Resolution

---

**Root Cause:** The robot account `RobotUser1` running the
`AssetRobotUnlicensed` process is **unlicensed** in Orchestrator
(Connected, Unlicensed — `IsLicensed: false`, `LicenseType: null`).
Without a license, the robot cannot authenticate against Orchestrator,
so its `Get Credential` activity fails immediately with HTTP 401 /
"You are not authenticated! Error code: 0" before any asset call can
execute.

**What went wrong:** The `AssetRobotUnlicensed` job (started
2026-05-13T13:24:17Z) faulted ~1 second after launch with an
authentication error — the failing layer is robot identity, not the
asset.

**Why:** The workflow's `GetRobotCredential` activity targets
`AssetName="myHiddenAsset"` and `FolderPath="Remote Debugging"`. The
asset list shows `myHiddenAsset` is present in `Remote Debugging` with
the correct type (`Credential`, `Global`). The folder exists. The
robot account holds appropriate roles (Robot + Asset Administrator).
The only configuration gap is in the `or users list` output:
`RobotUser1` returns `IsLicensed: false`, `LicenseType: null` — the
robot is connected to Orchestrator but has not been assigned a
license. Without a license, every Orchestrator API call from this
robot returns 401 "not authenticated" — including the asset read that
this workflow would otherwise have made.

The phrasing "not **authenticated**" distinguishes this case from
permission-denied ("not **authorized**"), even though both share
`Error code: 0`. The fix is at the licensing layer, not the
role/permissions layer.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: AssetRobotUnlicensed — Faulted at 2026-05-13T13:24:18.602Z (ran for ~1.0 seconds)
- Job type: Unattended, triggered manually under robot account `RobotUser1` on machine MOCK-HOST
- Folder: Remote Debugging (key `3e6f9b4c-1a2d-4f7e-8c5d-9b3a4c5d6e7f`) — folder exists
- Robot account license state: `IsLicensed: false`, `LicenseType: null` — Connected but Unlicensed

### System Activities (Root Cause)
- Activity (from `Main.xaml`): `GetRobotCredential` (DisplayName: "Get Credential") — correct activity for the Credential asset
- AssetName (from `Main.xaml`): `myHiddenAsset` (correctly spelled, present in folder asset list)
- FolderPath (from `Main.xaml`): `Remote Debugging`
- Asset configuration in Orchestrator: `myHiddenAsset` exists with `ValueType: "Credential"`, `ValueScope: "Global"` — fully compatible with the activity
- Executing robot: `RobotUser1` (from `OrchestratorUserIdentity` in the job details)
- Robot license: **none** (`IsLicensed: false`, `LicenseType: null`)
- Error at 2026-05-13T13:24:18.580Z: `[Get Credential] Status code: 401 (Unauthorized). Orchestrator response: You are not authenticated! Error code: 0`
- The error phrasing "not authenticated" (not "not authorized") rules out the permission-denied playbook even though both share error code 0.

---

**Immediate fix:**

### Orchestrator (Root Cause)
1. Assign a license to robot account `RobotUser1`.
   - **Why:** The robot is connected to Orchestrator but has no license. Without a license, all API calls return 401 "not authenticated".
   - **Where:** Orchestrator UI → Tenant → Licenses → Robot Services. Either (a) assign one of the available `Unattended` license seats to `RobotUser1`, or (b) free a seat by unassigning an idle robot, or (c) ask the admin to purchase additional capacity if all seats are occupied. After assigning, the robot will move from `Connected, Unlicensed` to `Connected, Licensed` and the next job run will succeed.
   - **Who:** Tenant admin
   - **Source:** `system-activities/playbooks/get-asset-robot-not-authenticated.md` ("Robot is not licensed in Orchestrator" branch)

---

**Preventive fix:**

1. **Orchestrator** — Configure an alert subscription for `Robot disconnected / unlicensed` events.
   - **Why:** Unlicensed robots that were previously licensed will fail silently the next time they're invoked. An alert at license-revocation time prevents production faults.
   - **Where:** Orchestrator UI → Alerts → severity "Error" + component filter for robot license state changes.
   - **Who:** Admin or platform team
   - **Source:** https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/alerts

2. **Onboarding runbook** — Add a license assignment step to the new-robot onboarding checklist.
   - **Why:** New robots are routinely created without a license assigned. The first job run will fail with "not authenticated" until a license is attached.
   - **Where:** Update the team's onboarding runbook to include a final "verify robot is Connected, Licensed" check after assignment.
   - **Who:** Tenant admin / platform team

3. **Studio** — Wrap `Get Credential` / `Get Asset` activities in a Try/Catch that surfaces robot-identity errors distinctly from asset-level errors.
   - **Why:** A raw 401 / "not authenticated" message is easy to mistake for a permission issue, leading to wasted triage time. A wrapped exception that includes the robot account name and points at license/auth state speeds up the next incident.
   - **Where:** `Main.xaml` → wrap the `GetRobotCredential` activity in Try/Catch → catch `UiPath.Core.Activities.OrchestratorCommunicationException`, inspect the HTTP code, and throw a meaningful application exception.
   - **Who:** RPA developer

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Robot account `RobotUser1` is unlicensed in Orchestrator | Medium-High | Confirmed | Yes | Error message "You are not authenticated! Error code: 0" + `or users list` shows `RobotUser1` with `IsLicensed: false`, `LicenseType: null` + asset/folder/permission/type all check out correctly | Assign an Unattended license seat to `RobotUser1` in Orchestrator |

---

Would you like help applying the fix — walking through the Orchestrator UI path to assign a license seat? I can also clean up the `.local/investigations/` folder if you no longer need it.
