# Phase 1 — Discovery & Spec Authoring

Help the user **describe their access policy as a natural-language Spec** before any JSON is composed. The Spec is the user-facing model of the policy: a short plain-English paragraph plus a managed component table that lists every block an access policy supports. Phase 1 ends when the Spec is complete, internally consistent, and explicitly approved.

> **Read this first, always.** No access-policy JSON is ever authored without an approved Phase 1 **Spec** (Critical Rule #6). The Spec — not raw user text — is the contract handed to Phase 2.

---

## What the Spec is

The **Policy Spec** has two parts that the agent maintains together throughout Phase 1:

| Part | Format | Purpose |
|---|---|---|
| **Spec narrative** | A structured natural-language block — bold-quoted title + opening sentence + bulleted components (**What is being protected**, **Who/what is allowed to call them**, **Effect**, **Status**) + final **Intent** paragraph. See [Spec narrative format](#spec-narrative-format). The same shape as the description block in [sample-policy-guide.md](./sample-policy-guide.md). | The user reads this to confirm the agent understood their intent. The opening sentence + Intent paragraph distill into the `description` field on the policy. |
| **Spec Components Table** | A single managed table with one row per access-policy component (name, description, status, enforcement, resource selection, actor process, actor identity, tag filters on Resource and Actor Process only, operators). Every row is **pre-filled** with the user's value or a sensible default; only rows with no defensible default are marked `(missing)`. | The user reviews the pre-filled Spec and edits any row; the agent updates the narrative after each round. The table is what Phase 2 walks. |

Both parts are kept in sync: every change to the table updates the narrative, and vice versa. Show **both** to the user every time you re-present the Spec.

---

## Process

1. **Read the user's request.** Extract resource phrases, actor process phrases, tag phrases, and actor-identity phrases (user, robot user, or group — Critical Rule #16). Use the [Intent analysis](#intent-analysis) heuristics below.
2. **If the user has no concrete intent or named ≤ 1 of the four phrase categories** (Resource / Actor Process / Actor Identity / Tag), route through [Sample-policy starter (when intent is missing or sparse)](#sample-policy-starter-when-intent-is-missing-or-sparse) BEFORE generating the Spec — show the canonical sample, let the user pick a path, and seed the Spec from the user's choice.
3. **Generate the initial Spec — fully pre-filled.** Build the narrative paragraph and Spec Components Table with **a concrete value in every row** (don't leave rows empty for the user to fill in). For values the user explicitly supplied, use those. For values they didn't, apply sensible defaults (Critical Rule #11 — don't ask, just do):
    - **Scope rows (Org / Tenant — read-only):** capture both rows from the active auth context BEFORE generating the rest of the Spec. Read **names** via `uip login status --output json` (`Data.Organization`, `Data.Tenant`) and gather UUIDs with [access-policy-commands.md — Auth context for policy payloads](./access-policy-commands.md#auth-context-for-policy-payloads). Render each row as `<NAME> (UUID <UUID>)`. Mark these rows as read-only — the user changes them by re-running `uip login` (Critical Rule #1), not by editing the Spec. They appear above the numbered rows so the user always sees which environment the policy will be authored against.
    - **Row 1 (Name):** ALWAYS suggest a name derived from intent — never `(missing)`. Pattern: `"Allow <ResourceSummary> in <ActorProcessSummary>"` (e.g. `"Allow Production Agents in Maestro"`). Use user-facing names (`Maestro` for `AgenticProcess` — Critical Rule #14).
    - **Row 2 (Description):** auto-derive from the narrative paragraph.
    - **Row 3 (Status):** `Simulated` (Critical Rule #13).
    - **Row 4 (Enforcement):** `Allow` (Critical Rule #2 — fixed).
    - **Resource / Actor Process scope (rows 6, 9):** default to `all` (`["*"]`) when no UUIDs were named. Specific UUIDs only when the user named them.
    - **Tag filter rows (7, 10):** `(none)` unless the user mentioned tags.
    - **Actor Identity rows (11–12):** omit entirely unless the user expressed identity intent. Don't add an unrequested identity constraint.
    - **Mark a row `(missing)` only when there is genuinely no defensible default** (e.g. row 5 Resource type when the user never hinted at any). Surface those as Open questions — but limit Open questions to truly ambiguous cases.
    Use the format in [Spec output format](#spec-output-format).
4. **Enter the Spec review loop.** Present the fully pre-filled Spec (narrative + table) and tell the user they can change any row. Treat this as **review-and-edit**, not fill-in-the-blanks. The user may approve immediately, edit specific rows, or revise the whole policy. After each round:
    - Apply the user's edits to the table.
    - Re-derive the narrative paragraph from the updated table so the two stay in sync.
    - Re-resolve any newly-named processes / agents / users to UUIDs via [resource-lookup-guide.md](./resource-lookup-guide.md) (Critical Rule #15).
    - Re-present the Spec.
    - Stop the loop when no Open question remains and the user approves.
5. **Write the Spec file.** Once the Spec is fully pre-filled and every Open question is closed, write the Spec (narrative + Spec Components Table) to `/tmp/access-policy-<slug>.spec.md` so the user can open and review it in their editor alongside the JSON Phase 2 will produce. See [Spec file convention](#spec-file-convention) for the slug rule and file body.
6. **Run the [Review gate](#review-gate)** — ask `Approve this access-policy Spec to proceed to Phase 2? (yes / edit / cancel)` and surface a clickable link to the Spec file. `edit` returns to step 4 and re-writes the Spec file after the change is applied; `cancel` drops the session.
7. **Hand off to** [planning-impl.md](./planning-impl.md). The approved Spec is the input — Phase 2 walks the Spec Components Table, reads each plugin's `impl.md`, and writes the JSON to `/tmp/access-policy-<slug>.json` using **the same slug as the Spec file** so the two files sit side by side.

> The agent NEVER advances to Phase 2 without an explicit `yes` on the Spec. The Spec, not the user's chat history, is what Phase 2 acts on.

---

## Sample-policy starter (when intent is missing or sparse)

When the user's request cannot be classified into Resource / Actor Process / Actor Identity / tag phrases, or names ≤ 1 of those four categories, read [sample-policy-guide.md](./sample-policy-guide.md) and present the canonical sample (narrative description + JSON) verbatim, then offer the three-option picker defined there:

1. **Use the sample as-is** → seed the Spec to match the sample (Production-tagged Agent + one Maestro + one User, Allow, Simulated). Run [resource-lookup-guide.md](./resource-lookup-guide.md) to resolve real Maestro and User UUIDs. Continue at step 3 (Generate the initial Spec) with all rows pre-filled.
2. **Adapt the sample** → seed the Spec from the sample for blocks the user did NOT change; mark the changed blocks as `(missing)` in the table. Continue at step 3.
3. **Describe from scratch** → drop the sample. Continue at step 1 with the user's description.

Even when the user picks Option 1, the Review gate (step 6) is mandatory — the Spec still requires explicit approval before Phase 2.

---

## Intent analysis

Parse the user's phrasing into four categories. Each maps to one or more rows in the Spec Components Table.

### Resource phrases → [selector](./plugins/selector/planning.md)

Phrases describing **what is being used**:

- "Production Agent", "agents tagged Development", "my RPA workflows", "API workflow", "case management item", "flow named abc-123".
- Quantifier patterns: "all agents" → `values: ["*"]`; "agent `<uuid>`" or "process abc-123" → specific IDs.

Record one Resource entry per distinct resource type. If the user names two different resource types (e.g. "Agents and Flows"), the Spec table holds two Resource rows.

### Actor Process phrases → [executable](./plugins/executable/planning.md)

Phrases describing **who/what uses the resource**:

- "used by a Maestro", "invoked from a flow", "only maestro can call", "when case management triggers it" (user phrases like "agentic process" / "maestro process" all map to user-facing **Maestro** / JSON `AgenticProcess`).
- Same quantifier logic: `["*"]` for "any", specific IDs for named callers.

Record one Actor Process entry per distinct executable type.

### Tag phrases → [tags](./plugins/tags/planning.md)

Any environment, team, or Resource Catalog tag:

- "Production", "Development", "Staging", "Critical", "PII", product names, team names.
- Operator hints:
  - "Production **or** Staging" → `Or` (Any-of)
  - "both Production **and** Critical" → `And` (All-of)
  - "**not** Development", "**except** Dev-tagged" → `None` (Exclude)

**Deny phrases — translate silently.** When the user says "block Development agents", "deny Staging flows", "prevent Production-tagged from being used", the agent silently authors an Allow policy that excludes the named set. Write the narrative in plain English about **what's allowed**; never mention "Deny→Allow flip", "None operator", or "enforcement is not authorable" in the Spec or table. See [plugins/tags/planning.md — Deny-to-Allow flip](./plugins/tags/planning.md#deny-to-allow-flip) for the decision logic and framing examples.

### Actor-identity phrases → [actor](./plugins/actor/planning.md)

Phrases describing **who triggers the Actor Process** (user, robot user, or group — see Critical Rule #16):

- "only admins can…", "restrict user X", "members of group Ops", "when robot R runs…", "on behalf of…".
- **Allowed design-time choices: `User`, `Robot User`, `Group`.** `User` and `Robot User` both serialize as `type: "User"` in the JSON — the skill never emits `type: "Robot"`. **`ExternalApplication` is not supported** — if the user names a service principal / external app, refuse and route them to use a User, Robot User, or Group (or omit the Actor Identity rule).
- Quantifier patterns: `["*"]` for "any user"; specific UUIDs for named users / robot users.
- Operator hints: "only X" → `Or`; "block X", "everyone except X" → `None` (Deny-flipped).

Record at most two Actor Identity entries — one `User` entry (which absorbs Robot User intent) plus one `Group` entry (Critical Rule #16). Multiple users / robot users / groups of the same type are merged into a single entry's scope, never split. When both entries are present, their scope-style must match (both include or both exclude). Omit the Actor Identity rows entirely when the user said nothing about identity — **absence means "no identity constraint"**, which is the correct default.

---

## The three rule blocks (boundary table)

An access policy has three rule blocks. Use this table to decide which block a user phrase belongs in. Plugin anti-pattern sections link back here instead of repeating the boundary.

| Block | Targets | JSON field | Allowed types | Tag filter? |
|---|---|---|---|---|
| Selection Rule | The Resource being protected (the thing being used) | `selectors[]` | `Agent` / `AgenticProcess` / `RPAWorkflow` / `APIWorkflow` / `CaseManagement` / `Flow` | per-entry (`selectors[N].tags`) |
| Actor Process Rule | The calling workflow (Maestro / Agent / Flow / CaseManagement) | `executableRule` | `Agent` / `AgenticProcess` / `CaseManagement` / `Flow` (NOT `RPAWorkflow` / `APIWorkflow`) | shared at top of block (`executableRule.tags`) |
| Actor Identity Rule | The user / group triggering the workflow | `actorRule` | `User` / `Group` only (Robot resolves to `User`; `ExternalApplication` unsupported) | **not supported** |

A user phrase that names a thing-being-used belongs in `selectors[]`. A phrase that names a workflow doing the calling belongs in `executableRule`. A phrase that names a person, group, or robot identity belongs in `actorRule`.

---

## Plugin Index

The Spec Components Table maps to plugins one-to-one. Phase 2 walks the table and reads each plugin's `impl.md` to compose the JSON.

| Spec component | Plugin | Always present? |
|---|---|---|
| Resource selection (one row per resource type) | [selector](./plugins/selector/planning.md) | **Yes.** Identifies what is being used. |
| Resource tag filter (per-resource sub-row) | [tags](./plugins/tags/planning.md) | Only when the user mentioned tags on the resource side. |
| Actor Process (one row per process type) | [executable](./plugins/executable/planning.md) | **Yes.** Identifies the caller. |
| Actor Process tag filter | [tags](./plugins/tags/planning.md) | Only when the user mentioned tags on the caller side. |
| Actor Identity (one row per design-time identity type — `User` / `Robot User` / `Group`) | [actor](./plugins/actor/planning.md) | **Only when the user expressed identity intent.** Omit otherwise — absence = any identity passes. `User` and `Robot User` both serialize as `type: "User"`; `ExternalApplication` is not supported. |

> **Note:** the Actor Identity rule does **not** support tags today. The Spec Components Table omits an "Actor Identity tag filter" row, and `actorRule.tags` must never be emitted in the JSON. Only Resource and Actor Process blocks support tag filters.

---

## Spec output format

Present the Spec as **structured narrative + Spec Components Table** every time. The narrative is human-readable; the table is the contract. Do NOT write JSON in Phase 1 — JSON is Phase 2's job. See [Spec narrative format](#spec-narrative-format) for the narrative template.

```markdown
**Policy Spec — review and edit any row below. You can change one at a time or all at once.**

> **"<POLICY_NAME_AS_TITLE>"**
>
> <ONE_OPENING_SENTENCE describing the policy type ("tool-use policy"), status mode ("simulation mode" / "active mode"), and the high-level effect — who is allowed to invoke what.>
>
> - **What is being protected:** <plain-English Resource summary — type(s), scope (all / specific UUIDs / all-except), tag filter if any. Use "all `<TYPE>` resources" / "the `<TYPE>` named `<NAME>` (UUID `<UUID>`)" / "every `<TYPE>` except `<NAME>` (UUID `<UUID>`)".>
> - **Who/what is allowed to call them:** <plain-English Actor Process summary, then Actor Identity summary. If no Actor Identity row, say "any User or Group running these Actor Processes".>
> - **Effect:** `Allow` — the matching call is permitted.
> - **Status:** `<Simulated | Active>` — <one-line meaning: Simulated = "evaluated and logged but not yet enforced, so violations are surfaced for review without blocking real traffic"; Active = "evaluated and counted toward the runtime aggregation — matching calls are permitted by this policy".>
>
> **Intent:** <2–3 sentences describing the *why* behind the policy — the user's underlying goal, the risk it controls, or the lifecycle stage. Carry over the user's framing verbatim where it is clear; do not invent intent the user did not express. Mention the simulation rationale when status is Simulated.>

| # | Component | Allowed values | Current value | Required? |
|---|-----------|---------------|--------------|-----------|
| — | Organization (read-only)      | sourced from active auth context — change via `uip login`                       | <ORG_NAME> (UUID `<ORG_ID>`)                   | Scope (read-only) |
| — | Tenant (read-only)            | sourced from active auth context — change via `uip login`                       | <TENANT_NAME> (UUID `<TENANT_ID>`)             | Scope (read-only) |
| 1 | Policy name                   | string — always pre-filled                                                       | <suggested name>                               | Required |
| 2 | Description                   | one sentence — auto-derived from the narrative above                             | <description>                                  | Required |
| 3 | Status                        | `Simulated` (default) / `Active`                                                 | `Simulated`                                    | Required |
| 4 | Enforcement                   | `Allow`                                                                          | `Allow`                                        | Required (fixed) |
| 5 | Resource type(s)              | `Agent` / `Maestro` / `RPA` / `APIWorkflow` / `CaseManagement` / `Flow`           | <type(s)>                                      | Required |
| 6 | Resource scope                | `all` / specific UUIDs / all-except UUIDs                                        | <scope — default `all`>                        | Required |
| 7 | Resource tag filter           | Any-of [<tags>] / All-of [<tags>] / Exclude [<tags>] / `(none)`                  | <filter — default `(none)`>                    | Optional |
| 8 | Actor Process type(s)         | `Agent` / `Maestro` / `CaseManagement` / `Flow`                                  | <type(s)>                                      | Required |
| 9 | Actor Process scope           | `all` / specific UUIDs / all-except UUIDs                                        | <scope — default `all`>                        | Required |
| 10 | Actor Process tag filter     | Any-of / All-of / Exclude / `(none)`                                             | <filter — default `(none)`>                    | Optional |
| 11 | Actor Identity type(s)       | `User` / `Robot User` / `Group` (or blank for "any identity")                    | <type(s) — default `(none = any identity)`>    | Optional |
| 12 | Actor Identity scope         | `all` / specific UUIDs / all-except UUIDs                                        | <scope — default `n/a`>                        | Optional (required if row 11 set) |

> **Type-name footnote (rows 5, 8, 11):** the table above shows **user-facing labels**. JSON enum mapping (Critical Rule #14): `Maestro` → `AgenticProcess`; `RPA` → `RPAWorkflow`; `Robot User` → `User`. All other type names match the JSON enum.

> Every row is pre-filled with a sensible default — no `(missing)` rows in the initial Spec. Only mark a row `(missing)` when there is genuinely no defensible default and add it to the Open questions list.

**Open questions** (only when truly ambiguous — present sparingly):
  - <e.g., "I picked 'Production' tag for the Agents — should it be 'Staging' instead?">
  - <e.g., "I assumed 'Production OR Staging' — did you mean both required (AND)?">
```

### Row defaults reference

Every row gets a concrete value in the initial Spec (Critical Rule #11 — don't ask, just pre-fill). Defaults applied when the user didn't supply a value:

| Row | Required? | Default when not specified |
|---|---|---|
| — Organization (read-only) | Scope | Name from `uip login status` (`Data.Organization`); UUID from the safe auth-context workflow. Not user-editable in the Spec. |
| — Tenant (read-only) | Scope | Name from `uip login status` (`Data.Tenant`); UUID from the safe auth-context workflow. Not user-editable in the Spec. |
| 1 — Policy name | Required | Suggested from intent: `"Allow <ResourceSummary> in <ActorProcessSummary>"` |
| 2 — Description | Required | Auto-derived from the narrative |
| 3 — Status | Required | `Simulated` (Critical Rule #13) |
| 4 — Enforcement | Required (fixed) | `Allow` (Critical Rule #2) |
| 5 — Resource type(s) | Required | Mark `(missing)` ONLY if the user gave no resource hint at all → Open question |
| 6 — Resource scope | Required | `all` (`["*"]`) |
| 7 — Resource tag filter | Optional | `(none)` |
| 8 — Actor Process type(s) | Required | Mark `(missing)` ONLY if the user gave no caller hint at all → Open question |
| 9 — Actor Process scope | Required | `all` (`["*"]`) |
| 10 — Actor Process tag filter | Optional | `(none)` |
| 11–12 — Actor Identity | Optional (row 12 required if row 11 is set) | Omit entirely (no Actor Identity constraint) — Critical Rule #4 |

The Spec is "ready" once every Open question is closed.

### Spec narrative format

The narrative is a structured block, not a free-form paragraph. Every Spec narrative — in chat, in `/tmp/access-policy-<slug>.spec.md`, and in the Review gate — uses this exact shape:

1. **Title line** — the policy name in bold, wrapped in straight double quotes: `**"<POLICY_NAME>"**`. Same string as Spec row 1.
2. **Opening sentence** — one sentence stating the policy type ("tool-use policy"), status mode ("simulation mode" / "active mode"), and the high-level effect. Example: _"This is a **tool-use policy** in **simulation mode** that allows a specific Maestro running on behalf of a specific user to invoke any Agent tagged `Production`."_ Always say "Maestro" — never "AgenticProcess" or "Agentic Process" — in the narrative (Critical Rule #14).
3. **Bulleted components** — exactly four bullets, in this order:
    - `**What is being protected:**` — plain-English Resource summary (type, scope, tag filter).
    - `**Who/what is allowed to call them:**` — Actor Process summary, then Actor Identity summary in the same bullet. When no Actor Identity row is filled, say "any User or Group running these Actor Processes" rather than omitting the bullet.
    - `**Effect:**` — always `Allow`. Phrase as "`Allow` — the matching call is permitted." Do not mention "not Deny" or any internal-mechanics caveat.
    - `**Status:**` — `Simulated` or `Active`, with the one-line meaning attached.
4. **Intent paragraph** — `**Intent:**` followed by 2–3 sentences on the *why* behind the policy. Carry over the user's framing verbatim where it is clear; do not invent intent. Mention the simulation rationale when status is `Simulated`.

The narrative is rendered as a single Markdown blockquote (every line prefixed with `>`) so it visually groups in chat. See [sample-policy-guide.md — Sample Spec narrative](./sample-policy-guide.md#sample-spec-narrative-natural-language-description) for a worked example.

### Description-field derivation

Spec row 2 (`Description`) is the **one-sentence summary** that the policy carries on the server. Derive it from the narrative's opening sentence and Intent paragraph — keep it under 200 characters. Do NOT paste the full narrative into row 2; the narrative is the chat/spec-file artifact, the description is the API field.

### Spec rules

- **Org / Tenant rows are read-only scope.** The two un-numbered rows at the top of the table show the active auth context — `<NAME> (UUID <UUID>)` for both Organization and Tenant. They are sourced from `uip login status --output json` plus the safe auth-context workflow and are NOT user-editable in the Spec; if the user wants to author against a different org or tenant, route them to re-run `uip login` (Critical Rule #1) and regenerate the Spec. The same Scope is shown again at the Phase 2 review gate (Critical Rule #7).
- **Narrative and table are kept in sync.** When the user changes a row, re-derive the narrative; when the user changes the narrative ("make it match this description"), re-derive the table by re-running [Intent analysis](#intent-analysis) on the new narrative. Both must reflect the same policy.
- **Terminology (user-facing — Critical Rule #14):** say "Resource", "Actor Process", "Actor Identity", "tag filter", "Allow", "Simulated / Active" in the Spec. Never use the JSON field names (`selectors`, `executableRule`, `actorRule`, `operator: Or/And/None`) in the Spec. JSON terms appear only in Phase 2.
- **Multi-type rows.** If the user names two resource types ("Agents and Flows"), each type gets its own row group — duplicate rows 5/6/7 once per type and label them `5a / 6a / 7a` for the first type, `5b / 6b / 7b` for the second, etc. Do the same for Actor Process rows (8/9/10) when multiple Actor Process types are named. The Spec table grows row-wise; it never collapses two types into one row.
- **Actor Identity is constrained (Critical Rule #16).** Rows 11/12 carry **at most two entries** — one `User` entry plus one `Group` entry. Multiple users (including multiple Robot Users) are merged into the `User` row's scope, never split into duplicate rows. Multiple groups are merged into the `Group` row's scope. **When both entries are present, their scope-style (include vs. exclude) must match** — both "specific UUIDs" or both "all-except UUIDs". Mixed include/exclude intent ("allow these users but exclude that group") cannot fit in one policy and must be split into two policies; flag this in Open questions and confirm with the user.
- **Always suggest a name.** Row 1 is **always** pre-filled — never `(missing)`. Default pattern: `"Allow <ResourceSummary> in <ActorProcessSummary>"` (e.g. `"Allow Production Agents in Maestro"`). Use user-facing names — `Maestro` rather than `AgenticProcess` (Critical Rule #14). The user can change it during the review loop.
- **Description auto-derivation.** Row 2 is the one-sentence summary of the narrative — keep it under 200 characters and aligned with the narrative's opening sentence + Intent paragraph (see [Description-field derivation](#description-field-derivation)).
- **Status default.** Default row 3 to `Simulated` (Critical Rule #13 — see [SKILL.md § Enforcement and status](../SKILL.md#enforcement-and-status) for the meaning). When presenting the Spec, mention once: _"Created in Simulated mode — evaluated but not enforced. Tell me if you want it Active from the start, or activate it after review."_ Only fill `Active` when the user explicitly asks.
- **Enforcement is always `Allow`.** Row 4 is fixed (Critical Rule #2). Deny intent is silently translated to an Allow shape; never surface the flip in the narrative or table. See [plugins/tags/planning.md — Deny-to-Allow flip](./plugins/tags/planning.md#deny-to-allow-flip) for the decision logic.
- **Default scope.** Default the scope row to `all` (corresponds to `["*"]`) when the user didn't specify UUIDs. Specific UUIDs only when the user named them.
- **Resolving names to UUIDs.** When the user refers to a specific process / agent / flow / user / robot by **name** ("the Invoice Agent", "the build-bot robot"), do NOT ask the user for the UUID blindly — first run the lookup commands in [resource-lookup-guide.md](./resource-lookup-guide.md). Present matching rows as a numbered picker and let the user confirm one. **Robots resolve to `type: User`** (Critical Rule #16) — look up the robot, then resolve its linked user identity, and emit a `User`-typed Spec row. Surface an Open question only when the lookup returns no match or the identity type (Group) has no `uip or` wrapper yet (Critical Rule #15).
- **Tag rows.** Include a tag-filter row only when the user mentioned tags on that side. Otherwise leave the cell as `(none)`.
- **Actor Identity omission.** If the user said nothing about identity, leave rows 11–12 as `(none = any identity)`. Phase 2 will omit `actorRule` entirely from the JSON (Critical Rule #4).
- **No tags on Actor Identity.** The Spec table has no row 13 — `actorRule` does not support `tags` today. If the user asks for an identity tag filter, tell them it is not supported and offer to (a) enumerate users / groups directly under rows 11/12, or (b) drop the tag filter. Phase 2 must never emit `actorRule.tags`.

---

## Spec file convention

Once the Spec is fully pre-filled and every Open question is closed, write it to `/tmp/access-policy-<slug>.spec.md` so the user can open it in their editor and review it independently of the chat transcript. The same slug is reused for the Phase 2 JSON file (`/tmp/access-policy-<slug>.json`) so the two files sit side by side.

### Slug rule

Compute the slug from Spec row 1 (`Policy name`):

```bash
SLUG=$(echo "<POLICY_NAME>" | tr '[:upper:] ' '[:lower:]-' | tr -cd '[:alnum:]-')
SPEC_FILE="/tmp/access-policy-${SLUG}.spec.md"
```

Phase 2 will run the **identical** snippet to derive its `POLICY_FILE`, so the slug must come from row 1 — never from a transient placeholder.

### Spec file body

The file is a self-contained markdown document the user can read without chat context. Use this template verbatim:

```markdown
# Access Policy Spec — <POLICY_NAME>

> **"<POLICY_NAME>"**
>
> <ONE_OPENING_SENTENCE — policy type + status mode + high-level effect>
>
> - **What is being protected:** <plain-English Resource summary>
> - **Who/what is allowed to call them:** <Actor Process summary, then Actor Identity summary; use "any User or Group running these Actor Processes" when no Actor Identity row is filled>
> - **Effect:** `Allow` — the matching call is permitted.
> - **Status:** `<Simulated | Active>` — <one-line meaning>
>
> **Intent:** <2–3 sentences describing the *why* — carry over the user's framing verbatim where clear; mention simulation rationale when status is `Simulated`>

## Spec Components Table

| # | Component | Allowed values | Current value | Required? |
|---|-----------|---------------|--------------|-----------|
| <ALL_ROWS_AS_PRESENTED_IN_CHAT — see [Spec output format](#spec-output-format)> |

_Generated by Phase 1 of the `uipath-gov-access-policy` skill. The matching policy JSON will be written to `/tmp/access-policy-<slug>.json` by Phase 2._
```

### Re-write on every iteration round (after row 1 is set)

- Once Spec row 1 is filled for the first time, write the file.
- After every subsequent iteration round that changes any row, **re-write** the file so its contents always match what the user sees in chat. If row 1 itself changes, also `rm` the previous slug's `.spec.md` to avoid stale files.
- Show the resolved absolute path as a clickable markdown link (run `realpath` — Critical Rule #7) every time you re-present the Spec.

If row 1 is still `(missing)`, do NOT write the file yet — defer until the first round where the user supplies (or accepts a suggested) name.

---

## Review gate

When every Open question is closed, present the final Spec (narrative + table) IN CHAT, plus a clickable markdown link to the Spec file (`/tmp/access-policy-<slug>.spec.md` — resolved absolute path), and ask the user verbatim:

```
Approve this access-policy Spec to proceed to Phase 2? (yes / edit / cancel)
```

- `yes` → hand off to [planning-impl.md](./planning-impl.md). The Spec file stays on disk so the user can compare it to the JSON working file Phase 2 will create.
- `edit` → return to the iteration loop (step 4 of the [Process](#process)). Collect the change, update the table + narrative, **re-write the Spec file**, then re-present and re-enter this gate.
- `cancel` → stop and drop the session. Leave the Spec file on disk only if the user wants to keep a draft; otherwise `rm` it.

Do NOT advance to Phase 2 without an explicit `yes`. The approved Spec — both the narrative in chat AND the Spec file on disk — is the contract.

---

## Handoff to Phase 2

The approved Spec is the input to [planning-impl.md](./planning-impl.md), which walks the Spec Components Table row by row, reads the matching plugin's `impl.md`, and composes the concrete `PolicyDefinition` JSON. Phase 2 reuses the slug from the Spec file and writes the JSON to `/tmp/access-policy-<slug>.json`. The single review gate in [policy-manage-guide.md](./policy-manage-guide.md) presents both files side by side.
