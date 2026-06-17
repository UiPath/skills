# Maestro BPMN Validator (bundled, offline)

A dependency-light, offline semantic validator for UiPath Maestro BPMN XML. It
parses the BPMN with `bpmn-moddle` using the UiPath extension descriptor (the
same `getModdle()` + `fromXML()` pattern as PO.Frontend), reconstructs the
PO.Frontend `Node[] / Edge[] / CanvasState` model from the parse tree, and runs
**all 19** PO.Frontend validation rules plus a Maestro-original
variable-existence check and an optional connection-liveness ping.

## Usage

```bash
npm install
node validate-bpmn.mjs <bpmn-file> [resources]
```

- Prints `VALID` and exits `0` when there are no ERROR-severity findings.
- Otherwise lists every finding (rule code + message) and exits `1`.
- WARNING-severity findings are printed but do not gate.
- `resources` (optional): a numeric folder id (or comma-separated release names)
  for the connection-liveness ping via the `uip` CLI. Best-effort; a missing or
  unauthenticated CLI is reported as a NOTE, never a hard failure.

```bash
npm test   # runs all three suites below; green = no drift from the frontend
```

## Test suites (`test/`)

`npm test` runs three layers and asserts all 28 rule codes are exercised:

1. **Crafted-invalid XML coverage** (`run-tests.mjs`): for each rule, a minimal
   BPMN that should trip exactly that rule's code, plus a check that valid twins
   don't. Proves the full parse → model → rules pipeline end-to-end.
2. **Ported PO.Frontend rule tests** (`test/ported-rule-tests.mjs`): a 1:1
   translation of every `PO.Frontend/src/services/validation/bpmn/rules/*.test.ts`
   case (162 assertions). Each case carries a `// FE:` comment naming the
   originating frontend test and runs the same synthetic Node/Edge/CanvasState
   graph through **our** rule engine. This is the primary drift detector: if our
   port disagrees with a frontend test's expectation, this suite fails.
3. **Integration over real `.bpmn` files** (`test/integration.test.mjs`): every
   file in `test/fixtures/` is a real, externally-validated artifact (backend
   BpmnParser/Worker/Athena/V2-E2E TestData, and PO.Frontend editor mocks),
   bundled so the suite is self-contained in CI. `fixtures/known-good/` must
   produce **zero** ERROR-severity findings; `fixtures/expected-findings/` assert
   the exact ERROR codes the frontend would also raise (each verified by reading
   the file). Set `MAESTRO_BPMN_TESTDATA` / `MAESTRO_BPMN_FRONTEND_MOCKS` to also
   sweep a live corpus during development.

## Drift log (hand-port vs. PO.Frontend source of truth)

Surfaced by running the frontend's own test inputs and real `.bpmn` corpora
through this port. Each was either **fixed to match the frontend** or
**justified and documented**.

1. **Empty `<conditionExpression/>` crash — FIXED.** Legacy `model:`-namespace
   files (and any empty condition element) parse to a moddle object with no
   `.body`; `model.mjs` fell back to the moddle object itself, crashing the
   string-based rules (`expression.startsWith is not a function`). Now an empty
   condition element is treated as "no condition" (frontend behavior).
2. **`FakeJoinRule` over-firing — FIXED (match frontend behavior).** The frontend
   rule matches only the **literal** abstract types `"bpmn:Activity"` /
   `"bpmn:Event"`. On the real canvas every node carries its **concrete** `$type`
   (`bpmn:Task`, `bpmn:EndEvent`, …; `bpmn-from-xml.ts` sets `type: $type`), so
   the rule is **dormant on exported BPMN** — its own source has a `TODO` noting
   it must be rewritten to walk the inherited-type chain. An earlier hand-port
   fired `FAKE_JOIN` on concrete activities/events, producing false positives on
   many valid real files. The port now applies the frontend's exact predicate, so
   it is faithful (same inputs → same outputs). The rule's logic is proven in the
   ported suite (which feeds literal abstract types, like the frontend test); it
   is intentionally not triggerable via real XML.
3. **`validateRequiredFields(null)` crash — FIXED.** The frontend rule guards
   `if (!nodes || !edges) return []`; the port now guards null inputs too.
4. **`VARIABLE_DOES_NOT_EXIST` false positives on node-output variables — FIXED.**
   A node's `<uipath:output var="x">` **declares** variable `x` (frontend
   `mapNodeOutputsToVariables`: `id: v.var`), available to downstream nodes/edges.
   `collectKnownVariableIds` only gathered declared `uipath:variables` blocks, so
   a gateway condition reading a variable written by an upstream script/task
   output false-positived. Now node outputs' `var`/`name`/`canonicalId` are
   included in the known-id set. Also fixed: script-task IO lives under
   `uipath:Mapping` (same shape as `uipath:Activity`/`Event`), which the model now
   recognizes.

### Justified, intentional divergences (documented, not bugs)

