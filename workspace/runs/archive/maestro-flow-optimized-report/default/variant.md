# Variant Report: default

**Experiment**: skill-tests-smoke
**Description**: Linux PR-gate smoke tests — docker isolation, fast turn budget

## Summary

- **Tasks Run**: 123
- **Succeeded**: 111
- **Failed**: 12
- **Errors**: 0
- **Success Rate**: 90.2%
- **Average Score**: 0.949
- **Average Duration**: 329.4s
- **Total Tokens**: 156,334,278
- **Score Stddev**: 0.159
- **Duration Stddev**: 231.1s

## Task Details

| Task | Score | Status | Avg Duration |
|------|-------|--------|--------------|
| skill-flow-non-catalog-http-fallback | 1.000 | SUCCESS | 299.4s |
| skill-flow-bindings-idempotent-reconfigure | 1.000 | SUCCESS | 330.6s |
| skill-flow-outlook-trigger-inbox | 1.000 | SUCCESS | 291.3s |
| skill-flow-decision | 1.000 | SUCCESS | 326.3s |
| skill-flow-add-output | 1.000 | SUCCESS | 76.5s |
| skill-flow-openmeteo-weather | 1.000 | SUCCESS | 244.0s |
| skill-flow-calculator | 1.000 | SUCCESS | 203.6s |
| skill-flow-hitl-smoke-multi-outcome-routing | 1.000 | SUCCESS | 224.0s |
| skill-flow-hitl-schema-design-simulated | 0.895 | SUCCESS | 550.2s |
| skill-flow-wiki-pageviews | 0.615 | FAILURE | 894.7s |
| skill-flow-ipe-jira-search-triage | 0.286 | FAILURE | 427.8s |
| skill-flow-bindings-multi-connector-independence | 1.000 | SUCCESS | 192.7s |
| skill-flow-hitl-quality-boolean-decision | 1.000 | SUCCESS | 305.0s |
| skill-flow-ipe-enhanced-enum | 1.000 | SUCCESS | 460.6s |
| skill-flow-devcon-billing-discrepancy-detector | 0.375 | FAILURE | 680.2s |
| skill-flow-outlook-waitfor-email | 1.000 | SUCCESS | 289.9s |
| skill-flow-eval-inline-agent | 1.000 | SUCCESS | 422.9s |
| skill-flow-api-workflow | 1.000 | SUCCESS | 305.3s |
| skill-flow-bellevue-weather | 1.000 | SUCCESS | 444.2s |
| skill-flow-ipe-complex-array | 1.000 | SUCCESS | 627.7s |
| skill-flow-hitl-quality-brownfield-insert | 1.000 | SUCCESS | 398.0s |
| skill-flow-ipe-enum | 1.000 | SUCCESS | 563.4s |
| skill-flow-ixp-scaffold-multinode | 1.000 | SUCCESS | 451.0s |
| skill-flow-add-node | 1.000 | SUCCESS | 141.5s |
| skill-flow-ipe-dtl-load-by-default-true | 1.000 | SUCCESS | 230.0s |
| skill-flow-cli-dice-roller-simulated | 1.000 | SUCCESS | 415.6s |
| skill-flow-customer-escalation-simulated | 1.000 | SUCCESS | 1336.9s |
| skill-flow-transform-group-by | 1.000 | SUCCESS | 172.3s |
| skill-flow-registry-discovery | 1.000 | SUCCESS | 83.2s |
| skill-flow-scheduled-trigger | 1.000 | SUCCESS | 176.8s |
| skill-flow-inline-agent-robust | 1.000 | SUCCESS | 310.9s |
| skill-flow-slack-http-fallback | 1.000 | SUCCESS | 282.3s |
| skill-flow-solution-select-ask | 0.714 | FAILURE | 123.5s |
| skill-flow-batch-transform | 1.000 | SUCCESS | 200.6s |
| skill-flow-group-to-subflow | 1.000 | SUCCESS | 736.2s |
| skill-flow-lowcode-agent | 1.000 | SUCCESS | 274.7s |
| skill-flow-ipe-drive-to-slack | 1.000 | SUCCESS | 352.5s |
| skill-flow-eval-evaluator-type-choice | 1.000 | SUCCESS | 112.3s |
| skill-flow-coded-agent | 0.375 | MAX_TURNS_EXHAUSTED | 445.9s |
| skill-flow-hitl-quality-schema-design | 1.000 | SUCCESS | 357.3s |
| skill-flow-expense-approval-simulated | 1.000 | SUCCESS | 495.7s |
| skill-flow-bindings-reconfigure-different-connection | 1.000 | SUCCESS | 330.2s |
| skill-flow-slack-channel-description | 1.000 | SUCCESS | 329.9s |
| skill-flow-ipe-jira-get-issue | 1.000 | SUCCESS | 364.3s |
| skill-flow-remove-node | 1.000 | SUCCESS | 102.4s |
| skill-flow-delay | 1.000 | SUCCESS | 166.5s |
| skill-flow-ixp-scaffold-minimal | 1.000 | SUCCESS | 445.7s |
| skill-flow-ipe-jira-create-issue | 1.000 | SUCCESS | 290.8s |
| skill-flow-devcon-billing-dispute-analyst | 0.375 | FAILURE | 394.0s |
| skill-flow-transform-filter | 1.000 | SUCCESS | 197.8s |
| skill-flow-transform-map | 1.000 | SUCCESS | 187.2s |
| skill-flow-feet-inches | 1.000 | SUCCESS | 626.0s |
| skill-flow-summarize | 1.000 | SUCCESS | 203.6s |
| skill-flow-update-node | 1.000 | SUCCESS | 75.7s |
| skill-flow-eval-simulation-crud | 1.000 | SUCCESS | 127.0s |
| skill-flow-slack-channel-description-simulated | 0.500 | FAILURE | 764.0s |
| skill-flow-multi-city-weather | 1.000 | SUCCESS | 559.2s |
| skill-flow-ipe-dtl-load-by-default-false | 1.000 | SUCCESS | 304.8s |
| skill-flow-devcon-billing-dispute-resolution | 0.500 | FAILURE | 770.4s |
| skill-flow-webhook-waitfor-parallel | 1.000 | SUCCESS | 257.4s |
| skill-flow-e2e-devcon-expense-approval | 1.000 | SUCCESS | 365.1s |
| skill-flow-generic-dynamic-node | 0.429 | FAILURE | 566.3s |
| skill-flow-ixp-routing/explicit | 1.000 | SUCCESS | 446.4s |
| skill-flow-ixp-routing/invoice-extraction | 1.000 | SUCCESS | 332.8s |
| skill-flow-ixp-routing/receipts | 1.000 | SUCCESS | 238.1s |
| skill-flow-ixp-routing/contracts | 1.000 | SUCCESS | 262.5s |
| skill-flow-ixp-routing/forms-classify | 1.000 | SUCCESS | 551.7s |
| skill-flow-slack-weather-pipeline | 0.375 | MAX_TURNS_EXHAUSTED | 567.4s |
| skill-flow-merge-parallel-sync | 1.000 | SUCCESS | 156.5s |
| skill-flow-ipe-multiselect | 1.000 | SUCCESS | 384.3s |
| skill-flow-subflow | 1.000 | SUCCESS | 213.3s |
| skill-flow-ipe-path-params | 1.000 | SUCCESS | 224.1s |
| skill-flow-devcon-billing-resolution-writer | 1.000 | SUCCESS | 285.6s |
| skill-flow-terminate | 1.000 | SUCCESS | 380.4s |
| skill-flow-ixp-integration-handle-routing | 1.000 | SUCCESS | 273.8s |
| skill-flow-hitl-smoke-node-placed | 1.000 | SUCCESS | 210.9s |
| skill-flow-ipe-query-params | 1.000 | SUCCESS | 173.2s |
| skill-flow-hitl-quality-result-downstream | 1.000 | SUCCESS | 155.1s |
| skill-flow-customer-escalation | 1.000 | SUCCESS | 417.6s |
| skill-flow-rpa | 1.000 | SUCCESS | 278.5s |
| skill-flow-ipe-jira-lifecycle | 1.000 | SUCCESS | 556.5s |
| skill-flow-reading-list | 1.000 | SUCCESS | 232.3s |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 1.000 | SUCCESS | 422.4s |
| skill-flow-eval-no-auto-upload | 1.000 | SUCCESS | 170.4s |
| skill-flow-init-validate | 1.000 | SUCCESS | 100.7s |
| skill-flow-bellevue-weather-simulated | 1.000 | SUCCESS | 901.3s |
| skill-flow-devcon-billing-invoice-lookup | 1.000 | SUCCESS | 562.3s |
| skill-flow-ipe-ceql-where | 1.000 | SUCCESS | 435.8s |
| skill-flow-ipe-searchable-joins | 1.000 | SUCCESS | 370.9s |
| skill-flow-eval-local-crud | 1.000 | SUCCESS | 103.6s |
| skill-flow-trigger-with-filter | 1.000 | SUCCESS | 83.4s |
| skill-flow-loop-multiply | 1.000 | SUCCESS | 359.9s |
| skill-flow-ixp-routing-negative/stripe-http | 1.000 | SUCCESS | 257.6s |
| skill-flow-ixp-routing-negative/slack-summary | 1.000 | SUCCESS | 183.9s |
| skill-flow-ixp-routing-negative/sf-update | 1.000 | SUCCESS | 268.0s |
| skill-flow-ixp-routing-negative/http-webhook | 1.000 | SUCCESS | 238.6s |
| skill-flow-ixp-routing-negative/gsheet-loop | 1.000 | SUCCESS | 305.5s |
| skill-flow-ixp-routing-negative/queue-write | 1.000 | SUCCESS | 175.1s |
| skill-flow-ixp-routing-negative/teams-decision | 1.000 | SUCCESS | 238.3s |
| skill-flow-ixp-routing-negative/delay-email | 1.000 | SUCCESS | 390.8s |
| skill-flow-ixp-invoice-extraction-simulated | 0.900 | SUCCESS | 1560.4s |
| skill-flow-dice-roller | 1.000 | SUCCESS | 178.8s |
| skill-flow-ipe-required-groups | 1.000 | SUCCESS | 359.2s |
| skill-flow-move-node | 1.000 | SUCCESS | 373.1s |
| skill-flow-paginated-reference-lookup | 0.880 | FAILURE | 297.8s |
| skill-flow-file-attachment-debug | 1.000 | SUCCESS | 255.7s |
| skill-flow-bindings-no-duplicates | 1.000 | SUCCESS | 328.6s |
| skill-flow-ixp-routing-listing/r01 | 0.500 | FAILURE | 35.0s |
| skill-flow-ixp-routing-listing/r02 | 1.000 | SUCCESS | 68.9s |
| skill-flow-ixp-routing-listing/r03 | 1.000 | SUCCESS | 54.2s |
| skill-flow-ixp-routing-listing/r04 | 1.000 | SUCCESS | 63.1s |
| skill-flow-ixp-routing-listing/r05 | 1.000 | SUCCESS | 62.6s |
| skill-flow-ixp-routing-listing/r06 | 1.000 | SUCCESS | 52.4s |
| skill-flow-ixp-routing-listing/r07 | 1.000 | SUCCESS | 59.5s |
| skill-flow-ixp-routing-listing/r08 | 1.000 | SUCCESS | 48.2s |
| skill-flow-ixp-routing-listing/r09 | 1.000 | SUCCESS | 57.6s |
| skill-flow-ixp-routing-listing/r10 | 1.000 | SUCCESS | 52.4s |
| skill-flow-ixp-e2e-project-selection/aviation | 1.000 | SUCCESS | 300.9s |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 1.000 | SUCCESS | 314.4s |
| skill-flow-ipe-generate-schema | 1.000 | SUCCESS | 359.4s |
| skill-flow-hitl-smoke-completed-port | 1.000 | SUCCESS | 177.8s |
| skill-flow-interactive-customer-escalation-triage | 1.000 | SUCCESS | 465.7s |
| skill-flow-switch | 1.000 | SUCCESS | 391.5s |


