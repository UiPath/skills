# Final Resolution

---

**Root Cause:** The `Delete Outlook Mail Message` (`DeleteOutlookMailMessage`)
activity in `Main.xaml` runs **directly inside a `For Each`** that iterates the
live `List<MailMessage>` (`mailList`) returned by the preceding
`Get Outlook Mail Messages`. Deleting the current `item` removes it from the
very collection the `For Each` is enumerating, which invalidates the loop's
enumerator. The next iteration throws
`System.InvalidOperationException: Collection was modified; enumeration
operation may not execute.` This maps to
`references/activity-packages/mail-activities/playbooks/delete-outlook-mail-failures.md`
**Branch 2 (Collection modified inside the loop).**

**What went wrong:** The `BulkMailPurger` job (started 2026-06-04T13:30:00Z)
faulted ~4 seconds after launch. `Get Outlook Mail Messages` retrieved 37
messages into `mailList`; the `For Each` began iterating; the **first** message
was deleted successfully; on the **next** iteration the enumerator detected the
collection had changed and raised the `Collection was modified` exception. The
job faults on every run because the structure is wrong every time.

**Why:** A `For Each` holds an enumerator over the collection it loops. Deleting
an item from that same live collection mid-enumeration mutates it underneath the
enumerator. .NET detects the version change and throws on the next `MoveNext()`.
The fault is a **workflow-structure bug**, not an Outlook / COM / mailbox
problem.

This is **NOT**:

- **Branch 1 (stale message reference / "An object could not be found").** The
  exception is `Collection was modified`, not `object could not be found`, and
  the first delete succeeded — the item existed.
- **Branch 3 (New Outlook removed the desktop COM API).** There is no
  post-update COM-bind failure; messages were fetched and one was deleted, so
  the COM surface works.
- **Branch 4 (COM session blocked / modal dialog / timeout / privilege).** There
  is no timeout or hang; the failure is an immediate, deterministic
  `InvalidOperationException` on the second iteration.
- **Branch 5 (mailbox permission / access denied).** The account could read the
  Inbox and delete the first message, so it has delete rights.
- **Fixable by a bare `Try Catch`.** Catching the `Collection was modified`
  exception does not fix anything — the enumeration is already broken and every
  remaining message is skipped. The loop must be restructured.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: BulkMailPurger -- Faulted at 2026-06-04T13:30:04.470Z (ran ~4.3 seconds)
- Job type: Unattended, triggered by a scheduled trigger on machine MOCK-HOST
- Folder: RPA Production (key `d5e6f7a8-9012-4c3d-8e4f-5a6b7c8d9e0f`)
- Final error: `Collection was modified; enumeration operation may not execute.`
  -> `Main.xaml` -> `DeleteOutlookMailMessage "Delete Outlook Mail Message"`
  -> `ForEach<MailMessage> "For Each"` -> `Sequence "Main Sequence"`
  -> `Main "Main"`
- `System.InvalidOperationException` is the .NET signature for mutating a
  collection while enumerating it.

### Mail Activities (Root Cause)
- `Main.xaml` structure: `Get Outlook Mail Messages` reads `Inbox` into the
  `List<MailMessage>` variable `mailList`; a `For Each` (`ForEach<MailMessage>`)
  iterates `mailList`; **inside the loop body**, `Delete Outlook Mail Message`
  deletes the current `item` — mutating `mailList` mid-enumeration.
- Job logs show the smoking gun sequence:
  1. `[Get Outlook Mail Messages] Retrieved 37 messages from folder Inbox into mailList`
  2. `[For Each] Begin iterating mailList (37 items)`
  3. `[Delete Outlook Mail Message] Deleted message 1 of 37 (...)`
  4. `[Delete Outlook Mail Message] Collection was modified; enumeration operation may not execute.`
  The first delete succeeds, the next iteration faults — the delete mutated the
  collection being enumerated.

---

**Immediate fix:**

Do **not** delete inside a `For Each` over the live `mailList`. Use one of:

1. **Iterate a copy.** Loop over `mailList.ToList()` so deletes do not disturb
   the original collection's enumerator. (`For Each` over `mailList.ToList()`.)
2. **Loop backwards by index.** Use a `For` (or index loop) from
   `mailList.Count - 1` down to `0`, deleting `mailList[i]`, so removing an item
   never shifts the positions still to visit.
3. **Move-then-delete in a second pass.** Inside the `For Each`, use
   `Move Outlook Mail Message` to move each targeted item to `Deleted Items`
   (or a temp subfolder); after the loop, delete that set in a second pass.

Any of these stops mutating the collection that the loop is enumerating.

---

**Preventive fix:**

1. **Studio** -- never mutate the live `MailMessage` collection inside its own
   `For Each`. Iterate a `.ToList()` copy or backwards by index, or Move-then-
   delete in a second pass.
   - **Why:** A `For Each` enumerator throws on any mid-loop mutation of its
     source collection.
   - **Who:** RPA developer
2. **Code review** -- flag any "Get a list -> For Each over that list -> mutate
   the list inside the loop" shape in review; it is the canonical
   collection-modified bug.
   - **Who:** Reviewer / tech lead

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Delete Outlook Mail Message runs inside a For Each over the live List<MailMessage> from Get, mutating the collection mid-enumeration (Branch 2) | High | Confirmed | Yes | `Collection was modified; enumeration operation may not execute.` from `DeleteOutlookMailMessage` -> `ForEach<MailMessage>` in `Main.xaml`; job logs show first delete succeeded, next iteration faulted | Iterate `mailList.ToList()` / backwards by index, or Move-then-delete in a second pass |
| H2 | Stale message reference / object not found (Branch 1) | Low | Eliminated | No | Error is `Collection was modified`, not `object could not be found`; first delete succeeded | n/a |
| H3 | Outlook / COM session problem (Branch 3/4) | Low | Eliminated | No | No COM-bind failure, no timeout/hang; messages fetched and one deleted | n/a |

---

Would you like me to draft the corrected `Main.xaml` (iterate `.ToList()` or
loop backwards by index), or clean up the `.local/investigations/` folder?
