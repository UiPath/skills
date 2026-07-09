---
confidence: high
---

# O365 — Insufficient Graph permission scope / access denied (403)

## Context

What this looks like — the job faults when an Office 365 activity calls Microsoft Graph and Graph returns HTTP 403. The caller is authenticated, but is not permitted to perform the operation. The message is one of:

- `The caller doesn't have permission to perform the action.` — the canonical 403.
- `Access restricted to the item's owner.`
- `The action is not allowed by the system.`
- A raw Microsoft Graph 403 message surfaced verbatim, e.g. `Insufficient privileges to complete the operation.`, `You do not have permissions to open this file in the browser.`, or `Group Shard is used in non-Groups URI.` — these arrive with a Graph error code the package doesn't recognize, so the original Graph text is shown as-is. (The common `accessDenied` code is *not* one of these — it maps to the fixed `The caller doesn't have permission to perform the action.` above.)

What activities can produce this:
- **Any** Mail, Files/OneDrive, or Excel Online activity. The required permission depends on the operation — common offenders are write/share operations that need broad scopes:
  - **Send Mail** (`SendMailConnections`) → `Mail.Send`
  - **Share Item** (`ShareItemConnections`), **Move/Copy/Delete/Upload** (`MoveItemConnections`, `CopyItemConnections`, `DeleteItemConnections`, `UploadFilesConnections`) → `Files.ReadWrite.All` / `Sites.ReadWrite.All`
  - **Read Range / Write Range** on SharePoint-hosted workbooks (`ReadRangeConnections`, `WriteRangeConnections`) → `Sites.Read.All` / `Sites.ReadWrite.All`
  - Read operations → the matching `*.Read` scope (`Mail.Read`, `Files.Read.All`, `Sites.Read.All`).

What can cause it:
- **Missing Graph permission scope.** The connected app registration (application permissions) or the signed-in user (delegated permissions) was never granted / admin-consented the permission the operation requires. With application (app-only) auth the scope set is fixed to the admin-consented permissions on the app — if the needed one isn't there, every call 403s.
- **App-only impersonation not authorized.** App-only auth is targeting a mailbox/user the app isn't allowed to act for, or that an application-access policy excludes.
- **Item-owner / sharing restriction.** The caller has the scope but is denied access to the specific resource (a SharePoint/OneDrive item restricted to its owner, or a file blocked from browser open).

> **Different cause, do not apply this playbook:**
> - `The resource could not be found.` / `Folder named '<name>' could not be found ...` — a missing or mistyped resource. Microsoft Graph sometimes returns **404 instead of 403** for cross-mailbox or shared-resource access the caller isn't entitled to (it hides existence from unauthorized callers). Those cases are covered by **mail-folder-not-found** and **drive-item-not-found**. Practical rule: wrong/mistyped path, name, or id → the not-found playbooks; the target is correct but the caller lacks the Graph permission or is denied access to it → this playbook.
> - `The caller is not authenticated.` / token-expiry messages — identity couldn't be established. Use **authentication-token-invalid**.
> - `The sharing link no longer exists, or you do not have permission to access it.` (Graph `accessDenied` / 403, often with an `@onedrive.linkFeatures` annotation, raised while resolving a OneDrive/SharePoint **sharing link**) — this is a **per-resource** failure on one specific shared item (the link was revoked, its sharing scope changed, or the item moved/was deleted), **not** a connection-wide missing scope. A genuine missing scope denies *every* call with the generic `The caller doesn't have permission to perform the action.` / raw `Insufficient privileges to complete the operation.`; this message names the link specifically. Treat it as **drive-item-not-found** (shared-link-no-longer-valid cause) — fix the sharing link, and do **not** keep "missing scope" as a live cause once you see this signature.

## Investigation

1. Confirm the message is a 403 permission pattern above and not a 404 not-found (which has a different message and a different fix).
2. Identify the failing operation and the Microsoft Graph permission it requires (read vs send vs write/share; OneDrive vs SharePoint Sites). The required scope follows from the operation, not the resource name.

## Resolution

- **If a permission scope is missing:** grant the required delegated or application permission on the app registration and have an administrator consent it — e.g. `Mail.Send` for sending mail, `Files.ReadWrite.All` / `Sites.ReadWrite.All` for sharing or writing files/SharePoint, the matching `*.Read` scope for read operations. Re-run after consent propagates.
- **If app-only impersonation is denied:** ensure the app is authorized for the target mailbox/site (e.g. the mailbox application-access policy includes the app) and that the impersonated user is correct.
- **If an item-owner / sharing restriction:** the resource owner must grant the caller access — the caller cannot self-authorize. Confirm the item isn't owner-locked or blocked from the operation.

If the connection already has the required scope consented and the target is correct yet the 403 persists, the cause is outside the activity — escalate (tenant conditional-access policy, sensitivity-label/DLP block, or a SharePoint site permission).
