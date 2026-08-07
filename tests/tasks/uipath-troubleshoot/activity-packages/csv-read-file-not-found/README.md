# Read CSV Failure - "Could not find file" (Async Download Timing)

This scenario reproduces a `Read CSV` failure where the CSV is produced by an
**upstream download immediately before the read**, and `Read CSV` runs before the
file is finished writing to disk — so it faults with `Could not find file
'...\data\daily-export.csv'` (`FileNotFoundException`). The file is present when
checked afterward, which points at a timing race rather than a permanently wrong
path.

## What this scenario uncovers

**Root Cause:** A download/export step runs just before `Read CSV`; at read time
the file isn't on disk yet (async write not complete), so the read fails
intermittently. (The playbook also covers a path variable wrapped in quotes and
relative-path drift.)

This maps to:
`references/activity-packages/csv-activities/playbooks/read-csv-file-not-found.md`

The fix is a workflow change (wait for the file: File Exists retry / Delay;
verify the path), not a host action.

## How this test reproduces it

| Layer | Source |
|---|---|
| `process/` | hand-authored UiPath project that reads `data\daily-export.csv` with `Read CSV`; the file is produced by an upstream download (not committed, mirroring "not on disk yet") |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent's diagnosis matches `RESOLUTION.md`: identifies the async-download timing
  race (file not written yet at read time; intermittent) and recommends guarding
  the read with a File Exists retry / Delay (and verifying the path / unquoted
  path variable), without fabricating host actions

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's host-side protected mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
