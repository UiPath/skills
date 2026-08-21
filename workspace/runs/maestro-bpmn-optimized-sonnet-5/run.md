# Evaluation Run Report

**Run ID**: `maestro-bpmn-optimized-sonnet-5-new`
**Date**: 2026-08-20 21:05:19
**Duration**: 2630.70s
**Model**: `claude-sonnet-5`

## Summary

- **Total Tasks**: 70
- **Succeeded**: 60
- **Failed**: 7
- **Errors**: 3
- **Pass Rate**: 85.7% (60/70)
- **Error Share**: 4.3% of tasks never produced a gradeable attempt and count as misses
- **Avg Reliability Score**: 0.885
- **Avg Generation Latency**: 312.5s
- **Total Assistant Turns**: 3655
- **Crashed Partials**: 3 (0 recovered, 3 terminal)

## Task Details

| Task ID | Status | Reliability Score | Latency | Model | Tags |
|---------|--------|-------------------|---------|-------|------|
| skill-bpmn-e2e-customer-escalation | SUCCESS | 1.000 | 403.9s | claude-sonnet-5 | uipath-maestro-bpmn, e2e, mode:build, lifecycle:generate, shape:multi-node, node:decision, node:hitl, feature:escalation |
| skill-bpmn-hitl-brownfield-insert | SUCCESS | 1.000 | 312.8s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, feature:approval-gate |
| skill-bpmn-multi-city-weather | SUCCESS | 1.000 | 692.8s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:loop |
| skill-bpmn-feet-inches | SUCCESS | 1.000 | 339.7s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node |
| skill-bpmn-script-jint-guidance | SUCCESS | 1.000 | 523.9s | claude-sonnet-5 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:single-node, node:script |
| skill-bpmn-agent-job | SUCCESS | 1.000 | 342.8s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:single-node, resource |
| skill-bpmn-diagnose-scoped-variables | SUCCESS | 1.000 | 67.4s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:diagnose, lifecycle:discover |
| skill-bpmn-message-catch | SUCCESS | 1.000 | 197.8s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, feature:trigger |
| skill-bpmn-hitl-result-downstream | SUCCESS | 1.000 | 210.9s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, node:decision, feature:approval-gate |
| skill-bpmn-integration-service-boundary | FAILURE | 0.167 | 649.3s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, connector, feature:connections |
| skill-bpmn-subprocess | SUCCESS | 1.000 | 130.6s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:subflow |
| skill-bpmn-operate-diagnose-minimal-fault-triage | SUCCESS | 1.000 | 87.2s | claude-sonnet-5 | uipath-maestro-bpmn, smoke, mode:diagnose, lifecycle:discover |
| skill-bpmn-safety-sanitize | SUCCESS | 1.000 | 53.1s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate |
| skill-bpmn-author-validate | SUCCESS | 1.000 | 143.6s | claude-sonnet-5 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate |
| skill-bpmn-dice-roller | SUCCESS | 1.000 | 128.8s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:decision |
| skill-bpmn-event-based-gateway | SUCCESS | 1.000 | 267.8s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, node:gateway |
| skill-bpmn-edit-move-node | SUCCESS | 1.000 | 108.9s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node |
| skill-bpmn-reading-list | SUCCESS | 1.000 | 224.2s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:transform |
| skill-bpmn-gateway-sequence-flows | SUCCESS | 1.000 | 380.0s | claude-sonnet-5 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:multi-node, node:gateway |
| skill-bpmn-hitl-completed-wired | SUCCESS | 1.000 | 478.9s | claude-sonnet-5 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:multi-node, node:hitl, feature:approval-gate |
| skill-bpmn-error-event-subprocess | SUCCESS | 1.000 | 212.0s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, node:subflow |
| skill-bpmn-expr-multiinstance-iterator | SUCCESS | 1.000 | 775.8s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, node:loop |
| skill-bpmn-e2e-invoice-exception-triage | SUCCESS | 1.000 | 474.0s | claude-sonnet-5 | uipath-maestro-bpmn, e2e, mode:build, lifecycle:generate, shape:multi-node, node:decision, node:hitl, feature:approval-gate |
| skill-bpmn-registry-discovery | SUCCESS | 1.000 | 110.0s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:inspect, connector, feature:connections, resource |
| skill-bpmn-hitl-schema-design | ERROR | 0.000 | 913.4s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, feature:approval-gate |
| skill-bpmn-switch | SUCCESS | 1.000 | 87.5s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:switch |
| skill-bpmn-timer-boundary-noninterrupting | SUCCESS | 1.000 | 143.5s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate |
| skill-bpmn-debug-workflow-mocked | SUCCESS | 1.000 | 59.8s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:operate, lifecycle:discover |
| skill-bpmn-script-task-group-by | SUCCESS | 1.000 | 247.7s | claude-sonnet-5 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:single-node, node:script |
| skill-bpmn-timer | SUCCESS | 1.000 | 51.7s | claude-sonnet-5 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:single-node, feature:timer |
| skill-bpmn-business-rule-task | MAX_TURNS_EXHAUSTED | 0.200 | 568.4s | claude-sonnet-5 | uipath-maestro-bpmn, e2e, mode:build, lifecycle:generate, node:business-rule, feature:orchestrator |
| skill-bpmn-calculator | SUCCESS | 1.000 | 239.0s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:decision |
| skill-bpmn-callactivity-agentic-process | SUCCESS | 1.000 | 265.6s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, node:call-activity |
| skill-bpmn-inclusive-gateway-forkjoin | SUCCESS | 1.000 | 171.5s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, node:gateway |
| skill-bpmn-loop-multiply | SUCCESS | 1.000 | 349.9s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:loop |
| skill-bpmn-rpa-job | SUCCESS | 1.000 | 165.8s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:single-node, resource |
| skill-bpmn-hitl-multi-outcome-routing | SUCCESS | 1.000 | 445.8s | claude-sonnet-5 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:multi-node, node:hitl, node:decision, feature:approval-gate |
| skill-bpmn-diagnose-stuck-gateway | SUCCESS | 1.000 | 78.8s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:diagnose, lifecycle:discover |
| skill-bpmn-timer-start | SUCCESS | 1.000 | 139.4s | claude-sonnet-5 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, feature:trigger |
| skill-bpmn-queue-create-and-wait | SUCCESS | 1.000 | 393.5s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate |
| skill-bpmn-edit-update-node | SUCCESS | 1.000 | 53.9s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node |
| skill-bpmn-debug-not-validation | FAILURE | 0.882 | 77.6s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate |
| skill-bpmn-diagnose-job-traces | SUCCESS | 1.000 | 50.6s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:diagnose, lifecycle:discover |
| skill-bpmn-diagnose-incident-root-cause | SUCCESS | 1.000 | 44.4s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:diagnose, lifecycle:discover |
| skill-bpmn-script-task-map | MAX_TURNS_EXHAUSTED | 0.000 | 355.1s | claude-sonnet-5 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:single-node, node:script |
| skill-bpmn-diagnose-deployed-drift | SUCCESS | 1.000 | 62.3s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:diagnose, lifecycle:discover |
| skill-bpmn-contract-variant-wrappers | SUCCESS | 1.000 | 2454.5s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, contract:xml, node:service-task, node:call-activity, connector |
| skill-bpmn-edit-group-to-subflow | SUCCESS | 1.000 | 402.2s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:subflow |
| skill-bpmn-e2e-live-debug | SUCCESS | 1.000 | 246.0s | claude-sonnet-5 | uipath-maestro-bpmn, e2e, mode:operate, lifecycle:setup, path-to-ga |
| skill-bpmn-script-jint-lifecycle | FAILURE | 0.200 | 289.2s | claude-sonnet-5 | uipath-maestro-bpmn, e2e, mode:build, lifecycle:generate, node:script, feature:jint |
| skill-bpmn-terminate | SUCCESS | 1.000 | 68.0s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:terminate |
| skill-bpmn-http-weather | SUCCESS | 1.000 | 283.5s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:single-node, feature:http |
| skill-bpmn-event-trigger-start | SUCCESS | 1.000 | 158.9s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:single-node, connector, feature:trigger |
| skill-bpmn-hitl-boolean-decision | SUCCESS | 1.000 | 312.0s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, node:decision, feature:approval-gate |
| skill-bpmn-simple-approval-bpmn | ERROR | 0.000 | 905.0s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:gateway, node:script, node:service-task, resource |
| skill-bpmn-api-workflow-task | MAX_TURNS_EXHAUSTED | 0.200 | 560.4s | claude-sonnet-5 | uipath-maestro-bpmn, e2e, mode:build, lifecycle:generate, node:service-task, feature:api-workflow |
| skill-bpmn-edit-remove-node | FAILURE | 0.333 | 358.3s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node |
| skill-bpmn-diagnose-validate-fix-loop | SUCCESS | 1.000 | 41.4s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:diagnose, lifecycle:discover |
| skill-bpmn-debug-instance-inspect | SUCCESS | 1.000 | 107.2s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:diagnose, lifecycle:discover |
| skill-bpmn-edit-add-output | SUCCESS | 1.000 | 398.0s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node |
| skill-bpmn-smoke-registry-discovery | SUCCESS | 1.000 | 67.5s | claude-sonnet-5 | uipath-maestro-bpmn, smoke, mode:build |
| skill-bpmn-hitl-rpa-wrappers | SUCCESS | 1.000 | 358.5s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, resource |
| skill-bpmn-edit-add-node | SUCCESS | 1.000 | 139.1s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node |
| skill-bpmn-expr-error-mapping | SUCCESS | 1.000 | 334.2s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate |
| skill-bpmn-script-task-filter | SUCCESS | 1.000 | 245.8s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:single-node, node:script |
| skill-bpmn-error-boundary-handler | SUCCESS | 1.000 | 184.9s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate |
| skill-bpmn-e2e-wiki-pageviews | SUCCESS | 1.000 | 402.6s | claude-sonnet-5 | uipath-maestro-bpmn, e2e, mode:build, lifecycle:generate, shape:multi-node, node:decision, node:transform |
| skill-bpmn-message-send-receive-pair | ERROR | 0.000 | 903.8s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, feature:trigger |
| skill-bpmn-parallel-fork-join | SUCCESS | 1.000 | 59.2s | claude-sonnet-5 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:multi-node, node:gateway, feature:parallel-tasks |
| skill-bpmn-expr-computed-js | SUCCESS | 1.000 | 311.0s | claude-sonnet-5 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate |

## Run-time Notes

> **WARNING:** [skill-bpmn-e2e-customer-escalation] expected_turns exceeded: 31/28 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-hitl-brownfield-insert] expected_turns exceeded: 25/22 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-multi-city-weather] max_turns exhausted
> **WARNING:** [skill-bpmn-multi-city-weather] expected_turns exceeded: 85/22 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-feet-inches] expected_turns exceeded: 36/22 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-script-jint-guidance] expected_turns exceeded: 51/15 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-agent-job] expected_turns exceeded: 47/16 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-message-catch] expected_turns exceeded: 21/16 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-integration-service-boundary] expected_turns exceeded: 35/19 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-reading-list] expected_turns exceeded: 27/22 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-gateway-sequence-flows] expected_turns exceeded: 32/21 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-hitl-completed-wired] expected_turns exceeded: 46/18 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-expr-multiinstance-iterator] expected_turns exceeded: 71/20 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-e2e-invoice-exception-triage] max_turns exhausted
> **WARNING:** [skill-bpmn-e2e-invoice-exception-triage] expected_turns exceeded: 49/25 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-hitl-schema-design] expected_turns exceeded: 51/22 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-script-task-group-by] expected_turns exceeded: 32/20 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-business-rule-task] max_turns exhausted
> **WARNING:** [skill-bpmn-business-rule-task] expected_turns exceeded: 47/28 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-calculator] expected_turns exceeded: 26/22 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-callactivity-agentic-process] expected_turns exceeded: 29/18 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-loop-multiply] expected_turns exceeded: 42/22 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-rpa-job] expected_turns exceeded: 20/16 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-timer-start] expected_turns exceeded: 23/18 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-queue-create-and-wait] expected_turns exceeded: 36/18 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-script-task-map] max_turns exhausted
> **WARNING:** [skill-bpmn-script-task-map] expected_turns exceeded: 55/20 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-contract-variant-wrappers] max_turns exhausted
> **WARNING:** [skill-bpmn-contract-variant-wrappers] expected_turns exceeded: 92/20 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-edit-group-to-subflow] expected_turns exceeded: 33/26 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-e2e-live-debug] expected_turns exceeded: 46/30 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-script-jint-lifecycle] expected_turns exceeded: 37/22 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-http-weather] expected_turns exceeded: 26/16 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-event-trigger-start] expected_turns exceeded: 21/16 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-hitl-boolean-decision] expected_turns exceeded: 33/24 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-simple-approval-bpmn] expected_turns exceeded: 63/24 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-api-workflow-task] max_turns exhausted
> **WARNING:** [skill-bpmn-api-workflow-task] expected_turns exceeded: 44/32 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-edit-remove-node] expected_turns exceeded: 23/18 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-debug-instance-inspect] expected_turns exceeded: 19/14 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-edit-add-output] expected_turns exceeded: 25/16 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-hitl-rpa-wrappers] expected_turns exceeded: 28/14 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-expr-error-mapping] expected_turns exceeded: 27/18 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-script-task-filter] expected_turns exceeded: 33/20 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-e2e-wiki-pageviews] expected_turns exceeded: 47/28 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-message-send-receive-pair] expected_turns exceeded: 74/20 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-expr-computed-js] expected_turns exceeded: 45/18 (cumulative SDK turns)


