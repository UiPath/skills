---
confidence: medium
---

# O365 Mail — NullReferenceException from legacy Mail activity

## Context

What this looks like — a legacy (non-Connections) Mail activity faults with a raw:

- `System.NullReferenceException: Object reference not set to an instance of an object.`

Routing rule: the **raw exception type itself is the signal**. Connections activities remap an internal NullReferenceException to the friendly text `The object used in the activity does not exist.` — so a raw `NullReferenceException` from this package always means a legacy activity (`UiPath.MicrosoftOffice365.Activities.Mail.SendMail`, `ForwardMail`, `ReplyToMail`, ...) dereferenced a null input before/while building the Graph request.

What activities can produce this error:
- Legacy **Send Mail** (`SendMail`) — a `null` element inside the `To` / `Cc` / `Bcc` string arrays (e.g., an array built with an unassigned variable), or a null required input dereferenced during message construction.
- Legacy **Forward Mail** (`ForwardMail`) / **Reply To Mail** (`ReplyToMail`) — the `Message` input is `null`; the activity dereferences it to read the original message ID.

What can cause it:
- **`Message` not set / upstream returned nothing** — Forward/Reply bound to the output of a Get Mail-style activity that matched no message, so the variable is null.
- **Null element in a recipient array** — `{var1, var2}` where one variable was never assigned; the array itself is non-null so validation passes, but the null element is dereferenced later.
- **Any other null required input** consumed during request construction — body/subject composition from null variables.

What to look for:
- The stack trace — confirms the frames are in `UiPath.MicrosoftOffice365.Activities.Mail.*` (legacy namespace).
- The faulted activity's input bindings in the workflow source, and where each bound variable is assigned.

> **Different cause, do not apply this playbook:**
> - `The object used in the activity does not exist.` — same root condition but on the Connections path; investigate that activity's inputs the same way, but the activity is not legacy.
> - A `NullReferenceException` whose stack trace is in the **user's workflow code** (Assign, Invoke Code), not the package — that is a workflow-logic null; use the general runtime-exception playbook (`references/runtime-exceptions/playbooks/null-reference-exception.md`).

## Investigation

1. Get the stack trace and confirm the top frames are in the legacy Mail activity namespace, not user code.
2. Identify the faulted activity by `DisplayName` in the workflow source and list its input bindings (`Message`, `To`, `Cc`, `Bcc`, body/subject expressions).
3. For Forward/Reply: trace the `Message` variable to its producer and check whether the producer can return null/empty (no match, conditional branch).
4. For Send: inspect array literals for elements that can be null at runtime; check each element variable's assignment.

## Resolution

- **If `Message` is null:** ensure the producing activity actually found a message before forwarding/replying — add an If/null-check (or fix the producer's filter) and handle the no-message case explicitly.
- **If a recipient array element is null:** assign the variable before the send, or build the array dynamically excluding null/empty entries.
- **General:** the root cause is WHY the input was null — fix the upstream assignment, then optionally migrate to the Connections equivalent, which validates inputs and reports actionable messages instead of raw NREs.
