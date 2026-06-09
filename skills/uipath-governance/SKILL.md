---
name: uipath-governance
description: "UiPath governance via `uip gov` — author and deploy policies on three layers. AOps product policies (`uip gov aops-policy`): block/restrict/enforce features in Studio, StudioX, Assistant, Robot, AI Trust Layer, Agent Builder; deploy to user/group/tenant. Access ToolUsePolicy (`uip gov access-policy`): allow/deny when one workflow invokes another as a tool (Agent→Agent/Maestro/Flow/RPA/API/Case), gated by tag, caller, or actor (User/Group). Custom policies (`uip gov custom-policy`): WASM rules evaluated at every lifecycle hook — PII, model, tool checks; verdicts in audit trail (audit mode only); create/update/delete/enable/disable. Skill classifies intent before authoring. For platform ops→uipath-platform."
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# UiPath Governance

> **Preview** — skill is under active development; surface and behavior may change.

Uber skill for UiPath governance authoring. Three backing CLI surfaces:

| Surface | Governs | CLI |
|---|---|---|
| **AOps product policy** | Product feature behavior — what Studio / StudioX / Assistant / Robot / AI Trust Layer / Agent Builder can do at design-time / runtime | `uip gov aops-policy` |
| **Access policy** (`ToolUsePolicy`) | Resource/tool-use boundary — when an Actor Process invokes a child Resource (Agent / Maestro / Flow / RPA / API / Case Management), is the call allowed? | `uip gov access-policy` |
| **Custom policy** | Agent runtime rules — WASM-compiled, evaluated at every lifecycle hook (model calls, tool calls, agent I/O); verdicts recorded in audit trail (audit mode only — enforcement coming) | `uip gov custom-policy` |

All three surfaces share verbs (`block`, `restrict`, `deny`, `allow`, `require`, `enforce`). The same English sentence often maps to different layers, so this skill **classifies first** and only then routes to the matching mechanic.

## When to Use This Skill

Activate on **any** governance / policy / rule intent — even when the user did not name the underlying CLI:

- `policy / rule / guardrail / govern / gate / control` requests
- `block / restrict / deny / disable / disallow` an action, model, app, URL, agent, flow, or process
- `require / enforce / mandate` a behavior or rule
- `allow only / permit only / limit to / restrict to` X
- `who can / which … can / on behalf of` — actor- or identity-shaped governance
- `compliance / posture / audit` framing on top of policies

**Sibling redirects:**
- Platform ops (auth, Orchestrator resources, packaging, deploy) → `uipath-platform`
- Authoring agents / workflows / RPA themselves → `uipath-agents` / `uipath-rpa` / `uipath-maestro-flow`

## Critical Rules

