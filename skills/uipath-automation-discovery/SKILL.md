---
name: uipath-automation-discovery
description: "[PREVIEW] UiPath automation discovery — mines Slack/email/wikis/CRM/HRIS/ERP for repetitive work, SPOFs, and replicable models; produces 4-tier prioritized opportunity report with UiPath implementation paths. TRIGGER when: user asks to discover automations, find automation opportunities, run an internal automation audit, or asks what to automate in a UiPath project context. DO NOT TRIGGER when: user is building a specific automation (→uipath-rpa), authoring a Flow (→uipath-maestro-flow), or working with agents (→uipath-agents)."
---

# Automation Discovery

Investigate how employees actually work, then identify and prioritize internal
automation opportunities backed by real behavioral evidence. Produces a
UiPath-ready backlog with recommended implementation paths.

## When to Use This Skill

- User asks to **discover automation opportunities** in a UiPath project context
- User wants to **find manual work to automate** and build a UiPath implementation backlog
- User asks "what should we automate?" while working with UiPath tools
- User wants an **internal automation audit** to feed into UiPath Automation Hub or a UiPath pipeline
- User explicitly invokes `/uipath-automation-discovery`

## Critical Rules

1. **Authorization and privacy first.** Confirm the requester is authorized to analyze the selected systems and employee data. Avoid private channels, DMs, and special-category HR data (payroll, performance reviews) unless explicitly approved. Pseudonymize SPOFs by default (e.g., "Sales Ops Lead A"); use real names only when explicitly authorized. Maintain a `name-mapping.json` workspace file (e.g., `{"Jake Martinez": "IT Lead A"}`) and apply it consistently before any write operation. Ask about jurisdiction constraints (GDPR, works council, internal policy); apply the stricter rule when uncertain.
2. **Never assume — always ask first.** Complete the full intake (Phase 0) before mining. You need company context, tool access, org structure, privacy scope, and scope agreement.
3. **Verify access before mining.** Test each data source with a minimal read-only operation. If access fails, note it and move on — don't block discovery.
4. **Evidence over opinion.** Every opportunity (Tiers 1-3) must cite a specific source, quantitative metric, and affected role or team. No unsupported claims. If a source yields fewer than 5 signals, mark all findings from that source as low-confidence. Do not promote low-confidence findings above Tier 3.
5. **Replication is always Tier 1.** A proven model working in one area that could replicate elsewhere is the highest-value finding. Always lead with these. Never skip the replicable-model search (Phase 2C). Exception: if the replicable model's source has fewer than 5 signals, classify as Tier 1 with a low-confidence flag until corroborated by a second source.

## Workflow Overview

```
Phase 0: INTAKE    → Gather context, verify access, agree on scope and privacy
Phase 1: MINE      → Gather raw data from all verified sources
Phase 2: ANALYZE   → Extract patterns, SPOFs, replicable models, gaps
Phase 3: REFLECT   → Layer on business strategy for strategic gaps
Phase 4: REPORT    → Produce prioritized report with 4 tiers
Phase 5: HANDOFF   → Map opportunities to UiPath implementation skills
```

**Stop conditions:** Quick scan caps at 10 findings, Standard at 25, Deep dive
at 35. Max 2 retries per failed source. Phase 1 timeboxed at 3 hours for deep
dives. See [references/intake-guide.md](references/intake-guide.md) §0G for details.

## Phase 0: INTAKE (interactive)

Build a complete picture before mining. Ask — don't assume.

See [references/intake-guide.md](references/intake-guide.md) for detailed steps
covering company context, tool inventory, access verification, org structure,
output preferences, user hypotheses, scope control, and privacy authorization.

**Key outputs from intake:**
- Company context and department list
- Tool & system inventory with verified access
- Agreed scope (quick scan / standard / deep dive) with finding caps
- Privacy scope (pseudonymize by default, jurisdiction constraints)

## Phase 1: MINE

Cast a wide net. Prioritize by signal density. Use parallel agents (Agent tool
with `subagent_type: general-purpose`, one agent per source category).

See [references/mining-guide.md](references/mining-guide.md) for detailed
per-source guidance on what to look for and how to search.

