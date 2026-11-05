# Component Placement Guide

Per-task component placement and Level 3 capability add-ons of product selection. Levels 0–1 and the Constraint Gate: [product-selection-guide.md](product-selection-guide.md).

## Per-task component placement (the to-be, per step)

Type each step and place it on the component that fits — the canonical UiPath placement model. Applied **twice**: at Phase 1 Step 3.5 to build the step→executor map that feeds Level 1 (layer 2 before layer 3), and at Phase 2 Steps 3–4 of the [Design Guide](../design/design-guide.md) to record each placement in the template's inventory table and flag non-primary components as integrated components. This is how the SDD says **where** API / RPA / Agents / DU / DMN / HITL / Maestro are each needed.

| Task type (verb) | Best-fit component | Routes to |
|---|---|---|
| **Validate / Transfer** — deterministic, rule-based | RPA, or Integration Service / API Workflow if a stable API exists and is reachable from that runtime (rule 5) | `uipath-rpa` / `uipath-platform` / `uipath-api-workflow` |
| **Read / write / transform machine-local data** — Excel/Office files, files & folders on local or network storage, on-prem databases, desktop email | RPA (Excel / Database / Mail activities) — cloud runtimes cannot reach these; API Workflow / Function only when the source is cloud-reachable (rule 5) or the Function is robot-hosted (on-prem endpoints — desktop apps and interactive UI stay RPA) | `uipath-rpa` |
| **Collect** from semi-structured documents | Document Understanding / IXP | `uipath-ixp` (or a DU activity inside RPA/Flow) |
| **Decide / classify** — judgment | AI Agent; or a Business Rules project (DMN decision table) for threshold / eligibility logic | `uipath-agents` / `uipath-rules` |
| **Create / author / summarize** free-form | AI Agent; simple generation with no decisioning = an LLM activity inside the host project (no separate project or task) | `uipath-agents` (standalone Agent only) |
| **Review / Escalate / sign-off**, exception handling | HITL — host-aware: Flow host → HITL skill; coded Agents → escalation wired by `uipath-agents` (per the HITL skill's own deferral); BPMN → inline userTask by the BPMN specialist; Case → inline `action` task detail block in the Case Blueprint; RPA → Action Center / long-running | `uipath-human-in-the-loop` (Flow hosts only) |
| **Wait / approve inside ONE process** | Long-running RPA (persistence + Action Center); an ordinary scheduled or queue-triggered run is just RPA + an Orchestrator trigger — never Maestro | `uipath-rpa` (trigger config → `uipath-platform`) |
| **Sequence / coordinate MULTIPLE automations** — real orchestration only: state outliving a run, parallel / event branches, end-to-end visibility. Synchronous in-run child calls are light orchestration absorbed by the host (Decision table) | Maestro orchestration (Flow / BPMN / Case) | `uipath-maestro-flow` / `-bpmn` / `-case` |
| **Transform / compute** — atomic deterministic custom logic (parsing, scoring, custom-auth API call, ERP query via IS connection) | Host-native code first (rule 6); a Coded Function (TypeScript / JavaScript / Python) when extraction is justified — typed input → deterministic code → typed output; invoked from Maestro / agents / Orchestrator. Runs serverless or robot-hosted — robot-hosted Functions execute inside the environment and reach on-prem endpoints; interactive UI / desktop-app / attended work stays RPA | `uipath-functions` |
| **Aggregate / persist shared data across systems** | Data Fabric entities are the **persistence**, not an executor — the aggregation logic runs in an API Workflow / Function / RPA query that reads and writes the entities | executor per this table + `uipath-platform` (entities) |

Rules:
1. **DU / IXP is extraction from semi-structured documents — NOT free-form authoring** (that's an Agent). Route document-heavy `Collect` to `uipath-ixp`.
2. **Business Rules / DMN** is its own BusinessRules project (`uipath-rules`), deployed in the solution and called by Maestro (BPMN business rule task, Case `business-rule` task) or RPA. Each deterministic decision table that a deployed rule evaluates is a separate project and task routed to `uipath-rules`; rule logic an Agent reasons over stays in the Agent.
3. **Data Fabric / Data Service is storage, never an executor** — entities hold the shared data (`uipath-platform`); the computation over them is always placed on an executor (API Workflow / Function / RPA).
4. **Coded Functions are components, not primaries** — a Function is consumed by Maestro / agents / Orchestrator callers; a request that is *only* a Function is a single-project deferral to `uipath-functions`, not a plan.
5. Deterministic `Validate` / `Transfer` should not reflexively become RPA when a stable API / connector exists **and is reachable from that executor's runtime** — prefer Integration Service / API Workflow (API-first). On-prem HTTP(S) APIs can be reached from Automation Cloud via **Automation Relay** (Integration Service + API Workflows only; needs Unified Standard/Enterprise or Flex Standard/Advanced licensing plus a Relay client deployed on-network) — offer it and confirm with the user; unconfirmed → RPA + `[SME REVIEW]`. Non-HTTP local interfaces (file shares, desktop apps, raw database connections, terminals) are robot-only → RPA.
6. **Extraction test — a separate deployed component must be justified.** Default is host-native: RPA runs Invoke Code, coded Agents use their own Python, API Workflows use script activities, Maestro transforms data between nodes. Mint a separate component (Coded Function, API Workflow) only when at least one holds: (a) the host's surface cannot express the logic or call (low-code IS-only surface, custom auth the host cannot do); (b) 2+ consumers share it; (c) it needs a lifecycle independent of the host — separate versioning, scaling, or ownership. One consumer + host-capable → keep it in the host; no new project, no new task. A call to a third-party system is not subject to this test: it follows the [Integration Service](#integration-service) tiers, so a system with no catalog connector gets a custom connector even for one consumer. Inverse guard: a headless deterministic compute step needing no UI, no activities, and no attended context prefers a Coded Function over minting an RPA process — RPA is not the default home for pure code.

## Level 3 — Capability Add-ons

These are capabilities added to the primary product, not standalone products. When detected, flag them in the appropriate template section. The genome reads the flags from the SDD and routes the work to the correct skill.

### HITL (Human-in-the-Loop)

**Scope:** Adds approval gates, exception escalation, and write-back validation. **Only Flow hosts route to `uipath-human-in-the-loop`** (in a single-project request the Flow specialist authors the inline node itself — the HITL-skill task applies to planner-generated multi-project plans). Every other host owns HITL itself: coded Agents → escalation wired by `uipath-agents` (the HITL skill's own deferral); BPMN → inline userTask authored by `uipath-maestro-bpmn`; Case → inline `action` task detail block authored by `uipath-maestro-case`; RPA → Action Center / long-running workflow.

**Signals the PDD needs HITL:**
- "Approval before..."
- "Human reviews..."
- "If confidence is low, escalate..."
- "Validate before writing back..."
- "Fills in missing data..."

**How to flag:** Add a "HITL Touchpoints" line in the host template's relevant section (node table, agent description). For Flow hosts the planner adds an "Add HITL node per §X" task routed to `uipath-human-in-the-loop`; for coded-Agent hosts the escalation is part of the `uipath-agents` build task; for BPMN / Case / RPA hosts the touchpoint stays with the host's own specialist — no HITL-skill task.

### Integration Service

**Scope:** Adds connector activities (Salesforce, Jira, ServiceNow, Slack, etc.) to RPA, Flow, Case Management, or Agents. IS connectors are the standard integration surface for **API Workflows, Maestro (Flow / BPMN / Case), and Agents** — these consume connector activities, not raw UI. A system with no catalog connector gets a custom connector, not a raw API call.

**Signals the PDD needs Integration Service:**
- Third-party SaaS system mentioned (not a custom web app): Salesforce, Jira, ServiceNow, Slack, HubSpot, Workday, Zendesk, etc.
- "Create a ticket in...", "Post a message to...", "Read records from..."

**Check availability — reuse before build.** For each required integration, retrieve the catalog before assuming a connector exists (auth required; best-effort like tenant library discovery):

```bash
uip is connectors list --output json                          # full catalog
uip is connectors list --filter "<KEYWORD>" --output json     # narrow by system name
```

- **Connector exists →** reuse it, whether or not a connection is configured yet. Flag `Access Method = Integration Service — <CONNECTOR_SLUG>`; the planner adds a "Configure <X> connector" task routed to `uipath-platform`, and a missing connection is an `[SME REVIEW]` provisioning item.
- **No connector, and the API is REST+JSON →** build a **custom connector**, for every consumer, including one that could call HTTP itself. Flag `Access Method = Custom connector — <CONNECTOR_SLUG>`; the task is routed to `uipath-connector-builder` and ordered before its consumers. Do not fall back to a direct HTTP call or an API Workflow wrapper because only one host consumes the API. An unverified connector is an `[SME REVIEW]` item — never assume one exists. The connector is an integrated component — scope is unchanged ([derived-component rule](product-selection-guide.md#solution-signals)).
- **No connector, and a custom connector cannot cover the API** (not REST+JSON, or an auth scheme the connector builder cannot express) → a direct authenticated call (tier 4 below). Flag `Access Method = Direct HTTP`, keep the key in a `Credential` asset, and write the justification in the SDD.

#### Integration mechanism — connection before raw API call

For each third-party system the design talks to, pick the highest tier that works and record it in the SDD:

| Tier | Approach | Use when |
|---|---|---|
| 1 | IS **connector activity** | A catalog connector covers the operation |
| 2 | HTTP request through that connector's **IS connection** | Connector exists, activity missing |
| 3 | **Build a custom connector** (`uipath-connector-builder`) | No catalog connector; REST+JSON API |
| 4 | Direct authenticated call, key in a `Credential` asset | Nothing above fits; justify it in the SDD |

A `Credential` asset keeps the secret safe, not the integration managed: a tier-4 call is absent from `uip is connections list` and cannot be re-pointed per environment. A missing catalog connector argues for tier 3, not tier 4.

### API Workflow (as integrated component)

**Scope:** When API Workflow is NOT the primary but is called by the primary (Maestro Flow, Maestro BPMN, Case Management, Agent, another API Workflow).

**Signals** (must also pass the extraction test — [placement rule 6](#per-task-component-placement-the-to-be-per-step)):
- The primary product invokes a callable system-to-system integration with structured JSON input/output (not UI), AND at least one extraction justifier holds: the host cannot make the call natively (IS-only surface), 2+ consumers share the integration, or it needs independent versioning / scaling / ownership.

A third-party API with no catalog connector gets a custom connector (see Integration Service above), not an API Workflow wrapper.

**How to flag:** In the primary product's template, list API Workflow invocations in the relevant section (Flow nodes, BPMN Activities Inventory serviceTask rows, Agent tools, Case tasks). The planner picks this up and creates a per-API-Workflow task that routes to `uipath-api-workflow`. Scope is unchanged ([derived-component rule](product-selection-guide.md#solution-signals)).

### Reusability & shared assets

Design for reuse — a modular solution built from small automations is cheaper to build and maintain. For each candidate shared asset, **reuse before build**, and when building new, treat it as its own buildable project built **before** its consumers:

- **RPA Library** — shared/common workflows (date/string/mapping helpers, app wrappers) extracted into a Library (Level 1.5 sub-type). **Reuse:** discover deployed tenant libraries via the [Tenant Library Search](tenant-library-search-guide.md) (Phase 1 Step 2.5) and reference them in §Packages. **Build new:** a new Library is its own RPA project routed to `uipath-rpa`, consumed by others.
- **Custom connector** — when the catalog has no Integration Service connector (see [Integration Service](#integration-service) above), build a reusable custom connector via `uipath-connector-builder`; one connector serves many projects.
- **Reusable components** — shared components from the Marketplace / org repo (reuse) or new-to-build. List both in the SDD's **Reusable Components** section (reused existing + new reusable).
- **Shared scope / modularity** — an asset used by 2+ projects (Library, custom connector, IS connection, asset, queue) lives at the **parent-folder / solution level**, built once and referenced by all — never duplicated per project.

Flag every reused and new-to-build shared asset in the SDD; the planner emits a build task for each new one (Library → `uipath-rpa`; custom connector → `uipath-connector-builder`), ordered before its consumers.
