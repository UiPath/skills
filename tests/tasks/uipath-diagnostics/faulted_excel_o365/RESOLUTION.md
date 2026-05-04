# Final Resolution

**Root Cause:** The published process **RPA Workflow** is hard-bound in source code to the **Microsoft OneDrive & SharePoint** connection key `e62228b7-ffc2-49dc-a779-29207b0d2b6f`, which lives in **original_email@test.com**'s personal workspace. When the job ran under **replacement_email@test.com** in their own Personal folder ("replacement_email@test.com's workspace"), Integration Service rejected the lookup because a personal-workspace connection is not accessible to another user. The workflow has no `bindings_v2.json`, so the connection ID cannot rebind per-folder at deploy time — the foreign ID is what the robot sent.

**What went wrong:** The "For Each Sheet in Workbook" activity in `Main.xaml` calls Integration Service with another user's connection ID, and Integration Service responds with `Connection [...] is invalid or you do not have access to it`, which faults the job immediately.

**Why:** The author published the project while bound to **original_email@test.com**'s OneDrive connection (resource file `resources/solution_folder/connection/uipath-microsoft-onedrive/original_email@test.com.json`, key `e62228b7-…`). Both `<ForEachSheetConnections>` (line 81) and the nested `<DriveItemArgument>` (line 96) of `RPA Workflow/Main.xaml` hard-code this key as `ConnectionId` / `ConnectionKey`, with `UseConnectionService="True"`. Since no `bindings_v2.json` rebinds the connection per folder, the runner's robot sends original_email@test.com's key to Integration Service. The runner does have a valid OneDrive connection (`86ec2bec-fcde-44e3-a793-9bd3ea0cd0ab`, **Enabled**, **IsDefault=Yes**) in their own Personal folder — but the workflow does not reference it. Integration Service's `GraphConnectionFactory.Create` calls `ConnectionClient.GetConnectionAsync(...)`, the HTTP probe returns the access error, and `BaseForEachConnectionServiceActivity.Execute` propagates `UiPath.MicrosoftOffice365.Office365Exception` up to the Orchestrator job, which records `State=Faulted` with `ErrorCode=Robot`.

## Evidence

### Integration Service (Root Cause)

- Connection in error: ID `e62228b7-ffc2-49dc-a779-29207b0d2b6f` — declared in `resources/solution_folder/connection/uipath-microsoft-onedrive/original_email@test.com.json` as `resource.name="original_email@test.com"`, `spec.connectorName="Microsoft OneDrive & SharePoint"`, `spec.connectorKey="uipath-microsoft-onedrive"`, `spec.authenticationType="AuthenticateAfterDeployment"`.
- Workflow binding: `RPA Workflow/Main.xaml` line 81, `<umae:ForEachSheetConnections DisplayName="For Each Sheet in Workbook" IdRef="ForEachSheetConnections_1" ConnectionId="e62228b7-ffc2-49dc-a779-29207b0d2b6f" UseConnectionService="True">`; line 96 nested `<umafm:DriveItemArgument ConnectionKey="e62228b7-ffc2-49dc-a779-29207b0d2b6f" ManualEntryItemUrl="IT_Services_Marketshare_2018Q2.XLSM">`.
- No `bindings_v2.json` exists anywhere under the project — no per-folder rebinding is configured.
- Runner's connection in their Personal folder ("replacement_email@test.com's workspace", key `7b6f4886-bec5-4ffc-91cc-dd9a3f9febd0`): one **Microsoft OneDrive & SharePoint** connection — **replacement_email@test.com** (ID `86ec2bec-fcde-44e3-a793-9bd3ea0cd0ab`), State **Enabled**, IsDefault **Yes**. The offending key `e62228b7-…` is **not present** in this folder.
- Source: `evidence/triage-initial.json`, `evidence/H1-source-analysis.json`, `raw/H1-connection-resource.json`, `raw/H1-main-xaml-foreachsheet.json`, `raw/triage-connections-list.json`.

### Orchestrator (Propagation)

- Job key `3033bce6-5585-4455-aaec-db7a9f791126`, ReleaseName **RPA.Workflow**, Type **Unattended**, RuntimeType **Development**, State **Faulted**, ErrorCode **Robot**.
- StartTime `2026-03-31T10:15:49.240Z` → EndTime `2026-03-31T10:15:57.013Z` (~8 s — fault on first IS call).
- Folder: "replacement_email@test.com's workspace" (Personal, key `7b6f4886-bec5-4ffc-91cc-dd9a3f9febd0`, id 1321239), HostMachineName `DESKTOP-HOME-WO`, OrchestratorUserIdentity `replacement_email@test.com`.
- Job `Info` carries the verbatim downstream stack: `UiPath.MicrosoftOffice365.Office365Exception: Connection [e62228b7-ffc2-49dc-a779-29207b0d2b6f] is invalid or you do not have access to it` → inner `UiPath.ConnectionClient.Contracts.ConnectionHttpException` raised at `GraphConnectionFactory.Create` and surfaced by `BaseForEachConnectionServiceActivity.Execute` in `Main.xaml at ForEachSheetConnections "For Each Sheet in Workbook"`.
- Activity package: `UiPath.MicrosoftOffice365.Activities 3.7.10`.
- Source: `raw/triage-job-details.json`, `raw/triage-folders-list.json`.

## Immediate fix

### Integration Service (Root Cause)