1. **Classify before authoring.** First action on any governance request is to classify intent into Branch A (AOps) or Branch B (Access). Use the priors in [`references/disambiguation-guide.md`](./references/disambiguation-guide.md). Never start `create` / `update` / `delete` until classification is settled — by user wording or by the [disambiguation question](#disambiguation-question).
2. **Classification lives at the top.** Mechanic libraries assume the branch is chosen. Do not let those flows ask "did you mean the other branch?" — that question belongs here.
3. **One branch per mutation.** A single user request produces a policy on one branch only. If the user wants both, run two sequential flows with two confirmation gates.
4. **Each mechanic owns its own Critical Rules.** Once routed, follow the branch's rules — do not relax them from this top level.
5. **Always `uip login` before any `uip gov …` command.** `evaluate` (Access) additionally requires tenant-scoped login — see [`access-policy-overview-guide.md` § Critical Rules](./references/access-policy/access-policy-overview-guide.md#critical-rules).
6. **Never fabricate UUIDs.** Resolve every named user / group / process / agent / flow / robot / tenant via the relevant branch's lookups.

## Workflow

1. **Classify the intent.** Read [`references/disambiguation-guide.md`](./references/disambiguation-guide.md) — it lists the strong signals for each branch, the phrase patterns that need disambiguation, and the canonical worked example. If a strong signal matches, route silently. If the phrasing is ambiguous (matches both branches), ask the [disambiguation question](#disambiguation-question) and wait for a digit reply. If the user replies with anything other than `1`, `2`, or `3`, treat it as a re-statement of intent and re-classify. **Do not run any CLI command before classification is settled** — the disambiguation question itself does not need `uip`, and an unrelated request (platform ops, agent authoring) must redirect to a sibling skill before any setup happens here.
2. **Verify `uip` and login** *(only after classification routes to a governance branch).*
   ```bash
   which uip && uip --version
   uip login status --output json
   ```
   If not installed: `npm install -g @uipath/uipcli`. If not logged in: `uip login` (`--authority <URL>` for non-prod). For Access `evaluate`, login MUST be tenant-scoped.
3. **Route to the chosen mechanic** and follow its flow end-to-end.
   - Branch A → [`references/aops-policy/aops-policy-overview-guide.md`](./references/aops-policy/aops-policy-overview-guide.md)
   - Branch B → [`references/access-policy/access-policy-overview-guide.md`](./references/access-policy/access-policy-overview-guide.md)
   - Branch C → [`references/custom-policy/custom-policy-overview-guide.md`](./references/custom-policy/custom-policy-overview-guide.md)

## Disambiguation Question

When the user's intent fits both branches, render exactly this numbered list (no `AskUserQuestion`, no table) and wait for a digit reply:

```markdown
### Which layer should this rule govern?

1. **Govern the product** — control what Studio / StudioX / Assistant / Robot / AI Trust Layer / Agent Builder *can do* (e.g. block ChatGPT inside Studio, enforce Workflow Analyzer, disable a Marketplace widget). Backed by `uip gov aops-policy`.
2. **Govern resource/tool use** — control which Actor Processes / identities can *invoke* which child Resource as a tool (e.g. block agents tagged `Sandbox` from being called, only let the finance group trigger this Flow). Backed by `uip gov access-policy`.
3. **Govern agent runtime** — enforce guardrails inside a running agent at every lifecycle hook (e.g. block PII in prompts, restrict which models the agent may call, cap tool calls per session). Backed by `uip gov custom-policy`.

Reply with the number.
```

The canonical ambiguous prompt is *"Block ChatGPT for my finance team using Studio."* See [`references/disambiguation-guide.md`](./references/disambiguation-guide.md#worked-example--the-canonical-ambiguous-prompt) for the worked-out reasoning of why both interpretations produce a working but different artifact.

## Reference Navigation

| I need to... | Read |
| --- | --- |
| **Decide which branch a request belongs to** (priors, phrase tables, worked example) | [`references/disambiguation-guide.md`](./references/disambiguation-guide.md) |
| **Author an AOps product policy** | [`references/aops-policy/aops-policy-overview-guide.md`](./references/aops-policy/aops-policy-overview-guide.md) |
| **Deploy an AOps policy to user / group / tenant** | [`references/aops-policy/aops-policy-deploy-guide.md`](./references/aops-policy/aops-policy-deploy-guide.md) |
| **Query the deployed AOps policy / effective rules** | [`references/aops-policy/aops-policy-deployed-guide.md`](./references/aops-policy/aops-policy-deployed-guide.md) |
| **Author an Access ToolUsePolicy** | [`references/access-policy/access-policy-overview-guide.md`](./references/access-policy/access-policy-overview-guide.md) |
| **Look up CLI flags / output shapes** (AOps) | [`references/aops-policy/aops-policy-commands.md`](./references/aops-policy/aops-policy-commands.md) |
| **Look up CLI flags / output shapes** (Access) | [`references/access-policy/access-policy-commands.md`](./references/access-policy/access-policy-commands.md) |
| **Resolve a name to a UUID for Access** | [`references/access-policy/resource-lookup-guide.md`](./references/access-policy/resource-lookup-guide.md) |
| **Manage or author an agent runtime policy** | [`references/custom-policy/custom-policy-overview-guide.md`](./references/custom-policy/custom-policy-overview-guide.md) |
| **Look up CLI flags / output shapes** (custom policy) | [`references/custom-policy/custom-policy-commands.md`](./references/custom-policy/custom-policy-commands.md) |
| **Custom policy YAML schema and check types** | [`references/custom-policy/custom-policy-schema-guide.md`](./references/custom-policy/custom-policy-schema-guide.md) |

## Anti-patterns

- Do NOT skip the disambiguation question when the phrasing fits both branches. Mechanic libraries assume the branch is chosen and will not catch wrong-branch routing.
- Do NOT hand off to a mechanic, then ask "did you mean the other branch?". That question must happen at this top level.
- Do NOT merge AOps and Access intent into one policy. Different artifacts, different CLIs, different schemas.
- Do NOT activate this skill for platform ops. Route to `uipath-platform`.
- Do NOT propose skill edits when intent doesn't map to either branch. Ask the user to clarify.