## Generation Metrics

| Task ID | Total Latency | Turns | Asst Turns | Avg Turn Latency |
|---------|---------------|-------|------------|------------------|
| skill-flow-non-catalog-http-fallback | 299.4s | 1 | 56 | 289.2s |
| skill-flow-bindings-idempotent-reconfigure | 330.6s | 1 | 48 | 326.4s |
| skill-flow-outlook-trigger-inbox | 291.3s | 1 | 45 | 281.0s |
| skill-flow-decision | 326.3s | 1 | 26 | 272.1s |
| skill-flow-add-output | 76.5s | 1 | 13 | 39.6s |
| skill-flow-openmeteo-weather | 244.0s | 1 | 40 | 217.3s |
| skill-flow-calculator | 203.6s | 1 | 25 | 169.1s |
| skill-flow-hitl-smoke-multi-outcome-routing | 224.0s | 1 | 35 | 211.3s |
| skill-flow-hitl-schema-design-simulated | 550.2s | 5 | 59 | 91.7s |
| skill-flow-wiki-pageviews | 894.7s | 1 | 39 | 831.1s |
| skill-flow-ipe-jira-search-triage | 427.8s | 1 | 31 | 383.4s |
| skill-flow-bindings-multi-connector-independence | 192.7s | 1 | 50 | 188.6s |
| skill-flow-hitl-quality-boolean-decision | 305.0s | 1 | 57 | 296.2s |
| skill-flow-ipe-enhanced-enum | 460.6s | 1 | 58 | 456.7s |
| skill-flow-devcon-billing-discrepancy-detector | 680.2s | 1 | 80 | 647.3s |
| skill-flow-outlook-waitfor-email | 289.9s | 1 | 41 | 283.0s |
| skill-flow-eval-inline-agent | 422.9s | 1 | 32 | 419.5s |
| skill-flow-api-workflow | 305.3s | 1 | 38 | 268.6s |
| skill-flow-bellevue-weather | 444.2s | 1 | 45 | 400.8s |
| skill-flow-ipe-complex-array | 627.7s | 1 | 46 | 625.0s |
| skill-flow-hitl-quality-brownfield-insert | 398.0s | 1 | 33 | 384.4s |
| skill-flow-ipe-enum | 563.4s | 1 | 41 | 558.9s |
| skill-flow-ixp-scaffold-multinode | 451.0s | 1 | 39 | 442.5s |
| skill-flow-add-node | 141.5s | 1 | 21 | 100.9s |
| skill-flow-ipe-dtl-load-by-default-true | 230.0s | 1 | 41 | 220.0s |
| skill-flow-cli-dice-roller-simulated | 415.6s | 6 | 44 | 52.7s |
| skill-flow-customer-escalation-simulated | 1336.9s | 7 | 105 | 175.7s |
| skill-flow-transform-group-by | 172.3s | 1 | 24 | 163.9s |
| skill-flow-registry-discovery | 83.2s | 1 | 17 | 73.3s |
| skill-flow-scheduled-trigger | 176.8s | 1 | 29 | 168.9s |
| skill-flow-inline-agent-robust | 310.9s | 1 | 43 | 308.9s |
| skill-flow-slack-http-fallback | 282.3s | 1 | 50 | 257.5s |
| skill-flow-solution-select-ask | 123.5s | 3 | 24 | 35.2s |
| skill-flow-batch-transform | 200.6s | 1 | 28 | 185.4s |
| skill-flow-group-to-subflow | 736.2s | 1 | 25 | 707.2s |
| skill-flow-lowcode-agent | 274.7s | 1 | 39 | 233.6s |
| skill-flow-ipe-drive-to-slack | 352.5s | 1 | 60 | 348.2s |
| skill-flow-eval-evaluator-type-choice | 112.3s | 1 | 16 | 109.5s |
| skill-flow-coded-agent | 445.9s | 1 | 80 | 419.8s |
| skill-flow-hitl-quality-schema-design | 357.3s | 1 | 46 | 347.9s |
| skill-flow-expense-approval-simulated | 495.7s | 5 | 47 | 78.5s |
| skill-flow-bindings-reconfigure-different-connection | 330.2s | 1 | 46 | 321.3s |
| skill-flow-slack-channel-description | 329.9s | 1 | 59 | 303.2s |
| skill-flow-ipe-jira-get-issue | 364.3s | 1 | 59 | 330.5s |
| skill-flow-remove-node | 102.4s | 1 | 28 | 71.8s |
| skill-flow-delay | 166.5s | 1 | 31 | 158.2s |
| skill-flow-ixp-scaffold-minimal | 445.7s | 1 | 47 | 429.5s |
| skill-flow-ipe-jira-create-issue | 290.8s | 1 | 39 | 250.5s |
| skill-flow-devcon-billing-dispute-analyst | 394.0s | 1 | 54 | 326.2s |
| skill-flow-transform-filter | 197.8s | 1 | 21 | 182.7s |
| skill-flow-transform-map | 187.2s | 1 | 35 | 180.6s |
| skill-flow-feet-inches | 626.0s | 1 | 54 | 590.0s |
| skill-flow-summarize | 203.6s | 1 | 25 | 197.4s |
| skill-flow-update-node | 75.7s | 1 | 11 | 38.5s |
| skill-flow-eval-simulation-crud | 127.0s | 1 | 12 | 123.9s |
| skill-flow-slack-channel-description-simulated | 764.0s | 6 | 86 | 73.3s |
| skill-flow-multi-city-weather | 559.2s | 1 | 48 | 505.2s |
| skill-flow-ipe-dtl-load-by-default-false | 304.8s | 1 | 55 | 294.7s |
| skill-flow-devcon-billing-dispute-resolution | 770.4s | 1 | 129 | 731.3s |
| skill-flow-webhook-waitfor-parallel | 257.4s | 1 | 46 | 254.3s |
| skill-flow-e2e-devcon-expense-approval | 365.1s | 1 | 28 | 354.5s |
| skill-flow-generic-dynamic-node | 566.3s | 1 | 81 | 528.6s |
| skill-flow-ixp-routing/explicit | 446.4s | 1 | 73 | 441.0s |
| skill-flow-ixp-routing/invoice-extraction | 332.8s | 1 | 62 | 326.7s |
| skill-flow-ixp-routing/receipts | 238.1s | 1 | 47 | 232.6s |
| skill-flow-ixp-routing/contracts | 262.5s | 1 | 37 | 258.1s |
| skill-flow-ixp-routing/forms-classify | 551.7s | 1 | 92 | 546.8s |
| skill-flow-slack-weather-pipeline | 567.4s | 1 | 71 | 506.4s |
| skill-flow-merge-parallel-sync | 156.5s | 1 | 33 | 140.7s |
| skill-flow-ipe-multiselect | 384.3s | 1 | 48 | 382.3s |
| skill-flow-subflow | 213.3s | 1 | 26 | 187.8s |
| skill-flow-ipe-path-params | 224.1s | 1 | 40 | 218.2s |
| skill-flow-devcon-billing-resolution-writer | 285.6s | 1 | 26 | 224.8s |
| skill-flow-terminate | 380.4s | 1 | 44 | 357.5s |
| skill-flow-ixp-integration-handle-routing | 273.8s | 1 | 44 | 265.7s |
| skill-flow-hitl-smoke-node-placed | 210.9s | 1 | 23 | 203.3s |
| skill-flow-ipe-query-params | 173.2s | 1 | 36 | 169.8s |
| skill-flow-hitl-quality-result-downstream | 155.1s | 1 | 18 | 140.4s |
| skill-flow-customer-escalation | 417.6s | 1 | 63 | 403.6s |
| skill-flow-rpa | 278.5s | 1 | 41 | 174.3s |
| skill-flow-ipe-jira-lifecycle | 556.5s | 1 | 34 | 490.8s |
| skill-flow-reading-list | 232.3s | 1 | 30 | 203.8s |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 422.4s | 1 | 78 | 412.5s |
| skill-flow-eval-no-auto-upload | 170.4s | 1 | 23 | 160.7s |
| skill-flow-init-validate | 100.7s | 1 | 20 | 98.2s |
| skill-flow-bellevue-weather-simulated | 901.3s | 5 | 72 | 159.4s |
| skill-flow-devcon-billing-invoice-lookup | 562.3s | 1 | 51 | 483.9s |
| skill-flow-ipe-ceql-where | 435.8s | 1 | 38 | 425.8s |
| skill-flow-ipe-searchable-joins | 370.9s | 1 | 53 | 365.1s |
| skill-flow-eval-local-crud | 103.6s | 1 | 16 | 101.1s |
| skill-flow-trigger-with-filter | 83.4s | 1 | 11 | 73.6s |
| skill-flow-loop-multiply | 359.9s | 1 | 25 | 317.5s |
| skill-flow-ixp-routing-negative/stripe-http | 257.6s | 1 | 33 | 254.4s |
| skill-flow-ixp-routing-negative/slack-summary | 183.9s | 1 | 29 | 180.5s |
| skill-flow-ixp-routing-negative/sf-update | 268.0s | 1 | 49 | 265.3s |
| skill-flow-ixp-routing-negative/http-webhook | 238.6s | 1 | 47 | 236.7s |
| skill-flow-ixp-routing-negative/gsheet-loop | 305.5s | 1 | 35 | 301.4s |
| skill-flow-ixp-routing-negative/queue-write | 175.1s | 1 | 44 | 172.0s |
| skill-flow-ixp-routing-negative/teams-decision | 238.3s | 1 | 27 | 235.6s |
| skill-flow-ixp-routing-negative/delay-email | 390.8s | 1 | 37 | 388.1s |
| skill-flow-ixp-invoice-extraction-simulated | 1560.4s | 5 | 146 | 290.9s |
| skill-flow-dice-roller | 178.8s | 1 | 21 | 152.6s |
| skill-flow-ipe-required-groups | 359.2s | 1 | 43 | 349.3s |
| skill-flow-move-node | 373.1s | 1 | 10 | 220.9s |
| skill-flow-paginated-reference-lookup | 297.8s | 1 | 54 | 291.0s |
| skill-flow-file-attachment-debug | 255.7s | 1 | 32 | 228.4s |
| skill-flow-bindings-no-duplicates | 328.6s | 1 | 47 | 322.7s |
| skill-flow-ixp-routing-listing/r01 | 35.0s | 1 | 9 | 31.6s |
| skill-flow-ixp-routing-listing/r02 | 68.9s | 1 | 14 | 64.4s |
| skill-flow-ixp-routing-listing/r03 | 54.2s | 1 | 8 | 48.8s |
| skill-flow-ixp-routing-listing/r04 | 63.1s | 1 | 11 | 58.4s |
| skill-flow-ixp-routing-listing/r05 | 62.6s | 1 | 13 | 58.3s |
| skill-flow-ixp-routing-listing/r06 | 52.4s | 1 | 8 | 49.2s |
| skill-flow-ixp-routing-listing/r07 | 59.5s | 1 | 17 | 56.9s |
| skill-flow-ixp-routing-listing/r08 | 48.2s | 1 | 8 | 43.0s |
| skill-flow-ixp-routing-listing/r09 | 57.6s | 1 | 10 | 50.8s |
| skill-flow-ixp-routing-listing/r10 | 52.4s | 1 | 13 | 46.7s |
| skill-flow-ixp-e2e-project-selection/aviation | 300.9s | 1 | 50 | 293.2s |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 314.4s | 1 | 62 | 306.1s |
| skill-flow-ipe-generate-schema | 359.4s | 1 | 61 | 349.8s |
| skill-flow-hitl-smoke-completed-port | 177.8s | 1 | 34 | 168.1s |
| skill-flow-interactive-customer-escalation-triage | 465.7s | 5 | 44 | 50.1s |
| skill-flow-switch | 391.5s | 1 | 40 | 372.0s |


