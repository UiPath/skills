# Final Resolution

Investigation complete. Here is the finding, presented as the presenter agent assembled it.

---

**Root Cause:** The Microsoft 365 Scope in the **ERN** process is configured for **Interactive Token** authentication (no account bound — the Account field still reads "Please select an account.", Integration Service off), which is the wrong and fragile auth choice for this Agent/StudioPro execution context. Interactive Token requires a human to complete a browser sign-in within a 30-second window; in this no-bound-account agent run nobody completed it, so authentication timed out and the job faulted. Switch the scope to app-only authentication (Application ID + Client Secret, or Application ID + Certificate).

**What went wrong:** The **Get Email List** (`GetEmailListConnections`) activity tried to resolve the **Inbox** mail folder, which forced an interactive Microsoft sign-in that no one completed within 30 seconds, raising `System.TimeoutException` and faulting the job.

**Why:** Tracing the chain across both domains:
- **o365-activities (root cause):** The Microsoft 365 Scope is set to `AuthenticationType=InteractiveToken` with Integration Service off (`UseConnectionService=False`) and no account bound (`Account = "Please select an account."`). Interactive Token is a delegated, attended-only flow — per UiPath docs it requires a person to finish a browser/WAM sign-in and is not supported directly in the scope for unattended-style robots (only via Integration Service, which refreshes the token and was not in use here). When **Get Email List** called Graph to resolve the **Inbox** folder, the runtime had no bound account and no cached token to reuse silently, so it raised a fresh interactive sign-in prompt (`GraphClientServiceFactory.LoginWithInteractiveTokenAsync`). With no sign-in completed in the 30-second limit, `TimeoutAfter` cancelled the operation and threw `System.TimeoutException`, wrapped up to `Office365Exception`.
- **orchestrator (propagation):** The job ran as Source=Agent / RuntimeType=StudioPro (Type=Attended, RequiresUserInteraction=true) on machine **MOCK-HOST**. This execution context is where the auth choice became fragile: there was no guaranteed interactive desktop session to complete the sign-in, so the underlying activity timeout surfaced as a **Faulted** job rather than a recoverable prompt. This is the dominant recurring failure mode for **ERN** — at least four Agent/Attended runs timed out in the 30-second-plus band across 2026-05-12 to 2026-06-09. Note one prior Agent/Attended run did succeed (job key af31127b, 2026-05-14), so this context is not categorically incapable of completing interactive auth; Interactive Token is simply the wrong, fragile choice here and fails whenever no human completes the prompt in time.

**Evidence**

### o365-activities (Root Cause)
- Microsoft 365 Scope span (`Office365ApplicationScope`) ran 10:49:39.313 → 10:49:39.351 UTC and completed successfully (Status=1). Attributes: `AuthenticationType=InteractiveToken`, `UseConnectionService=False`, `OAuthApplication=UIPATH`, `DataStoreLocation=DISK`, `Environment=Global`, and `Account = "Please select an account."` (no account bound).
- **Get Email List** (`GetEmailListConnections`) started 10:49:39.921 UTC, configured for mail folder **Inbox** (SelectionMode=EnterPath), MaxResults=50, connector `uipath-microsoft-outlook365`.
- The .NET call chain genuinely entered the interactive token path: `GetEmailListConnections.SafeExecuteAsync` → `BaseMailFolderArgument.ResolveAsync` → `GraphServiceClientProxy.GetMailFolderByPathAsync` → `UserMailFoldersCollectionRequest.GetAsync` → `AuthenticationHandler.SendAsync` → `AuthorizeAsync` → `GraphClientServiceFactory.AuthenticateAsync` → `ResolveAccessTokenAsync` → `LoginWithInteractiveTokenAsync` → `TimeoutAfter`. This was not a silent/cached-token path and not a pre-Graph configuration short-circuit.
- Inner-most exception, verbatim: `System.TimeoutException: The client did not complete the authentication after 30 seconds, and as a result the operation was canceled. Authentication type: InteractiveToken.` No "Access token has expired", no `AADSTS` code, no consent text, no "Automation Cloud cannot be reached" wording — this is the interactive-timeout pattern, not the token-expiry/consent/network variants.
- Timing is consistent with the 30-second auth limit: the child "Resolving drive item by path" (Inbox) ran at 10:50:11.195 UTC, about 31.5 seconds after the activity started; the job faulted at 10:50:41.847 UTC (~63 seconds total).
- Source: `authentication-token-invalid.md` (§ Context — "Interactive login timed out or was cancelled"); evidence `H1-trace-analysis.json`, `H2-auth-mode-analysis.json`; raw `triage-job-traces.json`, `triage-job-get.json`.

