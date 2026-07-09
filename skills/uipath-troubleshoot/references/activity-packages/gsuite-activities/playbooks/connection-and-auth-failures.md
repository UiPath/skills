---
confidence: medium
---

# GSuite — Connection, authentication, and permission failures

## Context

This playbook covers failures that originate in the identity/connection layers — Integration Service connection resolution, Google OAuth token validation, or Google-side authorization — rather than in the requested resource or the activity inputs. The fix is always about *who is connecting and what they are allowed to do*, never about the file/range/filter the activity targets.

What this looks like — any of the following messages:

- `Authentication attempt took longer than <N> seconds to complete, and was cancelled.` — a `System.TimeoutException` thrown while establishing the connection / acquiring the OAuth token, **not** while calling the Google API. This is the only place GSuite throws a real `TimeoutException`. `<N>` is the configured connection/auth timeout in seconds (legacy scope: the `TimeoutMS` property).
- `Invalid authentication credentials.` — wrapped `GSuiteException`, Google API returned **HTTP 401** with no more specific reason. The access token presented to Google was rejected.
- `Authentication error: the access token is expired or invalid.` — wrapped `GSuiteException`, Google error reason `authError`. Same root as 401: the token is no longer valid.
- `Permission to the resource was denied.` — wrapped `GSuiteException`, Google API returned **HTTP 403** with no more specific reason. The token is valid but the account/connection is not authorized for this operation.
- `The user does not have sufficient permissions for the file.` — wrapped `GSuiteException`, Google reason `insufficientFilePermissions`. The authenticated account lacks access to the specific Drive item.
- `The domain administrators have disabled Drive apps.` — wrapped `GSuiteException`, Google reason `domainPolicy`. A Workspace admin policy blocks the connection's app.
- A raw `UiPath.ConnectionClient.Contracts.ConnectionHttpException` (or a `GSuiteException` carrying its message verbatim) — the Integration Service connection layer itself failed when the activity tried to fetch a token: connection deleted after the workflow started, connection unreachable, token refresh rejected because the user revoked authorization. Legacy `GSuiteApplicationScope` activities using `IntegrationService` auth surface this raw at runtime.
- ``Connection [<connectionId>] is invalid or you do not have access to it`` — wrapped `GSuiteException` (the `ConnectionHttpException` surfaced on the activity). The configured `ConnectionId` does not resolve to a connection the running identity can use: it was deleted/disabled, is owned in another folder/workspace, the robot account lacks permission to the connection's folder, or the project binding points at the wrong connection. Thrown during token acquisition, before any Google API call.

**Design-time variant:** when picking a Drive/Sheets item in the Studio browse dialog fails with *"Items cannot be retrieved"*, the underlying cause is frequently a `ConnectionHttpException` with **HTTP 403** and code `CNS1044` (insufficient permissions) or `CNS1045` (insufficient folder permissions). This is the same authorization problem surfacing at design time instead of run time.

**Any `CNS…` code in the `ConnectionHttpException` detail** identifies the exact Connection Service failure and outranks the status class — route it via the [CNS error-code reference](../../../products/integration-service/cns-error-codes-reference.md). The ones seen from these activities: `CNS1008` (connection not in authorized state → re-authenticate), `CNS1006`/`CNS1049` (connection deleted / personal-workspace), `CNS1045` (folder permission — the message names which one), `CNS2xxx` (Connection Service dependency failure — retry, then escalate).

What activities can produce these errors:
Every `*Connections` activity (all Gmail, Drive, Sheets, Docs, Calendar, Tasks, Forms, Apps Script modern activities) and every legacy `GSuiteApplicationScope` child, because all of them resolve a connection and acquire a token before doing any work. Auth-timeout is most visible on the scope/connection itself and on the first activity to execute after a cold token.

