# O365 Get Mail — Stale Message ID (ErrorItemNotFound) — Faithful Replay

This scenario replays a real UiPath troubleshooting investigation where the
agent reached a verified resolution. The fixtures are the verbatim
`uip` CLI responses captured from that session (scrubbed).

## What the original session uncovered

The user asked why their last job in folder `Shared` failed. The most recent
job, `ERN_O365_MailMessageNotFound` (key `cbbaaaf6-b416-4025-9a98-c8ee50990f76`),
faulted at the **Get Mail** activity ("Get Mail by corrupted ID (expect
ErrorInvalidIdMalformed; for ErrorItemNotFound use the ID of a deleted
email)" in `O365_MailMessageNotFound.xaml`) inside the Microsoft 365 Scope
with a raw `Microsoft.Graph.ServiceException` — `Code: ErrorItemNotFound`,
`Message: The specified object was not found in the store., The process
failed to get the correct properties.`, `Status Code: NotFound`. The raw
(unwrapped) ServiceException marks the legacy O365 activity, not a
Connections-based one. The activity's `EmailId` was bound to variable
`staleId` — an ID that passes Outlook's integrity check (so not
`ErrorInvalidIdMalformed`) but resolves to no message in the store: the
signature of a stale/deleted message ID. Fix: confirm the message still
exists / fix the ID source, and re-fetch by filter at consumption time
instead of persisting message IDs across runs.

### Span evidence pattern

This scenario's distinguishing evidence lives in the **trace spans**, not
the job Info alone: the recorded spans show a two-`GetMail` sequence inside
the same Microsoft 365 Scope — "Get newest email (source of a real ID)"
**succeeded** against the same Inbox/connection immediately before the
faulting "Get Mail by corrupted ID ..." span whose attributes carry
`Private.EmailId="staleId"`. The preceding success on the same mailbox
eliminates the playbook's sibling branches: mailbox mismatch
(`ErrorInvalidMailboxItemId` absent), authentication, and
missing-scope-as-404 causes. Playbook:
`references/activity-packages/o365-activities/playbooks/mail-message-not-found.md`.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `fixtures/mocks/responses/*.json` | real stdout extracted verbatim from the session's investigation `raw/` outputs |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its recorded fixture |

No `process/` snapshot — the original investigation determined the root cause
from platform evidence alone (job Info/logs carry the full ServiceException
stack; the trace spans carry the `staleId` binding and the
preceding-success evidence).

### Trace spans

Four spans were recorded for this job and both trace retrieval forms
(`or jobs traces <key>` and `traces spans get --job-key <key>`) replay them:
the RobotJob span (full exception stack incl. `Status Code: NotFound` in
Attributes), the Microsoft 365 Scope span, the successful "Get newest email
(source of a real ID)" `GetMail` span, and the faulting "Get Mail by
corrupted ID ..." `GetMail` span (`Private.EmailId="staleId"`).

### Fixture derivations and scrubs

- `or-jobs-logs-...-level-error.json` is the Error-level subset of the
  recorded log set (rows verbatim, filtered to `Level == "Error"`).
- No `--state Faulted` jobs-list raw was recorded, so there is no
  Faulted-only fixture; the folder-key rule substring-matches
  `--state Faulted` variants and returns the full recorded list.
- No `is connections` probe was run in this session, so the manifest has no
  IS rule — unmatched commands fall to the empty `unmocked_default`.
- Mailbox-content scrub: the span attributes were scanned for real email
  subjects/addresses (the first `GetMail` fetched the newest real email) —
  none were present in the recorded attributes (`Private.Results` holds the
  variable name `results`, not message content), so no content scrub was
  needed. Standard scrubs applied: hostname → `MOCK-HOST`, workspace owner
  email → `original_email@test.com`, Windows account →
  `UIPATH\REPLACEMENT_USER`.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent's final response reaches the same root cause and fix as `RESOLUTION.md`

## Re-running the extraction

This scenario was hand-built from the investigation's `raw/` verbatim CLI
outputs. If the source investigation changes, update the fixture JSONs
directly and re-run the scrub checks, or regenerate with:

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path> --transcript <path> --resolution <path> \
    --scenario-name o365-getmail-message-not-found --apply
```