### orchestrator (Propagation)
- Job: process **ERN**, in folder **Shared**, State=**Faulted**, started 2026-06-09 10:49:38 UTC, ended 2026-06-09 10:50:41 UTC (job key b7974725-4438-4315-a9cc-9ec41f8acd62, job ID 4015051). Entry point `O365_Auth401.xaml`.
- Execution context: Source=Agent, SourceType=Agent, Type=Attended, RuntimeType=StudioPro, RequiresUserInteraction=true, RemoteControlAccess=None, machine **MOCK-HOST**, ErrorCode=Robot. One error logged, from **Get Email List**.
- Recurring pattern across **ERN** Agent/Attended runs (2026-05-12 to 2026-06-09): at least four faults in the 30-second-plus timeout band (this job ~63s; plus job keys d5fed611 ~71s, bad89b79 ~34s, 43e192cf ~41s). One Agent/Attended run succeeded (af31127b, 2026-05-14, ~3.4s), bounding the claim — the mode is fragile, not impossible. (Four sub-2-second Agent/Attended faults exist but are a different/earlier mode whose traces were not fetched; they are not claimed as instances of this 30-second timeout.)
- Source: evidence `H2-auth-mode-analysis.json`; raw `triage-job-get.json`, `triage-jobs-list.json`, `triage-job-history.json`.

**Immediate fix**

### o365-activities (Root Cause)
1. Switch the Microsoft 365 Scope from Interactive Token to app-only authentication — set the scope's authentication to **Application ID + Client Secret** or **Application ID + Certificate** (OAuth 2.0 client-credentials, with application permissions), which requires no runtime user interaction.
   - **Why:** The fault is a 30-second interactive sign-in timeout (`System.TimeoutException ... Authentication type: InteractiveToken`) in an Agent/StudioPro run with no human to complete the browser prompt and no bound account to reuse a token silently. App-only auth removes the runtime sign-in entirely.
   - **Where:** In Studio, on the **Microsoft 365 Scope** activity in `O365_Auth401.xaml`, change the `AuthenticationType` property to `ApplicationIdAndSecret` or `ApplicationIdAndCertificate` and supply the App ID + secret/certificate from your Entra ID (Azure AD) app registration.
   - **Who:** RPA developer (with an admin to provision/grant application permissions on the app registration).
   - **Source:** `authentication-token-invalid.md` (§ Resolution — "For unattended runs, switch to app-only authentication (App ID + Secret or Certificate) instead of Interactive Token."); corroborated by docsai `https://docs-staging.uipath.com/activities/other/latest/productivity/application-id-and-secret` and `…/application-id-and-certificate`

   Note: Selecting/binding an account for Interactive Token (the "Please select an account." facet) would only help on an attended desktop where a human completes the sign-in — it does NOT make Interactive Token viable for this Agent/StudioPro path. The auth-type change is the fix.

### orchestrator (Propagation)
1. After switching auth, re-run **ERN** in the same Agent/StudioPro mode and confirm it reaches Successful in **Job Details**; treat any remaining Faulted state as a separate fault to investigate.
   - **Why:** The job surfaced as Faulted (a faulted job must be restarted manually — Orchestrator does not auto-retry it), so a manual verification run is needed to confirm the auth change cleared the timeout.
   - **Where:** Orchestrator → folder **Shared** → Jobs → **ERN** → Job Details.
   - **Who:** Process owner / RPA developer.
   - **Source:** docsai `https://docs-staging.uipath.com/orchestrator/automation-cloud/latest/user-guide/job-states`

