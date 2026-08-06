# Download File from URL Failure - HTTP Client Reused in a Loop

This scenario reproduces a `Download File from URL` failure inside a `For Each`
loop. The activity's internal HTTP client is reused across iterations, so the
first file downloads but a later iteration faults with `This instance has already
started one or more requests. Properties can only be modified before sending the
first request` (`System.InvalidOperationException`).

## What this scenario uncovers

**Root Cause:** Reused/improperly-disposed HTTP client across loop iterations —
the second iteration can't start a fresh request on a client that already sent
one.

This maps to:
`references/activity-packages/file-operations/playbooks/download-file-httpclient-reused-in-loop.md`

"First item works, later items fail" is the tell. The fix is a workflow change
(new `HttpClient` per iteration, or `GC.Collect`/`WaitForPendingFinalizers` after
the download) — not a host action.

## How this test reproduces it

| Layer | Source |
|---|---|
| `process/` | hand-authored UiPath project with `Download File from URL` inside a `For Each` over a list of URLs |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent's diagnosis matches `RESOLUTION.md`: identifies the reused HTTP client
  across loop iterations and recommends a fresh `System.Net.Http.HttpClient` per
  iteration (or `GC.Collect`/`WaitForPendingFinalizers` after the download),
  without fabricating host actions

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's host-side protected mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
