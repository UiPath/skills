# Word Application Scope Failure - Word Not Installed on the Robot Host

This scenario reproduces a classic `Word Application Scope` failure caused
by **desktop Microsoft Word not being usable** on the execution machine.
The classic activity drives the Word Interop API, so the scope cannot
create the `Word.Application` COM object and faults at startup with
`REGDB_E_CLASSNOTREG` (0x80040154).

## What this scenario uncovers

**Root Cause:** The classic `Word Application Scope`
(`UiPath.Word.Activities.WordApplicationScope`) needs a registered desktop
Word install at a bitness compatible with the robot. The new unattended
robot host cannot create the `Word.Application` COM class, so the scope
faults before the document is opened. The "worked on dev, broke after the
move to the new robot" detail points at a host-environment cause, not a
workflow defect.

This maps to:
`references/activity-packages/word-activities/playbooks/word-scope-com-not-installed.md`

The user is framed as **off-host**, so the correct agent behavior is to
tie the HRESULT to an unusable Word install and recommend installing Word
(or fixing bitness / repairing the Office COM registration) - not to
attempt host commands.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project with a classic `Word Application Scope` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `word-scope-com-not-installed.md`
- Agent identified "desktop Word not usable on the robot host" as the cause
  and recommended installing Word, fixing the Office/robot bitness mismatch,
  or repairing the Office COM registration (any valid fix path scores full
  marks), without fabricating host actions
