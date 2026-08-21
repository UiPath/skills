# Evaluation Run Report

**Run ID**: `maestro-bpmn-baseline-report-70`
**Date**: 2026-07-28 06:05:12
**Duration**: 1895.66s
**Model**: `claude-sonnet-4-6`

## Summary

- **Total Tasks**: 70
- **Succeeded**: 67
- **Failed**: 3
- **Errors**: 0
- **Success Rate**: 95.7%
- **Avg Reliability Score**: 0.962
- **Avg Generation Latency**: 292.5s
- **Total Assistant Turns**: 2161

## Task Details

| Task ID | Status | Reliability Score | Latency | Model | Tags |
|---------|--------|-------------------|---------|-------|------|
| skill-bpmn-e2e-customer-escalation | SUCCESS | 1.000 | 446.9s | claude-sonnet-4-6 | uipath-maestro-bpmn, e2e, mode:build, lifecycle:generate, shape:multi-node, node:decision, node:hitl, feature:escalation |
| skill-bpmn-edit-add-output | SUCCESS | 1.000 | 96.4s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node |
| skill-bpmn-script-jint-guidance | SUCCESS | 1.000 | 192.6s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:single-node, node:script |
| skill-bpmn-calculator | SUCCESS | 1.000 | 566.1s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:decision |
| skill-bpmn-diagnose-stuck-gateway | SUCCESS | 1.000 | 76.1s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:diagnose, lifecycle:discover |
| skill-bpmn-hitl-schema-design | SUCCESS | 1.000 | 513.6s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, feature:approval-gate |
| skill-bpmn-diagnose-deployed-drift | SUCCESS | 1.000 | 50.3s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:diagnose, lifecycle:discover |
| skill-bpmn-debug-workflow-mocked | SUCCESS | 1.000 | 67.3s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:operate, lifecycle:discover |
| skill-bpmn-expr-multiinstance-iterator | SUCCESS | 1.000 | 447.9s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, node:loop |
| skill-bpmn-parallel-fork-join | SUCCESS | 1.000 | 106.6s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:multi-node, node:gateway, feature:parallel-tasks |
| skill-bpmn-http-weather | SUCCESS | 1.000 | 249.5s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:single-node, feature:http |
| skill-bpmn-integration-service-boundary | FAILURE | 0.000 | 524.0s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, connector, feature:connections |
| skill-bpmn-e2e-invoice-exception-triage | SUCCESS | 1.000 | 429.6s | claude-sonnet-4-6 | uipath-maestro-bpmn, e2e, mode:build, lifecycle:generate, shape:multi-node, node:decision, node:hitl, feature:approval-gate |
| skill-bpmn-edit-remove-node | SUCCESS | 1.000 | 91.6s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node |
| skill-bpmn-edit-add-node | SUCCESS | 1.000 | 158.9s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node |
| skill-bpmn-hitl-result-downstream | SUCCESS | 1.000 | 671.9s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, node:decision, feature:approval-gate |
| skill-bpmn-e2e-live-debug | FAILURE | 0.333 | 1877.9s | claude-sonnet-4-6 | uipath-maestro-bpmn, e2e, mode:operate, lifecycle:setup, path-to-ga |
| skill-bpmn-e2e-wiki-pageviews | SUCCESS | 1.000 | 602.5s | claude-sonnet-4-6 | uipath-maestro-bpmn, e2e, mode:build, lifecycle:generate, shape:multi-node, node:decision, node:transform |
| skill-bpmn-hitl-rpa-wrappers | FAILURE | 0.000 | 233.3s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, resource |
| skill-bpmn-timer-boundary-noninterrupting | SUCCESS | 1.000 | 372.9s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate |
| skill-bpmn-diagnose-validate-fix-loop | SUCCESS | 1.000 | 65.1s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:diagnose, lifecycle:discover |
| skill-bpmn-feet-inches | SUCCESS | 1.000 | 312.6s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node |
| skill-bpmn-terminate | SUCCESS | 1.000 | 107.5s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:terminate |
| skill-bpmn-event-trigger-start | SUCCESS | 1.000 | 197.8s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:single-node, connector, feature:trigger |
| skill-bpmn-loop-multiply | SUCCESS | 1.000 | 476.9s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:loop |
| skill-bpmn-author-validate | SUCCESS | 1.000 | 144.0s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate |
| skill-bpmn-event-based-gateway | SUCCESS | 1.000 | 542.6s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, node:gateway |
| skill-bpmn-expr-error-mapping | SUCCESS | 1.000 | 510.4s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate |
| skill-bpmn-expr-computed-js | SUCCESS | 1.000 | 247.1s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate |
| skill-bpmn-diagnose-scoped-variables | SUCCESS | 1.000 | 53.9s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:diagnose, lifecycle:discover |
| skill-bpmn-script-jint-lifecycle | SUCCESS | 1.000 | 331.6s | claude-sonnet-4-6 | uipath-maestro-bpmn, e2e, mode:build, lifecycle:generate, node:script, feature:jint |
| skill-bpmn-error-boundary-handler | SUCCESS | 1.000 | 282.7s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate |
| skill-bpmn-agent-job | SUCCESS | 1.000 | 351.4s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:single-node, resource |
| skill-bpmn-smoke-registry-discovery | SUCCESS | 1.000 | 67.4s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build |
| skill-bpmn-script-task-filter | SUCCESS | 1.000 | 182.5s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:single-node, node:script |
| skill-bpmn-api-workflow-task | SUCCESS | 1.000 | 674.4s | claude-sonnet-4-6 | uipath-maestro-bpmn, e2e, mode:build, lifecycle:generate, node:service-task, feature:api-workflow |
| skill-bpmn-timer-start | SUCCESS | 1.000 | 199.8s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, feature:trigger |
| skill-bpmn-script-task-map | SUCCESS | 1.000 | 252.8s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:single-node, node:script |
| skill-bpmn-diagnose-job-traces | SUCCESS | 1.000 | 109.9s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:diagnose, lifecycle:discover |
| skill-bpmn-queue-create-and-wait | SUCCESS | 1.000 | 245.7s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate |
| skill-bpmn-switch | SUCCESS | 1.000 | 130.3s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:switch |
| skill-bpmn-debug-not-validation | SUCCESS | 1.000 | 77.0s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate |
| skill-bpmn-contract-variant-wrappers | SUCCESS | 1.000 | 848.1s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, contract:xml, node:service-task, node:call-activity, connector |
| skill-bpmn-operate-diagnose-minimal-fault-triage | SUCCESS | 1.000 | 99.0s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:diagnose, lifecycle:discover |
| skill-bpmn-edit-group-to-subflow | SUCCESS | 1.000 | 150.9s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:subflow |
| skill-bpmn-reading-list | SUCCESS | 1.000 | 561.0s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:transform |
| skill-bpmn-timer | SUCCESS | 1.000 | 108.8s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:single-node, feature:timer |
| skill-bpmn-hitl-multi-outcome-routing | SUCCESS | 1.000 | 359.8s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:multi-node, node:hitl, node:decision, feature:approval-gate |
| skill-bpmn-hitl-brownfield-insert | SUCCESS | 1.000 | 132.8s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, feature:approval-gate |
| skill-bpmn-multi-city-weather | SUCCESS | 1.000 | 556.8s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:loop |
| skill-bpmn-hitl-boolean-decision | SUCCESS | 1.000 | 477.3s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, node:decision, feature:approval-gate |
| skill-bpmn-dice-roller | SUCCESS | 1.000 | 285.9s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:decision |
| skill-bpmn-diagnose-incident-root-cause | SUCCESS | 1.000 | 42.8s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:diagnose, lifecycle:discover |
| skill-bpmn-script-task-group-by | SUCCESS | 1.000 | 148.7s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:single-node, node:script |
| skill-bpmn-inclusive-gateway-forkjoin | SUCCESS | 1.000 | 150.5s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, node:gateway |
| skill-bpmn-hitl-completed-wired | SUCCESS | 1.000 | 296.9s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:multi-node, node:hitl, feature:approval-gate |
| skill-bpmn-edit-update-node | SUCCESS | 1.000 | 42.8s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node |
| skill-bpmn-business-rule-task | SUCCESS | 1.000 | 362.6s | claude-sonnet-4-6 | uipath-maestro-bpmn, e2e, mode:build, lifecycle:generate, node:business-rule, feature:orchestrator |
| skill-bpmn-simple-approval-bpmn | SUCCESS | 1.000 | 523.5s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:gateway, node:script, node:service-task, resource |
| skill-bpmn-error-event-subprocess | SUCCESS | 1.000 | 150.5s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, node:subflow |
| skill-bpmn-message-send-receive-pair | SUCCESS | 1.000 | 324.7s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, feature:trigger |
| skill-bpmn-gateway-sequence-flows | SUCCESS | 1.000 | 460.7s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:multi-node, node:gateway |
| skill-bpmn-rpa-job | SUCCESS | 1.000 | 134.4s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:single-node, resource |
| skill-bpmn-safety-sanitize | SUCCESS | 1.000 | 54.3s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate |
| skill-bpmn-registry-discovery | SUCCESS | 1.000 | 88.9s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:inspect, connector, feature:connections, resource |
| skill-bpmn-debug-instance-inspect | SUCCESS | 1.000 | 41.9s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:diagnose, lifecycle:discover |
| skill-bpmn-callactivity-agentic-process | SUCCESS | 1.000 | 279.6s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, node:call-activity |
| skill-bpmn-message-catch | SUCCESS | 1.000 | 237.4s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, feature:trigger |
| skill-bpmn-subprocess | SUCCESS | 1.000 | 128.1s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:subflow |
| skill-bpmn-edit-move-node | SUCCESS | 1.000 | 84.4s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node |