## Generation Metrics

| Task ID | Total Latency | Turns | Asst Turns | Avg Turn Latency |
|---------|---------------|-------|------------|------------------|
| skill-bpmn-e2e-customer-escalation | 403.9s | 1 | 56 | 382.9s |
| skill-bpmn-hitl-brownfield-insert | 312.8s | 1 | 44 | 300.6s |
| skill-bpmn-multi-city-weather | 692.8s | 1 | 142 | 680.0s |
| skill-bpmn-feet-inches | 339.7s | 1 | 70 | 326.7s |
| skill-bpmn-script-jint-guidance | 523.9s | 1 | 89 | 510.1s |
| skill-bpmn-agent-job | 342.8s | 1 | 86 | 329.5s |
| skill-bpmn-diagnose-scoped-variables | 67.4s | 1 | 15 | 52.9s |
| skill-bpmn-message-catch | 197.8s | 1 | 41 | 185.3s |
| skill-bpmn-hitl-result-downstream | 210.9s | 1 | 29 | 197.8s |
| skill-bpmn-integration-service-boundary | 649.3s | 1 | 62 | 636.8s |
| skill-bpmn-subprocess | 130.6s | 1 | 33 | 111.8s |
| skill-bpmn-operate-diagnose-minimal-fault-triage | 87.2s | 1 | 20 | 68.1s |
| skill-bpmn-safety-sanitize | 53.1s | 1 | 16 | 40.6s |
| skill-bpmn-author-validate | 143.6s | 1 | 35 | 130.0s |
| skill-bpmn-dice-roller | 128.8s | 1 | 26 | 115.3s |
| skill-bpmn-event-based-gateway | 267.8s | 1 | 36 | 253.8s |
| skill-bpmn-edit-move-node | 108.9s | 1 | 21 | 96.4s |
| skill-bpmn-reading-list | 224.2s | 1 | 53 | 211.2s |
| skill-bpmn-gateway-sequence-flows | 380.0s | 1 | 56 | 366.7s |
| skill-bpmn-hitl-completed-wired | 478.9s | 1 | 77 | 464.9s |
| skill-bpmn-error-event-subprocess | 212.0s | 1 | 26 | 199.3s |
| skill-bpmn-expr-multiinstance-iterator | 775.8s | 1 | 126 | 762.1s |
| skill-bpmn-e2e-invoice-exception-triage | 474.0s | 1 | 80 | 451.4s |
| skill-bpmn-registry-discovery | 110.0s | 1 | 26 | 97.0s |
| skill-bpmn-hitl-schema-design | 913.4s | 1 | 102 | 900.1s |
| skill-bpmn-switch | 87.5s | 1 | 13 | 69.8s |
| skill-bpmn-timer-boundary-noninterrupting | 143.5s | 1 | 19 | 130.9s |
| skill-bpmn-debug-workflow-mocked | 59.8s | 1 | 18 | 47.6s |
| skill-bpmn-script-task-group-by | 247.7s | 1 | 61 | 235.0s |
| skill-bpmn-timer | 51.7s | 1 | 9 | 38.7s |
| skill-bpmn-business-rule-task | 568.4s | 1 | 87 | 555.1s |
| skill-bpmn-calculator | 239.0s | 1 | 45 | 225.6s |
| skill-bpmn-callactivity-agentic-process | 265.6s | 1 | 57 | 252.2s |
| skill-bpmn-inclusive-gateway-forkjoin | 171.5s | 1 | 22 | 158.3s |
| skill-bpmn-loop-multiply | 349.9s | 1 | 81 | 337.8s |
| skill-bpmn-rpa-job | 165.8s | 1 | 36 | 158.2s |
| skill-bpmn-hitl-multi-outcome-routing | 445.8s | 1 | 44 | 437.0s |
| skill-bpmn-diagnose-stuck-gateway | 78.8s | 1 | 26 | 70.3s |
| skill-bpmn-timer-start | 139.4s | 1 | 44 | 132.1s |
| skill-bpmn-queue-create-and-wait | 393.5s | 1 | 72 | 385.9s |
| skill-bpmn-edit-update-node | 53.9s | 1 | 10 | 47.0s |
| skill-bpmn-debug-not-validation | 77.6s | 1 | 17 | 70.5s |
| skill-bpmn-diagnose-job-traces | 50.6s | 1 | 16 | 45.6s |
| skill-bpmn-diagnose-incident-root-cause | 44.4s | 1 | 14 | 38.8s |
| skill-bpmn-script-task-map | 355.1s | 1 | 108 | 350.7s |
| skill-bpmn-diagnose-deployed-drift | 62.3s | 1 | 17 | 55.5s |
| skill-bpmn-contract-variant-wrappers | 2454.5s | 1 | 174 | 2448.7s |
| skill-bpmn-edit-group-to-subflow | 402.2s | 1 | 66 | 396.6s |
| skill-bpmn-e2e-live-debug | 246.0s | 1 | 88 | 240.7s |
| skill-bpmn-script-jint-lifecycle | 289.2s | 1 | 64 | 282.3s |
| skill-bpmn-terminate | 68.0s | 1 | 12 | 55.4s |
| skill-bpmn-http-weather | 283.5s | 1 | 50 | 276.8s |
| skill-bpmn-event-trigger-start | 158.9s | 1 | 40 | 143.6s |
| skill-bpmn-hitl-boolean-decision | 312.0s | 1 | 60 | 306.9s |
| skill-bpmn-simple-approval-bpmn | 905.0s | 1 | 125 | 900.1s |
| skill-bpmn-api-workflow-task | 560.4s | 1 | 82 | 556.2s |
| skill-bpmn-edit-remove-node | 358.3s | 1 | 47 | 352.6s |
| skill-bpmn-diagnose-validate-fix-loop | 41.4s | 1 | 9 | 28.3s |
| skill-bpmn-debug-instance-inspect | 107.2s | 1 | 37 | 102.1s |
| skill-bpmn-edit-add-output | 398.0s | 1 | 48 | 393.0s |
| skill-bpmn-smoke-registry-discovery | 67.5s | 1 | 19 | 62.6s |
| skill-bpmn-hitl-rpa-wrappers | 358.5s | 1 | 56 | 352.2s |
| skill-bpmn-edit-add-node | 139.1s | 1 | 25 | 132.5s |
| skill-bpmn-expr-error-mapping | 334.2s | 1 | 51 | 329.7s |
| skill-bpmn-script-task-filter | 245.8s | 1 | 63 | 240.2s |
| skill-bpmn-error-boundary-handler | 184.9s | 1 | 34 | 180.1s |
| skill-bpmn-e2e-wiki-pageviews | 402.6s | 1 | 89 | 390.4s |
| skill-bpmn-message-send-receive-pair | 903.8s | 1 | 140 | 900.1s |
| skill-bpmn-parallel-fork-join | 59.2s | 1 | 11 | 53.1s |
| skill-bpmn-expr-computed-js | 311.0s | 1 | 82 | 305.4s |


