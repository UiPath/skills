# Variant Report: default

**Experiment**: skill-tests-smoke
**Description**: Linux PR-gate smoke tests — docker isolation, fast turn budget

## Summary

- **Tasks Run**: 127
- **Succeeded**: 108
- **Failed**: 14
- **Errors**: 5
- **Pass Rate**: 85.0% (108/127)
- **Average Score**: 0.892
- **Average Duration**: 342.4s
- **Total Tokens**: 488,397,358
- **Score Stddev**: 0.276
- **Duration Stddev**: 283.3s

## Task Details

| Task | Score | Status | Avg Duration |
|------|-------|--------|--------------|
| skill-flow-paginated-reference-lookup | 1.000 | SUCCESS | 178.0s |
| skill-flow-summarize | 1.000 | SUCCESS | 118.5s |
| skill-flow-slack-channel-description-simulated | 1.000 | SUCCESS | 314.0s |
| skill-flow-loop-multiply | 0.625 | MAX_TURNS_EXHAUSTED | 534.7s |
| skill-flow-ipe-searchable-joins | 0.375 | FAILURE | 451.3s |
| skill-flow-bellevue-weather-simulated | 1.000 | SUCCESS | 541.5s |
| skill-flow-lowcode-agent | 1.000 | SUCCESS | 295.4s |
| skill-flow-bindings-reconfigure-different-connection | 1.000 | SUCCESS | 278.0s |
| skill-flow-ixp-invoice-extraction-simulated | 0.000 | ERROR | 0.0s |
| skill-flow-group-to-subflow | 0.000 | TIMEOUT | 908.7s |
| skill-flow-eval-simulation-crud | 1.000 | SUCCESS | 98.8s |
| skill-flow-cli-dice-roller-simulated | 1.000 | SUCCESS | 249.3s |
| skill-flow-batch-transform | 1.000 | SUCCESS | 181.3s |
| skill-flow-inline-agent-robust | 1.000 | SUCCESS | 338.3s |
| skill-flow-add-output | 1.000 | SUCCESS | 129.0s |
| skill-flow-dice-roller | 1.000 | SUCCESS | 125.6s |
| skill-flow-slack-channel-description | 1.000 | SUCCESS | 246.0s |
| skill-flow-rpa | 1.000 | SUCCESS | 300.9s |
| skill-flow-generic-dynamic-node | 1.000 | SUCCESS | 332.1s |
| skill-flow-ipe-dtl-load-by-default-true | 0.750 | FAILURE | 393.2s |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 0.000 | ERROR | 0.0s |
| skill-flow-webhook-waitfor-parallel | 1.000 | SUCCESS | 238.2s |
| skill-flow-ipe-jira-search-triage | 1.000 | SUCCESS | 532.7s |
| skill-flow-ixp-routing/explicit | 0.000 | ERROR | 0.0s |
| skill-flow-ixp-routing/invoice-extraction | 1.000 | SUCCESS | 802.9s |
| skill-flow-ixp-routing/receipts | 1.000 | SUCCESS | 773.1s |
| skill-flow-ixp-routing/contracts | 1.000 | SUCCESS | 783.0s |
| skill-flow-ixp-routing/forms-classify | 1.000 | SUCCESS | 251.1s |
| skill-flow-terminate | 1.000 | SUCCESS | 282.2s |
| skill-flow-devcon-billing-resolution-writer | 1.000 | SUCCESS | 468.8s |
| skill-flow-ipe-query-params | 1.000 | SUCCESS | 163.1s |
| skill-flow-devcon-billing-dispute-analyst | 1.000 | SUCCESS | 823.4s |
| skill-flow-openmeteo-weather | 1.000 | SUCCESS | 234.7s |
| skill-flow-update-node | 1.000 | SUCCESS | 107.8s |
| skill-flow-ixp-routing-negative/stripe-http | 1.000 | SUCCESS | 215.8s |
| skill-flow-ixp-routing-negative/slack-summary | 1.000 | SUCCESS | 166.7s |
| skill-flow-ixp-routing-negative/sf-update | 1.000 | SUCCESS | 210.8s |
| skill-flow-ixp-routing-negative/http-webhook | 1.000 | SUCCESS | 284.2s |
| skill-flow-ixp-routing-negative/gsheet-loop | 1.000 | SUCCESS | 197.7s |
| skill-flow-ixp-routing-negative/queue-write | 1.000 | SUCCESS | 222.6s |
| skill-flow-ixp-routing-negative/teams-decision | 1.000 | SUCCESS | 230.8s |
| skill-flow-ixp-routing-negative/delay-email | 1.000 | SUCCESS | 273.7s |
| skill-flow-eval-no-auto-upload | 1.000 | SUCCESS | 93.3s |
| skill-flow-transform-map | 1.000 | SUCCESS | 149.1s |
| skill-flow-ipe-ceql-where | 1.000 | SUCCESS | 438.3s |
| skill-flow-hitl-smoke-completed-port | 1.000 | SUCCESS | 398.2s |
| skill-flow-ixp-routing-listing/r01 | 1.000 | SUCCESS | 46.2s |
| skill-flow-ixp-routing-listing/r02 | 1.000 | SUCCESS | 47.4s |
| skill-flow-ixp-routing-listing/r03 | 1.000 | SUCCESS | 41.2s |
| skill-flow-ixp-routing-listing/r04 | 1.000 | SUCCESS | 45.4s |
| skill-flow-ixp-routing-listing/r05 | 1.000 | SUCCESS | 51.7s |
| skill-flow-ixp-routing-listing/r06 | 1.000 | SUCCESS | 52.0s |
| skill-flow-ixp-routing-listing/r07 | 1.000 | SUCCESS | 48.6s |
| skill-flow-ixp-routing-listing/r08 | 1.000 | SUCCESS | 63.4s |
| skill-flow-ixp-routing-listing/r09 | 1.000 | SUCCESS | 50.0s |
| skill-flow-ixp-routing-listing/r10 | 1.000 | SUCCESS | 52.0s |
| skill-flow-slack-weather-pipeline | 0.375 | MAX_TURNS_EXHAUSTED | 636.9s |
| skill-flow-hitl-quality-brownfield-insert | 1.000 | SUCCESS | 295.3s |
| skill-flow-devcon-billing-invoice-lookup | 1.000 | SUCCESS | 929.1s |
| skill-flow-non-catalog-http-fallback | 1.000 | SUCCESS | 278.6s |
| skill-flow-ipe-enhanced-enum | 1.000 | SUCCESS | 406.9s |
| skill-flow-ixp-integration-handle-routing | 1.000 | SUCCESS | 690.2s |
| skill-flow-calculator | 1.000 | SUCCESS | 155.4s |
| skill-flow-eval-inline-agent | 1.000 | SUCCESS | 348.1s |
| skill-flow-scheduled-trigger | 0.375 | FAILURE | 130.6s |
| skill-flow-api-workflow | 0.375 | FAILURE | 241.5s |
| skill-flow-coded-agent | 0.375 | FAILURE | 814.8s |
| skill-flow-feet-inches | 1.000 | SUCCESS | 457.2s |
| skill-flow-ixp-e2e-project-selection/aviation | 1.000 | SUCCESS | 771.4s |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 1.000 | SUCCESS | 658.2s |
| skill-flow-bindings-no-duplicates | 0.600 | MAX_TURNS_EXHAUSTED | 591.7s |
| skill-flow-file-attachment-debug | 0.500 | FAILURE | 139.7s |
| skill-flow-delay | 1.000 | SUCCESS | 164.7s |
| skill-flow-multi-city-weather | 1.000 | SUCCESS | 625.9s |
| skill-flow-decision | 1.000 | SUCCESS | 166.7s |
| skill-flow-ipe-jira-get-issue | 1.000 | SUCCESS | 421.5s |
| skill-flow-ipe-jira-create-issue | 1.000 | SUCCESS | 284.3s |
| skill-flow-eval-local-crud | 1.000 | SUCCESS | 110.9s |
| skill-flow-init-validate | 1.000 | SUCCESS | 35.6s |
| skill-flow-devcon-billing-dispute-resolution | 1.000 | SUCCESS | 1834.5s |
| skill-flow-ipe-dtl-load-by-default-false | 1.000 | SUCCESS | 710.4s |
| skill-flow-expense-approval-simulated | 1.000 | SUCCESS | 505.7s |
| skill-flow-e2e-escalation-orchestrator-paths | 1.000 | SUCCESS | 913.2s |
| skill-flow-hitl-quality-result-downstream | 1.000 | SUCCESS | 295.4s |
| skill-flow-customer-escalation-simulated | 1.000 | SUCCESS | 905.5s |
| skill-flow-ixp-scaffold-minimal | 1.000 | SUCCESS | 347.2s |
| skill-flow-hitl-quality-boolean-decision | 1.000 | SUCCESS | 337.0s |
| skill-flow-subflow | 1.000 | SUCCESS | 188.4s |
| skill-flow-e2e-escalation-slack-alert | 1.000 | SUCCESS | 461.1s |
| skill-flow-bellevue-weather | 1.000 | SUCCESS | 313.9s |
| skill-flow-hitl-smoke-node-placed | 1.000 | SUCCESS | 500.3s |
| skill-flow-eval-evaluator-type-choice | 1.000 | SUCCESS | 85.3s |
| skill-flow-merge-parallel-sync | 1.000 | SUCCESS | 84.7s |
| skill-flow-hitl-quality-schema-design | 1.000 | SUCCESS | 486.3s |
| skill-flow-ipe-path-params | 1.000 | SUCCESS | 207.1s |
| skill-flow-switch | 1.000 | SUCCESS | 286.9s |
| skill-flow-remove-node | 1.000 | SUCCESS | 371.2s |
| skill-flow-outlook-trigger-inbox | 1.000 | SUCCESS | 239.5s |
| skill-flow-interactive-customer-escalation-triage | 1.000 | SUCCESS | 288.8s |
| skill-flow-outlook-waitfor-email | 1.000 | SUCCESS | 210.7s |
| skill-flow-solution-select-ask | 1.000 | SUCCESS | 84.0s |
| skill-flow-hitl-schema-design-simulated | 1.000 | SUCCESS | 525.6s |
| skill-flow-reading-list | 1.000 | SUCCESS | 287.4s |
| skill-flow-e2e-escalation-jira-ticket | 0.684 | FAILURE | 715.1s |
| skill-flow-ipe-multiselect | 0.000 | FAILURE | 156.8s |
| skill-flow-registry-discovery | 1.000 | SUCCESS | 67.1s |
| skill-flow-ipe-enum | 1.000 | SUCCESS | 692.0s |
| skill-flow-bindings-idempotent-reconfigure | 1.000 | SUCCESS | 301.6s |
| skill-flow-ixp-scaffold-multinode | 0.000 | ERROR | 0.0s |
| skill-flow-hitl-smoke-multi-outcome-routing | 1.000 | SUCCESS | 444.9s |
| skill-flow-jdbc-databricks-query | 1.000 | SUCCESS | 298.3s |
| skill-flow-transform-group-by | 1.000 | SUCCESS | 139.6s |
| skill-flow-ipe-generate-schema | 1.000 | SUCCESS | 260.3s |
| skill-flow-ipe-complex-array | 0.875 | SUCCESS | 163.1s |
| skill-flow-bindings-multi-connector-independence | 1.000 | SUCCESS | 371.4s |
| skill-flow-trigger-with-filter | 1.000 | SUCCESS | 51.7s |
| skill-flow-add-node | 1.000 | SUCCESS | 127.4s |
| skill-flow-ipe-required-groups | 1.000 | SUCCESS | 319.5s |
| skill-flow-e2e-devcon-expense-approval | 1.000 | SUCCESS | 564.8s |
| skill-flow-slack-http-fallback | 1.000 | SUCCESS | 301.1s |
| skill-flow-ipe-jira-lifecycle | 0.000 | ERROR | 0.0s |
| skill-flow-transform-filter | 1.000 | SUCCESS | 152.6s |
| skill-flow-ipe-drive-to-slack | 1.000 | SUCCESS | 398.6s |
| skill-flow-move-node | 0.375 | MAX_TURNS_EXHAUSTED | 529.5s |
| skill-flow-devcon-billing-discrepancy-detector | 1.000 | SUCCESS | 1092.1s |
| skill-flow-customer-escalation | 1.000 | SUCCESS | 751.0s |
| skill-flow-wiki-pageviews | 0.000 | TIMEOUT | 903.1s |


