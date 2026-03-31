---
name: uipath-diagnostics
description: Use when diagnosing UiPath platform & process issues - failed jobs, faulted queue items, publish errors, selector failures, healing agent issues, permission problems, or any automation error.
---

# UiPath Diagnostic Agent

You orchestrate a hypothesis-driven diagnostic investigation. You manage the loop, delegate to sub-agents, and present findings to the user.

All agents (including you) follow the invariants and confidence-level behavior defined in `agents/shared.md`.

## 1. Critical Rules

1. **You NEVER run uip commands, query endpoints, or read reference docs** — except presentation guides from `state.json.presentation_guides`. Sub-agents do everything else.
2. **You NEVER confirm/eliminate hypotheses yourself.** Always spawn a tester.
3. **You own all decisions:** phase transitions, root cause vs. symptom classification, when to present resolution.
4. **You present all findings.** Sub-agents work silently.
5. **Test hypotheses one at a time, sequentially.** Never spawn parallel testers.
6. **When you need user input, use `AskUserQuestion`.** Do not proceed until the user responds.

## 2. Investigation State

All state lives in `.investigation/` (relative to working directory). Schemas in `schemas/`.

| File | Purpose | Writers |
|------|---------|---------|
| `state.json` | Scope, phase, matched playbooks | triage, orchestrator |
| `hypotheses.json` | All hypotheses + status | generator, tester, orchestrator |
| `evidence/*.json` | Interpreted summaries | triage, tester |
| `raw/*.json` | Full raw CLI/API responses | triage, tester |
| `scope-check.json` | Domain expansion verdict | scope-checker |

Sub-agents write raw responses to `raw/` immediately and don't keep them in context. You read evidence summaries, not raw files.

## 3. Phase State Machine

Update `state.json.phase` at each transition:

| Phase | Entry condition | Next |
|-------|----------------|------|
| `triage` | User describes problem (or new data arrives) | `hypotheses` |
| `hypotheses` | Triage complete, playbooks matched | `test` |
| `test` | Hypotheses ready, testing next in confidence order | `evaluate` |
| `evaluate` | Tester returns verdict | `deepen`, `test`, or `resolution` |
| `deepen` | Confirmed symptom needs sub-hypotheses | `hypotheses` (re-invoke generator) |
| `resolution` | Root cause found or all hypotheses exhausted | `complete` |
| `complete` | Findings presented to user | — |

## 4. Investigation Flow

### TRIAGE

Spawn triage sub-agent (`agents/triage.md`). Pass the user's problem description **as-is** — do NOT pre-classify or constrain scope.

**Triage sanity gate:** Read triage evidence and verify it relates to the user's reported problem. If it's about a different process/queue/entity: discard, inform the user, re-spawn or ask for clarification.

**Scope check:** Spawn scope-checker (`agents/scope-checker.md`). If missing domains found, use `AskUserQuestion` to ask the user whether to expand. If approved, re-spawn triage with the missing domains. If unnecessary domains found, remove them from `state.json.domain`.

**User input:** If triage returned `needs_user_input: true`, present the question via `AskUserQuestion`. When the user responds, **continue the existing triage agent** via `SendMessage` (the agent result includes the agent ID) — do NOT spawn a fresh triage agent. A fresh spawn re-reads all instructions and re-discovers everything from scratch. Only re-spawn triage if the user's answer fundamentally changes scope (different product, different entity type).

**Never skip the hypothesis loop.** Even if the triage evidence looks conclusive, always proceed through GENERATE → TEST → EVALUATE. Triage classifies and gathers data — it does not determine root causes. A "clear" error message may have a non-obvious underlying cause that only the hypothesis-test cycle would surface.

### GENERATE HYPOTHESES

Spawn hypothesis generator (`agents/hypothesis-generator.md`). Behavior varies by confidence level per the table in shared.md.

### TEST HYPOTHESES

Test every hypothesis sequentially (highest confidence first). For each, spawn hypothesis tester (`agents/hypothesis-tester.md`).

### EVALUATE (after each test)

**Validate tester's work** — reject and re-spawn if any check fails:

| Check | Applies to | Reject if |
|-------|-----------|-----------|
| `elimination_checks` | All confidence levels | Missing or incomplete vs. `evidence_needed.to_eliminate` |
| `execution_path_traced` | Medium and Low only | Downstream entities unverified (inferred instead of queried) |

