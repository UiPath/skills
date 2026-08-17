---
name: uipath-maestro-case
description: "Always invoke for UiPath Maestro Case Management build work: `caseplan.json`, `sdd.md`, or building/creating a case when no SDD exists yet (the case design is produced first, then confirmed in one review). Produces tasks.md and authors or edits caseplan.json directly with Write/Edit. For .xaml→uipath-rpa, .flow→uipath-maestro-flow, .bpmn→uipath-maestro-bpmn. For standalone case SDD design, case `sdd.draft.md` finalization, PDD→SDD, or cross-product planning→uipath-planner."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion, TodoWrite, Agent
---

# UiPath Case Management Authoring Assistant

Builds UiPath Case Management definitions from `sdd.md`. Generates the `tasks.md` plan, then writes `caseplan.json` directly via per-plugin JSON recipes. Shared case facts/semantics live in [references/case-knowledge/](references/case-knowledge/INDEX.md) (symlinked single source, `K-*` rule IDs) — cited below, never restated.

> **Authoring invariant:** Never use mutating `uip maestro case` commands (`cases|stages|tasks|*-conditions ... add|update|remove`, including `tasks add-connector`) or explore them via `--help`. Use the CLI only for scaffolding, metadata reads, validation/debug, runtime operations, and solution sync/upload; consult [case-commands.md](references/case-commands.md) only when exact syntax is needed. CLI availability or a final `validate` requirement does not override this rule.

**No `sdd.md`? The design belongs to `uipath-planner`** — one continuous flow per the handoff contract ([case-knowledge/contracts/handoff.md](references/case-knowledge/contracts/handoff.md), K-HOF-1..5): the planner's Case Design Lane runs in THIS conversation, confirms in ONE eight-section Case Review, writes `sdd.md` on the Build answer, and this skill continues immediately. This skill never designs (Rule 1).

