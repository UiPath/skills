# Evaluation Run Report

**Run ID**: `maestro-flow-baseline-report-1`
**Date**: 2026-07-23 20:42:10
**Duration**: 2599.00s
**Model**: `claude-sonnet-4-6`

## Summary

- **Total Tasks**: 123
- **Succeeded**: 111
- **Failed**: 11
- **Errors**: 1
- **Success Rate**: 91.0%
- **Avg Reliability Score**: 0.934
- **Avg Generation Latency**: 376.5s
- **Total Assistant Turns**: 5321
- **Crashed Partials**: 1 (0 recovered, 1 terminal)

## Task Details

| Task ID | Status | Reliability Score | Latency | Model | Tags |
|---------|--------|-------------------|---------|-------|------|
| skill-flow-ipe-path-params | SUCCESS | 1.000 | 284.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-hitl-schema-design-simulated | SUCCESS | 1.000 | 594.3s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, simulation |
| skill-flow-ixp-routing-negative/stripe-http | SUCCESS | 1.000 | 212.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/slack-summary | SUCCESS | 1.000 | 244.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/sf-update | SUCCESS | 1.000 | 260.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/http-webhook | SUCCESS | 1.000 | 316.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/gsheet-loop | SUCCESS | 1.000 | 358.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/queue-write | SUCCESS | 1.000 | 242.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/teams-decision | SUCCESS | 1.000 | 236.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/delay-email | SUCCESS | 1.000 | 222.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-non-catalog-http-fallback | SUCCESS | 1.000 | 240.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, connector, uipath-uipath-http, feature:http, ipe |
| skill-flow-expense-approval-simulated | SUCCESS | 1.000 | 1025.9s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, e2e, mode:build, lifecycle:generate, devcon, simulation |
| skill-flow-eval-no-auto-upload | SUCCESS | 1.000 | 129.2s | claude-sonnet-4-6 | uipath-maestro-flow, mode:operate, lifecycle:execute, feature:eval |
| skill-flow-devcon-billing-dispute-analyst | FAILURE | 0.375 | 531.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, path-to-ga |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | SUCCESS | 1.000 | 736.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:ixp, connector, feature:http |
| skill-flow-e2e-devcon-expense-approval | SUCCESS | 1.000 | 324.4s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, e2e, devcon |
| skill-flow-calculator | SUCCESS | 1.000 | 249.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node |
| skill-flow-ipe-generate-schema | SUCCESS | 1.000 | 265.6s | claude-sonnet-4-6 | uipath-platform, integration, lifecycle:generate, shape:multi-node, connector, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-dice-roller | SUCCESS | 1.000 | 210.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node |
| skill-flow-update-node | SUCCESS | 1.000 | 96.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:decision |
| skill-flow-eval-simulation-crud | SUCCESS | 1.000 | 168.8s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, feature:eval |
| skill-flow-init-validate | SUCCESS | 1.000 | 140.1s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, lifecycle:generate |
| skill-flow-hitl-smoke-multi-outcome-routing | SUCCESS | 1.000 | 293.3s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-hitl-smoke-node-placed | SUCCESS | 1.000 | 231.4s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, lifecycle:generate, shape:single-node, node:hitl |
| skill-flow-outlook-trigger-inbox | SUCCESS | 1.000 | 280.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, feature:trigger, connector, mode:build, ipe |
| skill-flow-bindings-reconfigure-different-connection | SUCCESS | 1.000 | 546.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-wiki-pageviews | TIMEOUT | 0.000 | 911.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:transform, feature:http |
| skill-flow-add-node | SUCCESS | 1.000 | 213.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:edit, shape:multi-node |
| skill-flow-transform-filter | SUCCESS | 1.000 | 210.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-merge-parallel-sync | SUCCESS | 1.000 | 210.2s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:multi-node, node:merge |
| skill-flow-ipe-query-params | SUCCESS | 1.000 | 190.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-google-tasks, ipe, mode:build |
| skill-flow-ixp-routing/explicit | SUCCESS | 1.000 | 256.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/invoice-extraction | SUCCESS | 1.000 | 615.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/receipts | SUCCESS | 1.000 | 349.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/contracts | SUCCESS | 1.000 | 434.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/forms-classify | SUCCESS | 1.000 | 290.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-remove-node | SUCCESS | 1.000 | 235.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node |
| skill-flow-hitl-smoke-completed-port | SUCCESS | 1.000 | 250.8s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, mode:build, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-openmeteo-weather | SUCCESS | 1.000 | 267.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node, connector, custom-codereval-openmeteoapis, ipe, custom-connector |
| skill-flow-slack-weather-pipeline | MAX_TURNS_EXHAUSTED | 0.000 | 403.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:decision, connector, feature:http |
| skill-flow-loop-multiply | SUCCESS | 1.000 | 364.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:loop |
| skill-flow-ipe-dtl-load-by-default-true | SUCCESS | 1.000 | 206.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-microsoft-azure, ipe, mode:build |
| skill-flow-ixp-e2e-project-selection/aviation | SUCCESS | 1.000 | 472.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-ixp-e2e-project-selection/birth-certificate | SUCCESS | 1.000 | 483.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-lowcode-agent | SUCCESS | 1.000 | 299.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-rpa | SUCCESS | 1.000 | 296.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-ipe-dtl-load-by-default-false | SUCCESS | 1.000 | 343.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-automaticc-woocommerce, ipe, mode:build |
| skill-flow-ipe-multiselect | SUCCESS | 1.000 | 423.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-act-act365, ipe, mode:build |
| skill-flow-ipe-complex-array | SUCCESS | 1.000 | 662.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, ipe, mode:build |
| skill-flow-outlook-waitfor-email | SUCCESS | 1.000 | 243.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, feature:trigger, connector, uipath-microsoft-outlook365, filter, ipe, wait-for-event |
| skill-flow-webhook-waitfor-parallel | SUCCESS | 1.000 | 307.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, connector, feature:trigger, feature:http, wait-for-event, uipath-http-webhook, ipe |
| skill-flow-summarize | SUCCESS | 1.000 | 198.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, node:summarize, context-grounding, mode:build |
| skill-flow-registry-discovery | SUCCESS | 1.000 | 116.4s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, lifecycle:discover, feature:registry |
| skill-flow-ixp-invoice-extraction-simulated | SUCCESS | 0.900 | 1887.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, node:ixp, connector, feature:http, simulation |
| skill-flow-feet-inches | SUCCESS | 1.000 | 435.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:switch |
| skill-flow-ixp-routing-listing/r01 | SUCCESS | 1.000 | 117.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r02 | SUCCESS | 1.000 | 65.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r03 | SUCCESS | 1.000 | 52.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r04 | SUCCESS | 1.000 | 64.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r05 | SUCCESS | 1.000 | 65.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r06 | SUCCESS | 1.000 | 54.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r07 | SUCCESS | 1.000 | 90.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r08 | SUCCESS | 1.000 | 52.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r09 | SUCCESS | 1.000 | 55.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r10 | SUCCESS | 1.000 | 48.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-customer-escalation | SUCCESS | 1.000 | 441.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:decision, feature:trigger, connector |
| skill-flow-customer-escalation-simulated | SUCCESS | 1.000 | 1336.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, node:decision, feature:trigger, connector, simulation |
| skill-flow-coded-agent | MAX_TURNS_EXHAUSTED | 0.375 | 316.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource, path-to-ga |
| skill-flow-terminate | SUCCESS | 1.000 | 444.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:terminate |
| skill-flow-ipe-jira-lifecycle | SUCCESS | 1.000 | 546.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:loop, node:switch, node:decision, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-eval-inline-agent | SUCCESS | 1.000 | 837.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:inline-agent, feature:eval |
| skill-flow-eval-local-crud | SUCCESS | 1.000 | 82.8s | claude-sonnet-4-6 | uipath-maestro-flow, mode:build, lifecycle:generate, feature:eval |
| skill-flow-scheduled-trigger | SUCCESS | 1.000 | 293.8s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:scheduled-trigger, feature:trigger |
| skill-flow-hitl-quality-boolean-decision | SUCCESS | 1.000 | 300.1s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-multi-city-weather | SUCCESS | 1.000 | 664.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:loop, feature:http |
| skill-flow-hitl-quality-brownfield-insert | SUCCESS | 1.000 | 531.7s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-ipe-enhanced-enum | SUCCESS | 1.000 | 749.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-automaticc-woocommerce, ipe, mode:build |
| skill-flow-generic-dynamic-node | FAILURE | 0.429 | 611.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node, connector, uipath-servicenow-servicenow, ipe |
| skill-flow-slack-channel-description-simulated | FAILURE | 0.583 | 2101.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, connector, simulation |
| skill-flow-bellevue-weather-simulated | SUCCESS | 1.000 | 1084.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, node:decision, feature:http, ipe, simulation |
| skill-flow-ipe-drive-to-slack | SUCCESS | 1.000 | 311.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, e2e, uipath-google-drive, uipath-salesforce-slack, ipe, mode:build |
| skill-flow-reading-list | SUCCESS | 1.000 | 322.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:transform |
| skill-flow-devcon-billing-resolution-writer | SUCCESS | 1.000 | 316.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, path-to-ga |
| skill-flow-ipe-jira-get-issue | SUCCESS | 1.000 | 296.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-bindings-no-duplicates | SUCCESS | 1.000 | 246.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-group-to-subflow | MAX_TURNS_EXHAUSTED | 0.000 | 666.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:subflow |
| skill-flow-ipe-ceql-where | SUCCESS | 1.000 | 350.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, connector, ceql, filter, uipath-microsoft-azureactivedirectory, ipe, mode:build |
| skill-flow-file-attachment-debug | SUCCESS | 1.000 | 192.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node |
| skill-flow-hitl-quality-result-downstream | SUCCESS | 1.000 | 206.2s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-ipe-jira-search-triage | FAILURE | 0.286 | 446.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:loop, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-add-output | SUCCESS | 1.000 | 50.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node |
| skill-flow-transform-map | SUCCESS | 1.000 | 162.5s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-bindings-multi-connector-independence | SUCCESS | 1.000 | 333.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, bindings, regression |
| skill-flow-hitl-quality-schema-design | SUCCESS | 1.000 | 314.4s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-subflow | SUCCESS | 1.000 | 194.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:subflow |
| skill-flow-trigger-with-filter | SUCCESS | 1.000 | 127.3s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:discover, connector-trigger, uipath-microsoft-outlook365, filter, ipe |
| skill-flow-transform-group-by | SUCCESS | 1.000 | 166.4s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-decision | SUCCESS | 1.000 | 240.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:decision |
| skill-flow-move-node | SUCCESS | 1.000 | 169.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:decision |
| skill-flow-ipe-enum | SUCCESS | 1.000 | 423.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle-generate, shape-multi-node, connector, uipath-google-gmail, ipe, mode:build |
| skill-flow-slack-http-fallback | SUCCESS | 1.000 | 275.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:single-node, connector, uipath-salesforce-slack, feature:http, ipe |
| skill-flow-ixp-scaffold-multinode | SUCCESS | 1.000 | 497.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, node:ixp |
| skill-flow-ipe-jira-create-issue | SUCCESS | 1.000 | 422.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-bellevue-weather | SUCCESS | 1.000 | 505.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:decision, feature:http, ipe |
| skill-flow-bindings-idempotent-reconfigure | SUCCESS | 1.000 | 334.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-solution-select-ask | FAILURE | 0.714 | 102.7s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, simulation |
| skill-flow-switch | SUCCESS | 1.000 | 226.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:switch |
| skill-flow-batch-transform | SUCCESS | 1.000 | 171.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, node:batch-transform, context-grounding, mode:build |
| skill-flow-interactive-customer-escalation-triage | SUCCESS | 1.000 | 333.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, feature:escalation, feature:conversational |
| skill-flow-delay | SUCCESS | 1.000 | 194.9s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:delay |
| skill-flow-api-workflow | SUCCESS | 1.000 | 257.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-devcon-billing-invoice-lookup | SUCCESS | 1.000 | 603.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, connector, path-to-ga |
| skill-flow-devcon-billing-discrepancy-detector | SUCCESS | 1.000 | 756.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, connector, path-to-ga |
| skill-flow-eval-evaluator-type-choice | SUCCESS | 1.000 | 160.0s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:discover, feature:eval |
| skill-flow-ixp-scaffold-minimal | SUCCESS | 1.000 | 372.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-ipe-searchable-joins | SUCCESS | 1.000 | 601.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-salesforce, ipe, mode:build |
| skill-flow-cli-dice-roller-simulated | FAILURE | 0.714 | 451.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, simulation |
| skill-flow-paginated-reference-lookup | SUCCESS | 1.000 | 287.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, e2e, mode:build, lifecycle:generate, shape:multi-node, connector, uipath-salesforce-slack, feature:records |
| skill-flow-ixp-integration-handle-routing | ERROR | 0.000 | 902.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:ixp, node:decision |
| skill-flow-inline-agent-robust | SUCCESS | 1.000 | 258.6s | claude-sonnet-4-6 | uipath-maestro-flow, mode:build, lifecycle:generate, node:inline-agent |
| skill-flow-ipe-required-groups | SUCCESS | 1.000 | 196.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-microsoft-teams, ipe, mode:build |
| skill-flow-devcon-billing-dispute-resolution | FAILURE | 0.500 | 1617.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, node:ixp, connector, path-to-ga |
| skill-flow-slack-channel-description | SUCCESS | 1.000 | 205.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, connector |

