# Case Editing Operations

Read this file for direct `caseplan.json` mutation mechanics. Per-element JSON
shapes live in the corresponding `plugins/**/impl-json.md` recipe.

## Responsibilities of Direct JSON Authoring

| Concern | Requirement |
|---|---|
| Runtime task schema | Source from `case-build/registry-resolved.json` or a fresh `tasks describe`/connector spec. Never invent it. |
| IDs | Mint with the prefixes below; require global uniqueness. |
| Task `elementId` | Always `${stageId}-${taskId}`. |
| Stage data | Include `parentElement`, `isInvalidDropTarget`, and `isPendingParent`. |
| Layout | Emit only top-level `layout: {}`. Never author node coordinates or styles. |
| Edges | Keep `schema.edges: []`; conditions express flow. |
| Root bindings | Remove declarations no longer referenced by tasks/triggers/rules. |
| Task ordering | Encode parallel groups in `stage.data.tasks`; encode dependencies in entry conditions. |
| Sidecar | Key `id-map.json` by stable SDD locators, never by generated task numbers. |

## Pre-flight Checklist

Before a structural write, prove:

1. The target is `<SolutionDir>/<ProjectName>/caseplan.json` next to
   `project.uiproj`.
2. The first scaffold write creates the project files described by
   [plugins/case/impl-json.md](plugins/case/impl-json.md); later writes require
   the file to exist.
3. Every ID matches its prefix/length and is globally unique.
4. Primary stages omit `stageType`; exception stages set
   `stageType: "secondary"`.
5. Every regular stage is reachable by at least one entry condition. The first
   uses `case-entered`; successors reference a reachable predecessor.
6. `schema.edges` is empty and `layout` is `{}`.
7. Every task has the correct `elementId` and occurs exactly once in its
   stage's task-group structure.
8. Parallel siblings share a group; sequential tasks occupy ordered groups and
   have authored dependency rules.
9. Task entry conditions come exclusively from SDD Entry Condition rows. Never
   inject a type-based default while creating the task.
10. Every cross-task binding names existing source stage/task/output IDs.
11. Every runtime task's identity and I/O match the resolution evidence.
12. A write never removes unrelated nodes, bindings, variables, or metadata.

## ID Generation

Use prefix plus random characters from `[A-Za-z0-9]`. Scan every existing `id`
before accepting a candidate. Mix character classes and reject patterned or
reused suffixes.

| Entity | Format |
|---|---|
| Case | `case-` + 10 |
| Stage | `Stage_` + 6 |
| First trigger | literal `trigger_1` |
| Other trigger | `trigger_` + 6 |
| Task | `t` + 8 |
| Task condition / rule | `c` + 8 / `r` + 8 |
| File-level condition / rule | `Condition_` + 6 / `Rule_` + 6 |
| SLA / escalation | `sla_` + 8 / `esc_` + 6 |
| Binding | `b` + 8 |
| Variable formal slot | `v` + 8 |

IDs exposed through `=vars.<id>`, BPMN, or XML must begin with a letter or
underscore. UUID fields in `operate.json` and `entry-points.json` are UUID v4;
they are not prefixed IDs.

### `id-map.json`

Use semantic locators derived from the normalized SDD contract:

```json
{
  "case": { "id": "root" },
  "trigger:Invoice received": { "id": "trigger_1" },
  "stage:Review": { "id": "Stage_aB3kL9" },
  "task:Review/Validate invoice": {
    "id": "t8GQTYo8O",
    "stageId": "Stage_aB3kL9"
  },
  "rule:task:Review/Validate invoice/1": {
    "id": "rK9xQw3Lp",
    "conditionId": "c4fGhJ2Mn"
  }
}
```

Create it with the Case scaffold, append after each completed lowering section,
and keep it beside `caseplan.json`. A duplicate semantic locator or locator
pointing to a missing ID is a deterministic failure.

## Expression Prefixes

