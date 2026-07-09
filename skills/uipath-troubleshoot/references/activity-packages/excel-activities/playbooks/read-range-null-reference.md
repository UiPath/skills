---
confidence: low
---

# Read Range — NullReferenceException / TargetInvocationException From Inside The Activity

## Context

A `UiPath.Excel.Activities` Read Range (or any activity that parses workbook content) fails with a generic .NET runtime exception thrown from inside the activity's parsing code — not from file acquisition or sheet resolution. The workbook opens (no `IOException`, `FileNotFoundException`, or `BusinessException`), but somewhere during cell / range / formula / formatting parsing the activity hits a condition it cannot handle, and the .NET runtime surfaces a wrapper exception with little or no cell-level pointer.

> **Confidence: low.** Unlike the file-locked, sheet-not-found, and file-not-found playbooks, the fingerprint here does not distinguish cause-branches by error wording alone. All five branches below can produce the same `NullReferenceException` or `TargetInvocationException` text. Diagnosis usually requires opening the workbook manually and inspecting it visually — the agent should investigate via Orchestrator evidence to rule out the easy cases, then hand the user a list of host-side / workbook-side checks rather than guessing a branch.

What this looks like:
- Activity fails with one of:
  - `System.NullReferenceException: Object reference not set to an instance of an object.` — most common, surfaces from cell / range / named-range / formula parsing.
  - `System.Reflection.TargetInvocationException: Exception has been thrown by the target of an invocation.` — a wrapper around an inner exception that the activity's reflection-based dispatch caught and re-threw. The `InnerException` (visible in `or jobs get` Info if the stack is included) is the load-bearing detail.
  - Provider-specific wrappers: `UiPath.Excel.ExcelException` or `DocumentFormat.OpenXml.OpenXmlPackageException` for OpenXML provider failures; `System.Runtime.InteropServices.COMException` for Excel COM provider failures.
- The exception's stack trace originates inside `UiPath.Excel.Activities.*` or `DocumentFormat.OpenXml.*` — NOT inside `System.IO.*` (that points at file-not-found / file-locked) and NOT inside `UiPath.Excel.WorkbookActivities.ReadRangeImpl.ResolveSheet` (that points at sheet-not-found).
- The error has no cell address, no sheet name, no range expression — it's a generic runtime exception. The agent cannot pinpoint cause from the error string alone.
- The workbook opens successfully on a developer's machine via interactive Excel; the problem surfaces only under the workflow's parsing path.

What can cause it (cause-branches — none distinguishable by error wording alone):

1. **Sensitivity label (Microsoft Purview / Azure Information Protection)** — the workbook is labeled (Confidential, Highly Confidential, etc.) and the label policy blocks programmatic access for the Robot user. The interactive user has the label permission and can open the file; the Robot service, running under a different identity, does not. Symptom: NRE / TIE on open or first read; an interactive admin RDPing in CAN open the file and see content; if the Robot user opens an Excel instance manually, the workbook either refuses to open or opens with a banner requesting authentication.
2. **Workbook structural corruption** — the XLSX file (a ZIP container) was edited by another tool that left structurally invalid XML, broken relationships, or truncated parts. Common sources: a python script that wrote the workbook with `openpyxl` and a bug; a Power Automate flow that saved partial output; a network copy that was interrupted; a manual ZIP edit. Symptom: NRE or `OpenXmlPackageException`; Excel itself may open the file with a "Repaired" notice and a list of issues.
3. **Broken named range or formula reference** — the workbook contains a defined name (named range) that points at a deleted sheet or out-of-range cell, OR a formula references `#REF!` or a non-existent range. When the activity walks the workbook's defined names or evaluates formulas, the parser hits a null / unresolvable reference. Symptom: NRE during read; opening the workbook in Excel and pressing `Ctrl+F3` (Name Manager) reveals defined names with `#REF!` in their formula.
4. **Unsupported OpenXML feature** — the workbook contains an Excel feature only the COM provider supports (legacy XLS-format pages, certain macro objects, embedded OLE objects, specific chart types, dynamic arrays in older OpenXML versions). The default OpenXML provider in `Use Excel File` cannot parse it and fails with NRE or TIE. Symptom: works under `Excel Application Scope` (or `Use Excel File` with `ReadFormatting: True` forcing COM); fails under default `Use Excel File`.
5. **Heavy conditional formatting / scale-related parser limit** — the workbook has thousands of conditional formatting rules, very large defined-range pivot caches, or millions of cells with formatting metadata. The parser hits a memory or recursion limit during the read. Symptom: NRE late in parsing (after open succeeded); workbook is unusually large (several hundred MB or millions of populated cells); opening it manually in Excel is also slow.