**Scope:** two journeys — **greenfield** (build a new case from `sdd.md`, user-provided or planner-designed) and **brownfield** (targeted edits to an existing `caseplan.json` — see [references/brownfield.md](references/brownfield.md)). Editing a case that also lives in Studio Web? Brownfield pulls the current server state first (`uip solution download` / `solution projects resync`) — see [brownfield.md § Pull latest first](references/brownfield.md#pull-latest-first-before-editing).

## When to Use This Skill

- User provides `sdd.md` and wants a Case Management project built
- User asks to create a case but has no `sdd.md` (design handoff — Rule 1; this skill builds from the `sdd.md` the lane writes)
- User asks to generate implementation tasks from `sdd.md` or convert a spec to a plan
- User asks to edit an existing `caseplan.json` (add/remove a stage or task, change a condition, swap a trigger) — brownfield, skips planning
- User asks about the case JSON schema, or wants to manage runtime case instances ([case-commands.md](references/case-commands.md))

**Do not use for:** `.xaml` → `uipath-rpa`. `.flow` → `uipath-maestro-flow`. Standalone agents/APIs/processes outside case context → the corresponding UiPath skill.

## Critical Rules

1. **No `sdd.md` → hand the design to the planner lane, build on its Build answer.** Full protocol: K-HOF-1..3 — hand off immediately on detection, in this conversation, never a subagent; the lane's Case Review is the ONLY approval surface (a generic "Build Plan" yes must not create files); on the Build answer proceed straight to `uip solution init` + Phase 1 with no extra prompt. Never overwrite an existing `sdd.md`. Plan-only requests (`sdd.md` + `tasks/tasks.md`, stop before `caseplan.json`): hand off the same way, then write compact `tasks/tasks.md` ([planning.md § Step 3](references/planning.md)) with no plugin reads or tenant discovery. Draft finalization → the lane's fast path.
2. **`sdd.md` is the sole input post-design — across sessions.** Trust it as written; never validate or gap-fill it. In the conversation that just confirmed the design, the in-memory model IS the content — do not re-read the just-written file. Build-phase ambiguity → AskUserQuestion, never silent inference.
3. **PHASE 1 HARD GATE — fresh registry before planning, pulled at most once per session.** `uip login status --output json` then `uip maestro case registry pull` before any cache inspection, resolution, or Phase 1 artifact write. The same-session fast path, verify-only planning (persist the lane's ledger verbatim per K-LEDG-1, execute recorded `gateDecision`s per K-LEDG-2), the plan-only exception, and the cache-state rule (K-LEDG-3) are specified in [planning.md § Step 1](references/planning.md); discovery reads `~/.uip/case-resources/<type>-index.json` directly ([registry-discovery.md](references/registry-discovery.md)). Login/pull failure → surface it and stop Phase 1.
4. **`--output json` on every parsed read.**
5. **Follow the plugin per node type.** Open the matching `planning.md` during planning and `impl-json.md` during execution. Never guess JSON shapes from memory.
6. **`tasks.md` is declarative and lossless.** One T-entry per `sdd.md` declaration — never group, never silently omit, defaults-looking rows included; unrecognized/ambiguous rows → AskUserQuestion ([planning.md § 4.0](references/planning.md)). Explicit SDD rules are authoritative once they pass the Critical Rules (every `selected-tasks-completed` selector names a non-adhoc same-stage sibling — stop and repair violations, never preserve them). Preserve rationale, binding modes, and JSON literals verbatim; project Outputs rows through [io-binding § projection](references/plugins/variables/io-binding/planning.md#sdd-outputs-table-to-tasksmd-projection-mandatory) with operators and operands unchanged. T-entry headings quote display names (`## T08: Add wait-for-timer task "First Step" to "Process"`); every §4.6 task T-entry carries its own `activation-mode:` + `entry-rule:` lines.
7. **`tasks.md` gate — auto-approved by default.** Phase 1 auto-proceeds into Phase 2; stop after `tasks.md` only when the request explicitly asked for a plan-only / review-first run. Re-read `tasks.md` before executing.
8. **Unresolved resource → placeholder, never fabricate IDs.** Keep `<UNRESOLVED: ...>` markers in `tasks.md`. Shapes: [placeholder-tasks.md](references/placeholder-tasks.md) + [event-trigger placeholder](references/plugins/triggers/event/impl-json.md).
9. **Persist every registry resolution to `registry-resolved.json`** — exact entry shape, `gateDecision` presence semantics, and same-session seeding: K-LEDG-1..3 ([case-knowledge/contracts/resolution-ledger.md](references/case-knowledge/contracts/resolution-ledger.md)).
10. **Cross-task refs are direct output references** (K-VAR-1): plan as `"Stage"."Task".output`; resolve whole-value `<-` and in-expression `vars.$xref(...)` through [io-binding § output-reference-ID](references/plugins/variables/io-binding/impl-json.md#output-reference-id-authoritative) — use the source output's `.id`, never a reassigned output's `.var`. Discover output names via `case spec` / `tasks describe`, never fabricate.
11. **Build-review preference decides the Phase 2 → 3 boundary — captured ONCE, up front, never mid-build.** Greenfield-with-handoff folds it into the lane's Build options; provided-SDD asks once after the roadmap; non-interactive/resumed runs default straight-through. Boundary mechanics, the `--skeleton` fallback contract, and the publish-for-review flow: [phased-execution.md](references/phased-execution.md). Hard stops NEVER bypassed: Phase 4 retry exhaustion, Phase 5 entry, Phase 6 entry, Phase 7 entry.
12. **Never run `uip maestro case debug` or the Phase 7 Orchestrator publish automatically.** Both execute real side effects; each requires its own AskUserQuestion consent gate.
13. **All skill artifacts: Read + Write/Edit only.** No `python`/`node`/`jq`/`sed`/`awk`/shell-redirection reads or writes of `caseplan.json`, `sdd.md`, `tasks.md`, `registry-resolved.json`, `bindings_v2.json`, `entry-points.json`, or any listed artifact — including helper scripts under `/tmp` (the build-assembler pattern is the same violation). The `node -e ... fs.*` ban covers ALL file reads including `~/.uip/case-resources/`. Bash subprocesses only for UUID generation, CLI metadata fetches, validate, debug, and solution scaffold/upload. Full contract + the ~30KB split cadence: [case-editing-operations.md § Tool usage](references/case-editing-operations.md#tool-usage--mandatory).
14. **Resolved resources must be runnable; sidecar parity is an unconditional Phase 3 exit check.** Run Step 12 Checks 7/9/11/12 before Phase 4 even when publish/debug/refresh are skipped ([implementation.md § Step 12](references/implementation.md#step-12--end-of-phase-3-validator-pass)); `validate` success never substitutes. Always `resources refresh` before `solution upload`/`debug`; every upload carries `--output-filter "{Status: Status, SolutionId: SolutionId, DesignerUrl: DesignerUrl}"`.
15. **Design handoff runs in-conversation per K-HOF-1; planner unavailable → degraded path** (one line, ask for an `sdd.md`, stop — never improvise a design). **Receipt spot-check** on any `sdd.md` this conversation did not watch being written: K-SDD-5 (one Grep — four Section headings + ≥ 1 `##### Task` block; summary SDDs route back to the lane's conformance gate).
16. **Caseplan task `type` enum is closed — 9 schema-kebab values** (K-TYP-1); never the plugin folder or CLI flag names, never the K-TYP-2 never-author list. Naming asymmetry table: [case-knowledge/facts/types.yaml](references/case-knowledge/facts/types.yaml).
17. **Empty registry lookup → AskUserQuestion BEFORE any placeholder fallback — unless the user already ruled at the design-time gate** (execute recorded `gateDecision`s without re-asking; entries with NO `gateDecision` are defaulted deferrals and get the full gate — K-LEDG-2). Gate options, `(name, type)` grouping, the inline-create path (agents + API workflows only, gate-selected only), and build/register/verify mechanics: [registry-discovery.md § Create-on-Missing](references/registry-discovery.md#create-on-missing-build-and-rediscovery).
18. **Layout state lives in top-level `layout: {}`, never on nodes/edges.** No node-level `position`/`style`/`measured`/`width`/`height`/`zIndex`, no computed stage positions, no edge waypoints — the FE strips them anyway ([case-editing-operations.md](references/case-editing-operations.md)).
19. **Generated output IDs use one global namespace** — run Step 12 Check 8 at Phase 3 exit; `validate` never substitutes.
20. **Edges retired — `schema.edges` stays `[]`** (K-EDGE-1); flow is condition-driven, case start is the first stage's `case-entered` entry. Read-only edge shapes for round-tripped files: [case-schema.md § Appendix](references/case-schema.md#appendix--edge-shapes-read-only--never-author).
21. **Global events are modeled once; SLA responses are chosen, not assumed** (K-STG-6, K-SLA-4/5): response from the source's words, `start-task` on the task's OWN entry (never a stage-entry row), breach = `slaId` alone (K-SLA-3), no per-stage duplication. Emit shapes: the SLA/condition plugins; facts: [case-knowledge/facts/sla.yaml](references/case-knowledge/facts/sla.yaml).
22. **Formal-arg slot ids are minted `v`+8-chars, never copied from the companion name** — run Step 12 Check 10 at Phase 3 exit; `validate` does not check this ([global-vars/impl-json.md § Formal-arg slot ID format](references/plugins/variables/global-vars/impl-json.md#formal-arg-slot-id-format)).
23. **Never run `uip maestro case init` — it forks the solution.** Always `uip solution init <SolutionName>` + the T01 direct-JSON scaffold ([implementation.md § Step 6](references/implementation.md#step-6--create-the-case-project-structure)).
24. **Read-to-EOF is a mutation gate for every reference-derived shape.** Every `references/*.md` (and `case-knowledge/**.md`) ends with `<!-- END: <filename> -->`; before the first Write/Edit that uses a shape from a reference, Read that file until its END marker appears this session. HARD STOP otherwise; re-open after context compaction. Tail contracts are normative.
25. **Stage labels and task display names: whole-case-unique, no `:`** (K-NAME-1/3 — exact, case-sensitive comparison; an omitted `displayName` resolves to the bound resource name and shares the pool). Assign unique names in Phase 1 — renaming after Phase 3 re-touches every name-keyed artifact.

## Routing — greenfield vs brownfield

| Condition | Journey |
|---|---|
| New case, or `sdd.md` provided, or no `caseplan.json` yet, or (re)build from a spec | **Greenfield** — design handoff (when no `sdd.md`) + Phases 1→7 |
| `caseplan.json` exists AND intent is a targeted edit | **Brownfield** — [references/brownfield.md](references/brownfield.md); honors the Rule 12 consent gates and the Phase 5/6/7 contracts |

## User-facing roadmap — required at skill start

After routing, print one short roadmap (≤ 5 lines, business language, once per invocation):

| Journey | Roadmap |
|---|---|
| New case without an SDD | `1. I read your request and make the design calls, checking your UiPath tenant along the way. 2. One review packet: case snapshot, primary journey, other paths, SLA responses, business rules, resources, and every decision I made — you confirm or correct. 3. Build and validate without interruptions; the full technical design doc is saved alongside for reference. 4. Pause for your call before any run or publish.` |
| New case with an SDD | `1. Read the design and verify available UiPath resources. 2. One question: build straight through, or pause at a mid-build preview. 3. Plan, build, and validate without further interruptions. 4. Pause for your call before any run or publish.` |
| Targeted edit | `1. Pull the latest case. 2. Apply the requested change. 3. Validate the updated case. 4. Ask before running or publishing anything.` |

## Workflow

**Design handoff** (conditional — no `sdd.md` at the resolved path; an `.md` whose basename contains `sdd` counts, copied to `./sdd.md` via Read+Write; protocol K-HOF-1..3) → **Phase 1 Planning** ([planning.md](references/planning.md): `tasks/tasks.md` + `tasks/registry-resolved.json` at the working root, adjacent to `sdd.md`, NEVER inside `<Solution>/`; Create-selected resources built as in-solution siblings per Rule 17) → **Phase 2 Prototyping** ([implementation.md](references/implementation.md) + [phased-execution.md](references/phased-execution.md): solution + triggers + variables + entry-points sync + stages + shape-only tasks + SLA + condition stubs + informational validate; boundary per Rule 11) → **Phase 3 Implementation** (connector schemas via `case spec`, I/O binding, stub upgrades, `$xref` resolution, Step 12 checks — no stop) → **Phase 4 Validate** (Step 12 checks, then full `validate`; ≤ 3 retries, each preceded by a fix edit; 3rd failure → HARD STOP) → **Phase 5 Publish** (HARD STOP: `Publish to Studio Web` / `Skip to Debug`) → **Phase 6 Debug** (HARD STOP: `Run debug session` / `Continue to publish`) → **Phase 7 Publish to Orchestrator** (HARD STOP: on Publish run `resources refresh` → `case pack` → `solution pack` → `solution publish` — `case pack` is mandatory every pass, it alone compiles `caseplan.json.bpmn`; publish the `solution pack` `.zip`, path from `Data.Packages`).

### Kickoff — set dev expectations first

Present the flow once per run (at design-handoff start when it runs, else at Phase 1 start) — allow-listed standalone block:

> Here's how I'll build this case, and where I'll stop for your call:
> - **Planning** — I draft a task plan from the spec and continue; ask up front if you want to review it first.
> - **Prototyping** — I build the reviewable case flow (stages, tasks, triggers, rules, SLA/escalation; connector rules use stubs). Whether I pause here for a Studio Web preview is **your up-front call** — asked once at the start, never mid-build.
> - **Implementation** — I wire task inputs/outputs, connector schemas, and resolved connector-rule details.
> - **Validate** — I run validation and fix errors.
> - **Publish / Debug / Publish to Orchestrator** (optional) — **you choose** at each gate.

When the design handoff runs, prefix one line: "First I'll design the case from what you've given me — checking your UiPath tenant along the way — and show one decision-first review packet; one confirmation, then I build; the full technical design doc (`sdd.md`) is saved alongside for reference." Brownfield: the short version in [brownfield.md](references/brownfield.md).

## Reference Navigation — the router

| Key in hand | Read |
|---|---|
| No `sdd.md` (design needed) | [case-knowledge/contracts/handoff.md](references/case-knowledge/contracts/handoff.md), then the planner lane |
| Phase 1 planning | [planning.md](references/planning.md) |
| Phase 2/3 execution | [implementation.md](references/implementation.md) + [phased-execution.md](references/phased-execution.md) |
| Targeted edit to existing case | [brownfield.md](references/brownfield.md) |
| Edit mechanics (IDs, anchoring, batch contract, tool rules) | [case-editing-operations.md](references/case-editing-operations.md) |
| Document-level JSON shape | [case-schema.md](references/case-schema.md) |
| Shared facts: type enums / slot legality / naming / SLA | [case-knowledge/facts/](references/case-knowledge/INDEX.md) (types, pairing, naming, sla) |
| Shared semantics: stages / sequencing / edges / expressions / variables | [case-knowledge/semantics/](references/case-knowledge/INDEX.md) |
| Validate failure message | [case-knowledge/errors/validate-codes.md](references/case-knowledge/errors/validate-codes.md) |
| CLI syntax (read-only surface + runtime ops) | [case-commands.md](references/case-commands.md) |
| Troubleshoot a failed run | [troubleshooting-guide.md](references/troubleshooting-guide.md) |
| Registry resolution / create-on-missing | [registry-discovery.md](references/registry-discovery.md) |
| I/O wiring + expression prefixes | [bindings-and-expressions.md](references/bindings-and-expressions.md) |
| Connector activity/trigger/event config | [connector-integration.md](references/connector-integration.md) · [case-spec-input-details.md](references/case-spec-input-details.md) |
| Placeholders / bindings sidecar / entry-points sync | [placeholder-tasks.md](references/placeholder-tasks.md) · [bindings-v2-sync.md](references/bindings-v2-sync.md) · [entry-points-sync.md](references/entry-points-sync.md) |

**Per-type plugins** (`references/plugins/` — `planning.md` in Phase 1, `impl-json.md` in Phase 2/3). Structural: [case](references/plugins/case/planning.md) (root, T01) · [stages](references/plugins/stages/planning.md) · [sla](references/plugins/sla/planning.md) · [global-vars](references/plugins/variables/global-vars/planning.md) · [io-binding](references/plugins/variables/io-binding/planning.md) · [logging](references/plugins/logging/impl-json.md). Tasks (SDD `Type:` = JSON `type`, schema-kebab — mapping + CLI flags in K-TYP-1): [process](references/plugins/tasks/process/planning.md) · [agent](references/plugins/tasks/agent/planning.md) · [rpa](references/plugins/tasks/rpa/planning.md) · [action](references/plugins/tasks/action/planning.md) · [api-workflow](references/plugins/tasks/api-workflow/planning.md) · [case-management](references/plugins/tasks/case-management/planning.md) · [connector-activity](references/plugins/tasks/connector-activity/planning.md) (`execute-connector-activity`) · [connector-trigger](references/plugins/tasks/connector-trigger/planning.md) (`wait-for-connector`) · [wait-for-timer](references/plugins/tasks/wait-for-timer/planning.md). Triggers: [manual](references/plugins/triggers/manual/planning.md) · [timer](references/plugins/triggers/timer/planning.md) · [event](references/plugins/triggers/event/planning.md). Conditions: [stage-entry](references/plugins/conditions/stage-entry-conditions/planning.md) · [stage-exit](references/plugins/conditions/stage-exit-conditions/planning.md) · [task-entry](references/plugins/conditions/task-entry-conditions/planning.md) · [case-exit](references/plugins/conditions/case-exit-conditions/planning.md). Connector-bound condition rules carry `rule.uipath` from `case spec` — bare rules are invalid in Studio Web and NOT caught by `validate` ([connector-trigger-impl.md § condition rule](references/connector-trigger-impl.md#target-connector-bound-condition-rule)).

## Anti-patterns

- **Do NOT design in this skill** — no improvised interviews, no design subagents, no generic "Build Plan" checkpoints (K-HOF-1; Rule 1).
- **Do NOT start Phase 1 before the Case Review is approved**, and do NOT build on a summary SDD (receipt check — K-SDD-5).
- **Do NOT validate after each T-entry, and NEVER re-validate without an intervening edit.** Once at Phase 2 end (informational), once in Phase 4 (authoritative); every retry needs a fix edit first ([phased-execution.md § Validate-loop guard](references/phased-execution.md#validate-loop-guard--no-re-validate-without-an-intervening-edit)).
- **`tasks.md` and `caseplan.json` use per-section batched writes — never per-T-entry, never one mega-Write.** Contracts: [planning.md § 4.0a](references/planning.md) and [case-editing-operations.md § Per-section batch write contract](references/case-editing-operations.md#per-section-batch-write-contract--canonical). TaskUpdate per T-entry is the audit trail; recovery = re-Read + resume from the next un-applied T-entry.
- **Do NOT emit standalone narration turns between tool calls.** Status text shares the turn with the next tool_use; ≤ 1 sentence inline. HARD CAP 200 tokens per text block (500 for the allow-list: kickoff, hard-stop preambles, completion reports, DesignerUrl print, post-validate summaries). Announcement verbs (`Building`, `Composing`, `Now I'll`, `Next:`, `Let me`, …) are forbidden regardless of length — invoke the tool instead.
- **Structure and activation follow the shared grammar** — sequencing/task-set structure K-SEQ-1/2/3, adhoc K-SEQ-4, secondary stages + global events K-STG-2..6, case completion as a root rule K-PAIR-6. Never re-derive these from memory; cite the K-file.
- **Do NOT edit the auto-generated `caseplan.json.bpmn`** — only `uip maestro case pack` writes it.
- **Case file is flat at `<Solution>/<Project>/caseplan.json` — never under `content/`**, and never authored via `cases add` ([plugins/case/impl-json.md](references/plugins/case/impl-json.md)).
- **Do NOT fabricate expression syntax for conditional SLA rules** — describe the condition; the execution phase determines the exact form.
- **Do NOT place `tasks/` inside the solution or project directory** — it tracks `sdd.md` at the working root.
- **Do NOT invoke other skills automatically** — except the Rule 1/15 design handoff (in-conversation) and the Rule 17 gate-selected inline-create path (subagents: `uipath-agents` / `uipath-api-workflow`). No subagents for design, draft finalization, or plan-only generation.

> **Trouble?** Use `/uipath-feedback` to send a report.
