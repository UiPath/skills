# Evaluation Run Report

**Run ID**: `maestro-flow-baseline-report-repeat-5`
**Date**: 2026-07-24 17:02:24
**Duration**: 7994.39s
**Model**: `claude-sonnet-4-6`

## Summary

- **Total Tasks**: 615
- **Succeeded**: 546
- **Failed**: 63
- **Errors**: 6
- **Success Rate**: 89.7%
- **Avg Reliability Score**: 0.928
- **Avg Generation Latency**: 344.6s
- **Total Assistant Turns**: 26127
- **Crashed Partials**: 6 (3 recovered, 3 terminal)

## Task Details

| Task ID | Status | Reliability Score | Latency | Model | Tags |
|---------|--------|-------------------|---------|-------|------|
| skill-flow-wiki-pageviews | SUCCESS | 1.000 | 709.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:transform, feature:http |
| skill-flow-e2e-devcon-expense-approval | SUCCESS | 1.000 | 346.5s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, e2e, devcon |
| skill-flow-hitl-quality-boolean-decision | SUCCESS | 1.000 | 287.2s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-bellevue-weather-simulated | SUCCESS | 1.000 | 526.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, node:decision, feature:http, ipe, simulation |
| skill-flow-ixp-routing-negative/stripe-http | SUCCESS | 1.000 | 241.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/slack-summary | SUCCESS | 1.000 | 213.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/sf-update | SUCCESS | 1.000 | 348.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/http-webhook | SUCCESS | 1.000 | 208.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/gsheet-loop | SUCCESS | 1.000 | 381.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/queue-write | SUCCESS | 1.000 | 210.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/teams-decision | SUCCESS | 1.000 | 328.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/delay-email | SUCCESS | 1.000 | 342.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-paginated-reference-lookup | SUCCESS | 1.000 | 287.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, e2e, mode:build, lifecycle:generate, shape:multi-node, connector, uipath-salesforce-slack, feature:records |
| skill-flow-calculator | SUCCESS | 1.000 | 204.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node |
| skill-flow-eval-no-auto-upload | SUCCESS | 1.000 | 114.4s | claude-sonnet-4-6 | uipath-maestro-flow, mode:operate, lifecycle:execute, feature:eval |
| skill-flow-bindings-reconfigure-different-connection | SUCCESS | 1.000 | 342.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-ipe-jira-get-issue | SUCCESS | 1.000 | 339.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-ipe-dtl-load-by-default-true | SUCCESS | 1.000 | 202.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-microsoft-azure, ipe, mode:build |
| skill-flow-ipe-path-params | SUCCESS | 1.000 | 347.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-ipe-jira-create-issue | SUCCESS | 1.000 | 397.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-ixp-invoice-extraction-simulated | TIMEOUT | 0.000 | 2410.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, node:ixp, connector, feature:http, simulation |
| skill-flow-ixp-integration-handle-routing | SUCCESS | 1.000 | 506.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:ixp, node:decision |
| skill-flow-delay | SUCCESS | 1.000 | 248.0s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:delay |
| skill-flow-openmeteo-weather | SUCCESS | 1.000 | 325.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node, connector, custom-codereval-openmeteoapis, ipe, custom-connector |
| skill-flow-bindings-no-duplicates | SUCCESS | 1.000 | 415.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-outlook-waitfor-email | SUCCESS | 1.000 | 286.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, feature:trigger, connector, uipath-microsoft-outlook365, filter, ipe, wait-for-event |
| skill-flow-devcon-billing-invoice-lookup | SUCCESS | 1.000 | 830.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, connector, path-to-ga |
| skill-flow-file-attachment-debug | SUCCESS | 1.000 | 220.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node |
| skill-flow-terminate | SUCCESS | 1.000 | 228.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:terminate |
| skill-flow-ipe-dtl-load-by-default-false | SUCCESS | 1.000 | 393.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-automaticc-woocommerce, ipe, mode:build |
| skill-flow-merge-parallel-sync | SUCCESS | 1.000 | 169.4s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:multi-node, node:merge |
| skill-flow-ipe-jira-lifecycle | SUCCESS | 1.000 | 883.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:loop, node:switch, node:decision, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-ixp-scaffold-multinode | SUCCESS | 1.000 | 487.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, node:ixp |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | SUCCESS | 1.000 | 675.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:ixp, connector, feature:http |
| skill-flow-devcon-billing-resolution-writer | SUCCESS | 1.000 | 291.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, path-to-ga |
| skill-flow-batch-transform | SUCCESS | 1.000 | 165.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, node:batch-transform, context-grounding, mode:build |
| skill-flow-ixp-routing/explicit | SUCCESS | 1.000 | 684.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/invoice-extraction | SUCCESS | 1.000 | 362.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/receipts | SUCCESS | 1.000 | 304.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/contracts | SUCCESS | 1.000 | 259.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/forms-classify | SUCCESS | 1.000 | 272.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-transform-filter | SUCCESS | 1.000 | 224.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-non-catalog-http-fallback | SUCCESS | 1.000 | 188.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, connector, uipath-uipath-http, feature:http, ipe |
| skill-flow-customer-escalation | SUCCESS | 1.000 | 616.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:decision, feature:trigger, connector |
| skill-flow-expense-approval-simulated | SUCCESS | 1.000 | 982.0s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, e2e, mode:build, lifecycle:generate, devcon, simulation |
| skill-flow-ipe-enhanced-enum | SUCCESS | 1.000 | 411.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-automaticc-woocommerce, ipe, mode:build |
| skill-flow-hitl-quality-schema-design | SUCCESS | 1.000 | 242.0s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-add-output | SUCCESS | 1.000 | 62.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node |
| skill-flow-ixp-e2e-project-selection/aviation | SUCCESS | 1.000 | 377.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-ixp-e2e-project-selection/birth-certificate | SUCCESS | 1.000 | 292.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-eval-simulation-crud | SUCCESS | 1.000 | 112.8s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, feature:eval |
| skill-flow-slack-channel-description-simulated | FAILURE | 0.250 | 388.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, connector, simulation |
| skill-flow-solution-select-ask | FAILURE | 0.714 | 130.9s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, simulation |
| skill-flow-eval-local-crud | SUCCESS | 1.000 | 112.5s | claude-sonnet-4-6 | uipath-maestro-flow, mode:build, lifecycle:generate, feature:eval |
| skill-flow-api-workflow | SUCCESS | 1.000 | 247.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-hitl-schema-design-simulated | SUCCESS | 1.000 | 1143.3s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, simulation |
| skill-flow-generic-dynamic-node | ERROR | 0.000 | 1208.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node, connector, uipath-servicenow-servicenow, ipe |
| skill-flow-ipe-generate-schema | SUCCESS | 1.000 | 296.1s | claude-sonnet-4-6 | uipath-platform, integration, lifecycle:generate, shape:multi-node, connector, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-ipe-enum | SUCCESS | 1.000 | 382.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle-generate, shape-multi-node, connector, uipath-google-gmail, ipe, mode:build |
| skill-flow-update-node | SUCCESS | 1.000 | 99.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:decision |
| skill-flow-switch | SUCCESS | 1.000 | 247.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:switch |
| skill-flow-webhook-waitfor-parallel | SUCCESS | 1.000 | 268.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, connector, feature:trigger, feature:http, wait-for-event, uipath-http-webhook, ipe |
| skill-flow-eval-evaluator-type-choice | SUCCESS | 1.000 | 110.5s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:discover, feature:eval |
| skill-flow-transform-group-by | SUCCESS | 1.000 | 179.7s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-multi-city-weather | SUCCESS | 1.000 | 500.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:loop, feature:http |
| skill-flow-ixp-scaffold-minimal | SUCCESS | 1.000 | 320.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-ipe-complex-array | SUCCESS | 1.000 | 583.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, ipe, mode:build |
| skill-flow-dice-roller | SUCCESS | 1.000 | 193.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node |
| skill-flow-slack-channel-description | SUCCESS | 1.000 | 263.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, connector |
| skill-flow-hitl-smoke-node-placed | SUCCESS | 1.000 | 265.8s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, lifecycle:generate, shape:single-node, node:hitl |
| skill-flow-bellevue-weather | SUCCESS | 1.000 | 381.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:decision, feature:http, ipe |
| skill-flow-interactive-customer-escalation-triage | FAILURE | 0.448 | 354.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, feature:escalation, feature:conversational |
| skill-flow-ipe-multiselect | SUCCESS | 1.000 | 421.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-act-act365, ipe, mode:build |
| skill-flow-eval-inline-agent | SUCCESS | 1.000 | 584.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:inline-agent, feature:eval |
| skill-flow-outlook-trigger-inbox | SUCCESS | 1.000 | 418.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, feature:trigger, connector, mode:build, ipe |
| skill-flow-inline-agent-robust | SUCCESS | 1.000 | 326.9s | claude-sonnet-4-6 | uipath-maestro-flow, mode:build, lifecycle:generate, node:inline-agent |
| skill-flow-decision | SUCCESS | 1.000 | 247.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:decision |
| skill-flow-feet-inches | SUCCESS | 1.000 | 263.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:switch |
| skill-flow-slack-http-fallback | SUCCESS | 1.000 | 337.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:single-node, connector, uipath-salesforce-slack, feature:http, ipe |
| skill-flow-slack-weather-pipeline | SUCCESS | 1.000 | 743.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:decision, connector, feature:http |
| skill-flow-init-validate | SUCCESS | 1.000 | 131.4s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, lifecycle:generate |
| skill-flow-devcon-billing-dispute-resolution | FAILURE | 0.500 | 722.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, node:ixp, connector, path-to-ga |
| skill-flow-hitl-smoke-completed-port | SUCCESS | 1.000 | 226.3s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, mode:build, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-devcon-billing-dispute-analyst | FAILURE | 0.375 | 398.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, path-to-ga |
| skill-flow-move-node | SUCCESS | 1.000 | 165.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:decision |
| skill-flow-ipe-drive-to-slack | SUCCESS | 1.000 | 357.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, e2e, uipath-google-drive, uipath-salesforce-slack, ipe, mode:build |
| skill-flow-registry-discovery | SUCCESS | 1.000 | 124.1s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, lifecycle:discover, feature:registry |
| skill-flow-transform-map | SUCCESS | 1.000 | 313.3s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-devcon-billing-discrepancy-detector | FAILURE | 0.375 | 603.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, connector, path-to-ga |
| skill-flow-hitl-smoke-multi-outcome-routing | SUCCESS | 1.000 | 303.1s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-ipe-required-groups | SUCCESS | 1.000 | 302.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-microsoft-teams, ipe, mode:build |
| skill-flow-cli-dice-roller-simulated | SUCCESS | 1.000 | 245.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, simulation |
| skill-flow-remove-node | SUCCESS | 1.000 | 155.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node |
| skill-flow-trigger-with-filter | FAILURE | 0.000 | 113.1s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:discover, connector-trigger, uipath-microsoft-outlook365, filter, ipe |
| skill-flow-coded-agent | MAX_TURNS_EXHAUSTED | 0.000 | 581.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource, path-to-ga |
| skill-flow-customer-escalation-simulated | SUCCESS | 1.000 | 1445.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, node:decision, feature:trigger, connector, simulation |
| skill-flow-ipe-query-params | SUCCESS | 1.000 | 172.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-google-tasks, ipe, mode:build |
| skill-flow-ipe-jira-search-triage | FAILURE | 0.286 | 413.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:loop, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-scheduled-trigger | SUCCESS | 1.000 | 207.7s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:scheduled-trigger, feature:trigger |
| skill-flow-bindings-idempotent-reconfigure | SUCCESS | 1.000 | 363.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-summarize | SUCCESS | 1.000 | 200.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, node:summarize, context-grounding, mode:build |
| skill-flow-hitl-quality-brownfield-insert | SUCCESS | 1.000 | 348.9s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-hitl-quality-result-downstream | SUCCESS | 1.000 | 202.1s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-reading-list | SUCCESS | 1.000 | 227.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:transform |
| skill-flow-bindings-multi-connector-independence | SUCCESS | 1.000 | 317.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, bindings, regression |
| skill-flow-loop-multiply | SUCCESS | 1.000 | 259.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:loop |
| skill-flow-ipe-searchable-joins | SUCCESS | 1.000 | 427.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-salesforce, ipe, mode:build |
| skill-flow-add-node | SUCCESS | 1.000 | 118.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:edit, shape:multi-node |
| skill-flow-ipe-ceql-where | SUCCESS | 1.000 | 576.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, connector, ceql, filter, uipath-microsoft-azureactivedirectory, ipe, mode:build |
| skill-flow-subflow | SUCCESS | 1.000 | 221.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:subflow |
| skill-flow-ixp-routing-listing/r01 | SUCCESS | 1.000 | 60.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r02 | SUCCESS | 1.000 | 69.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r03 | SUCCESS | 1.000 | 57.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r04 | SUCCESS | 1.000 | 60.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r05 | SUCCESS | 1.000 | 39.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r06 | SUCCESS | 1.000 | 59.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r07 | SUCCESS | 1.000 | 185.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r08 | SUCCESS | 1.000 | 52.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r09 | SUCCESS | 1.000 | 60.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r10 | SUCCESS | 1.000 | 45.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-rpa | SUCCESS | 1.000 | 270.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-lowcode-agent | SUCCESS | 1.000 | 214.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-group-to-subflow | SUCCESS | 1.000 | 479.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:subflow |
| skill-flow-wiki-pageviews | SUCCESS | 1.000 | 659.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:transform, feature:http |
| skill-flow-e2e-devcon-expense-approval | SUCCESS | 1.000 | 327.3s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, e2e, devcon |
| skill-flow-hitl-quality-boolean-decision | SUCCESS | 1.000 | 298.0s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-bellevue-weather-simulated | SUCCESS | 1.000 | 620.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, node:decision, feature:http, ipe, simulation |
| skill-flow-ixp-routing-negative/stripe-http | SUCCESS | 1.000 | 170.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/slack-summary | SUCCESS | 1.000 | 267.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/sf-update | SUCCESS | 1.000 | 562.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/http-webhook | SUCCESS | 1.000 | 208.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/gsheet-loop | SUCCESS | 1.000 | 264.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/queue-write | SUCCESS | 1.000 | 185.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/teams-decision | SUCCESS | 1.000 | 192.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/delay-email | SUCCESS | 1.000 | 216.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-paginated-reference-lookup | SUCCESS | 1.000 | 242.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, e2e, mode:build, lifecycle:generate, shape:multi-node, connector, uipath-salesforce-slack, feature:records |
| skill-flow-calculator | SUCCESS | 1.000 | 180.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node |
| skill-flow-eval-no-auto-upload | SUCCESS | 1.000 | 95.9s | claude-sonnet-4-6 | uipath-maestro-flow, mode:operate, lifecycle:execute, feature:eval |
| skill-flow-bindings-reconfigure-different-connection | SUCCESS | 1.000 | 325.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-ipe-jira-get-issue | SUCCESS | 1.000 | 288.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-ipe-dtl-load-by-default-true | SUCCESS | 1.000 | 243.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-microsoft-azure, ipe, mode:build |
| skill-flow-ipe-path-params | SUCCESS | 1.000 | 306.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-ipe-jira-create-issue | SUCCESS | 1.000 | 410.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-ixp-invoice-extraction-simulated | ERROR | 0.000 | 1378.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, node:ixp, connector, feature:http, simulation |
| skill-flow-ixp-integration-handle-routing | SUCCESS | 1.000 | 347.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:ixp, node:decision |
| skill-flow-delay | SUCCESS | 1.000 | 182.0s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:delay |
| skill-flow-openmeteo-weather | SUCCESS | 1.000 | 289.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node, connector, custom-codereval-openmeteoapis, ipe, custom-connector |
| skill-flow-bindings-no-duplicates | SUCCESS | 1.000 | 496.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-outlook-waitfor-email | SUCCESS | 1.000 | 237.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, feature:trigger, connector, uipath-microsoft-outlook365, filter, ipe, wait-for-event |
| skill-flow-devcon-billing-invoice-lookup | SUCCESS | 1.000 | 541.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, connector, path-to-ga |
| skill-flow-file-attachment-debug | SUCCESS | 1.000 | 219.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node |
| skill-flow-terminate | SUCCESS | 1.000 | 299.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:terminate |
| skill-flow-ipe-dtl-load-by-default-false | SUCCESS | 1.000 | 279.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-automaticc-woocommerce, ipe, mode:build |
| skill-flow-merge-parallel-sync | SUCCESS | 1.000 | 153.2s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:multi-node, node:merge |
| skill-flow-ipe-jira-lifecycle | SUCCESS | 1.000 | 677.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:loop, node:switch, node:decision, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-ixp-scaffold-multinode | ERROR | 0.000 | 603.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, node:ixp |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | SUCCESS | 1.000 | 735.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:ixp, connector, feature:http |
| skill-flow-devcon-billing-resolution-writer | SUCCESS | 1.000 | 242.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, path-to-ga |
| skill-flow-batch-transform | SUCCESS | 1.000 | 177.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, node:batch-transform, context-grounding, mode:build |
| skill-flow-ixp-routing/explicit | SUCCESS | 1.000 | 270.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/invoice-extraction | SUCCESS | 1.000 | 336.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/receipts | SUCCESS | 1.000 | 290.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/contracts | SUCCESS | 1.000 | 240.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/forms-classify | SUCCESS | 1.000 | 216.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-transform-filter | SUCCESS | 1.000 | 198.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-non-catalog-http-fallback | SUCCESS | 1.000 | 344.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, connector, uipath-uipath-http, feature:http, ipe |
| skill-flow-customer-escalation | SUCCESS | 1.000 | 611.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:decision, feature:trigger, connector |
| skill-flow-expense-approval-simulated | SUCCESS | 1.000 | 604.2s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, e2e, mode:build, lifecycle:generate, devcon, simulation |
| skill-flow-ipe-enhanced-enum | SUCCESS | 1.000 | 390.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-automaticc-woocommerce, ipe, mode:build |
| skill-flow-hitl-quality-schema-design | SUCCESS | 1.000 | 292.7s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-add-output | SUCCESS | 1.000 | 68.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node |
| skill-flow-ixp-e2e-project-selection/aviation | SUCCESS | 1.000 | 386.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-ixp-e2e-project-selection/birth-certificate | SUCCESS | 1.000 | 340.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-eval-simulation-crud | SUCCESS | 1.000 | 137.1s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, feature:eval |
| skill-flow-slack-channel-description-simulated | SUCCESS | 1.000 | 610.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, connector, simulation |
| skill-flow-solution-select-ask | FAILURE | 0.714 | 131.7s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, simulation |
| skill-flow-eval-local-crud | SUCCESS | 1.000 | 147.5s | claude-sonnet-4-6 | uipath-maestro-flow, mode:build, lifecycle:generate, feature:eval |
| skill-flow-api-workflow | FAILURE | 0.000 | 163.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-hitl-schema-design-simulated | SUCCESS | 0.895 | 788.8s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, simulation |
| skill-flow-generic-dynamic-node | FAILURE | 0.429 | 499.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node, connector, uipath-servicenow-servicenow, ipe |
| skill-flow-ipe-generate-schema | FAILURE | 0.800 | 210.4s | claude-sonnet-4-6 | uipath-platform, integration, lifecycle:generate, shape:multi-node, connector, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-ipe-enum | SUCCESS | 1.000 | 460.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle-generate, shape-multi-node, connector, uipath-google-gmail, ipe, mode:build |
| skill-flow-update-node | SUCCESS | 1.000 | 99.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:decision |
| skill-flow-switch | SUCCESS | 1.000 | 221.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:switch |
| skill-flow-webhook-waitfor-parallel | SUCCESS | 1.000 | 282.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, connector, feature:trigger, feature:http, wait-for-event, uipath-http-webhook, ipe |
| skill-flow-eval-evaluator-type-choice | SUCCESS | 1.000 | 90.1s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:discover, feature:eval |
| skill-flow-transform-group-by | SUCCESS | 1.000 | 191.1s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-multi-city-weather | SUCCESS | 1.000 | 650.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:loop, feature:http |
| skill-flow-ixp-scaffold-minimal | SUCCESS | 1.000 | 316.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-ipe-complex-array | SUCCESS | 1.000 | 366.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, ipe, mode:build |
| skill-flow-dice-roller | SUCCESS | 1.000 | 163.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node |
| skill-flow-slack-channel-description | SUCCESS | 1.000 | 293.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, connector |
| skill-flow-hitl-smoke-node-placed | SUCCESS | 1.000 | 267.9s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, lifecycle:generate, shape:single-node, node:hitl |
| skill-flow-bellevue-weather | SUCCESS | 1.000 | 497.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:decision, feature:http, ipe |
| skill-flow-interactive-customer-escalation-triage | SUCCESS | 1.000 | 349.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, feature:escalation, feature:conversational |
| skill-flow-ipe-multiselect | SUCCESS | 1.000 | 374.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-act-act365, ipe, mode:build |
| skill-flow-eval-inline-agent | SUCCESS | 1.000 | 448.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:inline-agent, feature:eval |
| skill-flow-outlook-trigger-inbox | SUCCESS | 1.000 | 217.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, feature:trigger, connector, mode:build, ipe |
| skill-flow-inline-agent-robust | FAILURE | 0.905 | 393.5s | claude-sonnet-4-6 | uipath-maestro-flow, mode:build, lifecycle:generate, node:inline-agent |
| skill-flow-decision | SUCCESS | 1.000 | 234.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:decision |
| skill-flow-feet-inches | SUCCESS | 1.000 | 305.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:switch |
| skill-flow-slack-http-fallback | SUCCESS | 1.000 | 255.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:single-node, connector, uipath-salesforce-slack, feature:http, ipe |
| skill-flow-slack-weather-pipeline | MAX_TURNS_EXHAUSTED | 0.375 | 624.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:decision, connector, feature:http |
| skill-flow-init-validate | SUCCESS | 1.000 | 152.4s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, lifecycle:generate |
| skill-flow-devcon-billing-dispute-resolution | FAILURE | 0.500 | 703.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, node:ixp, connector, path-to-ga |
| skill-flow-hitl-smoke-completed-port | SUCCESS | 1.000 | 246.3s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, mode:build, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-devcon-billing-dispute-analyst | FAILURE | 0.375 | 376.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, path-to-ga |
| skill-flow-move-node | SUCCESS | 1.000 | 433.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:decision |
| skill-flow-ipe-drive-to-slack | SUCCESS | 1.000 | 380.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, e2e, uipath-google-drive, uipath-salesforce-slack, ipe, mode:build |
| skill-flow-registry-discovery | SUCCESS | 1.000 | 92.1s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, lifecycle:discover, feature:registry |
| skill-flow-transform-map | SUCCESS | 1.000 | 233.6s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-devcon-billing-discrepancy-detector | FAILURE | 0.375 | 1066.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, connector, path-to-ga |
| skill-flow-hitl-smoke-multi-outcome-routing | SUCCESS | 1.000 | 286.2s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-ipe-required-groups | SUCCESS | 1.000 | 293.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-microsoft-teams, ipe, mode:build |
| skill-flow-cli-dice-roller-simulated | SUCCESS | 1.000 | 284.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, simulation |
| skill-flow-remove-node | SUCCESS | 1.000 | 141.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node |
| skill-flow-trigger-with-filter | SUCCESS | 1.000 | 86.6s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:discover, connector-trigger, uipath-microsoft-outlook365, filter, ipe |
| skill-flow-coded-agent | MAX_TURNS_EXHAUSTED | 0.375 | 534.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource, path-to-ga |
| skill-flow-customer-escalation-simulated | SUCCESS | 1.000 | 1993.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, node:decision, feature:trigger, connector, simulation |
| skill-flow-ipe-query-params | SUCCESS | 1.000 | 165.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-google-tasks, ipe, mode:build |
| skill-flow-ipe-jira-search-triage | FAILURE | 0.286 | 380.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:loop, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-scheduled-trigger | SUCCESS | 1.000 | 185.0s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:scheduled-trigger, feature:trigger |
| skill-flow-bindings-idempotent-reconfigure | FAILURE | 0.938 | 480.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-summarize | SUCCESS | 1.000 | 217.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, node:summarize, context-grounding, mode:build |
| skill-flow-hitl-quality-brownfield-insert | SUCCESS | 1.000 | 423.6s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-hitl-quality-result-downstream | SUCCESS | 1.000 | 185.8s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-reading-list | SUCCESS | 1.000 | 239.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:transform |
| skill-flow-bindings-multi-connector-independence | SUCCESS | 1.000 | 242.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, bindings, regression |
| skill-flow-loop-multiply | SUCCESS | 1.000 | 270.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:loop |
| skill-flow-ipe-searchable-joins | SUCCESS | 1.000 | 347.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-salesforce, ipe, mode:build |
| skill-flow-add-node | SUCCESS | 1.000 | 106.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:edit, shape:multi-node |
| skill-flow-ipe-ceql-where | SUCCESS | 1.000 | 328.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, connector, ceql, filter, uipath-microsoft-azureactivedirectory, ipe, mode:build |
| skill-flow-subflow | SUCCESS | 1.000 | 219.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:subflow |
| skill-flow-ixp-routing-listing/r01 | SUCCESS | 1.000 | 59.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r02 | SUCCESS | 1.000 | 55.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r03 | SUCCESS | 1.000 | 50.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r04 | SUCCESS | 1.000 | 55.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r05 | SUCCESS | 1.000 | 50.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r06 | SUCCESS | 1.000 | 46.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r07 | SUCCESS | 1.000 | 48.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r08 | SUCCESS | 1.000 | 56.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r09 | SUCCESS | 1.000 | 43.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r10 | SUCCESS | 1.000 | 48.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-rpa | SUCCESS | 1.000 | 242.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-lowcode-agent | SUCCESS | 1.000 | 329.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-group-to-subflow | TIMEOUT | 0.000 | 907.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:subflow |
| skill-flow-wiki-pageviews | FAILURE | 0.615 | 560.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:transform, feature:http |
| skill-flow-e2e-devcon-expense-approval | SUCCESS | 1.000 | 305.8s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, e2e, devcon |
| skill-flow-hitl-quality-boolean-decision | SUCCESS | 1.000 | 340.9s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-bellevue-weather-simulated | SUCCESS | 0.889 | 942.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, node:decision, feature:http, ipe, simulation |
| skill-flow-ixp-routing-negative/stripe-http | SUCCESS | 1.000 | 187.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/slack-summary | SUCCESS | 1.000 | 257.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/sf-update | SUCCESS | 1.000 | 303.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/http-webhook | SUCCESS | 1.000 | 231.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/gsheet-loop | SUCCESS | 1.000 | 318.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/queue-write | SUCCESS | 1.000 | 168.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/teams-decision | SUCCESS | 1.000 | 216.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/delay-email | SUCCESS | 1.000 | 264.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-paginated-reference-lookup | SUCCESS | 1.000 | 213.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, e2e, mode:build, lifecycle:generate, shape:multi-node, connector, uipath-salesforce-slack, feature:records |
| skill-flow-calculator | FAILURE | 0.375 | 238.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node |
| skill-flow-eval-no-auto-upload | SUCCESS | 1.000 | 113.5s | claude-sonnet-4-6 | uipath-maestro-flow, mode:operate, lifecycle:execute, feature:eval |
| skill-flow-bindings-reconfigure-different-connection | SUCCESS | 1.000 | 374.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-ipe-jira-get-issue | SUCCESS | 1.000 | 403.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-ipe-dtl-load-by-default-true | SUCCESS | 1.000 | 250.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-microsoft-azure, ipe, mode:build |
| skill-flow-ipe-path-params | SUCCESS | 1.000 | 295.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-ipe-jira-create-issue | SUCCESS | 1.000 | 404.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-ixp-invoice-extraction-simulated | ERROR | 0.000 | 1378.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, node:ixp, connector, feature:http, simulation |
| skill-flow-ixp-integration-handle-routing | SUCCESS | 1.000 | 778.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:ixp, node:decision |
| skill-flow-delay | SUCCESS | 1.000 | 155.2s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:delay |
| skill-flow-openmeteo-weather | SUCCESS | 1.000 | 405.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node, connector, custom-codereval-openmeteoapis, ipe, custom-connector |
| skill-flow-bindings-no-duplicates | SUCCESS | 1.000 | 335.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-outlook-waitfor-email | SUCCESS | 1.000 | 247.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, feature:trigger, connector, uipath-microsoft-outlook365, filter, ipe, wait-for-event |
| skill-flow-devcon-billing-invoice-lookup | SUCCESS | 1.000 | 653.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, connector, path-to-ga |
| skill-flow-file-attachment-debug | SUCCESS | 1.000 | 203.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node |
| skill-flow-terminate | SUCCESS | 1.000 | 274.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:terminate |
| skill-flow-ipe-dtl-load-by-default-false | SUCCESS | 1.000 | 482.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-automaticc-woocommerce, ipe, mode:build |
| skill-flow-merge-parallel-sync | SUCCESS | 1.000 | 192.3s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:multi-node, node:merge |
| skill-flow-ipe-jira-lifecycle | FAILURE | 0.286 | 1215.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:loop, node:switch, node:decision, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-ixp-scaffold-multinode | SUCCESS | 1.000 | 372.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, node:ixp |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | SUCCESS | 1.000 | 460.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:ixp, connector, feature:http |
| skill-flow-devcon-billing-resolution-writer | SUCCESS | 1.000 | 341.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, path-to-ga |
| skill-flow-batch-transform | SUCCESS | 1.000 | 184.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, node:batch-transform, context-grounding, mode:build |
| skill-flow-ixp-routing/explicit | SUCCESS | 1.000 | 219.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/invoice-extraction | SUCCESS | 1.000 | 291.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/receipts | SUCCESS | 1.000 | 607.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/contracts | SUCCESS | 1.000 | 348.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/forms-classify | SUCCESS | 1.000 | 223.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-transform-filter | SUCCESS | 1.000 | 179.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-non-catalog-http-fallback | SUCCESS | 1.000 | 204.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, connector, uipath-uipath-http, feature:http, ipe |
| skill-flow-customer-escalation | SUCCESS | 1.000 | 734.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:decision, feature:trigger, connector |
| skill-flow-expense-approval-simulated | SUCCESS | 1.000 | 599.1s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, e2e, mode:build, lifecycle:generate, devcon, simulation |
| skill-flow-ipe-enhanced-enum | SUCCESS | 1.000 | 270.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-automaticc-woocommerce, ipe, mode:build |
| skill-flow-hitl-quality-schema-design | SUCCESS | 1.000 | 210.1s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-add-output | SUCCESS | 1.000 | 73.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node |
| skill-flow-ixp-e2e-project-selection/aviation | SUCCESS | 1.000 | 393.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-ixp-e2e-project-selection/birth-certificate | SUCCESS | 1.000 | 316.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-eval-simulation-crud | SUCCESS | 1.000 | 193.9s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, feature:eval |
| skill-flow-slack-channel-description-simulated | SUCCESS | 1.000 | 410.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, connector, simulation |
| skill-flow-solution-select-ask | FAILURE | 0.714 | 140.6s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, simulation |
| skill-flow-eval-local-crud | SUCCESS | 1.000 | 104.9s | claude-sonnet-4-6 | uipath-maestro-flow, mode:build, lifecycle:generate, feature:eval |
| skill-flow-api-workflow | SUCCESS | 1.000 | 227.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-hitl-schema-design-simulated | SUCCESS | 0.895 | 631.8s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, simulation |
| skill-flow-generic-dynamic-node | FAILURE | 0.429 | 439.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node, connector, uipath-servicenow-servicenow, ipe |
| skill-flow-ipe-generate-schema | SUCCESS | 1.000 | 234.4s | claude-sonnet-4-6 | uipath-platform, integration, lifecycle:generate, shape:multi-node, connector, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-ipe-enum | SUCCESS | 1.000 | 401.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle-generate, shape-multi-node, connector, uipath-google-gmail, ipe, mode:build |
| skill-flow-update-node | SUCCESS | 1.000 | 74.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:decision |
| skill-flow-switch | SUCCESS | 1.000 | 191.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:switch |
| skill-flow-webhook-waitfor-parallel | SUCCESS | 1.000 | 284.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, connector, feature:trigger, feature:http, wait-for-event, uipath-http-webhook, ipe |
| skill-flow-eval-evaluator-type-choice | SUCCESS | 1.000 | 91.7s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:discover, feature:eval |
| skill-flow-transform-group-by | SUCCESS | 1.000 | 205.4s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-multi-city-weather | SUCCESS | 1.000 | 484.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:loop, feature:http |
| skill-flow-ixp-scaffold-minimal | ERROR | 0.000 | 603.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-ipe-complex-array | SUCCESS | 1.000 | 307.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, ipe, mode:build |
| skill-flow-dice-roller | SUCCESS | 1.000 | 222.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node |
| skill-flow-slack-channel-description | SUCCESS | 1.000 | 273.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, connector |
| skill-flow-hitl-smoke-node-placed | SUCCESS | 1.000 | 172.0s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, lifecycle:generate, shape:single-node, node:hitl |
| skill-flow-bellevue-weather | SUCCESS | 1.000 | 492.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:decision, feature:http, ipe |
| skill-flow-interactive-customer-escalation-triage | FAILURE | 0.448 | 258.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, feature:escalation, feature:conversational |
| skill-flow-ipe-multiselect | SUCCESS | 1.000 | 386.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-act-act365, ipe, mode:build |
| skill-flow-eval-inline-agent | SUCCESS | 1.000 | 692.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:inline-agent, feature:eval |
| skill-flow-outlook-trigger-inbox | SUCCESS | 1.000 | 389.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, feature:trigger, connector, mode:build, ipe |
| skill-flow-inline-agent-robust | SUCCESS | 1.000 | 261.8s | claude-sonnet-4-6 | uipath-maestro-flow, mode:build, lifecycle:generate, node:inline-agent |
| skill-flow-decision | SUCCESS | 1.000 | 208.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:decision |
| skill-flow-feet-inches | SUCCESS | 1.000 | 284.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:switch |
| skill-flow-slack-http-fallback | FAILURE | 0.760 | 285.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:single-node, connector, uipath-salesforce-slack, feature:http, ipe |
| skill-flow-slack-weather-pipeline | SUCCESS | 1.000 | 834.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:decision, connector, feature:http |
| skill-flow-init-validate | SUCCESS | 1.000 | 115.7s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, lifecycle:generate |
| skill-flow-devcon-billing-dispute-resolution | FAILURE | 0.500 | 1153.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, node:ixp, connector, path-to-ga |
| skill-flow-hitl-smoke-completed-port | SUCCESS | 1.000 | 177.6s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, mode:build, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-devcon-billing-dispute-analyst | FAILURE | 0.375 | 486.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, path-to-ga |
| skill-flow-move-node | SUCCESS | 1.000 | 124.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:decision |
| skill-flow-ipe-drive-to-slack | SUCCESS | 1.000 | 369.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, e2e, uipath-google-drive, uipath-salesforce-slack, ipe, mode:build |
| skill-flow-registry-discovery | SUCCESS | 1.000 | 73.9s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, lifecycle:discover, feature:registry |
| skill-flow-transform-map | SUCCESS | 1.000 | 246.9s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-devcon-billing-discrepancy-detector | SUCCESS | 1.000 | 645.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, connector, path-to-ga |
| skill-flow-hitl-smoke-multi-outcome-routing | SUCCESS | 1.000 | 258.9s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-ipe-required-groups | SUCCESS | 1.000 | 304.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-microsoft-teams, ipe, mode:build |
| skill-flow-cli-dice-roller-simulated | SUCCESS | 1.000 | 1374.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, simulation |
| skill-flow-remove-node | SUCCESS | 1.000 | 120.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node |
| skill-flow-trigger-with-filter | SUCCESS | 1.000 | 110.4s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:discover, connector-trigger, uipath-microsoft-outlook365, filter, ipe |
| skill-flow-coded-agent | MAX_TURNS_EXHAUSTED | 0.375 | 341.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource, path-to-ga |
| skill-flow-customer-escalation-simulated | SUCCESS | 1.000 | 993.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, node:decision, feature:trigger, connector, simulation |
| skill-flow-ipe-query-params | SUCCESS | 1.000 | 198.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-google-tasks, ipe, mode:build |
| skill-flow-ipe-jira-search-triage | FAILURE | 0.286 | 372.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:loop, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-scheduled-trigger | SUCCESS | 1.000 | 214.1s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:scheduled-trigger, feature:trigger |
| skill-flow-bindings-idempotent-reconfigure | SUCCESS | 1.000 | 604.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-summarize | SUCCESS | 1.000 | 188.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, node:summarize, context-grounding, mode:build |
| skill-flow-hitl-quality-brownfield-insert | SUCCESS | 1.000 | 418.5s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-hitl-quality-result-downstream | SUCCESS | 1.000 | 223.2s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-reading-list | SUCCESS | 1.000 | 285.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:transform |
| skill-flow-bindings-multi-connector-independence | SUCCESS | 1.000 | 398.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, bindings, regression |
| skill-flow-loop-multiply | SUCCESS | 1.000 | 384.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:loop |
| skill-flow-ipe-searchable-joins | SUCCESS | 1.000 | 608.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-salesforce, ipe, mode:build |
| skill-flow-add-node | SUCCESS | 1.000 | 104.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:edit, shape:multi-node |
| skill-flow-ipe-ceql-where | SUCCESS | 1.000 | 534.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, connector, ceql, filter, uipath-microsoft-azureactivedirectory, ipe, mode:build |
| skill-flow-subflow | FAILURE | 0.375 | 202.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:subflow |
| skill-flow-ixp-routing-listing/r01 | SUCCESS | 1.000 | 51.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r02 | SUCCESS | 1.000 | 53.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r03 | SUCCESS | 1.000 | 44.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r04 | SUCCESS | 1.000 | 44.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r05 | SUCCESS | 1.000 | 52.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r06 | SUCCESS | 1.000 | 43.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r07 | SUCCESS | 1.000 | 72.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r08 | SUCCESS | 1.000 | 47.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r09 | SUCCESS | 1.000 | 46.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r10 | SUCCESS | 1.000 | 52.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-rpa | SUCCESS | 1.000 | 312.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-lowcode-agent | SUCCESS | 1.000 | 263.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-group-to-subflow | SUCCESS | 1.000 | 634.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:subflow |
| skill-flow-wiki-pageviews | SUCCESS | 1.000 | 568.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:transform, feature:http |
| skill-flow-e2e-devcon-expense-approval | SUCCESS | 1.000 | 424.4s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, e2e, devcon |
| skill-flow-hitl-quality-boolean-decision | SUCCESS | 1.000 | 181.4s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-bellevue-weather-simulated | SUCCESS | 1.000 | 456.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, node:decision, feature:http, ipe, simulation |
| skill-flow-ixp-routing-negative/stripe-http | SUCCESS | 1.000 | 180.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/slack-summary | SUCCESS | 1.000 | 217.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/sf-update | SUCCESS | 1.000 | 208.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/http-webhook | SUCCESS | 1.000 | 134.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/gsheet-loop | SUCCESS | 1.000 | 240.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/queue-write | SUCCESS | 1.000 | 177.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/teams-decision | SUCCESS | 1.000 | 167.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/delay-email | SUCCESS | 1.000 | 219.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-paginated-reference-lookup | SUCCESS | 1.000 | 212.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, e2e, mode:build, lifecycle:generate, shape:multi-node, connector, uipath-salesforce-slack, feature:records |
| skill-flow-calculator | SUCCESS | 1.000 | 293.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node |
| skill-flow-eval-no-auto-upload | SUCCESS | 1.000 | 112.7s | claude-sonnet-4-6 | uipath-maestro-flow, mode:operate, lifecycle:execute, feature:eval |
| skill-flow-bindings-reconfigure-different-connection | SUCCESS | 1.000 | 820.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-ipe-jira-get-issue | SUCCESS | 1.000 | 278.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-ipe-dtl-load-by-default-true | SUCCESS | 1.000 | 206.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-microsoft-azure, ipe, mode:build |
| skill-flow-ipe-path-params | SUCCESS | 1.000 | 391.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-ipe-jira-create-issue | SUCCESS | 1.000 | 562.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-ixp-invoice-extraction-simulated | SUCCESS | 1.000 | 1020.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, node:ixp, connector, feature:http, simulation |
| skill-flow-ixp-integration-handle-routing | SUCCESS | 1.000 | 741.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:ixp, node:decision |
| skill-flow-delay | SUCCESS | 1.000 | 162.0s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:delay |
| skill-flow-openmeteo-weather | SUCCESS | 1.000 | 380.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node, connector, custom-codereval-openmeteoapis, ipe, custom-connector |
| skill-flow-bindings-no-duplicates | SUCCESS | 1.000 | 566.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-outlook-waitfor-email | SUCCESS | 1.000 | 272.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, feature:trigger, connector, uipath-microsoft-outlook365, filter, ipe, wait-for-event |
| skill-flow-devcon-billing-invoice-lookup | SUCCESS | 1.000 | 923.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, connector, path-to-ga |
| skill-flow-file-attachment-debug | SUCCESS | 1.000 | 243.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node |
| skill-flow-terminate | SUCCESS | 1.000 | 259.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:terminate |
| skill-flow-ipe-dtl-load-by-default-false | SUCCESS | 1.000 | 282.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-automaticc-woocommerce, ipe, mode:build |
| skill-flow-merge-parallel-sync | SUCCESS | 1.000 | 171.0s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:multi-node, node:merge |
| skill-flow-ipe-jira-lifecycle | SUCCESS | 1.000 | 688.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:loop, node:switch, node:decision, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-ixp-scaffold-multinode | SUCCESS | 1.000 | 563.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, node:ixp |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | SUCCESS | 1.000 | 797.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:ixp, connector, feature:http |
| skill-flow-devcon-billing-resolution-writer | SUCCESS | 1.000 | 287.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, path-to-ga |
| skill-flow-batch-transform | SUCCESS | 1.000 | 159.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, node:batch-transform, context-grounding, mode:build |
| skill-flow-ixp-routing/explicit | SUCCESS | 1.000 | 239.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/invoice-extraction | SUCCESS | 1.000 | 317.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/receipts | SUCCESS | 1.000 | 242.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/contracts | SUCCESS | 1.000 | 293.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/forms-classify | SUCCESS | 1.000 | 276.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-transform-filter | SUCCESS | 1.000 | 172.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-non-catalog-http-fallback | FAILURE | 0.400 | 286.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, connector, uipath-uipath-http, feature:http, ipe |
| skill-flow-customer-escalation | SUCCESS | 1.000 | 452.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:decision, feature:trigger, connector |
| skill-flow-expense-approval-simulated | SUCCESS | 1.000 | 845.9s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, e2e, mode:build, lifecycle:generate, devcon, simulation |
| skill-flow-ipe-enhanced-enum | SUCCESS | 1.000 | 424.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-automaticc-woocommerce, ipe, mode:build |
| skill-flow-hitl-quality-schema-design | SUCCESS | 1.000 | 295.8s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-add-output | SUCCESS | 1.000 | 68.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node |
| skill-flow-ixp-e2e-project-selection/aviation | SUCCESS | 1.000 | 337.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-ixp-e2e-project-selection/birth-certificate | SUCCESS | 1.000 | 423.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-eval-simulation-crud | SUCCESS | 1.000 | 138.4s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, feature:eval |
| skill-flow-slack-channel-description-simulated | SUCCESS | 1.000 | 444.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, connector, simulation |
| skill-flow-solution-select-ask | FAILURE | 0.714 | 119.2s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, simulation |
| skill-flow-eval-local-crud | SUCCESS | 1.000 | 164.5s | claude-sonnet-4-6 | uipath-maestro-flow, mode:build, lifecycle:generate, feature:eval |
| skill-flow-api-workflow | SUCCESS | 1.000 | 241.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-hitl-schema-design-simulated | SUCCESS | 1.000 | 494.4s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, simulation |
| skill-flow-generic-dynamic-node | FAILURE | 0.429 | 627.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node, connector, uipath-servicenow-servicenow, ipe |
| skill-flow-ipe-generate-schema | SUCCESS | 1.000 | 284.7s | claude-sonnet-4-6 | uipath-platform, integration, lifecycle:generate, shape:multi-node, connector, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-ipe-enum | SUCCESS | 1.000 | 539.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle-generate, shape-multi-node, connector, uipath-google-gmail, ipe, mode:build |
| skill-flow-update-node | SUCCESS | 1.000 | 77.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:decision |
| skill-flow-switch | SUCCESS | 1.000 | 273.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:switch |
| skill-flow-webhook-waitfor-parallel | SUCCESS | 1.000 | 236.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, connector, feature:trigger, feature:http, wait-for-event, uipath-http-webhook, ipe |
| skill-flow-eval-evaluator-type-choice | SUCCESS | 1.000 | 88.5s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:discover, feature:eval |
| skill-flow-transform-group-by | SUCCESS | 1.000 | 182.0s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-multi-city-weather | SUCCESS | 1.000 | 427.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:loop, feature:http |
| skill-flow-ixp-scaffold-minimal | SUCCESS | 1.000 | 227.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-ipe-complex-array | SUCCESS | 1.000 | 365.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, ipe, mode:build |
| skill-flow-dice-roller | SUCCESS | 1.000 | 156.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node |
| skill-flow-slack-channel-description | SUCCESS | 1.000 | 315.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, connector |
| skill-flow-hitl-smoke-node-placed | SUCCESS | 1.000 | 233.2s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, lifecycle:generate, shape:single-node, node:hitl |
| skill-flow-bellevue-weather | SUCCESS | 1.000 | 382.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:decision, feature:http, ipe |
| skill-flow-interactive-customer-escalation-triage | SUCCESS | 1.000 | 310.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, feature:escalation, feature:conversational |
| skill-flow-ipe-multiselect | SUCCESS | 1.000 | 366.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-act-act365, ipe, mode:build |
| skill-flow-eval-inline-agent | SUCCESS | 1.000 | 699.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:inline-agent, feature:eval |
| skill-flow-outlook-trigger-inbox | SUCCESS | 1.000 | 225.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, feature:trigger, connector, mode:build, ipe |
| skill-flow-inline-agent-robust | SUCCESS | 1.000 | 395.1s | claude-sonnet-4-6 | uipath-maestro-flow, mode:build, lifecycle:generate, node:inline-agent |
| skill-flow-decision | SUCCESS | 1.000 | 226.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:decision |
| skill-flow-feet-inches | SUCCESS | 1.000 | 370.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:switch |
| skill-flow-slack-http-fallback | SUCCESS | 1.000 | 330.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:single-node, connector, uipath-salesforce-slack, feature:http, ipe |
| skill-flow-slack-weather-pipeline | MAX_TURNS_EXHAUSTED | 0.375 | 724.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:decision, connector, feature:http |
| skill-flow-init-validate | SUCCESS | 1.000 | 120.5s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, lifecycle:generate |
| skill-flow-devcon-billing-dispute-resolution | FAILURE | 0.500 | 1342.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, node:ixp, connector, path-to-ga |
| skill-flow-hitl-smoke-completed-port | SUCCESS | 1.000 | 246.1s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, mode:build, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-devcon-billing-dispute-analyst | FAILURE | 0.375 | 345.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, path-to-ga |
| skill-flow-move-node | SUCCESS | 1.000 | 372.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:decision |
| skill-flow-ipe-drive-to-slack | SUCCESS | 1.000 | 364.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, e2e, uipath-google-drive, uipath-salesforce-slack, ipe, mode:build |
| skill-flow-registry-discovery | FAILURE | 0.818 | 92.9s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, lifecycle:discover, feature:registry |
| skill-flow-transform-map | SUCCESS | 1.000 | 227.2s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-devcon-billing-discrepancy-detector | FAILURE | 0.375 | 582.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, connector, path-to-ga |
| skill-flow-hitl-smoke-multi-outcome-routing | SUCCESS | 1.000 | 215.1s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-ipe-required-groups | SUCCESS | 1.000 | 265.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-microsoft-teams, ipe, mode:build |
| skill-flow-cli-dice-roller-simulated | SUCCESS | 1.000 | 477.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, simulation |
| skill-flow-remove-node | SUCCESS | 1.000 | 308.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node |
| skill-flow-trigger-with-filter | SUCCESS | 1.000 | 284.4s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:discover, connector-trigger, uipath-microsoft-outlook365, filter, ipe |
| skill-flow-coded-agent | MAX_TURNS_EXHAUSTED | 0.375 | 320.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource, path-to-ga |
| skill-flow-customer-escalation-simulated | SUCCESS | 1.000 | 2308.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, node:decision, feature:trigger, connector, simulation |
| skill-flow-ipe-query-params | SUCCESS | 1.000 | 132.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-google-tasks, ipe, mode:build |
| skill-flow-ipe-jira-search-triage | FAILURE | 0.286 | 396.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:loop, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-scheduled-trigger | SUCCESS | 1.000 | 170.8s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:scheduled-trigger, feature:trigger |
| skill-flow-bindings-idempotent-reconfigure | SUCCESS | 1.000 | 352.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-summarize | SUCCESS | 1.000 | 193.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, node:summarize, context-grounding, mode:build |
| skill-flow-hitl-quality-brownfield-insert | SUCCESS | 1.000 | 407.3s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-hitl-quality-result-downstream | SUCCESS | 1.000 | 345.6s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-reading-list | SUCCESS | 1.000 | 311.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:transform |
| skill-flow-bindings-multi-connector-independence | SUCCESS | 1.000 | 340.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, bindings, regression |
| skill-flow-loop-multiply | SUCCESS | 1.000 | 297.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:loop |
| skill-flow-ipe-searchable-joins | SUCCESS | 1.000 | 505.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-salesforce, ipe, mode:build |
| skill-flow-add-node | SUCCESS | 1.000 | 150.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:edit, shape:multi-node |
| skill-flow-ipe-ceql-where | SUCCESS | 1.000 | 499.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, connector, ceql, filter, uipath-microsoft-azureactivedirectory, ipe, mode:build |
| skill-flow-subflow | SUCCESS | 1.000 | 280.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:subflow |
| skill-flow-ixp-routing-listing/r01 | FAILURE | 0.500 | 32.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r02 | SUCCESS | 1.000 | 56.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r03 | SUCCESS | 1.000 | 56.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r04 | SUCCESS | 1.000 | 60.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r05 | FAILURE | 0.500 | 48.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r06 | SUCCESS | 1.000 | 57.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r07 | SUCCESS | 1.000 | 79.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r08 | SUCCESS | 1.000 | 62.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r09 | SUCCESS | 1.000 | 61.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r10 | SUCCESS | 1.000 | 60.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-rpa | SUCCESS | 1.000 | 371.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-lowcode-agent | SUCCESS | 1.000 | 290.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-group-to-subflow | FAILURE | 0.000 | 409.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:subflow |
| skill-flow-wiki-pageviews | SUCCESS | 1.000 | 469.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:transform, feature:http |
| skill-flow-e2e-devcon-expense-approval | SUCCESS | 1.000 | 235.2s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, e2e, devcon |
| skill-flow-hitl-quality-boolean-decision | SUCCESS | 1.000 | 313.8s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-bellevue-weather-simulated | SUCCESS | 1.000 | 1359.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, node:decision, feature:http, ipe, simulation |
| skill-flow-ixp-routing-negative/stripe-http | SUCCESS | 1.000 | 210.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/slack-summary | SUCCESS | 1.000 | 303.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/sf-update | SUCCESS | 1.000 | 170.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/http-webhook | SUCCESS | 1.000 | 237.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/gsheet-loop | SUCCESS | 1.000 | 338.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/queue-write | SUCCESS | 1.000 | 175.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/teams-decision | SUCCESS | 1.000 | 241.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing-negative/delay-email | SUCCESS | 1.000 | 177.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-paginated-reference-lookup | SUCCESS | 1.000 | 259.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, e2e, mode:build, lifecycle:generate, shape:multi-node, connector, uipath-salesforce-slack, feature:records |
| skill-flow-calculator | SUCCESS | 1.000 | 315.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node |
| skill-flow-eval-no-auto-upload | SUCCESS | 1.000 | 121.5s | claude-sonnet-4-6 | uipath-maestro-flow, mode:operate, lifecycle:execute, feature:eval |
| skill-flow-bindings-reconfigure-different-connection | SUCCESS | 1.000 | 396.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-ipe-jira-get-issue | SUCCESS | 1.000 | 308.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-ipe-dtl-load-by-default-true | SUCCESS | 1.000 | 226.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-microsoft-azure, ipe, mode:build |
| skill-flow-ipe-path-params | SUCCESS | 1.000 | 350.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-ipe-jira-create-issue | SUCCESS | 1.000 | 396.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-ixp-invoice-extraction-simulated | SUCCESS | 1.000 | 1922.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, node:ixp, connector, feature:http, simulation |
| skill-flow-ixp-integration-handle-routing | SUCCESS | 1.000 | 430.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:ixp, node:decision |
| skill-flow-delay | SUCCESS | 1.000 | 189.2s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:delay |
| skill-flow-openmeteo-weather | SUCCESS | 1.000 | 188.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node, connector, custom-codereval-openmeteoapis, ipe, custom-connector |
| skill-flow-bindings-no-duplicates | SUCCESS | 1.000 | 562.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-outlook-waitfor-email | SUCCESS | 1.000 | 255.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, feature:trigger, connector, uipath-microsoft-outlook365, filter, ipe, wait-for-event |
| skill-flow-devcon-billing-invoice-lookup | SUCCESS | 1.000 | 601.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, connector, path-to-ga |
| skill-flow-file-attachment-debug | SUCCESS | 1.000 | 284.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node |
| skill-flow-terminate | SUCCESS | 1.000 | 264.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:terminate |
| skill-flow-ipe-dtl-load-by-default-false | SUCCESS | 1.000 | 363.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-automaticc-woocommerce, ipe, mode:build |
| skill-flow-merge-parallel-sync | SUCCESS | 1.000 | 207.3s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:multi-node, node:merge |
| skill-flow-ipe-jira-lifecycle | FAILURE | 0.286 | 1118.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:loop, node:switch, node:decision, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-ixp-scaffold-multinode | SUCCESS | 1.000 | 363.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, node:ixp |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | SUCCESS | 1.000 | 851.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:ixp, connector, feature:http |
| skill-flow-devcon-billing-resolution-writer | SUCCESS | 1.000 | 341.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, path-to-ga |
| skill-flow-batch-transform | SUCCESS | 1.000 | 167.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, node:batch-transform, context-grounding, mode:build |
| skill-flow-ixp-routing/explicit | SUCCESS | 1.000 | 254.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/invoice-extraction | SUCCESS | 1.000 | 403.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/receipts | SUCCESS | 1.000 | 247.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/contracts | SUCCESS | 1.000 | 293.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-ixp-routing/forms-classify | SUCCESS | 1.000 | 231.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:ixp |
| skill-flow-transform-filter | SUCCESS | 1.000 | 184.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-non-catalog-http-fallback | SUCCESS | 1.000 | 267.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, connector, uipath-uipath-http, feature:http, ipe |
| skill-flow-customer-escalation | SUCCESS | 1.000 | 851.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:decision, feature:trigger, connector |
| skill-flow-expense-approval-simulated | SUCCESS | 1.000 | 633.6s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, e2e, mode:build, lifecycle:generate, devcon, simulation |
| skill-flow-ipe-enhanced-enum | SUCCESS | 1.000 | 418.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-automaticc-woocommerce, ipe, mode:build |
| skill-flow-hitl-quality-schema-design | SUCCESS | 1.000 | 233.7s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-add-output | SUCCESS | 1.000 | 69.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node |
| skill-flow-ixp-e2e-project-selection/aviation | SUCCESS | 1.000 | 332.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-ixp-e2e-project-selection/birth-certificate | SUCCESS | 1.000 | 264.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-eval-simulation-crud | SUCCESS | 1.000 | 160.7s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, feature:eval |
| skill-flow-slack-channel-description-simulated | SUCCESS | 0.917 | 1633.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, connector, simulation |
| skill-flow-solution-select-ask | FAILURE | 0.714 | 131.8s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, simulation |
| skill-flow-eval-local-crud | SUCCESS | 1.000 | 162.1s | claude-sonnet-4-6 | uipath-maestro-flow, mode:build, lifecycle:generate, feature:eval |
| skill-flow-api-workflow | SUCCESS | 1.000 | 253.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-hitl-schema-design-simulated | SUCCESS | 0.895 | 336.4s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, mode:build, lifecycle:generate, shape:multi-node, node:hitl, simulation |
| skill-flow-generic-dynamic-node | FAILURE | 0.429 | 564.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:operate, lifecycle:generate, shape:single-node, connector, uipath-servicenow-servicenow, ipe |
| skill-flow-ipe-generate-schema | SUCCESS | 1.000 | 416.6s | claude-sonnet-4-6 | uipath-platform, integration, lifecycle:generate, shape:multi-node, connector, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-ipe-enum | SUCCESS | 1.000 | 378.5s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle-generate, shape-multi-node, connector, uipath-google-gmail, ipe, mode:build |
| skill-flow-update-node | FAILURE | 0.375 | 59.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:decision |
| skill-flow-switch | SUCCESS | 1.000 | 268.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:switch |
| skill-flow-webhook-waitfor-parallel | SUCCESS | 1.000 | 276.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, connector, feature:trigger, feature:http, wait-for-event, uipath-http-webhook, ipe |
| skill-flow-eval-evaluator-type-choice | SUCCESS | 1.000 | 154.5s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:discover, feature:eval |
| skill-flow-transform-group-by | SUCCESS | 1.000 | 189.1s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-multi-city-weather | SUCCESS | 1.000 | 634.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:loop, feature:http |
| skill-flow-ixp-scaffold-minimal | SUCCESS | 1.000 | 488.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:single-node, node:ixp |
| skill-flow-ipe-complex-array | SUCCESS | 1.000 | 329.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, ipe, mode:build |
| skill-flow-dice-roller | SUCCESS | 1.000 | 187.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node |
| skill-flow-slack-channel-description | SUCCESS | 1.000 | 300.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, connector |
| skill-flow-hitl-smoke-node-placed | SUCCESS | 1.000 | 184.8s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, lifecycle:generate, shape:single-node, node:hitl |
| skill-flow-bellevue-weather | SUCCESS | 1.000 | 567.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:decision, feature:http, ipe |
| skill-flow-interactive-customer-escalation-triage | SUCCESS | 1.000 | 718.7s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, feature:escalation, feature:conversational |
| skill-flow-ipe-multiselect | SUCCESS | 1.000 | 476.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-act-act365, ipe, mode:build |
| skill-flow-eval-inline-agent | SUCCESS | 1.000 | 420.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, node:inline-agent, feature:eval |
| skill-flow-outlook-trigger-inbox | SUCCESS | 1.000 | 254.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, feature:trigger, connector, mode:build, ipe |
| skill-flow-inline-agent-robust | SUCCESS | 1.000 | 228.6s | claude-sonnet-4-6 | uipath-maestro-flow, mode:build, lifecycle:generate, node:inline-agent |
| skill-flow-decision | SUCCESS | 1.000 | 215.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:decision |
| skill-flow-feet-inches | SUCCESS | 1.000 | 513.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:switch |
| skill-flow-slack-http-fallback | SUCCESS | 1.000 | 314.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:single-node, connector, uipath-salesforce-slack, feature:http, ipe |
| skill-flow-slack-weather-pipeline | MAX_TURNS_EXHAUSTED | 0.375 | 1119.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:decision, connector, feature:http |
| skill-flow-init-validate | SUCCESS | 1.000 | 88.5s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, lifecycle:generate |
| skill-flow-devcon-billing-dispute-resolution | FAILURE | 0.500 | 921.9s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, node:ixp, connector, path-to-ga |
| skill-flow-hitl-smoke-completed-port | SUCCESS | 1.000 | 286.8s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, mode:build, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-devcon-billing-dispute-analyst | FAILURE | 0.375 | 437.1s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, node:inline-agent, path-to-ga |
| skill-flow-move-node | SUCCESS | 1.000 | 245.2s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:decision |
| skill-flow-ipe-drive-to-slack | SUCCESS | 1.000 | 328.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, e2e, uipath-google-drive, uipath-salesforce-slack, ipe, mode:build |
| skill-flow-registry-discovery | SUCCESS | 1.000 | 87.9s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, lifecycle:discover, feature:registry |
| skill-flow-transform-map | SUCCESS | 1.000 | 183.1s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:transform, feature:transform |
| skill-flow-devcon-billing-discrepancy-detector | FAILURE | 0.375 | 635.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:execute, shape:multi-node, connector, path-to-ga |
| skill-flow-hitl-smoke-multi-outcome-routing | SUCCESS | 1.000 | 261.8s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, smoke, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-ipe-required-groups | SUCCESS | 1.000 | 252.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-microsoft-teams, ipe, mode:build |
| skill-flow-cli-dice-roller-simulated | ERROR | 0.000 | 1207.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:generate, shape:multi-node, simulation |
| skill-flow-remove-node | SUCCESS | 1.000 | 121.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node |
| skill-flow-trigger-with-filter | FAILURE | 0.000 | 72.5s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:discover, connector-trigger, uipath-microsoft-outlook365, filter, ipe |
| skill-flow-coded-agent | MAX_TURNS_EXHAUSTED | 0.000 | 323.4s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource, path-to-ga |
| skill-flow-customer-escalation-simulated | TIMEOUT | 0.000 | 2402.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:build, lifecycle:generate, shape:multi-node, node:decision, feature:trigger, connector, simulation |
| skill-flow-ipe-query-params | SUCCESS | 1.000 | 163.7s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-google-tasks, ipe, mode:build |
| skill-flow-ipe-jira-search-triage | FAILURE | 0.286 | 494.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, node:loop, connector, e2e, uipath-atlassian-jira, ipe, mode:build |
| skill-flow-scheduled-trigger | SUCCESS | 1.000 | 120.9s | claude-sonnet-4-6 | uipath-maestro-flow, smoke, mode:build, lifecycle:generate, shape:single-node, node:scheduled-trigger, feature:trigger |
| skill-flow-bindings-idempotent-reconfigure | SUCCESS | 1.000 | 400.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, connector, bindings, regression |
| skill-flow-summarize | SUCCESS | 1.000 | 184.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:single-node, node:summarize, context-grounding, mode:build |
| skill-flow-hitl-quality-brownfield-insert | SUCCESS | 1.000 | 325.1s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-hitl-quality-result-downstream | SUCCESS | 1.000 | 153.5s | claude-sonnet-4-6 | uipath-maestro-flow, uipath-human-in-the-loop, integration, lifecycle:generate, shape:multi-node, node:hitl |
| skill-flow-reading-list | SUCCESS | 1.000 | 318.6s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:transform |
| skill-flow-bindings-multi-connector-independence | SUCCESS | 1.000 | 495.6s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, bindings, regression |
| skill-flow-loop-multiply | SUCCESS | 1.000 | 249.5s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:multi-node, node:loop |
| skill-flow-ipe-searchable-joins | SUCCESS | 1.000 | 262.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, lifecycle:generate, shape:multi-node, connector, uipath-salesforce, ipe, mode:build |
| skill-flow-add-node | SUCCESS | 1.000 | 128.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, mode:build, lifecycle:edit, shape:multi-node |
| skill-flow-ipe-ceql-where | SUCCESS | 1.000 | 277.0s | claude-sonnet-4-6 | uipath-maestro-flow, integration, connector, ceql, filter, uipath-microsoft-azureactivedirectory, ipe, mode:build |
| skill-flow-subflow | SUCCESS | 1.000 | 255.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, node:subflow |
| skill-flow-ixp-routing-listing/r01 | SUCCESS | 1.000 | 55.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r02 | SUCCESS | 1.000 | 87.1s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r03 | SUCCESS | 1.000 | 59.9s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r04 | SUCCESS | 1.000 | 52.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r05 | FAILURE | 0.500 | 90.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r06 | SUCCESS | 1.000 | 50.2s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r07 | SUCCESS | 1.000 | 59.3s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r08 | SUCCESS | 1.000 | 51.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r09 | FAILURE | 0.500 | 46.8s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-ixp-routing-listing/r10 | SUCCESS | 1.000 | 59.4s | claude-sonnet-4-6 | uipath-maestro-flow, integration, mode:operate, lifecycle:discover, node:ixp |
| skill-flow-rpa | SUCCESS | 1.000 | 287.3s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-lowcode-agent | SUCCESS | 1.000 | 242.0s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:generate, shape:single-node, resource |
| skill-flow-group-to-subflow | FAILURE | 0.375 | 449.8s | claude-sonnet-4-6 | uipath-maestro-flow, e2e, lifecycle:edit, shape:multi-node, node:subflow |

