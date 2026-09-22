# Flow → BPMN eval porting: live-tier handoff

Branch: `test/bpmn-port-live`, stacked on `test/bpmn-port-connectors` (PR #3426, the structural bucket). This document is the state of the live-tier port work as of 2026-09-20 and how to continue it. Methodology files sit beside it in this directory.

## Context

The Flow suite (`tests/tasks/uipath-maestro-flow/`) has 131 tasks; the BPMN suite had 82. A per-task map put 62 Flow tasks in scope (`parity-ledger.md`): 29 structural (authoring + `validate`), 17 live (the Flow grader runs `flow debug`), 16 feasibility probes; 30 are Flow-only surface (IXP, evaluate, voice, conversational, bindings, native Data Fabric nodes).

Reading the Flow graders during the loop reclassified four "structural" tasks as live (their graders debug): `slack_http_fallback`, `bellevue_weather_simulated`, `cli_dice_roller_simulated`, `slack_channel_description_simulated`; and four "live" tasks as structural (their graders never debug): `smoke_error`, `jdbc_databricks_query`, `webhook_waitfor_parallel`, `testmanager_crud_grounded` (self-reported result file, as Flow). The live bucket is therefore 21 tasks.

## Status (as of 2026-09-22, after batch 15)

Live bucket (21) and field-shape probes (9) on this branch. Every row is a CI result on the alpha tenant, codex driver.

| Task | State | Evidence |
|---|---|---|
| e2e/customer_escalation_triage | green (already on main) | pre-existing |
| e2e/jira_get_issue | green | run 35501830119 |
| e2e/jira_create_issue | green | run 35503094182 |
| e2e/escalation_jira_ticket | green | run 35503094182 |
| e2e/escalation_orchestrator_paths | green | run 35503094182 |
| e2e/escalation_slack_alert | green it.2 | run 35524004307 |
| multi_node/slack_channel_description | green it.2 | run 35525387843 |
| connector_features/generic_dynamic_node | green | run 35538279757 |
| connector_features/jdbc_databricks_query (structural) | green | run 35538279757 |
| connector_features/datafabric_connector/smoke_error (structural) | green | run 35538279757 |
| connector_features/slack_http_fallback | green | run 35783045540 |
| connector_trigger/webhook_waitfor_parallel (structural) | green | run 35783045540 |
| connector_features/testmanager_crud_grounded | green | run 35783045540 |
| interactive/cli_dice_roller_simulated | green | run 35783045540 |
| multi_node/billing_invoice_lookup | green | run 35785806030 |
| multi_node/slack_weather_pipeline | green it.3 | run 35785806030 |
| connector_features/enum | green | run 35789221753 |
| connector_features/query_params | green | run 35789221753 |
| connector_features/multiselect | green | run 35789221753 |
| connector_features/searchable_joins | green | run 35789221753 |
| connector_features/complex_array | green 0.875 (advisory miss only) | run 35789221753 |
| connector_features/path_params | green it.2 | run 35790934047 |
| connector_features/paginated_reference_lookup | green it.3 | run 35791969905 |
| multi_node/bellevue_weather | parked, skill gap | HttpExecution response shape (`temperature_2m` of undefined), runs 35523787101 + 35525387843 |
| interactive/bellevue_weather_simulated | parked, same gap | run 35785806030 |
| e2e/jira_search_triage | parked, platform/skill gap | multi-instance over a connector response, 400008 (run 35525387843) |
| e2e/jira_lifecycle | parked, needs live investigation | three different runtime failures; Flow flaky |
| multi_node/billing_discrepancy_detector | parked, skill gap | Data Service where clause from a process variable, two different 400s (runs 35538279757, 35783045540) |
| interactive/slack_channel_description_simulated | parked, skill gap | Slack channel pagination: page 1 only (run 35789221753); Flow 4/12 |
| connector_features/ceql_where | parked, surface gap | agent writes the CEQL `where` string, never Flow's filter tree (runs 35783045540, 35785806030) |
| connector_features/enhanced_enum | parked, skill gap | no WooCommerce connector node in either run (runs 35789221753, 35790934047) |

Total: 23 green, 8 parked. Not started: the 4 probes that need tenant fixtures (billing_dispute_analyst / _resolution / _writer need a published agent substitute for Flow inline agents; single_node/file_attachment needs a file-typed process variable).

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
