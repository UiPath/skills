# Final Resolution

---

**Root Cause:** The workbook
`C:\Robot\Data\sales-2026-05.xlsx` is protected by a Microsoft
Purview / Azure Information Protection sensitivity label
(`Confidential\Limited Access`). The label policy grants permission
to the workbook owner's interactive user identity but NOT to the
Robot user (`UIPATH\AUTOMATION1`). When the `Use Excel File`
activity opens the file under the Robot's identity, the label's
encryption / policy engine refuses programmatic access; the
activity's parsing code receives a null reference where it expected
workbook content, and `NullReferenceException` fires inside the
activity.

The user's "Confidential banner at the top" observation is the
diagnostic. They see the banner when they double-click the file in
Explorer because their interactive identity has the label
permission; the Robot identity does not.

**What went wrong:** Failing job
`aa111111-bbbb-cccc-dddd-eeeeffffaaaa` opened the workbook
successfully (no `IOException`, no `FileNotFoundException`) but
failed mid-parse with a bare `NullReferenceException` and no cell /
sheet pointer in the stack trace. The `or jobs logs` Trace entry
from `Use Excel File` includes the label name in its content-
inspection line:

```
Use Excel File: sales-2026-05.xlsx -- workbook opened (sensitivity label: 'Confidential\Limited Access'; encryption: enabled; access principal: UIPATH\AUTOMATION1; decision: AccessDenied)
```

The `decision: AccessDenied` for the Robot principal is the
authoritative evidence: the file opened from the filesystem's
perspective but the Purview / AIP layer refused programmatic
content access. The downstream parser then null-deref'd on the
empty workbook handle.

**Why:** Sensitivity labels with Limited-Access policies enforce
per-identity encryption. The label's policy enumerates the
identities (users, groups, automation accounts) that may decrypt
the content. An identity not in the policy receives an empty /
unauthorized workbook handle from the AIP integration; the
activity's parser does not anticipate this case and surfaces a
generic NRE rather than a label-specific error.

---

**Evidence:**

### Orchestrator (Root cause)
- Failing job: `ExcelDailyImport` (key `aa111111-...`) -- Faulted at
  `2026-05-20T08:00:02.812Z`.
- Folder: `ExcelImports` (key `f0011111-2222-3333-4444-555566667777`).
- Host: `MOCK-HOST`, runtime type `Unattended`. Robot user:
  `UIPATH\AUTOMATION1`.
- Error (verbatim from `or jobs get`):
  `System.NullReferenceException: Object reference not set to an
  instance of an object.` Stack trace points inside
  `UiPath.Excel.Activities.UseExcelFile.OnExecuteAsync`. No cell
  address, no sheet name, no range expression.
- Faulting activity: `UseExcelFile_1` (`Use Excel File`) at
  `Main.xaml`.

### Workflow source (rules out other branches)
- `Main.xaml`: `<uix:UseExcelFile WorkbookPath="C:\Robot\Data\sales-2026-05.xlsx" .../>`
  -- absolute literal path on the local C: drive. Not relative,
  not a mapped drive, not UNC, not OneDrive.
- `Range: ""` (no named-range reference) -- rules out branch 3
  (broken named range).
- No `ReadFormatting`, `EditPassword`, or macro-related properties
  set -- the runtime uses the OpenXML provider; but this is true
  for all `Use Excel File` cases and is not the specific cause
  here.

### Job logs (decisive)
- `Use Excel File: sales-2026-05.xlsx -- workbook opened (sensitivity label: 'Confidential\Limited Access'; encryption: enabled; access principal: UIPATH\AUTOMATION1; decision: AccessDenied)`
- The activity's content-inspection layer recognized the label
  but the Robot user is not in the label's allow list. The
  `decision: AccessDenied` is the smoking gun.

### User clue (decisive)
- "There's a 'Confidential' banner at the top." Interactive users
  with the label permission see a Purview / AIP banner on the
  workbook when they open it. The user observing this banner
  confirms the workbook IS labeled, which combined with the Robot
  user's `AccessDenied` is the full diagnosis.

### Cross-check -- what this is NOT
- Not branch 2 (structural corruption): Excel itself opens the
  file fine for the user; no "Repaired" dialog reported. The
  XLSX structure is intact -- the label encryption sits on top
  of valid structure.
- Not branch 3 (named-range): workflow source uses an empty
  `Range` (used-range read); no named-range reference.
- Not branch 4 (unsupported OpenXML feature): the user can open
  the file in Excel without compatibility warnings; the issue
  is not parser feature support but label-policy enforcement.
- Not branch 5 (heavy formatting / scale): no scale clues; the
  file is presumably normal-sized; the NRE fires at open, not
  late in parsing.

---

**Recommended Fix (Resolution):**

### Primary fix -- grant the Robot user permission for the label

In Microsoft Purview admin center:

1. Navigate to: **Information Protection -> Labels -> Policies**.
2. Open the policy that publishes the `Confidential\Limited Access`
   label.
3. Add the Robot user `UIPATH\AUTOMATION1` (or an automation group
   it belongs to, such as `Service-Accounts-Automation`) to the
   policy's published-to list AND to any encryption / access
   permissions associated with the `Confidential\Limited Access`
   label.
4. Wait for label policy propagation (typically minutes; up to
   24h in some tenants).
5. Re-run the job to confirm.

### Alternative -- have the workbook owner remove or lower the label

If granting Purview permission to automation accounts is not
permitted by tenant policy:

1. The workbook owner opens the file in Excel.
2. **Home -> Sensitivity (or Insert -> Sensitivity)** -> choose a
   less-restrictive label (e.g., `Internal` rather than
   `Confidential\Limited Access`) OR `Remove Label`.
3. Save the file. The workflow can now read it via the Robot
   identity.

### Long-term (prevention)

- Do not classify automation-consumed workbooks with sensitivity
  labels that exclude the Robot identity. The tenant should
  define an `Automation Accounts` group and a documented
  exemption policy: any label intended to coexist with automation
  must include the group.
- Document the label-permission requirement in the workbook's
  publishing contract; the publisher must apply only labels that
  the consuming Robot identity can decrypt.
- For workbooks where the label MUST exclude automation, switch
  the workflow to a different surface: SharePoint cloud reads
  via the `o365-activities` package can use a service principal
  identity that the label policy can grant, sidestepping the
  per-Robot-host identity problem.

### Validation at job start (prevention)

The agent should consider adding a label-check at job start (a
one-line `Get Workbook Sheets` smoke test on the workbook). When
the label-permission issue exists, the smoke test fails with the
same NRE -- but immediately, with a clear "label / encryption /
access denied" log message that operators can read in seconds
rather than scrolling through a full job trace.
