# Classification Details — uipath-admin

**Classification: Strong**

---

## What the Skill Teaches

Administrative operations on UiPath org/tenant/identity via `uip admin` — Identity (users, groups, robot accounts, external apps, PATs), Authorization (custom roles, role assignments, effective-access PDP), OMS (tenant lifecycle, services, regions, async polling), IP Restriction (allowlist, enforcement, lockout safety), and Audit (scoped event queries, paginated exports, investigation playbooks).

| # | Area | Codifiable? | Notes |
|---|------|-------------|-------|
| 1 | **Principal resolution before mutations** | **Yes — VALIDATE/CHECK** | Fixed rule: search directory, echo resolved identity, stop on zero or multiple matches |
| 2 | **Identity lifecycle (users, groups, robot accounts, external apps)** | **Yes — TRANSFORM-PIPELINE** | Discover → create/invite → group-assign → confirm; fully sequenced CLI steps |
| 3 | **Role management and assignment** | **Yes — TRANSFORM-PIPELINE** | roles get → build actions file → roles create/update; role-service vs scope-path validation in Rule 17 |
| 4 | **Effective access check (PDP)** | **Yes — VALIDATE/CHECK** | `check-access` with fixed scope/principal args; pass/fail verdict per permission |
| 5 | **OMS tenant lifecycle with async polling** | **Yes — TRANSFORM-PIPELINE** | resolve region → create/enable/disable/delete → auto-poll 3× at 5 s → numbered menu fallback |
| 6 | **IP restriction enforcement with lockout safety** | **Yes — VALIDATE/CHECK** | `my-ip` → `ip-ranges list` → coverage check → prompt → `enforcement enable --confirm` |
| 7 | **Audit scope disambiguation and discovery** | **Yes — DETECT** | If ambiguous, stop and ask OR query both scopes; always `audit <scope> sources` before `events` |
| 8 | **Audit event query and export pipeline** | **Yes — TRANSFORM-PIPELINE** | Discover sources → resolve time window to ISO 8601 UTC → bound query / day-wise export |
| 9 | **Troubleshoot playbooks (5 named patterns)** | No | Structured but require investigative judgment to navigate evidence |

---

## Codifiable Procedures (not yet scripted)

### 1. Principal Resolution Pre-flight — VALIDATE/CHECK

**Source:** `skills/uipath-admin/SKILL.md` §Critical Rules → Universal

**What it does:** Before any mutation touching a named user, group, robot account, or external app, the skill requires the agent to search the directory and echo a resolved identity string. Zero matches halt execution; multiple matches produce a numbered list awaiting a digit. The check gates a fixed set of destructive verbs: `roles assignments create/delete`, `users delete`, `groups delete`, `groups members add/revoke`, `robot-accounts delete`, `external-apps delete`, `external-apps generate-secret`. Line 91: "Any command that touches a named user / group / robot account / external app — `roles assignments create/delete`, `users delete`, `groups delete`, `groups members add/revoke`, `robot-accounts delete`, `external-apps delete`, `external-apps generate-secret` — MUST first search the directory and echo `Principal: <displayName> (<userName>) — <id>` back before the mutation runs."

**Why it's mechanical:** The rule specifies exactly which verbs require the pre-flight and the exact output format; no judgment is needed to determine when or how to apply it.

**Turn savings:** The agent currently resolves principals ad-hoc across multiple turns of directory search and ID confirmation; a single script that accepts a display name and emits the resolved identity (or halts on ambiguity) collapses this to one call.

---

### 2. OMS Async Operation Polling — TRANSFORM-PIPELINE

**Source:** `skills/uipath-admin/SKILL.md` §Critical Rules → OMS

**What it does:** After any OMS tenant mutation, the CLI returns an `operationId`. The skill prescribes an automatic polling loop: call `organizations operation get <OP_ID>` three times at 5-second intervals, stop and report on a terminal status, and present a numbered menu if still in-progress after the third poll. The loop never runs indefinitely. Line 113: "Auto-poll `organizations operation get <OP_ID>` 3× at 5 s; on terminal status stop and report; still in-progress after 3 polls → numbered menu, never indefinite loop."

