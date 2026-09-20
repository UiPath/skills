# Flow → BPMN eval porting: live-tier handoff

Branch: `test/bpmn-port-live`, stacked on `test/bpmn-port-connectors` (PR #3426, the structural bucket). This document is the state of the live-tier port work as of 2026-09-20 and how to continue it. Methodology files sit beside it in this directory.

## Context

The Flow suite (`tests/tasks/uipath-maestro-flow/`) has 131 tasks; the BPMN suite had 82. A per-task map put 62 Flow tasks in scope (`parity-ledger.md`): 29 structural (authoring + `validate`), 17 live (the Flow grader runs `flow debug`), 16 feasibility probes; 30 are Flow-only surface (IXP, evaluate, voice, conversational, bindings, native Data Fabric nodes).

Reading the Flow graders during the loop reclassified four "structural" tasks as live (their graders debug): `slack_http_fallback`, `bellevue_weather_simulated`, `cli_dice_roller_simulated`, `slack_channel_description_simulated`; and four "live" tasks as structural (their graders never debug): `smoke_error`, `jdbc_databricks_query`, `webhook_waitfor_parallel`, `testmanager_crud_grounded` (self-reported result file, as Flow). The live bucket is therefore 21 tasks.

## Live bucket status

| Task | State | Evidence |
|---|---|---|
| e2e/customer_escalation_triage | green (already on main) | pre-existing |
| e2e/jira_get_issue | green | run 35501830119 |
| e2e/jira_create_issue | green | run 35503094182 |
| e2e/escalation_jira_ticket | green | run 35503094182 |
| e2e/escalation_orchestrator_paths | green (7 debug runs) | run 35503094182 |
| e2e/escalation_slack_alert | green on iteration 2 | run 35524004307; iteration 1 the agent omitted the Slack `folderKey` binding (runtime 102010) |
| multi_node/slack_channel_description | green on iteration 2 | run 35525387843; iteration 1 the agent omitted the channel parameter |
| multi_node/bellevue_weather | parked, skill gap | runs 35523787101 + 35525387843: identical runtime fault, the script task reads `temperature_2m` off an undefined HTTP response. The skill does not teach the `Intsvc.HttpExecution` response shape well enough for downstream scripts |
| e2e/jira_search_triage | parked, skill/platform gap | run 35525387843: runtime 400008 "Failed to evaluate the input collection variable for the marker element" — `multiInstanceLoopCharacteristics` over a connector response (`=vars.Var_SearchResponse.issues`) does not evaluate |
| e2e/jira_lifecycle | parked, needs live investigation | three different runtime failures in three runs (our CLI poll cap bug; instance never terminal in 720 s; `bpmn debug` exit 1 before creating an instance). Flow's own version is flaky (0.82 typical, 2/12 zero in the week's nightlies) |
| multi_node/slack_weather_pipeline | FAIL 0.375, iteration 1 of 3 | run 35538279757: runtime 300501 "Slack channel office-bellevue was not found" in the agent's channel-select script; agent defect (channel exists, Flow finds it) |
| multi_node/billing_invoice_lookup | green on the graded criteria (0.91); bindings advisory fixed, not re-run | run 35538279757; grader read its own ephemeral live solution as a second project |
| multi_node/billing_discrepancy_detector | FAIL 0.30, iteration 1 of 3 | run 35538279757: Integration Services 400 "Expected a field name expression but got 'StringValue'" on the ERP query (malformed Data Service filter, agent authoring); accountTier not derived from CRM |
| connector_features/generic_dynamic_node | green | run 35538279757 |
| connector_features/slack_http_fallback | 0.76; grader fixed, not re-run | run 35538279757: debug completed; grader wanted `emoji.list`, connector generic resource is `emoji_list_GET` |
| connector_features/jdbc_databricks_query (structural) | green | run 35538279757 |
| connector_trigger/webhook_waitfor_parallel (structural) | 0.47; grader fixed, not re-run | run 35538279757: agent used intermediateCatchEvent + WaitForEvent and Intsvc.UnifiedHttpRequest, both valid |
| connector_features/datafabric_connector/smoke_error (structural) | green | run 35538279757 |
| connector_features/testmanager_crud_grounded (self-report, Flow `skip:true` dropped) | 0.89; grader fixed, not re-run | run 35538279757: two byte-identical `.bpmn` (scaffold + solution copy) |
| interactive/bellevue_weather_simulated | written, reviewed, not run | commit 80033663f; live criterion timeout 1050, task_timeout 2550 (sanctioned) |
| interactive/cli_dice_roller_simulated | written, reviewed, not run | commit 8fc7a7692; task_timeout 2800 (sanctioned) |
| interactive/slack_channel_description_simulated | written, reviewed, not run | commit f000d026d; all five Flow criteria kept, live timeout 1050 |

