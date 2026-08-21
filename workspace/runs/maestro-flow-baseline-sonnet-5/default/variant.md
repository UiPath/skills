# Variant Report: default

**Experiment**: skill-tests-smoke
**Description**: Linux PR-gate smoke tests — docker isolation, fast turn budget

## Summary

- **Tasks Run**: 127
- **Succeeded**: 115
- **Failed**: 10
- **Errors**: 2
- **Pass Rate**: 90.6% (115/127)
- **Average Score**: 0.935
- **Average Duration**: 325.2s
- **Total Tokens**: 418,032,039
- **Score Stddev**: 0.202
- **Duration Stddev**: 244.0s

## Task Details

| Task | Score | Status | Avg Duration |
|------|-------|--------|--------------|
| skill-flow-devcon-billing-resolution-writer | 1.000 | SUCCESS | 403.2s |
| skill-flow-hitl-quality-brownfield-insert | 1.000 | SUCCESS | 309.6s |
| skill-flow-file-attachment-debug | 1.000 | SUCCESS | 333.5s |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 1.000 | SUCCESS | 875.9s |
| skill-flow-init-validate | 1.000 | SUCCESS | 66.8s |
| skill-flow-jdbc-databricks-query | 1.000 | SUCCESS | 448.5s |
| skill-flow-reading-list | 1.000 | SUCCESS | 386.9s |
| skill-flow-ixp-routing-negative/stripe-http | 1.000 | SUCCESS | 223.1s |
| skill-flow-ixp-routing-negative/slack-summary | 1.000 | SUCCESS | 262.7s |
| skill-flow-ixp-routing-negative/sf-update | 1.000 | SUCCESS | 241.8s |
| skill-flow-ixp-routing-negative/http-webhook | 1.000 | SUCCESS | 289.3s |
| skill-flow-ixp-routing-negative/gsheet-loop | 1.000 | SUCCESS | 272.4s |
| skill-flow-ixp-routing-negative/queue-write | 1.000 | SUCCESS | 313.0s |
| skill-flow-ixp-routing-negative/teams-decision | 1.000 | SUCCESS | 256.8s |
| skill-flow-ixp-routing-negative/delay-email | 1.000 | SUCCESS | 309.6s |
| skill-flow-transform-group-by | 1.000 | SUCCESS | 200.2s |
| skill-flow-customer-escalation | 0.333 | FAILURE | 686.1s |
| skill-flow-terminate | 1.000 | SUCCESS | 294.8s |
| skill-flow-bindings-no-duplicates | 1.000 | SUCCESS | 491.8s |
| skill-flow-eval-simulation-crud | 1.000 | SUCCESS | 153.1s |
| skill-flow-ixp-routing-listing/r01 | 1.000 | SUCCESS | 61.6s |
| skill-flow-ixp-routing-listing/r02 | 1.000 | SUCCESS | 57.3s |
| skill-flow-ixp-routing-listing/r03 | 1.000 | SUCCESS | 75.2s |
| skill-flow-ixp-routing-listing/r04 | 1.000 | SUCCESS | 65.1s |
| skill-flow-ixp-routing-listing/r05 | 1.000 | SUCCESS | 57.1s |
| skill-flow-ixp-routing-listing/r06 | 1.000 | SUCCESS | 70.4s |
| skill-flow-ixp-routing-listing/r07 | 0.500 | FAILURE | 37.6s |
| skill-flow-ixp-routing-listing/r08 | 1.000 | SUCCESS | 51.8s |
| skill-flow-ixp-routing-listing/r09 | 1.000 | SUCCESS | 68.0s |
| skill-flow-ixp-routing-listing/r10 | 1.000 | SUCCESS | 106.0s |
| skill-flow-ipe-drive-to-slack | 1.000 | SUCCESS | 451.0s |
| skill-flow-ipe-required-groups | 1.000 | SUCCESS | 615.0s |
| skill-flow-ipe-enhanced-enum | 1.000 | SUCCESS | 422.3s |
| skill-flow-bindings-idempotent-reconfigure | 1.000 | SUCCESS | 423.6s |
| skill-flow-slack-http-fallback | 1.000 | SUCCESS | 393.6s |
| skill-flow-hitl-quality-boolean-decision | 1.000 | SUCCESS | 256.0s |
| skill-flow-bindings-multi-connector-independence | 1.000 | SUCCESS | 387.5s |
| skill-flow-rpa | 1.000 | SUCCESS | 370.6s |
| skill-flow-ipe-dtl-load-by-default-true | 0.375 | FAILURE | 483.5s |
| skill-flow-lowcode-agent | 1.000 | SUCCESS | 225.2s |
| skill-flow-webhook-waitfor-parallel | 1.000 | SUCCESS | 259.1s |
| skill-flow-hitl-schema-design-simulated | 1.000 | SUCCESS | 666.1s |
| skill-flow-registry-discovery | 1.000 | SUCCESS | 77.6s |
| skill-flow-add-node | 1.000 | SUCCESS | 106.0s |
| skill-flow-multi-city-weather | 1.000 | SUCCESS | 403.3s |
| skill-flow-bellevue-weather-simulated | 0.889 | SUCCESS | 552.3s |
| skill-flow-ixp-invoice-extraction-simulated | 0.000 | ERROR | 0.0s |
| skill-flow-api-workflow | 0.375 | MAX_TURNS_EXHAUSTED | 429.2s |
| skill-flow-loop-multiply | 0.625 | MAX_TURNS_EXHAUSTED | 486.1s |
| skill-flow-devcon-billing-dispute-analyst | 1.000 | SUCCESS | 392.1s |
| skill-flow-eval-inline-agent | 1.000 | SUCCESS | 314.8s |
| skill-flow-ipe-complex-array | 0.875 | SUCCESS | 191.4s |
| skill-flow-e2e-escalation-slack-alert | 1.000 | SUCCESS | 519.7s |
| skill-flow-expense-approval-simulated | 1.000 | SUCCESS | 379.5s |
| skill-flow-transform-map | 1.000 | SUCCESS | 142.2s |
| skill-flow-wiki-pageviews | 1.000 | SUCCESS | 493.2s |
| skill-flow-paginated-reference-lookup | 1.000 | SUCCESS | 224.6s |
| skill-flow-eval-evaluator-type-choice | 1.000 | SUCCESS | 136.4s |
| skill-flow-outlook-waitfor-email | 1.000 | SUCCESS | 173.3s |
| skill-flow-switch | 1.000 | SUCCESS | 226.9s |
| skill-flow-cli-dice-roller-simulated | 1.000 | SUCCESS | 255.3s |
| skill-flow-ipe-multiselect | 0.231 | FAILURE | 287.6s |
| skill-flow-decision | 1.000 | SUCCESS | 182.1s |
| skill-flow-ipe-ceql-where | 1.000 | SUCCESS | 520.6s |
| skill-flow-remove-node | 1.000 | SUCCESS | 189.0s |
| skill-flow-transform-filter | 1.000 | SUCCESS | 181.1s |
| skill-flow-ixp-scaffold-multinode | 0.276 | MAX_TURNS_EXHAUSTED | 343.9s |
| skill-flow-outlook-trigger-inbox | 1.000 | SUCCESS | 217.0s |
| skill-flow-scheduled-trigger | 1.000 | SUCCESS | 150.1s |
| skill-flow-ixp-e2e-project-selection/aviation | 1.000 | SUCCESS | 414.9s |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 1.000 | SUCCESS | 527.0s |
| skill-flow-slack-channel-description | 1.000 | SUCCESS | 348.7s |
| skill-flow-ipe-path-params | 1.000 | SUCCESS | 242.1s |
| skill-flow-dice-roller | 1.000 | SUCCESS | 102.0s |
| skill-flow-openmeteo-weather | 1.000 | SUCCESS | 180.1s |
| skill-flow-eval-no-auto-upload | 1.000 | SUCCESS | 98.6s |
| skill-flow-ipe-generate-schema | 1.000 | SUCCESS | 192.2s |
| skill-flow-eval-local-crud | 1.000 | SUCCESS | 92.6s |
| skill-flow-interactive-customer-escalation-triage | 1.000 | SUCCESS | 600.6s |
| skill-flow-ixp-routing/explicit | 1.000 | SUCCESS | 770.8s |
| skill-flow-ixp-routing/invoice-extraction | 0.000 | ERROR | 0.0s |
| skill-flow-ixp-routing/receipts | 1.000 | SUCCESS | 445.8s |
| skill-flow-ixp-routing/contracts | 1.000 | SUCCESS | 400.8s |
| skill-flow-ixp-routing/forms-classify | 1.000 | SUCCESS | 219.9s |
| skill-flow-hitl-quality-result-downstream | 1.000 | SUCCESS | 321.3s |
| skill-flow-slack-weather-pipeline | 0.375 | MAX_TURNS_EXHAUSTED | 674.7s |
| skill-flow-hitl-smoke-node-placed | 1.000 | SUCCESS | 359.6s |
| skill-flow-ixp-integration-handle-routing | 1.000 | SUCCESS | 626.5s |
| skill-flow-e2e-escalation-orchestrator-paths | 1.000 | SUCCESS | 549.3s |
| skill-flow-trigger-with-filter | 1.000 | SUCCESS | 69.3s |
| skill-flow-ipe-jira-search-triage | 1.000 | SUCCESS | 414.3s |
| skill-flow-non-catalog-http-fallback | 1.000 | SUCCESS | 162.8s |
| skill-flow-hitl-quality-schema-design | 1.000 | SUCCESS | 302.9s |
| skill-flow-ipe-enum | 1.000 | SUCCESS | 365.5s |
| skill-flow-update-node | 1.000 | SUCCESS | 68.3s |
| skill-flow-devcon-billing-discrepancy-detector | 1.000 | SUCCESS | 579.0s |
| skill-flow-solution-select-ask | 1.000 | SUCCESS | 91.9s |
| skill-flow-add-output | 1.000 | SUCCESS | 70.9s |
| skill-flow-ipe-jira-get-issue | 1.000 | SUCCESS | 309.3s |
| skill-flow-merge-parallel-sync | 1.000 | SUCCESS | 159.7s |
| skill-flow-devcon-billing-dispute-resolution | 1.000 | SUCCESS | 2052.0s |
| skill-flow-ipe-dtl-load-by-default-false | 1.000 | SUCCESS | 502.1s |
| skill-flow-batch-transform | 1.000 | SUCCESS | 150.4s |
| skill-flow-coded-agent | 0.375 | FAILURE | 812.3s |
| skill-flow-hitl-smoke-multi-outcome-routing | 1.000 | SUCCESS | 379.2s |
| skill-flow-delay | 1.000 | SUCCESS | 103.5s |
| skill-flow-slack-channel-description-simulated | 1.000 | SUCCESS | 250.9s |
| skill-flow-summarize | 1.000 | SUCCESS | 131.6s |
| skill-flow-ipe-jira-lifecycle | 1.000 | SUCCESS | 660.6s |
| skill-flow-bindings-reconfigure-different-connection | 1.000 | SUCCESS | 578.6s |
| skill-flow-calculator | 1.000 | SUCCESS | 146.0s |
| skill-flow-group-to-subflow | 1.000 | SUCCESS | 495.9s |
| skill-flow-ipe-searchable-joins | 1.000 | SUCCESS | 508.4s |
| skill-flow-bellevue-weather | 1.000 | SUCCESS | 315.9s |
| skill-flow-ipe-query-params | 1.000 | SUCCESS | 215.4s |
| skill-flow-feet-inches | 1.000 | SUCCESS | 232.9s |
| skill-flow-inline-agent-robust | 1.000 | SUCCESS | 280.4s |
| skill-flow-customer-escalation-simulated | 0.938 | SUCCESS | 625.6s |
| skill-flow-e2e-devcon-expense-approval | 1.000 | SUCCESS | 519.3s |
| skill-flow-hitl-smoke-completed-port | 1.000 | SUCCESS | 252.7s |
| skill-flow-subflow | 1.000 | SUCCESS | 174.1s |
| skill-flow-ipe-jira-create-issue | 1.000 | SUCCESS | 255.9s |
| skill-flow-devcon-billing-invoice-lookup | 0.909 | SUCCESS | 550.8s |
| skill-flow-generic-dynamic-node | 1.000 | SUCCESS | 232.7s |
| skill-flow-move-node | 1.000 | SUCCESS | 501.1s |
| skill-flow-ixp-scaffold-minimal | 1.000 | SUCCESS | 217.9s |
| skill-flow-e2e-escalation-jira-ticket | 0.684 | FAILURE | 396.8s |


