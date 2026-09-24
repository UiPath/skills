# Flow → BPMN eval parity map

## Porting ledger

One row per task, final state. Iterations are summarised in the notes; runs are GitHub Actions `run-coder-eval.yml` ids on the alpha tenant, codex driver. Structural rows landed in PR #3426; live and field-shape rows are PR #3502; parked rows live on branch `test/bpmn-port-parked` (stacked on #3502), each with `skip: true` and its evidence in the YAML.

### Structural (PR #3426)

| Flow task | BPMN port | Final | Notes |
|---|---|---|---|
| `connector_features/drive_to_slack.yaml` | `connector_features/drive_to_slack/` | PASS (run 35484984200) | pilot |
| `…/datafabric_connector/smoke_create_all_types.yaml` | `…/smoke_create_all_types/` | PASS it.2 (run 35489744689) | grader widened to the generic entity-CRUD form |
| `…/datafabric_connector/integration_create_get.yaml` | `…/integration_create_get/` | PASS it.2 (run 35489744689) | same |
| `…/datafabric_connector/contractregistry_crud_filters.yaml` | `…/contractregistry_crud_filters/` | PASS it.2 (run 35489744689) | same, plus transitive output mapping |
| `…/datafabric_connector/smoke_query.yaml` | `…/smoke_query/` | SKIPPED, surface gap | passed it.3 (run 35490499651) only via an invented `sortField` input; the curated Query Entity Records template has no sort-field parameter (only `isAscending`), so the "sorted by score" criterion has no carrier. Two smoke-gate runs (35674400362) confirmed. |
| `…/datafabric_connector/smoke_update.yaml` | `…/smoke_update/` | PASS (run 36056004092) | earlier PASS (run 35499789502) |
| `…/datafabric_connector/smoke_file_activities.yaml` | `…/smoke_file_activities/` | PASS (run 36056004092) | earlier PASS (run 35499789502) |
| `…/datafabric_connector/e2e_contract_intake_pipeline.yaml` | `…/e2e_contract_intake_pipeline/` | PASS (run 36056004092) | earlier PASS (run 35499789502) |
| `…/datafabric_connector/trigger_lifecycle.yaml` | `…/trigger_lifecycle/` | PASS it.3 (run 35501830119) | it.1 agent omitted the entity parameter; it.2 grader required messageEventDefinition as a direct child |
| `…/datafabric_connector/smoke_update_existing_flow.yaml` | `…/smoke_update_existing_flow/` | PASS (run 35500726138) | brownfield scaffold via `bpmn init` |
| `connector_features/testmanager_{testcase,testset,requirement}_lifecycle`, `testmanager_{attachments,execution_results,generic_records}` | same names | PASS (runs 35488848026, 35499789502) | Flow's `skip: true` not carried over |
| `connector_features/non-catalog-http-fallback/…` | `connector_features/non_catalog_http_fallback/` | PASS (run 35500726138) | grader now ActivityExecution-only (#3476) |
| `single_node/outlook_waitfor_email/…` | same | PASS (run 36056004092) | earlier PASS (run 35500726138) |
| `single_node/outlook_trigger_inbox/…` | same | PASS it.2 (run 35501830119) | it.1 agent omitted `parentFolderId`; `uip is triggers` advisory stays 0 |
| `e2e/devcon_expense_approval.yaml` | `e2e/devcon_expense_approval/` | SKIPPED, platform gap (0.885 it.3, run 35503094182) | every HITL assertion passes; `validate` needs a deployed Action App for Actions.HITL |
| `interactive/customer_escalation_simulated/…` | same | PASS 0.94 (run 35501830119) | advisory name check missed, as in Flow |
| `interactive/expense_approval_simulated/…` | same | SKIPPED, platform gap (0.70) | same Action App gap |
| `interactive/hitl_schema_design_simulated/…` | same | SKIPPED, platform gap (0.68) | same Action App gap |
| `interactive/solution_select.yaml` | `interactive/solution_select/` | SKIPPED, skill gap (0.46, run 35538478362) | no "existing solutions → ask" greenfield rule; agent auto-scaffolds |
| `connector_trigger/trigger_with_filter.yaml` | — | not ported | no structured trigger-filter carrier on `Intsvc.EventTrigger` |

### Live and field-shape (PR #3502)

Final is the latest run after the review fixes; each row's earlier result is kept in its notes.

| Flow task | BPMN port | Final | Notes |
|---|---|---|---|
| `e2e/jira_get_issue/…` | same | PASS (run 36056004092) | earlier PASS (run 35501830119); live pilot: ephemeral solution + `bpmn debug` + `variables-all` |
| `e2e/jira_create_issue/…` | same | PASS (run 36056004092) | earlier PASS (run 35503094182) |
| `e2e/escalation_jira_ticket/…` | same | PASS (run 36056004092) | earlier PASS (run 35503094182) |
| `e2e/escalation_orchestrator_paths/…` | same | PASS (run 36058708886) | earlier PASS (run 35503094182); 7 debug runs |
| `e2e/escalation_slack_alert/…` | same | FAIL (runs 36053143338, 36056004092) | after the review fixes the Slack step faulted at runtime in both runs (102010 `folderKey` in the first); earlier PASS it.2 (run 35524004307); it.1 agent omitted the Slack `folderKey` binding (102010) |
| `multi_node/slack_channel_description/…` | same | PASS (run 36056004092) | earlier PASS it.2 (run 35525387843); it.1 agent omitted the channel parameter |
| `connector_features/datafabric_connector/smoke_error.yaml` | `…/smoke_error/` | PASS (run 36056004092) | earlier PASS (run 35538279757); structural |
| `connector_features/generic_dynamic_node/…` | same | PASS (run 36056004092) | earlier PASS (run 35538279757) |
| `connector_features/jdbc_databricks_query/…` | same | PASS (run 36056004092) | earlier PASS (run 35538279757); structural |
| `connector_features/slack-http-fallback/…` | `connector_features/slack_http_fallback/` | PASS (run 36056004092) | earlier PASS (run 35783045540); it.1 grader wanted `emoji.list`; the connector's generic resource is `emoji_list_GET` |
| `connector_trigger/webhook_waitfor_parallel.yaml` | same | PASS (run 36053143338) | run 36056004092 failed on an agent-written `<bpmn:ReceiveTask>` (invalid tag); earlier PASS (run 35783045540); it.1 grader classified the wait by BPMN tag; agent emits `intermediateCatchEvent` + `Intsvc.WaitForEvent` and `Intsvc.UnifiedHttpRequest` |
| `connector_features/testmanager_crud_grounded/…` | same | SKIPPED, as in Flow | grades an agent-written `result.json`; unskip once it grades the live run |
| `interactive/cli_dice_roller_simulated/…` | same | PASS (run 36056004092) | earlier PASS (run 35783045540) |
| `multi_node/billing_invoice_lookup/…` | same | PASS (run 36056004092) | earlier PASS (run 35785806030); it.1 grader read its own ephemeral live solution as a second project; run 35783045540 was a platform 504 |
| `multi_node/slack_weather_pipeline/…` | same | PASS (run 36056004092) | earlier PASS it.3 (run 35785806030); it.1 channel not found, it.2 wrong Slack connection bound (401); Flow passes 6/12 nightlies |
| `connector_features/enum.yaml` | `connector_features/enum/` | PASS (run 36056004092) | earlier PASS (run 35789221753) |
| `connector_features/query_params.yaml` | `connector_features/query_params/` | PASS (run 36056004092) | earlier PASS (run 35789221753) |
| `connector_features/multiselect.yaml` | `connector_features/multiselect/` | PASS (run 36056004092) | earlier PASS (run 35789221753) |
| `connector_features/searchable_joins.yaml` | `connector_features/searchable_joins/` | PASS (run 36056004092) | earlier PASS (run 35789221753) |
| `connector_features/complex_array.yaml` | `connector_features/complex_array/` | PASS 0.875 (run 36056004092) | earlier PASS 0.875 (run 35789221753); only the advisory resolved-user-id check missed; Flow fully passes 3/12 |
| `connector_features/path_params.yaml` | `connector_features/path_params/` | PASS (run 36056004092) | earlier PASS it.2 (run 35790934047); it.1 agent left the issue key as an unbound variable |
| `connector_features/paginated_reference_lookup.yaml` | `connector_features/paginated_reference_lookup/` | FAIL (runs 36053143338, 36056004092) | after the review fixes the agent never resolved the channel id in either run; earlier PASS it.3 (run 35791969905); it.1 channel by name, no pagination; it.2 channel id with its last character dropped |

### Parked (branch `test/bpmn-port-parked`, all `skip: true`)

| Flow task | BPMN port | Evidence |
|---|---|---|
| `multi_node/bellevue_weather/…` | same | runs 35523787101, 35525387843: script reads `temperature_2m` off an undefined `Intsvc.HttpExecution` response; response shape not taught |
| `interactive/bellevue_weather_simulated/…` | same | run 35785806030: same fault; run 35783045540 was a harness stop on turn 1 |
| `e2e/jira_search_triage/…` | same | run 35525387843: 400008, multi-instance over a connector response does not evaluate |
| `e2e/jira_lifecycle/…` | same | three different runtime failures (runs 35503094182, 35524004307, 35525387843); Flow flaky (0.82 typical) |
| `multi_node/billing_discrepancy_detector/…` | same | runs 35538279757, 35783045540: two different malformed Data Service where clauses built from a process variable |
| `interactive/slack_channel_description_simulated/…` | same | run 35789221753: page 1 of conversations only, target channel never appears; it.2 (run 35785806030) was a grader defect since fixed; Flow fully passes 4/12 |
| `connector_features/ceql_where.yaml` | `connector_features/ceql_where/` | runs 35783045540, 35785806030: agent writes the connector's CEQL `where` string, never Flow's numeric-groupOperator tree; no BPMN carrier |
| `connector_features/enhanced_enum.yaml` | `connector_features/enhanced_enum/` | runs 35789221753, 35790934047: no WooCommerce connector node produced |

## Initial classification (2026-09-19)

The buckets the ports were chosen from. The ledger above supersedes a row once its task is ported or parked.

### Ported 1:1 (21)

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
| `interactive/customer_escalation_triage/customer_escalation_triage.yaml` | e2e/customer_escalation_triage (live) |
| `multi_node/calculator/calculator.yaml` | multi_node/calculator (structural only; Flow is live) |
| `multi_node/customer_escalation/customer_escalation.yaml` | multi_node/customer_escalation |
| `multi_node/dice_roller/dice_roller.yaml` | multi_node/dice_roller (structural only; Flow is live) |
| `multi_node/feet_inches/feet_inches.yaml` | multi_node/feet_inches (structural only; Flow is live) |
| `multi_node/loop_multiply/loop_multiply.yaml` | multi_node/loop_multiply (structural only; Flow is live) |
| `multi_node/multi_city_weather/multi_city_weather.yaml` | multi_node/multi_city_weather (structural only; Flow is live) |
| `multi_node/reading_list/reading_list.yaml` | multi_node/reading_list (structural only; Flow is live) |
| `multi_node/wiki_pageviews/wiki_pageviews.yaml` | multi_node/wiki_pageviews (structural only; Flow is live) |

### Covered by an equivalent BPMN task (18)

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

### Portable — structural (authoring + validate) (29)

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
| `connector_features/slack-http-fallback/slack_http_fallback.yaml` | connector-mode HTTP fallback (Intsvc.ActivityExecution on Slack connection) |
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

### Portable — live (bpmn debug + tenant re-read) (17)

| Flow task | BPMN target / note |
|---|---|
| `connector_features/datafabric_connector/smoke_error.yaml` | live 4xx on missing entity; debug + incidents |
| `connector_features/generic_dynamic_node/generic_dynamic_node.yaml` | generic activity + --object-name at registry get; live |
| `connector_features/jdbc_databricks_query/jdbc_databricks_query.yaml` | JDBC ActivityExecution; live |
| `connector_features/testmanager_crud_grounded/testmanager_crud_grounded.yaml` | Test Manager create+get round trip; live debug |
| `connector_trigger/webhook_waitfor_parallel.yaml` | parallelGateway + Intsvc.WaitForEvent (webhook) + HttpExecution self-trigger; live debug |
| `e2e/escalation_jira_ticket/escalation_jira_ticket.yaml` | sibling of the live escalation port; reuse escalation_is.py |
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

### Portable pending a feasibility probe (16)

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

### Not portable (Flow-only surface) (30)

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
