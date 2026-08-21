# Evaluation Run Report

**Run ID**: `maestro-flow-baseline-sonnet-4-6`
**Date**: 2026-08-19 17:51:17
**Duration**: 1617.63s
**Model**: `claude-sonnet-4-6`

## Summary

- **Total Tasks**: 127
- **Succeeded**: 120
- **Failed**: 7
- **Errors**: 0
- **Pass Rate**: 94.5% (120/127)
- **Avg Reliability Score**: 0.964
- **Avg Generation Latency**: 326.0s
- **Total Assistant Turns**: 5173

## Task Details

| Task ID | Status | Reliability Score | Latency | Model | Tags |
|---------|--------|-------------------|---------|-------|------|
| skill-flow-e2e-escalation-jira-ticket | SUCCESS | 1.000 | 515.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, connector, feature:escalation |
| skill-flow-registry-discovery | SUCCESS | 1.000 | 63.6s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, lifecycle:discover, feature:registry |
| skill-flow-ixp-routing-listing/r01 | SUCCESS | 1.000 | 61.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r02 | SUCCESS | 1.000 | 66.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r03 | SUCCESS | 1.000 | 72.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r04 | SUCCESS | 1.000 | 55.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r05 | SUCCESS | 1.000 | 67.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r06 | SUCCESS | 1.000 | 57.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r07 | SUCCESS | 1.000 | 70.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r08 | SUCCESS | 1.000 | 61.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r09 | SUCCESS | 1.000 | 62.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r10 | SUCCESS | 1.000 | 66.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-file-attachment-debug | SUCCESS | 1.000 | 253.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node |
| skill-flow-slack-channel-description | SUCCESS | 1.000 | 358.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, connector |
| skill-flow-group-to-subflow | SUCCESS | 1.000 | 676.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:subflow |
| skill-flow-decision | SUCCESS | 1.000 | 228.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:decision |
| skill-flow-devcon-billing-dispute-resolution | FAILURE | 0.545 | 1273.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, node:ixp, connector, path-to-ga |
| skill-flow-api-workflow | FAILURE | 0.375 | 303.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-add-output | SUCCESS | 1.000 | 87.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node |
| skill-flow-bindings-multi-connector-independence | SUCCESS | 1.000 | 236.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, bindings, regression |
| skill-flow-eval-inline-agent | SUCCESS | 1.000 | 520.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:inline-agent, feature:eval |
| skill-flow-bindings-no-duplicates | SUCCESS | 1.000 | 389.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-devcon-billing-discrepancy-detector | SUCCESS | 1.000 | 859.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, connector, path-to-ga |
| skill-flow-slack-channel-description-simulated | SUCCESS | 1.000 | 413.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, connector, simulation |
| skill-flow-outlook-waitfor-email | SUCCESS | 1.000 | 220.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, feature:trigger, connector, uipath-microsoft-outlook365, filter, ipe, wait-for-event |
| skill-flow-webhook-waitfor-parallel | SUCCESS | 1.000 | 304.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, connector, feature:trigger, feature:http, wait-for-event, uipath-http-webhook, ipe |
| skill-flow-multi-city-weather | SUCCESS | 1.000 | 738.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:loop, feature:http |
| skill-flow-ixp-scaffold-minimal | SUCCESS | 1.000 | 321.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | SUCCESS | 1.000 | 962.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, node:ixp, connector, feature:http |
| skill-flow-eval-simulation-crud | SUCCESS | 1.000 | 159.6s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, feature:eval |
| skill-flow-ipe-ceql-where | SUCCESS | 1.000 | 454.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, connector, ceql, filter, uipath-microsoft-azureactivedirectory, ipe, mode:build |
| skill-flow-ixp-e2e-project-selection/aviation | SUCCESS | 1.000 | 247.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-ixp-e2e-project-selection/birth-certificate | SUCCESS | 1.000 | 399.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-reading-list | SUCCESS | 1.000 | 239.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:transform |
| skill-flow-ipe-jira-lifecycle | SUCCESS | 1.000 | 822.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:loop, node:switch, node:decision, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-rpa | FAILURE | 0.625 | 349.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-init-validate | SUCCESS | 1.000 | 97.3s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, lifecycle:generate |
| skill-flow-transform-map | SUCCESS | 1.000 | 289.5s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-ipe-generate-schema | SUCCESS | 1.000 | 300.9s | claude-sonnet-4-6 | uipath-platform, integration, lifecycle:generate, shape:multi-node, connector, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-slack-http-fallback | SUCCESS | 1.000 | 278.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:single-node, connector, uipath-salesforce-slack, feature:http, ipe |
| skill-flow-devcon-billing-resolution-writer | SUCCESS | 1.000 | 298.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, path-to-ga |
| skill-flow-e2e-escalation-orchestrator-paths | SUCCESS | 1.000 | 1016.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, node:decision, connector, feature:escalation |
| skill-flow-loop-multiply | FAILURE | 0.375 | 423.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:loop |
| skill-flow-hitl-quality-boolean-decision | SUCCESS | 1.000 | 312.0s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-slack-weather-pipeline | MAX_TURNS_EXHAUSTED | 0.000 | 624.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:decision, connector, feature:http |
| skill-flow-merge-parallel-sync | SUCCESS | 1.000 | 186.2s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:multi-node, node:merge |
| skill-flow-ipe-required-groups | SUCCESS | 1.000 | 172.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-microsoft-teams, ipe, mode:build |
| skill-flow-solution-select-ask | SUCCESS | 1.000 | 99.4s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, simulation |
| skill-flow-ipe-enum | SUCCESS | 1.000 | 754.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle-generate, shape-multi-node, connector, uipath-google-gmail, ipe, mode:build |
| skill-flow-ixp-routing-negative/stripe-http | SUCCESS | 1.000 | 240.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/slack-summary | SUCCESS | 1.000 | 276.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/sf-update | SUCCESS | 1.000 | 215.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/http-webhook | SUCCESS | 1.000 | 208.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/gsheet-loop | SUCCESS | 1.000 | 202.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/queue-write | SUCCESS | 1.000 | 205.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/teams-decision | SUCCESS | 1.000 | 163.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/delay-email | SUCCESS | 1.000 | 442.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-e2e-devcon-expense-approval | SUCCESS | 1.000 | 374.4s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, e2e, devcon |
| skill-flow-bindings-idempotent-reconfigure | SUCCESS | 1.000 | 381.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-hitl-quality-result-downstream | SUCCESS | 1.000 | 366.9s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-ipe-jira-create-issue | SUCCESS | 1.000 | 296.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-customer-escalation | SUCCESS | 1.000 | 743.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:decision, feature:trigger, connector |
| skill-flow-ipe-dtl-load-by-default-true | SUCCESS | 1.000 | 164.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-microsoft-azure, ipe, mode:build |
| skill-flow-e2e-escalation-slack-alert | SUCCESS | 1.000 | 350.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, connector, feature:escalation |
| skill-flow-hitl-smoke-node-placed | SUCCESS | 1.000 | 338.3s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, lifecycle:generate, shape:single-node, node:hitl |
| skill-flow-ixp-routing/explicit | SUCCESS | 1.000 | 234.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/invoice-extraction | SUCCESS | 1.000 | 442.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/receipts | SUCCESS | 1.000 | 192.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/contracts | SUCCESS | 1.000 | 190.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/forms-classify | SUCCESS | 1.000 | 193.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ipe-jira-get-issue | SUCCESS | 1.000 | 412.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-ixp-integration-handle-routing | SUCCESS | 1.000 | 559.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:ixp, node:decision |
| skill-flow-update-node | SUCCESS | 1.000 | 68.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:decision |
| skill-flow-eval-local-crud | SUCCESS | 1.000 | 142.4s | claude-sonnet-4-6 | uipath-maestro-flow, mode:build, lifecycle:generate, feature:eval |
| skill-flow-delay | SUCCESS | 1.000 | 112.4s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:delay |
| skill-flow-paginated-reference-lookup | SUCCESS | 1.000 | 167.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, e2e, mode:build, lifecycle:generate, shape:multi-node, connector, uipath-salesforce-slack, feature:records |
| skill-flow-coded-agent | FAILURE | 0.375 | 571.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:single-node, resource, path-to-ga |
| skill-flow-interactive-customer-escalation-triage | SUCCESS | 1.000 | 384.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, feature:escalation, feature:conversational |
| skill-flow-ixp-invoice-extraction-simulated | SUCCESS | 1.000 | 1090.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, node:ixp, connector, feature:http, simulation |
| skill-flow-calculator | SUCCESS | 1.000 | 168.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node |
| skill-flow-transform-filter | SUCCESS | 1.000 | 256.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-bellevue-weather | SUCCESS | 1.000 | 514.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:decision, feature:http, ipe |
| skill-flow-ixp-scaffold-multinode | SUCCESS | 1.000 | 774.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, node:ixp |
| skill-flow-feet-inches | SUCCESS | 1.000 | 443.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:switch |
| skill-flow-ipe-drive-to-slack | SUCCESS | 1.000 | 317.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, e2e, uipath-google-drive, uipath-salesforce-slack, ipe, mode:build |
| skill-flow-scheduled-trigger | SUCCESS | 1.000 | 211.8s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:scheduled-trigger, feature:trigger |
| skill-flow-terminate | SUCCESS | 1.000 | 309.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:terminate |
| skill-flow-bellevue-weather-simulated | SUCCESS | 0.889 | 703.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, node:decision, feature:http, ipe, simulation |
| skill-flow-trigger-with-filter | SUCCESS | 1.000 | 72.7s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:discover, connector-trigger, uipath-microsoft-outlook365, filter, ipe |
| skill-flow-dice-roller | SUCCESS | 1.000 | 188.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node |
| skill-flow-ipe-query-params | SUCCESS | 1.000 | 174.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-google-tasks, ipe, mode:build |
| skill-flow-hitl-smoke-multi-outcome-routing | SUCCESS | 1.000 | 364.7s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-devcon-billing-invoice-lookup | SUCCESS | 0.909 | 439.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, connector, path-to-ga |
| skill-flow-non-catalog-http-fallback | SUCCESS | 1.000 | 185.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, connector, uipath-uipath-http, feature:http, ipe |
| skill-flow-hitl-schema-design-simulated | SUCCESS | 1.000 | 436.2s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, simulation |
| skill-flow-inline-agent-robust | SUCCESS | 1.000 | 317.8s | claude-sonnet-4-6 | uipath-maestro-flow, mode:build, lifecycle:generate, node:inline-agent |
| skill-flow-ipe-dtl-load-by-default-false | SUCCESS | 1.000 | 272.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-automaticc-woocommerce, ipe, mode:build |
| skill-flow-hitl-quality-schema-design | SUCCESS | 1.000 | 405.3s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-move-node | SUCCESS | 1.000 | 131.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:decision |
| skill-flow-transform-group-by | SUCCESS | 1.000 | 190.5s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-batch-transform | SUCCESS | 1.000 | 156.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, node:batch-transform, context-grounding, mode:build |
| skill-flow-customer-escalation-simulated | SUCCESS | 0.938 | 380.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, node:decision, feature:trigger, connector, simulation |
| skill-flow-bindings-reconfigure-different-connection | SUCCESS | 1.000 | 231.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-ipe-multiselect | SUCCESS | 1.000 | 179.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, ipe, mode:build |
| skill-flow-lowcode-agent | SUCCESS | 1.000 | 200.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-openmeteo-weather | SUCCESS | 1.000 | 280.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node, connector, custom-codereval-openmeteoapis, ipe, custom-connector |
| skill-flow-ipe-complex-array | SUCCESS | 0.875 | 192.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-salesforce-slack, ipe, mode:build |
| skill-flow-switch | SUCCESS | 1.000 | 291.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:switch |
| skill-flow-devcon-billing-dispute-analyst | FAILURE | 0.500 | 335.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, path-to-ga |
| skill-flow-ipe-path-params | SUCCESS | 1.000 | 266.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-jdbc-databricks-query | SUCCESS | 1.000 | 605.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:single-node, connector, uipath-uipath-jdbc, ipe |
| skill-flow-ipe-enhanced-enum | SUCCESS | 1.000 | 338.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-automaticc-woocommerce, ipe, mode:build |
| skill-flow-ipe-jira-search-triage | SUCCESS | 1.000 | 410.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:loop, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-hitl-quality-brownfield-insert | SUCCESS | 1.000 | 518.9s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-outlook-trigger-inbox | SUCCESS | 1.000 | 367.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, feature:trigger, connector, mode:build, ipe |
| skill-flow-expense-approval-simulated | SUCCESS | 1.000 | 449.9s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, e2e, mode:build, lifecycle:generate, devcon, simulation |
| skill-flow-wiki-pageviews | SUCCESS | 1.000 | 694.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:transform, feature:http |
| skill-flow-eval-evaluator-type-choice | SUCCESS | 1.000 | 75.5s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:discover, feature:eval |
| skill-flow-summarize | SUCCESS | 1.000 | 193.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, node:summarize, context-grounding, mode:build |
| skill-flow-add-node | SUCCESS | 1.000 | 105.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:edit, shape:multi-node |
| skill-flow-generic-dynamic-node | SUCCESS | 1.000 | 310.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node, connector, uipath-servicenow-servicenow, ipe |
| skill-flow-subflow | SUCCESS | 1.000 | 206.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:subflow |
| skill-flow-ipe-searchable-joins | SUCCESS | 1.000 | 398.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-salesforce, ipe, mode:build |
| skill-flow-hitl-smoke-completed-port | SUCCESS | 1.000 | 256.0s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, mode:build, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-eval-no-auto-upload | SUCCESS | 1.000 | 53.9s | claude-sonnet-4-6 | uipath-maestro-flow, mode:operate, lifecycle:execute, feature:eval |
| skill-flow-remove-node | SUCCESS | 1.000 | 152.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node |
| skill-flow-cli-dice-roller-simulated | SUCCESS | 1.000 | 250.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, simulation |

