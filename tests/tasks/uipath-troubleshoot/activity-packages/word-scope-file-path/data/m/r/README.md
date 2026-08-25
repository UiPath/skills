# Word Application Scope Failure - File Path Not Found (Relative Path)

This scenario reproduces a `Word Application Scope` `FileNotFoundException`
caused by a **relative document path** that resolves against the unattended
robot's working directory instead of the project folder.

## What this scenario uncovers

**Root Cause:** The `Word Application Scope`'s `FileName` is the relative
path `Output\OfferLetter.docx`. On the robot, the relative path resolves
against `C:\Windows\System32\config\systemprofile` (the service account
profile / robot working directory), not the project folder, so the file is
not found. "Works from Studio, fails on the robot" confirms a
working-directory resolution gap, not a missing file or a Word defect. The
resolved path in the error message is the tell.

This maps to:
`references/activity-packages/word-activities/playbooks/word-scope-file-path-not-found.md`

The correct agent behavior is to tie the resolved path to relative-path
resolution and recommend an absolute path / `Path.Combine` (or
`Create if not exists` when the document is generated) - NOT to edit the
document content or declare the file genuinely missing.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project whose `Word Application Scope` uses a relative `FileName` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** The faulted job's error resolves the relative path
> to `C:\Windows\System32\config\systemprofile\Output\OfferLetter.docx` -
> the service-profile root an unattended robot uses as its working
> directory - which is the diagnostic signal distinguishing this from a
> genuinely missing file.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `word-scope-file-path-not-found.md`
- Agent identified the relative-path-resolving-against-the-robot-working-
  directory cause and recommended an absolute path / `Path.Combine` (or
  `Create if not exists` when the document is generated) - without editing
  document content or fabricating actions