## Generation Metrics

| Task ID | Total Latency | Turns | Asst Turns | Avg Turn Latency |
|---------|---------------|-------|------------|------------------|
| skill-flow-paginated-reference-lookup | 178.0s | 1 | 48 | 168.7s |
| skill-flow-summarize | 118.5s | 1 | 26 | 106.0s |
| skill-flow-slack-channel-description-simulated | 314.0s | 2 | 60 | 132.9s |
| skill-flow-loop-multiply | 534.7s | 1 | 94 | 501.0s |
| skill-flow-ipe-searchable-joins | 451.3s | 1 | 47 | 443.2s |
| skill-flow-bellevue-weather-simulated | 541.5s | 4 | 72 | 120.0s |
| skill-flow-lowcode-agent | 295.4s | 1 | 27 | 197.2s |
| skill-flow-bindings-reconfigure-different-connection | 278.0s | 1 | 53 | 266.1s |
| skill-flow-ixp-invoice-extraction-simulated | 1396.9s | 3 | 106 | 452.8s |
| skill-flow-group-to-subflow | 908.7s | 1 | 70 | 900.0s |
| skill-flow-eval-simulation-crud | 98.8s | 1 | 27 | 87.2s |
| skill-flow-cli-dice-roller-simulated | 249.3s | 4 | 40 | 49.0s |
| skill-flow-batch-transform | 181.3s | 1 | 43 | 166.8s |
| skill-flow-inline-agent-robust | 338.3s | 1 | 82 | 327.4s |
| skill-flow-add-output | 129.0s | 1 | 21 | 94.9s |
| skill-flow-dice-roller | 125.6s | 1 | 28 | 103.9s |
| skill-flow-slack-channel-description | 246.0s | 1 | 55 | 213.3s |
| skill-flow-rpa | 300.9s | 1 | 51 | 209.2s |
| skill-flow-generic-dynamic-node | 332.1s | 1 | 93 | 292.3s |
| skill-flow-ipe-dtl-load-by-default-true | 393.2s | 1 | 87 | 386.4s |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 1209.2s | 1 | 186 | 1200.2s |
| skill-flow-webhook-waitfor-parallel | 238.2s | 1 | 60 | 228.0s |
| skill-flow-ipe-jira-search-triage | 532.7s | 1 | 96 | 470.4s |
| skill-flow-ixp-routing/explicit | 909.9s | 1 | 78 | 900.0s |
| skill-flow-ixp-routing/invoice-extraction | 802.9s | 1 | 127 | 797.2s |
| skill-flow-ixp-routing/receipts | 773.1s | 1 | 99 | 763.9s |
| skill-flow-ixp-routing/contracts | 783.0s | 1 | 138 | 773.5s |
| skill-flow-ixp-routing/forms-classify | 251.1s | 1 | 44 | 243.1s |
| skill-flow-terminate | 282.2s | 1 | 62 | 259.1s |
| skill-flow-devcon-billing-resolution-writer | 468.8s | 1 | 103 | 434.2s |
| skill-flow-ipe-query-params | 163.1s | 1 | 38 | 152.5s |
| skill-flow-devcon-billing-dispute-analyst | 823.4s | 1 | 145 | 769.3s |
| skill-flow-openmeteo-weather | 234.7s | 1 | 61 | 201.8s |
| skill-flow-update-node | 107.8s | 1 | 23 | 67.7s |
| skill-flow-ixp-routing-negative/stripe-http | 215.8s | 1 | 42 | 206.0s |
| skill-flow-ixp-routing-negative/slack-summary | 166.7s | 1 | 42 | 163.5s |
| skill-flow-ixp-routing-negative/sf-update | 210.8s | 1 | 61 | 209.0s |
| skill-flow-ixp-routing-negative/http-webhook | 284.2s | 1 | 65 | 282.1s |
| skill-flow-ixp-routing-negative/gsheet-loop | 197.7s | 1 | 52 | 195.4s |
| skill-flow-ixp-routing-negative/queue-write | 222.6s | 1 | 53 | 220.6s |
| skill-flow-ixp-routing-negative/teams-decision | 230.8s | 1 | 45 | 229.2s |
| skill-flow-ixp-routing-negative/delay-email | 273.7s | 1 | 51 | 272.2s |
| skill-flow-eval-no-auto-upload | 93.3s | 1 | 37 | 91.6s |
| skill-flow-transform-map | 149.1s | 1 | 40 | 142.7s |
| skill-flow-ipe-ceql-where | 438.3s | 1 | 77 | 435.4s |
| skill-flow-hitl-smoke-completed-port | 398.2s | 1 | 49 | 392.4s |
| skill-flow-ixp-routing-listing/r01 | 46.2s | 1 | 12 | 44.4s |
| skill-flow-ixp-routing-listing/r02 | 47.4s | 1 | 15 | 45.7s |
| skill-flow-ixp-routing-listing/r03 | 41.2s | 1 | 17 | 39.8s |
| skill-flow-ixp-routing-listing/r04 | 45.4s | 1 | 13 | 43.9s |
| skill-flow-ixp-routing-listing/r05 | 51.7s | 1 | 14 | 49.9s |
| skill-flow-ixp-routing-listing/r06 | 52.0s | 1 | 11 | 49.7s |
| skill-flow-ixp-routing-listing/r07 | 48.6s | 1 | 16 | 46.5s |
| skill-flow-ixp-routing-listing/r08 | 63.4s | 1 | 13 | 61.6s |
| skill-flow-ixp-routing-listing/r09 | 50.0s | 1 | 14 | 46.6s |
| skill-flow-ixp-routing-listing/r10 | 52.0s | 1 | 13 | 49.4s |
| skill-flow-slack-weather-pipeline | 636.9s | 1 | 95 | 616.6s |
| skill-flow-hitl-quality-brownfield-insert | 295.3s | 1 | 59 | 288.5s |
| skill-flow-devcon-billing-invoice-lookup | 929.1s | 1 | 167 | 852.9s |
| skill-flow-non-catalog-http-fallback | 278.6s | 1 | 79 | 277.1s |
| skill-flow-ipe-enhanced-enum | 406.9s | 1 | 89 | 405.0s |
| skill-flow-ixp-integration-handle-routing | 690.2s | 1 | 104 | 685.1s |
| skill-flow-calculator | 155.4s | 1 | 44 | 135.3s |
| skill-flow-eval-inline-agent | 348.1s | 1 | 101 | 344.1s |
| skill-flow-scheduled-trigger | 130.6s | 1 | 29 | 122.6s |
| skill-flow-api-workflow | 241.5s | 1 | 53 | 214.3s |
| skill-flow-coded-agent | 814.8s | 1 | 201 | 788.6s |
| skill-flow-feet-inches | 457.2s | 1 | 78 | 425.6s |
| skill-flow-ixp-e2e-project-selection/aviation | 771.4s | 1 | 92 | 766.9s |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 658.2s | 1 | 107 | 652.5s |
| skill-flow-bindings-no-duplicates | 591.7s | 1 | 104 | 588.8s |
| skill-flow-file-attachment-debug | 139.7s | 1 | 46 | 133.5s |
| skill-flow-delay | 164.7s | 1 | 49 | 158.1s |
| skill-flow-multi-city-weather | 625.9s | 1 | 75 | 571.5s |
| skill-flow-decision | 166.7s | 1 | 31 | 137.0s |
| skill-flow-ipe-jira-get-issue | 421.5s | 1 | 75 | 391.1s |
| skill-flow-ipe-jira-create-issue | 284.3s | 1 | 70 | 257.3s |
| skill-flow-eval-local-crud | 110.9s | 1 | 29 | 108.9s |
| skill-flow-init-validate | 35.6s | 1 | 10 | 33.7s |
| skill-flow-devcon-billing-dispute-resolution | 1834.5s | 1 | 261 | 1727.7s |
| skill-flow-ipe-dtl-load-by-default-false | 710.4s | 1 | 74 | 708.5s |
| skill-flow-expense-approval-simulated | 505.7s | 2 | 56 | 244.7s |
| skill-flow-e2e-escalation-orchestrator-paths | 913.2s | 1 | 148 | 769.8s |
| skill-flow-hitl-quality-result-downstream | 295.4s | 1 | 43 | 290.6s |
| skill-flow-customer-escalation-simulated | 905.5s | 3 | 145 | 287.4s |
| skill-flow-ixp-scaffold-minimal | 347.2s | 1 | 77 | 340.4s |
| skill-flow-hitl-quality-boolean-decision | 337.0s | 1 | 61 | 329.1s |
| skill-flow-subflow | 188.4s | 1 | 38 | 169.9s |
| skill-flow-e2e-escalation-slack-alert | 461.1s | 1 | 94 | 435.5s |
| skill-flow-bellevue-weather | 313.9s | 1 | 62 | 290.9s |
| skill-flow-hitl-smoke-node-placed | 500.3s | 1 | 54 | 494.4s |
| skill-flow-eval-evaluator-type-choice | 85.3s | 1 | 29 | 83.7s |
| skill-flow-merge-parallel-sync | 84.7s | 1 | 27 | 79.3s |
| skill-flow-hitl-quality-schema-design | 486.3s | 1 | 62 | 481.3s |
| skill-flow-ipe-path-params | 207.1s | 1 | 60 | 204.2s |
| skill-flow-switch | 286.9s | 1 | 59 | 264.5s |
| skill-flow-remove-node | 371.2s | 1 | 76 | 350.0s |
| skill-flow-outlook-trigger-inbox | 239.5s | 1 | 69 | 231.2s |
| skill-flow-interactive-customer-escalation-triage | 288.8s | 2 | 32 | 115.7s |
| skill-flow-outlook-waitfor-email | 210.7s | 1 | 54 | 205.0s |
| skill-flow-solution-select-ask | 84.0s | 5 | 16 | 11.2s |
| skill-flow-hitl-schema-design-simulated | 525.6s | 3 | 56 | 161.0s |
| skill-flow-reading-list | 287.4s | 1 | 52 | 268.4s |
| skill-flow-e2e-escalation-jira-ticket | 715.1s | 1 | 111 | 682.8s |
| skill-flow-ipe-multiselect | 156.8s | 1 | 49 | 155.1s |
| skill-flow-registry-discovery | 67.1s | 1 | 17 | 65.5s |
| skill-flow-ipe-enum | 692.0s | 1 | 109 | 687.5s |
| skill-flow-bindings-idempotent-reconfigure | 301.6s | 1 | 83 | 298.4s |
| skill-flow-ixp-scaffold-multinode | 902.2s | 1 | 87 | 900.1s |
| skill-flow-hitl-smoke-multi-outcome-routing | 444.9s | 1 | 65 | 436.7s |
| skill-flow-jdbc-databricks-query | 298.3s | 1 | 61 | 293.0s |
| skill-flow-transform-group-by | 139.6s | 1 | 32 | 131.1s |
| skill-flow-ipe-generate-schema | 260.3s | 1 | 80 | 257.9s |
| skill-flow-ipe-complex-array | 163.1s | 1 | 43 | 160.6s |
| skill-flow-bindings-multi-connector-independence | 371.4s | 1 | 92 | 368.6s |
| skill-flow-trigger-with-filter | 51.7s | 1 | 11 | 50.1s |
| skill-flow-add-node | 127.4s | 1 | 26 | 103.2s |
| skill-flow-ipe-required-groups | 319.5s | 1 | 58 | 318.0s |
| skill-flow-e2e-devcon-expense-approval | 564.8s | 1 | 90 | 557.5s |
| skill-flow-slack-http-fallback | 301.1s | 1 | 68 | 278.7s |
| skill-flow-ipe-jira-lifecycle | 902.2s | 1 | 93 | 900.1s |
| skill-flow-transform-filter | 152.6s | 1 | 34 | 147.2s |
| skill-flow-ipe-drive-to-slack | 398.6s | 1 | 82 | 396.6s |
| skill-flow-move-node | 529.5s | 1 | 81 | 519.5s |
| skill-flow-devcon-billing-discrepancy-detector | 1092.1s | 1 | 149 | 1054.6s |
| skill-flow-customer-escalation | 751.0s | 1 | 153 | 744.5s |
| skill-flow-wiki-pageviews | 903.1s | 1 | 56 | 900.2s |


