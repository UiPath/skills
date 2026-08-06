# Download File from URL Failure - File Stuck as .tmp (Finalize Race)

This scenario reproduces a `Download File from URL` finalize race. The download
"completes," but the next step (`Read CSV` on `data\daily.csv`) faults with
`Could not find file` because the file is still the temporary `daily.csv.tmp` —
the workflow consumed it before the stream finalized to the real name.

## What this scenario uncovers

**Root Cause:** The downstream `Read CSV` runs before the downloaded file is
finalized from `*.tmp` to `daily.csv`, so the target path doesn't resolve yet.
Intermittent (sometimes works).

This maps to:
`references/activity-packages/file-operations/playbooks/download-file-stuck-tmp.md`

The discriminator vs a plain file-not-found: a `daily.csv.tmp` is present and the
failure is timing-dependent. The fix is a workflow change (Retry Scope / File
Exists on the final name) — not a host action.

## How this test reproduces it

| Layer | Source |
|---|---|
| `process/` | hand-authored UiPath project: `Download File from URL` (FileName `daily.csv`) followed by `Read CSV` on `data\daily.csv` |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent's diagnosis matches `RESOLUTION.md`: identifies the download/finalize race
  (file still `.tmp` when the downstream step runs; intermittent) and recommends a
  Retry Scope / File Exists gate on the **final** target extension before
  consuming the file, without fabricating host actions

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's UID/GID-isolated mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
