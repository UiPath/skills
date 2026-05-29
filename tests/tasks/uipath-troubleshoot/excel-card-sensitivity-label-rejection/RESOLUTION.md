# Final Resolution

---

**Root Cause:** The target workbook `client-report.xlsx` has a
Microsoft Purview sensitivity label applied:
**`Confidential - Client Data`** (label ID
`8c2f3a4d-1234-5678-abcd-aip00client01`). The package
`UiPath.Excel.Activities 2.24.7` (≥ v2.23.4) supports the
`SensitivityLabel` and `SensitivityOperation` properties on the
`Use Excel File` card, but neither property is configured on
`UseExcelFile_1`. Under v2.23.4+ semantics, write operations
against a Purview-labeled workbook REQUIRE both properties to be
set so the runtime can acknowledge / apply / preserve the label
during the write. With both properties unset, the card detects
the label, validates against the configured operation (none),
and throws `UiPath.Excel.BusinessException` before the Write
Range inside the body runs.

**What went wrong:** Failing job
`gg333333-cccc-dddd-eeee-ffffaaaabbbb` started at
`2026-05-30T10:00:01.300Z`. The sub-workflow returned an 89-row
client-metrics DataTable. The `Use Excel File: client-report.xlsx`
card opened the workbook via OpenXML (no COM-forcing properties).
On open, the runtime detected the Purview label
`Confidential - Client Data` and logged it. The card then
inspected its own configuration for SensitivityLabel /
SensitivityOperation, found both `<unset>`, and refused the
acquisition with the canonical BusinessException.

**Why:** Microsoft Purview / Azure Information Protection labels
are enforced at the file-format layer — the label is embedded in
the workbook's OPC package metadata. Any application that writes
to the file must acknowledge the label (preserve it, change it,
or remove it) AND prove it has the AIP rights to do the
acknowledged operation. UiPath's v2.23.4 release added the
SensitivityLabel / SensitivityOperation card properties to expose
this acknowledgement to workflow authors. Pre-v2.23.4 packages
either silently produced wrong data (the label was stripped on
write) OR threw at the AIP layer in a confusing way — the
explicit BusinessException with named label is the v2.23.4+ guard
that makes the requirement visible.

The fix is straightforward: configure the card's two label
properties to match the workbook's label and the workflow's
intent (typically `Keep` to preserve the existing label).

---

**Evidence:**

### Orchestrator (Root cause)
- Failing job: `ExcelClientReportProcess` (key `gg333333-...`) —
  Faulted at `2026-05-30T10:00:04.612Z`.
- Folder: `ClientReports` (key `f00ddddd-3333-4444-5555-666677778888`).
- Host: `MOCK-HOST`. Robot user: `UIPATH\AUTOMATION1`.
- Error (verbatim from `or jobs get`):
  `UiPath.Excel.BusinessException: The workbook is protected by a
  Microsoft Purview sensitivity label ('Confidential - Client Data')
  that requires explicit handling. The SensitivityLabel and
  SensitivityOperation properties on the Use Excel File activity
  are not configured.` Stack trace through
  `UiPath.Excel.Activities.Business.UseExcelFile.ValidateSensitivityLabel(WorkbookLabel, SensitivityLabelOperation)`
  and `UseExcelFile.OnExecute(NativeActivityContext)`.
- Faulting activity: `UseExcelFile_1`
  (`Use Excel File: client-report.xlsx`) at `Main.xaml`.

### Workflow source (decisive)
- `Main.xaml`:
  - `<uix:UseExcelFile WorkbookPath="C:\Robot\Data\client-report.xlsx" ReferenceName="ReportScope" ...>`
    — **no `SensitivityLabel` or `SensitivityOperation`
    properties set on the card**. Both are absent from the
    XAML element attributes.
  - Body contains `<uix:ExcelWriteRange SheetName="Metrics"
    StartingCell="A1" DataTable="[dtClientMetrics]"
    ExcludeHeaders="False" ...>` — a write activity, which is
    why the label enforcement triggers.

### Package version (decisive)
- `project.json`: `"UiPath.Excel.Activities": "[2.24.7]"` — well
  above the v2.23.4 threshold where the SensitivityLabel /
  SensitivityOperation properties were introduced. The card
  supports the properties; the workflow just doesn't use them.

### Job logs (decisive)
- `Use Excel File: client-report.xlsx — opened workbook (OpenXML provider). Package version: UiPath.Excel.Activities 2.24.7 (>= 2.23.4: SensitivityLabel and SensitivityOperation properties available).`
- `Use Excel File: client-report.xlsx — Microsoft Purview sensitivity label detected on workbook: 'Confidential - Client Data' (label ID: 8c2f3a4d-1234-5678-abcd-aip00client01). This label requires programmatic acknowledgement before write operations.`
- `Use Excel File: client-report.xlsx — card property inspection: SensitivityLabel=<unset>, SensitivityOperation=<unset>. Both properties are required for write operations against labeled workbooks under v2.23.4+.`
- `Use Excel File: client-report.xlsx — UiPath.Excel.BusinessException: The workbook is protected by a Microsoft Purview sensitivity label ('Confidential - Client Data') that requires explicit handling.`

