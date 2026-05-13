# Final Resolution

---

**Root Cause:** The robot account running the `AssetPermissionDenied`
process lacks the `Assets.View` permission on the `Remote Debugging`
folder. The workflow's `Get Credential` activity targets a real folder
and a real asset that exist in Orchestrator, but the robot's assigned
role does not include View permission on Assets — so Orchestrator
returns HTTP 403 / error code 0 ("You are not authorized!") and the
job faults.

**What went wrong:** The `AssetPermissionDenied` job (started
2026-05-12T15:42:18Z) faulted ~2 seconds after launch because the
`Get Credential` activity (`GetRobotCredential`) in `Main.xaml` was
not authorized to read assets in the target folder.

**Why:** The workflow's `GetRobotCredential` activity sets
`AssetName="myHiddenAsset"` (a correctly-spelled name) and
`FolderPath="Remote Debugging"` (a real folder). Listing folders
returns `Remote Debugging` (rules out folder-scope-mismatch). Listing
assets in that folder (from the CLI user's session) returns
`myHiddenAsset` (rules out asset-not-found). The failure is at the
authorization layer: the robot account is assigned to the folder but
its role does not include the `Assets.View` permission. Orchestrator
therefore returns HTTP 403 with `"You are not authorized! The robot
account does not have the required permissions on Assets in this
folder. Error code: 0"`.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: AssetPermissionDenied — Faulted at 2026-05-12T15:42:20.314Z (ran for ~2.1 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-HOST
- Folder: Remote Debugging (key `7e9d4f2a-3b5c-4d8e-9f1a-2b3c4d5e6f7a`) — folder exists and is in the folders list
- Robot account assigned to the folder: `RobotUser1` (with role `Robot` — no `Assets.View` permission)

### System Activities (Root Cause)
- Activity: `GetRobotCredential` (DisplayName: "Get Credential")
- AssetName referenced (from `Main.xaml`): `myHiddenAsset` (correctly spelled — confirmed present in folder asset list)
- FolderPath referenced (from `Main.xaml`): `Remote Debugging` (folder exists — confirmed in folder list)
- Error at 2026-05-12T15:42:20.291Z: `[Get Credential] Status code: 403 (Forbidden). Orchestrator response: You are not authorized! The robot account does not have the required permissions on Assets in this folder. Error code: 0`
- The asset and folder both exist — this is a robot-account authorization issue, not a missing-resource issue.

---

**Immediate fix:**

### System Activities (Root Cause)
1. Grant the robot account a role that includes `Assets.View` permission on the `Remote Debugging` folder.
   - **Why:** The robot must hold a role with `Assets.View` (or higher: `Assets.Edit`, `Assets.Create`, `Assets.Delete`) on the folder where the asset lives. Without it, every `Get Asset` / `Get Credential` call from that robot returns 403.
   - **Where:** Orchestrator UI → Tenant → Folders → `Remote Debugging` → Manage → Accounts & Groups → find the robot account (`RobotUser1`) → assign a role such as `Robot` plus `Asset Administrator`, or a custom role that grants `Assets.View`.
   - **Who:** Tenant admin or folder owner
   - **Source:** `system-activities/playbooks/get-asset-permission-denied.md` ("Robot account role does not include View permission on Assets" branch)

Alternative: if multiple robots run this process, grant the permission at the group level rather than per-robot.

---

**Preventive fix:**

1. **Orchestrator** — Audit role assignments against folder asset usage on a recurring basis.
   - **Why:** Permission drift (role removed during a tenant cleanup, robot reassigned to a new folder without role copy) is a common source of silent regression. A recurring audit surfaces it before production jobs hit 403.
   - **Where:** Orchestrator UI → Tenant → Folders → for each folder used by automations, review Accounts & Groups assignments and the `Permissions` matrix. Alternatively, script the check via `uip orch users list` + `uip orch roles list`.
   - **Who:** Tenant admin / platform team

2. **Studio** — Wrap `Get Credential` / `Get Asset` activities in a Try/Catch that detects 403 and surfaces a descriptive error.
   - **Why:** A raw `UiPath.Core.Activities.OrchestratorCommunicationException` with HTTP 403 is harder to triage than a wrapped exception that says "Robot lacks Assets.View on folder X."
   - **Where:** `Main.xaml` → wrap the `GetRobotCredential` activity in Try/Catch → catch `UiPath.Core.Activities.OrchestratorCommunicationException` and throw a meaningful application exception including the folder name and the asset name.
   - **Who:** RPA developer

3. **Orchestrator** — Configure an alert subscription for faulted jobs in the `Remote Debugging` folder so permission failures surface immediately.
   - **Why:** The 403 would have been caught the first time the job ran if alerts were configured.
   - **Where:** Orchestrator UI → Alerts → severity "Error" + folder filter for `Remote Debugging`.
   - **Who:** Admin or platform team
   - **Source:** https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/alerts

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Robot account running the job lacks `Assets.View` permission on the `Remote Debugging` folder | High | Confirmed | Yes | HTTP 403 / error code 0 + asset present in folder asset list + folder present in folder list | Grant the robot a role with `Assets.View` on `Remote Debugging` |

---

Would you like help applying the fix — assigning a role with `Assets.View` to the robot account, or showing the exact Orchestrator UI path? I can also clean up the `.investigation/` folder if you no longer need it.
