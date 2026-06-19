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

### Agentic output review
An AI agent produced a document, draft, classification, or recommendation — a human must verify it before the result is used or published.

| Signal phrases | Examples |
|---|---|
| "review AI-generated content", "human verifies before sending" | Agent-drafted emails, RCA reports, meeting summaries |
| "check before publishing", "validate AI output" | AI-written case notes, support ticket responses |
| "human in the loop for AI decisions" | Any LLM output going to a system of record or customer |

**Insertion point:** After the agent node, before the downstream action that consumes the output.

---

### IT / change management approval
A change request or access request needs human authorization before the automation executes it.

| Signal phrases | Examples |
|---|---|
| "CAB approval", "change request", "change window" | IT change management (ServiceNow, Jira Service Management) |
| "access request", "provision access", "grant permission" | Identity and access management workflows |
| "runbook approval", "deployment sign-off" | DevOps release gates |

**Insertion point:** After the automation prepares the change record, before it applies the change.

---

### HR and offer / contract workflows
A document or decision with legal or HR significance must be reviewed before it is sent to a third party.

| Signal phrases | Examples |
|---|---|
| "offer letter", "employment contract", "onboarding approval" | HR hiring workflows |
| "termination review", "performance decision" | HR case management |
| "contract terms", "counter-sign", "legal review gate" | Procurement, vendor onboarding |

**Insertion point:** After document generation, before the document is dispatched.

---

### Customer communication approval
An automation is about to send a message on behalf of a person or brand — a human must review tone, accuracy, or content before it goes out.

| Signal phrases | Examples |
|---|---|
| "approve before sending", "review draft email", "check before posting" | Customer support responses, marketing emails |
| "agent-written reply", "draft response" | Helpdesk, CRM follow-ups |

**Insertion point:** After the draft is generated, before the send/post action.

---

### Financial transaction approval
A monetary action above a threshold or of a certain type requires human sign-off.

| Signal phrases | Examples |
|---|---|
| "above threshold", "over limit", "exceeds budget" | PO approval, expense reimbursement over limit |
| "wire transfer", "payment release", "credit note" | AP/AR workflows |
| "price override", "discount approval" | Sales quote approval |

**Insertion point:** After the automation determines the transaction details, before it submits the payment or posts the entry.

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
