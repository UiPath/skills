# Classification Details — uipath-mcp-servers

**Classification: Partial**

---

## What the Skill Teaches

Register, configure, verify, and manage AgentHub MCP servers via `uip agenthub mcp`, and author resource tools on `uipath`-type servers via `uip agenthub mcp-tools`.

| # | Area | Codifiable? | Notes |
|---|------|-------------|-------|
| 1 | Server type selection (choosing among uipath / coded / command / remote / platform / swagger) | No | Judgment based on integration intent, process availability, and whether tools are static or dynamic |
| **2** | **Slug validation** | **Yes — VALIDATE/CHECK** | Rule 1: backend enforces `^[a-z0-9-]+$`, length 3–50; client-side validated before POST |
| **3** | **Folder context resolution** | **Yes — VALIDATE/CHECK** | Rule 2: every AgentHub call requires `--folder-path` or `--folder-key`; GUID required for personal workspaces; `--all-folders` for locate-then-target pattern |
| **4** | **Post-mutation verification** | **Yes — VALIDATE/CHECK** | Rule 3: after every create/update/delete/refresh-tools, re-list or get and confirm expected state |
| **5** | **refresh-tools behavior routing** | **Yes — DETECT** | Rule 4: `coded`/`command` → async 202 + runtime id; `remote`/`platform`/`swagger` → sync 200; `uipath`/`selfhosted` → rejected, author via `mcp-tools create-resource` |
| 6 | Resource tool schema design (input-schema, output-schema, metadata) | No | Requires judgment on what inputs/outputs the tool should expose for its bound Orchestrator resource |
| **7** | **Resource tool creation pipeline** | **Yes — TRANSFORM-PIPELINE** | `mcp-tools candidates` → pick target → `create-resource` → verify via `mcp-tools list`; fixed sequence |
| 8 | Troubleshooting error responses (HTTP 400, folder conflicts, slug conflicts) | Marginal | Rule-based routing table exists but each error requires reading the actual response and deciding next action |

---

## Codifiable Procedures (not yet scripted)

### 1. Slug Validation — VALIDATE/CHECK

**Source:** `skills/uipath-mcp-servers/SKILL.md` §Critical Rules

**What it does:** Before creating or updating an MCP server, validate the slug against the backend-enforced regex and length constraints. The CLI validates client-side before POST, but the rule is explicit and can be checked independently. Line 34: "Slug regex. Backend enforces `^[a-z0-9-]+$`, length 3-50. Lowercase, digits, hyphens — no underscores, dots, or uppercase. CLI validates client-side before POST."

**Why it's mechanical:** The regex and length bounds are fixed constants; a check function takes a string and returns pass/fail deterministically.

**Turn savings:** Without a check, agents discover invalid slugs only after POST fails, requiring an extra turn to fix and retry; a pre-check eliminates the round-trip.

---

### 2. Post-Mutation Verification — VALIDATE/CHECK

**Source:** `skills/uipath-mcp-servers/SKILL.md` §Critical Rules

**What it does:** After every create, update, delete, or refresh-tools call, re-list or get the server and confirm the expected state before reporting completion. For `mcp-tools` mutations, re-list tools on the parent server. Line 38: "Verify after every mutation. After `create` / `update` / `delete` / `refresh-tools`, re-list (`mcp list`, `mcp-tools list --mcp <slug>`) or `mcp get <slug>` and confirm the expected state."

**Why it's mechanical:** The verification command pattern is fixed for each mutation type; the state check (presence/absence of the slug, tool count) is deterministic.

**Turn savings:** Without a script, agents run the mutation, then manually run a list/get and parse the response across 2 turns; a mutation-and-verify wrapper collapses to one call.

---

### 3. refresh-tools Type Routing — DETECT

**Source:** `skills/uipath-mcp-servers/SKILL.md` §Critical Rules

**What it does:** The `refresh-tools` command behavior differs by server type: `coded` and `command` return HTTP 202 with an async runtime id (poll `mcp-tools list` to confirm); `remote`, `platform`, and `swagger` return HTTP 200 after synchronous fetch+upsert; `uipath` and `selfhosted` reject refresh-tools (tools are authored via `mcp-tools create-resource`). Line 40: "`refresh-tools` behavior depends on server type. `coded` / `command` — async, returns HTTP 202 + runtime id. Surface the runtime id; never claim refreshed before a follow-up `mcp-tools list --mcp <slug>` confirms. `remote` / `platform` / `swagger` — sync, returns 200 after a synchronous fetch+upsert. `uipath` / `selfhosted` — rejected locally."

**Why it's mechanical:** The type-to-behavior mapping is an explicit lookup table with no ambiguous cases; the server type is known from creation time.

**Turn savings:** Without upfront routing, agents discover async behavior only after waiting unnecessarily for a synchronous response, then retry; a pre-check eliminates the confusion.

---

### 4. Resource Tool Creation Pipeline — TRANSFORM-PIPELINE

**Source:** `skills/uipath-mcp-servers/SKILL.md` §Resource Tools

**What it does:** Creating a resource tool on a `uipath`-type server follows a fixed four-step sequence: (1) `mcp-tools candidates --category <kind>` to discover bindable targets; (2) select target (user picks or agent picks from list); (3) `mcp-tools create-resource` with `--target-identifier`, schema flags, and folder context; (4) verify via `mcp-tools list --mcp <slug>`. Line 72: "`mcp-tools candidates --category <kind>` (kind ∈ `automation` / `agent` / `agentic-process` / `api-workflow`) … Pass `--target-identifier <resource-id>`. Read metadata shape from `mcp-tools template resource --output json`."

**Why it's mechanical:** The command sequence and flag requirements are fixed; the only judgment is in step 2 (which target to bind) when multiple candidates are returned.

**Turn savings:** Without a pipeline script, agents run candidates, parse, select, and create across 3–4 turns; a guided pipeline script collapses discovery and creation to 1–2 calls.

---

## Justification for Classification

**Partial** — not Strong, not None.

**Why not Strong:** The two highest-value decisions the skill requires — selecting the right server type and designing the resource tool's input/output schema — are judgment-based and account for roughly half of what the skill teaches. Server type selection drives the entire subsequent workflow but depends on integration intent; schema design requires understanding what consumers of the tool will need.

**Why not None:** The slug validation (VALIDATE/CHECK), post-mutation verification (VALIDATE/CHECK), refresh-tools type routing (DETECT), and resource tool creation pipeline (TRANSFORM-PIPELINE) are all explicitly rule-driven procedures with fixed commands and deterministic outcomes.

**Evidence locations:**
- Slug validation rule: `skills/uipath-mcp-servers/SKILL.md` §Critical Rules, Rule 1 (line 34)
- Post-mutation verification: `skills/uipath-mcp-servers/SKILL.md` §Critical Rules, Rule 3 (line 38)
- refresh-tools routing table: `skills/uipath-mcp-servers/SKILL.md` §Critical Rules, Rule 4 (line 40)
- Resource tool pipeline: `skills/uipath-mcp-servers/SKILL.md` §Resource Tools (lines 66–76)
- Judgment for server type: `skills/uipath-mcp-servers/SKILL.md` §Server Types table (lines 50–58)
