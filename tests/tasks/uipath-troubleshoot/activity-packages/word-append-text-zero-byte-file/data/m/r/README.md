# Append Text Failure - "Archive file cannot be size zero"

This scenario reproduces an `Append Text` failure where the target `.docx`
is a **0-byte file** (not a valid OpenXML package), so opening it faults with
`System.IO.InvalidDataException: Archive file cannot be size zero`.

## What this scenario uncovers

**Root Cause:** A `.docx` is an OpenXML ZIP archive; a 0-byte file (a renamed
`.txt`, or a failed/truncated write) has no archive structure, so the Word
scope rejects it on open — before `Append Text` runs. The extension alone
doesn't make a valid Word document.

This maps to:
`references/activity-packages/word-activities/playbooks/append-text-zero-byte-file.md`

The correct agent behavior is to tie the error to the 0-byte / invalid input
file and recommend deleting it + `Create if not exists` (or fixing the
upstream that produced it) — not blaming a missing Word install, a lock, the
activity placement, or the workflow logic.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project; `Word Application Scope` opening `data\Notes.docx` + `Append Text` inside |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** The faulted job's `InvalidDataException: Archive file
> cannot be size zero` fires at the scope's document open (before Append
> Text), and the activity placement is valid — isolating the cause to the
> 0-byte input file. Distinct from the corrupt-but-non-empty case
> (`word-scope-file-corrupted`).

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `append-text-zero-byte-file.md`
- Agent identified the 0-byte / invalid `.docx` as the cause and recommended
  deleting it + `Create if not exists` (and/or fixing the upstream write) —
  without blaming install/lock/placement/logic or fabricating actions
