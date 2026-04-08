# HITL Business Pattern Recognition Guide

Use this guide to decide whether a business process needs a Human-in-the-Loop node, and where to place it — even when the user has not explicitly asked for one.

---

## When to Recommend HITL

Look for these signals in the business description or process context:

### Approval gate
The automation produces something that requires sign-off before it can proceed.

| Signal phrases | Examples |
|---|---|
| "approve", "sign off", "authorize", "get approval" | Invoice approval, PO sign-off, budget authorization |
| "four-eyes check", "dual control", "maker-checker" | Financial transactions, compliance workflows |
| "review before posting", "validate before sending" | CRM updates, email campaigns, database writes |

**Insertion point:** After the automation generates the artifact to review, before it takes the action requiring approval.

---

### Exception escalation
The automation hits a case it cannot resolve autonomously and needs a human decision.

| Signal phrases | Examples |
|---|---|
| "if uncertain / low confidence, escalate" | AI agent confidence threshold |
| "edge case", "anomaly", "exception handling" | Fraud alerts, out-of-policy transactions |
| "escalate to manager / supervisor" | Customer service workflows |

**Insertion point:** Inside a conditional branch where the automation detects it cannot proceed alone.

---

### Data enrichment
The automation extracted or generated data that is incomplete — a human must fill in the gaps.

| Signal phrases | Examples |
|---|---|
| "fill in missing fields", "enrich", "complete the record" | Partially extracted invoice data |
| "human validates / corrects" | OCR output verification |
| "needs human input before continuing" | Missing vendor code, unknown cost center |

**Insertion point:** After extraction/generation, before the downstream step that requires complete data.

---

### Compliance and audit checkpoint
A regulation or internal policy requires documented human sign-off.

| Signal phrases | Examples |
|---|---|
| "compliance", "audit trail", "regulatory sign-off" | SOX controls, GDPR consent flows |
| "must be reviewed by", "requires attestation" | Legal review gates, privacy impact assessments |

**Insertion point:** At the mandated checkpoint defined by the regulation or policy.

---

### Write-back validation
An agent or automation is about to write to an external system — a human must confirm the proposed change.

| Signal phrases | Examples |
|---|---|
| "before writing to", "before posting to", "agent writes to ServiceNow / SAP / CRM" | Any write to a system of record |
| "human confirms before agent acts" | Autonomous agent guard rails |

**Insertion point:** Immediately before the write/post action.

---

## When NOT to Recommend HITL

- The process description is fully automated with no decision point (e.g. "process all invoices automatically")
- The human interaction is asynchronous notification only (use email/Slack activity instead)
- The user explicitly says no human review is needed
- The decision can be made by a rule or AI model with sufficient confidence

---

## Proactive HITL Recommendation

If a business description contains any of the above signals but the user has not asked for a HITL, flag it:

> "This process includes [signal]. Before the automation [action], a human should review [data]. I recommend inserting a HITL node here — want me to add it?"

Then proceed to Step 3 (schema design) only after the user confirms.
