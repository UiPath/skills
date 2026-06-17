# Maestro BPMN Validator (bundled, offline)

A dependency-light, offline semantic validator for UiPath Maestro BPMN XML. It
parses the BPMN with `bpmn-moddle` using the UiPath extension descriptor (the
same `getModdle()` + `fromXML()` pattern as PO.Frontend), reconstructs the
PO.Frontend `Node[] / Edge[] / CanvasState` model from the parse tree, and runs
**all 19** PO.Frontend validation rules plus the variable-validation checks
(`VARIABLE_DOES_NOT_EXIST`, including element-local `result.X`, and the
flow-order `VARIABLE_NOT_SET` warning) and an optional connection-liveness ping.

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

`npm test` runs three layers and asserts all 29 rule codes are exercised:

1. **Crafted-invalid XML coverage** (`run-tests.mjs`): for each rule, a minimal
   BPMN that should trip exactly that rule's code, plus a check that valid twins
   don't. Proves the full parse → model → rules pipeline end-to-end.
2. **Ported PO.Frontend rule tests** (`test/ported-rule-tests.mjs`): a 1:1
   translation of every `PO.Frontend/src/services/validation/bpmn/rules/*.test.ts`
   case plus the variable-validation cases from `VariableUtil.test.ts`
   (173 assertions). Each case carries a `// FE:` comment naming the
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

## Parity status

**Full parity with the PO.Frontend rule engine is now reached for every rule
except two clearly-bounded residuals (below).** Each rule is a faithful port of
the frontend rule of the same name: same inputs → same outputs, verified by the
1:1 ported test suite (frontend test inputs) and the real-`.bpmn` integration
corpus (zero ERROR findings on 31 known-good files; exact ERROR-code match on 28
expected-findings files).

### Closed gaps (now at parity)

1. **`RequiredFields` flags ABSENT required fields, not only present-but-empty.**
   Frontend `RequiredFieldsRule.ts:24-27` + `ValidateRequiredFieldsInData.ts:15-16`
   fire on `field.required && isNilOrEmpty(field.value)`. On canvas every field a
   serviceType declares is present in node data, so an *unbound* required field is
   present-with-empty-value. In exported BPMN that field is simply absent. The
   model (`model.mjs`) attaches the serviceType's full registry required-field name
   set (`bpmn-spec.json`, 128 `required` entries) as `uipath.requiredFieldNames`,
   and the rule now treats an absent required name exactly as the frontend treats
   an unbound field. Present-but-empty still fires too, in the frontend's
   context → inputs → outputs order, one finding per node.
2. **`VARIABLE_NOT_SET` (WARNING) is now implemented.** Port of the flow-order
   reachability half of `VariableUtil.validateVariablesInExpression`
   (`VariableUtil.ts:758-866`), built on the pure topology helpers
   `getSourceEdgeMappings` (`:121-130`), `mapNodeOutputsToVariables` (`:539-579`),
   `getVariablesForSubProcess` (`:495-525`), `getAvailableVariablesFromSourceNodes`
   (`:303-389`, backward BFS over sequence-flow edges + boundary re-parenting +
   subprocess scope), and `getAvailableVariablesForElement` (`:401-481`, parent
   chain + event-subprocess shared scope + subprocess EndEvent exposure). A
   *declared* variable referenced where no flow path reaches its producer fires
   `VARIABLE_NOT_SET` (WARNING, non-gating). **Skipped entirely for Case
   Management** (`VariableUtil.ts:826-828`). Root variables are globally available
   and never warn.
3. **`result.X` existence is now validated element-locally.** Frontend puts an
   unresolved `result.X` in the non-existing set (`VariableUtil.ts:263`) and a
   `result.X` is valid only if `X` names one of the *referencing element's own*
   outputs (`isResultVariableValidForElement`, `:166-178`). The port previously
   skipped all `result.` refs unconditionally; it now resolves `result.X` against
   the element's own output identifiers and fires `VARIABLE_DOES_NOT_EXIST` for an
   invalid one (edge conditions have no own outputs, so every `result.X` on an
   edge is invalid, matching the frontend).
4. **`ConnectionRule` unknown-type fallback now returns `false`.** Frontend
   `canNodeTypesBeConnected` (`BPMNTypesUtils.ts:51-82`) returns **false** when no
   rule matches the source type, yielding `INVALID_CONNECTION_TYPE` (WARNING). The
   port previously returned `true` for unknown source types; it now matches the
   frontend. The abstract-type inheritance the frontend additionally walks is
   already folded into our concrete allow-map (every concrete activity/event type
   has an explicit entry), so an unknown source type genuinely has no rule. The
   ported `ConnectionRule` test was un-doctored to the frontend's actual input
   (source `"output"` → target `"input"`, both unknown) per `ConnectionRule.test.ts:33-43`.
