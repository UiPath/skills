# Evaluation Run Report

**Run ID**: `maestro-bpmn-baseline-sonnet-4-6`
**Date**: 2026-08-15 00:30:36
**Duration**: 1751.01s
**Model**: `claude-sonnet-4-6`

## Summary

- **Total Tasks**: 70
- **Succeeded**: 62
- **Failed**: 5
- **Errors**: 3
- **Success Rate**: 92.5%
- **Avg Reliability Score**: 0.918
- **Avg Generation Latency**: 291.0s
- **Total Assistant Turns**: 2006
- **Crashed Partials**: 3 (0 recovered, 3 terminal)

## Task Details

| Task ID | Status | Reliability Score | Latency | Model | Tags |
|---------|--------|-------------------|---------|-------|------|
| skill-bpmn-event-trigger-start | SUCCESS | 1.000 | 307.3s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:single-node, connector, feature:trigger |
| skill-bpmn-diagnose-job-traces | SUCCESS | 1.000 | 83.2s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:diagnose, lifecycle:discover |
| skill-bpmn-edit-add-node | FAILURE | 0.333 | 138.7s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node |
| skill-bpmn-message-catch | SUCCESS | 1.000 | 179.1s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, feature:trigger |
| skill-bpmn-edit-remove-node | FAILURE | 0.333 | 137.8s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node |
| skill-bpmn-hitl-rpa-wrappers | SUCCESS | 1.000 | 253.7s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, resource |
| skill-bpmn-hitl-schema-design | SUCCESS | 1.000 | 567.8s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, feature:approval-gate |
| skill-bpmn-e2e-invoice-exception-triage | SUCCESS | 1.000 | 232.8s | claude-sonnet-4-6 | uipath-maestro-bpmn, e2e, mode:build, lifecycle:generate, shape:multi-node, node:decision, node:hitl, feature:approval-gate |
| skill-bpmn-edit-move-node | SUCCESS | 1.000 | 110.9s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node |
| skill-bpmn-diagnose-scoped-variables | SUCCESS | 1.000 | 80.9s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:diagnose, lifecycle:discover |
| skill-bpmn-hitl-brownfield-insert | SUCCESS | 1.000 | 231.7s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, feature:approval-gate |
| skill-bpmn-calculator | SUCCESS | 1.000 | 349.2s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:decision |
| skill-bpmn-hitl-multi-outcome-routing | SUCCESS | 1.000 | 491.0s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:multi-node, node:hitl, node:decision, feature:approval-gate |
| skill-bpmn-script-jint-lifecycle | SUCCESS | 1.000 | 226.3s | claude-sonnet-4-6 | uipath-maestro-bpmn, e2e, mode:build, lifecycle:generate, node:script, feature:jint |
| skill-bpmn-debug-workflow-mocked | SUCCESS | 1.000 | 50.6s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:operate, lifecycle:discover |
| skill-bpmn-timer-boundary-noninterrupting | SUCCESS | 1.000 | 275.6s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate |
| skill-bpmn-e2e-live-debug | SUCCESS | 1.000 | 270.2s | claude-sonnet-4-6 | uipath-maestro-bpmn, e2e, mode:operate, lifecycle:setup, path-to-ga |
| skill-bpmn-terminate | SUCCESS | 1.000 | 135.5s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:terminate |
| skill-bpmn-diagnose-incident-root-cause | SUCCESS | 1.000 | 73.0s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:diagnose, lifecycle:discover |
| skill-bpmn-simple-approval-bpmn | ERROR | 0.000 | 911.3s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:gateway, node:script, node:service-task, resource |
| skill-bpmn-integration-service-boundary | SUCCESS | 1.000 | 441.8s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, connector, feature:connections |
| skill-bpmn-edit-group-to-subflow | FAILURE | 0.333 | 332.4s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:subflow |
| skill-bpmn-debug-not-validation | SUCCESS | 1.000 | 83.6s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate |
| skill-bpmn-http-weather | SUCCESS | 1.000 | 262.6s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:single-node, feature:http |
| skill-bpmn-debug-instance-inspect | FAILURE | 0.900 | 77.2s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:diagnose, lifecycle:discover |
| skill-bpmn-contract-variant-wrappers | SUCCESS | 1.000 | 1718.6s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, contract:xml, node:service-task, node:call-activity, connector |
| skill-bpmn-inclusive-gateway-forkjoin | SUCCESS | 1.000 | 202.3s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, node:gateway |
| skill-bpmn-hitl-completed-wired | SUCCESS | 1.000 | 238.8s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:multi-node, node:hitl, feature:approval-gate |
| skill-bpmn-dice-roller | SUCCESS | 1.000 | 192.9s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:decision |
| skill-bpmn-script-jint-guidance | SUCCESS | 1.000 | 297.5s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:single-node, node:script |
| skill-bpmn-diagnose-stuck-gateway | SUCCESS | 1.000 | 84.3s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:diagnose, lifecycle:discover |
| skill-bpmn-hitl-boolean-decision | SUCCESS | 1.000 | 788.3s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, node:decision, feature:approval-gate |
| skill-bpmn-edit-add-output | SUCCESS | 1.000 | 89.1s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node |
| skill-bpmn-author-validate | SUCCESS | 1.000 | 168.1s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate |
| skill-bpmn-expr-multiinstance-iterator | SUCCESS | 1.000 | 595.9s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, node:loop |
| skill-bpmn-operate-diagnose-minimal-fault-triage | SUCCESS | 1.000 | 98.0s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:diagnose, lifecycle:discover |
| skill-bpmn-diagnose-validate-fix-loop | SUCCESS | 1.000 | 50.2s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:diagnose, lifecycle:discover |
| skill-bpmn-callactivity-agentic-process | SUCCESS | 1.000 | 181.6s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, node:call-activity |
| skill-bpmn-registry-discovery | SUCCESS | 1.000 | 111.3s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:inspect, connector, feature:connections, resource |
| skill-bpmn-diagnose-deployed-drift | SUCCESS | 1.000 | 84.8s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:diagnose, lifecycle:discover |
| skill-bpmn-script-task-map | SUCCESS | 1.000 | 148.2s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:single-node, node:script |
| skill-bpmn-script-task-group-by | SUCCESS | 1.000 | 130.9s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:single-node, node:script |
| skill-bpmn-switch | SUCCESS | 1.000 | 107.7s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:switch |
| skill-bpmn-e2e-customer-escalation | SUCCESS | 1.000 | 313.7s | claude-sonnet-4-6 | uipath-maestro-bpmn, e2e, mode:build, lifecycle:generate, shape:multi-node, node:decision, node:hitl, feature:escalation |
| skill-bpmn-feet-inches | SUCCESS | 1.000 | 225.5s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node |
| skill-bpmn-safety-sanitize | SUCCESS | 1.000 | 56.6s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate |
| skill-bpmn-expr-computed-js | SUCCESS | 1.000 | 449.6s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate |
| skill-bpmn-script-task-filter | SUCCESS | 1.000 | 173.4s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:single-node, node:script |
| skill-bpmn-parallel-fork-join | SUCCESS | 1.000 | 69.8s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:multi-node, node:gateway, feature:parallel-tasks |
| skill-bpmn-event-based-gateway | SUCCESS | 1.000 | 336.6s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, node:gateway |
| skill-bpmn-timer-start | SUCCESS | 1.000 | 179.5s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, feature:trigger |
| skill-bpmn-edit-update-node | FAILURE | 0.333 | 83.0s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node |
| skill-bpmn-subprocess | SUCCESS | 1.000 | 133.7s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:subflow |
| skill-bpmn-multi-city-weather | SUCCESS | 1.000 | 568.3s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:loop |
| skill-bpmn-error-boundary-handler | SUCCESS | 1.000 | 177.3s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate |
| skill-bpmn-loop-multiply | SUCCESS | 1.000 | 410.3s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:loop |
| skill-bpmn-message-send-receive-pair | SUCCESS | 1.000 | 845.0s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, feature:trigger |
| skill-bpmn-reading-list | SUCCESS | 1.000 | 452.6s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:transform |
| skill-bpmn-queue-create-and-wait | SUCCESS | 1.000 | 116.8s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate |
| skill-bpmn-e2e-wiki-pageviews | SUCCESS | 1.000 | 793.9s | claude-sonnet-4-6 | uipath-maestro-bpmn, e2e, mode:build, lifecycle:generate, shape:multi-node, node:decision, node:transform |
| skill-bpmn-rpa-job | SUCCESS | 1.000 | 276.2s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:single-node, resource |
| skill-bpmn-business-rule-task | SUCCESS | 1.000 | 161.0s | claude-sonnet-4-6 | uipath-maestro-bpmn, e2e, mode:build, lifecycle:generate, node:business-rule, feature:orchestrator |
| skill-bpmn-gateway-sequence-flows | ERROR | 0.000 | 903.4s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:multi-node, node:gateway |
| skill-bpmn-smoke-registry-discovery | SUCCESS | 1.000 | 111.4s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build |
| skill-bpmn-api-workflow-task | SUCCESS | 1.000 | 231.9s | claude-sonnet-4-6 | uipath-maestro-bpmn, e2e, mode:build, lifecycle:generate, node:service-task, feature:api-workflow |
| skill-bpmn-error-event-subprocess | SUCCESS | 1.000 | 155.8s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, node:subflow |
| skill-bpmn-expr-error-mapping | SUCCESS | 1.000 | 290.5s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate |
| skill-bpmn-hitl-result-downstream | SUCCESS | 1.000 | 280.0s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, node:decision, feature:approval-gate |
| skill-bpmn-timer | SUCCESS | 1.000 | 75.3s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:single-node, feature:timer |
| skill-bpmn-agent-job | ERROR | 0.000 | 904.9s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:single-node, resource |

