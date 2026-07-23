# Evaluation Run Report

**Run ID**: `maestro-bpmn-baseline-report-1`
**Date**: 2026-07-21 00:52:23
**Duration**: 903.52s
**Model**: `claude-sonnet-4-6`

## Summary

- **Total Tasks**: 48
- **Succeeded**: 47
- **Failed**: 1
- **Errors**: 0
- **Success Rate**: 97.9%
- **Avg Reliability Score**: 0.979
- **Avg Generation Latency**: 290.8s
- **Total Assistant Turns**: 1637

## Task Details

| Task ID | Status | Reliability Score | Latency | Model | Tags |
|---------|--------|-------------------|---------|-------|------|
| skill-bpmn-script-jint-guidance | SUCCESS | 1.000 | 143.2s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:single-node, node:script |
| skill-bpmn-transform-group-by | SUCCESS | 1.000 | 171.6s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:single-node, node:script, feature:transform |
| skill-bpmn-operate-diagnose-minimal-fault-triage | SUCCESS | 1.000 | 75.7s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:diagnose, lifecycle:execute |
| skill-bpmn-loop-multiply | SUCCESS | 1.000 | 310.1s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:loop |
| skill-bpmn-hitl-rpa-wrappers | SUCCESS | 1.000 | 276.7s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, resource |
| skill-bpmn-edit-update-node | SUCCESS | 1.000 | 47.8s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node |
| skill-bpmn-edit-add-node | SUCCESS | 1.000 | 102.3s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node |
| skill-bpmn-gateway-sequence-flows | SUCCESS | 1.000 | 255.1s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:multi-node, node:gateway |
| skill-bpmn-e2e-customer-escalation | SUCCESS | 1.000 | 289.3s | claude-sonnet-4-6 | uipath-maestro-bpmn, e2e, mode:build, lifecycle:generate, shape:multi-node, node:decision, node:hitl, feature:escalation |
| skill-bpmn-reading-list | SUCCESS | 1.000 | 400.3s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:transform |
| skill-bpmn-message-catch | SUCCESS | 1.000 | 240.7s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, feature:trigger |
| skill-bpmn-feet-inches | SUCCESS | 1.000 | 498.4s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node |
| skill-bpmn-edit-move-node | SUCCESS | 1.000 | 59.3s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node |
| skill-bpmn-hitl-completed-wired | SUCCESS | 1.000 | 227.0s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:multi-node, node:hitl, feature:approval-gate |
| skill-bpmn-script-jint-lifecycle | SUCCESS | 1.000 | 266.4s | claude-sonnet-4-6 | uipath-maestro-bpmn, e2e, lifecycle:generate, node:script, feature:jint |
| skill-bpmn-e2e-wiki-pageviews | SUCCESS | 1.000 | 656.7s | claude-sonnet-4-6 | uipath-maestro-bpmn, e2e, mode:build, lifecycle:generate, shape:multi-node, node:decision, node:transform |
| skill-bpmn-transform-map | SUCCESS | 1.000 | 205.7s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:single-node, node:script, feature:transform |
| skill-bpmn-agent-job | SUCCESS | 1.000 | 381.7s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:single-node, resource |
| skill-bpmn-subprocess | SUCCESS | 1.000 | 182.2s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:subflow |
| skill-bpmn-edit-add-output | SUCCESS | 1.000 | 55.8s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node |
| skill-bpmn-hitl-multi-outcome-routing | SUCCESS | 1.000 | 748.9s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:multi-node, node:hitl, node:decision, feature:approval-gate |
| skill-bpmn-smoke-registry-discovery | SUCCESS | 1.000 | 46.0s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build |
| skill-bpmn-hitl-schema-design | SUCCESS | 1.000 | 492.5s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, feature:approval-gate |
| skill-bpmn-integration-service-boundary | SUCCESS | 1.000 | 465.0s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, connector, feature:connections |
| skill-bpmn-timer | SUCCESS | 1.000 | 74.4s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:single-node, feature:timer |
| skill-bpmn-calculator | SUCCESS | 1.000 | 439.0s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:decision |
| skill-bpmn-event-trigger-start | SUCCESS | 1.000 | 179.1s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:single-node, connector, feature:trigger |
| skill-bpmn-business-rule-task | SUCCESS | 1.000 | 286.8s | claude-sonnet-4-6 | uipath-maestro-bpmn, e2e, lifecycle:generate, node:business-rule, feature:orchestrator |
| skill-bpmn-author-validate | SUCCESS | 1.000 | 158.3s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate |
| skill-bpmn-edit-remove-node | SUCCESS | 1.000 | 102.3s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node |
| skill-bpmn-simple-approval-bpmn | SUCCESS | 1.000 | 743.2s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, lifecycle:generate, shape:multi-node, node:gateway, node:script, node:service-task, resource |
| skill-bpmn-e2e-invoice-exception-triage | SUCCESS | 1.000 | 237.7s | claude-sonnet-4-6 | uipath-maestro-bpmn, e2e, mode:build, lifecycle:generate, shape:multi-node, node:decision, node:hitl, feature:approval-gate |
| skill-bpmn-edit-group-to-subflow | SUCCESS | 1.000 | 539.0s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:subflow |
| skill-bpmn-switch | SUCCESS | 1.000 | 94.1s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:switch |
| skill-bpmn-http-weather | SUCCESS | 1.000 | 195.8s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:single-node, feature:http |
| skill-bpmn-registry-discovery | SUCCESS | 1.000 | 151.8s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, lifecycle:inspect, connector, feature:connections, resource |
| skill-bpmn-api-workflow-task | SUCCESS | 1.000 | 383.6s | claude-sonnet-4-6 | uipath-maestro-bpmn, e2e, lifecycle:generate, node:service-task, feature:api-workflow |
| skill-bpmn-hitl-brownfield-insert | SUCCESS | 1.000 | 139.9s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, feature:approval-gate |
| skill-bpmn-hitl-result-downstream | SUCCESS | 1.000 | 458.0s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, node:decision, feature:approval-gate |
| skill-bpmn-rpa-job | SUCCESS | 1.000 | 148.0s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:single-node, resource |
| skill-bpmn-multi-city-weather | SUCCESS | 1.000 | 420.9s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:loop |
| skill-bpmn-hitl-boolean-decision | SUCCESS | 1.000 | 763.7s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, node:decision, feature:approval-gate |
| skill-bpmn-terminate | SUCCESS | 1.000 | 160.7s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:terminate |
| skill-bpmn-transform-filter | SUCCESS | 1.000 | 130.6s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:single-node, node:script, feature:transform |
| skill-bpmn-parallel-fork-join | SUCCESS | 1.000 | 133.5s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, shape:multi-node, node:gateway, feature:parallel-tasks |
| skill-bpmn-timer-start | SUCCESS | 1.000 | 324.8s | claude-sonnet-4-6 | uipath-maestro-bpmn, smoke, mode:build, lifecycle:generate, feature:trigger |
| skill-bpmn-dice-roller | SUCCESS | 1.000 | 191.1s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, mode:build, lifecycle:generate, shape:multi-node, node:decision |
| skill-bpmn-contract-variant-wrappers | TIMEOUT | 0.000 | 901.3s | claude-sonnet-4-6 | uipath-maestro-bpmn, integration, lifecycle:generate, contract:xml, node:service-task, node:call-activity, connector |