## Run-time Notes

> **WARNING:** [skill-flow-ixp-routing-negative/gsheet-loop] max_turns exhausted
> **WARNING:** [skill-flow-paginated-reference-lookup] expected_turns exceeded: 32/30 (cumulative SDK turns)
> **WARNING:** [skill-flow-ixp-integration-handle-routing] expected_turns exceeded: 40/26 (cumulative SDK turns)
> **WARNING:** [skill-flow-ixp-scaffold-multinode] expected_turns exceeded: 27/24 (cumulative SDK turns)
> **WARNING:** [skill-flow-ipe-enhanced-enum] expected_turns exceeded: 36/35 (cumulative SDK turns)
> **WARNING:** [skill-flow-ipe-generate-schema] expected_turns exceeded: 41/39 (cumulative SDK turns)
> **WARNING:** [skill-flow-outlook-trigger-inbox] max_turns exhausted
> **WARNING:** [skill-flow-slack-http-fallback] expected_turns exceeded: 33/32 (cumulative SDK turns)
> **WARNING:** [skill-flow-slack-weather-pipeline] max_turns exhausted
> **WARNING:** [skill-flow-init-validate] expected_turns exceeded: 13/9 (cumulative SDK turns)
> **WARNING:** [skill-flow-move-node] expected_turns exceeded: 13/11 (cumulative SDK turns)
> **WARNING:** [skill-flow-registry-discovery] expected_turns exceeded: 14/9 (cumulative SDK turns)
> **WARNING:** [skill-flow-remove-node] expected_turns exceeded: 23/14 (cumulative SDK turns)
> **WARNING:** [skill-flow-coded-agent] max_turns exhausted
> **WARNING:** [skill-flow-coded-agent] expected_turns exceeded: 51/35 (cumulative SDK turns)
> **WARNING:** [skill-flow-ipe-ceql-where] expected_turns exceeded: 53/34 (cumulative SDK turns)
> **WARNING:** [skill-flow-ixp-routing-listing/r07] max_turns exhausted
> **WARNING:** [skill-flow-group-to-subflow] expected_turns exceeded: 19/13 (cumulative SDK turns)
> **WARNING:** [skill-flow-ixp-routing-negative/sf-update] max_turns exhausted
> **WARNING:** [skill-flow-ixp-routing-negative/gsheet-loop] max_turns exhausted
> **WARNING:** [skill-flow-ixp-routing-negative/queue-write] max_turns exhausted
> **WARNING:** [skill-flow-ixp-routing-negative/teams-decision] max_turns exhausted
> **WARNING:** [skill-flow-calculator] expected_turns exceeded: 19/18 (cumulative SDK turns)
> **WARNING:** [skill-flow-ixp-integration-handle-routing] expected_turns exceeded: 27/26 (cumulative SDK turns)
> **WARNING:** [skill-flow-hitl-quality-schema-design] expected_turns exceeded: 30/29 (cumulative SDK turns)
> **WARNING:** [skill-flow-slack-weather-pipeline] max_turns exhausted
> **WARNING:** [skill-flow-init-validate] expected_turns exceeded: 15/9 (cumulative SDK turns)
> **WARNING:** [skill-flow-move-node] expected_turns exceeded: 15/11 (cumulative SDK turns)
> **WARNING:** [skill-flow-remove-node] expected_turns exceeded: 16/14 (cumulative SDK turns)
> **WARNING:** [skill-flow-coded-agent] max_turns exhausted
> **WARNING:** [skill-flow-coded-agent] expected_turns exceeded: 59/35 (cumulative SDK turns)
> **WARNING:** [skill-flow-reading-list] expected_turns exceeded: 26/20 (cumulative SDK turns)
> **WARNING:** [skill-flow-ixp-routing-negative/http-webhook] max_turns exhausted
> **WARNING:** [skill-flow-ixp-routing-negative/gsheet-loop] max_turns exhausted
> **WARNING:** [skill-flow-ixp-integration-handle-routing] expected_turns exceeded: 41/26 (cumulative SDK turns)
> **WARNING:** [skill-flow-terminate] expected_turns exceeded: 29/27 (cumulative SDK turns)
> **WARNING:** [skill-flow-ipe-dtl-load-by-default-false] expected_turns exceeded: 60/51 (cumulative SDK turns)
> **WARNING:** [skill-flow-ixp-scaffold-multinode] expected_turns exceeded: 27/24 (cumulative SDK turns)
> **WARNING:** [skill-flow-eval-simulation-crud] expected_turns exceeded: 21/20 (cumulative SDK turns)
> **WARNING:** [skill-flow-eval-inline-agent] expected_turns exceeded: 39/30 (cumulative SDK turns)
> **WARNING:** [skill-flow-outlook-trigger-inbox] max_turns exhausted
> **WARNING:** [skill-flow-slack-weather-pipeline] max_turns exhausted
> **WARNING:** [skill-flow-init-validate] expected_turns exceeded: 15/9 (cumulative SDK turns)
> **WARNING:** [skill-flow-ipe-drive-to-slack] expected_turns exceeded: 53/49 (cumulative SDK turns)
> **WARNING:** [skill-flow-remove-node] expected_turns exceeded: 17/14 (cumulative SDK turns)
> **WARNING:** [skill-flow-coded-agent] max_turns exhausted
> **WARNING:** [skill-flow-coded-agent] expected_turns exceeded: 45/35 (cumulative SDK turns)
> **WARNING:** [skill-flow-reading-list] expected_turns exceeded: 23/20 (cumulative SDK turns)
> **WARNING:** [skill-flow-loop-multiply] expected_turns exceeded: 26/22 (cumulative SDK turns)
> **WARNING:** [skill-flow-ixp-routing-negative/sf-update] max_turns exhausted
> **WARNING:** [skill-flow-calculator] expected_turns exceeded: 20/18 (cumulative SDK turns)
> **WARNING:** [skill-flow-ipe-jira-create-issue] expected_turns exceeded: 43/40 (cumulative SDK turns)
> **WARNING:** [skill-flow-ixp-integration-handle-routing] expected_turns exceeded: 38/26 (cumulative SDK turns)
> **WARNING:** [skill-flow-eval-inline-agent] expected_turns exceeded: 45/30 (cumulative SDK turns)
> **WARNING:** [skill-flow-slack-http-fallback] expected_turns exceeded: 34/32 (cumulative SDK turns)
> **WARNING:** [skill-flow-slack-weather-pipeline] max_turns exhausted
> **WARNING:** [skill-flow-slack-weather-pipeline] expected_turns exceeded: 52/51 (cumulative SDK turns)
> **WARNING:** [skill-flow-init-validate] expected_turns exceeded: 10/9 (cumulative SDK turns)
> **WARNING:** [skill-flow-move-node] expected_turns exceeded: 13/11 (cumulative SDK turns)
> **WARNING:** [skill-flow-registry-discovery] expected_turns exceeded: 10/9 (cumulative SDK turns)
> **WARNING:** [skill-flow-remove-node] expected_turns exceeded: 20/14 (cumulative SDK turns)
> **WARNING:** [skill-flow-trigger-with-filter] expected_turns exceeded: 25/7 (cumulative SDK turns)
> **WARNING:** [skill-flow-coded-agent] max_turns exhausted
> **WARNING:** [skill-flow-coded-agent] expected_turns exceeded: 44/35 (cumulative SDK turns)
> **WARNING:** [skill-flow-reading-list] expected_turns exceeded: 21/20 (cumulative SDK turns)
> **WARNING:** [skill-flow-loop-multiply] expected_turns exceeded: 28/22 (cumulative SDK turns)
> **WARNING:** [skill-flow-ipe-ceql-where] expected_turns exceeded: 38/34 (cumulative SDK turns)
> **WARNING:** [skill-flow-rpa] expected_turns exceeded: 28/26 (cumulative SDK turns)
> **WARNING:** [skill-flow-ixp-routing-negative/http-webhook] max_turns exhausted
> **WARNING:** [skill-flow-ipe-dtl-load-by-default-false] expected_turns exceeded: 53/51 (cumulative SDK turns)
> **WARNING:** [skill-flow-ixp-scaffold-multinode] expected_turns exceeded: 39/24 (cumulative SDK turns)
> **WARNING:** [skill-flow-webhook-waitfor-parallel] expected_turns exceeded: 39/35 (cumulative SDK turns)
> **WARNING:** [skill-flow-eval-evaluator-type-choice] expected_turns exceeded: 16/15 (cumulative SDK turns)
> **WARNING:** [skill-flow-slack-channel-description] max_turns exhausted
> **WARNING:** [skill-flow-slack-http-fallback] expected_turns exceeded: 40/32 (cumulative SDK turns)
> **WARNING:** [skill-flow-slack-weather-pipeline] max_turns exhausted
> **WARNING:** [skill-flow-init-validate] expected_turns exceeded: 15/9 (cumulative SDK turns)
> **WARNING:** [skill-flow-registry-discovery] expected_turns exceeded: 19/9 (cumulative SDK turns)
> **WARNING:** [skill-flow-remove-node] expected_turns exceeded: 19/14 (cumulative SDK turns)
> **WARNING:** [skill-flow-coded-agent] max_turns exhausted
> **WARNING:** [skill-flow-coded-agent] expected_turns exceeded: 47/35 (cumulative SDK turns)
> **WARNING:** [skill-flow-group-to-subflow] expected_turns exceeded: 18/13 (cumulative SDK turns)