**Source priority when time is limited:**
1. Messaging help channels — highest signal, fastest to mine
2. Email patterns — reveals hidden recurring work
3. CRM/ERP — reveals structured process bottlenecks
4. Wiki/docs — reveals existing automation landscape
5. Issue tracker — reveals service desk patterns
6. HRIS — reveals people-process friction
7. Web research — reveals strategic gaps

Note: Web research (priority 7) feeds Phase 3 strategic analysis. Even under
time pressure, do a brief web search for the company's public financials and
strategy — this takes minutes and enables Tier 4 findings.

Work with whatever access is verified. Even messaging channels alone can yield
15+ opportunities. Each additional source adds depth, not changes the methodology.

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

Identify roles that are sole responders. If they're out, the process stops.
Pseudonymize by default — use role/team labels unless naming is authorized.

```
| Role/Pseudonym | System/Channel | Function | Risk |
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

**Greenfield case:** If no existing automations are found (nothing to replicate),
Tier 1 will be empty. Promote the highest-volume Tier 2 finding to the headline
slot and note that the company has no proven models to replicate yet.

### 2D. Department Coverage Map

```
| Department | Existing Automations | Key Gap |
```

Flag ZERO-coverage departments as biggest blind spots.

### 2E. Process Deep Reads

For promising existing projects, extract: pain point, manual process today,
volume/frequency, ROI if documented, systems involved, dev status.

Apply low-confidence handling per Critical Rule 4.

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
See [references/report-template.md](references/report-template.md) for structure,
tier definitions, evidence standards, and platform-specific guidance.

### Quality Bar

- Every opportunity has specific evidence (source, metric, affected role/team)
- No unsupported claims (except Tier 4, which references strategy docs)
- SPOFs identified by role (or name if authorized)
- Replicable models highlighted as Tier 1
- Department map is complete (all departments, not just gapped ones)
- ROI benchmarks from existing projects included
- Strategic analysis ties to real financials

## Phase 5: HANDOFF

Map each Tier 1-2 opportunity to a UiPath implementation path. Add a
"Next Step" column to the report's Tier 1-2 tables.

| Opportunity Type | Recommended Skill | Artifact |
|---|---|---|
| Desktop/app automation (UI, data entry) | →uipath-rpa | Coded workflow (.cs) or XAML |
| Multi-step automation or orchestration | →uipath-maestro-flow | Flow (.flow) |
| Scheduled / triggered automation | →uipath-maestro-flow | Flow with trigger |
| Agent-based (conversational, reasoning) | →uipath-agents | Coded agent |
| Approval / human review gate | →uipath-human-in-the-loop | HITL node in Flow |
| Cross-system integration | →uipath-platform | Integration Service connector |

For complex or multi-component opportunities, hand off to →uipath-planner
for full solution design.

## Execution Strategy

Parallelize aggressively using the Agent tool with `subagent_type: general-purpose`:
- 3 agents simultaneously for Phase 1: messaging, wiki/tracker, systems of record
- Department-specific behavioral agents in Phase 2
- Multiple process doc reads in parallel
- Web research concurrent with internal mining

Always share interim findings. Don't disappear for hours. Check in after
each phase with a brief summary and ask if the user wants to adjust scope.

## Reference Navigation

- [references/intake-guide.md](references/intake-guide.md) — Phase 0 detailed steps (company context, tool inventory, access verification, privacy)
- [references/mining-guide.md](references/mining-guide.md) — Per-source search guidance (load during Phase 1)
- [references/report-template.md](references/report-template.md) — Output structure, tier definitions, and evidence standards (load during Phase 4)

## Anti-patterns

- **Mining before intake.** Never start searching systems before completing Phase 0. Without context you'll waste time on irrelevant signals.
- **Naming individuals without consent.** Always pseudonymize SPOFs unless the requester explicitly authorizes naming. Apply the `name-mapping.json` before every write.
- **Fabricating metrics.** If a source returns sparse data, mark findings as low-confidence. Never invent volume numbers.
- **Promising ROI without source citations.** Every ROI estimate must reference an existing project benchmark or explicit data point.
- **Skipping the replicable-model search.** The highest-value findings are always proven models that can replicate. Never skip Phase 2C.
- **Speculating from insufficient evidence.** Below signal threshold → mark low confidence. Insufficient evidence → don't promote to Tier 1-3.
