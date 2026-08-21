# Evaluation Run Report

**Run ID**: `maestro-bpmn-baseline-sonnet-5`
**Date**: 2026-08-14 21:48:03
**Duration**: 2840.48s
**Model**: `claude-sonnet-5`

## Summary

- **Total Tasks**: 70
- **Succeeded**: 62
- **Failed**: 4
- **Errors**: 4
- **Success Rate**: 93.9%
- **Avg Reliability Score**: 0.888
- **Avg Generation Latency**: 408.8s
- **Total Assistant Turns**: 4403
- **Crashed Partials**: 4 (0 recovered, 4 terminal)

## Task Details

| Task ID | Status | Reliability Score | Latency | Model | Tags |
|---------|--------|-------------------|---------|-------|------|
| skill-bpmn-feet-inches | SUCCESS | 1.000 | 867.2s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node |
| skill-bpmn-registry-discovery | SUCCESS | 1.000 | 111.8s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:inspect, connector, feature:connections, resource |
| skill-bpmn-hitl-schema-design | ERROR | 0.000 | 909.6s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, feature:approval-gate |
| skill-bpmn-loop-multiply | SUCCESS | 1.000 | 704.4s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:loop |
| skill-bpmn-script-jint-guidance | SUCCESS | 1.000 | 755.3s | claude-sonnet-5 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:single-node, node:script |
| skill-bpmn-diagnose-stuck-gateway | SUCCESS | 1.000 | 68.8s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:diagnose, lifecycle:discover |
| skill-bpmn-e2e-customer-escalation | SUCCESS | 1.000 | 607.0s | claude-sonnet-5 | uipath-maestro-bpmn, e2e, mode:build, lifecycle:generate, shape:multi-node, node:decision, node:hitl, feature:escalation |
| skill-bpmn-inclusive-gateway-forkjoin | SUCCESS | 1.000 | 629.2s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, node:gateway |
| skill-bpmn-script-jint-lifecycle | SUCCESS | 1.000 | 324.5s | claude-sonnet-5 | uipath-maestro-bpmn, e2e, mode:build, lifecycle:generate, node:script, feature:jint |
| skill-bpmn-timer-boundary-noninterrupting | SUCCESS | 1.000 | 218.3s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate |
| skill-bpmn-subprocess | SUCCESS | 1.000 | 402.8s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:subflow |
| skill-bpmn-parallel-fork-join | SUCCESS | 1.000 | 74.0s | claude-sonnet-5 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:multi-node, node:gateway, feature:parallel-tasks |
| skill-bpmn-error-boundary-handler | SUCCESS | 1.000 | 221.6s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate |
| skill-bpmn-rpa-job | SUCCESS | 1.000 | 608.5s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:single-node, resource |
| skill-bpmn-operate-diagnose-minimal-fault-triage | SUCCESS | 1.000 | 122.3s | claude-sonnet-5 | uipath-maestro-bpmn, smoke, mode:diagnose, lifecycle:discover |
| skill-bpmn-hitl-completed-wired | SUCCESS | 1.000 | 904.3s | claude-sonnet-5 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:multi-node, node:hitl, feature:approval-gate |
| skill-bpmn-gateway-sequence-flows | SUCCESS | 1.000 | 839.4s | claude-sonnet-5 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:multi-node, node:gateway |
| skill-bpmn-diagnose-scoped-variables | SUCCESS | 1.000 | 65.0s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:diagnose, lifecycle:discover |
| skill-bpmn-dice-roller | SUCCESS | 1.000 | 160.1s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:decision |
| skill-bpmn-diagnose-deployed-drift | SUCCESS | 1.000 | 52.2s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:diagnose, lifecycle:discover |
| skill-bpmn-safety-sanitize | SUCCESS | 1.000 | 59.7s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate |
| skill-bpmn-debug-instance-inspect | SUCCESS | 1.000 | 80.5s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:diagnose, lifecycle:discover |
| skill-bpmn-e2e-wiki-pageviews | TIMEOUT | 0.000 | 909.9s | claude-sonnet-5 | uipath-maestro-bpmn, e2e, mode:build, lifecycle:generate, shape:multi-node, node:decision, node:transform |
| skill-bpmn-edit-group-to-subflow | ERROR | 0.000 | 908.6s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:subflow |
| skill-bpmn-debug-not-validation | SUCCESS | 1.000 | 72.8s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate |
| skill-bpmn-api-workflow-task | SUCCESS | 1.000 | 601.5s | claude-sonnet-5 | uipath-maestro-bpmn, e2e, mode:build, lifecycle:generate, node:service-task, feature:api-workflow |
| skill-bpmn-author-validate | SUCCESS | 1.000 | 273.5s | claude-sonnet-5 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate |
| skill-bpmn-expr-error-mapping | SUCCESS | 1.000 | 342.9s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate |
| skill-bpmn-expr-computed-js | SUCCESS | 1.000 | 575.7s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate |
| skill-bpmn-e2e-invoice-exception-triage | SUCCESS | 1.000 | 474.8s | claude-sonnet-5 | uipath-maestro-bpmn, e2e, mode:build, lifecycle:generate, shape:multi-node, node:decision, node:hitl, feature:approval-gate |
| skill-bpmn-callactivity-agentic-process | SUCCESS | 1.000 | 443.6s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, node:call-activity |
| skill-bpmn-script-task-filter | MAX_TURNS_EXHAUSTED | 0.000 | 449.1s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:single-node, node:script |
| skill-bpmn-multi-city-weather | SUCCESS | 1.000 | 631.3s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:loop |
| skill-bpmn-expr-multiinstance-iterator | ERROR | 0.000 | 909.7s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, node:loop |
| skill-bpmn-calculator | SUCCESS | 1.000 | 360.1s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:decision |
| skill-bpmn-edit-add-output | SUCCESS | 1.000 | 109.4s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node |
| skill-bpmn-business-rule-task | SUCCESS | 1.000 | 515.2s | claude-sonnet-5 | uipath-maestro-bpmn, e2e, mode:build, lifecycle:generate, node:business-rule, feature:orchestrator |
| skill-bpmn-script-task-map | SUCCESS | 1.000 | 296.3s | claude-sonnet-5 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:single-node, node:script |
| skill-bpmn-debug-workflow-mocked | SUCCESS | 1.000 | 41.3s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:operate, lifecycle:discover |
| skill-bpmn-edit-update-node | SUCCESS | 1.000 | 336.4s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node |
| skill-bpmn-terminate | SUCCESS | 1.000 | 87.3s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:terminate |
| skill-bpmn-edit-remove-node | SUCCESS | 1.000 | 205.0s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node |
| skill-bpmn-edit-add-node | SUCCESS | 1.000 | 196.5s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node |
| skill-bpmn-smoke-registry-discovery | SUCCESS | 1.000 | 44.4s | claude-sonnet-5 | uipath-maestro-bpmn, smoke, mode:build |
| skill-bpmn-hitl-result-downstream | SUCCESS | 1.000 | 634.0s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, node:decision, feature:approval-gate |
| skill-bpmn-queue-create-and-wait | SUCCESS | 1.000 | 501.9s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate |
| skill-bpmn-edit-move-node | SUCCESS | 1.000 | 106.3s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node |
| skill-bpmn-message-send-receive-pair | ERROR | 0.000 | 901.6s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, feature:trigger |
| skill-bpmn-diagnose-job-traces | SUCCESS | 1.000 | 72.0s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:diagnose, lifecycle:discover |
| skill-bpmn-hitl-multi-outcome-routing | SUCCESS | 1.000 | 223.3s | claude-sonnet-5 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:multi-node, node:hitl, node:decision, feature:approval-gate |
| skill-bpmn-diagnose-incident-root-cause | SUCCESS | 1.000 | 46.1s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:diagnose, lifecycle:discover |
| skill-bpmn-e2e-live-debug | SUCCESS | 1.000 | 380.2s | claude-sonnet-5 | uipath-maestro-bpmn, e2e, mode:operate, lifecycle:setup, path-to-ga |
| skill-bpmn-integration-service-boundary | FAILURE | 0.167 | 871.4s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, connector, feature:connections |
| skill-bpmn-diagnose-validate-fix-loop | SUCCESS | 1.000 | 28.1s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:diagnose, lifecycle:discover |
| skill-bpmn-timer-start | SUCCESS | 1.000 | 155.4s | claude-sonnet-5 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, feature:trigger |
| skill-bpmn-message-catch | SUCCESS | 1.000 | 141.6s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, feature:trigger |
| skill-bpmn-http-weather | SUCCESS | 1.000 | 674.6s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:single-node, feature:http |
| skill-bpmn-event-based-gateway | SUCCESS | 1.000 | 157.6s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, node:gateway |
| skill-bpmn-hitl-rpa-wrappers | SUCCESS | 1.000 | 139.4s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, resource |
| skill-bpmn-error-event-subprocess | SUCCESS | 1.000 | 216.1s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, node:subflow |
| skill-bpmn-timer | SUCCESS | 1.000 | 34.7s | claude-sonnet-5 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:single-node, feature:timer |
| skill-bpmn-event-trigger-start | SUCCESS | 1.000 | 260.0s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:single-node, connector, feature:trigger |
| skill-bpmn-agent-job | SUCCESS | 1.000 | 706.9s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:single-node, resource |
| skill-bpmn-script-task-group-by | SUCCESS | 1.000 | 342.8s | claude-sonnet-5 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:single-node, node:script |
| skill-bpmn-hitl-brownfield-insert | SUCCESS | 1.000 | 245.5s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, feature:approval-gate |
| skill-bpmn-switch | SUCCESS | 1.000 | 69.9s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:switch |
| skill-bpmn-simple-approval-bpmn | SUCCESS | 1.000 | 831.4s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:gateway, node:script, node:service-task, resource |
| skill-bpmn-contract-variant-wrappers | MAX_TURNS_EXHAUSTED | 0.000 | 2370.9s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, contract:xml, node:service-task, node:call-activity, connector |
| skill-bpmn-reading-list | SUCCESS | 1.000 | 400.0s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:transform |
| skill-bpmn-hitl-boolean-decision | SUCCESS | 1.000 | 531.5s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, node:decision, feature:approval-gate |