1. **Repoint the workflow at the runner's own Microsoft OneDrive & SharePoint connection.**
   - Why: The activity is hard-bound to `e62228b7-…` (original_email@test.com's personal-workspace connection), which the runner cannot access. The runner already has a valid Enabled connection (`86ec2bec-fcde-44e3-a793-9bd3ea0cd0ab`, **replacement_email@test.com**) in their own Personal folder, so no new connection needs to be created — it just needs to be selected.
   - Where: In UiPath Studio, open `RPA Workflow/Main.xaml`, select the **For Each Sheet in Workbook** activity (`ForEachSheetConnections_1`), and in the activity's connection dropdown pick the **replacement_email@test.com** Microsoft OneDrive & SharePoint connection. This rewrites both `ConnectionId` at line 81 and the nested `DriveItemArgument.ConnectionKey` at line 96 to `86ec2bec-fcde-44e3-a793-9bd3ea0cd0ab`. Save, then republish the package and update the **RPA.Workflow** process in "replacement_email@test.com's workspace".
   - Who: RPA developer (the user, since this is the Personal workspace).
   - Source: Playbook `skills/uipath-diagnostics/references/products/integration-service/playbooks/connection-invalid.md`, `## Resolution` → "If connection belongs to a different user's workspace".

2. **Re-run the failed job after republishing.**
   - Why: The job ended after ~8 s on the first IS call, before any business logic ran, so it is safe to restart cleanly with the corrected connection.
   - Where: Orchestrator → "replacement_email@test.com's workspace" → Jobs → Start a new job for **RPA.Workflow** (or rerun the faulted job).
   - Who: RPA developer / process owner.
   - Source: Job details `raw/triage-job-details.json` (StartTime → EndTime span ≈ 8 s, fault at first activity).

## Preventive fix

1. **Integration Service — make the connection per-user via `bindings_v2.json` if this process will be reused outside the author's workspace.**
   - Why: There is currently no `bindings_v2.json` in the project, so the connection ID is hard-coded in `Main.xaml`. Anyone who deploys this elsewhere will hit the same fault. A folder binding lets each deployment resolve to its own connection at publish time.
   - Where: Add `bindings_v2.json` at the project root binding the `uipath-microsoft-onedrive` connection per folder/user, so on deploy each environment maps to a connection in that folder. Alternatively, deploy to a **shared (Standard) folder** with a single shared **Microsoft OneDrive & SharePoint** connection that has the right scope, instead of a Personal workspace.
   - Who: RPA developer.
   - Source: Playbook `skills/uipath-diagnostics/references/products/integration-service/playbooks/connection-invalid.md`, `## Resolution` → "If this is a solution" / "consider deploying to a shared folder with a shared connection".

2. **Integration Service — never publish a project against another user's personal-workspace connection.**
   - Why: The resource file `resources/solution_folder/connection/uipath-microsoft-onedrive/original_email@test.com.json` shipped inside the project; this is exactly the misconfiguration the playbook calls out.
   - Where: Before publishing, check `resources/solution_folder/connection/<connector>/*.json` and confirm `resource.name` matches the deploying user (or is a connection in a Shared/Standard folder). For `authenticationType: AuthenticateAfterDeployment`, remember to authenticate the connection from the target folder before the first run.
   - Who: RPA developer.
   - Source: Playbook `## Resolution` → "If connection not found in folder" (authenticate after deployment guidance) and `## Investigation` step 1 (use `spec.connectorName` and `resource.name` to verify ownership before publish).

3. **Orchestrator — add an explicit retry/alert policy around the faulted child-job pattern (propagation layer).**
   - Why: Orchestrator does not auto-retry **Faulted** unattended jobs; the job ended in **Faulted** with `ErrorCode=Robot` and stayed there until manual intervention. This propagated the IS fault into a stuck job state with no automatic recovery.
   - Where: If this process will be invoked from a parent workflow, monitor the child job's state via Orchestrator activities/APIs and, on **Faulted**, log the failure and start a new job run (using a retry counter to avoid retry storms). Use the **Should Stop** activity inside the child workflow so the cancel signal is honored cleanly. For unattended faulted jobs, enable **Enable Recording** so execution media is captured for diagnosis.
   - Who: RPA developer (parent process), with platform team consulted on cloud Orchestrator settings.
   - Source: docsai — https://docs-staging.uipath.com/orchestrator/automation-cloud/latest/user-guide/job-states and https://docs-staging.uipath.com/orchestrator/automation-suite/2024.10/user-guide/job-states ; "Should Stop" activity https://docs-staging.uipath.com/activities/docs/should-stop ; download execution media https://docs-staging.uipath.com/orchestrator/automation-cloud/latest/user-guide/managing-jobs#downloading-execution-media .

## Investigation summary

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Process **RPA Workflow** is hard-bound in `Main.xaml` to **Microsoft OneDrive & SharePoint** connection `e62228b7-ffc2-49dc-a779-29207b0d2b6f` owned by **original_email@test.com**'s personal workspace; runner **replacement_email@test.com** cannot access it, with no `bindings_v2.json` to rebind per folder. | High | Confirmed | Yes | Job error contains the offending connection key verbatim; `resources/solution_folder/connection/uipath-microsoft-onedrive/original_email@test.com.json` declares `key=e62228b7-…` with `name=original_email@test.com`; `Main.xaml` line 81 (`ForEachSheetConnections_1`) and line 96 (`DriveItemArgument`) hard-code that key; runner's Personal folder lists only `86ec2bec-…` (their own enabled connection); no `bindings_v2.json` anywhere in the project. | Repoint **For Each Sheet in Workbook** at the runner's **Microsoft OneDrive & SharePoint** connection (`replacement_email@test.com`, `86ec2bec-fcde-44e3-a793-9bd3ea0cd0ab`) in Studio, republish, and rerun the job; longer term, add `bindings_v2.json` (or move to a Shared folder with a shared connection) so the connection is not hard-bound to one user's workspace. |

---