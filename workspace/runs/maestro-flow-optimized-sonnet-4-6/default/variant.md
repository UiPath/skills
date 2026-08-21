# Variant Report: default

**Experiment**: skill-tests-smoke
**Description**: Linux PR-gate smoke tests — docker isolation, fast turn budget

## Summary

- **Tasks Run**: 127
- **Succeeded**: 115
- **Failed**: 12
- **Errors**: 0
- **Pass Rate**: 90.6% (115/127)
- **Average Score**: 0.940
- **Average Duration**: 332.0s
- **Total Tokens**: 216,368,117
- **Score Stddev**: 0.177
- **Duration Stddev**: 209.2s

## Task Details

| Task | Score | Status | Avg Duration |
|------|-------|--------|--------------|
| skill-flow-e2e-escalation-orchestrator-paths | 0.474 | FAILURE | 874.2s |
| skill-flow-ixp-routing-negative/stripe-http | 1.000 | SUCCESS | 181.3s |
| skill-flow-ixp-routing-negative/slack-summary | 1.000 | SUCCESS | 221.0s |
| skill-flow-ixp-routing-negative/sf-update | 1.000 | SUCCESS | 203.6s |
| skill-flow-ixp-routing-negative/http-webhook | 1.000 | SUCCESS | 238.1s |
| skill-flow-ixp-routing-negative/gsheet-loop | 1.000 | SUCCESS | 188.4s |
| skill-flow-ixp-routing-negative/queue-write | 1.000 | SUCCESS | 283.2s |
| skill-flow-ixp-routing-negative/teams-decision | 1.000 | SUCCESS | 228.1s |
| skill-flow-ixp-routing-negative/delay-email | 1.000 | SUCCESS | 240.5s |
| skill-flow-ipe-complex-array | 0.875 | SUCCESS | 212.5s |
| skill-flow-ixp-scaffold-multinode | 1.000 | SUCCESS | 565.1s |
| skill-flow-hitl-smoke-node-placed | 1.000 | SUCCESS | 288.6s |
| skill-flow-ixp-invoice-extraction-simulated | 0.900 | SUCCESS | 635.8s |
| skill-flow-lowcode-agent | 1.000 | SUCCESS | 387.1s |
| skill-flow-devcon-billing-dispute-resolution | 0.545 | FAILURE | 997.5s |
| skill-flow-e2e-devcon-expense-approval | 1.000 | SUCCESS | 495.4s |
| skill-flow-decision | 1.000 | SUCCESS | 429.9s |
| skill-flow-generic-dynamic-node | 1.000 | SUCCESS | 434.1s |
| skill-flow-terminate | 1.000 | SUCCESS | 398.4s |
| skill-flow-dice-roller | 1.000 | SUCCESS | 248.6s |
| skill-flow-wiki-pageviews | 1.000 | SUCCESS | 891.0s |
| skill-flow-bindings-reconfigure-different-connection | 1.000 | SUCCESS | 278.3s |
| skill-flow-interactive-customer-escalation-triage | 1.000 | SUCCESS | 477.7s |
| skill-flow-delay | 1.000 | SUCCESS | 156.3s |
| skill-flow-bellevue-weather-simulated | 1.000 | SUCCESS | 372.2s |
| skill-flow-move-node | 1.000 | SUCCESS | 272.6s |
| skill-flow-update-node | 1.000 | SUCCESS | 101.0s |
| skill-flow-ipe-searchable-joins | 1.000 | SUCCESS | 292.8s |
| skill-flow-hitl-smoke-completed-port | 1.000 | SUCCESS | 273.3s |
| skill-flow-devcon-billing-dispute-analyst | 1.000 | SUCCESS | 419.5s |
| skill-flow-feet-inches | 1.000 | SUCCESS | 430.0s |
| skill-flow-expense-approval-simulated | 1.000 | SUCCESS | 469.3s |
| skill-flow-ipe-generate-schema | 1.000 | SUCCESS | 334.7s |
| skill-flow-slack-channel-description-simulated | 0.917 | SUCCESS | 383.2s |
| skill-flow-scheduled-trigger | 1.000 | SUCCESS | 179.8s |
| skill-flow-ixp-routing-listing/r01 | 1.000 | SUCCESS | 42.4s |
| skill-flow-ixp-routing-listing/r02 | 1.000 | SUCCESS | 49.4s |
| skill-flow-ixp-routing-listing/r03 | 1.000 | SUCCESS | 48.0s |
| skill-flow-ixp-routing-listing/r04 | 1.000 | SUCCESS | 62.2s |
| skill-flow-ixp-routing-listing/r05 | 1.000 | SUCCESS | 67.0s |
| skill-flow-ixp-routing-listing/r06 | 1.000 | SUCCESS | 66.0s |
| skill-flow-ixp-routing-listing/r07 | 1.000 | SUCCESS | 50.8s |
| skill-flow-ixp-routing-listing/r08 | 1.000 | SUCCESS | 51.4s |
| skill-flow-ixp-routing-listing/r09 | 1.000 | SUCCESS | 69.6s |
| skill-flow-ixp-routing-listing/r10 | 1.000 | SUCCESS | 57.7s |
| skill-flow-slack-channel-description | 1.000 | SUCCESS | 264.9s |
| skill-flow-group-to-subflow | 1.000 | SUCCESS | 454.1s |
| skill-flow-hitl-quality-brownfield-insert | 1.000 | SUCCESS | 445.7s |
| skill-flow-customer-escalation | 1.000 | SUCCESS | 506.3s |
| skill-flow-ipe-jira-get-issue | 1.000 | SUCCESS | 384.1s |
| skill-flow-eval-no-auto-upload | 1.000 | SUCCESS | 91.3s |
| skill-flow-remove-node | 0.375 | FAILURE | 131.0s |
| skill-flow-ipe-dtl-load-by-default-false | 1.000 | SUCCESS | 407.8s |
| skill-flow-eval-local-crud | 1.000 | SUCCESS | 178.6s |
| skill-flow-ixp-routing/explicit | 1.000 | SUCCESS | 361.5s |
| skill-flow-ixp-routing/invoice-extraction | 1.000 | SUCCESS | 311.6s |
| skill-flow-ixp-routing/receipts | 1.000 | SUCCESS | 157.3s |
| skill-flow-ixp-routing/contracts | 1.000 | SUCCESS | 237.8s |
| skill-flow-ixp-routing/forms-classify | 1.000 | SUCCESS | 240.2s |
| skill-flow-e2e-escalation-slack-alert | 1.000 | SUCCESS | 541.7s |
| skill-flow-add-output | 1.000 | SUCCESS | 105.4s |
| skill-flow-api-workflow | 0.375 | FAILURE | 328.6s |
| skill-flow-eval-evaluator-type-choice | 1.000 | SUCCESS | 163.2s |
| skill-flow-rpa | 1.000 | SUCCESS | 360.5s |
| skill-flow-devcon-billing-discrepancy-detector | 0.500 | FAILURE | 854.9s |
| skill-flow-ipe-jira-search-triage | 1.000 | SUCCESS | 464.1s |
| skill-flow-slack-http-fallback | 1.000 | SUCCESS | 296.9s |
| skill-flow-bindings-multi-connector-independence | 1.000 | SUCCESS | 332.9s |
| skill-flow-ipe-path-params | 1.000 | SUCCESS | 302.7s |
| skill-flow-ixp-e2e-project-selection/aviation | 1.000 | SUCCESS | 367.5s |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 1.000 | SUCCESS | 393.5s |
| skill-flow-cli-dice-roller-simulated | 1.000 | SUCCESS | 345.5s |
| skill-flow-ixp-scaffold-minimal | 1.000 | SUCCESS | 297.1s |
| skill-flow-eval-simulation-crud | 1.000 | SUCCESS | 94.0s |
| skill-flow-ipe-query-params | 1.000 | SUCCESS | 152.9s |
| skill-flow-outlook-waitfor-email | 1.000 | SUCCESS | 174.0s |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 1.000 | SUCCESS | 793.8s |
| skill-flow-eval-inline-agent | 1.000 | SUCCESS | 454.5s |
| skill-flow-ipe-enhanced-enum | 1.000 | SUCCESS | 334.9s |
| skill-flow-customer-escalation-simulated | 0.938 | SUCCESS | 906.2s |
| skill-flow-registry-discovery | 1.000 | SUCCESS | 76.2s |
| skill-flow-loop-multiply | 0.625 | MAX_TURNS_EXHAUSTED | 448.3s |
| skill-flow-paginated-reference-lookup | 1.000 | SUCCESS | 201.5s |
| skill-flow-transform-group-by | 1.000 | SUCCESS | 190.5s |
| skill-flow-ipe-drive-to-slack | 1.000 | SUCCESS | 374.0s |
| skill-flow-trigger-with-filter | 1.000 | SUCCESS | 71.5s |
| skill-flow-devcon-billing-invoice-lookup | 0.909 | SUCCESS | 581.8s |
| skill-flow-hitl-quality-schema-design | 1.000 | SUCCESS | 218.6s |
| skill-flow-non-catalog-http-fallback | 0.400 | FAILURE | 231.6s |
| skill-flow-ipe-ceql-where | 0.200 | FAILURE | 461.8s |
| skill-flow-openmeteo-weather | 1.000 | SUCCESS | 353.2s |
| skill-flow-ipe-multiselect | 1.000 | SUCCESS | 288.1s |
| skill-flow-add-node | 1.000 | SUCCESS | 136.3s |
| skill-flow-outlook-trigger-inbox | 1.000 | SUCCESS | 273.4s |
| skill-flow-devcon-billing-resolution-writer | 1.000 | SUCCESS | 235.0s |
| skill-flow-ipe-jira-lifecycle | 0.286 | FAILURE | 1204.1s |
| skill-flow-e2e-escalation-jira-ticket | 1.000 | SUCCESS | 594.1s |
| skill-flow-ipe-enum | 1.000 | SUCCESS | 504.9s |
| skill-flow-batch-transform | 1.000 | SUCCESS | 239.6s |
| skill-flow-bellevue-weather | 1.000 | SUCCESS | 679.9s |
| skill-flow-bindings-idempotent-reconfigure | 1.000 | SUCCESS | 258.0s |
| skill-flow-jdbc-databricks-query | 1.000 | SUCCESS | 379.4s |
| skill-flow-ixp-integration-handle-routing | 1.000 | SUCCESS | 313.8s |
| skill-flow-coded-agent | 0.375 | FAILURE | 613.6s |
| skill-flow-ipe-jira-create-issue | 1.000 | SUCCESS | 369.2s |
| skill-flow-ipe-dtl-load-by-default-true | 1.000 | SUCCESS | 310.1s |
| skill-flow-hitl-smoke-multi-outcome-routing | 1.000 | SUCCESS | 456.5s |
| skill-flow-solution-select-ask | 1.000 | SUCCESS | 146.9s |
| skill-flow-transform-filter | 1.000 | SUCCESS | 197.6s |
| skill-flow-file-attachment-debug | 1.000 | SUCCESS | 347.3s |
| skill-flow-summarize | 1.000 | SUCCESS | 313.5s |
| skill-flow-merge-parallel-sync | 1.000 | SUCCESS | 167.6s |
| skill-flow-subflow | 1.000 | SUCCESS | 223.8s |
| skill-flow-multi-city-weather | 1.000 | SUCCESS | 751.6s |
| skill-flow-transform-map | 1.000 | SUCCESS | 237.2s |
| skill-flow-hitl-quality-boolean-decision | 1.000 | SUCCESS | 325.6s |
| skill-flow-webhook-waitfor-parallel | 1.000 | SUCCESS | 284.0s |
| skill-flow-reading-list | 1.000 | SUCCESS | 266.5s |
| skill-flow-slack-weather-pipeline | 0.375 | MAX_TURNS_EXHAUSTED | 432.3s |
| skill-flow-init-validate | 1.000 | SUCCESS | 104.1s |
| skill-flow-ipe-required-groups | 1.000 | SUCCESS | 285.6s |
| skill-flow-switch | 0.375 | FAILURE | 301.5s |
| skill-flow-bindings-no-duplicates | 1.000 | SUCCESS | 346.1s |
| skill-flow-inline-agent-robust | 1.000 | SUCCESS | 325.1s |
| skill-flow-hitl-quality-result-downstream | 1.000 | SUCCESS | 294.5s |
| skill-flow-calculator | 1.000 | SUCCESS | 265.4s |
| skill-flow-hitl-schema-design-simulated | 0.895 | SUCCESS | 594.6s |


