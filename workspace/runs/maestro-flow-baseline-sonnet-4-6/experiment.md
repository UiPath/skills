# Experiment Report: skill-tests-smoke

**Description**: Linux PR-gate smoke tests — docker isolation, fast turn budget
**Variants**: default
**Total Duration**: 1617.6s

## Aggregate Metrics

| Metric | default |
|--------|--------|
| Tasks Run | 127 |
| Succeeded | 120 |
| Failed | 7 |
| Errors | 0 |
| Pass Rate | 94.5% |
| Score | 0.964 ± 0.145 |
| Avg Duration (s) | 326.0 ± 228.9 |
| Assistant Turns | 40.7 ± 20.8 |
| Tokens | 1,355,998 ± 1,021,944 |

## Win Rates

- **default**: 127/127 tasks (100%)

## Per-Task Comparison

| Task | default | Best | Spread |
|------|------|------|--------|
| skill-flow-e2e-escalation-jira-ticket | 1.000 (+) | default | 0.000 |
| skill-flow-registry-discovery | 1.000 (+) | default | 0.000 |
| skill-flow-ixp-routing-listing/r01 | 1.000 (+) | default | 0.000 |
| skill-flow-ixp-routing-listing/r02 | 1.000 (+) | default | 0.000 |
| skill-flow-ixp-routing-listing/r03 | 1.000 (+) | default | 0.000 |
| skill-flow-ixp-routing-listing/r04 | 1.000 (+) | default | 0.000 |
| skill-flow-ixp-routing-listing/r05 | 1.000 (+) | default | 0.000 |
| skill-flow-ixp-routing-listing/r06 | 1.000 (+) | default | 0.000 |
| skill-flow-ixp-routing-listing/r07 | 1.000 (+) | default | 0.000 |
| skill-flow-ixp-routing-listing/r08 | 1.000 (+) | default | 0.000 |
| skill-flow-ixp-routing-listing/r09 | 1.000 (+) | default | 0.000 |
| skill-flow-ixp-routing-listing/r10 | 1.000 (+) | default | 0.000 |
| skill-flow-file-attachment-debug | 1.000 (+) | default | 0.000 |
| skill-flow-slack-channel-description | 1.000 (+) | default | 0.000 |
| skill-flow-group-to-subflow | 1.000 (+) | default | 0.000 |
| skill-flow-decision | 1.000 (+) | default | 0.000 |
| skill-flow-devcon-billing-dispute-resolution | 0.545 (-) | default | 0.000 |
| skill-flow-api-workflow | 0.375 (-) | default | 0.000 |
| skill-flow-add-output | 1.000 (+) | default | 0.000 |
| skill-flow-bindings-multi-connector-independence | 1.000 (+) | default | 0.000 |
| skill-flow-eval-inline-agent | 1.000 (+) | default | 0.000 |
| skill-flow-bindings-no-duplicates | 1.000 (+) | default | 0.000 |
| skill-flow-devcon-billing-discrepancy-detector | 1.000 (+) | default | 0.000 |
| skill-flow-slack-channel-description-simulated | 1.000 (+) | default | 0.000 |
| skill-flow-outlook-waitfor-email | 1.000 (+) | default | 0.000 |
| skill-flow-webhook-waitfor-parallel | 1.000 (+) | default | 0.000 |
| skill-flow-multi-city-weather | 1.000 (+) | default | 0.000 |
| skill-flow-ixp-scaffold-minimal | 1.000 (+) | default | 0.000 |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 1.000 (+) | default | 0.000 |
| skill-flow-eval-simulation-crud | 1.000 (+) | default | 0.000 |
| skill-flow-ipe-ceql-where | 1.000 (+) | default | 0.000 |
| skill-flow-ixp-e2e-project-selection/aviation | 1.000 (+) | default | 0.000 |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 1.000 (+) | default | 0.000 |
| skill-flow-reading-list | 1.000 (+) | default | 0.000 |
| skill-flow-ipe-jira-lifecycle | 1.000 (+) | default | 0.000 |
| skill-flow-rpa | 0.625 (-) | default | 0.000 |
| skill-flow-init-validate | 1.000 (+) | default | 0.000 |
| skill-flow-transform-map | 1.000 (+) | default | 0.000 |
| skill-flow-ipe-generate-schema | 1.000 (+) | default | 0.000 |
| skill-flow-slack-http-fallback | 1.000 (+) | default | 0.000 |
| skill-flow-devcon-billing-resolution-writer | 1.000 (+) | default | 0.000 |
| skill-flow-e2e-escalation-orchestrator-paths | 1.000 (+) | default | 0.000 |
| skill-flow-loop-multiply | 0.375 (-) | default | 0.000 |
| skill-flow-hitl-quality-boolean-decision | 1.000 (+) | default | 0.000 |
| skill-flow-slack-weather-pipeline | 0.000 (M) | default | 0.000 |
| skill-flow-merge-parallel-sync | 1.000 (+) | default | 0.000 |
| skill-flow-ipe-required-groups | 1.000 (+) | default | 0.000 |
| skill-flow-solution-select-ask | 1.000 (+) | default | 0.000 |
| skill-flow-ipe-enum | 1.000 (+) | default | 0.000 |
| skill-flow-ixp-routing-negative/stripe-http | 1.000 (+) | default | 0.000 |
| skill-flow-ixp-routing-negative/slack-summary | 1.000 (+) | default | 0.000 |
| skill-flow-ixp-routing-negative/sf-update | 1.000 (+) | default | 0.000 |
| skill-flow-ixp-routing-negative/http-webhook | 1.000 (+) | default | 0.000 |
| skill-flow-ixp-routing-negative/gsheet-loop | 1.000 (+) | default | 0.000 |
| skill-flow-ixp-routing-negative/queue-write | 1.000 (+) | default | 0.000 |
| skill-flow-ixp-routing-negative/teams-decision | 1.000 (+) | default | 0.000 |
| skill-flow-ixp-routing-negative/delay-email | 1.000 (+) | default | 0.000 |
| skill-flow-e2e-devcon-expense-approval | 1.000 (+) | default | 0.000 |
| skill-flow-bindings-idempotent-reconfigure | 1.000 (+) | default | 0.000 |
| skill-flow-hitl-quality-result-downstream | 1.000 (+) | default | 0.000 |
| skill-flow-ipe-jira-create-issue | 1.000 (+) | default | 0.000 |
| skill-flow-customer-escalation | 1.000 (+) | default | 0.000 |
| skill-flow-ipe-dtl-load-by-default-true | 1.000 (+) | default | 0.000 |
| skill-flow-e2e-escalation-slack-alert | 1.000 (+) | default | 0.000 |
| skill-flow-hitl-smoke-node-placed | 1.000 (+) | default | 0.000 |
| skill-flow-ixp-routing/explicit | 1.000 (+) | default | 0.000 |
| skill-flow-ixp-routing/invoice-extraction | 1.000 (+) | default | 0.000 |
| skill-flow-ixp-routing/receipts | 1.000 (+) | default | 0.000 |
| skill-flow-ixp-routing/contracts | 1.000 (+) | default | 0.000 |
| skill-flow-ixp-routing/forms-classify | 1.000 (+) | default | 0.000 |
| skill-flow-ipe-jira-get-issue | 1.000 (+) | default | 0.000 |
| skill-flow-ixp-integration-handle-routing | 1.000 (+) | default | 0.000 |
| skill-flow-update-node | 1.000 (+) | default | 0.000 |
| skill-flow-eval-local-crud | 1.000 (+) | default | 0.000 |
| skill-flow-delay | 1.000 (+) | default | 0.000 |
| skill-flow-paginated-reference-lookup | 1.000 (+) | default | 0.000 |
| skill-flow-coded-agent | 0.375 (-) | default | 0.000 |
| skill-flow-interactive-customer-escalation-triage | 1.000 (+) | default | 0.000 |
| skill-flow-ixp-invoice-extraction-simulated | 1.000 (+) | default | 0.000 |
| skill-flow-calculator | 1.000 (+) | default | 0.000 |
| skill-flow-transform-filter | 1.000 (+) | default | 0.000 |
| skill-flow-bellevue-weather | 1.000 (+) | default | 0.000 |
| skill-flow-ixp-scaffold-multinode | 1.000 (+) | default | 0.000 |
| skill-flow-feet-inches | 1.000 (+) | default | 0.000 |
| skill-flow-ipe-drive-to-slack | 1.000 (+) | default | 0.000 |
| skill-flow-scheduled-trigger | 1.000 (+) | default | 0.000 |
| skill-flow-terminate | 1.000 (+) | default | 0.000 |
| skill-flow-bellevue-weather-simulated | 0.889 (+) | default | 0.000 |
| skill-flow-trigger-with-filter | 1.000 (+) | default | 0.000 |
| skill-flow-dice-roller | 1.000 (+) | default | 0.000 |
| skill-flow-ipe-query-params | 1.000 (+) | default | 0.000 |
| skill-flow-hitl-smoke-multi-outcome-routing | 1.000 (+) | default | 0.000 |
| skill-flow-devcon-billing-invoice-lookup | 0.909 (+) | default | 0.000 |
| skill-flow-non-catalog-http-fallback | 1.000 (+) | default | 0.000 |
| skill-flow-hitl-schema-design-simulated | 1.000 (+) | default | 0.000 |
| skill-flow-inline-agent-robust | 1.000 (+) | default | 0.000 |
| skill-flow-ipe-dtl-load-by-default-false | 1.000 (+) | default | 0.000 |
| skill-flow-hitl-quality-schema-design | 1.000 (+) | default | 0.000 |
| skill-flow-move-node | 1.000 (+) | default | 0.000 |
| skill-flow-transform-group-by | 1.000 (+) | default | 0.000 |
| skill-flow-batch-transform | 1.000 (+) | default | 0.000 |
| skill-flow-customer-escalation-simulated | 0.938 (+) | default | 0.000 |
| skill-flow-bindings-reconfigure-different-connection | 1.000 (+) | default | 0.000 |
| skill-flow-ipe-multiselect | 1.000 (+) | default | 0.000 |
| skill-flow-lowcode-agent | 1.000 (+) | default | 0.000 |
| skill-flow-openmeteo-weather | 1.000 (+) | default | 0.000 |
| skill-flow-ipe-complex-array | 0.875 (+) | default | 0.000 |
| skill-flow-switch | 1.000 (+) | default | 0.000 |
| skill-flow-devcon-billing-dispute-analyst | 0.500 (-) | default | 0.000 |
| skill-flow-ipe-path-params | 1.000 (+) | default | 0.000 |
| skill-flow-jdbc-databricks-query | 1.000 (+) | default | 0.000 |
| skill-flow-ipe-enhanced-enum | 1.000 (+) | default | 0.000 |
| skill-flow-ipe-jira-search-triage | 1.000 (+) | default | 0.000 |
| skill-flow-hitl-quality-brownfield-insert | 1.000 (+) | default | 0.000 |
| skill-flow-outlook-trigger-inbox | 1.000 (+) | default | 0.000 |
| skill-flow-expense-approval-simulated | 1.000 (+) | default | 0.000 |
| skill-flow-wiki-pageviews | 1.000 (+) | default | 0.000 |
| skill-flow-eval-evaluator-type-choice | 1.000 (+) | default | 0.000 |
| skill-flow-summarize | 1.000 (+) | default | 0.000 |
| skill-flow-add-node | 1.000 (+) | default | 0.000 |
| skill-flow-generic-dynamic-node | 1.000 (+) | default | 0.000 |
| skill-flow-subflow | 1.000 (+) | default | 0.000 |
| skill-flow-ipe-searchable-joins | 1.000 (+) | default | 0.000 |
| skill-flow-hitl-smoke-completed-port | 1.000 (+) | default | 0.000 |
| skill-flow-eval-no-auto-upload | 1.000 (+) | default | 0.000 |
| skill-flow-remove-node | 1.000 (+) | default | 0.000 |
| skill-flow-cli-dice-roller-simulated | 1.000 (+) | default | 0.000 |