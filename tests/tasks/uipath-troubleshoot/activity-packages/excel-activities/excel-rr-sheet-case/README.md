# Excel Read Range — Sheet Name Case Mismatch on OpenXML

This scenario reproduces a Read Range failure where the configured
`SheetName` differs from the actual sheet only in letter casing,
and the activity runs on the OpenXML provider (case-sensitive). The
job ends with:

```
UiPath.Excel.BusinessException: The sheet with the name 'data' does not exist.
```

## What this scenario uncovers

**Root Cause:** Workflow configured `SheetName: "data"` (lowercase)
on the Read Range activity. The workbook's actual sheet is `Data`
(capital D). The workflow uses `Use Excel File` (modern scope) with
no `ReadFormatting`, `EditPassword`, or macro-related properties —
the runtime uses the OpenXML provider, which is **case-sensitive**
in sheet name lookups. The agent must:

1. Match the playbook (BusinessException fingerprint).
2. Read the job logs and find the `Get Workbook Sheets` output
   showing `["Sheet1", "Data", "Summary"]`.
3. Read workflow source and see that the scope is `Use Excel File`
   with no COM-forcing properties.
4. Conclude: case-mismatch branch — `"data"` vs `"Data"` only
   differs in case, and the active provider (OpenXML) is
   case-sensitive.
5. Explain the user's "worked yesterday on my dev machine" clue:
   the dev machine has Excel installed → COM provider →
   case-insensitive; the Robot host has no Excel → OpenXML →
   case-sensitive.

This maps to:
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/read-range-sheet-not-found.md`
(the "Case mismatch under the OpenXML provider" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | `ExcelDailyImport` project — `Use Excel File` (no COM-forcing properties) → `Get Workbook Sheets` (logs result) → `Read Range "data"` (fails) |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

The expected investigation chain: `folders list-current-user` →
`jobs list --state Faulted` → `jobs get` → `jobs logs` (reveals
actual sheets list) → workflow source inspection (identifies
`Use Excel File` scope + no COM-forcing properties → OpenXML
provider).

> **Note on fixtures.** Synthetic. The job key, folder key,
> workbook path are placeholders — the test grades whether the
> agent surfaces the case-mismatch branch with both the casing
> evidence AND the provider-behavior reasoning.
