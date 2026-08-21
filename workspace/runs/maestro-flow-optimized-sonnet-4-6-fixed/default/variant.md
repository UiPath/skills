# Variant Report: default

**Experiment**: skill-tests-smoke
**Description**: Linux PR-gate smoke tests — docker isolation, fast turn budget

## Summary

- **Tasks Run**: 127
- **Succeeded**: 117
- **Failed**: 10
- **Errors**: 0
- **Pass Rate**: 92.1% (117/127)
- **Average Score**: 0.955
- **Average Duration**: 337.6s
- **Total Tokens**: 173,570,677
- **Score Stddev**: 0.160
- **Duration Stddev**: 235.9s

## Task Details

| Task | Score | Status | Avg Duration |
|------|-------|--------|--------------|
| skill-flow-ipe-generate-schema | 0.800 | FAILURE | 356.6s |
| skill-flow-subflow | 1.000 | SUCCESS | 301.4s |
| skill-flow-hitl-smoke-completed-port | 1.000 | SUCCESS | 488.3s |
| skill-flow-outlook-trigger-inbox | 1.000 | SUCCESS | 328.9s |
| skill-flow-ipe-path-params | 1.000 | SUCCESS | 389.2s |
| skill-flow-webhook-waitfor-parallel | 1.000 | SUCCESS | 323.6s |
| skill-flow-eval-simulation-crud | 1.000 | SUCCESS | 229.1s |
| skill-flow-e2e-escalation-slack-alert | 1.000 | SUCCESS | 439.8s |
| skill-flow-decision | 1.000 | SUCCESS | 306.2s |
| skill-flow-slack-http-fallback | 1.000 | SUCCESS | 390.2s |
| skill-flow-trigger-with-filter | 1.000 | SUCCESS | 95.4s |
| skill-flow-bindings-reconfigure-different-connection | 1.000 | SUCCESS | 371.0s |
| skill-flow-hitl-schema-design-simulated | 0.895 | SUCCESS | 781.0s |
| skill-flow-transform-map | 1.000 | SUCCESS | 318.3s |
| skill-flow-ipe-required-groups | 1.000 | SUCCESS | 306.7s |
| skill-flow-customer-escalation-simulated | 0.938 | SUCCESS | 983.4s |
| skill-flow-ipe-jira-get-issue | 1.000 | SUCCESS | 418.6s |
| skill-flow-ixp-routing-listing/r01 | 1.000 | SUCCESS | 81.6s |
| skill-flow-ixp-routing-listing/r02 | 1.000 | SUCCESS | 79.1s |
| skill-flow-ixp-routing-listing/r03 | 1.000 | SUCCESS | 87.0s |
| skill-flow-ixp-routing-listing/r04 | 1.000 | SUCCESS | 79.1s |
| skill-flow-ixp-routing-listing/r05 | 1.000 | SUCCESS | 85.4s |
| skill-flow-ixp-routing-listing/r06 | 1.000 | SUCCESS | 78.5s |
| skill-flow-ixp-routing-listing/r07 | 1.000 | SUCCESS | 65.8s |
| skill-flow-ixp-routing-listing/r08 | 1.000 | SUCCESS | 69.3s |
| skill-flow-ixp-routing-listing/r09 | 1.000 | SUCCESS | 78.0s |
| skill-flow-ixp-routing-listing/r10 | 1.000 | SUCCESS | 102.2s |
| skill-flow-ipe-dtl-load-by-default-false | 1.000 | SUCCESS | 320.1s |
| skill-flow-cli-dice-roller-simulated | 1.000 | SUCCESS | 316.3s |
| skill-flow-update-node | 1.000 | SUCCESS | 169.5s |
| skill-flow-ipe-ceql-where | 1.000 | SUCCESS | 426.1s |
| skill-flow-customer-escalation | 1.000 | SUCCESS | 845.0s |
| skill-flow-bellevue-weather-simulated | 1.000 | SUCCESS | 383.0s |
| skill-flow-reading-list | 1.000 | SUCCESS | 316.4s |
| skill-flow-jdbc-databricks-query | 0.769 | FAILURE | 418.9s |
| skill-flow-file-attachment-debug | 1.000 | SUCCESS | 245.3s |
| skill-flow-bindings-multi-connector-independence | 1.000 | SUCCESS | 342.2s |
| skill-flow-ipe-query-params | 1.000 | SUCCESS | 233.9s |
| skill-flow-wiki-pageviews | 1.000 | SUCCESS | 620.1s |
| skill-flow-ipe-complex-array | 0.875 | SUCCESS | 259.3s |
| skill-flow-merge-parallel-sync | 1.000 | SUCCESS | 182.1s |
| skill-flow-ipe-dtl-load-by-default-true | 1.000 | SUCCESS | 282.3s |
| skill-flow-bindings-no-duplicates | 1.000 | SUCCESS | 327.9s |
| skill-flow-lowcode-agent | 1.000 | SUCCESS | 323.1s |
| skill-flow-eval-no-auto-upload | 1.000 | SUCCESS | 147.8s |
| skill-flow-hitl-quality-schema-design | 1.000 | SUCCESS | 408.5s |
| skill-flow-terminate | 1.000 | SUCCESS | 257.7s |
| skill-flow-ipe-jira-search-triage | 1.000 | SUCCESS | 430.4s |
| skill-flow-hitl-quality-boolean-decision | 1.000 | SUCCESS | 311.2s |
| skill-flow-multi-city-weather | 0.000 | TIMEOUT | 903.6s |
| skill-flow-solution-select-ask | 1.000 | SUCCESS | 88.6s |
| skill-flow-hitl-smoke-node-placed | 1.000 | SUCCESS | 480.1s |
| skill-flow-e2e-escalation-jira-ticket | 1.000 | SUCCESS | 459.0s |
| skill-flow-coded-agent | 0.375 | FAILURE | 516.2s |
| skill-flow-ixp-scaffold-multinode | 1.000 | SUCCESS | 422.5s |
| skill-flow-inline-agent-robust | 0.905 | FAILURE | 244.7s |
| skill-flow-eval-local-crud | 1.000 | SUCCESS | 147.6s |
| skill-flow-paginated-reference-lookup | 1.000 | SUCCESS | 265.8s |
| skill-flow-api-workflow | 0.375 | FAILURE | 267.4s |
| skill-flow-expense-approval-simulated | 1.000 | SUCCESS | 564.5s |
| skill-flow-bellevue-weather | 1.000 | SUCCESS | 285.4s |
| skill-flow-devcon-billing-dispute-resolution | 0.545 | FAILURE | 1772.7s |
| skill-flow-ixp-routing/explicit | 1.000 | SUCCESS | 488.9s |
| skill-flow-ixp-routing/invoice-extraction | 1.000 | SUCCESS | 417.6s |
| skill-flow-ixp-routing/receipts | 1.000 | SUCCESS | 142.1s |
| skill-flow-ixp-routing/contracts | 1.000 | SUCCESS | 421.7s |
| skill-flow-ixp-routing/forms-classify | 1.000 | SUCCESS | 522.5s |
| skill-flow-slack-channel-description | 0.250 | MAX_TURNS_EXHAUSTED | 330.4s |
| skill-flow-transform-group-by | 0.375 | FAILURE | 141.8s |
| skill-flow-ipe-enum | 1.000 | SUCCESS | 352.4s |
| skill-flow-interactive-customer-escalation-triage | 1.000 | SUCCESS | 349.6s |
| skill-flow-add-output | 1.000 | SUCCESS | 65.9s |
| skill-flow-rpa | 1.000 | SUCCESS | 208.7s |
| skill-flow-feet-inches | 1.000 | SUCCESS | 281.1s |
| skill-flow-summarize | 1.000 | SUCCESS | 212.7s |
| skill-flow-devcon-billing-dispute-analyst | 1.000 | SUCCESS | 524.9s |
| skill-flow-ixp-invoice-extraction-simulated | 1.000 | SUCCESS | 659.7s |
| skill-flow-hitl-quality-brownfield-insert | 1.000 | SUCCESS | 477.9s |
| skill-flow-registry-discovery | 1.000 | SUCCESS | 54.9s |
| skill-flow-ixp-routing-negative/stripe-http | 1.000 | SUCCESS | 102.7s |
| skill-flow-ixp-routing-negative/slack-summary | 1.000 | SUCCESS | 143.4s |
| skill-flow-ixp-routing-negative/sf-update | 1.000 | SUCCESS | 271.6s |
| skill-flow-ixp-routing-negative/http-webhook | 1.000 | SUCCESS | 122.3s |
| skill-flow-ixp-routing-negative/gsheet-loop | 1.000 | SUCCESS | 192.8s |
| skill-flow-ixp-routing-negative/queue-write | 1.000 | SUCCESS | 152.4s |
| skill-flow-ixp-routing-negative/teams-decision | 1.000 | SUCCESS | 171.6s |
| skill-flow-ixp-routing-negative/delay-email | 1.000 | SUCCESS | 359.4s |
| skill-flow-remove-node | 1.000 | SUCCESS | 179.8s |
| skill-flow-calculator | 1.000 | SUCCESS | 129.2s |
| skill-flow-move-node | 1.000 | SUCCESS | 255.0s |
| skill-flow-devcon-billing-resolution-writer | 1.000 | SUCCESS | 264.1s |
| skill-flow-add-node | 1.000 | SUCCESS | 124.1s |
| skill-flow-devcon-billing-invoice-lookup | 0.909 | SUCCESS | 676.6s |
| skill-flow-ipe-jira-create-issue | 1.000 | SUCCESS | 411.7s |
| skill-flow-eval-evaluator-type-choice | 1.000 | SUCCESS | 104.2s |
| skill-flow-batch-transform | 1.000 | SUCCESS | 192.5s |
| skill-flow-ipe-jira-lifecycle | 1.000 | SUCCESS | 673.0s |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 1.000 | SUCCESS | 322.9s |
| skill-flow-ipe-multiselect | 1.000 | SUCCESS | 179.3s |
| skill-flow-bindings-idempotent-reconfigure | 1.000 | SUCCESS | 398.2s |
| skill-flow-non-catalog-http-fallback | 1.000 | SUCCESS | 251.7s |
| skill-flow-dice-roller | 1.000 | SUCCESS | 124.4s |
| skill-flow-transform-filter | 1.000 | SUCCESS | 362.9s |
| skill-flow-ipe-enhanced-enum | 1.000 | SUCCESS | 289.9s |
| skill-flow-group-to-subflow | 1.000 | SUCCESS | 416.4s |
| skill-flow-slack-channel-description-simulated | 0.917 | SUCCESS | 365.8s |
| skill-flow-e2e-escalation-orchestrator-paths | 1.000 | SUCCESS | 1017.3s |
| skill-flow-scheduled-trigger | 1.000 | SUCCESS | 195.2s |
| skill-flow-devcon-billing-discrepancy-detector | 1.000 | SUCCESS | 443.1s |
| skill-flow-e2e-devcon-expense-approval | 1.000 | SUCCESS | 571.6s |
| skill-flow-ixp-integration-handle-routing | 1.000 | SUCCESS | 407.3s |
| skill-flow-openmeteo-weather | 1.000 | SUCCESS | 170.3s |
| skill-flow-slack-weather-pipeline | 1.000 | SUCCESS | 655.4s |
| skill-flow-generic-dynamic-node | 1.000 | SUCCESS | 260.3s |
| skill-flow-ipe-searchable-joins | 1.000 | SUCCESS | 352.5s |
| skill-flow-hitl-quality-result-downstream | 1.000 | SUCCESS | 435.6s |
| skill-flow-init-validate | 1.000 | SUCCESS | 83.9s |
| skill-flow-outlook-waitfor-email | 1.000 | SUCCESS | 161.9s |
| skill-flow-switch | 1.000 | SUCCESS | 261.6s |
| skill-flow-ixp-scaffold-minimal | 1.000 | SUCCESS | 741.6s |
| skill-flow-delay | 1.000 | SUCCESS | 150.4s |
| skill-flow-eval-inline-agent | 1.000 | SUCCESS | 319.2s |
| skill-flow-hitl-smoke-multi-outcome-routing | 1.000 | SUCCESS | 469.8s |
| skill-flow-ipe-drive-to-slack | 1.000 | SUCCESS | 260.9s |
| skill-flow-loop-multiply | 0.375 | FAILURE | 809.2s |
| skill-flow-ixp-e2e-project-selection/aviation | 1.000 | SUCCESS | 281.9s |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 1.000 | SUCCESS | 314.0s |