## Run-time Notes

> **WARNING:** [skill-bpmn-feet-inches] expected_turns exceeded: 60/22 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-hitl-schema-design] expected_turns exceeded: 35/22 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-loop-multiply] expected_turns exceeded: 61/22 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-script-jint-guidance] max_turns exhausted
> **WARNING:** [skill-bpmn-script-jint-guidance] expected_turns exceeded: 72/15 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-e2e-customer-escalation] expected_turns exceeded: 65/28 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-inclusive-gateway-forkjoin] expected_turns exceeded: 36/20 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-script-jint-lifecycle] expected_turns exceeded: 34/22 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-subprocess] expected_turns exceeded: 33/22 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-error-boundary-handler] expected_turns exceeded: 21/18 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-rpa-job] expected_turns exceeded: 40/16 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-hitl-completed-wired] expected_turns exceeded: 59/18 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-gateway-sequence-flows] expected_turns exceeded: 41/21 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-edit-group-to-subflow] expected_turns exceeded: 68/26 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-api-workflow-task] max_turns exhausted
> **WARNING:** [skill-bpmn-api-workflow-task] expected_turns exceeded: 61/32 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-author-validate] expected_turns exceeded: 22/20 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-expr-error-mapping] expected_turns exceeded: 25/18 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-expr-computed-js] expected_turns exceeded: 57/18 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-e2e-invoice-exception-triage] max_turns exhausted
> **WARNING:** [skill-bpmn-e2e-invoice-exception-triage] expected_turns exceeded: 51/25 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-callactivity-agentic-process] expected_turns exceeded: 47/18 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-script-task-filter] max_turns exhausted
> **WARNING:** [skill-bpmn-script-task-filter] expected_turns exceeded: 70/20 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-multi-city-weather] expected_turns exceeded: 56/22 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-expr-multiinstance-iterator] expected_turns exceeded: 89/20 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-calculator] expected_turns exceeded: 38/22 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-business-rule-task] max_turns exhausted
> **WARNING:** [skill-bpmn-business-rule-task] expected_turns exceeded: 58/28 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-script-task-map] expected_turns exceeded: 45/20 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-edit-update-node] expected_turns exceeded: 23/14 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-hitl-result-downstream] expected_turns exceeded: 28/24 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-queue-create-and-wait] expected_turns exceeded: 42/18 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-message-send-receive-pair] expected_turns exceeded: 70/20 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-e2e-live-debug] expected_turns exceeded: 64/30 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-integration-service-boundary] expected_turns exceeded: 58/19 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-timer-start] expected_turns exceeded: 28/18 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-message-catch] expected_turns exceeded: 17/16 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-http-weather] expected_turns exceeded: 84/16 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-hitl-rpa-wrappers] expected_turns exceeded: 21/14 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-event-trigger-start] expected_turns exceeded: 40/16 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-agent-job] expected_turns exceeded: 77/16 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-script-task-group-by] expected_turns exceeded: 44/20 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-hitl-brownfield-insert] expected_turns exceeded: 27/22 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-simple-approval-bpmn] expected_turns exceeded: 77/24 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-contract-variant-wrappers] max_turns exhausted
> **WARNING:** [skill-bpmn-contract-variant-wrappers] expected_turns exceeded: 93/20 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-reading-list] expected_turns exceeded: 40/22 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-hitl-boolean-decision] expected_turns exceeded: 38/24 (cumulative SDK turns)


