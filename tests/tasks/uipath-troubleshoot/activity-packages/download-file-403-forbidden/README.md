# Download File from URL Failure - HTTP 403 (Forbidden)

This scenario reproduces a `Download File from URL` failure where the server
returns `403 (Forbidden)`. The activity issues a native HTTP request that carries
no authentication / cookies / browser session, so a portal-gated URL rejects it —
even though the same link downloads in a logged-in browser.

## What this scenario uncovers

**Root Cause:** The native download has no auth/session; the portal-gated URL
returns 403.

This maps to:
`references/activity-packages/file-operations/playbooks/download-file-403-401-auth.md`

"Works in my logged-in browser, 403 for the robot" is the tell. The fix is to
authenticate / set `UserAgentHeader`, or download via an authenticated UI browser
session (Click + Wait for Download) — not a host action.

## How this test reproduces it

| Layer | Source |
|---|---|
| `process/` | hand-authored UiPath project with a single `Download File from URL` to a portal URL (no `UserAgentHeader`/auth) |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent's diagnosis matches `RESOLUTION.md`: identifies that the native download
  carries no authentication for the portal-gated URL (403) and recommends
  authenticating / setting `UserAgentHeader`, or downloading via an authenticated
  UI browser session (Click + Wait for Download), without fabricating host actions

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's host-side protected mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
