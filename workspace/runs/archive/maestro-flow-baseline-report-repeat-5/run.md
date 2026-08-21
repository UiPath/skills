# Evaluation Run Report

**Run ID**: `maestro-flow-baseline-report-repeat-5`
**Date**: 2026-07-24 19:24:04
**Duration**: 7698.04s
**Model**: `claude-sonnet-4-6`

## Summary

- **Total Tasks**: 615
- **Succeeded**: 550
- **Failed**: 58
- **Errors**: 7
- **Success Rate**: 90.5%
- **Avg Reliability Score**: 0.928
- **Avg Generation Latency**: 360.9s
- **Total Assistant Turns**: 26235
- **Crashed Partials**: 7 (1 recovered, 6 terminal)

## Task Details

| Task ID | Status | Reliability Score | Latency | Model | Tags |
|---------|--------|-------------------|---------|-------|------|
| skill-flow-inline-agent-robust | SUCCESS | 1.000 | 307.0s | claude-sonnet-4-6 | uipath-maestro-flow, mode:build, lifecycle:generate, node:inline-agent |
| skill-flow-remove-node | SUCCESS | 1.000 | 161.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node |
| skill-flow-decision | SUCCESS | 1.000 | 212.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:decision |
| skill-flow-ixp-scaffold-minimal | SUCCESS | 1.000 | 469.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-reading-list | SUCCESS | 1.000 | 243.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:transform |
| skill-flow-ipe-drive-to-slack | SUCCESS | 1.000 | 390.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, e2e, uipath-google-drive, uipath-salesforce-slack, ipe, mode:build |
| skill-flow-eval-inline-agent | SUCCESS | 1.000 | 556.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:inline-agent, feature:eval |
| skill-flow-ipe-jira-get-issue | FAILURE | 0.286 | 445.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-coded-agent | MAX_TURNS_EXHAUSTED | 0.375 | 293.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource, path-to-ga |
| skill-flow-ixp-routing-negative/stripe-http | SUCCESS | 1.000 | 212.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/slack-summary | SUCCESS | 1.000 | 297.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/sf-update | SUCCESS | 1.000 | 332.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/http-webhook | SUCCESS | 1.000 | 279.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/gsheet-loop | SUCCESS | 1.000 | 343.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/queue-write | SUCCESS | 1.000 | 210.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/teams-decision | SUCCESS | 1.000 | 253.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/delay-email | SUCCESS | 1.000 | 325.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-integration-handle-routing | SUCCESS | 1.000 | 427.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:ixp, node:decision |
| skill-flow-paginated-reference-lookup | SUCCESS | 1.000 | 259.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, e2e, mode:build, lifecycle:generate, shape:multi-node, connector, uipath-salesforce-slack, feature:records |
| skill-flow-registry-discovery | SUCCESS | 1.000 | 131.8s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, lifecycle:discover, feature:registry |
| skill-flow-ipe-jira-lifecycle | SUCCESS | 1.000 | 707.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:loop, node:switch, node:decision, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-summarize | SUCCESS | 1.000 | 189.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, node:summarize, context-grounding, mode:build |
| skill-flow-scheduled-trigger | SUCCESS | 1.000 | 263.6s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:scheduled-trigger, feature:trigger |
| skill-flow-slack-weather-pipeline | ERROR | 0.000 | 1211.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:decision, connector, feature:http |
| skill-flow-eval-no-auto-upload | SUCCESS | 1.000 | 119.0s | claude-sonnet-4-6 | uipath-maestro-flow, mode:operate, lifecycle:execute, feature:eval |
| skill-flow-ixp-routing/explicit | SUCCESS | 1.000 | 331.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/invoice-extraction | SUCCESS | 1.000 | 445.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/receipts | SUCCESS | 1.000 | 330.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/contracts | SUCCESS | 1.000 | 313.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/forms-classify | SUCCESS | 1.000 | 354.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-bellevue-weather | SUCCESS | 1.000 | 509.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:decision, feature:http, ipe |
| skill-flow-customer-escalation-simulated | MAX_TURNS_EXHAUSTED | 0.000 | 874.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, node:decision, feature:trigger, connector, simulation |
| skill-flow-ipe-enum | SUCCESS | 1.000 | 698.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle-generate, shape-multi-node, connector, uipath-google-gmail, ipe, mode:build |
| skill-flow-hitl-quality-schema-design | SUCCESS | 1.000 | 276.9s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-webhook-waitfor-parallel | SUCCESS | 1.000 | 278.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, connector, feature:trigger, feature:http, wait-for-event, uipath-http-webhook, ipe |
| skill-flow-solution-select-ask | FAILURE | 0.714 | 119.5s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, simulation |
| skill-flow-terminate | SUCCESS | 1.000 | 311.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:terminate |
| skill-flow-merge-parallel-sync | FAILURE | 0.625 | 198.3s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:multi-node, node:merge |
| skill-flow-multi-city-weather | SUCCESS | 1.000 | 830.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:loop, feature:http |
| skill-flow-ixp-routing-listing/r01 | SUCCESS | 1.000 | 62.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r02 | SUCCESS | 1.000 | 67.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r03 | SUCCESS | 1.000 | 45.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r04 | SUCCESS | 1.000 | 50.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r05 | SUCCESS | 1.000 | 59.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r06 | SUCCESS | 1.000 | 55.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r07 | SUCCESS | 1.000 | 66.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r08 | SUCCESS | 1.000 | 70.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r09 | SUCCESS | 1.000 | 54.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r10 | SUCCESS | 1.000 | 58.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-add-output | SUCCESS | 1.000 | 61.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node |
| skill-flow-hitl-quality-brownfield-insert | SUCCESS | 1.000 | 548.9s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-feet-inches | SUCCESS | 1.000 | 386.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:switch |
| skill-flow-bindings-multi-connector-independence | SUCCESS | 1.000 | 277.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, bindings, regression |
| skill-flow-non-catalog-http-fallback | SUCCESS | 1.000 | 214.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, connector, uipath-uipath-http, feature:http, ipe |
| skill-flow-update-node | SUCCESS | 1.000 | 76.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:decision |
| skill-flow-devcon-billing-dispute-resolution | FAILURE | 0.500 | 938.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, node:ixp, connector, path-to-ga |
| skill-flow-cli-dice-roller-simulated | SUCCESS | 1.000 | 290.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, simulation |
| skill-flow-ipe-complex-array | SUCCESS | 1.000 | 508.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, ipe, mode:build |
| skill-flow-ipe-searchable-joins | SUCCESS | 1.000 | 514.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-salesforce, ipe, mode:build |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | SUCCESS | 1.000 | 842.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:ixp, connector, feature:http |
| skill-flow-add-node | SUCCESS | 1.000 | 105.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:edit, shape:multi-node |
| skill-flow-delay | SUCCESS | 1.000 | 200.9s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:delay |
| skill-flow-generic-dynamic-node | FAILURE | 0.429 | 493.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node, connector, uipath-servicenow-servicenow, ipe |
| skill-flow-devcon-billing-invoice-lookup | SUCCESS | 1.000 | 827.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, connector, path-to-ga |
| skill-flow-ipe-multiselect | SUCCESS | 1.000 | 541.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-act-act365, ipe, mode:build |
| skill-flow-transform-group-by | SUCCESS | 1.000 | 201.7s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-file-attachment-debug | SUCCESS | 1.000 | 253.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node |
| skill-flow-ipe-required-groups | SUCCESS | 1.000 | 246.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-microsoft-teams, ipe, mode:build |
| skill-flow-eval-evaluator-type-choice | SUCCESS | 1.000 | 111.9s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:discover, feature:eval |
| skill-flow-ipe-jira-search-triage | FAILURE | 0.286 | 336.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:loop, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-eval-local-crud | SUCCESS | 1.000 | 231.1s | claude-sonnet-4-6 | uipath-maestro-flow, mode:build, lifecycle:generate, feature:eval |
| skill-flow-devcon-billing-discrepancy-detector | SUCCESS | 1.000 | 713.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, connector, path-to-ga |
| skill-flow-batch-transform | SUCCESS | 1.000 | 178.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, node:batch-transform, context-grounding, mode:build |
| skill-flow-ipe-jira-create-issue | SUCCESS | 1.000 | 339.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-outlook-trigger-inbox | SUCCESS | 1.000 | 293.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, feature:trigger, connector, mode:build, ipe |
| skill-flow-hitl-smoke-completed-port | SUCCESS | 1.000 | 224.7s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, mode:build, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-hitl-smoke-node-placed | SUCCESS | 1.000 | 196.2s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, lifecycle:generate, shape:single-node, node:hitl |
| skill-flow-devcon-billing-resolution-writer | SUCCESS | 1.000 | 320.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, path-to-ga |
| skill-flow-ipe-enhanced-enum | SUCCESS | 1.000 | 430.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-automaticc-woocommerce, ipe, mode:build |
| skill-flow-bindings-idempotent-reconfigure | SUCCESS | 1.000 | 616.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-expense-approval-simulated | SUCCESS | 1.000 | 621.0s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, e2e, mode:build, lifecycle:generate, devcon, simulation |
| skill-flow-rpa | SUCCESS | 1.000 | 211.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-loop-multiply | SUCCESS | 1.000 | 331.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:loop |
| skill-flow-init-validate | SUCCESS | 1.000 | 116.5s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, lifecycle:generate |
| skill-flow-slack-http-fallback | SUCCESS | 1.000 | 231.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:single-node, connector, uipath-salesforce-slack, feature:http, ipe |
| skill-flow-move-node | SUCCESS | 1.000 | 140.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:decision |
| skill-flow-ipe-path-params | SUCCESS | 1.000 | 369.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-dice-roller | SUCCESS | 1.000 | 184.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node |
| skill-flow-hitl-quality-result-downstream | SUCCESS | 1.000 | 142.4s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-ixp-e2e-project-selection/aviation | SUCCESS | 1.000 | 388.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-ixp-e2e-project-selection/birth-certificate | SUCCESS | 1.000 | 316.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-ipe-dtl-load-by-default-true | SUCCESS | 1.000 | 268.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-microsoft-azure, ipe, mode:build |
| skill-flow-slack-channel-description | SUCCESS | 1.000 | 277.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, connector |
| skill-flow-wiki-pageviews | SUCCESS | 1.000 | 644.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:transform, feature:http |
| skill-flow-ixp-invoice-extraction-simulated | SUCCESS | 0.900 | 2016.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, node:ixp, connector, feature:http, simulation |
| skill-flow-openmeteo-weather | SUCCESS | 1.000 | 239.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node, connector, custom-codereval-openmeteoapis, ipe, custom-connector |
| skill-flow-outlook-waitfor-email | SUCCESS | 1.000 | 201.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, feature:trigger, connector, uipath-microsoft-outlook365, filter, ipe, wait-for-event |
| skill-flow-customer-escalation | SUCCESS | 1.000 | 448.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:decision, feature:trigger, connector |
| skill-flow-calculator | SUCCESS | 1.000 | 224.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node |
| skill-flow-trigger-with-filter | SUCCESS | 1.000 | 111.1s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:discover, connector-trigger, uipath-microsoft-outlook365, filter, ipe |
| skill-flow-e2e-devcon-expense-approval | SUCCESS | 1.000 | 312.4s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, e2e, devcon |
| skill-flow-ipe-dtl-load-by-default-false | SUCCESS | 1.000 | 374.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-automaticc-woocommerce, ipe, mode:build |
| skill-flow-transform-map | SUCCESS | 1.000 | 245.4s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-slack-channel-description-simulated | SUCCESS | 1.000 | 375.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, connector, simulation |
| skill-flow-eval-simulation-crud | SUCCESS | 1.000 | 163.8s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, feature:eval |
| skill-flow-devcon-billing-dispute-analyst | FAILURE | 0.375 | 332.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, path-to-ga |
| skill-flow-api-workflow | FAILURE | 0.375 | 285.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-hitl-smoke-multi-outcome-routing | SUCCESS | 1.000 | 314.3s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-interactive-customer-escalation-triage | FAILURE | 0.448 | 328.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, feature:escalation, feature:conversational |
| skill-flow-hitl-quality-boolean-decision | SUCCESS | 1.000 | 315.4s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-group-to-subflow | TIMEOUT | 0.000 | 905.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:subflow |
| skill-flow-switch | SUCCESS | 1.000 | 336.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:switch |
| skill-flow-ipe-query-params | SUCCESS | 1.000 | 168.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-google-tasks, ipe, mode:build |
| skill-flow-ipe-ceql-where | SUCCESS | 1.000 | 498.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, connector, ceql, filter, uipath-microsoft-azureactivedirectory, ipe, mode:build |
| skill-flow-ixp-scaffold-multinode | SUCCESS | 1.000 | 398.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, node:ixp |
| skill-flow-bellevue-weather-simulated | ERROR | 0.000 | 1209.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, node:decision, feature:http, ipe, simulation |
| skill-flow-subflow | SUCCESS | 1.000 | 231.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:subflow |
| skill-flow-bindings-reconfigure-different-connection | SUCCESS | 1.000 | 507.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-bindings-no-duplicates | SUCCESS | 1.000 | 615.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-ipe-generate-schema | SUCCESS | 1.000 | 285.5s | claude-sonnet-4-6 | uipath-platform, integration, lifecycle:generate, shape:multi-node, connector, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-transform-filter | SUCCESS | 1.000 | 139.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-lowcode-agent | SUCCESS | 1.000 | 249.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-hitl-schema-design-simulated | SUCCESS | 0.895 | 306.2s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, simulation |
| skill-flow-inline-agent-robust | SUCCESS | 1.000 | 384.3s | claude-sonnet-4-6 | uipath-maestro-flow, mode:build, lifecycle:generate, node:inline-agent |
| skill-flow-remove-node | SUCCESS | 1.000 | 137.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node |
| skill-flow-decision | SUCCESS | 1.000 | 218.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:decision |
| skill-flow-ixp-scaffold-minimal | SUCCESS | 1.000 | 385.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-reading-list | SUCCESS | 1.000 | 258.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:transform |
| skill-flow-ipe-drive-to-slack | SUCCESS | 1.000 | 278.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, e2e, uipath-google-drive, uipath-salesforce-slack, ipe, mode:build |
| skill-flow-eval-inline-agent | SUCCESS | 1.000 | 621.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:inline-agent, feature:eval |
| skill-flow-ipe-jira-get-issue | SUCCESS | 1.000 | 519.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-coded-agent | MAX_TURNS_EXHAUSTED | 0.375 | 402.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource, path-to-ga |
| skill-flow-ixp-routing-negative/stripe-http | SUCCESS | 1.000 | 181.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/slack-summary | SUCCESS | 1.000 | 272.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/sf-update | SUCCESS | 1.000 | 303.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/http-webhook | SUCCESS | 1.000 | 210.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/gsheet-loop | SUCCESS | 1.000 | 395.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/queue-write | SUCCESS | 1.000 | 167.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/teams-decision | SUCCESS | 1.000 | 250.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/delay-email | SUCCESS | 1.000 | 300.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-integration-handle-routing | SUCCESS | 1.000 | 602.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:ixp, node:decision |
| skill-flow-paginated-reference-lookup | SUCCESS | 1.000 | 195.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, e2e, mode:build, lifecycle:generate, shape:multi-node, connector, uipath-salesforce-slack, feature:records |
| skill-flow-registry-discovery | SUCCESS | 1.000 | 88.5s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, lifecycle:discover, feature:registry |
| skill-flow-ipe-jira-lifecycle | FAILURE | 0.286 | 1267.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:loop, node:switch, node:decision, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-summarize | SUCCESS | 1.000 | 189.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, node:summarize, context-grounding, mode:build |
| skill-flow-scheduled-trigger | SUCCESS | 1.000 | 187.3s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:scheduled-trigger, feature:trigger |
| skill-flow-slack-weather-pipeline | MAX_TURNS_EXHAUSTED | 0.000 | 1175.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:decision, connector, feature:http |
| skill-flow-eval-no-auto-upload | SUCCESS | 1.000 | 79.8s | claude-sonnet-4-6 | uipath-maestro-flow, mode:operate, lifecycle:execute, feature:eval |
| skill-flow-ixp-routing/explicit | SUCCESS | 1.000 | 486.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/invoice-extraction | SUCCESS | 1.000 | 392.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/receipts | SUCCESS | 1.000 | 259.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/contracts | SUCCESS | 1.000 | 289.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/forms-classify | SUCCESS | 1.000 | 226.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-bellevue-weather | SUCCESS | 1.000 | 441.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:decision, feature:http, ipe |
| skill-flow-customer-escalation-simulated | MAX_TURNS_EXHAUSTED | 0.000 | 1022.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, node:decision, feature:trigger, connector, simulation |
| skill-flow-ipe-enum | FAILURE | 0.857 | 464.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle-generate, shape-multi-node, connector, uipath-google-gmail, ipe, mode:build |
| skill-flow-hitl-quality-schema-design | SUCCESS | 1.000 | 429.4s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-webhook-waitfor-parallel | SUCCESS | 1.000 | 295.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, connector, feature:trigger, feature:http, wait-for-event, uipath-http-webhook, ipe |
| skill-flow-solution-select-ask | FAILURE | 0.714 | 145.1s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, simulation |
| skill-flow-terminate | SUCCESS | 1.000 | 338.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:terminate |
| skill-flow-merge-parallel-sync | SUCCESS | 1.000 | 171.1s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:multi-node, node:merge |
| skill-flow-multi-city-weather | SUCCESS | 1.000 | 879.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:loop, feature:http |
| skill-flow-ixp-routing-listing/r01 | SUCCESS | 1.000 | 52.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r02 | SUCCESS | 1.000 | 55.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r03 | SUCCESS | 1.000 | 51.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r04 | SUCCESS | 1.000 | 58.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r05 | FAILURE | 0.500 | 38.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r06 | SUCCESS | 1.000 | 62.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r07 | SUCCESS | 1.000 | 96.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r08 | SUCCESS | 1.000 | 53.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r09 | SUCCESS | 1.000 | 55.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r10 | SUCCESS | 1.000 | 61.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-add-output | SUCCESS | 1.000 | 62.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node |
| skill-flow-hitl-quality-brownfield-insert | SUCCESS | 1.000 | 393.0s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-feet-inches | SUCCESS | 1.000 | 312.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:switch |
| skill-flow-bindings-multi-connector-independence | SUCCESS | 1.000 | 299.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, bindings, regression |
| skill-flow-non-catalog-http-fallback | SUCCESS | 1.000 | 182.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, connector, uipath-uipath-http, feature:http, ipe |
| skill-flow-update-node | SUCCESS | 1.000 | 63.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:decision |
| skill-flow-devcon-billing-dispute-resolution | FAILURE | 0.500 | 1535.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, node:ixp, connector, path-to-ga |
| skill-flow-cli-dice-roller-simulated | SUCCESS | 1.000 | 348.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, simulation |
| skill-flow-ipe-complex-array | SUCCESS | 1.000 | 487.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, ipe, mode:build |
| skill-flow-ipe-searchable-joins | SUCCESS | 1.000 | 323.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-salesforce, ipe, mode:build |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | ERROR | 0.000 | 1203.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:ixp, connector, feature:http |
| skill-flow-add-node | SUCCESS | 1.000 | 102.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:edit, shape:multi-node |
| skill-flow-delay | SUCCESS | 1.000 | 181.7s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:delay |
| skill-flow-generic-dynamic-node | FAILURE | 0.429 | 510.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node, connector, uipath-servicenow-servicenow, ipe |
| skill-flow-devcon-billing-invoice-lookup | SUCCESS | 1.000 | 809.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, connector, path-to-ga |
| skill-flow-ipe-multiselect | SUCCESS | 1.000 | 357.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-act-act365, ipe, mode:build |
| skill-flow-transform-group-by | SUCCESS | 1.000 | 206.9s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-file-attachment-debug | SUCCESS | 1.000 | 191.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node |
| skill-flow-ipe-required-groups | SUCCESS | 1.000 | 242.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-microsoft-teams, ipe, mode:build |
| skill-flow-eval-evaluator-type-choice | SUCCESS | 1.000 | 102.8s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:discover, feature:eval |
| skill-flow-ipe-jira-search-triage | FAILURE | 0.286 | 465.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:loop, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-eval-local-crud | SUCCESS | 1.000 | 158.9s | claude-sonnet-4-6 | uipath-maestro-flow, mode:build, lifecycle:generate, feature:eval |
| skill-flow-devcon-billing-discrepancy-detector | FAILURE | 0.375 | 704.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, connector, path-to-ga |
| skill-flow-batch-transform | SUCCESS | 1.000 | 163.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, node:batch-transform, context-grounding, mode:build |
| skill-flow-ipe-jira-create-issue | SUCCESS | 1.000 | 304.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-outlook-trigger-inbox | SUCCESS | 1.000 | 265.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, feature:trigger, connector, mode:build, ipe |
| skill-flow-hitl-smoke-completed-port | SUCCESS | 1.000 | 202.2s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, mode:build, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-hitl-smoke-node-placed | SUCCESS | 1.000 | 196.4s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, lifecycle:generate, shape:single-node, node:hitl |
| skill-flow-devcon-billing-resolution-writer | SUCCESS | 1.000 | 322.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, path-to-ga |
| skill-flow-ipe-enhanced-enum | SUCCESS | 1.000 | 417.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-automaticc-woocommerce, ipe, mode:build |
| skill-flow-bindings-idempotent-reconfigure | SUCCESS | 1.000 | 279.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-expense-approval-simulated | SUCCESS | 1.000 | 1073.2s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, e2e, mode:build, lifecycle:generate, devcon, simulation |
| skill-flow-rpa | SUCCESS | 1.000 | 206.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-loop-multiply | SUCCESS | 1.000 | 341.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:loop |
| skill-flow-init-validate | SUCCESS | 1.000 | 109.1s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, lifecycle:generate |
| skill-flow-slack-http-fallback | SUCCESS | 1.000 | 266.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:single-node, connector, uipath-salesforce-slack, feature:http, ipe |
| skill-flow-move-node | SUCCESS | 1.000 | 138.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:decision |
| skill-flow-ipe-path-params | SUCCESS | 1.000 | 308.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-dice-roller | SUCCESS | 1.000 | 195.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node |
| skill-flow-hitl-quality-result-downstream | SUCCESS | 1.000 | 204.5s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-ixp-e2e-project-selection/aviation | SUCCESS | 1.000 | 410.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-ixp-e2e-project-selection/birth-certificate | SUCCESS | 1.000 | 365.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-ipe-dtl-load-by-default-true | SUCCESS | 1.000 | 176.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-microsoft-azure, ipe, mode:build |
| skill-flow-slack-channel-description | SUCCESS | 1.000 | 238.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, connector |
| skill-flow-wiki-pageviews | TIMEOUT | 0.000 | 904.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:transform, feature:http |
| skill-flow-ixp-invoice-extraction-simulated | SUCCESS | 0.900 | 2317.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, node:ixp, connector, feature:http, simulation |
| skill-flow-openmeteo-weather | SUCCESS | 1.000 | 334.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node, connector, custom-codereval-openmeteoapis, ipe, custom-connector |
| skill-flow-outlook-waitfor-email | SUCCESS | 1.000 | 246.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, feature:trigger, connector, uipath-microsoft-outlook365, filter, ipe, wait-for-event |
| skill-flow-customer-escalation | SUCCESS | 1.000 | 702.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:decision, feature:trigger, connector |
| skill-flow-calculator | SUCCESS | 1.000 | 181.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node |
| skill-flow-trigger-with-filter | SUCCESS | 1.000 | 86.5s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:discover, connector-trigger, uipath-microsoft-outlook365, filter, ipe |
| skill-flow-e2e-devcon-expense-approval | SUCCESS | 1.000 | 327.3s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, e2e, devcon |
| skill-flow-ipe-dtl-load-by-default-false | SUCCESS | 1.000 | 361.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-automaticc-woocommerce, ipe, mode:build |
| skill-flow-transform-map | SUCCESS | 1.000 | 212.7s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-slack-channel-description-simulated | FAILURE | 0.583 | 529.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, connector, simulation |
| skill-flow-eval-simulation-crud | SUCCESS | 1.000 | 224.2s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, feature:eval |
| skill-flow-devcon-billing-dispute-analyst | FAILURE | 0.375 | 358.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, path-to-ga |
| skill-flow-api-workflow | SUCCESS | 1.000 | 253.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-hitl-smoke-multi-outcome-routing | SUCCESS | 1.000 | 300.6s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-interactive-customer-escalation-triage | SUCCESS | 1.000 | 291.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, feature:escalation, feature:conversational |
| skill-flow-hitl-quality-boolean-decision | SUCCESS | 1.000 | 280.1s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-group-to-subflow | SUCCESS | 1.000 | 663.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:subflow |
| skill-flow-switch | SUCCESS | 1.000 | 321.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:switch |
| skill-flow-ipe-query-params | SUCCESS | 1.000 | 143.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-google-tasks, ipe, mode:build |
| skill-flow-ipe-ceql-where | SUCCESS | 1.000 | 616.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, connector, ceql, filter, uipath-microsoft-azureactivedirectory, ipe, mode:build |
| skill-flow-ixp-scaffold-multinode | SUCCESS | 1.000 | 455.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, node:ixp |
| skill-flow-bellevue-weather-simulated | SUCCESS | 1.000 | 514.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, node:decision, feature:http, ipe, simulation |
| skill-flow-subflow | SUCCESS | 1.000 | 255.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:subflow |
| skill-flow-bindings-reconfigure-different-connection | SUCCESS | 1.000 | 236.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-bindings-no-duplicates | SUCCESS | 1.000 | 358.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-ipe-generate-schema | SUCCESS | 1.000 | 287.4s | claude-sonnet-4-6 | uipath-platform, integration, lifecycle:generate, shape:multi-node, connector, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-transform-filter | SUCCESS | 1.000 | 196.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-lowcode-agent | SUCCESS | 1.000 | 269.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-hitl-schema-design-simulated | SUCCESS | 1.000 | 394.1s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, simulation |
| skill-flow-inline-agent-robust | SUCCESS | 1.000 | 290.0s | claude-sonnet-4-6 | uipath-maestro-flow, mode:build, lifecycle:generate, node:inline-agent |
| skill-flow-remove-node | SUCCESS | 1.000 | 125.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node |
| skill-flow-decision | SUCCESS | 1.000 | 282.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:decision |
| skill-flow-ixp-scaffold-minimal | SUCCESS | 1.000 | 439.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-reading-list | SUCCESS | 1.000 | 250.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:transform |
| skill-flow-ipe-drive-to-slack | SUCCESS | 1.000 | 269.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, e2e, uipath-google-drive, uipath-salesforce-slack, ipe, mode:build |
| skill-flow-eval-inline-agent | SUCCESS | 1.000 | 427.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:inline-agent, feature:eval |
| skill-flow-ipe-jira-get-issue | SUCCESS | 1.000 | 302.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-coded-agent | MAX_TURNS_EXHAUSTED | 0.375 | 417.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource, path-to-ga |
| skill-flow-ixp-routing-negative/stripe-http | SUCCESS | 1.000 | 217.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/slack-summary | SUCCESS | 1.000 | 316.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/sf-update | SUCCESS | 1.000 | 157.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/http-webhook | SUCCESS | 1.000 | 206.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/gsheet-loop | SUCCESS | 1.000 | 223.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/queue-write | SUCCESS | 1.000 | 185.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/teams-decision | SUCCESS | 1.000 | 234.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/delay-email | SUCCESS | 1.000 | 175.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-integration-handle-routing | SUCCESS | 1.000 | 790.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:ixp, node:decision |
| skill-flow-paginated-reference-lookup | SUCCESS | 1.000 | 228.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, e2e, mode:build, lifecycle:generate, shape:multi-node, connector, uipath-salesforce-slack, feature:records |
| skill-flow-registry-discovery | SUCCESS | 1.000 | 88.4s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, lifecycle:discover, feature:registry |
| skill-flow-ipe-jira-lifecycle | FAILURE | 0.286 | 1486.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:loop, node:switch, node:decision, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-summarize | SUCCESS | 1.000 | 181.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, node:summarize, context-grounding, mode:build |
| skill-flow-scheduled-trigger | SUCCESS | 1.000 | 244.6s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:scheduled-trigger, feature:trigger |
| skill-flow-slack-weather-pipeline | ERROR | 0.000 | 1203.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:decision, connector, feature:http |
| skill-flow-eval-no-auto-upload | SUCCESS | 1.000 | 86.4s | claude-sonnet-4-6 | uipath-maestro-flow, mode:operate, lifecycle:execute, feature:eval |
| skill-flow-ixp-routing/explicit | SUCCESS | 1.000 | 208.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/invoice-extraction | SUCCESS | 1.000 | 322.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/receipts | SUCCESS | 1.000 | 733.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/contracts | SUCCESS | 1.000 | 362.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/forms-classify | SUCCESS | 1.000 | 217.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-bellevue-weather | SUCCESS | 1.000 | 398.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:decision, feature:http, ipe |
| skill-flow-customer-escalation-simulated | SUCCESS | 1.000 | 2013.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, node:decision, feature:trigger, connector, simulation |
| skill-flow-ipe-enum | SUCCESS | 1.000 | 408.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle-generate, shape-multi-node, connector, uipath-google-gmail, ipe, mode:build |
| skill-flow-hitl-quality-schema-design | SUCCESS | 1.000 | 310.7s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-webhook-waitfor-parallel | SUCCESS | 1.000 | 345.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, connector, feature:trigger, feature:http, wait-for-event, uipath-http-webhook, ipe |
| skill-flow-solution-select-ask | FAILURE | 0.714 | 128.1s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, simulation |
| skill-flow-terminate | SUCCESS | 1.000 | 336.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:terminate |
| skill-flow-merge-parallel-sync | SUCCESS | 1.000 | 167.3s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:multi-node, node:merge |
| skill-flow-multi-city-weather | TIMEOUT | 0.000 | 905.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:loop, feature:http |
| skill-flow-ixp-routing-listing/r01 | SUCCESS | 1.000 | 83.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r02 | SUCCESS | 1.000 | 79.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r03 | SUCCESS | 1.000 | 66.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r04 | SUCCESS | 1.000 | 65.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r05 | FAILURE | 0.500 | 54.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r06 | SUCCESS | 1.000 | 65.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r07 | SUCCESS | 1.000 | 124.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r08 | SUCCESS | 1.000 | 65.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r09 | SUCCESS | 1.000 | 48.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r10 | SUCCESS | 1.000 | 65.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-add-output | SUCCESS | 1.000 | 74.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node |
| skill-flow-hitl-quality-brownfield-insert | SUCCESS | 1.000 | 391.7s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-feet-inches | SUCCESS | 1.000 | 501.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:switch |
| skill-flow-bindings-multi-connector-independence | SUCCESS | 1.000 | 403.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, bindings, regression |
| skill-flow-non-catalog-http-fallback | SUCCESS | 1.000 | 260.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, connector, uipath-uipath-http, feature:http, ipe |
| skill-flow-update-node | SUCCESS | 1.000 | 85.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:decision |
| skill-flow-devcon-billing-dispute-resolution | FAILURE | 0.500 | 1421.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, node:ixp, connector, path-to-ga |
| skill-flow-cli-dice-roller-simulated | SUCCESS | 1.000 | 456.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, simulation |
| skill-flow-ipe-complex-array | SUCCESS | 1.000 | 599.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, ipe, mode:build |
| skill-flow-ipe-searchable-joins | SUCCESS | 1.000 | 342.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-salesforce, ipe, mode:build |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | FAILURE | 0.812 | 659.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:ixp, connector, feature:http |
| skill-flow-add-node | SUCCESS | 1.000 | 157.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:edit, shape:multi-node |
| skill-flow-delay | SUCCESS | 1.000 | 130.2s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:delay |
| skill-flow-generic-dynamic-node | FAILURE | 0.429 | 556.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node, connector, uipath-servicenow-servicenow, ipe |
| skill-flow-devcon-billing-invoice-lookup | SUCCESS | 1.000 | 570.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, connector, path-to-ga |
| skill-flow-ipe-multiselect | SUCCESS | 1.000 | 438.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-act-act365, ipe, mode:build |
| skill-flow-transform-group-by | SUCCESS | 1.000 | 212.9s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-file-attachment-debug | SUCCESS | 1.000 | 231.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node |
| skill-flow-ipe-required-groups | SUCCESS | 1.000 | 256.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-microsoft-teams, ipe, mode:build |
| skill-flow-eval-evaluator-type-choice | SUCCESS | 1.000 | 139.2s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:discover, feature:eval |
| skill-flow-ipe-jira-search-triage | FAILURE | 0.286 | 449.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:loop, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-eval-local-crud | SUCCESS | 1.000 | 111.6s | claude-sonnet-4-6 | uipath-maestro-flow, mode:build, lifecycle:generate, feature:eval |
| skill-flow-devcon-billing-discrepancy-detector | SUCCESS | 1.000 | 997.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, connector, path-to-ga |
| skill-flow-batch-transform | SUCCESS | 1.000 | 193.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, node:batch-transform, context-grounding, mode:build |
| skill-flow-ipe-jira-create-issue | SUCCESS | 1.000 | 316.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-outlook-trigger-inbox | SUCCESS | 1.000 | 352.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, feature:trigger, connector, mode:build, ipe |
| skill-flow-hitl-smoke-completed-port | SUCCESS | 1.000 | 229.9s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, mode:build, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-hitl-smoke-node-placed | SUCCESS | 1.000 | 272.2s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, lifecycle:generate, shape:single-node, node:hitl |
| skill-flow-devcon-billing-resolution-writer | SUCCESS | 1.000 | 360.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, path-to-ga |
| skill-flow-ipe-enhanced-enum | SUCCESS | 1.000 | 286.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-automaticc-woocommerce, ipe, mode:build |
| skill-flow-bindings-idempotent-reconfigure | SUCCESS | 1.000 | 628.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-expense-approval-simulated | SUCCESS | 1.000 | 450.6s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, e2e, mode:build, lifecycle:generate, devcon, simulation |
| skill-flow-rpa | SUCCESS | 1.000 | 284.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-loop-multiply | SUCCESS | 1.000 | 289.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:loop |
| skill-flow-init-validate | SUCCESS | 1.000 | 136.7s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, lifecycle:generate |
| skill-flow-slack-http-fallback | SUCCESS | 1.000 | 332.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:single-node, connector, uipath-salesforce-slack, feature:http, ipe |
| skill-flow-move-node | SUCCESS | 1.000 | 305.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:decision |
| skill-flow-ipe-path-params | SUCCESS | 1.000 | 335.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-dice-roller | SUCCESS | 1.000 | 290.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node |
| skill-flow-hitl-quality-result-downstream | SUCCESS | 1.000 | 146.6s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-ixp-e2e-project-selection/aviation | SUCCESS | 1.000 | 383.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-ixp-e2e-project-selection/birth-certificate | SUCCESS | 1.000 | 352.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-ipe-dtl-load-by-default-true | SUCCESS | 1.000 | 246.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-microsoft-azure, ipe, mode:build |
| skill-flow-slack-channel-description | SUCCESS | 1.000 | 232.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, connector |
| skill-flow-wiki-pageviews | SUCCESS | 1.000 | 731.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:transform, feature:http |
| skill-flow-ixp-invoice-extraction-simulated | SUCCESS | 0.900 | 1542.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, node:ixp, connector, feature:http, simulation |
| skill-flow-openmeteo-weather | SUCCESS | 1.000 | 248.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node, connector, custom-codereval-openmeteoapis, ipe, custom-connector |
| skill-flow-outlook-waitfor-email | SUCCESS | 1.000 | 267.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, feature:trigger, connector, uipath-microsoft-outlook365, filter, ipe, wait-for-event |
| skill-flow-customer-escalation | SUCCESS | 1.000 | 872.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:decision, feature:trigger, connector |
| skill-flow-calculator | SUCCESS | 1.000 | 199.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node |
| skill-flow-trigger-with-filter | SUCCESS | 1.000 | 152.8s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:discover, connector-trigger, uipath-microsoft-outlook365, filter, ipe |
| skill-flow-e2e-devcon-expense-approval | SUCCESS | 1.000 | 514.8s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, e2e, devcon |
| skill-flow-ipe-dtl-load-by-default-false | SUCCESS | 1.000 | 344.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-automaticc-woocommerce, ipe, mode:build |
| skill-flow-transform-map | SUCCESS | 1.000 | 249.2s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-slack-channel-description-simulated | SUCCESS | 1.000 | 1835.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, connector, simulation |
| skill-flow-eval-simulation-crud | SUCCESS | 1.000 | 157.9s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, feature:eval |
| skill-flow-devcon-billing-dispute-analyst | FAILURE | 0.375 | 502.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, path-to-ga |
| skill-flow-api-workflow | SUCCESS | 1.000 | 220.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-hitl-smoke-multi-outcome-routing | SUCCESS | 1.000 | 293.0s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-interactive-customer-escalation-triage | SUCCESS | 1.000 | 439.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, feature:escalation, feature:conversational |
| skill-flow-hitl-quality-boolean-decision | SUCCESS | 1.000 | 281.8s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-group-to-subflow | SUCCESS | 1.000 | 842.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:subflow |
| skill-flow-switch | SUCCESS | 1.000 | 268.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:switch |
| skill-flow-ipe-query-params | SUCCESS | 1.000 | 175.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-google-tasks, ipe, mode:build |
| skill-flow-ipe-ceql-where | SUCCESS | 1.000 | 432.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, connector, ceql, filter, uipath-microsoft-azureactivedirectory, ipe, mode:build |
| skill-flow-ixp-scaffold-multinode | SUCCESS | 1.000 | 374.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, node:ixp |
| skill-flow-bellevue-weather-simulated | SUCCESS | 1.000 | 757.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, node:decision, feature:http, ipe, simulation |
| skill-flow-subflow | SUCCESS | 1.000 | 243.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:subflow |
| skill-flow-bindings-reconfigure-different-connection | SUCCESS | 1.000 | 575.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-bindings-no-duplicates | SUCCESS | 1.000 | 491.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-ipe-generate-schema | SUCCESS | 1.000 | 223.9s | claude-sonnet-4-6 | uipath-platform, integration, lifecycle:generate, shape:multi-node, connector, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-transform-filter | SUCCESS | 1.000 | 174.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-lowcode-agent | SUCCESS | 1.000 | 259.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-hitl-schema-design-simulated | SUCCESS | 0.895 | 401.4s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, simulation |
| skill-flow-inline-agent-robust | SUCCESS | 1.000 | 378.1s | claude-sonnet-4-6 | uipath-maestro-flow, mode:build, lifecycle:generate, node:inline-agent |
| skill-flow-remove-node | SUCCESS | 1.000 | 108.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node |
| skill-flow-decision | SUCCESS | 1.000 | 290.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:decision |
| skill-flow-ixp-scaffold-minimal | SUCCESS | 1.000 | 463.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-reading-list | SUCCESS | 1.000 | 224.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:transform |
| skill-flow-ipe-drive-to-slack | SUCCESS | 1.000 | 344.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, e2e, uipath-google-drive, uipath-salesforce-slack, ipe, mode:build |
| skill-flow-eval-inline-agent | SUCCESS | 1.000 | 383.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:inline-agent, feature:eval |
| skill-flow-ipe-jira-get-issue | FAILURE | 0.286 | 406.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-coded-agent | MAX_TURNS_EXHAUSTED | 0.375 | 381.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource, path-to-ga |
| skill-flow-ixp-routing-negative/stripe-http | SUCCESS | 1.000 | 175.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/slack-summary | SUCCESS | 1.000 | 337.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/sf-update | SUCCESS | 1.000 | 182.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/http-webhook | SUCCESS | 1.000 | 277.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/gsheet-loop | SUCCESS | 1.000 | 176.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/queue-write | SUCCESS | 1.000 | 212.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/teams-decision | SUCCESS | 1.000 | 174.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/delay-email | SUCCESS | 1.000 | 262.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-integration-handle-routing | SUCCESS | 1.000 | 523.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:ixp, node:decision |
| skill-flow-paginated-reference-lookup | SUCCESS | 1.000 | 283.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, e2e, mode:build, lifecycle:generate, shape:multi-node, connector, uipath-salesforce-slack, feature:records |
| skill-flow-registry-discovery | SUCCESS | 1.000 | 74.4s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, lifecycle:discover, feature:registry |
| skill-flow-ipe-jira-lifecycle | SUCCESS | 1.000 | 599.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:loop, node:switch, node:decision, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-summarize | SUCCESS | 1.000 | 180.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, node:summarize, context-grounding, mode:build |
| skill-flow-scheduled-trigger | SUCCESS | 1.000 | 235.7s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:scheduled-trigger, feature:trigger |
| skill-flow-slack-weather-pipeline | ERROR | 0.000 | 1204.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:decision, connector, feature:http |
| skill-flow-eval-no-auto-upload | SUCCESS | 1.000 | 96.8s | claude-sonnet-4-6 | uipath-maestro-flow, mode:operate, lifecycle:execute, feature:eval |
| skill-flow-ixp-routing/explicit | SUCCESS | 1.000 | 196.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/invoice-extraction | SUCCESS | 1.000 | 470.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/receipts | SUCCESS | 1.000 | 295.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/contracts | SUCCESS | 1.000 | 268.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/forms-classify | SUCCESS | 1.000 | 199.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-bellevue-weather | SUCCESS | 1.000 | 534.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:decision, feature:http, ipe |
| skill-flow-customer-escalation-simulated | SUCCESS | 1.000 | 1290.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, node:decision, feature:trigger, connector, simulation |
| skill-flow-ipe-enum | SUCCESS | 1.000 | 398.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle-generate, shape-multi-node, connector, uipath-google-gmail, ipe, mode:build |
| skill-flow-hitl-quality-schema-design | SUCCESS | 1.000 | 267.3s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-webhook-waitfor-parallel | SUCCESS | 1.000 | 283.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, connector, feature:trigger, feature:http, wait-for-event, uipath-http-webhook, ipe |
| skill-flow-solution-select-ask | FAILURE | 0.714 | 143.3s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, simulation |
| skill-flow-terminate | SUCCESS | 1.000 | 552.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:terminate |
| skill-flow-merge-parallel-sync | SUCCESS | 1.000 | 161.2s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:multi-node, node:merge |
| skill-flow-multi-city-weather | FAILURE | 0.375 | 428.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:loop, feature:http |
| skill-flow-ixp-routing-listing/r01 | SUCCESS | 1.000 | 86.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r02 | SUCCESS | 1.000 | 60.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r03 | SUCCESS | 1.000 | 67.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r04 | SUCCESS | 1.000 | 63.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r05 | SUCCESS | 1.000 | 79.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r06 | SUCCESS | 1.000 | 71.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r07 | SUCCESS | 1.000 | 73.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r08 | SUCCESS | 1.000 | 60.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r09 | SUCCESS | 1.000 | 57.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r10 | SUCCESS | 1.000 | 58.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-add-output | SUCCESS | 1.000 | 59.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node |
| skill-flow-hitl-quality-brownfield-insert | SUCCESS | 1.000 | 328.3s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-feet-inches | SUCCESS | 1.000 | 393.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:switch |
| skill-flow-bindings-multi-connector-independence | SUCCESS | 1.000 | 540.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, bindings, regression |
| skill-flow-non-catalog-http-fallback | SUCCESS | 1.000 | 211.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, connector, uipath-uipath-http, feature:http, ipe |
| skill-flow-update-node | SUCCESS | 1.000 | 66.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:decision |
| skill-flow-devcon-billing-dispute-resolution | FAILURE | 0.500 | 931.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, node:ixp, connector, path-to-ga |
| skill-flow-cli-dice-roller-simulated | SUCCESS | 1.000 | 405.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, simulation |
| skill-flow-ipe-complex-array | SUCCESS | 1.000 | 565.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, ipe, mode:build |
| skill-flow-ipe-searchable-joins | SUCCESS | 1.000 | 490.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-salesforce, ipe, mode:build |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | SUCCESS | 1.000 | 875.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:ixp, connector, feature:http |
| skill-flow-add-node | SUCCESS | 1.000 | 129.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:edit, shape:multi-node |
| skill-flow-delay | SUCCESS | 1.000 | 187.7s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:delay |
| skill-flow-generic-dynamic-node | FAILURE | 0.429 | 515.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node, connector, uipath-servicenow-servicenow, ipe |
| skill-flow-devcon-billing-invoice-lookup | SUCCESS | 1.000 | 875.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, connector, path-to-ga |
| skill-flow-ipe-multiselect | SUCCESS | 1.000 | 339.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-act-act365, ipe, mode:build |
| skill-flow-transform-group-by | SUCCESS | 1.000 | 240.6s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-file-attachment-debug | SUCCESS | 1.000 | 227.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node |
| skill-flow-ipe-required-groups | SUCCESS | 1.000 | 268.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-microsoft-teams, ipe, mode:build |
| skill-flow-eval-evaluator-type-choice | SUCCESS | 1.000 | 103.0s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:discover, feature:eval |
| skill-flow-ipe-jira-search-triage | FAILURE | 0.286 | 431.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:loop, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-eval-local-crud | SUCCESS | 1.000 | 109.9s | claude-sonnet-4-6 | uipath-maestro-flow, mode:build, lifecycle:generate, feature:eval |
| skill-flow-devcon-billing-discrepancy-detector | SUCCESS | 1.000 | 1125.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, connector, path-to-ga |
| skill-flow-batch-transform | SUCCESS | 1.000 | 176.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, node:batch-transform, context-grounding, mode:build |
| skill-flow-ipe-jira-create-issue | SUCCESS | 1.000 | 444.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-outlook-trigger-inbox | SUCCESS | 1.000 | 304.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, feature:trigger, connector, mode:build, ipe |
| skill-flow-hitl-smoke-completed-port | SUCCESS | 1.000 | 206.8s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, mode:build, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-hitl-smoke-node-placed | SUCCESS | 1.000 | 177.2s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, lifecycle:generate, shape:single-node, node:hitl |
| skill-flow-devcon-billing-resolution-writer | SUCCESS | 1.000 | 317.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, path-to-ga |
| skill-flow-ipe-enhanced-enum | SUCCESS | 1.000 | 432.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-automaticc-woocommerce, ipe, mode:build |
| skill-flow-bindings-idempotent-reconfigure | SUCCESS | 1.000 | 430.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-expense-approval-simulated | SUCCESS | 1.000 | 830.8s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, e2e, mode:build, lifecycle:generate, devcon, simulation |
| skill-flow-rpa | SUCCESS | 1.000 | 244.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-loop-multiply | SUCCESS | 1.000 | 303.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:loop |
| skill-flow-init-validate | SUCCESS | 1.000 | 125.5s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, lifecycle:generate |
| skill-flow-slack-http-fallback | SUCCESS | 1.000 | 285.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:single-node, connector, uipath-salesforce-slack, feature:http, ipe |
| skill-flow-move-node | SUCCESS | 1.000 | 256.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:decision |
| skill-flow-ipe-path-params | SUCCESS | 1.000 | 226.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-dice-roller | SUCCESS | 1.000 | 228.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node |
| skill-flow-hitl-quality-result-downstream | SUCCESS | 1.000 | 265.6s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-ixp-e2e-project-selection/aviation | SUCCESS | 1.000 | 274.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-ixp-e2e-project-selection/birth-certificate | SUCCESS | 1.000 | 351.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-ipe-dtl-load-by-default-true | SUCCESS | 1.000 | 173.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-microsoft-azure, ipe, mode:build |
| skill-flow-slack-channel-description | SUCCESS | 1.000 | 264.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, connector |
| skill-flow-wiki-pageviews | SUCCESS | 1.000 | 834.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:transform, feature:http |
| skill-flow-ixp-invoice-extraction-simulated | SUCCESS | 0.900 | 1652.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, node:ixp, connector, feature:http, simulation |
| skill-flow-openmeteo-weather | SUCCESS | 1.000 | 257.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node, connector, custom-codereval-openmeteoapis, ipe, custom-connector |
| skill-flow-outlook-waitfor-email | SUCCESS | 1.000 | 242.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, feature:trigger, connector, uipath-microsoft-outlook365, filter, ipe, wait-for-event |
| skill-flow-customer-escalation | SUCCESS | 1.000 | 851.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:decision, feature:trigger, connector |
| skill-flow-calculator | SUCCESS | 1.000 | 210.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node |
| skill-flow-trigger-with-filter | FAILURE | 0.000 | 325.3s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:discover, connector-trigger, uipath-microsoft-outlook365, filter, ipe |
| skill-flow-e2e-devcon-expense-approval | SUCCESS | 1.000 | 271.2s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, e2e, devcon |
| skill-flow-ipe-dtl-load-by-default-false | SUCCESS | 1.000 | 254.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-automaticc-woocommerce, ipe, mode:build |
| skill-flow-transform-map | SUCCESS | 1.000 | 211.5s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-slack-channel-description-simulated | SUCCESS | 1.000 | 407.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, connector, simulation |
| skill-flow-eval-simulation-crud | SUCCESS | 1.000 | 180.4s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, feature:eval |
| skill-flow-devcon-billing-dispute-analyst | FAILURE | 0.375 | 424.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, path-to-ga |
| skill-flow-api-workflow | SUCCESS | 1.000 | 350.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-hitl-smoke-multi-outcome-routing | SUCCESS | 1.000 | 263.8s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-interactive-customer-escalation-triage | SUCCESS | 1.000 | 270.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, feature:escalation, feature:conversational |
| skill-flow-hitl-quality-boolean-decision | SUCCESS | 1.000 | 277.9s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-group-to-subflow | TIMEOUT | 0.000 | 903.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:subflow |
| skill-flow-switch | SUCCESS | 1.000 | 307.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:switch |
| skill-flow-ipe-query-params | SUCCESS | 1.000 | 158.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-google-tasks, ipe, mode:build |
| skill-flow-ipe-ceql-where | SUCCESS | 1.000 | 423.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, connector, ceql, filter, uipath-microsoft-azureactivedirectory, ipe, mode:build |
| skill-flow-ixp-scaffold-multinode | SUCCESS | 1.000 | 528.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, node:ixp |
| skill-flow-bellevue-weather-simulated | SUCCESS | 0.889 | 1611.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, node:decision, feature:http, ipe, simulation |
| skill-flow-subflow | SUCCESS | 1.000 | 207.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:subflow |
| skill-flow-bindings-reconfigure-different-connection | SUCCESS | 1.000 | 260.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-bindings-no-duplicates | SUCCESS | 1.000 | 474.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-ipe-generate-schema | SUCCESS | 1.000 | 255.4s | claude-sonnet-4-6 | uipath-platform, integration, lifecycle:generate, shape:multi-node, connector, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-transform-filter | SUCCESS | 1.000 | 167.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-lowcode-agent | SUCCESS | 1.000 | 298.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-hitl-schema-design-simulated | SUCCESS | 0.895 | 394.6s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, simulation |
| skill-flow-inline-agent-robust | SUCCESS | 1.000 | 299.7s | claude-sonnet-4-6 | uipath-maestro-flow, mode:build, lifecycle:generate, node:inline-agent |
| skill-flow-remove-node | SUCCESS | 1.000 | 109.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node |
| skill-flow-decision | SUCCESS | 1.000 | 229.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:decision |
| skill-flow-ixp-scaffold-minimal | SUCCESS | 1.000 | 493.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-reading-list | SUCCESS | 1.000 | 308.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:transform |
| skill-flow-ipe-drive-to-slack | SUCCESS | 1.000 | 243.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, e2e, uipath-google-drive, uipath-salesforce-slack, ipe, mode:build |
| skill-flow-eval-inline-agent | SUCCESS | 1.000 | 507.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:inline-agent, feature:eval |
| skill-flow-ipe-jira-get-issue | SUCCESS | 1.000 | 285.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-coded-agent | MAX_TURNS_EXHAUSTED | 0.375 | 295.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource, path-to-ga |
| skill-flow-ixp-routing-negative/stripe-http | SUCCESS | 1.000 | 166.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/slack-summary | SUCCESS | 1.000 | 334.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/sf-update | SUCCESS | 1.000 | 278.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/http-webhook | SUCCESS | 1.000 | 227.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/gsheet-loop | SUCCESS | 1.000 | 331.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/queue-write | SUCCESS | 1.000 | 201.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/teams-decision | SUCCESS | 1.000 | 173.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/delay-email | SUCCESS | 1.000 | 275.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-integration-handle-routing | SUCCESS | 1.000 | 442.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:ixp, node:decision |
| skill-flow-paginated-reference-lookup | SUCCESS | 1.000 | 198.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, e2e, mode:build, lifecycle:generate, shape:multi-node, connector, uipath-salesforce-slack, feature:records |
| skill-flow-registry-discovery | SUCCESS | 1.000 | 75.2s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, lifecycle:discover, feature:registry |
| skill-flow-ipe-jira-lifecycle | ERROR | 0.000 | 904.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:loop, node:switch, node:decision, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-summarize | SUCCESS | 1.000 | 167.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, node:summarize, context-grounding, mode:build |
| skill-flow-scheduled-trigger | SUCCESS | 1.000 | 233.7s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:scheduled-trigger, feature:trigger |
| skill-flow-slack-weather-pipeline | MAX_TURNS_EXHAUSTED | 0.375 | 786.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:decision, connector, feature:http |
| skill-flow-eval-no-auto-upload | SUCCESS | 1.000 | 83.5s | claude-sonnet-4-6 | uipath-maestro-flow, mode:operate, lifecycle:execute, feature:eval |
| skill-flow-ixp-routing/explicit | SUCCESS | 1.000 | 319.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/invoice-extraction | SUCCESS | 1.000 | 282.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/receipts | SUCCESS | 1.000 | 206.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/contracts | SUCCESS | 1.000 | 299.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/forms-classify | SUCCESS | 1.000 | 204.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-bellevue-weather | SUCCESS | 1.000 | 407.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:decision, feature:http, ipe |
| skill-flow-customer-escalation-simulated | FAILURE | 0.000 | 1988.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, node:decision, feature:trigger, connector, simulation |
| skill-flow-ipe-enum | SUCCESS | 1.000 | 461.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle-generate, shape-multi-node, connector, uipath-google-gmail, ipe, mode:build |
| skill-flow-hitl-quality-schema-design | SUCCESS | 1.000 | 360.5s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-webhook-waitfor-parallel | SUCCESS | 1.000 | 272.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, connector, feature:trigger, feature:http, wait-for-event, uipath-http-webhook, ipe |
| skill-flow-solution-select-ask | FAILURE | 0.714 | 139.7s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, simulation |
| skill-flow-terminate | SUCCESS | 1.000 | 387.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:terminate |
| skill-flow-merge-parallel-sync | SUCCESS | 1.000 | 148.7s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:multi-node, node:merge |
| skill-flow-multi-city-weather | SUCCESS | 1.000 | 743.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:loop, feature:http |
| skill-flow-ixp-routing-listing/r01 | FAILURE | 0.500 | 29.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r02 | SUCCESS | 1.000 | 59.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r03 | SUCCESS | 1.000 | 57.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r04 | SUCCESS | 1.000 | 54.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r05 | FAILURE | 0.500 | 38.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r06 | SUCCESS | 1.000 | 48.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r07 | SUCCESS | 1.000 | 73.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r08 | SUCCESS | 1.000 | 58.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r09 | SUCCESS | 1.000 | 54.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r10 | SUCCESS | 1.000 | 58.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-add-output | SUCCESS | 1.000 | 96.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node |
| skill-flow-hitl-quality-brownfield-insert | SUCCESS | 1.000 | 446.7s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-feet-inches | SUCCESS | 1.000 | 485.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:switch |
| skill-flow-bindings-multi-connector-independence | SUCCESS | 1.000 | 467.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, bindings, regression |
| skill-flow-non-catalog-http-fallback | SUCCESS | 1.000 | 239.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, connector, uipath-uipath-http, feature:http, ipe |
| skill-flow-update-node | SUCCESS | 1.000 | 60.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:decision |
| skill-flow-devcon-billing-dispute-resolution | FAILURE | 0.500 | 1808.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, node:ixp, connector, path-to-ga |
| skill-flow-cli-dice-roller-simulated | SUCCESS | 1.000 | 799.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, simulation |
| skill-flow-ipe-complex-array | SUCCESS | 1.000 | 648.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, ipe, mode:build |
| skill-flow-ipe-searchable-joins | SUCCESS | 1.000 | 345.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-salesforce, ipe, mode:build |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | ERROR | 0.000 | 1203.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:ixp, connector, feature:http |
| skill-flow-add-node | SUCCESS | 1.000 | 139.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:edit, shape:multi-node |
| skill-flow-delay | SUCCESS | 1.000 | 185.5s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:delay |
| skill-flow-generic-dynamic-node | FAILURE | 0.429 | 470.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node, connector, uipath-servicenow-servicenow, ipe |
| skill-flow-devcon-billing-invoice-lookup | FAILURE | 0.375 | 834.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, connector, path-to-ga |
| skill-flow-ipe-multiselect | SUCCESS | 1.000 | 456.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-act-act365, ipe, mode:build |
| skill-flow-transform-group-by | SUCCESS | 1.000 | 157.5s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-file-attachment-debug | SUCCESS | 1.000 | 233.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node |
| skill-flow-ipe-required-groups | SUCCESS | 1.000 | 214.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-microsoft-teams, ipe, mode:build |
| skill-flow-eval-evaluator-type-choice | SUCCESS | 1.000 | 171.0s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:discover, feature:eval |
| skill-flow-ipe-jira-search-triage | FAILURE | 0.286 | 393.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:loop, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-eval-local-crud | SUCCESS | 1.000 | 91.3s | claude-sonnet-4-6 | uipath-maestro-flow, mode:build, lifecycle:generate, feature:eval |
| skill-flow-devcon-billing-discrepancy-detector | SUCCESS | 1.000 | 1248.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, connector, path-to-ga |
| skill-flow-batch-transform | SUCCESS | 1.000 | 192.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, node:batch-transform, context-grounding, mode:build |
| skill-flow-ipe-jira-create-issue | SUCCESS | 1.000 | 294.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-outlook-trigger-inbox | SUCCESS | 1.000 | 358.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, feature:trigger, connector, mode:build, ipe |
| skill-flow-hitl-smoke-completed-port | SUCCESS | 1.000 | 248.2s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, mode:build, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-hitl-smoke-node-placed | SUCCESS | 1.000 | 157.7s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, lifecycle:generate, shape:single-node, node:hitl |
| skill-flow-devcon-billing-resolution-writer | SUCCESS | 1.000 | 317.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, path-to-ga |
| skill-flow-ipe-enhanced-enum | SUCCESS | 1.000 | 458.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-automaticc-woocommerce, ipe, mode:build |
| skill-flow-bindings-idempotent-reconfigure | SUCCESS | 1.000 | 274.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-expense-approval-simulated | SUCCESS | 1.000 | 934.4s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, e2e, mode:build, lifecycle:generate, devcon, simulation |
| skill-flow-rpa | SUCCESS | 1.000 | 260.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-loop-multiply | SUCCESS | 1.000 | 246.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:loop |
| skill-flow-init-validate | SUCCESS | 1.000 | 112.5s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, lifecycle:generate |
| skill-flow-slack-http-fallback | SUCCESS | 1.000 | 271.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:single-node, connector, uipath-salesforce-slack, feature:http, ipe |
| skill-flow-move-node | SUCCESS | 1.000 | 164.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:decision |
| skill-flow-ipe-path-params | SUCCESS | 1.000 | 277.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-dice-roller | SUCCESS | 1.000 | 150.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node |
| skill-flow-hitl-quality-result-downstream | SUCCESS | 1.000 | 189.8s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-ixp-e2e-project-selection/aviation | SUCCESS | 1.000 | 622.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-ixp-e2e-project-selection/birth-certificate | SUCCESS | 1.000 | 198.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-ipe-dtl-load-by-default-true | SUCCESS | 1.000 | 293.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-microsoft-azure, ipe, mode:build |
| skill-flow-slack-channel-description | SUCCESS | 1.000 | 241.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, connector |
| skill-flow-wiki-pageviews | SUCCESS | 1.000 | 756.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:transform, feature:http |
| skill-flow-ixp-invoice-extraction-simulated | SUCCESS | 0.900 | 1814.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, node:ixp, connector, feature:http, simulation |
| skill-flow-openmeteo-weather | SUCCESS | 1.000 | 239.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node, connector, custom-codereval-openmeteoapis, ipe, custom-connector |
| skill-flow-outlook-waitfor-email | SUCCESS | 1.000 | 299.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, feature:trigger, connector, uipath-microsoft-outlook365, filter, ipe, wait-for-event |
| skill-flow-customer-escalation | SUCCESS | 1.000 | 590.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:decision, feature:trigger, connector |
| skill-flow-calculator | SUCCESS | 1.000 | 168.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node |
| skill-flow-trigger-with-filter | SUCCESS | 1.000 | 318.2s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:discover, connector-trigger, uipath-microsoft-outlook365, filter, ipe |
| skill-flow-e2e-devcon-expense-approval | SUCCESS | 1.000 | 316.6s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, e2e, devcon |
| skill-flow-ipe-dtl-load-by-default-false | SUCCESS | 1.000 | 349.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-automaticc-woocommerce, ipe, mode:build |
| skill-flow-transform-map | SUCCESS | 1.000 | 270.4s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-slack-channel-description-simulated | SUCCESS | 1.000 | 335.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, connector, simulation |
| skill-flow-eval-simulation-crud | SUCCESS | 1.000 | 152.0s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, feature:eval |
| skill-flow-devcon-billing-dispute-analyst | FAILURE | 0.375 | 432.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, path-to-ga |
| skill-flow-api-workflow | FAILURE | 0.000 | 130.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-hitl-smoke-multi-outcome-routing | SUCCESS | 1.000 | 227.1s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-interactive-customer-escalation-triage | SUCCESS | 1.000 | 356.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, feature:escalation, feature:conversational |
| skill-flow-hitl-quality-boolean-decision | SUCCESS | 1.000 | 448.4s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-group-to-subflow | SUCCESS | 1.000 | 816.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:subflow |
| skill-flow-switch | SUCCESS | 1.000 | 212.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:switch |
| skill-flow-ipe-query-params | SUCCESS | 1.000 | 153.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-google-tasks, ipe, mode:build |
| skill-flow-ipe-ceql-where | SUCCESS | 1.000 | 416.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, connector, ceql, filter, uipath-microsoft-azureactivedirectory, ipe, mode:build |
| skill-flow-ixp-scaffold-multinode | SUCCESS | 1.000 | 562.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, node:ixp |
| skill-flow-bellevue-weather-simulated | SUCCESS | 0.889 | 1729.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, node:decision, feature:http, ipe, simulation |
| skill-flow-subflow | SUCCESS | 1.000 | 312.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:subflow |
| skill-flow-bindings-reconfigure-different-connection | SUCCESS | 1.000 | 286.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-bindings-no-duplicates | SUCCESS | 1.000 | 632.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-ipe-generate-schema | SUCCESS | 1.000 | 248.7s | claude-sonnet-4-6 | uipath-platform, integration, lifecycle:generate, shape:multi-node, connector, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-transform-filter | SUCCESS | 1.000 | 225.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-lowcode-agent | SUCCESS | 1.000 | 337.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-hitl-schema-design-simulated | SUCCESS | 1.000 | 854.7s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, simulation |

