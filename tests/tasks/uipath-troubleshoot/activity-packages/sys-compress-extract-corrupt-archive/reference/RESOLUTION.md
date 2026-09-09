# Final Resolution

---

**Root Cause:** The `Extract/Unzip Files` activity in `Main.xaml` cannot
open its input archive `C:\AutomationData\Invoices\batch_2026.zip`
because that file is not a valid, complete ZIP. The
`CompressionException: Cannot extract data from archive` wraps an inner
`ICSharpCode.SharpZipLib.Zip.ZipException: Cannot find central directory`
— the ZIP's central-directory record is missing, which means the file is
truncated, corrupt, or a non-zip file renamed with a `.zip` extension.

**What went wrong:** The `InvoiceIntake` job (started
2026-06-24T09:15:02.010Z) faulted ~11 seconds after launch when the
`Extract/Unzip Files` activity tried to extract
`C:\AutomationData\Invoices\batch_2026.zip` to
`C:\AutomationData\Invoices\extracted`.

**Why:** `ExtractFiles` opened the archive and the underlying
`SharpZipLib` reader could not locate the central directory — the record
at the end of every valid ZIP that indexes its entries. A missing central
directory is not a permissions or destination problem; the file itself is
not a readable ZIP (truncated download, corrupt archive, or a different
file type renamed `.zip`). The generic activity message ("Check if the
archive is corrupted or if you have write permissions to the destination")
lists both possibilities, but the inner `ZipException` narrows it to a
corrupt/incomplete archive.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: InvoiceIntake — Faulted at 2026-06-24T09:15:13.220Z (ran ~11 seconds)
- Folder: Finance (key `4b1c7e90-2a3d-4f5e-9c8b-1a2b3c4d5e6f`)
- Machine: MOCK-HOST
- ErrorCode: `System.Compression.Sys.ExtractFailed`
- Final error: `Cannot extract data from archive "C:\AutomationData\Invoices\batch_2026.zip"` → `Main.xaml` → `ExtractFiles "Extract/Unzip Files"` → `Sequence "Main Sequence"` → `InvoiceIntake "InvoiceIntake"`

### System Activities (Root Cause)
- Activity: `ExtractFiles` (DisplayName: "Extract/Unzip Files")
- FileToExtract: `C:\AutomationData\Invoices\batch_2026.zip`
- DestinationFolder: `C:\AutomationData\Invoices\extracted`
- Outer exception: `UiPath.Activities.System.Compression.CompressionException: Cannot extract data from archive "C:\AutomationData\Invoices\batch_2026.zip".`
- Inner exception: `ICSharpCode.SharpZipLib.Zip.ZipException: Cannot find central directory` — the ZIP is invalid/incomplete.

---

**Immediate fix:**

### System Activities (Root Cause)
1. Confirm the input file is a complete, valid, unencrypted ZIP before extracting.
   - **Why:** The inner `ZipException: Cannot find central directory` proves the file is not a readable ZIP. Correcting activity properties will not help — the byte stream itself is the problem.
   - **Where:** Inspect `C:\AutomationData\Invoices\batch_2026.zip` on the robot host. If it comes from an upstream download, re-fetch it and confirm the downloaded byte size matches the source before the extract runs. Verify it opens in a standard ZIP tool and is not password-protected.
   - **Who:** RPA developer / whoever owns the upstream download step
   - **Source:** `system-activities/playbooks/compress-extract-files-failed.md` ("Cannot extract data from archive" branch)

---

**Preventive fix:**

1. **Studio** — Before `Extract/Unzip Files`, validate the archive: check the file exists and its size is non-zero (and, where feasible, matches the expected/reported source size), and wrap the extract in a Try/Catch that fails the job with a clear "archive corrupt or incomplete" message.
   - **Why:** A truncated or corrupt download otherwise surfaces as a low-level `ZipException` deep in the stack instead of an actionable business error.
   - **Who:** RPA developer

2. **Upstream** — Make the download step verify completeness (Content-Length match, checksum if available) and retry on partial transfer.
   - **Why:** The most common cause of a missing central directory is a truncated download.
   - **Who:** RPA developer / integration owner

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Input ZIP is corrupt/incomplete (missing central directory) | High | Confirmed | Yes | Inner `ZipException: Cannot find central directory` | Re-fetch/replace with a valid complete ZIP; validate before extract |
| H2 | No write permission on destination folder | Low | Rejected | No | Failure is on read/open of the archive, not the destination write | — |

---

Would you like help adding an archive-validation guard before the
`Extract/Unzip Files` activity, or reviewing the upstream download step? I
can also clean up the `.local/investigations/` folder if you no longer
need it.
