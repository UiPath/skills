# Word Application Scope Failure - "The file appears to be corrupted"

This scenario reproduces a `Word Application Scope` failure where the
document opens reporting `The file appears to be corrupted`. The workflow
edits a template **in place** and an orphaned WINWORD.EXE from a prior run
holds the file lock, leaving the template half-written.

## What this scenario uncovers

**Root Cause:** The workflow opens `MonthlyTemplate.docx` and edits it in
place (no save-as-new). A Word instance was already running on the host
when the scope started (orphaned WINWORD.EXE), so the file is locked /
half-written and Word reports it as corrupted. "Worked the first few runs,
opens fine on my own machine" points at a host-state / locking problem -
not a workflow-logic defect or a genuinely corrupt template.

This maps to:
`references/activity-packages/word-activities/playbooks/word-scope-file-corrupted.md`

The correct agent behavior is to tie the corruption error to an
orphaned/locked Word session plus the in-place template overwrite, and
recommend clearing the lock (Kill Process WINWORD before the scope) and
saving to a new file - not to declare the template irrecoverably corrupt or
attempt host commands itself (the user is off-host).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project whose `Word Application Scope` edits a template in place |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session. The full job log includes a
> "Word already running on the host" warning that points at the orphaned
> WINWORD.EXE lock.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `word-scope-file-corrupted.md`
- Agent identified an orphaned/locked Word session and/or in-place template
  overwrite as the cause and recommended clearing the lock (Kill Process
  WINWORD before the scope) and/or saving to a new file - without
  fabricating host actions
