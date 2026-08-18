# Direct implementation: SDD to caseplan.json

Lower the normalized Planner SDD contract directly into Case JSON. This guide
owns ordering, batching, recovery, and the structural/detail split. Exact JSON
shapes live in `plugin-index.md` recipes.

Targeted changes to an existing case use `brownfield.md`.

## Preconditions

- `check-sdd` returned `ok: true` for the source file.
- `inspect-sdd` returned the ordered inventory used in this run.
- Tenant-bound resources have resolution evidence under `case-build/`, or the
  user explicitly accepted placeholders.
- The build-review preference is already known.
- No project artifact has been written before SDD preflight.

Do not save a second design or plan. If context is lost, run `inspect-sdd`
again.

## Write contract

Use Read + Write/Edit for artifacts. Never assemble or transform artifacts
with Python, Node, `jq`, `sed`, `awk`, redirection, `tee`, or a temporary
script. The bundled contract checker is read-only and may inspect artifacts.

Process one container at a time:

1. Read the current artifact at container entry.
2. Gather every CLI schema/spec response needed by that container.
3. Compose the complete post-container state in reasoning.
4. Apply sibling edits without re-reading between them.
5. Re-read once at the container boundary and verify nothing outside the
   container changed.

For fewer than 10 declarations, prefer one Edit per declaration. For 10 or
more, replace the complete container once. Never emit a populated Case file
larger than about 40 KB in one Write; split root/variables, structural nodes,
conditions/SLA, then connector/detail wiring.

Read each selected plugin recipe once per type. Re-read only after context
compaction or when resuming that type after a user stop.

## ID discipline

- Mint stable unique IDs inline; use subprocess UUID v4 only for fields that
  require UUIDs.
- Keep an in-memory name-to-ID map while a pass is active.
- `caseplan.json` is the source of truth after any stop or compaction.
- Human names never substitute for IDs in reference fields.
- Formal argument slot IDs are synthetic and distinct from companion variable
  names.
- Output IDs share one global namespace.

An optional `id-map.json` is a cache only. Never depend on it for correctness
or use it as a second semantic plan.

## Structural pass

### 1. Initialize one solution

Run:

```bash
uip solution init <SolutionName>
```

Skip only when that exact solution manifest already exists at the intended
working-root path. Never run `uip maestro case init`; it can create a second
solution.

### 2. Scaffold the Case project and root

Read `plugins/case/impl-json.md` to EOF. Write:

- `project.uiproj`
- `operate.json`
- `entry-points.json`
- `bindings_v2.json`
- `package-descriptor.json`
- root `caseplan.json`

Then register the project with absolute paths:

```bash
uip solution projects add <absolute-project-dir> <absolute-uipx> --output json
```

Verify exactly one `.uipx` exists under the working root.

### 3. Add triggers

Process SDD `Case Triggers` in declaration order. Read only the matching
manual/timer/event recipe. Each trigger writes one `uipath.case.trigger` node
and one `entry-points.json` entry. Record every SDD trigger label → TriggerId
mapping for argument `elementId` resolution.

An unresolved event trigger retains the canonical placeholder shape and an
entry point. It creates no edge.

### 4. Add variables and arguments

Read `plugins/variables/global-vars/impl-json.md` to EOF. Lower every Case
Variables row exactly:

- `Variable` → state companion in `variables.inputOutputs`
- `In` → formal input plus companion; bind `elementId` to its declared trigger
  or the primary trigger when blank
- `Out` → formal output plus companion and producer contract

Preserve type, explicit default, JSON schema, source trigger, and trigger
field semantics. Never silently coerce an object literal into an expression.

After all arguments exist, synchronize `entry-points.json` using
`entry-points-sync.md`.

### 5. Add stages

Read `plugins/stages/impl-json.md` to EOF. Lower stages in SDD order:

- primary → `case-management:Stage`, `data.stageType: primary`
- secondary → the same node type, `data.stageType: secondary`
- preserve `isRequired`, description, and interrupting semantics
- do not emit node layout fields

Record stage name → StageId.

### 6. Add task shapes and grouping

Gather non-connector schemas with one `tasks describe` call per distinct
`(type, entityKey)`; always request JSON. Connector specs wait for the detail
pass. Inline-created sibling resources use their on-disk entry-point contract.

Read the matching task recipe once per type, then lower tasks in stage order.
Preserve the SDD task envelope and entry behavior.

Task-set grouping is semantic:

