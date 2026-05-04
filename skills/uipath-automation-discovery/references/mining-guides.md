# Mining Guides by Source Type

Detailed guidance for what to look for and how to search each data source.
Load this file during Phase 1 for whichever sources are verified.

## Messaging (Slack, Teams, Google Chat)

The single best source. Help channels are the highest-signal proxy for pain.

**What to look for:**
- All `#help-*` or `#ask-*` channels — capture message counts
- Whether a bot already handles queries in each channel
- Who responds most often (potential SPOF)
- Top 5 repeated question patterns per channel
- Alert/notification channels with undifferentiated noise
- Account/customer channels with manually compiled weekly updates

**Search queries (adapt phrasing per platform):**
```
"can someone help"          → where people get stuck
"manually update"           → manual data entry
"every week I have to"      → recurring manual work
"should automate"           → employee-identified opportunities
"waiting for approval"      → approval bottlenecks
"does anyone know how to"   → knowledge gaps
"is this documented"        → documentation gaps
"how do I"                  → process confusion
"who handles"               → unclear ownership
```

**Pro tip:** Search for team-specific channels beyond `#help-*`. Channels like
`#ops-*`, `#team-*`, `#proj-*` often contain manual coordination patterns.

## Email (Gmail, Outlook)

Reveals patterns invisible in messaging: approval chains, vendor communication,
scheduled manual work, report distribution.

**What to look for:**
- Recurring emails (daily/weekly reports sent manually)
- Approval request threads (forwarded chains = manual routing)
- Vendor/supplier communication (manual order placement, invoice follow-up)
- Auto-forwarding rules (workarounds for missing integrations)
- Calendar invites for recurring "data compilation" or "report review" meetings
- High-volume distribution lists (newsletters, status updates compiled by hand)
- "FYI" emails with attachments that should be in a shared system

**Search queries:**
```
"please find attached the weekly"  → manual report distribution
"updated spreadsheet"              → manual data compilation
"please approve"                   → manual approval routing
"reminder to submit"               → recurring manual process
subject:"weekly report"            → scheduled manual work
subject:"monthly update"           → scheduled manual work
```

## CRM (Salesforce, HubSpot, Dynamics)

Structured workflow data revealing process bottlenecks.

**What to look for:**
- Manual data entry (fields humans fill that could be auto-populated)
- Swivel-chairing (copying data between CRM and other systems)
- Approval workflows and where they stall
- Report/dashboard creation frequency (manual vs. automated)
- Case/ticket routing rules and exceptions
- Lead assignment and follow-up compliance gaps
- Quote-to-close cycle time bottlenecks
- Data hygiene (duplicates, stale records, missing fields)
- Chatter/activity feed patterns (manual status updates)

**Salesforce-specific queries:**
```
sf data query "SELECT Id, Subject, Status FROM Case WHERE Status = 'Escalated'"
sf data query "SELECT Id, StageName, LastModifiedDate FROM Opportunity WHERE StageName = 'Closed Won' AND LastModifiedDate = LAST_N_DAYS:30"
```

## Wiki / Knowledge Base (Confluence, Notion, SharePoint)

**What to look for:**
- Internal automation spaces ("INTAUTO", "COE", "RPA", "automation")
- Process documentation per department (PDDs, SOPs, runbooks)
- Pages mentioning "manual process", "pain point", "bottleneck"
- Org charts and department structure pages
- Existing automation pipeline/backlog/idea list
- Process mining outputs
- Meeting notes with recurring action items never completed

**Confluence CQL examples:**
```
type = page AND text ~ "manual process" ORDER BY lastModified DESC
type = page AND text ~ "automation" AND space = "{space_key}"
type = page AND title ~ "runbook" ORDER BY lastModified DESC
```

## Issue Tracker (Jira, Linear, Asana, ServiceNow)

**What to look for:**
- Internal ops projects and backlogs
- Issues tagged "automation", "process improvement", "manual"
- Service desk request patterns (what employees ask IT/HR/Finance for)
- Recurring ticket types (same request weekly = automation candidate)
- SLA breaches and escalation patterns
- Ticket volume per category over time

**Jira JQL examples:**
```
project = {proj} AND labels = "automation" ORDER BY created DESC
project = {proj} AND type = "Service Request" ORDER BY created DESC
project = {proj} AND status = "Waiting for Support" AND updated < -7d
```

## HRIS (Workday, BambooHR, ADP)

**What to look for:**
- Onboarding/offboarding workflows and manual steps
- Time-off and leave management friction
- Performance review process pain points
- Payroll processing manual interventions
- Benefits enrollment confusion patterns
- Name/email change processes that require multi-system updates
- Headcount reporting manual compilation

## ERP / Finance (SAP, NetSuite, QuickBooks)

**What to look for:**
- Manual journal entries and reconciliation
- Invoice processing and approval workflows
- Purchase order creation and vendor management
- Month-end/quarter-end close procedures
- Expense report processing and reimbursement delays
- Intercompany transactions requiring manual coordination
- Tax filing and compliance reporting
- Revenue recognition manual steps

## Code / DevOps (GitHub, GitLab, Azure DevOps)

**What to look for:**
- CI/CD pipeline manual steps (approvals, environment promotion)
- Deployment checklists maintained manually
- Release notes compiled by hand from commit logs
- On-call rotation management (manual or automated?)
- Incident postmortem → action item tracking gaps
- Feature flag management manual steps
- Dependency update processes

## Monitoring (Datadog, PagerDuty, Rootly)

**What to look for:**
- Alert channels with undifferentiated noise (high volume, all same severity)
- P1/critical signals buried in noise
- Staging and production alerts mixed in same channel
- Incident response workflows with manual steps
- Post-incident review processes
- SLA tracking and breach notification gaps
