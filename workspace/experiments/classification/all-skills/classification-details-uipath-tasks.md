# Classification Details — uipath-tasks

**Classification: Strong**

---

## What the Skill Teaches

How to manage UiPath Action Center human-in-the-loop tasks via `uip tasks` — from login/tenant resolution and task discovery through assign, complete, and post-action verification.

| # | Area | Codifiable? | Notes |
|---|------|-------------|-------|
| 1 | **Login and tenant resolution** | **Yes — VALIDATE/CHECK** | Fixed probe + branch on environment/tenant mismatch |
| 2 | **Task discovery (list + get)** | **Yes — EXTRACT** | Parameterized filter commands with fixed output fields |
| 3 | **Discover→Plan→Act→Verify workflow** | **Yes — TRANSFORM-PIPELINE** | Explicitly documented four-step fixed sequence |
| 4 | **Post-action verification** | **Yes — VALIDATE/CHECK** | Re-read task after every mutation to confirm state change |
| 5 | **Task types / statuses / priorities tables** | **Yes — LOOKUP/REFERENCE-TABLE** | Fixed mapping tables embedded in the skill |
| 6 | Deciding which action/data payload to supply when completing a FormTask | No | Payload content is business-logic judgment |
| 7 | Assignee selection (who should receive the task) | No | Business/org-structure judgment |

---

## Codifiable Procedures (not yet scripted)

### 1. Login and Tenant Resolution — VALIDATE/CHECK

**Source:** `skills/uipath-tasks/SKILL.md` §Login & Tenant Setup

**What it does:** Runs `uip login status --output json`, parses `UIPATH_URL`, `Organization`, and `Tenant`, and compares them against the request's target environment. If the environment differs, issues `uip login --authority <url> --tenant <tenant>`; if the environment matches but the tenant differs, runs `uip login tenant set <tenant>`. Aborts if the final status does not reflect the expected state. Line 25: "Check current login: `uip login status --output json` — verify `UIPATH_URL`, `Organization`, and `Tenant`"

**Why it's mechanical:** The decision tree is fully enumerated (three branches: correct, wrong environment, wrong tenant) with exact commands for each; no judgment is required.

**Turn savings:** Without a script the agent spends 1–2 turns probing and branching before any `tasks` command; a check-and-switch script collapses this to one call that returns the active tenant name or exits with an error.

---

### 2. Task Discovery — EXTRACT

**Source:** `skills/uipath-tasks/SKILL.md` §Task Navigation

**What it does:** Issues `uip tasks list [--folder-id <id>] --output json` and/or `uip tasks get <task-id> --output json` to extract structured task records including ID, type, status, priority, and folder. Supports scoping by folder, admin view (`--as-admin`), and type-hint routing for endpoint disambiguation. Line 150: "List all tasks | `tasks list`"

**Why it's mechanical:** The extraction is a parameterized CLI call returning a fixed JSON schema; field mapping from output to agent state is deterministic.

**Turn savings:** Without a script the agent runs list and get separately, then manually extracts fields across multiple turns; a discover script accepts filter parameters and returns a structured task summary in one call.

---

### 3. Discover→Plan→Act→Verify Workflow — TRANSFORM-PIPELINE

**Source:** `skills/uipath-tasks/SKILL.md` §Workflow: Discover → Plan → Act → Verify

**What it does:** Executes the four-step mandated sequence: (1) list tasks and get details, (2) determine the operation, (3) execute assign/complete/reassign/unassign, (4) re-read the task to confirm the state change. The sequence is the same regardless of the specific operation. Line 180: "Always follow this pattern:"

**Why it's mechanical:** The step order is fixed and explicit; the only variable is the specific Act command (assign vs complete vs reassign), which is determined by the request, not by interpretation of task state.

**Turn savings:** Without a script the agent issues each of the four steps in separate turns; a workflow script accepts task-id, operation, and operation-specific args, and executes all four steps in one turn.

---

### 4. Task Types / Statuses / Priorities Lookup — LOOKUP/REFERENCE-TABLE

**Source:** `skills/uipath-tasks/SKILL.md` §Task Types, §Task Statuses & Priorities

**What it does:** Maps a human-readable task concept to its CLI value: e.g., "form approval" → `FormTask`, "pending but not assigned" → `Unassigned`, "urgent" → `Critical`. The tables are exhaustive and embedded in the skill. Line 69: "| Type | CLI value | Description |"

**Why it's mechanical:** The mapping is a fixed three-column table; lookup is a key→value resolution with no ambiguity.

**Turn savings:** Without a script the agent scans and reads the tables in context to find CLI values; a lookup script accepts a human-readable term and returns the canonical CLI value in one call.

---

## Justification for Classification

**Strong** — not Partial, not None.

**Why not Partial:** Five of seven distinct teaching areas are codifiable. The only non-codifiable areas are the business content of task payloads (what action/data to send) and assignee selection — both are downstream decisions that belong to the requester, not to the skill's mechanics. The mechanics themselves (login, discovery, workflow sequencing, verification, type/status mapping) are all codifiable.

**Why not None:** The skill's entire operational model is a documented four-step pipeline (Discover→Plan→Act→Verify) with accompanying lookup tables and a login-check gate — all mechanically codifiable.

**Evidence locations:**
- Login/tenant resolution: `skills/uipath-tasks/SKILL.md` §Login & Tenant Setup (lines 18–44)
- Task discovery: `skills/uipath-tasks/SKILL.md` §Task Navigation table (lines 150–174)
- Workflow pipeline: `skills/uipath-tasks/SKILL.md` §Workflow: Discover → Plan → Act → Verify (lines 179–203)
- Type/status/priority tables: `skills/uipath-tasks/SKILL.md` §Task Types (lines 68–76), §Task Statuses & Priorities (lines 80–93)
