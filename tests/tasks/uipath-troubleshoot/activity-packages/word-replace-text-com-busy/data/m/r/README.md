# Replace Text Failure - "Application is busy" / COM Interop Retry

This scenario reproduces an intermittent `Replace Text` COM failure where
WINWORD.EXE is busy (a Word instance was already running on the host) and
the activity's COM call is rejected with `RPC_E_SERVERCALL_RETRYLATER`
(0x8001010A).

## What this scenario uncovers

**Root Cause:** Word was busy when the activity issued its COM call — the
job log shows a Word instance already running on the host (orphaned or
concurrent WINWORD.EXE). COM rejects the call; the intermittency
("re-running sometimes works") is the tell of a transient busy state, not a
code defect.

This maps to:
`references/activity-packages/word-activities/playbooks/replace-text-com-busy.md`

The correct agent behavior is to tie the `0x8001010A` HRESULT to a
busy/locked Word session and recommend clearing it (Kill Process WINWORD
before the scope, ensure not open elsewhere) and/or a Retry Scope — not to
attempt host commands itself (the user is off-host), and not to confuse it
with the scope-startup "Word not installed" COM error.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project; `Replace Text` inside a `Word Application Scope` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** The full job log includes a "Word already running on
> the host" warning immediately before the `RPC_E_SERVERCALL_RETRYLATER`
> error — the signal that distinguishes a busy/locked instance from the
> scope-startup `REGDB_E_CLASSNOTREG` "Word not installed" fault.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `replace-text-com-busy.md`
- Agent identified a busy/locked Word session (orphaned or concurrent
  WINWORD.EXE) as the cause and recommended clearing it (Kill Process
  WINWORD before the scope, not-open-elsewhere) and/or a Retry Scope —
  without fabricating host actions