## Generation Metrics

| Task ID | Total Latency | Turns | Asst Turns | Avg Turn Latency |
|---------|---------------|-------|------------|------------------|
| skill-flow-ipe-generate-schema | 356.6s | 1 | 49 | 343.6s |
| skill-flow-subflow | 301.4s | 1 | 29 | 263.7s |
| skill-flow-hitl-smoke-completed-port | 488.3s | 1 | 26 | 465.7s |
| skill-flow-outlook-trigger-inbox | 328.9s | 1 | 47 | 302.3s |
| skill-flow-ipe-path-params | 389.2s | 1 | 62 | 374.1s |
| skill-flow-webhook-waitfor-parallel | 323.6s | 1 | 46 | 307.6s |
| skill-flow-eval-simulation-crud | 229.1s | 1 | 21 | 215.3s |
| skill-flow-e2e-escalation-slack-alert | 439.8s | 1 | 53 | 398.1s |
| skill-flow-decision | 306.2s | 1 | 29 | 253.1s |
| skill-flow-slack-http-fallback | 390.2s | 1 | 56 | 352.6s |
| skill-flow-trigger-with-filter | 95.4s | 1 | 11 | 81.2s |
| skill-flow-bindings-reconfigure-different-connection | 371.0s | 1 | 48 | 354.0s |
| skill-flow-hitl-schema-design-simulated | 781.0s | 2 | 46 | 365.4s |
| skill-flow-transform-map | 318.3s | 1 | 31 | 301.6s |
| skill-flow-ipe-required-groups | 306.7s | 1 | 42 | 291.2s |
| skill-flow-customer-escalation-simulated | 983.4s | 3 | 97 | 308.2s |
| skill-flow-ipe-jira-get-issue | 418.6s | 1 | 56 | 360.9s |
| skill-flow-ixp-routing-listing/r01 | 81.6s | 1 | 8 | 66.3s |
| skill-flow-ixp-routing-listing/r02 | 79.1s | 1 | 8 | 63.7s |
| skill-flow-ixp-routing-listing/r03 | 87.0s | 1 | 11 | 72.0s |
| skill-flow-ixp-routing-listing/r04 | 79.1s | 1 | 8 | 64.9s |
| skill-flow-ixp-routing-listing/r05 | 85.4s | 1 | 12 | 69.7s |
| skill-flow-ixp-routing-listing/r06 | 78.5s | 1 | 8 | 66.1s |
| skill-flow-ixp-routing-listing/r07 | 65.8s | 1 | 8 | 49.9s |
| skill-flow-ixp-routing-listing/r08 | 69.3s | 1 | 7 | 62.3s |
| skill-flow-ixp-routing-listing/r09 | 78.0s | 1 | 8 | 64.2s |
| skill-flow-ixp-routing-listing/r10 | 102.2s | 1 | 9 | 86.3s |
| skill-flow-ipe-dtl-load-by-default-false | 320.1s | 1 | 31 | 304.5s |
| skill-flow-cli-dice-roller-simulated | 316.3s | 3 | 33 | 83.0s |
| skill-flow-update-node | 169.5s | 1 | 20 | 85.6s |
| skill-flow-ipe-ceql-where | 426.1s | 1 | 60 | 412.1s |
| skill-flow-customer-escalation | 845.0s | 1 | 67 | 826.8s |
| skill-flow-bellevue-weather-simulated | 383.0s | 2 | 39 | 159.6s |
| skill-flow-reading-list | 316.4s | 1 | 22 | 277.4s |
| skill-flow-jdbc-databricks-query | 418.9s | 1 | 48 | 403.6s |
| skill-flow-file-attachment-debug | 245.3s | 1 | 30 | 198.9s |
| skill-flow-bindings-multi-connector-independence | 342.2s | 1 | 63 | 325.1s |
| skill-flow-ipe-query-params | 233.9s | 1 | 35 | 217.4s |
| skill-flow-wiki-pageviews | 620.1s | 1 | 35 | 553.3s |
| skill-flow-ipe-complex-array | 259.3s | 1 | 44 | 241.1s |
| skill-flow-merge-parallel-sync | 182.1s | 1 | 29 | 160.4s |
| skill-flow-ipe-dtl-load-by-default-true | 282.3s | 1 | 43 | 270.2s |
| skill-flow-bindings-no-duplicates | 327.9s | 1 | 43 | 311.2s |
| skill-flow-lowcode-agent | 323.1s | 1 | 34 | 277.2s |
| skill-flow-eval-no-auto-upload | 147.8s | 1 | 23 | 129.9s |
| skill-flow-hitl-quality-schema-design | 408.5s | 1 | 40 | 387.0s |
| skill-flow-terminate | 257.7s | 1 | 34 | 218.6s |
| skill-flow-ipe-jira-search-triage | 430.4s | 1 | 43 | 376.7s |
| skill-flow-hitl-quality-boolean-decision | 311.2s | 1 | 35 | 298.4s |
| skill-flow-multi-city-weather | 903.6s | 1 | 23 | 900.0s |
| skill-flow-solution-select-ask | 88.6s | 5 | 16 | 10.7s |
| skill-flow-hitl-smoke-node-placed | 480.1s | 1 | 35 | 469.1s |
| skill-flow-e2e-escalation-jira-ticket | 459.0s | 1 | 45 | 414.1s |
| skill-flow-coded-agent | 516.2s | 1 | 116 | 490.8s |
| skill-flow-ixp-scaffold-multinode | 422.5s | 1 | 46 | 407.1s |
| skill-flow-inline-agent-robust | 244.7s | 1 | 41 | 240.1s |
| skill-flow-eval-local-crud | 147.6s | 1 | 15 | 143.0s |
| skill-flow-paginated-reference-lookup | 265.8s | 1 | 57 | 262.1s |
| skill-flow-api-workflow | 267.4s | 1 | 35 | 236.8s |
| skill-flow-expense-approval-simulated | 564.5s | 3 | 36 | 175.2s |
| skill-flow-bellevue-weather | 285.4s | 1 | 29 | 252.6s |
| skill-flow-devcon-billing-dispute-resolution | 1772.7s | 1 | 194 | 1735.2s |
| skill-flow-ixp-routing/explicit | 488.9s | 1 | 69 | 486.2s |
| skill-flow-ixp-routing/invoice-extraction | 417.6s | 1 | 43 | 415.3s |
| skill-flow-ixp-routing/receipts | 142.1s | 1 | 38 | 138.2s |
| skill-flow-ixp-routing/contracts | 421.7s | 1 | 69 | 416.9s |
| skill-flow-ixp-routing/forms-classify | 522.5s | 1 | 35 | 518.6s |
| skill-flow-slack-channel-description | 330.4s | 1 | 66 | 298.8s |
| skill-flow-transform-group-by | 141.8s | 1 | 25 | 132.2s |
| skill-flow-ipe-enum | 352.4s | 1 | 53 | 347.9s |
| skill-flow-interactive-customer-escalation-triage | 349.6s | 3 | 33 | 93.9s |
| skill-flow-add-output | 65.9s | 1 | 13 | 37.6s |
| skill-flow-rpa | 208.7s | 1 | 41 | 158.2s |
| skill-flow-feet-inches | 281.1s | 1 | 33 | 248.3s |
| skill-flow-summarize | 212.7s | 1 | 36 | 203.3s |
| skill-flow-devcon-billing-dispute-analyst | 524.9s | 1 | 90 | 467.2s |
| skill-flow-ixp-invoice-extraction-simulated | 659.7s | 3 | 42 | 194.8s |
| skill-flow-hitl-quality-brownfield-insert | 477.9s | 1 | 45 | 466.4s |
| skill-flow-registry-discovery | 54.9s | 1 | 13 | 51.8s |
| skill-flow-ixp-routing-negative/stripe-http | 102.7s | 1 | 28 | 100.7s |
| skill-flow-ixp-routing-negative/slack-summary | 143.4s | 1 | 33 | 141.3s |
| skill-flow-ixp-routing-negative/sf-update | 271.6s | 1 | 25 | 269.7s |
| skill-flow-ixp-routing-negative/http-webhook | 122.3s | 1 | 36 | 119.7s |
| skill-flow-ixp-routing-negative/gsheet-loop | 192.8s | 1 | 33 | 189.9s |
| skill-flow-ixp-routing-negative/queue-write | 152.4s | 1 | 39 | 150.5s |
| skill-flow-ixp-routing-negative/teams-decision | 171.6s | 1 | 35 | 169.6s |
| skill-flow-ixp-routing-negative/delay-email | 359.4s | 1 | 25 | 356.6s |
| skill-flow-remove-node | 179.8s | 1 | 18 | 150.7s |
| skill-flow-calculator | 129.2s | 1 | 27 | 101.8s |
| skill-flow-move-node | 255.0s | 1 | 14 | 227.9s |
| skill-flow-devcon-billing-resolution-writer | 264.1s | 1 | 29 | 204.6s |
| skill-flow-add-node | 124.1s | 1 | 23 | 98.8s |
| skill-flow-devcon-billing-invoice-lookup | 676.6s | 1 | 53 | 595.2s |
| skill-flow-ipe-jira-create-issue | 411.7s | 1 | 39 | 381.4s |
| skill-flow-eval-evaluator-type-choice | 104.2s | 1 | 25 | 101.7s |
| skill-flow-batch-transform | 192.5s | 1 | 32 | 184.6s |
| skill-flow-ipe-jira-lifecycle | 673.0s | 1 | 69 | 623.7s |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 322.9s | 1 | 62 | 313.9s |
| skill-flow-ipe-multiselect | 179.3s | 1 | 34 | 176.4s |
| skill-flow-bindings-idempotent-reconfigure | 398.2s | 1 | 67 | 395.2s |
| skill-flow-non-catalog-http-fallback | 251.7s | 1 | 49 | 248.9s |
| skill-flow-dice-roller | 124.4s | 1 | 26 | 103.1s |
| skill-flow-transform-filter | 362.9s | 1 | 38 | 332.1s |
| skill-flow-ipe-enhanced-enum | 289.9s | 1 | 40 | 287.6s |
| skill-flow-group-to-subflow | 416.4s | 1 | 19 | 391.2s |
| skill-flow-slack-channel-description-simulated | 365.8s | 2 | 70 | 155.7s |
| skill-flow-e2e-escalation-orchestrator-paths | 1017.3s | 1 | 77 | 876.4s |
| skill-flow-scheduled-trigger | 195.2s | 1 | 41 | 185.2s |
| skill-flow-devcon-billing-discrepancy-detector | 443.1s | 1 | 58 | 408.9s |
| skill-flow-e2e-devcon-expense-approval | 571.6s | 1 | 40 | 565.9s |
| skill-flow-ixp-integration-handle-routing | 407.3s | 1 | 53 | 401.2s |
| skill-flow-openmeteo-weather | 170.3s | 1 | 30 | 141.9s |
| skill-flow-slack-weather-pipeline | 655.4s | 1 | 75 | 622.0s |
| skill-flow-generic-dynamic-node | 260.3s | 1 | 54 | 234.6s |
| skill-flow-ipe-searchable-joins | 352.5s | 1 | 44 | 349.7s |
| skill-flow-hitl-quality-result-downstream | 435.6s | 1 | 46 | 430.2s |
| skill-flow-init-validate | 83.9s | 1 | 20 | 81.4s |
| skill-flow-outlook-waitfor-email | 161.9s | 1 | 37 | 154.8s |
| skill-flow-switch | 261.6s | 1 | 26 | 240.4s |
| skill-flow-ixp-scaffold-minimal | 741.6s | 1 | 34 | 736.6s |
| skill-flow-delay | 150.4s | 1 | 38 | 145.2s |
| skill-flow-eval-inline-agent | 319.2s | 1 | 32 | 317.4s |
| skill-flow-hitl-smoke-multi-outcome-routing | 469.8s | 1 | 38 | 463.0s |
| skill-flow-ipe-drive-to-slack | 260.9s | 1 | 68 | 259.1s |
| skill-flow-loop-multiply | 809.2s | 1 | 39 | 781.6s |
| skill-flow-ixp-e2e-project-selection/aviation | 281.9s | 1 | 39 | 274.1s |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 314.0s | 1 | 51 | 306.3s |


