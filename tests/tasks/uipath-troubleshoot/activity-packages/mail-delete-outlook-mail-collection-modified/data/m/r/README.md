# Delete Outlook Mail Failure - Collection Modified Inside the Loop (Branch 2)

This scenario reproduces a runtime `Delete Outlook Mail Message` failure caused
by deleting **inside a `For Each`** that iterates the live `List<MailMessage>`
returned by `Get Outlook Mail Messages`. Deleting the current item mutates the
collection being enumerated, so the next iteration raises
`System.InvalidOperationException: Collection was modified; enumeration
operation may not execute.`

## What this scenario uncovers

**Root Cause:** In `Main.xaml`, `Get Outlook Mail Messages` reads the Inbox into
the `List<MailMessage>` variable `mailList`. A `For Each` (`ForEach<MailMessage>`)
iterates `mailList`, and `Delete Outlook Mail Message` deletes the current `item`
**directly inside that loop**. The first delete succeeds; on the next iteration
the `For Each` enumerator detects the collection changed and throws
`Collection was modified; enumeration operation may not execute.`

It is a **workflow-structure bug**, not an Outlook / COM / mailbox problem.

This maps to:
`references/activity-packages/mail-activities/playbooks/delete-outlook-mail-failures.md`
(specifically **Branch 2 — Collection modified inside the loop**).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project with `Delete Outlook Mail Message` nested inside a `For Each` over `mailList` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook Branch 2 signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table (quoted + unquoted arg forms) |

The smoking gun is in `or-jobs-logs-e6f7a8b9-output-json.json`: an Info that Get
retrieved 37 messages into `mailList`, an Info that the `For Each` began
iterating, an Info that message 1 of 37 was deleted, then the
`Collection was modified` Error on the next iteration — the delete-inside-loop
mutated the collection mid-enumeration.

> **Note on fixtures.** Fixtures here were authored from the documented playbook
> Branch 2 signature rather than captured from a real `.local/investigations/`
> session.

## Sibling-branch comparison (delete-outlook-mail-failures playbook)

| Branch | Signature | This scenario? | Why not |
|---|---|---|---|
| 1 — Stale message reference | `The operation failed. An object could not be found.` | No | Error is `Collection was modified`; the first delete succeeded |
| **2 — Collection modified in loop** | `Collection was modified; enumeration operation may not execute.` inside a For Each | **Yes** | Delete runs inside For Each over the live `mailList` |
| 3 — New Outlook (COM API removed) | Broke completely after an Office/system update; COM-bind failure | No | Messages fetched and one deleted — COM surface works |
| 4 — COM session blocked / privilege | `The operation has timed out` / freeze | No | Immediate deterministic `InvalidOperationException`, no timeout |
| 5 — Mailbox permission / access denied | Access-denied on a (shared) mailbox | No | Account read the Inbox and deleted the first message |

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched `delete-outlook-mail-failures.md` Branch 2 (collection modified
  inside the loop).
- Agent attributed the fault to deleting inside the `For Each` over the live
  `mailList`, and recommended iterating a `.ToList()` copy / backwards by index,
  or Move-then-delete in a second pass — **NOT** merely wrapping the loop in a
  `Try Catch` (the enumeration is already broken).

This scenario is workflow-fixable from the project source and the Orchestrator
evidence alone; no host access is required. The judge **scores the conclusion,
not the trajectory** — any investigation path that reaches the Branch 2 root
cause and the safe-iteration fix passes.
