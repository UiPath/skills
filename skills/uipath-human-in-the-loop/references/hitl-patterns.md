# HITL Business Pattern Recognition Guide

Decide whether a business process needs a Human-in-the-Loop (HITL) node, and where to place it, even when the user has not explicitly requested one.

## When to Recommend HITL

Recommend HITL when any of these signals appears:

| Signal | Indicators | Insertion point |
|---|---|---|
| **Approval gate** | Approval, sign-off, authorization, four-eyes/dual control/maker-checker, or review before posting or sending; includes invoices, orders, budgets, CRM updates, campaigns, and database writes. | After generating the artifact and before the action requiring approval. |
| **Exception escalation** | Uncertainty, low confidence, edge cases, anomalies, exception handling, or escalation to a manager/supervisor; includes fraud, out-of-policy transactions, and customer cases. | In the branch where automation cannot proceed autonomously. |
| **Data enrichment** | Missing fields, enrichment, record completion, or human validation/correction; includes incomplete extraction, missing vendor codes, and unknown cost centers. | After extraction or generation and before the step requiring complete data. |
| **Compliance and audit checkpoint** | Compliance, audit trail, regulatory sign-off, required review, or attestation; includes financial controls, consent, legal review, and privacy assessments. | At the checkpoint required by regulation or policy. |
| **Write-back validation** | Human confirmation before writing or posting to an external system. | Immediately before the write or post action. |
| **Agentic output review** | Review or validation of AI-generated documents, drafts, classifications, recommendations, case notes, decisions, or responses before sending, publishing, consuming, or recording them. | After the agent node and before the downstream action. |
| **IT/change-management approval** | CAB approval, change requests/windows, access requests, provisioning, permission grants, runbook approval, or deployment sign-off. | After preparing the change or access record and before applying it. |
| **HR, offer, or contract workflow** | Offer letters, employment contracts, onboarding approval, termination or performance decisions, contract terms, counter-signature, or legal review. | After document generation or decision preparation and before dispatch or execution. |
| **Customer communication approval** | Review or approval of an email, post, or agent-written reply before sending or posting. | After draft generation and before the send or post action. |
| **Financial transaction approval** | Threshold or budget overruns, wire transfers, payment release, credit notes, price overrides, or discount approval. | After determining transaction details and before submitting payment or posting the entry. |

## When NOT to Recommend HITL

- The process is fully automated with no decision point, such as processing all invoices automatically.
- The interaction is asynchronous notification only; use an email or Slack activity instead.
- The user explicitly says no human review is needed.
- A rule or AI model can make the decision with sufficient confidence.
- The user asks about **runtime task management**—reassigning, monitoring, cancelling, or checking the status of existing Action Center tasks. Answer with `uip tasks` commands or the Orchestrator UI, not by adding a HITL node. Reassigning a task sitting for days is task administration, not automation authoring.

## Proactive HITL Recommendation

**Never block on this.** If any signal is present and the user has not asked for HITL, state the recommendation and proceed straight to Step 3 (schema design); do not wait for a reply:

> “This process includes [signal]. Before the automation [action], a human should review [data]. I'm inserting a HITL node here — remove it if you don't want it.”