## Run-time Notes

> **WARNING:** [skill-bpmn-hitl-schema-design] expected_turns exceeded: 23/22 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-hitl-multi-outcome-routing] expected_turns exceeded: 25/24 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-integration-service-boundary] expected_turns exceeded: 28/19 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-contract-variant-wrappers] max_turns exhausted
> **WARNING:** [skill-bpmn-contract-variant-wrappers] expected_turns exceeded: 104/20 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-expr-multiinstance-iterator] expected_turns exceeded: 22/20 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-operate-diagnose-minimal-fault-triage] expected_turns exceeded: 17/16 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-expr-computed-js] expected_turns exceeded: 20/18 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-multi-city-weather] expected_turns exceeded: 25/22 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-message-send-receive-pair] max_turns exhausted
> **WARNING:** [skill-bpmn-message-send-receive-pair] expected_turns exceeded: 81/20 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-reading-list] expected_turns exceeded: 27/22 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-rpa-job] expected_turns exceeded: 20/16 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-agent-job] expected_turns exceeded: 35/16 (cumulative SDK turns)


## Generation Metrics

| Task ID | Total Latency | Turns | Asst Turns | Avg Turn Latency |
|---------|---------------|-------|------------|------------------|
| skill-bpmn-event-trigger-start | 307.3s | 1 | 30 | 288.6s |
| skill-bpmn-diagnose-job-traces | 83.2s | 1 | 23 | 70.7s |
| skill-bpmn-edit-add-node | 138.7s | 1 | 23 | 126.6s |
| skill-bpmn-message-catch | 179.1s | 1 | 28 | 168.7s |
| skill-bpmn-edit-remove-node | 137.8s | 1 | 32 | 125.5s |
| skill-bpmn-hitl-rpa-wrappers | 253.7s | 1 | 22 | 241.4s |
| skill-bpmn-hitl-schema-design | 567.8s | 1 | 41 | 556.3s |
| skill-bpmn-e2e-invoice-exception-triage | 232.8s | 1 | 32 | 216.0s |
| skill-bpmn-edit-move-node | 110.9s | 1 | 22 | 98.9s |
| skill-bpmn-diagnose-scoped-variables | 80.9s | 1 | 22 | 70.1s |
| skill-bpmn-hitl-brownfield-insert | 231.7s | 1 | 26 | 219.9s |
| skill-bpmn-calculator | 349.2s | 1 | 31 | 337.4s |
| skill-bpmn-hitl-multi-outcome-routing | 491.0s | 1 | 44 | 480.2s |
| skill-bpmn-script-jint-lifecycle | 226.3s | 1 | 28 | 214.6s |
| skill-bpmn-debug-workflow-mocked | 50.6s | 1 | 14 | 39.2s |
| skill-bpmn-timer-boundary-noninterrupting | 275.6s | 1 | 24 | 264.5s |
| skill-bpmn-e2e-live-debug | 270.2s | 1 | 42 | 258.7s |
| skill-bpmn-terminate | 135.5s | 1 | 11 | 118.3s |
| skill-bpmn-diagnose-incident-root-cause | 73.0s | 1 | 18 | 61.7s |
| skill-bpmn-simple-approval-bpmn | 911.3s | 1 | 29 | 900.2s |
| skill-bpmn-integration-service-boundary | 441.8s | 1 | 47 | 429.9s |
| skill-bpmn-edit-group-to-subflow | 332.4s | 1 | 23 | 320.1s |
| skill-bpmn-debug-not-validation | 83.6s | 1 | 10 | 71.9s |
| skill-bpmn-http-weather | 262.6s | 1 | 21 | 249.5s |
| skill-bpmn-debug-instance-inspect | 77.2s | 1 | 17 | 67.1s |
| skill-bpmn-contract-variant-wrappers | 1718.6s | 1 | 152 | 1707.6s |
| skill-bpmn-inclusive-gateway-forkjoin | 202.3s | 1 | 20 | 190.4s |
| skill-bpmn-hitl-completed-wired | 238.8s | 1 | 24 | 225.8s |
| skill-bpmn-dice-roller | 192.9s | 1 | 18 | 181.8s |
| skill-bpmn-script-jint-guidance | 297.5s | 1 | 30 | 285.6s |
| skill-bpmn-diagnose-stuck-gateway | 84.3s | 1 | 24 | 73.6s |
| skill-bpmn-hitl-boolean-decision | 788.3s | 1 | 37 | 776.9s |
| skill-bpmn-edit-add-output | 89.1s | 1 | 19 | 77.6s |
| skill-bpmn-author-validate | 168.1s | 1 | 21 | 155.5s |
| skill-bpmn-expr-multiinstance-iterator | 595.9s | 1 | 34 | 583.6s |
| skill-bpmn-operate-diagnose-minimal-fault-triage | 98.0s | 1 | 21 | 83.3s |
| skill-bpmn-diagnose-validate-fix-loop | 50.2s | 1 | 10 | 37.8s |
| skill-bpmn-callactivity-agentic-process | 181.6s | 1 | 31 | 175.4s |
| skill-bpmn-registry-discovery | 111.3s | 1 | 27 | 104.4s |
| skill-bpmn-diagnose-deployed-drift | 84.8s | 1 | 15 | 76.8s |
| skill-bpmn-script-task-map | 148.2s | 1 | 15 | 142.2s |
| skill-bpmn-script-task-group-by | 130.9s | 1 | 15 | 123.0s |
| skill-bpmn-switch | 107.7s | 1 | 10 | 95.1s |
| skill-bpmn-e2e-customer-escalation | 313.7s | 1 | 31 | 300.0s |
| skill-bpmn-feet-inches | 225.5s | 1 | 18 | 218.6s |
| skill-bpmn-safety-sanitize | 56.6s | 1 | 16 | 49.0s |
| skill-bpmn-expr-computed-js | 449.6s | 1 | 38 | 441.8s |
| skill-bpmn-script-task-filter | 173.4s | 1 | 15 | 169.6s |
| skill-bpmn-parallel-fork-join | 69.8s | 1 | 11 | 65.0s |
| skill-bpmn-event-based-gateway | 336.6s | 1 | 25 | 331.2s |
| skill-bpmn-timer-start | 179.5s | 1 | 21 | 174.8s |
| skill-bpmn-edit-update-node | 83.0s | 1 | 17 | 77.6s |
| skill-bpmn-subprocess | 133.7s | 1 | 11 | 124.2s |
| skill-bpmn-multi-city-weather | 568.3s | 1 | 44 | 563.8s |
| skill-bpmn-error-boundary-handler | 177.3s | 1 | 22 | 170.0s |
| skill-bpmn-loop-multiply | 410.3s | 1 | 25 | 404.6s |
| skill-bpmn-message-send-receive-pair | 845.0s | 1 | 110 | 838.7s |
| skill-bpmn-reading-list | 452.6s | 1 | 47 | 449.1s |
| skill-bpmn-queue-create-and-wait | 116.8s | 1 | 21 | 109.0s |
| skill-bpmn-e2e-wiki-pageviews | 793.9s | 1 | 33 | 777.9s |
| skill-bpmn-rpa-job | 276.2s | 1 | 36 | 270.9s |
| skill-bpmn-business-rule-task | 161.0s | 1 | 29 | 156.6s |
| skill-bpmn-gateway-sequence-flows | 903.4s | 1 | 16 | 900.0s |
| skill-bpmn-smoke-registry-discovery | 111.4s | 1 | 43 | 106.9s |
| skill-bpmn-api-workflow-task | 231.9s | 1 | 34 | 226.9s |
| skill-bpmn-error-event-subprocess | 155.8s | 1 | 15 | 151.0s |
| skill-bpmn-expr-error-mapping | 290.5s | 1 | 35 | 285.3s |
| skill-bpmn-hitl-result-downstream | 280.0s | 1 | 28 | 276.1s |
| skill-bpmn-timer | 75.3s | 1 | 11 | 70.7s |
| skill-bpmn-agent-job | 904.9s | 1 | 71 | 900.0s |


