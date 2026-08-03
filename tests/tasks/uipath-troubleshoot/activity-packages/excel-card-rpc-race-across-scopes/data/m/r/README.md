# Use Excel File — COM / RPC Race Across Sequential Scopes

This scenario reproduces a Modern `Use Excel File` failure where two
sequential cards (with `ReadFormatting=True` COM-forcing) race on
the EXCEL.EXE process lifecycle. The first card's scope-end
terminates EXCEL.EXE; the second card tries to reuse the COM
apartment from the dead process. The job ends with:

```
System.Runtime.InteropServices.COMException (0x80010108): The object invoked has disconnected from its clients. (RPC_E_DISCONNECTED)
```

## What this scenario uncovers

**Root Cause:** Two `Use Excel File` cards in sequence, both with
`ReadFormatting=True` forcing COM fallback, with NO outer `Excel
Process Scope` wrapping them. Card 1's scope-end policy terminates
EXCEL.EXE (PID 8472) because there's no Process Scope governing
the lifecycle. Card 2's COM acquisition tries to reuse the dead
process's apartment and hits RPC_E_DISCONNECTED.

The canonical fix is wrapping both cards in an `Excel Process
Scope` — the outer container that governs EXCEL.EXE lifecycle
across inner cards.

This maps to:
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/excel-application-card-failures.md`
(the "COM / RPC failures across scopes" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | `ExcelMultiReportProcess` project — two sequential `<uix:UseExcelFile>` cards (sales-q1.xlsm + sales-q2.xlsm), both with `ReadFormatting=True`, NO outer `<uix:ExcelProcessScope>` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses; the `or jobs logs` Trace entries trace the EXCEL.EXE PID 8472 lifecycle: launch → first scope completes → "No outer Excel Process Scope detected: terminating EXCEL.EXE PID 8472" → second scope tries to reuse the gone apartment → RPC_E_DISCONNECTED |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

The expected investigation chain: `folders list-current-user` →
`jobs list --state Faulted` → `jobs get` (COMException 0x80010108
RPC_E_DISCONNECTED on UseExcelFile_2) → `jobs logs` (PID 8472
lifecycle chain naming the missing Excel Process Scope) → workflow
source review (confirms no outer Process Scope) → conclude branch 3.

> **Note on the anti-pattern trap.** The natural temptation is to
> add a `Delay` between the two cards. The playbook explicitly
> rejects this — the Delay sometimes works by coincidence but the
> race is still there. The test penalizes Delay-as-fix
> recommendations and rewards the Process Scope wrap.

> **Note on fixtures.** Synthetic. The exact PID, COM apartment
> details, and scope-policy log wording are placeholders. The
> test grades whether the agent identifies the missing Process
> Scope as the root cause AND recommends the Process Scope wrap
> (or one of the alternatives: remove COM-forcing properties,
> consolidate workbooks).
