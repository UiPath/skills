# O365 Sharing Link Access Denied — Faithful Replay

This scenario replays a real UiPath troubleshooting investigation where the
agent reached a verified resolution. The fixtures are the verbatim
`uip` CLI responses captured from that session.

## What the original session uncovered

**Root Cause:** The OneDrive/SharePoint sharing link that the Read Range activity uses to locate its Excel workbook is no longer valid for the job's Microsoft 365 connection — the link was revoked, its sharing scope was changed, or the underlying item's access was removed for the connection's account. When Read Range tried to resolve that sharing link through Microsoft Graph, Graph returned `accessDenied` (HTTP 403), faulting the job before the range was ever read.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `process/` | frozen snapshot of the failing UiPath project |
| `fixtures/mocks/responses/*.json` | real stdout extracted verbatim from the session transcript |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its recorded fixture |

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched the correct playbook AND reached the same root cause as `RESOLUTION.md`

## Re-running the extraction

If the source transcript or project changes, regenerate the scenario:

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path> --project <path> --transcript <path> \
    --scenario-name o365-sharing-link-access-denied --apply
```
