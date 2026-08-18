---
name: uipath-maestro-case
description: "TRIGGER for UiPath Maestro Case Management implementation or operation: build `caseplan.json` from a Planner-authored Case `sdd.md`, edit an existing case, validate/debug/publish a case, or manage case instances. Also trigger when a user requests a new case without an SDD; hand Case SDD authoring to `uipath-planner`, then resume here. DO NOT TRIGGER for standalone Case SDD design/finalization or PDD-to-SDD (`uipath-planner`), `.xaml`/`.cs` (`uipath-rpa`), `.flow` (`uipath-maestro-flow`), or `.bpmn` (`uipath-maestro-bpmn`)."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion, TodoWrite, Agent
---

# UiPath Maestro Case

Build `caseplan.json` directly from an approved `sdd.md`. The SDD is the only
design contract; never create or consume `tasks.md`.

> **Authoring invariant:** Author Case artifacts with Read + Write/Edit. Never
> mutate a definition with `uip maestro case ... add|update|remove`, including
> `tasks add-connector`, and never probe those commands with `--help`. The
> bundled contract checker is the sole exception: it may read SDD/JSON files
> but is read-only by construction.

## Route first

| Input and intent | Route |
|---|---|
| New case and no approved Case SDD | Invoke `uipath-planner` Case Design Lane in this conversation; Planner is the sole SDD author. Resume at Phase 1 after its Build answer writes `sdd.md`. |
| Planner-authored `sdd.md`, or rebuild from one | Greenfield Phases 1–5. |
| Existing `caseplan.json` and a targeted change | [Brownfield](references/brownfield.md); then Phase 4 and the requested Phase 5 gates. |
| Case schema question | Read [Case schema](references/case-schema.md) only. |
| Runtime case-instance operation | Read [Case commands](references/case-commands.md) only. |

If an SDD is missing, draft, malformed, or not Planner-authored, route it to
`uipath-planner`; never repair or redesign it here. User-facing language stays
continuous—the product handoff is an internal ownership boundary.

## Critical rules

1. **Planner owns every Case SDD.** This skill never writes, finalizes,
   normalizes, or gap-fills `sdd.md`. Never overwrite it.
2. **Preflight before build.** Run the deterministic `check-sdd` command in
   Phase 1. Any error blocks tenant discovery and artifact writes. A receipt
   grep or successful `uip maestro case validate` is not a substitute.
3. **No intermediate plan artifact.** Read declarations directly from the
   normalized SDD contract. Never create `tasks.md`, a T-number list, or a
   second prose representation of the design. For plan-only/review-first
   requests, show the normalized inventory in chat and stop.
4. **Lossless lowering.** Preserve every SDD stage, task, trigger, variable,
   argument, condition, SLA rule, activation mode, required flag, run-once
   flag, input binding, output operator, and explicit default. Do not infer a
   different rule from proximity or list order.
5. **Deterministic parity is a hard gate.** Before CLI validation, run
   `check-caseplan` and `check-parity`. Repair every error and re-run both. The
   build is incomplete until all deterministic checks and full CLI validation
   pass.
6. **Load references just in time.** Read [Greenfield](references/greenfield.md)
   at Phase 1. Read registry guidance only at Phase 2, the matching JSON recipe
   only when lowering that declaration in Phase 3, and release guidance only
   when entering Phase 5. Do not preload the reference tree.
7. **Read a selected reference to EOF.** Every reference ends with
   `<!-- END: ... -->`. Observe that exact marker before using a shape or rule
   from the file; repeat after context compaction.
8. **Fresh registry before resolution.** Run `uip login status --output json`,
   then `uip maestro case registry pull`, at most once per session. Reuse a
   successful same-session Planner pull; otherwise do not inspect stale cache
   files first. See [Registry discovery](references/registry-discovery.md).
9. **Never fabricate tenant identities or schema.** Resolve exact SDD resource
   names. A genuine empty lookup reaches one batched user gate before any
   placeholder or supported inline-create path. Record evidence in
   `case-build/registry-resolved.json`.
10. **Use `--output json` for every parsed `uip` read.** Never parse display
    text.
11. **Write JSON directly.** Do not use Python, Node, `jq`, shell redirection,
    or temporary assembler scripts to create or modify Case artifacts. The
    read-only checker may inspect them. UUID-only subprocesses are allowed.
12. **The task `type` enum is closed:** `process`, `agent`, `rpa`, `action`,
    `api-workflow`, `case-management`, `execute-connector-activity`,
    `wait-for-connector`, `wait-for-timer`.
13. **Edges stay retired.** Emit `edges: []` and top-level `layout: {}`. Model
    reachability with entry/exit conditions; never author visual layout fields.
