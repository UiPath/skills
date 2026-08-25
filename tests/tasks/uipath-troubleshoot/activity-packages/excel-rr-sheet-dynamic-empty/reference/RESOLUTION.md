# Final Resolution

Investigation complete. Here is the resolution:

---

**Root Cause:** **The Read Range `SheetName` is a dynamic expression bound to the `in_TargetSheet`
input argument, which arrived empty at runtime — so Read Range looked up a sheet named `''`, which
cannot exist.** This is the "variable resolved to the wrong value" branch of the Read Range
sheet-not-found family — NOT a typo, rename, whitespace, look-alike character, or hidden sheet. The
workflow references no literal sheet name at all; the fault is that the value feeding `SheetName` was
blank when the job ran.

**What went wrong:** The workbook opened successfully and `Get Workbook Sheets` returned
`["Sheet1", "Data", "Summary"]`. The `SheetName` on `Read monthly sales sheet` (`ExcelReadRangeX_1`) is
`[in_TargetSheet]`; at runtime `in_TargetSheet` resolved to an empty string, so the activity threw
`UiPath.Excel.BusinessException: The sheet with the name '' does not exist.` The empty name in the error
is the tell — no one configures an empty sheet name, so the value came from an upstream source that was
not populated.

**Why:**
- `process/Main.xaml` — `Read monthly sales sheet` has `SheetName="[in_TargetSheet]"` (a dynamic
  expression, not a literal). The project declares the `in_TargetSheet` input argument.
- Job `bb222222-8888-9999-0000-111122223333` `InputArguments` is `{"in_TargetSheet":""}` — the argument
  was supplied empty by whatever started the job (schedule/trigger input, an Orchestrator asset, or a
  queue-item field that was blank/misconfigured).
- The job log line `Target sheet resolved to: ''` confirms the resolved runtime value was empty before
  Read Range ran.
- Because the name is empty, it matches none of the real sheets — the activity faults at sheet
  resolution, after the workbook opened.

**Evidence:**
- `State = Faulted`; `JobError.Type = BusinessException`, `ActivityDisplayName = "Read monthly sales
  sheet"`; `Info` echoes `The sheet with the name '' does not exist.` with a stack in
  `UiPath.Excel.WorkbookActivities.ReadRangeImpl.ResolveSheet`.
- Actual sheets present: `["Sheet1", "Data", "Summary"]` (from Get Workbook Sheets log) — the workbook
  is fine.
- Source: `SheetName="[in_TargetSheet]"` (dynamic); `InputArguments: {"in_TargetSheet":""}`; resolved
  value logged as `''`.

**Immediate fix:**
1. Fix the upstream source that supplies `in_TargetSheet` so it delivers the intended sheet name (the
   schedule/trigger input, the Orchestrator asset, or the queue-item field that fed it was blank).
   Confirm the corrected value matches one of the workbook's actual sheets verbatim (`Sheet1` / `Data` /
   `Summary`).
2. Add a guard before Read Range that validates the resolved sheet name — fail fast (with a clear
   message naming the resolved value AND the actual sheet list) when `in_TargetSheet` is null/empty or
   is not present in the `Get Workbook Sheets` output. Do not let an empty/unknown name fall through to
   Read Range.

**Do NOT** treat this as a typo, rename, whitespace, look-alike-character, or hidden-sheet issue — the
workflow has no configured literal sheet name to correct; the value is dynamic and arrived empty. Do
NOT edit a sheet-name literal in the `.xaml` (there isn't one). Do NOT rebuild the activity or switch
Excel providers.

**Preventive fix:**
- Validate dynamic sheet names against `Get Workbook Sheets` at the start of the Excel scope; treat an
  empty/unresolved name as a configuration error, not a runtime error.
- Make the source of `in_TargetSheet` required and non-empty at its origin (asset default, queue-item
  schema validation, trigger-input contract). Log the resolved sheet name whenever it is dynamic so
  future debugging is cheap.

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | `SheetName` is bound to `in_TargetSheet`, which arrived empty at runtime, so Read Range looked up sheet `''`. | high | confirmed | Yes | `SheetName="[in_TargetSheet]"`; `InputArguments {"in_TargetSheet":""}`; log `Target sheet resolved to: ''`; error `The sheet with the name '' does not exist.` | Fix the upstream source feeding `in_TargetSheet`; guard/validate the resolved name against Get Workbook Sheets before reading. |
| H2 | Typo in a configured sheet-name literal. | low | eliminated | No | There is no literal `SheetName` — it is the dynamic expression `[in_TargetSheet]`; the resolved value is empty, not a misspelling of a real sheet. | N/A |
| H3 | Sheet was renamed / deleted upstream. | low | eliminated | No | The workbook still has `Sheet1`, `Data`, `Summary`; the lookup value is empty, not a stale-but-plausible name. | N/A |
| H4 | Case / whitespace / look-alike-character mismatch. | low | eliminated | No | An empty string differs from every real sheet by more than case/whitespace/code-point; the value simply was not supplied. | N/A |
| H5 | Hidden / very-hidden sheet. | low | eliminated | No | Failure is an empty lookup name, not a present-but-hidden sheet; Get Workbook Sheets listed the real sheets. | N/A |
