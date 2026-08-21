# Diagnosis: inst-triage-001 (folder-public)

## Context
- Instance: `inst-triage-001`, folder: `folder-public`
- Final status: `Completed`
- Stakeholder-reported symptom: tax on the invoice is wrong

## Investigation

**Process-level variables** (`uip maestro bpmn instance variables inst-triage-001 -f folder-public --output json`):

| name | value |
| --- | --- |
| runStatus | Completed |
| invoiceTotal | 1200.00 |

These look plausible at a glance — nothing here signals a problem.

**Subprocess-scoped variables**, scoped to `SubProcess_TaxCalc`
(`uip maestro bpmn instance variables inst-triage-001 -f folder-public --parent-element-id SubProcess_TaxCalc --output json`):

| name | value |
| --- | --- |
| taxRate | 0.00 |
| taxAmount | 0.00 |
| taxableBase | 1200.00 |

`taxableBase` (1200.00) is consistent with the process-level `invoiceTotal`, and
`taxAmount` (0.00) is arithmetically consistent with `taxAmount = taxableBase *
taxRate` — i.e. the subprocess computed correctly given its inputs. The defect
is the input: `taxRate` is `0.00`, which is not a plausible tax rate for a
non-exempt invoice. This zeroed-out rate is what drove the invoice's tax to
0.00, which is the wrong value the stakeholder noticed.

## Conclusion

OFFENDING_VARIABLE: taxRate
OFFENDING_VALUE: 0.00

## Why a Completed status doesn't guarantee correctness

`Completed` only tells you that every token reached an end event along a valid
path — it verifies control flow, not the semantic correctness of the data that
flowed through it. A subprocess can read a bad or default input (here,
`taxRate` sitting at `0.00`, likely an unset/default rate rather than the
correct jurisdictional rate), compute deterministically and without error from
that input, and still finish with a "successful" status. No exception, retry,
or incident is raised because nothing crashed — the math is internally
consistent, just wrong. That's why diagnosing a reported behavioral mismatch
requires inspecting element-scoped runtime variables (not just the top-level
process variables, which looked fine) rather than trusting the run's terminal
status.
