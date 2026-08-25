# Assign — "The source contains no data rows" (LINQ / CopyToDataTable, Runtime)

Runtime troubleshooting scenario for `System.Activities.Statements.Assign`.

## What this scenario exercises

An unattended job faults with `System.InvalidOperationException: The source contains no data rows`. The
agent must trace it to an `Assign` running a LINQ `.Where(...).CopyToDataTable()` whose filter matched
**zero rows** on this run, and recognize that `CopyToDataTable()` throws on an empty sequence. The fix
is to guard the materialization with `.Any()` (assign only when matches exist; otherwise `.Clone()` /
handle the empty case). The source table is non-null and populated (42 rows loaded) — this is NOT a
`NullReferenceException`.

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` | shared manifest-driven mock dispatcher from `../../_shared/mock_template/` |
| `process/` | crafted VB project source: `Main.xaml` with an `Assign` "Filter active invoices" whose `Value` is `dtInvoices.AsEnumerable().Where(...).CopyToDataTable()` with no `.Any()` guard |
| `data/m/r/*.json` | faulted-job fixtures — `job-get`/`job-logs` carry `The source contains no data rows` + a stack bottoming out in `CopyToDataTable` (user expression, not a package); `jobs-list` shows prior Successful runs (data-dependent); log shows "rows loaded: 42" (source non-empty) |
| `data/m/r/manifest.json` | `docsai ask` passthrough + `or jobs/folders` fixtures + permissive empty `unmocked_default` |

## Success criteria

Scores the **conclusion**, not the trajectory (`skill_triggered` + `llm_judge` against `RESOLUTION.md`):

- Agent invoked the `uipath-troubleshoot` skill.
- Agent identified the unguarded `CopyToDataTable()` on a zero-match LINQ filter and the fix (guard with
  `.Any()` / handle the empty result), and did NOT misdiagnose it as a null/uninitialized-table error.

Playbook: `references/runtime-exceptions/playbooks/assign-linq-no-data-rows.md`.
