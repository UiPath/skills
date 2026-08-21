# Evaluation Run Report

**Run ID**: `maestro-flow-optimized-sonnet-5`
**Date**: 2026-08-19 00:07:04
**Duration**: 2620.89s
**Model**: `claude-sonnet-5`

## Summary

- **Total Tasks**: 127
- **Succeeded**: 110
- **Failed**: 16
- **Errors**: 1
- **Pass Rate**: 86.6% (110/127)
- **Error Share**: 0.8% of tasks never produced a gradeable attempt and count as misses
- **Avg Reliability Score**: 0.912
- **Avg Generation Latency**: 397.0s
- **Total Assistant Turns**: 8771
- **Crashed Partials**: 3 (1 recovered, 2 terminal)

## Task Details

| Task ID | Status | Reliability Score | Latency | Model | Tags |
|---------|--------|-------------------|---------|-------|------|
| skill-flow-bellevue-weather-simulated | SUCCESS | 0.889 | 531.1s | claude-sonnet-5 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, node:decision, feature:http, ipe, simulation |
| skill-flow-group-to-subflow | TIMEOUT | 0.000 | 910.0s | claude-sonnet-5 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:subflow |
| skill-flow-ixp-invoice-extraction-simulated | SUCCESS | 0.900 | 1341.1s | claude-sonnet-5 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, node:ixp, connector, feature:http, simulation |
| skill-flow-trigger-with-filter | SUCCESS | 1.000 | 59.8s | claude-sonnet-5 | uipath-maestro-flow, smoke, mode:build, lifecycle:discover, connector-trigger, uipath-microsoft-outlook365, filter, ipe |
| skill-flow-slack-http-fallback | SUCCESS | 1.000 | 303.2s | claude-sonnet-5 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:single-node, connector, uipath-salesforce-slack, feature:http, ipe |
| skill-flow-customer-escalation | FAILURE | 0.333 | 868.9s | claude-sonnet-5 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:decision, feature:trigger, connector |
| skill-flow-hitl-schema-design-simulated | SUCCESS | 1.000 | 672.5s | claude-sonnet-5 | uipath-maestro-flow, uipath-human-in-the-loop, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, simulation |
| skill-flow-add-output | SUCCESS | 1.000 | 225.2s | claude-sonnet-5 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node |
| skill-flow-ipe-jira-get-issue | SUCCESS | 1.000 | 289.4s | claude-sonnet-5 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-ixp-scaffold-multinode | MAX_TURNS_EXHAUSTED | 0.483 | 584.7s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, node:ixp |
| skill-flow-hitl-smoke-completed-port | SUCCESS | 1.000 | 322.1s | claude-sonnet-5 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, mode:build, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-ipe-jira-create-issue | SUCCESS | 1.000 | 302.1s | claude-sonnet-5 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-ipe-jira-search-triage | SUCCESS | 1.000 | 429.9s | claude-sonnet-5 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:loop, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-ipe-dtl-load-by-default-true | FAILURE | 0.750 | 463.6s | claude-sonnet-5 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-microsoft-azure, ipe, mode:build |
| skill-flow-delay | SUCCESS | 1.000 | 135.8s | claude-sonnet-5 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:delay |
| skill-flow-hitl-quality-result-downstream | SUCCESS | 1.000 | 451.5s | claude-sonnet-5 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-hitl-smoke-node-placed | SUCCESS | 1.000 | 324.9s | claude-sonnet-5 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, lifecycle:generate, shape:single-node, node:hitl |
| skill-flow-generic-dynamic-node | SUCCESS | 1.000 | 311.3s | claude-sonnet-5 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node, connector, uipath-servicenow-servicenow, ipe |
| skill-flow-eval-simulation-crud | SUCCESS | 1.000 | 112.4s | claude-sonnet-5 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, feature:eval |
| skill-flow-feet-inches | SUCCESS | 1.000 | 391.6s | claude-sonnet-5 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:switch |
| skill-flow-ixp-integration-handle-routing | SUCCESS | 1.000 | 781.0s | claude-sonnet-5 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:ixp, node:decision |
| skill-flow-file-attachment-debug | FAILURE | 0.500 | 187.9s | claude-sonnet-5 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node |
| skill-flow-devcon-billing-discrepancy-detector | SUCCESS | 1.000 | 1326.1s | claude-sonnet-5 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, connector, path-to-ga |
| skill-flow-hitl-smoke-multi-outcome-routing | SUCCESS | 1.000 | 341.5s | claude-sonnet-5 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-remove-node | SUCCESS | 1.000 | 142.9s | claude-sonnet-5 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node |
| skill-flow-calculator | SUCCESS | 1.000 | 150.6s | claude-sonnet-5 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node |
| skill-flow-e2e-escalation-jira-ticket | FAILURE | 0.684 | 494.1s | claude-sonnet-5 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, connector, feature:escalation |
| skill-flow-bindings-reconfigure-different-connection | SUCCESS | 1.000 | 326.5s | claude-sonnet-5 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-move-node | MAX_TURNS_EXHAUSTED | 0.375 | 633.2s | claude-sonnet-5 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:decision |
| skill-flow-customer-escalation-simulated | SUCCESS | 1.000 | 1693.4s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, node:decision, feature:trigger, connector, simulation |
| skill-flow-ipe-enhanced-enum | SUCCESS | 1.000 | 561.2s | claude-sonnet-5 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-automaticc-woocommerce, ipe, mode:build |
| skill-flow-eval-inline-agent | SUCCESS | 1.000 | 356.4s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:inline-agent, feature:eval |
| skill-flow-ipe-required-groups | SUCCESS | 1.000 | 1025.2s | claude-sonnet-5 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-microsoft-teams, ipe, mode:build |
| skill-flow-hitl-quality-schema-design | SUCCESS | 1.000 | 345.6s | claude-sonnet-5 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-decision | SUCCESS | 1.000 | 248.2s | claude-sonnet-5 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:decision |
| skill-flow-switch | SUCCESS | 1.000 | 204.0s | claude-sonnet-5 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:switch |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | ERROR | 0.000 | 1203.1s | claude-sonnet-5 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, node:ixp, connector, feature:http |
| skill-flow-ipe-searchable-joins | SUCCESS | 1.000 | 660.7s | claude-sonnet-5 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-salesforce, ipe, mode:build |
| skill-flow-multi-city-weather | MAX_TURNS_EXHAUSTED | 0.000 | 832.5s | claude-sonnet-5 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:loop, feature:http |
| skill-flow-eval-local-crud | SUCCESS | 1.000 | 84.7s | claude-sonnet-5 | uipath-maestro-flow, mode:build, lifecycle:generate, feature:eval |
| skill-flow-ixp-routing-negative/stripe-http | SUCCESS | 1.000 | 170.4s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/slack-summary | SUCCESS | 1.000 | 132.0s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/sf-update | SUCCESS | 1.000 | 291.8s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/http-webhook | SUCCESS | 1.000 | 260.3s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/gsheet-loop | SUCCESS | 1.000 | 327.9s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/queue-write | SUCCESS | 1.000 | 257.7s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/teams-decision | SUCCESS | 1.000 | 186.5s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/delay-email | SUCCESS | 1.000 | 200.6s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ipe-ceql-where | SUCCESS | 1.000 | 412.5s | claude-sonnet-5 | uipath-maestro-flow, integration, connector, ceql, filter, uipath-microsoft-azureactivedirectory, ipe, mode:build |
| skill-flow-bindings-no-duplicates | SUCCESS | 1.000 | 205.8s | claude-sonnet-5 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-e2e-devcon-expense-approval | SUCCESS | 1.000 | 460.8s | claude-sonnet-5 | uipath-maestro-flow, uipath-human-in-the-loop, e2e, devcon |
| skill-flow-ixp-scaffold-minimal | SUCCESS | 1.000 | 366.6s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-add-node | SUCCESS | 1.000 | 159.8s | claude-sonnet-5 | uipath-maestro-flow, e2e, mode:build, lifecycle:edit, shape:multi-node |
| skill-flow-transform-group-by | SUCCESS | 1.000 | 162.8s | claude-sonnet-5 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-e2e-escalation-orchestrator-paths | SUCCESS | 1.000 | 1098.3s | claude-sonnet-5 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, node:decision, connector, feature:escalation |
| skill-flow-eval-evaluator-type-choice | SUCCESS | 1.000 | 85.4s | claude-sonnet-5 | uipath-maestro-flow, smoke, mode:build, lifecycle:discover, feature:eval |
| skill-flow-openmeteo-weather | SUCCESS | 1.000 | 216.6s | claude-sonnet-5 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node, connector, custom-codereval-openmeteoapis, ipe, custom-connector |
| skill-flow-devcon-billing-dispute-resolution | SUCCESS | 1.000 | 2219.1s | claude-sonnet-5 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, node:ixp, connector, path-to-ga |
| skill-flow-devcon-billing-dispute-analyst | FAILURE | 0.500 | 662.0s | claude-sonnet-5 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, path-to-ga |
| skill-flow-outlook-trigger-inbox | SUCCESS | 1.000 | 265.7s | claude-sonnet-5 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, feature:trigger, connector, mode:build, ipe |
| skill-flow-api-workflow | SUCCESS | 1.000 | 218.0s | claude-sonnet-5 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-bindings-idempotent-reconfigure | SUCCESS | 1.000 | 353.1s | claude-sonnet-5 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-e2e-escalation-slack-alert | SUCCESS | 1.000 | 530.1s | claude-sonnet-5 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, connector, feature:escalation |
| skill-flow-jdbc-databricks-query | SUCCESS | 1.000 | 607.4s | claude-sonnet-5 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:single-node, connector, uipath-uipath-jdbc, ipe |
| skill-flow-scheduled-trigger | FAILURE | 0.375 | 185.6s | claude-sonnet-5 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:scheduled-trigger, feature:trigger |
| skill-flow-webhook-waitfor-parallel | SUCCESS | 1.000 | 204.1s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, connector, feature:trigger, feature:http, wait-for-event, uipath-http-webhook, ipe |
| skill-flow-dice-roller | SUCCESS | 1.000 | 150.3s | claude-sonnet-5 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node |
| skill-flow-hitl-quality-boolean-decision | SUCCESS | 1.000 | 741.9s | claude-sonnet-5 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-loop-multiply | MAX_TURNS_EXHAUSTED | 0.625 | 562.3s | claude-sonnet-5 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:loop |
| skill-flow-coded-agent | FAILURE | 0.375 | 676.7s | claude-sonnet-5 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:single-node, resource, path-to-ga |
| skill-flow-transform-map | SUCCESS | 1.000 | 180.6s | claude-sonnet-5 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-reading-list | SUCCESS | 1.000 | 215.6s | claude-sonnet-5 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:transform |
| skill-flow-ixp-routing/explicit | SUCCESS | 1.000 | 755.8s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/invoice-extraction | SUCCESS | 1.000 | 571.1s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/receipts | FAILURE | 0.000 | 56.8s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/contracts | SUCCESS | 1.000 | 511.0s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/forms-classify | SUCCESS | 1.000 | 677.6s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ipe-jira-lifecycle | SUCCESS | 1.000 | 729.7s | claude-sonnet-5 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:loop, node:switch, node:decision, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-hitl-quality-brownfield-insert | SUCCESS | 1.000 | 436.3s | claude-sonnet-5 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-ipe-complex-array | SUCCESS | 0.875 | 285.7s | claude-sonnet-5 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-salesforce-slack, ipe, mode:build |
| skill-flow-ipe-drive-to-slack | SUCCESS | 1.000 | 341.5s | claude-sonnet-5 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, e2e, uipath-google-drive, uipath-salesforce-slack, ipe, mode:build |
| skill-flow-bellevue-weather | SUCCESS | 1.000 | 335.0s | claude-sonnet-5 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:decision, feature:http, ipe |
| skill-flow-solution-select-ask | SUCCESS | 1.000 | 71.9s | claude-sonnet-5 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, simulation |
| skill-flow-summarize | SUCCESS | 1.000 | 139.4s | claude-sonnet-5 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, node:summarize, context-grounding, mode:build |
| skill-flow-interactive-customer-escalation-triage | SUCCESS | 1.000 | 296.0s | claude-sonnet-5 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, feature:escalation, feature:conversational |
| skill-flow-lowcode-agent | MAX_TURNS_EXHAUSTED | 0.000 | 553.0s | claude-sonnet-5 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-ixp-e2e-project-selection/aviation | SUCCESS | 1.000 | 833.4s | claude-sonnet-5 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-ixp-e2e-project-selection/birth-certificate | SUCCESS | 1.000 | 581.9s | claude-sonnet-5 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-cli-dice-roller-simulated | SUCCESS | 1.000 | 278.8s | claude-sonnet-5 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, simulation |
| skill-flow-merge-parallel-sync | SUCCESS | 1.000 | 96.6s | claude-sonnet-5 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:multi-node, node:merge |
| skill-flow-subflow | SUCCESS | 1.000 | 228.9s | claude-sonnet-5 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:subflow |
| skill-flow-ixp-routing-listing/r01 | SUCCESS | 1.000 | 42.9s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r02 | SUCCESS | 1.000 | 139.1s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r03 | SUCCESS | 1.000 | 53.6s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r04 | SUCCESS | 1.000 | 47.6s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r05 | SUCCESS | 1.000 | 40.0s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r06 | SUCCESS | 1.000 | 51.1s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r07 | SUCCESS | 1.000 | 42.2s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r08 | SUCCESS | 1.000 | 35.1s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r09 | SUCCESS | 1.000 | 44.1s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r10 | SUCCESS | 1.000 | 57.9s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-inline-agent-robust | SUCCESS | 1.000 | 264.2s | claude-sonnet-5 | uipath-maestro-flow, mode:build, lifecycle:generate, node:inline-agent |
| skill-flow-slack-weather-pipeline | MAX_TURNS_EXHAUSTED | 0.625 | 708.0s | claude-sonnet-5 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:decision, connector, feature:http |
| skill-flow-expense-approval-simulated | SUCCESS | 1.000 | 839.7s | claude-sonnet-5 | uipath-maestro-flow, uipath-human-in-the-loop, e2e, mode:build, lifecycle:generate, devcon, simulation |
| skill-flow-slack-channel-description-simulated | SUCCESS | 0.917 | 365.1s | claude-sonnet-5 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, connector, simulation |
| skill-flow-devcon-billing-resolution-writer | SUCCESS | 1.000 | 344.0s | claude-sonnet-5 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, path-to-ga |
| skill-flow-eval-no-auto-upload | SUCCESS | 1.000 | 90.8s | claude-sonnet-5 | uipath-maestro-flow, mode:operate, lifecycle:execute, feature:eval |
| skill-flow-rpa | SUCCESS | 1.000 | 223.0s | claude-sonnet-5 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-update-node | SUCCESS | 1.000 | 79.9s | claude-sonnet-5 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:decision |
| skill-flow-outlook-waitfor-email | SUCCESS | 1.000 | 172.8s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, feature:trigger, connector, uipath-microsoft-outlook365, filter, ipe, wait-for-event |
| skill-flow-init-validate | SUCCESS | 1.000 | 33.1s | claude-sonnet-5 | uipath-maestro-flow, smoke, lifecycle:generate |
| skill-flow-ipe-multiselect | SUCCESS | 1.000 | 281.1s | claude-sonnet-5 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, ipe, mode:build |
| skill-flow-bindings-multi-connector-independence | SUCCESS | 1.000 | 309.6s | claude-sonnet-5 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, bindings, regression |
| skill-flow-paginated-reference-lookup | SUCCESS | 1.000 | 189.2s | claude-sonnet-5 | uipath-maestro-flow, integration, e2e, mode:build, lifecycle:generate, shape:multi-node, connector, uipath-salesforce-slack, feature:records |
| skill-flow-ipe-enum | MAX_TURNS_EXHAUSTED | 0.571 | 923.4s | claude-sonnet-5 | uipath-maestro-flow, integration, lifecycle-generate, shape-multi-node, connector, uipath-google-gmail, ipe, mode:build |
| skill-flow-ipe-dtl-load-by-default-false | SUCCESS | 1.000 | 355.7s | claude-sonnet-5 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-automaticc-woocommerce, ipe, mode:build |
| skill-flow-transform-filter | SUCCESS | 1.000 | 145.9s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-registry-discovery | SUCCESS | 1.000 | 63.5s | claude-sonnet-5 | uipath-maestro-flow, smoke, lifecycle:discover, feature:registry |
| skill-flow-slack-channel-description | SUCCESS | 1.000 | 259.3s | claude-sonnet-5 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, connector |
| skill-flow-wiki-pageviews | SUCCESS | 1.000 | 480.6s | claude-sonnet-5 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:transform, feature:http |
| skill-flow-batch-transform | SUCCESS | 1.000 | 133.8s | claude-sonnet-5 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, node:batch-transform, context-grounding, mode:build |
| skill-flow-non-catalog-http-fallback | SUCCESS | 1.000 | 390.6s | claude-sonnet-5 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, connector, uipath-uipath-http, feature:http, ipe |
| skill-flow-ipe-path-params | SUCCESS | 1.000 | 169.4s | claude-sonnet-5 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-ipe-generate-schema | SUCCESS | 1.000 | 240.1s | claude-sonnet-5 | uipath-platform, integration, lifecycle:generate, shape:multi-node, connector, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-devcon-billing-invoice-lookup | SUCCESS | 1.000 | 1110.4s | claude-sonnet-5 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, connector, path-to-ga |
| skill-flow-ipe-query-params | SUCCESS | 1.000 | 313.9s | claude-sonnet-5 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-google-tasks, ipe, mode:build |
| skill-flow-terminate | SUCCESS | 1.000 | 201.7s | claude-sonnet-5 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:terminate |

