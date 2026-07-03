# Final Resolution

---

**Root Cause:** The `Get Asset` activity (`GetRobotAsset`) in
`Main.xaml` targets `AssetName="MyPerRobotConfig"` in the
`Remote Debugging` folder. The asset exists, is the right type for
the activity (`Text`), and the folder is accessible — but the asset's
`ValueScope` is `PerRobot` and the robot running the job
(`RobotUser1`) has no entry in the asset's per-robot value table.
Orchestrator therefore reports "The asset 'MyPerRobotConfig' does not
have a value associated with this robot."

**What went wrong:** The `AssetPerRobotNoValue` job (started
2026-05-13T11:08:24Z) faulted ~1 second after launch because the
`Get Asset` activity could not resolve a per-robot value for the
asset.

**Why:** The workflow's `GetRobotAsset` activity reads
`MyPerRobotConfig` from the `Remote Debugging` folder. The asset
list in that folder shows `MyPerRobotConfig` is configured with
`ValueScope: "PerRobot"` (each robot gets its own value rather than
sharing a global value). The robot account running this job is
`RobotUser1`, and the per-robot value table for `MyPerRobotConfig`
does not include an entry for `RobotUser1`. This is a **configuration
gap in Orchestrator**, not a workflow bug — the activity, asset name,
folder path, and asset type all match correctly; the only missing
piece is the per-robot value mapping.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: AssetPerRobotNoValue — Faulted at 2026-05-13T11:08:25.241Z (ran for ~1.0 seconds)
- Job type: Unattended, triggered manually under robot account `RobotUser1` on machine MOCK-HOST
- Folder: Remote Debugging (key `2c5e8f4a-9b3d-4f6c-8e1d-7a2b3c4d5e6f`) — folder exists
- Asset list: `MyPerRobotConfig` is present with `ValueType: "Text"` (compatible with Get Asset) and `ValueScope: "PerRobot"` — values vary per robot

### System Activities (Root Cause)
- Activity (from `Main.xaml`): `GetRobotAsset` (DisplayName: "Get Asset") — correct activity for a `Text` asset
- AssetName (from `Main.xaml`): `MyPerRobotConfig`
- FolderPath (from `Main.xaml`): `Remote Debugging`
- Asset scope in Orchestrator: **`PerRobot`** (NOT `Global`)
- Executing robot: `RobotUser1` (from `OrchestratorUserIdentity` in the job details)
- Error at 2026-05-13T11:08:25.215Z: `[Get Asset] Orchestrator response: The asset 'MyPerRobotConfig' does not have a value associated with this robot.`
- This is NOT asset-not-found (asset present), NOT folder-not-found (folder present), NOT permission-denied (no 403/auth error), NOT wrong-activity-type (Get Asset is the right activity for a Text asset) — the failure is the **missing per-robot value entry**.

---

**Immediate fix:**

### System Activities (Root Cause) — pick ONE of two branches

1. **Branch A — Add a per-robot value for the executing robot (most common).**
   - **Why:** The asset is intentionally per-robot (different robots run with different config values, e.g., per-environment settings). The fix is to populate the missing entry, not to change the scope.
   - **Where:** Orchestrator UI → Folder `Remote Debugging` → Assets → `MyPerRobotConfig` → Manage Values → Add value → select robot `RobotUser1` → enter the Text value this robot should see. Repeat for any other robots that need to run this process.
   - **Who:** Tenant admin or folder owner
   - **Source:** `system-activities/playbooks/get-asset-per-robot-no-value.md` ("Asset uses 'Per Robot' value mode but no entry exists for the executing robot" branch)

2. **Branch B — Switch the asset to Global scope.**
   - **Why:** If every robot should use the same value (the per-robot scope was set in error), change the asset's `ValueScope` from `PerRobot` to `Global` and set a single value.
   - **Where:** Orchestrator UI → Folder `Remote Debugging` → Assets → `MyPerRobotConfig` → Edit. Some Orchestrator versions do not allow in-place scope changes — in that case, delete the existing per-robot asset and recreate it as `Global`.
   - **Who:** Tenant admin or folder owner
   - **Caution:** any workflow or robot already relying on different per-robot values will break after the switch to Global — audit first.

---

**Preventive fix:**

1. **Orchestrator** — When adding a new robot to a folder, copy over per-robot asset value tables as part of onboarding.
   - **Why:** This error class commonly appears after a new robot is added to an existing folder. A per-robot value-table audit at robot-onboarding time prevents the silent regression.
   - **Where:** Update the onboarding runbook for new robots; optionally script via `uip orch users list` + per-asset value-table inspection.
   - **Who:** Tenant admin / platform team

2. **Studio** — Wrap `Get Asset` activities that read per-robot assets in a Try/Catch that surfaces a descriptive error.
   - **Why:** The raw "does not have a value associated with this robot" message is informative but easy to miss in long job logs. A wrapped exception that includes the robot account name and the asset's expected per-robot value table makes triage faster.
   - **Where:** `Main.xaml` → wrap the `GetRobotAsset` activity in Try/Catch → catch `UiPath.Core.Activities.OrchestratorCommunicationException` and throw a meaningful application exception.
   - **Who:** RPA developer

3. **Audit script** — Periodically scan all per-robot assets in production folders and report assets where the per-robot value table is missing entries for any robot assigned to that folder.
   - **Why:** Catches drift between robot assignments and per-robot value tables before jobs start failing.
   - **Where:** Schedule a script that calls `uip orch assets list --folder-key <folder> --output json`, filters for `ValueScope: "PerRobot"`, and cross-references against `uip orch users list` for robot accounts assigned to that folder.
   - **Who:** Platform / DevOps

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Asset `MyPerRobotConfig` has `ValueScope: PerRobot` and no value entry for the executing robot `RobotUser1` | High | Confirmed | Yes | Error message "does not have a value associated with this robot" + asset list shows `MyPerRobotConfig` with `ValueScope: "PerRobot"` + job's `OrchestratorUserIdentity` is `RobotUser1` | Branch A: add per-robot value entry for `RobotUser1`; OR Branch B: switch asset to `Global` scope |

---

Would you like help applying the fix — walking through the Orchestrator UI path to add a per-robot value, or switching the asset to Global scope? I can also clean up the `.local/investigations/` folder if you no longer need it.