## Run-time Notes

> **WARNING:** [skill-flow-ixp-routing-negative/http-webhook] max_turns exhausted
> **WARNING:** [skill-flow-ixp-routing-negative/queue-write] max_turns exhausted
> **WARNING:** [skill-flow-e2e-devcon-expense-approval] expected_turns exceeded: 30/29 (cumulative SDK turns)
> **WARNING:** [skill-flow-eval-simulation-crud] expected_turns exceeded: 41/20 (cumulative SDK turns)
> **WARNING:** [skill-flow-init-validate] expected_turns exceeded: 16/9 (cumulative SDK turns)
> **WARNING:** [skill-flow-slack-weather-pipeline] max_turns exhausted
> **WARNING:** [skill-flow-registry-discovery] expected_turns exceeded: 20/9 (cumulative SDK turns)
> **WARNING:** [skill-flow-feet-inches] expected_turns exceeded: 24/23 (cumulative SDK turns)
> **WARNING:** [skill-flow-ixp-routing-listing/r01] max_turns exhausted
> **WARNING:** [skill-flow-ixp-routing-listing/r07] max_turns exhausted
> **WARNING:** [skill-flow-coded-agent] max_turns exhausted
> **WARNING:** [skill-flow-coded-agent] expected_turns exceeded: 48/35 (cumulative SDK turns)
> **WARNING:** [skill-flow-eval-inline-agent] expected_turns exceeded: 39/30 (cumulative SDK turns)
> **WARNING:** [skill-flow-ipe-enhanced-enum] expected_turns exceeded: 38/35 (cumulative SDK turns)
> **WARNING:** [skill-flow-reading-list] expected_turns exceeded: 21/20 (cumulative SDK turns)
> **WARNING:** [skill-flow-group-to-subflow] max_turns exhausted
> **WARNING:** [skill-flow-group-to-subflow] expected_turns exceeded: 46/13 (cumulative SDK turns)
> **WARNING:** [skill-flow-slack-http-fallback] expected_turns exceeded: 37/32 (cumulative SDK turns)
> **WARNING:** [skill-flow-eval-evaluator-type-choice] expected_turns exceeded: 22/15 (cumulative SDK turns)
> **WARNING:** [skill-flow-ixp-integration-handle-routing] expected_turns exceeded: 31/26 (cumulative SDK turns)


