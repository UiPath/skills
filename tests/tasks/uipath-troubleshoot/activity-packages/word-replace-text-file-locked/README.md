# Replace Text Failure - File Lock / "Being Used By Another Process"

This scenario reproduces a `Replace Text` file-lock failure: a `Use Word
File` scope with **Auto Save** enabled edits the same shared file on every
iteration of a `For Each` loop, so a save races the next iteration's access
and faults with `System.IO.IOException: ... because it is being used by
another process`.

## What this scenario uncovers

**Root Cause:** `Use Word File` with `AutoSave="True"` targets one shared
file (`MasterContract.docx`) inside a loop. Auto Save persists the document
while the next iteration is already opening it, so the save races another
access and locks. The "first item works, then it dies" pattern plus the
per-iteration Auto-Save/re-open logs are the tell — not a corrupt file, a
missing install, or a path problem.

This maps to:
`references/activity-packages/word-activities/playbooks/replace-text-file-locked.md`

The correct agent behavior is to tie the `IOException` to the Auto-Save +
loop-on-a-shared-file contention and recommend unchecking Auto Save, writing
a distinct output path per iteration, or clearing a concurrent accessor —
not blaming corruption, Word install, or the path.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project; `Use Word File` (`AutoSave="True"`) + `Replace Text in Document` inside a `For Each` over one shared file |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** The full job log shows per-iteration trace lines
> (`Iteration 1: Auto Save writing ...` -> `Iteration 2: opened ...` ->
> IOException), exposing the save-vs-access race on the single shared file.
> Distinct from `word-scope-file-corrupted` (corrupted-on-open from a
> half-written template).

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `replace-text-file-locked.md`
- Agent identified the Auto-Save + loop-on-a-shared-file lock as the cause
  and recommended unchecking Auto Save, writing a distinct path per
  iteration, or clearing the concurrent accessor — without blaming
  corruption / install / path or fabricating host actions