## Generation Metrics

| Task ID | Total Latency | Turns | Asst Turns | Avg Turn Latency |
|---------|---------------|-------|------------|------------------|
| skill-flow-wiki-pageviews | 709.3s | 1 | 43 | 647.5s |
| skill-flow-e2e-devcon-expense-approval | 346.5s | 1 | 29 | 330.7s |
| skill-flow-hitl-quality-boolean-decision | 287.2s | 1 | 36 | 269.6s |
| skill-flow-bellevue-weather-simulated | 526.5s | 4 | 67 | 100.5s |
| skill-flow-ixp-routing-negative/stripe-http | 241.4s | 1 | 32 | 230.3s |
| skill-flow-ixp-routing-negative/slack-summary | 213.0s | 1 | 23 | 203.1s |
| skill-flow-ixp-routing-negative/sf-update | 348.9s | 1 | 34 | 340.9s |
| skill-flow-ixp-routing-negative/http-webhook | 208.7s | 1 | 36 | 199.0s |
| skill-flow-ixp-routing-negative/gsheet-loop | 381.5s | 1 | 46 | 372.5s |
| skill-flow-ixp-routing-negative/queue-write | 210.3s | 1 | 44 | 200.3s |
| skill-flow-ixp-routing-negative/teams-decision | 328.0s | 1 | 37 | 317.7s |
| skill-flow-ixp-routing-negative/delay-email | 342.4s | 1 | 28 | 331.5s |
| skill-flow-paginated-reference-lookup | 287.2s | 1 | 52 | 278.2s |
| skill-flow-calculator | 204.1s | 1 | 26 | 174.2s |
| skill-flow-eval-no-auto-upload | 114.4s | 1 | 19 | 104.1s |
| skill-flow-bindings-reconfigure-different-connection | 342.7s | 1 | 31 | 330.8s |
| skill-flow-ipe-jira-get-issue | 339.3s | 1 | 44 | 294.3s |
| skill-flow-ipe-dtl-load-by-default-true | 202.0s | 1 | 36 | 192.0s |
| skill-flow-ipe-path-params | 347.8s | 1 | 55 | 335.0s |
| skill-flow-ipe-jira-create-issue | 397.1s | 1 | 49 | 332.8s |
| skill-flow-ixp-invoice-extraction-simulated | 2410.2s | 8 | 224 | 269.0s |
| skill-flow-ixp-integration-handle-routing | 506.3s | 1 | 65 | 491.5s |
| skill-flow-delay | 248.0s | 1 | 26 | 232.1s |
| skill-flow-openmeteo-weather | 325.0s | 1 | 45 | 282.2s |
| skill-flow-bindings-no-duplicates | 415.8s | 1 | 55 | 404.3s |
| skill-flow-outlook-waitfor-email | 286.0s | 1 | 40 | 266.6s |
| skill-flow-devcon-billing-invoice-lookup | 830.6s | 1 | 88 | 743.6s |
| skill-flow-file-attachment-debug | 220.3s | 1 | 33 | 193.4s |
| skill-flow-terminate | 228.8s | 1 | 31 | 196.5s |
| skill-flow-ipe-dtl-load-by-default-false | 393.1s | 1 | 58 | 384.1s |
| skill-flow-merge-parallel-sync | 169.4s | 1 | 32 | 153.3s |
| skill-flow-ipe-jira-lifecycle | 883.9s | 1 | 54 | 826.3s |
| skill-flow-ixp-scaffold-multinode | 487.3s | 1 | 50 | 470.5s |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 675.0s | 1 | 92 | 660.4s |
| skill-flow-devcon-billing-resolution-writer | 291.7s | 1 | 34 | 245.5s |
| skill-flow-batch-transform | 165.5s | 1 | 23 | 153.9s |
| skill-flow-ixp-routing/explicit | 684.4s | 1 | 93 | 681.5s |
| skill-flow-ixp-routing/invoice-extraction | 362.1s | 1 | 62 | 358.5s |
| skill-flow-ixp-routing/receipts | 304.2s | 1 | 54 | 302.2s |
| skill-flow-ixp-routing/contracts | 259.7s | 1 | 48 | 257.2s |
| skill-flow-ixp-routing/forms-classify | 272.9s | 1 | 42 | 270.4s |
| skill-flow-transform-filter | 224.7s | 1 | 27 | 215.2s |
| skill-flow-non-catalog-http-fallback | 188.4s | 1 | 42 | 185.8s |
| skill-flow-customer-escalation | 616.6s | 1 | 61 | 609.2s |
| skill-flow-expense-approval-simulated | 982.0s | 6 | 60 | 142.5s |
| skill-flow-ipe-enhanced-enum | 411.3s | 1 | 61 | 407.9s |
| skill-flow-hitl-quality-schema-design | 242.0s | 1 | 27 | 233.1s |
| skill-flow-add-output | 62.5s | 1 | 11 | 27.1s |
| skill-flow-ixp-e2e-project-selection/aviation | 377.0s | 1 | 54 | 367.4s |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 292.9s | 1 | 53 | 281.1s |
| skill-flow-eval-simulation-crud | 112.8s | 1 | 27 | 107.4s |
| skill-flow-slack-channel-description-simulated | 388.2s | 5 | 48 | 57.3s |
| skill-flow-solution-select-ask | 130.9s | 3 | 27 | 38.5s |
| skill-flow-eval-local-crud | 112.5s | 1 | 14 | 107.7s |
| skill-flow-api-workflow | 247.7s | 1 | 36 | 208.8s |
| skill-flow-hitl-schema-design-simulated | 1143.3s | 6 | 97 | 172.6s |
| skill-flow-generic-dynamic-node | 1208.0s | 1 | 150 | 1200.5s |
| skill-flow-ipe-generate-schema | 296.1s | 1 | 59 | 292.3s |
| skill-flow-ipe-enum | 382.8s | 1 | 45 | 374.5s |
| skill-flow-update-node | 99.6s | 1 | 14 | 43.2s |
| skill-flow-switch | 247.6s | 1 | 26 | 221.0s |
| skill-flow-webhook-waitfor-parallel | 268.5s | 1 | 42 | 264.0s |
| skill-flow-eval-evaluator-type-choice | 110.5s | 1 | 18 | 107.9s |
| skill-flow-transform-group-by | 179.7s | 1 | 24 | 165.5s |
| skill-flow-multi-city-weather | 500.6s | 1 | 37 | 458.7s |
| skill-flow-ixp-scaffold-minimal | 320.2s | 1 | 47 | 305.8s |
| skill-flow-ipe-complex-array | 583.1s | 1 | 48 | 579.9s |
| skill-flow-dice-roller | 193.4s | 1 | 29 | 161.4s |
| skill-flow-slack-channel-description | 263.1s | 1 | 53 | 226.2s |
| skill-flow-hitl-smoke-node-placed | 265.8s | 1 | 31 | 252.7s |
| skill-flow-bellevue-weather | 381.2s | 1 | 51 | 347.2s |
| skill-flow-interactive-customer-escalation-triage | 354.5s | 5 | 34 | 54.1s |
| skill-flow-ipe-multiselect | 421.1s | 1 | 55 | 417.3s |
| skill-flow-eval-inline-agent | 584.3s | 1 | 52 | 581.6s |
| skill-flow-outlook-trigger-inbox | 418.5s | 1 | 75 | 407.1s |
| skill-flow-inline-agent-robust | 326.9s | 1 | 33 | 324.7s |
| skill-flow-decision | 247.1s | 1 | 28 | 198.2s |
| skill-flow-feet-inches | 263.7s | 1 | 34 | 222.5s |
| skill-flow-slack-http-fallback | 337.9s | 1 | 53 | 251.3s |
| skill-flow-slack-weather-pipeline | 743.7s | 1 | 65 | 700.4s |
| skill-flow-init-validate | 131.4s | 1 | 23 | 127.7s |
| skill-flow-devcon-billing-dispute-resolution | 722.4s | 1 | 105 | 676.0s |
| skill-flow-hitl-smoke-completed-port | 226.3s | 1 | 31 | 216.6s |
| skill-flow-devcon-billing-dispute-analyst | 398.9s | 1 | 43 | 328.7s |
| skill-flow-move-node | 165.3s | 1 | 24 | 130.2s |
| skill-flow-ipe-drive-to-slack | 357.8s | 1 | 57 | 355.0s |
| skill-flow-registry-discovery | 124.1s | 1 | 22 | 120.7s |
| skill-flow-transform-map | 313.3s | 1 | 38 | 303.3s |
| skill-flow-devcon-billing-discrepancy-detector | 603.4s | 1 | 72 | 569.5s |
| skill-flow-hitl-smoke-multi-outcome-routing | 303.1s | 1 | 35 | 291.5s |
| skill-flow-ipe-required-groups | 302.0s | 1 | 52 | 296.8s |
| skill-flow-cli-dice-roller-simulated | 245.0s | 2 | 26 | 84.5s |
| skill-flow-remove-node | 155.9s | 1 | 35 | 128.8s |
| skill-flow-trigger-with-filter | 113.1s | 1 | 12 | 107.0s |
| skill-flow-coded-agent | 581.2s | 1 | 75 | 268.9s |
| skill-flow-customer-escalation-simulated | 1445.5s | 6 | 148 | 224.7s |
| skill-flow-ipe-query-params | 172.5s | 1 | 33 | 170.0s |
| skill-flow-ipe-jira-search-triage | 413.3s | 1 | 32 | 373.1s |
| skill-flow-scheduled-trigger | 207.7s | 1 | 24 | 195.5s |
| skill-flow-bindings-idempotent-reconfigure | 363.4s | 1 | 44 | 356.0s |
| skill-flow-summarize | 200.0s | 1 | 27 | 190.7s |
| skill-flow-hitl-quality-brownfield-insert | 348.9s | 1 | 48 | 339.0s |
| skill-flow-hitl-quality-result-downstream | 202.1s | 1 | 30 | 191.7s |
| skill-flow-reading-list | 227.3s | 1 | 25 | 197.9s |
| skill-flow-bindings-multi-connector-independence | 317.0s | 1 | 37 | 310.4s |
| skill-flow-loop-multiply | 259.3s | 1 | 29 | 220.0s |
| skill-flow-ipe-searchable-joins | 427.2s | 1 | 47 | 422.9s |
| skill-flow-add-node | 118.5s | 1 | 22 | 79.0s |
| skill-flow-ipe-ceql-where | 576.0s | 1 | 88 | 573.7s |
| skill-flow-subflow | 221.8s | 1 | 25 | 188.0s |
| skill-flow-ixp-routing-listing/r01 | 60.2s | 1 | 12 | 58.2s |
| skill-flow-ixp-routing-listing/r02 | 69.8s | 1 | 17 | 67.7s |
| skill-flow-ixp-routing-listing/r03 | 57.6s | 1 | 13 | 55.5s |
| skill-flow-ixp-routing-listing/r04 | 60.4s | 1 | 10 | 58.4s |
| skill-flow-ixp-routing-listing/r05 | 39.5s | 1 | 8 | 34.6s |
| skill-flow-ixp-routing-listing/r06 | 59.4s | 1 | 8 | 55.9s |
| skill-flow-ixp-routing-listing/r07 | 185.8s | 1 | 38 | 180.8s |
| skill-flow-ixp-routing-listing/r08 | 52.7s | 1 | 9 | 47.3s |
| skill-flow-ixp-routing-listing/r09 | 60.9s | 1 | 13 | 55.2s |
| skill-flow-ixp-routing-listing/r10 | 45.3s | 1 | 8 | 40.9s |
| skill-flow-rpa | 270.9s | 1 | 31 | 221.5s |
| skill-flow-lowcode-agent | 214.2s | 1 | 33 | 175.4s |
| skill-flow-group-to-subflow | 479.7s | 1 | 33 | 438.3s |
| skill-flow-wiki-pageviews | 659.5s | 1 | 34 | 596.0s |
| skill-flow-e2e-devcon-expense-approval | 327.3s | 1 | 33 | 315.2s |
| skill-flow-hitl-quality-boolean-decision | 298.0s | 1 | 37 | 287.8s |
| skill-flow-bellevue-weather-simulated | 620.7s | 6 | 69 | 82.2s |
| skill-flow-ixp-routing-negative/stripe-http | 170.9s | 1 | 37 | 167.8s |
| skill-flow-ixp-routing-negative/slack-summary | 267.1s | 1 | 39 | 264.5s |
| skill-flow-ixp-routing-negative/sf-update | 562.6s | 1 | 55 | 558.7s |
| skill-flow-ixp-routing-negative/http-webhook | 208.9s | 1 | 33 | 205.6s |
| skill-flow-ixp-routing-negative/gsheet-loop | 264.0s | 1 | 39 | 260.5s |
| skill-flow-ixp-routing-negative/queue-write | 185.4s | 1 | 43 | 181.2s |
| skill-flow-ixp-routing-negative/teams-decision | 192.3s | 1 | 46 | 188.5s |
| skill-flow-ixp-routing-negative/delay-email | 216.0s | 1 | 36 | 212.4s |
| skill-flow-paginated-reference-lookup | 242.7s | 1 | 48 | 240.3s |
| skill-flow-calculator | 180.8s | 1 | 32 | 150.6s |
| skill-flow-eval-no-auto-upload | 95.9s | 1 | 22 | 91.0s |
| skill-flow-bindings-reconfigure-different-connection | 325.1s | 1 | 43 | 314.5s |
| skill-flow-ipe-jira-get-issue | 288.0s | 1 | 50 | 252.2s |
| skill-flow-ipe-dtl-load-by-default-true | 243.3s | 1 | 43 | 238.9s |
| skill-flow-ipe-path-params | 306.4s | 1 | 64 | 300.9s |
| skill-flow-ipe-jira-create-issue | 410.1s | 1 | 48 | 368.5s |
| skill-flow-ixp-invoice-extraction-simulated | 1378.3s | 5 | 96 | 267.6s |
| skill-flow-ixp-integration-handle-routing | 347.7s | 1 | 43 | 338.2s |
| skill-flow-delay | 182.0s | 1 | 26 | 173.1s |
| skill-flow-openmeteo-weather | 289.9s | 1 | 49 | 252.1s |
| skill-flow-bindings-no-duplicates | 496.0s | 1 | 65 | 490.7s |
| skill-flow-outlook-waitfor-email | 237.3s | 1 | 47 | 224.5s |
| skill-flow-devcon-billing-invoice-lookup | 541.6s | 1 | 70 | 469.0s |
| skill-flow-file-attachment-debug | 219.1s | 1 | 35 | 188.2s |
| skill-flow-terminate | 299.1s | 1 | 33 | 261.2s |
| skill-flow-ipe-dtl-load-by-default-false | 279.2s | 1 | 41 | 273.9s |
| skill-flow-merge-parallel-sync | 153.2s | 1 | 28 | 143.8s |
| skill-flow-ipe-jira-lifecycle | 677.9s | 1 | 61 | 624.8s |
| skill-flow-ixp-scaffold-multinode | 603.2s | 1 | 36 | 600.1s |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 735.5s | 1 | 94 | 724.6s |
| skill-flow-devcon-billing-resolution-writer | 242.1s | 1 | 27 | 202.9s |
| skill-flow-batch-transform | 177.4s | 1 | 25 | 162.2s |
| skill-flow-ixp-routing/explicit | 270.0s | 1 | 54 | 265.5s |
| skill-flow-ixp-routing/invoice-extraction | 336.0s | 1 | 60 | 329.6s |
| skill-flow-ixp-routing/receipts | 290.3s | 1 | 55 | 284.9s |
| skill-flow-ixp-routing/contracts | 240.8s | 1 | 48 | 237.0s |
| skill-flow-ixp-routing/forms-classify | 216.1s | 1 | 45 | 213.3s |
| skill-flow-transform-filter | 198.3s | 1 | 24 | 186.5s |
| skill-flow-non-catalog-http-fallback | 344.0s | 1 | 51 | 340.2s |
| skill-flow-customer-escalation | 611.7s | 1 | 93 | 599.4s |
| skill-flow-expense-approval-simulated | 604.2s | 5 | 67 | 99.6s |
| skill-flow-ipe-enhanced-enum | 390.9s | 1 | 52 | 388.0s |
| skill-flow-hitl-quality-schema-design | 292.7s | 1 | 44 | 286.2s |
| skill-flow-add-output | 68.9s | 1 | 11 | 29.5s |
| skill-flow-ixp-e2e-project-selection/aviation | 386.0s | 1 | 61 | 377.9s |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 340.0s | 1 | 60 | 332.5s |
| skill-flow-eval-simulation-crud | 137.1s | 1 | 12 | 132.7s |
| skill-flow-slack-channel-description-simulated | 610.7s | 5 | 77 | 103.0s |
| skill-flow-solution-select-ask | 131.7s | 3 | 20 | 36.8s |
| skill-flow-eval-local-crud | 147.5s | 1 | 16 | 142.8s |
| skill-flow-api-workflow | 163.1s | 1 | 33 | 151.8s |
| skill-flow-hitl-schema-design-simulated | 788.8s | 6 | 57 | 108.2s |
| skill-flow-generic-dynamic-node | 499.9s | 1 | 76 | 459.8s |
| skill-flow-ipe-generate-schema | 210.4s | 1 | 45 | 202.1s |
| skill-flow-ipe-enum | 460.9s | 1 | 45 | 450.5s |
| skill-flow-update-node | 99.5s | 1 | 16 | 60.0s |
| skill-flow-switch | 221.1s | 1 | 31 | 193.5s |
| skill-flow-webhook-waitfor-parallel | 282.7s | 1 | 41 | 277.3s |
| skill-flow-eval-evaluator-type-choice | 90.1s | 1 | 18 | 85.5s |
| skill-flow-transform-group-by | 191.1s | 1 | 26 | 181.1s |
| skill-flow-multi-city-weather | 650.0s | 1 | 32 | 595.9s |
| skill-flow-ixp-scaffold-minimal | 316.2s | 1 | 41 | 303.9s |
| skill-flow-ipe-complex-array | 366.7s | 1 | 42 | 361.8s |
| skill-flow-dice-roller | 163.3s | 1 | 30 | 140.5s |
| skill-flow-slack-channel-description | 293.3s | 1 | 51 | 262.0s |
| skill-flow-hitl-smoke-node-placed | 267.9s | 1 | 26 | 259.7s |
| skill-flow-bellevue-weather | 497.6s | 1 | 44 | 466.8s |
| skill-flow-interactive-customer-escalation-triage | 349.1s | 3 | 29 | 94.2s |
| skill-flow-ipe-multiselect | 374.3s | 1 | 38 | 371.1s |
| skill-flow-eval-inline-agent | 448.3s | 1 | 35 | 446.1s |
| skill-flow-outlook-trigger-inbox | 217.6s | 1 | 41 | 202.3s |
| skill-flow-inline-agent-robust | 393.5s | 1 | 30 | 391.4s |
| skill-flow-decision | 234.2s | 1 | 27 | 188.4s |
| skill-flow-feet-inches | 305.6s | 1 | 31 | 251.7s |
| skill-flow-slack-http-fallback | 255.4s | 1 | 50 | 230.1s |
| skill-flow-slack-weather-pipeline | 624.7s | 1 | 76 | 600.0s |
| skill-flow-init-validate | 152.4s | 1 | 27 | 150.3s |
| skill-flow-devcon-billing-dispute-resolution | 703.7s | 1 | 78 | 667.3s |
| skill-flow-hitl-smoke-completed-port | 246.3s | 1 | 30 | 234.4s |
| skill-flow-devcon-billing-dispute-analyst | 376.3s | 1 | 59 | 339.8s |
| skill-flow-move-node | 433.0s | 1 | 27 | 397.5s |
| skill-flow-ipe-drive-to-slack | 380.2s | 1 | 75 | 376.7s |
| skill-flow-registry-discovery | 92.1s | 1 | 14 | 87.5s |
| skill-flow-transform-map | 233.6s | 1 | 32 | 225.6s |
| skill-flow-devcon-billing-discrepancy-detector | 1066.6s | 1 | 52 | 1033.7s |
| skill-flow-hitl-smoke-multi-outcome-routing | 286.2s | 1 | 38 | 275.6s |
| skill-flow-ipe-required-groups | 293.0s | 1 | 48 | 287.3s |
| skill-flow-cli-dice-roller-simulated | 284.5s | 3 | 36 | 71.0s |
| skill-flow-remove-node | 141.9s | 1 | 25 | 113.1s |
| skill-flow-trigger-with-filter | 86.6s | 1 | 10 | 82.9s |
| skill-flow-coded-agent | 534.2s | 1 | 87 | 478.5s |
| skill-flow-customer-escalation-simulated | 1993.6s | 5 | 175 | 371.6s |
| skill-flow-ipe-query-params | 165.8s | 1 | 29 | 162.3s |
| skill-flow-ipe-jira-search-triage | 380.7s | 1 | 37 | 345.1s |
| skill-flow-scheduled-trigger | 185.0s | 1 | 30 | 173.1s |
| skill-flow-bindings-idempotent-reconfigure | 480.2s | 1 | 68 | 472.7s |
| skill-flow-summarize | 217.9s | 1 | 22 | 208.8s |
| skill-flow-hitl-quality-brownfield-insert | 423.6s | 1 | 38 | 412.8s |
| skill-flow-hitl-quality-result-downstream | 185.8s | 1 | 27 | 174.6s |
| skill-flow-reading-list | 239.8s | 1 | 47 | 209.7s |
| skill-flow-bindings-multi-connector-independence | 242.9s | 1 | 44 | 236.0s |
| skill-flow-loop-multiply | 270.6s | 1 | 28 | 236.1s |
| skill-flow-ipe-searchable-joins | 347.0s | 1 | 52 | 343.2s |
| skill-flow-add-node | 106.6s | 1 | 16 | 76.7s |
| skill-flow-ipe-ceql-where | 328.0s | 1 | 51 | 325.0s |
| skill-flow-subflow | 219.7s | 1 | 24 | 188.8s |
| skill-flow-ixp-routing-listing/r01 | 59.7s | 1 | 17 | 57.5s |
| skill-flow-ixp-routing-listing/r02 | 55.5s | 1 | 13 | 53.2s |
| skill-flow-ixp-routing-listing/r03 | 50.5s | 1 | 12 | 48.3s |
| skill-flow-ixp-routing-listing/r04 | 55.2s | 1 | 10 | 52.5s |
| skill-flow-ixp-routing-listing/r05 | 50.0s | 1 | 13 | 47.7s |
| skill-flow-ixp-routing-listing/r06 | 46.7s | 1 | 8 | 44.5s |
| skill-flow-ixp-routing-listing/r07 | 48.2s | 1 | 9 | 45.7s |
| skill-flow-ixp-routing-listing/r08 | 56.9s | 1 | 11 | 53.9s |
| skill-flow-ixp-routing-listing/r09 | 43.4s | 1 | 8 | 40.1s |
| skill-flow-ixp-routing-listing/r10 | 48.5s | 1 | 8 | 45.5s |
| skill-flow-rpa | 242.1s | 1 | 43 | 194.4s |
| skill-flow-lowcode-agent | 329.2s | 1 | 31 | 295.8s |
| skill-flow-group-to-subflow | 907.1s | 0 | 0 | N/A |
| skill-flow-wiki-pageviews | 560.8s | 1 | 35 | 507.0s |
| skill-flow-e2e-devcon-expense-approval | 305.8s | 1 | 32 | 293.9s |
| skill-flow-hitl-quality-boolean-decision | 340.9s | 1 | 36 | 330.6s |
| skill-flow-bellevue-weather-simulated | 942.6s | 8 | 91 | 95.9s |
| skill-flow-ixp-routing-negative/stripe-http | 187.7s | 1 | 41 | 181.5s |
| skill-flow-ixp-routing-negative/slack-summary | 257.6s | 1 | 38 | 253.4s |
| skill-flow-ixp-routing-negative/sf-update | 303.4s | 1 | 32 | 299.4s |
| skill-flow-ixp-routing-negative/http-webhook | 231.8s | 1 | 45 | 227.8s |
| skill-flow-ixp-routing-negative/gsheet-loop | 318.9s | 1 | 44 | 315.6s |
| skill-flow-ixp-routing-negative/queue-write | 168.8s | 1 | 27 | 165.8s |
| skill-flow-ixp-routing-negative/teams-decision | 216.5s | 1 | 26 | 213.4s |
| skill-flow-ixp-routing-negative/delay-email | 264.0s | 1 | 30 | 261.1s |
| skill-flow-paginated-reference-lookup | 213.7s | 1 | 44 | 209.2s |
| skill-flow-calculator | 238.2s | 1 | 24 | 154.2s |
| skill-flow-eval-no-auto-upload | 113.5s | 1 | 14 | 109.2s |
| skill-flow-bindings-reconfigure-different-connection | 374.3s | 1 | 46 | 367.8s |
| skill-flow-ipe-jira-get-issue | 403.1s | 1 | 50 | 373.1s |
| skill-flow-ipe-dtl-load-by-default-true | 250.3s | 1 | 40 | 245.1s |
| skill-flow-ipe-path-params | 295.5s | 1 | 46 | 288.6s |
| skill-flow-ipe-jira-create-issue | 404.5s | 1 | 50 | 376.0s |
| skill-flow-ixp-invoice-extraction-simulated | 1378.6s | 5 | 100 | 264.9s |
| skill-flow-ixp-integration-handle-routing | 778.9s | 1 | 73 | 770.3s |
| skill-flow-delay | 155.2s | 1 | 23 | 146.5s |
| skill-flow-openmeteo-weather | 405.0s | 1 | 43 | 372.5s |
| skill-flow-bindings-no-duplicates | 335.6s | 1 | 44 | 330.5s |
| skill-flow-outlook-waitfor-email | 247.7s | 1 | 41 | 236.1s |
| skill-flow-devcon-billing-invoice-lookup | 653.9s | 1 | 70 | 576.9s |
| skill-flow-file-attachment-debug | 203.2s | 1 | 39 | 174.6s |
| skill-flow-terminate | 274.7s | 1 | 50 | 253.8s |
| skill-flow-ipe-dtl-load-by-default-false | 482.8s | 1 | 79 | 479.5s |
| skill-flow-merge-parallel-sync | 192.3s | 1 | 35 | 182.7s |
| skill-flow-ipe-jira-lifecycle | 1215.2s | 1 | 51 | 611.0s |
| skill-flow-ixp-scaffold-multinode | 372.0s | 1 | 48 | 363.4s |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 460.0s | 1 | 90 | 453.4s |
| skill-flow-devcon-billing-resolution-writer | 341.7s | 1 | 28 | 291.6s |
| skill-flow-batch-transform | 184.2s | 1 | 24 | 175.5s |
| skill-flow-ixp-routing/explicit | 219.4s | 1 | 49 | 215.4s |
| skill-flow-ixp-routing/invoice-extraction | 291.3s | 1 | 55 | 287.4s |
| skill-flow-ixp-routing/receipts | 607.3s | 1 | 87 | 603.4s |
| skill-flow-ixp-routing/contracts | 348.7s | 1 | 50 | 343.9s |
| skill-flow-ixp-routing/forms-classify | 223.9s | 1 | 31 | 219.5s |
| skill-flow-transform-filter | 179.4s | 1 | 25 | 170.9s |
| skill-flow-non-catalog-http-fallback | 204.2s | 1 | 40 | 200.5s |
| skill-flow-customer-escalation | 734.5s | 1 | 76 | 724.5s |
| skill-flow-expense-approval-simulated | 599.1s | 5 | 57 | 103.0s |
| skill-flow-ipe-enhanced-enum | 270.0s | 1 | 48 | 266.6s |
| skill-flow-hitl-quality-schema-design | 210.1s | 1 | 37 | 199.1s |
| skill-flow-add-output | 73.1s | 1 | 13 | 42.0s |
| skill-flow-ixp-e2e-project-selection/aviation | 393.9s | 1 | 52 | 382.7s |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 316.1s | 1 | 54 | 307.5s |
| skill-flow-eval-simulation-crud | 193.9s | 1 | 34 | 190.6s |
| skill-flow-slack-channel-description-simulated | 410.7s | 5 | 55 | 67.4s |
| skill-flow-solution-select-ask | 140.6s | 3 | 22 | 42.5s |
| skill-flow-eval-local-crud | 104.9s | 1 | 25 | 102.5s |
| skill-flow-api-workflow | 227.6s | 1 | 28 | 200.4s |
| skill-flow-hitl-schema-design-simulated | 631.8s | 5 | 68 | 110.5s |
| skill-flow-generic-dynamic-node | 439.7s | 1 | 64 | 407.4s |
| skill-flow-ipe-generate-schema | 234.4s | 1 | 43 | 232.1s |
| skill-flow-ipe-enum | 401.7s | 1 | 56 | 397.0s |
| skill-flow-update-node | 74.7s | 1 | 11 | 38.8s |
| skill-flow-switch | 191.5s | 1 | 27 | 164.0s |
| skill-flow-webhook-waitfor-parallel | 284.6s | 1 | 53 | 280.4s |
| skill-flow-eval-evaluator-type-choice | 91.7s | 1 | 16 | 88.3s |
| skill-flow-transform-group-by | 205.4s | 1 | 44 | 194.1s |
| skill-flow-multi-city-weather | 484.9s | 1 | 30 | 438.4s |
| skill-flow-ixp-scaffold-minimal | 603.7s | 1 | 42 | 600.0s |
| skill-flow-ipe-complex-array | 307.1s | 1 | 50 | 302.9s |
| skill-flow-dice-roller | 222.3s | 1 | 29 | 199.1s |
| skill-flow-slack-channel-description | 273.3s | 1 | 45 | 239.5s |
| skill-flow-hitl-smoke-node-placed | 172.0s | 1 | 26 | 162.8s |
| skill-flow-bellevue-weather | 492.6s | 1 | 33 | 466.5s |
| skill-flow-interactive-customer-escalation-triage | 258.5s | 3 | 29 | 67.9s |
| skill-flow-ipe-multiselect | 386.7s | 1 | 46 | 383.3s |
| skill-flow-eval-inline-agent | 692.5s | 1 | 55 | 689.7s |
| skill-flow-outlook-trigger-inbox | 389.3s | 1 | 67 | 375.8s |
| skill-flow-inline-agent-robust | 261.8s | 1 | 37 | 259.1s |
| skill-flow-decision | 208.4s | 1 | 25 | 168.4s |
| skill-flow-feet-inches | 284.3s | 1 | 31 | 235.7s |
| skill-flow-slack-http-fallback | 285.3s | 1 | 51 | 260.1s |
| skill-flow-slack-weather-pipeline | 834.1s | 1 | 72 | 798.2s |
| skill-flow-init-validate | 115.7s | 1 | 26 | 113.6s |
| skill-flow-devcon-billing-dispute-resolution | 1153.4s | 1 | 148 | 1098.9s |
| skill-flow-hitl-smoke-completed-port | 177.6s | 1 | 26 | 168.0s |
| skill-flow-devcon-billing-dispute-analyst | 486.8s | 1 | 54 | 393.3s |
| skill-flow-move-node | 124.1s | 1 | 16 | 93.0s |
| skill-flow-ipe-drive-to-slack | 369.5s | 1 | 83 | 367.5s |
| skill-flow-registry-discovery | 73.9s | 1 | 13 | 71.4s |
| skill-flow-transform-map | 246.9s | 1 | 43 | 240.4s |
| skill-flow-devcon-billing-discrepancy-detector | 645.7s | 1 | 57 | 609.2s |
| skill-flow-hitl-smoke-multi-outcome-routing | 258.9s | 1 | 30 | 251.4s |
| skill-flow-ipe-required-groups | 304.8s | 1 | 47 | 301.7s |
| skill-flow-cli-dice-roller-simulated | 1374.8s | 8 | 112 | 154.7s |
| skill-flow-remove-node | 120.7s | 1 | 29 | 86.7s |
| skill-flow-trigger-with-filter | 110.4s | 1 | 13 | 106.3s |
| skill-flow-coded-agent | 341.9s | 1 | 73 | 294.1s |
| skill-flow-customer-escalation-simulated | 993.1s | 8 | 96 | 101.9s |
| skill-flow-ipe-query-params | 198.0s | 1 | 30 | 194.4s |
| skill-flow-ipe-jira-search-triage | 372.9s | 1 | 32 | 334.3s |
| skill-flow-scheduled-trigger | 214.1s | 1 | 23 | 204.0s |
| skill-flow-bindings-idempotent-reconfigure | 604.9s | 1 | 67 | 597.8s |
| skill-flow-summarize | 188.8s | 1 | 32 | 178.6s |
| skill-flow-hitl-quality-brownfield-insert | 418.5s | 1 | 50 | 406.9s |
| skill-flow-hitl-quality-result-downstream | 223.2s | 1 | 29 | 213.6s |
| skill-flow-reading-list | 285.5s | 1 | 37 | 253.7s |
| skill-flow-bindings-multi-connector-independence | 398.3s | 1 | 47 | 392.3s |
| skill-flow-loop-multiply | 384.1s | 1 | 45 | 352.7s |
| skill-flow-ipe-searchable-joins | 608.6s | 1 | 58 | 604.5s |
| skill-flow-add-node | 104.0s | 1 | 19 | 75.3s |
| skill-flow-ipe-ceql-where | 534.9s | 1 | 58 | 532.0s |
| skill-flow-subflow | 202.2s | 1 | 42 | 172.9s |
| skill-flow-ixp-routing-listing/r01 | 51.6s | 1 | 12 | 49.8s |
| skill-flow-ixp-routing-listing/r02 | 53.1s | 1 | 9 | 50.3s |
| skill-flow-ixp-routing-listing/r03 | 44.7s | 1 | 11 | 41.9s |
| skill-flow-ixp-routing-listing/r04 | 44.0s | 1 | 10 | 41.9s |
| skill-flow-ixp-routing-listing/r05 | 52.3s | 1 | 11 | 50.4s |
| skill-flow-ixp-routing-listing/r06 | 43.4s | 1 | 8 | 41.6s |
| skill-flow-ixp-routing-listing/r07 | 72.4s | 1 | 22 | 70.6s |
| skill-flow-ixp-routing-listing/r08 | 47.5s | 1 | 9 | 45.6s |
| skill-flow-ixp-routing-listing/r09 | 46.0s | 1 | 8 | 41.4s |
| skill-flow-ixp-routing-listing/r10 | 52.1s | 1 | 10 | 48.2s |
| skill-flow-rpa | 312.7s | 1 | 44 | 261.6s |
| skill-flow-lowcode-agent | 263.1s | 1 | 36 | 228.5s |
| skill-flow-group-to-subflow | 634.7s | 1 | 20 | 601.6s |
| skill-flow-wiki-pageviews | 568.8s | 1 | 33 | 506.7s |
| skill-flow-e2e-devcon-expense-approval | 424.4s | 1 | 40 | 416.2s |
| skill-flow-hitl-quality-boolean-decision | 181.4s | 1 | 38 | 174.7s |
| skill-flow-bellevue-weather-simulated | 456.2s | 4 | 37 | 94.0s |
| skill-flow-ixp-routing-negative/stripe-http | 180.3s | 1 | 32 | 177.9s |
| skill-flow-ixp-routing-negative/slack-summary | 217.5s | 1 | 30 | 215.4s |
| skill-flow-ixp-routing-negative/sf-update | 208.0s | 1 | 44 | 206.1s |
| skill-flow-ixp-routing-negative/http-webhook | 134.6s | 1 | 28 | 132.7s |
| skill-flow-ixp-routing-negative/gsheet-loop | 240.5s | 1 | 34 | 238.7s |
| skill-flow-ixp-routing-negative/queue-write | 177.7s | 1 | 36 | 174.8s |
| skill-flow-ixp-routing-negative/teams-decision | 167.5s | 1 | 34 | 164.7s |
| skill-flow-ixp-routing-negative/delay-email | 219.8s | 1 | 36 | 216.9s |
| skill-flow-paginated-reference-lookup | 212.9s | 1 | 46 | 210.6s |
| skill-flow-calculator | 293.2s | 1 | 37 | 264.7s |
| skill-flow-eval-no-auto-upload | 112.7s | 1 | 30 | 109.6s |
| skill-flow-bindings-reconfigure-different-connection | 820.4s | 1 | 66 | 813.6s |
| skill-flow-ipe-jira-get-issue | 278.1s | 1 | 44 | 246.9s |
| skill-flow-ipe-dtl-load-by-default-true | 206.2s | 1 | 41 | 204.1s |
| skill-flow-ipe-path-params | 391.9s | 1 | 69 | 387.2s |
| skill-flow-ipe-jira-create-issue | 562.8s | 1 | 70 | 531.8s |
| skill-flow-ixp-invoice-extraction-simulated | 1020.5s | 9 | 84 | 96.9s |
| skill-flow-ixp-integration-handle-routing | 741.3s | 1 | 61 | 732.2s |
| skill-flow-delay | 162.0s | 1 | 20 | 151.9s |
| skill-flow-openmeteo-weather | 380.6s | 1 | 55 | 352.3s |
| skill-flow-bindings-no-duplicates | 566.6s | 1 | 70 | 563.3s |
| skill-flow-outlook-waitfor-email | 272.4s | 1 | 47 | 262.3s |
| skill-flow-devcon-billing-invoice-lookup | 923.5s | 1 | 73 | 848.8s |
| skill-flow-file-attachment-debug | 243.4s | 1 | 36 | 219.3s |
| skill-flow-terminate | 259.5s | 1 | 28 | 232.4s |
| skill-flow-ipe-dtl-load-by-default-false | 282.7s | 1 | 60 | 280.6s |
| skill-flow-merge-parallel-sync | 171.0s | 1 | 37 | 163.2s |
| skill-flow-ipe-jira-lifecycle | 688.9s | 1 | 66 | 635.9s |
| skill-flow-ixp-scaffold-multinode | 563.1s | 1 | 31 | 556.9s |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 797.3s | 1 | 91 | 788.5s |
| skill-flow-devcon-billing-resolution-writer | 287.1s | 1 | 33 | 254.8s |
| skill-flow-batch-transform | 159.6s | 1 | 23 | 151.7s |
| skill-flow-ixp-routing/explicit | 239.8s | 1 | 39 | 237.3s |
| skill-flow-ixp-routing/invoice-extraction | 317.8s | 1 | 53 | 315.4s |
| skill-flow-ixp-routing/receipts | 242.6s | 1 | 48 | 240.4s |
| skill-flow-ixp-routing/contracts | 293.1s | 1 | 51 | 289.9s |
| skill-flow-ixp-routing/forms-classify | 276.1s | 1 | 44 | 273.3s |
| skill-flow-transform-filter | 172.0s | 1 | 26 | 162.7s |
| skill-flow-non-catalog-http-fallback | 286.8s | 1 | 51 | 283.7s |
| skill-flow-customer-escalation | 452.5s | 1 | 86 | 446.2s |
| skill-flow-expense-approval-simulated | 845.9s | 4 | 56 | 187.1s |
| skill-flow-ipe-enhanced-enum | 424.2s | 1 | 58 | 421.8s |
| skill-flow-hitl-quality-schema-design | 295.8s | 1 | 39 | 283.6s |
| skill-flow-add-output | 68.3s | 1 | 13 | 32.1s |
| skill-flow-ixp-e2e-project-selection/aviation | 337.4s | 1 | 44 | 330.3s |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 423.0s | 1 | 60 | 414.8s |
| skill-flow-eval-simulation-crud | 138.4s | 1 | 12 | 133.4s |
| skill-flow-slack-channel-description-simulated | 444.9s | 4 | 56 | 66.2s |
| skill-flow-solution-select-ask | 119.2s | 3 | 22 | 33.2s |
| skill-flow-eval-local-crud | 164.5s | 1 | 15 | 160.3s |
| skill-flow-api-workflow | 241.9s | 1 | 39 | 218.9s |
| skill-flow-hitl-schema-design-simulated | 494.4s | 6 | 70 | 67.0s |
| skill-flow-generic-dynamic-node | 627.1s | 1 | 79 | 595.5s |
| skill-flow-ipe-generate-schema | 284.7s | 1 | 55 | 282.0s |
| skill-flow-ipe-enum | 539.8s | 1 | 44 | 534.1s |
| skill-flow-update-node | 77.2s | 1 | 11 | 44.3s |
| skill-flow-switch | 273.8s | 1 | 36 | 248.8s |
| skill-flow-webhook-waitfor-parallel | 236.9s | 1 | 51 | 233.6s |
| skill-flow-eval-evaluator-type-choice | 88.5s | 1 | 18 | 85.2s |
| skill-flow-transform-group-by | 182.0s | 1 | 23 | 173.9s |
| skill-flow-multi-city-weather | 427.2s | 1 | 29 | 380.9s |
| skill-flow-ixp-scaffold-minimal | 227.5s | 1 | 41 | 220.4s |
| skill-flow-ipe-complex-array | 365.8s | 1 | 53 | 363.1s |
| skill-flow-dice-roller | 156.7s | 1 | 28 | 135.5s |
| skill-flow-slack-channel-description | 315.0s | 1 | 57 | 284.4s |
| skill-flow-hitl-smoke-node-placed | 233.2s | 1 | 32 | 223.3s |
| skill-flow-bellevue-weather | 382.0s | 1 | 43 | 348.1s |
| skill-flow-interactive-customer-escalation-triage | 310.7s | 3 | 31 | 77.6s |
| skill-flow-ipe-multiselect | 366.6s | 1 | 49 | 362.4s |
| skill-flow-eval-inline-agent | 699.9s | 1 | 64 | 695.7s |
| skill-flow-outlook-trigger-inbox | 225.8s | 1 | 49 | 211.9s |
| skill-flow-inline-agent-robust | 395.1s | 1 | 40 | 392.5s |
| skill-flow-decision | 226.4s | 1 | 28 | 184.7s |
| skill-flow-feet-inches | 370.0s | 1 | 28 | 325.2s |
| skill-flow-slack-http-fallback | 330.9s | 1 | 57 | 308.3s |
| skill-flow-slack-weather-pipeline | 724.9s | 1 | 82 | 690.1s |
| skill-flow-init-validate | 120.5s | 1 | 18 | 118.2s |
| skill-flow-devcon-billing-dispute-resolution | 1342.0s | 1 | 165 | 1226.9s |
| skill-flow-hitl-smoke-completed-port | 246.1s | 1 | 31 | 238.2s |
| skill-flow-devcon-billing-dispute-analyst | 345.3s | 1 | 55 | 283.9s |
| skill-flow-move-node | 372.3s | 1 | 23 | 334.5s |
| skill-flow-ipe-drive-to-slack | 364.5s | 1 | 63 | 362.0s |
| skill-flow-registry-discovery | 92.9s | 1 | 17 | 91.0s |
| skill-flow-transform-map | 227.2s | 1 | 31 | 219.5s |
| skill-flow-devcon-billing-discrepancy-detector | 582.2s | 1 | 56 | 553.1s |
| skill-flow-hitl-smoke-multi-outcome-routing | 215.1s | 1 | 33 | 206.1s |
| skill-flow-ipe-required-groups | 265.2s | 1 | 37 | 260.6s |
| skill-flow-cli-dice-roller-simulated | 477.4s | 5 | 45 | 75.1s |
| skill-flow-remove-node | 308.6s | 1 | 30 | 276.8s |
| skill-flow-trigger-with-filter | 284.4s | 1 | 45 | 281.3s |
| skill-flow-coded-agent | 320.4s | 1 | 64 | 289.7s |
| skill-flow-customer-escalation-simulated | 2308.3s | 6 | 255 | 367.6s |
| skill-flow-ipe-query-params | 132.5s | 1 | 30 | 127.5s |
| skill-flow-ipe-jira-search-triage | 396.5s | 1 | 49 | 361.8s |
| skill-flow-scheduled-trigger | 170.8s | 1 | 24 | 158.7s |
| skill-flow-bindings-idempotent-reconfigure | 352.1s | 1 | 56 | 346.0s |
| skill-flow-summarize | 193.9s | 1 | 21 | 183.6s |
| skill-flow-hitl-quality-brownfield-insert | 407.3s | 1 | 45 | 400.7s |
| skill-flow-hitl-quality-result-downstream | 345.6s | 1 | 41 | 338.4s |
| skill-flow-reading-list | 311.2s | 1 | 38 | 282.4s |
| skill-flow-bindings-multi-connector-independence | 340.1s | 1 | 57 | 335.0s |
| skill-flow-loop-multiply | 297.3s | 1 | 51 | 268.1s |
| skill-flow-ipe-searchable-joins | 505.9s | 1 | 56 | 501.9s |
| skill-flow-add-node | 150.0s | 1 | 20 | 113.3s |
| skill-flow-ipe-ceql-where | 499.2s | 1 | 63 | 494.7s |
| skill-flow-subflow | 280.4s | 1 | 24 | 254.9s |
| skill-flow-ixp-routing-listing/r01 | 32.8s | 1 | 9 | 30.3s |
| skill-flow-ixp-routing-listing/r02 | 56.7s | 1 | 9 | 54.5s |
| skill-flow-ixp-routing-listing/r03 | 56.8s | 1 | 12 | 54.7s |
| skill-flow-ixp-routing-listing/r04 | 60.0s | 1 | 11 | 57.7s |
| skill-flow-ixp-routing-listing/r05 | 48.3s | 1 | 13 | 46.3s |
| skill-flow-ixp-routing-listing/r06 | 57.0s | 1 | 8 | 54.2s |
| skill-flow-ixp-routing-listing/r07 | 79.5s | 1 | 16 | 77.0s |
| skill-flow-ixp-routing-listing/r08 | 62.5s | 1 | 12 | 56.6s |
| skill-flow-ixp-routing-listing/r09 | 61.4s | 1 | 10 | 56.8s |
| skill-flow-ixp-routing-listing/r10 | 60.6s | 1 | 12 | 55.3s |
| skill-flow-rpa | 371.0s | 1 | 49 | 319.7s |
| skill-flow-lowcode-agent | 290.1s | 1 | 26 | 253.1s |
| skill-flow-group-to-subflow | 409.8s | 1 | 12 | 395.7s |
| skill-flow-wiki-pageviews | 469.9s | 1 | 31 | 399.2s |
| skill-flow-e2e-devcon-expense-approval | 235.2s | 1 | 38 | 224.2s |
| skill-flow-hitl-quality-boolean-decision | 313.8s | 1 | 29 | 303.9s |
| skill-flow-bellevue-weather-simulated | 1359.4s | 9 | 122 | 131.4s |
| skill-flow-ixp-routing-negative/stripe-http | 210.9s | 1 | 29 | 207.6s |
| skill-flow-ixp-routing-negative/slack-summary | 303.4s | 1 | 36 | 299.0s |
| skill-flow-ixp-routing-negative/sf-update | 170.3s | 1 | 36 | 166.6s |
| skill-flow-ixp-routing-negative/http-webhook | 237.0s | 1 | 47 | 234.1s |
| skill-flow-ixp-routing-negative/gsheet-loop | 338.2s | 1 | 34 | 335.5s |
| skill-flow-ixp-routing-negative/queue-write | 175.7s | 1 | 39 | 173.8s |
| skill-flow-ixp-routing-negative/teams-decision | 241.9s | 1 | 31 | 239.9s |
| skill-flow-ixp-routing-negative/delay-email | 177.6s | 1 | 32 | 174.7s |
| skill-flow-paginated-reference-lookup | 259.2s | 1 | 40 | 255.8s |
| skill-flow-calculator | 315.2s | 1 | 27 | 292.4s |
| skill-flow-eval-no-auto-upload | 121.5s | 1 | 24 | 118.6s |
| skill-flow-bindings-reconfigure-different-connection | 396.0s | 1 | 54 | 388.2s |
| skill-flow-ipe-jira-get-issue | 308.7s | 1 | 46 | 271.9s |
| skill-flow-ipe-dtl-load-by-default-true | 226.9s | 1 | 55 | 222.4s |
| skill-flow-ipe-path-params | 350.9s | 1 | 50 | 333.9s |
| skill-flow-ipe-jira-create-issue | 396.0s | 1 | 60 | 312.0s |
| skill-flow-ixp-invoice-extraction-simulated | 1922.7s | 10 | 183 | 174.4s |
| skill-flow-ixp-integration-handle-routing | 430.0s | 1 | 37 | 420.5s |
| skill-flow-delay | 189.2s | 1 | 20 | 181.8s |
| skill-flow-openmeteo-weather | 188.4s | 1 | 45 | 161.7s |
| skill-flow-bindings-no-duplicates | 562.2s | 1 | 48 | 557.7s |
| skill-flow-outlook-waitfor-email | 255.7s | 1 | 42 | 243.6s |
| skill-flow-devcon-billing-invoice-lookup | 601.3s | 1 | 51 | 525.6s |
| skill-flow-file-attachment-debug | 284.6s | 1 | 35 | 256.6s |
| skill-flow-terminate | 264.9s | 1 | 30 | 232.6s |
| skill-flow-ipe-dtl-load-by-default-false | 363.9s | 1 | 77 | 360.6s |
| skill-flow-merge-parallel-sync | 207.3s | 1 | 27 | 195.1s |
| skill-flow-ipe-jira-lifecycle | 1118.6s | 1 | 71 | 514.7s |
| skill-flow-ixp-scaffold-multinode | 363.9s | 1 | 69 | 356.0s |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 851.2s | 1 | 97 | 840.7s |
| skill-flow-devcon-billing-resolution-writer | 341.2s | 1 | 39 | 304.4s |
| skill-flow-batch-transform | 167.7s | 1 | 25 | 155.9s |
| skill-flow-ixp-routing/explicit | 254.7s | 1 | 49 | 252.0s |
| skill-flow-ixp-routing/invoice-extraction | 403.0s | 1 | 56 | 400.9s |
| skill-flow-ixp-routing/receipts | 247.2s | 1 | 45 | 245.3s |
| skill-flow-ixp-routing/contracts | 293.8s | 1 | 37 | 290.8s |
| skill-flow-ixp-routing/forms-classify | 231.0s | 1 | 46 | 227.5s |
| skill-flow-transform-filter | 184.8s | 1 | 28 | 178.0s |
| skill-flow-non-catalog-http-fallback | 267.5s | 1 | 48 | 264.9s |
| skill-flow-customer-escalation | 851.8s | 1 | 99 | 844.2s |
| skill-flow-expense-approval-simulated | 633.6s | 6 | 53 | 89.5s |
| skill-flow-ipe-enhanced-enum | 418.7s | 1 | 38 | 412.9s |
| skill-flow-hitl-quality-schema-design | 233.7s | 1 | 32 | 221.4s |
| skill-flow-add-output | 69.0s | 1 | 11 | 31.9s |
| skill-flow-ixp-e2e-project-selection/aviation | 332.4s | 1 | 51 | 322.2s |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 264.2s | 1 | 47 | 250.3s |
| skill-flow-eval-simulation-crud | 160.7s | 1 | 12 | 154.8s |
| skill-flow-slack-channel-description-simulated | 1633.8s | 5 | 163 | 310.3s |
| skill-flow-solution-select-ask | 131.8s | 3 | 24 | 37.5s |
| skill-flow-eval-local-crud | 162.1s | 1 | 15 | 157.2s |
| skill-flow-api-workflow | 253.4s | 1 | 33 | 222.4s |
| skill-flow-hitl-schema-design-simulated | 336.4s | 3 | 49 | 86.2s |
| skill-flow-generic-dynamic-node | 564.6s | 1 | 71 | 555.1s |
| skill-flow-ipe-generate-schema | 416.6s | 1 | 61 | 414.5s |
| skill-flow-ipe-enum | 378.5s | 1 | 53 | 373.7s |
| skill-flow-update-node | 59.7s | 1 | 11 | 29.6s |
| skill-flow-switch | 268.2s | 1 | 40 | 240.4s |
| skill-flow-webhook-waitfor-parallel | 276.9s | 1 | 60 | 273.3s |
| skill-flow-eval-evaluator-type-choice | 154.5s | 1 | 25 | 151.2s |
| skill-flow-transform-group-by | 189.1s | 1 | 28 | 181.0s |
| skill-flow-multi-city-weather | 634.9s | 1 | 38 | 588.7s |
| skill-flow-ixp-scaffold-minimal | 488.2s | 1 | 37 | 477.5s |
| skill-flow-ipe-complex-array | 329.3s | 1 | 50 | 325.9s |
| skill-flow-dice-roller | 187.5s | 1 | 26 | 162.4s |
| skill-flow-slack-channel-description | 300.3s | 1 | 63 | 263.5s |
| skill-flow-hitl-smoke-node-placed | 184.8s | 1 | 27 | 175.9s |
| skill-flow-bellevue-weather | 567.1s | 1 | 43 | 535.9s |
| skill-flow-interactive-customer-escalation-triage | 718.7s | 5 | 47 | 122.0s |
| skill-flow-ipe-multiselect | 476.4s | 1 | 45 | 472.2s |
| skill-flow-eval-inline-agent | 420.4s | 1 | 34 | 417.1s |
| skill-flow-outlook-trigger-inbox | 254.4s | 1 | 56 | 242.2s |
| skill-flow-inline-agent-robust | 228.6s | 1 | 35 | 226.2s |
| skill-flow-decision | 215.3s | 1 | 25 | 172.9s |
| skill-flow-feet-inches | 513.8s | 1 | 40 | 469.5s |
| skill-flow-slack-http-fallback | 314.3s | 1 | 61 | 282.7s |
| skill-flow-slack-weather-pipeline | 1119.9s | 1 | 76 | 1096.0s |
| skill-flow-init-validate | 88.5s | 1 | 25 | 86.5s |
| skill-flow-devcon-billing-dispute-resolution | 921.9s | 1 | 135 | 879.6s |
| skill-flow-hitl-smoke-completed-port | 286.8s | 1 | 26 | 276.7s |
| skill-flow-devcon-billing-dispute-analyst | 437.1s | 1 | 47 | 393.7s |
| skill-flow-move-node | 245.2s | 1 | 10 | 218.2s |
| skill-flow-ipe-drive-to-slack | 328.7s | 1 | 66 | 325.8s |
| skill-flow-registry-discovery | 87.9s | 1 | 25 | 85.5s |
| skill-flow-transform-map | 183.1s | 1 | 27 | 174.9s |
| skill-flow-devcon-billing-discrepancy-detector | 635.3s | 1 | 118 | 610.5s |
| skill-flow-hitl-smoke-multi-outcome-routing | 261.8s | 1 | 26 | 255.9s |
| skill-flow-ipe-required-groups | 252.4s | 1 | 43 | 247.5s |
| skill-flow-cli-dice-roller-simulated | 1207.4s | 2 | 52 | 600.0s |
| skill-flow-remove-node | 121.6s | 1 | 33 | 92.0s |
| skill-flow-trigger-with-filter | 72.5s | 1 | 9 | 69.7s |
| skill-flow-coded-agent | 323.4s | 1 | 79 | 299.8s |
| skill-flow-customer-escalation-simulated | 2402.0s | 6 | 184 | 312.4s |
| skill-flow-ipe-query-params | 163.7s | 1 | 30 | 160.6s |
| skill-flow-ipe-jira-search-triage | 494.2s | 1 | 42 | 464.4s |
| skill-flow-scheduled-trigger | 120.9s | 1 | 20 | 111.9s |
| skill-flow-bindings-idempotent-reconfigure | 400.9s | 1 | 43 | 397.0s |
| skill-flow-summarize | 184.2s | 1 | 22 | 175.7s |
| skill-flow-hitl-quality-brownfield-insert | 325.1s | 1 | 40 | 319.6s |
| skill-flow-hitl-quality-result-downstream | 153.5s | 1 | 20 | 144.5s |
| skill-flow-reading-list | 318.6s | 1 | 33 | 297.3s |
| skill-flow-bindings-multi-connector-independence | 495.6s | 1 | 68 | 487.7s |
| skill-flow-loop-multiply | 249.5s | 1 | 27 | 221.2s |
| skill-flow-ipe-searchable-joins | 262.8s | 1 | 47 | 259.1s |
| skill-flow-add-node | 128.0s | 1 | 16 | 74.7s |
| skill-flow-ipe-ceql-where | 277.0s | 1 | 49 | 273.8s |
| skill-flow-subflow | 255.8s | 1 | 26 | 231.2s |
| skill-flow-ixp-routing-listing/r01 | 55.1s | 1 | 11 | 52.8s |
| skill-flow-ixp-routing-listing/r02 | 87.1s | 1 | 22 | 84.9s |
| skill-flow-ixp-routing-listing/r03 | 59.9s | 1 | 12 | 57.6s |
| skill-flow-ixp-routing-listing/r04 | 52.2s | 1 | 11 | 50.0s |
| skill-flow-ixp-routing-listing/r05 | 90.8s | 1 | 26 | 88.6s |
| skill-flow-ixp-routing-listing/r06 | 50.2s | 1 | 9 | 48.0s |
| skill-flow-ixp-routing-listing/r07 | 59.3s | 1 | 15 | 56.0s |
| skill-flow-ixp-routing-listing/r08 | 51.4s | 1 | 8 | 48.3s |
| skill-flow-ixp-routing-listing/r09 | 46.8s | 1 | 15 | 43.5s |
| skill-flow-ixp-routing-listing/r10 | 59.4s | 1 | 9 | 56.5s |
| skill-flow-rpa | 287.3s | 1 | 39 | 236.5s |
| skill-flow-lowcode-agent | 242.0s | 1 | 36 | 213.6s |
| skill-flow-group-to-subflow | 449.8s | 1 | 25 | 442.1s |