## Run-time Notes

> **WARNING:** [skill-bpmn-script-jint-guidance] expected_turns exceeded: 22/15 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-operate-diagnose-minimal-fault-triage] expected_turns exceeded: 18/16 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-loop-multiply] expected_turns exceeded: 28/22 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-hitl-rpa-wrappers] expected_turns exceeded: 29/14 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-e2e-customer-escalation] expected_turns exceeded: 32/28 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-reading-list] expected_turns exceeded: 24/22 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-message-catch] expected_turns exceeded: 36/16 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-feet-inches] expected_turns exceeded: 30/22 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-script-jint-lifecycle] expected_turns exceeded: 31/22 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-e2e-wiki-pageviews] expected_turns exceeded: 30/28 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-agent-job] expected_turns exceeded: 20/16 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-hitl-multi-outcome-routing] expected_turns exceeded: 39/24 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-hitl-schema-design] expected_turns exceeded: 23/22 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-integration-service-boundary] expected_turns exceeded: 30/19 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-calculator] expected_turns exceeded: 34/22 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-business-rule-task] expected_turns exceeded: 35/28 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-author-validate] expected_turns exceeded: 25/20 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-edit-remove-node] expected_turns exceeded: 29/18 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-simple-approval-bpmn] expected_turns exceeded: 26/24 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-e2e-invoice-exception-triage] max_turns exhausted
> **WARNING:** [skill-bpmn-e2e-invoice-exception-triage] expected_turns exceeded: 42/25 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-http-weather] expected_turns exceeded: 31/16 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-registry-discovery] expected_turns exceeded: 33/28 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-api-workflow-task] max_turns exhausted
> **WARNING:** [skill-bpmn-api-workflow-task] expected_turns exceeded: 45/32 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-hitl-brownfield-insert] expected_turns exceeded: 23/22 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-hitl-result-downstream] expected_turns exceeded: 34/24 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-multi-city-weather] expected_turns exceeded: 25/22 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-hitl-boolean-decision] expected_turns exceeded: 31/24 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-timer-start] expected_turns exceeded: 34/18 (cumulative SDK turns)
> **WARNING:** [skill-bpmn-dice-roller] expected_turns exceeded: 25/20 (cumulative SDK turns)


