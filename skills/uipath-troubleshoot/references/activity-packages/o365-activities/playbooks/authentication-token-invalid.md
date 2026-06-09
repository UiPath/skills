---
confidence: medium
---

# O365 — Authentication / token invalid (401)

## Context

What this looks like — the job faults the moment an Office 365 activity (or the Microsoft 365 Application Scope) tries to authenticate, before any business operation runs. The message is one of:

- A raw Microsoft Graph authentication message surfaced verbatim — most often `Access token has expired or is not yet valid.` or similar wording mentioning an invalid/expired token. This is the typical token-expiry case.
- `The caller is not authenticated.`
- `Authentication failed.`
- `Authentication was cancelled.`
- `A configuration error AADSTS<code> occurred in the activity. For information on how to solve this, visit the page: https://docs.uipath.com/activities/other/latest/productivity/aadsts-errors` — an Entra ID (Azure AD) failure at token acquisition. The `AADSTS<code>` identifies the exact cause (e.g. `AADSTS65001` = admin consent not granted; `AADSTS700016`/`AADSTS7000215` = wrong app id/secret).
- `Authentication attempt took longer than <N> seconds to complete, and was cancelled.` — an interactive sign-in that wasn't completed in time. This fires while *creating / adding* the connection (the interactive sign-in wizard, default 60s), not mid-run for an already-authenticated connection.
- `The client did not complete the authentication after <N> seconds, and as a result the operation was canceled. Authentication type: InteractiveToken.` — an **Interactive Token** sign-in triggered *mid-run* (an activity needed a token and opened a browser/WAM sign-in) that nobody completed in the window (default 30s). This is the signature of Interactive Token running where no human can complete the prompt — most often an **unattended / Agent / StudioPro** job, or an attended run where the user never finished the sign-in.
- `No default connection is available.`
- `Automation Cloud cannot be reached. It may be a network fluctuation on the Runtime machine.`

What activities can produce this:
- **Any** Mail, Files/OneDrive, or Excel Online activity — they all authenticate through the same Microsoft 365 connection / Application Scope. Representative: **Send Mail** (`SendMailConnections`), **Get Email List** (`GetEmailListConnections`), **Get File List** (`GetFileListConnections`), **Upload File** (`UploadFilesConnections`), **Read Range** (`ReadRangeConnections`).

What can cause it:
- **Access token expired or invalid.** The cached token is no longer valid and could not be silently refreshed (refresh token expired, password changed, session revoked).
- **Consent revoked or never granted.** The app registration lacks admin consent for a requested permission, surfaced as an `AADSTS` configuration error (commonly `AADSTS65001`).
- **Interactive login timed out or was cancelled — usually the *symptom* of a wrong auth choice.** With Interactive Token auth a browser/WAM sign-in wasn't completed within the timeout. The timeout itself is the surface symptom; look one level up: **Interactive Token needs a human to complete the sign-in, so it is the wrong auth mode for an unattended / Agent / StudioPro job, or a scope with no bound account** — there the prompt can never be completed and every run times out. (An occasional attended run can succeed when a person happens to finish the sign-in, so a single past success doesn't make the mode viable for unattended use.)
- **No connection / wrong connection.** No default Microsoft 365 connection is configured, or the selected connection has lost its authentication.
- **Connection service unreachable.** The Runtime machine can't reach Automation Cloud (network fluctuation) to resolve the connection.

> **Different cause, do not apply this playbook:**
> - `The caller doesn't have permission to perform the action.` / `Access restricted to the item's owner.` / a raw `Insufficient privileges to complete the operation.` — the caller **is** authenticated but lacks the Graph permission for the operation. Use **insufficient-graph-scope**.
> - Configuration faults that fire before authentication (`Could not retrieve the selected asset`, `You must provide a value for ...`, `Please select an account.`) — use **application-scope-misconfigured**.

## Investigation

1. Read the exact message and match it to one of the patterns above — the wording determines the fix path (token vs consent vs interactive-timeout vs connection vs network).
2. If the message contains `AADSTS<code>`, note the code and look it up (the linked docs page maps each code to its cause). `AADSTS65001` = consent not granted; secret/cert/app-id codes = wrong or expired credentials.
3. Identify the connection / Application Scope authentication type (Interactive Token, Integration Service connection, App ID + Secret/Certificate, Username/Password) — this determines how the token is obtained and how to renew it.
4. **If the message is an interactive sign-in timeout** (`The client did not complete the authentication ...`), check the job's **execution context**: an unattended / Agent / StudioPro robot has no one to complete the browser/WAM prompt, so the timeout is structural (every run fails the same way) — the root cause is the auth mode, not the timeout value. An attended run could simply have had the user not finish the sign-in in time.
5. Confirm whether the failure is permanent (token / consent / credential / auth-mode problem — fails every run) or intermittent (network reaching Automation Cloud — clears on retry).

## Resolution

- **If the token is expired/invalid:** re-authenticate the connection — re-run the interactive login, refresh/reconnect the Integration Service connection, or rotate and update the app secret/certificate that has expired.
- **If `AADSTS65001` / consent:** have an administrator grant admin consent for the permissions the app registration requests.
- **If another `AADSTS` credential code:** correct the Application ID / Tenant / secret / certificate to match the app registration.
- **If an interactive sign-in timed out in an unattended / Agent / StudioPro context** (`The client did not complete the authentication after <N> seconds ... Authentication type: InteractiveToken.`): the root cause is the **auth mode**, not the timeout value. Switch the Microsoft 365 Scope to **app-only authentication (App ID + Secret or Certificate)** — the client-credentials flow needs no human — or route the connection through **Integration Service** (which refreshes the token). Selecting/binding an account only helps an *attended* desktop where a person completes the sign-in; it does **not** make Interactive Token viable for unattended/Agent runs, and raising the timeout won't help when no one is there to complete the prompt.
- **If an interactive sign-in timed out on an attended desktop:** complete the browser/WAM sign-in within the timeout window on the next run.
- **If `No default connection is available`:** select or configure a valid Microsoft 365 connection on the activity / Application Scope.
- **If `Automation Cloud cannot be reached`:** transient network issue — verify the Runtime machine's connectivity to Automation Cloud and re-run.

If the connection authenticates cleanly on its own (e.g. a test call succeeds) yet the activity still 401s, the cause is outside the activity — escalate (tenant-level conditional access, token lifetime policy, or a revoked session).
