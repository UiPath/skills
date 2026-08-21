# BPMN Run Diagnosis — inst-triage-001

## Diagnostic Steps

### Step 1 — Context

| Field | Value |
|---|---|
| Instance ID | inst-triage-001 |
| Folder key | folder-public |
| Final status | Completed |
| Reported symptom | Tax on invoice came out wrong |

### Step 2 — Incidents

No incident reads were needed; the run status is `Completed` and the symptom is a semantic data error, not a control-flow failure.

### Step 3 — Runtime Variables

**Process-level scope** (`uip maestro bpmn instance variables inst-triage-001 -f folder-public`):

| Variable | Value |
|---|---|
| runStatus | Completed |
| invoiceTotal | 1200.00 |

Process-level variables look plausible.

**Subprocess scope** (`uip maestro bpmn instance variables inst-triage-001 -f folder-public --parent-element-id SubProcess_TaxCalc`):

| Variable | Value |
|---|---|
| taxableBase | 1200.00 |
| taxRate | **0.00** ← offending value |
| taxAmount | 0.00 (derived from taxRate × taxableBase) |

`taxableBase` is correct (matches `invoiceTotal`). However, `taxRate` was zero, so `taxAmount` computed as zero — no tax was applied to the invoice.

---

## Findings

OFFENDING_VARIABLE: taxRate
OFFENDING_VALUE: 0.00

---

## Why a Completed Run Can Still Be Semantically Wrong

A `Completed` status only proves that the process's control-flow reached a valid end event without an unhandled fault. The BPMN engine does not validate the *business meaning* of variable values — it has no knowledge that a `taxRate` of `0.00` is incorrect for this invoice context. As long as every task executed and every gateway found a matching sequence-flow condition, the engine reports success. Semantic errors such as a miscalculated rate, a zero written where a non-zero was expected, or a variable that was never populated by an upstream task are invisible to the runtime's completion logic. This is why behavioral mismatches must be investigated by inspecting scoped runtime variables even after a `Completed` run.
