---
name: uipath-gov-access-policy
description: "[PREVIEW] UiPath access policies (`uip gov access-policy`): govern tool-use when an Actor Process invokes a child Resource. Selection + Actor Process + Actor Identity rules. For product settings→uipath-gov-aops-policy."
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# UiPath Access Policy Governance

Skill for authoring UiPath **access policies** of type `ToolUsePolicy` via the `uip gov access-policy` CLI. The `ToolUsePolicy` type **governs tool-use / resource-use** inside Agents and workflow automations: when an Actor Process tries to invoke a child Resource/Tool, the policy decides whether the call is allowed. The `uip gov access-policy` surface returns other policy types as well, but they are out of scope for this skill.

## Scenario this skill governs

When an **Actor Process** (an executable workflow — Maestro, Flow, Case Management, or Agent) invokes a child **Resource/Tool** (another Agent, Maestro, Flow, Case Management, API Workflow, or RPA) as a tool use, the PDP evaluates every applicable access policy and returns an aggregate `Allow` / `Deny` decision. This skill authors those policies.

A policy decides its per-call outcome from three rule blocks — **Selection Rule** (`selectors[]`), **Actor Process Rule** (`executableRule`), and **Actor Identity Rule** (`actorRule`). See [Key Concepts § The three rule blocks](#the-three-rule-blocks-selection--actor-process--actor-identity) for the full structural shape and constraints.

Evaluation flow for a single tool-use request:
1. **PDP selects** every policy whose Selection Rule matches the Resource/Tool.
2. For each selected policy, the PDP evaluates its Actor Process Rule AND Actor Identity Rule against the request. Both pass ⇒ the policy contributes `Allow`; otherwise it does not contribute (no-match).
3. **Aggregation:** if **any** non-simulated policy contributes `Allow`, the final enforcement is `Allow`. Otherwise the request falls through to the runtime default (`Deny` / `NoOp`). `enforcement: "Deny"` is not authorable — Deny is the runtime default when no Allow policy matches (Critical Rule #2).
4. Policies with `status: "Simulated"` are evaluated but excluded from aggregation (see [Key Concepts § Enforcement and status](#enforcement-and-status)).

> **Terminology.** A Governance **Access Policy** is the broad category — `uip gov access-policy` can list, get, evaluate, or delete policies of multiple types. This skill authors the `ToolUsePolicy` type, which gates resource-vs-executable **tool use**. Access policies are **distinct from Automation Ops Governance Policies** (product runtime / design-time behavior for Studio, StudioX, Assistant, Robot, AI Trust Layer, …), handled by the sibling `uipath-gov-aops-policy` skill. For product settings, route there.

## When to Use This Skill

Activate on both **explicit access-policy requests** and **natural-language tool-use / resource-use governance intent**.

**Explicit requests:**
- User asks to create, update, delete, list, get, or evaluate an access policy
- User mentions `uip gov access-policy`, `ToolUsePolicy`, or `tool-use policy`
- User asks "which executables / users can call this resource?" or the inverse

**Tool-use / resource-use governance intent:**
- "When my Agent calls `<sub-agent / flow / process>`, allow/block it" — tool-use governance at the Actor Process ↔ Resource boundary
- "Only `<Actor Process>` should be able to invoke `<Resource>`"
- "Allow / let / permit `<Actor Process>` to use `<Resource>`" — e.g. "allow the Production Maestro to invoke the Production Agent"
- "Block / deny / restrict `<tag>` `<Resource>` from `<Actor Process>`" — silently translate to an Allow shape (Critical Rule #2). The Spec narrative shows only the Allow framing; do not surface the translation to the user.
- "Restrict agent / flow / RPA tool use by tag" — e.g. "only Production-tagged agents may be invoked"
- "Only `<user / robot user / group / admin>` can trigger `<tool-use>`" — Actor Identity governance (emit `actorRule`; only `User` and `Group` types — robots resolve to `User`, ExternalApplication is unsupported)
- "Exclude `<tag-or-UUID>` resources from `<Actor Process>`" — flip via the `None` operator on tags, values, or both

**Sibling redirect:** if the user wants to govern **product settings** (Studio, StudioX, AI Trust Layer, Robot feature flags), that is the `uip gov aops-policy` surface — hand off to `uipath-gov-aops-policy`.

## Recognize Intent → Pick the Right Plugin Blocks

Map intent phrases to the three policy blocks. These priors feed directly into Phase 1 ([planning-arch.md](./references/planning-arch.md)):

| User says... | Likely block(s) | Plugin |
|---|---|---|
| "When `<Actor Process>` invokes `<Resource>`..." (tool-use) | `selectors[]` + `executableRule` | [selector](./references/plugins/selector/planning.md) + [executable](./references/plugins/executable/planning.md) |
| "Only `<tagged>` resources" / "limit tool use to `<tag>`" | `selectors[N].tags` with `Or` operator | [tags](./references/plugins/tags/planning.md) |
| "Block / deny / restrict / exclude `<tag>` resources" | `selectors[N].tags` with `None` operator | [tags](./references/plugins/tags/planning.md#deny-to-allow-flip) |
| "Specific resource UUIDs `<id1>, <id2>`" | `selectors[N].values: ["<id>", ...]` | [selector](./references/plugins/selector/planning.md) |
| "All agents except `<id>`" / "all except `<tag>`" | `values` or `tags` with `None` operator | [selector](./references/plugins/selector/planning.md) + [tags](./references/plugins/tags/planning.md) |
| "Any caller type except `<type>`" (e.g. "any caller except Agent") | `executableRule.values[]` — single entry of the **excluded** type with `operator: "None"` and `values: ["*"]`; omit every other type | [executable — Excluding a caller type](./references/plugins/executable/planning.md#excluding-a-caller-type) |
| "Only `<user>` / `<robot user>` / `<group>` can..." | `actorRule` (Actor Identity) | [actor](./references/plugins/actor/planning.md) |
| "On behalf of `<user>`" / "when `<robot>` triggers..." | `actorRule` with `type: "User"` (Robot User resolves to User UUID) | [actor](./references/plugins/actor/planning.md) |

**Workflow for intent-based requests:**
1. Phase 1 — hand off to [planning-arch.md](./references/planning-arch.md) to author a reviewable **Policy Spec** (natural-language narrative + Spec Components Table covering name, description, status, enforcement, resource selection, actor process, actor identity, tags, operators). The agent **pre-fills every row** with the user's values or sensible defaults (Critical Rule #11); the user reviews and edits any row, then approves before any JSON is composed.
2. Phase 2 — hand off to [planning-impl.md](./references/planning-impl.md) to compose the concrete JSON from the approved Spec by reading each plugin's `impl.md`.
3. Never hand-author policy JSON. The Spec is the contract; plugin `impl.md` files are the **only** authoritative source for block-level shape (Critical Rule #6).

## Critical Rules

1. Always verify login with `uip login status --output json` before any `uip gov access-policy` command. If not logged in, ask the user to run `uip login` (or `uip login --authority <URL>` for non-prod environments).
2. **`policyType` is always `"ToolUsePolicy"`; `enforcement` is always `"Allow"`. Never emit `"Deny"`.**
    - **Why:** the API rejects `enforcement: "Deny"`; Deny is the runtime default when no Allow policy matches, so blocking is expressed as the complement of an Allow set.
    - **Applies to:** every create / update payload. When the user expresses Deny intent, silently translate to an Allow shape and never surface the mechanic (no "Deny→Allow flip" jargon, no `(flipped)` badge, no "enforcement: Deny is not authorable" caveat). See [plugins/tags/planning.md — Deny-to-Allow flip](./references/plugins/tags/planning.md#deny-to-allow-flip) for the decision logic.
3. Gather the active organization / tenant context with the safe auth-context workflow in [access-policy-commands.md — Auth context for policy payloads](./references/access-policy-commands.md#auth-context-for-policy-payloads). Use `uip login status --output json` for names and extract only the non-secret org / tenant UUID fields when the CLI status output does not expose them. Never hardcode UUIDs, never print or source the full auth file, and never expose tokens in chat, logs, files, or review gates.
4. **Three rule blocks; `actorRule` is optional.** A `ToolUsePolicy` access policy is composed of **Selection Rule** (`selectors[]`), **Actor Process Rule** (`executableRule`), and **Actor Identity Rule** (`actorRule`). The first two are mandatory; `actorRule` is emitted only when the user expressed actor-shaped intent — its absence means "any identity passes".
5. **`values` is required on every entry; `tags` only on `selectors[]` / `executableRule`.**
    - **Why:** missing `values` returns `400 Bad Request`; `actorRule` does not accept a `tags` block today (the API rejects `actorRule.tags`).
    - **Applies to:** every entry under `selectors[]`, `executableRule.values[]`, and `actorRule.values[]` — use `["*"]` for "all of this type" even when `tags` narrow the scope. Never emit `actorRule.tags`.
6. **Two-phase authoring is mandatory.** Never construct policy JSON from scratch. Author and approve a **Policy Spec** (natural-language narrative + Spec Components Table) via [planning-arch.md](./references/planning-arch.md) (Phase 1), then compose the concrete JSON via [planning-impl.md](./references/planning-impl.md) (Phase 2), which walks the approved Spec and delegates to each plugin's `impl.md` for block-level JSON.
7. **Single confirmation gate per mutation.** Exactly one `yes / no` review precedes each `create`, `update`, or `delete` call. The gate must show: (a) the **Scope** — the organization name / tenant name plus their UUIDs from the safe auth-context workflow — so the user sees which environment is about to be mutated; (b) the complete policy JSON in chat; (c) clickable markdown links to **both** the Spec file (`/tmp/access-policy-<slug>.spec.md`, written by Phase 1) and the JSON working file (`/tmp/access-policy-<slug>.json`, written by Phase 2) using their **resolved absolute paths** (run `realpath` — never a relative path, a `<WORKING_FILE>` placeholder, or a `~/` path). For update flows the Spec file does not exist (Critical Rule #8) — show the Scope, the diff, and the JSON working file only. See [Confirmation-gate wording](#confirmation-gate-wording).
8. **For `update`: always `get` first and start from `Data` verbatim. Update is a full replacement.**
    - **Why:** any field you omit from the file is cleared on the server (including the whole `actorRule` block); a fresh Phase 1 Spec would silently wipe fields the user did not re-specify.
    - **Applies to:** every update flow. Use the returned `Data` object verbatim as the starting state, then strip audit fields (`isBuiltIn`, `isTemplate`, `createdBy`, `createdOn`, `modifiedBy`, `modifiedOn`, `deletedBy`, `deletedOn`).
9. For `delete`: always `get` and show a summary, then require an explicit `yes` to the verbatim prompt. Deletion is permanent. Multiple UUIDs may be deleted in one call.
10. Every `uip gov access-policy` command in a scripted flow uses `--output json`.
11. **Pre-fill aggressively; prompt only for genuinely ambiguous gaps.** The Phase 1 Spec is presented as **review-and-edit**, not fill-in-the-blanks: every row gets a concrete value from what the user supplied OR a sensible default (always-suggested name, default scope `all`, default tag filter `(none)`, default status `Simulated`, etc.). Treat any value the user already supplied as final — never re-confirm. Surface Open questions only when there is no defensible default. The user changes whatever they want during the review loop.
12. **`evaluate` is user-initiated only and tenant-scoped.** Do NOT call `evaluate` with synthetic/dummy UUIDs after `create` — dummy UUIDs with no Resource Catalog tags or no matching actor identity correctly return `NoOp` / `Deny` and confuse the user into thinking the policy is broken. Only run `evaluate` when the user explicitly asks. The login MUST target a specific tenant (not just an organization); if the PDP rejects with a tenant-context error, route the user to re-login with `--tenant`. See [access-policy-commands.md — evaluate](./references/access-policy-commands.md#uip-gov-access-policy-evaluate).
13. **Default new policies to `status: "Simulated"`.** Create in `Simulated` first; prompt the user to `Activate` after review via the post-create **Activate this policy** option. Emit `Active` at create time only when the user explicitly asks. See [Key Concepts § Enforcement and status](#enforcement-and-status) for the meaning of Simulated.
14. **Use user-facing terminology in user-visible text; JSON field / enum names only in code contexts.**
    - **Why:** JSON identifiers (`executableRule`, `actorRule`, `AgenticProcess`, `RPAWorkflow`) are implementation details that confuse end users.
    - **Applies to:** Spec narrative, Spec Components Table, review gate, and completion output — always say **Actor Process rule**, **Actor Identity rule**, **Maestro** (not `AgenticProcess` / "Agentic Process"), **RPA** (not `RPAWorkflow` / "RPA Workflow"). JSON names appear only inside ```json code blocks, working file paths, plugin shape templates, API enum tables, CLI flag enum lists, or CLI error messages.
15. **Resolve names to UUIDs via Orchestrator lookups.** When the user names a specific process / agent / flow / user / robot, run the lookups in [resource-lookup-guide.md](./references/resource-lookup-guide.md) — **never fabricate a UUID**. **Processes are folder-scoped**: if the user did not name a folder, run `uip or folders list` FIRST. **Translate the type string** — Orchestrator's `--process-type` is NOT the same as the access-policy enum (`AgenticProcess`→`ProcessOrchestration`, `RPAWorkflow`→`Process`, `APIWorkflow`→`Api`); see [the mapping table](./references/resource-lookup-guide.md#access-policy-type--orchestrator---process-type). For robots, see Critical Rule #16 — they resolve to a `User` UUID via [resource-lookup-guide.md § Robots](./references/resource-lookup-guide.md#robots-resolve-to-type-user).
16. **`actorRule.values[]` accepts at most two entries — one `User`, one `Group`.**
    - **Why:** the API rejects duplicate-type entries, mismatched operators across `User` and `Group`, and `ExternalApplication`.
    - **Applies to:** every `actorRule` block.
        - **(a)** At most one entry per type — merge same-type identities into a single entry's `values[]` array.
        - **(b)** When both `User` and `Group` are present, operators must match (both `Or` or both `None`); mixed-operator intent splits into two policies.
        - **(c)** `ExternalApplication` is unsupported — refuse and route to User / Group / no-actor.
        - **(d)** "Robot User" is a kind of User: design-time UX shows `User` / `Robot User` / `Group`, but JSON always emits `type: "User"`. Look up the robot via [resource-lookup-guide.md § Robots](./references/resource-lookup-guide.md#robots-resolve-to-type-user), resolve to the linked User UUID, and merge into the single `User` entry. Never emit `type: "Robot"` or `type: "ExternalApplication"`.

## Quick Start

These steps cover **creating a new access policy from scratch**. For existing policies or targeted operations, jump to the [Task Navigation](#task-navigation) table below.

### Step 0 — Verify the `uip` CLI

```bash
which uip && uip --version
```

If not installed:
```bash
npm install -g @uipath/uipcli
```

### Step 1 — Check login status

See [access-policy-commands.md — Authentication](./references/access-policy-commands.md#authentication) for the login flow (`uip login status`, `uip login`, non-production `--authority`, tenant scoping for `evaluate`).

### Step 2 — Phase 1: author the Policy Spec

Hand off to [planning-arch.md](./references/planning-arch.md). It builds a **Policy Spec** with two synchronized parts:

1. **Spec narrative** — a 3–6 sentence plain-English paragraph describing the policy. Becomes the `description` field at create time.
2. **Spec Components Table** — one row per access-policy component (name, description, status, enforcement, resource type, resource scope, resource tag filter, actor process type, actor process scope, actor process tag filter, actor identity type, actor identity scope). The agent pre-fills every row with the user's values or sensible defaults — the user reviews and edits, not fills in blanks. **Note:** there is no Actor Identity tag filter row — `actorRule` does not support tags today.

The user reviews the pre-filled Spec and changes any row they want; the agent re-derives the narrative after every round so the two parts stay in sync. Phase 1 ends when every Open question is closed and the user approves with `yes`.

> **If the user has no concrete intent** ("just create an access policy", "help me make one") **or supplied only one of the four phrase categories** (Resource / Actor Process / Actor Identity / Tag), Phase 1 routes through [sample-policy-guide.md](./references/sample-policy-guide.md) FIRST — it surfaces a canonical Spec narrative + JSON and offers the user three paths: adopt as-is, adapt one block, or describe from scratch. The chosen path seeds the Spec; the user still iterates rows and approves before Phase 2.

### Step 3 — Phase 2: compose the JSON via plugins

Hand off to [planning-impl.md](./references/planning-impl.md). It gathers the active auth context, then walks each row of the approved **Spec Components Table** and reads the matching plugin's `impl.md`:

- Each Resource entry (Spec rows 5–7 — type, scope, optional tag filter) → one `selectors[]` entry via [plugins/selector/impl.md](./references/plugins/selector/impl.md)
- Each Actor Process entry (Spec rows 8–10 — type, scope, optional tag filter) → one `executableRule.values[]` entry via [plugins/executable/impl.md](./references/plugins/executable/impl.md)
- Each Actor Identity entry (Spec rows 11–12 — type, scope) → one `actorRule.values[]` entry via [plugins/actor/impl.md](./references/plugins/actor/impl.md). **No tag filter** — `actorRule.tags` is unsupported (Critical Rule #5).
- Every Resource / Actor Process tag-filter row → `tags` sub-object via [plugins/tags/impl.md](./references/plugins/tags/impl.md)

Phase 2 reuses the slug Phase 1 used for the Spec file and writes the assembled `PolicyDefinition` to `/tmp/access-policy-<slug>.json`, so the Spec (`.spec.md`) and JSON (`.json`) sit side by side. Phase 2 hands back both paths.

### Step 4 — Single review gate

Show a **short human-readable summary** that includes:
- A **Scope** line on top — `Organization "<NAME>" / Tenant "<NAME>"` plus the matching `organizationId` / `tenantId` UUIDs from the safe auth-context workflow — so the user always sees which environment they are about to mutate before approving.
- One plain-English line per block — `Resources`, `Actor Process`, `Actor Identity` — with the per-entry technical breakdown tucked inside a collapsible `<details>` section.

Then output the complete JSON as a ```json code block in the chat (do not rely on the file links alone — the user may not be able to open them), plus clickable markdown links to **both** files using their **resolved absolute paths** (Critical Rule #7):
- `/tmp/access-policy-<slug>.spec.md` — the human-readable Policy Spec from Phase 1
- `/tmp/access-policy-<slug>.json` — the JSON payload Phase 2 will submit

See [policy-manage-guide.md — Create Step 4](./references/policy-manage-guide.md#step-4--single-review-gate) for the exact layout, the auth-context source mapping for the Scope line, and the phrasing rules. Use the canonical wording from [Confirmation-gate wording](#confirmation-gate-wording) below. This is the only confirmation gate in the create flow.

### Step 5 — Create

```bash
uip gov access-policy create --file /tmp/access-policy-<slug>.json --output json
```

Record `Data.upsertedPolicy.id` as the new policy UUID. If `Data.errors` is non-null, surface the error and route back to Step 4 (`keep editing`).

### Step 6 — Verify

```bash
uip gov access-policy get <POLICY_ID> --output json
```

Display the raw server-stored JSON to the user.

### Step 7 — Post-create choice

Render next steps as a **numbered Markdown list** under a `### What would you like to do next?` heading so the user can reply with the number. Do NOT use `AskUserQuestion`. The list is **conditional on the policy's `status`** — if the policy is `Simulated` (the default), the first option is **Activate this policy** so the user can flip it to effective. See [Completion Output](#completion-output) below for the exact lists. Do NOT offer `Evaluate` and do NOT auto-run `evaluate` (Critical Rule #12).

## Anti-patterns

Non-obvious mistakes the Critical Rules don't already cover by name. (Restatements of Critical Rules — hardcoded org/tenant, `enforcement: "Deny"`, missing `values`, auto-running `evaluate`, stacking confirmation gates — live with the rules themselves.)

- Do NOT hand-author policy JSON. Every policy flows through Phase 1 Spec → Phase 2 plugins; plugin `impl.md` files are the only authoritative JSON source.
- Do NOT skip the Spec review just because the user "already gave you everything" — the Spec, not the chat history, is the contract.
- Do NOT silently drop actor-shaped intent (e.g. "only admins can…", "when robot X triggers…"). Emit `actorRule` whenever identity intent is expressed.
- Do NOT emit `actorRule` when the user gave no actor constraint — adding an unrequested `actorRule` narrows scope silently.
- Do NOT merge distinct resource or executable types into one entry — one `selectors[]` entry per `resourceType`, one `executableRule.values[]` entry per executable `type`. (For `actorRule`, same-type identities merge — see Critical Rule #16.)
- Do NOT put `RPAWorkflow` or `APIWorkflow` in `executableRule.values[].type` — they are resource-only.
- Do NOT use `operator: "And"` on `values` — only `Or` / `None`. `And` is only valid on `tags`.
- Do NOT put resource or actor UUIDs in `tags.values` — different arrays.
- Do NOT start an update from a fresh Phase 1 Spec — server `Data` is the source of truth (Critical Rule #8).

## Task Navigation

| I need to... | Read these |
| --- | --- |
| **Author a Policy Spec from intent** | Quick Start + [planning-arch.md](./references/planning-arch.md) — narrative paragraph + Spec Components Table |
| **Start from a sample when the user has no concrete intent** | [sample-policy-guide.md](./references/sample-policy-guide.md) — canonical Spec narrative + JSON with a 3-option picker (use as-is / adapt / from scratch) |
| **Compose the concrete JSON from an approved Spec** | [planning-impl.md](./references/planning-impl.md) + the relevant plugin `impl.md` |
| **Create a policy (end-to-end)** | [policy-manage-guide.md — Create](./references/policy-manage-guide.md#create-a-policy) |
| **Update a policy** | [policy-manage-guide.md — Update](./references/policy-manage-guide.md#update-a-policy) — start from server `Data`, NOT a fresh Phase 1 Spec (Rule #9) |
| **Delete a policy** | [policy-manage-guide.md — Delete](./references/policy-manage-guide.md#delete-a-policy) — show summary + explicit `yes` (Rule #10) |
| **List policies** | [policy-manage-guide.md — List](./references/policy-manage-guide.md#list-policies) |
| **Get a single policy by UUID** | [policy-manage-guide.md — Get](./references/policy-manage-guide.md#get-a-policy) |
| **Evaluate a policy against a request context** | [access-policy-commands.md — evaluate](./references/access-policy-commands.md#uip-gov-access-policy-evaluate) — user-initiated only (Rule #13) |
| **Resolve a process / agent / flow / user / robot name to a UUID** | [resource-lookup-guide.md](./references/resource-lookup-guide.md) — `uip or processes list` / `uip or folders list` / `uip or users list`; robot intent resolves to the linked User UUID without exposing auth tokens |
| **Compose a `selectors[]` entry (Selection Rule)** | [plugins/selector/planning.md](./references/plugins/selector/planning.md) + [plugins/selector/impl.md](./references/plugins/selector/impl.md) |
| **Compose the `executableRule` block (Actor Process Rule)** | [plugins/executable/planning.md](./references/plugins/executable/planning.md) + [plugins/executable/impl.md](./references/plugins/executable/impl.md) |
| **Compose the `actorRule` block (Actor Identity Rule)** | [plugins/actor/planning.md](./references/plugins/actor/planning.md) + [plugins/actor/impl.md](./references/plugins/actor/impl.md) |
| **Pick tag operators / flip Deny→Allow** | [plugins/tags/planning.md](./references/plugins/tags/planning.md) + [plugins/tags/impl.md](./references/plugins/tags/impl.md) |
| **Look up CLI flags and output shapes** | [access-policy-commands.md](./references/access-policy-commands.md) |

## Key Concepts

### Policy type

Every policy this skill mutates is of type `ToolUsePolicy`. The API exposes other policy types but they are out of scope — this skill treats any non-`ToolUsePolicy` response from `get` as read-only.

### The three rule blocks (Selection / Actor Process / Actor Identity)

A `ToolUsePolicy` access policy is structured as three rule blocks evaluated against a tool-use request:

| Block | Governs | Required? | Shape |
|---|---|---|---|
| `selectors[]` — **Selection Rule** | The child **Resource/Tool** being invoked | **Yes** | Array — one entry per resource `type`. Each entry has `values` + optional `tags`. |
| `executableRule` — **Actor Process Rule** | The calling **workflow** (Actor Process) | **Yes** | Object with `values[]` (one entry per executable `type`) + optional shared `tags`. |
| `actorRule` — **Actor Identity Rule** | The **identity** running the Actor Process (User or Group) | Optional | Object with `values[]` carrying **at most two entries** — one `User`, one `Group`. When both are present, their `operator` must match. **No `tags`** — not supported on `actorRule` today (Critical Rule #5). |

**Resource/Tool types** (`selectors[].resourceType`): `Agent`, `AgenticProcess`, `RPAWorkflow`, `APIWorkflow`, `CaseManagement`, `Flow`.
**Actor Process types** (`executableRule.values[].type`): `Agent`, `AgenticProcess`, `CaseManagement`, `Flow`. (RPA and API workflows are resource-only — they cannot be callers.)
**Actor Identity types** (`actorRule.values[].type`): `User`, `Group` only. `actorRule.values[]` carries **at most two entries** — one `User` entry, one `Group` entry — and when both are present their `operator` must match (both `Or` or both `None`). Multiple users / groups go inside the single entry's `values[]` array, never as duplicate entries of the same type. `ExternalApplication` is **not supported** today. **Design-time / Spec terminology** distinguishes "User" from "Robot User" (a robot is a kind of user), but **both serialize as `type: "User"`** in the JSON — the skill never emits `type: "Robot"`. See Critical Rule #16.

### PAP vs PDP (two API endpoints)

The CLI wraps two endpoints:
- **PAP (Policy Administration Point)** — `list` / `get` / `create` / `update` / `delete` operate on policy records in the catalog.
- **PDP (Policy Decision Point)** — `evaluate` asks the service to resolve the effective decision for a concrete request context. `evaluate` requires tenant-scoped login (Critical Rule #12).

### Evaluation & aggregation

Per-request decision flow:
1. The PDP finds every policy whose **Selection Rule** matches the Resource/Tool.
2. For each matched policy, it evaluates the **Actor Process Rule** AND the **Actor Identity Rule** (if present) against the request.
3. A policy evaluates to **Allow** when every present rule matches; otherwise the policy does **not contribute** (no-match — call it `NoOp` for that policy).
4. **Aggregation** across all non-simulated matched policies:
   - Any matching `Allow` → final enforcement `Allow`.
   - No matching `Allow` → request falls through to the runtime default (`Deny` / `NoOp`).
5. `enforcement: "Deny"` is **not authorable** (Critical Rule #2) — Deny is the default outcome when no Allow policy matches. To "block" something, write an Allow policy that targets the **complement** of what should be blocked (or use `operator: "None"` on `tags` / `values`).
6. `status: "Simulated"` policies are excluded from aggregation (see [Enforcement and status](#enforcement-and-status)).

### Tags (Resource Catalog Tags)

Tags are named labels attached to resources in the UiPath Resource Catalog. Used inside `selectors[].tags` and `executableRule.tags` to narrow scope. Operators: `Or` (any), `And` (all), `None` (exclude). The `None` operator is also how Deny intents get flipped into Allow policies — see [plugins/tags/planning.md](./references/plugins/tags/planning.md). **`actorRule` does NOT support tags today** — never emit `actorRule.tags` (Critical Rule #5 / [plugins/actor/](./references/plugins/actor/)).

### Enforcement and status

- `enforcement`: **always `"Allow"`** — `"Deny"` is not authorable (Critical Rule #2). The runtime delivers Deny by default when no Allow policy matches, so "blocking" intent is expressed by writing an Allow policy targeting the complement of what should be blocked.
- `status`: `Active` (counted in runtime aggregation) or `Simulated` (the policy IS evaluated, but its verdict is excluded from aggregation — it shows up in `evaluationDetails` for debugging only). **Default `Simulated` for newly created policies** (Critical Rule #13) — it is the safe way to preview a rule before flipping to `Active`. Do not conflate Simulated with "disabled" or "draft". Other places in the skill that refer to "Simulated" link back here for the meaning.

### Authoring Deny intent as Allow (internal mechanic)

`enforcement: "Deny"` is not authorable (Critical Rule #2). The agent silently translates Deny intent into an Allow shape and never exposes the mechanic to the user. See [plugins/tags/planning.md — Deny-to-Allow flip](./references/plugins/tags/planning.md#deny-to-allow-flip) for the decision logic and worked examples.

### Working file convention

Two paired files live in `/tmp` for every create flow:

| File | Written by | Purpose |
|------|------------|---------|
| `/tmp/access-policy-<slug>.spec.md` | Phase 1 ([planning-arch.md — Spec file convention](./references/planning-arch.md#spec-file-convention)) | Human-readable Policy Spec — narrative paragraph + Spec Components Table. Re-written on every Phase 1 iteration round once the policy name (Spec row 1) is set. |
| `/tmp/access-policy-<slug>.json` | Phase 2 ([planning-impl.md — Step 4](./references/planning-impl.md#step-4--write-the-working-file)) | Raw `PolicyDefinition` JSON submitted to `uip gov access-policy create`. |

The slug is computed from the policy name and is identical across both files — they sit side by side in `/tmp` so the user can diff `.spec.md` against `.json` to confirm Phase 2 didn't drift from the approved Spec. Show **both** paths in the review gate as clickable markdown links using their **resolved absolute paths** (run `realpath` — Critical Rule #7).

For **update** flows the file is `/tmp/access-policy-<id>-working.json` only — there is no `.spec.md` because the existing server-stored definition is the source of truth (Critical Rule #8), not a freshly-authored Spec.

### Confirmation-gate wording

Every mutation runs through a single `yes / no` review (Critical Rule #7). Use these templates verbatim so wording stays consistent across the skill:

| Operation | Template |
|-----------|----------|
| Create | `Create access policy "<POLICY_NAME>"? (yes / no / keep editing)` |
| Update | `Apply update to access policy "<POLICY_NAME>"? (yes / no / keep editing)` |
| Delete (single) | `Delete access policy "<POLICY_NAME>"? This cannot be undone. (yes / no)` |
| Delete (multi) | `Delete <N> access policies (<POLICY_NAME_1>, <POLICY_NAME_2>, ...)? This cannot be undone. (yes / no)` |

`keep editing` is treated the same as `no` — route the user back to the step that owns the field being changed (metadata → [policy-manage-guide.md — Create Step 3](./references/policy-manage-guide.md#create-a-policy); a specific block → the matching plugin's `impl.md`; intent itself → [planning-arch.md](./references/planning-arch.md)) and re-enter the gate only after the change is applied.

## Completion Output

When you finish a mutating operation, report:

1. **Operation & result** — e.g., `Created access policy "<NAME>" (ID: <POLICY_ID>) — Resources: <RESOURCE_SUMMARY> · Actor Process: <ACTOR_PROCESS_SUMMARY> · Actor Identity: <ACTOR_IDENTITY_SUMMARY or "any identity">`. Use plain-English phrasing ("all Agent resources tagged 'Production'"), not JSON terms like `resourceType` / `operator`.
2. **Status banner** — if the new/updated policy is `Simulated`, print: `⚠️ This policy is in Simulated mode — it is evaluated but does NOT affect enforcement. Activate it when you want it to take effect.`
3. **Working file paths** — print the absolute paths the operation used:
    - For `create`: both `/tmp/access-policy-<slug>.spec.md` (the approved Policy Spec) and `/tmp/access-policy-<slug>.json` (the submitted JSON).
    - For `update`: `/tmp/access-policy-<id>-working.json` only.
    The user can re-open these to inspect what was sent.
4. **Technical details** — wrap the per-entry breakdown (resource types, process types, identity types, tag filters) in a `<details><summary>Show technical details</summary>…</details>` block so it is collapsed by default. (Omit after `delete`.)
5. **Next step** — present the options as a **numbered Markdown list under a `### What would you like to do next?` heading** so the user can reply with the number. Do NOT use `AskUserQuestion`, do NOT render as a table, and do NOT wrap the list in `<details>`. The "Something else" option is always last. Options depend on the current `status` of the policy:

**After `create` or `update` where `status == "Simulated"`** (the default):

```markdown
### What would you like to do next?

1. **Activate this policy** — re-run `update` with the working file patched to `status: "Active"` via [policy-manage-guide.md — Update](./references/policy-manage-guide.md#update-a-policy). Recommended follow-up — Simulated policies do not enforce anything.
2. **List policies to verify** — run `uip gov access-policy list --output json` and show the new/updated entry.
3. **Update this policy** — jump to [policy-manage-guide.md — Update](./references/policy-manage-guide.md#update-a-policy) with this policy ID.
4. **Create another policy** — return to Quick Start Step 2.
5. **Something else** — accept free-form string input and act on it.

Reply with the number.
```

**After `create` or `update` where `status == "Active"`:**

```markdown
### What would you like to do next?

1. **List policies to verify** — run `uip gov access-policy list --output json` and show the new/updated entry.
2. **Update this policy** — jump to [policy-manage-guide.md — Update](./references/policy-manage-guide.md#update-a-policy) with this policy ID.
3. **Create another policy** — return to Quick Start Step 2.
4. **Something else** — accept free-form string input and act on it.

Reply with the number.
```

**After `delete`:** offer only:

```markdown
### What would you like to do next?

1. **List policies to verify** — run `uip gov access-policy list --output json`.
2. **Something else** — accept free-form string input and act on it.

Reply with the number.
```

**Do NOT offer `Evaluate this policy` in the post-mutation list** — end users creating or updating a policy do not need to dry-run it, and dummy-UUID evaluations produce confusing results (Critical Rule #12). `evaluate` remains available on demand only when the user explicitly asks; route via [access-policy-commands.md — evaluate](./references/access-policy-commands.md#uip-gov-access-policy-evaluate) (real UUIDs + tenant-scoped login required — Critical Rule #12).

Do not run any of these actions automatically. Wait for the user's selection.

## References

- **[access-policy-commands.md](./references/access-policy-commands.md)** — single source of truth for every `uip gov access-policy` subcommand, its flags, input/output shapes, and authentication. Every other guide links here for command details rather than inlining them.
- **[resource-lookup-guide.md](./references/resource-lookup-guide.md)** — `uip or processes list` / `uip or folders list` / `uip or users list` lookups to resolve human-readable names to the UUIDs required by `selectors[].values`, `executableRule.values[].values`, and `actorRule.values[].values`. Route here whenever the user names a process, folder, or user without supplying a UUID.
- **[planning-arch.md](./references/planning-arch.md)** — Phase 1: author a **Policy Spec** (narrative paragraph + Spec Components Table covering name, description, status, enforcement, resource selection, actor process, actor identity, tags, operators). The agent pre-fills every row; the user reviews and edits before approving, and approval is required before any JSON is composed.
- **[sample-policy-guide.md](./references/sample-policy-guide.md)** — canonical Spec narrative + JSON (Production Agent + one Maestro + one User, Allow, Simulated). Phase 1 routes here when the user has no concrete intent or has gaps; surfaces a 3-option picker so the user can adopt, adapt, or replace the sample.
- **[planning-impl.md](./references/planning-impl.md)** — Phase 2: walk the approved Spec Components Table and assemble the concrete `PolicyDefinition` JSON by gathering the safe auth context and reading each plugin's `impl.md` for block-level JSON.
- **[policy-manage-guide.md](./references/policy-manage-guide.md)** — Full CRUD lifecycle (list / get / create / update / delete). Owns the single final-review gate before every mutation.
- **[plugins/selector/](./references/plugins/selector/)** — `selectors[]` (Selection Rule): resource/tool types (`Agent`, `AgenticProcess`, `RPAWorkflow`, `APIWorkflow`, `CaseManagement`, `Flow`), targeting modes, tag filters.
- **[plugins/executable/](./references/plugins/executable/)** — `executableRule` (Actor Process Rule): executable types (`Agent`, `AgenticProcess`, `CaseManagement`, `Flow`), targeting modes, shared tag filter.
- **[plugins/actor/](./references/plugins/actor/)** — `actorRule` (Actor Identity Rule): identity types (`User`, `Group` only — `ExternalApplication` not supported; robot intent serializes as `User`), targeting modes. **No tag filter today** — emitting `actorRule.tags` is rejected by the API. Optional block — emit only when the user supplies actor-shaped intent.
- **[plugins/tags/](./references/plugins/tags/)** — shared `tags` sub-object with `Or` / `And` / `None` operators and the Deny-to-Allow flip.
