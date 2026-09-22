# Batch 1 addendum — connector (Integration Service) ports

Read [PORTING-BRIEF.md](PORTING-BRIEF.md) first; this file adds the connector-specific rules learned from the passing pilot. Where the two disagree, this file wins. [NORMALIZATION.md](NORMALIZATION.md) governs re-normalizing an existing port.

## Ground truth you have (use it, do not guess)

- **A real, CI-passing BPMN the skill emitted.** What `Intsvc.ActivityExecution` nodes, bindings, variables and body/parameter inputs look like when the eval agent follows the skill is recorded in the table below; model every grader assertion on that shape. To see it end-to-end, take the `.bpmn` artifacts of a passing coder-eval run for one of the exemplar tasks listed under *Batch 2 notes*.
- **Completed pilot port**: `tests/tasks/uipath-maestro-bpmn/connector_features/drive_to_slack/drive_to_slack.yaml` + `_shared/check_drive_to_slack.py`. Copy its structure and helper usage.
- **Connector activity catalogs**: regenerate with `uip is activities list <CONNECTOR_KEY> --output json` (columns Name | DisplayName | ObjectName | MethodName | Operation) — read-only. Grade `objectName` (and `method` where object names collide) against these. For Data Service accept both the `…Curated`/`…V2` and `…_V3` spellings of an operation (Flow's node types do not distinguish them): e.g. `CreateEntityRecordCurated|CreateEntityRecord_V3`, `GetEntityRecordByIdCurated|GetEntityRecord_V3`, `QueryEntityRecordsCurated|QueryEntityRecords_V3`, `UpdateEntityRecordV2|UpdateEntityRecord_V3`, `DeleteEntityRecordCurated|DeleteEntityRecord_V3`. For Test Manager, object names collide (`TestCase` is create/get/update/delete) — distinguish by the `method` context field: POST=create, GETBYID=get one, GET=list, PATCH=update, DELETE=delete; `ExecuteTestCases` is its own object.
- Without a local Data Service connection you cannot `describe` request fields. Authoring a grader needs read-only commands only (`uip is activities list`, `uip maestro bpmn registry …`); anything that creates or seeds tenant state belongs in the task's `_setup/` scripts, run from `pre_run` (see `connector_features/datafabric_connector/_setup/ensure_entity.py`).

## Where connector node values live in BPMN (from `good.bpmn`)

| Flow (`inputs.detail.*`) | BPMN (`<uipath:activity>` inside the `bpmn:sendTask`) |
|---|---|
| node `type` = `uipath.connector.<key>.<op>` | `<uipath:type value="Intsvc.ActivityExecution">` + context `<uipath:input name="connectorKey" value="<key>">` + context `objectName` (+ `method`) |
| `pathParameters.<p>` | `<uipath:input name="<p>" target="path" value="…">` (sibling of `<uipath:context>`), OR embedded in the context `path` field |
| `queryParameters.<q>` | `<uipath:input name="<q>" target="query" value="…">` |
| `bodyParameters` | exactly ONE `<uipath:input name="body" type="json" target="body"><![CDATA[{…}]]></uipath:input>` holding the whole request JSON; values may be JSON literals or expression strings (`=vars.X`, `=js:…`) |
| output / node-id data binding | `<uipath:output name="response" … var="Var_X">` produces; a consumer's input `value`/CDATA contains `vars.Var_X` |
| connection | context `connection` = `=bindings.<id>` → process-level `<uipath:binding id="<id>" resource="Connection" propertyAttribute="ConnectionId" …>` |

Grader rule for **entity name**: pass if the entity string appears as the value of ANY `uipath:input` of that node (path/query/body) or inside its context `path` — the skill does not pin where `entityName` lands. Grader rule for **body fields**: parse the `target="body"` CDATA as JSON; a value that is a string starting with `=` is an expression and passes any type check (Flow's grader does the same for `=js:`); otherwise apply Flow's literal-shape checks unchanged. If the body CDATA is not valid JSON, fail with a clear message.

## Criterion translations for this batch

| Flow criterion | BPMN criterion (same weight, same position) |
|---|---|
| `run_command`: `for f in $(find . -name "*.flow"); do uip maestro flow validate "$f" --output json \| python3 -c '…Result==Success…' && exit 0; done; exit 1` | `run_command`: `for f in $(find . -maxdepth 6 -name "*.bpmn" -not -path "*/node_modules/*"); do uip maestro bpmn validate "$f" --output json >/dev/null 2>&1 && exit 0; done; exit 1` — `bpmn validate` exits 0 on Valid and 1 on Failure (verified). Keep Flow's `timeout`. |
| `run_command` `_shared/validate_flow.py` | same loop as above |
| `command_executed` on `flow validate` | `command_executed` on `(uip\|\$UIP)\s+maestro\s+bpmn\s+validate` |
| `command_executed` on `flow registry pull` | `command_executed` on `(uip\|\$UIP)\s+maestro\s+bpmn\s+registry\s+pull` |
| `command_executed` "Advisory: live-v1 agent added <Op> nodes" on `flow node add … uipath.connector.<key>.<op>` | `command_executed` on the BPMN authoring analog — the enriched registry call for that object: `(uip\|\$UIP)\s+maestro\s+bpmn\s+registry\s+get\s+Intsvc\.ActivityExecution\b[^\n]*--object-name\s+"?(<ObjA>\|<ObjB>)` with the object names from the catalog. Keep description prefix "Advisory:", keep weight. State in the task description that Flow's `node add` maps to `registry get --object-name`. |
| `run_command` `_shared/flow_contains.py '<key>.'` | `run_command` grader step: at least one `Intsvc.ActivityExecution` sendTask with `connectorKey == <key>` |
| `run_command` `_shared/flow_contains.py '<key>.<op1>' … '<key>.<opN>'` | `run_command` grader step: one sendTask per operation, matched on `connectorKey` + `objectName` (+ `method`) per the catalog |

## Staging and paths (BPMN tasks live one directory deeper than Flow's)

Data Fabric ports go to `tests/tasks/uipath-maestro-bpmn/connector_features/datafabric_connector/<name>/<name>.yaml`; Test Manager to `tests/tasks/uipath-maestro-bpmn/connector_features/<name>/<name>.yaml`. Graders go to `tests/tasks/uipath-maestro-bpmn/_shared/check_<name>.py` (prefix Data Fabric ones `check_df_…`). Keep each grader self-contained apart from imports of existing `_shared` modules (`bpmn_check`, `graph`); do not add new shared modules.

Setup scripts already copied into the BPMN suite (do not copy again):
- `tests/tasks/uipath-maestro-bpmn/_setup/preflight_connections.py`
- `tests/tasks/uipath-maestro-bpmn/connector_features/datafabric_connector/_setup/{ensure_entity.py, seed_flow_code_eval_records.py, flow_code_eval_entity.entity.json, contract_registry.entity.json}`

For a Data Fabric task at depth `connector_features/datafabric_connector/<name>/`:

```yaml
sandbox:
  template_sources:
    - type: template_dir
      path: ../../../../../../skills/uipath-maestro-bpmn
    - type: template_dir
      path: ../../../_setup
      mount_point: _setup
    - type: template_dir
      path: ../_setup
      mount_point: _setup
reference:
  directory: ../../..
```

For a task at depth `connector_features/<name>/`: skills path has five `..`, `reference.directory: ../..`, and `_setup` is `../../_setup`. Copy `pre_run` from the Flow task verbatim (the mounted `_setup/` names are unchanged).

## Prompt translation for this batch

- "Build this with the UiPath Data Service connector activities (`uipath.connector.uipath-uipath-dataservice.*`) … not the native `core.datafabric.*` nodes." → "Build this with the UiPath Data Service Integration Service connector (`uipath-uipath-dataservice`) activities for every entity operation." Drop the `core.datafabric.*` clause — BPMN has no native Data Fabric node, so the contrast is meaningless there. Say so in the description.
- "Build a Flow / UiPath Flow named X with a manual trigger" → "Build a UiPath Maestro BPMN process named X with a manual start".
- "The Flow is not complete until `uip maestro flow validate` passes." → "The process is not complete until `uip maestro bpmn validate` passes."
- "Data Fabric Create node", "Query Entity Records activities", "map to the flow output" → keep the activity display names (they match the catalog's DisplayName), say "process output" / "output variable" for flow output.
- Keep every literal value, count ("exactly THREE"), field list, filter condition, sort, limit, offset and entity name verbatim. Keep the headless preamble verbatim.

## Lessons from batch 1 CI (run 35488848026) — apply to every later connector port

The eval agent legitimately emits TWO forms for a connector operation, and graders must accept both:

1. **Curated activity**: `objectName` is the catalog's curated name (`QueryEntityRecordsCurated`, `TestCase`, `send_files_to_channel`…); parameters arrive as separate `target="path"` / `target="query"` inputs (e.g. `entityName`, `queryExpression`, `start`, `limit`, `sortBy`, `isAscending`, `expansionLevel`, `id`), and a structured design-time tree may sit in the context `metadata` JSON (`essentialConfiguration.savedFilterTrees.queryExpression.filters[]`).
2. **Generic object CRUD** (what the skill's discoveryNotes steer toward): `objectName` = the entity/object name itself (`FlowCodeEvalEntity`, `ContractRegistry`), `operation` ∈ Create / Retrieve / List / Update / Replace / Delete with the matching `method` (POST / GETBYID / GET / PATCH|PUT / DELETE), `path` = `/<Entity>` or `/<Entity>/{id}`, filters as a `where` query input holding a CEQL-like string, `limit` / `expansionLevel` as query inputs, `id` as a path input.

Rules:
- Classify a node by `connectorKey` AND (curated `objectName` regex OR (`objectName` == entity AND operation/method match the verb)). Never by objectName alone.
- Collect `uipath:input` elements at ANY depth under `uipath:activity` — agents sometimes nest body/query/path inputs inside `uipath:context`.
- A `target="body"` input is required only for Create/Update; query/get/delete nodes may have none. When present it must parse as JSON.
- Search filter/sort/pagination tokens across the VALUES of filter-bearing inputs only (`queryExpression`, `where`, `filter`, `filterExpression`, `query`, `metadata`), plus the structured leaves parsed out of a JSON-shaped input. Exclude input NAMES, non-filter values and `=bindings.`/`=vars.` references: each puts a free `=` in the blob and makes the operator half of an assertion unfalsifiable. Reference implementation: `_shared/check_df_smoke_query_filter.py` `node_representation()` / `FILTER_TEXT_NAMES`.
- Public outputs are often exposed through an intermediate `BPMN.Variables` copy task; follow variable derivation transitively (≤3 hops) when asserting "output maps a CRUD result".
- Advisory `registry get … --object-name` patterns must include the entity name as an alternative to the curated names.
- Prompts do not need to change: the eval agent's solutions were correct; only the graders were too narrow.

## Batch 2 notes

- **Passing exemplars now exist for both connectors** — copy them, do not re-derive: Data Fabric `connector_features/datafabric_connector/{smoke_create_all_types,integration_create_get,contractregistry_crud_filters}/` with graders `_shared/check_df_*.py`; Test Manager `connector_features/testmanager_testcase_lifecycle/` with `_shared/check_testmanager_testcase_lifecycle.py`. (`smoke_query` is `skip: true` — the curated query template has no sort field; do not copy it as an exemplar.) Import the shared node helpers from `_shared/bpmn_check.py` — `context_value`, `has_type`, `context_inputs`, `all_node_values`, `order_by`, `declared_variable_elements` — and add to that module rather than copying a helper into a new grader; two graders that read one input two ways give one artifact two verdicts. Verify a change against the `.bpmn` artifacts of a passing coder-eval run for those tasks.
- **Test Manager `skip: true` is NOT carried over** (all seven Flow TM tasks are skipped; a skipped port yields no signal). Say so in the header comment as `testmanager_testcase_lifecycle.yaml` does.
- **Flow `check_ops_present.py <Entity> <op-suffix>…`** → a grader step asserting one classified node per op (curated OR generic form).
- **Flow `_shared/check_connector_node_shape.py`** (Flow connector node shape check) → in BPMN: every connector sendTask carries `Intsvc.ActivityExecution`, a `connection` = `=bindings.<id>` backed by a declared `resource="Connection"` binding, and at most ONE `target="body"` input. Read the Flow script first and port each of its assertions that has a BPMN meaning; list the ones that do not.
- **Connector triggers** (Data Fabric Record Created / Record Updated): `bpmn:startEvent` carrying `Intsvc.EventTrigger` (context `connectionId`, not `connection`). Exemplar: BPMN `single_node/event_trigger_start/` + `_shared/check_event_trigger_start.py`. Read `references/registry-workflow.md` on event triggers before grading; a process may have several start events, one per trigger.
- File-field activities (Download/Upload/Delete File from Record Field) have curated names only — see the Data Service activity catalog (`…FieldV2` and `…Field_V3`).