## Run-time Notes

> **WARNING:** [skill-bpmn-e2e-customer-escalation] expected_turns exceeded: 34/28 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-script-jint-guidance] expected_turns exceeded: 18/15 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-calculator] expected_turns exceeded: 23/22 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-debug-workflow-mocked] expected_turns exceeded: 18/14 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-expr-multiinstance-iterator] expected_turns exceeded: 24/20 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-http-weather] expected_turns exceeded: 20/16 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-e2e-invoice-exception-triage] expected_turns exceeded: 29/25 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-hitl-result-downstream] expected_turns exceeded: 26/24 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-e2e-live-debug] expected_turns exceeded: 91/30 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-e2e-wiki-pageviews] expected_turns exceeded: 35/28 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-hitl-rpa-wrappers] expected_turns exceeded: 22/14 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-event-based-gateway] expected_turns exceeded: 39/20 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-expr-error-mapping] expected_turns exceeded: 26/18 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-expr-computed-js] expected_turns exceeded: 23/18 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-script-jint-lifecycle] expected_turns exceeded: 32/22 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-agent-job] expected_turns exceeded: 18/16 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-diagnose-job-traces] expected_turns exceeded: 23/16 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-queue-create-and-wait] expected_turns exceeded: 22/18 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-contract-variant-wrappers] expected_turns exceeded: 43/20 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-operate-diagnose-minimal-fault-triage] expected_turns exceeded: 18/16 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-hitl-completed-wired] expected_turns exceeded: 19/18 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-business-rule-task] expected_turns exceeded: 36/28 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-message-send-receive-pair] expected_turns exceeded: 38/20 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-callactivity-agentic-process] expected_turns exceeded: 21/18 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-message-catch] expected_turns exceeded: 22/16 (cumulative SDK turns)