## Run-time Notes

> **WARNING:** [skill-flow-group-to-subflow] expected_turns exceeded: 14/13 (cumulative SDK turns)
> **WARNING:** [skill-flow-api-workflow] expected_turns exceeded: 33/25 (cumulative SDK turns)
> **WARNING:** [skill-flow-eval-inline-agent] expected_turns exceeded: 32/30 (cumulative SDK turns)
> **WARNING:** [skill-flow-eval-simulation-crud] expected_turns exceeded: 27/20 (cumulative SDK turns)
> **WARNING:** [skill-flow-rpa] expected_turns exceeded: 33/26 (cumulative SDK turns)
> **WARNING:** [skill-flow-init-validate] expected_turns exceeded: 12/9 (cumulative SDK turns)
> **WARNING:** [skill-flow-slack-weather-pipeline] max_turns exhausted
> **WARNING:** [skill-flow-slack-weather-pipeline] expected_turns exceeded: 56/51 (cumulative SDK turns)
> **WARNING:** [skill-flow-ixp-routing-negative/sf-update] max_turns exhausted
> **WARNING:** [skill-flow-ixp-integration-handle-routing] expected_turns exceeded: 45/26 (cumulative SDK turns)
> **WARNING:** [skill-flow-coded-agent] expected_turns exceeded: 59/35 (cumulative SDK turns)
> **WARNING:** [skill-flow-feet-inches] expected_turns exceeded: 39/23 (cumulative SDK turns)
> **WARNING:** [skill-flow-move-node] expected_turns exceeded: 12/11 (cumulative SDK turns)
> **WARNING:** [skill-flow-hitl-quality-brownfield-insert] expected_turns exceeded: 39/34 (cumulative SDK turns)
> **WARNING:** [skill-flow-remove-node] expected_turns exceeded: 18/14 (cumulative SDK turns)


