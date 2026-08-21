# Experiment Report: skill-tests-smoke

**Description**: Linux PR-gate smoke tests — docker isolation, fast turn budget
**Variants**: default
**Total Duration**: 7698.0s

## Aggregate Metrics

| Metric | default |
|--------|--------|
| Tasks Run | 123 |
| Succeeded | 98 |
| Failed | 21 |
| Errors | 4 |
| Success Rate | 82.4% |
| Score | 0.928 ± 0.175 |
| Avg Duration (s) | 347.7 ± 271.5 |
| Assistant Turns | 42.8 ± 26.1 |
| Tokens | 6,927,969 ± 6,780,589 |
| Replicates/task | 5 |

## Win Rates

- **default**: 123/123 tasks (100%)

## Per-Task Comparison

| Task | default | Best | Spread | Reps |
|------|------|------|--------|------|
| skill-flow-inline-agent-robust | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-remove-node | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-decision | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ixp-scaffold-minimal | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-reading-list | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ipe-drive-to-slack | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-eval-inline-agent | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ipe-jira-get-issue | 0.714 (-) | default | 0.000 | 5 |
| skill-flow-coded-agent | 0.375 (M) | default | 0.000 | 5 |
| skill-flow-ixp-routing-negative/stripe-http | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ixp-routing-negative/slack-summary | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ixp-routing-negative/sf-update | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ixp-routing-negative/http-webhook | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ixp-routing-negative/gsheet-loop | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ixp-routing-negative/queue-write | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ixp-routing-negative/teams-decision | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ixp-routing-negative/delay-email | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ixp-integration-handle-routing | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-paginated-reference-lookup | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-registry-discovery | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ipe-jira-lifecycle | 0.514 (!) | default | 0.000 | 5 |
| skill-flow-summarize | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-scheduled-trigger | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-slack-weather-pipeline | 0.075 (!) | default | 0.000 | 5 |
| skill-flow-eval-no-auto-upload | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ixp-routing/explicit | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ixp-routing/invoice-extraction | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ixp-routing/receipts | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ixp-routing/contracts | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ixp-routing/forms-classify | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-bellevue-weather | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-customer-escalation-simulated | 0.400 (M) | default | 0.000 | 5 |
| skill-flow-ipe-enum | 0.971 (-) | default | 0.000 | 5 |
| skill-flow-hitl-quality-schema-design | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-webhook-waitfor-parallel | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-solution-select-ask | 0.714 (-) | default | 0.000 | 5 |
| skill-flow-terminate | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-merge-parallel-sync | 0.925 (-) | default | 0.000 | 5 |
| skill-flow-multi-city-weather | 0.675 (T) | default | 0.000 | 5 |
| skill-flow-ixp-routing-listing/r01 | 0.900 (-) | default | 0.000 | 5 |
| skill-flow-ixp-routing-listing/r02 | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ixp-routing-listing/r03 | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ixp-routing-listing/r04 | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ixp-routing-listing/r05 | 0.700 (-) | default | 0.000 | 5 |
| skill-flow-ixp-routing-listing/r06 | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ixp-routing-listing/r07 | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ixp-routing-listing/r08 | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ixp-routing-listing/r09 | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ixp-routing-listing/r10 | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-add-output | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-hitl-quality-brownfield-insert | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-feet-inches | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-bindings-multi-connector-independence | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-non-catalog-http-fallback | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-update-node | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-devcon-billing-dispute-resolution | 0.500 (-) | default | 0.000 | 5 |
| skill-flow-cli-dice-roller-simulated | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ipe-complex-array | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ipe-searchable-joins | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 0.562 (!) | default | 0.000 | 5 |
| skill-flow-add-node | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-delay | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-generic-dynamic-node | 0.429 (-) | default | 0.000 | 5 |
| skill-flow-devcon-billing-invoice-lookup | 0.875 (-) | default | 0.000 | 5 |
| skill-flow-ipe-multiselect | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-transform-group-by | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-file-attachment-debug | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ipe-required-groups | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-eval-evaluator-type-choice | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ipe-jira-search-triage | 0.286 (-) | default | 0.000 | 5 |
| skill-flow-eval-local-crud | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-devcon-billing-discrepancy-detector | 0.875 (-) | default | 0.000 | 5 |
| skill-flow-batch-transform | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ipe-jira-create-issue | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-outlook-trigger-inbox | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-hitl-smoke-completed-port | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-hitl-smoke-node-placed | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-devcon-billing-resolution-writer | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ipe-enhanced-enum | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-bindings-idempotent-reconfigure | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-expense-approval-simulated | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-rpa | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-loop-multiply | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-init-validate | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-slack-http-fallback | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-move-node | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ipe-path-params | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-dice-roller | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-hitl-quality-result-downstream | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ixp-e2e-project-selection/aviation | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ipe-dtl-load-by-default-true | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-slack-channel-description | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-wiki-pageviews | 0.800 (T) | default | 0.000 | 5 |
| skill-flow-ixp-invoice-extraction-simulated | 0.900 (+) | default | 0.000 | 5 |
| skill-flow-openmeteo-weather | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-outlook-waitfor-email | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-customer-escalation | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-calculator | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-trigger-with-filter | 0.800 (-) | default | 0.000 | 5 |
| skill-flow-e2e-devcon-expense-approval | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ipe-dtl-load-by-default-false | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-transform-map | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-slack-channel-description-simulated | 0.917 (-) | default | 0.000 | 5 |
| skill-flow-eval-simulation-crud | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-devcon-billing-dispute-analyst | 0.375 (-) | default | 0.000 | 5 |
| skill-flow-api-workflow | 0.675 (-) | default | 0.000 | 5 |
| skill-flow-hitl-smoke-multi-outcome-routing | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-interactive-customer-escalation-triage | 0.890 (-) | default | 0.000 | 5 |
| skill-flow-hitl-quality-boolean-decision | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-group-to-subflow | 0.600 (T) | default | 0.000 | 5 |
| skill-flow-switch | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ipe-query-params | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ipe-ceql-where | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ixp-scaffold-multinode | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-bellevue-weather-simulated | 0.756 (!) | default | 0.000 | 5 |
| skill-flow-subflow | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-bindings-reconfigure-different-connection | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-bindings-no-duplicates | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-ipe-generate-schema | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-transform-filter | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-lowcode-agent | 1.000 (+) | default | 0.000 | 5 |
| skill-flow-hitl-schema-design-simulated | 0.937 (+) | default | 0.000 | 5 |

## Replicate Statistics

| Variant | Replicates/task | Mean score | 95% CI | Pass-rate (Wilson 95%) |
|---------|-----------------|------------|--------|------------------------|
| default | 5 | 0.928 | [0.911, 0.945] | 545/615 [0.86, 0.91] |