## Generation Metrics

| Task ID | Total Latency | Turns | Asst Turns | Avg Turn Latency |
|---------|---------------|-------|------------|------------------|
| skill-bpmn-script-jint-guidance | 143.2s | 1 | 32 | 141.4s |
| skill-bpmn-transform-group-by | 171.6s | 1 | 22 | 167.0s |
| skill-bpmn-operate-diagnose-minimal-fault-triage | 75.7s | 1 | 23 | 66.1s |
| skill-bpmn-loop-multiply | 310.1s | 1 | 43 | 305.8s |
| skill-bpmn-hitl-rpa-wrappers | 276.7s | 1 | 42 | 275.1s |
| skill-bpmn-edit-update-node | 47.8s | 1 | 16 | 42.6s |
| skill-bpmn-edit-add-node | 102.3s | 1 | 28 | 97.7s |
| skill-bpmn-gateway-sequence-flows | 255.1s | 1 | 27 | 253.5s |
| skill-bpmn-e2e-customer-escalation | 289.3s | 1 | 46 | 281.0s |
| skill-bpmn-reading-list | 400.3s | 1 | 39 | 398.9s |
| skill-bpmn-message-catch | 240.7s | 1 | 51 | 238.7s |
| skill-bpmn-feet-inches | 498.4s | 1 | 49 | 496.8s |
| skill-bpmn-edit-move-node | 59.3s | 1 | 18 | 57.7s |
| skill-bpmn-hitl-completed-wired | 227.0s | 1 | 25 | 222.4s |
| skill-bpmn-script-jint-lifecycle | 266.4s | 1 | 39 | 264.7s |
| skill-bpmn-e2e-wiki-pageviews | 656.7s | 1 | 42 | 644.9s |
| skill-bpmn-transform-map | 205.7s | 1 | 23 | 203.9s |
| skill-bpmn-agent-job | 381.7s | 1 | 33 | 379.9s |
| skill-bpmn-subprocess | 182.2s | 1 | 20 | 174.2s |
| skill-bpmn-edit-add-output | 55.8s | 1 | 23 | 54.1s |
| skill-bpmn-hitl-multi-outcome-routing | 748.9s | 1 | 54 | 744.6s |
| skill-bpmn-smoke-registry-discovery | 46.0s | 1 | 15 | 45.4s |
| skill-bpmn-hitl-schema-design | 492.5s | 1 | 36 | 488.0s |
| skill-bpmn-integration-service-boundary | 465.0s | 1 | 48 | 463.6s |
| skill-bpmn-timer | 74.4s | 1 | 11 | 69.3s |
| skill-bpmn-calculator | 439.0s | 1 | 48 | 437.4s |
| skill-bpmn-event-trigger-start | 179.1s | 1 | 26 | 170.1s |
| skill-bpmn-business-rule-task | 286.8s | 1 | 51 | 285.2s |
| skill-bpmn-author-validate | 158.3s | 1 | 32 | 156.5s |
| skill-bpmn-edit-remove-node | 102.3s | 1 | 44 | 100.7s |
| skill-bpmn-simple-approval-bpmn | 743.2s | 1 | 42 | 741.8s |
| skill-bpmn-e2e-invoice-exception-triage | 237.7s | 1 | 60 | 228.7s |
| skill-bpmn-edit-group-to-subflow | 539.0s | 1 | 33 | 534.2s |
| skill-bpmn-switch | 94.1s | 1 | 12 | 87.8s |
| skill-bpmn-http-weather | 195.8s | 1 | 43 | 194.1s |
| skill-bpmn-registry-discovery | 151.8s | 1 | 41 | 150.2s |
| skill-bpmn-api-workflow-task | 383.6s | 1 | 64 | 382.1s |
| skill-bpmn-hitl-brownfield-insert | 139.9s | 1 | 34 | 138.2s |
| skill-bpmn-hitl-result-downstream | 458.0s | 1 | 45 | 453.8s |
| skill-bpmn-rpa-job | 148.0s | 1 | 22 | 146.2s |
| skill-bpmn-multi-city-weather | 420.9s | 1 | 38 | 419.3s |
| skill-bpmn-hitl-boolean-decision | 763.7s | 1 | 53 | 762.1s |
| skill-bpmn-terminate | 160.7s | 1 | 22 | 150.1s |
| skill-bpmn-transform-filter | 130.6s | 1 | 19 | 126.4s |
| skill-bpmn-parallel-fork-join | 133.5s | 1 | 25 | 129.2s |
| skill-bpmn-timer-start | 324.8s | 1 | 42 | 320.6s |
| skill-bpmn-dice-roller | 191.1s | 1 | 36 | 189.4s |
| skill-bpmn-contract-variant-wrappers | 901.3s | 0 | 0 | N/A |