## Token Usage

**Total Tokens**: 151,297,111 (input: 88,607, output: 1,622,805)
**Cache Tokens**: write: 4,568,348, read: 145,017,351
**Agent Cost**: $85.2444
**Eval Overhead (judge + simulator)**: $0.1341
**Total Cost**: $85.3785
**Avg Tokens/Task**: 2,161,387

| Task ID | Input (uncached) | Output | Cache Write | Cache Read | Total | Cost |
|---------|------------------|--------|-------------|------------|-------|------|
| skill-bpmn-e2e-customer-escalation | 7,801 | 31,725 | 118,261 | 2,349,112 | 2,506,899 | $1.6677 |
| skill-bpmn-hitl-brownfield-insert | 800 | 24,314 | 80,897 | 1,353,481 | 1,459,492 | $1.0765 |
| skill-bpmn-multi-city-weather | 1,180 | 48,832 | 182,892 | 6,896,105 | 7,129,009 | $3.4907 |
| skill-bpmn-feet-inches | 829 | 19,601 | 62,102 | 2,889,824 | 2,972,356 | $1.3963 |
| skill-bpmn-script-jint-guidance | 930 | 38,824 | 133,077 | 3,765,999 | 3,938,830 | $2.2140 |
| skill-bpmn-agent-job | 824 | 20,127 | 121,940 | 4,473,910 | 4,616,801 | $2.1038 |
| skill-bpmn-diagnose-scoped-variables | 699 | 3,108 | 58,780 | 319,853 | 382,440 | $0.3651 |
| skill-bpmn-message-catch | 742 | 11,685 | 85,681 | 1,387,319 | 1,485,427 | $0.9150 |
| skill-bpmn-hitl-result-downstream | 6,314 | 13,820 | 90,261 | 900,266 | 1,010,661 | $0.8348 |
| skill-bpmn-integration-service-boundary | 670 | 51,756 | 108,923 | 2,363,389 | 2,524,738 | $1.8958 |
| skill-bpmn-subprocess | 782 | 7,251 | 91,722 | 1,095,560 | 1,195,315 | $0.7962 |
| skill-bpmn-operate-diagnose-minimal-fault-triage | 677 | 4,135 | 61,964 | 388,179 | 454,955 | $0.4252 |
| skill-bpmn-safety-sanitize | 679 | 2,515 | 56,661 | 260,567 | 320,422 | $0.3304 |
| skill-bpmn-author-validate | 6,305 | 6,477 | 43,507 | 1,125,028 | 1,181,317 | $0.6167 |
| skill-bpmn-dice-roller | 730 | 6,629 | 39,382 | 852,365 | 899,106 | $0.5050 |
| skill-bpmn-event-based-gateway | 859 | 18,704 | 96,307 | 1,353,456 | 1,469,326 | $1.0503 |
| skill-bpmn-edit-move-node | 636 | 7,515 | 60,734 | 486,800 | 555,685 | $0.4884 |
| skill-bpmn-reading-list | 6,428 | 11,770 | 63,741 | 2,032,102 | 2,114,041 | $1.0445 |
| skill-bpmn-gateway-sequence-flows | 662 | 32,638 | 74,843 | 2,041,184 | 2,149,327 | $1.3846 |
| skill-bpmn-hitl-completed-wired | 770 | 36,993 | 117,278 | 2,671,245 | 2,826,286 | $1.7984 |
| skill-bpmn-error-event-subprocess | 862 | 14,563 | 76,070 | 797,337 | 888,832 | $0.7455 |
| skill-bpmn-expr-multiinstance-iterator | 1,100 | 63,126 | 126,885 | 5,014,717 | 5,205,828 | $2.9304 |
| skill-bpmn-e2e-invoice-exception-triage | 698 | 35,539 | 124,925 | 2,888,479 | 3,049,641 | $1.8948 |
| skill-bpmn-registry-discovery | 616 | 3,628 | 18,260 | 728,475 | 750,979 | $0.3433 |
| skill-bpmn-hitl-schema-design | 102 | 74,083 | 116,527 | 4,389,354 | 4,580,066 | $2.8653 |
| skill-bpmn-switch | 772 | 4,471 | 71,997 | 365,910 | 443,150 | $0.4601 |
| skill-bpmn-timer-boundary-noninterrupting | 815 | 8,719 | 39,980 | 491,714 | 541,228 | $0.4307 |
| skill-bpmn-debug-workflow-mocked | 661 | 2,107 | 23,320 | 500,461 | 526,549 | $0.2712 |
| skill-bpmn-script-task-group-by | 833 | 14,523 | 46,792 | 2,179,870 | 2,242,018 | $1.0498 |
| skill-bpmn-timer | 727 | 2,323 | 27,128 | 266,673 | 296,851 | $0.2188 |
| skill-bpmn-business-rule-task | 1,673 | 43,357 | 128,812 | 3,859,113 | 4,032,955 | $2.2962 |
| skill-bpmn-calculator | 752 | 18,624 | 69,487 | 1,740,649 | 1,829,512 | $1.0644 |
| skill-bpmn-callactivity-agentic-process | 814 | 17,484 | 73,974 | 2,314,758 | 2,407,030 | $1.2365 |
| skill-bpmn-inclusive-gateway-forkjoin | 871 | 11,651 | 40,577 | 647,012 | 700,111 | $0.5236 |
| skill-bpmn-loop-multiply | 848 | 21,291 | 87,551 | 3,892,833 | 4,002,523 | $1.8181 |
| skill-bpmn-rpa-job | 737 | 10,542 | 42,116 | 1,171,416 | 1,224,811 | $0.6697 |
| skill-bpmn-hitl-multi-outcome-routing | 3,027 | 39,031 | 54,019 | 1,594,770 | 1,690,847 | $1.2755 |
| skill-bpmn-diagnose-stuck-gateway | 657 | 4,040 | 20,704 | 650,920 | 676,321 | $0.3355 |
| skill-bpmn-timer-start | 829 | 6,467 | 32,809 | 1,368,416 | 1,408,521 | $0.6331 |
| skill-bpmn-queue-create-and-wait | 881 | 29,116 | 62,161 | 2,862,015 | 2,954,173 | $1.5311 |
| skill-bpmn-edit-update-node | 619 | 2,797 | 13,818 | 240,473 | 257,707 | $0.1678 |
| skill-bpmn-debug-not-validation | 608 | 4,581 | 31,437 | 543,252 | 579,878 | $0.3514 |
| skill-bpmn-diagnose-job-traces | 690 | 2,449 | 18,387 | 415,794 | 437,320 | $0.2325 |
| skill-bpmn-diagnose-incident-root-cause | 678 | 2,214 | 18,906 | 359,428 | 381,226 | $0.2140 |
| skill-bpmn-script-task-map | 848 | 20,563 | 59,900 | 4,096,323 | 4,177,634 | $1.7645 |
| skill-bpmn-diagnose-deployed-drift | 711 | 3,869 | 19,203 | 360,457 | 384,240 | $0.2403 |
| skill-bpmn-contract-variant-wrappers | 2,169 | 223,909 | 119,153 | 10,480,902 | 10,826,133 | $6.9562 |
| skill-bpmn-edit-group-to-subflow | 704 | 32,961 | 49,750 | 2,242,864 | 2,326,279 | $1.3559 |
| skill-bpmn-e2e-live-debug | 1,282 | 11,199 | 70,001 | 3,606,517 | 3,688,999 | $1.5163 |
| skill-bpmn-script-jint-lifecycle | 754 | 20,717 | 64,556 | 2,496,339 | 2,582,366 | $1.3040 |
| skill-bpmn-terminate | 731 | 3,821 | 28,913 | 399,867 | 433,332 | $0.2982 |
| skill-bpmn-http-weather | 6,334 | 21,641 | 55,085 | 1,886,504 | 1,969,564 | $1.1161 |
| skill-bpmn-event-trigger-start | 930 | 9,153 | 46,177 | 1,336,979 | 1,393,239 | $0.7328 |
| skill-bpmn-hitl-boolean-decision | 880 | 27,057 | 81,860 | 2,556,672 | 2,666,469 | $1.4825 |
| skill-bpmn-simple-approval-bpmn | 126 | 74,936 | 83,375 | 5,785,254 | 5,943,691 | $3.1727 |
| skill-bpmn-api-workflow-task | 794 | 45,109 | 78,414 | 3,469,069 | 3,593,386 | $2.0138 |
| skill-bpmn-edit-remove-node | 686 | 29,351 | 41,172 | 1,483,478 | 1,554,687 | $1.0418 |
| skill-bpmn-diagnose-validate-fix-loop | 658 | 1,261 | 14,734 | 293,623 | 310,276 | $0.1642 |
| skill-bpmn-debug-instance-inspect | 673 | 5,462 | 27,002 | 1,091,198 | 1,124,335 | $0.5126 |
| skill-bpmn-edit-add-output | 665 | 30,467 | 29,591 | 1,403,871 | 1,464,594 | $0.9911 |
| skill-bpmn-smoke-registry-discovery | 714 | 2,761 | 17,908 | 609,125 | 630,508 | $0.2934 |
| skill-bpmn-hitl-rpa-wrappers | 641 | 29,394 | 56,312 | 2,045,836 | 2,132,183 | $1.2678 |
| skill-bpmn-edit-add-node | 654 | 10,915 | 23,152 | 711,284 | 746,005 | $0.4659 |
| skill-bpmn-expr-error-mapping | 3,123 | 29,557 | 70,582 | 1,990,226 | 2,093,488 | $1.3145 |
| skill-bpmn-script-task-filter | 809 | 15,973 | 88,832 | 2,804,308 | 2,909,922 | $1.4164 |
| skill-bpmn-error-boundary-handler | 868 | 13,273 | 53,140 | 1,115,227 | 1,182,508 | $0.7355 |
| skill-bpmn-e2e-wiki-pageviews | 829 | 30,266 | 91,879 | 3,754,312 | 3,877,286 | $1.9521 |
| skill-bpmn-message-send-receive-pair | 146 | 69,005 | 93,357 | 7,035,966 | 7,198,474 | $3.4964 |
| skill-bpmn-parallel-fork-join | 780 | 4,558 | 29,512 | 336,747 | 371,597 | $0.2824 |
| skill-bpmn-expr-computed-js | 911 | 20,482 | 59,193 | 3,334,820 | 3,415,406 | $1.5324 |