## Token Usage

**Total Tokens**: 857,305,258 (input: 152,065, output: 10,059,410)
**Cache Tokens**: write: 41,555,029, read: 805,538,754
**Total Cost**: $548.8403
**Avg Tokens/Task**: 1,396,262

| Task ID | Input (uncached) | Output | Cache Write | Cache Read | Total | Cost |
|---------|------------------|--------|-------------|------------|-------|------|
| skill-flow-wiki-pageviews | 18 | 39,102 | 79,872 | 1,028,448 | 1,147,440 | $1.1946 |
| skill-flow-e2e-devcon-expense-approval | 14 | 19,954 | 60,505 | 693,352 | 773,825 | $0.7343 |
| skill-flow-hitl-quality-boolean-decision | 14 | 17,018 | 74,765 | 710,268 | 802,065 | $0.7488 |
| skill-flow-bellevue-weather-simulated | 37 | 18,185 | 91,547 | 2,397,067 | 2,506,836 | $1.3353 |
| skill-flow-ixp-routing-negative/stripe-http | 15 | 11,473 | 57,384 | 741,738 | 810,610 | $0.6099 |
| skill-flow-ixp-routing-negative/slack-summary | 11 | 9,772 | 49,340 | 414,836 | 473,959 | $0.4561 |
| skill-flow-ixp-routing-negative/sf-update | 14 | 18,674 | 76,776 | 757,100 | 852,564 | $0.7952 |
| skill-flow-ixp-routing-negative/http-webhook | 19 | 7,732 | 59,934 | 1,018,997 | 1,086,682 | $0.6465 |
| skill-flow-ixp-routing-negative/gsheet-loop | 27 | 18,928 | 68,808 | 1,672,193 | 1,759,956 | $1.0437 |
| skill-flow-ixp-routing-negative/queue-write | 21 | 5,989 | 40,939 | 982,241 | 1,029,190 | $0.5381 |
| skill-flow-ixp-routing-negative/teams-decision | 17 | 16,496 | 54,122 | 783,552 | 854,187 | $0.6855 |
| skill-flow-ixp-routing-negative/delay-email | 12 | 18,672 | 55,990 | 483,184 | 557,858 | $0.6350 |
| skill-flow-paginated-reference-lookup | 22 | 12,095 | 80,190 | 1,477,427 | 1,569,734 | $0.9254 |
| skill-flow-calculator | 12 | 7,865 | 55,355 | 457,761 | 520,993 | $0.4629 |
| skill-flow-eval-no-auto-upload | 14 | 3,048 | 17,821 | 434,379 | 455,262 | $0.2429 |
| skill-flow-bindings-reconfigure-different-connection | 19 | 16,991 | 70,970 | 1,035,194 | 1,123,174 | $0.8316 |
| skill-flow-ipe-jira-get-issue | 21 | 12,109 | 75,419 | 1,339,021 | 1,426,570 | $0.8662 |
| skill-flow-ipe-dtl-load-by-default-true | 17 | 8,262 | 66,607 | 894,495 | 969,381 | $0.6421 |
| skill-flow-ipe-path-params | 24 | 16,169 | 73,680 | 1,459,031 | 1,548,904 | $0.9566 |
| skill-flow-ipe-jira-create-issue | 21 | 15,588 | 79,965 | 1,329,374 | 1,424,948 | $0.9326 |
| skill-flow-ixp-invoice-extraction-simulated | 3,444 | 93,509 | 295,570 | 12,378,660 | 12,771,183 | $6.2350 |
| skill-flow-ixp-integration-handle-routing | 30 | 26,623 | 72,409 | 2,039,492 | 2,138,554 | $1.2828 |
| skill-flow-delay | 11 | 12,976 | 44,600 | 407,894 | 465,481 | $0.4843 |
| skill-flow-openmeteo-weather | 22 | 11,015 | 73,019 | 1,431,585 | 1,515,641 | $0.8686 |
| skill-flow-bindings-no-duplicates | 32 | 20,217 | 71,807 | 2,110,780 | 2,202,836 | $1.2059 |
| skill-flow-outlook-waitfor-email | 19 | 11,352 | 68,599 | 1,013,129 | 1,093,099 | $0.7315 |
| skill-flow-devcon-billing-invoice-lookup | 46 | 35,980 | 106,422 | 3,903,606 | 4,046,054 | $2.1100 |
| skill-flow-file-attachment-debug | 15 | 8,381 | 58,861 | 685,234 | 752,491 | $0.5521 |
| skill-flow-terminate | 16 | 7,354 | 49,455 | 779,282 | 836,107 | $0.5296 |
| skill-flow-ipe-dtl-load-by-default-false | 22 | 18,844 | 89,481 | 1,584,468 | 1,692,815 | $1.0936 |
| skill-flow-merge-parallel-sync | 13 | 6,786 | 48,445 | 556,514 | 611,758 | $0.4505 |
| skill-flow-ipe-jira-lifecycle | 682 | 47,810 | 158,796 | 1,312,874 | 1,520,162 | $1.7085 |
| skill-flow-ixp-scaffold-multinode | 25 | 25,934 | 72,772 | 1,575,606 | 1,674,337 | $1.1347 |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 37 | 33,184 | 126,831 | 3,749,545 | 3,909,597 | $2.0984 |
| skill-flow-devcon-billing-resolution-writer | 15 | 14,729 | 64,669 | 778,520 | 857,933 | $0.6970 |
| skill-flow-batch-transform | 11 | 7,739 | 46,547 | 417,938 | 472,235 | $0.4161 |
| skill-flow-ixp-routing/explicit | 66 | 35,697 | 92,944 | 5,367,225 | 5,495,932 | $2.4944 |
| skill-flow-ixp-routing/invoice-extraction | 23 | 15,536 | 77,920 | 1,499,506 | 1,592,985 | $0.9752 |
| skill-flow-ixp-routing/receipts | 25 | 14,489 | 63,442 | 1,376,649 | 1,454,605 | $0.8683 |
| skill-flow-ixp-routing/contracts | 19 | 12,363 | 70,769 | 1,070,112 | 1,153,263 | $0.7719 |
| skill-flow-ixp-routing/forms-classify | 20 | 13,423 | 59,889 | 1,029,155 | 1,102,487 | $0.7347 |
| skill-flow-transform-filter | 13 | 10,963 | 48,868 | 556,733 | 616,577 | $0.5148 |
| skill-flow-non-catalog-http-fallback | 16 | 8,262 | 61,000 | 740,788 | 810,066 | $0.5750 |
| skill-flow-customer-escalation | 23 | 32,786 | 134,402 | 2,190,614 | 2,357,825 | $1.6531 |
| skill-flow-expense-approval-simulated | 36 | 54,681 | 100,688 | 1,962,926 | 2,118,331 | $1.7868 |
| skill-flow-ipe-enhanced-enum | 29 | 19,919 | 80,508 | 1,985,125 | 2,085,581 | $1.1963 |
| skill-flow-hitl-quality-schema-design | 14 | 14,733 | 60,418 | 583,462 | 658,627 | $0.6226 |
| skill-flow-add-output | 7 | 1,685 | 29,351 | 230,085 | 261,128 | $0.2044 |
| skill-flow-ixp-e2e-project-selection/aviation | 28 | 18,598 | 65,981 | 1,808,581 | 1,893,188 | $1.0691 |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 31 | 12,788 | 58,870 | 1,799,344 | 1,871,033 | $0.9525 |
| skill-flow-eval-simulation-crud | 18 | 3,457 | 22,340 | 597,393 | 623,208 | $0.3149 |
| skill-flow-slack-channel-description-simulated | 33 | 11,922 | 59,064 | 1,215,347 | 1,286,366 | $0.7650 |
| skill-flow-solution-select-ask | 17 | 4,345 | 29,738 | 456,996 | 491,096 | $0.3138 |
| skill-flow-eval-local-crud | 8 | 3,528 | 30,047 | 221,683 | 255,266 | $0.2321 |
| skill-flow-api-workflow | 14 | 10,789 | 52,715 | 605,687 | 669,205 | $0.5413 |
| skill-flow-hitl-schema-design-simulated | 123 | 59,178 | 113,178 | 4,454,995 | 4,627,474 | $2.6490 |
| skill-flow-generic-dynamic-node | 1,429 | 44,434 | 132,814 | 10,349,881 | 10,528,558 | $4.2738 |
| skill-flow-ipe-generate-schema | 36 | 12,404 | 74,323 | 2,454,623 | 2,541,386 | $1.2013 |
| skill-flow-ipe-enum | 19 | 19,575 | 75,766 | 1,190,816 | 1,286,176 | $0.9350 |
| skill-flow-update-node | 11 | 1,816 | 35,887 | 347,323 | 385,037 | $0.2660 |
| skill-flow-switch | 8,501 | 12,459 | 56,234 | 379,089 | 456,283 | $0.5370 |
| skill-flow-webhook-waitfor-parallel | 16 | 11,859 | 77,959 | 894,496 | 984,330 | $0.7386 |
| skill-flow-eval-evaluator-type-choice | 13 | 3,978 | 19,853 | 407,187 | 431,031 | $0.2563 |
| skill-flow-transform-group-by | 11 | 8,028 | 45,452 | 423,566 | 477,057 | $0.4180 |
| skill-flow-multi-city-weather | 20 | 30,313 | 83,607 | 1,307,858 | 1,421,798 | $1.1606 |
| skill-flow-ixp-scaffold-minimal | 19 | 16,202 | 87,223 | 1,152,773 | 1,256,217 | $0.9160 |
| skill-flow-ipe-complex-array | 20 | 33,841 | 79,715 | 1,249,997 | 1,363,573 | $1.1816 |
| skill-flow-dice-roller | 13 | 7,794 | 54,108 | 559,263 | 621,178 | $0.4876 |
| skill-flow-slack-channel-description | 27 | 9,204 | 83,855 | 1,779,949 | 1,873,035 | $0.9866 |
| skill-flow-hitl-smoke-node-placed | 14 | 13,108 | 48,880 | 624,239 | 686,241 | $0.5672 |
| skill-flow-bellevue-weather | 25 | 17,830 | 68,813 | 1,559,003 | 1,645,671 | $0.9933 |
| skill-flow-interactive-customer-escalation-triage | 23 | 17,057 | 65,852 | 857,859 | 940,791 | $0.7602 |
| skill-flow-ipe-multiselect | 27 | 19,619 | 86,376 | 1,892,449 | 1,998,471 | $1.1860 |
| skill-flow-eval-inline-agent | 22 | 34,390 | 83,515 | 1,613,061 | 1,730,988 | $1.3130 |
| skill-flow-outlook-trigger-inbox | 34 | 19,266 | 87,489 | 2,324,364 | 2,431,153 | $1.3145 |
| skill-flow-inline-agent-robust | 14 | 17,607 | 65,976 | 702,915 | 786,512 | $0.7224 |
| skill-flow-decision | 15 | 9,027 | 62,101 | 763,083 | 834,226 | $0.5973 |
| skill-flow-feet-inches | 17 | 10,252 | 50,506 | 736,340 | 797,115 | $0.5641 |
| skill-flow-slack-http-fallback | 24 | 8,287 | 92,930 | 1,766,868 | 1,868,109 | $1.0029 |
| skill-flow-slack-weather-pipeline | 766 | 40,013 | 114,743 | 2,369,980 | 2,525,502 | $1.7438 |
| skill-flow-init-validate | 14 | 5,378 | 29,105 | 505,897 | 540,394 | $0.3416 |
| skill-flow-devcon-billing-dispute-resolution | 55 | 35,746 | 128,395 | 6,329,345 | 6,493,541 | $2.9166 |
| skill-flow-hitl-smoke-completed-port | 14 | 11,842 | 53,364 | 550,775 | 615,995 | $0.5430 |
| skill-flow-devcon-billing-dispute-analyst | 13,049 | 18,020 | 69,413 | 890,326 | 990,808 | $0.8368 |
| skill-flow-move-node | 13 | 10,636 | 37,485 | 564,533 | 612,667 | $0.4695 |
| skill-flow-ipe-drive-to-slack | 23 | 17,113 | 92,880 | 1,746,544 | 1,856,560 | $1.1290 |
| skill-flow-registry-discovery | 10 | 4,007 | 34,471 | 282,332 | 320,820 | $0.2741 |
| skill-flow-transform-map | 16 | 16,913 | 44,558 | 719,186 | 780,673 | $0.6366 |
| skill-flow-devcon-billing-discrepancy-detector | 29 | 26,197 | 109,635 | 2,534,423 | 2,670,284 | $1.5645 |
| skill-flow-hitl-smoke-multi-outcome-routing | 709 | 16,752 | 51,829 | 842,821 | 912,111 | $0.7006 |
| skill-flow-ipe-required-groups | 27 | 12,215 | 73,200 | 1,761,746 | 1,847,188 | $0.9863 |
| skill-flow-cli-dice-roller-simulated | 16 | 7,456 | 42,543 | 547,145 | 597,160 | $0.4356 |
| skill-flow-remove-node | 24 | 7,122 | 55,869 | 1,292,757 | 1,355,772 | $0.7042 |
| skill-flow-trigger-with-filter | 8 | 5,804 | 29,756 | 225,291 | 260,859 | $0.2663 |
| skill-flow-coded-agent | 1,679 | 11,737 | 92,891 | 2,806,785 | 2,913,092 | $1.3715 |
| skill-flow-customer-escalation-simulated | 1,899 | 68,832 | 218,093 | 4,969,370 | 5,258,194 | $3.3468 |
| skill-flow-ipe-query-params | 13 | 6,380 | 55,154 | 566,714 | 628,261 | $0.4726 |
| skill-flow-ipe-jira-search-triage | 13 | 22,743 | 92,248 | 691,435 | 806,439 | $0.8945 |
| skill-flow-scheduled-trigger | 15 | 12,061 | 46,889 | 644,601 | 703,566 | $0.5502 |
| skill-flow-bindings-idempotent-reconfigure | 22 | 19,782 | 66,569 | 1,390,537 | 1,476,910 | $0.9636 |
| skill-flow-summarize | 12 | 8,759 | 43,109 | 483,412 | 535,292 | $0.4381 |
| skill-flow-hitl-quality-brownfield-insert | 23 | 18,704 | 72,107 | 1,527,449 | 1,618,283 | $1.0093 |
| skill-flow-hitl-quality-result-downstream | 17 | 10,464 | 67,221 | 850,993 | 928,695 | $0.6644 |
| skill-flow-reading-list | 12 | 10,317 | 49,166 | 503,561 | 563,056 | $0.4902 |
| skill-flow-bindings-multi-connector-independence | 18 | 14,670 | 70,816 | 1,000,118 | 1,085,622 | $0.7857 |
| skill-flow-loop-multiply | 14 | 13,214 | 50,143 | 560,532 | 623,903 | $0.5544 |
| skill-flow-ipe-searchable-joins | 20 | 21,948 | 79,510 | 1,221,556 | 1,323,034 | $0.9939 |
| skill-flow-add-node | 481 | 6,041 | 36,253 | 507,771 | 550,546 | $0.3803 |
| skill-flow-ipe-ceql-where | 46 | 26,458 | 95,369 | 3,932,772 | 4,054,645 | $1.9345 |
| skill-flow-subflow | 11 | 10,122 | 47,866 | 419,876 | 477,875 | $0.4573 |
| skill-flow-ixp-routing-listing/r01 | 9 | 2,986 | 23,932 | 179,104 | 206,031 | $0.1883 |
| skill-flow-ixp-routing-listing/r02 | 9 | 2,812 | 25,672 | 211,282 | 239,775 | $0.2019 |
| skill-flow-ixp-routing-listing/r03 | 11 | 2,228 | 35,916 | 225,309 | 263,464 | $0.2357 |
| skill-flow-ixp-routing-listing/r04 | 9 | 2,978 | 22,727 | 121,977 | 147,691 | $0.1665 |
| skill-flow-ixp-routing-listing/r05 | 7 | 1,369 | 18,432 | 121,674 | 141,482 | $0.1262 |
| skill-flow-ixp-routing-listing/r06 | 7 | 3,174 | 22,484 | 121,686 | 147,351 | $0.1685 |
| skill-flow-ixp-routing-listing/r07 | 21 | 5,652 | 32,193 | 688,044 | 725,910 | $0.4120 |
| skill-flow-ixp-routing-listing/r08 | 9 | 1,960 | 24,702 | 122,009 | 148,680 | $0.1587 |
| skill-flow-ixp-routing-listing/r09 | 10 | 2,497 | 25,360 | 210,778 | 238,645 | $0.1958 |
| skill-flow-ixp-routing-listing/r10 | 7 | 1,892 | 22,485 | 121,677 | 146,061 | $0.1492 |
| skill-flow-rpa | 16 | 12,230 | 46,225 | 700,249 | 758,720 | $0.5669 |
| skill-flow-lowcode-agent | 15 | 7,483 | 51,909 | 687,167 | 746,574 | $0.5131 |
| skill-flow-group-to-subflow | 19 | 32,349 | 60,812 | 1,091,137 | 1,184,317 | $1.0407 |
| skill-flow-wiki-pageviews | 15 | 38,283 | 83,128 | 817,774 | 939,200 | $1.1314 |
| skill-flow-e2e-devcon-expense-approval | 12 | 20,182 | 69,150 | 575,957 | 665,301 | $0.7349 |
| skill-flow-hitl-quality-boolean-decision | 22 | 14,914 | 46,020 | 929,898 | 990,854 | $0.6753 |
| skill-flow-bellevue-weather-simulated | 45 | 19,858 | 181,604 | 2,879,925 | 3,081,432 | $1.8430 |
| skill-flow-ixp-routing-negative/stripe-http | 17 | 6,182 | 58,294 | 883,578 | 948,071 | $0.5765 |
| skill-flow-ixp-routing-negative/slack-summary | 18 | 13,878 | 55,499 | 857,535 | 926,930 | $0.6736 |
| skill-flow-ixp-routing-negative/sf-update | 22 | 31,202 | 68,557 | 1,283,916 | 1,383,697 | $1.1104 |
| skill-flow-ixp-routing-negative/http-webhook | 14 | 9,262 | 58,386 | 668,344 | 736,006 | $0.5584 |
| skill-flow-ixp-routing-negative/gsheet-loop | 21 | 11,708 | 60,082 | 1,167,975 | 1,239,786 | $0.7514 |
| skill-flow-ixp-routing-negative/queue-write | 28 | 6,593 | 39,590 | 1,290,760 | 1,336,971 | $0.6347 |
| skill-flow-ixp-routing-negative/teams-decision | 24 | 7,310 | 51,790 | 1,159,789 | 1,218,913 | $0.6519 |
| skill-flow-ixp-routing-negative/delay-email | 18 | 8,504 | 48,796 | 866,524 | 923,842 | $0.5706 |
| skill-flow-paginated-reference-lookup | 21 | 9,422 | 81,345 | 1,334,419 | 1,425,207 | $0.8468 |
| skill-flow-calculator | 15 | 6,615 | 56,139 | 701,056 | 763,825 | $0.5201 |
| skill-flow-eval-no-auto-upload | 15 | 2,936 | 18,232 | 475,546 | 496,729 | $0.2551 |
| skill-flow-bindings-reconfigure-different-connection | 24 | 12,927 | 82,838 | 1,809,103 | 1,904,892 | $1.0474 |
| skill-flow-ipe-jira-get-issue | 21 | 12,070 | 83,347 | 1,363,450 | 1,458,888 | $0.9027 |
| skill-flow-ipe-dtl-load-by-default-true | 17 | 11,779 | 68,900 | 919,752 | 1,000,448 | $0.7110 |
| skill-flow-ipe-path-params | 34 | 12,082 | 91,420 | 2,878,278 | 2,981,814 | $1.3876 |
| skill-flow-ipe-jira-create-issue | 20 | 17,134 | 87,767 | 1,437,918 | 1,542,839 | $1.0176 |
| skill-flow-ixp-invoice-extraction-simulated | 4,080 | 77,885 | 196,547 | 1,941,036 | 2,219,548 | $2.4999 |
| skill-flow-ixp-integration-handle-routing | 19 | 18,021 | 57,634 | 990,046 | 1,065,720 | $0.7835 |
| skill-flow-delay | 13 | 10,044 | 45,277 | 537,301 | 592,635 | $0.4817 |
| skill-flow-openmeteo-weather | 26 | 9,876 | 74,325 | 1,768,417 | 1,852,644 | $0.9575 |
| skill-flow-bindings-no-duplicates | 29 | 27,742 | 74,798 | 1,946,829 | 2,049,398 | $1.2808 |
| skill-flow-outlook-waitfor-email | 20 | 9,425 | 76,904 | 1,173,640 | 1,259,989 | $0.7819 |
| skill-flow-devcon-billing-invoice-lookup | 30 | 21,896 | 108,000 | 2,559,881 | 2,689,807 | $1.5015 |
| skill-flow-file-attachment-debug | 19 | 7,476 | 59,745 | 1,035,804 | 1,103,044 | $0.6470 |
| skill-flow-terminate | 18 | 12,942 | 51,659 | 794,073 | 858,692 | $0.6261 |
| skill-flow-ipe-dtl-load-by-default-false | 15 | 12,751 | 74,215 | 837,991 | 924,972 | $0.7210 |
| skill-flow-merge-parallel-sync | 12 | 6,616 | 46,858 | 469,122 | 522,608 | $0.4157 |
| skill-flow-ipe-jira-lifecycle | 27 | 35,342 | 96,922 | 1,930,125 | 2,062,416 | $1.4727 |
| skill-flow-ixp-scaffold-multinode | 15 | 33,939 | 61,732 | 786,827 | 882,513 | $0.9767 |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 40 | 37,425 | 119,418 | 3,988,587 | 4,145,470 | $2.2059 |
| skill-flow-devcon-billing-resolution-writer | 12 | 11,429 | 73,921 | 573,672 | 659,034 | $0.6208 |
| skill-flow-batch-transform | 12 | 8,970 | 46,708 | 461,399 | 517,089 | $0.4482 |
| skill-flow-ixp-routing/explicit | 22 | 12,674 | 79,748 | 1,319,467 | 1,411,911 | $0.8851 |
| skill-flow-ixp-routing/invoice-extraction | 26 | 13,003 | 73,358 | 1,658,974 | 1,745,361 | $0.9679 |
| skill-flow-ixp-routing/receipts | 39 | 12,305 | 60,492 | 2,392,355 | 2,465,191 | $1.1292 |
| skill-flow-ixp-routing/contracts | 23 | 10,534 | 65,078 | 1,320,542 | 1,396,177 | $0.7983 |
| skill-flow-ixp-routing/forms-classify | 22 | 9,293 | 62,095 | 1,211,595 | 1,283,005 | $0.7358 |
| skill-flow-transform-filter | 12 | 8,622 | 48,391 | 483,571 | 540,596 | $0.4559 |
| skill-flow-non-catalog-http-fallback | 26 | 14,079 | 63,836 | 1,405,034 | 1,482,975 | $0.8722 |
| skill-flow-customer-escalation | 54 | 27,288 | 120,205 | 5,280,545 | 5,428,092 | $2.4444 |
| skill-flow-expense-approval-simulated | 40 | 24,164 | 100,084 | 2,505,090 | 2,629,378 | $1.4894 |
| skill-flow-ipe-enhanced-enum | 25 | 19,499 | 83,155 | 1,694,954 | 1,797,633 | $1.1129 |
| skill-flow-hitl-quality-schema-design | 31 | 15,023 | 45,006 | 1,378,691 | 1,438,751 | $0.8078 |
| skill-flow-add-output | 7 | 1,723 | 29,339 | 230,153 | 261,222 | $0.2049 |
| skill-flow-ixp-e2e-project-selection/aviation | 31 | 19,144 | 74,728 | 2,164,453 | 2,258,356 | $1.2168 |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 29 | 15,990 | 66,923 | 1,879,936 | 1,962,878 | $1.0549 |
| skill-flow-eval-simulation-crud | 8 | 3,921 | 21,092 | 203,373 | 228,394 | $0.1989 |
| skill-flow-slack-channel-description-simulated | 42 | 24,791 | 98,629 | 2,342,986 | 2,466,448 | $1.4447 |
| skill-flow-solution-select-ask | 16 | 2,966 | 29,205 | 397,225 | 429,412 | $0.2732 |
| skill-flow-eval-local-crud | 12 | 5,492 | 28,711 | 363,328 | 397,543 | $0.2991 |
| skill-flow-api-workflow | 644 | 8,448 | 54,538 | 719,956 | 783,586 | $0.5492 |
| skill-flow-hitl-schema-design-simulated | 3,143 | 36,774 | 81,463 | 1,601,333 | 1,722,713 | $1.3469 |
| skill-flow-generic-dynamic-node | 43 | 20,100 | 95,289 | 3,693,813 | 3,809,245 | $1.7671 |
| skill-flow-ipe-generate-schema | 23 | 7,355 | 76,227 | 1,547,348 | 1,630,953 | $0.8604 |
| skill-flow-ipe-enum | 19 | 25,014 | 86,063 | 1,272,554 | 1,383,650 | $1.0798 |
| skill-flow-update-node | 481 | 2,516 | 36,300 | 399,695 | 438,992 | $0.2952 |
| skill-flow-switch | 14 | 11,284 | 63,412 | 633,462 | 708,172 | $0.5971 |
| skill-flow-webhook-waitfor-parallel | 14 | 13,300 | 94,799 | 839,896 | 948,009 | $0.8070 |
| skill-flow-eval-evaluator-type-choice | 13 | 2,865 | 19,268 | 364,860 | 387,006 | $0.2247 |
| skill-flow-transform-group-by | 11 | 10,793 | 48,447 | 421,591 | 480,842 | $0.4701 |
| skill-flow-multi-city-weather | 15 | 39,247 | 75,149 | 716,391 | 830,802 | $1.0855 |
| skill-flow-ixp-scaffold-minimal | 22 | 14,881 | 72,833 | 1,311,316 | 1,399,052 | $0.8898 |
| skill-flow-ipe-complex-array | 19 | 19,257 | 81,421 | 1,164,147 | 1,264,844 | $0.9435 |
| skill-flow-dice-roller | 15 | 6,275 | 46,492 | 662,222 | 715,004 | $0.4672 |
| skill-flow-slack-channel-description | 23 | 12,914 | 75,725 | 1,470,150 | 1,558,812 | $0.9188 |
| skill-flow-hitl-smoke-node-placed | 13 | 16,331 | 47,921 | 473,869 | 538,134 | $0.5669 |
| skill-flow-bellevue-weather | 23 | 27,050 | 56,471 | 1,248,345 | 1,331,889 | $0.9921 |
| skill-flow-interactive-customer-escalation-triage | 15 | 17,646 | 65,393 | 557,588 | 640,642 | $0.6772 |
| skill-flow-ipe-multiselect | 18 | 21,037 | 79,536 | 1,040,458 | 1,141,049 | $0.9260 |
| skill-flow-eval-inline-agent | 17 | 27,389 | 77,743 | 1,025,082 | 1,130,231 | $1.0099 |
| skill-flow-outlook-trigger-inbox | 20 | 8,899 | 71,873 | 1,102,446 | 1,183,238 | $0.7338 |
| skill-flow-inline-agent-robust | 14 | 25,221 | 62,216 | 684,764 | 772,215 | $0.8171 |
| skill-flow-decision | 12 | 10,183 | 61,974 | 458,656 | 530,825 | $0.5228 |
| skill-flow-feet-inches | 14 | 15,140 | 49,710 | 630,350 | 695,214 | $0.6027 |
| skill-flow-slack-http-fallback | 24 | 7,199 | 98,455 | 1,842,996 | 1,948,674 | $1.0302 |
| skill-flow-slack-weather-pipeline | 31 | 32,280 | 116,548 | 2,926,987 | 3,075,846 | $1.7994 |
| skill-flow-init-validate | 17 | 6,371 | 31,094 | 627,843 | 665,325 | $0.4006 |
| skill-flow-devcon-billing-dispute-resolution | 31 | 38,638 | 129,500 | 3,329,580 | 3,497,749 | $2.0642 |
| skill-flow-hitl-smoke-completed-port | 14 | 13,558 | 50,774 | 542,357 | 606,703 | $0.5565 |
| skill-flow-devcon-billing-dispute-analyst | 27 | 17,473 | 79,446 | 1,911,188 | 2,008,134 | $1.1335 |
| skill-flow-move-node | 16 | 29,997 | 53,284 | 815,107 | 898,404 | $0.8944 |
| skill-flow-ipe-drive-to-slack | 28 | 15,608 | 97,470 | 2,257,497 | 2,370,603 | $1.2770 |
| skill-flow-registry-discovery | 8 | 3,067 | 20,276 | 186,123 | 209,474 | $0.1779 |
| skill-flow-transform-map | 16 | 10,510 | 52,315 | 762,998 | 825,839 | $0.5828 |
| skill-flow-devcon-billing-discrepancy-detector | 22 | 63,893 | 195,924 | 1,387,769 | 1,647,608 | $2.1095 |
| skill-flow-hitl-smoke-multi-outcome-routing | 15 | 15,109 | 65,979 | 760,414 | 841,517 | $0.7022 |
| skill-flow-ipe-required-groups | 24 | 11,124 | 65,843 | 1,337,498 | 1,414,489 | $0.8151 |
| skill-flow-cli-dice-roller-simulated | 22 | 9,667 | 46,411 | 644,964 | 701,064 | $0.5126 |
| skill-flow-remove-node | 16 | 8,759 | 35,070 | 721,300 | 765,145 | $0.4793 |
| skill-flow-trigger-with-filter | 8 | 4,270 | 29,906 | 225,302 | 259,486 | $0.2438 |
| skill-flow-coded-agent | 43 | 27,064 | 89,208 | 3,488,927 | 3,605,242 | $1.7873 |
| skill-flow-customer-escalation-simulated | 1,553 | 104,344 | 244,406 | 7,657,184 | 8,007,487 | $4.7835 |
| skill-flow-ipe-query-params | 12 | 6,176 | 53,537 | 456,343 | 516,068 | $0.4303 |
| skill-flow-ipe-jira-search-triage | 16 | 19,486 | 93,214 | 883,383 | 996,099 | $0.9069 |
| skill-flow-scheduled-trigger | 18 | 9,066 | 48,222 | 847,414 | 904,720 | $0.5711 |
| skill-flow-bindings-idempotent-reconfigure | 35 | 24,773 | 79,349 | 2,607,547 | 2,711,704 | $1.4515 |
| skill-flow-summarize | 11 | 12,176 | 47,277 | 421,865 | 481,329 | $0.4865 |
| skill-flow-hitl-quality-brownfield-insert | 19 | 25,845 | 64,533 | 1,024,002 | 1,114,399 | $0.9369 |
| skill-flow-hitl-quality-result-downstream | 17 | 11,409 | 28,686 | 610,361 | 650,473 | $0.4619 |
| skill-flow-reading-list | 22 | 8,961 | 59,534 | 1,198,660 | 1,267,177 | $0.7173 |
| skill-flow-bindings-multi-connector-independence | 18 | 10,492 | 73,288 | 1,118,432 | 1,202,230 | $0.7678 |
| skill-flow-loop-multiply | 13 | 13,155 | 53,628 | 567,682 | 634,478 | $0.5688 |
| skill-flow-ipe-searchable-joins | 18 | 18,493 | 73,848 | 1,081,697 | 1,174,056 | $0.8789 |
| skill-flow-add-node | 9 | 6,465 | 32,949 | 339,253 | 378,676 | $0.3223 |
| skill-flow-ipe-ceql-where | 22 | 15,512 | 94,406 | 1,788,745 | 1,898,685 | $1.1234 |
| skill-flow-subflow | 11 | 11,851 | 48,311 | 421,773 | 481,946 | $0.4855 |
| skill-flow-ixp-routing-listing/r01 | 13 | 2,222 | 38,819 | 348,158 | 389,212 | $0.2834 |
| skill-flow-ixp-routing-listing/r02 | 9 | 2,716 | 24,900 | 194,796 | 222,421 | $0.1926 |
| skill-flow-ixp-routing-listing/r03 | 12 | 2,138 | 35,992 | 281,688 | 319,830 | $0.2516 |
| skill-flow-ixp-routing-listing/r04 | 7 | 3,024 | 22,811 | 121,735 | 147,577 | $0.1674 |
| skill-flow-ixp-routing-listing/r05 | 11 | 2,022 | 23,657 | 252,367 | 278,057 | $0.1948 |
| skill-flow-ixp-routing-listing/r06 | 9 | 2,313 | 22,677 | 121,840 | 146,839 | $0.1563 |
| skill-flow-ixp-routing-listing/r07 | 8 | 2,568 | 25,707 | 149,591 | 177,874 | $0.1798 |
| skill-flow-ixp-routing-listing/r08 | 11 | 2,543 | 35,936 | 225,366 | 263,856 | $0.2405 |
| skill-flow-ixp-routing-listing/r09 | 9 | 2,058 | 22,656 | 121,813 | 146,536 | $0.1524 |
| skill-flow-ixp-routing-listing/r10 | 9 | 2,125 | 22,724 | 121,909 | 146,767 | $0.1537 |
| skill-flow-rpa | 21 | 8,939 | 53,006 | 1,051,071 | 1,113,037 | $0.6482 |
| skill-flow-lowcode-agent | 15 | 17,939 | 49,785 | 598,424 | 666,163 | $0.6354 |
| skill-flow-wiki-pageviews | 16 | 32,381 | 72,627 | 877,470 | 982,494 | $1.0214 |
| skill-flow-e2e-devcon-expense-approval | 12 | 17,434 | 67,938 | 575,840 | 661,224 | $0.6891 |
| skill-flow-hitl-quality-boolean-decision | 20 | 21,598 | 74,588 | 1,161,599 | 1,257,805 | $0.9522 |
| skill-flow-bellevue-weather-simulated | 60 | 45,882 | 114,933 | 3,852,567 | 4,013,442 | $2.2752 |
| skill-flow-ixp-routing-negative/stripe-http | 21 | 7,066 | 59,773 | 1,180,372 | 1,247,232 | $0.6843 |
| skill-flow-ixp-routing-negative/slack-summary | 17 | 13,751 | 79,771 | 942,114 | 1,035,653 | $0.7881 |
| skill-flow-ixp-routing-negative/sf-update | 12 | 15,950 | 75,314 | 592,845 | 684,121 | $0.6996 |
| skill-flow-ixp-routing-negative/http-webhook | 22 | 8,601 | 66,811 | 1,288,455 | 1,363,889 | $0.7662 |
| skill-flow-ixp-routing-negative/gsheet-loop | 19 | 16,475 | 62,103 | 995,597 | 1,074,194 | $0.7787 |
| skill-flow-ixp-routing-negative/queue-write | 16 | 6,463 | 39,495 | 615,205 | 661,179 | $0.4297 |
| skill-flow-ixp-routing-negative/teams-decision | 12 | 11,535 | 47,587 | 470,918 | 530,052 | $0.4928 |
| skill-flow-ixp-routing-negative/delay-email | 14 | 14,716 | 61,957 | 571,085 | 647,772 | $0.6244 |
| skill-flow-paginated-reference-lookup | 18 | 8,637 | 86,672 | 1,159,401 | 1,254,728 | $0.8024 |
| skill-flow-calculator | 12 | 7,482 | 61,478 | 484,137 | 553,109 | $0.4880 |
| skill-flow-eval-no-auto-upload | 9 | 4,629 | 17,686 | 237,162 | 259,486 | $0.2069 |
| skill-flow-bindings-reconfigure-different-connection | 24 | 17,257 | 82,608 | 1,523,840 | 1,623,729 | $1.0259 |
| skill-flow-ipe-jira-get-issue | 23 | 18,765 | 86,166 | 1,671,214 | 1,776,168 | $1.1060 |
| skill-flow-ipe-dtl-load-by-default-true | 17 | 10,359 | 71,595 | 903,560 | 985,531 | $0.6950 |
| skill-flow-ipe-path-params | 19 | 13,350 | 79,354 | 1,226,864 | 1,319,587 | $0.8659 |
| skill-flow-ipe-jira-create-issue | 23 | 17,656 | 85,868 | 1,703,252 | 1,806,799 | $1.0979 |
| skill-flow-ixp-invoice-extraction-simulated | 49 | 54,652 | 187,975 | 3,557,356 | 3,800,032 | $2.5920 |
| skill-flow-ixp-integration-handle-routing | 33 | 43,131 | 83,103 | 2,411,783 | 2,538,050 | $1.6822 |
| skill-flow-delay | 11 | 8,173 | 44,510 | 404,973 | 457,667 | $0.4110 |
| skill-flow-openmeteo-weather | 20 | 19,551 | 72,038 | 1,278,177 | 1,369,786 | $0.9469 |
| skill-flow-bindings-no-duplicates | 23 | 17,285 | 72,789 | 1,450,813 | 1,540,910 | $0.9675 |
| skill-flow-outlook-waitfor-email | 16 | 10,941 | 73,278 | 833,766 | 918,001 | $0.6891 |
| skill-flow-devcon-billing-invoice-lookup | 32 | 28,511 | 101,129 | 2,850,669 | 2,980,341 | $1.6622 |
| skill-flow-file-attachment-debug | 2,328 | 6,840 | 67,484 | 1,081,088 | 1,157,740 | $0.6870 |
| skill-flow-terminate | 28 | 10,167 | 61,075 | 1,737,787 | 1,809,057 | $0.9030 |
| skill-flow-ipe-dtl-load-by-default-false | 44 | 17,790 | 122,746 | 4,350,781 | 4,491,361 | $2.0325 |
| skill-flow-merge-parallel-sync | 14 | 9,496 | 56,080 | 665,003 | 730,593 | $0.5523 |
| skill-flow-ipe-jira-lifecycle | 21 | 36,654 | 100,673 | 1,464,326 | 1,601,674 | $1.3667 |
| skill-flow-ixp-scaffold-multinode | 21 | 19,693 | 73,977 | 1,337,128 | 1,430,819 | $0.9740 |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 40 | 20,706 | 105,521 | 3,665,050 | 3,791,317 | $1.8059 |
| skill-flow-devcon-billing-resolution-writer | 11 | 17,027 | 63,838 | 479,512 | 560,388 | $0.6387 |
| skill-flow-batch-transform | 12 | 7,229 | 46,204 | 480,906 | 534,351 | $0.4260 |
| skill-flow-ixp-routing/explicit | 26 | 9,092 | 66,144 | 1,476,857 | 1,552,119 | $0.8276 |
| skill-flow-ixp-routing/invoice-extraction | 22 | 11,565 | 74,275 | 1,468,474 | 1,554,336 | $0.8926 |
| skill-flow-ixp-routing/receipts | 64 | 29,180 | 95,171 | 4,668,373 | 4,792,788 | $2.1953 |
| skill-flow-ixp-routing/contracts | 22 | 18,944 | 67,003 | 1,372,065 | 1,458,034 | $0.9471 |
| skill-flow-ixp-routing/forms-classify | 16 | 10,430 | 62,467 | 804,330 | 877,243 | $0.6320 |
| skill-flow-transform-filter | 11 | 8,563 | 48,422 | 424,957 | 481,953 | $0.4375 |
| skill-flow-non-catalog-http-fallback | 16 | 8,946 | 59,776 | 738,066 | 806,804 | $0.5798 |
| skill-flow-customer-escalation | 24 | 40,866 | 127,178 | 2,336,232 | 2,504,300 | $1.7908 |
| skill-flow-expense-approval-simulated | 30 | 28,605 | 74,107 | 1,455,770 | 1,558,512 | $1.1438 |
| skill-flow-ipe-enhanced-enum | 24 | 11,774 | 71,774 | 1,525,583 | 1,609,155 | $0.9035 |
| skill-flow-hitl-quality-schema-design | 24 | 10,867 | 47,982 | 1,031,233 | 1,090,106 | $0.6524 |
| skill-flow-add-output | 10 | 1,697 | 35,433 | 288,325 | 325,465 | $0.2449 |
| skill-flow-ixp-e2e-project-selection/aviation | 28 | 18,728 | 60,625 | 1,759,537 | 1,838,918 | $1.0362 |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 29 | 15,511 | 64,514 | 1,909,819 | 1,989,873 | $1.0476 |
| skill-flow-eval-simulation-crud | 22 | 8,504 | 27,816 | 894,287 | 930,629 | $0.5002 |
| skill-flow-slack-channel-description-simulated | 38 | 12,329 | 92,989 | 2,075,971 | 2,181,327 | $1.1565 |
| skill-flow-solution-select-ask | 17 | 4,252 | 29,376 | 454,834 | 488,479 | $0.3104 |
| skill-flow-eval-local-crud | 15 | 3,148 | 31,038 | 588,344 | 622,545 | $0.3402 |
| skill-flow-api-workflow | 13 | 10,881 | 47,133 | 467,426 | 525,453 | $0.4802 |
| skill-flow-hitl-schema-design-simulated | 44 | 29,223 | 54,535 | 1,852,519 | 1,936,321 | $1.1987 |
| skill-flow-generic-dynamic-node | 32 | 16,338 | 91,097 | 2,554,247 | 2,661,714 | $1.3531 |
| skill-flow-ipe-generate-schema | 23 | 8,842 | 76,089 | 1,547,798 | 1,632,752 | $0.8824 |
| skill-flow-ipe-enum | 26 | 20,759 | 86,605 | 1,904,936 | 2,012,326 | $1.2077 |
| skill-flow-update-node | 7 | 1,773 | 29,728 | 230,178 | 261,686 | $0.2071 |
| skill-flow-switch | 15 | 7,964 | 55,782 | 635,083 | 698,844 | $0.5192 |
| skill-flow-webhook-waitfor-parallel | 24 | 11,053 | 81,700 | 1,676,769 | 1,769,546 | $0.9753 |
| skill-flow-eval-evaluator-type-choice | 11 | 2,825 | 20,518 | 327,156 | 350,510 | $0.2175 |
| skill-flow-transform-group-by | 22 | 8,145 | 54,428 | 1,167,740 | 1,230,335 | $0.6767 |
| skill-flow-multi-city-weather | 13 | 26,381 | 71,323 | 627,060 | 724,777 | $0.8513 |
| skill-flow-ixp-scaffold-minimal | 14 | 34,595 | 63,156 | 686,982 | 784,747 | $0.9619 |
| skill-flow-ipe-complex-array | 1,984 | 13,119 | 71,753 | 1,438,286 | 1,525,142 | $0.9033 |
| skill-flow-dice-roller | 11 | 10,765 | 44,174 | 403,750 | 458,700 | $0.4483 |
| skill-flow-slack-channel-description | 20 | 11,389 | 74,205 | 1,177,734 | 1,263,348 | $0.8025 |
| skill-flow-hitl-smoke-node-placed | 13 | 8,064 | 53,421 | 498,652 | 560,150 | $0.4709 |
| skill-flow-bellevue-weather | 17 | 31,052 | 70,598 | 803,949 | 905,616 | $0.9718 |
| skill-flow-interactive-customer-escalation-triage | 17 | 10,620 | 51,368 | 622,102 | 684,107 | $0.5386 |
| skill-flow-ipe-multiselect | 21 | 21,074 | 83,985 | 1,393,004 | 1,498,084 | $1.0490 |
| skill-flow-eval-inline-agent | 31 | 41,423 | 80,715 | 2,401,928 | 2,524,097 | $1.6447 |
| skill-flow-outlook-trigger-inbox | 30 | 17,886 | 97,091 | 2,239,301 | 2,354,308 | $1.3043 |
| skill-flow-inline-agent-robust | 15 | 14,950 | 61,681 | 794,299 | 870,945 | $0.6939 |
| skill-flow-decision | 12 | 8,928 | 51,635 | 465,009 | 525,584 | $0.4671 |
| skill-flow-feet-inches | 14 | 12,278 | 53,747 | 567,275 | 633,314 | $0.5559 |
| skill-flow-slack-http-fallback | 19 | 9,415 | 85,200 | 1,267,290 | 1,361,924 | $0.8410 |
| skill-flow-slack-weather-pipeline | 26 | 45,096 | 122,244 | 2,384,872 | 2,552,238 | $1.8504 |
| skill-flow-init-validate | 16 | 4,420 | 29,725 | 608,749 | 642,910 | $0.3604 |
| skill-flow-devcon-billing-dispute-resolution | 1,664 | 58,764 | 191,585 | 5,921,927 | 6,173,940 | $3.3815 |
| skill-flow-hitl-smoke-completed-port | 12 | 8,569 | 45,681 | 426,984 | 481,246 | $0.4280 |
| skill-flow-devcon-billing-dispute-analyst | 26 | 21,916 | 85,275 | 1,871,487 | 1,978,704 | $1.2100 |
| skill-flow-move-node | 478 | 7,745 | 33,865 | 345,347 | 387,435 | $0.3482 |
| skill-flow-ipe-drive-to-slack | 35 | 15,575 | 95,880 | 2,959,053 | 3,070,543 | $1.4810 |
| skill-flow-registry-discovery | 1,416 | 2,234 | 20,132 | 185,392 | 209,174 | $0.1689 |
| skill-flow-transform-map | 21 | 10,694 | 52,810 | 1,126,637 | 1,190,162 | $0.6965 |
| skill-flow-devcon-billing-discrepancy-detector | 24 | 33,602 | 189,379 | 1,743,546 | 1,966,551 | $1.7373 |
| skill-flow-hitl-smoke-multi-outcome-routing | 12 | 14,138 | 58,913 | 510,091 | 583,154 | $0.5861 |
| skill-flow-ipe-required-groups | 20 | 13,751 | 60,158 | 1,044,924 | 1,118,853 | $0.7454 |
| skill-flow-cli-dice-roller-simulated | 75 | 23,810 | 131,478 | 5,365,353 | 5,520,716 | $2.4600 |
| skill-flow-remove-node | 17 | 6,297 | 37,514 | 789,877 | 833,705 | $0.4721 |
| skill-flow-trigger-with-filter | 9 | 5,667 | 31,699 | 281,239 | 318,614 | $0.2883 |
| skill-flow-coded-agent | 41 | 11,837 | 109,859 | 2,850,309 | 2,972,046 | $1.4447 |
| skill-flow-customer-escalation-simulated | 13,335 | 37,176 | 126,675 | 4,609,519 | 4,786,705 | $2.4555 |
| skill-flow-ipe-query-params | 14 | 9,063 | 53,568 | 545,753 | 608,398 | $0.5006 |
| skill-flow-ipe-jira-search-triage | 14 | 20,267 | 82,658 | 649,800 | 752,739 | $0.8090 |
| skill-flow-scheduled-trigger | 14 | 12,102 | 48,806 | 599,247 | 660,169 | $0.5444 |
| skill-flow-bindings-idempotent-reconfigure | 36 | 37,729 | 64,676 | 2,309,856 | 2,412,297 | $1.5015 |
| skill-flow-summarize | 14 | 9,524 | 48,786 | 615,556 | 673,880 | $0.5105 |
| skill-flow-hitl-quality-brownfield-insert | 22 | 24,578 | 66,116 | 1,302,558 | 1,393,274 | $1.0074 |
| skill-flow-hitl-quality-result-downstream | 15 | 12,399 | 60,237 | 694,409 | 767,060 | $0.6202 |
| skill-flow-reading-list | 15 | 13,361 | 66,536 | 816,217 | 896,129 | $0.6948 |
| skill-flow-bindings-multi-connector-independence | 20 | 22,047 | 79,735 | 1,330,753 | 1,432,555 | $1.0290 |
| skill-flow-loop-multiply | 24 | 18,019 | 56,395 | 1,288,421 | 1,362,859 | $0.8684 |
| skill-flow-ipe-searchable-joins | 28 | 33,181 | 82,904 | 1,946,332 | 2,062,445 | $1.3926 |
| skill-flow-add-node | 480 | 5,729 | 35,982 | 453,219 | 495,410 | $0.3583 |
| skill-flow-ipe-ceql-where | 24 | 25,906 | 80,932 | 1,655,961 | 1,762,823 | $1.1889 |
| skill-flow-subflow | 20 | 10,056 | 49,671 | 984,538 | 1,044,285 | $0.6325 |
| skill-flow-ixp-routing-listing/r01 | 9 | 2,290 | 23,819 | 178,317 | 204,435 | $0.1772 |
| skill-flow-ixp-routing-listing/r02 | 8 | 2,304 | 22,739 | 161,278 | 186,329 | $0.1682 |
| skill-flow-ixp-routing-listing/r03 | 11 | 1,859 | 35,868 | 225,134 | 262,872 | $0.2300 |
| skill-flow-ixp-routing-listing/r04 | 7 | 2,210 | 22,638 | 121,732 | 146,587 | $0.1546 |
| skill-flow-ixp-routing-listing/r05 | 11 | 2,040 | 35,908 | 225,275 | 263,234 | $0.2329 |
| skill-flow-ixp-routing-listing/r06 | 7 | 2,332 | 22,572 | 121,686 | 146,597 | $0.1562 |
| skill-flow-ixp-routing-listing/r07 | 13 | 3,708 | 28,080 | 302,029 | 333,830 | $0.2516 |
| skill-flow-ixp-routing-listing/r08 | 9 | 1,931 | 22,919 | 121,895 | 146,754 | $0.1515 |
| skill-flow-ixp-routing-listing/r09 | 7 | 2,182 | 22,569 | 121,683 | 146,441 | $0.1539 |
| skill-flow-ixp-routing-listing/r10 | 7 | 2,201 | 22,642 | 121,714 | 146,564 | $0.1545 |
| skill-flow-rpa | 22 | 13,037 | 51,345 | 1,088,236 | 1,152,640 | $0.7146 |
| skill-flow-lowcode-agent | 18 | 14,027 | 52,980 | 898,083 | 965,108 | $0.6786 |
| skill-flow-group-to-subflow | 12 | 50,074 | 73,093 | 582,990 | 706,169 | $1.2001 |
| skill-flow-wiki-pageviews | 17 | 29,414 | 80,994 | 1,073,891 | 1,184,316 | $1.0672 |
| skill-flow-e2e-devcon-expense-approval | 20 | 24,338 | 77,011 | 1,297,519 | 1,398,888 | $1.0432 |
| skill-flow-hitl-quality-boolean-decision | 18 | 8,447 | 59,362 | 917,745 | 985,572 | $0.6247 |
| skill-flow-bellevue-weather-simulated | 22 | 21,843 | 66,654 | 857,192 | 945,711 | $0.8348 |
| skill-flow-ixp-routing-negative/stripe-http | 13 | 7,928 | 57,545 | 596,841 | 662,327 | $0.5138 |
| skill-flow-ixp-routing-negative/slack-summary | 14 | 10,891 | 47,850 | 573,670 | 632,425 | $0.5149 |
| skill-flow-ixp-routing-negative/sf-update | 24 | 7,757 | 56,630 | 1,258,462 | 1,322,873 | $0.7063 |
| skill-flow-ixp-routing-negative/http-webhook | 13 | 5,558 | 44,312 | 531,131 | 581,014 | $0.4089 |
| skill-flow-ixp-routing-negative/gsheet-loop | 13 | 11,772 | 66,471 | 633,437 | 711,693 | $0.6159 |
| skill-flow-ixp-routing-negative/queue-write | 20 | 7,598 | 42,894 | 900,634 | 951,146 | $0.5451 |
| skill-flow-ixp-routing-negative/teams-decision | 18 | 6,589 | 45,281 | 842,259 | 894,147 | $0.5214 |
| skill-flow-ixp-routing-negative/delay-email | 20 | 10,563 | 45,553 | 945,360 | 1,001,496 | $0.6129 |
| skill-flow-paginated-reference-lookup | 22 | 8,609 | 92,727 | 1,450,754 | 1,552,112 | $0.9122 |
| skill-flow-calculator | 20 | 16,011 | 52,377 | 941,314 | 1,009,722 | $0.7190 |
| skill-flow-eval-no-auto-upload | 20 | 3,936 | 21,205 | 703,354 | 728,515 | $0.3496 |
| skill-flow-bindings-reconfigure-different-connection | 27 | 52,136 | 85,487 | 2,125,302 | 2,262,952 | $1.7403 |
| skill-flow-ipe-jira-get-issue | 22 | 10,996 | 72,394 | 1,470,593 | 1,554,005 | $0.8777 |
| skill-flow-ipe-dtl-load-by-default-true | 19 | 8,392 | 66,660 | 1,042,157 | 1,117,228 | $0.6886 |
| skill-flow-ipe-path-params | 39 | 17,970 | 86,554 | 3,076,894 | 3,181,457 | $1.5173 |
| skill-flow-ipe-jira-create-issue | 36 | 26,333 | 89,169 | 2,995,698 | 3,111,236 | $1.6282 |
| skill-flow-ixp-invoice-extraction-simulated | 2,414 | 43,675 | 155,729 | 4,081,671 | 4,283,489 | $2.4709 |
| skill-flow-ixp-integration-handle-routing | 29 | 41,410 | 75,750 | 2,070,417 | 2,187,606 | $1.5264 |
| skill-flow-delay | 10 | 9,473 | 44,376 | 353,226 | 407,085 | $0.4145 |
| skill-flow-openmeteo-weather | 25 | 16,696 | 79,869 | 1,779,961 | 1,876,551 | $1.0840 |
| skill-flow-bindings-no-duplicates | 42 | 29,391 | 75,179 | 2,968,745 | 3,073,357 | $1.6135 |
| skill-flow-outlook-waitfor-email | 26 | 10,457 | 70,934 | 1,580,273 | 1,661,690 | $0.8970 |
| skill-flow-devcon-billing-invoice-lookup | 32 | 47,169 | 196,926 | 2,792,162 | 3,036,289 | $2.2838 |
| skill-flow-file-attachment-debug | 16 | 11,925 | 65,185 | 891,007 | 968,133 | $0.6907 |
| skill-flow-terminate | 13 | 13,405 | 59,665 | 537,205 | 610,288 | $0.5860 |
| skill-flow-ipe-dtl-load-by-default-false | 25 | 14,807 | 102,118 | 1,970,952 | 2,087,902 | $1.1964 |
| skill-flow-merge-parallel-sync | 14 | 8,621 | 57,628 | 688,343 | 754,606 | $0.5520 |
| skill-flow-ipe-jira-lifecycle | 33 | 36,651 | 98,494 | 2,717,158 | 2,852,336 | $1.7344 |
| skill-flow-ixp-scaffold-multinode | 16 | 34,635 | 69,392 | 922,551 | 1,026,594 | $1.0566 |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 37 | 39,531 | 144,498 | 3,925,019 | 4,109,085 | $2.3124 |
| skill-flow-devcon-billing-resolution-writer | 15 | 16,277 | 68,639 | 788,360 | 873,291 | $0.7381 |
| skill-flow-batch-transform | 11 | 7,106 | 46,912 | 419,285 | 473,314 | $0.4083 |
| skill-flow-ixp-routing/explicit | 19 | 11,253 | 57,078 | 921,425 | 989,775 | $0.6593 |
| skill-flow-ixp-routing/invoice-extraction | 26 | 15,175 | 98,338 | 2,026,989 | 2,140,528 | $1.2046 |
| skill-flow-ixp-routing/receipts | 24 | 11,220 | 64,171 | 1,389,823 | 1,465,238 | $0.8260 |
| skill-flow-ixp-routing/contracts | 24 | 14,817 | 79,721 | 1,642,502 | 1,737,064 | $1.0140 |
| skill-flow-ixp-routing/forms-classify | 22 | 13,599 | 66,832 | 1,231,048 | 1,311,501 | $0.8240 |
| skill-flow-transform-filter | 14 | 8,327 | 49,409 | 608,231 | 665,981 | $0.4927 |
| skill-flow-non-catalog-http-fallback | 24 | 13,160 | 77,674 | 1,324,550 | 1,415,408 | $0.8861 |
| skill-flow-customer-escalation | 35 | 19,929 | 126,574 | 3,693,317 | 3,839,855 | $1.8817 |
| skill-flow-expense-approval-simulated | 37 | 45,270 | 108,446 | 2,527,438 | 2,681,191 | $1.8441 |
| skill-flow-ipe-enhanced-enum | 27 | 21,368 | 73,386 | 1,844,036 | 1,938,817 | $1.1490 |
| skill-flow-hitl-quality-schema-design | 19 | 18,713 | 67,026 | 954,847 | 1,040,605 | $0.8186 |
| skill-flow-add-output | 8 | 1,659 | 29,686 | 282,113 | 313,466 | $0.2209 |
| skill-flow-ixp-e2e-project-selection/aviation | 22 | 17,387 | 68,577 | 1,294,773 | 1,380,759 | $0.9065 |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 31 | 22,076 | 64,654 | 1,957,819 | 2,044,580 | $1.1610 |
| skill-flow-eval-simulation-crud | 8 | 6,325 | 26,130 | 210,846 | 243,309 | $0.2561 |
| skill-flow-slack-channel-description-simulated | 31 | 11,003 | 99,655 | 1,870,979 | 1,981,668 | $1.1001 |
| skill-flow-solution-select-ask | 15 | 2,810 | 29,393 | 353,002 | 385,220 | $0.2583 |
| skill-flow-eval-local-crud | 6,839 | 7,723 | 37,090 | 270,162 | 321,814 | $0.3565 |
| skill-flow-api-workflow | 16 | 11,823 | 67,631 | 811,677 | 891,147 | $0.6745 |
| skill-flow-hitl-schema-design-simulated | 49 | 22,453 | 46,175 | 1,955,220 | 2,023,897 | $1.0967 |
| skill-flow-generic-dynamic-node | 34 | 20,324 | 97,538 | 2,746,998 | 2,864,894 | $1.4948 |
| skill-flow-ipe-generate-schema | 26 | 12,246 | 90,772 | 1,914,529 | 2,017,573 | $1.0985 |
| skill-flow-ipe-enum | 17 | 33,383 | 146,696 | 944,134 | 1,124,230 | $1.3341 |
| skill-flow-update-node | 7 | 2,238 | 30,192 | 230,198 | 262,635 | $0.2159 |
| skill-flow-switch | 18 | 13,136 | 56,617 | 907,014 | 976,785 | $0.6815 |
| skill-flow-webhook-waitfor-parallel | 17 | 9,249 | 78,281 | 953,486 | 1,041,033 | $0.7184 |
| skill-flow-eval-evaluator-type-choice | 11 | 2,924 | 23,440 | 337,486 | 363,861 | $0.2330 |
| skill-flow-transform-group-by | 11 | 9,904 | 48,054 | 420,442 | 478,411 | $0.4549 |
| skill-flow-multi-city-weather | 14 | 22,992 | 73,294 | 707,570 | 803,870 | $0.8320 |
| skill-flow-ixp-scaffold-minimal | 17 | 10,486 | 60,956 | 938,850 | 1,010,309 | $0.6676 |
| skill-flow-ipe-complex-array | 25 | 17,883 | 77,702 | 1,691,671 | 1,787,281 | $1.0672 |
| skill-flow-dice-roller | 11 | 5,943 | 49,569 | 440,364 | 495,887 | $0.4072 |
| skill-flow-slack-channel-description | 31 | 12,509 | 85,836 | 2,317,059 | 2,415,435 | $1.2047 |
| skill-flow-hitl-smoke-node-placed | 15 | 12,949 | 48,182 | 608,095 | 669,241 | $0.5574 |
| skill-flow-bellevue-weather | 17 | 21,417 | 63,372 | 903,118 | 987,924 | $0.8299 |
| skill-flow-interactive-customer-escalation-triage | 20 | 12,484 | 59,780 | 883,071 | 955,355 | $0.6764 |
| skill-flow-ipe-multiselect | 22 | 19,699 | 82,437 | 1,574,607 | 1,676,765 | $1.0771 |
| skill-flow-eval-inline-agent | 3,566 | 41,781 | 82,775 | 2,533,498 | 2,661,620 | $1.7079 |
| skill-flow-outlook-trigger-inbox | 21 | 8,324 | 77,499 | 1,317,591 | 1,403,435 | $0.8108 |
| skill-flow-inline-agent-robust | 17 | 23,641 | 64,448 | 923,131 | 1,011,237 | $0.8733 |
| skill-flow-decision | 14 | 9,072 | 44,286 | 532,126 | 585,498 | $0.4618 |
| skill-flow-feet-inches | 12 | 19,230 | 57,370 | 453,613 | 530,225 | $0.6397 |
| skill-flow-slack-http-fallback | 20 | 12,518 | 92,810 | 1,384,288 | 1,489,636 | $0.9512 |
| skill-flow-slack-weather-pipeline | 36 | 32,573 | 104,653 | 2,940,105 | 3,077,367 | $1.7632 |
| skill-flow-init-validate | 13 | 4,733 | 29,055 | 420,205 | 454,006 | $0.3061 |
| skill-flow-devcon-billing-dispute-resolution | 3,974 | 64,919 | 209,825 | 7,883,608 | 8,162,326 | $4.1376 |
| skill-flow-hitl-smoke-completed-port | 15 | 12,723 | 54,129 | 616,614 | 683,481 | $0.5789 |
| skill-flow-devcon-billing-dispute-analyst | 26 | 13,246 | 81,690 | 1,862,932 | 1,957,894 | $1.0640 |
| skill-flow-move-node | 14 | 26,635 | 41,014 | 612,560 | 680,223 | $0.7371 |
| skill-flow-ipe-drive-to-slack | 27 | 15,513 | 96,414 | 2,084,750 | 2,196,704 | $1.2198 |
| skill-flow-registry-discovery | 1,417 | 3,359 | 21,696 | 223,822 | 250,294 | $0.2031 |
| skill-flow-transform-map | 14 | 10,174 | 47,778 | 629,792 | 687,758 | $0.5208 |
| skill-flow-devcon-billing-discrepancy-detector | 23 | 29,789 | 102,275 | 1,738,509 | 1,870,596 | $1.3520 |
| skill-flow-hitl-smoke-multi-outcome-routing | 25 | 9,563 | 36,577 | 1,046,844 | 1,093,009 | $0.5947 |
| skill-flow-ipe-required-groups | 15 | 11,398 | 68,813 | 725,607 | 805,833 | $0.6467 |
| skill-flow-cli-dice-roller-simulated | 29 | 14,574 | 58,995 | 1,110,193 | 1,183,791 | $0.7730 |
| skill-flow-remove-node | 485 | 19,447 | 45,760 | 746,091 | 811,783 | $0.6886 |
| skill-flow-trigger-with-filter | 24 | 11,052 | 62,070 | 1,297,490 | 1,370,636 | $0.7879 |
| skill-flow-coded-agent | 42 | 12,049 | 48,077 | 2,298,524 | 2,358,692 | $1.0507 |
| skill-flow-customer-escalation-simulated | 4,956 | 125,897 | 364,006 | 13,719,665 | 14,214,524 | $7.3842 |
| skill-flow-ipe-query-params | 16 | 4,242 | 53,123 | 768,834 | 826,215 | $0.4935 |
| skill-flow-ipe-jira-search-triage | 19 | 18,017 | 79,602 | 1,199,144 | 1,296,782 | $0.9286 |
| skill-flow-scheduled-trigger | 15 | 7,914 | 46,981 | 645,348 | 700,258 | $0.4885 |
| skill-flow-bindings-idempotent-reconfigure | 25 | 15,349 | 59,800 | 1,402,939 | 1,478,113 | $0.8754 |
| skill-flow-summarize | 10 | 9,815 | 47,246 | 366,206 | 423,277 | $0.4343 |
| skill-flow-hitl-quality-brownfield-insert | 16 | 21,847 | 67,612 | 872,282 | 961,757 | $0.8430 |
| skill-flow-hitl-quality-result-downstream | 2,963 | 20,191 | 46,924 | 974,398 | 1,044,476 | $0.7800 |
| skill-flow-reading-list | 18 | 14,882 | 54,707 | 945,314 | 1,014,921 | $0.7120 |
| skill-flow-bindings-multi-connector-independence | 22 | 15,230 | 80,989 | 1,514,570 | 1,610,811 | $0.9866 |
| skill-flow-loop-multiply | 24 | 12,448 | 59,135 | 1,314,773 | 1,386,380 | $0.8030 |
| skill-flow-ipe-searchable-joins | 28 | 26,273 | 81,214 | 1,965,387 | 2,072,902 | $1.2883 |
| skill-flow-add-node | 480 | 8,699 | 35,375 | 447,843 | 492,397 | $0.3989 |
| skill-flow-ipe-ceql-where | 34 | 24,613 | 87,398 | 2,568,209 | 2,680,254 | $1.4675 |
| skill-flow-subflow | 11 | 16,576 | 47,644 | 416,270 | 480,501 | $0.5522 |
| skill-flow-ixp-routing-listing/r01 | 8 | 1,034 | 6,622 | 190,263 | 197,927 | $0.0974 |
| skill-flow-ixp-routing-listing/r02 | 7 | 2,519 | 27,248 | 121,712 | 151,486 | $0.1765 |
| skill-flow-ixp-routing-listing/r03 | 9 | 1,913 | 35,774 | 224,814 | 262,510 | $0.2303 |
| skill-flow-ixp-routing-listing/r04 | 11 | 2,155 | 35,908 | 225,343 | 263,417 | $0.2346 |
| skill-flow-ixp-routing-listing/r05 | 10 | 1,659 | 7,937 | 249,577 | 259,183 | $0.1296 |
| skill-flow-ixp-routing-listing/r06 | 7 | 3,109 | 22,572 | 121,686 | 147,374 | $0.1678 |
| skill-flow-ixp-routing-listing/r07 | 12 | 3,237 | 25,512 | 280,001 | 308,762 | $0.2283 |
| skill-flow-ixp-routing-listing/r08 | 11 | 2,253 | 35,991 | 225,558 | 263,813 | $0.2365 |
| skill-flow-ixp-routing-listing/r09 | 9 | 2,406 | 23,744 | 178,280 | 204,439 | $0.1786 |
| skill-flow-ixp-routing-listing/r10 | 9 | 1,977 | 35,782 | 224,814 | 262,582 | $0.2313 |
| skill-flow-rpa | 21 | 17,567 | 50,504 | 981,751 | 1,049,843 | $0.7475 |
| skill-flow-lowcode-agent | 14 | 14,968 | 47,971 | 543,229 | 606,182 | $0.5674 |
| skill-flow-group-to-subflow | 10 | 36,408 | 121,789 | 188,609 | 346,816 | $1.0594 |
| skill-flow-wiki-pageviews | 13 | 24,361 | 72,843 | 617,785 | 715,002 | $0.8240 |
| skill-flow-e2e-devcon-expense-approval | 17 | 11,506 | 69,672 | 886,968 | 968,163 | $0.7000 |
| skill-flow-hitl-quality-boolean-decision | 12 | 21,708 | 64,238 | 475,587 | 561,545 | $0.7092 |
| skill-flow-bellevue-weather-simulated | 16,007 | 68,482 | 221,623 | 3,740,625 | 4,046,737 | $3.0285 |
| skill-flow-ixp-routing-negative/stripe-http | 15 | 9,095 | 57,073 | 760,037 | 826,220 | $0.5785 |
| skill-flow-ixp-routing-negative/slack-summary | 13 | 18,143 | 50,541 | 555,920 | 624,617 | $0.6285 |
| skill-flow-ixp-routing-negative/sf-update | 16 | 5,839 | 51,585 | 738,482 | 795,922 | $0.5026 |
| skill-flow-ixp-routing-negative/http-webhook | 18 | 9,696 | 53,785 | 863,561 | 927,060 | $0.6063 |
| skill-flow-ixp-routing-negative/gsheet-loop | 16 | 17,380 | 57,836 | 811,349 | 886,581 | $0.7210 |
| skill-flow-ixp-routing-negative/queue-write | 59 | 6,808 | 41,932 | 1,096,861 | 1,145,660 | $0.5886 |
| skill-flow-ixp-routing-negative/teams-decision | 12 | 12,244 | 45,816 | 464,920 | 522,992 | $0.4950 |
| skill-flow-ixp-routing-negative/delay-email | 15 | 6,884 | 46,031 | 683,956 | 736,886 | $0.4811 |
| skill-flow-paginated-reference-lookup | 17 | 9,781 | 80,703 | 983,080 | 1,073,581 | $0.7443 |
| skill-flow-calculator | 12 | 17,756 | 51,603 | 434,923 | 504,294 | $0.5904 |
| skill-flow-eval-no-auto-upload | 16 | 4,171 | 20,830 | 537,080 | 562,097 | $0.3018 |
| skill-flow-bindings-reconfigure-different-connection | 28 | 19,404 | 80,407 | 1,868,729 | 1,968,568 | $1.1533 |
| skill-flow-ipe-jira-get-issue | 21 | 12,325 | 72,088 | 1,327,836 | 1,412,270 | $0.8536 |
| skill-flow-ipe-dtl-load-by-default-true | 24 | 10,041 | 53,942 | 1,206,845 | 1,270,852 | $0.7150 |
| skill-flow-ipe-path-params | 25 | 14,869 | 74,169 | 1,679,407 | 1,768,470 | $1.0051 |
| skill-flow-ipe-jira-create-issue | 31 | 12,705 | 83,183 | 2,355,511 | 2,451,430 | $1.2093 |
| skill-flow-ixp-invoice-extraction-simulated | 5,907 | 89,528 | 269,372 | 9,241,998 | 9,606,805 | $5.1434 |
| skill-flow-ixp-integration-handle-routing | 17 | 24,878 | 86,972 | 1,008,908 | 1,120,775 | $1.0020 |
| skill-flow-delay | 10 | 11,564 | 44,267 | 353,130 | 408,971 | $0.4454 |
| skill-flow-openmeteo-weather | 22 | 6,440 | 69,381 | 1,359,114 | 1,434,957 | $0.7646 |
| skill-flow-bindings-no-duplicates | 28 | 31,221 | 73,890 | 1,881,631 | 1,986,770 | $1.3100 |
| skill-flow-outlook-waitfor-email | 21 | 9,671 | 72,842 | 1,202,387 | 1,284,921 | $0.7790 |
| skill-flow-devcon-billing-invoice-lookup | 22 | 26,337 | 86,524 | 1,564,455 | 1,677,338 | $1.1889 |
| skill-flow-file-attachment-debug | 19 | 12,462 | 63,320 | 995,808 | 1,071,609 | $0.7232 |
| skill-flow-terminate | 11 | 13,325 | 59,475 | 464,365 | 537,176 | $0.5622 |
| skill-flow-ipe-dtl-load-by-default-false | 53 | 15,136 | 94,462 | 4,337,577 | 4,447,228 | $1.8827 |
| skill-flow-merge-parallel-sync | 10 | 10,928 | 56,630 | 410,477 | 478,045 | $0.4995 |
| skill-flow-ipe-jira-lifecycle | 33 | 24,019 | 83,289 | 2,482,842 | 2,590,183 | $1.4176 |
| skill-flow-ixp-scaffold-multinode | 33 | 16,754 | 61,952 | 2,169,512 | 2,248,251 | $1.1346 |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 64 | 38,973 | 118,503 | 6,501,737 | 6,659,277 | $2.9797 |
| skill-flow-devcon-billing-resolution-writer | 18 | 19,246 | 74,038 | 1,145,122 | 1,238,424 | $0.9099 |
| skill-flow-batch-transform | 11 | 8,466 | 47,002 | 417,332 | 472,811 | $0.4285 |
| skill-flow-ixp-routing/explicit | 24 | 11,290 | 68,424 | 1,439,660 | 1,519,398 | $0.8579 |
| skill-flow-ixp-routing/invoice-extraction | 25 | 18,243 | 90,224 | 1,747,515 | 1,856,007 | $1.1363 |
| skill-flow-ixp-routing/receipts | 17 | 11,536 | 66,526 | 857,675 | 935,754 | $0.6799 |
| skill-flow-ixp-routing/contracts | 15 | 14,425 | 68,146 | 857,095 | 939,681 | $0.7291 |
| skill-flow-ixp-routing/forms-classify | 23 | 10,178 | 72,083 | 1,369,976 | 1,452,260 | $0.8340 |
| skill-flow-transform-filter | 14 | 8,592 | 50,723 | 629,166 | 688,495 | $0.5079 |
| skill-flow-non-catalog-http-fallback | 22 | 13,269 | 66,096 | 1,161,182 | 1,240,569 | $0.7953 |
| skill-flow-customer-escalation | 50 | 42,790 | 229,574 | 5,302,677 | 5,575,091 | $3.0937 |
| skill-flow-expense-approval-simulated | 38 | 31,308 | 91,157 | 1,909,243 | 2,031,746 | $1.3843 |
| skill-flow-ipe-enhanced-enum | 15 | 21,137 | 92,593 | 870,955 | 984,700 | $0.9256 |
| skill-flow-hitl-quality-schema-design | 17 | 14,002 | 47,667 | 629,882 | 691,568 | $0.5778 |
| skill-flow-add-output | 7 | 1,866 | 29,209 | 230,127 | 261,209 | $0.2066 |
| skill-flow-ixp-e2e-project-selection/aviation | 24 | 14,949 | 63,894 | 1,523,409 | 1,602,276 | $0.9209 |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 21 | 13,672 | 57,340 | 1,097,318 | 1,168,351 | $0.7494 |
| skill-flow-eval-simulation-crud | 8 | 8,284 | 27,296 | 215,216 | 250,804 | $0.2912 |
| skill-flow-slack-channel-description-simulated | 4,457 | 85,209 | 429,393 | 7,098,894 | 7,617,953 | $5.0314 |
| skill-flow-solution-select-ask | 17 | 4,790 | 29,537 | 455,632 | 489,976 | $0.3194 |
| skill-flow-eval-local-crud | 6,840 | 7,562 | 37,906 | 274,157 | 326,465 | $0.3583 |
| skill-flow-api-workflow | 17 | 13,646 | 48,697 | 721,465 | 783,825 | $0.6038 |
| skill-flow-hitl-schema-design-simulated | 32 | 13,729 | 42,259 | 1,076,832 | 1,132,852 | $0.6876 |
| skill-flow-generic-dynamic-node | 35 | 24,029 | 91,959 | 2,772,697 | 2,888,720 | $1.5372 |
| skill-flow-ipe-generate-schema | 25 | 19,621 | 92,265 | 1,843,676 | 1,955,587 | $1.1935 |
| skill-flow-ipe-enum | 24 | 20,326 | 81,842 | 1,528,982 | 1,631,174 | $1.0706 |
| skill-flow-update-node | 7 | 1,932 | 29,581 | 230,208 | 261,728 | $0.2090 |
| skill-flow-switch | 21 | 13,051 | 45,420 | 978,449 | 1,036,941 | $0.6597 |
| skill-flow-webhook-waitfor-parallel | 26 | 10,827 | 81,281 | 1,776,589 | 1,868,723 | $1.0003 |
| skill-flow-eval-evaluator-type-choice | 18 | 5,957 | 25,579 | 670,987 | 702,541 | $0.3866 |
| skill-flow-transform-group-by | 13 | 8,828 | 47,281 | 546,026 | 602,148 | $0.4736 |
| skill-flow-multi-city-weather | 16 | 38,946 | 84,122 | 941,038 | 1,064,122 | $1.1820 |
| skill-flow-ixp-scaffold-minimal | 1,462 | 26,815 | 70,926 | 1,036,121 | 1,135,324 | $0.9834 |
| skill-flow-ipe-complex-array | 22 | 16,441 | 70,764 | 1,377,289 | 1,464,516 | $0.9252 |
| skill-flow-dice-roller | 14 | 8,684 | 43,915 | 528,464 | 581,077 | $0.4535 |
| skill-flow-slack-channel-description | 32 | 11,539 | 98,250 | 2,787,623 | 2,897,444 | $1.3779 |
| skill-flow-hitl-smoke-node-placed | 14 | 8,223 | 56,424 | 576,620 | 641,281 | $0.5080 |
| skill-flow-bellevue-weather | 14 | 34,912 | 68,108 | 658,401 | 761,435 | $0.9766 |
| skill-flow-interactive-customer-escalation-triage | 29 | 44,724 | 94,919 | 1,570,312 | 1,709,984 | $1.4980 |
| skill-flow-ipe-multiselect | 19 | 25,659 | 80,200 | 1,126,598 | 1,232,476 | $1.0237 |
| skill-flow-eval-inline-agent | 3,548 | 24,468 | 70,651 | 713,737 | 812,404 | $0.8567 |
| skill-flow-outlook-trigger-inbox | 25 | 10,763 | 82,647 | 1,696,977 | 1,790,412 | $0.9805 |
| skill-flow-inline-agent-robust | 14 | 13,009 | 67,360 | 721,033 | 801,416 | $0.6641 |
| skill-flow-decision | 12 | 9,328 | 51,400 | 433,217 | 493,957 | $0.4627 |
| skill-flow-feet-inches | 18 | 28,994 | 58,187 | 913,864 | 1,001,063 | $0.9273 |
| skill-flow-slack-http-fallback | 27 | 11,020 | 97,742 | 2,045,607 | 2,154,396 | $1.1456 |
| skill-flow-slack-weather-pipeline | 28 | 65,079 | 166,902 | 2,493,248 | 2,725,257 | $2.3501 |
| skill-flow-init-validate | 12 | 2,886 | 29,739 | 413,973 | 446,610 | $0.2790 |
| skill-flow-devcon-billing-dispute-resolution | 65 | 48,200 | 132,180 | 7,155,843 | 7,336,288 | $3.3656 |
| skill-flow-hitl-smoke-completed-port | 13 | 16,465 | 55,759 | 515,721 | 587,958 | $0.6108 |
| skill-flow-devcon-billing-dispute-analyst | 20 | 20,414 | 75,819 | 1,288,010 | 1,384,263 | $0.9770 |
| skill-flow-move-node | 6 | 22,437 | 48,427 | 196,498 | 267,368 | $0.5771 |
| skill-flow-ipe-drive-to-slack | 30 | 15,363 | 99,844 | 2,635,178 | 2,750,415 | $1.3955 |
| skill-flow-registry-discovery | 13 | 3,006 | 19,265 | 341,446 | 363,730 | $0.2198 |
| skill-flow-transform-map | 14 | 9,086 | 46,320 | 591,756 | 647,176 | $0.4876 |
| skill-flow-devcon-billing-discrepancy-detector | 60 | 24,633 | 108,208 | 5,763,635 | 5,896,536 | $2.5045 |
| skill-flow-hitl-smoke-multi-outcome-routing | 11 | 14,803 | 58,373 | 455,928 | 529,115 | $0.5778 |
| skill-flow-ipe-required-groups | 17 | 11,383 | 68,034 | 901,996 | 981,430 | $0.6965 |
| skill-flow-cli-dice-roller-simulated | 32 | 9,319 | 64,448 | 2,055,260 | 2,129,059 | $0.9981 |
| skill-flow-remove-node | 19 | 6,696 | 37,091 | 903,400 | 947,206 | $0.5106 |
| skill-flow-trigger-with-filter | 7 | 3,573 | 29,315 | 173,690 | 206,585 | $0.2157 |
| skill-flow-coded-agent | 1,679 | 12,647 | 101,732 | 3,061,460 | 3,177,518 | $1.4947 |
| skill-flow-customer-escalation-simulated | 9,246 | 104,394 | 260,274 | 9,420,833 | 9,794,747 | $5.3959 |
| skill-flow-ipe-query-params | 12 | 6,964 | 53,196 | 486,093 | 546,265 | $0.4498 |
| skill-flow-ipe-jira-search-triage | 18 | 28,252 | 91,185 | 1,168,432 | 1,287,887 | $1.1163 |
| skill-flow-scheduled-trigger | 15 | 5,787 | 18,087 | 444,241 | 468,130 | $0.2879 |
| skill-flow-bindings-idempotent-reconfigure | 20 | 22,823 | 67,906 | 1,200,071 | 1,290,820 | $0.9571 |
| skill-flow-summarize | 11 | 9,032 | 47,189 | 420,559 | 476,791 | $0.4386 |
| skill-flow-hitl-quality-brownfield-insert | 21 | 17,393 | 54,337 | 1,070,887 | 1,142,638 | $0.7860 |
| skill-flow-hitl-quality-result-downstream | 14 | 8,585 | 29,277 | 471,478 | 509,354 | $0.3800 |
| skill-flow-reading-list | 15 | 15,425 | 53,866 | 702,879 | 772,185 | $0.6443 |
| skill-flow-bindings-multi-connector-independence | 31 | 25,312 | 81,505 | 2,414,890 | 2,521,738 | $1.4099 |
| skill-flow-loop-multiply | 14 | 12,291 | 52,036 | 562,757 | 627,098 | $0.5484 |
| skill-flow-ipe-searchable-joins | 20 | 12,216 | 74,038 | 1,279,824 | 1,366,098 | $0.8449 |
| skill-flow-add-node | 9 | 5,631 | 32,674 | 339,221 | 377,535 | $0.3088 |
| skill-flow-ipe-ceql-where | 24 | 11,756 | 74,100 | 1,559,732 | 1,645,612 | $0.9222 |
| skill-flow-subflow | 12 | 13,775 | 48,488 | 475,321 | 537,596 | $0.5311 |
| skill-flow-ixp-routing-listing/r01 | 11 | 2,751 | 24,160 | 179,338 | 206,260 | $0.1857 |
| skill-flow-ixp-routing-listing/r02 | 12 | 2,670 | 25,731 | 339,385 | 367,798 | $0.2384 |
| skill-flow-ixp-routing-listing/r03 | 10 | 2,341 | 35,849 | 281,051 | 319,251 | $0.2539 |
| skill-flow-ixp-routing-listing/r04 | 11 | 1,933 | 35,938 | 225,399 | 263,281 | $0.2314 |
| skill-flow-ixp-routing-listing/r05 | 14 | 3,562 | 16,307 | 392,044 | 411,927 | $0.2322 |
| skill-flow-ixp-routing-listing/r06 | 7 | 2,432 | 22,606 | 121,720 | 146,765 | $0.1578 |
| skill-flow-ixp-routing-listing/r07 | 12 | 2,203 | 36,140 | 335,410 | 373,765 | $0.2692 |
| skill-flow-ixp-routing-listing/r08 | 9 | 2,603 | 22,711 | 121,933 | 147,256 | $0.1608 |
| skill-flow-ixp-routing-listing/r09 | 10 | 1,543 | 9,385 | 253,468 | 264,406 | $0.1344 |
| skill-flow-ixp-routing-listing/r10 | 7 | 3,371 | 22,761 | 121,677 | 147,816 | $0.1724 |
| skill-flow-rpa | 21 | 13,603 | 54,418 | 1,067,816 | 1,135,858 | $0.7285 |
| skill-flow-lowcode-agent | 21 | 12,529 | 57,835 | 1,125,030 | 1,195,415 | $0.7424 |
| skill-flow-group-to-subflow | 14 | 32,273 | 42,351 | 661,280 | 735,918 | $0.8413 |


