# Word Application Scope Failure - "Cannot create unknown type" (Missing Package)

This scenario reproduces a `Word Application Scope` **load-time** failure on
an unattended robot whose `UiPath.Word.Activities` package version does not
match the published dependency. The process faults in under a second with
`Cannot create unknown type ... WordApplicationScope`, before any activity
executes.

## What this scenario uncovers

**Root Cause:** `Main.xaml` references `WordApplicationScope` from
`UiPath.Word.Activities` (pinned `[1.17.2]` in `project.json`). The robot
did not restore that package version, so the type cannot be created and the
workflow fails to load. "Works in Studio, fails only on the remote robot"
is the signature of a package restore / version-availability gap - not a
workflow-logic defect.

This maps to:
`references/activity-packages/word-activities/playbooks/word-scope-cannot-create-unknown-type.md`

The correct agent behavior is to tie the `XamlObjectWriterException` to a
missing/mismatched `UiPath.Word.Activities` package on the robot and hand
the user the feed/publish steps - NOT to edit the workflow or the activity.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project referencing `Word Application Scope`, pinning `UiPath.Word.Activities [1.17.2]` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session. The load-time fault (~0.8s, no
> `Starting Microsoft Word` log line) distinguishes it from the COM
> `REGDB_E_CLASSNOTREG` startup fault in `word-scope-not-installed`.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `word-scope-cannot-create-unknown-type.md`
- Agent identified a missing/mismatched `UiPath.Word.Activities` package on
  the robot as the cause and recommended making the pinned version available
  on the feed / pinning it / republishing - without editing the workflow or
  fabricating actions