## Generation Metrics

| Task ID | Total Latency | Turns | Asst Turns | Avg Turn Latency |
|---------|---------------|-------|------------|------------------|
| skill-flow-devcon-billing-resolution-writer | 403.2s | 1 | 73 | 350.6s |
| skill-flow-hitl-quality-brownfield-insert | 309.6s | 1 | 49 | 290.2s |
| skill-flow-file-attachment-debug | 333.5s | 1 | 36 | 303.2s |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 875.9s | 1 | 167 | 858.4s |
| skill-flow-init-validate | 66.8s | 1 | 14 | 55.2s |
| skill-flow-jdbc-databricks-query | 448.5s | 1 | 70 | 437.5s |
| skill-flow-reading-list | 386.9s | 1 | 43 | 346.1s |
| skill-flow-ixp-routing-negative/stripe-http | 223.1s | 1 | 33 | 212.4s |
| skill-flow-ixp-routing-negative/slack-summary | 262.7s | 1 | 49 | 251.7s |
| skill-flow-ixp-routing-negative/sf-update | 241.8s | 1 | 43 | 229.5s |
| skill-flow-ixp-routing-negative/http-webhook | 289.3s | 1 | 57 | 276.7s |
| skill-flow-ixp-routing-negative/gsheet-loop | 272.4s | 1 | 46 | 261.2s |
| skill-flow-ixp-routing-negative/queue-write | 313.0s | 1 | 56 | 302.0s |
| skill-flow-ixp-routing-negative/teams-decision | 256.8s | 1 | 40 | 246.7s |
| skill-flow-ixp-routing-negative/delay-email | 309.6s | 1 | 52 | 297.9s |
| skill-flow-transform-group-by | 200.2s | 1 | 30 | 185.3s |
| skill-flow-customer-escalation | 686.1s | 1 | 110 | 671.1s |
| skill-flow-terminate | 294.8s | 1 | 47 | 267.1s |
| skill-flow-bindings-no-duplicates | 491.8s | 1 | 95 | 480.4s |
| skill-flow-eval-simulation-crud | 153.1s | 1 | 36 | 140.8s |
| skill-flow-ixp-routing-listing/r01 | 61.6s | 1 | 13 | 50.8s |
| skill-flow-ixp-routing-listing/r02 | 57.3s | 1 | 11 | 47.6s |
| skill-flow-ixp-routing-listing/r03 | 75.2s | 1 | 14 | 64.4s |
| skill-flow-ixp-routing-listing/r04 | 65.1s | 1 | 12 | 54.9s |
| skill-flow-ixp-routing-listing/r05 | 57.1s | 1 | 13 | 47.1s |
| skill-flow-ixp-routing-listing/r06 | 70.4s | 1 | 14 | 58.5s |
| skill-flow-ixp-routing-listing/r07 | 37.6s | 1 | 8 | 25.4s |
| skill-flow-ixp-routing-listing/r08 | 51.8s | 1 | 6 | 40.6s |
| skill-flow-ixp-routing-listing/r09 | 68.0s | 1 | 12 | 55.5s |
| skill-flow-ixp-routing-listing/r10 | 106.0s | 1 | 17 | 93.6s |
| skill-flow-ipe-drive-to-slack | 451.0s | 1 | 68 | 439.2s |
| skill-flow-ipe-required-groups | 615.0s | 1 | 74 | 602.5s |
| skill-flow-ipe-enhanced-enum | 422.3s | 1 | 50 | 410.5s |
| skill-flow-bindings-idempotent-reconfigure | 423.6s | 1 | 62 | 406.8s |
| skill-flow-slack-http-fallback | 393.6s | 1 | 78 | 350.7s |
| skill-flow-hitl-quality-boolean-decision | 256.0s | 1 | 46 | 241.2s |
| skill-flow-bindings-multi-connector-independence | 387.5s | 1 | 82 | 374.6s |
| skill-flow-rpa | 370.6s | 1 | 71 | 298.4s |
| skill-flow-ipe-dtl-load-by-default-true | 483.5s | 1 | 114 | 473.6s |
| skill-flow-lowcode-agent | 225.2s | 1 | 38 | 177.6s |
| skill-flow-webhook-waitfor-parallel | 259.1s | 1 | 72 | 247.8s |
| skill-flow-hitl-schema-design-simulated | 666.1s | 3 | 55 | 200.9s |
| skill-flow-registry-discovery | 77.6s | 1 | 11 | 66.5s |
| skill-flow-add-node | 106.0s | 1 | 19 | 74.7s |
| skill-flow-multi-city-weather | 403.3s | 1 | 39 | 339.7s |
| skill-flow-bellevue-weather-simulated | 552.3s | 4 | 127 | 121.0s |
| skill-flow-ixp-invoice-extraction-simulated | 1348.4s | 4 | 141 | 327.2s |
| skill-flow-api-workflow | 429.2s | 1 | 75 | 398.4s |
| skill-flow-loop-multiply | 486.1s | 1 | 125 | 453.5s |
| skill-flow-devcon-billing-dispute-analyst | 392.1s | 1 | 85 | 340.1s |
| skill-flow-eval-inline-agent | 314.8s | 1 | 83 | 309.7s |
| skill-flow-ipe-complex-array | 191.4s | 1 | 48 | 186.6s |
| skill-flow-e2e-escalation-slack-alert | 519.7s | 1 | 92 | 491.6s |
| skill-flow-expense-approval-simulated | 379.5s | 3 | 44 | 115.6s |
| skill-flow-transform-map | 142.2s | 1 | 30 | 130.8s |
| skill-flow-wiki-pageviews | 493.2s | 1 | 50 | 436.3s |
| skill-flow-paginated-reference-lookup | 224.6s | 1 | 58 | 220.7s |
| skill-flow-eval-evaluator-type-choice | 136.4s | 1 | 32 | 132.4s |
| skill-flow-outlook-waitfor-email | 173.3s | 1 | 44 | 165.4s |
| skill-flow-switch | 226.9s | 1 | 37 | 206.5s |
| skill-flow-cli-dice-roller-simulated | 255.3s | 4 | 47 | 52.1s |
| skill-flow-ipe-multiselect | 287.6s | 1 | 69 | 283.8s |
| skill-flow-decision | 182.1s | 1 | 32 | 147.1s |
| skill-flow-ipe-ceql-where | 520.6s | 1 | 108 | 516.7s |
| skill-flow-remove-node | 189.0s | 1 | 31 | 157.8s |
| skill-flow-transform-filter | 181.1s | 1 | 33 | 170.5s |
| skill-flow-ixp-scaffold-multinode | 343.9s | 1 | 98 | 337.7s |
| skill-flow-outlook-trigger-inbox | 217.0s | 1 | 58 | 202.3s |
| skill-flow-scheduled-trigger | 150.1s | 1 | 33 | 143.0s |
| skill-flow-ixp-e2e-project-selection/aviation | 414.9s | 1 | 85 | 408.8s |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 527.0s | 1 | 93 | 519.1s |
| skill-flow-slack-channel-description | 348.7s | 1 | 76 | 319.3s |
| skill-flow-ipe-path-params | 242.1s | 1 | 56 | 236.2s |
| skill-flow-dice-roller | 102.0s | 1 | 24 | 83.6s |
| skill-flow-openmeteo-weather | 180.1s | 1 | 42 | 150.5s |
| skill-flow-eval-no-auto-upload | 98.6s | 1 | 31 | 96.2s |
| skill-flow-ipe-generate-schema | 192.2s | 1 | 52 | 189.1s |
| skill-flow-eval-local-crud | 92.6s | 1 | 28 | 86.8s |
| skill-flow-interactive-customer-escalation-triage | 600.6s | 4 | 60 | 133.2s |
| skill-flow-ixp-routing/explicit | 770.8s | 1 | 80 | 769.2s |
| skill-flow-ixp-routing/invoice-extraction | 901.9s | 1 | 109 | 900.0s |
| skill-flow-ixp-routing/receipts | 445.8s | 1 | 70 | 443.6s |
| skill-flow-ixp-routing/contracts | 400.8s | 1 | 60 | 398.4s |
| skill-flow-ixp-routing/forms-classify | 219.9s | 1 | 32 | 216.8s |
| skill-flow-hitl-quality-result-downstream | 321.3s | 1 | 43 | 313.4s |
| skill-flow-slack-weather-pipeline | 674.7s | 1 | 109 | 653.4s |
| skill-flow-hitl-smoke-node-placed | 359.6s | 1 | 70 | 344.8s |
| skill-flow-ixp-integration-handle-routing | 626.5s | 1 | 104 | 620.6s |
| skill-flow-e2e-escalation-orchestrator-paths | 549.3s | 1 | 73 | 422.2s |
| skill-flow-trigger-with-filter | 69.3s | 1 | 16 | 66.4s |
| skill-flow-ipe-jira-search-triage | 414.3s | 1 | 73 | 372.0s |
| skill-flow-non-catalog-http-fallback | 162.8s | 1 | 43 | 158.2s |
| skill-flow-hitl-quality-schema-design | 302.9s | 1 | 35 | 292.6s |
| skill-flow-ipe-enum | 365.5s | 1 | 84 | 360.2s |
| skill-flow-update-node | 68.3s | 1 | 16 | 40.8s |
| skill-flow-devcon-billing-discrepancy-detector | 579.0s | 1 | 103 | 548.9s |
| skill-flow-solution-select-ask | 91.9s | 5 | 13 | 11.3s |
| skill-flow-add-output | 70.9s | 1 | 12 | 38.7s |
| skill-flow-ipe-jira-get-issue | 309.3s | 1 | 81 | 276.5s |
| skill-flow-merge-parallel-sync | 159.7s | 1 | 44 | 151.9s |
| skill-flow-devcon-billing-dispute-resolution | 2052.0s | 1 | 232 | 1921.7s |
| skill-flow-ipe-dtl-load-by-default-false | 502.1s | 1 | 93 | 496.1s |
| skill-flow-batch-transform | 150.4s | 1 | 28 | 140.7s |
| skill-flow-coded-agent | 812.3s | 1 | 153 | 771.6s |
| skill-flow-hitl-smoke-multi-outcome-routing | 379.2s | 1 | 50 | 369.9s |
| skill-flow-delay | 103.5s | 1 | 27 | 95.6s |
| skill-flow-slack-channel-description-simulated | 250.9s | 3 | 52 | 68.8s |
| skill-flow-summarize | 131.6s | 1 | 30 | 124.5s |
| skill-flow-ipe-jira-lifecycle | 660.6s | 1 | 104 | 617.1s |
| skill-flow-bindings-reconfigure-different-connection | 578.6s | 1 | 97 | 575.1s |
| skill-flow-calculator | 146.0s | 1 | 39 | 119.0s |
| skill-flow-group-to-subflow | 495.9s | 1 | 61 | 472.9s |
| skill-flow-ipe-searchable-joins | 508.4s | 1 | 75 | 506.5s |
| skill-flow-bellevue-weather | 315.9s | 1 | 41 | 292.2s |
| skill-flow-ipe-query-params | 215.4s | 1 | 52 | 213.7s |
| skill-flow-feet-inches | 232.9s | 1 | 39 | 204.8s |
| skill-flow-inline-agent-robust | 280.4s | 1 | 55 | 278.9s |
| skill-flow-customer-escalation-simulated | 625.6s | 4 | 160 | 145.4s |
| skill-flow-e2e-devcon-expense-approval | 519.3s | 1 | 74 | 512.5s |
| skill-flow-hitl-smoke-completed-port | 252.7s | 1 | 33 | 247.7s |
| skill-flow-subflow | 174.1s | 1 | 32 | 150.0s |
| skill-flow-ipe-jira-create-issue | 255.9s | 1 | 62 | 228.8s |
| skill-flow-devcon-billing-invoice-lookup | 550.8s | 1 | 78 | 481.4s |
| skill-flow-generic-dynamic-node | 232.7s | 1 | 67 | 206.5s |
| skill-flow-move-node | 501.1s | 1 | 92 | 471.9s |
| skill-flow-ixp-scaffold-minimal | 217.9s | 1 | 37 | 212.3s |
| skill-flow-e2e-escalation-jira-ticket | 396.8s | 1 | 82 | 369.9s |


