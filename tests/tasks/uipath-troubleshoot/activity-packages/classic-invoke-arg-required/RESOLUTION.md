# Final Resolution

Investigation complete. Here is the resolution:

---

**Root Cause:** The invoked workflow gained a **new required `In` argument** that the parent's `Invoke
Workflow File` never mapped. `ArchiveInvoice.xaml` declares two required inputs — `in_InvoiceId` and
`in_ArchivePath` (both `InArgument(x:String)`, no default) — but `Main.xaml`'s invoke only supplies
`in_InvoiceId`. The unmapped required argument `in_ArchivePath` triggers "Value for a required activity
argument was not supplied."

**What went wrong:** This is a **design-time validation** error, not a robot job fault. The child
workflow's argument list drifted — a mandatory argument was added — while the parent's `Invoke Workflow
File` still carries the older argument layout. The invoke's `Arguments` dictionary is missing an entry
for the new required input.

**Why:**
- `process/ArchiveInvoice.xaml` — `<x:Members>` declares `in_InvoiceId` (`InArgument(x:String)`) **and**
  `in_ArchivePath` (`InArgument(x:String)`). Neither has a default, so both are required inputs.
- `process/Main.xaml` — `<uca:InvokeWorkflowFile>` InvokeWorkflowFile_1 (DisplayName "Invoke
  ArchiveInvoice", targeting `ArchiveInvoice.xaml`) maps only `in_InvoiceId` in its `Arguments`
  dictionary. There is **no** `in_ArchivePath` entry.
- The invoked file resolves and its member set is fine — the fault is the missing mapping for the new
  required argument, which is exactly what "Value for a required activity argument was not supplied"
  reports.

**Evidence:**
- Error string: `Value for a required activity argument was not supplied` (on the Invoke Workflow File).
- `ArchiveInvoice.xaml` `<x:Members>`: `in_InvoiceId` + `in_ArchivePath`.
- `Main.xaml` invoke `Arguments` dictionary: only `in_InvoiceId` mapped; `in_ArchivePath` absent.
- No Orchestrator job/log/trace — surfaces in Studio validation.

**Immediate fix:**
1. Open the **Invoke Workflow File** activity ("Invoke ArchiveInvoice") in `Main.xaml`.
2. Click **Import Arguments** to pull in the invoked workflow's current argument list.
3. Map the newly required `in_ArchivePath` to a valid value (a variable or literal).
   - Where: `Main.xaml` InvokeWorkflowFile_1 `Arguments` — add the `in_ArchivePath` entry.

**Preventive fix:**
- Whenever an invoked workflow's arguments change, re-open every caller's `Invoke Workflow File` and
  click **Import Arguments** so required inputs stay mapped. `Find References` on the changed workflow
  locates all invocations to update.

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | `ArchiveInvoice.xaml` requires `in_InvoiceId` and `in_ArchivePath`, but `Main.xaml`'s invoke maps only `in_InvoiceId`; the unmapped required `in_ArchivePath` fails validation. | high | confirmed | Yes | Child `<x:Members>` lists both inputs; parent invoke `Arguments` maps only `in_InvoiceId`. | Open the Invoke Workflow File, Import Arguments, and map `in_ArchivePath`. |
| H2 | The invoked file is missing or its path is wrong. | low | eliminated | No | `ArchiveInvoice.xaml` is present and the invoke resolves it; the error is a missing argument value, not a missing file. | N/A. |
