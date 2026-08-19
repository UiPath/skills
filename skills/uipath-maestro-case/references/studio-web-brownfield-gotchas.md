# Studio Web Brownfield Gotchas — field notes from editing server round-tripped cases

Everything below was hit (and verified) while brownfield-editing a large production
case (`solution download` → JSON edits → `solution upload`) that lives primarily in
the Studio Web designer. These behaviors are invisible in greenfield builds and are
not covered by the plugin docs. Symptoms are listed first so this file is greppable.

Scope: designer/runtime behaviors of Case Management itself — durable semantics, not
tool bugs. The one CLI-sensitive note (§1,
validate/debug format ceiling) should be re-verified after each CLI upgrade and
deleted once the local transform accepts the server format.

## 1. Server file format is NOT the skill's authored format

A case that has been saved by the Studio Web designer round-trips at a **newer
schema version than the skill's authored format**, with:

- **plural** `selectedStageIds: ["Stage_x"]` / `selectedTasksIds` on rules (the
  authored format uses singular `selectedStageId`),
- a **populated** top-level `edges: []` array plus `edgeIds: []` on entry conditions,
- a **populated** top-level `layout` block.

When editing such a file, **preserve all three**. Stripping edges/edgeIds/layout (or
flipping plural keys to singular) uploads fine — but the designer canvas silently
loses its stage connectors and never re-derives them. Rule 20's "edges retired"
applies to *authoring new cases*, not to round-tripped files.

**Layout is all-or-nothing.** When `layout` is non-empty, EVERY node (stages, tasks,
triggers) needs a `layout.nodes` entry. Adding a new stage/task without one crashes
the canvas with `Cannot read properties of undefined (reading 'x')`. Either add
entries for every new node, or empty the whole block.

**CLI incompatibility (re-check after each CLI upgrade — delete this note once
the local transform accepts the server format).** `uip maestro case validate` /
`debug` can reject the server's own round-trip format ("JSON is not a valid Case
Management JSON of any previous version") when the designer's schema version is
newer than the CLI's local migration ceiling. To run them against a round-tripped
case, transiently downgrade a COPY to the authored format: lower the top-level
`version` until the transform accepts it, flip `selectedStageIds` →
`selectedStageId` (single string), drop `edgeIds`, set `edges: []` — and never
upload that copy's format back over the designer's.

## 2. Task display names reject `:` and `.`

The designer refuses to save a case whose task `displayName` contains a colon or a
period (e.g. `TODO: fix` or `v1.2 refresh`). Use bracketed markers (`[TODO] fix`)
instead. The CLI does not validate this, so it surfaces only at designer save time.

## 3. `caseplan.json.bpmn` is the runtime artifact — and sometimes the only fix site

The compiled sidecar next to `caseplan.json` is what actually executes. Facts that
matter when patching it:

- The raw model is **distributed per element**; there is no single blob. Task
  envelopes are duplicated inside the compiled stage node's `data.tasks` with
  *different key order* than caseplan (whole-string replacement of a caseplan
  fragment will not match).
- Connector task `configuration` is an **escaped string** in `caseplan.json` but an
  **object** in the bpmn.
- Compiled condition blocks carry the expression **twice**: `"expression":
  "=js:…"` and `"expressionString": "…"` (no prefix). Patch **both**, or the
  designer shows one thing and the runtime does another.
- Structure-only changes (new stages/tasks/edges) can be made in `caseplan.json`
  alone — the next designer save compiles them. Guards/expressions anchored to
  existing fragments can be mirrored into the bpmn directly.

## 4. HITL/RPA outputs reach case variables ONLY via subprocess propagation blocks

The single most expensive gap. Task-level output bindings (`var`, `target`,
`originalVar`) are designer metadata. At runtime, a completed task's outputs reach
the parent case scope through compiled `<uipath:output>` entries in the **two event
subprocess response blocks**, keyed by the task's **display name**:

```
source="=js:vars.mainEventSubprocessResponse.taskCompletedOutputs?.[&#34;<Task Display Name>&#34;]?.[&#34;<outputName>&#34;] ?? vars.<caseVar>" var="<caseVar>"
```

(one pair per output: `mainEventSubprocessResponse` and
`tasksEventSubprocessResponse`).

Consequences:

- A HITL/RPA task added by JSON edit (without a designer rebind) has **no
  propagation entries** — its outputs silently never reach any condition, and
  stage rules reading those vars evaluate against stale/empty values.
  When resplicing a task, hand-write the propagation pairs in BOTH blocks
  (anchor: any existing `taskCompletedOutputs` entry).
- **Renaming a task's display name breaks its output propagation** — the keys are
  the display name, not the task id.
- Conditions only bind **declared root variables**; propagating into an undeclared
  name means gates read `undefined` forever. Symptom: a task visibly completes
  with the right output (job logs / Action Center), yet the gate that reads it
  never fires.
- The designer compiles these entries from the **app's actionSchema stored in the
  solution's CodedAction resource** — see §6.

## 5. Expression semantics the docs don't state

- Task **output** `=js:` expressions have **no `vars` binding** (reference throws →
  output becomes null) — EXCEPT on `action` tasks, where `vars` works (custom
  outputs like `=js:((vars.rejectionCount||0)+1)` are valid there).
- Condition/input expressions bind `vars` to **declared case variables only**;
  unknown names are `undefined` (no throw). `=vars.<id>` also resolves task-output
  ids, not just root variables.
- Boolean case variables default to `""`, not `false` — gates are effectively
  tri-state; write `=== true` / `!== true` rather than truthiness.
- `selected-stage-exited` fires only on `marksStageComplete: false` exits;
  a completing exit fires `selected-stage-completed`. Tasks do NOT re-run within a
  single stage entry — loops require leaving and re-entering the stage, with
  mutually exclusive exits and gated re-entries to avoid dual-fire.

## 6. Designer save round-trip behaviors

- Saves **re-mint element ids** and can duplicate binding definitions (dedupe by
  id when re-editing).
- Saves add `parentElement` refs that **share the stage's id** — scope any
  find-by-id walk to `d['nodes']` or you will mutate the wrong object.
- Saves have been observed to **blank Data Fabric task inputs** — re-verify DF
  tasks after a save.
- A task's `description` is a **top-level envelope field**, not under `data`.
- The designer regenerates task input/output bindings from the **actionSchema in
  the solution's CodedAction resource file**. If an app was scaffolded by copying
  another app and its `action-schema.json` was never rewritten, a designer save
  quietly rewrites the task's I/O to the donor app's schema. Always keep
  `action-schema.json` in sync with the app's real interface, and check the
  resource file after publishing a new app version.