## Token Usage

**Total Tokens**: 55,762,847 (input: 79,724, output: 1,325,275)
**Cache Tokens**: write: 2,075,484, read: 52,282,364
**Total Cost**: $43.5861
**Avg Tokens/Task**: 796,612

| Task ID | Input (uncached) | Output | Cache Write | Cache Read | Total | Cost |
|---------|------------------|--------|-------------|------------|-------|------|
| skill-bpmn-event-trigger-start | 4,197 | 16,805 | 30,627 | 580,489 | 632,118 | $0.5537 |
| skill-bpmn-diagnose-job-traces | 17 | 2,822 | 15,572 | 518,888 | 537,299 | $0.2564 |
| skill-bpmn-edit-add-node | 13 | 8,023 | 29,434 | 463,561 | 501,031 | $0.3698 |
| skill-bpmn-message-catch | 4,197 | 8,976 | 31,444 | 572,214 | 616,831 | $0.4368 |
| skill-bpmn-edit-remove-node | 20 | 6,725 | 18,482 | 632,181 | 657,408 | $0.3599 |
| skill-bpmn-hitl-rpa-wrappers | 4,195 | 14,888 | 31,564 | 433,862 | 484,509 | $0.4844 |
| skill-bpmn-hitl-schema-design | 4,203 | 40,020 | 38,948 | 985,733 | 1,068,904 | $1.0547 |
| skill-bpmn-e2e-invoice-exception-triage | 2,897 | 15,406 | 31,064 | 907,335 | 956,702 | $0.6285 |
| skill-bpmn-edit-move-node | 12 | 5,995 | 14,084 | 321,582 | 341,673 | $0.2393 |
| skill-bpmn-diagnose-scoped-variables | 13 | 2,947 | 15,114 | 388,887 | 406,961 | $0.2176 |
| skill-bpmn-hitl-brownfield-insert | 15 | 13,561 | 29,628 | 553,374 | 596,578 | $0.4806 |
| skill-bpmn-calculator | 17 | 21,854 | 33,972 | 697,859 | 753,702 | $0.6646 |
| skill-bpmn-hitl-multi-outcome-routing | 4,207 | 33,662 | 38,765 | 1,188,845 | 1,265,479 | $1.0196 |
| skill-bpmn-script-jint-lifecycle | 2,894 | 15,754 | 26,931 | 747,249 | 792,828 | $0.5702 |
| skill-bpmn-debug-workflow-mocked | 10 | 1,591 | 13,284 | 254,810 | 269,695 | $0.1502 |
| skill-bpmn-timer-boundary-noninterrupting | 14 | 14,847 | 25,993 | 485,832 | 526,686 | $0.4660 |
| skill-bpmn-e2e-live-debug | 3,395 | 11,675 | 36,695 | 1,006,953 | 1,058,718 | $0.6250 |
| skill-bpmn-terminate | 8 | 8,022 | 21,942 | 209,745 | 239,717 | $0.2656 |
| skill-bpmn-diagnose-incident-root-cause | 11 | 2,620 | 38,156 | 303,011 | 343,798 | $0.2733 |
| skill-bpmn-simple-approval-bpmn | 4,195 | 63,283 | 37,462 | 508,180 | 613,120 | $1.2548 |
| skill-bpmn-integration-service-boundary | 4,208 | 26,510 | 41,796 | 1,274,857 | 1,347,371 | $0.9495 |
| skill-bpmn-edit-group-to-subflow | 15 | 23,358 | 29,617 | 558,447 | 611,437 | $0.6290 |
| skill-bpmn-debug-not-validation | 7 | 3,726 | 21,122 | 166,227 | 191,082 | $0.1850 |
| skill-bpmn-http-weather | 4,196 | 15,433 | 29,956 | 519,571 | 569,156 | $0.5123 |
| skill-bpmn-debug-instance-inspect | 12 | 2,384 | 8,199 | 299,876 | 310,471 | $0.1565 |
| skill-bpmn-contract-variant-wrappers | 4,274 | 120,049 | 155,750 | 8,576,621 | 8,856,694 | $4.9706 |
| skill-bpmn-inclusive-gateway-forkjoin | 4,194 | 13,419 | 31,871 | 422,926 | 472,410 | $0.4603 |
| skill-bpmn-hitl-completed-wired | 4,194 | 13,862 | 30,302 | 428,622 | 476,980 | $0.4627 |
| skill-bpmn-dice-roller | 11 | 10,616 | 24,666 | 350,118 | 385,411 | $0.3568 |
| skill-bpmn-script-jint-guidance | 1,717 | 20,199 | 33,966 | 617,334 | 673,216 | $0.6207 |
| skill-bpmn-diagnose-stuck-gateway | 12 | 3,452 | 15,638 | 362,814 | 381,916 | $0.2193 |
| skill-bpmn-hitl-boolean-decision | 1,720 | 56,515 | 34,134 | 859,244 | 951,613 | $1.2387 |
| skill-bpmn-edit-add-output | 12 | 3,452 | 23,956 | 391,743 | 419,163 | $0.2592 |
| skill-bpmn-author-validate | 11 | 8,431 | 22,576 | 342,692 | 373,710 | $0.3140 |
| skill-bpmn-expr-multiinstance-iterator | 23 | 42,372 | 35,317 | 1,035,291 | 1,113,003 | $1.0787 |
| skill-bpmn-operate-diagnose-minimal-fault-triage | 16 | 4,109 | 16,026 | 513,839 | 533,990 | $0.2759 |
| skill-bpmn-diagnose-validate-fix-loop | 7 | 1,427 | 11,239 | 147,828 | 160,501 | $0.1079 |
| skill-bpmn-callactivity-agentic-process | 18 | 9,287 | 31,994 | 692,686 | 733,985 | $0.4671 |
| skill-bpmn-registry-discovery | 19 | 4,033 | 26,889 | 621,033 | 651,974 | $0.3477 |
| skill-bpmn-diagnose-deployed-drift | 7 | 5,615 | 7,009 | 163,389 | 176,020 | $0.1595 |
| skill-bpmn-script-task-map | 9 | 9,176 | 22,133 | 254,198 | 285,516 | $0.2969 |
| skill-bpmn-script-task-group-by | 1,709 | 7,731 | 23,822 | 258,738 | 292,000 | $0.2880 |
| skill-bpmn-switch | 7 | 7,929 | 21,669 | 167,268 | 196,873 | $0.2504 |
| skill-bpmn-e2e-customer-escalation | 2,890 | 22,794 | 31,878 | 590,795 | 648,357 | $0.6474 |
| skill-bpmn-feet-inches | 11 | 15,692 | 24,494 | 347,528 | 387,725 | $0.4315 |
| skill-bpmn-safety-sanitize | 11 | 3,108 | 14,780 | 289,503 | 307,402 | $0.1889 |
| skill-bpmn-expr-computed-js | 21 | 31,156 | 34,819 | 900,949 | 966,945 | $0.8683 |
| skill-bpmn-script-task-filter | 10 | 11,128 | 22,303 | 297,534 | 330,975 | $0.3398 |
| skill-bpmn-parallel-fork-join | 7 | 4,755 | 21,827 | 167,473 | 194,062 | $0.2034 |
| skill-bpmn-event-based-gateway | 12 | 26,707 | 31,251 | 430,367 | 488,337 | $0.6469 |
| skill-bpmn-timer-start | 11 | 12,439 | 27,601 | 370,683 | 410,734 | $0.4013 |
| skill-bpmn-edit-update-node | 11 | 3,975 | 13,515 | 282,805 | 300,306 | $0.1952 |
| skill-bpmn-subprocess | 8 | 8,941 | 21,824 | 209,695 | 240,468 | $0.2789 |
| skill-bpmn-multi-city-weather | 4,208 | 37,142 | 38,857 | 1,227,462 | 1,307,669 | $1.0837 |
| skill-bpmn-error-boundary-handler | 11 | 10,916 | 26,463 | 354,813 | 392,203 | $0.3695 |
| skill-bpmn-loop-multiply | 14 | 27,516 | 25,698 | 492,997 | 546,225 | $0.6570 |
| skill-bpmn-message-send-receive-pair | 82 | 54,436 | 71,717 | 5,326,975 | 5,453,210 | $2.6838 |
| skill-bpmn-reading-list | 26 | 28,574 | 38,098 | 1,231,850 | 1,298,548 | $0.9411 |
| skill-bpmn-queue-create-and-wait | 12 | 6,061 | 25,405 | 398,399 | 429,877 | $0.3057 |
| skill-bpmn-e2e-wiki-pageviews | 20 | 52,659 | 36,586 | 911,922 | 1,001,187 | $1.2007 |
| skill-bpmn-rpa-job | 21 | 18,326 | 35,690 | 928,404 | 982,441 | $0.6873 |
| skill-bpmn-business-rule-task | 2,894 | 11,306 | 28,849 | 768,796 | 811,845 | $0.5171 |
| skill-bpmn-gateway-sequence-flows | 9 | 73,462 | 29,914 | 258,847 | 362,232 | $1.2918 |
| skill-bpmn-smoke-registry-discovery | 35 | 5,173 | 15,830 | 1,102,125 | 1,123,163 | $0.4677 |
| skill-bpmn-api-workflow-task | 22 | 15,869 | 34,868 | 947,218 | 997,977 | $0.6530 |
| skill-bpmn-error-event-subprocess | 10 | 11,167 | 23,323 | 302,405 | 336,905 | $0.3457 |
| skill-bpmn-expr-error-mapping | 17 | 21,544 | 36,575 | 684,946 | 743,082 | $0.6659 |
| skill-bpmn-hitl-result-downstream | 4,198 | 20,226 | 32,578 | 642,539 | 699,541 | $0.6309 |
| skill-bpmn-timer | 8 | 4,441 | 20,807 | 208,585 | 233,841 | $0.2072 |
| skill-bpmn-agent-job | 4,217 | 63,201 | 51,126 | 1,820,797 | 1,939,341 | $1.6986 |