## Generation Metrics

| Task ID | Total Latency | Turns | Asst Turns | Avg Turn Latency |
|---------|---------------|-------|------------|------------------|
| skill-flow-e2e-escalation-jira-ticket | 515.7s | 1 | 75 | 474.2s |
| skill-flow-registry-discovery | 63.6s | 1 | 12 | 53.4s |
| skill-flow-ixp-routing-listing/r01 | 61.4s | 1 | 13 | 51.7s |
| skill-flow-ixp-routing-listing/r02 | 66.9s | 1 | 12 | 57.4s |
| skill-flow-ixp-routing-listing/r03 | 72.4s | 1 | 14 | 62.8s |
| skill-flow-ixp-routing-listing/r04 | 55.9s | 1 | 9 | 46.5s |
| skill-flow-ixp-routing-listing/r05 | 67.7s | 1 | 12 | 57.9s |
| skill-flow-ixp-routing-listing/r06 | 57.9s | 1 | 14 | 48.0s |
| skill-flow-ixp-routing-listing/r07 | 70.7s | 1 | 21 | 61.9s |
| skill-flow-ixp-routing-listing/r08 | 61.2s | 1 | 12 | 52.3s |
| skill-flow-ixp-routing-listing/r09 | 62.4s | 1 | 10 | 53.0s |
| skill-flow-ixp-routing-listing/r10 | 66.8s | 1 | 13 | 57.1s |
| skill-flow-file-attachment-debug | 253.2s | 1 | 35 | 220.4s |
| skill-flow-slack-channel-description | 358.1s | 1 | 54 | 317.2s |
| skill-flow-group-to-subflow | 676.5s | 1 | 27 | 642.0s |
| skill-flow-decision | 228.5s | 1 | 24 | 190.9s |
| skill-flow-devcon-billing-dispute-resolution | 1273.2s | 1 | 142 | 1224.3s |
| skill-flow-api-workflow | 303.6s | 1 | 59 | 269.4s |
| skill-flow-add-output | 87.0s | 1 | 16 | 42.1s |
| skill-flow-bindings-multi-connector-independence | 236.7s | 1 | 44 | 224.3s |
| skill-flow-eval-inline-agent | 520.9s | 1 | 51 | 511.5s |
| skill-flow-bindings-no-duplicates | 389.2s | 1 | 43 | 379.1s |
| skill-flow-devcon-billing-discrepancy-detector | 859.0s | 1 | 79 | 815.9s |
| skill-flow-slack-channel-description-simulated | 413.7s | 2 | 65 | 184.0s |
| skill-flow-outlook-waitfor-email | 220.2s | 1 | 40 | 207.2s |
| skill-flow-webhook-waitfor-parallel | 304.2s | 1 | 41 | 294.5s |
| skill-flow-multi-city-weather | 738.2s | 1 | 38 | 691.0s |
| skill-flow-ixp-scaffold-minimal | 321.3s | 1 | 36 | 305.1s |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 962.4s | 1 | 79 | 947.2s |
| skill-flow-eval-simulation-crud | 159.6s | 1 | 40 | 149.4s |
| skill-flow-ipe-ceql-where | 454.1s | 1 | 45 | 445.3s |
| skill-flow-ixp-e2e-project-selection/aviation | 247.2s | 1 | 43 | 233.9s |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 399.1s | 1 | 53 | 386.0s |
| skill-flow-reading-list | 239.4s | 1 | 30 | 211.6s |
| skill-flow-ipe-jira-lifecycle | 822.9s | 1 | 48 | 766.4s |
| skill-flow-rpa | 349.2s | 1 | 54 | 270.7s |
| skill-flow-init-validate | 97.3s | 1 | 21 | 92.0s |
| skill-flow-transform-map | 289.5s | 1 | 32 | 279.6s |
| skill-flow-ipe-generate-schema | 300.9s | 1 | 49 | 293.3s |
| skill-flow-slack-http-fallback | 278.2s | 1 | 56 | 234.9s |
| skill-flow-devcon-billing-resolution-writer | 298.9s | 1 | 26 | 262.5s |
| skill-flow-e2e-escalation-orchestrator-paths | 1016.9s | 1 | 77 | 865.4s |
| skill-flow-loop-multiply | 423.6s | 1 | 38 | 389.0s |
| skill-flow-hitl-quality-boolean-decision | 312.0s | 1 | 28 | 301.9s |
| skill-flow-slack-weather-pipeline | 624.6s | 1 | 88 | 586.3s |
| skill-flow-merge-parallel-sync | 186.2s | 1 | 32 | 174.2s |
| skill-flow-ipe-required-groups | 172.1s | 1 | 37 | 167.6s |
| skill-flow-solution-select-ask | 99.4s | 5 | 18 | 12.1s |
| skill-flow-ipe-enum | 754.4s | 1 | 62 | 744.4s |
| skill-flow-ixp-routing-negative/stripe-http | 240.5s | 1 | 29 | 238.0s |
| skill-flow-ixp-routing-negative/slack-summary | 276.3s | 1 | 31 | 273.9s |
| skill-flow-ixp-routing-negative/sf-update | 215.9s | 1 | 41 | 214.1s |
| skill-flow-ixp-routing-negative/http-webhook | 208.7s | 1 | 33 | 206.2s |
| skill-flow-ixp-routing-negative/gsheet-loop | 202.8s | 1 | 29 | 200.3s |
| skill-flow-ixp-routing-negative/queue-write | 205.8s | 1 | 38 | 203.6s |
| skill-flow-ixp-routing-negative/teams-decision | 163.4s | 1 | 36 | 160.0s |
| skill-flow-ixp-routing-negative/delay-email | 442.3s | 1 | 40 | 439.2s |
| skill-flow-e2e-devcon-expense-approval | 374.4s | 1 | 37 | 367.9s |
| skill-flow-bindings-idempotent-reconfigure | 381.6s | 1 | 55 | 375.2s |
| skill-flow-hitl-quality-result-downstream | 366.9s | 1 | 28 | 352.9s |
| skill-flow-ipe-jira-create-issue | 296.1s | 1 | 53 | 259.0s |
| skill-flow-customer-escalation | 743.7s | 1 | 71 | 734.4s |
| skill-flow-ipe-dtl-load-by-default-true | 164.2s | 1 | 44 | 161.8s |
| skill-flow-e2e-escalation-slack-alert | 350.9s | 1 | 67 | 318.5s |
| skill-flow-hitl-smoke-node-placed | 338.3s | 1 | 28 | 332.0s |
| skill-flow-ixp-routing/explicit | 234.1s | 1 | 42 | 232.4s |
| skill-flow-ixp-routing/invoice-extraction | 442.1s | 1 | 65 | 440.5s |
| skill-flow-ixp-routing/receipts | 192.1s | 1 | 37 | 190.5s |
| skill-flow-ixp-routing/contracts | 190.3s | 1 | 35 | 188.6s |
| skill-flow-ixp-routing/forms-classify | 193.8s | 1 | 33 | 192.2s |
| skill-flow-ipe-jira-get-issue | 412.0s | 1 | 54 | 383.6s |
| skill-flow-ixp-integration-handle-routing | 559.5s | 1 | 75 | 549.1s |
| skill-flow-update-node | 68.4s | 1 | 12 | 37.6s |
| skill-flow-eval-local-crud | 142.4s | 1 | 22 | 138.5s |
| skill-flow-delay | 112.4s | 1 | 25 | 104.7s |
| skill-flow-paginated-reference-lookup | 167.7s | 1 | 45 | 163.1s |
| skill-flow-coded-agent | 571.2s | 1 | 97 | 509.0s |
| skill-flow-interactive-customer-escalation-triage | 384.0s | 2 | 31 | 165.6s |
| skill-flow-ixp-invoice-extraction-simulated | 1090.4s | 3 | 82 | 346.9s |
| skill-flow-calculator | 168.3s | 1 | 29 | 144.0s |
| skill-flow-transform-filter | 256.8s | 1 | 26 | 248.2s |
| skill-flow-bellevue-weather | 514.3s | 1 | 30 | 486.9s |
| skill-flow-ixp-scaffold-multinode | 774.6s | 1 | 45 | 767.6s |
| skill-flow-feet-inches | 443.0s | 1 | 66 | 402.8s |
| skill-flow-ipe-drive-to-slack | 317.6s | 1 | 55 | 315.6s |
| skill-flow-scheduled-trigger | 211.8s | 1 | 33 | 204.8s |
| skill-flow-terminate | 309.7s | 1 | 40 | 290.0s |
| skill-flow-bellevue-weather-simulated | 703.1s | 3 | 39 | 216.9s |
| skill-flow-trigger-with-filter | 72.7s | 1 | 12 | 70.3s |
| skill-flow-dice-roller | 188.9s | 1 | 26 | 169.4s |
| skill-flow-ipe-query-params | 174.3s | 1 | 33 | 171.0s |
| skill-flow-hitl-smoke-multi-outcome-routing | 364.7s | 1 | 32 | 350.9s |
| skill-flow-devcon-billing-invoice-lookup | 439.7s | 1 | 70 | 364.0s |
| skill-flow-non-catalog-http-fallback | 185.2s | 1 | 49 | 181.2s |
| skill-flow-hitl-schema-design-simulated | 436.2s | 3 | 37 | 133.5s |
| skill-flow-inline-agent-robust | 317.8s | 1 | 30 | 312.1s |
| skill-flow-ipe-dtl-load-by-default-false | 272.9s | 1 | 65 | 268.2s |
| skill-flow-hitl-quality-schema-design | 405.3s | 1 | 35 | 396.2s |
| skill-flow-move-node | 131.3s | 1 | 23 | 102.7s |
| skill-flow-transform-group-by | 190.5s | 1 | 26 | 183.3s |
| skill-flow-batch-transform | 156.7s | 1 | 27 | 148.4s |
| skill-flow-customer-escalation-simulated | 380.6s | 2 | 78 | 178.0s |
| skill-flow-bindings-reconfigure-different-connection | 231.7s | 1 | 45 | 227.3s |
| skill-flow-ipe-multiselect | 179.8s | 1 | 44 | 176.3s |
| skill-flow-lowcode-agent | 200.5s | 1 | 30 | 166.2s |
| skill-flow-openmeteo-weather | 280.6s | 1 | 42 | 253.7s |
| skill-flow-ipe-complex-array | 192.8s | 1 | 43 | 190.2s |
| skill-flow-switch | 291.2s | 1 | 31 | 269.9s |
| skill-flow-devcon-billing-dispute-analyst | 335.9s | 1 | 70 | 298.6s |
| skill-flow-ipe-path-params | 266.2s | 1 | 48 | 261.4s |
| skill-flow-jdbc-databricks-query | 605.2s | 1 | 65 | 602.1s |
| skill-flow-ipe-enhanced-enum | 338.0s | 1 | 49 | 334.8s |
| skill-flow-ipe-jira-search-triage | 410.0s | 1 | 46 | 369.1s |
| skill-flow-hitl-quality-brownfield-insert | 518.9s | 1 | 60 | 513.3s |
| skill-flow-outlook-trigger-inbox | 367.5s | 1 | 53 | 359.3s |
| skill-flow-expense-approval-simulated | 449.9s | 2 | 33 | 210.8s |
| skill-flow-wiki-pageviews | 694.5s | 1 | 30 | 651.3s |
| skill-flow-eval-evaluator-type-choice | 75.5s | 1 | 18 | 72.6s |
| skill-flow-summarize | 193.7s | 1 | 27 | 185.7s |
| skill-flow-add-node | 105.2s | 1 | 17 | 78.6s |
| skill-flow-generic-dynamic-node | 310.5s | 1 | 59 | 282.4s |
| skill-flow-subflow | 206.0s | 1 | 23 | 183.0s |
| skill-flow-ipe-searchable-joins | 398.1s | 1 | 37 | 395.3s |
| skill-flow-hitl-smoke-completed-port | 256.0s | 1 | 29 | 248.5s |
| skill-flow-eval-no-auto-upload | 53.9s | 1 | 16 | 51.9s |
| skill-flow-remove-node | 152.5s | 1 | 33 | 130.4s |
| skill-flow-cli-dice-roller-simulated | 250.4s | 3 | 37 | 72.2s |