- Single-value task input lookup: `=vars.<id>` or `=bindings.<id>`.
- Conditions, operators, dotted access, connector bodies, and metadata access:
  `=js:<expression>`.

See [bindings-and-expressions.md](bindings-and-expressions.md) before authoring
non-literal expressions.

## Tool usage — mandatory

Use the host's Read/Write/Edit primitives for artifact mutation. Use CLI
commands only for UiPath operations and read-only discovery. Do not hide JSON
mutation in Python, Node, `jq`, shell redirection, `sed`, or `awk`.

The bundled `check_case_contract.py` is deliberately read-only. It validates
artifacts but never rewrites them.

## Per-section batch write contract — canonical

The normalized SDD contract supplies ordered sections: scaffold, variables,
triggers, stages, task shapes, conditions, SLA, and bindings.

For each section:

1. Read `caseplan.json` once.
2. Compose the complete post-section state from that snapshot.
3. Prefer narrow edits anchored on a unique generated ID. For a large section,
   replace its whole container only when every untouched field is copied
   verbatim.
4. Do not re-read between independent sibling edits. Re-read when a later edit
   depends on text created by an earlier edit.
5. Run `check-caseplan`, then `uip maestro case validate --output json` at the
   section boundary when the intermediate artifact is expected to be valid.
6. On interruption, re-run `inspect-sdd`, read the artifact and semantic
   `id-map.json`, and resume at the first missing locator. No plan file or
   checkpoint prose is needed.

The scaffold-only and stage-only states can be intentionally incomplete. For
those two boundaries, use JSON/root invariants and defer tenant validation until
conditions make the graph reachable.

## Primitive Operations

### Generate a fresh ID

Mint according to the table, scan the complete artifact and current batch for a
collision, then append the semantic locator to `id-map.json`.

### Add a node (Trigger / Stage)

Use the owning plugin shape, mint a unique ID, append to `schema.nodes`, keep
`schema.edges` empty, and record the semantic locator.

### Add an edge — RETIRED

Never author an edge. Add or edit the destination stage's condition instead.

### Add a task to a stage

Use the type recipe and resolved runtime schema, set `elementId`, append to the
correct parallel/sequential group, and add only the SDD-authored entry rules.

### Bind an input

Confirm source existence and type compatibility, use the sink-correct expression
form, and keep connector bindings synchronized with `bindings_v2.json`.

### Delete a node

Before removal, sweep task groups, conditions, bindings, entry points, variable
bridges, SLA targets, and `id-map.json`. Deleting a stage also requires every
successor condition to be repointed or removed.

### Delete a task

Remove it from the stage group, delete rules targeting it, repoint consumers of
its outputs, prune unreferenced root bindings, and remove its semantic locator.

### Delete a condition rule

Remove the rule from its owning condition. If the condition becomes empty,
remove the condition. For connector rules, prune unreferenced context bindings
and refresh `bindings_v2.json`.

### Delete a case-exit completion rule

Remove the matching completion rule and its IDs. The remaining case must still
have at least one reachable completion rule; otherwise parity fails.

### Delete an edge — defensive only

If a canvas round trip materialized edge objects, remove them all and restore
`schema.edges: []`. Never adapt one into a new transition.

## Composite Operations

### Insert a stage between two existing stages

Add the stage, give it an entry rule referencing the predecessor, repoint the
successor's relevant entry rule to the inserted stage, and preserve unrelated
conditions.

### Replace a placeholder task with an enriched task

Keep the task `id`, `elementId`, group position, and semantic locator. Replace
only unresolved runtime data with the freshly described identity, inputs,
outputs, and context. See [placeholder-tasks.md](placeholder-tasks.md).

### Re-sync a task after its source schema changed

Fetch the new contract; diff inputs/outputs; preserve compatible values; remove
obsolete bindings; add newly required inputs as unresolved; sweep consumers of
removed outputs; then validate parity and CLI shape.

### Repoint a non-connector task at a different resource

Verify type compatibility, fetch the target contract, perform the re-sync
procedure, and update the resolution evidence. Never change only the ID while
leaving the old schema.