## Generation Metrics

| Task ID | Total Latency | Turns | Asst Turns | Avg Turn Latency |
|---------|---------------|-------|------------|------------------|
| skill-flow-ipe-path-params | 284.8s | 1 | 58 | 271.6s |
| skill-flow-hitl-schema-design-simulated | 594.3s | 6 | 79 | 80.0s |
| skill-flow-ixp-routing-negative/stripe-http | 212.6s | 1 | 29 | 201.6s |
| skill-flow-ixp-routing-negative/slack-summary | 244.7s | 1 | 24 | 237.4s |
| skill-flow-ixp-routing-negative/sf-update | 260.6s | 1 | 31 | 251.8s |
| skill-flow-ixp-routing-negative/http-webhook | 316.4s | 1 | 46 | 305.8s |
| skill-flow-ixp-routing-negative/gsheet-loop | 358.7s | 1 | 35 | 348.4s |
| skill-flow-ixp-routing-negative/queue-write | 242.4s | 1 | 47 | 232.6s |
| skill-flow-ixp-routing-negative/teams-decision | 236.5s | 1 | 32 | 225.9s |
| skill-flow-ixp-routing-negative/delay-email | 222.2s | 1 | 37 | 212.2s |
| skill-flow-non-catalog-http-fallback | 240.1s | 1 | 47 | 231.3s |
| skill-flow-expense-approval-simulated | 1025.9s | 5 | 45 | 179.6s |
| skill-flow-eval-no-auto-upload | 129.2s | 1 | 27 | 120.0s |
| skill-flow-devcon-billing-dispute-analyst | 531.1s | 1 | 51 | 492.9s |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 736.9s | 1 | 95 | 723.5s |
| skill-flow-e2e-devcon-expense-approval | 324.4s | 1 | 45 | 303.6s |
| skill-flow-calculator | 249.4s | 1 | 28 | 220.0s |
| skill-flow-ipe-generate-schema | 265.6s | 1 | 52 | 254.6s |
| skill-flow-dice-roller | 210.4s | 1 | 23 | 172.9s |
| skill-flow-update-node | 96.5s | 1 | 15 | 41.0s |
| skill-flow-eval-simulation-crud | 168.8s | 1 | 53 | 158.2s |
| skill-flow-init-validate | 140.1s | 1 | 27 | 131.6s |
| skill-flow-hitl-smoke-multi-outcome-routing | 293.3s | 1 | 28 | 276.5s |
| skill-flow-hitl-smoke-node-placed | 231.4s | 1 | 27 | 214.3s |
| skill-flow-outlook-trigger-inbox | 280.6s | 1 | 54 | 260.5s |
| skill-flow-bindings-reconfigure-different-connection | 546.9s | 1 | 81 | 534.6s |
| skill-flow-wiki-pageviews | 911.1s | 0 | 0 | N/A |
| skill-flow-add-node | 213.2s | 1 | 20 | 171.7s |
| skill-flow-transform-filter | 210.0s | 1 | 24 | 194.0s |
| skill-flow-merge-parallel-sync | 210.2s | 1 | 30 | 197.2s |
| skill-flow-ipe-query-params | 190.1s | 1 | 27 | 179.3s |
| skill-flow-ixp-routing/explicit | 256.2s | 1 | 43 | 247.1s |
| skill-flow-ixp-routing/invoice-extraction | 615.3s | 1 | 63 | 604.9s |
| skill-flow-ixp-routing/receipts | 349.9s | 1 | 47 | 340.7s |
| skill-flow-ixp-routing/contracts | 434.8s | 1 | 38 | 424.2s |
| skill-flow-ixp-routing/forms-classify | 290.3s | 1 | 43 | 286.2s |
| skill-flow-remove-node | 235.6s | 1 | 14 | 202.2s |
| skill-flow-hitl-smoke-completed-port | 250.8s | 1 | 29 | 242.3s |
| skill-flow-openmeteo-weather | 267.0s | 1 | 42 | 234.6s |
| skill-flow-slack-weather-pipeline | 403.1s | 1 | 61 | 395.5s |
| skill-flow-loop-multiply | 364.2s | 1 | 30 | 334.9s |
| skill-flow-ipe-dtl-load-by-default-true | 206.1s | 1 | 35 | 201.9s |
| skill-flow-ixp-e2e-project-selection/aviation | 472.2s | 1 | 50 | 465.3s |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 483.2s | 1 | 40 | 476.0s |
| skill-flow-lowcode-agent | 299.9s | 1 | 40 | 235.0s |
| skill-flow-rpa | 296.4s | 1 | 35 | 250.2s |
| skill-flow-ipe-dtl-load-by-default-false | 343.0s | 1 | 60 | 339.8s |
| skill-flow-ipe-multiselect | 423.9s | 1 | 44 | 420.8s |
| skill-flow-ipe-complex-array | 662.3s | 1 | 50 | 659.1s |
| skill-flow-outlook-waitfor-email | 243.6s | 1 | 44 | 233.9s |
| skill-flow-webhook-waitfor-parallel | 307.7s | 1 | 52 | 302.2s |
| skill-flow-summarize | 198.7s | 1 | 30 | 190.1s |
| skill-flow-registry-discovery | 116.4s | 1 | 24 | 112.4s |
| skill-flow-ixp-invoice-extraction-simulated | 1887.6s | 9 | 222 | 193.2s |
| skill-flow-feet-inches | 435.3s | 1 | 42 | 393.2s |
| skill-flow-ixp-routing-listing/r01 | 117.6s | 1 | 35 | 111.0s |
| skill-flow-ixp-routing-listing/r02 | 65.7s | 1 | 17 | 61.8s |
| skill-flow-ixp-routing-listing/r03 | 52.3s | 1 | 11 | 48.5s |
| skill-flow-ixp-routing-listing/r04 | 64.3s | 1 | 13 | 59.7s |
| skill-flow-ixp-routing-listing/r05 | 65.5s | 1 | 13 | 61.6s |
| skill-flow-ixp-routing-listing/r06 | 54.7s | 1 | 11 | 49.4s |
| skill-flow-ixp-routing-listing/r07 | 90.5s | 1 | 30 | 85.0s |
| skill-flow-ixp-routing-listing/r08 | 52.7s | 1 | 13 | 49.3s |
| skill-flow-ixp-routing-listing/r09 | 55.8s | 1 | 10 | 50.9s |
| skill-flow-ixp-routing-listing/r10 | 48.1s | 1 | 11 | 45.5s |
| skill-flow-customer-escalation | 441.0s | 1 | 44 | 433.2s |
| skill-flow-customer-escalation-simulated | 1336.8s | 4 | 125 | 314.2s |
| skill-flow-coded-agent | 316.9s | 1 | 68 | 308.3s |
| skill-flow-terminate | 444.8s | 1 | 41 | 417.5s |
| skill-flow-ipe-jira-lifecycle | 546.4s | 1 | 44 | 494.5s |
| skill-flow-eval-inline-agent | 837.3s | 1 | 54 | 834.2s |
| skill-flow-eval-local-crud | 82.8s | 1 | 19 | 79.7s |
| skill-flow-scheduled-trigger | 293.8s | 1 | 31 | 287.2s |
| skill-flow-hitl-quality-boolean-decision | 300.1s | 1 | 33 | 293.9s |
| skill-flow-multi-city-weather | 664.2s | 1 | 35 | 619.1s |
| skill-flow-hitl-quality-brownfield-insert | 531.7s | 1 | 38 | 524.3s |
| skill-flow-ipe-enhanced-enum | 749.2s | 1 | 65 | 746.9s |
| skill-flow-generic-dynamic-node | 611.4s | 1 | 95 | 580.9s |
| skill-flow-slack-channel-description-simulated | 2101.5s | 6 | 181 | 335.8s |
| skill-flow-bellevue-weather-simulated | 1084.8s | 9 | 117 | 103.5s |
| skill-flow-ipe-drive-to-slack | 311.4s | 1 | 59 | 309.3s |
| skill-flow-reading-list | 322.7s | 1 | 41 | 296.0s |
| skill-flow-devcon-billing-resolution-writer | 316.5s | 1 | 29 | 283.2s |
| skill-flow-ipe-jira-get-issue | 296.9s | 1 | 51 | 267.0s |
| skill-flow-bindings-no-duplicates | 246.7s | 1 | 49 | 241.1s |
| skill-flow-group-to-subflow | 666.1s | 1 | 80 | 660.4s |
| skill-flow-ipe-ceql-where | 350.9s | 1 | 44 | 348.5s |
| skill-flow-file-attachment-debug | 192.3s | 1 | 31 | 164.7s |
| skill-flow-hitl-quality-result-downstream | 206.2s | 1 | 23 | 197.1s |
| skill-flow-ipe-jira-search-triage | 446.7s | 1 | 50 | 408.9s |
| skill-flow-add-output | 50.6s | 1 | 11 | 25.4s |
| skill-flow-transform-map | 162.5s | 1 | 21 | 155.8s |
| skill-flow-bindings-multi-connector-independence | 333.7s | 1 | 44 | 329.5s |
| skill-flow-hitl-quality-schema-design | 314.4s | 1 | 34 | 309.1s |
| skill-flow-subflow | 194.5s | 1 | 26 | 165.4s |
| skill-flow-trigger-with-filter | 127.3s | 1 | 12 | 125.0s |
| skill-flow-transform-group-by | 166.4s | 1 | 27 | 160.0s |
| skill-flow-decision | 240.3s | 1 | 26 | 201.7s |
| skill-flow-move-node | 169.4s | 1 | 18 | 139.5s |
| skill-flow-ipe-enum | 423.3s | 1 | 39 | 419.6s |
| skill-flow-slack-http-fallback | 275.2s | 1 | 54 | 255.7s |
| skill-flow-ixp-scaffold-multinode | 497.5s | 1 | 30 | 490.5s |
| skill-flow-ipe-jira-create-issue | 422.7s | 1 | 46 | 388.2s |
| skill-flow-bellevue-weather | 505.8s | 1 | 34 | 474.7s |
| skill-flow-bindings-idempotent-reconfigure | 334.2s | 1 | 53 | 329.8s |
| skill-flow-solution-select-ask | 102.7s | 3 | 19 | 29.1s |
| skill-flow-switch | 226.8s | 1 | 30 | 202.7s |
| skill-flow-batch-transform | 171.9s | 1 | 21 | 165.7s |
| skill-flow-interactive-customer-escalation-triage | 333.3s | 3 | 34 | 83.4s |
| skill-flow-delay | 194.9s | 1 | 27 | 188.5s |
| skill-flow-api-workflow | 257.5s | 1 | 39 | 231.1s |
| skill-flow-devcon-billing-invoice-lookup | 603.2s | 1 | 73 | 532.0s |
| skill-flow-devcon-billing-discrepancy-detector | 756.1s | 1 | 44 | 726.7s |
| skill-flow-eval-evaluator-type-choice | 160.0s | 1 | 33 | 157.4s |
| skill-flow-ixp-scaffold-minimal | 372.9s | 1 | 42 | 367.0s |
| skill-flow-ipe-searchable-joins | 601.7s | 1 | 35 | 599.4s |
| skill-flow-cli-dice-roller-simulated | 451.0s | 6 | 71 | 63.8s |
| skill-flow-paginated-reference-lookup | 287.7s | 1 | 48 | 285.3s |
| skill-flow-ixp-integration-handle-routing | 902.3s | 1 | 52 | 900.0s |
| skill-flow-inline-agent-robust | 258.6s | 1 | 35 | 255.4s |
| skill-flow-ipe-required-groups | 196.5s | 1 | 36 | 193.1s |
| skill-flow-devcon-billing-dispute-resolution | 1617.4s | 1 | 152 | 1577.8s |
| skill-flow-slack-channel-description | 205.1s | 1 | 49 | 179.3s |