## Generation Metrics

| Task ID | Total Latency | Turns | Asst Turns | Avg Turn Latency |
|---------|---------------|-------|------------|------------------|
| skill-bpmn-feet-inches | 867.2s | 1 | 110 | 858.2s |
| skill-bpmn-registry-discovery | 111.8s | 1 | 30 | 103.4s |
| skill-bpmn-hitl-schema-design | 909.6s | 1 | 67 | 900.0s |
| skill-bpmn-loop-multiply | 704.4s | 1 | 107 | 694.9s |
| skill-bpmn-script-jint-guidance | 755.3s | 1 | 121 | 745.6s |
| skill-bpmn-diagnose-stuck-gateway | 68.8s | 1 | 17 | 60.2s |
| skill-bpmn-e2e-customer-escalation | 607.0s | 1 | 117 | 588.3s |
| skill-bpmn-inclusive-gateway-forkjoin | 629.2s | 1 | 72 | 620.4s |
| skill-bpmn-script-jint-lifecycle | 324.5s | 1 | 61 | 315.2s |
| skill-bpmn-timer-boundary-noninterrupting | 218.3s | 1 | 29 | 209.2s |
| skill-bpmn-subprocess | 402.8s | 1 | 66 | 387.8s |
| skill-bpmn-parallel-fork-join | 74.0s | 1 | 15 | 65.5s |
| skill-bpmn-error-boundary-handler | 221.6s | 1 | 37 | 211.3s |
| skill-bpmn-rpa-job | 608.5s | 1 | 76 | 598.9s |
| skill-bpmn-operate-diagnose-minimal-fault-triage | 122.3s | 1 | 20 | 105.9s |
| skill-bpmn-hitl-completed-wired | 904.3s | 1 | 108 | 894.7s |
| skill-bpmn-gateway-sequence-flows | 839.4s | 1 | 76 | 830.7s |
| skill-bpmn-diagnose-scoped-variables | 65.0s | 1 | 17 | 55.4s |
| skill-bpmn-dice-roller | 160.1s | 1 | 38 | 150.2s |
| skill-bpmn-diagnose-deployed-drift | 52.2s | 1 | 10 | 43.0s |
| skill-bpmn-safety-sanitize | 59.7s | 1 | 15 | 49.6s |
| skill-bpmn-debug-instance-inspect | 80.5s | 1 | 27 | 71.2s |
| skill-bpmn-e2e-wiki-pageviews | 909.9s | 0 | 0 | N/A |
| skill-bpmn-edit-group-to-subflow | 908.6s | 1 | 136 | 900.0s |
| skill-bpmn-debug-not-validation | 72.8s | 1 | 17 | 63.6s |
| skill-bpmn-api-workflow-task | 601.5s | 1 | 102 | 592.2s |
| skill-bpmn-author-validate | 273.5s | 1 | 43 | 263.7s |
| skill-bpmn-expr-error-mapping | 342.9s | 1 | 45 | 334.2s |
| skill-bpmn-expr-computed-js | 575.7s | 1 | 104 | 567.0s |
| skill-bpmn-e2e-invoice-exception-triage | 474.8s | 1 | 85 | 458.8s |
| skill-bpmn-callactivity-agentic-process | 443.6s | 1 | 90 | 433.8s |
| skill-bpmn-script-task-filter | 449.1s | 1 | 122 | 439.4s |
| skill-bpmn-multi-city-weather | 631.3s | 1 | 92 | 621.4s |
| skill-bpmn-expr-multiinstance-iterator | 909.7s | 1 | 145 | 900.0s |
| skill-bpmn-calculator | 360.1s | 1 | 69 | 351.2s |
| skill-bpmn-edit-add-output | 109.4s | 1 | 26 | 106.6s |
| skill-bpmn-business-rule-task | 515.2s | 1 | 94 | 513.0s |
| skill-bpmn-script-task-map | 296.3s | 1 | 85 | 294.7s |
| skill-bpmn-debug-workflow-mocked | 41.3s | 1 | 15 | 39.7s |
| skill-bpmn-edit-update-node | 336.4s | 1 | 45 | 334.5s |
| skill-bpmn-terminate | 87.3s | 1 | 17 | 80.3s |
| skill-bpmn-edit-remove-node | 205.0s | 1 | 35 | 203.3s |
| skill-bpmn-edit-add-node | 196.5s | 1 | 28 | 195.0s |
| skill-bpmn-smoke-registry-discovery | 44.4s | 1 | 16 | 42.9s |
| skill-bpmn-hitl-result-downstream | 634.0s | 1 | 50 | 632.5s |
| skill-bpmn-queue-create-and-wait | 501.9s | 1 | 79 | 500.5s |
| skill-bpmn-edit-move-node | 106.3s | 1 | 20 | 104.8s |
| skill-bpmn-message-send-receive-pair | 901.6s | 1 | 133 | 900.0s |
| skill-bpmn-diagnose-job-traces | 72.0s | 1 | 22 | 70.3s |
| skill-bpmn-hitl-multi-outcome-routing | 223.3s | 1 | 37 | 221.9s |
| skill-bpmn-diagnose-incident-root-cause | 46.1s | 1 | 17 | 44.6s |
| skill-bpmn-e2e-live-debug | 380.2s | 1 | 121 | 378.6s |
| skill-bpmn-integration-service-boundary | 871.4s | 1 | 101 | 869.8s |
| skill-bpmn-diagnose-validate-fix-loop | 28.1s | 1 | 9 | 25.3s |
| skill-bpmn-timer-start | 155.4s | 1 | 46 | 153.8s |
| skill-bpmn-message-catch | 141.6s | 1 | 31 | 140.0s |
| skill-bpmn-http-weather | 674.6s | 1 | 155 | 673.1s |
| skill-bpmn-event-based-gateway | 157.6s | 1 | 29 | 156.1s |
| skill-bpmn-hitl-rpa-wrappers | 139.4s | 1 | 41 | 137.8s |
| skill-bpmn-error-event-subprocess | 216.1s | 1 | 26 | 214.6s |
| skill-bpmn-timer | 34.7s | 1 | 9 | 33.2s |
| skill-bpmn-event-trigger-start | 260.0s | 1 | 74 | 249.4s |
| skill-bpmn-agent-job | 706.9s | 1 | 127 | 705.5s |
| skill-bpmn-script-task-group-by | 342.8s | 1 | 85 | 341.4s |
| skill-bpmn-hitl-brownfield-insert | 245.5s | 1 | 51 | 243.9s |
| skill-bpmn-switch | 69.9s | 1 | 15 | 63.8s |
| skill-bpmn-simple-approval-bpmn | 831.4s | 1 | 144 | 829.8s |
| skill-bpmn-contract-variant-wrappers | 2370.9s | 1 | 183 | 2368.9s |
| skill-bpmn-reading-list | 400.0s | 1 | 75 | 398.5s |
| skill-bpmn-hitl-boolean-decision | 531.5s | 1 | 76 | 530.0s |


