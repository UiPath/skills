# Read Text Failure - Activity Outside Its Container

This scenario reproduces a `Read Text` failure where the modern Word-pack
`Read Text` activity is dropped **outside** a `Use Word File` /
`Word Application Scope` and faults as invalid — it has no file input of its
own and reads the container's open document.

## What this scenario uncovers

**Root Cause:** The Word-pack `Read Text` sits loose in the sequence with no
container. It reads the document held open by a surrounding scope; outside
one it is invalid, so the job faults immediately with "The 'Read Text'
activity must be placed inside a 'Use Word File' or 'Word Application
Scope'". The file/format/install are not implicated.

This maps to:
`references/activity-packages/word-activities/playbooks/read-text-missing-container.md`

The correct agent behavior is to tie the fault to the missing container /
wrong Read Text surface and recommend either nesting it in a `Use Word File`
or switching to the standalone `System > File > Word Document` `Read Text`
(which takes a file path) — not blaming the file path, format, or Word
install.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project with a Word-pack `Read Text` loose in the sequence (no container, no file path) |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** The faulted job's error names the `Read Text`
> activity and the missing `Use Word File` / `Word Application Scope`
> container; the `.xaml` shows the activity loose in the `Main Sequence`.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `read-text-missing-container.md`
- Agent identified the Word-pack Read Text being outside a `Use Word File` /
  `Word Application Scope` as the cause and recommended nesting it in a
  container OR switching to the standalone `System > File > Word Document`
  `Read Text` — without blaming the file/format/install or fabricating
  actions
