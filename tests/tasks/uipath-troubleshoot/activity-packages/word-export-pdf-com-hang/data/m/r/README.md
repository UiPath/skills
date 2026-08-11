# Export to PDF Failure - COM Interop Hang / Crash (Orphaned WINWORD)

This scenario reproduces an intermittent `Export to PDF` COM failure where an
orphaned `WINWORD.EXE` (a Word instance already running on the host) blocks
the export's COM call, which faults with `COMException` (`RPC_E_CALL_REJECTED`
/ `0x80010001`).

## What this scenario uncovers

**Root Cause:** A stale/orphaned `WINWORD.EXE` blocks the export call; the
job log warns "A Microsoft Word instance was already running on the host".
The intermittency ("re-running sometimes works") is the tell of a transient
busy/locked Word state — not a code defect, not the output path (which is
valid here).

This maps to:
`references/activity-packages/word-activities/playbooks/export-pdf-com-hang.md`

The correct agent behavior is to tie the `COMException` to a busy/orphaned
WINWORD and recommend clearing it (Kill Process WINWORD before the scope +
dispose, ensure input free), optionally the Invoke Code C# `ExportAsFixedFormat`
fallback — framed as host/workflow steps for the off-host user, not blaming
the output path or document.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project; `Word Application Scope` + `Export to PDF` to a valid `.pdf` path |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** The full job log includes a "Word already running on
> the host" warning immediately before the `RPC_E_CALL_REJECTED` COM error,
> and the output path/folder is valid — isolating the cause to the busy/
> orphaned WINWORD rather than the missing-dir or path-format scenarios.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `export-pdf-com-hang.md`
- Agent identified a busy/orphaned WINWORD blocking the export's COM call as
  the cause and recommended clearing it (Kill Process WINWORD before the
  scope / dispose / ensure input free, optionally the Invoke Code fallback) —
  without fabricating host actions or blaming the output path/document
