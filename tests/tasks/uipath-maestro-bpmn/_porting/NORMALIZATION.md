# Normalization pass — bring every BPMN port back to Flow's graded surface

Goal: a BPMN port grades exactly what its Flow source grades, translated to the `.bpmn` artifact, and nothing more. Ports are produced per [PORTING-BRIEF.md](PORTING-BRIEF.md); connector ports also follow [BATCH1-ADDENDUM.md](BATCH1-ADDENDUM.md).

## Grader rule (the important one)

Every assertion in a BPMN grader must trace to ONE of:

- **(F) a Flow assertion** — a check in the Flow grader script(s) the task's criteria call, or a Flow criterion (`file_contains`, `flow_contains.py` args, `command_executed` pattern). Cite it as `F: <script>:<line>` or `F: criterion <n>`.
- **(I) artifact-intrinsic plumbing** — locating the `.bpmn` (`parse_bpmn`, project.uiproj rule), parsing XML, parsing a `target="body"` CDATA as JSON when Flow read `bodyParameters`, and reporting a clean `FAIL:` when those fail. Nothing else is intrinsic.
- **(T) a translation tolerance** that makes a Flow assertion expressible in BPMN without being stricter: curated OR generic entity-CRUD node classification; inputs at any depth; entity name anywhere in the node's inputs/objectName/path; expression strings (`=…`) passing type checks; GETBYID/GET equivalence; ORDER BY in query text; transitive variable derivation through `BPMN.Variables` copy tasks; `vars.<VarId>` references in place of Flow node-id references.

Everything else is **DROPPED**. Known offenders to remove wherever they are not traceable to F:
- `require_no_private_connector_values`, `require_sequence_integrity`, `require_di_for_visible_elements` (the `validate` criterion already covers structure; Flow graders never checked this)
- connection-binding checks (`=bindings.<id>` resolves to a declared `resource="Connection"` binding) — Flow graders never checked connections
- sequence-flow ordering / `graph.reaches` checks where Flow only checked a data reference (node id or `$vars`) — keep `reaches` ONLY where Flow asserted order
- "exactly one node" / "no other start events" / "no manual start" where Flow did not assert it
- "at most one `target="body"` input" as a hard failure where Flow had no equivalent (parsing the body when Flow read `bodyParameters` is I; enforcing single-body is not)
- required `<uipath:output>` on a node where Flow did not require an output

Do not make anything stricter while you are in there, and do not remove a tolerance (T). If a Flow assertion has no BPMN equivalent, keep it dropped and list it.

Deliverable per grader: a mapping table at the top of the module docstring:

```
Assertion map (Flow → BPMN):
  F check_x.py:41  entityName == ENTITY            → entity_ok(node)
  F criterion 3    flow_contains 'a' 'b' 'c'       → one classified node per op
  I                locate/parse .bpmn               → parse_bpmn()
  T                curated|generic classification   → is_kind()
  DROPPED          require_di_for_visible_elements  (not in Flow)
```

## YAML rules (uniform across all ports)

1. **run_limits: Flow's values verbatim.** No 20% raises, no added `expected_turns` unless Flow had it. (BPMN authoring took 1–3 codex turns in CI; Flow's limits are already generous.)
2. **Closing line: every structural port ends its prompt, before the headless preamble, with exactly:**
   `Do NOT upload, publish, deploy, debug, or run the process. Do not pause for approval, confirmation, or feedback.`
   Rationale (state once here, not per task): Flow's `validate`-only intent is implicit; in BPMN `debug` uploads a solution to the tenant with no cleanup wired into these tasks, so the guard is the same scope Flow had, made explicit. This is the one deliberate uniform addition.
3. **Project name: only if Flow named one.** If Flow's prompt names no project, the BPMN prompt names none and the grader calls `parse_bpmn()` with no hint (the helper prefers the `.bpmn` beside `project.uiproj`).
4. **Tags: Flow's tags with `uipath-maestro-flow` → `uipath-maestro-bpmn` and `ipe` removed. Nothing added** (`feature:connections`, `shape:multi-node`, `feature:records`, `feature:entities` etc. go unless Flow had them). Quote tags containing `:`.
5. **Criteria:** same count, order, type, weight, `pass_threshold`, `timeout` as Flow; only the CLI verb, regex object names and grader path differ. Advisory `registry get --object-name` patterns keep curated + `_V3` + entity-name alternatives.
6. **Description:** Flow's description, then one sentence "Ported from Flow `<path>`; <what changed>." Remove other editorialising (lint-carve-out paragraphs, generic-vs-curated essays). Keep it short.
7. **skip:** Test Manager ports stay un-skipped (decided). Header comment explains in one or two lines.
8. **pre_run, template_sources, reference:** unchanged from the current port.

## Verification you must run

- The normalized grader must still PASS on every real CI artifact for its task — take the artifacts directory of a passing coder-eval run (`…/default/<task-id>/00/artifacts/`), copy it to a temp dir, and run the grader from there. Dropping assertions can only widen; if something now fails, stop and report.
- Empty dir → clean `FAIL:` exit 1.
- `tests/.venv/bin/python -m pytest tests/tasks/uipath-maestro-bpmn/_shared -q` passes (from the repository root).
- YAML parses; `python3 scripts/check-cli-verbs.py --json <yaml>` clean.