What to look for:
- **The exception class and stack origin** — `NullReferenceException` vs. `TargetInvocationException` (and its inner exception if available). Stack origin inside `OpenXml.*` points at branch 4 or 2. Stack origin inside the activity's name-resolution code points at branch 3.
- **Workbook size on disk** — branch 5 candidates are usually large (> 100 MB) or have very high populated-cell counts.
- **Recent provenance of the workbook** — was it just downloaded? Was it generated by a script or Power Automate? Was it edited by hand? Branch 2 (corruption) clusters around freshly-written files.
- **Whether the same workflow worked on a different host with Excel installed** — branch 4 (unsupported OpenXML feature) is the canonical "works on dev box, fails on Robot" pattern from the sheet-not-found playbook's branch 2, but for parsing features rather than case sensitivity.
- **Whether the workbook has visible sensitivity / classification banners** — when an interactive user opens the workbook, do they see a Purview / AIP banner? Branch 1 fingerprint.
- **`Get Workbook Sheets` behavior** — if it succeeds and returns sheet names but `Read Range` fails, the failure is mid-parse (likely branches 3, 4, or 5). If it fails too, the failure is at open / first-read (likely branches 1 or 2).

## Investigation

This is a low-confidence playbook — the agent's job is to rule out the easier branches via Orchestrator evidence, then hand the user a list of host-side / workbook-side checks. Do NOT guess a specific branch without strong evidence.

1. **Confirm the activity and the workbook.** From `or jobs get`: the exception class, the resolved workbook path, and the `Info` field's full stack trace if available. From workflow source: the activity (Read Range / Read Cell / etc.) and the scope (`Use Excel File` vs. `Excel Application Scope`). Capture the configured `SheetName`, `Range`, and any non-default properties (`ReadFormatting`, `EditPassword`, password expressions).

2. **Categorize the exception.** Stack origin and inner exception narrow the suspect branches:
   - `OpenXmlPackageException` / stack inside `DocumentFormat.OpenXml.*` → branch 2 (structural corruption) or branch 4 (unsupported OpenXML feature).
   - `COMException` / stack inside `Microsoft.Office.Interop.Excel.*` → likely branch 4 (COM-side parsing issue) or branch 5 (COM hitting memory limit).
   - Plain `NullReferenceException` with stack inside `UiPath.Excel.Activities.*` → could be any branch; need more evidence.
   - `TargetInvocationException` with an inner exception → unwrap and re-categorize on the inner.