## Command Telemetry

**Total Commands**: 1110
**Success Rate**: 1036/1110 (93.3%)

### Commands by Tool

| Tool | Count | % |
|------|-------|---|
| Bash | 572 | 51.5% |
| Read | 200 | 18.0% |
| Write | 146 | 13.2% |
| Edit | 91 | 8.2% |
| Skill | 63 | 5.7% |
| TaskUpdate | 23 | 2.1% |
| TaskCreate | 12 | 1.1% |
| Glob | 2 | 0.2% |
| Grep | 1 | 0.1% |

### Performance

- **Average Command Time**: 1656.6ms
- **Total Command Time**: 1838.87s

### Slowest Commands

| Tool | Duration | Parameters |
|------|----------|------------|
| Bash | 49497ms | {'command': 'uip maestro bpmn registry get BPMN.Va... |
| Bash | 46996ms | {'command': 'uip maestro bpmn registry get BPMN.Sc... |
| Bash | 43772ms | {'command': 'uip maestro bpmn registry get BPMN.Sc... |
| Bash | 35647ms | {'command': 'uip maestro bpmn registry get Orchest... |
| Bash | 32727ms | {'command': 'uip maestro bpmn registry get Orchest... |

**Most Common Pattern**: `Bash → Bash → Bash`

**Skill Tool Invoked**: 63 time(s)

## Agent Settings

- **Permission Mode**: acceptEdits
- **Allowed Tools**: Skill, Bash, Read, Write, Edit, Glob, Grep
- **Model**: us.anthropic.claude-sonnet-4-6
- **Max Turns**: 80
- **System Prompt**: You are a coding agent. Do not access files in sibling runs/* directories. Everywhere else is permitted. 
- **Plugins**: /home/azureuser/projects/skills

## Environment

- **git_commit**: acc1c86
- **skills_git_commit**: ade6a64c6
- **cli_version**: 1.201.0-dev.8272
- **tool_plugins**: {'admin-tool': '1.201.0-dev.8272', 'agent-tool': '1.201.0-dev.8272', 'agenthub-tool': '1.201.0-dev.8272', 'aops-tool': '1.201.0-dev.8272', 'api-workflow-tool': '1.201.0-dev.8272', 'automation-hub-tool': '1.201.0-dev.8272', 'codedagent-tool': '1.201.0-dev.8272', 'codedapp-tool': '1.201.0-dev.8272', 'coder-tool': '1.201.0-dev.8272', 'context-grounding-tool': '1.201.0-dev.8272', 'conversational-tool': '1.201.0-dev.8272', 'data-fabric-tool': '1.201.0-dev.8272', 'docsai-tool': '1.201.0-dev.8272', 'function-tool': '1.201.0-dev.8272', 'gov-tool': '1.201.0-dev.8272', 'guardrails-tool': '1.201.0-dev.8272', 'insights-tool': '1.201.0-dev.8276', 'integrationservice-tool': '1.201.0-dev.8272', 'ixp-tool': '1.201.0-dev.8272', 'llm-gateway-tool': '1.201.0-dev.8272', 'llmgw-tool': '1.201.0-dev.8272', 'maestro-tool': '1.201.0-dev.8275', 'model-hub-tool': '1.201.0-dev.8272', 'orchestrator-tool': '1.201.0-dev.8272', 'platform-tool': '1.201.0-dev.8272', 'pm-tool': '1.201.0-dev.8272', 'rpa-legacy-tool': '1.201.0-dev.8272', 'rpa-tool': '1.201.0-dev.20260809.3', 'solution-tool': '1.201.0-dev.8272', 'tasks-tool': '1.201.0-dev.8272', 'test-manager-tool': '1.201.0-dev.8272', 'traces-tool': '1.201.0-dev.8272', 'vertical-solutions-tool': '1.201.0-dev.8272'}
- **coder_eval**: 0.8.8
- **claude_code_cli**: 2.1.233 (Claude Code)
- **uv**: uv 0.11.21 (x86_64-unknown-linux-gnu)
- **anthropic**: 0.102.0
- **openai**: Not Installed
- **pydantic**: 2.12.5