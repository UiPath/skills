# Branch Disambiguation Guide

> Used by [`../SKILL.md`](../SKILL.md) Workflow Step 2. Lists the strong signals, the phrase patterns that need disambiguation, and the canonical worked example. Read once per governance request to classify the intent.

The two branches:

- **Branch A — AOps product policy** (`uip gov aops-policy`) → governs *product feature behavior* on Studio / StudioX / Assistant / Robot / AI Trust Layer / Agent Builder.
- **Branch B — Access ToolUsePolicy** (`uip gov access-policy`) → governs *resource/tool use* on the Actor Process → child Resource boundary.

## Compliance standard override (highest priority)

**Before evaluating Branch A / B signals**, check for compliance standard framing:

A **standard name** is any name resolving to a pack in `catalog list` — `ISO 42001` / `ISO/IEC 42001` / `AI Management System`, `ISO 27001` / `ISO/IEC 27001` / `ISMS` / `Information Security Management System`, `GDPR`, `HIPAA`, `SOC 2`, `EU AI Act`, or a bare standard number. Routing here does not mean the standard is usable: some catalog entries are announced with no bundle behind them. Which ones differ by environment, so the compliance flow reads it from `catalog list` and tells the user — never assume from the name. More than one standard is available, so the standard name is a routing signal, never an assumption: resolve which one via [`compliance-pack/catalog/impl.md` § Pack ID lookup](./compliance-pack/catalog/impl.md#pack-id-lookup) before running any pack-scoped command.

If the request contains a **standard name** **AND** a scope-limiting phrase (`just that area`, `only that part`, `not the whole standard`, `just that control`, `just the traceability`, `only the AI provider controls`, `just that compliance piece`), it is a **partial-apply** request regardless of whether the content words also match a Branch A model-gate signal.

The content-word rows below are examples of the shape, not a closed list — the standard name plus a scope phrase is what routes, whatever the subject matter. Clause topics differ per standard (42001 is AI-management-shaped; 27001 is information-security-shaped), so never infer the standard from the content words.

| Request shape | Route |
|---|---|
| standard name + "make AI usage traceable / logged" + "not the full standard" | Compliance standard → partial-apply (traceability clauses) |
| standard name + "lock down AI model providers / approved providers" + "just that control" | Compliance standard → partial-apply (AITrustLayer model-governance clauses) |
| standard name + "robot allowlists / URL allowlists / application allowlists" + scoped | Compliance standard → partial-apply (Robot UIAutomation clauses) |
| standard name + "access control / who can sign in / least privilege" + scoped | Compliance standard → partial-apply (access-control clauses) |
| standard name + "audit logging / retention / evidence trail" + scoped | Compliance standard → partial-apply (logging clauses) |
| standard name + "encryption / crypto / secrets handling" + scoped | Compliance standard → partial-apply (cryptography clauses) |
| standard name + no scope-limiting phrase | Compliance standard → full-apply or posture check |
| Compliance framing with NO standard name ("check my compliance posture", "am I compliant") | Compliance standard → resolve which standard first (ask, listing `catalog list` packs), then route |

Do **not** route a standard name + model/traceability/access-control intent to `aops-policy` directly — even though those intents look like Branch A signals, the standard-framing signals the catalog-based path that understands which clauses apply.

## Strong signals — Branch A (AOps)

Route directly, no disambiguation needed, when the user:

- Names a UiPath product surface — `Studio`, `StudioX`, `Assistant`, `Robot runtime`, `AI Trust Layer`, `Marketplace widget`, `Agent Builder feature`.
- Names a Studio / StudioX setting — `feedback`, `telemetry`, `package source`, `activity`, `publish`, `Workflow Analyzer`, `release notes`.
- Names a Robot runtime rule — `block regedit / cmd.exe`, `whitelist applications`, `allow only outlook.exe`, `block emails to gmail`, `blocked URLs`.
- Names a model-level gate at design-time — `block Gemini / Claude / ChatGPT in Studio`, `restrict which LLMs Studio can call`, `AI Trust Layer rule`.
- Names a tenant-wide default for the product — `apply to everyone in the tenant` paired with a product context.

→ Continue at [`aops-policy/aops-policy-overview-guide.md`](./aops-policy/aops-policy-overview-guide.md).

## Strong signals — Branch B (Access ToolUsePolicy)

Route directly when the user:

- Names an Actor → Resource boundary — `when my Agent calls <sub-agent / flow / process>`, `only the Production Maestro can invoke the Production Agent`.
- Names tag-based scoping over agents / flows / RPAs / APIs — `only Production-tagged agents may be invoked`, `exclude Sandbox-tagged resources`.
- Names an actor identity — `only the finance group can trigger this`, `only <user> can invoke <resource>`, `on behalf of <user> / <robot>`.
- Mentions `ToolUsePolicy`, `tool-use policy`, or `uip gov access-policy`.

→ Continue at [`access-policy/access-policy-overview-guide.md`](./access-policy/access-policy-overview-guide.md).

## Phrases that commonly need disambiguation

When the same phrasing fits both branches, ask the [disambiguation question](../SKILL.md#disambiguation-question).

| Phrase pattern | Why it's ambiguous |
|---|---|
| "block / restrict `<model>` for `<team>`" | Could be a Studio-layer model gate (A) or a tool-use block on agents wrapping that model (B). |
| "stop `<group>` from using `<resource>`" | Could be an AOps policy targeting the group's product behavior (A) or an Access policy with `actorRule` (B). |
| "only `<group>` can use `<resource>`" | Same — product-level allowlist (A) vs tool-use allowlist (B). |
| "compliance: `<team>` must not access `<thing>`" | Either layer; ask which boundary `<thing>` lives at. |
| "block `<agent / flow>`" | Likely B (tool-use). Confirm if the user mentioned a product surface like Studio. |

## Phrases that do NOT need disambiguation

Skip the question and route directly when the phrasing is unambiguous.

| Phrase | Branch |
|---|---|
| "Disable Studio feedback / telemetry / Marketplace widget" | A — product feature |
| "Enforce Workflow Analyzer rule X" | A — Studio runtime |
| "Block regedit / cmd.exe / specific URLs / specific emails on Robot" | A — Robot runtime |
| "When my Agent calls sub-agent X, allow it" | B — Actor → Resource |
| "Only Production-tagged agents may be invoked" | B — selectors + tags |
| "Only `<group>` can invoke `<flow>`" | B — actorRule |

## Worked example — the canonical ambiguous prompt

> "Block ChatGPT for my finance team using Studio."

- **Interpretation A:** Block the model itself at the Studio layer (AI Trust Layer policy under AOps). Nobody on the finance team can use ChatGPT *from inside Studio*, no matter what they build.
- **Interpretation B:** Block specific ChatGPT-wrapping resources at the tool-use layer (Access ToolUsePolicy). The finance team's Actor Processes cannot *invoke* particular agents / flows that wrap ChatGPT.

Both produce a working artifact and no error — the user has no way to tell which interpretation was applied. Always ask the disambiguation question on prompts of this shape.

If the user's reply describes something that fits no branch (e.g. platform ops, Orchestrator resources), redirect via [SKILL.md § Sibling redirects](../SKILL.md#when-to-use-this-skill) — do not propose skill edits.