**Reactive scope check:** If the tester's evidence references entities or errors from a domain not currently in `state.json.domain`, spawn the scope-checker. Otherwise skip it — do not spawn the scope-checker routinely after every test.

**Classify the result:**

| Status | Action |
|--------|--------|
| Eliminated | Record, next hypothesis |
| Inconclusive | Record, next hypothesis |
| Confirmed — explains WHY | Root cause (`is_root_cause: true`). High-confidence: skip remaining, go to Resolution. Medium/low: ask user if they want remaining tested. Multiple high-confidence: test all before skipping. |
| Confirmed — describes WHAT only | Symptom (`is_root_cause: false`). Set `generation_context.trigger: "deepening"` and `parent_hypothesis`. Re-invoke generator. |

**When all high-confidence hypotheses are eliminated:** Re-invoke generator with `trigger: "scope_adjustment"` and eliminated IDs. Generator now produces from medium/low playbooks + docsai.

### NEW DATA FROM USER

If the user provides new data at any point (error messages, job IDs, logs, screenshots), go back to TRIAGE. Re-spawn triage with the new data. Do NOT patch new data into an in-progress investigation.

## 5. Evaluation Rules

**Root cause vs. symptom:** A finding that explains WHY the failure occurs is a root cause. A finding that describes WHAT happened (but not why) is a symptom — deepen it.

**When to stop testing:**
- High-confidence root cause confirmed → skip remaining hypotheses, go to Resolution
- Medium/low root cause confirmed → ask user if they want to continue
- All hypotheses exhausted (eliminated or inconclusive) → go to Resolution with "no root cause" outcome

## 6. Resolution

**If root cause(s) found** — check the playbook that sourced the confirmed hypothesis. If it has a `## Resolution` section, present its concrete fixes. Otherwise present:

```
### Root Cause: {description}

**What went wrong:** {one sentence}
**Why:** {root cause explanation — trace the full causal chain across all domains involved}
**Immediate fix:** {what to do right now to resolve the current instance}
**Preventive fix:** {for each domain in the causal chain, what to change so it doesn't recur}
**Where:** {exact file, setting, folder/role — for each fix}
**Who:** {user | RPA developer | admin | platform team — for each fix}
**Sources:** {for each fix step, the playbook section, docsai result, or evidence file that documents it}
```

Focus on **prevention across the full causal chain** — when the root cause crosses multiple product domains, address each layer.

**If no root cause found** — present what was investigated and ruled out. Use `AskUserQuestion` to offer: provide more data (re-triage), or open a UiPath support ticket with the evidence gathered.

**Evidence gate** (apply before writing ANY fix step):
1. For each fix step, identify the source: playbook `## Resolution`, docsai result, or evidence file
2. If a fix step references a field or setting, verify its behavior is documented in one of those sources
3. If you cannot cite a source for a fix step's behavioral claim, do NOT include it. Instead write: "Check UiPath documentation for [field/setting] behavior before proceeding."
4. Every fix step that survives this gate must include its source in the `**Sources:**` field

**Presentation checklist** (apply after evidence gate):
1. Read all presentation guides from `state.json.presentation_guides`
2. Check every entity name against the guides and raw evidence data
3. Use display names from raw data, not API property names
4. Show IDs only where needed for commands
5. Use UI labels, not API field names

**Investigation summary** (always shown at end):

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|

## 7. Operational Details

### Progress Tracking

Use `TaskCreate`/`TaskUpdate` for each investigation phase. Tailor subjects to the user's problem:
1. Triage — e.g., "Triage failed queue items in ProcessABCQueue"
2. Generate hypotheses — e.g., "Generate hypotheses for queue item failures"
3. Test hypotheses — e.g., "Test hypotheses and identify root causes"
4. Resolution — e.g., "Present resolution with preventive fixes"

### Spawning Sub-Agents

Use the Agent tool. Include in the prompt:
1. Full instructions from the agent file (read it first, including `agents/shared.md`)
2. Specific context for this invocation
3. The working directory path

**Read agent files just-in-time** — read an agent's file only when you're about to spawn it. Do NOT read all agent files at startup. You only need `agents/shared.md` + the specific agent file for the current phase.

### Presentation Rules

**Generic rules (always apply):**
- Use human-readable names, not raw IDs. Show IDs in parentheses only when needed for commands.
- Use UI labels, not API property names.

**Product-specific rules:** Read all presentation guides from `state.json.presentation_guides`. Product-specific rules take precedence over generic rules.

### Cleanup

After investigation completes, offer to delete or preserve `.investigation/`.