## Token Usage

**Total Tokens**: 179,145,194 (input: 48,972, output: 2,368,383)
**Cache Tokens**: write: 9,071,323, read: 167,656,516
**Total Cost**: $119.9871
**Avg Tokens/Task**: 1,468,403

| Task ID | Input (uncached) | Output | Cache Write | Cache Read | Total | Cost |
|---------|------------------|--------|-------------|------------|-------|------|
| skill-flow-ipe-path-params | 24 | 10,052 | 80,825 | 1,643,132 | 1,734,033 | $0.9469 |
| skill-flow-hitl-schema-design-simulated | 53 | 23,944 | 54,907 | 2,366,653 | 2,445,557 | $1.2752 |
| skill-flow-ixp-routing-negative/stripe-http | 15 | 7,623 | 57,257 | 722,835 | 787,730 | $0.5460 |
| skill-flow-ixp-routing-negative/slack-summary | 11 | 12,357 | 49,783 | 412,104 | 474,255 | $0.4957 |
| skill-flow-ixp-routing-negative/sf-update | 15 | 11,728 | 49,991 | 686,036 | 747,770 | $0.5692 |
| skill-flow-ixp-routing-negative/http-webhook | 24 | 11,647 | 68,503 | 1,400,169 | 1,480,343 | $0.8517 |
| skill-flow-ixp-routing-negative/gsheet-loop | 15 | 19,612 | 72,209 | 666,730 | 758,566 | $0.7650 |
| skill-flow-ixp-routing-negative/queue-write | 28 | 8,135 | 42,140 | 1,360,545 | 1,410,848 | $0.6883 |
| skill-flow-ixp-routing-negative/teams-decision | 17 | 8,720 | 49,510 | 798,651 | 856,898 | $0.5561 |
| skill-flow-ixp-routing-negative/delay-email | 14 | 8,224 | 51,805 | 614,946 | 674,989 | $0.5022 |
| skill-flow-non-catalog-http-fallback | 21 | 9,812 | 70,938 | 1,159,102 | 1,239,873 | $0.7610 |
| skill-flow-expense-approval-simulated | 28 | 61,407 | 157,847 | 1,468,059 | 1,687,341 | $1.9535 |
| skill-flow-eval-no-auto-upload | 18 | 3,293 | 17,613 | 586,375 | 607,299 | $0.2914 |
| skill-flow-devcon-billing-dispute-analyst | 22 | 26,565 | 78,625 | 1,401,224 | 1,506,436 | $1.1138 |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 48 | 34,985 | 135,281 | 5,298,013 | 5,468,327 | $2.6216 |
| skill-flow-e2e-devcon-expense-approval | 1,064 | 18,464 | 71,378 | 1,212,029 | 1,302,935 | $0.9114 |
| skill-flow-calculator | 12 | 10,799 | 62,590 | 497,280 | 570,681 | $0.5459 |
| skill-flow-ipe-generate-schema | 24 | 8,126 | 94,539 | 1,858,127 | 1,960,816 | $1.0339 |
| skill-flow-dice-roller | 11 | 7,203 | 41,995 | 394,473 | 443,682 | $0.3839 |
| skill-flow-update-node | 8 | 2,303 | 30,143 | 282,386 | 314,840 | $0.2323 |
| skill-flow-eval-simulation-crud | 28 | 5,090 | 27,524 | 1,169,103 | 1,201,745 | $0.5304 |
| skill-flow-init-validate | 13 | 4,952 | 36,723 | 512,660 | 554,348 | $0.3658 |
| skill-flow-hitl-smoke-multi-outcome-routing | 13 | 15,928 | 66,734 | 553,809 | 636,484 | $0.6554 |
| skill-flow-hitl-smoke-node-placed | 12 | 10,852 | 52,092 | 489,521 | 552,477 | $0.5050 |
| skill-flow-outlook-trigger-inbox | 24 | 9,151 | 75,055 | 1,527,734 | 1,611,964 | $0.8771 |
| skill-flow-bindings-reconfigure-different-connection | 44 | 28,030 | 97,949 | 2,959,266 | 3,085,289 | $1.6757 |
| skill-flow-add-node | 479 | 12,373 | 51,792 | 387,943 | 452,587 | $0.4976 |
| skill-flow-transform-filter | 11 | 8,423 | 58,840 | 460,253 | 527,527 | $0.4851 |
| skill-flow-merge-parallel-sync | 12 | 9,035 | 46,211 | 473,602 | 528,860 | $0.4509 |
| skill-flow-ipe-query-params | 12 | 8,078 | 52,071 | 502,456 | 562,617 | $0.4672 |
| skill-flow-ixp-routing/explicit | 22 | 10,753 | 74,235 | 1,280,821 | 1,365,831 | $0.8240 |
| skill-flow-ixp-routing/invoice-extraction | 31 | 33,954 | 105,431 | 2,674,477 | 2,813,893 | $1.7071 |
| skill-flow-ixp-routing/receipts | 21 | 17,264 | 76,327 | 1,168,117 | 1,261,729 | $0.8957 |
| skill-flow-ixp-routing/contracts | 16 | 23,475 | 72,983 | 863,134 | 959,608 | $0.8848 |
| skill-flow-ixp-routing/forms-classify | 19 | 17,186 | 77,036 | 1,014,559 | 1,108,800 | $0.8511 |
| skill-flow-remove-node | 8 | 19,683 | 45,640 | 313,730 | 379,061 | $0.5605 |
| skill-flow-hitl-smoke-completed-port | 13 | 14,128 | 60,442 | 527,449 | 602,032 | $0.5969 |
| skill-flow-openmeteo-weather | 21 | 10,113 | 95,802 | 1,559,924 | 1,665,860 | $0.9790 |
| skill-flow-slack-weather-pipeline | 42 | 20,117 | 92,784 | 3,895,606 | 4,008,549 | $1.8185 |
| skill-flow-loop-multiply | 13 | 19,109 | 53,601 | 565,878 | 638,601 | $0.6574 |
| skill-flow-ipe-dtl-load-by-default-true | 13 | 7,897 | 66,850 | 622,066 | 696,826 | $0.5558 |
| skill-flow-ixp-e2e-project-selection/aviation | 28 | 25,141 | 78,898 | 1,866,789 | 1,970,856 | $1.2331 |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 18 | 29,376 | 80,206 | 1,113,504 | 1,223,104 | $1.0755 |
| skill-flow-lowcode-agent | 19 | 11,958 | 55,641 | 956,768 | 1,024,386 | $0.6751 |
| skill-flow-rpa | 15 | 13,409 | 53,028 | 664,742 | 731,194 | $0.5995 |
| skill-flow-ipe-dtl-load-by-default-false | 26 | 13,728 | 111,622 | 2,082,553 | 2,207,929 | $1.2493 |
| skill-flow-ipe-multiselect | 21 | 24,539 | 79,281 | 1,302,166 | 1,406,007 | $1.0561 |
| skill-flow-ipe-complex-array | 20 | 41,694 | 148,347 | 1,161,898 | 1,351,959 | $1.5303 |
| skill-flow-outlook-waitfor-email | 21 | 8,225 | 75,860 | 1,238,204 | 1,322,310 | $0.7794 |
| skill-flow-webhook-waitfor-parallel | 25 | 12,680 | 81,440 | 1,696,462 | 1,790,607 | $1.0046 |
| skill-flow-summarize | 9,379 | 12,080 | 68,779 | 526,639 | 616,877 | $0.6252 |
| skill-flow-registry-discovery | 16 | 2,980 | 19,139 | 449,817 | 471,952 | $0.2515 |
| skill-flow-ixp-invoice-extraction-simulated | 7,566 | 96,255 | 263,380 | 15,549,357 | 15,916,558 | $7.1190 |
| skill-flow-feet-inches | 18 | 25,477 | 69,655 | 1,082,990 | 1,178,140 | $0.9683 |
| skill-flow-ixp-routing-listing/r01 | 23 | 4,273 | 47,937 | 665,075 | 717,308 | $0.4435 |
| skill-flow-ixp-routing-listing/r02 | 8 | 2,569 | 24,202 | 160,432 | 187,211 | $0.1774 |
| skill-flow-ixp-routing-listing/r03 | 11 | 1,999 | 35,091 | 222,830 | 259,931 | $0.2285 |
| skill-flow-ixp-routing-listing/r04 | 9 | 2,165 | 34,966 | 222,404 | 259,544 | $0.2303 |
| skill-flow-ixp-routing-listing/r05 | 8 | 2,529 | 24,830 | 150,156 | 177,523 | $0.1761 |
| skill-flow-ixp-routing-listing/r06 | 9 | 1,916 | 34,498 | 222,399 | 258,822 | $0.2249 |
| skill-flow-ixp-routing-listing/r07 | 22 | 2,910 | 38,718 | 672,465 | 714,115 | $0.3906 |
| skill-flow-ixp-routing-listing/r08 | 12 | 1,920 | 35,256 | 278,768 | 315,956 | $0.2447 |
| skill-flow-ixp-routing-listing/r09 | 9 | 2,464 | 22,685 | 177,303 | 202,461 | $0.1752 |
| skill-flow-ixp-routing-listing/r10 | 9 | 1,708 | 34,962 | 222,384 | 259,063 | $0.2235 |
| skill-flow-customer-escalation | 17 | 25,977 | 121,597 | 1,284,094 | 1,431,685 | $1.2309 |
| skill-flow-customer-escalation-simulated | 2,104 | 72,188 | 313,115 | 5,455,238 | 5,842,645 | $3.8999 |
| skill-flow-coded-agent | 42 | 13,419 | 109,657 | 3,229,857 | 3,352,975 | $1.5816 |
| skill-flow-terminate | 17 | 26,666 | 67,985 | 843,317 | 937,985 | $0.9080 |
| skill-flow-ipe-jira-lifecycle | 16 | 30,231 | 105,571 | 1,051,800 | 1,187,618 | $1.1649 |
| skill-flow-eval-inline-agent | 32 | 52,768 | 88,639 | 2,577,406 | 2,718,845 | $1.8972 |
| skill-flow-eval-local-crud | 12 | 2,753 | 29,871 | 380,719 | 413,355 | $0.2676 |
| skill-flow-scheduled-trigger | 16 | 19,104 | 44,467 | 700,669 | 764,256 | $0.6636 |
| skill-flow-hitl-quality-boolean-decision | 15 | 20,735 | 55,161 | 631,393 | 707,304 | $0.7073 |
| skill-flow-multi-city-weather | 16 | 42,693 | 76,572 | 903,476 | 1,022,757 | $1.1986 |
| skill-flow-hitl-quality-brownfield-insert | 18 | 34,728 | 70,387 | 1,078,264 | 1,183,397 | $1.1084 |
| skill-flow-ipe-enhanced-enum | 28 | 27,423 | 87,606 | 1,853,958 | 1,969,015 | $1.2961 |
| skill-flow-generic-dynamic-node | 47 | 29,264 | 103,871 | 4,309,170 | 4,442,352 | $2.1214 |
| skill-flow-slack-channel-description-simulated | 6,898 | 110,283 | 232,911 | 7,723,369 | 8,073,461 | $4.8654 |
| skill-flow-bellevue-weather-simulated | 7,521 | 54,297 | 195,752 | 4,141,533 | 4,399,103 | $2.8135 |
| skill-flow-ipe-drive-to-slack | 22 | 14,677 | 102,114 | 1,636,653 | 1,753,466 | $1.0941 |
| skill-flow-reading-list | 17 | 15,027 | 55,060 | 870,347 | 940,451 | $0.6930 |
| skill-flow-devcon-billing-resolution-writer | 13 | 18,700 | 65,200 | 617,959 | 701,872 | $0.7104 |
| skill-flow-ipe-jira-get-issue | 23 | 11,775 | 111,866 | 1,948,710 | 2,072,374 | $1.1808 |
| skill-flow-bindings-no-duplicates | 23 | 10,622 | 72,299 | 1,407,339 | 1,490,283 | $0.8527 |
| skill-flow-group-to-subflow | 41 | 55,159 | 63,903 | 2,555,563 | 2,674,666 | $1.8338 |
| skill-flow-ipe-ceql-where | 17 | 20,840 | 89,739 | 1,102,026 | 1,212,622 | $0.9798 |
| skill-flow-file-attachment-debug | 15 | 6,849 | 58,192 | 679,755 | 744,811 | $0.5249 |
| skill-flow-hitl-quality-result-downstream | 16 | 12,206 | 40,482 | 598,792 | 651,496 | $0.5146 |
| skill-flow-ipe-jira-search-triage | 19 | 24,539 | 95,369 | 1,227,503 | 1,347,430 | $1.0940 |
| skill-flow-add-output | 7 | 1,571 | 29,269 | 230,129 | 260,976 | $0.2024 |
| skill-flow-transform-map | 11 | 8,604 | 44,433 | 409,123 | 462,171 | $0.4185 |
| skill-flow-bindings-multi-connector-independence | 18 | 19,068 | 88,306 | 1,134,700 | 1,242,092 | $0.9576 |
| skill-flow-hitl-quality-schema-design | 14 | 20,488 | 65,371 | 594,925 | 680,798 | $0.7310 |
| skill-flow-subflow | 11 | 10,745 | 47,274 | 412,037 | 470,067 | $0.4621 |
| skill-flow-trigger-with-filter | 9 | 7,413 | 30,105 | 272,998 | 310,525 | $0.3060 |
| skill-flow-transform-group-by | 13 | 9,157 | 48,263 | 550,308 | 607,741 | $0.4835 |
| skill-flow-decision | 11 | 12,072 | 52,404 | 377,251 | 441,738 | $0.4908 |
| skill-flow-move-node | 10 | 11,620 | 37,782 | 402,807 | 452,219 | $0.4369 |
| skill-flow-ipe-enum | 14 | 27,318 | 89,920 | 851,267 | 968,519 | $1.0024 |
| skill-flow-slack-http-fallback | 28 | 8,448 | 109,806 | 2,380,586 | 2,498,868 | $1.2528 |
| skill-flow-ixp-scaffold-multinode | 13 | 30,831 | 78,177 | 597,260 | 706,281 | $0.9348 |
| skill-flow-ipe-jira-create-issue | 18 | 20,740 | 86,180 | 1,160,873 | 1,267,811 | $0.9826 |
| skill-flow-bellevue-weather | 13 | 31,172 | 60,205 | 614,374 | 705,764 | $0.8777 |
| skill-flow-bindings-idempotent-reconfigure | 27 | 17,790 | 74,635 | 1,873,823 | 1,966,275 | $1.1090 |
| skill-flow-solution-select-ask | 15 | 2,961 | 28,146 | 346,725 | 377,847 | $0.2540 |
| skill-flow-switch | 14 | 11,483 | 62,502 | 612,249 | 686,248 | $0.5903 |
| skill-flow-batch-transform | 12 | 10,070 | 45,735 | 466,510 | 522,327 | $0.4625 |
| skill-flow-interactive-customer-escalation-triage | 18 | 15,318 | 69,135 | 815,214 | 899,685 | $0.7336 |
| skill-flow-delay | 11 | 11,084 | 43,781 | 399,599 | 454,475 | $0.4504 |
| skill-flow-api-workflow | 16 | 14,843 | 54,069 | 666,804 | 735,732 | $0.6255 |
| skill-flow-devcon-billing-invoice-lookup | 32 | 27,610 | 101,862 | 2,990,926 | 3,120,430 | $1.6935 |
| skill-flow-devcon-billing-discrepancy-detector | 18 | 45,081 | 116,378 | 1,339,074 | 1,500,551 | $1.5144 |
| skill-flow-eval-evaluator-type-choice | 20 | 7,593 | 33,528 | 866,863 | 908,004 | $0.4997 |
| skill-flow-ixp-scaffold-minimal | 17 | 22,770 | 70,723 | 982,711 | 1,076,221 | $0.9016 |
| skill-flow-ipe-searchable-joins | 14 | 38,334 | 82,887 | 665,162 | 786,397 | $1.0854 |
| skill-flow-cli-dice-roller-simulated | 43 | 19,127 | 59,547 | 1,781,943 | 1,860,660 | $1.0449 |
| skill-flow-paginated-reference-lookup | 28 | 15,120 | 81,747 | 2,003,165 | 2,100,060 | $1.1344 |
| skill-flow-ixp-integration-handle-routing | 22 | 57,152 | 76,543 | 1,342,428 | 1,476,145 | $1.5471 |
| skill-flow-inline-agent-robust | 15 | 16,791 | 69,410 | 769,579 | 855,795 | $0.7431 |
| skill-flow-ipe-required-groups | 15 | 8,833 | 71,965 | 725,934 | 806,747 | $0.6202 |
| skill-flow-devcon-billing-dispute-resolution | 11,788 | 93,245 | 271,886 | 7,703,080 | 8,079,999 | $4.7645 |
| skill-flow-slack-channel-description | 21 | 8,423 | 89,541 | 1,470,097 | 1,568,082 | $0.9032 |


