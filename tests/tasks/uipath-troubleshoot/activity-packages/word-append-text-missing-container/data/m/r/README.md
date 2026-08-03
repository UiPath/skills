# Append Text Failure - Activity Outside Its Container

This scenario reproduces an `Append Text` failure where the App-Integration
`Append Text` activity is dropped **outside** a `Word Application Scope` and
faults with `Activity is valid only inside WordApplicationScope` — it has no
file input of its own.

## What this scenario uncovers

**Root Cause:** The App-Integration `Append Text` (`WordAppendText`) sits
loose in the sequence with no container. It appends to the document held open
by a surrounding scope; outside one it is invalid, so the job faults
immediately. The file/document/install are not implicated.

This maps to:
`references/activity-packages/word-activities/playbooks/append-text-missing-container.md`

The correct agent behavior is to tie the fault to the missing container /
wrong Append Text surface and recommend either nesting it in a
`Word Application Scope` / `Use Word File` or switching to the standalone
`Word Document` `Append Text` (which takes a file path) — not blaming the
file path, document, or install.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project with a `Word Application Scope`-less `Append Text` loose in the sequence |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** The faulted job's error names the `Append Text`
> activity and the `WordApplicationScope` requirement; the `.xaml` shows the
> activity loose in the `Main Sequence`. Twin of `read-text-missing-container`
> for a different activity.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `append-text-missing-container.md`
- Agent identified the App-Integration Append Text being outside a
  `Word Application Scope` as the cause and recommended nesting it in a scope
  OR switching to the standalone `Word Document` `Append Text` — without
  blaming the file/document/install or fabricating actions