## Run-time Notes

> **WARNING:** [skill-flow-group-to-subflow] expected_turns exceeded: 37/13 (cumulative SDK turns)
> **WARNING:** [skill-flow-slack-http-fallback] expected_turns exceeded: 41/32 (cumulative SDK turns)
> **WARNING:** [skill-flow-customer-escalation] expected_turns exceeded: 90/73 (cumulative SDK turns)
> **WARNING:** [skill-flow-ixp-scaffold-multinode] max_turns exhausted
> **WARNING:** [skill-flow-hitl-smoke-completed-port] expected_turns exceeded: 29/24 (cumulative SDK turns)
> **WARNING:** [skill-flow-ipe-dtl-load-by-default-true] expected_turns exceeded: 60/40 (cumulative SDK turns)
> **WARNING:** [skill-flow-hitl-quality-result-downstream] expected_turns exceeded: 32/30 (cumulative SDK turns)
> **WARNING:** [skill-flow-hitl-smoke-node-placed] expected_turns exceeded: 23/21 (cumulative SDK turns)
> **WARNING:** [skill-flow-feet-inches] expected_turns exceeded: 31/23 (cumulative SDK turns)
> **WARNING:** [skill-flow-ixp-integration-handle-routing] max_turns exhausted
> **WARNING:** [skill-flow-ixp-integration-handle-routing] expected_turns exceeded: 70/26 (cumulative SDK turns)
> **WARNING:** [skill-flow-remove-node] expected_turns exceeded: 18/14 (cumulative SDK turns)
> **WARNING:** [skill-flow-calculator] expected_turns exceeded: 21/18 (cumulative SDK turns)
> **WARNING:** [skill-flow-move-node] max_turns exhausted
> **WARNING:** [skill-flow-move-node] expected_turns exceeded: 40/11 (cumulative SDK turns)
> **WARNING:** [skill-flow-ipe-enhanced-enum] expected_turns exceeded: 44/35 (cumulative SDK turns)
> **WARNING:** [skill-flow-eval-inline-agent] expected_turns exceeded: 62/30 (cumulative SDK turns)
> **WARNING:** [skill-flow-ipe-required-groups] expected_turns exceeded: 99/51 (cumulative SDK turns)
> **WARNING:** [skill-flow-hitl-quality-schema-design] expected_turns exceeded: 36/29 (cumulative SDK turns)
> **WARNING:** [skill-flow-multi-city-weather] max_turns exhausted
> **WARNING:** [skill-flow-multi-city-weather] expected_turns exceeded: 55/43 (cumulative SDK turns)
> **WARNING:** [skill-flow-ixp-routing-negative/stripe-http] max_turns exhausted
> **WARNING:** [skill-flow-ixp-routing-negative/sf-update] max_turns exhausted
> **WARNING:** [skill-flow-ixp-routing-negative/http-webhook] max_turns exhausted
> **WARNING:** [skill-flow-ixp-routing-negative/gsheet-loop] max_turns exhausted
> **WARNING:** [skill-flow-ixp-routing-negative/queue-write] max_turns exhausted
> **WARNING:** [skill-flow-ixp-routing-negative/teams-decision] max_turns exhausted
> **WARNING:** [skill-flow-ixp-routing-negative/delay-email] max_turns exhausted
> **WARNING:** [skill-flow-ipe-ceql-where] expected_turns exceeded: 66/34 (cumulative SDK turns)
> **WARNING:** [skill-flow-e2e-devcon-expense-approval] expected_turns exceeded: 36/29 (cumulative SDK turns)
> **WARNING:** [skill-flow-ixp-scaffold-minimal] expected_turns exceeded: 33/27 (cumulative SDK turns)
> **WARNING:** [skill-flow-add-node] expected_turns exceeded: 18/13 (cumulative SDK turns)
> **WARNING:** [skill-flow-e2e-escalation-orchestrator-paths] expected_turns exceeded: 89/80 (cumulative SDK turns)
> **WARNING:** [skill-flow-eval-evaluator-type-choice] expected_turns exceeded: 17/15 (cumulative SDK turns)
> **WARNING:** [skill-flow-api-workflow] expected_turns exceeded: 28/25 (cumulative SDK turns)
> **WARNING:** [skill-flow-e2e-escalation-slack-alert] expected_turns exceeded: 71/55 (cumulative SDK turns)
> **WARNING:** [skill-flow-jdbc-databricks-query] expected_turns exceeded: 80/40 (cumulative SDK turns)
> **WARNING:** [skill-flow-webhook-waitfor-parallel] expected_turns exceeded: 36/35 (cumulative SDK turns)
> **WARNING:** [skill-flow-dice-roller] expected_turns exceeded: 23/21 (cumulative SDK turns)
> **WARNING:** [skill-flow-hitl-quality-boolean-decision] expected_turns exceeded: 66/33 (cumulative SDK turns)
> **WARNING:** [skill-flow-loop-multiply] max_turns exhausted
> **WARNING:** [skill-flow-loop-multiply] expected_turns exceeded: 48/22 (cumulative SDK turns)
> **WARNING:** [skill-flow-coded-agent] expected_turns exceeded: 94/35 (cumulative SDK turns)
> **WARNING:** [skill-flow-reading-list] expected_turns exceeded: 23/20 (cumulative SDK turns)
> **WARNING:** [skill-flow-ipe-jira-lifecycle] expected_turns exceeded: 72/55 (cumulative SDK turns)
> **WARNING:** [skill-flow-hitl-quality-brownfield-insert] expected_turns exceeded: 41/34 (cumulative SDK turns)
> **WARNING:** [skill-flow-ipe-complex-array] expected_turns exceeded: 52/38 (cumulative SDK turns)
> **WARNING:** [skill-flow-bellevue-weather] expected_turns exceeded: 33/32 (cumulative SDK turns)
> **WARNING:** [skill-flow-lowcode-agent] max_turns exhausted
> **WARNING:** [skill-flow-lowcode-agent] expected_turns exceeded: 50/30 (cumulative SDK turns)
> **WARNING:** [skill-flow-ixp-e2e-project-selection/aviation] max_turns exhausted
> **WARNING:** [skill-flow-ixp-e2e-project-selection/birth-certificate] max_turns exhausted
> **WARNING:** [skill-flow-subflow] expected_turns exceeded: 27/24 (cumulative SDK turns)
> **WARNING:** [skill-flow-inline-agent-robust] expected_turns exceeded: 43/32 (cumulative SDK turns)
> **WARNING:** [skill-flow-slack-weather-pipeline] max_turns exhausted
> **WARNING:** [skill-flow-slack-weather-pipeline] expected_turns exceeded: 52/51 (cumulative SDK turns)
> **WARNING:** [skill-flow-ipe-multiselect] expected_turns exceeded: 47/37 (cumulative SDK turns)
> **WARNING:** [skill-flow-paginated-reference-lookup] expected_turns exceeded: 40/30 (cumulative SDK turns)
> **WARNING:** [skill-flow-ipe-enum] max_turns exhausted
> **WARNING:** [skill-flow-ipe-enum] expected_turns exceeded: 64/46 (cumulative SDK turns)
> **WARNING:** [skill-flow-slack-channel-description] max_turns exhausted
> **WARNING:** [skill-flow-non-catalog-http-fallback] expected_turns exceeded: 41/32 (cumulative SDK turns)
> **WARNING:** [skill-flow-ipe-generate-schema] expected_turns exceeded: 42/39 (cumulative SDK turns)
> **WARNING:** [skill-flow-terminate] expected_turns exceeded: 31/27 (cumulative SDK turns)


