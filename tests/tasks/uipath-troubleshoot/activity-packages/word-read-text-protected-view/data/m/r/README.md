# Read Text Failure - Protected View Blocks an Externally-Sourced File

This scenario reproduces a `Read Text` failure where Word opens an
email-sourced document (Mark-of-the-Web) in **Protected View**, blocking the
Interop read with a `COMException`. Internally-created documents read fine.

## What this scenario uncovers

**Root Cause:** The document arrived from email/internet, so it carries a
Mark-of-the-Web. Word opens it in Protected View (read-only sandbox) and the
Interop read is blocked. Locally-authored files have no Mark-of-the-Web and
read fine. This is a host file-trust / security configuration issue, not a
format, path, or install problem.

This maps to:
`references/activity-packages/word-activities/playbooks/read-text-protected-view.md`

The correct agent behavior is to tie the fault to Protected View /
Mark-of-the-Web on externally-sourced files and recommend unblocking the
file / Trusted Locations / disabling Protected View — framed as host steps
for the off-host user (not fabricating host actions, not blaming the format
or path).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project; `Word Application Scope` + `Read Text` on an inbound email-attachment `.docx` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** The faulted job's `COMException` explicitly names
> Protected View and the "Internet/email location" origin; the user frames
> the failure as specific to externally-arriving files (internal docs read
> fine). The off-host framing means the agent must hand over host steps.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `read-text-protected-view.md`
- Agent identified Protected View / Mark-of-the-Web on the externally-sourced
  file as the cause and recommended unblocking the file / Trusted Locations /
  disabling Protected View as host steps — without fabricating host actions
  or blaming the file format/path