## Command Telemetry

**Total Commands**: 3108
**Success Rate**: 2992/3108 (96.3%)

### Commands by Tool

| Tool | Count | % |
|------|-------|---|
| Bash | 1620 | 52.1% |
| Read | 866 | 27.9% |
| Edit | 287 | 9.2% |
| Skill | 134 | 4.3% |
| Write | 87 | 2.8% |
| TaskUpdate | 56 | 1.8% |
| TaskCreate | 29 | 0.9% |
| Glob | 16 | 0.5% |
| Grep | 11 | 0.4% |
| TaskOutput | 2 | 0.1% |

### Performance

- **Average Command Time**: 4260.2ms
- **Total Command Time**: 13240.62s

### Slowest Commands

| Tool | Duration | Parameters |
|------|----------|------------|
| Bash | 121276ms | {'command': 'uip login status --output json 2>/dev... |
| Bash | 120525ms | {'command': 'cd /work/output/artifacts/skill-flow-... |
| TaskOutput | 120101ms | {'task_id': 'b91ux4d42', 'block': True, 'timeout':... |
| Bash | 66367ms | {'command': 'uip maestro flow registry get core.co... |
| Bash | 65920ms | {'command': '\\\nuip maestro flow registry get cor... |

**Most Common Pattern**: `Bash → Bash → Bash`

**Skill Tool Invoked**: 134 time(s)

## Agent Settings

- **Permission Mode**: acceptEdits
- **Allowed Tools**: Skill, Bash, Read, Write, Edit, Glob, Grep
- **Model**: us.anthropic.claude-sonnet-4-6
- **Max Turns**: 120
- **System Prompt**: You are a coding agent. Do not access files in sibling runs/* directories. Everywhere else is permitted. 
- **Plugins**: /home/azureuser/projects/skills

## Environment

- **git_commit**: acc1c86
- **skills_git_commit**: 48b470716
- **cli_version**: 1.199.0-dev.7923 | 1.199.0-dev.7970
- **tool_plugins**: {'admin-tool': '1.199.0-dev.7962', 'agent-tool': '1.199.0-dev.7923 | 1.199.0-dev.7965', 'agenthub-tool': '1.199.0-dev.7923 | 1.199.0-dev.7962', 'aops-tool': '1.199.0-dev.7962', 'api-workflow-tool': '1.199.0-dev.7962', 'codedagent-tool': '1.199.0-dev.7923 | 1.199.0-dev.7965', 'codedapp-tool': '1.199.0-dev.7962', 'coder-tool': '1.199.0-dev.7962', 'context-grounding-tool': '1.199.0-dev.7962', 'conversational-tool': '1.199.0-dev.7962', 'data-fabric-tool': '1.199.0-dev.7923 | 1.199.0-dev.7962', 'docsai-tool': '1.199.0-dev.7962', 'functions-tool': '1.199.0-dev.7923 | 1.199.0-dev.7962', 'gov-tool': '1.199.0-dev.7923 | 1.199.0-dev.7962', 'insights-tool': '1.199.0-dev.7923 | 1.199.0-dev.7962', 'integrationservice-tool': '1.199.0-dev.7923 | 1.199.0-dev.7962', 'ixp-tool': '1.199.0-dev.7923 | 1.199.0-dev.7962', 'llm-gateway-tool': '1.199.0-dev.7962', 'llmgw-tool': '1.199.0-dev.7962', 'maestro-tool': '1.199.0-dev.7924 | 1.199.0-dev.7962', 'orchestrator-tool': '1.199.0-dev.7923 | 1.199.0-dev.7962', 'platform-tool': '1.199.0-dev.7962', 'pm-tool': '1.199.0-dev.7969', 'rpa-legacy-tool': '1.199.0-dev.7962', 'rpa-tool': '1.199.0-dev.20260722.4', 'solution-tool': '1.199.0-dev.7923 | 1.199.0-dev.7962', 'tasks-tool': '1.199.0-dev.7923 | 1.199.0-dev.7962', 'test-manager-tool': '1.199.0-dev.7923 | 1.199.0-dev.7962', 'traces-tool': '1.199.0-dev.7962', 'vertical-solutions-tool': '1.199.0-dev.7962'}
- **coder_eval**: 0.8.8
- **claude_code_cli**: 2.1.218 (Claude Code)
- **uv**: uv 0.11.21 (x86_64-unknown-linux-gnu)
- **anthropic**: 0.102.0
- **openai**: Not Installed
- **pydantic**: 2.12.5