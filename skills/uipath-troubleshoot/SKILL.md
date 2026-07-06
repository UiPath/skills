---
name: uipath-troubleshoot
description: "UiPath troubleshooting, diagnostics, and root-cause investigations across any UiPath product, feature, runtime, or artifact. Investigates errors, failures, faults, exceptions, regressions, performance problems, unexpected behavior, and silent malfunctions — answers why something failed, broke, stopped, hung, slowed down, returned wrong results, lost access, or stopped working after a change. Also diagnoses failures and faults in Integration Service connectors/connections, Office 365 / Outlook, Google Workspace (GSuite), Excel / Word / PDF activities, Computer Vision, databases / SQL, and HTTP / web activities — route here (not uipath-platform) when the intent is why it failed rather than operating the surface. Walks the available evidence (logs, traces, incidents, status fields, configuration, history) to identify the originating fault and explain what changed. For operating or CRUD on these surfaces→uipath-platform."
when_to_use: "User asks why something failed, broke, stopped, hung, was stuck, returns wrong results, or behaves unexpectedly in any UiPath system. Triggers: 'why did X fail', 'find the cause', 'find why', 'what changed', 'investigate', 'diagnose', 'debug this', 'triage', 'help me figure out', 'what's wrong', 'root cause', 'fix this error', 'inspect this trace / incident / log / job / instance', 'X worked yesterday but now …'. Also fires on raw error messages, exception stacks, error codes, job / queue IDs, or 'stuck / orphan / zombie' state descriptions."
---

# UiPath Troubleshooting Agent

Orchestrate a hypothesis-driven troubleshooting investigation: manage the phase loop, delegate to sub-agents, present findings.

All agents (including you) follow the invariants and confidence-level behavior defined in `agents/shared.md` (§ Invariants, § Confidence-Level Behavior).

## 1. Critical Rules

1. **You NEVER run uip commands, query endpoints, or read reference docs.** Sub-agents do everything else.
2. **You NEVER confirm/eliminate hypotheses yourself.** Always spawn a tester.
3. **You own all decisions:** phase transitions, root cause vs. symptom classification, when to present resolution.
4. **You present the presenter's output verbatim.** The presenter agent formats all findings — you do not rewrite or reformat them. The one exception: you parse and act on the `## Post-presentation actions` block (see §6).
5. **Test hypotheses one at a time, sequentially.** Never spawn parallel testers.
6. **When you need user input, use `AskUserQuestion`.** Do not proceed until the user responds.

## 2. Investigation State

All state lives in `.local/investigations/` (relative to working directory). Schemas in `schemas/`.

| File | Purpose | Writers |
|------|---------|---------|
| `state.json` | Scope, phase, matched playbooks | triage, orchestrator |
| `hypotheses.json` | All hypotheses + status | generator, tester, orchestrator |
| `evidence/*.json` | Interpreted summaries | triage, tester |
| `raw/*.json` | Full raw CLI/API responses | triage, tester |
| `scope-check.json` | Domain expansion verdict | scope-checker |
| `depth-check.json` | Depth-gate verdict on confirmed root causes | depth-verifier |
| `needs_input.json` | User-input request (sub-agent halts; orchestrator reads it, asks via `AskUserQuestion`) | triage, generator, tester |

Sub-agents write raw responses to `raw/` immediately and don't keep them in context. You read evidence summaries, not raw files.

## 3. Phase State Machine

Update `state.json.phase` at each transition:

| Phase | Entry condition | Next |
|-------|----------------|------|
| `triage` | User describes problem (or new data arrives) | `hypotheses` |
| `hypotheses` | Triage complete, playbooks matched | `test` |
| `test` | Hypotheses ready, testing next in confidence order | `evaluate` |
| `evaluate` | Tester returns verdict | `deepen`, `test`, or `depth_check` |
| `deepen` | Confirmed symptom needs sub-hypotheses | `hypotheses` (re-invoke generator) |
| `depth_check` | Hypothesis confirmed as root cause | `resolution` (verified), `test` (one re-round), or halt (write `needs_input.json`) |
| `resolution` | Depth check verified, or all hypotheses exhausted | `complete` |
| `complete` | Findings presented to user | — |

## 4. Investigation Flow

### TRIAGE

1. **Spawn triage** (`agents/triage.md`). Pass the user's problem **as-is** — do NOT pre-classify or constrain scope.
2. **Sanity gate.** Verify triage evidence relates to the reported problem (process/entity/time window). If it's about a different entity: discard, inform the user, re-spawn or ask for clarification.
3. **Scope check.** Spawn scope-checker (`agents/scope-checker.md`); read its `scope-check.json`. Missing domains (`missing_domains`) → `AskUserQuestion` whether to expand; if approved, re-spawn triage with them. Unnecessary domains (`unnecessary_domains`) → remove from `state.json.scope.domain`.
4. **User input.** If triage returned `needs_user_input: true`, ask via `AskUserQuestion`, then **continue the existing triage agent** via `SendMessage` — do NOT spawn a fresh one (a fresh spawn re-discovers everything from scratch). Re-spawn only if the answer fundamentally changes scope (different product/entity type).