## Token Usage

**Total Tokens**: 173,570,677 (input: 148,353, output: 1,962,600)
**Cache Tokens**: write: 9,082,838, read: 162,376,886
**Agent Cost**: $112.6578
**Eval Overhead (judge + simulator)**: $0.1041
**Total Cost**: $112.7619 (floor — 1 task(s) have spend missing from this total)
**Avg Tokens/Task**: 1,366,698

| Task ID | Input (uncached) | Output | Cache Write | Cache Read | Total | Cost |
|---------|------------------|--------|-------------|------------|-------|------|
| skill-flow-ipe-generate-schema | 526 | 12,302 | 101,242 | 1,373,701 | 1,487,771 | $0.9779 |
| skill-flow-subflow | 510 | 10,889 | 63,446 | 723,578 | 798,423 | $0.6199 |
| skill-flow-hitl-smoke-completed-port | 528 | 24,034 | 48,699 | 496,413 | 569,674 | $0.6936 |
| skill-flow-outlook-trigger-inbox | 578 | 7,356 | 79,700 | 977,446 | 1,065,080 | $0.7042 |
| skill-flow-ipe-path-params | 561 | 12,101 | 79,529 | 2,241,025 | 2,333,216 | $1.1537 |
| skill-flow-webhook-waitfor-parallel | 640 | 8,640 | 82,480 | 1,470,006 | 1,561,766 | $0.8818 |
| skill-flow-eval-simulation-crud | 960 | 7,595 | 28,719 | 424,478 | 461,752 | $0.3518 |
| skill-flow-e2e-escalation-slack-alert | 906 | 15,854 | 99,583 | 1,973,743 | 2,090,086 | $1.2061 |
| skill-flow-decision | 500 | 7,702 | 48,835 | 730,612 | 787,649 | $0.5193 |
| skill-flow-slack-http-fallback | 554 | 9,531 | 90,631 | 2,011,034 | 2,111,750 | $1.0878 |
| skill-flow-trigger-with-filter | 534 | 4,275 | 29,011 | 205,204 | 239,024 | $0.2361 |
| skill-flow-bindings-reconfigure-different-connection | 838 | 10,998 | 85,522 | 1,584,188 | 1,681,546 | $0.9634 |
| skill-flow-hitl-schema-design-simulated | 904 | 40,344 | 131,107 | 1,397,298 | 1,569,653 | $1.5305 |
| skill-flow-transform-map | 11,544 | 11,271 | 71,438 | 788,404 | 882,657 | $0.7081 |
| skill-flow-ipe-required-groups | 477 | 8,241 | 35,773 | 1,064,979 | 1,109,470 | $0.5787 |
| skill-flow-customer-escalation-simulated | 19,659 | 43,109 | 154,447 | 3,164,222 | 3,381,437 | $2.2482 |
| skill-flow-ipe-jira-get-issue | 596 | 10,835 | 88,425 | 1,867,495 | 1,967,351 | $1.0562 |
| skill-flow-ixp-routing-listing/r01 | 451 | 2,173 | 17,888 | 141,486 | 161,998 | $0.1435 |
| skill-flow-ixp-routing-listing/r02 | 450 | 2,120 | 22,323 | 141,540 | 166,433 | $0.1593 |
| skill-flow-ixp-routing-listing/r03 | 454 | 1,502 | 16,847 | 227,775 | 246,578 | $0.1554 |
| skill-flow-ixp-routing-listing/r04 | 455 | 1,904 | 17,835 | 141,386 | 161,580 | $0.1392 |
| skill-flow-ixp-routing-listing/r05 | 451 | 1,517 | 32,974 | 209,816 | 244,758 | $0.2107 |
| skill-flow-ixp-routing-listing/r06 | 454 | 2,733 | 22,249 | 141,385 | 166,821 | $0.1682 |
| skill-flow-ixp-routing-listing/r07 | 447 | 2,295 | 19,194 | 100,995 | 122,931 | $0.1380 |
| skill-flow-ixp-routing-listing/r08 | 453 | 2,098 | 17,855 | 101,007 | 121,413 | $0.1301 |
| skill-flow-ixp-routing-listing/r09 | 454 | 2,031 | 17,892 | 141,498 | 161,875 | $0.1414 |
| skill-flow-ixp-routing-listing/r10 | 453 | 1,674 | 14,577 | 223,572 | 240,276 | $0.1482 |
| skill-flow-ipe-dtl-load-by-default-false | 494 | 10,490 | 72,442 | 752,317 | 835,743 | $0.6562 |
| skill-flow-cli-dice-roller-simulated | 681 | 6,015 | 67,574 | 907,450 | 981,720 | $0.6233 |
| skill-flow-update-node | 483 | 2,116 | 44,082 | 420,834 | 467,515 | $0.3247 |
| skill-flow-ipe-ceql-where | 576 | 11,106 | 101,552 | 3,003,975 | 3,117,209 | $1.4503 |
| skill-flow-customer-escalation | 630 | 40,882 | 119,323 | 2,861,460 | 3,022,295 | $1.9210 |
| skill-flow-bellevue-weather-simulated | 771 | 10,738 | 64,743 | 1,116,745 | 1,192,997 | $0.7532 |
| skill-flow-reading-list | 976 | 11,491 | 50,104 | 425,245 | 487,816 | $0.4908 |
| skill-flow-jdbc-databricks-query | 610 | 11,387 | 84,236 | 1,467,927 | 1,564,160 | $0.9289 |
| skill-flow-file-attachment-debug | 3,249 | 4,799 | 59,923 | 791,524 | 859,495 | $0.5439 |
| skill-flow-bindings-multi-connector-independence | 567 | 11,568 | 94,167 | 2,346,172 | 2,452,474 | $1.2322 |
| skill-flow-ipe-query-params | 523 | 6,642 | 59,434 | 772,825 | 839,424 | $0.5559 |
| skill-flow-wiki-pageviews | 781 | 31,377 | 107,230 | 1,112,985 | 1,252,373 | $1.2090 |
| skill-flow-ipe-complex-array | 487 | 7,421 | 77,677 | 1,401,522 | 1,487,107 | $0.8245 |
| skill-flow-merge-parallel-sync | 1,145 | 3,708 | 43,342 | 639,468 | 687,663 | $0.4134 |
| skill-flow-ipe-dtl-load-by-default-true | 510 | 8,929 | 82,943 | 1,448,119 | 1,540,501 | $0.8809 |
| skill-flow-bindings-no-duplicates | 521 | 14,797 | 78,224 | 1,435,592 | 1,529,134 | $0.9475 |
| skill-flow-lowcode-agent | 516 | 11,126 | 55,889 | 741,335 | 808,866 | $0.6004 |
| skill-flow-eval-no-auto-upload | 896 | 2,892 | 19,850 | 527,115 | 550,753 | $0.2786 |
| skill-flow-hitl-quality-schema-design | 618 | 19,978 | 73,801 | 1,175,637 | 1,270,034 | $0.9310 |
| skill-flow-terminate | 521 | 10,306 | 59,060 | 784,430 | 854,317 | $0.6130 |
| skill-flow-ipe-jira-search-triage | 615 | 19,426 | 92,539 | 1,096,268 | 1,208,848 | $0.9691 |
| skill-flow-hitl-quality-boolean-decision | 657 | 17,882 | 54,892 | 698,253 | 771,684 | $0.6855 |
| skill-flow-multi-city-weather | 13 | 56,598 | 106,215 | 480,144 | 642,970 | $1.3914 |
| skill-flow-solution-select-ask | 459 | 1,212 | 12,739 | 305,621 | 320,031 | $0.1624 |
| skill-flow-hitl-smoke-node-placed | 541 | 25,865 | 48,212 | 860,484 | 935,102 | $0.8285 |
| skill-flow-e2e-escalation-jira-ticket | 873 | 23,804 | 85,398 | 1,320,698 | 1,430,773 | $1.0761 |
| skill-flow-coded-agent | 720 | 17,873 | 131,105 | 6,794,779 | 6,944,477 | $2.8003 |
| skill-flow-ixp-scaffold-multinode | 647 | 23,932 | 67,214 | 1,677,573 | 1,769,366 | $1.1162 |
| skill-flow-inline-agent-robust | 631 | 11,417 | 74,936 | 1,210,495 | 1,297,479 | $0.8173 |
| skill-flow-eval-local-crud | 837 | 7,599 | 33,422 | 278,610 | 320,468 | $0.3254 |
| skill-flow-paginated-reference-lookup | 560 | 10,863 | 105,972 | 2,616,889 | 2,734,284 | $1.3471 |
| skill-flow-api-workflow | 493 | 12,715 | 51,313 | 703,417 | 767,938 | $0.5957 |
| skill-flow-expense-approval-simulated | 914 | 29,438 | 59,914 | 961,930 | 1,052,196 | $0.9742 |
| skill-flow-bellevue-weather | 563 | 14,777 | 60,542 | 699,014 | 774,896 | $0.6601 |
| skill-flow-devcon-billing-dispute-resolution | 13,926 | 98,372 | 333,848 | 8,860,247 | 9,306,393 | $5.4274 |
| skill-flow-ixp-routing/explicit | 616 | 25,834 | 95,430 | 2,412,133 | 2,534,013 | $1.4709 |
| skill-flow-ixp-routing/invoice-extraction | 616 | 21,386 | 88,465 | 1,617,844 | 1,728,311 | $1.1397 |
| skill-flow-ixp-routing/receipts | 594 | 5,789 | 50,290 | 921,768 | 978,441 | $0.5537 |
| skill-flow-ixp-routing/contracts | 614 | 24,394 | 99,209 | 3,019,772 | 3,143,989 | $1.6457 |
| skill-flow-ixp-routing/forms-classify | 594 | 31,463 | 178,142 | 876,838 | 1,087,037 | $1.4048 |
| skill-flow-slack-channel-description | 502 | 13,480 | 83,800 | 2,440,146 | 2,537,928 | $1.2500 |
| skill-flow-transform-group-by | 892 | 5,337 | 47,738 | 499,834 | 553,801 | $0.4117 |
| skill-flow-ipe-enum | 575 | 17,275 | 81,110 | 1,708,480 | 1,807,440 | $1.0776 |
| skill-flow-interactive-customer-escalation-triage | 1,277 | 16,764 | 51,183 | 943,976 | 1,013,200 | $0.7452 |
| skill-flow-add-output | 470 | 1,505 | 36,114 | 270,588 | 308,677 | $0.2406 |
| skill-flow-rpa | 496 | 6,695 | 56,482 | 1,052,832 | 1,116,505 | $0.6296 |
| skill-flow-feet-inches | 590 | 13,464 | 55,833 | 799,893 | 869,780 | $0.6531 |
| skill-flow-summarize | 981 | 9,557 | 72,932 | 909,326 | 992,796 | $0.6926 |
| skill-flow-devcon-billing-dispute-analyst | 1,534 | 24,190 | 93,556 | 3,535,786 | 3,655,066 | $1.7790 |
| skill-flow-ixp-invoice-extraction-simulated | 1,088 | 31,807 | 114,326 | 1,600,405 | 1,747,626 | $1.4099 |
| skill-flow-hitl-quality-brownfield-insert | 659 | 26,833 | 69,931 | 1,106,036 | 1,203,459 | $0.9985 |
| skill-flow-registry-discovery | 570 | 1,900 | 20,823 | 227,363 | 250,656 | $0.1765 |
| skill-flow-ixp-routing-negative/stripe-http | 595 | 3,535 | 56,179 | 699,486 | 759,795 | $0.4753 |
| skill-flow-ixp-routing-negative/slack-summary | 589 | 5,477 | 52,626 | 1,055,891 | 1,114,583 | $0.5980 |
| skill-flow-ixp-routing-negative/sf-update | 585 | 16,763 | 60,050 | 573,751 | 651,149 | $0.6505 |
| skill-flow-ixp-routing-negative/http-webhook | 593 | 4,743 | 52,484 | 937,138 | 994,958 | $0.5509 |
| skill-flow-ixp-routing-negative/gsheet-loop | 590 | 8,540 | 66,270 | 852,854 | 928,254 | $0.6342 |
| skill-flow-ixp-routing-negative/queue-write | 594 | 6,410 | 48,791 | 1,239,692 | 1,295,487 | $0.6528 |
| skill-flow-ixp-routing-negative/teams-decision | 592 | 6,013 | 51,591 | 1,171,068 | 1,229,264 | $0.6368 |
| skill-flow-ixp-routing-negative/delay-email | 587 | 21,455 | 68,855 | 610,056 | 700,953 | $0.7648 |
| skill-flow-remove-node | 470 | 8,418 | 49,503 | 430,920 | 489,311 | $0.4426 |
| skill-flow-calculator | 481 | 4,307 | 44,542 | 547,556 | 596,886 | $0.3973 |
| skill-flow-move-node | 511 | 15,358 | 49,845 | 305,362 | 371,076 | $0.5104 |
| skill-flow-devcon-billing-resolution-writer | 638 | 12,588 | 81,351 | 823,031 | 917,608 | $0.7427 |
| skill-flow-add-node | 499 | 5,276 | 52,246 | 601,491 | 659,512 | $0.4570 |
| skill-flow-devcon-billing-invoice-lookup | 654 | 30,171 | 90,100 | 1,682,557 | 1,803,482 | $1.2972 |
| skill-flow-ipe-jira-create-issue | 618 | 20,367 | 79,709 | 1,223,003 | 1,323,697 | $0.9732 |
| skill-flow-eval-evaluator-type-choice | 990 | 4,313 | 32,806 | 622,571 | 660,680 | $0.3775 |
| skill-flow-batch-transform | 917 | 8,524 | 65,479 | 830,861 | 905,781 | $0.6254 |
| skill-flow-ipe-jira-lifecycle | 741 | 35,256 | 121,847 | 2,809,073 | 2,966,917 | $1.8307 |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 605 | 15,288 | 109,661 | 2,681,669 | 2,807,223 | $1.4469 |
| skill-flow-ipe-multiselect | 461 | 7,607 | 71,906 | 763,224 | 843,198 | $0.6141 |
| skill-flow-bindings-idempotent-reconfigure | 616 | 21,501 | 75,142 | 2,462,185 | 2,559,444 | $1.3448 |
| skill-flow-non-catalog-http-fallback | 545 | 11,362 | 68,362 | 1,563,942 | 1,644,211 | $0.8976 |
| skill-flow-dice-roller | 482 | 3,673 | 49,788 | 826,566 | 880,509 | $0.4912 |
| skill-flow-transform-filter | 854 | 20,642 | 59,764 | 1,013,418 | 1,094,678 | $0.8403 |
| skill-flow-ipe-enhanced-enum | 553 | 14,309 | 60,545 | 944,258 | 1,019,665 | $0.7266 |
| skill-flow-group-to-subflow | 500 | 33,298 | 120,765 | 454,520 | 609,083 | $1.0902 |
| skill-flow-slack-channel-description-simulated | 677 | 14,663 | 105,285 | 3,435,397 | 3,556,022 | $1.6528 |
| skill-flow-e2e-escalation-orchestrator-paths | 1,252 | 53,682 | 111,547 | 3,472,052 | 3,638,533 | $2.2689 |
| skill-flow-scheduled-trigger | 951 | 8,653 | 48,909 | 1,133,557 | 1,192,070 | $0.6561 |
| skill-flow-devcon-billing-discrepancy-detector | 859 | 20,565 | 103,592 | 1,913,939 | 2,038,955 | $1.2737 |
| skill-flow-e2e-devcon-expense-approval | 684 | 34,238 | 63,565 | 1,221,396 | 1,319,883 | $1.1204 |
| skill-flow-ixp-integration-handle-routing | 795 | 24,239 | 90,467 | 2,101,470 | 2,216,971 | $1.3357 |
| skill-flow-openmeteo-weather | 547 | 5,678 | 82,123 | 734,975 | 823,323 | $0.6153 |
| skill-flow-slack-weather-pipeline | 624 | 33,023 | 107,165 | 2,837,050 | 2,977,862 | $1.7502 |
| skill-flow-generic-dynamic-node | 11,259 | 7,771 | 86,823 | 2,000,426 | 2,106,279 | $1.0761 |
| skill-flow-ipe-searchable-joins | 507 | 17,846 | 99,848 | 1,327,760 | 1,445,961 | $1.0420 |
| skill-flow-hitl-quality-result-downstream | 658 | 27,120 | 69,347 | 1,283,624 | 1,380,749 | $1.0539 |
| skill-flow-init-validate | 555 | 2,996 | 31,470 | 375,587 | 410,608 | $0.2773 |
| skill-flow-outlook-waitfor-email | 547 | 5,478 | 75,348 | 1,090,432 | 1,171,805 | $0.6935 |
| skill-flow-switch | 543 | 12,883 | 46,639 | 628,919 | 688,984 | $0.5584 |
| skill-flow-ixp-scaffold-minimal | 11,297 | 44,283 | 120,833 | 658,255 | 834,668 | $1.3487 |
| skill-flow-delay | 715 | 5,911 | 63,553 | 1,316,007 | 1,386,186 | $0.7239 |
| skill-flow-eval-inline-agent | 1,068 | 20,459 | 73,914 | 727,777 | 823,218 | $0.8056 |
| skill-flow-hitl-smoke-multi-outcome-routing | 633 | 30,380 | 69,242 | 874,580 | 974,835 | $0.9796 |
| skill-flow-ipe-drive-to-slack | 607 | 12,344 | 104,928 | 2,610,367 | 2,728,246 | $1.3636 |
| skill-flow-loop-multiply | 495 | 49,714 | 114,339 | 1,168,069 | 1,332,617 | $1.5264 |
| skill-flow-ixp-e2e-project-selection/aviation | 608 | 16,475 | 58,938 | 1,164,092 | 1,240,113 | $0.8192 |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 603 | 16,667 | 67,314 | 1,870,607 | 1,955,191 | $1.0654 |


