# Excel Read Range — Mapped Drive Not Mapped Under Robot Session

This scenario reproduces a Read Range failure where the workflow uses
a mapped drive path (`Z:\Data\sales-2026-05.xlsx`) that exists in the
developer's interactive RDP session but is **not** mapped in the
Robot service's unattended session on the same host. The job ends
with:

```
System.IO.DirectoryNotFoundException: Could not find a part of the path 'Z:\Data\sales-2026-05.xlsx'.
```

## What this scenario uncovers

**Root Cause:** Windows mapped drives are **per-session**. A drive
letter mapped via `net use` (or via Explorer's "Map Network Drive")
in an interactive user session is visible to that session only. The
Robot service runs in its own session and does not inherit the
interactive user's drive mappings, even on the same host. The user's
"works on my machine" experience (when they RDP in and see
`Z:\Data\...`) is misleading.

This maps to:
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/read-range-file-not-found.md`
(the "Drive letter not mapped under Robot session" branch).

The CLI evidence chain (workflow source `Z:\` prefix +
`DirectoryNotFoundException` on the drive root) gives the agent a
strong indicator, but verifying the drive mappings on the host
requires either confident reasoning about per-session drive
mappings OR a host-side `net use` check under the Robot's session.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | `ExcelDailyImport` project — `Use Excel File` with **mapped-drive** `WorkbookPath: "Z:\Data\sales-2026-05.xlsx"`, then `Read Range` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses; the `or jobs get` Info field shows the drive-root `DirectoryNotFoundException` |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

The expected investigation chain: `folders list-current-user` →
`jobs list --state Faulted` → `jobs get` (sees `Z:\` prefix +
DirectoryNotFoundException on drive root) → `jobs logs` → workflow
source review (literal `Z:\` mapped-drive path) → either (A)
confident branch 4 diagnosis or (B) recommend `net use` host-side
check.

> **Note on fixtures.** Synthetic. The job key, folder key, and
> mapped-drive letter are placeholders. The test grades whether
> the agent surfaces the per-session-drive-mapping pattern using
> the workflow-source evidence + reasoning.