## Token Usage

**Total Tokens**: 172,211,700 (input: 106,793, output: 2,002,567)
**Cache Tokens**: write: 9,949,123, read: 160,153,217
**Agent Cost**: $115.7141
**Eval Overhead (judge + simulator)**: $0.0904
**Total Cost**: $115.8044
**Avg Tokens/Task**: 1,355,997

| Task ID | Input (uncached) | Output | Cache Write | Cache Read | Total | Cost |
|---------|------------------|--------|-------------|------------|-------|------|
| skill-flow-e2e-escalation-jira-ticket | 36 | 22,654 | 105,143 | 3,512,528 | 3,640,361 | $1.7880 |
| skill-flow-registry-discovery | 7 | 1,698 | 19,674 | 180,650 | 202,029 | $0.1535 |
| skill-flow-ixp-routing-listing/r01 | 8 | 2,356 | 28,419 | 200,335 | 231,118 | $0.2020 |
| skill-flow-ixp-routing-listing/r02 | 8 | 2,353 | 29,130 | 196,657 | 228,148 | $0.2036 |
| skill-flow-ixp-routing-listing/r03 | 10 | 1,851 | 69,061 | 308,571 | 379,493 | $0.3793 |
| skill-flow-ixp-routing-listing/r04 | 7 | 1,757 | 53,717 | 120,353 | 175,834 | $0.2639 |
| skill-flow-ixp-routing-listing/r05 | 9 | 2,365 | 29,547 | 245,709 | 277,630 | $0.2200 |
| skill-flow-ixp-routing-listing/r06 | 9 | 1,301 | 69,018 | 242,177 | 312,505 | $0.3510 |
| skill-flow-ixp-routing-listing/r07 | 13 | 1,829 | 41,132 | 442,818 | 485,792 | $0.3146 |
| skill-flow-ixp-routing-listing/r08 | 12 | 1,259 | 69,271 | 309,463 | 380,005 | $0.3715 |
| skill-flow-ixp-routing-listing/r09 | 8 | 2,211 | 53,699 | 167,504 | 223,422 | $0.2848 |
| skill-flow-ixp-routing-listing/r10 | 9 | 1,860 | 28,471 | 251,297 | 281,637 | $0.2101 |
| skill-flow-file-attachment-debug | 2,658 | 8,667 | 73,277 | 859,454 | 944,056 | $0.6706 |
| skill-flow-slack-channel-description | 26 | 11,849 | 93,240 | 2,232,788 | 2,337,903 | $1.1973 |
| skill-flow-group-to-subflow | 16 | 49,869 | 135,622 | 730,083 | 915,590 | $1.4757 |
| skill-flow-decision | 10 | 11,106 | 83,181 | 394,316 | 488,613 | $0.5968 |
| skill-flow-devcon-billing-dispute-resolution | 7,561 | 61,841 | 214,196 | 5,142,046 | 5,425,644 | $3.2961 |
| skill-flow-api-workflow | 23 | 13,128 | 103,603 | 1,574,355 | 1,691,109 | $1.0578 |
| skill-flow-add-output | 11 | 1,535 | 35,715 | 396,326 | 433,587 | $0.2759 |
| skill-flow-bindings-multi-connector-independence | 19 | 8,227 | 78,242 | 1,389,214 | 1,475,702 | $0.8336 |
| skill-flow-eval-inline-agent | 3,808 | 30,620 | 107,894 | 1,661,664 | 1,803,986 | $1.3738 |
| skill-flow-bindings-no-duplicates | 17 | 18,477 | 77,208 | 1,155,975 | 1,251,677 | $0.9135 |
| skill-flow-devcon-billing-discrepancy-detector | 33 | 38,518 | 132,848 | 3,944,746 | 4,116,145 | $2.2595 |
| skill-flow-slack-channel-description-simulated | 33 | 14,639 | 76,473 | 2,326,981 | 2,418,126 | $1.2093 |
| skill-flow-outlook-waitfor-email | 15 | 7,654 | 76,190 | 882,094 | 965,953 | $0.6652 |
| skill-flow-webhook-waitfor-parallel | 14 | 12,097 | 82,620 | 847,702 | 942,433 | $0.7456 |
| skill-flow-multi-city-weather | 19 | 42,250 | 67,323 | 1,201,084 | 1,310,676 | $1.2466 |
| skill-flow-ixp-scaffold-minimal | 17 | 14,842 | 73,179 | 1,116,661 | 1,204,699 | $0.8321 |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 30 | 47,303 | 106,416 | 2,763,031 | 2,916,780 | $1.9376 |
| skill-flow-eval-simulation-crud | 27 | 4,419 | 28,363 | 1,301,038 | 1,333,847 | $0.5630 |
| skill-flow-ipe-ceql-where | 19 | 22,317 | 87,457 | 1,307,379 | 1,417,172 | $1.0550 |
| skill-flow-ixp-e2e-project-selection/aviation | 21 | 10,878 | 88,483 | 1,567,734 | 1,667,116 | $0.9654 |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 27 | 14,815 | 77,498 | 1,949,925 | 2,042,265 | $1.0979 |
| skill-flow-reading-list | 12 | 9,086 | 69,593 | 670,259 | 748,950 | $0.5984 |
| skill-flow-ipe-jira-lifecycle | 19 | 44,811 | 211,048 | 1,663,677 | 1,919,555 | $1.9628 |
| skill-flow-rpa | 28 | 9,673 | 61,130 | 1,780,793 | 1,851,624 | $0.9087 |
| skill-flow-init-validate | 9 | 2,980 | 30,236 | 315,612 | 348,837 | $0.2528 |
| skill-flow-transform-map | 13 | 14,763 | 54,076 | 660,168 | 729,020 | $0.6223 |
| skill-flow-ipe-generate-schema | 17 | 9,568 | 87,223 | 1,182,345 | 1,279,153 | $0.8254 |
| skill-flow-slack-http-fallback | 20 | 7,859 | 84,874 | 1,325,715 | 1,418,468 | $0.8339 |
| skill-flow-devcon-billing-resolution-writer | 11 | 14,850 | 65,978 | 546,265 | 627,104 | $0.6341 |
| skill-flow-e2e-escalation-orchestrator-paths | 11,642 | 50,586 | 151,966 | 3,247,772 | 3,461,966 | $2.3379 |
| skill-flow-loop-multiply | 18 | 23,498 | 71,229 | 1,099,617 | 1,194,362 | $0.9495 |
| skill-flow-hitl-quality-boolean-decision | 12 | 18,261 | 67,099 | 590,170 | 675,542 | $0.7026 |
| skill-flow-slack-weather-pipeline | 42 | 24,966 | 129,681 | 4,725,757 | 4,880,446 | $2.2786 |
| skill-flow-merge-parallel-sync | 10,362 | 8,993 | 60,525 | 609,600 | 689,480 | $0.5758 |
| skill-flow-ipe-required-groups | 10,364 | 5,938 | 85,334 | 970,044 | 1,071,680 | $0.7312 |
| skill-flow-solution-select-ask | 18 | 1,321 | 11,483 | 336,889 | 349,711 | $0.1665 |
| skill-flow-ipe-enum | 24 | 40,710 | 102,874 | 2,127,241 | 2,270,849 | $1.6347 |
| skill-flow-ixp-routing-negative/stripe-http | 11 | 12,447 | 60,873 | 514,419 | 587,750 | $0.5693 |
| skill-flow-ixp-routing-negative/slack-summary | 12 | 16,633 | 75,773 | 709,569 | 801,987 | $0.7466 |
| skill-flow-ixp-routing-negative/sf-update | 21 | 9,839 | 59,677 | 1,203,897 | 1,273,434 | $0.7326 |
| skill-flow-ixp-routing-negative/http-webhook | 18 | 9,901 | 52,614 | 979,202 | 1,041,735 | $0.6396 |
| skill-flow-ixp-routing-negative/gsheet-loop | 12 | 10,178 | 70,293 | 625,342 | 705,825 | $0.6039 |
| skill-flow-ixp-routing-negative/queue-write | 23 | 5,681 | 44,381 | 1,255,001 | 1,305,086 | $0.6282 |
| skill-flow-ixp-routing-negative/teams-decision | 19 | 6,169 | 73,654 | 1,318,131 | 1,397,973 | $0.7642 |
| skill-flow-ixp-routing-negative/delay-email | 19 | 23,259 | 54,897 | 1,045,003 | 1,123,178 | $0.8683 |
| skill-flow-e2e-devcon-expense-approval | 14 | 23,211 | 70,685 | 809,305 | 903,215 | $0.8561 |
| skill-flow-bindings-idempotent-reconfigure | 26 | 19,333 | 75,362 | 2,073,987 | 2,168,708 | $1.1949 |
| skill-flow-hitl-quality-result-downstream | 12 | 21,796 | 69,293 | 620,418 | 711,519 | $0.7730 |
| skill-flow-ipe-jira-create-issue | 24 | 10,131 | 98,530 | 1,989,436 | 2,098,121 | $1.1184 |
| skill-flow-customer-escalation | 17,100 | 42,594 | 163,623 | 2,295,635 | 2,518,952 | $1.9925 |
| skill-flow-ipe-dtl-load-by-default-true | 2,737 | 6,420 | 77,228 | 1,041,289 | 1,127,674 | $0.7065 |
| skill-flow-e2e-escalation-slack-alert | 32 | 15,385 | 111,413 | 3,163,159 | 3,289,989 | $1.5976 |
| skill-flow-hitl-smoke-node-placed | 14 | 18,925 | 50,204 | 622,696 | 691,839 | $0.6590 |
| skill-flow-ixp-routing/explicit | 21 | 11,176 | 94,480 | 1,546,471 | 1,652,148 | $0.9859 |
| skill-flow-ixp-routing/invoice-extraction | 30 | 25,919 | 87,429 | 2,388,499 | 2,501,877 | $1.4333 |
| skill-flow-ixp-routing/receipts | 16 | 9,322 | 73,537 | 910,445 | 993,320 | $0.6888 |
| skill-flow-ixp-routing/contracts | 16 | 9,482 | 80,213 | 1,035,315 | 1,125,026 | $0.7537 |
| skill-flow-ixp-routing/forms-classify | 15 | 9,600 | 69,926 | 921,261 | 1,000,802 | $0.6826 |
| skill-flow-ipe-jira-get-issue | 26 | 18,587 | 95,785 | 2,204,234 | 2,318,632 | $1.2993 |
| skill-flow-ixp-integration-handle-routing | 34 | 31,083 | 102,199 | 2,895,597 | 3,028,913 | $1.7183 |
| skill-flow-update-node | 7 | 1,709 | 30,028 | 268,805 | 300,549 | $0.2189 |
| skill-flow-eval-local-crud | 11 | 6,667 | 31,898 | 440,795 | 479,371 | $0.3519 |
| skill-flow-delay | 13 | 3,912 | 55,786 | 705,607 | 765,318 | $0.4796 |
| skill-flow-paginated-reference-lookup | 20 | 6,667 | 100,255 | 1,628,652 | 1,735,594 | $0.9646 |
| skill-flow-coded-agent | 60 | 22,795 | 140,695 | 4,543,921 | 4,707,471 | $2.2329 |
| skill-flow-interactive-customer-escalation-triage | 13 | 19,472 | 68,625 | 647,653 | 735,763 | $0.7527 |
| skill-flow-ixp-invoice-extraction-simulated | 24,200 | 53,084 | 287,889 | 2,710,292 | 3,075,465 | $2.7843 |
| skill-flow-calculator | 11 | 6,645 | 65,646 | 578,327 | 650,629 | $0.5194 |
| skill-flow-transform-filter | 10 | 13,113 | 61,833 | 480,384 | 555,340 | $0.5727 |
| skill-flow-bellevue-weather | 13 | 34,144 | 126,928 | 599,244 | 760,329 | $1.1680 |
| skill-flow-ixp-scaffold-multinode | 19 | 47,140 | 98,817 | 1,372,010 | 1,517,986 | $1.4893 |
| skill-flow-feet-inches | 32 | 21,726 | 72,893 | 2,368,447 | 2,463,098 | $1.3099 |
| skill-flow-ipe-drive-to-slack | 22 | 14,026 | 89,700 | 1,659,254 | 1,763,002 | $1.0446 |
| skill-flow-scheduled-trigger | 17 | 11,709 | 63,179 | 1,028,052 | 1,102,957 | $0.7210 |
| skill-flow-terminate | 18 | 14,275 | 62,222 | 1,112,016 | 1,188,531 | $0.7811 |
| skill-flow-bellevue-weather-simulated | 17 | 38,058 | 153,957 | 791,075 | 983,107 | $1.3990 |
| skill-flow-trigger-with-filter | 7 | 3,483 | 30,342 | 206,330 | 240,162 | $0.2279 |
| skill-flow-dice-roller | 11 | 8,118 | 56,544 | 511,543 | 576,216 | $0.4873 |
| skill-flow-ipe-query-params | 15 | 7,581 | 56,746 | 764,027 | 828,369 | $0.5558 |
| skill-flow-hitl-smoke-multi-outcome-routing | 12 | 20,629 | 61,920 | 592,262 | 674,823 | $0.7193 |
| skill-flow-devcon-billing-invoice-lookup | 8,730 | 16,014 | 110,362 | 2,787,249 | 2,922,355 | $1.5164 |
| skill-flow-non-catalog-http-fallback | 24 | 6,986 | 84,290 | 1,757,104 | 1,848,404 | $0.9481 |
| skill-flow-hitl-schema-design-simulated | 17 | 22,896 | 76,432 | 765,516 | 864,861 | $0.8714 |
| skill-flow-inline-agent-robust | 12 | 18,527 | 69,247 | 625,342 | 713,128 | $0.7252 |
| skill-flow-ipe-dtl-load-by-default-false | 1,726 | 10,720 | 109,220 | 2,243,831 | 2,365,497 | $1.2487 |
| skill-flow-hitl-quality-schema-design | 15 | 23,212 | 60,526 | 804,455 | 888,208 | $0.8165 |
| skill-flow-move-node | 12 | 7,798 | 37,145 | 576,502 | 621,457 | $0.4293 |
| skill-flow-transform-group-by | 13 | 9,639 | 51,130 | 622,826 | 683,608 | $0.5232 |
| skill-flow-batch-transform | 11 | 7,720 | 60,426 | 551,296 | 619,453 | $0.5078 |
| skill-flow-customer-escalation-simulated | 30 | 16,712 | 128,799 | 2,935,043 | 3,080,584 | $1.6224 |
| skill-flow-bindings-reconfigure-different-connection | 19 | 9,875 | 87,773 | 1,525,131 | 1,622,798 | $0.9349 |
| skill-flow-ipe-multiselect | 19 | 6,225 | 77,127 | 1,114,722 | 1,198,093 | $0.7171 |
| skill-flow-lowcode-agent | 12 | 9,505 | 51,439 | 564,024 | 624,980 | $0.5047 |
| skill-flow-openmeteo-weather | 19 | 11,931 | 86,962 | 1,427,683 | 1,526,595 | $0.9334 |
| skill-flow-ipe-complex-array | 19 | 7,472 | 68,280 | 1,220,809 | 1,296,580 | $0.7344 |
| skill-flow-switch | 13 | 15,096 | 66,608 | 696,446 | 778,163 | $0.6852 |
| skill-flow-devcon-billing-dispute-analyst | 32 | 15,364 | 104,542 | 3,055,989 | 3,175,927 | $1.5394 |
| skill-flow-ipe-path-params | 3,866 | 11,447 | 92,138 | 1,227,556 | 1,335,007 | $0.8971 |
| skill-flow-jdbc-databricks-query | 27 | 25,330 | 98,662 | 2,533,041 | 2,657,060 | $1.5099 |
| skill-flow-ipe-enhanced-enum | 19 | 17,134 | 85,251 | 1,431,316 | 1,533,720 | $1.0062 |
| skill-flow-ipe-jira-search-triage | 18 | 18,353 | 101,590 | 1,368,964 | 1,488,925 | $1.0670 |
| skill-flow-hitl-quality-brownfield-insert | 23 | 30,551 | 85,579 | 1,883,197 | 1,999,350 | $1.3442 |
| skill-flow-outlook-trigger-inbox | 18 | 19,485 | 91,401 | 1,279,692 | 1,390,596 | $1.0190 |
| skill-flow-expense-approval-simulated | 13 | 25,830 | 72,215 | 661,639 | 759,697 | $0.8685 |
| skill-flow-wiki-pageviews | 13 | 40,955 | 93,916 | 753,379 | 888,263 | $1.1926 |
| skill-flow-eval-evaluator-type-choice | 11 | 2,340 | 20,178 | 381,456 | 403,985 | $0.2252 |
| skill-flow-summarize | 11 | 11,606 | 69,711 | 596,152 | 677,480 | $0.6144 |
| skill-flow-add-node | 9 | 5,478 | 32,480 | 389,063 | 427,030 | $0.3207 |
| skill-flow-generic-dynamic-node | 26 | 9,683 | 97,078 | 2,325,703 | 2,432,490 | $1.2071 |
| skill-flow-subflow | 11 | 11,278 | 51,643 | 501,366 | 564,298 | $0.5133 |
| skill-flow-ipe-searchable-joins | 13 | 24,159 | 84,118 | 769,670 | 877,960 | $0.9088 |
| skill-flow-hitl-smoke-completed-port | 11 | 14,951 | 53,830 | 511,053 | 579,845 | $0.5795 |
| skill-flow-eval-no-auto-upload | 10 | 1,757 | 15,952 | 319,794 | 337,513 | $0.1821 |
| skill-flow-remove-node | 19 | 8,189 | 35,967 | 999,155 | 1,043,330 | $0.5575 |
| skill-flow-cli-dice-roller-simulated | 21 | 9,917 | 69,475 | 995,464 | 1,074,877 | $0.7145 |