What can cause it:
- **Expired or revoked token** (401 / `authError`): the connection's OAuth grant lapsed, the user changed their Google password, or authorization was revoked in the Google account's security settings.
- **Insufficient scope / sharing** (403 / `insufficientFilePermissions`): the connection's OAuth scopes don't include the needed Drive/Gmail/Sheets scope, or the target resource was never shared with the authenticated account.
- **Admin / domain policy** (`domainPolicy`): a Workspace administrator disabled third-party apps or the specific connector.
- **Connection lifecycle** (raw `ConnectionHttpException`): the Integration Service connection was deleted, disabled, or is unreachable between scope setup and activity execution.
- **Auth timeout** (`TimeoutException`): the OAuth flow or token exchange exceeded the configured timeout — slow network to Google's OAuth endpoint, an interactive consent prompt that was never completed, or a `TimeoutMS` set too low on a legacy scope.

> **Different cause — do not apply this playbook:**
> - **`The storage quota was exceeded.`** / **`Upload failed after <N> bytes. ...`** is also an HTTP 403, but it is a *quota* failure, not an authorization failure — use [upload-storage-quota-exceeded.md](./upload-storage-quota-exceeded.md).
> - **`The resource was not found.`** (404) means the resource doesn't resolve, not that access was denied — use [drive-file-not-found.md](./drive-file-not-found.md).
> - Transient 5xx / rate-limit / per-request timeout (`A task was canceled.`) → use [transient-and-timeout-errors.md](./transient-and-timeout-errors.md).

## Investigation

1. **Identify the failing layer from the message.** Auth-timeout text → token acquisition. 401 / `authError` → token rejected. 403 / `insufficientFilePermissions` / `domainPolicy` → authorization. Raw `ConnectionHttpException` → the IS connection itself.
2. **Capture the connection** in evidence — the Integration Service connection name and the Google account email it authenticates as. Confirm the connection still exists and is enabled in Integration Service.
3. **For 401 / auth errors:** check whether the connection's token can be refreshed — reconnect/re-authorize the connection and confirm it succeeds against Google.
4. **For 403 / permission errors:** capture the target resource (Drive item, mailbox, spreadsheet) and confirm the authenticated account has access to it in the Google UI, and that the connection's OAuth scopes cover the operation.
5. **For auth-timeout:** capture the configured timeout (`TimeoutMS` on a legacy scope) and whether the auth path requires interactive consent. Confirm network reachability to Google's OAuth endpoint from the robot.

## Resolution

- **If the token is expired or revoked (401 / `authError`):** Reconnect/re-authorize the Integration Service connection (or refresh the legacy scope's credential). Confirm the Google account password/2FA didn't change and that authorization wasn't revoked in the Google account security settings.
- **If authorization is insufficient (403 / `insufficientFilePermissions`):** Grant the authenticated account access to the target resource, or recreate the connection with the OAuth scopes the operation requires (e.g., full Drive scope rather than read-only). For the design-time `CNS1044`/`CNS1045` browse failure, the same scope/permission grant fixes the picker.
- **If a domain policy blocks the app (`domainPolicy`):** Escalate to the Google Workspace administrator to allow the connector/app.
- **If the connection itself failed (raw `ConnectionHttpException`):** Confirm the connection exists and is enabled in Integration Service; recreate it if it was deleted. Verify the robot has network reachability to the connection service. If the detail carries a `CNS…` code, apply the exact remediation from the [CNS error-code reference](../../../products/integration-service/cns-error-codes-reference.md) instead of guessing from the status class.
- **If authentication timed out:** Confirm network reachability and latency to Google's OAuth endpoint. Raise the legacy scope's `TimeoutMS` if the auth path is legitimately slow; for interactive OAuth, ensure the consent flow can complete in the robot's session (unattended robots cannot answer an interactive prompt).

If the connection reconnects cleanly, the account demonstrably has access, and the error persists, the cause is outside the connection layer — re-triage against the resource-not-found or transient-error playbooks.
