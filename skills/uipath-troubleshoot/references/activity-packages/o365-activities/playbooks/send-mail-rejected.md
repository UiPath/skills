---
confidence: medium
---

# O365 Mail — Send / forward / reply rejected

## Context

What this looks like — a Mail write operation (send, forward, reply) faults on the message itself rather than on authentication or folders. The message is one of:

- `File does not exist: <path>` — a configured attachment path was not found on the runtime machine. Package-fixed text; surfaces as a raw `System.IO.FileNotFoundException` from legacy `SendMail`/`ForwardMail`, wrapped in `Office365Exception` on Connections activities.
- A raw Microsoft Graph rejection surfaced verbatim — these are **Graph's own wording, not fixed package strings; match on the error-code family and the theme, not exact text**:
  - `ErrorInvalidRecipients` / invalid-recipient wording — a recipient address is malformed or rejected.
  - `ErrorSendAsDenied` / send-as wording — the authenticated user may not send as the configured `From` / shared mailbox.
  - `ErrorMessageSizeExceeded` / size wording — the message (body + attachments) exceeds the Exchange size limit.

On legacy activities these arrive as raw `Microsoft.Graph.ServiceException` (message embeds `Code: <errorCode>`); on Connections activities as `Office365Exception` with the Graph message preserved.

What activities can produce this error:
- **Send Email** (`SendMailConnections`), legacy **Send Mail** (`SendMail`).
- **Forward Email** (`ForwardEmailConnections`), legacy **Forward Mail** (`ForwardMail`).
- **Reply To Email** (`ReplyToEmailConnections`), legacy **Reply To Mail** (`ReplyToMail`).

What can cause it:
- **Malformed or rejected recipient** — typo in an address, a stray separator producing an empty entry, or a recipient the tenant rejects.
- **Shared-mailbox send without Exchange rights.** Sending with a shared mailbox / `From` address requires the Exchange **Send As** (or **Send on Behalf**) permission for the authenticated user — the Graph scope `Mail.Send.Shared` alone is not enough.
- **Attachment file missing on the runtime machine** — the path is valid at design time but absent where the job runs (user-profile paths, unmapped shares).
- **Message too large** — attachments push the message over the Graph/Exchange limit.

What to look for:
- The recipient lists (`To`/`Cc`/`Bcc`), `From`/shared-mailbox argument, and attachment paths from the workflow source.
- Whether the same send works without attachments, without the shared `From`, or with a single known-good recipient — isolates which input is rejected.

> **Different cause, do not apply this playbook:**
> - `The caller doesn't have permission to perform the action.` (403) — Graph-scope permission, use [insufficient-graph-scope.md](./insufficient-graph-scope.md).
> - Token / `AADSTS` / not-authenticated messages — use [authentication-token-invalid.md](./authentication-token-invalid.md).
> - `(HTTP Status Code: <status>) Batching request failed with an unknown reason.` — a batched sub-request failed without a parseable body; route by the embedded status per [transient-service-error.md](./transient-service-error.md) / [request-throttled.md](./request-throttled.md).

## Investigation

1. Classify the message: attachment path (`File does not exist`), recipient (`ErrorInvalidRecipients`), send-as (`ErrorSendAsDenied`), or size (`ErrorMessageSizeExceeded`).
2. For recipient errors: read the exact `To`/`Cc`/`Bcc` values from the workflow source (or the composing variables) and look for malformed entries — empty strings from a trailing separator, missing `@domain`, display names without addresses.
3. For send-as errors: capture the authenticated principal (connection UPN / scope account) and the configured `From`/shared mailbox; check in Exchange admin whether the principal holds Send As on that mailbox.
4. For attachment errors: check the path exists **on the machine the job runs on**, under the robot's user profile.
5. For size errors: total the attachment sizes; compare against the tenant's message size limit.

## Resolution

- **If malformed recipient:** fix the address list — remove empty entries, correct the address; when lists are built dynamically, validate each entry before the send.
- **If send-as denied:** grant the authenticated user **Send As** (or **Send on Behalf**) on the shared mailbox in Exchange admin, and keep the shared-mailbox argument consistent with that grant. Re-run after Exchange permission propagation.
- **If attachment missing:** correct the path or stage the file on the runtime machine; avoid user-profile-relative paths for unattended runs.
- **If message size exceeded:** reduce attachment payload (compress, split across emails) or share a OneDrive link instead of attaching.
