# Word Activities Investigation Guide

## Data Correlation

Before using any fetched data, verify it matches the user's reported problem:

- **Activity** — the faulted activity's namespace and class match the reported failure (e.g., `UiPath.Word.Activities.WordExportToPdf` / display name "Save Document as PDF", `UiPath.Word.Activities.WordApplicationCard` / "Word Application Scope"). Interop activities (inside a `Word Application Scope` / `Use Word File`) and System Word activities share document-shaped operations but run different code paths — treat them as different. The COM wrong-thread fault only occurs on the interop surface.
- **Document** — the document path in evidence matches the file the user is asking about. A child activity operates on the document open inside the surrounding scope — different scope = different document = unrelated data.
- **Robot / machine identity** — the robot account and the machine where Word is installed match the one the user reports. Word interop is per-user-per-machine and per Office install; evidence from a different host is not transferable.
- **Office version** — the Word/Office version installed on the robot machine matches the one the user reports. Multiple Office versions on the same host produce COM dispatcher ambiguity unrelated to a single-version user's experience.
- **External Word state** — whether `WINWORD.EXE` was already running when the run started, and whether it stayed open through the export. Load-bearing for the COM wrong-thread cause — the failure depends on an externally-owned instance and on whether/when it closed.
- **Run surface** — whether the run was foreground Studio / attended (interactive STA) or unattended / Session 0 / background. The off-STA cause requires a non-interactive surface; do not conclude it for a confirmed foreground run.
- **Timestamp** — the failure occurred during the time window the user reported. Load-bearing for COM-interop investigations: transient apartment-affinity errors may not reproduce on demand and depend on what else was running.

If the data doesn't match: **discard it**. Do NOT use unrelated data as a proxy. Report the mismatch and ask for clarification.

## Testing Prerequisites

When testing hypotheses for `Word Application Scope` / `Save Document as PDF` COM failures, gather and verify these before drawing conclusions:

1. **Activity identity** — confirm the faulted activity is an interop Word activity (e.g., `WordExportToPdf`, "Save Document as PDF") inside a `Word Application Scope` / `Use Word File`, not a System Word activity (different code path, no shared interop instance).
2. **Scope structure** — from the `.xaml`, confirm the export is the sole/last child of the scope that opened the document, and capture the scope's `FilePath` / `CreateNewFile`. Distinguish "export correctly nested" from "export references a document handle across scopes/threads".
3. **Threading between scope-open and export** — grep the workflow(s) for `Parallel`, `ParallelForEach`, `Pick`, `PickBranch`, `InvokeWorkflowFile`, `InvokeCode`, and coded `.cs` workflows. Any of these between scope-open and the export puts the off-STA cause in play.
4. **In-workflow Word lifecycle** — grep for any activity that closes or kills Word or a host app (`Close Application`, `Close Window`, `Kill Process`, `Quit`, host `Dispose`). Absence means a mid-run close was external/manual, not in-graph.
5. **External Word state at run time** — whether a `WINWORD.EXE` was already open when the run started, and whether that window closed before the export. Not visible in the job log — the user (or someone with desktop access on the host) has to confirm.
6. **Run surface** — foreground Studio Run/Debug vs attended interactive session vs unattended / Session 0 / background. Confirms or eliminates the off-STA cause.
7. **Package version** — `UiPath.Word.Activities` version from `project.json`, and whether it is a pre-release / alpha build vs the stable version bundled with the runtime's LTS.

### Out-of-band confirmation

The deciding proof for the attachment / mid-run-close cause is an A/B re-run on the user's host (Trial A: external Word open and closed mid-run → expect the error; Trial B: no external Word → expect success). This requires the user's automation machine; record it as an out-of-band confirmation step — it does not block a hypothesis when no alternative cause is better supported.
