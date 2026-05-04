---
name: uipath-automation-discovery
description: >
  Discover internal automation opportunities for any company by investigating
  how employees actually work. Mines messaging (Slack/Teams), email (Gmail/Outlook),
  wikis (Confluence/Notion/SharePoint), issue trackers (Jira/Linear/ServiceNow),
  CRMs (Salesforce/HubSpot), HRIS (Workday/BambooHR), ERP (SAP/NetSuite),
  and any other accessible system of record. Identifies behavioral patterns,
  single points of failure, and proven models that can be replicated.
  Analyzes company strategy to find strategic gaps. Produces a prioritized
  report with 4 tiers. Use when asked to "discover automations", "find
  automation opportunities", "what should we automate", "internal automation
  audit", "automation discovery", "process improvement analysis", "find manual
  work to automate", or when asked about improving internal productivity,
  reducing operational costs, or finding repetitive work.
---

# Automation Discovery

Investigate how employees actually work, then identify and prioritize internal
automation opportunities backed by real behavioral evidence.

## When to Use This Skill

- User asks to **discover automation opportunities** in their company
- User wants to **find manual work to automate** across departments
- User asks "what should we automate?" or "where are the automation opportunities?"
- User wants an **internal automation audit** or process improvement analysis
- User wants to **reduce operational costs** by finding repetitive work
- User asks about **improving internal productivity** with automation

## Critical Rules

1. **Never assume — always ask first.** Complete the full intake (Phase 0) before mining. You need company context, tool access, org structure, and scope agreement.
2. **Verify access before mining.** Test each data source with a minimal read-only operation. If access fails, note it and move on — don't block discovery.
3. **Evidence over opinion.** Every opportunity (Tiers 1-3) must cite a specific source, quantitative metric, and affected person or team. No unsupported claims.
4. **Replication is always Tier 1.** A proven model working in one area that could replicate elsewhere is the highest-value finding. Always lead with these.
5. **Share interim findings after every phase.** Don't disappear for hours. Check in with a brief summary and ask if the user wants to adjust scope.
6. **Graceful degradation.** Work with whatever access is verified. Even messaging channels alone can yield 15+ opportunities.
7. **SPOFs are urgent.** A single person answering thousands of questions is a crisis — always flag these.

## Phase 0: INTAKE (interactive)

Build a complete picture before mining. Ask — don't assume.

### 0A. Company Context

Elicit from the user:
- What does the company do? (industry, size, business model)
- Relationship with automation today? (dedicated COE? ad-hoc? nothing?)
- Known pain points? (capture as hypotheses to validate, not conclusions)

### 0B. Tool & System Inventory

Ask explicitly for each category. Build this table:

```
| Category       | Tool             | Access Method        | Verified? |
|----------------|------------------|----------------------|-----------|
| Messaging      |                  | CLI / MCP / browser  |           |
| Email          |                  | CLI / MCP / API      |           |
| Wiki           |                  | MCP / API / browser  |           |
| Issue Tracker  |                  | MCP / API / CLI      |           |
| CRM            |                  | CLI / API / browser  |           |
| HRIS           |                  | API / browser        |           |
| ERP / Finance  |                  | API / browser        |           |
| Code / DevOps  |                  | CLI / API            |           |
| Monitoring     |                  | API / browser        |           |
| Expense/Travel |                  | browser              |           |
| Procurement    |                  | API / browser        |           |
| Calendar       |                  | CLI / API            |           |
| Doc Storage    |                  | CLI / API            |           |
| Internal Search|                  | browser              |           |
```

### 0C. Access Verification

Test each tool with a minimal read-only operation before committing to mine it.
If access fails, note it and move on — don't block discovery on one tool.

Example tests:
- Slack: `slack-cli search "test" -w {workspace}` or MCP `slack_read_channel`
- Confluence: MCP `searchConfluenceUsingCql` with simple CQL
- Jira: MCP `searchJiraIssuesUsingJql` with simple JQL
- Salesforce: `sf data query` or API test
- Gmail: `gws-gmail` or MCP read
- GitHub: `gh api user`

### 0D. Org Structure & Scope

- Point me to an org chart? (wiki page, HRIS, etc.)
- Complete department list (including shared services: IT, HR, Finance, Legal, Procurement)
- Any departments off-limits?
- Key people to watch? (executives, ops leads)

### 0E. Output & Audience

- Where should the report go? (Confluence, Notion, Google Docs, local file)
- Who is the audience? (leadership, COE, department heads)
- Draft or publish directly?

### 0F. User Hypotheses

Capture what the user already suspects as search targets, not conclusions:
- "I think expense is broken" → search for evidence in Phase 1
- "Sales forecasting takes too long" → look for signals

### 0G. Scope Control

Agree on depth before starting:
- **Quick scan** (~1 hour): Messaging channels + wiki only. Top 10 findings.
- **Standard** (~3 hours): All verified sources. Full department map. 20+ findings.
- **Deep dive** (~6+ hours): Per-department behavioral agents. PDD deep reads. Strategic analysis. 30+ findings.

Share interim findings after each phase. Ask before going deeper.