## Token Usage

**Total Tokens**: 190,105,976 (input: 11,279, output: 2,259,592)
**Cache Tokens**: write: 5,421,254, read: 182,413,851
**Total Cost**: $108.9816
**Avg Tokens/Task**: 2,755,159

| Task ID | Input (uncached) | Output | Cache Write | Cache Read | Total | Cost |
|---------|------------------|--------|-------------|------------|-------|------|
| skill-bpmn-feet-inches | 102 | 66,364 | 116,080 | 4,744,067 | 4,926,613 | $2.8543 |
| skill-bpmn-registry-discovery | 36 | 5,230 | 63,508 | 909,249 | 978,023 | $0.5895 |
| skill-bpmn-hitl-schema-design | 64 | 68,917 | 95,906 | 2,798,329 | 2,963,216 | $2.2331 |
| skill-bpmn-loop-multiply | 98 | 57,391 | 101,312 | 4,957,587 | 5,116,388 | $2.7284 |
| skill-bpmn-script-jint-guidance | 102 | 63,697 | 135,363 | 5,371,021 | 5,570,183 | $3.0747 |
| skill-bpmn-diagnose-stuck-gateway | 16 | 3,817 | 61,032 | 380,165 | 445,030 | $0.4002 |
| skill-bpmn-e2e-customer-escalation | 102 | 49,582 | 140,402 | 6,158,701 | 6,348,787 | $3.1182 |
| skill-bpmn-inclusive-gateway-forkjoin | 70 | 55,496 | 99,377 | 2,675,001 | 2,829,944 | $2.0078 |
| skill-bpmn-script-jint-lifecycle | 2,299 | 25,623 | 103,966 | 2,556,465 | 2,688,353 | $1.5481 |
| skill-bpmn-timer-boundary-noninterrupting | 26 | 15,811 | 56,772 | 894,442 | 967,051 | $0.7185 |
| skill-bpmn-subprocess | 66 | 32,071 | 88,429 | 2,432,283 | 2,552,849 | $1.5426 |
| skill-bpmn-parallel-fork-join | 15 | 5,208 | 68,008 | 421,819 | 495,050 | $0.4597 |
| skill-bpmn-error-boundary-handler | 42 | 16,337 | 55,826 | 1,346,221 | 1,418,426 | $0.8584 |
| skill-bpmn-rpa-job | 72 | 50,203 | 66,697 | 2,847,164 | 2,964,136 | $1.8575 |
| skill-bpmn-operate-diagnose-minimal-fault-triage | 22 | 6,641 | 27,593 | 571,653 | 605,909 | $0.3747 |
| skill-bpmn-hitl-completed-wired | 98 | 77,093 | 156,941 | 5,629,157 | 5,863,289 | $3.4340 |
| skill-bpmn-gateway-sequence-flows | 66 | 81,935 | 134,458 | 3,092,987 | 3,309,446 | $2.6613 |
| skill-bpmn-diagnose-scoped-variables | 16 | 3,384 | 26,470 | 403,097 | 432,967 | $0.2710 |
| skill-bpmn-dice-roller | 34 | 10,653 | 47,448 | 1,145,693 | 1,203,828 | $0.6815 |
| skill-bpmn-diagnose-deployed-drift | 10 | 2,640 | 55,780 | 202,623 | 261,053 | $0.3096 |
| skill-bpmn-safety-sanitize | 12 | 3,211 | 55,389 | 257,472 | 316,084 | $0.3332 |
| skill-bpmn-debug-instance-inspect | 28 | 3,588 | 59,806 | 714,046 | 777,468 | $0.4924 |
| skill-bpmn-edit-group-to-subflow | 136 | 73,868 | 121,158 | 5,626,759 | 5,821,921 | $3.2508 |
| skill-bpmn-debug-not-validation | 18 | 4,491 | 69,088 | 490,801 | 564,398 | $0.4737 |
| skill-bpmn-api-workflow-task | 1,721 | 51,991 | 153,957 | 4,187,331 | 4,395,000 | $2.6186 |
| skill-bpmn-author-validate | 44 | 21,189 | 56,614 | 1,582,264 | 1,660,111 | $1.0049 |
| skill-bpmn-expr-error-mapping | 42 | 28,801 | 94,823 | 1,622,958 | 1,746,624 | $1.2746 |
| skill-bpmn-expr-computed-js | 94 | 44,111 | 160,520 | 5,154,066 | 5,358,791 | $2.8101 |
| skill-bpmn-e2e-invoice-exception-triage | 68 | 40,520 | 117,025 | 3,004,437 | 3,162,050 | $1.9482 |
| skill-bpmn-callactivity-agentic-process | 94 | 33,079 | 72,717 | 3,881,430 | 3,987,320 | $1.9336 |
| skill-bpmn-script-task-filter | 110 | 30,170 | 115,652 | 4,521,902 | 4,667,834 | $2.2431 |
| skill-bpmn-multi-city-weather | 76 | 39,617 | 98,852 | 3,551,354 | 3,689,899 | $2.0306 |
| skill-bpmn-expr-multiinstance-iterator | 108 | 76,781 | 139,468 | 5,360,495 | 5,576,852 | $3.2832 |
| skill-bpmn-calculator | 66 | 29,718 | 122,436 | 2,948,035 | 3,100,255 | $1.7895 |
| skill-bpmn-edit-add-output | 26 | 8,254 | 43,314 | 744,619 | 796,213 | $0.5097 |
| skill-bpmn-business-rule-task | 1,060 | 35,246 | 87,639 | 3,377,428 | 3,501,373 | $1.8737 |
| skill-bpmn-script-task-map | 82 | 20,067 | 94,238 | 3,501,052 | 3,615,439 | $1.7050 |
| skill-bpmn-debug-workflow-mocked | 18 | 2,039 | 25,216 | 454,922 | 482,195 | $0.2617 |
| skill-bpmn-edit-update-node | 45 | 25,760 | 36,587 | 1,318,870 | 1,381,262 | $0.9194 |
| skill-bpmn-terminate | 18 | 6,289 | 37,261 | 519,329 | 562,897 | $0.3899 |
| skill-bpmn-edit-remove-node | 34 | 18,014 | 41,119 | 984,594 | 1,043,761 | $0.7199 |
| skill-bpmn-edit-add-node | 28 | 17,640 | 32,380 | 765,608 | 815,656 | $0.6158 |
| skill-bpmn-smoke-registry-discovery | 18 | 2,396 | 24,504 | 436,282 | 463,200 | $0.2588 |
| skill-bpmn-hitl-result-downstream | 48 | 58,676 | 72,548 | 1,907,203 | 2,038,475 | $1.7245 |
| skill-bpmn-queue-create-and-wait | 82 | 41,380 | 89,636 | 3,800,265 | 3,931,363 | $2.0972 |
| skill-bpmn-edit-move-node | 20 | 10,141 | 31,073 | 520,026 | 561,260 | $0.4247 |
| skill-bpmn-message-send-receive-pair | 140 | 73,171 | 108,397 | 7,196,197 | 7,377,905 | $3.6633 |
| skill-bpmn-diagnose-job-traces | 24 | 4,423 | 26,924 | 629,442 | 660,813 | $0.3562 |
| skill-bpmn-hitl-multi-outcome-routing | 34 | 21,390 | 67,038 | 1,313,839 | 1,402,301 | $0.9665 |
| skill-bpmn-diagnose-incident-root-cause | 16 | 3,174 | 26,945 | 404,586 | 434,721 | $0.2701 |
| skill-bpmn-e2e-live-debug | 116 | 20,893 | 81,804 | 5,231,001 | 5,333,814 | $2.1898 |
| skill-bpmn-integration-service-boundary | 90 | 76,491 | 99,388 | 4,353,600 | 4,529,569 | $2.8264 |
| skill-bpmn-diagnose-validate-fix-loop | 10 | 1,528 | 22,464 | 231,728 | 255,730 | $0.1767 |
| skill-bpmn-timer-start | 42 | 11,780 | 54,297 | 1,429,240 | 1,495,359 | $0.8092 |
| skill-bpmn-message-catch | 34 | 10,472 | 53,365 | 1,129,716 | 1,193,587 | $0.6962 |
| skill-bpmn-http-weather | 152 | 57,921 | 175,223 | 6,939,198 | 7,172,494 | $3.6081 |
| skill-bpmn-event-based-gateway | 30 | 13,697 | 54,671 | 979,050 | 1,047,448 | $0.7043 |
| skill-bpmn-hitl-rpa-wrappers | 42 | 9,867 | 59,526 | 1,404,232 | 1,473,667 | $0.7926 |
| skill-bpmn-error-event-subprocess | 28 | 18,820 | 45,976 | 891,269 | 956,093 | $0.7222 |
| skill-bpmn-timer | 10 | 2,657 | 33,431 | 253,051 | 289,149 | $0.2412 |
| skill-bpmn-event-trigger-start | 80 | 15,781 | 59,075 | 2,856,557 | 2,931,493 | $1.3155 |
| skill-bpmn-agent-job | 112 | 61,984 | 108,927 | 5,872,433 | 6,043,456 | $3.1003 |
| skill-bpmn-script-task-group-by | 88 | 23,936 | 62,777 | 3,096,437 | 3,183,238 | $1.5236 |
| skill-bpmn-hitl-brownfield-insert | 54 | 19,979 | 52,351 | 1,729,618 | 1,802,002 | $1.0150 |
| skill-bpmn-switch | 16 | 5,730 | 36,959 | 456,340 | 499,045 | $0.3615 |
| skill-bpmn-simple-approval-bpmn | 2,387 | 69,566 | 109,316 | 8,022,032 | 8,203,301 | $3.8672 |
| skill-bpmn-contract-variant-wrappers | 180 | 231,002 | 127,454 | 10,400,402 | 10,759,038 | $7.0636 |
| skill-bpmn-reading-list | 66 | 34,040 | 94,791 | 3,160,410 | 3,289,307 | $1.8144 |
| skill-bpmn-hitl-boolean-decision | 76 | 46,160 | 105,767 | 3,662,201 | 3,814,204 | $2.1879 |


