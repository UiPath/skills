# Flow → BPMN eval parity map

Flow tasks: 131 · BPMN tasks: 82 · generated 2026-09-19

| Bucket | Count |
|---|---|
| Ported 1:1 | 21 |
| Covered by an equivalent BPMN task | 18 |
| Portable — structural (authoring + validate) | 29 |
| Portable — live (bpmn debug + tenant re-read) | 17 |
| Portable pending a feasibility probe | 16 |
| Not portable (Flow-only surface) | 30 |

## Porting ledger (branch `test/bpmn-port-connectors`)

| Flow task | BPMN port | CI result | Notes |
|---|---|---|---|
| `connector_features/drive_to_slack.yaml` | `connector_features/drive_to_slack/` | PASS 1/1 (run 35484984200) | pilot |
| `connector_features/datafabric_connector/smoke_create_all_types.yaml` | `…/datafabric_connector/smoke_create_all_types/` | PASS (run 35489744689, iteration 2) | grader widened to generic entity-CRUD form |
| `connector_features/datafabric_connector/integration_create_get.yaml` | `…/datafabric_connector/integration_create_get/` | PASS (run 35489744689, iteration 2) | same |
| `connector_features/datafabric_connector/contractregistry_crud_filters.yaml` | `…/datafabric_connector/contractregistry_crud_filters/` | PASS (run 35489744689, iteration 2) | same + transitive output mapping |
| `connector_features/datafabric_connector/smoke_query.yaml` | `…/datafabric_connector/smoke_query/` | SKIPPED (surface gap) after PASS it.3 (run 35490499651) and two smoke-gate fails (run 35674400362 attempts 1+2) | the curated Query Entity Records template has no sort-field parameter (only `isAscending`); Flow carried `_sortFieldName`. The passing runs used an invented `sortField` input or CEQL `ORDER BY`; without a sanctioned carrier the task is `skip: true`, criteria unchanged. |
| `connector_features/datafabric_connector/smoke_update.yaml` | `…/datafabric_connector/smoke_update/` | PASS (run 35499789502) | batch 2 |
| `connector_features/datafabric_connector/smoke_file_activities.yaml` | `…/datafabric_connector/smoke_file_activities/` | PASS (run 35499789502) | batch 2 |
| `connector_features/datafabric_connector/e2e_contract_intake_pipeline.yaml` | `…/datafabric_connector/e2e_contract_intake_pipeline/` | PASS (run 35499789502) | batch 2 |
| `connector_features/datafabric_connector/trigger_lifecycle.yaml` | `…/datafabric_connector/trigger_lifecycle/` | PASS it.3 (run 35501830119) after two grader fixes (it.1 was a real agent omission of the entity param; it.2 a grader over-strictness) | |
| `connector_features/testmanager_attachments/…` | `connector_features/testmanager_attachments/` | PASS (run 35499789502) | batch 2 |
| `connector_features/testmanager_execution_results/…` | `connector_features/testmanager_execution_results/` | PASS (run 35499789502) | batch 2 |
| `connector_features/testmanager_generic_records/…` | `connector_features/testmanager_generic_records/` | PASS (run 35499789502) | batch 2 |
| `connector_features/testmanager_requirement_lifecycle/…` | `connector_features/testmanager_requirement_lifecycle/` | PASS (run 35499789502) | batch 2 |
| `connector_features/testmanager_testset_lifecycle/…` | `connector_features/testmanager_testset_lifecycle/` | PASS (run 35499789502) | batch 2 |
| `connector_features/datafabric_connector/smoke_update_existing_flow.yaml` | `…/datafabric_connector/smoke_update_existing_flow/` | PASS (run 35500726138) | batch 3, brownfield scaffold via bpmn init |
| `connector_features/non-catalog-http-fallback/…` | `connector_features/non_catalog_http_fallback/` | PASS (run 35500726138) | batch 3 |
| `single_node/outlook_waitfor_email/…` | `single_node/outlook_waitfor_email/` | PASS (run 35500726138) | batch 3 |
| `single_node/outlook_trigger_inbox/…` | `single_node/outlook_trigger_inbox/` | PASS it.2 (run 35501830119); it.1 the agent omitted parentFolderId | advisory `uip is triggers` telemetry stays 0 (skill does not teach trigger discovery) |
| `e2e/devcon_expense_approval.yaml` | `e2e/devcon_expense_approval/` | PARTIAL 0.885 it.3 (run 35503094182) | every HITL/schema/wiring assertion passes; only `validate` fails (Actions.HITL MISSING_BINDING: needs a deployed Action App; Flow's inline quick-form has no tenant dependency). Iterations exhausted; parity-minus-validate, same platform gap as the two simulated HITL ports. |
| `e2e/jira_get_issue/…` | `e2e/jira_get_issue/` | PASS (run 35501830119) | LIVE pilot: ephemeral solution + bpmn debug + variables-all recipe works |
| `interactive/customer_escalation_simulated/…` | `interactive/customer_escalation_simulated/` | PASS 0.94 (run 35501830119) | only the advisory name check (threshold 0) missed, as in Flow |
| `interactive/expense_approval_simulated/…` | `interactive/expense_approval_simulated/` | PARTIAL 0.70 (run 35501830119) | everything passes except `validate`: Actions.HITL needs a deployed Action App binding (MISSING_BINDING with placeholder appId). Platform gap vs Flow's inline quick-form. |
| `interactive/hitl_schema_design_simulated/…` | `interactive/hitl_schema_design_simulated/` | PARTIAL 0.68 (run 35501830119) | same validate/Action App gap |
| `interactive/solution_select.yaml` | `interactive/solution_select/` | PARKED (skill gap, run 35501830119) | BPMN skill has no existing-solution selection rule; agent auto-scaffolded `WeatherAlertSolution/` without asking, exactly as predicted. Port kept in tree as the documented gap. |
| `e2e/jira_create_issue/…` | `e2e/jira_create_issue/` | PASS (run 35503094182) | live |
| `e2e/escalation_jira_ticket/…` | `e2e/escalation_jira_ticket/` | PASS (run 35503094182) | live |
| `e2e/escalation_orchestrator_paths/…` | `e2e/escalation_orchestrator_paths/` | PASS (run 35503094182) | live, 7 debug runs |
| `e2e/escalation_slack_alert/…` | `e2e/escalation_slack_alert/` | PASS it.2 (run 35524004307); it.1 the agent omitted the Slack folderKey binding (runtime 102010) | live |
| `e2e/jira_lifecycle/…` | `e2e/jira_lifecycle/` | PARKED after 3 iterations | it.1 our poll-cap bug; it.2 instance never terminal in 720s; it.3 (run 35525387843) `bpmn debug` exited 1 before creating an instance. Three different runtime failures of a multi-instance Jira loop; Flow's own version is flaky (0.82 typical, 2/12 zero). Needs a live investigation, not more retries. |
| `e2e/jira_search_triage/…` | `e2e/jira_search_triage/` | PARKED (skill gap) after 3 iterations | it.3 (run 35525387843) runtime 400008 "Failed to evaluate the input collection variable for the marker element": the multi-instance `inputCollection="=vars.Var_SearchResponse.issues"` over a connector response does not evaluate — multi-instance over connector output not taught/supported. |
| `multi_node/bellevue_weather/…` | `multi_node/bellevue_weather/` | PARKED (skill gap) after it.1+it.2 (runs 35523787101, 35525387843) | identical runtime fault both times: the script task reads `temperature_2m` off an undefined HTTP response — the skill does not teach the Intsvc.HttpExecution response shape well enough for downstream scripts. |
| `multi_node/slack_channel_description/…` | `multi_node/slack_channel_description/` | PASS it.2 (run 35525387843); it.1 the agent omitted the Slack channel parameter | live |
| `connector_trigger/trigger_with_filter.yaml` | — | PARKED (skill gap) | Flow asserts a structured `filter` tree (groupOperator + filters[], MST-8802 guard); BPMN `Intsvc.EventTrigger` declares `filter` only as an untyped object with no template placeholder and the skill says trigger properties are CLI-owned enrichment. Re-port once a persisted filter shape is documented. |
| `connector_features/datafabric_connector/smoke_error.yaml` | `…/datafabric_connector/smoke_error/` | PASS 1.0 (run 35538279757) | batch 10, structural |
| `connector_features/generic_dynamic_node/…` | `connector_features/generic_dynamic_node/` | PASS 1.0 (run 35538279757) | batch 10, live: ServiceNow acr_user list ran, empty array as expected |
| `connector_features/jdbc_databricks_query/…` | `connector_features/jdbc_databricks_query/` | PASS 1.0 (run 35538279757) | batch 10, structural |
| `multi_node/billing_invoice_lookup/…` | `multi_node/billing_invoice_lookup/` | PASS 0.91 it.1 (run 35538279757); grader fixed, not re-run | live: all three malformed inputs normalized and queried. Only the advisory `bindings` step failed, on the grader's own ephemeral live solution being read as a second project (fixed: `resolve_project(exclude_under=[LIVE_RUN_DIR])`). |
| `connector_features/testmanager_crud_grounded/…` | `connector_features/testmanager_crud_grounded/` | 0.89 it.1 (run 35538279757); grader fixed, not re-run | self-report round-trip verified live. The node-types criterion died on two byte-identical `.bpmn` (scaffold + solution copy); `find_bpmn_file` now treats identical copies as one artifact. Replays green on the CI artifact. |
| `connector_features/slack-http-fallback/…` | `connector_features/slack_http_fallback/` | 0.76 it.1 (run 35538279757); grader fixed, not re-run | live debug completed with no incidents. The fallback check looked for `emoji.list`; the Slack connector's generic resource for that endpoint is `emoji_list_GET`, which the agent used. Tolerance `emoji[._]list` added; replays green. |
| `connector_trigger/webhook_waitfor_parallel.yaml` | `connector_trigger/webhook_waitfor_parallel/` | 0.47 it.1 (run 35538279757); grader fixed, not re-run | agent emitted the wait as `bpmn:intermediateCatchEvent` + `Intsvc.WaitForEvent` (validates) and the GET as `Intsvc.UnifiedHttpRequest` (the skill lists it beside HttpExecution). Grader now classifies by wrapper type and accepts both HTTP types; replays green. Advisory `uip is webhooks config` telemetry 0, as feared. |
| `multi_node/billing_discrepancy_detector/…` | `multi_node/billing_discrepancy_detector/` | FAIL 0.30 it.1 (run 35538279757) | validate passed; live debug raised an Integration Services 400 on `Task_QueryERP`: "Expected a field name expression but got 'StringValue'" (malformed Data Service query filter, agent authoring). Advisory: `accountTier` did not derive from the CRM query. Also hit the same `bindings` grader defect (fixed). One iteration left to spend when live work resumes. |
| `multi_node/slack_weather_pipeline/…` | `multi_node/slack_weather_pipeline/` | FAIL 0.375 it.1 (run 35538279757) | validate passed; live debug incident 300501 in script task `Task_SelectChannel`: "Slack channel office-bellevue was not found" — the agent's channel lookup did not find a channel Flow's port finds (likely list pagination/limit). Agent defect, not grader; retry when live work resumes. |
| `connector_features/slack-http-fallback/…` (batch 11) | `connector_features/slack_http_fallback/` | PASS 1.0 (run 35783045540) | confirmed after the emoji_list tolerance |
| `connector_trigger/webhook_waitfor_parallel.yaml` (batch 11) | `connector_trigger/webhook_waitfor_parallel/` | PASS 1.0 (run 35783045540) | confirmed after wrapper-type classification |
| `connector_features/testmanager_crud_grounded/…` (batch 11) | `connector_features/testmanager_crud_grounded/` | PASS 1.0 (run 35783045540) | confirmed after identical-copy tolerance |
| `interactive/cli_dice_roller_simulated/…` | `interactive/cli_dice_roller_simulated/` | PASS 1.0 first run (run 35783045540) | live, simulated user |
| `multi_node/billing_invoice_lookup/…` (batch 11) | `multi_node/billing_invoice_lookup/` | INFRA (run 35783045540): platform 504 on poll-instance-status; not counted | rerun in batch 12 |
| `multi_node/billing_discrepancy_detector/…` (it.2) | `multi_node/billing_discrepancy_detector/` | PARKED (skill gap) after it.2 (run 35783045540) | it.1 400 "Expected a field name expression but got 'StringValue'"; it.2 400 "Error parsing query: SELECT * FROM DUMMY WHERE `accountNumber`=" (variable interpolated as empty). Both: the skill does not teach how to build a Data Service where clause from a process variable. Flow passes 11/12 nightlies. |
| `connector_features/ceql_where.yaml` (it.1) | `connector_features/ceql_where/` | FAIL 0 it.1 (run 35783045540) | agent wrote the CEQL string `displayName='active'` plus a flat {field, operator, value} object, not the canonical tree (numeric groupOperator + filters[]) the prompt asks for. Iteration 2 in batch 12; if repeated, park: BPMN's sanctioned `where` carrier is a CEQL string. |
| `interactive/bellevue_weather_simulated/…` (it.1) | `interactive/bellevue_weather_simulated/` | HARNESS (run 35783045540): simulation stopped on turn 1 with an empty agent output (stop_token), no HTTP node built | rerun in batch 12; Flow's version passes 8/12 |
| `interactive/slack_channel_description_simulated/…` (it.1) | `interactive/slack_channel_description_simulated/` | FAIL 0.52 it.1 (run 35783045540) | runtime 400 channel_not_found on Get_Channel_Info (agent passed a channel the bot is not in). Flow's version fully passes 4/12 nightlies. Iteration 2 in batch 12. |
| `multi_node/slack_weather_pipeline/…` (it.2) | `multi_node/slack_weather_pipeline/` | FAIL 0 it.2 (run 35783045540) | validate MISSING_BINDING on the Slack node + runtime 401 "Invalid Organization or User secret" (wrong connection bound). it.1 was channel-not-found. Flow's version passes 6/12 nightlies. Iteration 3 in batch 12, then park. |
| `multi_node/billing_invoice_lookup/…` (batch 12) | `multi_node/billing_invoice_lookup/` | PASS 1.0 (run 35785806030) | live; the batch-11 504 was infra |
| `multi_node/slack_weather_pipeline/…` (it.3) | `multi_node/slack_weather_pipeline/` | PASS 1.0 it.3 (run 35785806030) | live; it.1 channel lookup, it.2 wrong connection — agent flakiness at Flow parity (Flow 6/12) |
| `interactive/bellevue_weather_simulated/…` (it.2) | `interactive/bellevue_weather_simulated/` | PARKED (skill gap) after it.2 (run 35785806030) | runtime "Cannot read property 'temperature_2m' of undefined" in the summarize script: same HttpExecution response-shape gap that parked multi_node/bellevue_weather. |
| `connector_features/ceql_where.yaml` (it.2) | `connector_features/ceql_where/` | PARKED (surface gap) after it.2 (run 35785806030) | both runs: agent writes the CEQL string `displayName='active'` (the connector's sanctioned `where` parameter) plus a flat object, never the numeric-groupOperator tree Flow's grader requires. The tree is a Flow-skill construct with no BPMN carrier. Verdict for the family: tree-shape assertions do not port; wire-parameter assertions (path, query, pagination, enum, multiselect, complex_array) do. |
| `interactive/slack_channel_description_simulated/…` (it.2) | `interactive/slack_channel_description_simulated/` | GRADER DEFECT it.2 (run 35785806030); fixed, it.3 in batch 13 | agent left an untyped draft under `<Name>Solution/` beside the real solution; `find_bpmn_file` without a hint saw two projects. It now drops candidates carrying no registry-typed node; replays to the real file. |
| `connector_features/enum.yaml` | `connector_features/enum/` | PASS 1.0 first run (run 35789221753) | field-shape family |
| `connector_features/query_params.yaml` | `connector_features/query_params/` | PASS 1.0 first run (run 35789221753) | field-shape family |
| `connector_features/multiselect.yaml` | `connector_features/multiselect/` | PASS 1.0 first run (run 35789221753) | field-shape family |
| `connector_features/searchable_joins.yaml` | `connector_features/searchable_joins/` | PASS 1.0 first run (run 35789221753) | field-shape family |
| `connector_features/complex_array.yaml` | `connector_features/complex_array/` | PASS 0.875 first run (run 35789221753) | only the advisory resolved-user-id check (threshold 0) missed; Flow's own version fully passes 3/12 |
| `connector_features/path_params.yaml` (it.1) | `connector_features/path_params/` | FAIL 0.83 it.1 (run 35789221753); it.2 in batch 14 | agent built the Jira GET as UnifiedHttpRequest with the issue key as an unbound variable, never the fixed ENGCE-00000 the prompt gives. Flow 12/12. |
| `connector_features/enhanced_enum.yaml` (it.1) | `connector_features/enhanced_enum/` | FAIL 0.5 it.1 (run 35789221753); it.2 in batch 14 | agent produced no connector node at all (only an enum-typed variable). Flow 12/12. |
| `connector_features/paginated_reference_lookup.yaml` (it.1) | `connector_features/paginated_reference_lookup/` | FAIL 0.28 it.1 (run 35789221753); it.2 in batch 14 | agent sent to channel "simple" by name, never resolved/paginated to C083AN4E61E; both discovery advisories 0. Flow 11/12: BPMN skill does not teach Slack channel-id resolution. |
| `interactive/slack_channel_description_simulated/…` (it.3) | `interactive/slack_channel_description_simulated/` | PARKED (skill gap) after it.3 (run 35789221753) | debug completed; the agent listed page 1 of conversations and scripted the description out of it, so office-bellevue never appeared. Same pagination gap as multi_node/slack_channel_description it.1. Flow's version fully passes 4/12. |
| `connector_features/path_params.yaml` (it.2) | `connector_features/path_params/` | PASS 1.0 it.2 (run 35790934047) | agent used the curated Jira get-issue node with issueId=ENGCE-00000 as a path input |
| `connector_features/enhanced_enum.yaml` (it.2) | `connector_features/enhanced_enum/` | PARKED (skill gap) after it.2 (run 35790934047) | both runs: no connector node in the artifact at all (types empty; only an enum-typed variable). The WooCommerce connector never gets a node in BPMN; Flow 12/12. |
| `connector_features/paginated_reference_lookup.yaml` (it.2) | `connector_features/paginated_reference_lookup/` | FAIL 0.76 it.2 (run 35790934047); it.3 in batch 15 (run 35791969905) | discovery advisories now pass; the send node carries channel "C083AN4E61", the resolved id with its last character dropped. Agent transcription error, not grader. |
| `connector_features/paginated_reference_lookup.yaml` (it.3) | `connector_features/paginated_reference_lookup/` | PASS 1.0 it.3 (run 35791969905) | discovery advisories and the resolved channel id all green |
| `connector_features/testmanager_testcase_lifecycle/…` | `connector_features/testmanager_testcase_lifecycle/` | PASS (run 35488848026) | Flow's skip:true not carried over |

## Ported 1:1 (21)

| Flow task | BPMN target / note |
|---|---|
| `edit/add_node/add_node.yaml` | edit/add_node (structural only; Flow is live) |
| `edit/add_output/add_output.yaml` | edit/add_output (structural only; Flow is live) |
| `edit/group_to_subflow/group_to_subflow.yaml` | edit/group_to_subflow (structural only; Flow is live) |
| `edit/move_node/move_node.yaml` | edit/move_node (structural only; Flow is live) |
| `edit/remove_node/remove_node.yaml` | edit/remove_node (structural only; Flow is live) |
| `edit/update_node/update_node.yaml` | edit/update_node (structural only; Flow is live) |
| `hitl/quality_01_schema_design.yaml` | hitl/quality_schema_design |
| `hitl/quality_02_result_downstream.yaml` | hitl/quality_result_downstream |
| `hitl/quality_03_boolean_decision.yaml` | hitl/quality_boolean_decision |
| `hitl/quality_04_brownfield_insert.yaml` | hitl/quality_brownfield_insert |
| `hitl/smoke_02_completed_port_wired.yaml` | hitl/smoke_completed_wired |
| `hitl/smoke_03_multi_outcome_routing.yaml` | hitl/smoke_multi_outcome_routing |
| `interactive/customer_escalation_triage/customer_escalation_triage.yaml` | e2e/customer_escalation_triage (live, this branch) |
| `multi_node/calculator/calculator.yaml` | multi_node/calculator (structural only; Flow is live) |
| `multi_node/customer_escalation/customer_escalation.yaml` | multi_node/customer_escalation |
| `multi_node/dice_roller/dice_roller.yaml` | multi_node/dice_roller (structural only; Flow is live) |
| `multi_node/feet_inches/feet_inches.yaml` | multi_node/feet_inches (structural only; Flow is live) |
| `multi_node/loop_multiply/loop_multiply.yaml` | multi_node/loop_multiply (structural only; Flow is live) |
| `multi_node/multi_city_weather/multi_city_weather.yaml` | multi_node/multi_city_weather (structural only; Flow is live) |
| `multi_node/reading_list/reading_list.yaml` | multi_node/reading_list (structural only; Flow is live) |
| `multi_node/wiki_pageviews/wiki_pageviews.yaml` | multi_node/wiki_pageviews (structural only; Flow is live) |

## Covered by an equivalent BPMN task (18)

| Flow task | BPMN target / note |
|---|---|
| `hitl/smoke_01_hitl_node_placed.yaml` | nodes/hitl_rpa_wrappers (HITL shell placed) |
| `single_node/api_workflow/api_workflow.yaml` | authoring/api_workflow_task (structural; Flow is live) |
| `single_node/coded_agent/coded_agent.yaml` | single_node/agent_job (same BPMN node; Flow is live) |
| `single_node/decision/decision.yaml` | author/gateway_sequence_flows (structural; Flow is live) |
| `single_node/delay/delay.yaml` | single_node/timer |
| `single_node/lowcode_agent/lowcode_agent.yaml` | single_node/agent_job (structural; Flow is live) |
| `single_node/openmeteo_weather/openmeteo_weather.yaml` | single_node/http_weather (structural; Flow is live) |
| `single_node/rpa/rpa.yaml` | single_node/rpa_job (structural; Flow is live) |
| `single_node/subflow/subflow.yaml` | single_node/subprocess |
| `single_node/switch/switch.yaml` | single_node/switch |
| `single_node/terminate/terminate.yaml` | single_node/terminate |
| `single_node/transform_filter/transform_filter.yaml` | single_node/script_task_filter |
| `single_node/transform_group_by/transform_group_by.yaml` | single_node/script_task_group_by |
| `single_node/transform_map/transform_map.yaml` | single_node/script_task_map |
| `smoke/init_validate.yaml` | smoke/author_validate |
| `smoke/merge_parallel_sync.yaml` | parallel/fork_join |
| `smoke/registry_discovery.yaml` | smoke/registry_discovery |
| `smoke/scheduled_trigger.yaml` | single_node/timer_start |

## Portable — structural (authoring + validate) (29)

| Flow task | BPMN target / note |
|---|---|
| `connector_features/datafabric_connector/contractregistry_crud_filters.yaml` | uipath-dataservice ActivityExecution payloads; validate-only |
| `connector_features/datafabric_connector/e2e_contract_intake_pipeline.yaml` | uipath-dataservice ActivityExecution payloads; validate-only |
| `connector_features/datafabric_connector/integration_create_get.yaml` | uipath-dataservice ActivityExecution payloads; validate-only |
| `connector_features/datafabric_connector/smoke_create_all_types.yaml` | uipath-dataservice ActivityExecution payloads; validate-only |
| `connector_features/datafabric_connector/smoke_file_activities.yaml` | uipath-dataservice ActivityExecution payloads; validate-only |
| `connector_features/datafabric_connector/smoke_query.yaml` | uipath-dataservice ActivityExecution payloads; validate-only |
| `connector_features/datafabric_connector/smoke_update.yaml` | uipath-dataservice ActivityExecution payloads; validate-only |
| `connector_features/datafabric_connector/smoke_update_existing_flow.yaml` | uipath-dataservice ActivityExecution payloads; validate-only |
| `connector_features/datafabric_connector/trigger_lifecycle.yaml` | Intsvc.EventTrigger Record Created/Updated + downstream ActivityExecution |
| `connector_features/drive_to_slack.yaml` | two ActivityExecution nodes; binary output chaining; validate-only |
| `connector_features/non-catalog-http-fallback/non_catalog_http_fallback.yaml` | generic HTTP connector (uipath-uipath-http) ActivityExecution |
| `connector_features/slack-http-fallback/slack_http_fallback.yaml` | connector-mode HTTP fallback (Intsvc.HttpExecution on Slack connection) |
| `connector_features/testmanager_attachments/testmanager_attachments.yaml` | one ActivityExecution per Test Manager operation; validate-only |
| `connector_features/testmanager_execution_results/testmanager_execution_results.yaml` | one ActivityExecution per Test Manager operation; validate-only |
| `connector_features/testmanager_generic_records/testmanager_generic_records.yaml` | one ActivityExecution per Test Manager operation; validate-only |
| `connector_features/testmanager_requirement_lifecycle/testmanager_requirement_lifecycle.yaml` | one ActivityExecution per Test Manager operation; validate-only |
| `connector_features/testmanager_testcase_lifecycle/testmanager_testcase_lifecycle.yaml` | one ActivityExecution per Test Manager operation; validate-only |
| `connector_features/testmanager_testset_lifecycle/testmanager_testset_lifecycle.yaml` | one ActivityExecution per Test Manager operation; validate-only |
| `connector_trigger/trigger_with_filter.yaml` | Intsvc.EventTrigger with structured filter tree |
| `e2e/devcon_expense_approval.yaml` | Actions.HITL + scriptTasks; schema-design judge |
| `interactive/bellevue_weather_simulated/bellevue_weather_simulated.yaml` | simulation harness is skill-agnostic; BPMN skill allows AskUserQuestion |
| `interactive/cli_dice_roller_simulated/cli_dice_roller_simulated.yaml` | simulation harness is skill-agnostic; BPMN skill allows AskUserQuestion |
| `interactive/customer_escalation_simulated/customer_escalation_simulated.yaml` | simulation harness is skill-agnostic; BPMN skill allows AskUserQuestion |
| `interactive/expense_approval_simulated/expense_approval_simulated.yaml` | simulation harness is skill-agnostic; BPMN skill allows AskUserQuestion |
| `interactive/hitl_schema_design_simulated/hitl_schema_design_simulated.yaml` | simulation harness is skill-agnostic; BPMN skill allows AskUserQuestion |
| `interactive/slack_channel_description_simulated/slack_channel_description_simulated.yaml` | simulation harness is skill-agnostic; BPMN skill allows AskUserQuestion |
| `interactive/solution_select.yaml` | existing-solution selection rule; check the BPMN skill states the same greenfield rule |
| `single_node/outlook_trigger_inbox/outlook_trigger_inbox.yaml` | Intsvc.EventTrigger startEvent with fresh parentFolderId reference resolution |
| `single_node/outlook_waitfor_email/outlook_waitfor_email.yaml` | Intsvc.WaitForEvent receiveTask with subject filter |

## Portable — live (bpmn debug + tenant re-read) (17)

| Flow task | BPMN target / note |
|---|---|
| `connector_features/datafabric_connector/smoke_error.yaml` | live 4xx on missing entity; debug + incidents |
| `connector_features/generic_dynamic_node/generic_dynamic_node.yaml` | generic activity + --object-name at registry get; live |
| `connector_features/jdbc_databricks_query/jdbc_databricks_query.yaml` | JDBC ActivityExecution; live |
| `connector_features/testmanager_crud_grounded/testmanager_crud_grounded.yaml` | Test Manager create+get round trip; live debug |
| `connector_trigger/webhook_waitfor_parallel.yaml` | parallelGateway + Intsvc.WaitForEvent (webhook) + HttpExecution self-trigger; live debug |
| `e2e/escalation_jira_ticket/escalation_jira_ticket.yaml` | sibling of the live escalation port on this branch; reuse escalation_is.py |
| `e2e/escalation_orchestrator_paths/escalation_orchestrator_paths.yaml` | exclusiveGateway paths + Orchestrator.* nodes; live debug |
| `e2e/escalation_slack_alert/escalation_slack_alert.yaml` | sibling of the live escalation port; reuse escalation_is.py |
| `e2e/jira_create_issue/jira_create_issue.yaml` | Jira ActivityExecution; live debug + tenant re-read; teardown journal |
| `e2e/jira_get_issue/jira_get_issue.yaml` | Jira ActivityExecution read-only; live debug + variables-all |
| `e2e/jira_lifecycle/jira_lifecycle.yaml` | multiInstance loop + exclusiveGateway + Jira create/comment/transition |
| `e2e/jira_search_triage/jira_search_triage.yaml` | Jira JQL search + multiInstance + add comment |
| `multi_node/bellevue_weather/bellevue_weather.yaml` | HttpExecution sendTask + scriptTask + exclusiveGateway; debug via bpmn_live |
| `multi_node/billing_discrepancy_detector/billing_discrepancy_detector.yaml` | two DF reads in parallelGateway fork/join; no agent |
| `multi_node/billing_invoice_lookup/billing_invoice_lookup.yaml` | Data Fabric via Intsvc.ActivityExecution (uipath-dataservice); no agent |
| `multi_node/slack_channel_description/slack_channel_description.yaml` | Intsvc.ActivityExecution Slack; Slack plumbing in e2e/customer_escalation_triage/escalation_is.py |
| `multi_node/slack_weather_pipeline/slack_weather_pipeline.yaml` | HttpExecution + Slack ActivityExecution; live debug |

## Portable pending a feasibility probe (16)

| Flow task | BPMN target / note |
|---|---|
| `connector_features/ceql_where.yaml` | IS field-shape feature on Intsvc.ActivityExecution payload; one probe decides the group |
| `connector_features/complex_array.yaml` | IS field-shape feature on Intsvc.ActivityExecution payload; one probe decides the group |
| `connector_features/dtl_load_by_default_false.yaml` | IS field-shape feature on Intsvc.ActivityExecution payload; one probe decides the group |
| `connector_features/dtl_load_by_default_true.yaml` | IS field-shape feature on Intsvc.ActivityExecution payload; one probe decides the group |
| `connector_features/enhanced_enum.yaml` | IS field-shape feature on Intsvc.ActivityExecution payload; one probe decides the group |
| `connector_features/enum.yaml` | IS field-shape feature on Intsvc.ActivityExecution payload; one probe decides the group |
| `connector_features/generate_schema.yaml` | IS field-shape feature on Intsvc.ActivityExecution payload; one probe decides the group |
| `connector_features/multiselect.yaml` | IS field-shape feature on Intsvc.ActivityExecution payload; one probe decides the group |
| `connector_features/paginated_reference_lookup.yaml` | IS field-shape feature on Intsvc.ActivityExecution payload; one probe decides the group |
| `connector_features/path_params.yaml` | IS field-shape feature on Intsvc.ActivityExecution payload; one probe decides the group |
| `connector_features/query_params.yaml` | IS field-shape feature on Intsvc.ActivityExecution payload; one probe decides the group |
| `connector_features/searchable_joins.yaml` | IS field-shape feature on Intsvc.ActivityExecution payload; one probe decides the group |
| `multi_node/billing_dispute_analyst/billing_dispute_analyst.yaml` | inline agent + context-grounding index: BPMN only has Orchestrator.StartAgentJob (published agent) — needs a published grounded agent on the tenant |
| `multi_node/billing_dispute_resolution/billing_dispute_resolution.yaml` | inline agent → StartAgentJob substitute |
| `multi_node/billing_resolution_writer/billing_resolution_writer.yaml` | inline agent → StartAgentJob substitute |
| `single_node/file_attachment/file_attachment.yaml` | file-typed process variable: confirm canvas variable contract supports it |

## Not portable (Flow-only surface) (30)

| Flow task | BPMN target / note |
|---|---|
| `bindings/idempotent_reconfigure.yaml` | tests `flow node configure` binding upsert; BPMN has no node configure. A bindings_v2.json correctness test would be new coverage, not a port |
| `bindings/multi_connector_independence.yaml` | tests `flow node configure` binding upsert; BPMN has no node configure. A bindings_v2.json correctness test would be new coverage, not a port |
| `bindings/no_duplicate_connection_bindings.yaml` | tests `flow node configure` binding upsert; BPMN has no node configure. A bindings_v2.json correctness test would be new coverage, not a port |
| `bindings/reconfigure_different_connection.yaml` | tests `flow node configure` binding upsert; BPMN has no node configure. A bindings_v2.json correctness test would be new coverage, not a port |
| `connector_features/datafabric_connector/smoke_activation_negative.yaml` | skill-routing smoke belongs to tests/tasks/activation, not a BPMN port |
| `connector_features/datafabric_connector/smoke_activation_positive.yaml` | skill-routing smoke belongs to tests/tasks/activation, not a BPMN port |
| `context-grounding/batch_transform/batch_transform.yaml` | Flow pattern node (batch transform) is Flow-only |
| `context-grounding/summarize/summarize.yaml` | Flow pattern node (deep-rag) is Flow-only |
| `conversational/conversational_chat_loop.yaml` | conversational agent loop is Flow-only |
| `evaluate/child_simulation/child_simulation_crud.yaml` | Flow evaluate capability (eval sets, simulations) has no BPMN counterpart |
| `evaluate/evaluator_type_choice.yaml` | Flow evaluate capability (eval sets, simulations) has no BPMN counterpart |
| `evaluate/inline_agent_eval/inline_agent_eval.yaml` | Flow evaluate capability (eval sets, simulations) has no BPMN counterpart |
| `evaluate/local_crud.yaml` | Flow evaluate capability (eval sets, simulations) has no BPMN counterpart |
| `evaluate/no_auto_upload.yaml` | Flow evaluate capability (eval sets, simulations) has no BPMN counterpart |
| `evaluate/simulation/simulation_crud.yaml` | Flow evaluate capability (eval sets, simulations) has no BPMN counterpart |
| `interactive/ixp_invoice_extraction_simulated/ixp_invoice_extraction_simulated.yaml` | IXP node is Flow-only |
| `ixp/e2e_01_invoice_extraction_greenfield.yaml` | IXP plugin is Flow-only; BPMN registry has no IXP node |
| `ixp/e2e_02_project_selection.yaml` | IXP plugin is Flow-only; BPMN registry has no IXP node |
| `ixp/e2e_03_project_creation_handoff/e2e_03_project_creation_handoff.yaml` | IXP plugin is Flow-only; BPMN registry has no IXP node |
| `ixp/e2e_04_build_mechanics.yaml` | IXP plugin is Flow-only; BPMN registry has no IXP node |
| `ixp/integration_handle_routing.yaml` | IXP plugin is Flow-only; BPMN registry has no IXP node |
| `ixp/routing.yaml` | IXP plugin is Flow-only; BPMN registry has no IXP node |
| `ixp/routing_listing.yaml` | IXP plugin is Flow-only; BPMN registry has no IXP node |
| `ixp/routing_negative.yaml` | IXP plugin is Flow-only; BPMN registry has no IXP node |
| `ixp/scaffold_minimal.yaml` | IXP plugin is Flow-only; BPMN registry has no IXP node |
| `ixp/scaffold_multinode.yaml` | IXP plugin is Flow-only; BPMN registry has no IXP node |
| `node_features/datafabric_native/integration_native_read_create.yaml` | native core.datafabric.* nodes are Flow-only; connector variant is covered by the DF connector ports |
| `smoke/inline_agent_robust.yaml` | inline agent is Flow-only; BPMN agents are published |
| `voice/voice_inbound_call.yaml` | voice nodes are Flow-only |
| `voice/voice_outbound_call.yaml` | voice nodes are Flow-only |
