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
| multi_node/slack_weather_pipeline | written, in CI batch 10 | run 35538279757 |
| multi_node/billing_invoice_lookup | written, in CI batch 10 | run 35538279757 |
| multi_node/billing_discrepancy_detector | written, in CI batch 10 | run 35538279757 |
| connector_features/generic_dynamic_node | written, in CI batch 10 | run 35538279757 |
| connector_features/slack_http_fallback | written, in CI batch 10 | run 35538279757 |
| connector_features/jdbc_databricks_query (structural) | written, in CI batch 10 | run 35538279757 |
| connector_trigger/webhook_waitfor_parallel (structural) | written, in CI batch 10 | run 35538279757 |
| connector_features/datafabric_connector/smoke_error (structural) | written, in CI batch 10 | run 35538279757 |
| connector_features/testmanager_crud_grounded (self-report, Flow `skip:true` dropped) | written, in CI batch 10 | run 35538279757 |
| interactive/bellevue_weather_simulated | being written (agent in flight when this doc was cut) | — |
| interactive/cli_dice_roller_simulated | being written | — |
| interactive/slack_channel_description_simulated | being written | — |

Batch 10 results and the three interactive ports are appended in the "Batch 10 and after" section when they land; if that section is missing, read `parity-ledger.md` or re-run the batch.

## Probe bucket (16), not started except the pilot

`connector_features/ceql_where` is the pilot for the 12 Integration Service field-shape evals (CEQL filter, complex_array, enum, enhanced_enum, multiselect, path_params, query_params, searchable_joins, generate_schema, dtl_load_by_default ×2, paginated_reference_lookup). An agent was probing it when this doc was cut; its verdict decides the other 11. The remaining 4 probes need a published agent substitute (billing_dispute_analyst / _resolution / _writer use Flow inline agents) or a file-typed process variable (single_node/file_attachment).

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

Connector trigger parameters (Data Fabric entity, Outlook `parentFolderId`) are omitted on first attempts; `uip is triggers objects/describe` discovery is not taught; Slack `folderKey` binding omitted; `Intsvc.HttpExecution` response shape unclear to downstream scripts; multi-instance over connector output fails at runtime; no "existing solutions → ask" greenfield rule; Actions.HITL requires a tenant Action App.

## Resuming

1. `git checkout test/bpmn-port-live` (stacked on the PR branch; rebase after the PR merges).
2. Read batch 10's run (35538279757) if the "Batch 10 and after" section is missing; record results in `parity-ledger.md`.
3. Finish or re-spawn the three interactive live ports and the `ceql_where` probe (briefs in this directory; spawn prompts followed the pattern "read PORTING-BRIEF, BATCH1-ADDENDUM, LIVE-ADDENDUM; port <task>; create <paths>; gates; report with assertion map").
4. Dispatch new ports as one batch; iterate per the rule; park with evidence.
5. Decide the 12 field-shape probes from the `ceql_where` verdict; the 4 agent/file-typed probes need tenant fixtures first.