Batch 10 landed; see "Batch 10 and after". The three interactive ports have never been dispatched.

## Batch 10 and after

Run 35538279757 (nine ports, one dispatch). Green: smoke_error, generic_dynamic_node, jdbc_databricks_query. Four more failed only on grader defects, all fixed on this branch and replayed green against the downloaded CI artifacts (`gh run download 35538279757`, `**/00/artifacts/`):

1. `find_bpmn_file` with no hint now treats byte-identical `.bpmn` copies as one artifact (testmanager_crud_grounded: the agent copied its scaffold into the solution wrapper).
2. `resolve_project(exclude_under=…)`: a live grader's own `uip solution projects import` leaves an identical project under its run directory; later criteria in the same task must exclude it (both billing graders pass `LIVE_RUN_DIR`). Any future multi-criterion live grader needs the same.
3. Classify wait-for-event by the `Intsvc.WaitForEvent` wrapper, not the BPMN tag: the agent emits `bpmn:intermediateCatchEvent` + messageEventDefinition as well as `bpmn:receiveTask`, and both validate (webhook_waitfor_parallel; same lesson as trigger_lifecycle for EventTrigger).
4. Accept `Intsvc.UnifiedHttpRequest` wherever a grader accepts `Intsvc.HttpExecution`; registry-workflow.md lists both for the managed HTTP sendTask.
5. Slack's generic resource for the `emoji.list` endpoint is `emoji_list_GET`; the fallback grader matches `emoji[._]list`.

