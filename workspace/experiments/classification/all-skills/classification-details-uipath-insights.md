# Classification Details — uipath-insights

**Classification: Partial**

---

## What the Skill Teaches

Query UiPath job execution metrics and discover monitoring scope identifiers via `uip insights` CLI, then route analysis and root-cause investigation to specialist skills.

| # | Area | Codifiable? | Notes |
|---|------|-------------|-------|
| **1** | **Auth state check before cloud calls** | **Yes — VALIDATE/CHECK** | Rule 9 context: `uip login status --output json` verifies session; explicit auth handoff pattern |
| **2** | **Task routing via navigation table** | **Yes — LOOKUP/REFERENCE-TABLE** | Lines 54–59: fixed guide-per-task mapping (job health → investigation-playbook, commands/flags → jobs-commands, scope resolution → filter-discovery) |
| **3** | **Jobs investigation pattern (summary → drill-down)** | **Yes — TRANSFORM-PIPELINE** | Rule 5: always start with `summary` for totals before targeted subcommands; fixed ordered sequence |
| **4** | **Filter discovery for scope identifiers** | **Yes — EXTRACT** | `filter-folders` / `filter-processes` / `filter-queues` / `filter-machines` produce folder keys, process names, machine names |
| **5** | **Response envelope parsing (Data PascalCase, Pagination)** | **Yes — PARSE** | Rule 1: `{ Result, Code, Data }` envelope; keys `FolderKey`, `JobsCount` (PascalCase); `Pagination` on filter-* |
| 6 | Job failure trend interpretation and causation analysis | No | Investigation playbook (in references) requires monitoring expertise and contextual judgment |
| 7 | Handoff routing to uipath-troubleshoot / uipath-rpa / uipath-agents | No | Judgment on which specialist skill to invoke based on failure type |
| 8 | Error/retry handling (RetryWillNotFix vs RetryLater vs auth failures) | No | Rule 8 gives routing labels but response to each case requires judgment on context and permissions |

---

## Codifiable Procedures (not yet scripted)

### 1. Auth State Check — VALIDATE/CHECK

**Source:** `skills/uipath-insights/SKILL.md` §Shared Workflow

**What it does:** Before any cloud-bound `uip insights` call, verify the active session is authenticated. The check is a single command whose output confirms the session state; if not authenticated, the agent provides the login command rather than running it interactively. Line 36: "Check the active login when the task will call UiPath Cloud: `uip login status --output json`."

**Why it's mechanical:** The command and success criterion are fixed; the pass/fail check requires no judgment.

**Turn savings:** Agents currently run the command ad hoc and inspect output manually; a check script returning structured auth state collapses to one call.

---

### 2. Jobs Investigation Pipeline — TRANSFORM-PIPELINE

**Source:** `skills/uipath-insights/SKILL.md` §Critical Rules, §Shared Workflow

**What it does:** The skill mandates a fixed two-step investigation order: first run `uip insights jobs summary` to obtain job totals and a denominator for failure rates, then run targeted subcommands (`failures`, `failure-reasons`, `completion-trends`, `process-details`) based on the investigation goal. Time range must always be supplied. Line 26: "Start with `summary`, then drill down. After any scope discovery the task needs, begin a job investigation with `uip insights jobs summary` for the totals, then run the targeted subcommands. The summary supplies the denominator that makes a failure count meaningful."

**Why it's mechanical:** The ordering rule (summary first, then targeted command) is an explicit invariant independent of the question being answered; the time-range requirement is validated locally by the CLI.

**Turn savings:** Without a script, the agent selects and sequences subcommands across 2–3 turns; an investigation runner accepting scope + time-range + goal collapses to one call.

---

### 3. Filter Discovery for Scope Identifiers — EXTRACT

**Source:** `skills/uipath-insights/SKILL.md` §Task Navigation, §Critical Rules

**What it does:** Before scoping a job query by folder, process, queue, or machine, the skill requires using `uip insights filter-folders`, `filter-processes`, `filter-queues`, or `filter-machines` to resolve exact identifiers rather than guessing. Pagination must be exhausted before concluding a resource is absent. Line 31: "Discover identifiers instead of guessing. Use `references/filter-discovery-guide.md` to resolve monitoring scope. Page through all results before concluding a resource is absent."

**Why it's mechanical:** The filter commands and pagination loop are fixed; identifier extraction from the response uses known PascalCase field names.

**Turn savings:** Agents currently run filter commands per resource type and page through results across 2–4 turns; a discovery script accepting a resource type + keyword collapses multi-page pagination to one call.

---

## Justification for Classification

**Partial** — not Strong, not None.

**Why not Strong:** The skill's reference files — `investigation-playbook-guide.md`, `jobs-commands-guide.md`, and `filter-discovery-guide.md` — are where the substantive analysis work happens, and that work (interpreting failure trends, understanding causation patterns, deciding when to escalate to `uipath-troubleshoot`) requires monitoring expertise and judgment. The SKILL.md itself is a dispatch layer; the actual investigation guidance in references is judgment-heavy.

**Why not None:** Rules 5 and 10, the Shared Workflow, and the navigation table establish at least three explicit codifiable procedures: auth check (VALIDATE/CHECK), the summary-first investigation sequence (TRANSFORM-PIPELINE), and paginated filter discovery (EXTRACT).

**Evidence locations:**
- Auth check: `skills/uipath-insights/SKILL.md` §Shared Workflow (line 36)
- Summary-first rule: `skills/uipath-insights/SKILL.md` §Critical Rules, Rule 5 (line 26)
- Filter discovery requirement: `skills/uipath-insights/SKILL.md` §Critical Rules, Rule 10 (line 31)
- Judgment delegation to references: `skills/uipath-insights/SKILL.md` §Task Navigation (lines 54–59)
