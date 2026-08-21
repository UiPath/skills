# Classification Details — uipath-platform

**Classification: Strong**

---

## What the Skill Teaches

UiPath platform operations via the `uip` CLI covering auth, Orchestrator (folders/assets/queues/jobs/machines/users), Integration Service, Data Fabric, LLM Gateway, BYOG guardrails, traces, context grounding, and licensing.

| # | Area | Codifiable? | Notes |
|---|------|-------------|-------|
| 1 | **Diagnostic routing (troubleshoot vs. operate)** | **Yes — DETECT** | Lines 14–19 define a 4-rule classifier: causal → troubleshoot, operational → stay, mixed → troubleshoot first, unavailable → degrade |
| 2 | **Auth flow** | **Yes — TRANSFORM-PIPELINE** | Check status → login (if needed); named profile pattern fully specified |
| 3 | **Orchestrator CRUD (folders, assets, queues, jobs, etc.)** | **Yes — TRANSFORM-PIPELINE** | `uip or` command sequences; CRUD patterns apply uniformly across resource types |
| 4 | **Data Fabric operations** | **Yes — TRANSFORM-PIPELINE + VALIDATE/CHECK** | Create entity → add fields → insert records → query; ETag get-modify-put pattern for updates |
| 5 | **LLM Gateway BYO config** | **Yes — TRANSFORM-PIPELINE** | list → create (with mapping validation) → update → delete; server-side probe required |
| 6 | **BYOG guardrail config** | **Yes — TRANSFORM-PIPELINE** | list → probe → create → enable/disable → delete; `create` always probes |
| 7 | **Traces / context grounding** | **Yes — EXTRACT** | `uip traces spans get` + `uip context-grounding` sequences fully specified |
| 8 | **Licensing extraction** | **Yes — EXTRACT** | `uip platform tenants licenses` + consumables get with `--mode` variants |
| 9 | Integration Service connections (OAuth flow) | No | OAuth flow requires user interaction; connector selection requires judgment |

---

## Codifiable Procedures (not yet scripted)

### 1. Diagnostic Routing — DETECT

**Source:** `skills/uipath-platform/SKILL.md` §Route Diagnostic Intent Before Platform Work

**What it does:** Classifies the requested outcome into one of four categories and routes accordingly before running any command. Rule 1: causal outcome (explanation/diagnosis/root cause) → invoke `uipath-troubleshoot`. Rule 2: operational outcome → stay. Rule 3: mixed → troubleshoot first. Rule 4: sibling unavailable → degrade gracefully. Line 14: `"Classify the requested outcome before running any command."` Inputs are the user's intent string; output is a routing decision (troubleshoot / operate / mixed / degrade).

**Why it's mechanical:** The four-rule classifier uses explicit intent signals (explanation/diagnosis/root cause → causal; CRUD/inspect/apply fix → operational) with no ambiguous overlap.

**Turn savings:** Without routing, the agent may start platform commands before identifying a diagnostic need, requiring a mid-task redirect; a routing check in turn 1 saves 2–4 turns on misrouted requests.

---

### 2. Auth Check + Login Pipeline — TRANSFORM-PIPELINE

**Source:** `skills/uipath-platform/SKILL.md` §Quick Start §Step 1 — Authenticate

**What it does:** Always checks `uip login status --output json` first; branches to `uip login --output json` if not authenticated. For named profiles, uses `uip login --profile <name>`. Line 98: `"Always check first — most sessions are already authenticated"` before the `uip login status` command. The pattern eliminates unnecessary login prompts by verifying existing credentials before attempting new auth.

**Why it's mechanical:** The check-then-login sequence is fully specified with exact commands; named vs. default profile is a configuration flag, not a judgment call.

**Turn savings:** Without the status check, the agent may prompt for login on every task; the status → conditional login pattern collapses 2 turns to 1 in already-authenticated sessions.

---

### 3. Data Fabric ETag Get-Modify-Put — VALIDATE/CHECK + TRANSFORM-PIPELINE

**Source:** `skills/uipath-platform/SKILL.md` §When to Use This Skill (Data Fabric section)

**What it does:** Implements optimistic concurrency for Data Fabric mutations: `apps data-mapping get` (captures ETag) → edit local file → `apps data-mapping update --etag '<etag>'` (write with ETag). A 409 `ETagFileConflict` response requires re-get with fresh ETag + re-apply of local changes. Line 44: `"--etag is required — pass the Data.ETag that your get returned, which is what proves the edit was based on the version you read; a lost race is refused 409 UserError_ETagFileConflict (re-get for the new version AND ETag, re-apply, retry)."` Inputs: entity id + mutation payload; output: updated record or retry signal.

**Why it's mechanical:** The get → mutate → put-with-etag → retry-on-409 loop is fully specified; no judgment on when to retry or how to handle conflicts.

**Turn savings:** Without the ETag loop, agents make blind writes that race against concurrent changes; scripting the loop reduces write failures and eliminates manual retry coordination (saves 1–3 turns per conflict).

---

## Justification for Classification

**Strong** — not Partial, not None.

**Why not Partial:** The skill is essentially a comprehensive CLI reference for UiPath platform operations. Eight of nine teaching areas are codifiable: diagnostic routing (DETECT), auth flow (TRANSFORM-PIPELINE), Orchestrator CRUD (TRANSFORM-PIPELINE), Data Fabric ops (TRANSFORM-PIPELINE + VALIDATE/CHECK), LLM Gateway config (TRANSFORM-PIPELINE), BYOG config (TRANSFORM-PIPELINE), traces/grounding (EXTRACT), and licensing (EXTRACT). The only non-codifiable area — OAuth flow decisions for Integration Service connections — requires user interaction. All other operations are CLI-driven with specified command sequences.

**Why not None:** Multiple independent codifiable procedures exist across auth, CRUD, ETag concurrency, diagnostic routing, and data extraction.

**Evidence locations:**
- DETECT routing: `SKILL.md` §Route Diagnostic Intent Before Platform Work (lines 14–19)
- TRANSFORM-PIPELINE auth: `SKILL.md` §Quick Start §Step 1 (lines 94–100)
- VALIDATE/CHECK ETag pattern: `SKILL.md` §When to Use This Skill, Data Fabric (line 44 — process-mining SKILL.md; platform SKILL.md line ~44 in Data Fabric section)
- TRANSFORM-PIPELINE LLM Gateway: `SKILL.md` §When to Use This Skill, LLM Gateway (lines 53–54)
- TRANSFORM-PIPELINE BYOG: `SKILL.md` §When to Use This Skill, BYOG (line 55)