3. **Recent-jobs pattern.** `uip or jobs list --process-name '<process>' --limit 20 --output json`:
   - All recent runs against the same workbook fail with the same exception → persistent (branches 1, 4, 5 candidates).
   - Only the latest run fails after a workbook update → branch 2 (corruption from a recent write) or branch 3 (someone deleted the named range's referent recently).
   - Some Robot hosts succeed, others fail → branch 1 (label permissions per Robot identity) or branch 4 (COM-installed vs. headless OpenXML).

4. **Workflow-source check for branch 3.** If the failing activity references named ranges (e.g., `Range: "MyDataRange"`) or formulas that depend on cross-sheet references, branch 3 is plausible. Note the named range and ask the user to verify it via Excel's Name Manager (`Ctrl+F3`).

5. **Provider check for branch 4.** If the scope is `Use Excel File` with no `ReadFormatting` / `EditPassword` / macro-related properties, the runtime uses OpenXML on a host without Excel installed. Ask the user to try the same workflow under `Excel Application Scope` on a host with Excel — if it succeeds there, branch 4 is confirmed.

6. **Hand the user a workbook-inspection checklist.** Once Orchestrator evidence is exhausted and the branch is not clearly identified, give the user the manual checks needed to confirm the cause. Examples:

   ```powershell
   # Size and modification time on the host
   Get-Item '<workbook-path>' | Select-Object FullName, Length, LastWriteTime, Attributes
   ```

   Then ask the user to do the following in Excel on a workstation with the workbook open:
   - **Branch 1 check:** Look for a sensitivity / classification banner at the top of the workbook (Confidential, Highly Confidential, label-specific text).
   - **Branch 2 check:** Open the workbook in Excel and look for a "Repaired" dialog or recovery log noting any issues with the file.
   - **Branch 3 check:** Press `Ctrl+F3` (Formulas → Name Manager). List any named ranges whose `Refers to` column shows `#REF!`, `#NAME?`, or `#VALUE!`.
   - **Branch 4 check:** File → Info → Inspect Workbook → Check for Issues → Check Compatibility. Note any "features not supported by earlier versions" — these are often features OpenXML cannot parse.
   - **Branch 5 check:** File → Info → workbook size; count of sheets; count of populated cells (Ctrl+End on each sheet). If the workbook is > 100 MB or has more than ~1M populated cells, branch 5 is plausible.

7. **If the workbook is regenerated by another process before this workflow reads it** (branch 2 cluster pattern): coordinate with the upstream owner. Have them save / write the workbook through Excel itself (rather than a third-party library) to produce structurally clean output.

The root cause is usually identifiable via Excel inspection more than via Orchestrator. A confirmed finding names the specific issue found in the workbook (a `#REF!` named range; a sensitivity label; an unsupported feature flagged by Compatibility Checker; a file size indicating scale) — not just "the workbook is broken."

## Resolution

Map the branch identified via Investigation + workbook inspection to the fix:

- **Branch 1 — Sensitivity label blocks the Robot user:**
  - The cleanest fix is to grant the Robot user permission for the label (Microsoft Purview → Information Protection → Labels → policy → add the Robot user / group).
  - If label permissions cannot be granted, ask the workbook owner to remove the label or apply a less restrictive label.
  - Long-term: do not classify workbooks consumed by automation with labels that exclude the Robot identity. Document an exemption for automation identities.

- **Branch 2 — Workbook structural corruption:**
  - One-off recovery: open the workbook in Excel manually; let Excel's repair dialog clean up the structure; save as a new `.xlsx`. Update the workflow to point at the repaired file.
  - Permanent fix: the upstream tool that wrote the broken file needs to be fixed. Common offenders: `openpyxl` writes without all required parts; manual ZIP edits; truncated network copies. Have the upstream owner write through Excel COM or a well-maintained library (e.g., latest `openpyxl` with `data_only=True` discipline; `ClosedXML`; Excel itself via VSTO).
  - Prevention: validate workbook integrity at the boundary where the file enters the automation pipeline. A one-line Open Excel File scope as a smoke test rejects corrupt files before downstream processing.

- **Branch 3 — Broken named range / formula reference:**
  - Open the workbook in Excel → `Ctrl+F3` → identify and either delete or fix every named range that shows `#REF!` in `Refers to`.
  - For formulas with `#REF!` cells: fix the formula or delete the formula if the referenced data is no longer needed.
  - Update the workflow's `Range` expression if it referenced a deleted named range.
  - Prevention: do not delete sheets or cells that named ranges depend on without first updating the named ranges. The workbook publisher should audit Name Manager after structural changes.

- **Branch 4 — Unsupported OpenXML feature:**
  - **Best fix:** simplify the workbook to use only OpenXML-supported features. Use Excel's `File → Info → Inspect Workbook → Check Compatibility` to identify the offending features; remove or replace them.
  - **Or force the COM provider:** set `ReadFormatting: True` (or another COM-forcing property) on `Use Excel File`, requiring Excel installed on the Robot host. Equivalent to the case-mismatch fix in the sheet-not-found playbook.
  - **Or migrate to legacy `Excel Application Scope`:** explicit COM-only path. Less portable, but rules out OpenXML feature gaps entirely.

- **Branch 5 — Heavy conditional formatting / parser scale limit:**
  - Reduce the workbook's size: remove unused conditional formatting rules (Home → Conditional Formatting → Manage Rules → delete unused rules); compress or remove pivot caches; split large workbooks into per-month or per-region files.
  - Raise the Robot host's memory (branch 5 often correlates with `MemoryException` if logs are detailed; sizing the host against the workbook is the fix).
  - If the data fits, switch to the cloud surface (`o365-activities` package): Microsoft Graph reads only the data, not the formatting metadata, and is more memory-efficient for very large workbooks.

## Prevention (cross-branch)

- Treat any workbook consumed by automation as a contract: agree on the file format (current `.xlsx`, no macros, no embedded OLE), the maximum size, and the source tool that writes it.
- Validate at the boundary: a one-line `Get Workbook Sheets` smoke test on the workbook at job start, with a clear failure message, catches branches 1 / 2 / 4 immediately and produces a much cleaner diagnosis than the generic NRE.
- Audit workbook size and Name Manager after structural changes — saves operators 30 minutes per support ticket.
- Do not classify automation-consumed workbooks with sensitivity labels that exclude the Robot identity.
- When choosing between `Use Excel File` (OpenXML default) and `Excel Application Scope` (COM only), be deliberate. OpenXML is more portable but supports fewer Excel features. COM is more capable but requires Excel installed and has higher orphan risk (see [`read-range-file-locked.md`](./read-range-file-locked.md)).

## Related

- Other Excel Read Range failure fingerprints (file-locked, sheet-not-found, file-not-found) are separate playbooks — see [`../summary.md`](../summary.md).
- For shared / cloud Excel workbooks accessed via Microsoft Graph rather than the local filesystem, see [`o365-activities/overview.md`](../../o365-activities/overview.md). Graph reads sidestep most branches of this playbook (no OpenXML parsing on the Robot host; no local sensitivity-label evaluation).
- The Excel.Activities package's behavior across versions can shift — for stack-trace-specific branches (especially branch 4), check `UiPath.Excel.Activities` release notes for the version in use and consider upgrading.