## Generation Metrics

| Task ID | Total Latency | Turns | Asst Turns | Avg Turn Latency |
|---------|---------------|-------|------------|------------------|
| skill-flow-e2e-escalation-orchestrator-paths | 874.2s | 1 | 62 | 814.7s |
| skill-flow-ixp-routing-negative/stripe-http | 181.3s | 1 | 30 | 171.7s |
| skill-flow-ixp-routing-negative/slack-summary | 221.0s | 1 | 32 | 210.9s |
| skill-flow-ixp-routing-negative/sf-update | 203.6s | 1 | 43 | 192.9s |
| skill-flow-ixp-routing-negative/http-webhook | 238.1s | 1 | 32 | 228.5s |
| skill-flow-ixp-routing-negative/gsheet-loop | 188.4s | 1 | 36 | 178.3s |
| skill-flow-ixp-routing-negative/queue-write | 283.2s | 1 | 52 | 273.2s |
| skill-flow-ixp-routing-negative/teams-decision | 228.1s | 1 | 36 | 216.4s |
| skill-flow-ixp-routing-negative/delay-email | 240.5s | 1 | 40 | 230.5s |
| skill-flow-ipe-complex-array | 212.5s | 1 | 51 | 200.8s |
| skill-flow-ixp-scaffold-multinode | 565.1s | 1 | 43 | 546.2s |
| skill-flow-hitl-smoke-node-placed | 288.6s | 1 | 38 | 268.8s |
| skill-flow-ixp-invoice-extraction-simulated | 635.8s | 3 | 74 | 190.6s |
| skill-flow-lowcode-agent | 387.1s | 1 | 46 | 332.2s |
| skill-flow-devcon-billing-dispute-resolution | 997.5s | 1 | 159 | 929.7s |
| skill-flow-e2e-devcon-expense-approval | 495.4s | 1 | 49 | 477.6s |
| skill-flow-decision | 429.9s | 1 | 23 | 372.5s |
| skill-flow-generic-dynamic-node | 434.1s | 1 | 67 | 390.6s |
| skill-flow-terminate | 398.4s | 1 | 39 | 356.4s |
| skill-flow-dice-roller | 248.6s | 1 | 37 | 199.6s |
| skill-flow-wiki-pageviews | 891.0s | 1 | 61 | 814.7s |
| skill-flow-bindings-reconfigure-different-connection | 278.3s | 1 | 42 | 263.0s |
| skill-flow-interactive-customer-escalation-triage | 477.7s | 3 | 34 | 129.9s |
| skill-flow-delay | 156.3s | 1 | 34 | 142.3s |
| skill-flow-bellevue-weather-simulated | 372.2s | 2 | 52 | 154.9s |
| skill-flow-move-node | 272.6s | 1 | 29 | 223.5s |
| skill-flow-update-node | 101.0s | 1 | 18 | 54.3s |
| skill-flow-ipe-searchable-joins | 292.8s | 1 | 55 | 281.2s |
| skill-flow-hitl-smoke-completed-port | 273.3s | 1 | 30 | 251.7s |
| skill-flow-devcon-billing-dispute-analyst | 419.5s | 1 | 82 | 357.1s |
| skill-flow-feet-inches | 430.0s | 1 | 32 | 379.8s |
| skill-flow-expense-approval-simulated | 469.3s | 2 | 56 | 218.3s |
| skill-flow-ipe-generate-schema | 334.7s | 1 | 72 | 323.8s |
| skill-flow-slack-channel-description-simulated | 383.2s | 2 | 65 | 156.5s |
| skill-flow-scheduled-trigger | 179.8s | 1 | 31 | 163.9s |
| skill-flow-ixp-routing-listing/r01 | 42.4s | 1 | 8 | 39.8s |
| skill-flow-ixp-routing-listing/r02 | 49.4s | 1 | 8 | 46.9s |
| skill-flow-ixp-routing-listing/r03 | 48.0s | 1 | 8 | 45.0s |
| skill-flow-ixp-routing-listing/r04 | 62.2s | 1 | 8 | 56.3s |
| skill-flow-ixp-routing-listing/r05 | 67.0s | 1 | 12 | 62.3s |
| skill-flow-ixp-routing-listing/r06 | 66.0s | 1 | 8 | 62.0s |
| skill-flow-ixp-routing-listing/r07 | 50.8s | 1 | 12 | 47.7s |
| skill-flow-ixp-routing-listing/r08 | 51.4s | 1 | 7 | 46.9s |
| skill-flow-ixp-routing-listing/r09 | 69.6s | 1 | 11 | 60.8s |
| skill-flow-ixp-routing-listing/r10 | 57.7s | 1 | 8 | 49.5s |
| skill-flow-slack-channel-description | 264.9s | 1 | 44 | 227.7s |
| skill-flow-group-to-subflow | 454.1s | 1 | 26 | 411.6s |
| skill-flow-hitl-quality-brownfield-insert | 445.7s | 1 | 69 | 433.7s |
| skill-flow-customer-escalation | 506.3s | 1 | 103 | 488.9s |
| skill-flow-ipe-jira-get-issue | 384.1s | 1 | 74 | 339.9s |
| skill-flow-eval-no-auto-upload | 91.3s | 1 | 18 | 82.9s |
| skill-flow-remove-node | 131.0s | 1 | 17 | 90.2s |
| skill-flow-ipe-dtl-load-by-default-false | 407.8s | 1 | 77 | 399.0s |
| skill-flow-eval-local-crud | 178.6s | 1 | 16 | 169.2s |
| skill-flow-ixp-routing/explicit | 361.5s | 1 | 35 | 353.3s |
| skill-flow-ixp-routing/invoice-extraction | 311.6s | 1 | 40 | 303.7s |
| skill-flow-ixp-routing/receipts | 157.3s | 1 | 36 | 150.2s |
| skill-flow-ixp-routing/contracts | 237.8s | 1 | 36 | 229.5s |
| skill-flow-ixp-routing/forms-classify | 240.2s | 1 | 27 | 233.9s |
| skill-flow-e2e-escalation-slack-alert | 541.7s | 1 | 85 | 494.9s |
| skill-flow-add-output | 105.4s | 1 | 18 | 58.8s |
| skill-flow-api-workflow | 328.6s | 1 | 40 | 294.9s |
| skill-flow-eval-evaluator-type-choice | 163.2s | 1 | 28 | 158.9s |
| skill-flow-rpa | 360.5s | 1 | 55 | 296.4s |
| skill-flow-devcon-billing-discrepancy-detector | 854.9s | 1 | 86 | 815.3s |
| skill-flow-ipe-jira-search-triage | 464.1s | 1 | 87 | 389.0s |
| skill-flow-slack-http-fallback | 296.9s | 1 | 51 | 271.2s |
| skill-flow-bindings-multi-connector-independence | 332.9s | 1 | 43 | 324.3s |
| skill-flow-ipe-path-params | 302.7s | 1 | 58 | 293.7s |
| skill-flow-ixp-e2e-project-selection/aviation | 367.5s | 1 | 72 | 355.4s |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 393.5s | 1 | 69 | 381.2s |
| skill-flow-cli-dice-roller-simulated | 345.5s | 3 | 46 | 98.4s |
| skill-flow-ixp-scaffold-minimal | 297.1s | 1 | 40 | 287.5s |
| skill-flow-eval-simulation-crud | 94.0s | 1 | 19 | 89.9s |
| skill-flow-ipe-query-params | 152.9s | 1 | 36 | 148.4s |
| skill-flow-outlook-waitfor-email | 174.0s | 1 | 42 | 161.0s |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 793.8s | 1 | 98 | 785.9s |
| skill-flow-eval-inline-agent | 454.5s | 1 | 45 | 449.9s |
| skill-flow-ipe-enhanced-enum | 334.9s | 1 | 61 | 329.1s |
| skill-flow-customer-escalation-simulated | 906.2s | 3 | 125 | 285.7s |
| skill-flow-registry-discovery | 76.2s | 1 | 14 | 69.9s |
| skill-flow-loop-multiply | 448.3s | 1 | 81 | 408.8s |
| skill-flow-paginated-reference-lookup | 201.5s | 1 | 57 | 196.6s |
| skill-flow-transform-group-by | 190.5s | 1 | 31 | 181.1s |
| skill-flow-ipe-drive-to-slack | 374.0s | 1 | 73 | 369.3s |
| skill-flow-trigger-with-filter | 71.5s | 1 | 11 | 67.7s |
| skill-flow-devcon-billing-invoice-lookup | 581.8s | 1 | 90 | 499.4s |
| skill-flow-hitl-quality-schema-design | 218.6s | 1 | 47 | 202.4s |
| skill-flow-non-catalog-http-fallback | 231.6s | 1 | 45 | 227.1s |
| skill-flow-ipe-ceql-where | 461.8s | 1 | 80 | 457.2s |
| skill-flow-openmeteo-weather | 353.2s | 1 | 43 | 313.2s |
| skill-flow-ipe-multiselect | 288.1s | 1 | 59 | 282.4s |
| skill-flow-add-node | 136.3s | 1 | 21 | 101.1s |
| skill-flow-outlook-trigger-inbox | 273.4s | 1 | 55 | 255.5s |
| skill-flow-devcon-billing-resolution-writer | 235.0s | 1 | 39 | 188.0s |
| skill-flow-ipe-jira-lifecycle | 1204.1s | 1 | 63 | 599.3s |
| skill-flow-e2e-escalation-jira-ticket | 594.1s | 1 | 73 | 553.5s |
| skill-flow-ipe-enum | 504.9s | 1 | 67 | 499.6s |
| skill-flow-batch-transform | 239.6s | 1 | 30 | 223.9s |
| skill-flow-bellevue-weather | 679.9s | 1 | 39 | 651.0s |
| skill-flow-bindings-idempotent-reconfigure | 258.0s | 1 | 47 | 248.4s |
| skill-flow-jdbc-databricks-query | 379.4s | 1 | 69 | 370.6s |
| skill-flow-ixp-integration-handle-routing | 313.8s | 1 | 39 | 298.9s |
| skill-flow-coded-agent | 613.6s | 1 | 102 | 582.8s |
| skill-flow-ipe-jira-create-issue | 369.2s | 1 | 55 | 322.5s |
| skill-flow-ipe-dtl-load-by-default-true | 310.1s | 1 | 48 | 305.4s |
| skill-flow-hitl-smoke-multi-outcome-routing | 456.5s | 1 | 43 | 444.9s |
| skill-flow-solution-select-ask | 146.9s | 4 | 23 | 26.2s |
| skill-flow-transform-filter | 197.6s | 1 | 32 | 184.4s |
| skill-flow-file-attachment-debug | 347.3s | 1 | 41 | 316.9s |
| skill-flow-summarize | 313.5s | 1 | 36 | 298.9s |
| skill-flow-merge-parallel-sync | 167.6s | 1 | 30 | 151.5s |
| skill-flow-subflow | 223.8s | 1 | 37 | 188.2s |
| skill-flow-multi-city-weather | 751.6s | 1 | 49 | 699.8s |
| skill-flow-transform-map | 237.2s | 1 | 28 | 225.9s |
| skill-flow-hitl-quality-boolean-decision | 325.6s | 1 | 57 | 309.9s |
| skill-flow-webhook-waitfor-parallel | 284.0s | 1 | 50 | 277.8s |
| skill-flow-reading-list | 266.5s | 1 | 27 | 240.8s |
| skill-flow-slack-weather-pipeline | 432.3s | 1 | 72 | 406.6s |
| skill-flow-init-validate | 104.1s | 1 | 22 | 97.9s |
| skill-flow-ipe-required-groups | 285.6s | 1 | 34 | 277.2s |
| skill-flow-switch | 301.5s | 1 | 50 | 265.8s |
| skill-flow-bindings-no-duplicates | 346.1s | 1 | 44 | 337.2s |
| skill-flow-inline-agent-robust | 325.1s | 1 | 45 | 319.5s |
| skill-flow-hitl-quality-result-downstream | 294.5s | 1 | 33 | 282.9s |
| skill-flow-calculator | 265.4s | 1 | 33 | 237.6s |
| skill-flow-hitl-schema-design-simulated | 594.6s | 2 | 37 | 278.3s |