## Token Usage

**Total Tokens**: 156,334,278 (input: 46,745, output: 2,022,391)
**Cache Tokens**: write: 8,457,246, read: 145,807,896
**Total Cost**: $105.9331
**Avg Tokens/Task**: 1,271,010

| Task ID | Input (uncached) | Output | Cache Write | Cache Read | Total | Cost |
|---------|------------------|--------|-------------|------------|-------|------|
| skill-flow-non-catalog-http-fallback | 30 | 13,142 | 66,477 | 1,659,967 | 1,739,616 | $0.9445 |
| skill-flow-bindings-idempotent-reconfigure | 23 | 16,118 | 72,378 | 1,497,119 | 1,585,638 | $0.9624 |
| skill-flow-outlook-trigger-inbox | 19 | 13,832 | 83,762 | 1,055,339 | 1,152,952 | $0.8382 |
| skill-flow-decision | 11 | 15,725 | 62,131 | 485,285 | 563,152 | $0.6145 |
| skill-flow-add-output | 477 | 2,229 | 29,691 | 281,811 | 314,208 | $0.2308 |
| skill-flow-openmeteo-weather | 17 | 10,889 | 70,942 | 998,379 | 1,080,227 | $0.7289 |
| skill-flow-calculator | 13 | 7,051 | 61,236 | 551,727 | 620,027 | $0.5010 |
| skill-flow-hitl-smoke-multi-outcome-routing | 20 | 10,120 | 47,689 | 819,816 | 877,645 | $0.5766 |
| skill-flow-hitl-schema-design-simulated | 46 | 26,706 | 53,732 | 1,866,692 | 1,947,176 | $1.1622 |
| skill-flow-wiki-pageviews | 18 | 52,398 | 83,694 | 1,162,094 | 1,298,204 | $1.4485 |
| skill-flow-ipe-jira-search-triage | 13 | 23,649 | 88,460 | 694,829 | 806,951 | $0.8949 |
| skill-flow-bindings-multi-connector-independence | 24 | 7,739 | 78,134 | 1,598,742 | 1,684,639 | $0.8888 |
| skill-flow-hitl-quality-boolean-decision | 40 | 16,564 | 55,092 | 1,945,626 | 2,017,322 | $1.0389 |
| skill-flow-ipe-enhanced-enum | 26 | 25,554 | 72,984 | 1,727,089 | 1,825,653 | $1.1752 |
| skill-flow-devcon-billing-discrepancy-detector | 32 | 35,750 | 116,621 | 2,844,599 | 2,997,002 | $1.8271 |
| skill-flow-outlook-waitfor-email | 17 | 13,320 | 80,163 | 949,830 | 1,043,330 | $0.7854 |
| skill-flow-eval-inline-agent | 13 | 27,831 | 75,862 | 745,884 | 849,590 | $0.9258 |
| skill-flow-api-workflow | 16 | 13,409 | 63,699 | 765,217 | 842,341 | $0.6696 |
| skill-flow-bellevue-weather | 19 | 24,850 | 64,484 | 1,076,823 | 1,166,176 | $0.9377 |
| skill-flow-ipe-complex-array | 17 | 38,138 | 91,219 | 1,101,368 | 1,230,742 | $1.2446 |
| skill-flow-hitl-quality-brownfield-insert | 17 | 23,015 | 63,286 | 858,275 | 944,593 | $0.8401 |
| skill-flow-ipe-enum | 15 | 34,983 | 147,225 | 777,328 | 959,551 | $1.3101 |
| skill-flow-ixp-scaffold-multinode | 17 | 24,709 | 69,455 | 903,110 | 997,291 | $0.9021 |
| skill-flow-add-node | 11 | 8,056 | 33,623 | 448,938 | 490,628 | $0.3816 |
| skill-flow-ipe-dtl-load-by-default-true | 15 | 9,144 | 68,101 | 754,556 | 831,816 | $0.6190 |
| skill-flow-cli-dice-roller-simulated | 31 | 13,157 | 66,874 | 1,025,595 | 1,105,657 | $0.7559 |
| skill-flow-customer-escalation-simulated | 19,891 | 72,284 | 271,829 | 3,409,774 | 3,773,778 | $3.1862 |
| skill-flow-transform-group-by | 11 | 9,215 | 48,300 | 420,947 | 478,473 | $0.4457 |
| skill-flow-registry-discovery | 9 | 2,776 | 35,714 | 247,067 | 285,566 | $0.2497 |
| skill-flow-scheduled-trigger | 15 | 9,350 | 58,170 | 739,207 | 806,742 | $0.5802 |
| skill-flow-inline-agent-robust | 21 | 16,381 | 64,638 | 1,245,748 | 1,326,788 | $0.8619 |
| skill-flow-slack-http-fallback | 1,832 | 10,191 | 96,928 | 1,463,088 | 1,572,039 | $0.9608 |
| skill-flow-solution-select-ask | 16 | 3,907 | 30,010 | 404,332 | 438,265 | $0.2925 |
| skill-flow-batch-transform | 12 | 9,405 | 57,022 | 513,175 | 579,614 | $0.5089 |
| skill-flow-group-to-subflow | 14 | 58,563 | 66,992 | 696,458 | 822,027 | $1.3386 |
| skill-flow-lowcode-agent | 19 | 12,690 | 51,307 | 960,447 | 1,024,463 | $0.6709 |
| skill-flow-ipe-drive-to-slack | 20 | 16,282 | 93,254 | 1,446,308 | 1,555,864 | $1.0279 |
| skill-flow-eval-evaluator-type-choice | 11 | 5,490 | 19,810 | 283,822 | 309,133 | $0.2418 |
| skill-flow-coded-agent | 43 | 22,068 | 118,608 | 3,025,838 | 3,166,557 | $1.6837 |
| skill-flow-hitl-quality-schema-design | 23 | 19,673 | 60,853 | 1,353,329 | 1,433,878 | $0.9294 |
| skill-flow-expense-approval-simulated | 38 | 23,948 | 48,626 | 1,317,470 | 1,390,082 | $0.9369 |
| skill-flow-bindings-reconfigure-different-connection | 27 | 16,441 | 74,361 | 1,814,763 | 1,905,592 | $1.0700 |
| skill-flow-slack-channel-description | 29 | 14,348 | 89,214 | 2,109,453 | 2,213,044 | $1.1827 |
| skill-flow-ipe-jira-get-issue | 27 | 15,798 | 92,232 | 2,175,802 | 2,283,859 | $1.2357 |
| skill-flow-remove-node | 16 | 5,116 | 36,039 | 731,745 | 772,916 | $0.4315 |
| skill-flow-delay | 14 | 8,239 | 42,392 | 592,344 | 642,989 | $0.4603 |
| skill-flow-ixp-scaffold-minimal | 26 | 24,733 | 60,902 | 1,579,336 | 1,664,997 | $1.0733 |
| skill-flow-ipe-jira-create-issue | 16 | 10,692 | 81,461 | 994,071 | 1,086,240 | $0.7641 |
| skill-flow-devcon-billing-dispute-analyst | 24 | 17,199 | 77,068 | 1,636,769 | 1,731,060 | $1.0381 |
| skill-flow-transform-filter | 10 | 9,406 | 47,798 | 365,561 | 422,775 | $0.4300 |
| skill-flow-transform-map | 15 | 9,844 | 50,448 | 688,830 | 749,137 | $0.5435 |
| skill-flow-feet-inches | 24 | 37,259 | 59,923 | 1,368,685 | 1,465,891 | $1.1943 |
| skill-flow-summarize | 12 | 10,776 | 58,832 | 488,274 | 557,894 | $0.5288 |
| skill-flow-update-node | 476 | 2,225 | 29,705 | 229,739 | 262,145 | $0.2151 |
| skill-flow-eval-simulation-crud | 9 | 6,239 | 25,646 | 215,049 | 246,943 | $0.2543 |
| skill-flow-slack-channel-description-simulated | 53 | 24,979 | 200,874 | 3,899,395 | 4,125,301 | $2.2979 |
| skill-flow-multi-city-weather | 24 | 27,799 | 64,096 | 1,417,292 | 1,509,211 | $1.0826 |
| skill-flow-ipe-dtl-load-by-default-false | 20 | 12,942 | 93,151 | 1,254,731 | 1,360,844 | $0.9199 |
| skill-flow-devcon-billing-dispute-resolution | 67 | 40,808 | 137,891 | 8,433,395 | 8,612,161 | $3.6594 |
| skill-flow-webhook-waitfor-parallel | 25 | 11,202 | 83,973 | 1,685,598 | 1,780,798 | $0.9887 |
| skill-flow-e2e-devcon-expense-approval | 13 | 23,503 | 68,611 | 592,815 | 684,942 | $0.7877 |
| skill-flow-generic-dynamic-node | 40 | 17,094 | 96,813 | 3,407,320 | 3,521,267 | $1.6418 |
| skill-flow-ixp-routing/explicit | 32 | 25,589 | 80,403 | 2,139,614 | 2,245,638 | $1.3273 |
| skill-flow-ixp-routing/invoice-extraction | 30 | 15,274 | 84,640 | 2,129,677 | 2,229,621 | $1.1855 |
| skill-flow-ixp-routing/receipts | 21 | 11,032 | 70,522 | 1,180,184 | 1,261,759 | $0.7841 |
| skill-flow-ixp-routing/contracts | 16 | 12,776 | 71,045 | 816,031 | 899,868 | $0.7029 |
| skill-flow-ixp-routing/forms-classify | 62 | 28,607 | 107,009 | 4,938,886 | 5,074,564 | $2.3122 |
| skill-flow-slack-weather-pipeline | 30 | 27,227 | 98,334 | 2,393,728 | 2,519,319 | $1.4954 |
| skill-flow-merge-parallel-sync | 12 | 6,181 | 56,061 | 537,219 | 599,473 | $0.4641 |
| skill-flow-ipe-multiselect | 19 | 21,621 | 79,327 | 1,205,148 | 1,306,115 | $0.9834 |
| skill-flow-subflow | 11 | 11,828 | 47,897 | 417,075 | 476,811 | $0.4822 |
| skill-flow-ipe-path-params | 18 | 10,220 | 68,449 | 1,010,671 | 1,089,358 | $0.7132 |
| skill-flow-devcon-billing-resolution-writer | 453 | 13,790 | 63,410 | 631,741 | 709,394 | $0.6355 |
| skill-flow-terminate | 20 | 21,391 | 61,191 | 998,090 | 1,080,692 | $0.8498 |
| skill-flow-ixp-integration-handle-routing | 21 | 13,820 | 60,637 | 1,156,191 | 1,230,669 | $0.7816 |
| skill-flow-hitl-smoke-node-placed | 13 | 11,423 | 53,824 | 500,728 | 565,988 | $0.5234 |
| skill-flow-ipe-query-params | 14 | 7,117 | 55,228 | 585,946 | 648,305 | $0.4897 |
| skill-flow-hitl-quality-result-downstream | 13 | 9,027 | 28,017 | 421,312 | 458,369 | $0.3669 |
| skill-flow-customer-escalation | 29 | 16,886 | 85,838 | 2,332,868 | 2,435,621 | $1.2751 |
| skill-flow-rpa | 17 | 9,356 | 59,700 | 855,799 | 924,872 | $0.6210 |
| skill-flow-ipe-jira-lifecycle | 14 | 27,127 | 84,681 | 845,680 | 957,502 | $0.9782 |
| skill-flow-reading-list | 15 | 9,345 | 65,395 | 811,083 | 885,838 | $0.6288 |
| skill-flow-ixp-e2e-invoice-extraction-greenfield | 30 | 18,216 | 113,930 | 2,791,987 | 2,924,163 | $1.5382 |
| skill-flow-eval-no-auto-upload | 14 | 7,416 | 23,801 | 467,782 | 499,013 | $0.3409 |
| skill-flow-init-validate | 9 | 4,288 | 28,728 | 267,516 | 300,541 | $0.2523 |
| skill-flow-bellevue-weather-simulated | 36 | 43,751 | 168,024 | 1,979,082 | 2,190,893 | $1.8802 |
| skill-flow-devcon-billing-invoice-lookup | 27 | 23,323 | 92,126 | 2,025,153 | 2,140,629 | $1.3029 |
| skill-flow-ipe-ceql-where | 20 | 23,984 | 82,809 | 1,334,742 | 1,441,555 | $1.0708 |
| skill-flow-ipe-searchable-joins | 20 | 20,536 | 70,739 | 1,222,240 | 1,313,535 | $0.9400 |
| skill-flow-eval-local-crud | 10 | 3,401 | 30,269 | 325,967 | 359,647 | $0.2623 |
| skill-flow-trigger-with-filter | 8 | 3,621 | 29,125 | 225,331 | 258,085 | $0.2312 |
| skill-flow-loop-multiply | 12 | 19,081 | 52,832 | 510,414 | 582,339 | $0.6375 |
| skill-flow-ixp-routing-negative/stripe-http | 12 | 15,276 | 60,040 | 512,433 | 587,761 | $0.6081 |
| skill-flow-ixp-routing-negative/slack-summary | 13 | 9,061 | 49,692 | 533,118 | 591,884 | $0.4822 |
| skill-flow-ixp-routing-negative/sf-update | 21 | 12,486 | 64,336 | 1,175,201 | 1,252,044 | $0.7812 |
| skill-flow-ixp-routing-negative/http-webhook | 27 | 9,524 | 62,310 | 1,545,750 | 1,617,611 | $0.8403 |
| skill-flow-ixp-routing-negative/gsheet-loop | 13 | 17,050 | 75,606 | 666,582 | 759,251 | $0.7393 |
| skill-flow-ixp-routing-negative/queue-write | 26 | 6,612 | 43,284 | 1,213,589 | 1,263,511 | $0.6256 |
| skill-flow-ixp-routing-negative/teams-decision | 13 | 13,624 | 48,806 | 513,957 | 576,400 | $0.5416 |
| skill-flow-ixp-routing-negative/delay-email | 16 | 23,831 | 54,831 | 751,896 | 830,574 | $0.7887 |
| skill-flow-ixp-invoice-extraction-simulated | 21,278 | 83,456 | 323,554 | 4,573,779 | 5,002,067 | $3.9011 |
| skill-flow-dice-roller | 12 | 7,594 | 42,874 | 400,979 | 451,459 | $0.3950 |
| skill-flow-ipe-required-groups | 16 | 17,206 | 61,708 | 776,486 | 855,416 | $0.7225 |
| skill-flow-move-node | 6 | 22,723 | 48,348 | 197,242 | 268,319 | $0.5813 |
| skill-flow-paginated-reference-lookup | 23 | 12,827 | 85,475 | 1,556,533 | 1,654,858 | $0.9800 |
| skill-flow-file-attachment-debug | 15 | 11,152 | 59,521 | 689,403 | 760,091 | $0.5973 |
| skill-flow-bindings-no-duplicates | 23 | 14,749 | 71,612 | 1,351,209 | 1,437,593 | $0.8952 |
| skill-flow-ixp-routing-listing/r01 | 7 | 1,182 | 6,320 | 160,889 | 168,398 | $0.0897 |
| skill-flow-ixp-routing-listing/r02 | 11 | 2,694 | 37,587 | 178,785 | 219,077 | $0.2350 |
| skill-flow-ixp-routing-listing/r03 | 9 | 2,993 | 22,527 | 121,876 | 147,405 | $0.1660 |
| skill-flow-ixp-routing-listing/r04 | 7 | 2,652 | 22,645 | 121,730 | 147,034 | $0.1612 |
| skill-flow-ixp-routing-listing/r05 | 10 | 2,039 | 37,444 | 258,367 | 297,860 | $0.2485 |
| skill-flow-ixp-routing-listing/r06 | 9 | 2,862 | 22,501 | 121,840 | 147,212 | $0.1639 |
| skill-flow-ixp-routing-listing/r07 | 13 | 2,354 | 36,989 | 367,163 | 406,519 | $0.2842 |
| skill-flow-ixp-routing-listing/r08 | 9 | 2,033 | 22,535 | 121,897 | 146,474 | $0.1516 |
| skill-flow-ixp-routing-listing/r09 | 9 | 2,487 | 23,568 | 178,280 | 204,344 | $0.1792 |
| skill-flow-ixp-routing-listing/r10 | 12 | 2,080 | 35,998 | 281,715 | 319,805 | $0.2507 |
| skill-flow-ixp-e2e-project-selection/aviation | 27 | 16,265 | 74,332 | 1,684,045 | 1,774,669 | $1.0280 |
| skill-flow-ixp-e2e-project-selection/birth-certificate | 33 | 15,607 | 67,646 | 2,023,078 | 2,106,364 | $1.0948 |
| skill-flow-ipe-generate-schema | 29 | 16,508 | 77,646 | 2,088,645 | 2,182,828 | $1.1655 |
| skill-flow-hitl-smoke-completed-port | 15 | 8,752 | 54,740 | 630,204 | 693,711 | $0.5257 |
| skill-flow-interactive-customer-escalation-triage | 27 | 14,991 | 73,164 | 1,262,455 | 1,350,637 | $0.8780 |
| skill-flow-switch | 19 | 25,524 | 55,111 | 886,870 | 967,524 | $0.8556 |