## Run-time Notes

> **WARNING:** [skill-flow-remove-node] expected_turns exceeded: 21/14 (cumulative SDK turns)
> **WARNING:** [skill-flow-coded-agent] max_turns exhausted
> **WARNING:** [skill-flow-coded-agent] expected_turns exceeded: 42/35 (cumulative SDK turns)
> **WARNING:** [skill-flow-ixp-routing-negative/sf-update] max_turns exhausted
> **WARNING:** [skill-flow-ixp-routing-negative/http-webhook] max_turns exhausted
> **WARNING:** [skill-flow-ixp-integration-handle-routing] expected_turns exceeded: 29/26 (cumulative SDK turns)
> **WARNING:** [skill-flow-registry-discovery] expected_turns exceeded: 14/9 (cumulative SDK turns)
> **WARNING:** [skill-flow-customer-escalation-simulated] max_turns exhausted
> **WARNING:** [skill-flow-init-validate] expected_turns exceeded: 16/9 (cumulative SDK turns)
> **WARNING:** [skill-flow-move-node] expected_turns exceeded: 13/11 (cumulative SDK turns)
> **WARNING:** [skill-flow-calculator] expected_turns exceeded: 20/18 (cumulative SDK turns)
> **WARNING:** [skill-flow-trigger-with-filter] expected_turns exceeded: 9/7 (cumulative SDK turns)
> **WARNING:** [skill-flow-eval-simulation-crud] expected_turns exceeded: 42/20 (cumulative SDK turns)
> **WARNING:** [skill-flow-remove-node] expected_turns exceeded: 19/14 (cumulative SDK turns)
> **WARNING:** [skill-flow-coded-agent] max_turns exhausted
> **WARNING:** [skill-flow-coded-agent] expected_turns exceeded: 64/35 (cumulative SDK turns)
> **WARNING:** [skill-flow-ixp-routing-negative/sf-update] max_turns exhausted
> **WARNING:** [skill-flow-ixp-routing-negative/queue-write] max_turns exhausted
> **WARNING:** [skill-flow-ixp-integration-handle-routing] expected_turns exceeded: 33/26 (cumulative SDK turns)
> **WARNING:** [skill-flow-registry-discovery] expected_turns exceeded: 16/9 (cumulative SDK turns)
> **WARNING:** [skill-flow-slack-weather-pipeline] max_turns exhausted
> **WARNING:** [skill-flow-slack-weather-pipeline] expected_turns exceeded: 58/51 (cumulative SDK turns)
> **WARNING:** [skill-flow-customer-escalation-simulated] max_turns exhausted
> **WARNING:** [skill-flow-hitl-quality-schema-design] expected_turns exceeded: 47/29 (cumulative SDK turns)
> **WARNING:** [skill-flow-outlook-trigger-inbox] max_turns exhausted
> **WARNING:** [skill-flow-init-validate] expected_turns exceeded: 15/9 (cumulative SDK turns)
> **WARNING:** [skill-flow-slack-http-fallback] expected_turns exceeded: 33/32 (cumulative SDK turns)
> **WARNING:** [skill-flow-ipe-dtl-load-by-default-false] expected_turns exceeded: 54/51 (cumulative SDK turns)
> **WARNING:** [skill-flow-eval-simulation-crud] expected_turns exceeded: 44/20 (cumulative SDK turns)
> **WARNING:** [skill-flow-group-to-subflow] expected_turns exceeded: 20/13 (cumulative SDK turns)
> **WARNING:** [skill-flow-remove-node] expected_turns exceeded: 18/14 (cumulative SDK turns)
> **WARNING:** [skill-flow-coded-agent] max_turns exhausted
> **WARNING:** [skill-flow-coded-agent] expected_turns exceeded: 45/35 (cumulative SDK turns)
> **WARNING:** [skill-flow-ixp-routing-negative/http-webhook] max_turns exhausted
> **WARNING:** [skill-flow-ixp-integration-handle-routing] expected_turns exceeded: 35/26 (cumulative SDK turns)
> **WARNING:** [skill-flow-registry-discovery] expected_turns exceeded: 16/9 (cumulative SDK turns)
> **WARNING:** [skill-flow-hitl-quality-brownfield-insert] expected_turns exceeded: 54/34 (cumulative SDK turns)
> **WARNING:** [skill-flow-feet-inches] expected_turns exceeded: 26/23 (cumulative SDK turns)
> **WARNING:** [skill-flow-ipe-complex-array] expected_turns exceeded: 41/38 (cumulative SDK turns)
> **WARNING:** [skill-flow-eval-evaluator-type-choice] expected_turns exceeded: 32/15 (cumulative SDK turns)
> **WARNING:** [skill-flow-hitl-smoke-node-placed] expected_turns exceeded: 24/21 (cumulative SDK turns)
> **WARNING:** [skill-flow-init-validate] expected_turns exceeded: 14/9 (cumulative SDK turns)
> **WARNING:** [skill-flow-trigger-with-filter] expected_turns exceeded: 8/7 (cumulative SDK turns)
> **WARNING:** [skill-flow-ipe-dtl-load-by-default-false] expected_turns exceeded: 55/51 (cumulative SDK turns)
> **WARNING:** [skill-flow-eval-simulation-crud] expected_turns exceeded: 43/20 (cumulative SDK turns)
> **WARNING:** [skill-flow-ipe-ceql-where] expected_turns exceeded: 36/34 (cumulative SDK turns)
> **WARNING:** [skill-flow-remove-node] expected_turns exceeded: 19/14 (cumulative SDK turns)
> **WARNING:** [skill-flow-coded-agent] max_turns exhausted
> **WARNING:** [skill-flow-coded-agent] expected_turns exceeded: 47/35 (cumulative SDK turns)
> **WARNING:** [skill-flow-ixp-routing-negative/slack-summary] max_turns exhausted
> **WARNING:** [skill-flow-ixp-routing-negative/http-webhook] max_turns exhausted
> **WARNING:** [skill-flow-ixp-routing-negative/queue-write] max_turns exhausted
> **WARNING:** [skill-flow-paginated-reference-lookup] expected_turns exceeded: 34/30 (cumulative SDK turns)
> **WARNING:** [skill-flow-hitl-quality-schema-design] expected_turns exceeded: 34/29 (cumulative SDK turns)
> **WARNING:** [skill-flow-hitl-smoke-node-placed] expected_turns exceeded: 22/21 (cumulative SDK turns)
> **WARNING:** [skill-flow-rpa] expected_turns exceeded: 29/26 (cumulative SDK turns)
> **WARNING:** [skill-flow-init-validate] expected_turns exceeded: 16/9 (cumulative SDK turns)
> **WARNING:** [skill-flow-trigger-with-filter] expected_turns exceeded: 36/7 (cumulative SDK turns)
> **WARNING:** [skill-flow-eval-simulation-crud] expected_turns exceeded: 31/20 (cumulative SDK turns)
> **WARNING:** [skill-flow-api-workflow] max_turns exhausted
> **WARNING:** [skill-flow-api-workflow] expected_turns exceeded: 43/25 (cumulative SDK turns)
> **WARNING:** [skill-flow-ipe-ceql-where] expected_turns exceeded: 35/34 (cumulative SDK turns)
> **WARNING:** [skill-flow-remove-node] expected_turns exceeded: 17/14 (cumulative SDK turns)
> **WARNING:** [skill-flow-coded-agent] max_turns exhausted
> **WARNING:** [skill-flow-coded-agent] expected_turns exceeded: 49/35 (cumulative SDK turns)
> **WARNING:** [skill-flow-ixp-routing-negative/http-webhook] max_turns exhausted
> **WARNING:** [skill-flow-ixp-routing-negative/queue-write] max_turns exhausted
> **WARNING:** [skill-flow-ixp-integration-handle-routing] expected_turns exceeded: 28/26 (cumulative SDK turns)
> **WARNING:** [skill-flow-slack-weather-pipeline] max_turns exhausted
> **WARNING:** [skill-flow-slack-weather-pipeline] expected_turns exceeded: 57/51 (cumulative SDK turns)
> **WARNING:** [skill-flow-add-output] expected_turns exceeded: 13/11 (cumulative SDK turns)
> **WARNING:** [skill-flow-non-catalog-http-fallback] expected_turns exceeded: 33/32 (cumulative SDK turns)
> **WARNING:** [skill-flow-ipe-multiselect] expected_turns exceeded: 38/37 (cumulative SDK turns)
> **WARNING:** [skill-flow-eval-evaluator-type-choice] expected_turns exceeded: 23/15 (cumulative SDK turns)
> **WARNING:** [skill-flow-outlook-trigger-inbox] max_turns exhausted
> **WARNING:** [skill-flow-init-validate] expected_turns exceeded: 16/9 (cumulative SDK turns)
> **WARNING:** [skill-flow-move-node] expected_turns exceeded: 12/11 (cumulative SDK turns)
> **WARNING:** [skill-flow-trigger-with-filter] expected_turns exceeded: 28/7 (cumulative SDK turns)
> **WARNING:** [skill-flow-group-to-subflow] expected_turns exceeded: 17/13 (cumulative SDK turns)
> **WARNING:** [skill-flow-ipe-ceql-where] expected_turns exceeded: 37/34 (cumulative SDK turns)
> **WARNING:** [skill-flow-bindings-no-duplicates] max_turns exhausted
> **WARNING:** [skill-flow-bindings-no-duplicates] expected_turns exceeded: 60/51 (cumulative SDK turns)