## Token Usage

**Total Tokens**: 42,305,613 (input: 102,261, output: 922,995)
**Cache Tokens**: write: 1,546,735, read: 39,733,622
**Total Cost**: $31.8721
**Avg Tokens/Task**: 900,119

| Task ID | Input (uncached) | Output | Cache Write | Cache Read | Total | Cost |
|---------|------------------|--------|-------------|------------|-------|------|
| skill-bpmn-script-jint-guidance | 1,442 | 8,802 | 27,382 | 818,702 | 856,328 | $0.4846 |
| skill-bpmn-transform-group-by | 3,670 | 10,546 | 26,053 | 491,162 | 531,431 | $0.4142 |
| skill-bpmn-operate-diagnose-minimal-fault-triage | 21 | 3,436 | 13,971 | 524,057 | 541,485 | $0.2612 |
| skill-bpmn-loop-multiply | 3,681 | 19,329 | 31,735 | 1,030,307 | 1,085,052 | $0.7291 |
| skill-bpmn-hitl-rpa-wrappers | 4,266 | 20,277 | 40,832 | 1,032,251 | 1,097,626 | $0.7797 |
| skill-bpmn-edit-update-node | 12 | 1,523 | 10,067 | 262,189 | 273,791 | $0.1393 |
| skill-bpmn-edit-add-node | 19 | 5,996 | 44,550 | 628,270 | 678,835 | $0.4455 |
| skill-bpmn-gateway-sequence-flows | 3,674 | 21,289 | 29,735 | 696,392 | 751,090 | $0.6508 |
| skill-bpmn-e2e-customer-escalation | 4,570 | 21,290 | 38,417 | 1,133,360 | 1,197,637 | $0.8171 |
| skill-bpmn-reading-list | 1,442 | 29,799 | 28,537 | 878,999 | 938,777 | $0.8220 |
| skill-bpmn-message-catch | 3,692 | 15,278 | 32,353 | 1,500,167 | 1,551,490 | $0.8116 |
| skill-bpmn-feet-inches | 5,184 | 38,325 | 44,801 | 1,164,321 | 1,252,631 | $1.1077 |
| skill-bpmn-edit-move-node | 13 | 4,663 | 11,413 | 300,583 | 316,672 | $0.2030 |
| skill-bpmn-hitl-completed-wired | 3,675 | 14,710 | 46,978 | 654,531 | 719,894 | $0.6042 |
| skill-bpmn-script-jint-lifecycle | 5,985 | 17,904 | 35,649 | 1,249,934 | 1,309,472 | $0.7952 |
| skill-bpmn-e2e-wiki-pageviews | 921 | 50,466 | 35,234 | 1,094,014 | 1,180,635 | $1.2201 |
| skill-bpmn-transform-map | 3,671 | 14,648 | 27,733 | 518,812 | 564,864 | $0.4904 |
| skill-bpmn-agent-job | 21 | 27,823 | 31,048 | 779,308 | 838,200 | $0.7676 |
| skill-bpmn-subprocess | 15 | 13,010 | 22,314 | 445,587 | 480,926 | $0.4125 |
| skill-bpmn-edit-add-output | 16 | 3,065 | 21,664 | 484,252 | 508,997 | $0.2725 |
| skill-bpmn-hitl-multi-outcome-routing | 1,547 | 54,686 | 51,845 | 1,244,336 | 1,352,414 | $1.3927 |
| skill-bpmn-smoke-registry-discovery | 10 | 1,976 | 16,415 | 221,014 | 239,415 | $0.1575 |
| skill-bpmn-hitl-schema-design | 3,677 | 36,203 | 55,388 | 842,165 | 937,433 | $1.0144 |
| skill-bpmn-integration-service-boundary | 3,683 | 31,011 | 40,610 | 1,161,461 | 1,236,765 | $0.9769 |
| skill-bpmn-timer | 8 | 5,120 | 17,514 | 172,391 | 195,033 | $0.1942 |
| skill-bpmn-calculator | 4,874 | 33,882 | 39,571 | 1,396,829 | 1,475,156 | $1.0903 |
| skill-bpmn-event-trigger-start | 15 | 11,851 | 26,999 | 488,281 | 527,146 | $0.4255 |
| skill-bpmn-business-rule-task | 6,384 | 19,024 | 40,628 | 1,417,380 | 1,483,416 | $0.8821 |
| skill-bpmn-author-validate | 3,679 | 9,857 | 26,085 | 859,553 | 899,174 | $0.5146 |
| skill-bpmn-edit-remove-node | 31 | 6,625 | 19,557 | 910,794 | 937,007 | $0.4460 |
| skill-bpmn-simple-approval-bpmn | 3,679 | 55,605 | 32,944 | 964,552 | 1,056,780 | $1.2580 |
| skill-bpmn-e2e-invoice-exception-triage | 936 | 15,985 | 43,311 | 1,954,719 | 2,014,951 | $0.9914 |
| skill-bpmn-edit-group-to-subflow | 21 | 39,355 | 36,157 | 869,947 | 945,480 | $0.9870 |
| skill-bpmn-switch | 9 | 7,578 | 18,826 | 211,988 | 238,401 | $0.2479 |
| skill-bpmn-http-weather | 64 | 12,156 | 30,085 | 1,035,061 | 1,077,366 | $0.6059 |
| skill-bpmn-registry-discovery | 27 | 11,923 | 30,775 | 869,035 | 911,760 | $0.5550 |
| skill-bpmn-api-workflow-task | 11,461 | 25,572 | 54,408 | 1,598,733 | 1,690,174 | $1.1016 |
| skill-bpmn-hitl-brownfield-insert | 23 | 9,675 | 28,968 | 803,226 | 841,892 | $0.4948 |
| skill-bpmn-hitl-result-downstream | 80 | 32,560 | 50,520 | 1,093,034 | 1,176,194 | $1.0060 |
| skill-bpmn-rpa-job | 14 | 10,077 | 25,615 | 439,201 | 474,907 | $0.3790 |
| skill-bpmn-multi-city-weather | 3,679 | 28,442 | 36,583 | 948,835 | 1,017,539 | $0.8595 |
| skill-bpmn-hitl-boolean-decision | 4,058 | 59,612 | 42,780 | 1,156,782 | 1,263,232 | $1.4138 |
| skill-bpmn-terminate | 16 | 9,006 | 20,870 | 483,994 | 513,886 | $0.3586 |
| skill-bpmn-transform-filter | 3,668 | 8,293 | 42,826 | 372,422 | 427,209 | $0.4077 |
| skill-bpmn-parallel-fork-join | 19 | 10,148 | 39,980 | 581,342 | 631,489 | $0.4766 |
| skill-bpmn-timer-start | 36 | 22,850 | 43,110 | 1,065,253 | 1,131,249 | $0.8241 |
| skill-bpmn-dice-roller | 4,573 | 11,744 | 33,899 | 884,096 | 934,312 | $0.5822 |