## Command Telemetry

**Total Commands**: 2903
**Success Rate**: 2763/2903 (95.2%)

### Commands by Tool

| Tool | Count | % |
|------|-------|---|
| Bash | 1713 | 59.0% |
| Read | 708 | 24.4% |
| Edit | 241 | 8.3% |
| Skill | 132 | 4.5% |
| Write | 71 | 2.4% |
| Glob | 17 | 0.6% |
| Grep | 12 | 0.4% |
| TaskUpdate | 5 | 0.2% |
| TaskCreate | 3 | 0.1% |
| TaskStop | 1 | 0.0% |

### Performance

- **Average Command Time**: 4225.9ms
- **Total Command Time**: 12267.91s

### Slowest Commands

| Tool | Duration | Parameters |
|------|----------|------------|
| Bash | 120517ms | {'command': 'uip is connections edit "197c7074-fa5... |
| Bash | 54426ms | {'command': 'cd /work/output/artifacts/skill-flow-... |
| Bash | 53505ms | {'command': 'uip login status --output json', 'des... |
| Bash | 52490ms | {'command': 'uip maestro flow registry get core.lo... |
| Bash | 52435ms | {'command': 'uip maestro flow registry get core.ac... |

**Most Common Pattern**: `Bash → Bash → Bash`

**Skill Tool Invoked**: 132 time(s)

## Agent Settings

- **Permission Mode**: acceptEdits
- **Allowed Tools**: Skill, Bash, Read, Write, Edit, Glob, Grep
- **Model**: us.anthropic.claude-sonnet-4-6
- **Max Turns**: 100
- **System Prompt**: You are a coding agent. Do not access files in sibling runs/* directories. Everywhere else is permitted. 
- **Plugins**: /home/azureuser/projects/skills

## Environment

- **git_commit**: unknown
- **skills_git_commit**: unknown
- **cli_version**: 1.199.0-dev.7970
- **tool_plugins**: {'admin-tool': '1.199.0-dev.7962', 'agent-tool': '1.199.0-dev.7965', 'agenthub-tool': '1.199.0-dev.7962', 'aops-tool': '1.199.0-dev.7962', 'api-workflow-tool': '1.199.0-dev.7962', 'codedagent-tool': '1.199.0-dev.7965', 'codedapp-tool': '1.199.0-dev.7962', 'coder-tool': '1.199.0-dev.7962', 'context-grounding-tool': '1.199.0-dev.7962', 'conversational-tool': '1.199.0-dev.7962', 'data-fabric-tool': '1.199.0-dev.7962', 'docsai-tool': '1.199.0-dev.7962', 'functions-tool': '1.199.0-dev.7962', 'gov-tool': '1.199.0-dev.7962', 'insights-tool': '1.199.0-dev.7962', 'integrationservice-tool': '1.199.0-dev.7962', 'ixp-tool': '1.199.0-dev.7962', 'llm-gateway-tool': '1.199.0-dev.7962', 'llmgw-tool': '1.199.0-dev.7962', 'maestro-tool': '1.199.0-dev.7962', 'orchestrator-tool': '1.199.0-dev.7962', 'platform-tool': '1.199.0-dev.7962', 'pm-tool': '1.199.0-dev.7969', 'rpa-legacy-tool': '1.199.0-dev.7962', 'rpa-tool': '1.199.0-dev.20260722.4', 'solution-tool': '1.199.0-dev.7962', 'tasks-tool': '1.199.0-dev.7962', 'test-manager-tool': '1.199.0-dev.7962', 'traces-tool': '1.199.0-dev.7962', 'vertical-solutions-tool': '1.199.0-dev.7962'}
- **coder_eval**: 0.8.8
- **claude_code_cli**: 2.1.177 (Claude Code)
- **uv**: uv 0.11.28 (x86_64-unknown-linux-gnu)
- **anthropic**: 0.102.0
- **openai**: 2.47.0
- **pydantic**: 2.12.5
- **api_routing**: aws_bedrock
- **aws_region**: us-east-2
- **bedrock_model**: us.anthropic.claude-sonnet-4-6