## Generation Metrics

| Task ID | Total Latency | Turns | Asst Turns | Avg Turn Latency |
|---------|---------------|-------|------------|------------------|
| skill-flow-bellevue-weather-simulated | 531.1s | 4 | 90 | 114.7s |
| skill-flow-group-to-subflow | 910.0s | 1 | 61 | 900.0s |
| skill-flow-ixp-invoice-extraction-simulated | 1341.1s | 4 | 139 | 318.7s |
| skill-flow-trigger-with-filter | 59.8s | 1 | 12 | 50.5s |
| skill-flow-slack-http-fallback | 303.2s | 1 | 69 | 275.3s |
| skill-flow-customer-escalation | 868.9s | 1 | 161 | 855.4s |
| skill-flow-hitl-schema-design-simulated | 672.5s | 5 | 76 | 120.8s |
| skill-flow-add-output | 225.2s | 1 | 18 | 64.9s |
| skill-flow-ipe-jira-get-issue | 289.4s | 1 | 66 | 247.4s |
| skill-flow-ixp-scaffold-multinode | 584.7s | 1 | 107 | 567.7s |
| skill-flow-hitl-smoke-completed-port | 322.1s | 1 | 50 | 304.7s |
| skill-flow-ipe-jira-create-issue | 302.1s | 1 | 68 | 261.7s |
| skill-flow-ipe-jira-search-triage | 429.9s | 1 | 75 | 380.0s |
| skill-flow-ipe-dtl-load-by-default-true | 463.6s | 1 | 109 | 454.6s |
| skill-flow-delay | 135.8s | 1 | 36 | 118.5s |
| skill-flow-hitl-quality-result-downstream | 451.5s | 1 | 55 | 437.6s |
| skill-flow-hitl-smoke-node-placed | 324.9s | 1 | 40 | 307.9s |
| skill-flow-generic-dynamic-node | 311.3s | 1 | 78 | 272.1s |
| skill-flow-eval-simulation-crud | 112.4s | 1 | 37 | 103.0s |
| skill-flow-feet-inches | 391.6s | 1 | 56 | 350.6s |
| skill-flow-ixp-integration-handle-routing | 781.0s | 1 | 123 | 762.3s |
| skill-flow-file-attachment-debug | 187.9s | 1 | 52 | 172.2s |
| skill-flow-devcon-billing-discrepancy-detector | 1326.1s | 1 | 168 | 1282.9s |
| skill-flow-hitl-smoke-multi-outcome-routing | 341.5s | 1 | 44 | 319.1s |
| skill-flow-remove-node | 142.9s | 1 | 33 | 104.8s |
| skill-flow-calculator | 150.6s | 1 | 35 | 124.3s |
| skill-flow-e2e-escalation-jira-ticket | 494.1s | 1 | 86 | 457.9s |
| skill-flow-bindings-reconfigure-different-connection | 326.5s | 1 | 76 | 315.9s |
| skill-flow-move-node | 633.2s | 1 | 80 | 615.6s |
| skill-flow-customer-escalation-simulated | 1693.4s | 4 | 234 | 410.0s |
| skill-flow-ipe-enhanced-enum | 561.2s | 1 | 77 | 552.0s |
| skill-flow-eval-inline-agent | 356.4s | 1 | 97 | 347.4s |
| skill-flow-ipe-required-groups | 1025.2s | 1 | 172 | 1016.0s |
| skill-flow-hitl-quality-schema-design | 345.6s | 1 | 57 | 321.4s |
| skill-flow-decision | 248.2s | 1 | 33 | 206.8s |
| skill-flow-switch | 204.0s | 1 | 34 | 172.8s |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 1203.1s | 1 | 155 | 1200.1s |
| skill-flow-ipe-searchable-joins | 660.7s | 1 | 100 | 658.9s |
| skill-flow-multi-city-weather | 832.5s | 1 | 94 | 794.2s |
| skill-flow-eval-local-crud | 84.7s | 1 | 34 | 82.9s |
| skill-flow-ixp-routing-negative/stripe-http | 170.4s | 1 | 43 | 169.0s |
| skill-flow-ixp-routing-negative/slack-summary | 132.0s | 1 | 38 | 130.4s |
| skill-flow-ixp-routing-negative/sf-update | 291.8s | 1 | 52 | 290.4s |
| skill-flow-ixp-routing-negative/http-webhook | 260.3s | 1 | 62 | 258.7s |
| skill-flow-ixp-routing-negative/gsheet-loop | 327.9s | 1 | 60 | 326.3s |
| skill-flow-ixp-routing-negative/queue-write | 257.7s | 1 | 59 | 256.1s |
| skill-flow-ixp-routing-negative/teams-decision | 186.5s | 1 | 52 | 184.5s |
| skill-flow-ixp-routing-negative/delay-email | 200.6s | 1 | 49 | 198.7s |
| skill-flow-ipe-ceql-where | 412.5s | 1 | 106 | 410.8s |
| skill-flow-bindings-no-duplicates | 205.8s | 1 | 62 | 202.5s |
| skill-flow-e2e-devcon-expense-approval | 460.8s | 1 | 59 | 451.6s |
| skill-flow-ixp-scaffold-minimal | 366.6s | 1 | 63 | 348.5s |
| skill-flow-add-node | 159.8s | 1 | 37 | 127.4s |
| skill-flow-transform-group-by | 162.8s | 1 | 28 | 149.2s |
| skill-flow-e2e-escalation-orchestrator-paths | 1098.3s | 1 | 149 | 959.2s |
| skill-flow-eval-evaluator-type-choice | 85.4s | 1 | 31 | 83.8s |
| skill-flow-openmeteo-weather | 216.6s | 1 | 53 | 166.9s |
| skill-flow-devcon-billing-dispute-resolution | 2219.1s | 1 | 255 | 2127.8s |
| skill-flow-devcon-billing-dispute-analyst | 662.0s | 1 | 111 | 508.5s |
| skill-flow-outlook-trigger-inbox | 265.7s | 1 | 64 | 254.0s |
| skill-flow-api-workflow | 218.0s | 1 | 49 | 186.1s |
| skill-flow-bindings-idempotent-reconfigure | 353.1s | 1 | 85 | 350.0s |
| skill-flow-e2e-escalation-slack-alert | 530.1s | 1 | 126 | 496.3s |
| skill-flow-jdbc-databricks-query | 607.4s | 1 | 138 | 604.4s |
| skill-flow-scheduled-trigger | 185.6s | 1 | 37 | 170.5s |
| skill-flow-webhook-waitfor-parallel | 204.1s | 1 | 61 | 202.6s |
| skill-flow-dice-roller | 150.3s | 1 | 35 | 124.3s |
| skill-flow-hitl-quality-boolean-decision | 741.9s | 1 | 110 | 735.0s |
| skill-flow-loop-multiply | 562.3s | 1 | 88 | 528.9s |
| skill-flow-coded-agent | 676.7s | 1 | 153 | 636.1s |
| skill-flow-transform-map | 180.6s | 1 | 44 | 173.2s |
| skill-flow-reading-list | 215.6s | 1 | 40 | 193.2s |
| skill-flow-ixp-routing/explicit | 755.8s | 1 | 130 | 754.2s |
| skill-flow-ixp-routing/invoice-extraction | 571.1s | 1 | 122 | 569.6s |
| skill-flow-ixp-routing/receipts | 56.8s | 1 | 20 | 55.3s |
| skill-flow-ixp-routing/contracts | 511.0s | 1 | 69 | 509.5s |
| skill-flow-ixp-routing/forms-classify | 677.6s | 1 | 76 | 676.0s |
| skill-flow-ipe-jira-lifecycle | 729.7s | 1 | 123 | 686.9s |
| skill-flow-hitl-quality-brownfield-insert | 436.3s | 1 | 68 | 428.6s |
| skill-flow-ipe-complex-array | 285.7s | 1 | 92 | 283.5s |
| skill-flow-ipe-drive-to-slack | 341.5s | 1 | 82 | 339.7s |
| skill-flow-bellevue-weather | 335.0s | 1 | 54 | 303.3s |
| skill-flow-solution-select-ask | 71.9s | 5 | 11 | 9.1s |
| skill-flow-summarize | 139.4s | 1 | 38 | 133.6s |
| skill-flow-interactive-customer-escalation-triage | 296.0s | 3 | 33 | 73.3s |
| skill-flow-lowcode-agent | 553.0s | 1 | 89 | 530.0s |
| skill-flow-ixp-e2e-project-selection/aviation | 833.4s | 1 | 119 | 828.9s |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 581.9s | 1 | 114 | 577.6s |
| skill-flow-cli-dice-roller-simulated | 278.8s | 3 | 63 | 80.8s |
| skill-flow-merge-parallel-sync | 96.6s | 1 | 30 | 89.4s |
| skill-flow-subflow | 228.9s | 1 | 43 | 200.5s |
| skill-flow-ixp-routing-listing/r01 | 42.9s | 1 | 11 | 41.0s |
| skill-flow-ixp-routing-listing/r02 | 139.1s | 1 | 38 | 137.3s |
| skill-flow-ixp-routing-listing/r03 | 53.6s | 1 | 14 | 52.2s |
| skill-flow-ixp-routing-listing/r04 | 47.6s | 1 | 14 | 45.9s |
| skill-flow-ixp-routing-listing/r05 | 40.0s | 1 | 13 | 38.6s |
| skill-flow-ixp-routing-listing/r06 | 51.1s | 1 | 12 | 48.8s |
| skill-flow-ixp-routing-listing/r07 | 42.2s | 1 | 15 | 40.6s |
| skill-flow-ixp-routing-listing/r08 | 35.1s | 1 | 12 | 33.8s |
| skill-flow-ixp-routing-listing/r09 | 44.1s | 1 | 13 | 42.7s |
| skill-flow-ixp-routing-listing/r10 | 57.9s | 1 | 14 | 56.5s |
| skill-flow-inline-agent-robust | 264.2s | 1 | 62 | 262.7s |
| skill-flow-slack-weather-pipeline | 708.0s | 1 | 93 | 670.1s |
| skill-flow-expense-approval-simulated | 839.7s | 2 | 78 | 409.3s |
| skill-flow-slack-channel-description-simulated | 365.1s | 3 | 86 | 109.1s |
| skill-flow-devcon-billing-resolution-writer | 344.0s | 1 | 82 | 320.9s |
| skill-flow-eval-no-auto-upload | 90.8s | 1 | 37 | 89.1s |
| skill-flow-rpa | 223.0s | 1 | 44 | 169.2s |
| skill-flow-update-node | 79.9s | 1 | 19 | 52.8s |
| skill-flow-outlook-waitfor-email | 172.8s | 1 | 50 | 165.3s |
| skill-flow-init-validate | 33.1s | 1 | 9 | 31.5s |
| skill-flow-ipe-multiselect | 281.1s | 1 | 87 | 278.9s |
| skill-flow-bindings-multi-connector-independence | 309.6s | 1 | 82 | 306.4s |
| skill-flow-paginated-reference-lookup | 189.2s | 1 | 65 | 186.9s |
| skill-flow-ipe-enum | 923.4s | 1 | 104 | 920.6s |
| skill-flow-ipe-dtl-load-by-default-false | 355.7s | 1 | 63 | 353.6s |
| skill-flow-transform-filter | 145.9s | 1 | 31 | 138.4s |
| skill-flow-registry-discovery | 63.5s | 1 | 14 | 61.6s |
| skill-flow-slack-channel-description | 259.3s | 1 | 74 | 235.9s |
| skill-flow-wiki-pageviews | 480.6s | 1 | 60 | 437.9s |
| skill-flow-batch-transform | 133.8s | 1 | 31 | 127.7s |
| skill-flow-non-catalog-http-fallback | 390.6s | 1 | 78 | 388.9s |
| skill-flow-ipe-path-params | 169.4s | 1 | 48 | 166.8s |
| skill-flow-ipe-generate-schema | 240.1s | 1 | 81 | 238.3s |
| skill-flow-devcon-billing-invoice-lookup | 1110.4s | 1 | 152 | 1045.7s |
| skill-flow-ipe-query-params | 313.9s | 1 | 73 | 312.2s |
| skill-flow-terminate | 201.7s | 1 | 50 | 182.4s |