- Sequential chain: consecutive single-task sets `[[A], [B], [C]]`; each task
  carries `runs-sequentially`.
- Parallel stage-start work: one shared set `[[A, B]]`; each carries
  `current-stage-entered`.
- Parallel after predecessor: shared next set `[[A], [B, C], [D]]`; siblings
  carry `runs-sequentially`.
- Adhoc, event-driven, fan-in, or conditional task: its own set with the SDD
  entry rule.

Never infer parallelism from missing data bindings. `uip validate` cannot
detect incorrect grouping.

For non-connector tasks, write full input/output schema with input values empty
until the detail pass. For connector tasks, write the structural identity stub
only. For an accepted unresolved resource, write the canonical placeholder
from `placeholder-tasks.md`; keep its TaskId usable by conditions.

### 7. Add SLA and escalations

Read `plugins/sla/impl-json.md` to EOF. Create target SLA objects before
conditions so `sla-status-change` can resolve emitted IDs. Preserve target,
title, duration, expression order, at-risk percentage, recipients, response,
and rationale. A breach does not carry an escalation ID; an at-risk response
does.

### 8. Add conditions

Read the recipe matching each of the four scopes. Resolve display-name
selectors through the current ID maps and preserve:

- rule type and arguments
- `marksStageComplete` / `marksCaseComplete`
- exit type
- interrupting behavior
- expression
- display name

The first primary stage enters on `case-entered`. Every primary stage must be
reachable. Secondary lanes remain optional and are not counted in the happy
path's required-stage set. Stage completion and case completion are separate.

Connector-bound rules use the canonical structural stub until the detail pass.

### 9. Structural preview

Run one structural validate. Prefer `--skeleton-v2`; fall back to `--skeleton`
only when the CLI explicitly rejects the v2 flag as unsupported. A genuine
validation failure is not a compatibility signal.

Print stage/task/condition/SLA counts. Continue immediately for
straight-through mode. For preview mode, use the publish-for-review branch in
`phased-execution.md`.

## Detail pass

### 10. Rebuild identity maps

Re-read `caseplan.json` and map:

- stage label → StageId
- trigger → TriggerId
- `(stage label, task displayName)` → TaskId
- variable name → companion/formal IDs
- SLA/escalation title per target → ID
- every condition/rule ID

Do not trust a pre-preview in-memory map.

### 11. Complete connector shapes

For every resolved connector activity/event/rule:

1. Build `--input-details` directly from the SDD input table.
2. Run `uip maestro case spec ... --output json` once per distinct spec tuple.
3. Reject missing required fields before editing.
4. Splice returned `caseShape.context` without renaming keys.
5. Mint input/output/binding IDs and substitute only documented placeholders.
6. Append Connection/Folder root bindings.
7. Synchronize the connection cache/sidecars.

Do not degrade a selected connector to a `typeId` + `connectionId`-only shape.

### 12. Bind task inputs and outputs

Read `plugins/variables/io-binding/impl-json.md` to EOF. For every SDD input
row, preserve the binding mode and value:

- literal remains literal
- JSON object remains a native object or the schema-required encoded string
- `=vars.X` resolves to the declared companion ID
- whole-value task output references resolve through the source output `.id`
- custom `=` outputs resolve through their verified root companion
- embedded task references use `$xref` until every output ID is final

For every output row, preserve `->` versus `=` and both operands. Equal-name
`greeting -> greeting` is not equivalent to a schema-discovered bare output.

### 13. Resolve embedded references and connector rules

After all outputs exist, replace every
`vars.$xref('Stage','Task','output')` with the source output reference ID.
Unresolved triples are blocking.

Upgrade each resolved connector-bound rule by replacing only `rule.uipath`.
Preserve IDs, expressions, scope, and placement. Accepted unresolved rules
retain their stub and are reported.

### 14. Synchronize sidecars

Regenerate `bindings_v2.json` from authoritative Case bindings and re-run
entry-point synchronization. Never publish or debug with stale sidecars.

## Verification handoff

Read `verification.md` and run its gates. Do not put validation logic back into
this procedural guide; deterministic rules belong in the checker whenever
they can be enforced mechanically.

## Recovery

On interruption:

1. Re-run `inspect-sdd` for the source inventory.
2. Re-read Case JSON and sidecars.
3. Run `check-caseplan` and `check-parity`.
4. Resume at the first missing or mismatched declaration.

Never reconstruct progress from chat narration or an intermediate Markdown
plan.

<!-- END: implementation.md -->
