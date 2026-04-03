# Genome: Email Triage

> Classify incoming emails by intent and urgency, then route to the right team or trigger downstream automations.

## Overview

A front-door automation for shared mailboxes that receive mixed-intent emails (support requests, order inquiries, complaints, spam). Classifies each email, extracts key entities, and routes it — either by forwarding to the right team, creating a ticket, or triggering another automation.

## Target Applications

| Application | Role | Notes |
|-------------|------|-------|
| Email (Outlook/Gmail) | Input source | Shared mailbox |
| Ticketing system | Routing target | ServiceNow, Jira, Zendesk — optional |
| Orchestrator Queues | Routing target | For triggering downstream automations |

## Configuration Questions

1. Which mailbox to monitor?
2. What are the email categories? (e.g. support request, order inquiry, complaint, invoice, spam)
3. For each category, what's the routing action? (forward to team, create ticket, add to queue, archive)
4. Should attachments be preserved and forwarded?
5. Is there a priority/urgency model? (e.g. VIP senders, keywords like "urgent", SLA-bound)

## Workflow

1. **Trigger**: Poll inbox on schedule or event-driven.
2. **Read**: Extract sender, subject, body, attachments, timestamp.
3. **Classify**: Determine category and urgency. Use rules first (sender domain, subject keywords), fall back to AI classification for ambiguous cases.
4. **Extract entities**: Pull relevant entities based on category — order numbers, account IDs, product names, dates.
5. **Route**:
   - Forward to team distribution list, or
   - Create ticket in ticketing system with extracted fields, or
   - Add to Orchestrator queue for downstream automation, or
   - Archive (spam/irrelevant)
6. **Tag**: Mark email as processed (move to folder, add label, mark read).
7. **Log**: Record classification, routing action, and confidence for audit.

## Business Rules

- VIP sender list gets auto-escalated to high priority regardless of content
- Emails with attachments > 10MB: flag for manual review rather than forwarding
- Multi-intent emails (e.g. complaint + order inquiry): route to primary category, note secondary in ticket
- Auto-reply to sender with acknowledgment if configured

## Error Handling

- Classification confidence below threshold: route to a "needs review" folder instead of guessing
- Ticketing system down: queue locally and retry on next run
- Malformed emails (no body, encoding issues): log and skip

## Acceptance Criteria

- [ ] Correctly classifies sample emails across all configured categories
- [ ] Routes each category to the correct destination
- [ ] Extracts order numbers / account IDs from email body
- [ ] Escalates VIP sender emails to high priority
- [ ] Handles an email with no body without crashing
- [ ] Produces an audit log of all classifications and routing actions

## Complexity

simple

## Tags

email, triage, classification, routing, Outlook, Gmail, ServiceNow, Jira, queue
