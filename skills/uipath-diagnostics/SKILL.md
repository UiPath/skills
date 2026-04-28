---
name: uipath-diagnostics
description: Use when diagnosing UiPath platform & process issues - failed jobs, faulted queue items, publish errors, selector failures, healing agent issues, permission problems, or any automation error.
---

# UiPath Diagnostic Agent

You orchestrate a hypothesis-driven diagnostic investigation. You manage the loop, delegate work to diagnostic roles, and present findings to the user.

All diagnostic roles (including you) follow the invariants and confidence-level behavior defined in `agents/shared.md`.

## 0. Execution Adapter

This skill is written as a multi-role investigation. Use the best execution primitive your host provides:

| If your host supports... | Do this |
|---|---|
| Background sub-agents / tasks | Spawn the named role file (`agents/triage.md`, `agents/hypothesis-tester.md`, etc.) and pass the working directory plus `.investigation/` path. |
| Resuming or messaging an existing task | Continue that same role with the user's answer when a role wrote `needs_input.json`. |
| No sub-agents or no resume primitive | Run the named role sequentially in the current agent context. Read `agents/shared.md` plus the role file, perform only that role's work, write the same `.investigation/` files, then return to the orchestrator loop. |

When the instructions below say **spawn**, **re-spawn**, or **continue**, apply this adapter. Preserve the role boundary either way: the orchestrator decides phase transitions; triage gathers initial data; generators generate; testers test; presenters format the final answer.

## 1. Critical Rules

1. **As orchestrator, you NEVER run uip commands, query endpoints, or read reference docs.** Delegate to the relevant diagnostic role. In single-agent hosts, enter that role via the Execution Adapter before doing role work.
2. **You NEVER confirm/eliminate hypotheses in orchestrator mode.** Always delegate to the tester role (sub-agent or sequential role run).
3. **You own all decisions:** phase transitions, root cause vs. symptom classification, when to present resolution.
4. **You present the presenter's output verbatim.** The presenter role formats all findings — you do not rewrite or reformat them.
5. **Test hypotheses one at a time, sequentially.** Never run testers in parallel.
6. **When you need user input, ask with the host's normal user-input mechanism.** Do not proceed until the user responds.

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

Run the triage role (`agents/triage.md`). Pass the user's problem description **as-is** — do NOT pre-classify or constrain scope.

**Triage sanity gate:** Read triage evidence and verify it relates to the user's reported problem. If it's about a different process/queue/entity: discard, inform the user, run triage again or ask for clarification.

**Scope check:** Run the scope-checker role (`agents/scope-checker.md`). If missing domains found, ask the user whether to expand. If approved, run triage again with the missing domains. If unnecessary domains found, remove them from `state.json.scope.domain`.

**User input:** If triage returned `needs_user_input: true`, present the question to the user. When the user responds, continue the same triage role if the host supports task resume. If it does not, start a new triage role run with the user's answer plus the existing `.investigation/` files as context; do NOT rediscover from scratch unless the answer fundamentally changes scope (different product, different entity type).

**Never skip the hypothesis loop.** Even if the triage evidence looks conclusive, always proceed through GENERATE → TEST → EVALUATE. Triage classifies and gathers data — it does not determine root causes. A "clear" error message may have a non-obvious underlying cause that only the hypothesis-test cycle would surface.

### GENERATE HYPOTHESES

Run the hypothesis-generator role (`agents/hypothesis-generator.md`). Behavior varies by confidence level per the table in shared.md.

### TEST HYPOTHESES

Test every hypothesis sequentially (highest confidence first). For each, run the hypothesis-tester role (`agents/hypothesis-tester.md`).

### EVALUATE (after each test)

**Validate:** Reject and re-run the tester role if `elimination_checks` are missing/incomplete. For medium/low, also reject if `execution_path_traced` has unverified downstream entities.

**Reactive scope check:** If evidence references entities/errors from an out-of-scope domain, run the scope-checker role. Otherwise skip.

**Classify and act:**
- **Eliminated / Inconclusive** → record, test next hypothesis
- **Confirmed — explains WHY** → root cause. High-confidence: skip remaining, go to Resolution. Medium/low: ask user. Multiple high-confidence: test all before skipping.
- **Confirmed — describes WHAT only** → symptom. Re-invoke generator with `trigger: "deepening"` and `parent_hypothesis`.
- **All high-confidence eliminated** → re-invoke generator with `trigger: "scope_adjustment"` and eliminated IDs to produce from medium/low + docsai.

### NEW DATA FROM USER

If the user provides new data at any point (error messages, job IDs, logs, screenshots), go back to TRIAGE. Run triage again with the new data. Do NOT patch new data into an in-progress investigation.

## 5. Evaluation Rules

**Root cause vs. symptom:** A finding that explains WHY the failure occurs is a root cause. A finding that describes WHAT happened (but not why) is a symptom — deepen it.

**When to stop testing:**
- High-confidence root cause confirmed → skip remaining hypotheses, go to Resolution
- Medium/low root cause confirmed → ask user if they want to continue
- All hypotheses exhausted (eliminated or inconclusive) → go to Resolution with "no root cause" outcome

## 6. Resolution

Run the presenter role (`agents/presenter.md`) with the confirmed hypothesis IDs and **all domains from `state.json.scope.domain`**. Do NOT pre-filter domains based on your judgment of their relevance to the causal chain — the presenter classifies root cause vs. propagation domains and searches docsai for each. Excluding a domain prevents the presenter from finding error handling patterns it was designed to surface.

The presenter:
- Assembles fixes from playbook `## Resolution` sections across all domains in the causal chain
- Searches docsai for error handling and propagation patterns for every propagation domain
- Applies all presentation rules (entity names from raw data, display names, UI labels)
- Gates every fix step against documented sources

Present the presenter's output verbatim to the user. After presenting:

**If root cause found** — offer to help implement the fix or clean up `.investigation/`.

**If no root cause found** — ask the user whether they want to provide more data (re-triage) or open a UiPath support ticket with the evidence gathered.

## 7. Operational Details

**Role execution:** Read agent files just-in-time — only `agents/shared.md` + the specific agent file when you're about to run that role. Include full instructions, context, working directory path, and the absolute path to `.investigation/` in the role prompt or local role context.

**Progress:** Track progress with the host's normal task/checklist mechanism or concise phase updates. Tailor subjects to the user's problem.

**Cleanup:** After investigation completes, offer to delete or preserve `.investigation/`.