## Generation Metrics

| Task ID | Total Latency | Turns | Asst Turns | Avg Turn Latency |
|---------|---------------|-------|------------|------------------|
| skill-bpmn-e2e-customer-escalation | 446.9s | 1 | 49 | 429.7s |
| skill-bpmn-edit-add-output | 96.4s | 1 | 24 | 86.3s |
| skill-bpmn-script-jint-guidance | 192.6s | 1 | 29 | 182.9s |
| skill-bpmn-calculator | 566.1s | 1 | 41 | 556.8s |
| skill-bpmn-diagnose-stuck-gateway | 76.1s | 1 | 22 | 66.2s |
| skill-bpmn-hitl-schema-design | 513.6s | 1 | 30 | 504.9s |
| skill-bpmn-diagnose-deployed-drift | 50.3s | 1 | 11 | 40.1s |
| skill-bpmn-debug-workflow-mocked | 67.3s | 1 | 27 | 58.4s |
| skill-bpmn-expr-multiinstance-iterator | 447.9s | 1 | 41 | 438.7s |
| skill-bpmn-parallel-fork-join | 106.6s | 1 | 20 | 96.9s |
| skill-bpmn-http-weather | 249.5s | 1 | 30 | 239.0s |
| skill-bpmn-integration-service-boundary | 524.0s | 1 | 16 | 513.6s |
| skill-bpmn-e2e-invoice-exception-triage | 429.6s | 1 | 43 | 414.3s |
| skill-bpmn-edit-remove-node | 91.6s | 1 | 25 | 82.4s |
| skill-bpmn-edit-add-node | 158.9s | 1 | 23 | 150.9s |
| skill-bpmn-hitl-result-downstream | 671.9s | 1 | 41 | 662.0s |
| skill-bpmn-e2e-live-debug | 1877.9s | 1 | 141 | 1850.7s |
| skill-bpmn-e2e-wiki-pageviews | 602.5s | 1 | 51 | 585.9s |
| skill-bpmn-hitl-rpa-wrappers | 233.3s | 1 | 33 | 224.6s |
| skill-bpmn-timer-boundary-noninterrupting | 372.9s | 1 | 26 | 364.2s |
| skill-bpmn-diagnose-validate-fix-loop | 65.1s | 1 | 20 | 54.8s |
| skill-bpmn-feet-inches | 312.6s | 1 | 36 | 304.0s |
| skill-bpmn-terminate | 107.5s | 1 | 12 | 95.5s |
| skill-bpmn-event-trigger-start | 197.8s | 1 | 25 | 180.5s |
| skill-bpmn-loop-multiply | 476.9s | 1 | 27 | 467.6s |
| skill-bpmn-author-validate | 144.0s | 1 | 18 | 134.1s |
| skill-bpmn-event-based-gateway | 542.6s | 1 | 61 | 532.4s |
| skill-bpmn-expr-error-mapping | 510.4s | 1 | 40 | 500.9s |
| skill-bpmn-expr-computed-js | 247.1s | 1 | 36 | 240.1s |
| skill-bpmn-diagnose-scoped-variables | 53.9s | 1 | 14 | 43.9s |
| skill-bpmn-script-jint-lifecycle | 331.6s | 1 | 51 | 322.0s |
| skill-bpmn-error-boundary-handler | 282.7s | 1 | 25 | 273.6s |
| skill-bpmn-agent-job | 351.4s | 1 | 29 | 341.2s |
| skill-bpmn-smoke-registry-discovery | 67.4s | 1 | 22 | 66.8s |
| skill-bpmn-script-task-filter | 182.5s | 1 | 22 | 174.0s |
| skill-bpmn-api-workflow-task | 674.4s | 1 | 48 | 672.0s |
| skill-bpmn-timer-start | 199.8s | 1 | 28 | 197.5s |
| skill-bpmn-script-task-map | 252.8s | 1 | 27 | 250.8s |
| skill-bpmn-diagnose-job-traces | 109.9s | 1 | 35 | 107.9s |
| skill-bpmn-queue-create-and-wait | 245.7s | 1 | 35 | 243.7s |
| skill-bpmn-switch | 130.3s | 1 | 19 | 122.3s |
| skill-bpmn-debug-not-validation | 77.0s | 1 | 21 | 75.5s |
| skill-bpmn-contract-variant-wrappers | 848.1s | 1 | 60 | 846.6s |
| skill-bpmn-operate-diagnose-minimal-fault-triage | 99.0s | 1 | 25 | 91.4s |
| skill-bpmn-edit-group-to-subflow | 150.9s | 1 | 18 | 149.2s |
| skill-bpmn-reading-list | 561.0s | 1 | 36 | 559.3s |
| skill-bpmn-timer | 108.8s | 1 | 14 | 107.2s |
| skill-bpmn-hitl-multi-outcome-routing | 359.8s | 1 | 37 | 358.3s |
| skill-bpmn-hitl-brownfield-insert | 132.8s | 1 | 28 | 131.3s |
| skill-bpmn-multi-city-weather | 556.8s | 1 | 33 | 555.2s |
| skill-bpmn-hitl-boolean-decision | 477.3s | 1 | 34 | 475.8s |
| skill-bpmn-dice-roller | 285.9s | 1 | 29 | 284.2s |
| skill-bpmn-diagnose-incident-root-cause | 42.8s | 1 | 18 | 40.9s |
| skill-bpmn-script-task-group-by | 148.7s | 1 | 20 | 146.9s |
| skill-bpmn-inclusive-gateway-forkjoin | 150.5s | 1 | 23 | 149.0s |
| skill-bpmn-hitl-completed-wired | 296.9s | 1 | 30 | 295.4s |
| skill-bpmn-edit-update-node | 42.8s | 1 | 17 | 41.2s |
| skill-bpmn-business-rule-task | 362.6s | 1 | 54 | 361.0s |
| skill-bpmn-simple-approval-bpmn | 523.5s | 1 | 36 | 522.0s |
| skill-bpmn-error-event-subprocess | 150.5s | 1 | 12 | 148.9s |
| skill-bpmn-message-send-receive-pair | 324.7s | 1 | 58 | 323.1s |
| skill-bpmn-gateway-sequence-flows | 460.7s | 1 | 8 | 459.1s |
| skill-bpmn-rpa-job | 134.4s | 1 | 25 | 132.9s |
| skill-bpmn-safety-sanitize | 54.3s | 1 | 16 | 52.7s |
| skill-bpmn-registry-discovery | 88.9s | 1 | 28 | 87.3s |
| skill-bpmn-debug-instance-inspect | 41.9s | 1 | 16 | 40.1s |
| skill-bpmn-callactivity-agentic-process | 279.6s | 1 | 37 | 277.8s |
| skill-bpmn-message-catch | 237.4s | 1 | 38 | 235.8s |
| skill-bpmn-subprocess | 128.1s | 1 | 12 | 122.4s |
| skill-bpmn-edit-move-node | 84.4s | 1 | 25 | 82.6s |


