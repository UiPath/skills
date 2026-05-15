# Final Resolution

---

**Root Cause:** The project targets `UiPath.System.Activities: [22.10.5]`,
a package version with a documented bug where `Get Credential`,
`Get Asset`, and `Get Orchestrator Asset` activities silently fail to
populate output variables when those variables were created via
`Ctrl+K` in the activity's property grid. The `Get Credential` activity
in `Main.xaml` runs to completion without throwing an exception, but
its `Username` and `Password` outputs remain `null`. The downstream
`LogMessage` activity then throws `NullReferenceException` trying to
read the null `pass` SecureString. The job faults with an NRE that
has **no apparent connection to the asset layer** — the asset itself
is fine.

**What went wrong:** The `AssetSilentFailure` job (started
2026-05-13T18:02:11Z) faulted ~1.3 seconds after launch with a
`NullReferenceException` at the `LogMessage` activity, downstream of
a `Get Credential` activity that completed without any error of its
own.

**Why:** Tracing the error backward:

1. Job logs show only ONE error entry: `NullReferenceException` at
   `LogMessage "Log Message"` in `Main.xaml`. There is NO error log
   entry naming the `Get Credential` (`GetRobotCredential`) activity.
2. The XAML's `LogMessage` consumes `username + new
   System.Net.NetworkCredential(string.Empty, pass).Password`. If
   `pass` is null, the `.Password` access throws NRE.
3. `pass` is the output binding of the upstream `GetRobotCredential`
   activity. If `GetRobotCredential` ran successfully, `pass` should
   not be null.
4. `project.json` shows `UiPath.System.Activities: [22.10.5]` — the
   exact version flagged by the
   `get-asset-activity-bug-silent-failure.md` playbook. In this
   version, output variables created via Ctrl+K during activity
   configuration silently fail to receive values at runtime; the
   activity reports success but produces no usable output.
5. Asset list verification: `myHiddenAsset` is present in the
   `Remote Debugging` folder with `ValueType: "Credential"`,
   `ValueScope: "Global"`, and a valid credential value — i.e., the
   asset layer is **healthy**. The failure is NOT at the asset side.
6. User/license check: `RobotUser1` has `IsLicensed: true`,
   `LicenseType: "Unattended"`, roles `[Robot, Asset Administrator]`
   — i.e., the robot identity layer is also healthy.

The fix is at the **package layer**, not the asset/folder/role/license
layer.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: AssetSilentFailure — Faulted at 2026-05-13T18:02:12.318Z (ran for ~1.3 seconds)
- Folder: Remote Debugging (key `5a8c4d3e-9f2b-4a6c-8e1f-2b3c4d5e6f7a`)
- Executing robot: `RobotUser1` (Connected, Licensed, Asset Administrator)
- Error log entry count from `Get Credential`: **0** (no error from the activity itself)
- Error log entry count from downstream `LogMessage`: **1** (NullReferenceException)

### System Activities (Root Cause)
- Activity in `Main.xaml`: `GetRobotCredential` (DisplayName: "Get Credential"), `AssetName="myHiddenAsset"`, `FolderPath="Remote Debugging"` — correct configuration
- Project dependency in `project.json`: **`UiPath.System.Activities: [22.10.5]`** (the bug version per the playbook)
- Asset record in Orchestrator: `myHiddenAsset` is present with `ValueType: "Credential"`, `ValueScope: "Global"`, valid credential value — asset layer is healthy
- Error at 2026-05-13T18:02:12.299Z: `NullReferenceException: Object reference not set to an instance of an object. in Main.xaml at LogMessage "Log Message" at Sequence "Main Sequence" at Main "Main"`
- The NRE is downstream of `Get Credential`, consuming `username + new System.Net.NetworkCredential(string.Empty, pass).Password`. Either `username` or `pass` must be null at evaluation time — both are output bindings of the upstream Get Credential.
- Package version 22.10.5 falls in the buggy range called out by `get-asset-activity-bug-silent-failure.md`.

---

**Immediate fix:**

### System Activities (Root Cause) — pick ONE of two branches

1. **Branch A — Upgrade the `UiPath.System.Activities` package (recommended).**
   - **Why:** Every release after 22.10.x ships the fix. The bug is in the activity's variable-binding code, not in the workflow.
   - **Where:** Studio → Manage Packages → `UiPath.System.Activities` → upgrade to the latest LTS (e.g., `25.10.x` or later). Save, rebuild, republish.
   - **Who:** RPA developer
   - **Source:** `system-activities/playbooks/get-asset-activity-bug-silent-failure.md` ("UiPath.System.Activities package version 22.10.x has a bug" branch)

2. **Branch B — Workaround: pre-create the output variables in the Variables panel BEFORE wiring them into the activity.**
   - **Why:** The bug only affects variables created via `Ctrl+K` during activity configuration. Variables created in the Variables panel first, then referenced from the activity, receive the output values correctly.
   - **Where:** Open `Main.xaml` in Studio. In the Variables panel for the Sequence, ensure `username` (String) and `pass` (SecureString) exist BEFORE the `Get Credential` activity. If they were created via Ctrl+K, delete the activity, recreate the variables in the panel, then re-add the activity and wire its outputs to the existing variables. Save, rebuild, republish.
   - **Who:** RPA developer
   - **Caution:** This is a workaround, not a fix. If a copy-paste or future edit re-introduces Ctrl+K-created variables, the bug returns. The package upgrade in Branch A is preferred.

---

**Preventive fix:**

1. **Studio** — Block project publish if `UiPath.System.Activities` is in the buggy range (`22.10.0` ≤ version ≤ `22.10.x latest patch`).
   - **Why:** The buggy version is documented and easily detected; preventing publish stops production regressions at the gate.
   - **Where:** Add a pre-publish check (Studio analyzer rule or CI workflow) that reads `project.json` and rejects the build if the package version is in the affected range.
   - **Who:** Platform / DevOps

2. **Studio** — Educate developers to use the Variables panel rather than `Ctrl+K` for activity output bindings.
   - **Why:** Ctrl+K is convenient but routinely confuses the variable-creation path for `Get` activities in any version. Pre-creating variables makes the binding explicit and robust against package regressions.
   - **Where:** Team coding standards / runbook.
   - **Who:** RPA team lead

3. **Orchestrator** — Configure an alert subscription for faulted jobs in the `Remote Debugging` folder so silent-failure-style regressions surface immediately.
   - **Where:** Orchestrator UI → Alerts → severity "Error" + folder filter for `Remote Debugging`.
   - **Who:** Admin or platform team
   - **Source:** https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/alerts

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | `UiPath.System.Activities` 22.10.x silent-failure bug — Get Credential completes without populating output variables | High | Confirmed | Yes | Job logs show NRE downstream of Get Credential with NO error from Get Credential itself + `project.json` lists `UiPath.System.Activities: [22.10.5]` + asset/folder/role/license all verified healthy | Branch A: upgrade `UiPath.System.Activities`; OR Branch B: pre-create output variables in Variables panel |

---

Would you like help applying the fix — bumping `UiPath.System.Activities` in `project.json` and regenerating the lock file, or walking through the Variables-panel workaround? I can also clean up the `.local/investigations/` folder if you no longer need it.
