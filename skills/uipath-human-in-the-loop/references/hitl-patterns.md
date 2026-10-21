# HITL Business Pattern Recognition Guide

Decide whether a business process needs a Human-in-the-Loop (HITL) node and where to place it, even without an explicit request.

## When to Recommend HITL

Recommend HITL when the business description or process context contains any of these signals:

- **Approval gate** — "approve", "sign off", "authorize", "get approval", "four-eyes check", "dual control", "maker-checker", "review before posting", or "validate before sending". Examples: invoice approval, PO sign-off, budget authorization; financial transactions, compliance workflows; CRM updates, email campaigns, database writes. Insert after automation generates the artifact and before the action requiring approval.
- **Exception escalation** — "if uncertain / low confidence, escalate", "edge case", "anomaly", "exception handling", or "escalate to manager / supervisor". Examples: AI agent confidence threshold; fraud alerts, out-of-policy transactions; customer service workflows. Insert in the conditional branch where automation cannot proceed alone.
- **Data enrichment** — "fill in missing fields", "enrich", "complete the record", "human validates / corrects", or "needs human input before continuing". Examples: partially extracted invoice data; OCR output verification; missing vendor code, unknown cost center. Insert after extraction/generation and before the downstream step requiring complete data.
- **Compliance and audit checkpoint** — "compliance", "audit trail", "regulatory sign-off", "must be reviewed by", or "requires attestation". Examples: SOX controls, GDPR consent flows; legal review gates, privacy impact assessments. Insert at the checkpoint mandated by regulation or policy.
- **Write-back validation** — "before writing to", "before posting to", "agent writes to ServiceNow / SAP / CRM", or "human confirms before agent acts". Examples: any write to a system of record; autonomous agent guard rails. Insert immediately before the write/post action.
- **Agentic output review** — "review AI-generated content", "human verifies before sending", "check before publishing", "validate AI output", or "human in the loop for AI decisions". Examples: agent-drafted emails, RCA reports, meeting summaries; AI-written case notes, support ticket responses; any LLM output going to a system of record or customer. Insert after the agent node and before the downstream action consuming its output.
- **IT / change management approval** — "CAB approval", "change request", "change window", "access request", "provision access", "grant permission", "runbook approval", or "deployment sign-off". Examples: IT change management (ServiceNow, Jira Service Management); identity and access management workflows; DevOps release gates. Insert after automation prepares the change record and before it applies the change.
- **HR and offer / contract workflows** — "offer letter", "employment contract", "onboarding approval", "termination review", "performance decision", "contract terms", "counter-sign", or "legal review gate". Examples: HR hiring workflows; HR case management; procurement, vendor onboarding. Insert after document generation and before dispatch to a third party.
- **Customer communication approval** — "approve before sending", "review draft email", "check before posting", "agent-written reply", or "draft response". Examples: customer support responses, marketing emails; helpdesk, CRM follow-ups. Insert after draft generation and before the send/post action.
- **Financial transaction approval** — "above threshold", "over limit", "exceeds budget", "wire transfer", "payment release", "credit note", "price override", or "discount approval". Examples: PO approval, expense reimbursement over limit; AP/AR workflows; sales quote approval. Insert after determining transaction details and before submitting payment or posting the entry.

## When NOT to Recommend HITL

- The process is fully automated with no decision point (for example, "process all invoices automatically").
- Human interaction is asynchronous notification only; use an email/Slack activity instead.
- The user explicitly says no human review is needed.
- A sufficiently confident rule or AI model can make the decision.
- The user asks about **runtime task management**—reassigning, monitoring, cancelling, or checking the status of existing Action Center tasks. Answer with `uip tasks` commands or the Orchestrator UI, not by adding a HITL node. For example, "how do I reassign a task sitting for 3 days?" is task administration, not automation authoring; do not recommend a HITL checkpoint.

## Proactive HITL Recommendation

**Never block on this.** If the description contains an above signal without an explicit HITL request, state it and proceed straight to Step 3 (schema design); do not wait for a reply:

> "This process includes [signal]. Before the automation [action], a human should review [data]. I'm inserting a HITL node here — remove it if you don't want it."