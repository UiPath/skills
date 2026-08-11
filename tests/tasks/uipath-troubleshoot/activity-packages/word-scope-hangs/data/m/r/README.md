# Word Application Scope Failure - Workflow Hangs on a Background Dialog

This scenario reproduces a `Word Application Scope` **hang**: the scope
opens a password-protected document, Word raises a password prompt the
unattended robot cannot answer, and the modal dialog blocks all COM calls.
The job never advances past the scope and is cancelled after ~30 minutes
with no error.

## What this scenario uncovers

**Root Cause:** The `Word Application Scope` opens `NDA-Protected.docx`
with no `Password` and `Visible=False`. Word's background password prompt
(invisible unattended) wedges the COM calls, so the scope hangs. The tell
is the absence of any error: a blocking dialog produces a hang, not an
exception, and the logs stop at "Opening document".

This maps to:
`references/activity-packages/word-activities/playbooks/word-scope-hangs-background-prompt.md`

The correct agent behavior is to recognize the no-error hang as a hidden
modal dialog (most likely the password prompt for the protected document)
and recommend reproducing with Word visible, then supplying the password /
clearing the prompt - not to attempt host commands itself (the user is
off-host).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project whose `Word Application Scope` opens a protected doc with no password, Visible=False |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** There are no faulted jobs - the hung job shows as
> **Stopped** (cancelled), and `or jobs logs --level Error` is empty. The
> full log ends at "Opening document 'data\\NDA-Protected.docx'" and jumps
> to "Execution was canceled". The agent must broaden from a faulted-jobs
> query to find the stopped job and read the no-error hang as the signal.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `word-scope-hangs-background-prompt.md`
- Agent identified a hidden background Word dialog (password prompt for the
  protected document, or recovery/Safe Mode/activation) blocking COM as the
  cause and recommended surfacing it (run visible) + supplying the password
  / clearing the prompt - without fabricating host actions
