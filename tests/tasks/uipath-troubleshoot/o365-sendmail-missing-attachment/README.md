# O365 Send Mail Missing Attachment — Faithful Replay

This scenario replays a real UiPath troubleshooting investigation where the
agent reached a verified resolution. The fixtures are the verbatim
`uip` CLI responses captured from that session (scrubbed).

## What the original session uncovered

The user asked why their last job in folder `Shared` failed. The most recent
job, `ERN_O365_SendMailRejected` (key `74db8e32-8535-40b2-9b40-62540456adab`),
faulted with a raw `System.IO.FileNotFoundException: File does not exist:
C:\Temp\missing-attachment-repro.pdf` thrown by the legacy O365 `SendMail`
activity. The package's `AttachmentsHelpers.EnsureFileExists` check threw
while assembling attachments — before any Microsoft Graph send call. Trace
spans show the Microsoft 365 Scope opened cleanly (auth OK), and no
`ErrorInvalidRecipients` / `ErrorSendAsDenied` / `ErrorMessageSizeExceeded`
codes appear anywhere — the other send-rejection causes are ruled out. Fix:
stage the file on the runtime machine and/or correct the `Attachments` path.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `fixtures/mocks/responses/*.json` | real stdout extracted verbatim from the session's investigation `raw/` outputs |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its recorded fixture |

No `process/` snapshot — the original investigation determined the root cause
from platform evidence alone (job Info/logs/traces carry the full fault stack).

### Local filesystem check (not mocked)

The original investigation also verified the missing path with a LOCAL
PowerShell `Test-Path` on the runtime machine (the local hostname matched the
job's host machine). That is not a `uip` call, so it is intentionally NOT in
the mock manifest. The eval agent may attempt the same check inside the
sandbox — `C:\Temp\missing-attachment-repro.pdf` is absent there too, which is
consistent with the recorded evidence.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent's final response reaches the same root cause and fix as `RESOLUTION.md`

## Re-running the extraction

This scenario was hand-built from the investigation's `raw/` verbatim CLI
outputs (the generator's transcript pass is unreliable for this session). If
the source investigation changes, update the fixture JSONs directly and re-run
the scrub checks, or regenerate with:

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path> --transcript <path> --resolution <path> \
    --scenario-name o365-sendmail-missing-attachment --apply
```
