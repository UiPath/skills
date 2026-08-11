# Inline Resource Creation

**Entry condition:** Read this guide only after a genuine empty lookup has passed the Rule 17 batch gate, local-registry capability is available, and the user selects **Create missing resources inline**. Do not read it for resolved lookups, pre-gate discovery, placeholder-only batches, or non-creatable resources.

## Contents

- [Prerequisite and capability state](#0--prerequisite-solution-must-exist--capability-probe-once-per-run)
- [Select resources](#1--select)
- [Deduplicate selected builds](#1c--dedup-the-selected-builds-one-resource-per-name-and-type)
- [Build and register](#2--build-parallel-capped-skip-registration)
- [Adopt interrupted builds](#3b--already-exists--adopt-kind-agnostic-residual)
- [Rediscover, verify, and bind](#4--rediscover--verify--bind-offline---local)
- [Keep rejected siblings visible](#reject-case)

The [registry owner](registry-discovery.md#must-confirm-before-placeholder-fallback) has already grouped every genuine empty and recorded the batch Create choice; non-creatable items are `placeholder only`. This guide first owns resource selection. After §1 returns checked resources, assign unchecked items to fallback, read [create-inline-common.md](plugins/tasks/create-inline-common.md) once, and read only each represented type's [agent guide](plugins/tasks/agent/inline-creation-guide.md) or [API-workflow guide](plugins/tasks/api-workflow/inline-creation-guide.md). If an owning skill is unavailable at runtime, return failure to the Case parent and follow the shared fallback instead of improvising.

## 0 — Prerequisite (solution must exist) + capability probe (once per run)

Carry forward the one cached local-registry capability decision made by the [Rule 17 gate](registry-discovery.md#must-confirm-before-placeholder-fallback); never repeat the probe here. If support is unavailable, Create must not have been offered: surface the inconsistency and assign the selected items to fallback.

Registration and successful local rediscovery require the case's enclosing solution `.uipx`. Because Rule 17 runs before [Phase 2 solution scaffolding](implementation.md#step-6--create-the-case-project-structure), initialize the solution only now, after Create was selected, when that exact `.uipx` is absent:

```bash
uip solution init <SolutionName> --output json
```

Derive the name and working-root location exactly as [case planning](plugins/case/planning.md#project-structure-prerequisites) and Step 6.0 do, so Phase 2 reuses it. Keep local commands within the registry owner's [Local Solution Scope](registry-discovery.md#local-solution-scope). Do not scaffold during capability probing.

## 1 — Select

Present an `AskUserQuestion` multi-select containing only still-empty creatable resources, one option per unique `(name, type)`, with every `<Stage>/<Task>` usage. Cap each prompt at four options and continue in batches when needed. Checked means build once for all compatible usages; unchecked means assign every usage to fallback. Non-creatable empties are absent here because the gate already labeled and assigned them `placeholder only`.

```text
Question: Build which of these inline? Checked → build an in-solution sibling for all compatible usages; unchecked → use <UNRESOLVED> placeholders.
Header: Build inline
multiSelect: true
Options: "<Name> (<type>) — used by <Stage>/<Task>[, ...]"
```

Before building, compare each selected name with registered local siblings of every kind. If another kind already owns the name, ask for a new name; the `solution_folder.<name>` namespace is shared. A same-name collision between two types selected in this batch is resolved by §1c. Then load the common guide once and only the represented type guides; the agent guide owns kind choice, while the API-workflow guide has none.

## 1c — Dedup the selected builds (one resource per name and type)

Run this only for Create-selected task usages. Resolved, unchecked, and placeholder-assigned tasks never join a build.

1. Group usages by trimmed, case-insensitive `(SDD Resolved Resource name, schema-kebab type)`. Folder is not part of the key because inline siblings share one flat solution namespace. When two selected types have the same name, the group whose first use appears earliest in SDD order keeps it; generate a stage-derived name unique across all selections, tenant caches, and local siblings of every kind—bumping its suffix on collision—and apply step 5 to the other group.
2. A single-use group becomes one build.
3. For a multi-use group, compute each usage's canonical contract exactly once through [create-inline-common.md § Step 1](plugins/tasks/create-inline-common.md#step-1--compute-the-pinned-io-contract). Do not derive a second contract or take types from an SDD Inputs-row `Type` cell. Partition usages by identical field-name sets and compatible known types. A deferred type may join one compatible subgroup but cannot bridge two conflicting known types. In SDD order, place a usage in the first compatible subgroup; otherwise start another. The first subgroup is the anchor and keeps the name. Give each other I/O-distinct subgroup one stage-derived name made unique by the same collision check as step 1; step 5 handles every rename.
4. When a subgroup has the same I/O but descriptions that may express different functions, ask without a recommended choice: `Same resource — build once` / `Different — split off the task(s) that don't belong` / `Abort`. On `Different`, let the user select tasks to split and repeat on the resulting pieces until each is a singleton or user-confirmed same-intent set. The final piece containing that subgroup's earliest SDD use keeps its current name; give every other piece a collision-checked stage-derived name, then apply step 5 to each rename. Non-interactive runs make singletons under the same keep-first/uniquely-rename-rest rule, keep renames in memory, and record one high review item per split.
5. For every rename, state `<old> → <new>` and its exact reason—pinned-I/O mismatch, shared cross-type namespace, or user-confirmed distinct intent—then ask permission to update `sdd.md`. On consent, atomically update the affected Section 2 `Resolved Resource` cells and the Section 4 roll-up (`Used By Tasks`, new resource row, and later resolved identity fields) per [the SDD integrations owner](sdd-generation-rules.md#integrations-content-rules-section-4). If denied or non-interactive, keep the SDD unchanged, use the rename only in memory, and warn that a rerun will again start from the old name. Never edit the SDD non-interactively.
6. Build once per resulting subgroup, not per task. Compose its purpose from the first usage through [create-inline-common.md § Step 1b](plugins/tasks/create-inline-common.md#step-1b--compose-the-purpose-from-the-sdd), and bind every subgroup usage to the resulting sibling.

## 2 — Build (parallel, capped, skip-registration)

Using the common guide and represented type guides loaded once after §1, spawn one runtime builder subagent per resulting resource, up to ten concurrently and in waves beyond that cap. Give it the type guide's self-contained brief, quoting SDD-derived names and paths; pass no other Case context, `caseplan.json`, or unrelated tasks. The builder must not register itself and returns `{ built, path, finalInputs[], finalOutputs[], error? }`; the returned I/O is a liveness signal, not the verification authority.

The Case parent never runs the type's init command or reads a sibling skill's files. The subagent invokes the installed owning skill at runtime. An unavailable skill, dead subagent, or `built:false` follows [the shared failure contract](plugins/tasks/create-inline-common.md#failure--surface-and-re-prompt-never-stall) and becomes visible fallback when not retried.

## 3 — Register (sequential)

After each build wave returns, register successful siblings sequentially because every command writes the shared `.uipx`:

```bash
uip solution projects add "<absolute built path>" "<absolute solution .uipx>" --output json
```

Both paths must be absolute. After the sequential registrations, run `uip solution resources refresh --solution-folder "<absolute solution dir>" --output json` before rediscovery-dependent upload/debug work. A registration failure uses the shared failure contract; it does not hide or delete the built directory.

## 3b — "Already exists" = adopt (kind-agnostic residual)

An interrupted run may leave a complete sibling on disk but absent from `.uipx`, causing init or registration to report that the directory/project already exists. Treat this as an adoption candidate, not an automatic failure:

1. Check `registry list --local --output json`. If the name is registered, use its `Category`; a different kind is a name collision, so rename and rebuild. If unregistered, inspect the colliding directory's `project.uiproj`/type marker using the selected type guide's adoption tokens. Adopt only a matching kind.
2. Register the matching existing directory with absolute paths. If `projects add` still reports the name exists while `.uipx` has no project, remove only the exact stale declarations `resources/solution_folder/package/<Name>.json` and `resources/solution_folder/process/<category>/<Name>.json`, retry registration, then refresh resources. Never delete or overwrite the sibling directory.
3. Continue with §4. Do not rebuild, prompt Retry/Skip, or placeholder an adopted matching sibling.

## 4 — Rediscover + verify + bind (offline `--local`)

Rediscover every registered sibling by exact name with `search`, never `get`:

```bash
uip maestro case registry search "<Name>" --type <agent|api> --local --output json
```

Filter `Data.Resources[].Resource` to `Name == <Name>` and `Source == "local"`; require `Folders[0].FullyQualifiedName == "solution_folder"`. Keyword partials do not count. `EntityKey` is an opaque local audit marker, not a project ID or a value to write into the task node. No exact local match follows the shared failure contract regardless of the builder's return value.

Use local discovery only to confirm registration. Its JSON output recursively PascalCases property names, so never take I/O field names from `Resource.Inputs` or `Resource.Outputs`. Read case-preserving names and types from the sibling's on-disk `entry-points.json`; the selected type guide owns its exact path and API-workflow fallback chain. Reconcile that on-disk contract with the pinned contract as matched, missing, or extra. Missing/extra fields are visible completion-report warnings, not fabricated repairs or build failures; call out downstream consumers of a missing pinned output.

For every usage, apply the registry owner's [audit contract](registry-discovery.md#4-return-all-matches), including its inline-local exception; record reconciled I/O in `tasks.md` and `registry-resolved.json`, and mark the task resolved. Inline-local `taskTypeId` is an audit marker only; Phase 2 uses the recorded on-disk schema and skips tenant `tasks describe`. Bind every usage through [create-inline-common.md § Step 3](plugins/tasks/create-inline-common.md#step-3--binding-invariants) and the selected type's subtype. Usages sharing one sibling share one deduplicated binding pair.

## Reject case

If a later hard stop or edit drops a task after its sibling was built, keep the sibling on disk and registered. Report it as `built but not referenced`, including any in-memory-only rename. Never silently deregister or delete it; offer manual cleanup only when the user wants removal. Likewise, report every unselected, failed, or skipped resource that was assigned to placeholder fallback.

<!-- END: inline-resource-creation-guide.md -->
