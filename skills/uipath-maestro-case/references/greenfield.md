# Greenfield: approved SDD to Case project

Use this guide only when the request builds or rebuilds a Case project from an
approved Planner SDD. Targeted edits use `brownfield.md`.

## Inputs and outputs

Input:

- One `sdd.md` written by `uipath-planner` with `Planner Handoff` status
  `ready` and template validation `passed`.
- Optional same-session Planner resolution ledger and successful registry
  refresh.

Outputs:

- `<Solution>/<Project>/caseplan.json`
- Case project sidecars: `project.uiproj`, `operate.json`,
  `entry-points.json`, `bindings_v2.json`, `package-descriptor.json`
- `case-build/registry-resolved.json` when tenant resources are present
- `build-issues.md` when the build has warnings, placeholders, or open items

Never create a Markdown implementation plan. The SDD is the source and the
contract checker's normalized JSON output is an ephemeral inventory.

## Phase 1 — preflight and inventory

### 1. Resolve the SDD

Use an explicitly named Markdown file. Otherwise use `./sdd.md`. Do not select
an arbitrary Markdown file or convert a non-SDD document here.

If the file is absent, invoke `uipath-planner` Case Design Lane in the current
conversation. Planner owns design, review, tenant grounding during design, and
the SDD write. Resume this guide after Planner's Build answer.

### 2. Prove the SDD is consumable

Run both commands from the skill directory:

```bash
python3 scripts/check_case_contract.py check-sdd \
  --sdd <path> --output json
python3 scripts/check_case_contract.py inspect-sdd \
  --sdd <path> --output json
```

`check-sdd` enforces the Planner receipt, template shape, closed enums, legal
rule/gate combinations, completion closure, variable mapping, and lineage.
`inspect-sdd` returns the ordered build inventory.

On any finding:

1. Report the stable code, path, and message.
2. Do not run tenant discovery or write project artifacts.
3. Route correction to `uipath-planner`; this skill does not edit the SDD.

### 3. Choose the execution boundary once

If Planner captured the choice in the same conversation, reuse it. Otherwise
ask once:

- `Build straight through`
- `Pause at the structural preview`

Non-interactive and resumed runs default to straight through. This preference
controls only the structural preview; publish/debug gates always remain.

If the request is plan-only or review-first, present this compact inventory in
chat and stop:

- case name and trigger types
- variables/arguments by category
- stages in order, with kind and completion requirement
- tasks in stage/group order, with type, activation, required, run-once
- condition rule types and SLA responses
- resource names whose tenant identities resolve during build

Do not save the inventory.

## Phase 2 — tenant resolution

Read `registry-discovery.md` to EOF now—not during Phase 1.

1. Run `uip login status --output json`.
2. Reuse a successful same-session Planner registry pull only when its ledger
   and cache remain available; otherwise run `uip maestro case registry pull`.
3. Resolve every resource using the exact `(task type, Resolved Resource,
   Folder Path)` tuple from the SDD. Do not use the task display name as the
   resource query.
4. Group exact empty results by `(name, type)` and ask one decision for the
   batch before placeholders or supported inline creation.
5. Persist evidence to `case-build/registry-resolved.json`. Each entry retains
   `stage`, `task`, `taskType`, `cacheFile`, `searchQuery`, the complete exact
   match set, `selected`, and `rationale`; add `gateDecision` only for an
   actual user decision.
6. Fetch non-connector schemas with `uip maestro case tasks describe ...
   --output json`. Memoize by `(type, entityKey)` for the session. Connector
   schema discovery remains in Phase 3 because it requires complete inputs.

Failure to authenticate or refresh is a Phase 2 stop, not an empty lookup.

## Phase 3 — direct lowering

Read `implementation.md` to EOF. For each SDD declaration, read exactly one
matching JSON recipe from `plugin-index.md`; read each recipe once per type.

### Structural pass

Lower in dependency order:

1. solution and Case project scaffold
2. root Case metadata
3. triggers
4. variables and In/Out arguments
5. `entry-points.json` argument projection
6. stages
7. task structural shapes and task-set grouping
8. SLA and escalation objects
9. conditions after every referenced ID exists

The structural pass preserves full non-connector input schemas with empty
values, connector identity stubs, and placeholders for explicitly accepted
unresolved resources. It never writes graph edges.

Run the structural validation profile once. Prefer `--skeleton-v2`; fall back
to `--skeleton` only when the parser response explicitly says
`--skeleton-v2` is unknown or unsupported. Validation findings are reported at
this boundary but do not hide behind a fallback.

For straight-through, continue. For preview mode, offer publish-for-review,
skip, or abort according to `phased-execution.md`.

### Detail pass

1. Re-read `caseplan.json`; rebuild stage/task/trigger/variable/SLA ID maps
   from the artifact.
2. Fetch connector activity/trigger specs with complete SDD input details.
3. Splice connector context and mint input/output identities.
4. Bind every task input and output directly from its SDD table.
5. Resolve whole-value task output references and in-expression `$xref`
   markers only after output IDs are final.
6. Upgrade resolved connector-bound condition stubs in place.
7. Synchronize `bindings_v2.json` and `entry-points.json`.

## Phase 4 — verification

Read `verification.md` to EOF. The required order is:

1. Case sidecar/resource invariants
2. `check-caseplan`
3. `check-parity`
4. full `uip maestro case validate ... --output json`

Every failed re-check follows a targeted edit. Never re-run an unchanged
validation command.

## Phase 5 — release gates

Read `phased-execution.md` to EOF only after local verification passes. Studio
Web upload, debug, and Orchestrator publish are separate user decisions and
remain optional.

## Recovery

After interruption or context compaction:

1. Re-run `check-sdd` and `inspect-sdd`.
2. Re-read `caseplan.json` and sidecars if they exist.
3. Run `check-caseplan` and `check-parity` to locate the first incomplete
   semantic boundary.
4. Reuse registry/spec evidence only when its query tuple matches the current
   SDD exactly; otherwise refresh/re-resolve.
5. Resume at the first failing phase. Do not regenerate an intermediate plan.

<!-- END: greenfield.md -->