## Token Usage

**Total Tokens**: 216,368,117 (input: 102,817, output: 1,838,395)
**Cache Tokens**: write: 8,525,720, read: 205,901,185
**Agent Cost**: $121.6262
**Eval Overhead (judge + simulator)**: $0.0959
**Total Cost**: $121.7220
**Avg Tokens/Task**: 1,703,685

| Task ID | Input (uncached) | Output | Cache Write | Cache Read | Total | Cost |
|---------|------------------|--------|-------------|------------|-------|------|
| skill-flow-e2e-escalation-orchestrator-paths | 1,247 | 43,231 | 121,490 | 2,581,218 | 2,747,186 | $1.8822 |
| skill-flow-ixp-routing-negative/stripe-http | 594 | 7,460 | 62,213 | 594,264 | 664,531 | $0.5253 |
| skill-flow-ixp-routing-negative/slack-summary | 584 | 8,561 | 48,883 | 666,366 | 724,394 | $0.5134 |
| skill-flow-ixp-routing-negative/sf-update | 594 | 7,092 | 83,765 | 1,267,539 | 1,358,990 | $0.8025 |
| skill-flow-ixp-routing-negative/http-webhook | 590 | 9,887 | 55,173 | 701,992 | 767,642 | $0.5676 |
| skill-flow-ixp-routing-negative/gsheet-loop | 595 | 8,102 | 62,779 | 1,272,908 | 1,344,384 | $0.7406 |
| skill-flow-ixp-routing-negative/queue-write | 599 | 7,001 | 48,399 | 1,620,562 | 1,676,561 | $0.7745 |
| skill-flow-ixp-routing-negative/teams-decision | 589 | 9,879 | 88,141 | 994,491 | 1,093,100 | $0.7788 |
| skill-flow-ixp-routing-negative/delay-email | 595 | 9,301 | 53,624 | 1,075,772 | 1,139,292 | $0.6651 |
| skill-flow-ipe-complex-array | 487 | 8,046 | 80,156 | 1,512,473 | 1,601,162 | $0.8765 |
| skill-flow-ixp-scaffold-multinode | 641 | 30,398 | 62,717 | 1,173,175 | 1,266,931 | $1.0450 |
| skill-flow-hitl-smoke-node-placed | 543 | 13,390 | 58,218 | 1,061,966 | 1,134,117 | $0.7394 |
| skill-flow-ixp-invoice-extraction-simulated | 987 | 27,784 | 102,528 | 2,986,599 | 3,117,898 | $1.7213 |
| skill-flow-lowcode-agent | 524 | 18,045 | 60,265 | 1,431,968 | 1,510,802 | $0.9278 |
| skill-flow-devcon-billing-dispute-resolution | 4,145 | 42,012 | 160,365 | 9,740,498 | 9,947,020 | $4.1661 |
| skill-flow-e2e-devcon-expense-approval | 2,002 | 26,351 | 73,269 | 1,335,201 | 1,436,823 | $1.0766 |
| skill-flow-decision | 497 | 18,178 | 52,027 | 510,544 | 581,246 | $0.6224 |
| skill-flow-generic-dynamic-node | 583 | 14,313 | 97,496 | 3,075,448 | 3,187,840 | $1.5047 |
| skill-flow-terminate | 524 | 17,566 | 63,051 | 1,069,800 | 1,150,941 | $0.8224 |
| skill-flow-dice-roller | 486 | 8,534 | 55,444 | 1,142,248 | 1,206,712 | $0.6801 |
| skill-flow-wiki-pageviews | 793 | 46,137 | 73,876 | 2,350,277 | 2,471,083 | $1.6766 |
| skill-flow-bindings-reconfigure-different-connection | 836 | 10,112 | 83,436 | 1,350,957 | 1,445,341 | $0.8724 |
| skill-flow-interactive-customer-escalation-triage | 1,307 | 20,907 | 70,498 | 959,372 | 1,052,084 | $0.8840 |
| skill-flow-delay | 711 | 4,927 | 44,152 | 907,511 | 957,301 | $0.5139 |
| skill-flow-bellevue-weather-simulated | 735 | 13,672 | 63,794 | 1,410,829 | 1,489,030 | $0.8750 |
| skill-flow-move-node | 518 | 14,057 | 47,240 | 788,387 | 850,202 | $0.6261 |
| skill-flow-update-node | 485 | 2,050 | 67,582 | 320,415 | 390,532 | $0.3818 |
| skill-flow-ipe-searchable-joins | 514 | 12,151 | 82,238 | 1,897,079 | 1,991,982 | $1.0613 |
| skill-flow-hitl-smoke-completed-port | 529 | 13,394 | 55,166 | 587,732 | 656,821 | $0.5857 |
| skill-flow-devcon-billing-dispute-analyst | 2,569 | 15,005 | 84,364 | 3,295,709 | 3,397,647 | $1.5379 |
| skill-flow-feet-inches | 588 | 22,576 | 66,298 | 696,668 | 786,130 | $0.7980 |
| skill-flow-expense-approval-simulated | 913 | 22,347 | 71,689 | 2,163,935 | 2,258,884 | $1.2624 |
| skill-flow-ipe-generate-schema | 550 | 12,280 | 85,747 | 3,680,828 | 3,779,405 | $1.6116 |
| skill-flow-slack-channel-description-simulated | 689 | 12,353 | 93,337 | 2,867,496 | 2,973,875 | $1.4050 |
| skill-flow-scheduled-trigger | 945 | 6,576 | 49,023 | 705,129 | 761,673 | $0.4968 |
| skill-flow-ixp-routing-listing/r01 | 450 | 1,904 | 17,109 | 141,356 | 160,819 | $0.1365 |
| skill-flow-ixp-routing-listing/r02 | 449 | 2,085 | 20,874 | 141,357 | 164,765 | $0.1533 |
| skill-flow-ixp-routing-listing/r03 | 452 | 2,401 | 17,893 | 141,492 | 162,238 | $0.1469 |
| skill-flow-ixp-routing-listing/r04 | 455 | 1,752 | 17,116 | 141,372 | 160,695 | $0.1342 |
| skill-flow-ixp-routing-listing/r05 | 453 | 2,296 | 27,945 | 255,027 | 285,721 | $0.2171 |
| skill-flow-ixp-routing-listing/r06 | 454 | 3,243 | 20,888 | 141,376 | 165,961 | $0.1707 |
| skill-flow-ixp-routing-listing/r07 | 448 | 1,875 | 17,485 | 141,554 | 161,362 | $0.1375 |
| skill-flow-ixp-routing-listing/r08 | 453 | 2,303 | 17,015 | 101,000 | 120,771 | $0.1300 |
| skill-flow-ixp-routing-listing/r09 | 455 | 1,915 | 21,151 | 189,680 | 213,201 | $0.1663 |
| skill-flow-ixp-routing-listing/r10 | 451 | 2,056 | 17,112 | 141,361 | 160,980 | $0.1388 |
| skill-flow-slack-channel-description | 489 | 10,229 | 76,187 | 1,289,065 | 1,375,970 | $0.8273 |
| skill-flow-group-to-subflow | 506 | 28,285 | 60,328 | 676,325 | 765,444 | $0.8549 |
| skill-flow-hitl-quality-brownfield-insert | 677 | 24,025 | 68,727 | 2,589,750 | 2,683,179 | $1.3971 |
| skill-flow-customer-escalation | 658 | 22,816 | 96,755 | 5,231,091 | 5,351,320 | $2.2764 |
| skill-flow-ipe-jira-get-issue | 612 | 13,989 | 91,167 | 3,459,753 | 3,565,521 | $1.5915 |
| skill-flow-eval-no-auto-upload | 893 | 2,702 | 19,255 | 381,849 | 404,699 | $0.2300 |
| skill-flow-remove-node | 471 | 3,995 | 43,920 | 490,056 | 538,442 | $0.3731 |
| skill-flow-ipe-dtl-load-by-default-false | 517 | 18,431 | 101,788 | 3,397,101 | 3,517,837 | $1.6789 |
| skill-flow-eval-local-crud | 839 | 9,576 | 24,857 | 364,060 | 399,332 | $0.3486 |
| skill-flow-ixp-routing/explicit | 604 | 17,511 | 79,992 | 1,034,704 | 1,132,811 | $0.8749 |
| skill-flow-ixp-routing/invoice-extraction | 615 | 15,981 | 81,368 | 1,445,821 | 1,543,785 | $0.9804 |
| skill-flow-ixp-routing/receipts | 596 | 5,791 | 52,612 | 1,074,844 | 1,133,843 | $0.6084 |
| skill-flow-ixp-routing/contracts | 597 | 9,732 | 60,209 | 1,104,267 | 1,174,805 | $0.7048 |
| skill-flow-ixp-routing/forms-classify | 593 | 11,212 | 56,739 | 713,231 | 781,775 | $0.5967 |
| skill-flow-e2e-escalation-slack-alert | 925 | 24,645 | 106,902 | 4,176,514 | 4,308,986 | $2.0263 |
| skill-flow-add-output | 474 | 1,981 | 37,373 | 532,304 | 572,132 | $0.3310 |
| skill-flow-api-workflow | 494 | 14,750 | 60,918 | 875,660 | 951,822 | $0.7139 |
| skill-flow-eval-evaluator-type-choice | 990 | 8,573 | 23,134 | 545,081 | 577,778 | $0.3818 |
| skill-flow-rpa | 504 | 15,279 | 64,076 | 1,712,192 | 1,792,051 | $0.9846 |
| skill-flow-devcon-billing-discrepancy-detector | 879 | 40,622 | 121,105 | 4,728,740 | 4,891,346 | $2.4847 |
| skill-flow-ipe-jira-search-triage | 638 | 18,319 | 106,382 | 3,846,253 | 3,971,592 | $1.8295 |
| skill-flow-slack-http-fallback | 549 | 11,905 | 99,007 | 1,504,914 | 1,616,375 | $1.0030 |
| skill-flow-bindings-multi-connector-independence | 11,102 | 17,867 | 75,037 | 1,163,841 | 1,267,847 | $0.9319 |
| skill-flow-ipe-path-params | 556 | 13,344 | 81,922 | 1,762,199 | 1,858,021 | $1.0377 |
| skill-flow-ixp-e2e-project-selection/aviation | 630 | 17,306 | 70,012 | 3,121,451 | 3,209,399 | $1.4605 |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 615 | 16,780 | 95,429 | 3,100,976 | 3,213,800 | $1.5417 |
| skill-flow-cli-dice-roller-simulated | 677 | 12,342 | 68,334 | 1,632,064 | 1,713,417 | $0.9415 |
| skill-flow-ixp-scaffold-minimal | 616 | 15,975 | 70,772 | 1,184,770 | 1,272,133 | $0.8623 |
| skill-flow-eval-simulation-crud | 961 | 3,313 | 28,370 | 423,933 | 456,577 | $0.2861 |
| skill-flow-ipe-query-params | 524 | 5,563 | 61,484 | 852,521 | 920,092 | $0.5713 |
| skill-flow-outlook-waitfor-email | 547 | 6,006 | 76,034 | 1,113,119 | 1,195,706 | $0.7108 |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 626 | 38,611 | 113,479 | 5,346,061 | 5,498,777 | $2.6104 |
| skill-flow-eval-inline-agent | 1,077 | 24,423 | 78,641 | 1,642,713 | 1,746,854 | $1.1573 |
| skill-flow-ipe-enhanced-enum | 567 | 14,714 | 86,238 | 2,444,249 | 2,545,768 | $1.2791 |
| skill-flow-customer-escalation-simulated | 2,673 | 41,714 | 156,036 | 4,911,159 | 5,111,582 | $2.7091 |
| skill-flow-registry-discovery | 572 | 2,429 | 22,923 | 329,250 | 355,174 | $0.2229 |
| skill-flow-loop-multiply | 519 | 22,350 | 67,510 | 3,174,985 | 3,265,364 | $1.5425 |
| skill-flow-paginated-reference-lookup | 564 | 7,230 | 82,421 | 2,595,131 | 2,685,346 | $1.1978 |
| skill-flow-transform-group-by | 897 | 7,736 | 50,867 | 893,682 | 953,182 | $0.5776 |
| skill-flow-ipe-drive-to-slack | 610 | 16,181 | 89,518 | 2,685,395 | 2,791,704 | $1.3859 |
| skill-flow-trigger-with-filter | 534 | 3,573 | 27,115 | 201,345 | 232,567 | $0.2173 |
| skill-flow-devcon-billing-invoice-lookup | 680 | 21,736 | 86,474 | 3,791,164 | 3,900,054 | $1.7897 |
| skill-flow-hitl-quality-schema-design | 623 | 9,026 | 66,405 | 1,495,264 | 1,571,318 | $0.8349 |
| skill-flow-non-catalog-http-fallback | 537 | 9,533 | 74,973 | 1,040,421 | 1,125,464 | $0.7379 |
| skill-flow-ipe-ceql-where | 685 | 20,810 | 90,445 | 3,235,382 | 3,347,322 | $1.6240 |
| skill-flow-openmeteo-weather | 552 | 13,720 | 81,404 | 1,206,853 | 1,302,529 | $0.8748 |
| skill-flow-ipe-multiselect | 477 | 10,724 | 57,500 | 1,769,208 | 1,837,909 | $0.9087 |
| skill-flow-add-node | 500 | 5,988 | 38,710 | 603,623 | 648,821 | $0.4176 |
| skill-flow-outlook-trigger-inbox | 594 | 10,051 | 78,364 | 2,373,165 | 2,462,174 | $1.1584 |
| skill-flow-devcon-billing-resolution-writer | 643 | 8,743 | 74,740 | 1,301,442 | 1,385,568 | $0.8038 |
| skill-flow-ipe-jira-lifecycle | 740 | 28,767 | 94,345 | 2,392,319 | 2,516,171 | $1.5052 |
| skill-flow-e2e-escalation-jira-ticket | 884 | 27,442 | 88,538 | 2,654,448 | 2,771,312 | $1.5426 |
| skill-flow-ipe-enum | 585 | 22,798 | 88,429 | 2,701,261 | 2,813,073 | $1.4857 |
| skill-flow-batch-transform | 917 | 10,984 | 53,956 | 735,401 | 801,258 | $0.5905 |
| skill-flow-bellevue-weather | 565 | 36,965 | 68,387 | 943,583 | 1,049,500 | $1.0957 |
| skill-flow-bindings-idempotent-reconfigure | 606 | 9,521 | 59,782 | 1,212,169 | 1,282,078 | $0.7325 |
| skill-flow-jdbc-databricks-query | 627 | 11,689 | 93,525 | 3,372,485 | 3,478,326 | $1.5397 |
| skill-flow-ixp-integration-handle-routing | 782 | 15,153 | 60,864 | 915,747 | 992,546 | $0.7326 |
| skill-flow-coded-agent | 2,812 | 18,843 | 90,322 | 4,716,606 | 4,828,583 | $2.0448 |
| skill-flow-ipe-jira-create-issue | 628 | 13,368 | 81,583 | 2,109,405 | 2,204,984 | $1.1412 |
| skill-flow-ipe-dtl-load-by-default-true | 512 | 11,342 | 59,918 | 1,267,046 | 1,338,818 | $0.7765 |
| skill-flow-hitl-smoke-multi-outcome-routing | 641 | 25,206 | 60,190 | 1,479,945 | 1,565,982 | $1.0497 |
| skill-flow-solution-select-ask | 457 | 2,825 | 32,386 | 426,925 | 462,593 | $0.2950 |
| skill-flow-transform-filter | 851 | 8,442 | 65,921 | 842,046 | 917,260 | $0.6290 |
| skill-flow-file-attachment-debug | 610 | 14,201 | 59,855 | 1,277,773 | 1,352,439 | $0.8226 |
| skill-flow-summarize | 984 | 16,649 | 73,789 | 1,158,066 | 1,249,488 | $0.8768 |
| skill-flow-merge-parallel-sync | 1,143 | 7,631 | 49,866 | 507,043 | 565,683 | $0.4570 |
| skill-flow-subflow | 514 | 6,879 | 61,809 | 1,095,654 | 1,164,856 | $0.6652 |
| skill-flow-multi-city-weather | 570 | 40,743 | 88,246 | 1,370,614 | 1,500,173 | $1.3550 |
| skill-flow-transform-map | 860 | 11,419 | 57,369 | 765,132 | 834,780 | $0.6185 |
| skill-flow-hitl-quality-boolean-decision | 670 | 16,638 | 61,841 | 1,747,926 | 1,827,075 | $1.0079 |
| skill-flow-webhook-waitfor-parallel | 642 | 12,335 | 83,378 | 1,640,909 | 1,737,264 | $0.9919 |
| skill-flow-reading-list | 978 | 11,956 | 70,687 | 660,504 | 744,125 | $0.6455 |
| skill-flow-slack-weather-pipeline | 635 | 17,394 | 103,903 | 4,345,011 | 4,466,943 | $1.9560 |
| skill-flow-init-validate | 555 | 3,549 | 32,049 | 374,761 | 410,914 | $0.2875 |
| skill-flow-ipe-required-groups | 468 | 12,626 | 73,106 | 842,669 | 928,869 | $0.7177 |
| skill-flow-switch | 553 | 15,329 | 60,168 | 1,434,818 | 1,510,868 | $0.8877 |
| skill-flow-bindings-no-duplicates | 521 | 17,119 | 75,086 | 1,555,444 | 1,648,170 | $1.0066 |
| skill-flow-inline-agent-robust | 630 | 17,519 | 74,787 | 1,136,095 | 1,229,031 | $0.8860 |
| skill-flow-hitl-quality-result-downstream | 651 | 16,043 | 56,125 | 685,894 | 758,713 | $0.6588 |
| skill-flow-calculator | 486 | 8,193 | 57,020 | 944,805 | 1,010,504 | $0.6216 |
| skill-flow-hitl-schema-design-simulated | 854 | 35,185 | 81,501 | 686,809 | 804,349 | $1.0563 |