## Command Telemetry

**Total Commands**: 1064
**Success Rate**: 973/1064 (91.4%)

### Commands by Tool

| Tool | Count | % |
|------|-------|---|
| Bash | 580 | 54.5% |
| Read | 182 | 17.1% |
| Write | 105 | 9.9% |
| TaskUpdate | 67 | 6.3% |
| Skill | 47 | 4.4% |
| TaskCreate | 34 | 3.2% |
| Glob | 26 | 2.4% |
| Edit | 23 | 2.2% |

### Performance

- **Average Command Time**: 647.8ms
- **Total Command Time**: 689.24s

### Slowest Commands

| Tool | Duration | Parameters |
|------|----------|------------|
| Write | 18493ms | {'file_path': '/work/output/artifacts/skill-bpmn-r... |
| Bash | 16675ms | {'command': 'cd /home/azureuser/projects/skills/sk... |
| Bash | 12738ms | {'command': 'cd /home/azureuser/projects/skills/sk... |
| Write | 12511ms | {'file_path': '/work/output/artifacts/skill-bpmn-r... |
| Bash | 11250ms | {'command': 'cd /home/azureuser/projects/skills/sk... |

**Most Common Pattern**: `Bash → Bash → Bash`

**Skill Tool Invoked**: 47 time(s)

## Agent Settings

- **Permission Mode**: acceptEdits
- **Allowed Tools**: Skill, Bash, Read, Write, Edit, Glob, Grep
- **Model**: us.anthropic.claude-sonnet-4-6
- **Max Turns**: 60
- **System Prompt**: You are a coding agent. Do not access files in sibling runs/* directories. Everywhere else is permitted. 
- **Plugins**: /home/azureuser/projects/skills

## Environment

- **git_commit**: 252722a
- **skills_git_commit**: 0fc8174d
- **cli_version**: 1.197.0-alpha.20260626.7673 | 1.199.0-dev.7923
- **tool_plugins**: {'agent-tool': '1.197.0 | 1.197.0-alpha.20260626.7673 | 1.199.0-dev.7923', 'agenthub-tool': '1.197.0 | 1.197.0-alpha.20260626.7673 | 1.199.0-dev.7923', 'codedagent-tool': '1.197.0 | 1.197.0-alpha.20260626.7673 | 1.199.0-dev.7923', 'data-fabric-tool': '1.197.0 | 1.197.0-alpha.20260626.7673 | 1.199.0-dev.7923', 'functions-tool': '1.197.0 | 1.197.0-alpha.20260626.7673 | 1.199.0-dev.7923', 'gov-tool': '1.197.0 | 1.197.0-alpha.20260626.7673 | 1.199.0-dev.7923', 'insights-tool': '1.197.0 | 1.197.0-alpha.20260626.7673 | 1.199.0-dev.7923', 'integrationservice-tool': '1.197.0 | 1.197.0-alpha.20260626.7673 | 1.199.0-dev.7923', 'ixp-tool': '1.197.0 | 1.197.0-alpha.20260626.7673 | 1.199.0-dev.7923', 'maestro-tool': '1.197.0 | 1.197.0-alpha.20260626.7673 | 1.199.0-dev.7924', 'orchestrator-tool': '1.197.0 | 1.197.0-alpha.20260626.7673 | 1.199.0-dev.7923', 'solution-tool': '1.197.0 | 1.197.0-alpha.20260626.7673 | 1.199.0-dev.7923', 'tasks-tool': '1.197.0 | 1.197.0-alpha.20260626.7673 | 1.199.0-dev.7923', 'test-manager-tool': '1.197.0 | 1.197.0-alpha.20260626.7673 | 1.199.0-dev.7923'}
- **coder_eval**: 0.8.4
- **claude_code_cli**: 2.1.216 (Claude Code)
- **uv**: uv 0.11.21 (x86_64-unknown-linux-gnu)
- **anthropic**: 0.102.0
- **openai**: Not Installed
- **pydantic**: 2.12.5