14. **Resolved resources must be runnable.** Phase 4 checks Case JSON,
    `bindings_v2.json`, `entry-points.json`, resource bindings, connector
    context, output-ID uniqueness, and formal argument IDs before publish.
15. **Never run `uip maestro case init`.** Initialize the solution with
    `uip solution init`, then write the Case project scaffold from the root
    JSON recipe; Case init can create a second solution.
16. **Never auto-run or publish.** Debug may execute live email/API/action
    effects. Studio Web upload, debug, and Orchestrator publish each retain
    their explicit consent gate.

## Phase 1 — SDD preflight

Read [Greenfield](references/greenfield.md), then run:

```bash
python3 <skill-dir>/scripts/check_case_contract.py check-sdd \
  --sdd <sdd.md> --output json
python3 <skill-dir>/scripts/check_case_contract.py inspect-sdd \
  --sdd <sdd.md> --output json
```

Stop on any finding. Treat the normalized contract as an ephemeral build
inventory—not a file to save. Capture the build-review preference once:
straight through, or pause at the structural preview. A plan-only request ends
after presenting the inventory; it creates no build artifact.

## Phase 2 — Resolve tenant dependencies

Read [Registry discovery](references/registry-discovery.md). Refresh once,
resolve exact SDD names, batch unresolved decisions, and write only the
resolution evidence under `case-build/`. Fetch non-connector task schemas with
`tasks describe`; defer connector `case spec` calls until Phase 3.

## Phase 3 — Build directly from the SDD

Read [Direct implementation](references/implementation.md) and the one matching
recipe from [Plugin index](references/plugin-index.md) for each declaration.

1. Initialize one solution and scaffold the Case project.
2. Lower root metadata, triggers, variables/arguments, stages, tasks,
   conditions, and SLA directly from the normalized SDD inventory.
3. Write structural sections in batches. Do not re-read between sibling edits.
4. At the optional preview boundary, run structural validation and pause only
   when the up-front preference requested it.
5. Fetch connector schemas, wire all inputs/outputs and cross-task references,
   complete connector-bound rules, and synchronize sidecars.

## Phase 4 — Prove and validate

Read [Verification](references/verification.md). Run in order:

```bash
python3 <skill-dir>/scripts/check_case_contract.py check-caseplan \
  --caseplan <caseplan.json> --output json
python3 <skill-dir>/scripts/check_case_contract.py check-parity \
  --sdd <sdd.md> --caseplan <caseplan.json> --output json
uip maestro case validate <project-dir> --output json
```

Fix before re-running; never validate twice without an intervening edit. After
three failed repair cycles, ask whether to retry, pause for manual editing, or
abort. Record unresolved or non-blocking issues in `build-issues.md`.

## Phase 5 — Optional lifecycle gates

Read [Phased execution](references/phased-execution.md) only now. In order:

1. Ask before Studio Web upload; refresh solution resources first.
2. Ask before debug; refresh resources first and warn that effects are live.
3. Ask before Orchestrator publish; pack the solution directory, read the
   package path from `Data.Packages`, then publish with `--wait --output json`.

## Reference map

| Need | Read |
|---|---|
| Direct SDD workflow and recovery | [greenfield.md](references/greenfield.md) |
| Deterministic and CLI gates | [verification.md](references/verification.md) |
| JSON recipe dispatch | [plugin-index.md](references/plugin-index.md) |
| Existing-case edits | [brownfield.md](references/brownfield.md) |
| Registry and inline-create decisions | [registry-discovery.md](references/registry-discovery.md) |
| Expressions and cross-task references | [bindings-and-expressions.md](references/bindings-and-expressions.md) |
| Case schema | [case-schema.md](references/case-schema.md) |
| CLI/runtime operations | [case-commands.md](references/case-commands.md) |
| Sidecar synchronization | [bindings-v2-sync.md](references/bindings-v2-sync.md), [entry-points-sync.md](references/entry-points-sync.md) |

## Common failures

- A Planner Handoff header is a receipt, not permission to invoke Planner Lane
  A. A ready Case SDD routes directly to this skill.
- A valid JSON schema does not prove SDD parity; run the parity checker.
- A valid CLI result does not prove connector context, sidecar parity, formal
  argument IDs, output-ID uniqueness, or SDD parity.
- Do not convert explicit sequential work into parallel tasks because no data
  binding joins them. Activation is business behavior.
- Do not repeat a global cancellation/withdrawal event on every primary stage;
  model one interrupting secondary lane.
- Stage completion does not close the case. Keep a root completing case-exit
  rule.

> **Trouble?** Use `/uipath-feedback` to send the report.