## Command Telemetry

**Total Commands**: 2746
**Success Rate**: 2628/2746 (95.7%)

### Commands by Tool

| Tool | Count | % |
|------|-------|---|
| Bash | 1704 | 62.1% |
| Read | 737 | 26.8% |
| Skill | 127 | 4.6% |
| Edit | 90 | 3.3% |
| Glob | 39 | 1.4% |
| Write | 36 | 1.3% |
| Grep | 7 | 0.3% |
| TaskUpdate | 4 | 0.1% |
| TaskCreate | 2 | 0.1% |

### Performance

- **Average Command Time**: 5023.7ms
- **Total Command Time**: 13795.08s

### Slowest Commands

| Tool | Duration | Parameters |
|------|----------|------------|
| Bash | 120039ms | {'command': 'python3 3<<\'PYEOF\'\nimport json\n\n... |
| Bash | 102943ms | {'command': 'uip maestro flow registry get core.lo... |
| Bash | 92764ms | {'command': 'uip maestro flow registry get core.ac... |
| Bash | 83355ms | {'command': 'uip maestro flow registry get core.co... |
| Bash | 82709ms | {'command': 'uip maestro flow registry get core.tr... |

**Most Common Pattern**: `Bash → Bash → Bash`

**Skill Tool Invoked**: 127 time(s)

## Agent Settings

- **Permission Mode**: acceptEdits
- **Allowed Tools**: Skill, Bash, Read, Write, Edit, Glob, Grep
- **Model**: us.anthropic.claude-sonnet-4-6
- **Max Turns**: 120
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