## Generation Metrics

| Task ID | Total Latency | Turns | Asst Turns | Avg Turn Latency |
|---------|---------------|-------|------------|------------------|
| skill-flow-inline-agent-robust | 307.0s | 1 | 49 | 297.0s |
| skill-flow-remove-node | 161.4s | 1 | 34 | 114.6s |
| skill-flow-decision | 212.8s | 1 | 27 | 170.2s |
| skill-flow-ixp-scaffold-minimal | 469.4s | 1 | 35 | 453.4s |
| skill-flow-reading-list | 243.4s | 1 | 27 | 208.1s |
| skill-flow-ipe-drive-to-slack | 390.5s | 1 | 59 | 380.2s |
| skill-flow-eval-inline-agent | 556.1s | 1 | 43 | 546.6s |
| skill-flow-ipe-jira-get-issue | 445.4s | 1 | 60 | 371.6s |
| skill-flow-coded-agent | 293.6s | 1 | 59 | 273.1s |
| skill-flow-ixp-routing-negative/stripe-http | 212.7s | 1 | 33 | 202.3s |
| skill-flow-ixp-routing-negative/slack-summary | 297.5s | 1 | 28 | 288.1s |
| skill-flow-ixp-routing-negative/sf-update | 332.9s | 1 | 41 | 322.6s |
| skill-flow-ixp-routing-negative/http-webhook | 279.6s | 1 | 41 | 269.8s |
| skill-flow-ixp-routing-negative/gsheet-loop | 343.8s | 1 | 40 | 334.9s |
| skill-flow-ixp-routing-negative/queue-write | 210.6s | 1 | 39 | 200.6s |
| skill-flow-ixp-routing-negative/teams-decision | 253.1s | 1 | 35 | 243.1s |
| skill-flow-ixp-routing-negative/delay-email | 325.8s | 1 | 32 | 316.0s |
| skill-flow-ixp-integration-handle-routing | 427.2s | 1 | 46 | 409.7s |
| skill-flow-paginated-reference-lookup | 259.5s | 1 | 43 | 249.4s |
| skill-flow-registry-discovery | 131.8s | 1 | 20 | 121.7s |
| skill-flow-ipe-jira-lifecycle | 707.3s | 1 | 47 | 647.6s |
| skill-flow-summarize | 189.8s | 1 | 22 | 176.1s |
| skill-flow-scheduled-trigger | 263.6s | 1 | 29 | 247.2s |
| skill-flow-slack-weather-pipeline | 1211.6s | 1 | 80 | 1200.0s |
| skill-flow-eval-no-auto-upload | 119.0s | 1 | 24 | 108.8s |
| skill-flow-ixp-routing/explicit | 331.1s | 1 | 36 | 321.9s |
| skill-flow-ixp-routing/invoice-extraction | 445.9s | 1 | 49 | 436.0s |
| skill-flow-ixp-routing/receipts | 330.2s | 1 | 50 | 320.4s |
| skill-flow-ixp-routing/contracts | 313.8s | 1 | 37 | 303.6s |
| skill-flow-ixp-routing/forms-classify | 354.8s | 1 | 37 | 345.0s |
| skill-flow-bellevue-weather | 509.4s | 1 | 35 | 473.1s |
| skill-flow-customer-escalation-simulated | 874.0s | 1 | 125 | 856.0s |
| skill-flow-ipe-enum | 698.2s | 1 | 44 | 686.3s |
| skill-flow-hitl-quality-schema-design | 276.9s | 1 | 34 | 263.1s |
| skill-flow-webhook-waitfor-parallel | 278.1s | 1 | 36 | 269.2s |
| skill-flow-solution-select-ask | 119.5s | 3 | 26 | 32.7s |
| skill-flow-terminate | 311.9s | 1 | 32 | 274.2s |
| skill-flow-merge-parallel-sync | 198.3s | 1 | 28 | 165.2s |
| skill-flow-multi-city-weather | 830.8s | 1 | 33 | 786.4s |
| skill-flow-ixp-routing-listing/r01 | 62.1s | 1 | 15 | 57.3s |
| skill-flow-ixp-routing-listing/r02 | 67.4s | 1 | 16 | 62.1s |
| skill-flow-ixp-routing-listing/r03 | 45.8s | 1 | 8 | 42.1s |
| skill-flow-ixp-routing-listing/r04 | 50.3s | 1 | 12 | 46.9s |
| skill-flow-ixp-routing-listing/r05 | 59.5s | 1 | 13 | 56.3s |
| skill-flow-ixp-routing-listing/r06 | 55.3s | 1 | 12 | 51.3s |
| skill-flow-ixp-routing-listing/r07 | 66.3s | 1 | 19 | 63.6s |
| skill-flow-ixp-routing-listing/r08 | 70.7s | 1 | 13 | 68.3s |
| skill-flow-ixp-routing-listing/r09 | 54.1s | 1 | 11 | 52.1s |
| skill-flow-ixp-routing-listing/r10 | 58.2s | 1 | 12 | 54.3s |
| skill-flow-add-output | 61.8s | 1 | 11 | 26.9s |
| skill-flow-hitl-quality-brownfield-insert | 548.9s | 1 | 49 | 534.5s |
| skill-flow-feet-inches | 386.9s | 1 | 31 | 340.8s |
| skill-flow-bindings-multi-connector-independence | 277.5s | 1 | 45 | 273.0s |
| skill-flow-non-catalog-http-fallback | 214.0s | 1 | 49 | 210.8s |
| skill-flow-update-node | 76.6s | 1 | 15 | 47.7s |
| skill-flow-devcon-billing-dispute-resolution | 938.3s | 1 | 115 | 877.8s |
| skill-flow-cli-dice-roller-simulated | 290.9s | 2 | 25 | 117.2s |
| skill-flow-ipe-complex-array | 508.6s | 1 | 47 | 503.4s |
| skill-flow-ipe-searchable-joins | 514.1s | 1 | 43 | 508.8s |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 842.3s | 1 | 94 | 830.3s |
| skill-flow-add-node | 105.3s | 1 | 15 | 66.5s |
| skill-flow-delay | 200.9s | 1 | 26 | 192.2s |
| skill-flow-generic-dynamic-node | 493.5s | 1 | 70 | 457.6s |
| skill-flow-devcon-billing-invoice-lookup | 827.5s | 1 | 46 | 747.9s |
| skill-flow-ipe-multiselect | 541.1s | 1 | 58 | 537.0s |
| skill-flow-transform-group-by | 201.7s | 1 | 25 | 194.0s |
| skill-flow-file-attachment-debug | 253.6s | 1 | 36 | 229.3s |
| skill-flow-ipe-required-groups | 246.2s | 1 | 37 | 243.5s |
| skill-flow-eval-evaluator-type-choice | 111.9s | 1 | 21 | 109.9s |
| skill-flow-ipe-jira-search-triage | 336.7s | 1 | 36 | 303.0s |
| skill-flow-eval-local-crud | 231.1s | 1 | 30 | 228.9s |
| skill-flow-devcon-billing-discrepancy-detector | 713.5s | 1 | 53 | 673.1s |
| skill-flow-batch-transform | 178.0s | 1 | 23 | 165.0s |
| skill-flow-ipe-jira-create-issue | 339.7s | 1 | 44 | 309.0s |
| skill-flow-outlook-trigger-inbox | 293.2s | 1 | 47 | 280.1s |
| skill-flow-hitl-smoke-completed-port | 224.7s | 1 | 36 | 214.3s |
| skill-flow-hitl-smoke-node-placed | 196.2s | 1 | 30 | 185.9s |
| skill-flow-devcon-billing-resolution-writer | 320.6s | 1 | 31 | 283.9s |
| skill-flow-ipe-enhanced-enum | 430.9s | 1 | 42 | 426.6s |
| skill-flow-bindings-idempotent-reconfigure | 616.3s | 1 | 51 | 612.7s |
| skill-flow-expense-approval-simulated | 621.0s | 7 | 58 | 70.7s |
| skill-flow-rpa | 211.2s | 1 | 28 | 163.7s |
| skill-flow-loop-multiply | 331.6s | 1 | 27 | 295.7s |
| skill-flow-init-validate | 116.5s | 1 | 28 | 114.5s |
| skill-flow-slack-http-fallback | 231.3s | 1 | 48 | 211.8s |
| skill-flow-move-node | 140.6s | 1 | 24 | 111.5s |
| skill-flow-ipe-path-params | 369.0s | 1 | 59 | 365.3s |
| skill-flow-dice-roller | 184.2s | 1 | 30 | 159.8s |
| skill-flow-hitl-quality-result-downstream | 142.4s | 1 | 32 | 136.1s |
| skill-flow-ixp-e2e-project-selection/aviation | 388.9s | 1 | 49 | 382.3s |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 316.3s | 1 | 41 | 309.0s |
| skill-flow-ipe-dtl-load-by-default-true | 268.1s | 1 | 44 | 266.1s |
| skill-flow-slack-channel-description | 277.1s | 1 | 55 | 249.9s |
| skill-flow-wiki-pageviews | 644.7s | 1 | 35 | 589.1s |
| skill-flow-ixp-invoice-extraction-simulated | 2016.0s | 11 | 215 | 167.6s |
| skill-flow-openmeteo-weather | 239.1s | 1 | 48 | 209.1s |
| skill-flow-outlook-waitfor-email | 201.4s | 1 | 44 | 191.1s |
| skill-flow-customer-escalation | 448.3s | 1 | 66 | 437.9s |
| skill-flow-calculator | 224.6s | 1 | 31 | 199.2s |
| skill-flow-trigger-with-filter | 111.1s | 1 | 15 | 108.6s |
| skill-flow-e2e-devcon-expense-approval | 312.4s | 1 | 36 | 305.1s |
| skill-flow-ipe-dtl-load-by-default-false | 374.0s | 1 | 77 | 371.5s |
| skill-flow-transform-map | 245.4s | 1 | 32 | 238.6s |
| skill-flow-slack-channel-description-simulated | 375.6s | 5 | 59 | 61.5s |
| skill-flow-eval-simulation-crud | 163.8s | 1 | 62 | 161.9s |
| skill-flow-devcon-billing-dispute-analyst | 332.6s | 1 | 50 | 283.5s |
| skill-flow-api-workflow | 285.4s | 1 | 39 | 260.7s |
| skill-flow-hitl-smoke-multi-outcome-routing | 314.3s | 1 | 41 | 302.2s |
| skill-flow-interactive-customer-escalation-triage | 328.5s | 4 | 38 | 61.6s |
| skill-flow-hitl-quality-boolean-decision | 315.4s | 1 | 37 | 303.5s |
| skill-flow-group-to-subflow | 905.4s | 0 | 0 | N/A |
| skill-flow-switch | 336.8s | 1 | 37 | 303.7s |
| skill-flow-ipe-query-params | 168.1s | 1 | 34 | 164.8s |
| skill-flow-ipe-ceql-where | 498.6s | 1 | 53 | 495.2s |
| skill-flow-ixp-scaffold-multinode | 398.4s | 1 | 32 | 390.6s |
| skill-flow-bellevue-weather-simulated | 1209.9s | 2 | 64 | 600.0s |
| skill-flow-subflow | 231.9s | 1 | 28 | 204.7s |
| skill-flow-bindings-reconfigure-different-connection | 507.9s | 1 | 48 | 502.3s |
| skill-flow-bindings-no-duplicates | 615.6s | 1 | 58 | 610.8s |
| skill-flow-ipe-generate-schema | 285.5s | 1 | 50 | 283.2s |
| skill-flow-transform-filter | 139.3s | 1 | 24 | 131.2s |
| skill-flow-lowcode-agent | 249.5s | 1 | 41 | 208.3s |
| skill-flow-hitl-schema-design-simulated | 306.2s | 5 | 46 | 47.9s |
| skill-flow-inline-agent-robust | 384.3s | 1 | 36 | 381.9s |
| skill-flow-remove-node | 137.7s | 1 | 32 | 106.1s |
| skill-flow-decision | 218.4s | 1 | 30 | 169.5s |
| skill-flow-ixp-scaffold-minimal | 385.8s | 1 | 33 | 377.2s |
| skill-flow-reading-list | 258.0s | 1 | 31 | 233.8s |
| skill-flow-ipe-drive-to-slack | 278.1s | 1 | 59 | 275.4s |
| skill-flow-eval-inline-agent | 621.5s | 1 | 33 | 618.9s |
| skill-flow-ipe-jira-get-issue | 519.9s | 1 | 54 | 489.6s |
| skill-flow-coded-agent | 402.3s | 1 | 95 | 390.1s |
| skill-flow-ixp-routing-negative/stripe-http | 181.4s | 1 | 31 | 179.1s |
| skill-flow-ixp-routing-negative/slack-summary | 272.6s | 1 | 28 | 269.5s |
| skill-flow-ixp-routing-negative/sf-update | 303.6s | 1 | 51 | 300.2s |
| skill-flow-ixp-routing-negative/http-webhook | 210.0s | 1 | 29 | 207.8s |
| skill-flow-ixp-routing-negative/gsheet-loop | 395.4s | 1 | 31 | 393.2s |
| skill-flow-ixp-routing-negative/queue-write | 167.8s | 1 | 39 | 165.0s |
| skill-flow-ixp-routing-negative/teams-decision | 250.1s | 1 | 34 | 245.7s |
| skill-flow-ixp-routing-negative/delay-email | 300.0s | 1 | 37 | 294.8s |
| skill-flow-ixp-integration-handle-routing | 602.0s | 1 | 55 | 591.1s |
| skill-flow-paginated-reference-lookup | 195.4s | 1 | 41 | 190.7s |
| skill-flow-registry-discovery | 88.5s | 1 | 21 | 82.9s |
| skill-flow-ipe-jira-lifecycle | 1267.1s | 1 | 39 | 661.4s |
| skill-flow-summarize | 189.0s | 1 | 23 | 177.3s |
| skill-flow-scheduled-trigger | 187.3s | 1 | 26 | 178.8s |
| skill-flow-slack-weather-pipeline | 1175.9s | 1 | 82 | 1146.6s |
| skill-flow-eval-no-auto-upload | 79.8s | 1 | 21 | 76.2s |
| skill-flow-ixp-routing/explicit | 486.3s | 1 | 85 | 483.2s |
| skill-flow-ixp-routing/invoice-extraction | 392.4s | 1 | 53 | 389.4s |
| skill-flow-ixp-routing/receipts | 259.4s | 1 | 50 | 257.4s |
| skill-flow-ixp-routing/contracts | 289.7s | 1 | 36 | 286.6s |
| skill-flow-ixp-routing/forms-classify | 226.1s | 1 | 38 | 222.5s |
| skill-flow-bellevue-weather | 441.8s | 1 | 39 | 411.8s |
| skill-flow-customer-escalation-simulated | 1022.2s | 2 | 137 | 500.6s |
| skill-flow-ipe-enum | 464.8s | 1 | 55 | 459.3s |
| skill-flow-hitl-quality-schema-design | 429.4s | 1 | 77 | 420.4s |
| skill-flow-webhook-waitfor-parallel | 295.0s | 1 | 50 | 291.5s |
| skill-flow-solution-select-ask | 145.1s | 3 | 25 | 42.4s |
| skill-flow-terminate | 338.4s | 1 | 45 | 308.5s |
| skill-flow-merge-parallel-sync | 171.1s | 1 | 29 | 159.9s |
| skill-flow-multi-city-weather | 879.2s | 1 | 52 | 830.4s |
| skill-flow-ixp-routing-listing/r01 | 52.3s | 1 | 13 | 50.3s |
| skill-flow-ixp-routing-listing/r02 | 55.8s | 1 | 11 | 53.6s |
| skill-flow-ixp-routing-listing/r03 | 51.5s | 1 | 13 | 48.9s |
| skill-flow-ixp-routing-listing/r04 | 58.4s | 1 | 14 | 55.8s |
| skill-flow-ixp-routing-listing/r05 | 38.7s | 1 | 9 | 34.8s |
| skill-flow-ixp-routing-listing/r06 | 62.4s | 1 | 8 | 58.7s |
| skill-flow-ixp-routing-listing/r07 | 96.1s | 1 | 28 | 92.7s |
| skill-flow-ixp-routing-listing/r08 | 53.8s | 1 | 12 | 50.4s |
| skill-flow-ixp-routing-listing/r09 | 55.5s | 1 | 15 | 52.1s |
| skill-flow-ixp-routing-listing/r10 | 61.1s | 1 | 12 | 57.5s |
| skill-flow-add-output | 62.1s | 1 | 13 | 30.3s |
| skill-flow-hitl-quality-brownfield-insert | 393.0s | 1 | 41 | 383.4s |
| skill-flow-feet-inches | 312.4s | 1 | 26 | 268.3s |
| skill-flow-bindings-multi-connector-independence | 299.3s | 1 | 59 | 293.5s |
| skill-flow-non-catalog-http-fallback | 182.2s | 1 | 40 | 179.2s |
| skill-flow-update-node | 63.6s | 1 | 11 | 33.7s |
| skill-flow-devcon-billing-dispute-resolution | 1535.6s | 1 | 160 | 1519.7s |
| skill-flow-cli-dice-roller-simulated | 348.6s | 5 | 41 | 56.6s |
| skill-flow-ipe-complex-array | 487.1s | 1 | 51 | 483.5s |
| skill-flow-ipe-searchable-joins | 323.9s | 1 | 45 | 320.4s |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 1203.2s | 1 | 94 | 1200.1s |
| skill-flow-add-node | 102.8s | 1 | 18 | 70.0s |
| skill-flow-delay | 181.7s | 1 | 32 | 170.5s |
| skill-flow-generic-dynamic-node | 510.0s | 1 | 80 | 482.5s |
| skill-flow-devcon-billing-invoice-lookup | 809.8s | 1 | 86 | 744.0s |
| skill-flow-ipe-multiselect | 357.4s | 1 | 56 | 355.1s |
| skill-flow-transform-group-by | 206.9s | 1 | 24 | 197.7s |
| skill-flow-file-attachment-debug | 191.7s | 1 | 31 | 163.5s |
| skill-flow-ipe-required-groups | 242.6s | 1 | 43 | 236.4s |
| skill-flow-eval-evaluator-type-choice | 102.8s | 1 | 18 | 96.5s |
| skill-flow-ipe-jira-search-triage | 465.9s | 1 | 45 | 430.1s |
| skill-flow-eval-local-crud | 158.9s | 1 | 25 | 154.7s |
| skill-flow-devcon-billing-discrepancy-detector | 704.9s | 1 | 69 | 677.0s |
| skill-flow-batch-transform | 163.3s | 1 | 21 | 154.2s |
| skill-flow-ipe-jira-create-issue | 304.0s | 1 | 42 | 270.4s |
| skill-flow-outlook-trigger-inbox | 265.3s | 1 | 69 | 254.3s |
| skill-flow-hitl-smoke-completed-port | 202.2s | 1 | 28 | 194.3s |
| skill-flow-hitl-smoke-node-placed | 196.4s | 1 | 31 | 189.1s |
| skill-flow-devcon-billing-resolution-writer | 322.0s | 1 | 31 | 290.2s |
| skill-flow-ipe-enhanced-enum | 417.3s | 1 | 43 | 415.3s |
| skill-flow-bindings-idempotent-reconfigure | 279.8s | 1 | 52 | 273.9s |
| skill-flow-expense-approval-simulated | 1073.2s | 9 | 101 | 101.5s |
| skill-flow-rpa | 206.3s | 1 | 29 | 156.6s |
| skill-flow-loop-multiply | 341.1s | 1 | 30 | 310.2s |
| skill-flow-init-validate | 109.1s | 1 | 27 | 104.1s |
| skill-flow-slack-http-fallback | 266.4s | 1 | 54 | 244.7s |
| skill-flow-move-node | 138.7s | 1 | 20 | 108.0s |
| skill-flow-ipe-path-params | 308.2s | 1 | 67 | 303.2s |
| skill-flow-dice-roller | 195.2s | 1 | 28 | 166.3s |
| skill-flow-hitl-quality-result-downstream | 204.5s | 1 | 31 | 197.1s |
| skill-flow-ixp-e2e-project-selection/aviation | 410.9s | 1 | 39 | 403.1s |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 365.0s | 1 | 37 | 356.2s |
| skill-flow-ipe-dtl-load-by-default-true | 176.7s | 1 | 35 | 173.9s |
| skill-flow-slack-channel-description | 238.5s | 1 | 47 | 214.0s |
| skill-flow-wiki-pageviews | 904.8s | 0 | 0 | N/A |
| skill-flow-ixp-invoice-extraction-simulated | 2317.7s | 9 | 230 | 237.8s |
| skill-flow-openmeteo-weather | 334.9s | 1 | 45 | 312.1s |
| skill-flow-outlook-waitfor-email | 246.2s | 1 | 51 | 237.7s |
| skill-flow-customer-escalation | 702.5s | 1 | 87 | 692.8s |
| skill-flow-calculator | 181.6s | 1 | 25 | 156.9s |
| skill-flow-trigger-with-filter | 86.5s | 1 | 10 | 83.8s |
| skill-flow-e2e-devcon-expense-approval | 327.3s | 1 | 31 | 319.6s |
| skill-flow-ipe-dtl-load-by-default-false | 361.1s | 1 | 88 | 358.6s |
| skill-flow-transform-map | 212.7s | 1 | 32 | 204.3s |
| skill-flow-slack-channel-description-simulated | 529.3s | 5 | 74 | 89.6s |
| skill-flow-eval-simulation-crud | 224.2s | 1 | 55 | 221.8s |
| skill-flow-devcon-billing-dispute-analyst | 358.5s | 1 | 50 | 291.9s |
| skill-flow-api-workflow | 253.1s | 1 | 35 | 228.9s |
| skill-flow-hitl-smoke-multi-outcome-routing | 300.6s | 1 | 31 | 294.1s |
| skill-flow-interactive-customer-escalation-triage | 291.7s | 3 | 35 | 73.4s |
| skill-flow-hitl-quality-boolean-decision | 280.1s | 1 | 30 | 273.0s |
| skill-flow-group-to-subflow | 663.7s | 1 | 31 | 614.4s |
| skill-flow-switch | 321.3s | 1 | 26 | 296.4s |
| skill-flow-ipe-query-params | 143.7s | 1 | 35 | 138.9s |
| skill-flow-ipe-ceql-where | 616.8s | 1 | 50 | 612.8s |
| skill-flow-ixp-scaffold-multinode | 455.9s | 1 | 36 | 446.3s |
| skill-flow-bellevue-weather-simulated | 514.6s | 4 | 49 | 102.6s |
| skill-flow-subflow | 255.2s | 1 | 33 | 229.6s |
| skill-flow-bindings-reconfigure-different-connection | 236.0s | 1 | 49 | 229.5s |
| skill-flow-bindings-no-duplicates | 358.9s | 1 | 51 | 354.9s |
| skill-flow-ipe-generate-schema | 287.4s | 1 | 55 | 285.1s |
| skill-flow-transform-filter | 196.8s | 1 | 23 | 189.7s |
| skill-flow-lowcode-agent | 269.9s | 1 | 37 | 227.4s |
| skill-flow-hitl-schema-design-simulated | 394.1s | 5 | 62 | 67.3s |
| skill-flow-inline-agent-robust | 290.0s | 1 | 35 | 287.0s |
| skill-flow-remove-node | 125.4s | 1 | 30 | 96.9s |
| skill-flow-decision | 282.7s | 1 | 29 | 237.4s |
| skill-flow-ixp-scaffold-minimal | 439.9s | 1 | 33 | 427.1s |
| skill-flow-reading-list | 250.1s | 1 | 25 | 226.2s |
| skill-flow-ipe-drive-to-slack | 269.5s | 1 | 60 | 267.6s |
| skill-flow-eval-inline-agent | 427.2s | 1 | 35 | 425.0s |
| skill-flow-ipe-jira-get-issue | 302.2s | 1 | 54 | 270.9s |
| skill-flow-coded-agent | 417.0s | 1 | 74 | 383.1s |
| skill-flow-ixp-routing-negative/stripe-http | 217.5s | 1 | 33 | 215.2s |
| skill-flow-ixp-routing-negative/slack-summary | 316.3s | 1 | 40 | 313.6s |
| skill-flow-ixp-routing-negative/sf-update | 157.7s | 1 | 35 | 155.6s |
| skill-flow-ixp-routing-negative/http-webhook | 206.9s | 1 | 42 | 203.9s |
| skill-flow-ixp-routing-negative/gsheet-loop | 223.1s | 1 | 28 | 218.9s |
| skill-flow-ixp-routing-negative/queue-write | 185.6s | 1 | 36 | 181.9s |
| skill-flow-ixp-routing-negative/teams-decision | 234.0s | 1 | 38 | 231.5s |
| skill-flow-ixp-routing-negative/delay-email | 175.9s | 1 | 30 | 173.5s |
| skill-flow-ixp-integration-handle-routing | 790.9s | 1 | 55 | 782.9s |
| skill-flow-paginated-reference-lookup | 228.7s | 1 | 44 | 226.3s |
| skill-flow-registry-discovery | 88.4s | 1 | 22 | 85.2s |
| skill-flow-ipe-jira-lifecycle | 1486.0s | 1 | 52 | 880.9s |
| skill-flow-summarize | 181.8s | 1 | 23 | 168.0s |
| skill-flow-scheduled-trigger | 244.6s | 1 | 36 | 235.0s |
| skill-flow-slack-weather-pipeline | 1203.9s | 1 | 52 | 1200.2s |
| skill-flow-eval-no-auto-upload | 86.4s | 1 | 20 | 83.7s |
| skill-flow-ixp-routing/explicit | 208.0s | 1 | 39 | 205.4s |
| skill-flow-ixp-routing/invoice-extraction | 322.3s | 1 | 58 | 319.9s |
| skill-flow-ixp-routing/receipts | 733.8s | 1 | 106 | 730.3s |
| skill-flow-ixp-routing/contracts | 362.7s | 1 | 48 | 358.9s |
| skill-flow-ixp-routing/forms-classify | 217.7s | 1 | 45 | 214.4s |
| skill-flow-bellevue-weather | 398.4s | 1 | 35 | 362.1s |
| skill-flow-customer-escalation-simulated | 2013.0s | 12 | 191 | 151.5s |
| skill-flow-ipe-enum | 408.5s | 1 | 43 | 403.9s |
| skill-flow-hitl-quality-schema-design | 310.7s | 1 | 36 | 298.6s |
| skill-flow-webhook-waitfor-parallel | 345.4s | 1 | 50 | 342.1s |
| skill-flow-solution-select-ask | 128.1s | 3 | 23 | 37.1s |
| skill-flow-terminate | 336.1s | 1 | 30 | 307.4s |
| skill-flow-merge-parallel-sync | 167.3s | 1 | 28 | 158.2s |
| skill-flow-multi-city-weather | 905.3s | 1 | 38 | 894.6s |
| skill-flow-ixp-routing-listing/r01 | 83.0s | 1 | 17 | 78.1s |
| skill-flow-ixp-routing-listing/r02 | 79.1s | 1 | 13 | 75.6s |
| skill-flow-ixp-routing-listing/r03 | 66.5s | 1 | 12 | 62.1s |
| skill-flow-ixp-routing-listing/r04 | 65.1s | 1 | 12 | 58.6s |
| skill-flow-ixp-routing-listing/r05 | 54.9s | 1 | 12 | 47.6s |
| skill-flow-ixp-routing-listing/r06 | 65.1s | 1 | 13 | 58.7s |
| skill-flow-ixp-routing-listing/r07 | 124.0s | 1 | 30 | 118.9s |
| skill-flow-ixp-routing-listing/r08 | 65.9s | 1 | 13 | 60.8s |
| skill-flow-ixp-routing-listing/r09 | 48.8s | 1 | 12 | 44.3s |
| skill-flow-ixp-routing-listing/r10 | 65.4s | 1 | 13 | 59.8s |
| skill-flow-add-output | 74.2s | 1 | 12 | 33.7s |
| skill-flow-hitl-quality-brownfield-insert | 391.7s | 1 | 85 | 382.9s |
| skill-flow-feet-inches | 501.7s | 1 | 45 | 458.0s |
| skill-flow-bindings-multi-connector-independence | 403.3s | 1 | 57 | 396.5s |
| skill-flow-non-catalog-http-fallback | 260.7s | 1 | 44 | 256.0s |
| skill-flow-update-node | 85.2s | 1 | 15 | 49.1s |
| skill-flow-devcon-billing-dispute-resolution | 1421.0s | 1 | 110 | 1344.5s |
| skill-flow-cli-dice-roller-simulated | 456.3s | 6 | 53 | 58.4s |
| skill-flow-ipe-complex-array | 599.9s | 1 | 61 | 593.2s |
| skill-flow-ipe-searchable-joins | 342.2s | 1 | 40 | 336.5s |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 659.0s | 1 | 100 | 649.9s |
| skill-flow-add-node | 157.0s | 1 | 22 | 116.3s |
| skill-flow-delay | 130.2s | 1 | 23 | 118.2s |
| skill-flow-generic-dynamic-node | 556.8s | 1 | 77 | 525.3s |
| skill-flow-devcon-billing-invoice-lookup | 570.0s | 1 | 90 | 491.9s |
| skill-flow-ipe-multiselect | 438.6s | 1 | 39 | 434.8s |
| skill-flow-transform-group-by | 212.9s | 1 | 38 | 205.5s |
| skill-flow-file-attachment-debug | 231.4s | 1 | 34 | 204.4s |
| skill-flow-ipe-required-groups | 256.4s | 1 | 41 | 254.3s |
| skill-flow-eval-evaluator-type-choice | 139.2s | 1 | 42 | 136.7s |
| skill-flow-ipe-jira-search-triage | 449.1s | 1 | 47 | 407.9s |
| skill-flow-eval-local-crud | 111.6s | 1 | 22 | 105.6s |
| skill-flow-devcon-billing-discrepancy-detector | 997.2s | 1 | 59 | 964.6s |
| skill-flow-batch-transform | 193.5s | 1 | 23 | 185.1s |
| skill-flow-ipe-jira-create-issue | 316.3s | 1 | 49 | 283.6s |
| skill-flow-outlook-trigger-inbox | 352.5s | 1 | 51 | 337.2s |
| skill-flow-hitl-smoke-completed-port | 229.9s | 1 | 30 | 220.5s |
| skill-flow-hitl-smoke-node-placed | 272.2s | 1 | 36 | 261.1s |
| skill-flow-devcon-billing-resolution-writer | 360.8s | 1 | 38 | 296.1s |
| skill-flow-ipe-enhanced-enum | 286.2s | 1 | 46 | 282.4s |
| skill-flow-bindings-idempotent-reconfigure | 628.8s | 1 | 79 | 624.5s |
| skill-flow-expense-approval-simulated | 450.6s | 4 | 46 | 90.2s |
| skill-flow-rpa | 284.2s | 1 | 44 | 229.6s |
| skill-flow-loop-multiply | 289.8s | 1 | 32 | 254.9s |
| skill-flow-init-validate | 136.7s | 1 | 26 | 132.8s |
| skill-flow-slack-http-fallback | 332.2s | 1 | 53 | 308.2s |
| skill-flow-move-node | 305.7s | 1 | 12 | 280.8s |
| skill-flow-ipe-path-params | 335.0s | 1 | 59 | 330.3s |
| skill-flow-dice-roller | 290.1s | 1 | 26 | 146.8s |
| skill-flow-hitl-quality-result-downstream | 146.6s | 1 | 29 | 138.0s |
| skill-flow-ixp-e2e-project-selection/aviation | 383.6s | 1 | 43 | 376.9s |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 352.6s | 1 | 51 | 343.8s |
| skill-flow-ipe-dtl-load-by-default-true | 246.7s | 1 | 36 | 244.5s |
| skill-flow-slack-channel-description | 232.7s | 1 | 48 | 203.5s |
| skill-flow-wiki-pageviews | 731.6s | 1 | 33 | 675.9s |
| skill-flow-ixp-invoice-extraction-simulated | 1542.2s | 8 | 199 | 178.2s |
| skill-flow-openmeteo-weather | 248.1s | 1 | 45 | 202.0s |
| skill-flow-outlook-waitfor-email | 267.7s | 1 | 44 | 258.0s |
| skill-flow-customer-escalation | 872.9s | 1 | 79 | 862.5s |
| skill-flow-calculator | 199.4s | 1 | 28 | 170.4s |
| skill-flow-trigger-with-filter | 152.8s | 1 | 15 | 148.9s |
| skill-flow-e2e-devcon-expense-approval | 514.8s | 1 | 35 | 505.5s |
| skill-flow-ipe-dtl-load-by-default-false | 344.0s | 1 | 84 | 341.9s |
| skill-flow-transform-map | 249.2s | 1 | 30 | 239.8s |
| skill-flow-slack-channel-description-simulated | 1835.5s | 4 | 159 | 441.9s |
| skill-flow-eval-simulation-crud | 157.9s | 1 | 54 | 154.5s |
| skill-flow-devcon-billing-dispute-analyst | 502.5s | 1 | 55 | 466.4s |
| skill-flow-api-workflow | 220.8s | 1 | 40 | 196.0s |
| skill-flow-hitl-smoke-multi-outcome-routing | 293.0s | 1 | 35 | 284.4s |
| skill-flow-interactive-customer-escalation-triage | 439.2s | 4 | 40 | 89.7s |
| skill-flow-hitl-quality-boolean-decision | 281.8s | 1 | 32 | 273.5s |
| skill-flow-group-to-subflow | 842.2s | 1 | 21 | 804.8s |
| skill-flow-switch | 268.0s | 1 | 28 | 244.1s |
| skill-flow-ipe-query-params | 175.0s | 1 | 29 | 172.8s |
| skill-flow-ipe-ceql-where | 432.7s | 1 | 58 | 430.1s |
| skill-flow-ixp-scaffold-multinode | 374.9s | 1 | 36 | 368.0s |
| skill-flow-bellevue-weather-simulated | 757.3s | 8 | 45 | 77.4s |
| skill-flow-subflow | 243.5s | 1 | 29 | 216.5s |
| skill-flow-bindings-reconfigure-different-connection | 575.0s | 1 | 43 | 568.1s |
| skill-flow-bindings-no-duplicates | 491.2s | 1 | 46 | 488.1s |
| skill-flow-ipe-generate-schema | 223.9s | 1 | 50 | 220.5s |
| skill-flow-transform-filter | 174.2s | 1 | 31 | 166.0s |
| skill-flow-lowcode-agent | 259.4s | 1 | 32 | 226.3s |
| skill-flow-hitl-schema-design-simulated | 401.4s | 4 | 34 | 80.6s |
| skill-flow-inline-agent-robust | 378.1s | 1 | 31 | 375.2s |
| skill-flow-remove-node | 108.9s | 1 | 32 | 81.2s |
| skill-flow-decision | 290.3s | 1 | 29 | 254.2s |
| skill-flow-ixp-scaffold-minimal | 463.7s | 1 | 42 | 450.1s |
| skill-flow-reading-list | 224.8s | 1 | 25 | 199.6s |
| skill-flow-ipe-drive-to-slack | 344.7s | 1 | 65 | 342.6s |
| skill-flow-eval-inline-agent | 383.0s | 1 | 37 | 380.2s |
| skill-flow-ipe-jira-get-issue | 406.0s | 1 | 61 | 340.3s |
| skill-flow-coded-agent | 381.4s | 1 | 73 | 273.4s |
| skill-flow-ixp-routing-negative/stripe-http | 175.6s | 1 | 32 | 173.2s |
| skill-flow-ixp-routing-negative/slack-summary | 337.7s | 1 | 42 | 335.4s |
| skill-flow-ixp-routing-negative/sf-update | 182.0s | 1 | 34 | 180.1s |
| skill-flow-ixp-routing-negative/http-webhook | 277.3s | 1 | 55 | 275.4s |
| skill-flow-ixp-routing-negative/gsheet-loop | 176.9s | 1 | 34 | 175.0s |
| skill-flow-ixp-routing-negative/queue-write | 212.5s | 1 | 40 | 210.6s |
| skill-flow-ixp-routing-negative/teams-decision | 174.4s | 1 | 31 | 172.6s |
| skill-flow-ixp-routing-negative/delay-email | 262.5s | 1 | 29 | 259.9s |
| skill-flow-ixp-integration-handle-routing | 523.5s | 1 | 40 | 514.9s |
| skill-flow-paginated-reference-lookup | 283.8s | 1 | 56 | 280.7s |
| skill-flow-registry-discovery | 74.4s | 1 | 14 | 70.3s |
| skill-flow-ipe-jira-lifecycle | 599.2s | 1 | 49 | 548.9s |
| skill-flow-summarize | 180.2s | 1 | 24 | 165.7s |
| skill-flow-scheduled-trigger | 235.7s | 1 | 31 | 224.9s |
| skill-flow-slack-weather-pipeline | 1204.0s | 1 | 75 | 1200.1s |
| skill-flow-eval-no-auto-upload | 96.8s | 1 | 24 | 94.6s |
| skill-flow-ixp-routing/explicit | 196.4s | 1 | 35 | 194.3s |
| skill-flow-ixp-routing/invoice-extraction | 470.2s | 1 | 59 | 468.1s |
| skill-flow-ixp-routing/receipts | 295.8s | 1 | 59 | 291.6s |
| skill-flow-ixp-routing/contracts | 268.0s | 1 | 50 | 264.6s |
| skill-flow-ixp-routing/forms-classify | 199.3s | 1 | 43 | 197.2s |
| skill-flow-bellevue-weather | 534.9s | 1 | 36 | 509.3s |
| skill-flow-customer-escalation-simulated | 1290.6s | 10 | 131 | 111.1s |
| skill-flow-ipe-enum | 398.2s | 1 | 34 | 393.3s |
| skill-flow-hitl-quality-schema-design | 267.3s | 1 | 45 | 257.6s |
| skill-flow-webhook-waitfor-parallel | 283.7s | 1 | 55 | 280.3s |
| skill-flow-solution-select-ask | 143.3s | 3 | 25 | 42.2s |
| skill-flow-terminate | 552.1s | 1 | 44 | 527.8s |
| skill-flow-merge-parallel-sync | 161.2s | 1 | 31 | 150.8s |
| skill-flow-multi-city-weather | 428.1s | 1 | 33 | 416.6s |
| skill-flow-ixp-routing-listing/r01 | 86.9s | 1 | 22 | 81.4s |
| skill-flow-ixp-routing-listing/r02 | 60.3s | 1 | 9 | 54.7s |
| skill-flow-ixp-routing-listing/r03 | 67.1s | 1 | 13 | 61.4s |
| skill-flow-ixp-routing-listing/r04 | 63.3s | 1 | 12 | 57.4s |
| skill-flow-ixp-routing-listing/r05 | 79.5s | 1 | 14 | 73.0s |
| skill-flow-ixp-routing-listing/r06 | 71.9s | 1 | 16 | 65.2s |
| skill-flow-ixp-routing-listing/r07 | 73.5s | 1 | 12 | 67.1s |
| skill-flow-ixp-routing-listing/r08 | 60.4s | 1 | 12 | 54.9s |
| skill-flow-ixp-routing-listing/r09 | 57.7s | 1 | 12 | 53.3s |
| skill-flow-ixp-routing-listing/r10 | 58.6s | 1 | 8 | 53.3s |
| skill-flow-add-output | 59.3s | 1 | 11 | 26.8s |
| skill-flow-hitl-quality-brownfield-insert | 328.3s | 1 | 42 | 318.5s |
| skill-flow-feet-inches | 393.7s | 1 | 39 | 349.6s |
| skill-flow-bindings-multi-connector-independence | 540.1s | 1 | 56 | 532.8s |
| skill-flow-non-catalog-http-fallback | 211.6s | 1 | 45 | 207.6s |
| skill-flow-update-node | 66.2s | 1 | 15 | 39.1s |
| skill-flow-devcon-billing-dispute-resolution | 931.3s | 1 | 117 | 893.2s |
| skill-flow-cli-dice-roller-simulated | 405.7s | 5 | 50 | 60.7s |
| skill-flow-ipe-complex-array | 565.4s | 1 | 55 | 560.7s |
| skill-flow-ipe-searchable-joins | 490.1s | 1 | 38 | 486.8s |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 875.2s | 1 | 102 | 866.5s |
| skill-flow-add-node | 129.0s | 1 | 20 | 95.9s |
| skill-flow-delay | 187.7s | 1 | 22 | 180.4s |
| skill-flow-generic-dynamic-node | 515.4s | 1 | 80 | 485.5s |
| skill-flow-devcon-billing-invoice-lookup | 875.4s | 1 | 55 | 807.2s |
| skill-flow-ipe-multiselect | 339.2s | 1 | 53 | 336.9s |
| skill-flow-transform-group-by | 240.6s | 1 | 25 | 233.5s |
| skill-flow-file-attachment-debug | 227.3s | 1 | 35 | 200.8s |
| skill-flow-ipe-required-groups | 268.7s | 1 | 43 | 265.2s |
| skill-flow-eval-evaluator-type-choice | 103.0s | 1 | 17 | 99.7s |
| skill-flow-ipe-jira-search-triage | 431.0s | 1 | 44 | 397.3s |
| skill-flow-eval-local-crud | 109.9s | 1 | 21 | 106.2s |
| skill-flow-devcon-billing-discrepancy-detector | 1125.1s | 1 | 66 | 1080.2s |
| skill-flow-batch-transform | 176.5s | 1 | 27 | 166.0s |
| skill-flow-ipe-jira-create-issue | 444.0s | 1 | 61 | 409.0s |
| skill-flow-outlook-trigger-inbox | 304.0s | 1 | 41 | 292.4s |
| skill-flow-hitl-smoke-completed-port | 206.8s | 1 | 30 | 195.9s |
| skill-flow-hitl-smoke-node-placed | 177.2s | 1 | 31 | 169.9s |
| skill-flow-devcon-billing-resolution-writer | 317.8s | 1 | 33 | 256.3s |
| skill-flow-ipe-enhanced-enum | 432.9s | 1 | 47 | 430.1s |
| skill-flow-bindings-idempotent-reconfigure | 430.1s | 1 | 54 | 424.9s |
| skill-flow-expense-approval-simulated | 830.8s | 7 | 66 | 103.6s |
| skill-flow-rpa | 244.5s | 1 | 45 | 196.4s |
| skill-flow-loop-multiply | 303.7s | 1 | 29 | 265.8s |
| skill-flow-init-validate | 125.5s | 1 | 27 | 122.9s |
| skill-flow-slack-http-fallback | 285.3s | 1 | 48 | 261.8s |
| skill-flow-move-node | 256.1s | 1 | 10 | 224.1s |
| skill-flow-ipe-path-params | 226.4s | 1 | 53 | 222.4s |
| skill-flow-dice-roller | 228.1s | 1 | 32 | 202.2s |
| skill-flow-hitl-quality-result-downstream | 265.6s | 1 | 27 | 255.2s |
| skill-flow-ixp-e2e-project-selection/aviation | 274.3s | 1 | 48 | 266.8s |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 351.2s | 1 | 44 | 341.0s |
| skill-flow-ipe-dtl-load-by-default-true | 173.1s | 1 | 38 | 170.6s |
| skill-flow-slack-channel-description | 264.2s | 1 | 49 | 230.4s |
| skill-flow-wiki-pageviews | 834.1s | 1 | 35 | 771.2s |
| skill-flow-ixp-invoice-extraction-simulated | 1652.5s | 5 | 131 | 309.7s |
| skill-flow-openmeteo-weather | 257.8s | 1 | 50 | 224.3s |
| skill-flow-outlook-waitfor-email | 242.4s | 1 | 47 | 230.3s |
| skill-flow-customer-escalation | 851.8s | 1 | 98 | 842.3s |
| skill-flow-calculator | 210.4s | 1 | 28 | 182.5s |
| skill-flow-trigger-with-filter | 325.3s | 1 | 52 | 323.2s |
| skill-flow-e2e-devcon-expense-approval | 271.2s | 1 | 34 | 263.5s |
| skill-flow-ipe-dtl-load-by-default-false | 254.3s | 1 | 60 | 251.1s |
| skill-flow-transform-map | 211.5s | 1 | 29 | 202.1s |
| skill-flow-slack-channel-description-simulated | 407.4s | 5 | 58 | 67.6s |
| skill-flow-eval-simulation-crud | 180.4s | 1 | 49 | 175.4s |
| skill-flow-devcon-billing-dispute-analyst | 424.3s | 1 | 66 | 358.2s |
| skill-flow-api-workflow | 350.3s | 1 | 62 | 323.2s |
| skill-flow-hitl-smoke-multi-outcome-routing | 263.8s | 1 | 30 | 257.9s |
| skill-flow-interactive-customer-escalation-triage | 270.7s | 3 | 30 | 69.2s |
| skill-flow-hitl-quality-boolean-decision | 277.9s | 1 | 30 | 269.1s |
| skill-flow-group-to-subflow | 903.9s | 0 | 0 | N/A |
| skill-flow-switch | 307.8s | 1 | 31 | 280.8s |
| skill-flow-ipe-query-params | 158.1s | 1 | 33 | 154.4s |
| skill-flow-ipe-ceql-where | 423.4s | 1 | 57 | 419.8s |
| skill-flow-ixp-scaffold-multinode | 528.8s | 1 | 38 | 518.7s |
| skill-flow-bellevue-weather-simulated | 1611.4s | 7 | 150 | 207.1s |
| skill-flow-subflow | 207.0s | 1 | 30 | 178.8s |
| skill-flow-bindings-reconfigure-different-connection | 260.4s | 1 | 48 | 253.8s |
| skill-flow-bindings-no-duplicates | 474.9s | 1 | 50 | 468.1s |
| skill-flow-ipe-generate-schema | 255.4s | 1 | 60 | 251.4s |
| skill-flow-transform-filter | 167.3s | 1 | 21 | 161.4s |
| skill-flow-lowcode-agent | 298.5s | 1 | 45 | 267.7s |
| skill-flow-hitl-schema-design-simulated | 394.6s | 5 | 40 | 63.0s |
| skill-flow-inline-agent-robust | 299.7s | 1 | 40 | 295.9s |
| skill-flow-remove-node | 109.5s | 1 | 28 | 82.7s |
| skill-flow-decision | 229.2s | 1 | 26 | 188.9s |
| skill-flow-ixp-scaffold-minimal | 493.1s | 1 | 33 | 484.1s |
| skill-flow-reading-list | 308.9s | 1 | 35 | 283.1s |
| skill-flow-ipe-drive-to-slack | 243.2s | 1 | 56 | 241.1s |
| skill-flow-eval-inline-agent | 507.2s | 1 | 37 | 504.8s |
| skill-flow-ipe-jira-get-issue | 285.2s | 1 | 49 | 252.6s |
| skill-flow-coded-agent | 295.0s | 1 | 71 | 283.8s |
| skill-flow-ixp-routing-negative/stripe-http | 166.6s | 1 | 37 | 164.0s |
| skill-flow-ixp-routing-negative/slack-summary | 334.3s | 1 | 28 | 331.4s |
| skill-flow-ixp-routing-negative/sf-update | 278.2s | 1 | 38 | 274.8s |
| skill-flow-ixp-routing-negative/http-webhook | 227.4s | 1 | 46 | 223.9s |
| skill-flow-ixp-routing-negative/gsheet-loop | 331.7s | 1 | 41 | 328.9s |
| skill-flow-ixp-routing-negative/queue-write | 201.6s | 1 | 47 | 198.8s |
| skill-flow-ixp-routing-negative/teams-decision | 173.6s | 1 | 31 | 170.7s |
| skill-flow-ixp-routing-negative/delay-email | 275.6s | 1 | 34 | 273.3s |
| skill-flow-ixp-integration-handle-routing | 442.4s | 1 | 46 | 431.4s |
| skill-flow-paginated-reference-lookup | 198.9s | 1 | 50 | 194.3s |
| skill-flow-registry-discovery | 75.2s | 1 | 12 | 70.9s |
| skill-flow-ipe-jira-lifecycle | 904.1s | 1 | 42 | 900.1s |
| skill-flow-summarize | 167.5s | 1 | 25 | 158.0s |
| skill-flow-scheduled-trigger | 233.7s | 1 | 23 | 225.8s |
| skill-flow-slack-weather-pipeline | 786.6s | 1 | 71 | 761.1s |
| skill-flow-eval-no-auto-upload | 83.5s | 1 | 21 | 80.9s |
| skill-flow-ixp-routing/explicit | 319.5s | 1 | 38 | 317.2s |
| skill-flow-ixp-routing/invoice-extraction | 282.7s | 1 | 53 | 279.9s |
| skill-flow-ixp-routing/receipts | 206.2s | 1 | 41 | 203.4s |
| skill-flow-ixp-routing/contracts | 299.4s | 1 | 34 | 296.2s |
| skill-flow-ixp-routing/forms-classify | 204.1s | 1 | 41 | 202.4s |
| skill-flow-bellevue-weather | 407.2s | 1 | 37 | 374.0s |
| skill-flow-customer-escalation-simulated | 1988.5s | 7 | 196 | 266.3s |
| skill-flow-ipe-enum | 461.3s | 1 | 42 | 456.5s |
| skill-flow-hitl-quality-schema-design | 360.5s | 1 | 31 | 351.1s |
| skill-flow-webhook-waitfor-parallel | 272.8s | 1 | 49 | 268.6s |
| skill-flow-solution-select-ask | 139.7s | 3 | 24 | 40.1s |
| skill-flow-terminate | 387.2s | 1 | 42 | 362.2s |
| skill-flow-merge-parallel-sync | 148.7s | 1 | 25 | 138.3s |
| skill-flow-multi-city-weather | 743.9s | 1 | 41 | 691.2s |
| skill-flow-ixp-routing-listing/r01 | 29.7s | 1 | 8 | 26.5s |
| skill-flow-ixp-routing-listing/r02 | 59.8s | 1 | 13 | 54.6s |
| skill-flow-ixp-routing-listing/r03 | 57.3s | 1 | 12 | 51.6s |
| skill-flow-ixp-routing-listing/r04 | 54.6s | 1 | 12 | 50.8s |
| skill-flow-ixp-routing-listing/r05 | 38.5s | 1 | 12 | 35.6s |
| skill-flow-ixp-routing-listing/r06 | 48.4s | 1 | 9 | 45.8s |
| skill-flow-ixp-routing-listing/r07 | 73.5s | 1 | 13 | 70.8s |
| skill-flow-ixp-routing-listing/r08 | 58.2s | 1 | 12 | 51.3s |
| skill-flow-ixp-routing-listing/r09 | 54.9s | 1 | 13 | 48.7s |
| skill-flow-ixp-routing-listing/r10 | 58.2s | 1 | 12 | 52.5s |
| skill-flow-add-output | 96.0s | 1 | 18 | 64.1s |
| skill-flow-hitl-quality-brownfield-insert | 446.7s | 1 | 38 | 435.1s |
| skill-flow-feet-inches | 485.3s | 1 | 33 | 428.6s |
| skill-flow-bindings-multi-connector-independence | 467.8s | 1 | 63 | 459.9s |
| skill-flow-non-catalog-http-fallback | 239.5s | 1 | 48 | 235.8s |
| skill-flow-update-node | 60.2s | 1 | 14 | 30.0s |
| skill-flow-devcon-billing-dispute-resolution | 1808.6s | 1 | 165 | 1768.4s |
| skill-flow-cli-dice-roller-simulated | 799.0s | 7 | 89 | 98.9s |
| skill-flow-ipe-complex-array | 648.1s | 1 | 53 | 644.5s |
| skill-flow-ipe-searchable-joins | 345.9s | 1 | 47 | 342.5s |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 1203.0s | 1 | 86 | 1200.1s |
| skill-flow-add-node | 139.6s | 1 | 19 | 101.7s |
| skill-flow-delay | 185.5s | 1 | 24 | 176.4s |
| skill-flow-generic-dynamic-node | 470.0s | 1 | 83 | 426.6s |
| skill-flow-devcon-billing-invoice-lookup | 834.5s | 1 | 68 | 750.3s |
| skill-flow-ipe-multiselect | 456.3s | 1 | 58 | 452.2s |
| skill-flow-transform-group-by | 157.5s | 1 | 23 | 149.5s |
| skill-flow-file-attachment-debug | 233.8s | 1 | 33 | 210.3s |
| skill-flow-ipe-required-groups | 214.5s | 1 | 35 | 209.8s |
| skill-flow-eval-evaluator-type-choice | 171.0s | 1 | 33 | 165.8s |
| skill-flow-ipe-jira-search-triage | 393.3s | 1 | 41 | 354.9s |
| skill-flow-eval-local-crud | 91.3s | 1 | 23 | 87.6s |
| skill-flow-devcon-billing-discrepancy-detector | 1248.7s | 1 | 51 | 1221.2s |
| skill-flow-batch-transform | 192.6s | 1 | 30 | 184.7s |
| skill-flow-ipe-jira-create-issue | 294.6s | 1 | 59 | 262.8s |
| skill-flow-outlook-trigger-inbox | 358.5s | 1 | 67 | 345.5s |
| skill-flow-hitl-smoke-completed-port | 248.2s | 1 | 30 | 240.1s |
| skill-flow-hitl-smoke-node-placed | 157.7s | 1 | 30 | 151.2s |
| skill-flow-devcon-billing-resolution-writer | 317.7s | 1 | 29 | 282.5s |
| skill-flow-ipe-enhanced-enum | 458.8s | 1 | 38 | 456.1s |
| skill-flow-bindings-idempotent-reconfigure | 274.9s | 1 | 53 | 269.3s |
| skill-flow-expense-approval-simulated | 934.4s | 6 | 75 | 139.5s |
| skill-flow-rpa | 260.6s | 1 | 28 | 209.2s |
| skill-flow-loop-multiply | 246.5s | 1 | 32 | 210.3s |
| skill-flow-init-validate | 112.5s | 1 | 27 | 109.7s |
| skill-flow-slack-http-fallback | 271.9s | 1 | 50 | 247.9s |
| skill-flow-move-node | 164.8s | 1 | 21 | 132.7s |
| skill-flow-ipe-path-params | 277.3s | 1 | 59 | 271.9s |
| skill-flow-dice-roller | 150.0s | 1 | 31 | 120.8s |
| skill-flow-hitl-quality-result-downstream | 189.8s | 1 | 28 | 181.5s |
| skill-flow-ixp-e2e-project-selection/aviation | 622.7s | 1 | 63 | 616.7s |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 198.6s | 1 | 31 | 190.1s |
| skill-flow-ipe-dtl-load-by-default-true | 293.5s | 1 | 49 | 291.0s |
| skill-flow-slack-channel-description | 241.5s | 1 | 49 | 211.2s |
| skill-flow-wiki-pageviews | 756.8s | 1 | 25 | 712.9s |
| skill-flow-ixp-invoice-extraction-simulated | 1814.1s | 11 | 225 | 147.5s |
| skill-flow-openmeteo-weather | 239.3s | 1 | 45 | 212.3s |
| skill-flow-outlook-waitfor-email | 299.6s | 1 | 45 | 283.0s |
| skill-flow-customer-escalation | 590.1s | 1 | 93 | 583.1s |
| skill-flow-calculator | 168.0s | 1 | 24 | 139.7s |
| skill-flow-trigger-with-filter | 318.2s | 1 | 42 | 315.2s |
| skill-flow-e2e-devcon-expense-approval | 316.6s | 1 | 34 | 309.2s |
| skill-flow-ipe-dtl-load-by-default-false | 349.9s | 1 | 75 | 346.3s |
| skill-flow-transform-map | 270.4s | 1 | 40 | 259.0s |
| skill-flow-slack-channel-description-simulated | 335.7s | 4 | 42 | 66.4s |
| skill-flow-eval-simulation-crud | 152.0s | 1 | 33 | 148.5s |
| skill-flow-devcon-billing-dispute-analyst | 432.5s | 1 | 58 | 379.4s |
| skill-flow-api-workflow | 130.9s | 1 | 27 | 123.0s |
| skill-flow-hitl-smoke-multi-outcome-routing | 227.1s | 1 | 28 | 217.0s |
| skill-flow-interactive-customer-escalation-triage | 356.7s | 5 | 31 | 53.4s |
| skill-flow-hitl-quality-boolean-decision | 448.4s | 1 | 36 | 440.1s |
| skill-flow-group-to-subflow | 816.4s | 1 | 29 | 790.2s |
| skill-flow-switch | 212.4s | 1 | 32 | 187.2s |
| skill-flow-ipe-query-params | 153.9s | 1 | 28 | 148.9s |
| skill-flow-ipe-ceql-where | 416.1s | 1 | 60 | 412.1s |
| skill-flow-ixp-scaffold-multinode | 562.3s | 1 | 40 | 555.5s |
| skill-flow-bellevue-weather-simulated | 1729.2s | 5 | 130 | 322.4s |
| skill-flow-subflow | 312.3s | 1 | 27 | 288.8s |
| skill-flow-bindings-reconfigure-different-connection | 286.9s | 1 | 42 | 282.3s |
| skill-flow-bindings-no-duplicates | 632.8s | 1 | 102 | 629.2s |
| skill-flow-ipe-generate-schema | 248.7s | 1 | 38 | 246.3s |
| skill-flow-transform-filter | 225.3s | 1 | 27 | 218.6s |
| skill-flow-lowcode-agent | 337.0s | 1 | 40 | 308.5s |
| skill-flow-hitl-schema-design-simulated | 854.7s | 6 | 75 | 119.2s |