## Token Usage

**Total Tokens**: 521,836,967 (input: 164,578, output: 3,423,350)
**Cache Tokens**: write: 14,382,311, read: 503,866,728
**Agent Cost**: $256.9377
**Eval Overhead (judge + simulator)**: $0.1263
**Total Cost**: $257.0640 (floor — 1 task(s) have spend missing from this total)
**Avg Tokens/Task**: 4,108,952

| Task ID | Input (uncached) | Output | Cache Write | Cache Read | Total | Cost |
|---------|------------------|--------|-------------|------------|-------|------|
| skill-flow-bellevue-weather-simulated | 734 | 30,095 | 191,634 | 6,013,464 | 6,235,927 | $2.9913 |
| skill-flow-group-to-subflow | 48 | 81,503 | 90,424 | 2,566,334 | 2,738,309 | $2.3317 |
| skill-flow-ixp-invoice-extraction-simulated | 1,080 | 102,500 | 248,480 | 13,129,843 | 13,481,903 | $6.4386 |
| skill-flow-trigger-with-filter | 537 | 3,620 | 86,177 | 251,834 | 342,168 | $0.4546 |
| skill-flow-slack-http-fallback | 598 | 12,047 | 75,541 | 2,750,615 | 2,838,801 | $1.2910 |
| skill-flow-customer-escalation | 752 | 65,249 | 208,204 | 14,293,045 | 14,567,250 | $6.0497 |
| skill-flow-hitl-schema-design-simulated | 474 | 44,945 | 124,143 | 3,392,807 | 3,562,369 | $2.1774 |
| skill-flow-add-output | 480 | 2,611 | 44,475 | 559,325 | 606,891 | $0.3752 |
| skill-flow-ipe-jira-get-issue | 5,292 | 13,797 | 126,725 | 3,276,264 | 3,422,078 | $1.6809 |
| skill-flow-ixp-scaffold-multinode | 717 | 39,717 | 161,269 | 4,643,477 | 4,845,180 | $2.5957 |
| skill-flow-hitl-smoke-completed-port | 559 | 23,794 | 105,517 | 2,087,716 | 2,217,586 | $1.3806 |
| skill-flow-ipe-jira-create-issue | 663 | 12,815 | 134,555 | 3,909,313 | 4,057,346 | $1.8716 |
| skill-flow-ipe-jira-search-triage | 658 | 27,364 | 161,466 | 4,593,125 | 4,782,613 | $2.3959 |
| skill-flow-ipe-dtl-load-by-default-true | 589 | 23,942 | 113,316 | 5,948,921 | 6,086,768 | $2.5705 |
| skill-flow-delay | 726 | 4,619 | 65,274 | 1,351,685 | 1,422,304 | $0.7217 |
| skill-flow-hitl-quality-result-downstream | 688 | 37,216 | 116,265 | 2,662,465 | 2,816,634 | $1.7950 |
| skill-flow-hitl-smoke-node-placed | 561 | 23,973 | 102,980 | 1,880,761 | 2,008,275 | $1.3117 |
| skill-flow-generic-dynamic-node | 610 | 12,308 | 110,176 | 3,113,270 | 3,236,364 | $1.5336 |
| skill-flow-eval-simulation-crud | 987 | 5,146 | 39,063 | 1,333,562 | 1,378,758 | $0.6267 |
| skill-flow-feet-inches | 623 | 16,698 | 138,435 | 2,448,011 | 2,603,767 | $1.5059 |
| skill-flow-ixp-integration-handle-routing | 877 | 54,790 | 182,677 | 7,869,489 | 8,107,833 | $3.8704 |
| skill-flow-file-attachment-debug | 626 | 9,998 | 101,420 | 1,991,117 | 2,103,161 | $1.1295 |
| skill-flow-devcon-billing-discrepancy-detector | 995 | 94,967 | 233,532 | 15,152,576 | 15,482,070 | $6.8490 |
| skill-flow-hitl-smoke-multi-outcome-routing | 650 | 29,412 | 109,527 | 1,670,534 | 1,810,123 | $1.3550 |
| skill-flow-remove-node | 496 | 6,209 | 52,710 | 1,403,073 | 1,462,488 | $0.7132 |
| skill-flow-calculator | 499 | 6,359 | 91,584 | 1,501,603 | 1,600,045 | $0.8908 |
| skill-flow-e2e-escalation-jira-ticket | 925 | 32,585 | 171,346 | 5,553,215 | 5,758,071 | $2.8001 |
| skill-flow-bindings-reconfigure-different-connection | 890 | 18,804 | 122,192 | 4,769,632 | 4,911,518 | $2.1738 |
| skill-flow-move-node | 583 | 51,173 | 90,340 | 4,127,955 | 4,270,051 | $2.3465 |
| skill-flow-customer-escalation-simulated | 1,105 | 98,331 | 290,930 | 22,929,206 | 23,319,572 | $9.4680 |
| skill-flow-ipe-enhanced-enum | 603 | 40,193 | 153,453 | 4,983,600 | 5,177,849 | $2.6752 |
| skill-flow-eval-inline-agent | 1,128 | 24,341 | 146,874 | 5,300,379 | 5,472,722 | $2.5094 |
| skill-flow-ipe-required-groups | 631 | 79,760 | 227,661 | 7,701,539 | 8,009,591 | $4.3625 |
| skill-flow-hitl-quality-schema-design | 649 | 25,889 | 109,081 | 2,758,904 | 2,894,523 | $1.6270 |
| skill-flow-decision | 508 | 16,255 | 89,817 | 991,504 | 1,098,084 | $0.8796 |
| skill-flow-switch | 556 | 13,513 | 85,465 | 1,188,589 | 1,288,123 | $0.8814 |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 134 | 87,943 | 197,804 | 12,473,899 | 12,759,780 | $5.8035 |
| skill-flow-ipe-searchable-joins | 578 | 47,146 | 147,491 | 6,184,899 | 6,380,114 | $3.1175 |
| skill-flow-multi-city-weather | 632 | 69,262 | 142,040 | 5,593,806 | 5,805,740 | $3.2516 |
| skill-flow-eval-local-crud | 859 | 4,420 | 50,319 | 1,156,554 | 1,212,152 | $0.6045 |
| skill-flow-ixp-routing-negative/stripe-http | 618 | 9,321 | 90,218 | 1,837,331 | 1,937,488 | $1.0312 |
| skill-flow-ixp-routing-negative/slack-summary | 14,700 | 8,741 | 101,208 | 1,781,146 | 1,905,795 | $1.0891 |
| skill-flow-ixp-routing-negative/sf-update | 619 | 20,521 | 121,212 | 2,612,840 | 2,755,192 | $1.5481 |
| skill-flow-ixp-routing-negative/http-webhook | 626 | 16,859 | 97,173 | 2,472,712 | 2,587,370 | $1.3610 |
| skill-flow-ixp-routing-negative/gsheet-loop | 625 | 23,191 | 123,768 | 3,129,272 | 3,276,856 | $1.7527 |
| skill-flow-ixp-routing-negative/queue-write | 622 | 16,137 | 67,002 | 2,114,902 | 2,198,663 | $1.1296 |
| skill-flow-ixp-routing-negative/teams-decision | 622 | 9,658 | 45,461 | 1,669,781 | 1,725,522 | $0.8181 |
| skill-flow-ixp-routing-negative/delay-email | 616 | 14,730 | 75,613 | 1,741,834 | 1,832,793 | $1.0289 |
| skill-flow-ipe-ceql-where | 619 | 27,805 | 133,416 | 5,015,008 | 5,176,848 | $2.4237 |
| skill-flow-bindings-no-duplicates | 550 | 10,765 | 135,143 | 3,261,743 | 3,408,201 | $1.6484 |
| skill-flow-e2e-devcon-expense-approval | 712 | 40,626 | 122,030 | 2,703,807 | 2,867,175 | $1.8803 |
| skill-flow-ixp-scaffold-minimal | 648 | 25,422 | 142,609 | 3,290,210 | 3,458,889 | $1.9051 |
| skill-flow-add-node | 523 | 8,189 | 53,725 | 1,410,608 | 1,473,045 | $0.7491 |
| skill-flow-transform-group-by | 905 | 10,037 | 94,103 | 1,086,904 | 1,191,949 | $0.8322 |
| skill-flow-e2e-escalation-orchestrator-paths | 1,337 | 80,694 | 190,453 | 11,218,656 | 11,491,140 | $5.2942 |
| skill-flow-eval-evaluator-type-choice | 1,010 | 4,336 | 36,899 | 1,154,677 | 1,196,922 | $0.5528 |
| skill-flow-openmeteo-weather | 14,955 | 8,761 | 131,826 | 2,634,551 | 2,790,093 | $1.4610 |
| skill-flow-devcon-billing-dispute-resolution | 1,930 | 183,344 | 298,572 | 27,360,169 | 27,844,015 | $12.0836 |
| skill-flow-devcon-billing-dispute-analyst | 764 | 41,953 | 176,518 | 6,141,121 | 6,360,356 | $3.1359 |
| skill-flow-outlook-trigger-inbox | 613 | 15,162 | 144,682 | 2,928,453 | 3,088,910 | $1.6504 |
| skill-flow-api-workflow | 520 | 11,447 | 103,337 | 2,291,856 | 2,407,160 | $1.2483 |
| skill-flow-bindings-idempotent-reconfigure | 656 | 21,972 | 114,790 | 4,154,820 | 4,292,238 | $2.0085 |
| skill-flow-e2e-escalation-slack-alert | 989 | 35,320 | 166,346 | 8,929,634 | 9,132,289 | $3.8355 |
| skill-flow-jdbc-databricks-query | 706 | 33,306 | 167,023 | 8,998,160 | 9,199,195 | $3.8275 |
| skill-flow-scheduled-trigger | 969 | 8,860 | 37,047 | 1,222,022 | 1,268,898 | $0.6413 |
| skill-flow-webhook-waitfor-parallel | 672 | 10,376 | 93,008 | 2,892,536 | 2,996,592 | $1.3742 |
| skill-flow-dice-roller | 496 | 7,716 | 90,900 | 1,416,035 | 1,515,147 | $0.8829 |
| skill-flow-hitl-quality-boolean-decision | 14,870 | 64,727 | 138,999 | 6,457,219 | 6,675,815 | $3.4739 |
| skill-flow-loop-multiply | 557 | 33,000 | 106,863 | 4,818,303 | 4,958,723 | $2.3429 |
| skill-flow-coded-agent | 11,400 | 43,677 | 230,069 | 11,259,224 | 11,544,370 | $4.9299 |
| skill-flow-transform-map | 884 | 10,191 | 101,630 | 2,097,602 | 2,210,307 | $1.1659 |
| skill-flow-reading-list | 1,000 | 14,726 | 103,091 | 1,833,601 | 1,952,418 | $1.1606 |
| skill-flow-ixp-routing/explicit | 697 | 58,962 | 199,802 | 9,493,313 | 9,752,774 | $4.4838 |
| skill-flow-ixp-routing/invoice-extraction | 704 | 38,989 | 188,910 | 9,609,465 | 9,838,068 | $4.1782 |
| skill-flow-ixp-routing/receipts | 595 | 3,256 | 16,718 | 473,977 | 494,546 | $0.2555 |
| skill-flow-ixp-routing/contracts | 643 | 39,917 | 112,818 | 3,800,544 | 3,953,922 | $2.1639 |
| skill-flow-ixp-routing/forms-classify | 654 | 52,407 | 120,409 | 4,102,952 | 4,276,422 | $2.4705 |
| skill-flow-ipe-jira-lifecycle | 810 | 51,813 | 187,617 | 7,925,757 | 8,165,997 | $3.8609 |
| skill-flow-hitl-quality-brownfield-insert | 744 | 37,322 | 115,138 | 2,900,135 | 3,053,339 | $1.8639 |
| skill-flow-ipe-complex-array | 545 | 16,046 | 98,377 | 4,143,618 | 4,258,586 | $1.8543 |
| skill-flow-ipe-drive-to-slack | 655 | 18,848 | 138,911 | 4,974,776 | 5,133,190 | $2.2980 |
| skill-flow-bellevue-weather | 14,689 | 22,364 | 118,131 | 2,680,230 | 2,835,414 | $1.6266 |
| skill-flow-solution-select-ask | 457 | 958 | 16,695 | 414,695 | 432,805 | $0.2065 |
| skill-flow-summarize | 1,001 | 9,386 | 101,428 | 1,786,763 | 1,898,578 | $1.0602 |
| skill-flow-interactive-customer-escalation-triage | 1,161 | 18,386 | 82,951 | 1,257,649 | 1,360,147 | $0.9910 |
| skill-flow-lowcode-agent | 582 | 38,756 | 83,377 | 3,510,576 | 3,633,291 | $1.9489 |
| skill-flow-ixp-e2e-project-selection/aviation | 705 | 56,027 | 130,444 | 7,026,719 | 7,213,895 | $3.4397 |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 682 | 40,978 | 159,297 | 7,863,138 | 8,064,095 | $3.5730 |
| skill-flow-cli-dice-roller-simulated | 672 | 9,284 | 59,430 | 2,097,113 | 2,166,499 | $0.9997 |
| skill-flow-merge-parallel-sync | 1,152 | 6,157 | 67,861 | 783,859 | 859,029 | $0.5854 |
| skill-flow-subflow | 529 | 15,382 | 90,043 | 1,589,360 | 1,695,314 | $1.0468 |
| skill-flow-ixp-routing-listing/r01 | 3,507 | 2,550 | 35,545 | 334,008 | 375,610 | $0.2823 |
| skill-flow-ixp-routing-listing/r02 | 481 | 8,063 | 31,809 | 1,085,756 | 1,126,109 | $0.5674 |
| skill-flow-ixp-routing-listing/r03 | 461 | 1,585 | 32,092 | 455,663 | 489,801 | $0.2822 |
| skill-flow-ixp-routing-listing/r04 | 463 | 2,336 | 35,052 | 412,258 | 450,109 | $0.2916 |
| skill-flow-ixp-routing-listing/r05 | 456 | 2,194 | 34,601 | 336,560 | 373,811 | $0.2650 |
| skill-flow-ixp-routing-listing/r06 | 462 | 2,691 | 34,851 | 409,096 | 447,100 | $0.2952 |
| skill-flow-ixp-routing-listing/r07 | 456 | 2,297 | 45,014 | 451,304 | 499,071 | $0.3400 |
| skill-flow-ixp-routing-listing/r08 | 460 | 1,691 | 35,396 | 336,761 | 374,308 | $0.2605 |
| skill-flow-ixp-routing-listing/r09 | 3,514 | 1,663 | 34,768 | 461,126 | 501,071 | $0.3042 |
| skill-flow-ixp-routing-listing/r10 | 461 | 2,971 | 35,510 | 466,465 | 505,407 | $0.3191 |
| skill-flow-inline-agent-robust | 651 | 22,269 | 138,948 | 2,403,461 | 2,565,329 | $1.5781 |
| skill-flow-slack-weather-pipeline | 673 | 52,963 | 163,661 | 5,598,390 | 5,815,687 | $3.0897 |
| skill-flow-expense-approval-simulated | 856 | 72,786 | 143,857 | 4,123,717 | 4,341,216 | $2.8790 |
| skill-flow-slack-channel-description-simulated | 742 | 19,067 | 167,283 | 4,668,962 | 4,856,054 | $2.3204 |
| skill-flow-devcon-billing-resolution-writer | 681 | 25,709 | 134,939 | 3,791,552 | 3,952,881 | $2.0312 |
| skill-flow-eval-no-auto-upload | 918 | 4,739 | 30,074 | 1,135,058 | 1,170,789 | $0.5271 |
| skill-flow-rpa | 514 | 8,740 | 78,998 | 1,644,936 | 1,733,188 | $0.9224 |
| skill-flow-update-node | 491 | 2,548 | 49,155 | 616,714 | 668,908 | $0.4090 |
| skill-flow-outlook-waitfor-email | 572 | 8,705 | 101,612 | 2,151,643 | 2,262,532 | $1.1588 |
| skill-flow-init-validate | 555 | 981 | 16,784 | 249,443 | 267,763 | $0.1542 |
| skill-flow-ipe-multiselect | 536 | 15,483 | 86,800 | 4,184,920 | 4,287,739 | $1.8148 |
| skill-flow-bindings-multi-connector-independence | 1,238 | 18,154 | 147,835 | 4,690,543 | 4,857,770 | $2.2376 |
| skill-flow-paginated-reference-lookup | 578 | 10,492 | 123,419 | 2,917,237 | 3,051,726 | $1.4971 |
| skill-flow-ipe-enum | 633 | 74,953 | 169,444 | 5,896,438 | 6,141,468 | $3.5305 |
| skill-flow-ipe-dtl-load-by-default-false | 547 | 23,702 | 92,460 | 3,203,977 | 3,320,686 | $1.6651 |
| skill-flow-transform-filter | 861 | 9,996 | 83,025 | 1,063,804 | 1,157,686 | $0.7830 |
| skill-flow-registry-discovery | 576 | 2,918 | 24,941 | 379,453 | 407,888 | $0.2529 |
| skill-flow-slack-channel-description | 532 | 13,773 | 155,211 | 4,150,289 | 4,319,805 | $2.0353 |
| skill-flow-wiki-pageviews | 805 | 37,958 | 149,773 | 2,817,980 | 3,006,516 | $1.9788 |
| skill-flow-batch-transform | 927 | 10,156 | 81,060 | 1,051,015 | 1,143,158 | $0.7744 |
| skill-flow-non-catalog-http-fallback | 592 | 24,695 | 152,953 | 5,030,730 | 5,208,970 | $2.4550 |
| skill-flow-ipe-path-params | 577 | 7,852 | 106,584 | 2,348,754 | 2,463,767 | $1.2238 |
| skill-flow-ipe-generate-schema | 583 | 12,251 | 89,705 | 3,583,008 | 3,685,547 | $1.5968 |
| skill-flow-devcon-billing-invoice-lookup | 787 | 77,169 | 171,165 | 11,776,003 | 12,025,124 | $5.3346 |
| skill-flow-ipe-query-params | 573 | 22,483 | 112,138 | 3,645,842 | 3,781,036 | $1.8532 |
| skill-flow-terminate | 549 | 12,650 | 92,376 | 2,114,576 | 2,220,151 | $1.1722 |