## Token Usage

**Total Tokens**: 418,032,039 (input: 41,144, output: 2,772,437)
**Cache Tokens**: write: 15,684,699, read: 399,533,759
**Agent Cost**: $220.3877
**Eval Overhead (judge + simulator)**: $0.1248
**Total Cost**: $220.5125
**Avg Tokens/Task**: 3,291,590

| Task ID | Input (uncached) | Output | Cache Write | Cache Read | Total | Cost |
|---------|------------------|--------|-------------|------------|-------|------|
| skill-flow-devcon-billing-resolution-writer | 48 | 20,927 | 191,848 | 3,448,196 | 3,661,019 | $2.0679 |
| skill-flow-hitl-quality-brownfield-insert | 4,368 | 19,345 | 112,631 | 2,503,725 | 2,640,069 | $1.4768 |
| skill-flow-file-attachment-debug | 3,700 | 7,088 | 140,569 | 1,440,351 | 1,591,708 | $1.0767 |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 130 | 71,311 | 434,854 | 11,822,047 | 12,328,342 | $6.2474 |
| skill-flow-init-validate | 14 | 1,328 | 63,111 | 359,516 | 423,969 | $0.3645 |
| skill-flow-jdbc-databricks-query | 66 | 17,401 | 177,882 | 4,289,826 | 4,485,175 | $2.2152 |
| skill-flow-reading-list | 40 | 23,893 | 100,884 | 2,308,101 | 2,432,918 | $1.4293 |
| skill-flow-ixp-routing-negative/stripe-http | 20 | 13,040 | 133,327 | 848,116 | 994,503 | $0.9501 |
| skill-flow-ixp-routing-negative/slack-summary | 34 | 15,217 | 163,134 | 1,905,808 | 2,084,193 | $1.4119 |
| skill-flow-ixp-routing-negative/sf-update | 38 | 11,025 | 110,815 | 2,002,500 | 2,124,378 | $1.1818 |
| skill-flow-ixp-routing-negative/http-webhook | 13,888 | 14,111 | 129,670 | 2,577,058 | 2,734,727 | $1.5127 |
| skill-flow-ixp-routing-negative/gsheet-loop | 40 | 14,442 | 93,617 | 2,076,276 | 2,184,375 | $1.1907 |
| skill-flow-ixp-routing-negative/queue-write | 48 | 13,227 | 115,099 | 2,120,089 | 2,248,463 | $1.2662 |
| skill-flow-ixp-routing-negative/teams-decision | 30 | 14,244 | 136,825 | 1,359,913 | 1,511,012 | $1.1348 |
| skill-flow-ixp-routing-negative/delay-email | 40 | 19,746 | 155,870 | 2,106,616 | 2,282,272 | $1.5128 |
| skill-flow-transform-group-by | 28 | 11,581 | 127,946 | 1,289,727 | 1,429,282 | $1.0405 |
| skill-flow-customer-escalation | 2,822 | 42,585 | 238,791 | 7,963,152 | 8,247,350 | $3.9317 |
| skill-flow-terminate | 36 | 16,158 | 152,049 | 2,016,278 | 2,184,521 | $1.4175 |
| skill-flow-bindings-no-duplicates | 141 | 21,320 | 178,805 | 5,818,274 | 6,018,540 | $2.7362 |
| skill-flow-eval-simulation-crud | 36 | 4,901 | 46,968 | 1,398,939 | 1,450,844 | $0.6694 |
| skill-flow-ixp-routing-listing/r01 | 3,065 | 2,022 | 80,923 | 403,792 | 489,802 | $0.4641 |
| skill-flow-ixp-routing-listing/r02 | 38 | 2,121 | 68,696 | 172,614 | 243,469 | $0.3413 |
| skill-flow-ixp-routing-listing/r03 | 14 | 1,641 | 67,160 | 366,085 | 434,900 | $0.3863 |
| skill-flow-ixp-routing-listing/r04 | 14 | 1,780 | 66,668 | 361,090 | 429,552 | $0.3851 |
| skill-flow-ixp-routing-listing/r05 | 12 | 1,666 | 89,643 | 356,689 | 448,010 | $0.4682 |
| skill-flow-ixp-routing-listing/r06 | 14 | 2,204 | 72,334 | 386,244 | 460,796 | $0.4202 |
| skill-flow-ixp-routing-listing/r07 | 8 | 904 | 21,699 | 212,384 | 234,995 | $0.1587 |
| skill-flow-ixp-routing-listing/r08 | 6 | 1,886 | 28,118 | 151,791 | 181,801 | $0.1793 |
| skill-flow-ixp-routing-listing/r09 | 12 | 1,869 | 49,717 | 396,396 | 447,994 | $0.3334 |
| skill-flow-ixp-routing-listing/r10 | 18 | 3,343 | 41,468 | 589,529 | 634,358 | $0.3826 |
| skill-flow-ipe-drive-to-slack | 56 | 24,214 | 137,011 | 3,665,747 | 3,827,028 | $1.9769 |
| skill-flow-ipe-required-groups | 66 | 39,601 | 166,107 | 4,042,388 | 4,248,162 | $2.4298 |
| skill-flow-ipe-enhanced-enum | 36 | 28,810 | 136,530 | 2,351,541 | 2,516,917 | $1.6497 |
| skill-flow-bindings-idempotent-reconfigure | 58 | 25,685 | 111,080 | 3,538,601 | 3,675,424 | $1.8636 |
| skill-flow-slack-http-fallback | 70 | 11,961 | 174,195 | 4,115,166 | 4,301,392 | $2.0674 |
| skill-flow-hitl-quality-boolean-decision | 30 | 21,387 | 125,124 | 1,631,561 | 1,778,102 | $1.2796 |
| skill-flow-bindings-multi-connector-independence | 68 | 21,336 | 146,853 | 4,633,013 | 4,801,270 | $2.2608 |
| skill-flow-rpa | 74 | 15,800 | 86,819 | 3,152,085 | 3,254,778 | $1.5084 |
| skill-flow-ipe-dtl-load-by-default-true | 102 | 23,755 | 78,120 | 4,450,178 | 4,552,155 | $1.9846 |
| skill-flow-lowcode-agent | 32 | 10,912 | 107,829 | 1,630,037 | 1,748,810 | $1.0571 |
| skill-flow-webhook-waitfor-parallel | 58 | 13,693 | 131,919 | 3,586,060 | 3,731,730 | $1.7761 |
| skill-flow-hitl-schema-design-simulated | 42 | 50,590 | 122,116 | 2,434,427 | 2,607,175 | $1.9639 |
| skill-flow-registry-discovery | 10 | 2,324 | 33,908 | 278,112 | 314,354 | $0.2455 |
| skill-flow-add-node | 16 | 5,744 | 73,178 | 657,717 | 736,655 | $0.5579 |
| skill-flow-multi-city-weather | 24 | 29,296 | 125,981 | 1,271,223 | 1,426,524 | $1.2933 |
| skill-flow-bellevue-weather-simulated | 112 | 29,220 | 172,917 | 7,244,805 | 7,447,054 | $3.2778 |
| skill-flow-ixp-invoice-extraction-simulated | 5,196 | 95,929 | 192,470 | 11,886,312 | 12,179,907 | $5.7620 |
| skill-flow-api-workflow | 64 | 24,796 | 122,679 | 3,188,781 | 3,336,320 | $1.7888 |
| skill-flow-loop-multiply | 112 | 41,785 | 161,325 | 5,504,077 | 5,707,299 | $2.8833 |
| skill-flow-devcon-billing-dispute-analyst | 62 | 24,898 | 155,402 | 4,506,519 | 4,686,881 | $2.3084 |
| skill-flow-eval-inline-agent | 64 | 21,229 | 132,142 | 4,260,390 | 4,413,825 | $2.0923 |
| skill-flow-ipe-complex-array | 36 | 7,973 | 125,446 | 2,062,319 | 2,195,774 | $1.2088 |
| skill-flow-e2e-escalation-slack-alert | 80 | 35,424 | 173,833 | 6,245,817 | 6,455,154 | $3.0572 |
| skill-flow-expense-approval-simulated | 34 | 26,051 | 118,333 | 1,973,833 | 2,118,251 | $1.4383 |
| skill-flow-transform-map | 22 | 8,686 | 96,182 | 1,055,596 | 1,160,486 | $0.8077 |
| skill-flow-wiki-pageviews | 40 | 34,923 | 130,904 | 2,518,503 | 2,684,370 | $1.7704 |
| skill-flow-paginated-reference-lookup | 50 | 9,383 | 143,495 | 3,307,924 | 3,460,852 | $1.6714 |
| skill-flow-eval-evaluator-type-choice | 36 | 5,236 | 31,384 | 1,162,741 | 1,199,397 | $0.5452 |
| skill-flow-outlook-waitfor-email | 32 | 6,924 | 110,874 | 1,682,268 | 1,800,098 | $1.0244 |
| skill-flow-switch | 28 | 13,859 | 95,751 | 1,436,349 | 1,545,987 | $0.9979 |
| skill-flow-cli-dice-roller-simulated | 38 | 10,838 | 209,560 | 2,027,609 | 2,248,045 | $1.5657 |
| skill-flow-ipe-multiselect | 72 | 12,998 | 86,239 | 3,197,280 | 3,296,589 | $1.4778 |
| skill-flow-decision | 26 | 8,853 | 94,209 | 1,279,916 | 1,383,004 | $0.8701 |
| skill-flow-ipe-ceql-where | 80 | 34,533 | 176,559 | 6,482,485 | 6,693,657 | $3.1251 |
| skill-flow-remove-node | 32 | 11,700 | 62,433 | 1,366,826 | 1,440,991 | $0.8198 |
| skill-flow-transform-filter | 26 | 13,656 | 100,023 | 1,213,180 | 1,326,885 | $0.9440 |
| skill-flow-ixp-scaffold-multinode | 80 | 18,985 | 102,642 | 4,735,514 | 4,857,221 | $2.0906 |
| skill-flow-outlook-trigger-inbox | 50 | 9,786 | 117,234 | 2,925,284 | 3,052,354 | $1.4642 |
| skill-flow-scheduled-trigger | 34 | 8,662 | 52,799 | 1,236,296 | 1,297,791 | $0.6989 |
| skill-flow-ixp-e2e-project-selection/aviation | 74 | 25,612 | 170,843 | 5,197,392 | 5,393,921 | $2.5843 |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 82 | 37,893 | 159,181 | 5,109,073 | 5,306,229 | $2.6983 |
| skill-flow-slack-channel-description | 68 | 15,359 | 144,722 | 4,716,371 | 4,876,520 | $2.1882 |
| skill-flow-ipe-path-params | 46 | 13,158 | 126,048 | 2,830,814 | 2,970,066 | $1.5194 |
| skill-flow-dice-roller | 18 | 5,874 | 79,030 | 730,902 | 815,824 | $0.6038 |
| skill-flow-openmeteo-weather | 32 | 7,066 | 131,931 | 1,924,396 | 2,063,425 | $1.1781 |
| skill-flow-eval-no-auto-upload | 28 | 4,572 | 48,105 | 1,065,055 | 1,117,760 | $0.5686 |
| skill-flow-ipe-generate-schema | 46 | 8,495 | 124,842 | 2,637,412 | 2,770,795 | $1.3869 |
| skill-flow-eval-local-crud | 26 | 4,027 | 41,195 | 928,296 | 973,544 | $0.4935 |
| skill-flow-interactive-customer-escalation-triage | 48 | 46,670 | 123,234 | 2,785,359 | 2,955,311 | $2.0195 |
| skill-flow-ixp-routing/explicit | 62 | 60,083 | 192,558 | 5,354,014 | 5,606,717 | $3.2297 |
| skill-flow-ixp-routing/invoice-extraction | 104 | 63,196 | 200,580 | 8,837,346 | 9,101,226 | $4.3516 |
| skill-flow-ixp-routing/receipts | 60 | 31,123 | 108,692 | 3,216,829 | 3,356,704 | $1.8397 |
| skill-flow-ixp-routing/contracts | 48 | 32,205 | 131,365 | 3,320,259 | 3,483,877 | $1.9719 |
| skill-flow-ixp-routing/forms-classify | 28 | 14,325 | 96,105 | 1,323,944 | 1,434,402 | $0.9725 |
| skill-flow-hitl-quality-result-downstream | 44 | 24,968 | 101,547 | 2,082,080 | 2,208,639 | $1.3801 |
| skill-flow-slack-weather-pipeline | 80 | 49,594 | 168,817 | 6,097,081 | 6,315,572 | $3.2063 |
| skill-flow-hitl-smoke-node-placed | 72 | 23,955 | 103,452 | 3,935,521 | 4,063,000 | $1.9281 |
| skill-flow-ixp-integration-handle-routing | 96 | 41,174 | 126,042 | 6,171,553 | 6,338,865 | $2.9420 |
| skill-flow-e2e-escalation-orchestrator-paths | 52 | 34,572 | 190,289 | 4,284,672 | 4,509,585 | $2.5177 |
| skill-flow-trigger-with-filter | 16 | 4,624 | 55,774 | 592,271 | 652,685 | $0.4562 |
| skill-flow-ipe-jira-search-triage | 46 | 26,855 | 167,158 | 3,543,636 | 3,737,695 | $2.0929 |
| skill-flow-non-catalog-http-fallback | 36 | 7,049 | 93,332 | 1,664,566 | 1,764,983 | $0.9552 |
| skill-flow-hitl-quality-schema-design | 28 | 25,774 | 105,108 | 1,371,234 | 1,502,144 | $1.1922 |
| skill-flow-ipe-enum | 48 | 26,769 | 144,426 | 3,146,509 | 3,317,752 | $1.8872 |
| skill-flow-update-node | 16 | 1,746 | 65,259 | 559,069 | 626,090 | $0.4387 |
| skill-flow-devcon-billing-discrepancy-detector | 70 | 40,323 | 183,932 | 5,362,462 | 5,586,787 | $2.9035 |
| skill-flow-solution-select-ask | 18 | 1,083 | 22,647 | 519,452 | 543,200 | $0.2612 |
| skill-flow-add-output | 16 | 1,428 | 49,244 | 566,038 | 616,726 | $0.3759 |
| skill-flow-ipe-jira-get-issue | 60 | 14,012 | 143,291 | 4,012,245 | 4,169,608 | $1.9514 |
| skill-flow-merge-parallel-sync | 32 | 9,910 | 85,910 | 1,398,224 | 1,494,076 | $0.8904 |
| skill-flow-devcon-billing-dispute-resolution | 186 | 165,897 | 305,511 | 24,339,069 | 24,810,663 | $10.9364 |
| skill-flow-ipe-dtl-load-by-default-false | 68 | 36,211 | 133,160 | 4,476,363 | 4,645,802 | $2.3856 |
| skill-flow-batch-transform | 22 | 10,041 | 100,031 | 1,029,151 | 1,139,245 | $0.8345 |
| skill-flow-coded-agent | 128 | 56,880 | 175,211 | 10,175,330 | 10,407,549 | $4.5632 |
| skill-flow-hitl-smoke-multi-outcome-routing | 44 | 32,136 | 118,224 | 2,595,825 | 2,746,229 | $1.7043 |
| skill-flow-delay | 20 | 6,284 | 69,260 | 812,161 | 887,725 | $0.5977 |
| skill-flow-slack-channel-description-simulated | 40 | 11,358 | 139,056 | 2,335,046 | 2,485,500 | $1.3998 |
| skill-flow-summarize | 26 | 8,540 | 85,476 | 1,164,742 | 1,258,784 | $0.7981 |
| skill-flow-ipe-jira-lifecycle | 72 | 46,234 | 170,173 | 5,716,250 | 5,932,729 | $3.0467 |
| skill-flow-bindings-reconfigure-different-connection | 98 | 43,655 | 153,193 | 6,553,217 | 6,750,163 | $3.1956 |
| skill-flow-calculator | 34 | 7,220 | 81,184 | 1,661,370 | 1,749,808 | $0.9113 |
| skill-flow-group-to-subflow | 52 | 45,462 | 96,163 | 2,774,063 | 2,915,740 | $1.8749 |
| skill-flow-ipe-searchable-joins | 62 | 37,078 | 136,016 | 3,672,517 | 3,845,673 | $2.1682 |
| skill-flow-bellevue-weather | 26 | 25,845 | 121,656 | 1,429,914 | 1,577,441 | $1.2729 |
| skill-flow-ipe-query-params | 40 | 12,347 | 104,941 | 1,960,532 | 2,077,860 | $1.1670 |
| skill-flow-feet-inches | 28 | 16,874 | 105,304 | 1,477,453 | 1,599,659 | $1.0913 |
| skill-flow-inline-agent-robust | 40 | 24,351 | 151,661 | 2,704,700 | 2,880,752 | $1.7455 |
| skill-flow-customer-escalation-simulated | 134 | 36,233 | 247,486 | 13,284,469 | 13,568,322 | $5.4748 |
| skill-flow-e2e-devcon-expense-approval | 62 | 45,793 | 126,465 | 3,678,522 | 3,850,842 | $2.2649 |
| skill-flow-hitl-smoke-completed-port | 26 | 19,986 | 113,358 | 1,335,038 | 1,468,408 | $1.1255 |
| skill-flow-subflow | 30 | 9,642 | 89,667 | 1,503,704 | 1,603,043 | $0.9321 |
| skill-flow-ipe-jira-create-issue | 52 | 11,156 | 134,607 | 3,182,582 | 3,328,397 | $1.6270 |
| skill-flow-devcon-billing-invoice-lookup | 2,215 | 32,642 | 168,421 | 5,482,278 | 5,685,556 | $2.7725 |
| skill-flow-generic-dynamic-node | 58 | 9,044 | 140,222 | 3,363,915 | 3,513,239 | $1.6708 |
| skill-flow-move-node | 80 | 38,564 | 100,669 | 4,552,116 | 4,691,429 | $2.3218 |
| skill-flow-ixp-scaffold-minimal | 30 | 15,984 | 145,608 | 1,740,055 | 1,901,677 | $1.3079 |
| skill-flow-e2e-escalation-jira-ticket | 55 | 29,725 | 174,591 | 4,259,700 | 4,464,071 | $2.3787 |