## Token Usage

**Total Tokens**: 852,140,222 (input: 230,876, output: 11,051,851)
**Cache Tokens**: write: 46,241,484, read: 794,616,011
**Total Cost**: $578.2608
**Avg Tokens/Task**: 1,392,385

| Task ID | Input (uncached) | Output | Cache Write | Cache Read | Total | Cost |
|---------|------------------|--------|-------------|------------|-------|------|
| skill-flow-inline-agent-robust | 28 | 13,712 | 68,662 | 1,807,276 | 1,889,678 | $1.0054 |
| skill-flow-remove-node | 21 | 7,408 | 37,065 | 1,023,491 | 1,067,985 | $0.5572 |
| skill-flow-decision | 12 | 6,529 | 61,247 | 479,984 | 547,772 | $0.4716 |
| skill-flow-ixp-scaffold-minimal | 2,995 | 27,759 | 79,462 | 760,514 | 870,730 | $0.9515 |
| skill-flow-reading-list | 13 | 8,622 | 64,065 | 629,242 | 701,942 | $0.5584 |
| skill-flow-ipe-drive-to-slack | 20 | 14,703 | 104,750 | 1,589,650 | 1,709,123 | $1.0903 |
| skill-flow-eval-inline-agent | 3,556 | 32,090 | 86,592 | 1,625,200 | 1,747,438 | $1.3043 |
| skill-flow-ipe-jira-get-issue | 24 | 15,805 | 85,808 | 1,734,511 | 1,836,148 | $1.0793 |
| skill-flow-coded-agent | 42 | 8,233 | 46,794 | 2,281,669 | 2,336,738 | $0.9836 |
| skill-flow-ixp-routing-negative/stripe-http | 16 | 7,584 | 59,029 | 806,691 | 873,320 | $0.5772 |
| skill-flow-ixp-routing-negative/slack-summary | 12 | 15,088 | 52,258 | 431,677 | 499,035 | $0.5518 |
| skill-flow-ixp-routing-negative/sf-update | 2,742 | 11,569 | 63,856 | 1,216,111 | 1,294,278 | $0.7861 |
| skill-flow-ixp-routing-negative/http-webhook | 20 | 9,079 | 52,165 | 1,000,511 | 1,061,775 | $0.6320 |
| skill-flow-ixp-routing-negative/gsheet-loop | 18 | 13,960 | 70,993 | 1,070,925 | 1,155,896 | $0.7970 |
| skill-flow-ixp-routing-negative/queue-write | 21 | 7,123 | 43,097 | 969,826 | 1,020,067 | $0.5595 |
| skill-flow-ixp-routing-negative/teams-decision | 18 | 8,680 | 74,450 | 847,922 | 931,070 | $0.6638 |
| skill-flow-ixp-routing-negative/delay-email | 14 | 15,343 | 54,548 | 591,538 | 661,443 | $0.6122 |
| skill-flow-ixp-integration-handle-routing | 19 | 22,801 | 94,686 | 1,269,043 | 1,386,549 | $1.0779 |
| skill-flow-paginated-reference-lookup | 20 | 9,064 | 79,955 | 1,279,888 | 1,368,927 | $0.8198 |
| skill-flow-registry-discovery | 9 | 3,224 | 18,704 | 231,864 | 253,801 | $0.1881 |
| skill-flow-ipe-jira-lifecycle | 18 | 37,281 | 96,323 | 1,192,531 | 1,326,153 | $1.2782 |
| skill-flow-summarize | 4,041 | 8,475 | 46,461 | 411,158 | 470,135 | $0.4368 |
| skill-flow-scheduled-trigger | 15 | 13,795 | 53,595 | 697,743 | 765,148 | $0.6173 |
| skill-flow-slack-weather-pipeline | 1,480 | 60,596 | 179,146 | 2,789,592 | 3,030,814 | $2.4221 |
| skill-flow-eval-no-auto-upload | 16 | 3,031 | 17,758 | 504,531 | 525,336 | $0.2635 |
| skill-flow-ixp-routing/explicit | 17 | 17,134 | 73,662 | 838,297 | 929,110 | $0.7848 |
| skill-flow-ixp-routing/invoice-extraction | 18 | 20,050 | 83,159 | 1,148,964 | 1,252,191 | $0.9573 |
| skill-flow-ixp-routing/receipts | 25 | 14,731 | 78,375 | 1,494,186 | 1,587,317 | $0.9632 |
| skill-flow-ixp-routing/contracts | 14 | 14,849 | 80,724 | 778,437 | 874,024 | $0.7590 |
| skill-flow-ixp-routing/forms-classify | 15 | 19,653 | 78,823 | 707,899 | 806,390 | $0.8028 |
| skill-flow-bellevue-weather | 17 | 30,008 | 68,539 | 946,862 | 1,045,426 | $0.9913 |
| skill-flow-customer-escalation-simulated | 90 | 45,418 | 129,191 | 10,102,728 | 10,277,427 | $4.1968 |
| skill-flow-ipe-enum | 21 | 40,895 | 161,955 | 1,310,002 | 1,512,873 | $1.6138 |
| skill-flow-hitl-quality-schema-design | 23 | 12,394 | 38,998 | 905,220 | 956,635 | $0.6038 |
| skill-flow-webhook-waitfor-parallel | 13 | 10,777 | 73,353 | 640,368 | 724,511 | $0.6289 |
| skill-flow-solution-select-ask | 17 | 3,402 | 29,008 | 449,881 | 482,308 | $0.2948 |
| skill-flow-terminate | 12 | 16,283 | 58,968 | 520,604 | 595,867 | $0.6216 |
| skill-flow-merge-parallel-sync | 12 | 9,710 | 54,935 | 525,508 | 590,165 | $0.5093 |
| skill-flow-multi-city-weather | 15 | 51,420 | 129,975 | 716,573 | 897,983 | $1.4737 |
| skill-flow-ixp-routing-listing/r01 | 12 | 1,930 | 36,218 | 337,898 | 376,058 | $0.2662 |
| skill-flow-ixp-routing-listing/r02 | 11 | 2,898 | 22,777 | 277,831 | 303,517 | $0.2123 |
| skill-flow-ixp-routing-listing/r03 | 9 | 1,927 | 21,850 | 121,003 | 144,789 | $0.1472 |
| skill-flow-ixp-routing-listing/r04 | 9 | 1,886 | 34,977 | 222,404 | 259,276 | $0.2262 |
| skill-flow-ixp-routing-listing/r05 | 9 | 2,191 | 35,034 | 222,529 | 259,763 | $0.2310 |
| skill-flow-ixp-routing-listing/r06 | 11 | 1,858 | 35,114 | 222,880 | 259,863 | $0.2264 |
| skill-flow-ixp-routing-listing/r07 | 13 | 2,356 | 36,366 | 365,133 | 403,868 | $0.2813 |
| skill-flow-ixp-routing-listing/r08 | 12 | 2,543 | 34,786 | 278,755 | 316,096 | $0.2523 |
| skill-flow-ixp-routing-listing/r09 | 9 | 2,406 | 34,967 | 222,394 | 259,776 | $0.2340 |
| skill-flow-ixp-routing-listing/r10 | 9 | 1,988 | 34,972 | 222,384 | 259,353 | $0.2277 |
| skill-flow-add-output | 7 | 1,493 | 29,255 | 230,137 | 260,892 | $0.2012 |
| skill-flow-hitl-quality-brownfield-insert | 23 | 32,559 | 71,026 | 1,443,763 | 1,547,371 | $1.1879 |
| skill-flow-feet-inches | 15 | 21,349 | 61,750 | 713,595 | 796,709 | $0.7659 |
| skill-flow-bindings-multi-connector-independence | 21 | 12,908 | 77,556 | 1,297,518 | 1,388,003 | $0.8738 |
| skill-flow-non-catalog-http-fallback | 21 | 9,600 | 84,419 | 1,381,705 | 1,475,745 | $0.8751 |
| skill-flow-update-node | 480 | 1,974 | 34,962 | 344,661 | 382,077 | $0.2656 |
| skill-flow-devcon-billing-dispute-resolution | 1,622 | 45,291 | 175,722 | 6,467,912 | 6,690,547 | $3.2836 |
| skill-flow-cli-dice-roller-simulated | 1,492 | 14,506 | 42,394 | 381,928 | 440,320 | $0.4956 |
| skill-flow-ipe-complex-array | 20 | 27,754 | 80,447 | 1,230,509 | 1,338,730 | $1.0872 |
| skill-flow-ipe-searchable-joins | 15 | 29,948 | 88,432 | 770,584 | 888,979 | $1.0121 |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 1,550 | 43,719 | 182,761 | 3,660,390 | 3,888,420 | $2.4439 |
| skill-flow-add-node | 9 | 5,290 | 31,997 | 336,200 | 373,496 | $0.3002 |
| skill-flow-delay | 11 | 12,507 | 53,438 | 457,330 | 523,286 | $0.5252 |
| skill-flow-generic-dynamic-node | 31 | 20,535 | 96,185 | 2,501,219 | 2,617,970 | $1.4192 |
| skill-flow-devcon-billing-invoice-lookup | 22 | 41,778 | 178,500 | 1,610,791 | 1,831,091 | $1.7793 |
| skill-flow-ipe-multiselect | 2,158 | 28,513 | 87,853 | 1,559,027 | 1,677,551 | $1.2313 |
| skill-flow-transform-group-by | 11 | 10,435 | 47,423 | 415,339 | 473,208 | $0.4590 |
| skill-flow-file-attachment-debug | 16 | 11,224 | 68,430 | 909,008 | 988,678 | $0.6977 |
| skill-flow-ipe-required-groups | 15 | 9,502 | 75,256 | 806,296 | 891,069 | $0.6667 |
| skill-flow-eval-evaluator-type-choice | 14 | 4,512 | 23,693 | 430,542 | 458,761 | $0.2857 |
| skill-flow-ipe-jira-search-triage | 13 | 14,097 | 104,792 | 687,326 | 806,228 | $0.8107 |
| skill-flow-eval-local-crud | 14 | 12,194 | 39,059 | 601,866 | 653,133 | $0.5100 |
| skill-flow-devcon-billing-discrepancy-detector | 24 | 37,654 | 191,423 | 1,679,090 | 1,908,191 | $1.7864 |
| skill-flow-batch-transform | 11 | 8,631 | 45,858 | 412,734 | 467,234 | $0.4253 |
| skill-flow-ipe-jira-create-issue | 18 | 14,715 | 80,782 | 1,199,001 | 1,294,516 | $0.8834 |
| skill-flow-outlook-trigger-inbox | 19 | 14,061 | 81,145 | 1,223,162 | 1,318,387 | $0.8822 |
| skill-flow-hitl-smoke-completed-port | 16 | 12,245 | 57,080 | 738,145 | 807,486 | $0.6192 |
| skill-flow-hitl-smoke-node-placed | 16 | 10,585 | 63,342 | 731,536 | 805,479 | $0.6158 |
| skill-flow-devcon-billing-resolution-writer | 13 | 18,870 | 74,076 | 644,396 | 737,355 | $0.7542 |
| skill-flow-ipe-enhanced-enum | 17 | 23,917 | 83,260 | 1,002,477 | 1,109,671 | $0.9718 |
| skill-flow-bindings-idempotent-reconfigure | 28 | 38,043 | 67,196 | 1,878,904 | 1,984,171 | $1.3864 |
| skill-flow-expense-approval-simulated | 37 | 30,751 | 97,831 | 2,064,768 | 2,193,387 | $1.4477 |
| skill-flow-rpa | 12 | 8,840 | 54,151 | 522,633 | 585,636 | $0.4925 |
| skill-flow-loop-multiply | 15 | 18,618 | 62,678 | 705,055 | 786,366 | $0.7259 |
| skill-flow-init-validate | 14 | 5,499 | 29,118 | 501,896 | 536,527 | $0.3423 |
| skill-flow-slack-http-fallback | 21 | 7,974 | 91,347 | 1,508,719 | 1,608,061 | $0.9148 |
| skill-flow-move-node | 13 | 8,986 | 38,649 | 567,514 | 615,162 | $0.4500 |
| skill-flow-ipe-path-params | 26 | 16,787 | 98,689 | 2,165,979 | 2,281,481 | $1.2718 |
| skill-flow-dice-roller | 12 | 8,853 | 53,310 | 450,188 | 512,363 | $0.4678 |
| skill-flow-hitl-quality-result-downstream | 20 | 7,812 | 47,379 | 754,028 | 809,239 | $0.5211 |
| skill-flow-ixp-e2e-project-selection/aviation | 29 | 22,899 | 78,709 | 2,028,386 | 2,130,023 | $1.2472 |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 18 | 17,600 | 78,766 | 1,116,397 | 1,212,781 | $0.8943 |
| skill-flow-ipe-dtl-load-by-default-true | 17 | 13,879 | 70,591 | 838,255 | 922,742 | $0.7244 |
| skill-flow-slack-channel-description | 30 | 10,805 | 104,832 | 2,641,857 | 2,757,524 | $1.3478 |
| skill-flow-wiki-pageviews | 14 | 37,656 | 70,156 | 689,084 | 796,910 | $1.0347 |
| skill-flow-ixp-invoice-extraction-simulated | 8,619 | 89,746 | 512,601 | 8,660,527 | 9,271,493 | $5.8925 |
| skill-flow-openmeteo-weather | 17 | 10,121 | 83,341 | 1,108,247 | 1,201,726 | $0.7969 |
| skill-flow-outlook-waitfor-email | 19 | 7,534 | 82,858 | 1,075,893 | 1,166,304 | $0.7466 |
| skill-flow-customer-escalation | 26 | 23,196 | 123,145 | 2,428,984 | 2,575,351 | $1.5385 |
| skill-flow-calculator | 13 | 11,737 | 61,383 | 539,443 | 612,576 | $0.5681 |
| skill-flow-trigger-with-filter | 10 | 5,840 | 35,110 | 337,263 | 378,223 | $0.3205 |
| skill-flow-e2e-devcon-expense-approval | 15 | 19,411 | 67,423 | 778,185 | 865,034 | $0.7775 |
| skill-flow-ipe-dtl-load-by-default-false | 37 | 16,224 | 99,899 | 3,097,053 | 3,213,213 | $1.5472 |
| skill-flow-transform-map | 14 | 12,987 | 47,294 | 621,156 | 681,451 | $0.5585 |
| skill-flow-slack-channel-description-simulated | 41 | 13,748 | 86,658 | 2,478,637 | 2,579,084 | $1.2749 |
| skill-flow-eval-simulation-crud | 36 | 5,920 | 33,958 | 1,573,656 | 1,613,570 | $0.6883 |
| skill-flow-devcon-billing-dispute-analyst | 24 | 15,107 | 84,918 | 1,743,103 | 1,843,152 | $1.0681 |
| skill-flow-api-workflow | 16 | 13,584 | 64,738 | 766,143 | 844,481 | $0.6764 |
| skill-flow-hitl-smoke-multi-outcome-routing | 18 | 19,496 | 62,662 | 890,889 | 973,065 | $0.7947 |
| skill-flow-interactive-customer-escalation-triage | 10,719 | 14,520 | 71,092 | 1,133,344 | 1,229,675 | $0.8566 |
| skill-flow-hitl-quality-boolean-decision | 15 | 20,016 | 71,016 | 682,814 | 773,861 | $0.7714 |
| skill-flow-switch | 17 | 18,327 | 60,234 | 848,195 | 926,773 | $0.7553 |
| skill-flow-ipe-query-params | 14 | 7,508 | 56,378 | 605,977 | 669,877 | $0.5059 |
| skill-flow-ipe-ceql-where | 25 | 28,416 | 114,345 | 2,259,984 | 2,402,770 | $1.5331 |
| skill-flow-ixp-scaffold-multinode | 14 | 24,315 | 78,444 | 756,642 | 859,415 | $0.8859 |
| skill-flow-bellevue-weather-simulated | 4,789 | 30,135 | 76,797 | 2,386,154 | 2,497,875 | $1.4702 |
| skill-flow-subflow | 11 | 13,561 | 47,148 | 411,534 | 472,254 | $0.5037 |
| skill-flow-bindings-reconfigure-different-connection | 27 | 25,645 | 76,564 | 1,768,583 | 1,870,819 | $1.2024 |
| skill-flow-bindings-no-duplicates | 24 | 38,325 | 72,151 | 1,456,729 | 1,567,229 | $1.2825 |
| skill-flow-ipe-generate-schema | 20 | 14,052 | 106,402 | 1,393,321 | 1,513,795 | $1.0278 |
| skill-flow-transform-filter | 11 | 6,531 | 46,767 | 414,253 | 467,562 | $0.3977 |
| skill-flow-lowcode-agent | 20 | 12,762 | 50,264 | 1,009,309 | 1,072,355 | $0.6828 |
| skill-flow-hitl-schema-design-simulated | 37 | 11,613 | 32,359 | 1,158,885 | 1,202,894 | $0.6433 |
| skill-flow-inline-agent-robust | 16 | 25,105 | 71,441 | 820,646 | 917,208 | $0.8907 |
| skill-flow-remove-node | 19 | 7,318 | 36,633 | 891,573 | 935,543 | $0.5147 |
| skill-flow-decision | 13 | 9,033 | 62,646 | 544,193 | 615,885 | $0.5337 |
| skill-flow-ixp-scaffold-minimal | 13 | 21,417 | 71,024 | 676,261 | 768,715 | $0.7905 |
| skill-flow-reading-list | 14 | 11,824 | 64,968 | 732,302 | 809,108 | $0.6407 |
| skill-flow-ipe-drive-to-slack | 23 | 11,092 | 100,700 | 1,923,610 | 2,035,425 | $1.1212 |
| skill-flow-eval-inline-agent | 14 | 37,936 | 80,887 | 830,738 | 949,575 | $1.1216 |
| skill-flow-ipe-jira-get-issue | 21 | 24,999 | 106,600 | 1,668,643 | 1,800,263 | $1.2754 |
| skill-flow-coded-agent | 1,692 | 18,286 | 202,433 | 3,274,342 | 3,496,753 | $2.0208 |
| skill-flow-ixp-routing-negative/stripe-http | 11 | 7,173 | 56,504 | 449,964 | 513,652 | $0.4545 |
| skill-flow-ixp-routing-negative/slack-summary | 86 | 14,444 | 68,336 | 551,302 | 634,168 | $0.6386 |
| skill-flow-ixp-routing-negative/sf-update | 24 | 11,839 | 68,003 | 1,442,977 | 1,522,843 | $0.8656 |
| skill-flow-ixp-routing-negative/http-webhook | 13 | 10,813 | 47,606 | 527,166 | 585,598 | $0.4989 |
| skill-flow-ixp-routing-negative/gsheet-loop | 13 | 24,104 | 72,786 | 612,361 | 709,264 | $0.8183 |
| skill-flow-ixp-routing-negative/queue-write | 27 | 5,545 | 42,430 | 1,366,186 | 1,414,188 | $0.6522 |
| skill-flow-ixp-routing-negative/teams-decision | 20 | 13,566 | 48,830 | 947,104 | 1,009,520 | $0.6708 |
| skill-flow-ixp-routing-negative/delay-email | 15 | 17,294 | 59,048 | 684,563 | 760,920 | $0.6863 |
| skill-flow-ixp-integration-handle-routing | 25 | 35,043 | 81,923 | 1,685,462 | 1,802,453 | $1.3386 |
| skill-flow-paginated-reference-lookup | 20 | 7,604 | 94,971 | 1,418,759 | 1,521,354 | $0.8959 |
| skill-flow-registry-discovery | 15 | 2,881 | 15,702 | 404,858 | 423,456 | $0.2236 |
| skill-flow-ipe-jira-lifecycle | 15 | 42,217 | 103,211 | 901,721 | 1,047,164 | $1.2909 |
| skill-flow-summarize | 11 | 9,867 | 47,316 | 418,356 | 475,550 | $0.4510 |
| skill-flow-scheduled-trigger | 16 | 10,339 | 47,141 | 699,195 | 756,691 | $0.5417 |
| skill-flow-slack-weather-pipeline | 42 | 64,178 | 138,496 | 4,519,459 | 4,722,175 | $2.8380 |
| skill-flow-eval-no-auto-upload | 14 | 2,493 | 16,976 | 426,499 | 445,982 | $0.2290 |
| skill-flow-ixp-routing/explicit | 54 | 24,108 | 77,202 | 3,944,355 | 4,045,719 | $1.8346 |
| skill-flow-ixp-routing/invoice-extraction | 24 | 19,560 | 91,670 | 1,712,200 | 1,823,454 | $1.1509 |
| skill-flow-ixp-routing/receipts | 24 | 13,399 | 78,993 | 1,486,695 | 1,579,111 | $0.9433 |
| skill-flow-ixp-routing/contracts | 16 | 17,980 | 87,552 | 849,714 | 955,262 | $0.8530 |
| skill-flow-ixp-routing/forms-classify | 18 | 12,404 | 75,186 | 914,681 | 1,002,289 | $0.7425 |
| skill-flow-bellevue-weather | 14 | 27,429 | 62,578 | 660,956 | 750,977 | $0.8444 |
| skill-flow-customer-escalation-simulated | 2,954 | 59,278 | 193,447 | 6,471,737 | 6,727,416 | $3.5650 |
| skill-flow-ipe-enum | 26 | 25,211 | 82,095 | 1,818,269 | 1,925,601 | $1.2316 |
| skill-flow-hitl-quality-schema-design | 50 | 18,056 | 53,132 | 2,687,387 | 2,758,625 | $1.2765 |
| skill-flow-webhook-waitfor-parallel | 22 | 13,263 | 79,510 | 1,280,111 | 1,372,906 | $0.8812 |
| skill-flow-solution-select-ask | 18 | 4,695 | 36,741 | 551,776 | 593,230 | $0.3738 |
| skill-flow-terminate | 18 | 16,067 | 69,518 | 967,645 | 1,053,248 | $0.7920 |
| skill-flow-merge-parallel-sync | 12 | 8,964 | 55,849 | 531,449 | 596,274 | $0.5034 |
| skill-flow-multi-city-weather | 23 | 53,717 | 74,252 | 1,474,395 | 1,602,387 | $1.5266 |
| skill-flow-ixp-routing-listing/r01 | 10 | 2,092 | 35,043 | 277,812 | 314,957 | $0.2462 |
| skill-flow-ixp-routing-listing/r02 | 9 | 2,048 | 34,969 | 222,374 | 259,400 | $0.2286 |
| skill-flow-ixp-routing-listing/r03 | 12 | 2,039 | 35,131 | 278,223 | 315,405 | $0.2458 |
| skill-flow-ixp-routing-listing/r04 | 9 | 2,142 | 35,006 | 222,524 | 259,681 | $0.2302 |
| skill-flow-ixp-routing-listing/r05 | 8 | 1,193 | 6,405 | 188,437 | 196,043 | $0.0985 |
| skill-flow-ixp-routing-listing/r06 | 7 | 3,307 | 21,762 | 120,876 | 145,952 | $0.1675 |
| skill-flow-ixp-routing-listing/r07 | 18 | 3,549 | 41,641 | 574,926 | 620,134 | $0.3819 |
| skill-flow-ixp-routing-listing/r08 | 11 | 1,964 | 35,108 | 222,860 | 259,943 | $0.2280 |
| skill-flow-ixp-routing-listing/r09 | 14 | 1,855 | 36,311 | 338,314 | 376,494 | $0.2655 |
| skill-flow-ixp-routing-listing/r10 | 9 | 2,659 | 34,960 | 222,384 | 260,012 | $0.2377 |
| skill-flow-add-output | 8 | 1,687 | 29,547 | 282,248 | 313,490 | $0.2208 |
| skill-flow-hitl-quality-brownfield-insert | 17 | 21,579 | 68,516 | 961,840 | 1,051,952 | $0.8692 |
| skill-flow-feet-inches | 12 | 17,147 | 66,642 | 536,307 | 620,108 | $0.6680 |
| skill-flow-bindings-multi-connector-independence | 26 | 12,587 | 79,517 | 1,874,447 | 1,966,577 | $1.0494 |
| skill-flow-non-catalog-http-fallback | 17 | 8,129 | 85,400 | 1,070,752 | 1,164,298 | $0.7635 |
| skill-flow-update-node | 7 | 1,995 | 29,746 | 230,200 | 261,948 | $0.2106 |
| skill-flow-devcon-billing-dispute-resolution | 4,407 | 83,665 | 208,700 | 6,211,455 | 6,508,227 | $3.9143 |
| skill-flow-cli-dice-roller-simulated | 29 | 14,619 | 69,586 | 1,004,292 | 1,088,526 | $0.7816 |
| skill-flow-ipe-complex-array | 22 | 27,822 | 102,312 | 1,796,201 | 1,926,357 | $1.3399 |
| skill-flow-ipe-searchable-joins | 17 | 18,270 | 76,315 | 914,201 | 1,008,803 | $0.8345 |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 35 | 63,337 | 233,991 | 2,834,298 | 3,131,661 | $2.6779 |
| skill-flow-add-node | 10 | 5,433 | 35,932 | 396,874 | 438,249 | $0.3353 |
| skill-flow-delay | 14 | 8,650 | 45,250 | 592,604 | 646,518 | $0.4773 |
| skill-flow-generic-dynamic-node | 38 | 19,652 | 100,999 | 3,279,594 | 3,400,283 | $1.6575 |
| skill-flow-devcon-billing-invoice-lookup | 45 | 39,079 | 187,054 | 2,620,729 | 2,846,907 | $2.0740 |
| skill-flow-ipe-multiselect | 22 | 19,083 | 80,068 | 1,412,357 | 1,511,530 | $1.0103 |
| skill-flow-transform-group-by | 12 | 11,284 | 48,622 | 480,238 | 540,156 | $0.4957 |
| skill-flow-file-attachment-debug | 2,324 | 6,751 | 57,680 | 673,323 | 740,078 | $0.5265 |
| skill-flow-ipe-required-groups | 18 | 9,330 | 72,221 | 985,608 | 1,067,177 | $0.7065 |
| skill-flow-eval-evaluator-type-choice | 12 | 3,387 | 31,905 | 375,200 | 410,504 | $0.2830 |
| skill-flow-ipe-jira-search-triage | 20 | 25,387 | 94,309 | 1,365,943 | 1,485,659 | $1.1443 |
| skill-flow-eval-local-crud | 12 | 6,028 | 38,750 | 483,991 | 528,781 | $0.3810 |
| skill-flow-devcon-billing-discrepancy-detector | 30 | 35,274 | 105,276 | 2,658,949 | 2,799,529 | $1.7217 |
| skill-flow-batch-transform | 11 | 7,499 | 45,786 | 412,340 | 465,636 | $0.4079 |
| skill-flow-ipe-jira-create-issue | 15 | 13,561 | 82,139 | 922,119 | 1,017,834 | $0.7881 |
| skill-flow-outlook-trigger-inbox | 34 | 10,421 | 100,161 | 2,724,038 | 2,834,654 | $1.3492 |
| skill-flow-hitl-smoke-completed-port | 14 | 10,823 | 63,818 | 624,826 | 699,481 | $0.5892 |
| skill-flow-hitl-smoke-node-placed | 15 | 9,467 | 63,880 | 702,730 | 776,092 | $0.5924 |
| skill-flow-devcon-billing-resolution-writer | 12 | 19,881 | 75,609 | 587,284 | 682,786 | $0.7580 |
| skill-flow-ipe-enhanced-enum | 21 | 22,684 | 74,607 | 1,322,324 | 1,419,636 | $1.0168 |
| skill-flow-bindings-idempotent-reconfigure | 24 | 14,116 | 80,167 | 1,720,212 | 1,814,519 | $1.0285 |
| skill-flow-expense-approval-simulated | 59 | 52,194 | 130,915 | 4,231,883 | 4,415,051 | $2.5436 |
| skill-flow-rpa | 14 | 7,787 | 62,983 | 707,783 | 778,567 | $0.5654 |
| skill-flow-loop-multiply | 12 | 19,686 | 63,878 | 583,755 | 667,331 | $0.7100 |
| skill-flow-init-validate | 12 | 4,486 | 28,913 | 401,545 | 434,956 | $0.2962 |
| skill-flow-slack-http-fallback | 24 | 9,013 | 112,792 | 2,087,023 | 2,208,852 | $1.1843 |
| skill-flow-move-node | 11 | 9,218 | 39,191 | 464,087 | 512,507 | $0.4245 |
| skill-flow-ipe-path-params | 28 | 13,704 | 90,201 | 2,240,890 | 2,344,823 | $1.2162 |
| skill-flow-dice-roller | 13 | 9,696 | 52,573 | 496,127 | 558,409 | $0.4915 |
| skill-flow-hitl-quality-result-downstream | 22 | 10,557 | 33,387 | 861,153 | 905,119 | $0.5420 |
| skill-flow-ixp-e2e-project-selection/aviation | 20 | 23,698 | 89,016 | 1,249,732 | 1,362,466 | $1.0643 |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 16 | 21,930 | 79,016 | 960,459 | 1,061,421 | $0.9134 |
| skill-flow-ipe-dtl-load-by-default-true | 15 | 8,410 | 60,376 | 723,700 | 792,501 | $0.5697 |
| skill-flow-slack-channel-description | 23 | 9,536 | 80,212 | 1,658,422 | 1,748,193 | $0.9414 |
| skill-flow-ixp-invoice-extraction-simulated | 8,247 | 105,775 | 460,144 | 10,383,228 | 10,957,394 | $6.4519 |
| skill-flow-openmeteo-weather | 17 | 16,672 | 76,892 | 1,069,817 | 1,163,398 | $0.8594 |
| skill-flow-outlook-waitfor-email | 20 | 10,989 | 83,165 | 1,198,180 | 1,292,354 | $0.8362 |
| skill-flow-customer-escalation | 10,912 | 41,261 | 169,519 | 2,984,310 | 3,206,002 | $2.1826 |
| skill-flow-calculator | 12 | 8,477 | 61,932 | 502,957 | 573,378 | $0.5103 |
| skill-flow-trigger-with-filter | 8 | 4,586 | 28,624 | 222,105 | 255,323 | $0.2428 |
| skill-flow-e2e-devcon-expense-approval | 12 | 21,447 | 68,511 | 556,138 | 646,108 | $0.7455 |
| skill-flow-ipe-dtl-load-by-default-false | 36 | 16,093 | 116,224 | 3,389,114 | 3,521,467 | $1.6941 |
| skill-flow-transform-map | 14 | 10,456 | 48,124 | 623,618 | 682,212 | $0.5244 |
| skill-flow-slack-channel-description-simulated | 44 | 20,017 | 110,802 | 2,960,519 | 3,091,382 | $1.6041 |
| skill-flow-eval-simulation-crud | 38 | 12,155 | 28,235 | 1,589,121 | 1,629,549 | $0.7651 |
| skill-flow-devcon-billing-dispute-analyst | 21 | 14,916 | 76,332 | 1,374,358 | 1,465,627 | $0.9224 |
| skill-flow-api-workflow | 15 | 12,710 | 57,330 | 702,116 | 772,171 | $0.6163 |
| skill-flow-hitl-smoke-multi-outcome-routing | 14 | 18,747 | 52,914 | 554,116 | 625,791 | $0.6459 |
| skill-flow-interactive-customer-escalation-triage | 19 | 12,588 | 75,016 | 853,154 | 940,777 | $0.7261 |
| skill-flow-hitl-quality-boolean-decision | 12 | 18,334 | 62,965 | 530,360 | 611,671 | $0.6703 |
| skill-flow-group-to-subflow | 18 | 46,633 | 61,788 | 973,530 | 1,081,969 | $1.2233 |
| skill-flow-switch | 12 | 19,942 | 51,818 | 431,886 | 503,658 | $0.6230 |
| skill-flow-ipe-query-params | 15 | 5,488 | 53,768 | 664,118 | 723,389 | $0.4832 |
| skill-flow-ipe-ceql-where | 19 | 33,367 | 102,796 | 1,290,886 | 1,427,068 | $1.2733 |
| skill-flow-ixp-scaffold-multinode | 15 | 28,720 | 83,516 | 805,639 | 917,890 | $0.9857 |
| skill-flow-bellevue-weather-simulated | 27 | 23,016 | 93,714 | 1,485,934 | 1,602,691 | $1.1425 |
| skill-flow-subflow | 13 | 15,104 | 58,781 | 599,570 | 673,468 | $0.6269 |
| skill-flow-bindings-reconfigure-different-connection | 28 | 9,281 | 78,986 | 1,893,411 | 1,981,706 | $1.0035 |
| skill-flow-bindings-no-duplicates | 24 | 18,559 | 71,558 | 1,492,199 | 1,582,340 | $0.9945 |
| skill-flow-ipe-generate-schema | 26 | 11,736 | 91,389 | 2,042,806 | 2,145,957 | $1.1317 |
| skill-flow-transform-filter | 11 | 12,378 | 46,837 | 413,854 | 473,080 | $0.4855 |
| skill-flow-lowcode-agent | 17 | 12,561 | 51,798 | 814,434 | 878,810 | $0.6270 |
| skill-flow-hitl-schema-design-simulated | 43 | 19,824 | 42,099 | 1,554,894 | 1,616,860 | $0.9218 |
| skill-flow-inline-agent-robust | 17 | 16,224 | 69,264 | 974,627 | 1,060,132 | $0.7955 |
| skill-flow-remove-node | 18 | 6,552 | 37,872 | 834,378 | 878,820 | $0.4907 |
| skill-flow-decision | 11 | 13,021 | 61,078 | 478,743 | 552,853 | $0.5680 |
| skill-flow-ixp-scaffold-minimal | 16 | 25,001 | 75,833 | 809,074 | 909,924 | $0.9022 |
| skill-flow-reading-list | 12 | 12,011 | 63,476 | 555,095 | 630,594 | $0.5848 |
| skill-flow-ipe-drive-to-slack | 26 | 11,240 | 101,633 | 2,254,086 | 2,366,985 | $1.2260 |
| skill-flow-eval-inline-agent | 16 | 25,723 | 79,438 | 1,028,470 | 1,133,647 | $0.9923 |
| skill-flow-ipe-jira-get-issue | 25 | 10,947 | 87,709 | 1,831,028 | 1,929,709 | $1.0425 |
| skill-flow-coded-agent | 42 | 14,937 | 111,972 | 3,333,884 | 3,460,835 | $1.6442 |
| skill-flow-ixp-routing-negative/stripe-http | 16 | 9,476 | 56,910 | 795,286 | 861,688 | $0.5942 |
| skill-flow-ixp-routing-negative/slack-summary | 19 | 18,585 | 70,778 | 1,171,155 | 1,260,537 | $0.8956 |
| skill-flow-ixp-routing-negative/sf-update | 16 | 5,852 | 53,047 | 707,057 | 765,972 | $0.4989 |
| skill-flow-ixp-routing-negative/http-webhook | 21 | 7,904 | 56,493 | 1,166,814 | 1,231,232 | $0.6805 |
| skill-flow-ixp-routing-negative/gsheet-loop | 14 | 10,270 | 55,334 | 598,069 | 663,687 | $0.5410 |
| skill-flow-ixp-routing-negative/queue-write | 19 | 6,789 | 42,366 | 866,133 | 915,307 | $0.5206 |
| skill-flow-ixp-routing-negative/teams-decision | 16 | 9,861 | 51,824 | 718,207 | 779,908 | $0.5578 |
| skill-flow-ixp-routing-negative/delay-email | 13 | 7,092 | 48,440 | 517,500 | 573,045 | $0.4433 |
| skill-flow-ixp-integration-handle-routing | 24 | 49,462 | 92,738 | 1,739,239 | 1,881,463 | $1.6115 |
| skill-flow-paginated-reference-lookup | 22 | 8,720 | 94,979 | 1,572,394 | 1,676,115 | $0.9588 |
| skill-flow-registry-discovery | 15 | 2,933 | 15,672 | 404,588 | 423,208 | $0.2242 |
| skill-flow-ipe-jira-lifecycle | 19 | 52,102 | 104,729 | 1,345,960 | 1,502,810 | $1.5781 |
| skill-flow-summarize | 12 | 9,686 | 47,738 | 423,521 | 480,957 | $0.4514 |
| skill-flow-scheduled-trigger | 19 | 12,743 | 50,855 | 909,924 | 973,541 | $0.6549 |
| skill-flow-slack-weather-pipeline | 19 | 75,583 | 123,199 | 1,641,937 | 1,840,738 | $2.0884 |
| skill-flow-eval-no-auto-upload | 15 | 2,558 | 17,115 | 465,517 | 485,205 | $0.2423 |
| skill-flow-ixp-routing/explicit | 19 | 9,920 | 55,213 | 927,265 | 992,417 | $0.6341 |
| skill-flow-ixp-routing/invoice-extraction | 26 | 13,213 | 89,059 | 1,943,371 | 2,045,669 | $1.1153 |
| skill-flow-ixp-routing/receipts | 71 | 38,845 | 104,380 | 6,306,019 | 6,449,315 | $2.8661 |
| skill-flow-ixp-routing/contracts | 23 | 18,937 | 89,093 | 1,552,673 | 1,660,726 | $1.0840 |
| skill-flow-ixp-routing/forms-classify | 21 | 9,290 | 74,424 | 1,210,399 | 1,294,134 | $0.7816 |
| skill-flow-bellevue-weather | 751 | 21,097 | 61,703 | 506,583 | 590,134 | $0.7021 |
| skill-flow-customer-escalation-simulated | 12,307 | 105,879 | 359,321 | 8,269,897 | 8,747,404 | $5.4535 |
| skill-flow-ipe-enum | 18 | 21,327 | 76,656 | 998,052 | 1,096,053 | $0.9068 |
| skill-flow-hitl-quality-schema-design | 20 | 17,154 | 48,979 | 884,562 | 950,715 | $0.7064 |
| skill-flow-webhook-waitfor-parallel | 21 | 13,768 | 86,110 | 1,490,755 | 1,590,654 | $0.9767 |
| skill-flow-solution-select-ask | 17 | 2,809 | 36,217 | 485,019 | 524,062 | $0.3235 |
| skill-flow-terminate | 14 | 16,689 | 60,119 | 613,909 | 690,731 | $0.6600 |
| skill-flow-merge-parallel-sync | 11 | 6,208 | 55,295 | 466,455 | 527,969 | $0.4404 |
| skill-flow-multi-city-weather | 18 | 66,310 | 131,293 | 833,662 | 1,031,283 | $1.7372 |
| skill-flow-ixp-routing-listing/r01 | 14 | 3,668 | 28,401 | 283,370 | 315,453 | $0.2466 |
| skill-flow-ixp-routing-listing/r02 | 8 | 3,091 | 32,846 | 160,077 | 196,022 | $0.2176 |
| skill-flow-ixp-routing-listing/r03 | 11 | 2,222 | 35,054 | 222,704 | 259,991 | $0.2316 |
| skill-flow-ixp-routing-listing/r04 | 9 | 1,983 | 34,970 | 222,404 | 259,366 | $0.2276 |
| skill-flow-ixp-routing-listing/r05 | 11 | 1,572 | 7,464 | 274,253 | 283,300 | $0.1339 |
| skill-flow-ixp-routing-listing/r06 | 12 | 2,404 | 35,149 | 278,300 | 315,865 | $0.2514 |
| skill-flow-ixp-routing-listing/r07 | 17 | 3,884 | 22,118 | 495,250 | 521,269 | $0.2898 |
| skill-flow-ixp-routing-listing/r08 | 12 | 2,208 | 35,241 | 278,598 | 316,059 | $0.2489 |
| skill-flow-ixp-routing-listing/r09 | 11 | 1,747 | 35,089 | 222,826 | 259,673 | $0.2247 |
| skill-flow-ixp-routing-listing/r10 | 10 | 2,646 | 35,054 | 277,817 | 315,527 | $0.2545 |
| skill-flow-add-output | 8 | 2,002 | 29,950 | 258,660 | 290,620 | $0.2200 |
| skill-flow-hitl-quality-brownfield-insert | 52 | 14,719 | 48,693 | 2,677,765 | 2,741,229 | $1.2069 |
| skill-flow-feet-inches | 21 | 29,506 | 70,543 | 1,224,853 | 1,324,923 | $1.0746 |
| skill-flow-bindings-multi-connector-independence | 23 | 20,352 | 79,856 | 1,512,138 | 1,612,369 | $1.0585 |
| skill-flow-non-catalog-http-fallback | 18 | 10,800 | 89,273 | 1,120,127 | 1,220,218 | $0.8329 |
| skill-flow-update-node | 10 | 3,159 | 31,170 | 387,465 | 421,804 | $0.2805 |
| skill-flow-devcon-billing-dispute-resolution | 10,502 | 80,818 | 207,641 | 3,231,545 | 3,530,506 | $2.9919 |
| skill-flow-cli-dice-roller-simulated | 34 | 13,779 | 62,301 | 1,300,856 | 1,376,970 | $0.8307 |
| skill-flow-ipe-complex-array | 26 | 33,499 | 105,891 | 2,032,934 | 2,172,350 | $1.5095 |
| skill-flow-ipe-searchable-joins | 15 | 17,890 | 84,862 | 803,282 | 906,049 | $0.8276 |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 4,727 | 30,679 | 189,518 | 5,414,554 | 5,639,478 | $2.8094 |
| skill-flow-add-node | 13 | 9,527 | 35,519 | 557,088 | 602,147 | $0.4433 |
| skill-flow-delay | 12 | 5,276 | 43,248 | 404,806 | 453,342 | $0.3628 |
| skill-flow-generic-dynamic-node | 33 | 23,959 | 100,824 | 2,699,658 | 2,824,474 | $1.5475 |
| skill-flow-devcon-billing-invoice-lookup | 41 | 22,235 | 115,681 | 4,055,533 | 4,193,490 | $1.9841 |
| skill-flow-ipe-multiselect | 15 | 22,621 | 82,614 | 816,982 | 922,232 | $0.8943 |
| skill-flow-transform-group-by | 19 | 10,254 | 55,387 | 963,885 | 1,029,545 | $0.6507 |
| skill-flow-file-attachment-debug | 17 | 7,522 | 63,721 | 875,257 | 946,517 | $0.6144 |
| skill-flow-ipe-required-groups | 21 | 10,275 | 65,328 | 1,122,978 | 1,198,602 | $0.7361 |
| skill-flow-eval-evaluator-type-choice | 26 | 5,020 | 25,659 | 1,026,928 | 1,057,633 | $0.4797 |
| skill-flow-ipe-jira-search-triage | 20 | 24,620 | 98,223 | 1,261,501 | 1,384,364 | $1.1161 |
| skill-flow-eval-local-crud | 13 | 3,153 | 40,334 | 552,150 | 595,650 | $0.3642 |
| skill-flow-devcon-billing-discrepancy-detector | 25 | 56,499 | 109,801 | 1,999,549 | 2,165,874 | $1.8592 |
| skill-flow-batch-transform | 12 | 9,892 | 46,315 | 415,755 | 471,974 | $0.4468 |
| skill-flow-ipe-jira-create-issue | 18 | 14,111 | 80,480 | 1,077,277 | 1,171,886 | $0.8367 |
| skill-flow-outlook-trigger-inbox | 21 | 17,298 | 82,203 | 1,281,044 | 1,380,566 | $0.9521 |
| skill-flow-hitl-smoke-completed-port | 13 | 12,455 | 59,394 | 523,396 | 595,258 | $0.5666 |
| skill-flow-hitl-smoke-node-placed | 22 | 15,059 | 61,137 | 1,292,093 | 1,368,311 | $0.8428 |
| skill-flow-devcon-billing-resolution-writer | 15 | 19,076 | 85,310 | 887,005 | 991,406 | $0.8722 |
| skill-flow-ipe-enhanced-enum | 24 | 13,674 | 79,621 | 1,676,403 | 1,769,722 | $1.0067 |
| skill-flow-bindings-idempotent-reconfigure | 37 | 36,958 | 79,188 | 2,872,847 | 2,989,030 | $1.7133 |
| skill-flow-expense-approval-simulated | 24 | 22,483 | 95,589 | 1,330,879 | 1,448,975 | $1.0950 |
| skill-flow-rpa | 20 | 12,121 | 49,634 | 939,034 | 1,000,809 | $0.6497 |
| skill-flow-loop-multiply | 15 | 14,065 | 64,291 | 693,510 | 771,881 | $0.6602 |
| skill-flow-init-validate | 14 | 6,749 | 28,558 | 490,886 | 526,207 | $0.3556 |
| skill-flow-slack-http-fallback | 20 | 12,422 | 94,628 | 1,443,720 | 1,550,790 | $0.9744 |
| skill-flow-move-node | 7 | 27,504 | 49,130 | 248,339 | 324,980 | $0.6713 |
| skill-flow-ipe-path-params | 24 | 15,115 | 87,654 | 1,671,596 | 1,774,389 | $1.0570 |
| skill-flow-dice-roller | 12 | 7,202 | 50,990 | 439,995 | 498,199 | $0.4313 |
| skill-flow-hitl-quality-result-downstream | 15 | 7,922 | 51,932 | 573,436 | 633,305 | $0.4857 |
| skill-flow-ixp-e2e-project-selection/aviation | 21 | 20,824 | 80,567 | 1,418,991 | 1,520,403 | $1.0402 |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 25 | 20,105 | 76,751 | 1,583,581 | 1,680,462 | $1.0645 |
| skill-flow-ipe-dtl-load-by-default-true | 16 | 11,617 | 67,186 | 794,969 | 873,788 | $0.6647 |
| skill-flow-slack-channel-description | 23 | 8,514 | 80,959 | 1,598,292 | 1,687,788 | $0.9109 |
| skill-flow-wiki-pageviews | 14 | 43,415 | 77,584 | 692,059 | 813,072 | $1.1498 |
| skill-flow-ixp-invoice-extraction-simulated | 1,719 | 67,022 | 248,519 | 11,112,264 | 11,429,524 | $5.2761 |
| skill-flow-openmeteo-weather | 21 | 8,704 | 81,463 | 1,459,841 | 1,550,029 | $0.8741 |
| skill-flow-outlook-waitfor-email | 18 | 11,444 | 77,406 | 950,154 | 1,039,022 | $0.7470 |
| skill-flow-customer-escalation | 40 | 52,435 | 220,209 | 3,705,323 | 3,978,007 | $2.7240 |
| skill-flow-calculator | 14 | 8,962 | 60,689 | 609,501 | 679,166 | $0.5449 |
| skill-flow-trigger-with-filter | 9 | 8,479 | 33,112 | 277,998 | 319,598 | $0.3348 |
| skill-flow-e2e-devcon-expense-approval | 16 | 32,922 | 76,800 | 886,186 | 995,924 | $1.0477 |
| skill-flow-ipe-dtl-load-by-default-false | 41 | 15,811 | 105,031 | 3,850,115 | 3,970,998 | $1.7862 |
| skill-flow-transform-map | 15 | 14,665 | 46,103 | 671,468 | 732,251 | $0.5943 |
| skill-flow-slack-channel-description-simulated | 22,820 | 80,404 | 314,973 | 6,351,119 | 6,769,316 | $4.3610 |
| skill-flow-eval-simulation-crud | 37 | 6,322 | 31,360 | 1,639,335 | 1,677,054 | $0.7043 |
| skill-flow-devcon-billing-dispute-analyst | 23 | 29,952 | 93,935 | 1,679,396 | 1,803,306 | $1.3054 |
| skill-flow-api-workflow | 17 | 10,104 | 60,441 | 847,055 | 917,617 | $0.6324 |
| skill-flow-hitl-smoke-multi-outcome-routing | 13 | 18,562 | 73,383 | 627,675 | 719,633 | $0.7420 |
| skill-flow-interactive-customer-escalation-triage | 26 | 22,299 | 73,714 | 1,273,169 | 1,369,208 | $0.9929 |
| skill-flow-hitl-quality-boolean-decision | 12 | 17,179 | 66,367 | 560,349 | 643,907 | $0.6747 |
| skill-flow-group-to-subflow | 17 | 64,136 | 116,977 | 662,831 | 843,961 | $1.5996 |
| skill-flow-switch | 15 | 15,345 | 55,303 | 619,387 | 690,050 | $0.6234 |
| skill-flow-ipe-query-params | 12 | 7,537 | 52,475 | 482,190 | 542,214 | $0.4545 |
| skill-flow-ipe-ceql-where | 24 | 24,326 | 97,334 | 1,819,398 | 1,941,082 | $1.2758 |
| skill-flow-ixp-scaffold-multinode | 14 | 24,279 | 83,268 | 793,265 | 900,826 | $0.9145 |
| skill-flow-bellevue-weather-simulated | 777 | 36,977 | 74,156 | 1,759,560 | 1,871,470 | $1.3629 |
| skill-flow-subflow | 12 | 14,886 | 57,137 | 514,002 | 586,037 | $0.5918 |
| skill-flow-bindings-reconfigure-different-connection | 24 | 34,002 | 70,628 | 1,480,507 | 1,585,161 | $1.2191 |
| skill-flow-bindings-no-duplicates | 19 | 29,926 | 66,185 | 1,121,818 | 1,217,948 | $1.0337 |
| skill-flow-ipe-generate-schema | 25 | 8,941 | 86,694 | 1,838,196 | 1,933,856 | $1.0108 |
| skill-flow-transform-filter | 15 | 8,587 | 53,494 | 699,254 | 761,350 | $0.5392 |
| skill-flow-lowcode-agent | 13 | 13,584 | 49,942 | 537,067 | 600,606 | $0.5522 |
| skill-flow-hitl-schema-design-simulated | 22 | 21,759 | 73,056 | 874,834 | 969,671 | $0.8629 |
| skill-flow-inline-agent-robust | 13 | 25,062 | 69,394 | 621,794 | 716,263 | $0.8227 |
| skill-flow-remove-node | 19 | 5,842 | 37,424 | 904,349 | 947,634 | $0.4993 |
| skill-flow-decision | 13 | 15,375 | 61,491 | 549,410 | 626,289 | $0.6261 |
| skill-flow-ixp-scaffold-minimal | 20 | 28,816 | 73,650 | 1,227,968 | 1,330,454 | $1.0769 |
| skill-flow-reading-list | 12 | 12,856 | 63,663 | 555,295 | 631,826 | $0.5982 |
| skill-flow-ipe-drive-to-slack | 26 | 16,183 | 117,808 | 2,370,955 | 2,504,972 | $1.3959 |
| skill-flow-eval-inline-agent | 16 | 20,308 | 79,614 | 990,146 | 1,090,084 | $0.9003 |
| skill-flow-ipe-jira-get-issue | 25 | 16,223 | 117,282 | 2,259,909 | 2,393,439 | $1.3612 |
| skill-flow-coded-agent | 42 | 11,908 | 110,851 | 3,128,579 | 3,251,380 | $1.5330 |
| skill-flow-ixp-routing-negative/stripe-http | 16 | 8,377 | 57,630 | 801,454 | 867,477 | $0.5823 |
| skill-flow-ixp-routing-negative/slack-summary | 22 | 20,170 | 74,286 | 1,350,642 | 1,445,120 | $0.9864 |
| skill-flow-ixp-routing-negative/sf-update | 14 | 8,562 | 73,682 | 742,843 | 825,101 | $0.6276 |
| skill-flow-ixp-routing-negative/http-webhook | 23 | 14,100 | 57,209 | 1,234,300 | 1,305,632 | $0.7964 |
| skill-flow-ixp-routing-negative/gsheet-loop | 19 | 8,188 | 59,551 | 987,777 | 1,055,535 | $0.6425 |
| skill-flow-ixp-routing-negative/queue-write | 24 | 7,975 | 44,957 | 1,120,947 | 1,173,903 | $0.6246 |
| skill-flow-ixp-routing-negative/teams-decision | 13 | 8,556 | 49,330 | 515,546 | 573,445 | $0.4680 |
| skill-flow-ixp-routing-negative/delay-email | 13 | 15,184 | 65,635 | 578,781 | 659,613 | $0.6476 |
| skill-flow-ixp-integration-handle-routing | 14 | 29,363 | 70,890 | 755,601 | 855,868 | $0.9330 |
| skill-flow-paginated-reference-lookup | 25 | 11,834 | 105,595 | 1,971,970 | 2,089,424 | $1.1652 |
| skill-flow-registry-discovery | 8 | 2,639 | 21,089 | 185,175 | 208,911 | $0.1742 |
| skill-flow-ipe-jira-lifecycle | 17 | 34,686 | 90,915 | 1,063,953 | 1,189,571 | $1.1805 |
| skill-flow-summarize | 11 | 10,080 | 47,051 | 417,457 | 474,599 | $0.4529 |
| skill-flow-scheduled-trigger | 17 | 12,596 | 58,330 | 864,164 | 935,107 | $0.6670 |
| skill-flow-slack-weather-pipeline | 27 | 52,721 | 186,172 | 2,536,917 | 2,775,837 | $2.2501 |
| skill-flow-eval-no-auto-upload | 18 | 3,031 | 17,708 | 585,385 | 606,142 | $0.2875 |
| skill-flow-ixp-routing/explicit | 17 | 9,213 | 70,761 | 832,002 | 911,993 | $0.6532 |
| skill-flow-ixp-routing/invoice-extraction | 26 | 23,070 | 111,396 | 2,260,581 | 2,395,073 | $1.4420 |
| skill-flow-ixp-routing/receipts | 37 | 13,474 | 78,640 | 2,601,731 | 2,693,882 | $1.2776 |
| skill-flow-ixp-routing/contracts | 24 | 13,065 | 90,534 | 1,635,828 | 1,739,451 | $1.0263 |
| skill-flow-ixp-routing/forms-classify | 23 | 8,038 | 57,379 | 1,169,788 | 1,235,228 | $0.6867 |
| skill-flow-bellevue-weather | 15 | 30,561 | 71,194 | 751,313 | 853,083 | $0.9508 |
| skill-flow-customer-escalation-simulated | 1,689 | 62,058 | 189,576 | 5,082,333 | 5,335,656 | $3.1715 |
| skill-flow-ipe-enum | 15 | 19,960 | 88,570 | 803,621 | 912,166 | $0.8727 |
| skill-flow-hitl-quality-schema-design | 31 | 14,201 | 50,847 | 1,353,967 | 1,419,046 | $0.8100 |
| skill-flow-webhook-waitfor-parallel | 21 | 10,738 | 101,938 | 1,655,434 | 1,768,131 | $1.0400 |
| skill-flow-solution-select-ask | 17 | 3,696 | 36,669 | 511,961 | 552,343 | $0.3466 |
| skill-flow-terminate | 24 | 30,535 | 62,131 | 1,309,743 | 1,402,433 | $1.0840 |
| skill-flow-merge-parallel-sync | 11 | 5,889 | 55,720 | 467,813 | 529,433 | $0.4377 |
| skill-flow-multi-city-weather | 12 | 25,197 | 64,506 | 519,049 | 608,764 | $0.7756 |
| skill-flow-ixp-routing-listing/r01 | 15 | 2,287 | 39,781 | 446,364 | 488,447 | $0.3174 |
| skill-flow-ixp-routing-listing/r02 | 7 | 2,650 | 26,524 | 120,861 | 150,042 | $0.1755 |
| skill-flow-ixp-routing-listing/r03 | 12 | 2,177 | 35,164 | 278,383 | 315,736 | $0.2481 |
| skill-flow-ixp-routing-listing/r04 | 9 | 2,031 | 34,966 | 222,404 | 259,410 | $0.2283 |
| skill-flow-ixp-routing-listing/r05 | 8 | 2,802 | 26,155 | 153,576 | 182,541 | $0.1862 |
| skill-flow-ixp-routing-listing/r06 | 9 | 2,030 | 35,070 | 222,628 | 259,737 | $0.2288 |
| skill-flow-ixp-routing-listing/r07 | 8 | 2,624 | 22,576 | 148,821 | 174,029 | $0.1687 |
| skill-flow-ixp-routing-listing/r08 | 11 | 1,968 | 34,693 | 223,050 | 259,722 | $0.2266 |
| skill-flow-ixp-routing-listing/r09 | 9 | 2,009 | 34,964 | 222,394 | 259,376 | $0.2280 |
| skill-flow-ixp-routing-listing/r10 | 9 | 2,725 | 21,907 | 121,087 | 145,728 | $0.1594 |
| skill-flow-add-output | 7 | 1,602 | 29,299 | 230,115 | 261,023 | $0.2030 |
| skill-flow-hitl-quality-brownfield-insert | 17 | 17,840 | 72,736 | 947,790 | 1,038,383 | $0.8247 |
| skill-flow-feet-inches | 20 | 23,135 | 69,175 | 1,202,757 | 1,295,087 | $0.9673 |
| skill-flow-bindings-multi-connector-independence | 30 | 31,085 | 81,533 | 2,159,759 | 2,272,407 | $1.4200 |
| skill-flow-non-catalog-http-fallback | 3,614 | 8,993 | 88,932 | 832,668 | 934,207 | $0.7290 |
| skill-flow-update-node | 11 | 1,731 | 35,812 | 346,023 | 383,577 | $0.2641 |
| skill-flow-devcon-billing-dispute-resolution | 1,608 | 52,762 | 184,280 | 5,034,082 | 5,272,732 | $2.9975 |
| skill-flow-cli-dice-roller-simulated | 32 | 13,172 | 63,141 | 1,202,927 | 1,279,272 | $0.7953 |
| skill-flow-ipe-complex-array | 22 | 30,371 | 83,800 | 1,491,689 | 1,605,882 | $1.2174 |
| skill-flow-ipe-searchable-joins | 15 | 29,129 | 83,873 | 790,067 | 903,084 | $0.9885 |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 1,983 | 47,528 | 166,479 | 6,354,523 | 6,570,513 | $3.2495 |
| skill-flow-add-node | 11 | 7,091 | 36,489 | 449,975 | 493,566 | $0.3782 |
| skill-flow-delay | 11 | 12,820 | 43,929 | 359,659 | 416,419 | $0.4650 |
| skill-flow-generic-dynamic-node | 33 | 21,449 | 101,313 | 2,793,471 | 2,916,266 | $1.5398 |
| skill-flow-devcon-billing-invoice-lookup | 21 | 44,904 | 102,167 | 1,715,293 | 1,862,385 | $1.5713 |
| skill-flow-ipe-multiselect | 22 | 17,323 | 99,538 | 1,669,055 | 1,785,938 | $1.1339 |
| skill-flow-transform-group-by | 11 | 13,851 | 47,680 | 415,901 | 477,443 | $0.5114 |
| skill-flow-file-attachment-debug | 15 | 9,956 | 65,682 | 799,501 | 875,154 | $0.6355 |
| skill-flow-ipe-required-groups | 18 | 12,743 | 75,234 | 1,112,056 | 1,200,051 | $0.8069 |
| skill-flow-eval-evaluator-type-choice | 10 | 4,574 | 24,538 | 300,118 | 329,240 | $0.2507 |
| skill-flow-ipe-jira-search-triage | 15 | 23,549 | 118,436 | 972,218 | 1,114,218 | $1.0891 |
| skill-flow-eval-local-crud | 10 | 4,387 | 36,522 | 357,748 | 398,667 | $0.3101 |
| skill-flow-devcon-billing-discrepancy-detector | 29 | 66,948 | 193,002 | 2,213,060 | 2,473,039 | $2.3920 |
| skill-flow-batch-transform | 13 | 8,728 | 47,016 | 547,411 | 603,168 | $0.4715 |
| skill-flow-ipe-jira-create-issue | 27 | 20,476 | 97,071 | 2,210,083 | 2,327,657 | $1.3343 |
| skill-flow-outlook-trigger-inbox | 15 | 16,389 | 81,402 | 760,966 | 858,772 | $0.7794 |
| skill-flow-hitl-smoke-completed-port | 12 | 10,931 | 60,877 | 467,343 | 539,163 | $0.5325 |
| skill-flow-hitl-smoke-node-placed | 24 | 9,035 | 30,861 | 871,769 | 911,689 | $0.5129 |
| skill-flow-devcon-billing-resolution-writer | 13 | 16,165 | 83,551 | 689,918 | 789,647 | $0.7628 |
| skill-flow-ipe-enhanced-enum | 19 | 24,021 | 75,997 | 1,177,330 | 1,277,367 | $0.9986 |
| skill-flow-bindings-idempotent-reconfigure | 27 | 21,808 | 73,070 | 1,755,040 | 1,849,945 | $1.1277 |
| skill-flow-expense-approval-simulated | 43 | 46,227 | 116,054 | 2,741,474 | 2,903,798 | $1.9512 |
| skill-flow-rpa | 22 | 10,610 | 54,038 | 999,804 | 1,064,474 | $0.6618 |
| skill-flow-loop-multiply | 13 | 15,724 | 52,279 | 559,112 | 627,128 | $0.5997 |
| skill-flow-init-validate | 16 | 5,560 | 31,891 | 616,273 | 653,740 | $0.3879 |
| skill-flow-slack-http-fallback | 17 | 10,373 | 96,905 | 1,162,052 | 1,269,347 | $0.8677 |
| skill-flow-move-node | 6 | 22,870 | 48,263 | 197,303 | 268,442 | $0.5832 |
| skill-flow-ipe-path-params | 20 | 9,345 | 110,985 | 1,569,492 | 1,689,842 | $1.0273 |
| skill-flow-dice-roller | 13 | 11,246 | 54,929 | 567,908 | 634,096 | $0.5451 |
| skill-flow-hitl-quality-result-downstream | 15 | 15,966 | 66,392 | 674,171 | 756,544 | $0.6908 |
| skill-flow-ixp-e2e-project-selection/aviation | 23 | 13,649 | 80,392 | 1,510,781 | 1,604,845 | $0.9595 |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 23 | 20,328 | 72,253 | 1,356,926 | 1,449,530 | $0.9830 |
| skill-flow-ipe-dtl-load-by-default-true | 17 | 7,314 | 70,678 | 915,799 | 993,808 | $0.6495 |
| skill-flow-slack-channel-description | 22 | 10,041 | 88,940 | 1,615,631 | 1,714,634 | $0.9689 |
| skill-flow-wiki-pageviews | 753 | 50,299 | 87,834 | 802,815 | 941,701 | $1.3270 |
| skill-flow-ixp-invoice-extraction-simulated | 7,055 | 84,682 | 228,261 | 5,099,870 | 5,419,868 | $3.6773 |
| skill-flow-openmeteo-weather | 24 | 8,703 | 85,022 | 1,703,414 | 1,797,163 | $0.9605 |
| skill-flow-outlook-waitfor-email | 20 | 10,425 | 79,696 | 1,162,168 | 1,252,309 | $0.8039 |
| skill-flow-customer-escalation | 10,924 | 48,192 | 208,112 | 3,334,167 | 3,601,395 | $2.5363 |
| skill-flow-calculator | 13 | 9,963 | 61,816 | 516,135 | 587,927 | $0.5361 |
| skill-flow-trigger-with-filter | 35 | 14,030 | 58,589 | 2,020,402 | 2,093,056 | $1.0364 |
| skill-flow-e2e-devcon-expense-approval | 15 | 14,651 | 69,382 | 711,911 | 795,959 | $0.6936 |
| skill-flow-ipe-dtl-load-by-default-false | 26 | 10,548 | 106,877 | 1,983,077 | 2,100,528 | $1.1540 |
| skill-flow-transform-map | 13 | 10,880 | 45,744 | 541,648 | 598,285 | $0.4973 |
| skill-flow-slack-channel-description-simulated | 36 | 14,873 | 93,575 | 2,260,409 | 2,368,893 | $1.2522 |
| skill-flow-eval-simulation-crud | 30 | 7,637 | 29,319 | 1,248,355 | 1,285,341 | $0.5991 |
| skill-flow-devcon-billing-dispute-analyst | 30 | 18,851 | 88,651 | 2,311,746 | 2,419,278 | $1.3088 |
| skill-flow-api-workflow | 657 | 15,623 | 90,690 | 1,831,206 | 1,938,176 | $1.1258 |
| skill-flow-hitl-smoke-multi-outcome-routing | 13 | 15,790 | 52,919 | 481,976 | 550,698 | $0.5799 |
| skill-flow-interactive-customer-escalation-triage | 19 | 12,520 | 61,226 | 756,413 | 830,178 | $0.6444 |
| skill-flow-hitl-quality-boolean-decision | 13 | 17,596 | 63,165 | 585,210 | 665,984 | $0.6764 |
| skill-flow-switch | 14 | 16,832 | 62,991 | 623,070 | 702,907 | $0.6757 |
| skill-flow-ipe-query-params | 13 | 5,887 | 53,813 | 545,960 | 605,673 | $0.4539 |
| skill-flow-ipe-ceql-where | 19 | 25,192 | 94,495 | 1,315,091 | 1,434,797 | $1.1268 |
| skill-flow-ixp-scaffold-multinode | 15 | 34,565 | 84,790 | 888,680 | 1,008,050 | $1.1031 |
| skill-flow-bellevue-weather-simulated | 30,182 | 71,269 | 250,691 | 6,404,624 | 6,756,766 | $4.0211 |
| skill-flow-subflow | 12 | 10,364 | 49,486 | 481,295 | 541,157 | $0.4855 |
| skill-flow-bindings-reconfigure-different-connection | 25 | 11,333 | 85,088 | 1,766,964 | 1,863,410 | $1.0192 |
| skill-flow-bindings-no-duplicates | 26 | 28,619 | 75,873 | 1,705,411 | 1,809,929 | $1.2255 |
| skill-flow-ipe-generate-schema | 22 | 10,871 | 95,056 | 1,668,484 | 1,774,433 | $1.0201 |
| skill-flow-transform-filter | 10 | 8,425 | 46,819 | 360,377 | 415,631 | $0.4101 |
| skill-flow-lowcode-agent | 21 | 16,024 | 57,292 | 1,050,611 | 1,123,948 | $0.7705 |
| skill-flow-hitl-schema-design-simulated | 32 | 16,152 | 40,689 | 1,069,844 | 1,126,717 | $0.7159 |
| skill-flow-inline-agent-robust | 20 | 17,844 | 72,873 | 1,254,583 | 1,345,320 | $0.9174 |
| skill-flow-remove-node | 17 | 5,563 | 35,936 | 782,993 | 824,509 | $0.4532 |
| skill-flow-decision | 12 | 10,557 | 51,378 | 431,229 | 493,176 | $0.4804 |
| skill-flow-ixp-scaffold-minimal | 16 | 30,632 | 68,477 | 832,365 | 931,490 | $0.9660 |
| skill-flow-reading-list | 14 | 14,479 | 65,067 | 732,505 | 812,065 | $0.6810 |
| skill-flow-ipe-drive-to-slack | 22 | 10,320 | 95,580 | 1,695,968 | 1,801,890 | $1.0221 |
| skill-flow-eval-inline-agent | 17 | 31,151 | 89,525 | 1,067,369 | 1,188,062 | $1.1232 |
| skill-flow-ipe-jira-get-issue | 21 | 11,000 | 105,891 | 1,742,556 | 1,859,468 | $1.0849 |
| skill-flow-coded-agent | 42 | 12,318 | 84,228 | 2,506,538 | 2,603,126 | $1.2527 |
| skill-flow-ixp-routing-negative/stripe-http | 19 | 6,326 | 58,153 | 1,005,657 | 1,070,155 | $0.6147 |
| skill-flow-ixp-routing-negative/slack-summary | 13 | 20,509 | 71,360 | 639,988 | 731,870 | $0.7673 |
| skill-flow-ixp-routing-negative/sf-update | 18 | 12,520 | 57,905 | 911,692 | 982,135 | $0.6785 |
| skill-flow-ixp-routing-negative/http-webhook | 21 | 9,848 | 52,815 | 1,067,160 | 1,129,844 | $0.6660 |
| skill-flow-ixp-routing-negative/gsheet-loop | 19 | 17,873 | 73,566 | 1,174,009 | 1,265,467 | $0.8962 |
| skill-flow-ixp-routing-negative/queue-write | 26 | 8,281 | 45,940 | 1,317,308 | 1,371,555 | $0.6918 |
| skill-flow-ixp-routing-negative/teams-decision | 13 | 8,483 | 45,493 | 527,218 | 581,207 | $0.4560 |
| skill-flow-ixp-routing-negative/delay-email | 14 | 15,088 | 69,098 | 648,610 | 732,810 | $0.6801 |
| skill-flow-ixp-integration-handle-routing | 20 | 25,655 | 84,117 | 1,304,229 | 1,414,021 | $1.0916 |
| skill-flow-paginated-reference-lookup | 20 | 8,908 | 78,638 | 1,173,932 | 1,261,498 | $0.7808 |
| skill-flow-registry-discovery | 7 | 2,428 | 20,119 | 148,908 | 171,462 | $0.1566 |
| skill-flow-ipe-jira-lifecycle | 17 | 31,424 | 84,827 | 1,038,322 | 1,154,590 | $1.1010 |
| skill-flow-summarize | 11 | 9,363 | 47,408 | 418,800 | 475,582 | $0.4439 |
| skill-flow-scheduled-trigger | 13 | 13,484 | 52,918 | 513,330 | 579,745 | $0.5547 |
| skill-flow-slack-weather-pipeline | 42 | 39,542 | 79,673 | 3,272,312 | 3,391,569 | $1.8737 |
| skill-flow-eval-no-auto-upload | 15 | 2,920 | 17,188 | 465,408 | 485,531 | $0.2479 |
| skill-flow-ixp-routing/explicit | 17 | 20,257 | 78,428 | 860,351 | 959,053 | $0.8561 |
| skill-flow-ixp-routing/invoice-extraction | 26 | 12,895 | 98,222 | 1,962,406 | 2,073,549 | $1.1506 |
| skill-flow-ixp-routing/receipts | 22 | 8,905 | 57,809 | 1,128,138 | 1,194,874 | $0.6889 |
| skill-flow-ixp-routing/contracts | 14 | 18,506 | 81,200 | 673,792 | 773,512 | $0.7843 |
| skill-flow-ixp-routing/forms-classify | 20 | 8,717 | 55,496 | 986,204 | 1,050,437 | $0.6348 |
| skill-flow-bellevue-weather | 17 | 22,923 | 63,888 | 920,760 | 1,007,588 | $0.8597 |
| skill-flow-customer-escalation-simulated | 9,250 | 105,703 | 271,725 | 9,578,408 | 9,965,086 | $5.5058 |
| skill-flow-ipe-enum | 18 | 25,822 | 93,525 | 1,101,915 | 1,221,280 | $1.0687 |
| skill-flow-hitl-quality-schema-design | 12 | 21,659 | 55,975 | 484,465 | 562,111 | $0.6802 |
| skill-flow-webhook-waitfor-parallel | 21 | 10,299 | 75,605 | 1,333,809 | 1,419,734 | $0.8382 |
| skill-flow-solution-select-ask | 18 | 3,564 | 36,716 | 551,809 | 592,107 | $0.3567 |
| skill-flow-terminate | 16 | 20,911 | 73,729 | 868,894 | 963,550 | $0.8509 |
| skill-flow-merge-parallel-sync | 12 | 6,214 | 54,007 | 521,389 | 581,622 | $0.4522 |
| skill-flow-multi-city-weather | 17 | 45,998 | 133,537 | 836,218 | 1,015,770 | $1.4417 |
| skill-flow-ixp-routing-listing/r01 | 7 | 864 | 6,627 | 161,168 | 168,666 | $0.0862 |
| skill-flow-ixp-routing-listing/r02 | 10 | 1,504 | 35,045 | 277,806 | 314,365 | $0.2374 |
| skill-flow-ixp-routing-listing/r03 | 11 | 2,085 | 35,059 | 222,704 | 259,859 | $0.2296 |
| skill-flow-ixp-routing-listing/r04 | 9 | 1,955 | 34,981 | 222,404 | 259,349 | $0.2273 |
| skill-flow-ixp-routing-listing/r05 | 8 | 1,349 | 6,946 | 189,131 | 197,434 | $0.1030 |
| skill-flow-ixp-routing-listing/r06 | 9 | 2,526 | 21,913 | 121,070 | 145,518 | $0.1564 |
| skill-flow-ixp-routing-listing/r07 | 9 | 3,508 | 22,869 | 176,397 | 202,783 | $0.1913 |
| skill-flow-ixp-routing-listing/r08 | 11 | 2,070 | 35,132 | 222,932 | 260,145 | $0.2297 |
| skill-flow-ixp-routing-listing/r09 | 10 | 1,923 | 35,046 | 277,830 | 314,809 | $0.2436 |
| skill-flow-ixp-routing-listing/r10 | 10 | 1,932 | 35,064 | 277,827 | 314,833 | $0.2438 |
| skill-flow-add-output | 13 | 2,129 | 33,103 | 552,327 | 587,572 | $0.3218 |
| skill-flow-hitl-quality-brownfield-insert | 20 | 27,306 | 73,139 | 1,265,120 | 1,365,585 | $1.0635 |
| skill-flow-feet-inches | 16 | 27,894 | 67,519 | 762,780 | 858,209 | $0.9005 |
| skill-flow-bindings-multi-connector-independence | 30 | 26,299 | 94,369 | 2,413,460 | 2,534,158 | $1.4725 |
| skill-flow-non-catalog-http-fallback | 64 | 11,270 | 80,362 | 1,270,467 | 1,362,163 | $0.8517 |
| skill-flow-update-node | 9 | 1,775 | 29,614 | 334,595 | 365,993 | $0.2381 |
| skill-flow-devcon-billing-dispute-resolution | 5,777 | 109,572 | 331,724 | 6,307,474 | 6,754,547 | $4.7971 |
| skill-flow-cli-dice-roller-simulated | 62 | 20,477 | 129,046 | 4,274,802 | 4,424,387 | $2.0737 |
| skill-flow-ipe-complex-array | 23 | 37,548 | 89,856 | 1,590,498 | 1,717,925 | $1.3774 |
| skill-flow-ipe-searchable-joins | 19 | 18,516 | 85,547 | 1,297,498 | 1,401,580 | $0.9878 |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 42 | 77,146 | 237,640 | 4,162,575 | 4,477,403 | $3.2972 |
| skill-flow-add-node | 11 | 8,174 | 33,752 | 443,194 | 485,131 | $0.3822 |
| skill-flow-delay | 11 | 11,445 | 44,509 | 412,516 | 468,481 | $0.4624 |
| skill-flow-generic-dynamic-node | 49 | 16,212 | 97,624 | 4,150,613 | 4,264,498 | $1.8546 |
| skill-flow-devcon-billing-invoice-lookup | 27 | 43,299 | 113,139 | 2,401,114 | 2,557,579 | $1.7942 |
| skill-flow-ipe-multiselect | 26 | 26,944 | 101,834 | 2,064,128 | 2,192,932 | $1.4054 |
| skill-flow-transform-group-by | 11 | 7,308 | 47,355 | 414,790 | 469,464 | $0.4117 |
| skill-flow-file-attachment-debug | 14 | 10,163 | 65,738 | 727,357 | 803,272 | $0.6172 |
| skill-flow-ipe-required-groups | 14 | 9,633 | 67,547 | 599,373 | 676,567 | $0.5777 |
| skill-flow-eval-evaluator-type-choice | 24 | 7,916 | 31,016 | 1,044,239 | 1,083,195 | $0.5484 |
| skill-flow-ipe-jira-search-triage | 15 | 20,226 | 96,607 | 873,728 | 990,576 | $0.9278 |
| skill-flow-eval-local-crud | 12 | 2,478 | 29,979 | 434,750 | 467,219 | $0.2801 |
| skill-flow-devcon-billing-discrepancy-detector | 23 | 79,696 | 270,673 | 1,328,539 | 1,678,931 | $2.6091 |
| skill-flow-batch-transform | 13 | 9,869 | 47,028 | 547,624 | 604,534 | $0.4887 |
| skill-flow-ipe-jira-create-issue | 27 | 11,710 | 89,339 | 2,080,506 | 2,181,582 | $1.1349 |
| skill-flow-outlook-trigger-inbox | 26 | 11,965 | 93,174 | 2,029,865 | 2,135,030 | $1.1379 |
| skill-flow-hitl-smoke-completed-port | 13 | 15,494 | 51,110 | 480,055 | 546,672 | $0.5681 |
| skill-flow-hitl-smoke-node-placed | 12 | 7,531 | 56,995 | 515,420 | 579,958 | $0.4814 |
| skill-flow-devcon-billing-resolution-writer | 13 | 18,297 | 81,270 | 721,686 | 821,266 | $0.7958 |
| skill-flow-ipe-enhanced-enum | 15 | 26,822 | 81,054 | 825,628 | 933,519 | $0.9540 |
| skill-flow-bindings-idempotent-reconfigure | 28 | 11,389 | 78,278 | 1,992,830 | 2,082,525 | $1.0623 |
| skill-flow-expense-approval-simulated | 53 | 43,569 | 114,180 | 4,211,092 | 4,368,894 | $2.3452 |
| skill-flow-rpa | 13 | 13,263 | 53,428 | 531,587 | 598,291 | $0.5588 |
| skill-flow-loop-multiply | 14 | 11,543 | 53,254 | 564,051 | 628,862 | $0.5421 |
| skill-flow-init-validate | 13 | 4,805 | 28,986 | 451,292 | 485,096 | $0.3162 |
| skill-flow-slack-http-fallback | 21 | 10,125 | 98,218 | 1,538,195 | 1,646,559 | $0.9817 |
| skill-flow-move-node | 12 | 11,047 | 37,390 | 509,774 | 558,223 | $0.4589 |
| skill-flow-ipe-path-params | 27 | 11,736 | 110,617 | 2,564,774 | 2,687,154 | $1.3604 |
| skill-flow-dice-roller | 755 | 5,544 | 49,550 | 698,129 | 753,978 | $0.4807 |
| skill-flow-hitl-quality-result-downstream | 15 | 10,297 | 68,110 | 690,208 | 768,630 | $0.6170 |
| skill-flow-ixp-e2e-project-selection/aviation | 29 | 40,677 | 82,375 | 2,007,605 | 2,130,686 | $1.5214 |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 15 | 10,626 | 78,290 | 824,519 | 913,450 | $0.7004 |
| skill-flow-ipe-dtl-load-by-default-true | 22 | 13,482 | 69,693 | 1,287,850 | 1,371,047 | $0.8500 |
| skill-flow-slack-channel-description | 21 | 9,045 | 91,888 | 1,481,557 | 1,582,511 | $0.9248 |
| skill-flow-wiki-pageviews | 13 | 46,740 | 121,479 | 507,977 | 676,209 | $1.3091 |
| skill-flow-ixp-invoice-extraction-simulated | 11,052 | 87,777 | 325,820 | 11,631,327 | 12,055,976 | $6.0610 |
| skill-flow-openmeteo-weather | 16 | 9,824 | 79,827 | 1,010,599 | 1,100,266 | $0.7499 |
| skill-flow-outlook-waitfor-email | 24 | 11,264 | 79,703 | 1,478,971 | 1,569,962 | $0.9116 |
| skill-flow-customer-escalation | 39 | 33,228 | 136,259 | 4,158,067 | 4,327,593 | $2.2569 |
| skill-flow-calculator | 11 | 8,549 | 51,055 | 390,361 | 449,976 | $0.4368 |
| skill-flow-trigger-with-filter | 23 | 13,404 | 63,703 | 1,262,376 | 1,339,506 | $0.8187 |
| skill-flow-e2e-devcon-expense-approval | 11 | 19,853 | 81,929 | 563,457 | 665,250 | $0.7741 |
| skill-flow-ipe-dtl-load-by-default-false | 32 | 15,618 | 105,619 | 2,574,420 | 2,695,689 | $1.4028 |
| skill-flow-transform-map | 17 | 12,998 | 66,117 | 995,466 | 1,074,598 | $0.7416 |
| skill-flow-slack-channel-description-simulated | 28 | 11,670 | 78,122 | 1,326,027 | 1,415,847 | $0.8659 |
| skill-flow-eval-simulation-crud | 20 | 5,645 | 32,113 | 820,823 | 858,601 | $0.4514 |
| skill-flow-devcon-billing-dispute-analyst | 24 | 21,610 | 97,038 | 1,989,319 | 2,107,991 | $1.2849 |
| skill-flow-api-workflow | 15 | 6,407 | 54,465 | 660,801 | 721,688 | $0.4986 |
| skill-flow-hitl-smoke-multi-outcome-routing | 13 | 13,775 | 54,643 | 490,169 | 558,600 | $0.5586 |
| skill-flow-interactive-customer-escalation-triage | 23 | 16,899 | 117,831 | 791,996 | 926,749 | $0.9330 |
| skill-flow-hitl-quality-boolean-decision | 15 | 29,571 | 71,101 | 717,971 | 818,658 | $0.9256 |
| skill-flow-group-to-subflow | 17 | 63,690 | 136,609 | 877,023 | 1,077,339 | $1.7308 |
| skill-flow-switch | 14 | 10,960 | 62,622 | 633,392 | 706,988 | $0.5893 |
| skill-flow-ipe-query-params | 11 | 6,490 | 52,603 | 382,924 | 442,028 | $0.4095 |
| skill-flow-ipe-ceql-where | 28 | 21,629 | 86,111 | 2,132,842 | 2,240,610 | $1.2873 |
| skill-flow-ixp-scaffold-multinode | 17 | 34,913 | 79,728 | 1,049,327 | 1,163,985 | $1.1375 |
| skill-flow-bellevue-weather-simulated | 4,202 | 64,566 | 226,418 | 4,638,984 | 4,934,170 | $3.2219 |
| skill-flow-subflow | 12 | 18,570 | 58,407 | 560,053 | 637,042 | $0.6656 |
| skill-flow-bindings-reconfigure-different-connection | 21 | 14,033 | 70,552 | 1,125,389 | 1,209,995 | $0.8127 |
| skill-flow-bindings-no-duplicates | 53 | 33,957 | 96,436 | 4,504,893 | 4,635,339 | $2.2226 |
| skill-flow-ipe-generate-schema | 15 | 11,352 | 79,078 | 788,152 | 878,597 | $0.7033 |
| skill-flow-transform-filter | 13 | 12,457 | 48,216 | 550,424 | 611,110 | $0.5328 |
| skill-flow-lowcode-agent | 20 | 18,830 | 57,285 | 1,086,654 | 1,162,789 | $0.8233 |
| skill-flow-hitl-schema-design-simulated | 39 | 46,319 | 90,595 | 2,297,264 | 2,434,217 | $1.7238 |


