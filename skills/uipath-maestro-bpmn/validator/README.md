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
npm test   # rule-coverage harness: asserts every rule fires on a crafted invalid
```

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
