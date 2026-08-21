# Diagnosis — inst-triage-001 (SubProcess_TaxCalc)

## Summary

Instance `inst-triage-001` finished with status **Completed**, but the tax on
the invoice is zero despite a non-zero invoice total. The fault is a subprocess-
scoped variable inside `SubProcess_TaxCalc`, not a process-level variable.

## Findings

### Process-level variables (scope: process)

| Variable | Value |
|---|---|
| runStatus | Completed |
| invoiceTotal | 1200.00 |

These look plausible — the total is correctly carried at the process level.

### Subprocess-scoped variables (scope: SubProcess_TaxCalc)

| Variable | Value |
|---|---|
| taxableBase | 1200.00 |
| taxRate | **0.00** |
| taxAmount | 0.00 |

`taxableBase` is correctly set to `1200.00`. However, `taxRate` resolved to
`0.00` inside the subprocess, which caused `taxAmount` to multiply out to
`0.00`. The tax was never applied.

## Root-cause labels

OFFENDING_VARIABLE: taxRate
OFFENDING_VALUE: 0.00

## Why a Completed run can still be semantically wrong

A **Completed** status in UiPath Maestro BPMN only guarantees that every
token in the process reached a valid end event without hitting a fault,
exception boundary, or incident that forced the runtime to abort. The engine
tracks *control-flow correctness* — did the sequence of gateways and tasks
execute without error? — not *data correctness*. A subprocess can receive a
zero or null input variable, propagate it silently through every activity
inside it, produce an arithmetically valid (but business-incorrect) output such
as `0.00`, and hand that value back to the parent process without triggering
any exception. Because no BPMN fault boundary fires and no incident is raised,
the instance transitions to **Completed** normally. In short, the runtime
engine cannot know that `taxRate = 0.00` is wrong for this business case;
only domain-level assertions (output validation tasks, gateway checks on
`taxAmount > 0`, or post-completion audits) would catch this class of semantic
error before it reaches a stakeholder.