## Phases 1-4 Overview

```
Phase 1: MINE     → Gather raw data from all verified sources
Phase 2: ANALYZE  → Extract patterns, SPOFs, replicable models, gaps
Phase 3: REFLECT  → Layer on business strategy for strategic gaps
Phase 4: REPORT   → Produce prioritized report with 4 tiers
```

## Phase 1: MINE

Cast a wide net. Prioritize by signal density. Use parallel agents.

See [references/mining-guides.md](references/mining-guides.md) for detailed
per-source guidance on what to look for and how to search.

**Source priority when time is limited:**
1. Messaging help channels — highest signal, fastest to mine
2. Email patterns — reveals hidden recurring work
3. CRM/ERP — reveals structured process bottlenecks
4. Wiki/docs — reveals existing automation landscape
5. Issue tracker — reveals service desk patterns
6. HRIS — reveals people-process friction
7. Web research — reveals strategic gaps

**Graceful degradation:** Work with whatever access is verified. Even messaging
channels alone can yield 15+ opportunities. Each additional source adds depth,
not changes the methodology.

**Checkpoint:** After Phase 1, share a raw signal summary with the user:
"I found X help channels, Y existing automation projects, Z departments.
Want me to go deeper on anything before I analyze?"

## Phase 2: ANALYZE

Transform raw data into structured findings.

### 2A. Behavioral Patterns

Per department, answer: What's manual? What questions repeat? What approvals
stall? What reports are compiled by hand? What data is swivel-chaired between
systems? What handoffs break? What scheduled tasks are done by humans?

### 2B. Single Points of Failure

Identify individuals who are sole responders. If they're out, the process stops.
```
| Person | System/Channel | Role | Risk |
```
These are the highest-urgency targets.

### 2C. Proven Replicable Models

The most important finding. Look for automation already working in one area
that could replicate to others:
- Bot in one channel but not others
- Auto-routing in one team but manual elsewhere
- Dashboard auto-generated for one dept but compiled by hand for another
```
| Working Model | Where It's Missing | Addressable Volume |
```
This is always Tier 1.

### 2D. Department Coverage Map

```
| Department | Existing Automations | Key Gap |
```
Flag ZERO-coverage departments as biggest blind spots.

### 2E. Process Deep Reads

For promising existing projects, extract: pain point, manual process today,
volume/frequency, ROI if documented, systems involved, dev status.

**Checkpoint:** Share analysis summary with user before reflecting:
"Here are the top patterns, SPOFs, and replicable models. Anything surprise you?
Anything I should investigate further?"

## Phase 3: REFLECT

Identify gaps behavioral data won't reveal.

### 3A. Business Context

Research via web search, investor docs, or internal strategy pages:
revenue, growth, strategic priorities, competitive challenges, key metrics.

### 3B. Strategic Gaps

For each strategic priority: "Is there an internal automation that accelerates this?"

| Priority | Potential Automation |
|---|---|
| Revenue growth | Lead scoring, pipeline acceleration, renewal prediction |
| Cost reduction | Self-service portals, report automation, process standardization |
| Customer retention | Health scoring, churn prediction, proactive outreach |
| Market expansion | Localization, compliance automation, partner enablement |
| M&A integration | Migration tracking, data reconciliation, org mapping |
| Compliance | Audit trails, policy enforcement, automated reporting |
| Talent retention | Onboarding, engagement monitoring, career pathing |
| Product-led growth | Usage monitoring, community management, certification automation |

### 3C. Dogfooding Check

If the company sells automation/productivity/AI/workflow tools:
does it use its own product? Is there a coverage metric? What's the narrative
gap between what they sell and what they do internally?

## Phase 4: REPORT

Produce a prioritized report in the user's preferred platform.
See [references/report-template.md](references/report-template.md) for structure.

### Tier Definitions

**Tier 1 — Replicate Proven Models**: Already working somewhere, replicate it.
Lowest risk, highest ROI. Always the headline.

**Tier 2 — Behavioral Automations**: Manual patterns observed in data.
Evidence-backed. Medium effort.

**Tier 3 — Operational Gaps**: Department blind spots from coverage mapping.
Needs scoping.

**Tier 4 — Strategic**: Driven by business strategy, not observed behavior.
Needs executive sponsorship.

### Quality Bar

- Every opportunity has specific evidence (source, metric, person name)
- No unsupported claims (except Tier 4, which references strategy docs)
- SPOFs identified by name
- Replicable models highlighted as Tier 1
- Department map is complete (all departments, not just gapped ones)
- ROI benchmarks from existing projects included
- Strategic analysis ties to real financials

## Execution Strategy

Parallelize aggressively:
- 3 agents simultaneously for Phase 1: messaging, wiki/tracker, systems of record
- Department-specific behavioral agents in Phase 2
- Multiple process doc reads in parallel
- Web research concurrent with internal mining

## Reference Navigation

- [references/mining-guides.md](references/mining-guides.md) — Per-source search guidance (load during Phase 1)
- [references/report-template.md](references/report-template.md) — Output structure and evidence standards (load during Phase 4)