## Command Telemetry

**Total Commands**: 1914
**Success Rate**: 1855/1914 (96.9%)

### Commands by Tool

| Tool | Count | % |
|------|-------|---|
| Bash | 1319 | 68.9% |
| Read | 323 | 16.9% |
| Write | 78 | 4.1% |
| Skill | 70 | 3.7% |
| Grep | 66 | 3.4% |
| Edit | 57 | 3.0% |
| TaskCreate | 1 | 0.1% |

### Performance

- **Average Command Time**: 1072.5ms
- **Total Command Time**: 2052.72s

### Slowest Commands

| Tool | Duration | Parameters |
|------|----------|------------|
| Bash | 39705ms | {'command': 'cd /tmp/registry-evidence\nTYPES=(\n ... |
| Bash | 22104ms | {'command': 'cd /tmp && uip maestro bpmn registry ... |
| Bash | 16311ms | {'command': 'mkdir -p ExpenseApprovalBpmn && uip m... |
| Bash | 15997ms | {'command': 'mkdir -p registry-evidence && uip mae... |
| Bash | 15675ms | {'command': 'uip maestro bpmn registry pull --outp... |

**Most Common Pattern**: `Bash → Bash → Bash`

**Skill Tool Invoked**: 70 time(s)

## Agent Settings

- **Permission Mode**: acceptEdits
- **Allowed Tools**: Skill, Bash, Read, Write, Edit, Glob, Grep
- **Model**: us.anthropic.claude-sonnet-5
- **Max Turns**: 90
- **System Prompt**: You are a coding agent. Do not access files in sibling runs/* directories. Everywhere else is permitted. 
- **Plugins**: /home/azureuser/projects/skills/tmp

## Environment

- **git_commit**: f7e9fda
- **skills_git_commit**: 6c266d5d2
- **cli_version**: 1.201.0-dev.8272
- **tool_plugins**: {'admin-tool': '1.201.0-dev.8272', 'agent-tool': '1.201.0-dev.8272', 'agenthub-tool': '1.201.0-dev.8272', 'aops-tool': '1.201.0-dev.8272', 'api-workflow-tool': '1.201.0-dev.8272', 'automation-hub-tool': '1.201.0-dev.8272', 'codedagent-tool': '1.201.0-dev.8272', 'codedapp-tool': '1.201.0-dev.8272', 'coder-tool': '1.201.0-dev.8272', 'context-grounding-tool': '1.201.0-dev.8272', 'conversational-tool': '1.201.0-dev.8272', 'data-fabric-tool': '1.201.0-dev.8272', 'docsai-tool': '1.201.0-dev.8272', 'function-tool': '1.201.0-dev.8272', 'gov-tool': '1.201.0-dev.8272', 'guardrails-tool': '1.201.0-dev.8272', 'insights-tool': '1.201.0-dev.8276', 'integrationservice-tool': '1.201.0-dev.8272', 'ixp-tool': '1.201.0-dev.8272', 'llm-gateway-tool': '1.201.0-dev.8272', 'llmgw-tool': '1.201.0-dev.8272', 'maestro-tool': '1.201.0-dev.8275', 'model-hub-tool': '1.201.0-dev.8272', 'orchestrator-tool': '1.201.0-dev.8272', 'platform-tool': '1.201.0-dev.8272', 'pm-tool': '1.201.0-dev.8272', 'rpa-legacy-tool': '1.201.0-dev.8272', 'rpa-tool': '1.201.0-dev.20260809.3', 'solution-tool': '1.201.0-dev.8272', 'tasks-tool': '1.201.0-dev.8272', 'test-manager-tool': '1.201.0-dev.8272', 'traces-tool': '1.201.0-dev.8272', 'vertical-solutions-tool': '1.201.0-dev.8272'}
- **coder_eval**: 0.9.6
- **claude_code_cli**: 2.1.238 (Claude Code)
- **uv**: uv 0.11.21 (x86_64-unknown-linux-gnu)
- **anthropic**: 0.102.0
- **openai**: Not Installed
- **pydantic**: 2.12.5