### Move a task to a different stage or lane

Remove it from the source group, insert it into the destination group, recompute
`elementId`, update the map's `stageId`, and sweep source/destination dependency
rules plus every cross-task binding's `sourceStage`.

### Rename or delete a global variable or argument

Sweep task inputs, all condition expressions, connector context/body fields,
trigger bridges, and variable companion arrays. Rename every exact reference;
for delete, repoint or clear every consumer. Refresh connector bindings when
affected.

### Change a variable's type or default

Keep the variable ID. Update every duplicated type slot (formal, companion, and
trigger bridge for In arguments), then type-check every expression consumer.
File variables retain the required JSON schema and empty default.

### Modify or remove an SLA or escalation

Address entries by ID. Keep the unconditional `=js:true` SLA rule last. Removing
the last SLA removes the property; removing an escalation leaves the rule's
`escalationRule: []`.

### Replace a trigger with a different type

Keep the node ID, replace only type-specific inputs from the target recipe, sync
`entry-points.json`, and migrate or remove trigger variable bridges. Manual
triggers omit `data.inputs`; timer/event triggers use their full recipes.

### Re-target an event trigger (same type, different event)

Fetch a new connector spec, rebuild the event data, re-resolve output bridges,
sync entry points and `bindings_v2.json`, and refresh solution resources.

### Convert a Stage to/from an Exception Stage

Keep the node type and ID. Add `stageType: "secondary"` for an exception stage;
remove the key for primary. Recheck reachability conditions.

### Re-wire a stage transition — RETIRED (no edges)

Edit the relevant stage entry/exit conditions. Do not create an edge.

## Validation Cadence

At every valid section boundary run, in order:

1. `check_case_contract.py check-caseplan`
2. `check_case_contract.py check-parity`
3. `uip maestro case validate <file> --output json`

Repair the first reported invariant at its source, not by deleting unrelated
topology. After three failed repair attempts, stop with the exact findings and
the last command output.

## Anti-Patterns

- generated task-number keys or an intermediate task plan;
- hand-authored runtime task schemas or connector context;
- edges or node-level layout fields;
- type-based default entry conditions;
- whole-file rewrites that drop untouched state;
- resource identity swaps without an I/O re-sync;
- claiming completion before parity and CLI validation both pass.

## Quick Reference — Operation to Plugin

| Need | Recipe |
|---|---|
| Scaffold | [case](plugins/case/impl-json.md) |
| Stage | [stages](plugins/stages/impl-json.md) |
| Trigger | [manual](plugins/triggers/manual/impl-json.md) · [timer](plugins/triggers/timer/impl-json.md) · [event](plugins/triggers/event/impl-json.md) |
| Task | [action](plugins/tasks/action/impl-json.md) · [agent](plugins/tasks/agent/impl-json.md) · [RPA](plugins/tasks/rpa/impl-json.md) · [process](plugins/tasks/process/impl-json.md) · [API workflow](plugins/tasks/api-workflow/impl-json.md) · [case management](plugins/tasks/case-management/impl-json.md) · [timer](plugins/tasks/wait-for-timer/impl-json.md) · [connector activity](plugins/tasks/connector-activity/impl-json.md) · [connector trigger](plugins/tasks/connector-trigger/impl-json.md) |
| Conditions | [stage entry](plugins/conditions/stage-entry-conditions/impl-json.md) · [stage exit](plugins/conditions/stage-exit-conditions/impl-json.md) · [task entry](plugins/conditions/task-entry-conditions/impl-json.md) · [case exit](plugins/conditions/case-exit-conditions/impl-json.md) |
| SLA / logging | [SLA](plugins/sla/impl-json.md) · [logging](plugins/logging/impl-json.md) |
| Variables / bindings | [globals](plugins/variables/global-vars/impl-json.md) · [I/O](plugins/variables/io-binding/impl-json.md) · [bindings](plugins/variables/bindings/impl-json.md) |

<!-- END: case-editing-operations.md -->
