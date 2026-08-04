# Excel Read Range — Dynamic SheetName Resolved To Empty At Runtime

Runtime troubleshooting scenario for `UiPath.Excel.Activities` Read Range (`ExcelReadRangeX`), covering
the **`read-range-sheet-not-found.md` branch 7** — a dynamic `SheetName` expression that resolved to the
wrong value (here, an empty string) at runtime.

## What this scenario exercises

An unattended job faults with `UiPath.Excel.BusinessException: The sheet with the name '' does not
exist.` The workbook opened fine and `Get Workbook Sheets` returned the real sheet list. The agent must
recognize that the `SheetName` is **not a literal** but the dynamic expression `[in_TargetSheet]`, that
the input argument arrived **empty** (`InputArguments: {"in_TargetSheet":""}`, log `Target sheet
resolved to: ''`), and prescribe fixing the upstream source that feeds the argument plus adding a
validate/guard before Read Range. It must NOT diagnose a typo, rename, whitespace, look-alike-character,
or hidden-sheet cause — there is no configured literal to correct.

This is the distinguishing skill for branch 7: the error names a value nobody configured (`''`), so the
fault is upstream data, not a mistyped sheet name.

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` | shared manifest-driven mock dispatcher from `../../_shared/mock_template/` |
| `process/` | crafted modern VB project: `Main.xaml` with `Use Excel File` → `Get Workbook Sheets` → Read Range whose `SheetName` is `[in_TargetSheet]`; the project declares the `in_TargetSheet` input argument |
| `data/m/r/` | canned `Faulted` job; `job-get.json` has `InputArguments {"in_TargetSheet":""}` and a `BusinessException` for sheet `''`; `job-logs.json` shows actual sheets `["Sheet1","Data","Summary"]` and `Target sheet resolved to: ''`; `docsai ask` passthrough |

The diagnosis is not leaked in any agent-visible name: the project is `MonthlySalesImport`, the activity
is `Read monthly sales sheet`. The prompt states the observed symptom (the pasted error with the empty
`''` name and the job key); the cause (empty input argument) is derived from the source + job evidence.

## Success criteria

Scores the **conclusion**, not the trajectory (`skill_triggered` + `llm_judge` against `RESOLUTION.md`):

- Agent invoked the `uipath-troubleshoot` skill.
- Agent identified the dynamic `SheetName` bound to the empty `in_TargetSheet` argument as the cause,
  and the fix (correct the upstream source that supplies the argument + validate the resolved sheet name
  against Get Workbook Sheets before reading) — not a typo/rename/whitespace/hidden-sheet misdiagnosis.

Playbook: `references/activity-packages/excel-activities/playbooks/read-range-sheet-not-found.md`
(branch 7 — variable resolved to wrong value).