## Token Usage

**Total Tokens**: 59,840,357 (input: 22,346, output: 1,388,267)
**Cache Tokens**: write: 2,008,710, read: 56,421,034
**Total Cost**: $45.3500
**Avg Tokens/Task**: 854,862

| Task ID | Input (uncached) | Output | Cache Write | Cache Read | Total | Cost |
|---------|------------------|--------|-------------|------------|-------|------|
| skill-bpmn-e2e-customer-escalation | 31 | 30,022 | 47,433 | 1,602,409 | 1,679,895 | $1.1090 |
| skill-bpmn-edit-add-output | 17 | 5,298 | 25,332 | 591,294 | 621,941 | $0.3519 |
| skill-bpmn-script-jint-guidance | 17 | 11,375 | 31,399 | 673,707 | 716,498 | $0.4905 |
| skill-bpmn-calculator | 1,552 | 41,847 | 45,165 | 996,184 | 1,084,748 | $1.1006 |
| skill-bpmn-diagnose-stuck-gateway | 16 | 3,228 | 14,940 | 487,323 | 505,507 | $0.2507 |
| skill-bpmn-hitl-schema-design | 20 | 38,540 | 35,456 | 837,722 | 911,738 | $0.9624 |
| skill-bpmn-diagnose-deployed-drift | 7 | 1,951 | 6,139 | 161,321 | 169,418 | $0.1007 |
| skill-bpmn-debug-workflow-mocked | 18 | 2,738 | 9,289 | 479,445 | 491,490 | $0.2198 |
| skill-bpmn-expr-multiinstance-iterator | 25 | 29,843 | 42,267 | 1,117,311 | 1,189,446 | $0.9414 |
| skill-bpmn-parallel-fork-join | 14 | 6,402 | 21,665 | 464,416 | 492,497 | $0.3166 |
| skill-bpmn-http-weather | 20 | 17,139 | 28,069 | 787,543 | 832,771 | $0.5987 |
| skill-bpmn-integration-service-boundary | 11 | 38,184 | 13,152 | 291,181 | 342,528 | $0.7095 |
| skill-bpmn-e2e-invoice-exception-triage | 26 | 28,618 | 34,917 | 1,206,517 | 1,270,078 | $0.9222 |
| skill-bpmn-edit-remove-node | 19 | 5,175 | 15,703 | 567,481 | 588,378 | $0.3068 |
| skill-bpmn-edit-add-node | 15 | 11,774 | 26,256 | 533,873 | 571,918 | $0.4353 |
| skill-bpmn-hitl-result-downstream | 25 | 47,498 | 35,952 | 1,107,265 | 1,190,740 | $1.1795 |
| skill-bpmn-e2e-live-debug | 87 | 110,977 | 86,364 | 6,361,441 | 6,558,869 | $3.8972 |
| skill-bpmn-e2e-wiki-pageviews | 1,216 | 41,324 | 44,023 | 1,392,844 | 1,479,407 | $1.2064 |
| skill-bpmn-hitl-rpa-wrappers | 21 | 15,734 | 31,400 | 877,182 | 924,337 | $0.6170 |
| skill-bpmn-timer-boundary-noninterrupting | 16 | 25,618 | 32,469 | 635,269 | 693,372 | $0.6967 |
| skill-bpmn-diagnose-validate-fix-loop | 14 | 2,512 | 11,486 | 373,986 | 387,998 | $0.1930 |
| skill-bpmn-feet-inches | 3,676 | 20,241 | 33,980 | 902,030 | 959,927 | $0.7127 |
| skill-bpmn-terminate | 9 | 6,751 | 18,766 | 241,230 | 266,756 | $0.2440 |
| skill-bpmn-event-trigger-start | 14 | 11,304 | 26,640 | 495,229 | 533,187 | $0.4181 |
| skill-bpmn-loop-multiply | 18 | 32,174 | 24,605 | 662,106 | 718,903 | $0.7736 |
| skill-bpmn-author-validate | 12 | 8,090 | 19,709 | 363,748 | 391,559 | $0.3044 |
| skill-bpmn-event-based-gateway | 37 | 38,215 | 52,719 | 2,022,222 | 2,113,193 | $1.3777 |
| skill-bpmn-expr-error-mapping | 26 | 36,125 | 39,522 | 1,238,281 | 1,313,954 | $1.0616 |
| skill-bpmn-expr-computed-js | 21 | 14,712 | 33,523 | 897,171 | 945,427 | $0.6156 |
| skill-bpmn-diagnose-scoped-variables | 8 | 1,974 | 11,908 | 210,793 | 224,683 | $0.1375 |
| skill-bpmn-script-jint-lifecycle | 25 | 23,129 | 44,657 | 1,262,983 | 1,330,794 | $0.8934 |
| skill-bpmn-error-boundary-handler | 17 | 18,395 | 27,522 | 651,236 | 697,170 | $0.5746 |
| skill-bpmn-agent-job | 17 | 24,511 | 27,644 | 641,209 | 693,381 | $0.6637 |
| skill-bpmn-smoke-registry-discovery | 17 | 2,809 | 15,834 | 499,038 | 517,698 | $0.2513 |
| skill-bpmn-script-task-filter | 14 | 10,119 | 26,503 | 506,864 | 543,500 | $0.4033 |
| skill-bpmn-api-workflow-task | 29 | 45,825 | 36,232 | 1,372,310 | 1,454,396 | $1.2350 |
| skill-bpmn-timer-start | 18 | 14,117 | 26,315 | 687,777 | 728,227 | $0.5168 |
| skill-bpmn-script-task-map | 17 | 16,333 | 23,899 | 612,298 | 652,547 | $0.5184 |
| skill-bpmn-diagnose-job-traces | 21 | 5,733 | 16,780 | 610,234 | 632,768 | $0.3321 |
| skill-bpmn-queue-create-and-wait | 21 | 16,702 | 30,500 | 863,813 | 911,036 | $0.6241 |
| skill-bpmn-switch | 15 | 9,455 | 21,064 | 505,175 | 535,709 | $0.3724 |
| skill-bpmn-debug-not-validation | 16 | 4,514 | 20,155 | 537,689 | 562,374 | $0.3046 |
| skill-bpmn-contract-variant-wrappers | 30 | 64,975 | 96,890 | 1,676,103 | 1,837,998 | $1.8409 |
| skill-bpmn-operate-diagnose-minimal-fault-triage | 14 | 5,355 | 10,749 | 374,814 | 390,932 | $0.2331 |
| skill-bpmn-edit-group-to-subflow | 13 | 12,023 | 24,427 | 441,413 | 477,876 | $0.4044 |
| skill-bpmn-reading-list | 19 | 39,998 | 34,385 | 785,397 | 859,799 | $0.9646 |
| skill-bpmn-timer | 9 | 7,509 | 22,891 | 252,955 | 283,364 | $0.2744 |
| skill-bpmn-hitl-multi-outcome-routing | 3,676 | 29,241 | 38,747 | 913,933 | 985,597 | $0.8691 |
| skill-bpmn-hitl-brownfield-insert | 19 | 9,285 | 27,648 | 711,591 | 748,543 | $0.4565 |
| skill-bpmn-multi-city-weather | 19 | 38,427 | 30,365 | 775,285 | 844,096 | $0.9229 |
| skill-bpmn-hitl-boolean-decision | 20 | 37,493 | 37,059 | 855,163 | 929,735 | $0.9580 |
| skill-bpmn-dice-roller | 18 | 19,382 | 30,071 | 715,488 | 764,959 | $0.6182 |
| skill-bpmn-diagnose-incident-root-cause | 12 | 1,971 | 13,032 | 332,892 | 347,907 | $0.1783 |
| skill-bpmn-script-task-group-by | 14 | 9,651 | 26,364 | 506,838 | 542,867 | $0.3957 |
| skill-bpmn-inclusive-gateway-forkjoin | 17 | 9,848 | 29,323 | 666,510 | 705,698 | $0.4577 |
| skill-bpmn-hitl-completed-wired | 18 | 22,737 | 31,379 | 713,818 | 767,952 | $0.6729 |
| skill-bpmn-edit-update-node | 13 | 1,811 | 10,798 | 339,124 | 351,746 | $0.1694 |
| skill-bpmn-business-rule-task | 31 | 24,573 | 42,243 | 1,588,786 | 1,655,633 | $1.0037 |
| skill-bpmn-simple-approval-bpmn | 19 | 39,029 | 40,263 | 806,720 | 886,031 | $0.9785 |
| skill-bpmn-error-event-subprocess | 9 | 11,033 | 19,848 | 243,862 | 274,752 | $0.3131 |
| skill-bpmn-message-send-receive-pair | 3,693 | 20,517 | 43,617 | 1,901,490 | 1,969,317 | $1.0528 |
| skill-bpmn-gateway-sequence-flows | 9 | 40,990 | 13,052 | 158,593 | 212,644 | $0.7114 |
| skill-bpmn-rpa-job | 3,671 | 8,745 | 27,619 | 586,115 | 626,150 | $0.4216 |
| skill-bpmn-safety-sanitize | 11 | 2,429 | 13,104 | 276,577 | 292,121 | $0.1686 |
| skill-bpmn-registry-discovery | 20 | 3,222 | 23,235 | 684,861 | 711,338 | $0.3410 |
| skill-bpmn-debug-instance-inspect | 12 | 1,836 | 7,813 | 301,867 | 311,528 | $0.1474 |
| skill-bpmn-callactivity-agentic-process | 3,676 | 18,330 | 33,318 | 858,843 | 914,167 | $0.6686 |
| skill-bpmn-message-catch | 23 | 16,565 | 29,923 | 889,806 | 936,317 | $0.6277 |
| skill-bpmn-subprocess | 9 | 9,007 | 19,147 | 242,065 | 270,228 | $0.2796 |
| skill-bpmn-edit-move-node | 17 | 5,260 | 14,047 | 490,975 | 510,299 | $0.2789 |


