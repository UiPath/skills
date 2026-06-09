# Final Resolution

Here's what the investigation found.

---

**Root Cause:** The Microsoft 365 Scope activity in process "ERN" is configured to read its connection from an Orchestrator asset, and that asset does not resolve when the job runs in folder "Shared". The asset identifier comes back null, so connection resolution throws before any Microsoft 365 (Graph) call is ever made.

**What went wrong:** The Microsoft 365 Application Scope tried to load its connection from an Orchestrator asset that could not be retrieved, so the job faulted at startup.

**Why:** Process "ERN" started and reached its entry point `O365_AppScopeMisconfig.xaml`. The first activity to run, the Microsoft 365 Scope (Orchestrator asset that does not resolve) (`Office365ApplicationScope`), was configured in Orchestrator-asset connection mode (`ConfigLocation = OrchestratorAsset`, input mode Browse) pointing at the asset "MissingO365Asset" (path `uipath.missing.o365.asset`). At runtime the scope asked Orchestrator for that asset to build its connection; Orchestrator returned no usable asset identifier, so the internal `assetId` resolved to null and `GetApplicationFromAssetAsync` threw `System.ArgumentNullException` (Parameter `assetId`), wrapped as `Office365Exception: Could not retrieve the selected asset`. This happened inside connection resolution — before any credential/account field was read and before any Microsoft Graph call — which is why the job faulted roughly one second after it started (Running 12:31:12.160Z, Faulted 12:31:13.043Z). The fault originates entirely in the Office 365 Application Scope's connection-resolution path; Orchestrator was only the reporting layer.

**Evidence:**

### o365-activities (Root Cause)
- Job: process "ERN" (job key `292c80e4-bc4f-41e3-9897-0fe73e0c64db`), folder "Shared", State **Faulted**, on machine MOCK-HOST; started 2026-06-09T12:31:11.730Z, ended 2026-06-09T12:31:13.000Z (history: Running 12:31:12.160Z → Faulted 12:31:13.043Z). Entry point `O365_AppScopeMisconfig.xaml`.
- Faulted activity: the **Microsoft 365 Scope (Orchestrator asset that does not resolve)** (`UiPath.MicrosoftOffice365.Activities.Office365ApplicationScope`) — the activity span carries error status.
- Error (identical across job Info, the Error log entry at 12:31:12.342Z, and the trace span Exception): `UiPath.MicrosoftOffice365.Office365Exception: Could not retrieve the selected asset: 'Value cannot be null. (Parameter 'assetId')'` → inner `System.ArgumentNullException: Value cannot be null. (Parameter 'assetId')`, thrown at `Office365ApplicationScopeUtils...GetConnectionAsync>g__GetApplicationFromAssetAsync`. The null parameter is `assetId` (the asset identifier), not a credential field; no Graph/HTTP/`AADSTS` frame is present.
- Connection mode (trace span attributes): `ConfigLocation = OrchestratorAsset`, `UseConnectionService = False`, `RuntimeItemInputMode = Browse`, browse selection friendly name `MissingO365Asset`, full path `uipath.missing.o365.asset`. This confirms the scope ran in Orchestrator-asset mode, so asset resolution was on the execution path.
- The span also records `AuthenticationType = InteractiveToken` and `Account = "Please select an account."` — these are non-throwing captured placeholders, not the cause; the throw happened upstream at `assetId` resolution, before any account read.

**Note — sub-cause not discriminated (data gap):** The asset family-level cause is confirmed, but the *specific* sub-cause could **not** be determined from the available data. It is one of: (a) no asset by that name/path exists in folder "Shared"; (b) the asset name or path is wrong; (c) the robot account the job ran as lacks read access to the asset; or (d) the referenced asset is not a valid/complete connection asset (empty value). Distinguishing these requires an Orchestrator asset existence/permission query scoped to folder "Shared", and no asset list/get command is documented in this troubleshooting toolset's references (per its no-CLI-discovery rule), so it could not be run. The family-level fix below is the same regardless of which sub-cause applies; verifying the asset's state in folder "Shared" is your confirming step that narrows it.

**Immediate fix:**