## Command Telemetry

**Total Commands**: 15066
**Success Rate**: 14439/15066 (95.8%)

### Commands by Tool

| Tool | Count | % |
|------|-------|---|
| Bash | 8695 | 57.7% |
| Read | 3697 | 24.5% |
| Edit | 1408 | 9.3% |
| Skill | 659 | 4.4% |
| Write | 338 | 2.2% |
| TaskUpdate | 90 | 0.6% |
| Glob | 82 | 0.5% |
| TaskCreate | 48 | 0.3% |
| Grep | 42 | 0.3% |
| Agent | 3 | 0.0% |
| TaskStop | 2 | 0.0% |
| WebFetch | 1 | 0.0% |
| TaskOutput | 1 | 0.0% |

### Performance

- **Average Command Time**: 4448.0ms
- **Total Command Time**: 67014.14s

### Slowest Commands

| Tool | Duration | Parameters |
|------|----------|------------|
| TaskOutput | 300030ms | {'task_id': 'bbyxyppt9', 'block': True, 'timeout':... |
| Bash | 122455ms | {'command': 'sleep 120 && uip ixp projects get-met... |
| Bash | 120986ms | {'command': 'uip rpa run --file-path "Main.xaml" -... |
| Bash | 120790ms | {'command': '# Try to wake up / edit the connectio... |
| Bash | 120525ms | {'command': 'uip is connections edit "197c7074-fa5... |

**Most Common Pattern**: `Bash → Bash → Bash`

**Skill Tool Invoked**: 659 time(s)

## Agent Settings

- **Permission Mode**: acceptEdits
- **Allowed Tools**: Skill, Bash, Read, Write, Edit, Glob, Grep
- **Model**: us.anthropic.claude-sonnet-4-6
- **Max Turns**: 40
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