## Command Telemetry

**Total Commands**: 1318
**Success Rate**: 1197/1318 (90.8%)

### Commands by Tool

| Tool | Count | % |
|------|-------|---|
| Bash | 827 | 62.7% |
| Read | 258 | 19.6% |
| Write | 106 | 8.0% |
| Skill | 61 | 4.6% |
| Edit | 40 | 3.0% |
| TaskUpdate | 12 | 0.9% |
| TaskCreate | 6 | 0.5% |
| Glob | 5 | 0.4% |
| Grep | 3 | 0.2% |

### Performance

- **Average Command Time**: 615.7ms
- **Total Command Time**: 811.53s

### Slowest Commands

| Tool | Duration | Parameters |
|------|----------|------------|
| Bash | 23152ms | {'command': 'cd /work/output/artifacts/skill-bpmn-... |
| Bash | 12039ms | {'command': 'cd /home/azureuser/projects/skills/sk... |
| Bash | 11384ms | {'command': 'uip maestro bpmn debug ProductCalc --... |
| Bash | 8734ms | {'command': 'uip maestro bpmn debug ProductCalc --... |
| Bash | 8391ms | {'command': 'uip maestro bpmn init RiskScoreScript... |

**Most Common Pattern**: `Bash → Bash → Bash`

**Skill Tool Invoked**: 61 time(s)

## Agent Settings

- **Permission Mode**: acceptEdits
- **Allowed Tools**: Skill, Bash, Read, Write, Edit, Glob, Grep
- **Model**: us.anthropic.claude-sonnet-4-6
- **Max Turns**: 90
- **System Prompt**: You are a coding agent. Do not access files in sibling runs/* directories. Everywhere else is permitted. 
- **Plugins**: /home/azureuser/projects/skills

## Environment

- **git_commit**: acc1c86
- **skills_git_commit**: 48b470716
- **cli_version**: 1.199.0
- **tool_plugins**: {'admin-tool': '1.200.0-dev.7984', 'agent-skill-tool': '1.199.0', 'agent-tool': '1.199.0-dev.7923 | 1.200.0-dev.7984', 'agenthub-tool': '1.199.0-dev.7923 | 1.200.0-dev.7984', 'aops-tool': '1.200.0-dev.7984', 'api-workflow-tool': '1.200.0-dev.7984', 'codedagent-tool': '1.199.0-dev.7923 | 1.200.0-dev.7984', 'codedapp-tool': '1.200.0-dev.7984', 'coder-tool': '1.200.0-dev.7984', 'context-grounding-tool': '1.200.0-dev.7984', 'conversational-tool': '1.200.0-dev.7984', 'data-fabric-tool': '1.199.0-dev.7923 | 1.200.0-dev.7984', 'docsai-tool': '1.200.0-dev.7984', 'function-tool': '1.200.0-dev.7984', 'functions-tool': '1.199.0-dev.7923', 'gov-tool': '1.199.0-dev.7923 | 1.200.0-dev.7998', 'insights-tool': '1.199.0-dev.7923 | 1.200.0-dev.7984', 'integrationservice-tool': '1.199.0-dev.7923 | 1.200.0-dev.7984', 'ixp-tool': '1.199.0-dev.7923 | 1.200.0-dev.7984', 'llm-gateway-tool': '1.200.0-dev.7984', 'llmgw-tool': '1.200.0-dev.7984', 'maestro-tool': '1.199.0-dev.7924 | 1.200.0-dev.7984', 'orchestrator-tool': '1.199.0-dev.7923 | 1.200.0-dev.7984', 'platform-tool': '1.200.0-dev.7984', 'pm-tool': '1.200.0-dev.7984', 'rpa-legacy-tool': '1.200.0-dev.7984', 'rpa-tool': '1.200.0-dev.20260726.2', 'solution-tool': '1.199.0-dev.7923 | 1.200.0-dev.7984', 'tasks-tool': '1.199.0-dev.7923 | 1.200.0-dev.7984', 'test-manager-tool': '1.199.0-dev.7923 | 1.200.0-dev.7984', 'traces-tool': '1.200.0-dev.7984', 'vertical-solutions-tool': '1.200.0-dev.7984'}
- **coder_eval**: 0.8.8
- **claude_code_cli**: 2.1.220 (Claude Code)
- **uv**: uv 0.11.21 (x86_64-unknown-linux-gnu)
- **anthropic**: 0.102.0
- **openai**: Not Installed
- **pydantic**: 2.12.5