## Command Telemetry

**Total Commands**: 2356
**Success Rate**: 2287/2356 (97.1%)

### Commands by Tool

| Tool | Count | % |
|------|-------|---|
| Bash | 1669 | 70.8% |
| Read | 293 | 12.4% |
| Grep | 167 | 7.1% |
| Write | 98 | 4.2% |
| Skill | 69 | 2.9% |
| Edit | 47 | 2.0% |
| TaskUpdate | 4 | 0.2% |
| TaskCreate | 3 | 0.1% |
| TaskStop | 2 | 0.1% |
| Glob | 2 | 0.1% |
| Agent | 1 | 0.0% |
| TaskOutput | 1 | 0.0% |

### Performance

- **Average Command Time**: 676.6ms
- **Total Command Time**: 1594.12s

### Slowest Commands

| Tool | Duration | Parameters |
|------|----------|------------|
| Bash | 120267ms | {'command': 'grep -rln "entryPointId" /home/azureu... |
| Bash | 120231ms | {'command': 'grep -rln "Actions.HITL" ~/projects/s... |
| Bash | 120088ms | {'command': 'grep -rn "aggregate" /home/azureuser/... |
| Bash | 94290ms | {'command': 'grep -rn "uipath:entryPointId" /home/... |
| Bash | 81919ms | {'command': 'find / -iname "*.bpmn" 2>/dev/null | ... |

**Most Common Pattern**: `Bash → Bash → Bash`

**Skill Tool Invoked**: 69 time(s)

## Agent Settings

- **Permission Mode**: acceptEdits
- **Allowed Tools**: Skill, Bash, Read, Write, Edit, Glob, Grep
- **Model**: us.anthropic.claude-sonnet-5
- **Max Turns**: 75
- **System Prompt**: You are a coding agent. Do not access files in sibling runs/* directories. Everywhere else is permitted. 
- **Plugins**: /home/azureuser/projects/skills

## Environment

- **git_commit**: acc1c86
- **skills_git_commit**: 7355bf6d0
- **cli_version**: 1.201.0-dev.8272
- **tool_plugins**: {'admin-tool': '1.201.0-dev.8272', 'agent-tool': '1.201.0-dev.8272', 'agenthub-tool': '1.201.0-dev.8272', 'aops-tool': '1.201.0-dev.8272', 'api-workflow-tool': '1.201.0-dev.8272', 'automation-hub-tool': '1.201.0-dev.8272', 'codedagent-tool': '1.201.0-dev.8272', 'codedapp-tool': '1.201.0-dev.8272', 'coder-tool': '1.201.0-dev.8272', 'context-grounding-tool': '1.201.0-dev.8272', 'conversational-tool': '1.201.0-dev.8272', 'data-fabric-tool': '1.201.0-dev.8272', 'docsai-tool': '1.201.0-dev.8272', 'function-tool': '1.201.0-dev.8272', 'gov-tool': '1.201.0-dev.8272', 'guardrails-tool': '1.201.0-dev.8272', 'insights-tool': '1.201.0-dev.8276', 'integrationservice-tool': '1.201.0-dev.8272', 'ixp-tool': '1.201.0-dev.8272', 'llm-gateway-tool': '1.201.0-dev.8272', 'llmgw-tool': '1.201.0-dev.8272', 'maestro-tool': '1.201.0-dev.8275', 'model-hub-tool': '1.201.0-dev.8272', 'orchestrator-tool': '1.201.0-dev.8272', 'platform-tool': '1.201.0-dev.8272', 'pm-tool': '1.201.0-dev.8272', 'rpa-legacy-tool': '1.201.0-dev.8272', 'rpa-tool': '1.201.0-dev.20260809.3', 'solution-tool': '1.201.0-dev.8272', 'tasks-tool': '1.201.0-dev.8272', 'test-manager-tool': '1.201.0-dev.8272', 'traces-tool': '1.201.0-dev.8272', 'vertical-solutions-tool': '1.201.0-dev.8272'}
- **coder_eval**: 0.8.8
- **claude_code_cli**: 2.1.233 (Claude Code)
- **uv**: uv 0.11.21 (x86_64-unknown-linux-gnu)
- **anthropic**: 0.102.0
- **openai**: Not Installed
- **pydantic**: 2.12.5