### o365-activities (Root Cause)
1. Verify the asset the scope points at actually exists in the folder the "ERN" robot runs in, with the exact name/path the activity references.
  - Why: At runtime the scope resolved `assetId` to null for browse selection `MissingO365Asset` / `uipath.missing.o365.asset`, throwing `ArgumentNullException(assetId)` in `GetApplicationFromAssetAsync` before any Graph call — the configured asset did not resolve in folder "Shared".
  - Where: Orchestrator → folder "Shared" → Assets. Confirm an asset matching the scope's configured name/path exists there; check the name/path for typos against what the activity references (`uipath.missing.o365.asset`).
  - Who: RPA developer (asset reference) with admin/platform team (folder asset existence + permissions).
  - Source: `application-scope-misconfigured.md` § Resolution (Asset).
2. If the asset exists but the job still can't read it, grant the robot account read access to it; if the name/path is wrong, correct the asset selection on the Microsoft 365 Scope activity.
  - Why: The asset family covers missing-from-folder, wrong-name/path, no-read-permission, and invalid/empty-asset sub-causes; the data needed to single one out was not available to this investigation, so apply whichever matches the state you find in step 1.
  - Where: Orchestrator → folder "Shared" → Assets (permissions); and in Studio, the Microsoft 365 Scope activity's connection/asset configuration in `O365_AppScopeMisconfig.xaml`.
  - Who: admin/platform team (permissions) and RPA developer (activity asset selection).
  - Source: `application-scope-misconfigured.md` § Resolution (Asset).
3. Alternatively, switch the Microsoft 365 Scope off Orchestrator-asset connection mode and configure credentials directly.
  - Why: The playbook offers configuring credentials directly as an alternative to relying on an Orchestrator asset, removing the asset-resolution dependency that failed here.
  - Where: Studio → the Microsoft 365 Scope (Orchestrator asset that does not resolve) activity in `O365_AppScopeMisconfig.xaml` → change the connection configuration from the Orchestrator asset to direct credentials.
  - Who: RPA developer.
  - Source: `application-scope-misconfigured.md` § Resolution (Asset).

**Preventive fix:**

1. o365-activities — After fixing the asset, validate the scope's connection before relying on the process in production (e.g., test the connection / run a smoke job in folder "Shared" so a non-resolving asset is caught at design/validation time rather than at runtime).
  - Why: This fault surfaced only at runtime (`assetId` null at execution), faulting the job ~1s after start with no Graph call; catching asset-resolution failures earlier prevents repeat faulted jobs.
  - Where: Studio (test connection on the Microsoft 365 Scope) and a controlled run in Orchestrator folder "Shared".
  - Who: RPA developer.
  - Source: `application-scope-misconfigured.md` § Resolution / Context.

**Investigation summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Microsoft 365 Scope reads its connection from an Orchestrator asset (`ConfigLocation = OrchestratorAsset`, browse selection `uipath.missing.o365.asset`) that does not resolve in folder "Shared"; `assetId` resolves null and `GetApplicationFromAssetAsync` throws before any Graph call. | Medium (playbook) | Confirmed | Yes | Inner `ArgumentNullException(assetId)` at `GetApplicationFromAssetAsync` (job Info, Error log, trace Exception); span `ConfigLocation=OrchestratorAsset`, Browse → `uipath.missing.o365.asset`; job Faulted ~1s after start. Sub-cause not discriminated. | Correct/locate the Orchestrator asset in folder "Shared", ensure it exists and the robot can read it, or switch the scope to direct credentials. |
| H2 | Same playbook, alternative reading: the asset resolves but the connection build fails on an empty/invalid asset payload or incomplete InteractiveToken auth. | Medium | Eliminated | No | Stack shows the null is `assetId` thrown *before* any payload parse or account read; the `Account="Please select an account."` / `InteractiveToken` attributes are non-throwing placeholders. | n/a |

---

**The one open item:** the investigation couldn't pin down *which* asset sub-cause it is (missing entirely / wrong name / no read permission / empty), because the troubleshooting toolset doesn't have a documented asset-listing command. I'm not bound by that restriction outside the investigation — I can query the assets in folder "Shared" directly to close that gap.