## Command Telemetry

**Total Commands**: 15122
**Success Rate**: 14538/15122 (96.1%)

### Commands by Tool

| Tool | Count | % |
|------|-------|---|
| Bash | 7904 | 52.3% |
| Read | 4210 | 27.8% |
| Edit | 1442 | 9.5% |
| Skill | 656 | 4.3% |
| Write | 418 | 2.8% |
| TaskUpdate | 217 | 1.4% |
| TaskCreate | 112 | 0.7% |
| Glob | 80 | 0.5% |
| Grep | 72 | 0.5% |
| TaskOutput | 4 | 0.0% |
| Agent | 3 | 0.0% |
| TaskStop | 2 | 0.0% |
| WebFetch | 2 | 0.0% |

### Performance

- **Average Command Time**: 4490.7ms
- **Total Command Time**: 67908.26s

### Slowest Commands

| Tool | Duration | Parameters |
|------|----------|------------|
| TaskOutput | 300074ms | {'task_id': 'ba62z5vwg', 'block': True, 'timeout':... |
| TaskOutput | 300013ms | {'task_id': 'bp5mt9jb6', 'block': True, 'timeout':... |
| Agent | 184893ms | {'description': 'Discover UiPath project structure... |
| TaskOutput | 180023ms | {'task_id': 'bp5mt9jb6', 'block': True, 'timeout':... |
| Agent | 129963ms | {'description': 'Look up flow wiring JSON shapes f... |

**Most Common Pattern**: `Bash → Bash → Bash`

**Skill Tool Invoked**: 656 time(s)

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
- **cli_version**: 1.199.0-dev.7923 | 1.199.0-dev.7970
- **tool_plugins**: {'admin-tool': '1.199.0-dev.7962', 'agent-tool': '1.199.0-dev.7923 | 1.199.0-dev.7965', 'agenthub-tool': '1.199.0-dev.7923 | 1.199.0-dev.7962', 'aops-tool': '1.199.0-dev.7962', 'api-workflow-tool': '1.199.0-dev.7962', 'codedagent-tool': '1.199.0-dev.7923 | 1.199.0-dev.7965', 'codedapp-tool': '1.199.0-dev.7962', 'coder-tool': '1.199.0-dev.7962', 'context-grounding-tool': '1.199.0-dev.7962', 'conversational-tool': '1.199.0-dev.7962', 'data-fabric-tool': '1.199.0-dev.7923 | 1.199.0-dev.7962', 'docsai-tool': '1.199.0-dev.7962', 'functions-tool': '1.199.0-dev.7923 | 1.199.0-dev.7962', 'gov-tool': '1.199.0-dev.7923 | 1.199.0-dev.7962', 'insights-tool': '1.199.0-dev.7923 | 1.199.0-dev.7962', 'integrationservice-tool': '1.199.0-dev.7923 | 1.199.0-dev.7962', 'ixp-tool': '1.199.0-dev.7923 | 1.199.0-dev.7962', 'llm-gateway-tool': '1.199.0-dev.7962', 'llmgw-tool': '1.199.0-dev.7962', 'maestro-tool': '1.199.0-dev.7924 | 1.199.0-dev.7962', 'orchestrator-tool': '1.199.0-dev.7923 | 1.199.0-dev.7962', 'platform-tool': '1.199.0-dev.7962', 'pm-tool': '1.199.0-dev.7969', 'rpa-legacy-tool': '1.199.0-dev.7962', 'rpa-tool': '1.199.0-dev.20260722.4', 'solution-tool': '1.199.0-dev.7923 | 1.199.0-dev.7962', 'tasks-tool': '1.199.0-dev.7923 | 1.199.0-dev.7962', 'test-manager-tool': '1.199.0-dev.7923 | 1.199.0-dev.7962', 'traces-tool': '1.199.0-dev.7962', 'vertical-solutions-tool': '1.199.0-dev.7962'}
- **coder_eval**: 0.8.8
- **claude_code_cli**: 2.1.219 (Claude Code)
- **uv**: uv 0.11.21 (x86_64-unknown-linux-gnu)
- **anthropic**: 0.102.0
- **openai**: Not Installed
- **pydantic**: 2.12.5