**Never skip the hypothesis loop.** Even conclusive-looking triage evidence proceeds through GENERATE → TEST → EVALUATE. Triage classifies and gathers data — it does not determine root cause; a non-obvious cause surfaces only in the test cycle.

### GENERATE HYPOTHESES

Spawn hypothesis generator (`agents/hypothesis-generator.md`). Behavior varies by confidence level per the table in shared.md.

### TEST HYPOTHESES

Test every hypothesis sequentially (highest confidence first). For each, spawn hypothesis tester (`agents/hypothesis-tester.md`).

### EVALUATE (after each test)

**Validate:** Reject and re-spawn if `elimination_checks` are missing/incomplete. For medium/low, also reject if `execution_path_traced` has unverified downstream entities.

**Reactive scope check:** If evidence references entities/errors from an out-of-scope domain, spawn scope-checker and act on its `scope-check.json` (`missing_domains` / `unnecessary_domains`). Otherwise skip.

**Classify and act:**

Before classifying as **explains-WHY**, apply the upstream-cause gate. The mechanism (explicit-event check + implicit-presupposition check) is owned by the depth-verifier — see [`agents/depth-verifier.md` § Causal precedence](agents/depth-verifier.md). Orchestrator decision rule: if the gate identifies any upstream condition that has a `pending` or `supported` sibling hypothesis answering it, classify the current hypothesis as **describes-WHAT** regardless of evidence strength.

**Sibling-precedence backstop** (orchestrator-only — siblings are visible here, not to the depth-verifier): if the candidate root cause is a persistence, propagation, cleanup, or state-transition pattern AND any sibling hypothesis is `pending` AND that sibling questions whether the underlying state has its own originating fault, the sibling MUST be tested before the candidate can be classified as **explains-WHY**. Stopping at the first confirmed hypothesis is incorrect when that hypothesis is downstream.

- **Eliminated / Inconclusive** → record, test next hypothesis
- **Confirmed — explains WHY** (and passes upstream-cause gate) → root cause. Go to DEPTH CHECK (do **not** jump straight to Resolution). Multiple confirmed root causes: depth-check each before skipping the rest.
- **Confirmed — describes WHAT only** → symptom. Re-invoke generator with `trigger: "deepening"` and `parent_hypothesis`.
- **All playbook hypotheses eliminated** → re-invoke generator with `trigger: "scope_adjustment"` and eliminated IDs to produce from docsai (every matched playbook — all confidence levels — was already drafted in the single round).

**Co-equal-roots guard.** Before applying any "skip remaining" exit after a confirmed+verified root cause, check `state.json.matched_playbooks`. If two or more playbooks are present at the same highest confidence level AND they correspond to **distinct, independent** error signatures (different activities, different error codes, neither upstream of the other), every pending hypothesis sourced from those playbooks MUST be tested before stopping. Do not exit on the first confirmed root cause when triage found multiple co-equal roots — you will under-report and miss fixes the user has to make. Only after each co-equal hypothesis is tested (confirmed, eliminated, or inconclusive) and depth-checked when confirmed do you proceed to Resolution.

### DEPTH CHECK (after a hypothesis is confirmed as root cause)

Spawn the depth-verifier sub-agent (`agents/depth-verifier.md`). Pass it the
confirmed hypothesis ID(s), `state.json` path, and the matched playbook path.
The verifier reads `hypotheses.json`, the playbook's `## Context` cause
list ("What can cause it") and `## Resolution` section, and the evidence
files, then writes
`.local/investigations/depth-check.json` with one of:

- `verdict: "verified"` — the confirmed hypothesis names a specific cause
  from the playbook, has cause-specific evidence (not just symptom-level),
  and recommends the matching resolution branch. Proceed to **Resolution**.
- `verdict: "shallow"` — one or more depth dimensions are missing.
  Inspect `gaps`. Each gap is classified `kind: "factual"` or
  `kind: "textual"` by the depth-verifier. Routing rule:
  - **If ANY gap has `kind: "factual"`** — spawn ONE additional
    hypothesis-tester round on the same hypothesis to gather the
    missing evidence, then re-spawn the depth-verifier. Stop after one
    re-round. After that, either declare medium-confidence and proceed
    to Resolution with the gaps surfaced to the user, or — if the gap
    is a genuine data limitation — write `needs_input.json` and stop.
  - **If ALL gaps are `kind: "textual"`** — do NOT spawn the tester.
    Re-running the tester cannot fix narrative-level issues (paraphrase
    looseness, wrong resolution branch picked) since those are the
    *generator's* output, not the tester's. Accept the confirmed
    hypothesis at `confidence: medium` and proceed to Resolution.
    Surface the textual gaps in the presenter's output so the user
    sees them.