**Why it's mechanical:** The poll count (3), interval (5 s), and exit conditions (terminal status vs. numbered menu) are all fixed constants in the skill.

**Turn savings:** Without a script the agent performs each poll as a separate turn with manual timing; a polling script compresses three timed polls plus result interpretation into one invocation.

---

### 3. Audit Scope Disambiguation and Sourced Query Pipeline — TRANSFORM-PIPELINE

**Source:** `skills/uipath-admin/SKILL.md` §Critical Rules → Audit (Rules 23–30)

**What it does:** When the user requests audit data, the skill mandates a fixed sequence: (1) classify prompt into `org` vs `tenant` scope (or ask once / query both if ambiguous), (2) run `audit <scope> sources` to discover live source GUIDs before any event query, (3) resolve relative time phrases to UTC ISO 8601, (4) call `audit <scope> events --from-date ... --to-date ... --limit ...` or `audit <scope> export --from-date ... --to-date ... --output-path ...`. Line 124: "Discover via `audit <scope> sources` first — never invent source / target / type GUIDs. The catalog response gives the GUIDs you pass to `events --source / --target / --type`."

**Why it's mechanical:** The pipeline order (disambiguate → discover → bound window → query/export) and the constraints (no invented GUIDs, bounded window, correct pagination via `--limit`) are all stated explicitly with no judgment required.

**Turn savings:** The agent currently performs scope disambiguation, source discovery, and window resolution in separate conversational turns; a script that accepts intent + time range and runs the full sourced-query pipeline reduces this to one call.

---

### 4. IP Restriction Enforcement Safety Pre-flight — VALIDATE/CHECK

**Source:** `skills/uipath-admin/SKILL.md` §Critical Rules → IP Restriction (Rule 31)

**What it does:** Before enabling IP restriction enforcement, the skill requires three sequential steps: (1) call `ip-restriction my-ip --output json` to determine the caller's public IP, (2) call `ip-restriction ip-ranges list --output json` and verify the caller's IP is covered by at least one CIDR entry, (3) present an explicit impact statement and require user confirmation. Only then may `ip-restriction enforcement enable --confirm` proceed. Line 134: "Run `ip-restriction my-ip` and verify the caller's IP is covered by an entry in `ip-ranges list`. Then prompt the user with the impact before flipping."

**Why it's mechanical:** The exact sequence (my-ip → ip-ranges list → coverage check → prompt → enable) and the CIDR overlap check are fully deterministic.

**Turn savings:** Without a script, the agent runs each command separately across multiple turns and manually verifies CIDR coverage; a script collapses the full safety pre-flight and coverage assertion into a single auditable check.

---

## Justification for Classification

**Strong** — not Partial, not None.

**Why not Partial:** Eight of nine teaching areas are codifiable with fixed CLI sequences, validation rules, or decision tables. The only non-codifiable area (troubleshoot playbooks) is a small fraction of the skill's total content; the dominant teaching across Identity, Authorization, OMS, Audit, and IP Restriction is mechanically structured CLI pipelines and guard checks.

**Why not None:** Multiple TRANSFORM-PIPELINE and VALIDATE/CHECK procedures exist with explicit sequencing and numeric constants (poll count, intervals, limits, CIDR coverage) that leave no room for agent judgment.

**Evidence locations:**
- Principal resolution pre-flight: `SKILL.md` §Critical Rules → Universal, Rule 5 (line 91)
- OMS async polling: `SKILL.md` §Critical Rules → OMS, Rule 18 (line 113)
- Audit scope disambiguation and sourced query: `SKILL.md` §Critical Rules → Audit, Rules 23–26 (lines 121–126)
- IP restriction enforcement pre-flight: `SKILL.md` §Critical Rules → IP Restriction, Rule 31 (line 134)
- Role-service vs scope-path validation: `SKILL.md` §Critical Rules → Authz, Rule 17 (line 109)