**Preventive fix**

1. **o365-activities** — Standardize the Microsoft 365 Scope on a non-interactive auth flow for any Agent/StudioPro or unattended-style execution: app-only auth (App ID + Secret/Certificate), or route through an Integration Service connection (which keeps an Interactive-Token-based connection alive by refreshing the token). Reserve bare Interactive Token for genuinely attended desktop runs where a human completes the sign-in.
   - **Why:** The cited auth matrix shows Interactive Token is attended-only and is not supported directly in the scope for unattended/headless robots; using it here is the structural cause of the recurring 30-second timeouts.
   - **Where:** The **Microsoft 365 Scope** authentication configuration in `O365_Auth401.xaml`, and/or an Integration Service Microsoft 365 connection.
   - **Who:** RPA developer / platform team.
   - **Source:** docsai `…/connect-with-microsoft-365-scope`, `…/interactive-token`, `…/how-to-connect-microsoft-365-activities`
2. **orchestrator** — Monitor for recurring authentication-timeout faults by querying faulted jobs filtered on the error text. Use the Orchestrator Jobs API with an `indexof(Info, '<error text>') ne -1` filter (e.g. matching "did not complete the authentication after 30 seconds") to retrieve faulted jobs carrying the interactive-auth timeout and analyze the pattern.
   - **Why:** At least four **ERN** Agent/Attended runs failed identically over roughly a month; Orchestrator provides no built-in retry or alerting on faulted jobs, so detection relies on inspecting Job Details / querying by error text.
   - **Where:** Orchestrator → Jobs (Job Details / Job States) and the Orchestrator Jobs API (filter on the `Info` error text).
   - **Who:** Platform team / admin.
   - **Source:** docsai `…/job-states`, `…/jobs-requests`

**Investigation summary**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H2 | Interactive Token is the wrong/fragile auth choice for this Agent/StudioPro no-bound-account context — fails whenever no human completes the 30s sign-in. | Medium | Confirmed | **Yes** (depth-verified) | `AuthenticationType=InteractiveToken`, `UseConnectionService=False`, `Account="Please select an account."`; Source=Agent/RuntimeType=StudioPro; stack reached `LoginWithInteractiveTokenAsync`; auth matrix; recurring 30s+ faults w/ one prior success | Switch scope to app-only auth, or route via Integration Service |
| H1 | Get Email List forced `LoginWithInteractiveTokenAsync`, which timed out at 30s. | Medium | Confirmed | No (symptom) | Inner-most `System.TimeoutException ... InteractiveToken`; span ordering proves token path entered; ~31.5s timing | Resolved by H2's fix |
| H3 | Scope has no account selected, forcing interactive sign-in. | Medium | Not confirmed (subsumed into H2) | No | Pre-Graph misconfig mechanism never fired — trace entered the Graph token path; playbook excludes token/auth-error cases | No separate fix |

---

**In short:** your last ERN job in the Shared folder faulted because the Microsoft 365 Scope uses **Interactive Token** auth with no bound account, running as an Agent/StudioPro job — no human completed the 30-second browser sign-in, so it timed out (`System.TimeoutException`). The fix is to switch that scope to **app-only authentication** (App ID + Secret or Certificate).

A couple of caveats worth your judgment: the doc links the search returned are `docs-staging.uipath.com` URLs (staging, not the public docs site) — treat them as pointers, not canonical. And H3 (the unselected-account hypothesis) was left untested-but-subsumed rather than independently confirmed; the depth-verifier judged its mechanism provably didn't fire, but I didn't run a separate test for it.

Want me to:
- **Test H3 explicitly** to close it out (cheap — reuses existing trace data), or
- **Help apply the fix** — I'd need the `O365_Auth401.xaml` project path (the working directory is empty, so I couldn't auto-locate it), or
- **Clean up** the `.local/investigations/` working files?