**Symptom ≠ cause** (shared.md invariant #9): a symptom-level match confirms the playbook *match*, not the *cause*. The depth-verifier enforces this gate — do not skip it.

### NEW DATA FROM USER

If the user provides new data at any point (error messages, job IDs, logs, screenshots), go back to TRIAGE. Re-spawn triage with the new data. Do NOT patch new data into an in-progress investigation.

## 5. Evaluation Rules

**Root cause vs. symptom:** A finding that explains WHY the failure occurs is a root cause. A finding that describes WHAT happened (but not why) is a symptom — deepen it.

**When to stop testing:**
- High-confidence root cause confirmed → DEPTH CHECK; if verified AND no other co-equal-confidence playbook is still pending (see Co-equal-roots guard above), skip remaining hypotheses and go to Resolution. If co-equal playbooks remain pending, continue testing them first.
- Medium/low root cause confirmed → DEPTH CHECK; if verified, ask user if they want to continue
- All hypotheses exhausted (eliminated or inconclusive) → go to Resolution with "no root cause" outcome (no depth check needed when there is nothing to gate)

## 6. Resolution

Spawn the presenter agent (`agents/presenter.md`) with the confirmed hypothesis IDs and **all domains from `state.json.scope.domain`**. Do NOT pre-filter domains based on your judgment of their relevance to the causal chain — the presenter classifies root cause vs. propagation domains and searches docsai for each. Excluding a domain prevents the presenter from finding error handling patterns it was designed to surface.

The presenter:
- Assembles fixes from playbook `## Resolution` sections across all domains in the causal chain
- Searches docsai for error handling and propagation patterns for every propagation domain
- Applies all presentation rules (entity names from raw data, display names, UI labels)
- Gates every fix step against documented sources

Present the presenter's output verbatim to the user. After presenting:

**Execute Post-presentation actions FIRST.** If the presenter's output has a `## Post-presentation actions` section, run every action in order before any generic follow-up. For each action:

1. Print the "Print as plain text" block exactly as written, separate from the question (raw XML/selectors render poorly inside `AskUserQuestion` options/previews).
2. Print the warning string verbatim if non-empty.
3. Call `AskUserQuestion` with the action's question and options. Ask the project path (or other missing input the action declares) in the same call.
4. If the user accepts, execute the "On user accept" procedure exactly as written — do not improvise. If it references a sub-skill (e.g., `uia-improve-selector`), follow its USAGE.md; otherwise apply the documented direct-edit path and run any validation command listed.
5. If the user declines, stop the action; do not modify files. Move to the next.
6. If the action's `Status` is `blocked` (missing evidence), surface it as a follow-up instead of asking the user to approve an incomplete fix — name the missing evidence field and the agent that should have populated it.

Do NOT skip the Post-presentation actions block when:
- The matched playbook was downgraded from `high` to `medium` by depth-check (the resolution procedure is preserved across confidence downgrades — see `agents/depth-verifier.md` on textual gaps).
- The depth-verifier flagged a cause-name mismatch (textual gap). A reclassified cause does NOT invalidate the playbook's interactive resolution; both can be reported together.
- The recovered/recommended data was produced in a recommendation-only or unproven mode (`InferredRecoveryInfo`, `RecoverySuccessful: false`). The action carries a warning string for exactly this case — present it and let the user decide.

Only after all actions are complete (accepted, declined, or surfaced as blocked) proceed to the generic follow-up:

**If root cause found** — offer to help implement any further changes or clean up `.local/investigations/`.

**If no root cause found** — use `AskUserQuestion` to offer: provide more data (re-triage), or open a UiPath support ticket with the evidence gathered.

## 7. Operational Details

**Spawning:** Read agent files just-in-time — only `agents/shared.md` + the specific agent file when you're about to spawn. Include full instructions and context in the prompt.

**Reasoning effort:** Where the spawn tool exposes a reasoning-effort parameter, set it per role. `low` for the mechanical step-followers — triage, hypothesis-tester, presenter — they execute documented playbook/investigation steps and do not need deep reasoning. `high` for the judgment roles — hypothesis-generator, scope-checker, depth-verifier.

**Progress:** Use `TaskCreate`/`TaskUpdate` for each phase. Tailor subjects to the user's problem.

**Cleanup:** After investigation completes, offer to delete or preserve `.local/investigations/`.