## Command Telemetry

**Total Commands**: 3311
**Success Rate**: 3131/3311 (94.6%)

### Commands by Tool

| Tool | Count | % |
|------|-------|---|
| Bash | 2078 | 62.8% |
| Read | 738 | 22.3% |
| Edit | 271 | 8.2% |
| Skill | 127 | 3.8% |
| Write | 48 | 1.4% |
| Glob | 24 | 0.7% |
| Grep | 17 | 0.5% |
| TaskUpdate | 4 | 0.1% |
| TaskCreate | 2 | 0.1% |
| Agent | 2 | 0.1% |

### Performance

- **Average Command Time**: 3562.3ms
- **Total Command Time**: 11794.88s

### Slowest Commands

| Tool | Duration | Parameters |
|------|----------|------------|
| Bash | 77397ms | {'command': 'uip maestro flow registry get core.co... |
| Bash | 72040ms | {'command': 'cd /work/output/artifacts/skill-flow-... |
| Bash | 64541ms | {'command': 'grep -rl \'"core.action.queue\' /home... |
| Bash | 48607ms | {'command': 'grep -r \'"core.action.queue\' /home/... |
| Bash | 44776ms | {'command': '\\\n  uip maestro flow registry searc... |

**Most Common Pattern**: `Bash → Bash → Bash`

**Skill Tool Invoked**: 127 time(s)

## Agent Settings

- **Permission Mode**: acceptEdits
- **Allowed Tools**: Skill, Bash, Read, Write, Edit, Glob, Grep
- **Model**: us.anthropic.claude-sonnet-4-6
- **Max Turns**: 200
- **System Prompt**: You are a coding agent. Do not access files in sibling runs/* directories. Everywhere else is permitted. 
- **Plugins**: /home/azureuser/projects/skills/tmp

## Environment

- **git_commit**: unknown
- **skills_git_commit**: unknown
- **cli_version**: 1.201.0-dev.8272
- **tool_plugins**: {'admin-tool': '1.201.0-dev.8272', 'agent-tool': '1.201.0-dev.8272', 'agenthub-tool': '1.201.0-dev.8272', 'aops-tool': '1.201.0-dev.8272', 'api-workflow-tool': '1.201.0-dev.8272', 'automation-hub-tool': '1.201.0-dev.8272', 'codedagent-tool': '1.201.0-dev.8272', 'codedapp-tool': '1.201.0-dev.8272', 'coder-tool': '1.201.0-dev.8272', 'context-grounding-tool': '1.201.0-dev.8272', 'conversational-tool': '1.201.0-dev.8272', 'data-fabric-tool': '1.201.0-dev.8272', 'docsai-tool': '1.201.0-dev.8272', 'function-tool': '1.201.0-dev.8272', 'gov-tool': '1.201.0-dev.8272', 'guardrails-tool': '1.201.0-dev.8272', 'insights-tool': '1.201.0-dev.8276', 'integrationservice-tool': '1.201.0-dev.8272', 'ixp-tool': '1.201.0-dev.8272', 'llm-gateway-tool': '1.201.0-dev.8272', 'llmgw-tool': '1.201.0-dev.8272', 'maestro-tool': '1.201.0-dev.8275', 'model-hub-tool': '1.201.0-dev.8272', 'orchestrator-tool': '1.201.0-dev.8272', 'platform-tool': '1.201.0-dev.8272', 'pm-tool': '1.201.0-dev.8272', 'rpa-legacy-tool': '1.201.0-dev.8272', 'rpa-tool': '1.201.0-dev.20260809.3', 'solution-tool': '1.201.0-dev.8272', 'tasks-tool': '1.201.0-dev.8272', 'test-manager-tool': '1.201.0-dev.8272', 'traces-tool': '1.201.0-dev.8272', 'vertical-solutions-tool': '1.201.0-dev.8272'}
- **coder_eval**: 0.9.6
- **claude_code_cli**: 2.1.177 (Claude Code)
- **uv**: uv 0.12.5 (x86_64-unknown-linux-gnu)
- **anthropic**: 0.122.0
- **openai**: 3.2.0
- **pydantic**: 2.12.5
- **api_routing**: aws_bedrock
- **eval_routing**: aws_bedrock
- **aws_region**: us-east-2
- **bedrock_model**: us.anthropic.claude-sonnet-4-6
- **system_prompt_semantics**: append