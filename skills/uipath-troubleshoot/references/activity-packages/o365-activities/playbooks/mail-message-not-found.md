---
confidence: high
---

# O365 Mail — Message not found

## Context

What this looks like — a message-by-ID Mail operation cannot resolve the email it was given:

- `The resource could not be found.` — the friendly mapping for Graph `ItemNotFound` (HTTP 404), raised by a **Mail** activity that addresses a specific message ID.
- `The specified object was not found in the store.` — raw Graph `ErrorItemNotFound` wording; on legacy (non-Connections) activities it surfaces inside a raw `Microsoft.Graph.ServiceException` with `Code: ErrorItemNotFound`.
- `Item ... doesn't belong to the targeted mailbox ...` — Graph `ErrorInvalidMailboxItemId`: the ID is valid but belongs to a different mailbox than the one the activity resolved.

The job faults the moment the activity dereferences the message ID.

What activities can produce this error:
- Modern: **Get Email By Id** (`GetEmailByIdConnections`), **Forward Email** (`ForwardEmailConnections`), **Reply To Email** (`ReplyToEmailConnections`), **Mark As Read/Unread** (`MarkAsReadUnreadConnections`), **Delete Email** (`DeleteEmailConnections`), **Archive Email** (`ArchiveEmailConnections`), **Move Email** (`MoveEmailConnections`, the message side), **Download Email/Attachments** (`DownloadEmailConnections`, `DownloadEmailAttachments`).
- Legacy: `ForwardMail`, `ReplyToMail`, `DeleteMail`, `SetMailCategories`, `GetMail` with `EmailId` set.
- **New Email Received** trigger (`NewEmailReceived`) — the by-ID fetch of the triggering email after the event fires (e.g., the message was deleted/moved between event delivery and the job picking it up).

What can cause it:
- **Message deleted or moved** between when the ID was captured and when the activity ran — including another process or an Outlook rule moving/purging it, or a trigger backlog processing stale events.
- **Mailbox mismatch.** Outlook message IDs are mailbox-scoped: an ID captured from the user's own mailbox does not resolve against a shared mailbox, and vice versa. `ErrorInvalidMailboxItemId` is the explicit form; Graph may also return plain 404.
- **Stale persisted ID.** An ID stored from a previous run (asset, queue item, file) no longer resolves — IDs can change when a message is moved between folders by some Exchange operations.
- **Insufficient scope for the target mailbox.** Missing `Mail.ReadWrite.Shared` for shared-mailbox access can surface as 404 instead of 403.

What to look for:
- Where the message ID came from (which upstream activity/trigger, which mailbox, how long ago).
- The mailbox the failing activity resolves to (`Account` / shared mailbox argument) vs. the mailbox the ID was captured from.

> **Different cause, do not apply this playbook:**
> - `The resource could not be found.` raised while resolving a mail **folder** (activities that take a `MailFolder` argument and no message ID) — use [mail-folder-not-found.md](./mail-folder-not-found.md).
> - The same message on OneDrive/SharePoint activities — use [drive-item-not-found.md](./drive-item-not-found.md).

## Resolution

The error is unambiguous; no further investigation is needed. Stop the investigation and verify the message reference with the user:

1. **Confirm the message still exists** — check the mailbox (including Deleted Items) for the message at the time of failure. A message deleted, archived, or moved by a rule between capture and use is the most common cause.
2. **Confirm both operations target the same mailbox.** The activity that produced the ID and the activity that consumed it must resolve the same `Account` / shared mailbox. For `ErrorInvalidMailboxItemId` this is the confirmed cause — fix the mailbox argument, not the ID.
3. **Do not persist message IDs across runs.** If the workflow stores IDs (assets, queues, files) and consumes them later, re-fetch the message by filter at consumption time instead.
4. **For trigger runs:** if the triggering email is routinely gone by the time the job runs (rules, competing consumers), make the workflow tolerate the miss (Try/Catch with a business-exception path) or remove the competing automation.
5. **For shared mailboxes:** confirm the connection/scope includes shared-mailbox access (`Mail.ReadWrite.Shared`) — a missing shared scope can surface as 404.
