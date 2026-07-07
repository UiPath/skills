# Final Resolution

---

**Root Cause:** The `Get Credential` activity in `Main.xaml` has
`FolderPath="OldDevFolder"`. That folder does not exist in the tenant
— Orchestrator's folder list returns only `Remote Debugging` and
`Shared`. Because the targeted folder is unresolvable, Orchestrator
returns error code 1100 ("Folder does not exist or the user does not
have access to the folder") and the job faults.

**What went wrong:** The `AssetFolderMismatch` job (started
2026-05-12T09:18:42Z) faulted ~2 seconds after launch because the
`Get Credential` activity (`GetRobotCredential`) in `Main.xaml`
targeted a folder that Orchestrator could not resolve.

**Why:** The workflow's `GetRobotCredential` activity sets
`AssetName="myHiddenAsset"` (a correctly-spelled name) and
`FolderPath="OldDevFolder"`. When the activity called Orchestrator,
the response was a 1100 error: `"Folder 'OldDevFolder' does not exist
or the user does not have access to the folder. Error code: 1100"`.
Listing folders in the tenant (`uip orch folders list-current-user`)
returns only `Remote Debugging` (where the job actually runs) and
`Shared` — there is no folder named `OldDevFolder`. Asset name spelling
is irrelevant in this scenario because Orchestrator fails at folder
resolution before it ever checks the asset name.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: AssetFolderMismatch — Faulted at 2026-05-12T09:18:44.380Z (ran for ~2.0 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-HOST
- Job runtime folder: Remote Debugging (key `6d8c5e3f-2a1b-4c9d-8e7f-0a1b2c3d4e5f`)
- Tenant folder list does NOT contain `OldDevFolder`

### System Activities (Root Cause)
- Activity: `GetRobotCredential` (DisplayName: "Get Credential")
- AssetName referenced (from `Main.xaml`): `myHiddenAsset` (correctly spelled)
- FolderPath referenced (from `Main.xaml`): **`OldDevFolder`** (does not exist in tenant)
- Error at 2026-05-12T09:18:44.355Z: `[Get Credential] Status code: 403 (Forbidden). Orchestrator response: Folder 'OldDevFolder' does not exist or the user does not have access to the folder. Error code: 1100`
- Folder list returned only `Remote Debugging` and `Shared`. `OldDevFolder` is absent both from the current-user list and the tenant-wide list, confirming it does not exist.

---

**Immediate fix:**

### System Activities (Root Cause)
1. Correct the `FolderPath` property in `Main.xaml`.
   - **Why:** The activity must reference a folder that exists in the tenant and that the robot account is assigned to. `OldDevFolder` does not exist; `Remote Debugging` does and is the folder the job runs from.
   - **Where:** `Main.xaml` → `<ui:GetRobotCredential ... FolderPath="OldDevFolder" ...>` → change to `FolderPath="Remote Debugging"` (or remove the property entirely so the activity uses the job's runtime folder). Save, rebuild, republish the process.
   - **Who:** RPA developer
   - **Source:** `system-activities/playbooks/get-asset-folder-scope-mismatch.md` ("OrchestratorFolderPath set to a wrong or nonexistent folder" branch)

Alternative: create a folder named `OldDevFolder` in Orchestrator and assign the robot account to it (Orchestrator UI → Tenant → Folders → Add Folder → name `OldDevFolder` → assign the robot account → add asset `myHiddenAsset`). Only do this if `OldDevFolder` is the intended deployment target and was accidentally deleted.

---

**Preventive fix:**

1. **Studio** — Bind `FolderPath` to a project constant or input argument rather than a string literal.
   - **Why:** Folder paths embedded as literals are brittle when folders are renamed or environments change. Centralizing the value or passing it as input makes the dependency explicit.
   - **Where:** Define `WorkflowFolderPath = "Remote Debugging"` as a project constant, or expose it as an input argument and configure it at the process or queue level.
   - **Who:** RPA developer

2. **Orchestrator** — Configure an alert subscription for faulted jobs in the `Remote Debugging` folder so missing-folder failures surface immediately.
   - **Why:** The 1100 error would have been caught the first time the job ran if alerts were configured.
   - **Where:** Orchestrator UI → Alerts → severity "Error" + folder filter for `Remote Debugging`.
   - **Who:** Admin or platform team
   - **Source:** https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/alerts

3. **CI / pre-publish check** — Validate workflow `FolderPath` properties against the tenant's folder list before publish.
   - **Why:** A simple static check at publish time catches stale or typo'd folder references before they reach production.
   - **Where:** Add a pre-publish step that scans `.xaml` files for `FolderPath="..."` attributes and queries `uip orch folders list --output json` to verify each value exists.
   - **Who:** Platform / DevOps

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | `FolderPath="OldDevFolder"` references a folder that does not exist in the tenant | High | Confirmed | Yes | Error code 1100 + tenant folder list contains only `Remote Debugging` and `Shared` (no `OldDevFolder`) | Fix `FolderPath` in `Main.xaml`, rebuild, republish |

---

Would you like help applying the fix — updating `Main.xaml` to reference `Remote Debugging` and republishing the package? I can also clean up the `.local/investigations/` folder if you no longer need it.
