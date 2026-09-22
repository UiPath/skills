# Flow → BPMN eval porting brief

How a coder-eval task is ported from `tests/tasks/uipath-maestro-flow/` to `tests/tasks/uipath-maestro-bpmn/`: one task at a time, one Flow source per port.

Companion documents in this directory:

- [BATCH1-ADDENDUM.md](BATCH1-ADDENDUM.md) — Integration Service connector ports. Where it disagrees with this brief, it wins.
- [NORMALIZATION.md](NORMALIZATION.md) — the pass that brings an existing port back to Flow's graded surface.

## Faithfulness contract

Same scenario, same graded behaviours, same weights, same tier tags. Only the artifact and its vocabulary change.

| Keep identical | May change | Never |
|---|---|---|
| Prompt scenario and wording (swap "Flow" → "Maestro BPMN process", "flow file" → ".bpmn"; drop Flow node names like "Script node", let the BPMN skill pick constructs) | File format: `.flow` JSON → `.bpmn` XML | Drop a graded behaviour because BPMN makes it awkward |
| Inputs, outputs, connection names, channel names, seeded values | CLI verbs: `flow validate` → `bpmn validate` | Weaken a criterion to make it pass |
| Headless preamble paragraph, verbatim | Grader implementation (JSON walk → XML walk via `_shared` helpers) | Add BPMN-only requirements the Flow prompt did not have (e.g. "include package metadata"), unless the BPMN skill requires them for `validate` to pass |
| Criterion weights, `pass_threshold`, tier (`smoke`/`integration`/`e2e`), `mode:*`, `lifecycle:*`, `shape:*`, `connector`, connector-key tags | (nothing: `run_limits` are Flow's verbatim) | Downgrade a live Flow eval to authoring-only silently |
| Project name | Tag `ipe` → drop (Flow-only); add nothing | Hand-invent connection IDs, folder keys, connector resource keys in prompt or grader |

If the port needs a construct BPMN lacks, STOP and report it as "parked: <reason>" instead of bending the test.

## Construct translation

| Flow | BPMN |
|---|---|
| Manual trigger | `bpmn:startEvent` (no event definition) |
| Script node | `bpmn:scriptTask` with registry `BPMN.ScriptTask` payload |
| Decision / Switch | `bpmn:exclusiveGateway`, `conditionExpression` per non-default flow, exactly one `default` |
| Merge (parallel sync) / fork | `bpmn:parallelGateway` |
| Delay | intermediate `timerEventDefinition` |
| Scheduled trigger | `startEvent` + `timerEventDefinition` |
| Subflow | `bpmn:subProcess` |
| Terminate | `endEvent` + `terminateEventDefinition` |
| Connector activity (`uipath.connector.<key>.<op>`) | `bpmn:sendTask` + `<uipath:activity type="Intsvc.ActivityExecution">` enriched via `uip maestro bpmn registry get Intsvc.ActivityExecution --connection-id <id> --object-name <object>`; connection via `=bindings.<id>` + process-level `<uipath:bindings>` (`resource="Connection" propertyAttribute="ConnectionId" resourceKey=default=<connection-id>`) |
| Connector trigger | `bpmn:startEvent` + `Intsvc.EventTrigger` (context `connectionId`) |
| Wait-for-event | `bpmn:receiveTask` + `Intsvc.WaitForEvent` |
| Managed HTTP | `bpmn:sendTask` + `Intsvc.HttpExecution` |
| HITL | `bpmn:userTask` + `Actions.HITL` |
| RPA / agent / API workflow | `bpmn:serviceTask` + `Orchestrator.StartJob` / `StartAgentJob` / `ExecuteApiWorkflow` |
| Loop | `multiInstanceLoopCharacteristics` |
| Inline agent | none — park unless a published agent substitute is acceptable AND stated in the description |
| Data binding `$vars.<node>.output.<f>` | `=vars.<VarId>` read from a declared `<uipath:variables>` entry that the producing task's `<uipath:output>` writes |

Authoritative BPMN contracts: `skills/uipath-maestro-bpmn/SKILL.md`, `references/registry-workflow.md` (§3 connector enrichment, §4 bindings), `references/structural-bpmn.md`. Read them before authoring the prompt or grader; the grader must use the element names and `type=` tokens the skill actually teaches when translating a Flow assertion.


## Grading contract (mandatory — ports are born normalized)

Every assertion in the grader you write must be one of:
- **F** — a translation of a specific Flow assertion (cite `F: <script>:<line>` or `F: criterion <n>`).
- **I** — artifact plumbing: locate/parse the `.bpmn`, parse a body CDATA as JSON when Flow read `bodyParameters`, clean `FAIL:` on those.
- **T** — a listed translation tolerance: curated OR generic entity-CRUD classification; inputs at any depth; entity anywhere in inputs/objectName/path; `=`-expressions pass type checks; GETBYID/GET equivalence; ORDER BY in query text; transitive variable derivation through `BPMN.Variables` copy tasks; `vars.<VarId>` in place of Flow node-id references.

If you cannot tag an assertion F, I or T, do not write it. In particular never add: `require_no_private_connector_values`, `require_sequence_integrity`, `require_di_for_visible_elements`, connection-binding checks, `graph.reaches` ordering (unless Flow asserted order), uniqueness/"exactly one" rules, single-body hard fails, output-presence requirements. Put the map at the top of the module docstring:

```
Assertion map (Flow → BPMN):
  F check_x.py:41   entityName == ENTITY        → entity_ok(node)
  F criterion 3     flow_contains 'a' 'b'       → one classified node per op
  I                 locate/parse .bpmn          → parse_bpmn()
  T                 curated|generic form        → is_kind()
```

YAML rules, fixed: run_limits = Flow's verbatim (no raises, no added `expected_turns`); tags = Flow's with `uipath-maestro-flow`→`uipath-maestro-bpmn` and `ipe` removed, nothing added; project name only if Flow names one, else `parse_bpmn()` with no hint; description = Flow's text + one "Ported from Flow `<path>`; <what changed>." sentence; every structural port ends its prompt, before the headless preamble, with exactly `Do NOT upload, publish, deploy, debug, or run the process. Do not pause for approval, confirmation, or feedback.`; criteria one-for-one with Flow (type, order, weight, pass_threshold, timeout); Test Manager `skip: true` is not carried over.

## Grader translation

Flow graders live in `tests/tasks/uipath-maestro-flow/**/check_*.py` and `_shared/flow_check.py` / `flow_contains.py`. BPMN equivalents:

| Flow | BPMN |
|---|---|
| `flow_contains.py --flow-name X 'a' 'b'` | `file_contains` criterion, or `run_command` over XML |
| `glob **/Name*.flow`, `json.loads` | `_shared/bpmn_check.py`: `parse_bpmn(name_hint)`, `resolve_project(name)`, `elements(root, "sendTask")`, `attr`, `text_content`, `has_typed_uipath_extension` (never the `require_*` structural helpers — see Grading contract) |
| node-id reference between nodes (data binding) | variable-flow check (use `_shared/graph.reaches` only if Flow asserted order): producer `<uipath:output ... var/target=V>` and consumer input text contains `=vars.V` |
| `_shared/validate_flow.py` | `run_command`: `uip maestro bpmn validate <path> --output json` (see how `e2e/customer_escalation_triage` does it), or `command_executed` on `(uip|\$UIP)\s+maestro\s+bpmn\s+validate` mirroring Flow's `command_executed` on `flow validate` |
| `check_connection_available.py <key>` preflight | copy the pattern; `uip is connections list <key> --output json` is connector-agnostic |
| `flow_check.run_debug` | `_shared/bpmn_live.run_debug` (live tier only — not for this batch) |

Grader files go in `tests/tasks/uipath-maestro-bpmn/_shared/check_<task>.py` and are called as `python3 $REFERENCE_DIR/_shared/check_<task>.py` with `reference: { directory: ../.. }` (depth-relative to the task YAML — count `..` so it resolves to `tests/tasks/uipath-maestro-bpmn`). This is main's convention: every BPMN task reaches its grader through `$REFERENCE_DIR`; the retired host-path variables are blocked by the task host-path gate. Exemplars: `single_node/http_weather/http_weather.yaml` + `_shared/check_http_weather.py`; `hitl/quality_boolean_decision/` + `_shared/check_quality_boolean_decision.py` (a completed port of Flow `hitl/quality_03_boolean_decision.yaml` — diff the pair to see the translation in practice).

## Task YAML skeleton

- Path: mirror the Flow path, leaf dir per task: `tests/tasks/uipath-maestro-bpmn/<flow group>/<name>/<name>.yaml`.
- `task_id: skill-bpmn-<slug>` (Flow's `skill-flow-<slug>` with the prefix swapped; drop `ipe-`).
- `description`: Flow's description + one sentence "Ported from Flow `<relative path>`; <what changed and why>."
- `tags`: `uipath-maestro-bpmn` first, then Flow's tags minus `uipath-maestro-flow`/`ipe`, plus `"mode:build"` if Flow lacked it. Quote tags containing `:` the way BPMN neighbours do.
- `sandbox.template_sources`: `- type: template_dir` / `path: ../../../../../skills/uipath-maestro-bpmn` (adjust `..` count to depth).
- `reference: { directory: ../.. }` (adjust to depth).
- `initial_prompt`: Flow's prompt, translated per the contract, ending with the headless preamble verbatim. Add the BPMN suite's standard closing line only if Flow's prompt had an equivalent ("Do NOT upload, publish, deploy, debug..." maps from Flow's validate-only intent).
- `success_criteria`: one-for-one with Flow's, same order, same weights.

## Gates

Run from the repository root:

```bash
tests/.venv/bin/python -m pytest tests/tasks/uipath-maestro-bpmn/_shared -q -x     # budget guard + helper tests
tests/.venv/bin/python -c "import yaml,sys; yaml.safe_load(open(sys.argv[1]))" <task yaml>
python3 <grader> ; echo "exit=$?"    # must fail cleanly (no BPMN present) with a FAIL: message, not a traceback
```

Also self-lint against `.claude/commands/lint-task.md` and fix anything Critical/High. Do NOT add `@uipath/cli` to `env_packages`. Do NOT gate on `--output json`.
