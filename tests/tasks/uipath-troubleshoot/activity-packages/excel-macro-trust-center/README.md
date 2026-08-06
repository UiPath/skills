# Excel Execute Macro — Trust Center Blocks Macros On Robot Host

This scenario reproduces an Execute Macro failure with the canonical
"Cannot run the macro..." COMException — same error string as the
macro-not-found case, but here the macro IS present in the
workbook. Excel's Trust Center policy on the Robot host's user
profile blocks macro execution. The job ends with:

```
System.Runtime.InteropServices.COMException: Cannot run the macro 'Module1.ProcessData'. The macro may not be available in this workbook or all macros may be disabled.
```

## What this scenario uncovers

**Root Cause:** The macro `Module1.ProcessData` exists in the
workbook's VBA project (confirmed by the activity's VBA-module
enumeration in job logs). The error's wording covers two cases:
"macro not in workbook" (branch 1) OR "all macros disabled"
(branch 5) — both produce identical COMException text. Here, the
second case applies: Excel's Trust Center on the Robot host's user
profile is configured to disable macros without notification, and
the workbook is neither in a Trusted Location nor signed by a
trusted publisher.

The user's "works on my dev machine" clue is the diagnostic:
developer Excel has permissive Trust Center defaults (or trusted
locations covering the dev workspace); Robot host's Excel under
the `UIPATH\AUTOMATION1` user does not.

The agent must distinguish branch 5 from branch 1 by combining:
1. **VBA enumeration evidence** — job logs show the macro IS
   present in the workbook (rules out branch 1).
2. **User clue** — "works on dev machine" is the canonical
   per-host Trust Center divergence signal.

CLI cannot inspect the Robot host's Trust Center settings; agent
must hand the user host-side inspection commands.

This maps to:
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/execute-macro-failures.md`
(the "Macros disabled by Trust Center policy" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `process/` | `ExcelMacroProcess` project — `Use Excel File` → `Execute Macro: Module1.ProcessData` |

The expected investigation chain: `folders list-current-user` →
`jobs list --state Faulted` → `jobs get` ("Cannot run the macro"
COMException) → `jobs logs` (VBA enumeration confirms macro IS
present) → workflow source (confirms configured MacroName matches
enumeration entry) → conclude branch 5 (since macro presence rules
out branch 1) → recommend host-side Trust Center inspection.

> **Note on fixtures.** Synthetic. The macro names and Robot user
> are placeholders representative of a real Trust Center
> deployment. The test grades whether the agent surfaces the
> Trust Center / Trusted Locations branch using the combination
> of VBA-enumeration evidence + the dev-machine user clue.

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's host-side protected mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
