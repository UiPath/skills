# SupplierPaymentHold — Solution Design (approved)

Status: approved for build.

## Process contract

| Variable | Direction | Type | Notes |
|---|---|---|---|
| `invoiceAmount` | input | number | Invoice total |
| `sanctionsCleared` | input | boolean | Unknown until assessed: the caller may omit it or send `null` |
| `outcome` | output | string | `blocked`, `compliance` or `scheduled` |

## Elements

| Id | Type | Name | Behaviour |
|---|---|---|---|
| `Start_InvoiceReceived` | Start event | Invoice received | Takes the inputs |
| `Task_NormalizeInvoice` | Script task | Normalize invoice | Rounds `invoiceAmount` to 2 decimals into `normalizedAmount` |
| `Gateway_SanctionsStatus` | Exclusive gateway | Sanctions status | BR-01 |
| `Task_BlockPayment` | Script task | Block payment | Sets `outcome` to `blocked` |
| `End_PaymentBlocked` | End event | Payment blocked | |
| `Task_RouteToCompliance` | Script task | Route to compliance review | Sets `outcome` to `compliance` |
| `End_ComplianceReview` | End event | Compliance review | |
| `Gateway_AmountCheck` | Exclusive gateway | Amount over 10000 | BR-02 |
| `Task_ApplyDualControl` | Script task | Apply dual-control flag | Sets `dualControl` to `true` |
| `Task_SchedulePayment` | Script task | Schedule payment | Sets `outcome` to `scheduled` |
| `End_PaymentScheduled` | End event | Payment scheduled | |

## Flows

| From | To | Condition |
|---|---|---|
| Invoice received | Normalize invoice | |
| Normalize invoice | Sanctions status | |
| Sanctions status | Amount over 10000 | BR-01: cleared |
| Sanctions status | Block payment | BR-01: not cleared |
| Sanctions status | Route to compliance review | BR-01: unknown |
| Block payment | Payment blocked | |
| Route to compliance review | Compliance review | |
| Amount over 10000 | Apply dual-control flag | BR-02: over 10000 |
| Amount over 10000 | Schedule payment | BR-02: otherwise |
| Apply dual-control flag | Schedule payment | |
| Schedule payment | Payment scheduled | |

## Business rules

| Id | Element | Rule |
|---|---|---|
| BR-01 | `Gateway_SanctionsStatus` | `sanctionsCleared` is `true`: continue to the amount check. `false`: block payment. Unknown until assessed: a missing or `null` value goes to compliance review, never toward payment. |
| BR-02 | `Gateway_AmountCheck` | `normalizedAmount` over 10000 needs the dual-control flag before scheduling; otherwise schedule directly. |
| BR-03 | — | Invoices from a Tier 3 supplier need an extra check before scheduling. [SME REVIEW: the check is not defined yet] |