## Token Usage

**Total Tokens**: 488,397,358 (input: 143,934, output: 3,302,066)
**Cache Tokens**: write: 14,722,977, read: 470,228,381
**Agent Cost**: $246.2425
**Eval Overhead (judge + simulator)**: $0.1083
**Total Cost**: $246.3507 (floor — 2 task(s) have spend missing from this total)
**Avg Tokens/Task**: 3,845,648

| Task ID | Input (uncached) | Output | Cache Write | Cache Read | Total | Cost |
|---------|------------------|--------|-------------|------------|-------|------|
| skill-flow-paginated-reference-lookup | 568 | 8,228 | 112,207 | 2,021,925 | 2,142,928 | $1.1525 |
| skill-flow-summarize | 987 | 6,334 | 69,423 | 812,539 | 889,283 | $0.6021 |
| skill-flow-slack-channel-description-simulated | 4,335 | 17,283 | 161,690 | 2,545,190 | 2,728,498 | $1.6468 |
| skill-flow-loop-multiply | 557 | 32,327 | 119,388 | 5,456,863 | 5,609,135 | $2.5713 |
| skill-flow-ipe-searchable-joins | 532 | 34,632 | 139,801 | 2,067,318 | 2,242,283 | $1.6655 |
| skill-flow-bellevue-weather-simulated | 744 | 24,178 | 131,176 | 3,120,012 | 3,276,110 | $1.8047 |
| skill-flow-lowcode-agent | 524 | 15,485 | 86,414 | 905,965 | 1,008,388 | $0.8297 |
| skill-flow-bindings-reconfigure-different-connection | 872 | 15,996 | 105,364 | 2,960,283 | 3,082,515 | $1.5258 |
| skill-flow-ixp-invoice-extraction-simulated | 1,046 | 107,323 | 364,256 | 8,645,227 | 9,117,852 | $5.5852 |
| skill-flow-group-to-subflow | 60 | 67,453 | 78,577 | 2,928,303 | 3,074,393 | $2.1851 |
| skill-flow-eval-simulation-crud | 975 | 4,342 | 40,492 | 906,834 | 952,643 | $0.4920 |
| skill-flow-cli-dice-roller-simulated | 668 | 12,039 | 89,717 | 1,447,361 | 1,549,785 | $0.9637 |
| skill-flow-batch-transform | 941 | 11,638 | 74,328 | 1,753,934 | 1,840,841 | $0.9823 |
| skill-flow-inline-agent-robust | 683 | 20,666 | 109,940 | 4,222,846 | 4,354,135 | $1.9912 |
| skill-flow-add-output | 486 | 3,942 | 50,291 | 876,464 | 931,183 | $0.5121 |
| skill-flow-dice-roller | 486 | 6,121 | 77,701 | 809,366 | 893,674 | $0.6275 |
| skill-flow-slack-channel-description | 516 | 11,046 | 161,913 | 2,564,596 | 2,738,071 | $1.5438 |
| skill-flow-rpa | 520 | 12,504 | 109,140 | 2,223,563 | 2,345,727 | $1.2655 |
| skill-flow-generic-dynamic-node | 9,768 | 13,755 | 108,528 | 3,504,146 | 3,636,197 | $1.6939 |
| skill-flow-ipe-dtl-load-by-default-true | 638 | 22,467 | 147,187 | 4,372,931 | 4,543,223 | $2.2027 |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 188 | 46,010 | 482,665 | 12,991,436 | 13,520,299 | $6.3981 |
| skill-flow-webhook-waitfor-parallel | 668 | 12,825 | 114,201 | 2,618,871 | 2,746,565 | $1.4083 |
| skill-flow-ipe-jira-search-triage | 678 | 33,307 | 154,685 | 5,830,325 | 6,018,995 | $2.8308 |
| skill-flow-ixp-routing/explicit | 62 | 73,469 | 181,798 | 5,011,571 | 5,266,900 | $3.2874 |
| skill-flow-ixp-routing/invoice-extraction | 712 | 54,360 | 190,059 | 10,883,863 | 11,128,994 | $4.7954 |
| skill-flow-ixp-routing/receipts | 671 | 53,524 | 98,977 | 4,830,628 | 4,983,800 | $2.6252 |
| skill-flow-ixp-routing/contracts | 709 | 53,270 | 191,009 | 10,727,676 | 10,972,664 | $4.7358 |
| skill-flow-ixp-routing/forms-classify | 618 | 15,937 | 122,270 | 2,106,393 | 2,245,218 | $1.3313 |
| skill-flow-terminate | 557 | 15,932 | 118,395 | 2,186,828 | 2,321,712 | $1.3407 |
| skill-flow-devcon-billing-resolution-writer | 707 | 23,646 | 155,069 | 6,322,669 | 6,502,091 | $2.8351 |
| skill-flow-ipe-query-params | 539 | 8,707 | 93,898 | 1,385,444 | 1,488,588 | $0.9000 |
| skill-flow-devcon-billing-dispute-analyst | 786 | 60,578 | 161,850 | 10,017,144 | 10,240,358 | $4.5231 |
| skill-flow-openmeteo-weather | 583 | 10,726 | 125,673 | 2,842,527 | 2,979,509 | $1.4867 |
| skill-flow-update-node | 495 | 2,955 | 62,283 | 814,290 | 880,023 | $0.5237 |
| skill-flow-ixp-routing-negative/stripe-http | 612 | 14,668 | 90,113 | 1,379,705 | 1,485,098 | $0.9737 |
| skill-flow-ixp-routing-negative/slack-summary | 599 | 11,989 | 127,740 | 1,500,033 | 1,640,361 | $1.1107 |
| skill-flow-ixp-routing-negative/sf-update | 623 | 12,025 | 88,763 | 2,349,254 | 2,450,665 | $1.2199 |
| skill-flow-ixp-routing-negative/http-webhook | 12,751 | 20,492 | 124,144 | 2,675,606 | 2,832,993 | $1.6139 |
| skill-flow-ixp-routing-negative/gsheet-loop | 615 | 12,362 | 114,629 | 2,447,170 | 2,574,776 | $1.3513 |
| skill-flow-ixp-routing-negative/queue-write | 622 | 11,319 | 67,005 | 2,176,030 | 2,254,976 | $1.0757 |
| skill-flow-ixp-routing-negative/teams-decision | 604 | 17,523 | 123,854 | 1,760,171 | 1,902,152 | $1.2572 |
| skill-flow-ixp-routing-negative/delay-email | 622 | 20,263 | 84,202 | 2,155,700 | 2,260,787 | $1.2683 |
| skill-flow-eval-no-auto-upload | 918 | 4,246 | 31,785 | 1,159,995 | 1,196,944 | $0.5336 |
| skill-flow-transform-map | 880 | 10,312 | 80,906 | 1,541,957 | 1,634,055 | $0.9233 |
| skill-flow-ipe-ceql-where | 613 | 29,900 | 138,102 | 4,571,515 | 4,740,130 | $2.3397 |
| skill-flow-hitl-smoke-completed-port | 557 | 34,678 | 112,951 | 2,173,628 | 2,321,814 | $1.5975 |
| skill-flow-ixp-routing-listing/r01 | 456 | 2,505 | 35,865 | 338,738 | 377,564 | $0.2751 |
| skill-flow-ixp-routing-listing/r02 | 457 | 1,958 | 45,895 | 455,056 | 503,366 | $0.3394 |
| skill-flow-ixp-routing-listing/r03 | 459 | 1,861 | 22,656 | 373,620 | 398,596 | $0.2263 |
| skill-flow-ixp-routing-listing/r04 | 461 | 2,603 | 36,020 | 339,080 | 378,164 | $0.2772 |
| skill-flow-ixp-routing-listing/r05 | 458 | 2,227 | 29,590 | 375,028 | 407,303 | $0.2582 |
| skill-flow-ixp-routing-listing/r06 | 460 | 2,632 | 36,258 | 339,592 | 378,942 | $0.2787 |
| skill-flow-ixp-routing-listing/r07 | 456 | 2,398 | 21,782 | 370,511 | 395,147 | $0.2302 |
| skill-flow-ixp-routing-listing/r08 | 464 | 2,970 | 29,155 | 461,743 | 494,332 | $0.2938 |
| skill-flow-ixp-routing-listing/r09 | 463 | 1,686 | 35,649 | 468,470 | 506,268 | $0.3009 |
| skill-flow-ixp-routing-listing/r10 | 459 | 2,729 | 35,713 | 413,114 | 452,015 | $0.3002 |
| skill-flow-slack-weather-pipeline | 673 | 45,341 | 181,127 | 5,685,962 | 5,913,103 | $3.0671 |
| skill-flow-hitl-quality-brownfield-insert | 5,197 | 21,927 | 88,771 | 2,579,678 | 2,695,573 | $1.4513 |
| skill-flow-devcon-billing-invoice-lookup | 797 | 56,969 | 176,307 | 13,999,307 | 14,233,380 | $5.7179 |
| skill-flow-non-catalog-http-fallback | 582 | 16,903 | 121,975 | 3,292,080 | 3,431,540 | $1.7003 |
| skill-flow-ipe-enhanced-enum | 603 | 33,924 | 140,981 | 4,441,019 | 4,616,527 | $2.3717 |
| skill-flow-ixp-integration-handle-routing | 859 | 55,001 | 170,056 | 6,108,568 | 6,334,484 | $3.2979 |
| skill-flow-calculator | 507 | 8,234 | 95,768 | 2,004,854 | 2,109,363 | $1.0856 |
| skill-flow-eval-inline-agent | 1,130 | 25,969 | 161,955 | 5,801,326 | 5,990,380 | $2.7407 |
| skill-flow-scheduled-trigger | 957 | 7,920 | 51,397 | 946,375 | 1,006,649 | $0.5983 |
| skill-flow-api-workflow | 520 | 13,651 | 111,211 | 2,271,431 | 2,396,813 | $1.3048 |
| skill-flow-coded-agent | 709 | 47,612 | 201,189 | 15,315,847 | 15,565,357 | $6.0655 |
| skill-flow-feet-inches | 637 | 34,518 | 123,087 | 3,623,227 | 3,781,469 | $2.0682 |
| skill-flow-ixp-e2e-project-selection/aviation | 671 | 61,567 | 140,974 | 5,342,587 | 5,545,799 | $3.0569 |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 672 | 49,873 | 137,577 | 6,030,328 | 6,218,450 | $3.0751 |
| skill-flow-bindings-no-duplicates | 600 | 41,972 | 151,709 | 7,286,675 | 7,480,956 | $3.3863 |
| skill-flow-file-attachment-debug | 620 | 7,901 | 87,521 | 1,512,713 | 1,608,755 | $0.9024 |
| skill-flow-delay | 730 | 11,158 | 86,163 | 1,726,272 | 1,824,323 | $1.0106 |
| skill-flow-multi-city-weather | 614 | 45,943 | 143,438 | 4,429,562 | 4,619,557 | $2.5577 |
| skill-flow-decision | 14,603 | 10,718 | 94,384 | 1,095,777 | 1,215,482 | $0.8873 |
| skill-flow-ipe-jira-get-issue | 635 | 29,874 | 167,054 | 4,497,607 | 4,695,170 | $2.4257 |
| skill-flow-ipe-jira-create-issue | 657 | 16,876 | 149,893 | 3,924,204 | 4,091,630 | $1.9945 |
| skill-flow-eval-local-crud | 853 | 7,097 | 37,016 | 781,468 | 826,434 | $0.4823 |
| skill-flow-init-validate | 557 | 1,129 | 17,492 | 307,774 | 326,952 | $0.1765 |
| skill-flow-devcon-billing-dispute-resolution | 2,862 | 130,806 | 308,531 | 30,577,550 | 31,019,749 | $12.3009 |
| skill-flow-ipe-dtl-load-by-default-false | 545 | 30,359 | 126,818 | 4,012,430 | 4,170,152 | $2.1363 |
| skill-flow-expense-approval-simulated | 860 | 41,709 | 117,422 | 2,700,820 | 2,860,811 | $1.8847 |
| skill-flow-e2e-escalation-orchestrator-paths | 1,339 | 62,355 | 189,326 | 10,147,190 | 10,400,210 | $4.6935 |
| skill-flow-hitl-quality-result-downstream | 674 | 24,869 | 115,925 | 1,939,114 | 2,080,582 | $1.3915 |
| skill-flow-customer-escalation-simulated | 1,103 | 63,175 | 229,518 | 10,816,080 | 11,109,876 | $5.0759 |
| skill-flow-ixp-scaffold-minimal | 667 | 24,163 | 131,484 | 3,980,389 | 4,136,703 | $2.0516 |
| skill-flow-hitl-quality-boolean-decision | 684 | 28,987 | 137,396 | 2,208,221 | 2,375,288 | $1.6146 |
| skill-flow-subflow | 529 | 13,726 | 80,840 | 1,399,392 | 1,494,487 | $0.9304 |
| skill-flow-e2e-escalation-slack-alert | 959 | 34,098 | 193,088 | 6,953,378 | 7,181,523 | $3.3244 |
| skill-flow-bellevue-weather | 602 | 21,929 | 104,443 | 3,173,975 | 3,300,949 | $1.6746 |
| skill-flow-hitl-smoke-node-placed | 571 | 44,839 | 115,476 | 2,588,405 | 2,749,291 | $1.8839 |
| skill-flow-eval-evaluator-type-choice | 1,002 | 4,863 | 39,859 | 890,094 | 935,818 | $0.4925 |
| skill-flow-merge-parallel-sync | 1,156 | 4,397 | 49,020 | 838,864 | 893,437 | $0.5049 |
| skill-flow-hitl-quality-schema-design | 649 | 43,562 | 107,519 | 2,543,166 | 2,694,896 | $1.8215 |
| skill-flow-ipe-path-params | 581 | 12,017 | 116,085 | 2,815,142 | 2,943,825 | $1.4619 |
| skill-flow-switch | 582 | 19,743 | 106,358 | 3,134,517 | 3,261,200 | $1.6371 |
| skill-flow-remove-node | 540 | 27,132 | 78,014 | 3,745,311 | 3,850,997 | $1.8247 |
| skill-flow-outlook-trigger-inbox | 14,712 | 14,967 | 122,798 | 3,265,922 | 3,418,399 | $1.7089 |
| skill-flow-interactive-customer-escalation-triage | 1,305 | 19,906 | 91,516 | 1,131,438 | 1,244,165 | $1.0039 |
| skill-flow-outlook-waitfor-email | 578 | 10,872 | 113,083 | 2,704,974 | 2,829,507 | $1.4004 |
| skill-flow-solution-select-ask | 471 | 1,252 | 17,437 | 418,818 | 437,978 | $0.2155 |
| skill-flow-hitl-schema-design-simulated | 991 | 43,270 | 128,885 | 2,272,716 | 2,445,862 | $1.8374 |
| skill-flow-reading-list | 1,012 | 22,234 | 102,253 | 2,649,908 | 2,775,407 | $1.5150 |
| skill-flow-e2e-escalation-jira-ticket | 961 | 48,792 | 155,243 | 8,237,253 | 8,442,249 | $3.7881 |
| skill-flow-ipe-multiselect | 488 | 9,817 | 74,398 | 1,534,962 | 1,619,665 | $0.8882 |
| skill-flow-registry-discovery | 578 | 3,193 | 27,500 | 427,832 | 459,103 | $0.2811 |
| skill-flow-ipe-enum | 631 | 55,949 | 145,471 | 5,334,313 | 5,536,364 | $2.9869 |
| skill-flow-bindings-idempotent-reconfigure | 658 | 20,807 | 59,278 | 2,921,975 | 3,002,718 | $1.4130 |
| skill-flow-ixp-scaffold-multinode | 78 | 65,841 | 133,083 | 4,802,230 | 5,001,232 | $2.9276 |
| skill-flow-hitl-smoke-multi-outcome-routing | 2,645 | 38,425 | 128,305 | 3,044,430 | 3,213,805 | $1.9788 |
| skill-flow-jdbc-databricks-query | 638 | 14,149 | 133,818 | 2,886,405 | 3,035,010 | $1.5819 |
| skill-flow-transform-group-by | 907 | 9,499 | 82,145 | 1,203,381 | 1,295,932 | $0.8143 |
| skill-flow-ipe-generate-schema | 579 | 14,620 | 134,607 | 4,597,884 | 4,747,690 | $2.1052 |
| skill-flow-ipe-complex-array | 503 | 10,161 | 109,788 | 1,958,400 | 2,078,852 | $1.1531 |
| skill-flow-bindings-multi-connector-independence | 631 | 24,094 | 117,386 | 5,577,242 | 5,719,353 | $2.4767 |
| skill-flow-trigger-with-filter | 537 | 3,990 | 61,314 | 322,453 | 388,294 | $0.3881 |
| skill-flow-add-node | 507 | 8,236 | 69,123 | 836,307 | 914,173 | $0.6352 |
| skill-flow-ipe-required-groups | 498 | 23,953 | 121,654 | 2,561,214 | 2,707,319 | $1.5854 |
| skill-flow-e2e-devcon-expense-approval | 738 | 49,973 | 117,781 | 4,251,689 | 4,420,181 | $2.4690 |
| skill-flow-slack-http-fallback | 582 | 12,610 | 141,456 | 3,379,660 | 3,534,308 | $1.7353 |
| skill-flow-ipe-jira-lifecycle | 72 | 74,637 | 189,334 | 5,681,476 | 5,945,519 | $3.5342 |
| skill-flow-transform-filter | 865 | 10,671 | 76,986 | 1,187,511 | 1,276,033 | $0.8076 |
| skill-flow-ipe-drive-to-slack | 649 | 22,883 | 153,324 | 5,052,192 | 5,229,048 | $2.4358 |
| skill-flow-move-node | 583 | 41,447 | 82,518 | 3,949,660 | 4,074,208 | $2.1178 |
| skill-flow-devcon-billing-discrepancy-detector | 979 | 77,411 | 219,979 | 13,491,786 | 13,790,155 | $6.0366 |
| skill-flow-customer-escalation | 736 | 53,897 | 184,679 | 11,661,267 | 11,900,579 | $5.0016 |
| skill-flow-wiki-pageviews | 46 | 73,353 | 140,526 | 2,873,357 | 3,087,282 | $2.4894 |


