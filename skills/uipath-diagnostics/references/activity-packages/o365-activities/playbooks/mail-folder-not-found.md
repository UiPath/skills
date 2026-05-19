---
confidence: high
---

# O365 — Mail folder not found

## Context

What this looks like — any of the following message patterns, all originating from the same root cause (the configured mail folder cannot be resolved against the user's mailbox):

- `The resource could not be found.` 
- `Folder named '<name>' could not be found on this account.` 
- `Cannot find item configured with connection <connection> at path <folderName>.` — wrapper around the above. The original `Folder named ...` text is preserved as the inner exception's message.
- `Value cannot be null. (Parameter 'Folder named '<name>' could not be found on this account.')` — same as above when the `ArgumentNullException` is surfaced unwrapped. Match on the inner sentence.

The job faults synchronously the moment the activity tries to resolve the destination folder.

What activities can produce this error:
- **Move Email** (`MoveEmailConnections`) — `MailFolder` argument when the destination folder doesn't exist and `CreateFolderIfMissing = false`. Legacy: `MoveMail` (`DestinationFolderName`).
- **Get Newest Email** (`GetNewestEmail`) — `MailFolder` argument when the source folder doesn't exist.
- **Get Email List** (`GetEmailListConnections`) — `MailFolder` argument when the source folder doesn't exist.
- **For Each Email** (`ForEachEmailConnections`) — `MailFolder` argument when the source folder doesn't exist.
- **Wait For Email Received** (`WaitForEmailReceived`) — `MailFolder` argument when the source folder doesn't exist.
- **New Email Received trigger** (`NewEmailReceived`) — `MailFolder` argument on the trigger or its debug/healing sample lookup.
- Any other Mail activity that reads a folder.

What can cause it:
- **Folder does not exist in the mailbox.** The configured folder name/path doesn't match any folder under the resolved account, or the folder ID points to a folder that has been deleted, moved out of scope, or never existed in this mailbox. The activity enumerates folders for the resolved `Account` and the target name does not appear (case-insensitive) — or Graph returns 404 for the ID.
- **Wrong mailbox in scope.** The folder exists, but in a different mailbox than the one the activity resolves to (`Account` / `Shared Mailbox`). Common when the connection was re-authenticated against a different account, or when a shared mailbox was passed but the folder lives only in the user's own mailbox (or vice versa).
- **Stale folder ID.** A folder ID captured from a previous run no longer resolves. Outlook folder IDs are mailbox-scoped — moving the folder between mailboxes invalidates the ID.
- **Path-segment mismatch.** Folder paths split on `/` and `\`. A folder name that itself contains one of those characters can fail to match. Leading/trailing whitespace or invisible characters in the configured name will also miss the case-insensitive comparison.
- **Insufficient scope to enumerate.** The connection lacks `Mail.Read` / `Mail.ReadWrite` / `Mail.ReadWrite.Shared` for the target mailbox, so the folder-list enumeration is empty or filtered. Graph may return 404 instead of 403 for cross-mailbox shared/delegated access.

> **Different cause, do not apply this playbook:**
> - `MarkAsReadUnreadConnections`, `DeleteEmailConnections`, `ArchiveEmailConnections`, `DownloadEmailConnections`, and similar message-by-ID activities surface `The resource could not be found.` for a missing **message** (not folder). The fix path is different — verify the message ID and mailbox, not the folder configuration.

## Resolution

The error is unambiguous; no further investigation is needed. Stop the investigation and ask the user to verify the target folder:

1. **Confirm the folder still exists** in the target mailbox — check Outlook / Outlook on the Web for the exact `DisplayName` and parent path. The lookup is case-insensitive but otherwise exact: trailing whitespace, mismatched separators, or a renamed folder all cause this error.
2. **Confirm the configured `MailFolder` argument matches** what's in the mailbox. For path-based input, paths split on `/` and `\`, so the activity expects e.g. `Inbox/Subfolder`, not the literal folder name when the folder is nested. For ID-based input, the ID must come from the same mailbox the activity is now running against.
3. **Confirm the resolved mailbox** (`Account` / shared-mailbox argument) is the one that owns the folder. If the connection has been re-authenticated against a different user, or if the activity is targeting a shared mailbox the connection cannot enumerate, the folder will not appear in the lookup.
4. **For `MoveEmailConnections`**, ask the user whether the folder is expected to exist beforehand. If the folder should be created on the fly, set `CreateFolderIfMissing = true` to create any missing path segments instead of throwing.
5. **Confirm the connection's scopes.** The connection must have `Mail.Read` (or `Mail.ReadWrite` for write operations), and `Mail.ReadWrite.Shared` for delegated/shared mailbox access. Missing scopes can surface as a 404 on enumeration even though the folder physically exists.

If the user confirms the folder exists with the exact configured name in the resolved mailbox, the connection has the required scopes, and the identifier is correct, the cause is outside the activity — escalate (mailbox-level permissions, retention policy that hid the folder, or a Graph-side delay after a recent rename) rather than continue under this playbook.