5. **Custom-output accessor gating aligned to the frontend.** Both the existence
   check and `VARIABLE_NOT_SET` now collect a custom output's `source` only when
   `getAccessorFromType(type) === "source"`, and `body` only when the accessor is
   `body` (`VariableUtil.ts:952-968`).

### Earlier fixes (already at parity before this round)

6. **Empty `<conditionExpression/>` crash — FIXED.** An empty condition element
   parses to a moddle object with no `.body`; the model now treats it as "no
   condition" (frontend behavior) instead of crashing the string-based rules.
7. **`FakeJoinRule` over-firing — FIXED (match frontend behavior).** See the
   residual note below.
8. **`validateRequiredFields(null)` crash — FIXED.** Matches the frontend's
   `if (!nodes || !edges) return []` guard.
9. **`VARIABLE_DOES_NOT_EXIST` false positives on node-output variables — FIXED.**
   A node's `<uipath:output var="x">` declares variable `x`
   (`mapNodeOutputsToVariables`: `id: v.var`); these are now in the known-id set,
   and script-task IO under `uipath:Mapping` is recognized.

## Genuine residuals (the only two)

These are the **only** places this port is not byte-for-byte identical to the
frontend, and both are bounded and justified — not drift.

- **Dynamic IS-connector required-ness needs `registry get` enrichment (shared
  with the frontend).** For Integration-Service connector activity types whose
  required fields are NOT in the static `bpmn-spec.json` registry — their
  required-ness only materializes after a live `registry get` enrichment — the
  model has no `requiredFieldNames`, so `RequiredFields` stays conservative
  (only present-but-empty fires; absence cannot be judged). **The frontend has
  the identical limitation:** it also needs that enrichment to learn the field is
  required. For every serviceType present in the static registry, absent-required
  detection is at full parity.
- **`FAKE_JOIN` is dormant on real/exported BPMN (faithful to the frontend).**
  The frontend `FakeJoinRule` matches only the **literal** abstract types
  `"bpmn:Activity"` / `"bpmn:Event"`, but the canvas assigns every node its
  **concrete** `$type` (`bpmn:Task`, `bpmn:EndEvent`, …; `bpmn-from-xml.ts` sets
  `type: $type`). The rule therefore never fires on exported BPMN — its own
  source carries a `TODO` admitting it must be rewritten to walk the inherited-
  type chain, which it does not yet do. The port applies the frontend's exact
  predicate, so it is faithful (same inputs → same outputs); its logic is proven
  in the ported suite (which feeds literal abstract types, like the frontend
  test) and is intentionally not triggerable via real XML.

## Architecture (Phase 1 → Phase 2)

| File | Role |
| --- | --- |
| `rules.mjs` | **Self-contained rule engine** — the swap target. In Phase 2 this single module is replaced by the published npm package with no behavior change. |
| `model.mjs` | Integration glue: reconstructs the frontend model from the moddle tree; bundles registry metadata. |
| `validate-bpmn.mjs` | CLI entry: parse → build model → run rules → gate. |
| `bpmn-spec.json` | Bundled maestro-sdk registry, consumed offline for RequiredFields. |
| `uipath-moddle.v1.json` | Verbatim UiPath moddle descriptor from PO.Frontend. |

## Rule coverage

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
| + | Variable existence (incl. element-local `result.X`) | XML extension + declared variables | `VARIABLE_DOES_NOT_EXIST` |
| + | Variable-not-set (flow-order reachability) | XML topology + declared variables | `VARIABLE_NOT_SET` (WARNING) |

## RequiredFields parity note

The PO.Frontend `RequiredFields` rule fires when `field.required && isNilOrEmpty(field.value)`
(`ValidateRequiredFieldsInData.ts:15-16`). On the canvas every field a serviceType
declares is present in node data with its `required` flag, so an *unbound*
required field is present-with-empty-value and is flagged.

Offline, `field.required` is recovered from the bundled registry
(`bpmn-spec.json`, 128 `required` entries keyed by serviceType; names are the
serialized names) and the model attaches the full required-name set as
`uipath.requiredFieldNames`. The rule fires for a required field that is either
**present-but-empty** OR entirely **absent** from the serialized data (an absent
required field is the exported-BPMN form of the canvas's unbound field), in the
frontend's context → inputs → outputs order, one finding per node. This reaches
full parity for every serviceType present in the static registry.

The single bounded exception is dynamic Integration-Service connector activity
types whose required-ness is **not** in the static registry (it only
materializes after a live `registry get` enrichment): for those,
`requiredFieldNames` is undefined and absence cannot be judged, so the rule stays
conservative (only present-but-empty fires). The frontend shares this exact
limitation — it also needs the enrichment to know the field is required. See
"Genuine residuals" above.