## Command Telemetry

**Total Commands**: 4719
**Success Rate**: 4606/4719 (97.6%)

### Commands by Tool

| Tool | Count | % |
|------|-------|---|
| Bash | 3057 | 64.8% |
| Read | 951 | 20.2% |
| Edit | 225 | 4.8% |
| Skill | 127 | 2.7% |
| TaskUpdate | 115 | 2.4% |
| Grep | 104 | 2.2% |
| TaskCreate | 71 | 1.5% |
| Write | 50 | 1.1% |
| Glob | 14 | 0.3% |
| Agent | 2 | 0.0% |
| SendMessage | 1 | 0.0% |
| Grag | 1 | 0.0% |
| TaskOutput | 1 | 0.0% |

### Performance

- **Average Command Time**: 1662.2ms
- **Total Command Time**: 7843.86s

### Slowest Commands

| Tool | Duration | Parameters |
|------|----------|------------|
| Agent | 611773ms | {'description': 'Search skill docs for octet-strea... |
| TaskOutput | 179306ms | {'task_id': 'bg2y9leat', 'block': True, 'timeout':... |
| Bash | 120943ms | {'command': 'uip is connections list "uipath-micro... |
| Bash | 120724ms | {'command': 'uip maestro flow registry get uipath.... |
| Bash | 120429ms | {'command': 'cd /work/output/artifacts/skill-flow-... |

**Most Common Pattern**: `Bash → Bash → Bash`

**Skill Tool Invoked**: 127 time(s)

## Agent Settings

- **Permission Mode**: acceptEdits
- **Allowed Tools**: Skill, Bash, Read, Write, Edit, Glob, Grep
- **Model**: us.anthropic.claude-sonnet-5
- **Max Turns**: 80
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