## Command Telemetry

**Total Commands**: 4231
**Success Rate**: 4141/4231 (97.9%)

### Commands by Tool

| Tool | Count | % |
|------|-------|---|
| Bash | 2426 | 57.3% |
| Read | 921 | 21.8% |
| Edit | 321 | 7.6% |
| TaskUpdate | 150 | 3.5% |
| Skill | 128 | 3.0% |
| Grep | 122 | 2.9% |
| TaskCreate | 99 | 2.3% |
| Write | 45 | 1.1% |
| Glob | 15 | 0.4% |
| Agent | 2 | 0.0% |
| SendMessage | 1 | 0.0% |
| TaskList | 1 | 0.0% |

### Performance

- **Average Command Time**: 2393.8ms
- **Total Command Time**: 10128.33s

### Slowest Commands

| Tool | Duration | Parameters |
|------|----------|------------|
| Bash | 137409ms | {'command': 'cd /work/output/artifacts/skill-flow-... |
| Bash | 89782ms | {'command': 'grep -rln "flow_files" /home/azureuse... |
| Bash | 55365ms | {'command': 'uip maestro flow registry get core.lo... |
| Bash | 52948ms | {'command': 'uip agent model list --output json --... |
| Bash | 51429ms | {'command': 'cd /work/output/artifacts/skill-flow-... |

**Most Common Pattern**: `Bash → Bash → Bash`

**Skill Tool Invoked**: 128 time(s)

## Agent Settings

- **Permission Mode**: acceptEdits
- **Allowed Tools**: Skill, Bash, Read, Write, Edit, Glob, Grep
- **Model**: us.anthropic.claude-sonnet-5
- **Max Turns**: 120
- **System Prompt**: You are a coding agent. Do not access files in sibling runs/* directories. Everywhere else is permitted. 
- **Plugins**: /home/azureuser/projects/skills

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