- **`FAKE_JOIN` dormant on real BPMN** (see #2): faithful to the frontend, which
  cannot fire it on concrete-typed canvas nodes.
- **`RequiredFields` is a conservative subset** offline (see the parity note
  below): flags present-but-empty required fields, not absent ones.
- **`VARIABLE_DOES_NOT_EXIST` is the existence half** of the frontend's variable
  validation. The frontend additionally emits a *separate* `VARIABLE_NOT_SET`
  WARNING for variables that exist but aren't reachable in flow order; this port
  intentionally implements only the existence check (declared/produced anywhere),
  which is why some backend parser fixtures with genuinely dangling `vars.*`
  references are listed as expected-findings — the frontend would flag them too.

## Architecture (Phase 1 → Phase 2)

| File | Role |
| --- | --- |
| `rules.mjs` | **Self-contained rule engine** — the swap target. In Phase 2 this single module is replaced by the published npm package with no behavior change. |
| `model.mjs` | Integration glue: reconstructs the frontend model from the moddle tree; bundles registry metadata. |
| `validate-bpmn.mjs` | CLI entry: parse → build model → run rules → gate. |
| `bpmn-spec.json` | Bundled maestro-sdk registry, consumed offline for RequiredFields. |
| `uipath-moddle.v1.json` | Verbatim UiPath moddle descriptor from PO.Frontend. |

## 19-rule coverage

Each rule is a faithful port of the PO.Frontend rule of the same name. Source
column shows where the rule's truth comes from offline.

| # | Rule (PO.Frontend) | Source | Codes emitted |
| --- | --- | --- | --- |
| 1 | ConditionalFlow | XML graph | `MISSING_CONDITION_EXPRESSION` |
| 2 | Connection | XML graph | `INVALID_CONNECTION`, `INVALID_CONNECTION_TYPE` |
| 3 | DuplicateErrorEventSubprocess | XML graph + `bpmn:Error` objects | `MULTIPLE_CATCH_ALL_ERROR_EVENT_SUBPROCESS`, `DUPLICATE_ERROR_EVENT_SUBPROCESS` |
| 4 | EmptyStartEventDefinitionInSubProcess | XML graph | `START_EVENT_WITH_DEFINITION_IN_SUBPROCESS`, `START_EVENT_WITHOUT_DEFINITION_IN_EVENT_SUBPROCESS`, `INVALID_EVENT_DEFINITION_IN_EVENT_SUBPROCESS` |
| 5 | ErrorBoundaryEvent | XML graph + `bpmn:Error` objects | `ERROR_BOUNDARY_EVENT_EMPTY_ERROR_REF`, `ERROR_BOUNDARY_EVENT_REQUIRES_ERROR_CODE`, `MULTIPLE_CATCH_ALL_BOUNDARY_EVENTS_ON_TASK`, `DUPLICATE_ERROR_BOUNDARY_EVENT_ON_TASK` |
| 6 | ErrorEndEvent | XML graph | `ERROR_END_EVENT_MISSING_EXCEPTION` |
| 7 | FakeJoin | XML graph | `FAKE_JOIN` |
| 8 | MessageFlowObjectsPool | XML graph (pools) | `SAME_POOL_MESSAGE_FLOW` |
| 9 | MissingResource | XML extension (`serviceType` + bindings) | `MISSING_RESOURCE` (WARNING) |
| 10 | MissingRootVariable | XML extension (variables + outputs) | `MISSING_ROOT_VARIABLE` (WARNING) |
| 11 | NoAssignments | Pure check on expressions | `ASSIGNMENT_NOT_ALLOWED` (WARNING) |
| 12 | RequiredFields | **Registry metadata** (`bpmn-spec.json`) | `EMPTY_REQUIRED_FIELD` |
| 13 | SequenceFlowPoolCrossing | XML graph (pools) | `CROSSING_POOL_BOUNDARY` |
| 14 | SequenceFlowSubProcessCrossing | XML graph | `CROSSING_SUBPROCESS_BOUNDARY` |
| 15 | SingleBlankStartEvent | XML graph | `MULTIPLE_BLANK_START_EVENTS` |
| 16 | SingleStartEventInEventSubProcess | XML graph | `MULTIPLE_START_EVENTS_IN_EVENT_SUBPROCESS` |
| 17 | SuperfluousGateway | XML graph | `SUPERFLUOUS_GATEWAY` |
| 18 | TaskTimer | Pure check (range) | `TASK_TIMER_OUT_OF_RANGE` (WARNING) |
| 19 | TimerDuration | Pure check (ISO 8601) | `TIMER_DURATION_INVALID`, `TIMER_DURATION_WEEK_UNSUPPORTED` (WARNING) |
| + | Variable existence (Maestro-original) | XML extension + declared variables | `VARIABLE_DOES_NOT_EXIST` |

## RequiredFields parity note (honest scope)

The PO.Frontend `RequiredFields` rule fires when `field.required && isNilOrEmpty(field.value)`.
On the canvas, `field.required` is attached to each *live* node field by
actions-service-enriched node data, where the field name already matches.

Offline we recover `required` from the bundled registry (`bpmn-spec.json`), but
the registry's required-field **names** are canonical designer names that do
**not** always match the names a field is serialized under in exported BPMN
(e.g. registry `url` vs serialized `path`; registry `name` vs serialized
`messageName`). The registry also does not carry a name-alias map.

Therefore this port flags a required field only when a serialized field whose
name matches a registry-required name is **present but empty** — the genuine
"user left a required field blank" case, and a true subset of the canvas
behavior. Required fields that are entirely **absent** from the serialized data
are not flagged, because offline their absence is ambiguous (bound elsewhere,
serialized under a different canonical name, or supplied by design-time
enrichment that exported BPMN does not carry). This is the one rule that cannot
reach full byte-for-byte parity offline; it is intentionally conservative to
avoid false positives on valid processes.