## Command Telemetry

**Total Commands**: 4867
**Success Rate**: 4710/4867 (96.8%)

### Commands by Tool

| Tool | Count | % |
|------|-------|---|
| Bash | 3140 | 64.5% |
| Read | 949 | 19.5% |
| Edit | 193 | 4.0% |
| TaskUpdate | 166 | 3.4% |
| Skill | 127 | 2.6% |
| TaskCreate | 106 | 2.2% |
| Grep | 105 | 2.2% |
| Write | 53 | 1.1% |
| Glob | 16 | 0.3% |
| TaskOutput | 6 | 0.1% |
| TaskStop | 4 | 0.1% |
| Agent | 2 | 0.0% |

### Performance

- **Average Command Time**: 1686.5ms
- **Total Command Time**: 8208.31s

### Slowest Commands

| Tool | Duration | Parameters |
|------|----------|------------|
| Bash | 120304ms | {'command': 'cd /home/azureuser/projects/skills/tm... |
| Bash | 120273ms | {'command': 'uip is connections create "uipath-moc... |
| Bash | 104465ms | {'command': 'for f in /home/azureuser/projects/ski... |
| Bash | 66044ms | {'command': 'timeout 60 uip is connections create ... |
| Bash | 41357ms | {'command': 'cd /tmp/migtest/MigTest/MigTest\nfor ... |

**Most Common Pattern**: `Bash → Bash → Bash`

**Skill Tool Invoked**: 127 time(s)

## Agent Settings

- **Permission Mode**: acceptEdits
- **Allowed Tools**: Skill, Bash, Read, Write, Edit, Glob, Grep
- **Model**: us.anthropic.claude-sonnet-5
- **Max Turns**: 70
- **System Prompt**: You are a coding agent. Do not access files in sibling runs/* directories. Everywhere else is permitted. 
- **Plugins**: /home/azureuser/projects/skills/tmp

## Environment

- **git_commit**: f7e9fda
- **skills_git_commit**: fca9ebdb0
- **cli_version**: 1.201.0-dev.8272
- **tool_plugins**: {'admin-tool': '1.201.0-dev.8272', 'agent-tool': '1.201.0-dev.8272', 'agenthub-tool': '1.201.0-dev.8272', 'aops-tool': '1.201.0-dev.8272', 'api-workflow-tool': '1.201.0-dev.8272', 'automation-hub-tool': '1.201.0-dev.8272', 'codedagent-tool': '1.201.0-dev.8272', 'codedapp-tool': '1.201.0-dev.8272', 'coder-tool': '1.201.0-dev.8272', 'context-grounding-tool': '1.201.0-dev.8272', 'conversational-tool': '1.201.0-dev.8272', 'data-fabric-tool': '1.201.0-dev.8272', 'docsai-tool': '1.201.0-dev.8272', 'function-tool': '1.201.0-dev.8272', 'gov-tool': '1.201.0-dev.8272', 'guardrails-tool': '1.201.0-dev.8272', 'insights-tool': '1.201.0-dev.8276', 'integrationservice-tool': '1.201.0-dev.8272', 'ixp-tool': '1.201.0-dev.8272', 'llm-gateway-tool': '1.201.0-dev.8272', 'llmgw-tool': '1.201.0-dev.8272', 'maestro-tool': '1.201.0-dev.8275', 'model-hub-tool': '1.201.0-dev.8272', 'orchestrator-tool': '1.201.0-dev.8272', 'platform-tool': '1.201.0-dev.8272', 'pm-tool': '1.201.0-dev.8272', 'rpa-legacy-tool': '1.201.0-dev.8272', 'rpa-tool': '1.201.0-dev.20260809.3', 'solution-tool': '1.201.0-dev.8272', 'tasks-tool': '1.201.0-dev.8272', 'test-manager-tool': '1.201.0-dev.8272', 'traces-tool': '1.201.0-dev.8272', 'vertical-solutions-tool': '1.201.0-dev.8272'}
- **coder_eval**: 0.9.6
- **claude_code_cli**: 2.1.235 (Claude Code)
- **uv**: uv 0.11.21 (x86_64-unknown-linux-gnu)
- **anthropic**: 0.102.0
- **openai**: Not Installed
- **pydantic**: 2.12.5