Two real failures, one iteration spent each: billing_discrepancy_detector (Integration Services 400 on the ERP query filter, "Expected a field name expression but got 'StringValue'": the agent wrote a malformed Data Service filter; add to the skill findings as "Data Service query filter grammar") and slack_weather_pipeline (script task could not find channel `office-bellevue`, which exists and Flow's agent finds; likely channel-list pagination).

Next dispatch, one batch: the four grader-fixed tasks for confirmation, the two real failures (iteration 2), the three interactive simulated ports and `ceql_where` (first run). Ten tasks.

## Probe bucket (16): pilot ported, 11 decided, 4 blocked

`connector_features/ceql_where` is ported (commit fd6312fde), not yet run. The probe confirmed the filter carrier exists: `Intsvc.ActivityExecution` enrichment for the Entra `groups` List operation exposes a `where` parameter (type `query`, `FilterBuilder`, `hasCEQL: true`), and the CI-passing Data Fabric artifact carries the same tree as a `target="query" name="queryExpression" type="json"` input. As in Flow, the sandbox has no live tenant for enrichment, so the port grades the same standalone `where_detail.json` planning artifact plus the connector node and terminate end. No `bpmn validate` gate, matching Flow. Its one review flag: the groups-operation tolerance (objectName contains `group`, or `groups` + GET/list) has no CI-passed fixture yet.

Verdict for the other 11 field-shape evals, from that probe:

| Eval | Verdict | Carrier |
|---|---|---|
| path_params, query_params | portable, high confidence | `target="path"` / `target="query"` inputs, proven live |
| paginated_reference_lookup | portable | same query carrier (`pageSize`, `nextPage` seen in the Entra enrichment) |
| complex_array, multiselect | portable | nested JSON in the single `target="body"` CDATA, or array-valued query inputs |
| enum | portable | any literal `uipath:input` graded against the allowed set |
| enhanced_enum, searchable_joins | plausible, unverified | needs the `metadata` json context field or a `where`/`queryExpression` carrier; verify with a live `registry get` for the target connector first |
| generate_schema | uncertain | BPMN's schema surface is the opaque `jsonSchema` output contract that the skill says not to pre-empt offline; side-artifact grading or park |
| dtl_load_by_default ×2 | uncertain | `design.loadByDefault` is discovery-time metadata, not wire XML; portable only if Flow's grader checks the wire value |

The remaining 4 probes need a published agent substitute (billing_dispute_analyst / _resolution / _writer use Flow inline agents) or a file-typed process variable (single_node/file_attachment).

## Methodology (how each port is made)

1. **One Sonnet subagent per task** with `PORTING-BRIEF.md` (faithfulness table, construct translation, mandatory grading contract), `BATCH1-ADDENDUM.md` (connector node forms, criterion translations, staging paths), and for live ports `LIVE-ADDENDUM.md`. Ports are born normalized: every grader assertion is tagged F (translation of a cited Flow assertion), I (artifact plumbing) or T (a listed tolerance); anything else is not written. `NORMALIZATION.md` is the pass that retro-fitted the first 15 ports to that rule.
2. **Review = mechanical cross-check + assertion map.** The cross-check (a small script used throughout; see the parity ledger notes) compares criteria type/order/weight/threshold/timeout, run_limits, tags, prompt literals, pre_run/post_run, relative paths against the Flow source. Deviations allowed: CLI verbs, grader implementation, live criterion timeouts sized to the priced BPMN CLI sequence, `task_timeout` = turn_timeout + grading + 60 when Flow's does not cover it.
3. **One CI dispatch per batch** (`gh workflow run run-coder-eval.yml --ref <branch> -f task_globs='…'`), default codex driver, alpha tenant. Results: `gh run download <id>` → `**/task.json` → `success_criteria_results`; artifacts under `**/00/artifacts/` hold the agent's `.bpmn` for grader regression.
4. **Iteration rule:** fix only port defects (grader over-strictness, wrong construct name); max 3 graded iterations; a repeat runtime/skill failure parks the task with evidence in the ledger. Never weaken a Flow assertion to go green.

## Live-grader recipe (proven on 7 tasks)

Canonical: `_shared/check_jira_get_issue.py`. Sequence via `_shared/bpmn_live.py`: `uip solution init <live-dir>/<Name>` under the sandbox CWD → `uip solution projects import <project> --solutionFile <.uipx>` (assert sha256 of the imported `.bpmn` equals the submitted one) → `run_debug(project, inputs, log, timeout)` → `debug-instance variables-all <id>` → `debug-instance incidents <id>`. Grade from `variables-all`: root scope Globals plus every element's `Outputs` (root public output values have read back `null`; element outputs are reliable; connector responses via `connector_response_values`). post_run `_setup/cleanup_solutions.py` sweeps the ephemeral solution.

Budget: `_shared/test_criterion_budgets.py` prices every `run_debug` call; criterion `timeout` ≥ solution init 90 + import 180 + debug 480 + variables-all 120 + incidents 120 + margin 60 = 1050 for one debug run (per-case loops multiply the debug/variables terms; annotate `# budget-guard: manual xN` when the loop count is not a module literal).

## Runtime and CLI facts learned (grade around them)

- `uip maestro bpmn debug` polls at most 300 times; `run_debug` derives `--poll-interval` from its timeout and raises a clear failure on the CLI's poll-timeout envelope or a `subprocess.TimeoutExpired` (carrying the CLI's stderr log).
- Incident 102010 "Value cannot be null (Parameter 'Folder')" on a Slack activity = missing `folderKey` binding (agent defect). 102009 "Parameter '<x>' has null or empty value" = missing activity parameter (agent defect). 400008 on a multi-instance marker = input collection over a connector response does not evaluate (platform/skill).
- Actions.HITL needs a deployed Action App to pass `bpmn validate`; HITL ports reach parity on every other criterion (decision: leave as is).
- The eval agent emits connector nodes in two forms (curated `objectName` with path/query inputs and a structured tree in `metadata`; or generic entity-CRUD with `objectName` = entity and the verb in `operation`/`method`). Graders accept both; inputs at any depth; body optional outside Create/Update.
- `_shared/validate_bpmn.py` validates every `.bpmn` in the sandbox: the old "any file validates" loop passed on a stray `bpmn init` scaffold.

## Skill findings to report upstream

Connector trigger parameters (Data Fabric entity, Outlook `parentFolderId`) are omitted on first attempts; `uip is triggers objects/describe` discovery is not taught; Slack `folderKey` binding omitted; `Intsvc.HttpExecution` response shape unclear to downstream scripts; Data Service query filter grammar (400 "Expected a field name expression"); Slack channel lookup misses existing channels (pagination); multi-instance over connector output fails at runtime; no "existing solutions → ask" greenfield rule; Actions.HITL requires a tenant Action App.

## Resuming

1. `git checkout test/bpmn-port-live` (stacked on the PR branch; rebase after the PR merges).
2. Dispatch the ten-task batch listed under "Batch 10 and after"; record results in `parity-ledger.md` and this table.
3. New ports follow the spawn pattern "read PORTING-BRIEF, BATCH1-ADDENDUM, LIVE-ADDENDUM; port <task>; create <paths>; gates; report with assertion map".
4. Dispatch new ports as one batch; iterate per the rule; park with evidence.
5. Port the 7 field-shape probes marked portable; verify the carrier live before the 2 plausible ones; the 4 agent/file-typed probes need tenant fixtures first.
