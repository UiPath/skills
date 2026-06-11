# O365 Get Mail — Mail Folder Not Found (unwrapped ArgumentNullException) — Faithful Replay

This scenario replays a real UiPath troubleshooting investigation where the
agent reached a verified resolution. The fixtures are the verbatim
`uip` CLI responses captured from that session (scrubbed).

## What the original session uncovered

The user asked why their last job in folder `Shared` failed. The most recent
job, `ERN_O365_MailFolderNotFound` (key `e893a4d4-e061-4cba-a799-6ed4de6ee4e2`),
faulted at the legacy **Get Mail** activity ("Get Mail from nonexistent
folder" in `O365_MailFolderNotFound.xaml`) inside the Microsoft 365 Scope
with the unwrapped `System.ArgumentNullException: Value cannot be null.
(Parameter 'Folder named 'NoSuchFolder-Repro-123' could not be found on
this account.')` — the unwrapped form of the mail-folder-not-found
signature; the inner sentence is the match. Faulting frame:
`GraphServiceClientExtensions.GetMailFolder(...)` during folder resolution,
before any message retrieval. The activity's `MailFolder` argument was the
literal name `NoSuchFolder-Repro-123`; folder enumeration of the mailbox
resolved by the scope (interactive-token auth, no shared-mailbox/account
override — the authenticated user's own mailbox) found no match. Fix:
verify/correct the folder name or the `MailFolder` argument (path form for
nested folders), confirm the resolved mailbox, then restart the job.

### Span evidence pattern

This scenario's cause disambiguation lives in the **trace spans**: the
"Get Mail from nonexistent folder" `GetMail` span carries
`Private.MailFolder="NoSuchFolder-Repro-123"` (matching the error verbatim)
and `Public.AuthScopesInvalid="False"` (eliminating the insufficient-scope
branch), and the Microsoft 365 Scope span shows
`AuthenticationType=InteractiveToken` with no Account/shared-mailbox
override (`Private.Account` holds the designer placeholder "Please select
an account.") — eliminating the wrong-mailbox argument variant. Lookup was
by name with no path separators or stray whitespace — eliminating the
stale-folder-ID and path-segment branches. Playbook:
`references/activity-packages/o365-activities/playbooks/mail-folder-not-found.md`.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `fixtures/mocks/responses/*.json` | real stdout extracted verbatim from the session's investigation `raw/` outputs |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its recorded fixture |

No `process/` snapshot — the original investigation determined the root cause
from platform evidence alone (job Info/logs carry the full
ArgumentNullException stack; the trace spans carry the `MailFolder` literal
and the scope/auth attributes).

### Trace spans

Three spans were recorded for this job and all trace retrieval forms
(`or jobs traces <key>`, `traces spans get --job-key <key>`, and the
session's recorded `traces spans get <trace-id>` form) replay them: the
RobotJob span (full exception stack with the `GetMailFolder` faulting frame
in Attributes), the Microsoft 365 Scope span, and the faulting "Get Mail
from nonexistent folder" `GetMail` span. In the original session the
`--job-key` form returned "Error retrieving trace ID for job" and the agent
re-fetched by TraceId; the replay serves the genuine spans for every form
so the investigation does not depend on reproducing that transient lookup
failure.

### Fixture derivations and scrubs

- `or-jobs-logs-...-level-error.json` is the recorded Error-level log query
  (the only logs raw captured); the generic logs rule maps to the same
  fixture — the exception row is the only diagnostic content.
- No `--state Faulted` jobs-list raw was recorded, so there is no
  Faulted-only fixture; the folder-key rule substring-matches
  `--state Faulted` variants and returns the full recorded list.
- No `jobs history` raw was captured; the history fixture is the
  Pending → Running → Faulted transition set derived from the recorded job
  row's CreationTime/StartTime/EndTime and Id. It confirms a clean single
  execution and carries no diagnostic signal beyond `jobs get`.
- Mailbox-content scrub: the span attributes were scanned for real email
  subjects/addresses — none were present (the activity faulted at folder
  resolution before any message retrieval; `Private.Account` holds the
  designer placeholder "Please select an account."), so no content scrub
  was needed. Standard scrubs applied: hostname → `MOCK-HOST`, workspace
  owner email → `original_email@test.com`, Windows account →
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
    --scenario-name o365-getmail-folder-not-found --apply
```