## Command Telemetry

**Total Commands**: 2883
**Success Rate**: 2781/2883 (96.5%)

### Commands by Tool

| Tool | Count | % |
|------|-------|---|
| Bash | 1436 | 49.8% |
| Read | 832 | 28.9% |
| Edit | 333 | 11.6% |
| Skill | 139 | 4.8% |
| Write | 76 | 2.6% |
| TaskUpdate | 24 | 0.8% |
| Glob | 19 | 0.7% |
| TaskCreate | 12 | 0.4% |
| Grep | 10 | 0.3% |
| Agent | 2 | 0.1% |

### Performance

- **Average Command Time**: 3484.9ms
- **Total Command Time**: 10046.98s

### Slowest Commands

| Tool | Duration | Parameters |
|------|----------|------------|
| Agent | 156461ms | {'description': 'Read flow wiring references for v... |
| Bash | 63911ms | {'command': 'cd /work/output/artifacts/skill-flow-... |
| Bash | 56975ms | {'command': 'python3 << \'EOF\'\nimport subprocess... |
| Bash | 55650ms | {'command': 'uip maestro flow registry get core.tr... |
| Bash | 55251ms | {'command': 'uip maestro flow registry get core.lo... |

**Most Common Pattern**: `Bash → Bash → Bash`

**Skill Tool Invoked**: 139 time(s)

## Agent Settings

- **Permission Mode**: acceptEdits
- **Allowed Tools**: Skill, Bash, Read, Write, Edit, Glob, Grep
- **Model**: us.anthropic.claude-sonnet-4-6
- **Max Turns**: 120
- **System Prompt**: You are a coding agent. Do not access files in sibling runs/* directories. Everywhere else is permitted. 
- **Plugins**: /home/azureuser/projects/skills

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