The four-line chain pins the failure: package supports the
properties + label detected + card properties unset + exception
naming the label. The agent doesn't need to infer the AIP
semantics — the runtime logs them explicitly.

### Cross-check — what this is NOT
- Not branch 1 (Excel not installed): the workbook opened via
  OpenXML — no Excel COM needed for this acquisition path. The
  failure is at sensitivity-label validation, AFTER successful
  workbook open.
- Not branch 2 (empty / illegal WorkbookPath): the path resolved
  cleanly and the workbook opened.
- Not branch 3 (COM/RPC race): no `RPC_E_*` HRESULTs, no
  cross-scope sequence — just a single card.
- Not branch 4 (child activity outside scope): the Write Range
  is correctly nested inside the Use Excel File card.

---

**Recommended Fix (Resolution):**

### Primary fix — configure SensitivityLabel and SensitivityOperation

The workflow needs to declare its intent for the label
explicitly. The simplest case (workflow reads / writes data,
keeps the existing label) uses `Keep` as the operation:

1. Open `Main.xaml`.
2. On `UseExcelFile_1`, set the card's properties:
   - **`SensitivityLabel`**: `"Confidential - Client Data"` (the
     exact label name as it appears in Microsoft Purview — must
     match verbatim, including case and any em-dashes /
     hyphens).
   - **`SensitivityOperation`**: `Keep` (preserve the existing
     label on the workbook — the workflow doesn't change the
     label, it just writes data underneath it).
3. Save and re-run.

After this fix, the card opens the workbook, acknowledges the
label via `Keep`, and proceeds with the write. The label remains
on the file post-write.

### Alternative — configure for label upgrade or downgrade

If the workflow's intent IS to change the label (e.g., promote
to "Highly Confidential" because new data lands in the sheet),
use `Apply` with the target label name. Requires the Robot user
to have AIP rights to apply that specific label.

If the workflow needs to REMOVE the label (rare), use `Remove`.
Requires the Robot user to have label-remove rights in Purview.

### Verify the Robot user has AIP rights

If after configuring the properties the workflow still fails with
a different (auth-related) error from the AIP layer, the Robot
user lacks the rights for the operation. Check Microsoft Purview:

1. Sign into the Microsoft Purview admin center.
2. Navigate to Information Protection → Labels.
3. Select the `Confidential - Client Data` label.
4. Check the "Users and groups" assignment for the label's
   policy. The Robot user (or a group it belongs to) must be in
   the allow-list for the operation being performed.

Coordinate with the Microsoft 365 admin to add the Robot user if
missing.

### Anti-pattern (do NOT use)

Do NOT downgrade `UiPath.Excel.Activities` to a pre-v2.23.4
version "to silence the error." Pre-v2.23.4 packages handle
labeled workbooks INCORRECTLY — either silently stripping the
label on write (a compliance violation that can leak data into
unlabeled files) or throwing a confusing AIP-layer error
elsewhere. The v2.23.4+ explicit error is the FIX, not the
symptom. Downgrading reintroduces the data-leak bug the
explicit error was added to prevent.

This is the playbook's anti-pattern #4.

### Prevention

- For workflows that touch AIP-labeled workbooks, pin
  `UiPath.Excel.Activities` to v2.23.4 or newer in
  `project.json`. Document the requirement in workflow comments.
- Document the workbook's expected label in the workflow's
  README / comments. When the label changes (e.g., a policy
  rename from "Confidential" to "Confidential - Client Data"),
  the workflow needs an update; surfacing the dependency makes
  the rename impact visible.
- For workflows that operate on multiple labeled workbooks
  with different labels, parameterize `SensitivityLabel` /
  `SensitivityOperation` per workbook — don't hard-code the
  label name unless the workflow targets a single file.
- Coordinate Robot user provisioning with the Microsoft 365 /
  Purview admin. Robot users should have the minimum AIP rights
  needed for the operations they perform — typically `Keep`
  rights for read/write workflows on existing-labeled files,
  `Apply` rights for labeling new files, `Remove` rights for
  unusual workflows that downgrade.
- For workflows where label handling isn't part of the
  workflow's purpose (e.g., a workflow that just reads
  unprotected data and the labeling is a future concern), still
  set `SensitivityOperation=Keep` defensively. If a workbook
  gains a label later, the workflow continues to work; if you
  leave the property unset, the workflow breaks the moment
  someone applies a label.
