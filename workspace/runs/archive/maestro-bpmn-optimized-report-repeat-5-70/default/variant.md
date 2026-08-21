# Variant Report: default

**Experiment**: skill-tests-smoke
**Description**: Linux PR-gate smoke tests — docker isolation, fast turn budget

## Summary

- **Tasks Run**: 70
- **Succeeded**: 64
- **Failed**: 5
- **Errors**: 1
- **Success Rate**: 92.8%
- **Average Score**: 0.975
- **Average Duration**: 193.0s
- **Total Tokens**: 270,099,728
- **Score Stddev**: 0.119
- **Duration Stddev**: 125.8s
- **Replicates/task**: 5
- **Score 95% CI**: [0.960, 0.990] (bootstrap over 350 samples)

## Task Details

| Task | Score | Status | Avg Duration | Reps |
|------|-------|--------|--------------|------|
| skill-bpmn-timer | 1.000 | SUCCESS | 73.0s | 5 |
| skill-bpmn-callactivity-agentic-process | 1.000 | SUCCESS | 195.5s | 5 |
| skill-bpmn-diagnose-job-traces | 1.000 | SUCCESS | 42.1s | 5 |
| skill-bpmn-script-jint-lifecycle | 1.000 | SUCCESS | 184.2s | 5 |
| skill-bpmn-script-task-map | 1.000 | SUCCESS | 146.1s | 5 |
| skill-bpmn-expr-multiinstance-iterator | 1.000 | SUCCESS | 372.9s | 5 |
| skill-bpmn-message-send-receive-pair | 1.000 | SUCCESS | 348.3s | 5 |
| skill-bpmn-script-jint-guidance | 1.000 | SUCCESS | 218.1s | 5 |
| skill-bpmn-switch | 1.000 | SUCCESS | 114.3s | 5 |
| skill-bpmn-error-event-subprocess | 1.000 | SUCCESS | 178.7s | 5 |
| skill-bpmn-script-task-filter | 1.000 | SUCCESS | 149.4s | 5 |
| skill-bpmn-hitl-brownfield-insert | 1.000 | SUCCESS | 124.9s | 5 |
| skill-bpmn-diagnose-scoped-variables | 1.000 | SUCCESS | 42.9s | 5 |
| skill-bpmn-gateway-sequence-flows | 1.000 | SUCCESS | 347.1s | 5 |
| skill-bpmn-hitl-completed-wired | 1.000 | SUCCESS | 174.7s | 5 |
| skill-bpmn-edit-update-node | 1.000 | SUCCESS | 36.9s | 5 |
| skill-bpmn-business-rule-task | 1.000 | SUCCESS | 212.2s | 5 |
| skill-bpmn-script-task-group-by | 1.000 | SUCCESS | 142.3s | 5 |
| skill-bpmn-loop-multiply | 1.000 | SUCCESS | 356.8s | 5 |
| skill-bpmn-parallel-fork-join | 1.000 | SUCCESS | 100.4s | 5 |
| skill-bpmn-feet-inches | 1.000 | SUCCESS | 236.0s | 5 |
| skill-bpmn-e2e-customer-escalation | 1.000 | SUCCESS | 225.1s | 5 |
| skill-bpmn-message-catch | 1.000 | SUCCESS | 225.1s | 5 |
| skill-bpmn-reading-list | 1.000 | SUCCESS | 366.5s | 5 |
| skill-bpmn-event-based-gateway | 1.000 | SUCCESS | 210.6s | 5 |
| skill-bpmn-agent-job | 1.000 | SUCCESS | 368.8s | 5 |
| skill-bpmn-dice-roller | 1.000 | SUCCESS | 136.8s | 5 |
| skill-bpmn-expr-computed-js | 1.000 | SUCCESS | 284.6s | 5 |
| skill-bpmn-operate-diagnose-minimal-fault-triage | 0.980 | FAILURE | 82.2s | 5 |
| skill-bpmn-edit-move-node | 1.000 | SUCCESS | 76.1s | 5 |
| skill-bpmn-debug-not-validation | 1.000 | SUCCESS | 72.9s | 5 |
| skill-bpmn-debug-workflow-mocked | 1.000 | SUCCESS | 34.6s | 5 |
| skill-bpmn-diagnose-validate-fix-loop | 1.000 | SUCCESS | 51.3s | 5 |
| skill-bpmn-http-weather | 1.000 | SUCCESS | 179.4s | 5 |
| skill-bpmn-api-workflow-task | 1.000 | SUCCESS | 279.3s | 5 |
| skill-bpmn-multi-city-weather | 1.000 | SUCCESS | 374.3s | 5 |
| skill-bpmn-expr-error-mapping | 1.000 | SUCCESS | 263.7s | 5 |
| skill-bpmn-rpa-job | 1.000 | SUCCESS | 159.9s | 5 |
| skill-bpmn-diagnose-incident-root-cause | 1.000 | SUCCESS | 37.4s | 5 |
| skill-bpmn-diagnose-deployed-drift | 1.000 | SUCCESS | 43.1s | 5 |
| skill-bpmn-terminate | 1.000 | SUCCESS | 107.4s | 5 |
| skill-bpmn-inclusive-gateway-forkjoin | 1.000 | SUCCESS | 159.7s | 5 |
| skill-bpmn-contract-variant-wrappers | 0.833 | FAILURE | 578.4s | 5 |
| skill-bpmn-timer-boundary-noninterrupting | 1.000 | SUCCESS | 184.3s | 5 |
| skill-bpmn-hitl-schema-design | 0.800 | ERROR | 291.6s | 5 |
| skill-bpmn-diagnose-stuck-gateway | 1.000 | SUCCESS | 47.7s | 5 |
| skill-bpmn-smoke-registry-discovery | 1.000 | SUCCESS | 47.9s | 5 |
| skill-bpmn-hitl-boolean-decision | 1.000 | SUCCESS | 263.8s | 5 |
| skill-bpmn-edit-group-to-subflow | 1.000 | SUCCESS | 221.9s | 5 |
| skill-bpmn-edit-remove-node | 1.000 | SUCCESS | 70.4s | 5 |
| skill-bpmn-error-boundary-handler | 1.000 | SUCCESS | 208.4s | 5 |
| skill-bpmn-hitl-rpa-wrappers | 1.000 | SUCCESS | 134.5s | 5 |
| skill-bpmn-author-validate | 1.000 | SUCCESS | 110.9s | 5 |
| skill-bpmn-event-trigger-start | 1.000 | SUCCESS | 180.4s | 5 |
| skill-bpmn-calculator | 1.000 | SUCCESS | 356.1s | 5 |
| skill-bpmn-edit-add-output | 1.000 | SUCCESS | 53.5s | 5 |
| skill-bpmn-e2e-wiki-pageviews | 1.000 | SUCCESS | 394.3s | 5 |
| skill-bpmn-safety-sanitize | 1.000 | SUCCESS | 34.3s | 5 |
| skill-bpmn-edit-add-node | 1.000 | SUCCESS | 105.0s | 5 |
| skill-bpmn-e2e-live-debug | 0.167 | MAX_TURNS_EXHAUSTED | 564.9s | 5 |
| skill-bpmn-registry-discovery | 1.000 | SUCCESS | 87.6s | 5 |
| skill-bpmn-subprocess | 0.978 | FAILURE | 228.7s | 5 |
| skill-bpmn-timer-start | 1.000 | SUCCESS | 146.5s | 5 |
| skill-bpmn-queue-create-and-wait | 1.000 | SUCCESS | 172.6s | 5 |
| skill-bpmn-e2e-invoice-exception-triage | 1.000 | SUCCESS | 240.0s | 5 |
| skill-bpmn-debug-instance-inspect | 1.000 | SUCCESS | 42.0s | 5 |
| skill-bpmn-hitl-result-downstream | 1.000 | SUCCESS | 198.8s | 5 |
| skill-bpmn-hitl-multi-outcome-routing | 1.000 | SUCCESS | 241.7s | 5 |
| skill-bpmn-simple-approval-bpmn | 1.000 | SUCCESS | 430.2s | 5 |
| skill-bpmn-integration-service-boundary | 0.500 | FAILURE | 336.7s | 5 |


## Generation Metrics

| Task ID | Total Latency | Turns | Asst Turns | Avg Turn Latency |
|---------|---------------|-------|------------|------------------|
| skill-bpmn-timer | 92.8s | 1 | 16 | 86.9s |
| skill-bpmn-timer | 58.6s | 1 | 18 | 56.9s |
| skill-bpmn-timer | 78.0s | 1 | 16 | 76.3s |
| skill-bpmn-timer | 56.0s | 1 | 19 | 54.4s |
| skill-bpmn-timer | 79.7s | 1 | 19 | 78.0s |
| skill-bpmn-callactivity-agentic-process | 161.0s | 1 | 44 | 159.3s |
| skill-bpmn-callactivity-agentic-process | 97.3s | 1 | 24 | 95.6s |
| skill-bpmn-callactivity-agentic-process | 185.2s | 1 | 48 | 183.6s |
| skill-bpmn-callactivity-agentic-process | 204.7s | 1 | 36 | 203.0s |
| skill-bpmn-callactivity-agentic-process | 329.4s | 1 | 49 | 327.7s |
| skill-bpmn-diagnose-job-traces | 42.6s | 1 | 15 | 40.8s |
| skill-bpmn-diagnose-job-traces | 37.8s | 1 | 16 | 35.9s |
| skill-bpmn-diagnose-job-traces | 39.1s | 1 | 14 | 37.3s |
| skill-bpmn-diagnose-job-traces | 45.1s | 1 | 15 | 43.4s |
| skill-bpmn-diagnose-job-traces | 46.1s | 1 | 15 | 44.2s |
| skill-bpmn-script-jint-lifecycle | 208.2s | 1 | 28 | 206.5s |
| skill-bpmn-script-jint-lifecycle | 165.1s | 1 | 30 | 163.5s |
| skill-bpmn-script-jint-lifecycle | 182.9s | 1 | 34 | 181.3s |
| skill-bpmn-script-jint-lifecycle | 213.4s | 1 | 48 | 211.8s |
| skill-bpmn-script-jint-lifecycle | 151.5s | 1 | 31 | 149.8s |
| skill-bpmn-script-task-map | 163.2s | 1 | 22 | 157.9s |
| skill-bpmn-script-task-map | 152.7s | 1 | 19 | 150.9s |
| skill-bpmn-script-task-map | 133.4s | 1 | 20 | 131.5s |
| skill-bpmn-script-task-map | 113.2s | 1 | 19 | 111.4s |
| skill-bpmn-script-task-map | 168.2s | 1 | 25 | 166.5s |
| skill-bpmn-expr-multiinstance-iterator | 382.3s | 1 | 37 | 380.7s |
| skill-bpmn-expr-multiinstance-iterator | 273.8s | 1 | 26 | 272.2s |
| skill-bpmn-expr-multiinstance-iterator | 568.1s | 1 | 30 | 566.5s |
| skill-bpmn-expr-multiinstance-iterator | 299.4s | 1 | 31 | 297.7s |
| skill-bpmn-expr-multiinstance-iterator | 340.6s | 1 | 35 | 338.9s |
| skill-bpmn-message-send-receive-pair | 314.3s | 1 | 59 | 312.7s |
| skill-bpmn-message-send-receive-pair | 652.9s | 1 | 62 | 651.3s |
| skill-bpmn-message-send-receive-pair | 244.2s | 1 | 61 | 242.5s |
| skill-bpmn-message-send-receive-pair | 265.2s | 1 | 56 | 263.4s |
| skill-bpmn-message-send-receive-pair | 264.7s | 1 | 60 | 262.9s |
| skill-bpmn-script-jint-guidance | 282.0s | 1 | 37 | 280.2s |
| skill-bpmn-script-jint-guidance | 141.6s | 1 | 27 | 139.9s |
| skill-bpmn-script-jint-guidance | 246.3s | 1 | 29 | 244.5s |
| skill-bpmn-script-jint-guidance | 187.3s | 1 | 41 | 185.7s |
| skill-bpmn-script-jint-guidance | 233.5s | 1 | 46 | 231.9s |
| skill-bpmn-switch | 119.2s | 1 | 20 | 112.1s |
| skill-bpmn-switch | 101.9s | 1 | 15 | 95.3s |
| skill-bpmn-switch | 123.0s | 1 | 14 | 116.6s |
| skill-bpmn-switch | 113.7s | 1 | 18 | 107.4s |
| skill-bpmn-switch | 113.6s | 1 | 18 | 106.6s |
| skill-bpmn-error-event-subprocess | 178.1s | 1 | 15 | 176.4s |
| skill-bpmn-error-event-subprocess | 193.5s | 1 | 22 | 191.8s |
| skill-bpmn-error-event-subprocess | 152.5s | 1 | 17 | 150.7s |
| skill-bpmn-error-event-subprocess | 157.5s | 1 | 17 | 155.7s |
| skill-bpmn-error-event-subprocess | 212.1s | 1 | 21 | 210.4s |
| skill-bpmn-script-task-filter | 128.1s | 1 | 16 | 126.2s |
| skill-bpmn-script-task-filter | 158.3s | 1 | 18 | 156.6s |
| skill-bpmn-script-task-filter | 124.6s | 1 | 10 | 122.7s |
| skill-bpmn-script-task-filter | 176.6s | 1 | 20 | 174.7s |
| skill-bpmn-script-task-filter | 159.5s | 1 | 19 | 157.8s |
| skill-bpmn-hitl-brownfield-insert | 98.8s | 1 | 25 | 97.1s |
| skill-bpmn-hitl-brownfield-insert | 134.1s | 1 | 27 | 132.5s |
| skill-bpmn-hitl-brownfield-insert | 118.5s | 1 | 25 | 116.8s |
| skill-bpmn-hitl-brownfield-insert | 136.6s | 1 | 25 | 135.0s |
| skill-bpmn-hitl-brownfield-insert | 136.6s | 1 | 27 | 135.0s |
| skill-bpmn-diagnose-scoped-variables | 42.7s | 1 | 13 | 40.9s |
| skill-bpmn-diagnose-scoped-variables | 43.7s | 1 | 14 | 42.0s |
| skill-bpmn-diagnose-scoped-variables | 44.2s | 1 | 13 | 42.3s |
| skill-bpmn-diagnose-scoped-variables | 42.3s | 1 | 13 | 40.5s |
| skill-bpmn-diagnose-scoped-variables | 41.8s | 1 | 13 | 40.1s |
| skill-bpmn-gateway-sequence-flows | 447.3s | 1 | 26 | 441.6s |
| skill-bpmn-gateway-sequence-flows | 305.4s | 1 | 39 | 303.8s |
| skill-bpmn-gateway-sequence-flows | 284.8s | 1 | 27 | 283.2s |
| skill-bpmn-gateway-sequence-flows | 210.0s | 1 | 26 | 208.4s |
| skill-bpmn-gateway-sequence-flows | 487.9s | 1 | 28 | 486.2s |
| skill-bpmn-hitl-completed-wired | 183.5s | 1 | 22 | 177.7s |
| skill-bpmn-hitl-completed-wired | 195.1s | 1 | 27 | 193.4s |
| skill-bpmn-hitl-completed-wired | 183.1s | 1 | 26 | 181.4s |
| skill-bpmn-hitl-completed-wired | 145.6s | 1 | 28 | 143.8s |
| skill-bpmn-hitl-completed-wired | 166.3s | 1 | 27 | 164.7s |
| skill-bpmn-edit-update-node | 35.2s | 1 | 18 | 33.4s |
| skill-bpmn-edit-update-node | 35.2s | 1 | 18 | 33.6s |
| skill-bpmn-edit-update-node | 47.3s | 1 | 21 | 45.6s |
| skill-bpmn-edit-update-node | 33.0s | 1 | 16 | 31.3s |
| skill-bpmn-edit-update-node | 33.9s | 1 | 17 | 32.2s |
| skill-bpmn-business-rule-task | 211.5s | 1 | 28 | 209.7s |
| skill-bpmn-business-rule-task | 269.4s | 1 | 47 | 267.7s |
| skill-bpmn-business-rule-task | 156.2s | 1 | 28 | 154.5s |
| skill-bpmn-business-rule-task | 233.0s | 1 | 36 | 231.3s |
| skill-bpmn-business-rule-task | 190.8s | 1 | 27 | 189.1s |
| skill-bpmn-script-task-group-by | 117.5s | 1 | 17 | 115.7s |
| skill-bpmn-script-task-group-by | 175.8s | 1 | 26 | 174.2s |
| skill-bpmn-script-task-group-by | 121.2s | 1 | 22 | 119.5s |
| skill-bpmn-script-task-group-by | 159.0s | 1 | 19 | 157.3s |
| skill-bpmn-script-task-group-by | 138.2s | 1 | 19 | 136.5s |
| skill-bpmn-loop-multiply | 345.3s | 1 | 25 | 343.6s |
| skill-bpmn-loop-multiply | 336.8s | 1 | 27 | 335.1s |
| skill-bpmn-loop-multiply | 193.7s | 1 | 26 | 192.0s |
| skill-bpmn-loop-multiply | 323.8s | 1 | 31 | 322.2s |
| skill-bpmn-loop-multiply | 584.4s | 1 | 31 | 582.7s |
| skill-bpmn-parallel-fork-join | 75.9s | 1 | 19 | 70.5s |
| skill-bpmn-parallel-fork-join | 89.9s | 1 | 18 | 88.3s |
| skill-bpmn-parallel-fork-join | 101.4s | 1 | 17 | 99.7s |
| skill-bpmn-parallel-fork-join | 102.0s | 1 | 17 | 99.9s |
| skill-bpmn-parallel-fork-join | 133.1s | 1 | 24 | 131.4s |
| skill-bpmn-feet-inches | 256.2s | 1 | 33 | 254.6s |
| skill-bpmn-feet-inches | 133.7s | 1 | 30 | 132.1s |
| skill-bpmn-feet-inches | 286.5s | 1 | 33 | 284.9s |
| skill-bpmn-feet-inches | 247.1s | 1 | 48 | 245.3s |
| skill-bpmn-feet-inches | 256.6s | 1 | 29 | 254.9s |
| skill-bpmn-e2e-customer-escalation | 270.1s | 1 | 37 | 253.7s |
| skill-bpmn-e2e-customer-escalation | 166.1s | 1 | 31 | 157.5s |
| skill-bpmn-e2e-customer-escalation | 210.8s | 1 | 34 | 203.1s |
| skill-bpmn-e2e-customer-escalation | 217.3s | 1 | 41 | 208.5s |
| skill-bpmn-e2e-customer-escalation | 261.1s | 1 | 46 | 253.1s |
| skill-bpmn-message-catch | 183.8s | 1 | 50 | 178.2s |
| skill-bpmn-message-catch | 312.9s | 1 | 51 | 311.2s |
| skill-bpmn-message-catch | 229.5s | 1 | 46 | 227.9s |
| skill-bpmn-message-catch | 230.0s | 1 | 52 | 228.3s |
| skill-bpmn-message-catch | 169.4s | 1 | 51 | 167.8s |
| skill-bpmn-reading-list | 421.4s | 1 | 29 | 419.8s |
| skill-bpmn-reading-list | 276.8s | 1 | 31 | 275.1s |
| skill-bpmn-reading-list | 377.4s | 1 | 33 | 375.5s |
| skill-bpmn-reading-list | 229.9s | 1 | 27 | 228.2s |
| skill-bpmn-reading-list | 526.8s | 1 | 35 | 525.2s |
| skill-bpmn-event-based-gateway | 200.6s | 1 | 21 | 198.9s |
| skill-bpmn-event-based-gateway | 336.1s | 1 | 60 | 334.3s |
| skill-bpmn-event-based-gateway | 144.4s | 1 | 26 | 142.7s |
| skill-bpmn-event-based-gateway | 243.2s | 1 | 29 | 241.5s |
| skill-bpmn-event-based-gateway | 128.9s | 1 | 27 | 127.2s |
| skill-bpmn-agent-job | 274.8s | 1 | 27 | 273.1s |
| skill-bpmn-agent-job | 427.0s | 1 | 30 | 425.3s |
| skill-bpmn-agent-job | 568.8s | 1 | 35 | 567.1s |
| skill-bpmn-agent-job | 263.4s | 1 | 32 | 261.7s |
| skill-bpmn-agent-job | 310.3s | 1 | 37 | 308.6s |
| skill-bpmn-dice-roller | 124.9s | 1 | 29 | 123.2s |
| skill-bpmn-dice-roller | 181.2s | 1 | 39 | 179.5s |
| skill-bpmn-dice-roller | 112.8s | 1 | 24 | 111.1s |
| skill-bpmn-dice-roller | 149.4s | 1 | 22 | 147.7s |
| skill-bpmn-dice-roller | 115.9s | 1 | 22 | 114.2s |
| skill-bpmn-expr-computed-js | 164.0s | 1 | 34 | 162.3s |
| skill-bpmn-expr-computed-js | 278.1s | 1 | 35 | 276.3s |
| skill-bpmn-expr-computed-js | 180.0s | 1 | 32 | 178.3s |
| skill-bpmn-expr-computed-js | 500.8s | 1 | 66 | 499.1s |
| skill-bpmn-expr-computed-js | 300.0s | 1 | 71 | 298.4s |
| skill-bpmn-operate-diagnose-minimal-fault-triage | 109.3s | 1 | 26 | 102.0s |
| skill-bpmn-operate-diagnose-minimal-fault-triage | 48.8s | 1 | 17 | 41.6s |
| skill-bpmn-operate-diagnose-minimal-fault-triage | 79.1s | 1 | 16 | 71.5s |
| skill-bpmn-operate-diagnose-minimal-fault-triage | 85.7s | 1 | 19 | 77.4s |
| skill-bpmn-operate-diagnose-minimal-fault-triage | 88.0s | 1 | 18 | 80.5s |
| skill-bpmn-edit-move-node | 70.8s | 1 | 25 | 69.1s |
| skill-bpmn-edit-move-node | 82.8s | 1 | 25 | 81.2s |
| skill-bpmn-edit-move-node | 76.3s | 1 | 21 | 74.6s |
| skill-bpmn-edit-move-node | 85.3s | 1 | 24 | 83.7s |
| skill-bpmn-edit-move-node | 65.2s | 1 | 23 | 63.5s |
| skill-bpmn-debug-not-validation | 79.2s | 1 | 17 | 77.6s |
| skill-bpmn-debug-not-validation | 67.3s | 1 | 22 | 65.6s |
| skill-bpmn-debug-not-validation | 84.3s | 1 | 28 | 82.3s |
| skill-bpmn-debug-not-validation | 68.5s | 1 | 20 | 66.8s |
| skill-bpmn-debug-not-validation | 65.3s | 1 | 18 | 63.7s |
| skill-bpmn-debug-workflow-mocked | 36.0s | 1 | 15 | 34.0s |
| skill-bpmn-debug-workflow-mocked | 31.2s | 1 | 14 | 29.4s |
| skill-bpmn-debug-workflow-mocked | 35.0s | 1 | 13 | 33.0s |
| skill-bpmn-debug-workflow-mocked | 35.2s | 1 | 15 | 33.5s |
| skill-bpmn-debug-workflow-mocked | 35.8s | 1 | 16 | 34.0s |
| skill-bpmn-diagnose-validate-fix-loop | 54.3s | 1 | 21 | 52.1s |
| skill-bpmn-diagnose-validate-fix-loop | 55.7s | 1 | 20 | 53.6s |
| skill-bpmn-diagnose-validate-fix-loop | 51.7s | 1 | 22 | 49.2s |
| skill-bpmn-diagnose-validate-fix-loop | 51.4s | 1 | 20 | 49.3s |
| skill-bpmn-diagnose-validate-fix-loop | 43.6s | 1 | 16 | 41.5s |
| skill-bpmn-http-weather | 141.6s | 1 | 26 | 139.9s |
| skill-bpmn-http-weather | 182.8s | 1 | 30 | 181.1s |
| skill-bpmn-http-weather | 155.4s | 1 | 25 | 153.7s |
| skill-bpmn-http-weather | 164.9s | 1 | 33 | 163.2s |
| skill-bpmn-http-weather | 252.2s | 1 | 30 | 250.5s |
| skill-bpmn-api-workflow-task | 233.9s | 1 | 36 | 229.0s |
| skill-bpmn-api-workflow-task | 328.5s | 1 | 33 | 326.7s |
| skill-bpmn-api-workflow-task | 214.7s | 1 | 38 | 213.0s |
| skill-bpmn-api-workflow-task | 234.3s | 1 | 32 | 232.7s |
| skill-bpmn-api-workflow-task | 384.9s | 1 | 31 | 383.2s |
| skill-bpmn-multi-city-weather | 357.0s | 1 | 38 | 355.2s |
| skill-bpmn-multi-city-weather | 313.4s | 1 | 28 | 311.7s |
| skill-bpmn-multi-city-weather | 378.2s | 1 | 37 | 376.5s |
| skill-bpmn-multi-city-weather | 440.5s | 1 | 34 | 438.8s |
| skill-bpmn-multi-city-weather | 382.4s | 1 | 28 | 380.6s |
| skill-bpmn-expr-error-mapping | 219.3s | 1 | 39 | 217.7s |
| skill-bpmn-expr-error-mapping | 192.3s | 1 | 30 | 190.5s |
| skill-bpmn-expr-error-mapping | 266.3s | 1 | 48 | 264.6s |
| skill-bpmn-expr-error-mapping | 343.1s | 1 | 52 | 341.5s |
| skill-bpmn-expr-error-mapping | 297.5s | 1 | 35 | 295.5s |
| skill-bpmn-rpa-job | 163.3s | 1 | 25 | 161.5s |
| skill-bpmn-rpa-job | 148.6s | 1 | 27 | 146.9s |
| skill-bpmn-rpa-job | 167.3s | 1 | 35 | 165.6s |
| skill-bpmn-rpa-job | 137.6s | 1 | 22 | 135.8s |
| skill-bpmn-rpa-job | 182.6s | 1 | 27 | 180.9s |
| skill-bpmn-diagnose-incident-root-cause | 40.2s | 1 | 14 | 34.8s |
| skill-bpmn-diagnose-incident-root-cause | 39.5s | 1 | 14 | 37.8s |
| skill-bpmn-diagnose-incident-root-cause | 35.2s | 1 | 13 | 33.5s |
| skill-bpmn-diagnose-incident-root-cause | 38.1s | 1 | 13 | 36.4s |
| skill-bpmn-diagnose-incident-root-cause | 34.1s | 1 | 14 | 32.4s |
| skill-bpmn-diagnose-deployed-drift | 35.9s | 1 | 14 | 34.1s |
| skill-bpmn-diagnose-deployed-drift | 44.2s | 1 | 15 | 42.5s |
| skill-bpmn-diagnose-deployed-drift | 33.8s | 1 | 14 | 32.0s |
| skill-bpmn-diagnose-deployed-drift | 41.5s | 1 | 17 | 39.8s |
| skill-bpmn-diagnose-deployed-drift | 60.3s | 1 | 20 | 58.6s |
| skill-bpmn-terminate | 117.7s | 1 | 18 | 111.2s |
| skill-bpmn-terminate | 112.4s | 1 | 17 | 105.7s |
| skill-bpmn-terminate | 133.2s | 1 | 17 | 126.8s |
| skill-bpmn-terminate | 82.3s | 1 | 16 | 76.5s |
| skill-bpmn-terminate | 91.3s | 1 | 17 | 84.6s |
| skill-bpmn-inclusive-gateway-forkjoin | 165.7s | 1 | 26 | 164.0s |
| skill-bpmn-inclusive-gateway-forkjoin | 173.1s | 1 | 25 | 171.3s |
| skill-bpmn-inclusive-gateway-forkjoin | 194.9s | 1 | 24 | 193.2s |
| skill-bpmn-inclusive-gateway-forkjoin | 108.0s | 1 | 22 | 106.3s |
| skill-bpmn-inclusive-gateway-forkjoin | 156.8s | 1 | 21 | 155.1s |
| skill-bpmn-contract-variant-wrappers | 451.5s | 1 | 54 | 446.2s |
| skill-bpmn-contract-variant-wrappers | 424.2s | 1 | 30 | 422.5s |
| skill-bpmn-contract-variant-wrappers | 731.3s | 1 | 54 | 729.8s |
| skill-bpmn-contract-variant-wrappers | 697.9s | 1 | 65 | 696.2s |
| skill-bpmn-contract-variant-wrappers | 587.0s | 1 | 37 | 585.3s |
| skill-bpmn-timer-boundary-noninterrupting | 133.7s | 1 | 29 | 128.1s |
| skill-bpmn-timer-boundary-noninterrupting | 178.7s | 1 | 21 | 177.0s |
| skill-bpmn-timer-boundary-noninterrupting | 188.0s | 1 | 24 | 186.3s |
| skill-bpmn-timer-boundary-noninterrupting | 268.5s | 1 | 27 | 266.4s |
| skill-bpmn-timer-boundary-noninterrupting | 152.5s | 1 | 24 | 150.9s |
| skill-bpmn-hitl-schema-design | 330.4s | 1 | 31 | 328.7s |
| skill-bpmn-hitl-schema-design | 549.3s | 1 | 36 | 547.7s |
| skill-bpmn-hitl-schema-design | 901.7s | 1 | 15 | 900.0s |
| skill-bpmn-hitl-schema-design | 340.5s | 1 | 30 | 338.8s |
| skill-bpmn-hitl-schema-design | 237.7s | 1 | 25 | 236.0s |
| skill-bpmn-diagnose-stuck-gateway | 50.3s | 1 | 18 | 48.6s |
| skill-bpmn-diagnose-stuck-gateway | 51.7s | 1 | 21 | 50.0s |
| skill-bpmn-diagnose-stuck-gateway | 52.2s | 1 | 15 | 50.5s |
| skill-bpmn-diagnose-stuck-gateway | 40.9s | 1 | 12 | 39.2s |
| skill-bpmn-diagnose-stuck-gateway | 43.3s | 1 | 14 | 41.4s |
| skill-bpmn-smoke-registry-discovery | 57.8s | 1 | 16 | 57.2s |
| skill-bpmn-smoke-registry-discovery | 49.9s | 1 | 14 | 49.6s |
| skill-bpmn-smoke-registry-discovery | 45.2s | 1 | 14 | 44.9s |
| skill-bpmn-smoke-registry-discovery | 38.4s | 1 | 12 | 38.1s |
| skill-bpmn-smoke-registry-discovery | 48.4s | 1 | 13 | 48.1s |
| skill-bpmn-hitl-boolean-decision | 258.3s | 1 | 36 | 256.4s |
| skill-bpmn-hitl-boolean-decision | 380.7s | 1 | 32 | 379.1s |
| skill-bpmn-hitl-boolean-decision | 216.9s | 1 | 25 | 215.3s |
| skill-bpmn-hitl-boolean-decision | 255.1s | 1 | 29 | 253.4s |
| skill-bpmn-hitl-boolean-decision | 207.8s | 1 | 25 | 206.2s |
| skill-bpmn-edit-group-to-subflow | 133.8s | 1 | 18 | 132.0s |
| skill-bpmn-edit-group-to-subflow | 148.7s | 1 | 18 | 147.1s |
| skill-bpmn-edit-group-to-subflow | 177.0s | 1 | 15 | 175.3s |
| skill-bpmn-edit-group-to-subflow | 467.1s | 1 | 27 | 465.4s |
| skill-bpmn-edit-group-to-subflow | 182.7s | 1 | 21 | 181.0s |
| skill-bpmn-edit-remove-node | 69.3s | 1 | 16 | 67.6s |
| skill-bpmn-edit-remove-node | 61.6s | 1 | 15 | 59.8s |
| skill-bpmn-edit-remove-node | 67.9s | 1 | 26 | 66.2s |
| skill-bpmn-edit-remove-node | 83.7s | 1 | 30 | 81.9s |
| skill-bpmn-edit-remove-node | 69.6s | 1 | 25 | 67.8s |
| skill-bpmn-error-boundary-handler | 223.9s | 1 | 27 | 219.7s |
| skill-bpmn-error-boundary-handler | 256.7s | 1 | 26 | 254.9s |
| skill-bpmn-error-boundary-handler | 209.4s | 1 | 28 | 207.7s |
| skill-bpmn-error-boundary-handler | 197.6s | 1 | 22 | 195.9s |
| skill-bpmn-error-boundary-handler | 154.1s | 1 | 23 | 152.4s |
| skill-bpmn-hitl-rpa-wrappers | 142.1s | 1 | 26 | 136.6s |
| skill-bpmn-hitl-rpa-wrappers | 110.0s | 1 | 27 | 108.5s |
| skill-bpmn-hitl-rpa-wrappers | 128.0s | 1 | 23 | 126.3s |
| skill-bpmn-hitl-rpa-wrappers | 138.1s | 1 | 26 | 136.4s |
| skill-bpmn-hitl-rpa-wrappers | 154.4s | 1 | 28 | 152.7s |
| skill-bpmn-author-validate | 88.7s | 1 | 19 | 83.9s |
| skill-bpmn-author-validate | 149.0s | 1 | 20 | 147.2s |
| skill-bpmn-author-validate | 140.0s | 1 | 27 | 138.3s |
| skill-bpmn-author-validate | 83.3s | 1 | 20 | 81.7s |
| skill-bpmn-author-validate | 93.7s | 1 | 24 | 92.1s |
| skill-bpmn-event-trigger-start | 166.9s | 1 | 23 | 158.0s |
| skill-bpmn-event-trigger-start | 151.8s | 1 | 18 | 141.7s |
| skill-bpmn-event-trigger-start | 169.8s | 1 | 22 | 160.7s |
| skill-bpmn-event-trigger-start | 210.7s | 1 | 32 | 199.9s |
| skill-bpmn-event-trigger-start | 202.7s | 1 | 29 | 194.1s |
| skill-bpmn-calculator | 847.9s | 1 | 34 | 846.0s |
| skill-bpmn-calculator | 224.8s | 1 | 39 | 223.0s |
| skill-bpmn-calculator | 162.2s | 1 | 22 | 160.5s |
| skill-bpmn-calculator | 259.9s | 1 | 46 | 258.1s |
| skill-bpmn-calculator | 285.6s | 1 | 54 | 283.9s |
| skill-bpmn-edit-add-output | 58.1s | 1 | 20 | 56.4s |
| skill-bpmn-edit-add-output | 52.5s | 1 | 19 | 50.7s |
| skill-bpmn-edit-add-output | 44.4s | 1 | 18 | 42.6s |
| skill-bpmn-edit-add-output | 49.6s | 1 | 19 | 47.8s |
| skill-bpmn-edit-add-output | 63.1s | 1 | 21 | 61.4s |
| skill-bpmn-e2e-wiki-pageviews | 443.3s | 1 | 34 | 434.0s |
| skill-bpmn-e2e-wiki-pageviews | 591.1s | 1 | 44 | 581.6s |
| skill-bpmn-e2e-wiki-pageviews | 343.8s | 1 | 36 | 335.9s |
| skill-bpmn-e2e-wiki-pageviews | 402.7s | 1 | 35 | 394.8s |
| skill-bpmn-e2e-wiki-pageviews | 190.8s | 1 | 38 | 182.7s |
| skill-bpmn-safety-sanitize | 33.6s | 1 | 15 | 31.9s |
| skill-bpmn-safety-sanitize | 32.0s | 1 | 15 | 30.3s |
| skill-bpmn-safety-sanitize | 35.4s | 1 | 15 | 33.7s |
| skill-bpmn-safety-sanitize | 35.5s | 1 | 16 | 33.8s |
| skill-bpmn-safety-sanitize | 35.1s | 1 | 16 | 33.5s |
| skill-bpmn-edit-add-node | 115.6s | 1 | 25 | 113.9s |
| skill-bpmn-edit-add-node | 108.7s | 1 | 19 | 107.0s |
| skill-bpmn-edit-add-node | 101.2s | 1 | 16 | 99.5s |
| skill-bpmn-edit-add-node | 83.5s | 1 | 24 | 81.7s |
| skill-bpmn-edit-add-node | 115.8s | 1 | 24 | 114.0s |
| skill-bpmn-e2e-live-debug | 479.2s | 1 | 152 | 474.5s |
| skill-bpmn-e2e-live-debug | 514.0s | 1 | 144 | 512.3s |
| skill-bpmn-e2e-live-debug | 611.9s | 1 | 155 | 610.2s |
| skill-bpmn-e2e-live-debug | 510.4s | 1 | 145 | 508.7s |
| skill-bpmn-e2e-live-debug | 709.0s | 1 | 143 | 707.3s |
| skill-bpmn-registry-discovery | 95.1s | 1 | 19 | 93.4s |
| skill-bpmn-registry-discovery | 77.1s | 1 | 12 | 75.5s |
| skill-bpmn-registry-discovery | 79.2s | 1 | 12 | 77.5s |
| skill-bpmn-registry-discovery | 89.1s | 1 | 16 | 87.5s |
| skill-bpmn-registry-discovery | 97.7s | 1 | 21 | 96.0s |
| skill-bpmn-subprocess | 181.9s | 1 | 24 | 169.7s |
| skill-bpmn-subprocess | 363.1s | 1 | 17 | 355.1s |
| skill-bpmn-subprocess | 129.4s | 1 | 15 | 123.2s |
| skill-bpmn-subprocess | 184.3s | 1 | 23 | 176.1s |
| skill-bpmn-subprocess | 284.8s | 1 | 20 | 278.0s |
| skill-bpmn-timer-start | 163.3s | 1 | 23 | 157.8s |
| skill-bpmn-timer-start | 114.0s | 1 | 23 | 112.2s |
| skill-bpmn-timer-start | 146.7s | 1 | 21 | 145.1s |
| skill-bpmn-timer-start | 163.5s | 1 | 31 | 161.8s |
| skill-bpmn-timer-start | 145.0s | 1 | 31 | 143.3s |
| skill-bpmn-queue-create-and-wait | 123.9s | 1 | 21 | 118.1s |
| skill-bpmn-queue-create-and-wait | 167.1s | 1 | 32 | 165.5s |
| skill-bpmn-queue-create-and-wait | 152.0s | 1 | 24 | 150.4s |
| skill-bpmn-queue-create-and-wait | 199.8s | 1 | 32 | 197.7s |
| skill-bpmn-queue-create-and-wait | 220.1s | 1 | 32 | 218.5s |
| skill-bpmn-e2e-invoice-exception-triage | 209.0s | 1 | 32 | 196.0s |
| skill-bpmn-e2e-invoice-exception-triage | 279.6s | 1 | 33 | 270.1s |
| skill-bpmn-e2e-invoice-exception-triage | 344.5s | 1 | 44 | 332.9s |
| skill-bpmn-e2e-invoice-exception-triage | 199.1s | 1 | 38 | 191.3s |
| skill-bpmn-e2e-invoice-exception-triage | 167.9s | 1 | 44 | 159.7s |
| skill-bpmn-debug-instance-inspect | 40.5s | 1 | 14 | 38.7s |
| skill-bpmn-debug-instance-inspect | 37.8s | 1 | 16 | 35.9s |
| skill-bpmn-debug-instance-inspect | 43.5s | 1 | 16 | 41.8s |
| skill-bpmn-debug-instance-inspect | 45.5s | 1 | 16 | 43.8s |
| skill-bpmn-debug-instance-inspect | 42.6s | 1 | 16 | 40.9s |
| skill-bpmn-hitl-result-downstream | 218.1s | 1 | 25 | 215.4s |
| skill-bpmn-hitl-result-downstream | 180.2s | 1 | 28 | 178.6s |
| skill-bpmn-hitl-result-downstream | 188.5s | 1 | 31 | 186.8s |
| skill-bpmn-hitl-result-downstream | 207.1s | 1 | 28 | 205.2s |
| skill-bpmn-hitl-result-downstream | 200.0s | 1 | 26 | 198.2s |
| skill-bpmn-hitl-multi-outcome-routing | 387.7s | 1 | 44 | 385.4s |
| skill-bpmn-hitl-multi-outcome-routing | 333.2s | 1 | 33 | 331.5s |
| skill-bpmn-hitl-multi-outcome-routing | 137.8s | 1 | 21 | 136.1s |
| skill-bpmn-hitl-multi-outcome-routing | 182.8s | 1 | 26 | 181.1s |
| skill-bpmn-hitl-multi-outcome-routing | 166.7s | 1 | 27 | 165.0s |
| skill-bpmn-simple-approval-bpmn | 331.0s | 1 | 35 | 328.6s |
| skill-bpmn-simple-approval-bpmn | 540.6s | 1 | 37 | 538.2s |
| skill-bpmn-simple-approval-bpmn | 499.2s | 1 | 53 | 497.5s |
| skill-bpmn-simple-approval-bpmn | 401.2s | 1 | 35 | 399.5s |
| skill-bpmn-simple-approval-bpmn | 378.8s | 1 | 38 | 377.2s |
| skill-bpmn-integration-service-boundary | 287.8s | 1 | 27 | 285.3s |
| skill-bpmn-integration-service-boundary | 346.2s | 1 | 45 | 343.8s |
| skill-bpmn-integration-service-boundary | 458.8s | 1 | 52 | 456.4s |
| skill-bpmn-integration-service-boundary | 256.2s | 1 | 31 | 254.4s |
| skill-bpmn-integration-service-boundary | 334.4s | 1 | 51 | 331.7s |


## Token Usage

**Total Tokens**: 270,099,728 (input: 675,077, output: 4,361,986)
**Cache Tokens**: write: 9,111,762, read: 255,950,903
**Total Cost**: $178.4094
**Avg Tokens/Task**: 771,713

| Task ID | Input (uncached) | Output | Cache Write | Cache Read | Total | Cost |
|---------|------------------|--------|-------------|------------|-------|------|
| skill-bpmn-timer | 631 | 6,319 | 19,515 | 322,419 | 348,884 | $0.2666 |
| skill-bpmn-timer | 633 | 3,721 | 19,843 | 399,667 | 423,864 | $0.2520 |
| skill-bpmn-timer | 630 | 6,084 | 19,860 | 284,294 | 310,868 | $0.2529 |
| skill-bpmn-timer | 633 | 3,517 | 19,750 | 400,074 | 423,974 | $0.2487 |
| skill-bpmn-timer | 634 | 5,301 | 19,382 | 435,922 | 461,239 | $0.2849 |
| skill-bpmn-callactivity-agentic-process | 705 | 8,618 | 28,717 | 909,754 | 947,794 | $0.5120 |
| skill-bpmn-callactivity-agentic-process | 4,351 | 5,438 | 26,139 | 529,340 | 565,268 | $0.3514 |
| skill-bpmn-callactivity-agentic-process | 712 | 10,528 | 29,843 | 1,188,290 | 1,229,373 | $0.6285 |
| skill-bpmn-callactivity-agentic-process | 705 | 11,669 | 28,611 | 919,462 | 960,447 | $0.5603 |
| skill-bpmn-callactivity-agentic-process | 4,405 | 17,530 | 32,067 | 1,216,047 | 1,270,049 | $0.7612 |
| skill-bpmn-diagnose-job-traces | 604 | 2,207 | 11,514 | 207,895 | 222,220 | $0.1405 |
| skill-bpmn-diagnose-job-traces | 603 | 2,136 | 11,401 | 178,918 | 193,058 | $0.1303 |
| skill-bpmn-diagnose-job-traces | 604 | 1,932 | 11,399 | 207,957 | 221,892 | $0.1359 |
| skill-bpmn-diagnose-job-traces | 603 | 2,521 | 11,368 | 178,953 | 193,445 | $0.1359 |
| skill-bpmn-diagnose-job-traces | 603 | 2,416 | 11,533 | 178,818 | 193,370 | $0.1349 |
| skill-bpmn-script-jint-lifecycle | 4,289 | 13,994 | 32,205 | 696,164 | 746,652 | $0.5524 |
| skill-bpmn-script-jint-lifecycle | 4,288 | 10,432 | 28,879 | 676,077 | 719,676 | $0.4805 |
| skill-bpmn-script-jint-lifecycle | 636 | 10,581 | 28,810 | 794,052 | 834,079 | $0.5069 |
| skill-bpmn-script-jint-lifecycle | 4,302 | 13,419 | 31,774 | 1,334,923 | 1,384,418 | $0.7338 |
| skill-bpmn-script-jint-lifecycle | 4,288 | 8,960 | 27,773 | 662,179 | 703,200 | $0.4501 |
| skill-bpmn-script-task-map | 2,183 | 9,461 | 23,021 | 379,188 | 413,853 | $0.3485 |
| skill-bpmn-script-task-map | 2,184 | 11,120 | 22,826 | 414,249 | 450,379 | $0.3832 |
| skill-bpmn-script-task-map | 2,184 | 9,093 | 21,478 | 414,573 | 447,328 | $0.3479 |
| skill-bpmn-script-task-map | 2,184 | 7,710 | 21,774 | 415,401 | 447,069 | $0.3285 |
| skill-bpmn-script-task-map | 2,186 | 10,785 | 22,958 | 502,922 | 538,851 | $0.4053 |
| skill-bpmn-expr-multiinstance-iterator | 2,337 | 25,904 | 32,527 | 856,035 | 916,803 | $0.7744 |
| skill-bpmn-expr-multiinstance-iterator | 2,332 | 18,425 | 25,579 | 591,111 | 637,447 | $0.5566 |
| skill-bpmn-expr-multiinstance-iterator | 2,335 | 39,998 | 28,914 | 759,014 | 830,261 | $0.9431 |
| skill-bpmn-expr-multiinstance-iterator | 2,334 | 19,001 | 10,098 | 688,446 | 719,879 | $0.5364 |
| skill-bpmn-expr-multiinstance-iterator | 2,337 | 20,702 | 32,952 | 851,046 | 907,037 | $0.6964 |
| skill-bpmn-message-send-receive-pair | 784 | 22,001 | 39,885 | 1,641,441 | 1,704,111 | $0.9744 |
| skill-bpmn-message-send-receive-pair | 786 | 42,416 | 39,246 | 1,776,808 | 1,859,256 | $1.3188 |
| skill-bpmn-message-send-receive-pair | 4,442 | 15,296 | 40,952 | 1,884,664 | 1,945,354 | $0.9617 |
| skill-bpmn-message-send-receive-pair | 782 | 17,283 | 36,083 | 1,533,074 | 1,587,222 | $0.8568 |
| skill-bpmn-message-send-receive-pair | 4,441 | 16,407 | 42,361 | 1,834,290 | 1,897,499 | $0.9686 |
| skill-bpmn-script-jint-guidance | 2,324 | 16,865 | 26,769 | 859,175 | 905,133 | $0.6181 |
| skill-bpmn-script-jint-guidance | 2,318 | 10,891 | 26,670 | 599,549 | 639,428 | $0.4502 |
| skill-bpmn-script-jint-guidance | 2,321 | 14,367 | 30,154 | 780,019 | 826,861 | $0.5696 |
| skill-bpmn-script-jint-guidance | 2,325 | 11,961 | 29,124 | 915,887 | 959,297 | $0.5704 |
| skill-bpmn-script-jint-guidance | 2,328 | 13,977 | 31,491 | 1,060,888 | 1,108,684 | $0.6530 |
| skill-bpmn-switch | 675 | 7,820 | 23,157 | 453,365 | 485,017 | $0.3422 |
| skill-bpmn-switch | 673 | 6,560 | 20,559 | 368,400 | 396,192 | $0.2880 |
| skill-bpmn-switch | 670 | 8,672 | 19,357 | 245,173 | 273,872 | $0.2782 |
| skill-bpmn-switch | 674 | 7,889 | 22,740 | 411,257 | 442,560 | $0.3290 |
| skill-bpmn-switch | 676 | 7,127 | 21,926 | 490,885 | 520,614 | $0.3384 |
| skill-bpmn-error-event-subprocess | 750 | 13,760 | 21,589 | 292,201 | 328,300 | $0.3773 |
| skill-bpmn-error-event-subprocess | 754 | 15,210 | 28,356 | 464,909 | 509,229 | $0.4762 |
| skill-bpmn-error-event-subprocess | 751 | 12,011 | 20,804 | 332,391 | 365,957 | $0.3602 |
| skill-bpmn-error-event-subprocess | 4,407 | 11,718 | 25,466 | 400,842 | 442,433 | $0.4047 |
| skill-bpmn-error-event-subprocess | 753 | 13,155 | 24,140 | 428,075 | 466,123 | $0.4185 |
| skill-bpmn-script-task-filter | 2,190 | 9,116 | 21,563 | 293,715 | 326,584 | $0.3123 |
| skill-bpmn-script-task-filter | 2,192 | 11,625 | 22,756 | 374,361 | 410,934 | $0.3786 |
| skill-bpmn-script-task-filter | 657 | 8,346 | 18,014 | 171,805 | 198,822 | $0.2463 |
| skill-bpmn-script-task-filter | 4,319 | 11,245 | 26,908 | 478,880 | 521,352 | $0.4262 |
| skill-bpmn-script-task-filter | 2,192 | 10,866 | 22,384 | 373,578 | 409,020 | $0.3656 |
| skill-bpmn-hitl-brownfield-insert | 693 | 6,373 | 24,919 | 551,447 | 583,432 | $0.3566 |
| skill-bpmn-hitl-brownfield-insert | 693 | 7,612 | 27,389 | 545,222 | 580,916 | $0.3825 |
| skill-bpmn-hitl-brownfield-insert | 2,162 | 7,771 | 15,817 | 379,225 | 404,975 | $0.2961 |
| skill-bpmn-hitl-brownfield-insert | 2,163 | 9,172 | 18,626 | 412,639 | 442,600 | $0.3377 |
| skill-bpmn-hitl-brownfield-insert | 3,299 | 6,921 | 19,466 | 520,427 | 550,113 | $0.3428 |
| skill-bpmn-diagnose-scoped-variables | 613 | 2,218 | 11,115 | 149,347 | 163,293 | $0.1216 |
| skill-bpmn-diagnose-scoped-variables | 614 | 2,176 | 11,196 | 178,658 | 192,644 | $0.1301 |
| skill-bpmn-diagnose-scoped-variables | 614 | 2,349 | 11,418 | 150,516 | 164,897 | $0.1250 |
| skill-bpmn-diagnose-scoped-variables | 613 | 2,097 | 11,179 | 149,359 | 163,248 | $0.1200 |
| skill-bpmn-diagnose-scoped-variables | 613 | 2,032 | 11,079 | 149,343 | 163,067 | $0.1187 |
| skill-bpmn-gateway-sequence-flows | 552 | 33,543 | 25,283 | 597,908 | 657,286 | $0.7790 |
| skill-bpmn-gateway-sequence-flows | 562 | 17,592 | 31,585 | 1,042,255 | 1,091,994 | $0.6967 |
| skill-bpmn-gateway-sequence-flows | 553 | 21,847 | 27,186 | 649,081 | 698,667 | $0.6260 |
| skill-bpmn-gateway-sequence-flows | 552 | 15,696 | 31,778 | 605,044 | 653,070 | $0.5378 |
| skill-bpmn-gateway-sequence-flows | 552 | 39,942 | 34,126 | 620,675 | 695,295 | $0.9150 |
| skill-bpmn-hitl-completed-wired | 643 | 12,264 | 23,452 | 458,275 | 494,634 | $0.4113 |
| skill-bpmn-hitl-completed-wired | 648 | 13,408 | 28,717 | 644,037 | 686,810 | $0.5040 |
| skill-bpmn-hitl-completed-wired | 4,303 | 12,764 | 28,911 | 669,554 | 715,532 | $0.5137 |
| skill-bpmn-hitl-completed-wired | 650 | 9,375 | 28,224 | 722,396 | 760,645 | $0.4651 |
| skill-bpmn-hitl-completed-wired | 4,302 | 10,616 | 27,645 | 626,409 | 668,972 | $0.4637 |
| skill-bpmn-edit-update-node | 543 | 1,710 | 10,535 | 316,648 | 329,436 | $0.1618 |
| skill-bpmn-edit-update-node | 542 | 1,719 | 9,796 | 286,912 | 298,969 | $0.1502 |
| skill-bpmn-edit-update-node | 544 | 2,545 | 11,433 | 347,965 | 362,487 | $0.1871 |
| skill-bpmn-edit-update-node | 541 | 1,625 | 9,908 | 258,461 | 270,535 | $0.1407 |
| skill-bpmn-edit-update-node | 541 | 1,712 | 10,155 | 259,791 | 272,199 | $0.1433 |
| skill-bpmn-business-rule-task | 4,273 | 14,558 | 27,993 | 624,217 | 671,041 | $0.5234 |
| skill-bpmn-business-rule-task | 4,287 | 17,894 | 36,488 | 1,322,905 | 1,381,574 | $0.8150 |
| skill-bpmn-business-rule-task | 4,273 | 9,819 | 29,196 | 638,391 | 681,679 | $0.4611 |
| skill-bpmn-business-rule-task | 4,275 | 15,602 | 35,098 | 767,563 | 822,538 | $0.6087 |
| skill-bpmn-business-rule-task | 4,274 | 14,122 | 30,054 | 690,287 | 738,737 | $0.5444 |
| skill-bpmn-script-task-group-by | 2,218 | 7,911 | 22,258 | 377,982 | 410,369 | $0.3222 |
| skill-bpmn-script-task-group-by | 2,221 | 11,711 | 23,815 | 497,036 | 534,783 | $0.4207 |
| skill-bpmn-script-task-group-by | 689 | 7,690 | 20,879 | 406,959 | 436,217 | $0.3178 |
| skill-bpmn-script-task-group-by | 2,220 | 10,336 | 22,604 | 459,203 | 494,363 | $0.3842 |
| skill-bpmn-script-task-group-by | 4,345 | 8,962 | 25,080 | 476,944 | 515,331 | $0.3846 |
| skill-bpmn-loop-multiply | 2,234 | 21,166 | 23,906 | 581,729 | 629,035 | $0.5884 |
| skill-bpmn-loop-multiply | 2,235 | 20,537 | 24,825 | 636,548 | 684,145 | $0.5988 |
| skill-bpmn-loop-multiply | 703 | 12,474 | 23,541 | 545,030 | 581,748 | $0.4410 |
| skill-bpmn-loop-multiply | 704 | 22,518 | 25,037 | 593,750 | 642,009 | $0.6119 |
| skill-bpmn-loop-multiply | 3,289 | 34,132 | 25,642 | 722,112 | 785,175 | $0.8346 |
| skill-bpmn-parallel-fork-join | 684 | 4,246 | 21,554 | 409,698 | 436,182 | $0.2695 |
| skill-bpmn-parallel-fork-join | 683 | 5,992 | 21,268 | 367,390 | 395,333 | $0.2819 |
| skill-bpmn-parallel-fork-join | 683 | 7,503 | 21,945 | 369,461 | 399,592 | $0.3077 |
| skill-bpmn-parallel-fork-join | 684 | 6,912 | 21,476 | 410,029 | 439,101 | $0.3093 |
| skill-bpmn-parallel-fork-join | 686 | 8,688 | 23,792 | 489,985 | 523,151 | $0.3686 |
| skill-bpmn-feet-inches | 2,228 | 16,049 | 28,397 | 735,503 | 782,177 | $0.5746 |
| skill-bpmn-feet-inches | 2,224 | 9,098 | 27,521 | 566,513 | 605,356 | $0.4163 |
| skill-bpmn-feet-inches | 4,352 | 19,091 | 28,125 | 722,779 | 774,347 | $0.6217 |
| skill-bpmn-feet-inches | 2,237 | 17,797 | 31,585 | 1,173,774 | 1,225,393 | $0.7442 |
| skill-bpmn-feet-inches | 2,227 | 17,496 | 28,731 | 699,515 | 747,969 | $0.5867 |
| skill-bpmn-e2e-customer-escalation | 4,317 | 17,185 | 38,497 | 1,107,406 | 1,167,405 | $0.7473 |
| skill-bpmn-e2e-customer-escalation | 654 | 11,099 | 30,328 | 682,019 | 724,100 | $0.4868 |
| skill-bpmn-e2e-customer-escalation | 657 | 14,084 | 33,803 | 853,788 | 902,332 | $0.5961 |
| skill-bpmn-e2e-customer-escalation | 5,504 | 14,085 | 35,260 | 1,021,032 | 1,075,881 | $0.6663 |
| skill-bpmn-e2e-customer-escalation | 4,318 | 16,634 | 33,064 | 1,114,278 | 1,168,294 | $0.7207 |
| skill-bpmn-message-catch | 651 | 10,444 | 35,699 | 1,237,271 | 1,284,065 | $0.6637 |
| skill-bpmn-message-catch | 4,307 | 21,862 | 35,187 | 1,313,184 | 1,374,540 | $0.8668 |
| skill-bpmn-message-catch | 652 | 14,277 | 33,969 | 1,269,319 | 1,318,217 | $0.7243 |
| skill-bpmn-message-catch | 652 | 14,707 | 32,533 | 1,232,044 | 1,279,936 | $0.7142 |
| skill-bpmn-message-catch | 4,307 | 10,113 | 34,295 | 1,289,333 | 1,338,048 | $0.6800 |
| skill-bpmn-reading-list | 2,310 | 24,939 | 30,678 | 625,615 | 683,542 | $0.6837 |
| skill-bpmn-reading-list | 782 | 17,564 | 26,729 | 688,447 | 733,522 | $0.5726 |
| skill-bpmn-reading-list | 783 | 24,023 | 29,315 | 727,240 | 781,361 | $0.6908 |
| skill-bpmn-reading-list | 2,311 | 14,435 | 24,960 | 637,691 | 679,397 | $0.5084 |
| skill-bpmn-reading-list | 2,315 | 31,455 | 26,789 | 805,568 | 866,127 | $0.8209 |
| skill-bpmn-event-based-gateway | 4,395 | 16,492 | 26,863 | 493,916 | 541,666 | $0.5095 |
| skill-bpmn-event-based-gateway | 764 | 22,979 | 42,702 | 1,780,548 | 1,846,993 | $1.0413 |
| skill-bpmn-event-based-gateway | 4,400 | 9,599 | 31,769 | 741,070 | 786,838 | $0.4986 |
| skill-bpmn-event-based-gateway | 745 | 17,053 | 27,308 | 676,828 | 721,934 | $0.5635 |
| skill-bpmn-event-based-gateway | 4,398 | 7,811 | 30,735 | 639,453 | 682,397 | $0.4375 |
| skill-bpmn-agent-job | 670 | 19,662 | 26,870 | 621,556 | 668,758 | $0.5842 |
| skill-bpmn-agent-job | 671 | 30,867 | 27,730 | 659,205 | 718,473 | $0.7668 |
| skill-bpmn-agent-job | 4,329 | 41,063 | 27,102 | 784,759 | 857,253 | $0.9660 |
| skill-bpmn-agent-job | 671 | 19,374 | 27,150 | 666,787 | 713,982 | $0.5945 |
| skill-bpmn-agent-job | 674 | 21,187 | 24,893 | 746,743 | 793,497 | $0.6372 |
| skill-bpmn-dice-roller | 2,174 | 6,720 | 25,358 | 682,562 | 716,814 | $0.4072 |
| skill-bpmn-dice-roller | 2,180 | 10,666 | 26,294 | 921,999 | 961,139 | $0.5417 |
| skill-bpmn-dice-roller | 2,172 | 6,989 | 23,656 | 583,086 | 615,903 | $0.3750 |
| skill-bpmn-dice-roller | 4,296 | 8,482 | 25,449 | 563,172 | 601,399 | $0.4045 |
| skill-bpmn-dice-roller | 641 | 6,927 | 22,508 | 530,957 | 561,033 | $0.3495 |
| skill-bpmn-expr-computed-js | 5,949 | 8,611 | 30,529 | 775,361 | 820,450 | $0.4941 |
| skill-bpmn-expr-computed-js | 2,301 | 17,421 | 30,279 | 806,163 | 856,164 | $0.6236 |
| skill-bpmn-expr-computed-js | 5,951 | 11,420 | 30,124 | 858,411 | 905,906 | $0.5596 |
| skill-bpmn-expr-computed-js | 790 | 30,308 | 42,370 | 1,897,727 | 1,971,195 | $1.1852 |
| skill-bpmn-expr-computed-js | 2,819 | 17,850 | 42,714 | 2,001,447 | 2,064,830 | $1.0368 |
| skill-bpmn-operate-diagnose-minimal-fault-triage | 915 | 12,482 | 12,941 | 271,077 | 297,415 | $0.3198 |
| skill-bpmn-operate-diagnose-minimal-fault-triage | 12 | 2,281 | 12,326 | 240,560 | 255,179 | $0.1526 |
| skill-bpmn-operate-diagnose-minimal-fault-triage | 594 | 7,660 | 12,602 | 268,171 | 289,027 | $0.2444 |
| skill-bpmn-operate-diagnose-minimal-fault-triage | 596 | 7,572 | 12,881 | 358,271 | 379,320 | $0.2712 |
| skill-bpmn-operate-diagnose-minimal-fault-triage | 14 | 4,521 | 12,612 | 298,314 | 315,461 | $0.2046 |
| skill-bpmn-edit-move-node | 555 | 4,660 | 14,638 | 475,539 | 495,392 | $0.2691 |
| skill-bpmn-edit-move-node | 554 | 5,295 | 13,575 | 453,901 | 473,325 | $0.2682 |
| skill-bpmn-edit-move-node | 551 | 4,786 | 11,696 | 353,506 | 370,539 | $0.2234 |
| skill-bpmn-edit-move-node | 554 | 6,143 | 14,686 | 443,838 | 465,221 | $0.2820 |
| skill-bpmn-edit-move-node | 552 | 4,346 | 14,031 | 386,079 | 405,008 | $0.2353 |
| skill-bpmn-debug-not-validation | 523 | 5,755 | 19,770 | 362,782 | 388,830 | $0.2709 |
| skill-bpmn-debug-not-validation | 525 | 4,467 | 20,040 | 438,123 | 463,155 | $0.2752 |
| skill-bpmn-debug-not-validation | 530 | 5,391 | 21,480 | 637,637 | 665,038 | $0.3543 |
| skill-bpmn-debug-not-validation | 525 | 4,062 | 20,506 | 441,115 | 466,208 | $0.2717 |
| skill-bpmn-debug-not-validation | 525 | 3,600 | 21,206 | 443,600 | 468,931 | $0.2682 |
| skill-bpmn-debug-workflow-mocked | 575 | 1,890 | 14,737 | 281,469 | 298,671 | $0.1698 |
| skill-bpmn-debug-workflow-mocked | 4,421 | 1,716 | 14,827 | 188,059 | 209,023 | $0.1510 |
| skill-bpmn-debug-workflow-mocked | 575 | 1,834 | 14,594 | 249,873 | 266,876 | $0.1589 |
| skill-bpmn-debug-workflow-mocked | 573 | 2,090 | 15,065 | 192,987 | 210,715 | $0.1475 |
| skill-bpmn-debug-workflow-mocked | 2,265 | 1,929 | 15,040 | 257,069 | 276,303 | $0.1693 |
| skill-bpmn-diagnose-validate-fix-loop | 15 | 2,946 | 11,964 | 354,587 | 369,512 | $0.1955 |
| skill-bpmn-diagnose-validate-fix-loop | 599 | 7,773 | 16,754 | 399,943 | 425,069 | $0.3012 |
| skill-bpmn-diagnose-validate-fix-loop | 17 | 2,767 | 11,112 | 387,717 | 401,613 | $0.1995 |
| skill-bpmn-diagnose-validate-fix-loop | 15 | 2,787 | 11,755 | 351,947 | 366,504 | $0.1915 |
| skill-bpmn-diagnose-validate-fix-loop | 12 | 2,230 | 10,751 | 262,555 | 275,548 | $0.1526 |
| skill-bpmn-http-weather | 685 | 8,831 | 23,585 | 535,791 | 568,892 | $0.3837 |
| skill-bpmn-http-weather | 4,345 | 11,984 | 28,617 | 786,359 | 831,305 | $0.5360 |
| skill-bpmn-http-weather | 683 | 10,392 | 22,880 | 451,433 | 485,388 | $0.3792 |
| skill-bpmn-http-weather | 4,346 | 9,903 | 28,479 | 841,266 | 883,994 | $0.5208 |
| skill-bpmn-http-weather | 4,345 | 14,076 | 26,360 | 779,511 | 824,292 | $0.5569 |
| skill-bpmn-api-workflow-task | 4,307 | 14,318 | 32,962 | 953,360 | 1,004,947 | $0.6373 |
| skill-bpmn-api-workflow-task | 1,747 | 22,451 | 30,495 | 858,680 | 913,373 | $0.7140 |
| skill-bpmn-api-workflow-task | 4,305 | 14,284 | 35,513 | 878,852 | 932,954 | $0.6240 |
| skill-bpmn-api-workflow-task | 648 | 14,744 | 32,415 | 799,063 | 846,870 | $0.5844 |
| skill-bpmn-api-workflow-task | 647 | 26,502 | 28,953 | 709,746 | 765,848 | $0.7210 |
| skill-bpmn-multi-city-weather | 2,295 | 23,190 | 29,140 | 900,872 | 955,497 | $0.7343 |
| skill-bpmn-multi-city-weather | 2,290 | 19,341 | 27,550 | 683,392 | 732,573 | $0.6053 |
| skill-bpmn-multi-city-weather | 2,293 | 23,707 | 28,071 | 821,868 | 875,939 | $0.7143 |
| skill-bpmn-multi-city-weather | 2,289 | 26,873 | 25,881 | 627,147 | 682,190 | $0.6952 |
| skill-bpmn-multi-city-weather | 2,288 | 23,025 | 26,874 | 600,350 | 652,537 | $0.6331 |
| skill-bpmn-expr-error-mapping | 5,965 | 12,291 | 32,433 | 1,107,894 | 1,158,583 | $0.6563 |
| skill-bpmn-expr-error-mapping | 5,957 | 13,153 | 28,597 | 720,725 | 768,432 | $0.5386 |
| skill-bpmn-expr-error-mapping | 2,317 | 15,155 | 40,511 | 1,222,069 | 1,280,052 | $0.7528 |
| skill-bpmn-expr-error-mapping | 789 | 22,753 | 35,327 | 1,166,813 | 1,225,682 | $0.8262 |
| skill-bpmn-expr-error-mapping | 4,433 | 19,291 | 30,384 | 735,540 | 789,648 | $0.6373 |
| skill-bpmn-rpa-job | 4,295 | 8,184 | 25,941 | 606,981 | 645,401 | $0.4150 |
| skill-bpmn-rpa-job | 4,297 | 8,894 | 28,345 | 694,487 | 736,023 | $0.4609 |
| skill-bpmn-rpa-job | 4,303 | 10,492 | 30,119 | 976,590 | 1,021,504 | $0.5762 |
| skill-bpmn-rpa-job | 638 | 8,951 | 25,982 | 525,973 | 561,544 | $0.3914 |
| skill-bpmn-rpa-job | 638 | 11,537 | 28,543 | 543,197 | 583,915 | $0.4450 |
| skill-bpmn-diagnose-incident-root-cause | 593 | 1,699 | 11,387 | 179,220 | 192,899 | $0.1237 |
| skill-bpmn-diagnose-incident-root-cause | 593 | 2,190 | 11,502 | 178,870 | 193,155 | $0.1314 |
| skill-bpmn-diagnose-incident-root-cause | 593 | 1,864 | 11,458 | 179,200 | 193,115 | $0.1265 |
| skill-bpmn-diagnose-incident-root-cause | 594 | 1,973 | 11,599 | 179,254 | 193,420 | $0.1286 |
| skill-bpmn-diagnose-incident-root-cause | 593 | 1,677 | 11,399 | 178,869 | 192,538 | $0.1233 |
| skill-bpmn-diagnose-deployed-drift | 626 | 1,961 | 12,255 | 180,862 | 195,704 | $0.1315 |
| skill-bpmn-diagnose-deployed-drift | 1,579 | 2,334 | 12,436 | 182,162 | 198,511 | $0.1410 |
| skill-bpmn-diagnose-deployed-drift | 627 | 1,822 | 12,427 | 181,686 | 196,562 | $0.1303 |
| skill-bpmn-diagnose-deployed-drift | 628 | 2,246 | 12,668 | 221,671 | 237,213 | $0.1496 |
| skill-bpmn-diagnose-deployed-drift | 1,583 | 3,455 | 14,867 | 309,117 | 329,022 | $0.2051 |
| skill-bpmn-terminate | 631 | 8,942 | 21,167 | 326,783 | 357,523 | $0.3134 |
| skill-bpmn-terminate | 631 | 8,385 | 20,741 | 324,246 | 354,003 | $0.3027 |
| skill-bpmn-terminate | 632 | 8,726 | 20,767 | 368,682 | 398,807 | $0.3213 |
| skill-bpmn-terminate | 632 | 4,924 | 20,215 | 364,881 | 390,652 | $0.2610 |
| skill-bpmn-terminate | 632 | 6,454 | 19,930 | 364,742 | 391,758 | $0.2829 |
| skill-bpmn-inclusive-gateway-forkjoin | 4,428 | 11,444 | 29,625 | 686,666 | 732,163 | $0.5020 |
| skill-bpmn-inclusive-gateway-forkjoin | 4,426 | 11,850 | 31,632 | 591,844 | 639,752 | $0.4872 |
| skill-bpmn-inclusive-gateway-forkjoin | 770 | 14,875 | 28,965 | 528,556 | 573,166 | $0.4926 |
| skill-bpmn-inclusive-gateway-forkjoin | 769 | 6,505 | 26,063 | 475,856 | 509,193 | $0.3404 |
| skill-bpmn-inclusive-gateway-forkjoin | 770 | 11,012 | 24,396 | 508,712 | 544,890 | $0.4116 |
| skill-bpmn-contract-variant-wrappers | 4,691 | 31,047 | 53,585 | 2,101,554 | 2,190,877 | $1.3112 |
| skill-bpmn-contract-variant-wrappers | 5,098 | 27,560 | 45,705 | 1,062,094 | 1,140,457 | $0.9187 |
| skill-bpmn-contract-variant-wrappers | 4,687 | 53,663 | 50,140 | 1,875,141 | 1,983,631 | $1.5696 |
| skill-bpmn-contract-variant-wrappers | 1,468 | 49,045 | 49,452 | 2,142,594 | 2,242,559 | $1.5683 |
| skill-bpmn-contract-variant-wrappers | 5,103 | 38,906 | 47,380 | 1,328,535 | 1,419,924 | $1.1751 |
| skill-bpmn-timer-boundary-noninterrupting | 724 | 6,731 | 29,704 | 791,607 | 828,766 | $0.4520 |
| skill-bpmn-timer-boundary-noninterrupting | 716 | 12,178 | 25,790 | 442,010 | 480,694 | $0.4141 |
| skill-bpmn-timer-boundary-noninterrupting | 4,372 | 13,281 | 26,871 | 489,998 | 534,522 | $0.4601 |
| skill-bpmn-timer-boundary-noninterrupting | 4,375 | 18,630 | 30,953 | 632,323 | 686,281 | $0.5983 |
| skill-bpmn-timer-boundary-noninterrupting | 4,375 | 11,007 | 26,565 | 612,202 | 654,149 | $0.4615 |
| skill-bpmn-hitl-schema-design | 4,400 | 27,152 | 34,215 | 752,413 | 818,180 | $0.7745 |
| skill-bpmn-hitl-schema-design | 4,404 | 40,175 | 35,396 | 958,985 | 1,038,960 | $1.0363 |
| skill-bpmn-hitl-schema-design | 3,664 | 22,933 | 24,556 | 183,633 | 234,786 | $0.5022 |
| skill-bpmn-hitl-schema-design | 4,398 | 26,532 | 30,008 | 651,181 | 712,119 | $0.7191 |
| skill-bpmn-hitl-schema-design | 742 | 16,763 | 28,664 | 587,793 | 633,962 | $0.5375 |
| skill-bpmn-diagnose-stuck-gateway | 563 | 7,003 | 12,053 | 208,624 | 228,243 | $0.2145 |
| skill-bpmn-diagnose-stuck-gateway | 565 | 5,934 | 12,325 | 269,737 | 288,561 | $0.2178 |
| skill-bpmn-diagnose-stuck-gateway | 563 | 6,276 | 12,010 | 180,684 | 199,533 | $0.1951 |
| skill-bpmn-diagnose-stuck-gateway | 10 | 2,156 | 11,686 | 180,020 | 193,872 | $0.1302 |
| skill-bpmn-diagnose-stuck-gateway | 563 | 3,884 | 11,436 | 207,881 | 223,764 | $0.1652 |
| skill-bpmn-smoke-registry-discovery | 630 | 2,887 | 12,302 | 270,981 | 286,800 | $0.1726 |
| skill-bpmn-smoke-registry-discovery | 629 | 2,703 | 12,376 | 211,215 | 226,923 | $0.1522 |
| skill-bpmn-smoke-registry-discovery | 629 | 2,528 | 12,247 | 212,322 | 227,726 | $0.1494 |
| skill-bpmn-smoke-registry-discovery | 626 | 1,941 | 11,112 | 180,643 | 194,322 | $0.1269 |
| skill-bpmn-smoke-registry-discovery | 628 | 2,173 | 10,790 | 209,876 | 223,467 | $0.1379 |
| skill-bpmn-hitl-boolean-decision | 2,297 | 18,561 | 35,755 | 892,537 | 949,150 | $0.6871 |
| skill-bpmn-hitl-boolean-decision | 763 | 27,047 | 31,543 | 748,603 | 807,956 | $0.7509 |
| skill-bpmn-hitl-boolean-decision | 4,416 | 15,092 | 31,843 | 695,060 | 746,411 | $0.5676 |
| skill-bpmn-hitl-boolean-decision | 4,420 | 19,392 | 35,405 | 865,334 | 924,551 | $0.6965 |
| skill-bpmn-hitl-boolean-decision | 760 | 14,311 | 29,107 | 594,587 | 638,765 | $0.5045 |
| skill-bpmn-edit-group-to-subflow | 571 | 9,733 | 24,323 | 389,360 | 423,987 | $0.3557 |
| skill-bpmn-edit-group-to-subflow | 572 | 11,494 | 23,892 | 434,466 | 470,424 | $0.3941 |
| skill-bpmn-edit-group-to-subflow | 569 | 14,610 | 22,745 | 306,279 | 344,203 | $0.3980 |
| skill-bpmn-edit-group-to-subflow | 577 | 35,802 | 27,092 | 670,742 | 734,213 | $0.8416 |
| skill-bpmn-edit-group-to-subflow | 574 | 14,600 | 24,743 | 520,595 | 560,512 | $0.4697 |
| skill-bpmn-edit-remove-node | 573 | 4,938 | 12,153 | 302,735 | 320,399 | $0.2122 |
| skill-bpmn-edit-remove-node | 571 | 4,241 | 12,599 | 242,405 | 259,816 | $0.1853 |
| skill-bpmn-edit-remove-node | 581 | 4,385 | 14,143 | 546,142 | 565,251 | $0.2844 |
| skill-bpmn-edit-remove-node | 583 | 5,317 | 15,673 | 615,640 | 637,213 | $0.3250 |
| skill-bpmn-edit-remove-node | 579 | 4,463 | 14,638 | 478,930 | 498,610 | $0.2673 |
| skill-bpmn-error-boundary-handler | 4,410 | 16,213 | 31,698 | 594,887 | 647,208 | $0.5538 |
| skill-bpmn-error-boundary-handler | 757 | 16,954 | 28,707 | 669,797 | 716,215 | $0.5652 |
| skill-bpmn-error-boundary-handler | 758 | 14,201 | 26,406 | 677,946 | 719,311 | $0.5177 |
| skill-bpmn-error-boundary-handler | 753 | 14,971 | 24,030 | 456,579 | 496,333 | $0.4539 |
| skill-bpmn-error-boundary-handler | 754 | 9,163 | 25,228 | 513,160 | 548,305 | $0.3883 |
| skill-bpmn-hitl-rpa-wrappers | 524 | 8,023 | 26,356 | 634,141 | 669,044 | $0.4110 |
| skill-bpmn-hitl-rpa-wrappers | 4,180 | 6,317 | 28,632 | 667,675 | 706,804 | $0.4150 |
| skill-bpmn-hitl-rpa-wrappers | 524 | 8,172 | 24,710 | 595,951 | 629,357 | $0.3956 |
| skill-bpmn-hitl-rpa-wrappers | 523 | 8,930 | 26,737 | 557,619 | 593,809 | $0.4031 |
| skill-bpmn-hitl-rpa-wrappers | 4,181 | 9,606 | 28,560 | 756,043 | 798,390 | $0.4905 |
| skill-bpmn-author-validate | 656 | 5,122 | 21,176 | 481,616 | 508,570 | $0.3027 |
| skill-bpmn-author-validate | 654 | 7,789 | 21,519 | 400,561 | 430,523 | $0.3197 |
| skill-bpmn-author-validate | 655 | 8,906 | 23,499 | 449,364 | 482,424 | $0.3585 |
| skill-bpmn-author-validate | 656 | 5,374 | 21,761 | 485,128 | 512,919 | $0.3097 |
| skill-bpmn-author-validate | 656 | 5,568 | 21,081 | 483,550 | 510,855 | $0.3096 |
| skill-bpmn-event-trigger-start | 825 | 9,182 | 21,665 | 369,848 | 401,520 | $0.3324 |
| skill-bpmn-event-trigger-start | 822 | 9,080 | 21,702 | 254,624 | 286,228 | $0.2964 |
| skill-bpmn-event-trigger-start | 4,481 | 10,459 | 25,058 | 435,493 | 475,491 | $0.3949 |
| skill-bpmn-event-trigger-start | 4,485 | 11,370 | 28,183 | 611,215 | 655,253 | $0.4731 |
| skill-bpmn-event-trigger-start | 4,485 | 12,925 | 28,318 | 626,249 | 671,977 | $0.5014 |
| skill-bpmn-calculator | 649 | 17,066 | 62,174 | 740,169 | 820,058 | $0.7131 |
| skill-bpmn-calculator | 654 | 14,833 | 32,555 | 1,000,441 | 1,048,483 | $0.6467 |
| skill-bpmn-calculator | 4,299 | 11,472 | 30,898 | 552,930 | 599,599 | $0.4667 |
| skill-bpmn-calculator | 2,190 | 15,009 | 37,843 | 1,324,054 | 1,379,096 | $0.7708 |
| skill-bpmn-calculator | 661 | 19,481 | 35,123 | 1,338,221 | 1,393,486 | $0.8274 |
| skill-bpmn-edit-add-output | 551 | 3,306 | 20,747 | 403,319 | 427,923 | $0.2500 |
| skill-bpmn-edit-add-output | 551 | 2,811 | 20,076 | 403,682 | 427,120 | $0.2402 |
| skill-bpmn-edit-add-output | 552 | 2,535 | 10,470 | 343,556 | 357,113 | $0.1820 |
| skill-bpmn-edit-add-output | 551 | 2,670 | 10,138 | 313,331 | 326,690 | $0.1737 |
| skill-bpmn-edit-add-output | 553 | 3,706 | 21,903 | 484,006 | 510,168 | $0.2846 |
| skill-bpmn-e2e-wiki-pageviews | 4,345 | 29,870 | 37,268 | 855,491 | 926,974 | $0.8575 |
| skill-bpmn-e2e-wiki-pageviews | 4,094 | 41,560 | 42,608 | 1,077,192 | 1,165,454 | $1.1186 |
| skill-bpmn-e2e-wiki-pageviews | 732 | 24,243 | 32,490 | 843,985 | 901,450 | $0.7409 |
| skill-bpmn-e2e-wiki-pageviews | 4,348 | 29,049 | 34,447 | 926,419 | 994,263 | $0.8559 |
| skill-bpmn-e2e-wiki-pageviews | 4,351 | 12,535 | 32,652 | 1,031,811 | 1,081,349 | $0.6331 |
| skill-bpmn-safety-sanitize | 598 | 2,034 | 10,276 | 233,652 | 246,560 | $0.1409 |
| skill-bpmn-safety-sanitize | 597 | 2,239 | 10,314 | 205,916 | 219,066 | $0.1358 |
| skill-bpmn-safety-sanitize | 598 | 2,369 | 10,358 | 234,834 | 248,159 | $0.1466 |
| skill-bpmn-safety-sanitize | 599 | 2,335 | 10,554 | 264,267 | 277,755 | $0.1557 |
| skill-bpmn-safety-sanitize | 598 | 2,281 | 10,550 | 234,822 | 248,251 | $0.1460 |
| skill-bpmn-edit-add-node | 565 | 8,532 | 24,698 | 545,432 | 579,227 | $0.3859 |
| skill-bpmn-edit-add-node | 560 | 8,624 | 22,631 | 337,322 | 369,137 | $0.3171 |
| skill-bpmn-edit-add-node | 560 | 7,352 | 12,560 | 274,782 | 295,254 | $0.2415 |
| skill-bpmn-edit-add-node | 565 | 5,571 | 25,132 | 542,310 | 573,578 | $0.3422 |
| skill-bpmn-edit-add-node | 566 | 7,204 | 13,722 | 457,207 | 478,699 | $0.2984 |
| skill-bpmn-e2e-live-debug | 6,422 | 24,443 | 72,917 | 7,938,159 | 8,041,941 | $3.0408 |
| skill-bpmn-e2e-live-debug | 4,264 | 26,199 | 83,369 | 8,540,598 | 8,654,430 | $3.2806 |
| skill-bpmn-e2e-live-debug | 4,264 | 30,994 | 90,890 | 8,867,985 | 8,994,133 | $3.4789 |
| skill-bpmn-e2e-live-debug | 6,422 | 27,756 | 79,932 | 8,094,083 | 8,208,193 | $3.1636 |
| skill-bpmn-e2e-live-debug | 4,264 | 29,941 | 82,326 | 7,975,722 | 8,092,253 | $3.1633 |
| skill-bpmn-registry-discovery | 520 | 3,045 | 13,249 | 278,536 | 295,350 | $0.1805 |
| skill-bpmn-registry-discovery | 519 | 2,444 | 11,791 | 240,839 | 255,593 | $0.1547 |
| skill-bpmn-registry-discovery | 519 | 2,089 | 11,502 | 239,411 | 253,521 | $0.1478 |
| skill-bpmn-registry-discovery | 520 | 3,167 | 12,653 | 272,795 | 289,135 | $0.1784 |
| skill-bpmn-registry-discovery | 521 | 3,107 | 12,669 | 301,081 | 317,378 | $0.1860 |
| skill-bpmn-subprocess | 668 | 12,810 | 26,442 | 538,214 | 578,134 | $0.4548 |
| skill-bpmn-subprocess | 661 | 26,528 | 26,256 | 260,725 | 314,170 | $0.5766 |
| skill-bpmn-subprocess | 662 | 9,499 | 20,590 | 288,661 | 319,412 | $0.3083 |
| skill-bpmn-subprocess | 669 | 8,817 | 24,765 | 600,089 | 634,340 | $0.4072 |
| skill-bpmn-subprocess | 666 | 20,055 | 23,214 | 464,854 | 508,789 | $0.5293 |
| skill-bpmn-timer-start | 4,377 | 8,970 | 26,035 | 609,532 | 648,914 | $0.4282 |
| skill-bpmn-timer-start | 721 | 6,855 | 22,776 | 533,622 | 563,974 | $0.3505 |
| skill-bpmn-timer-start | 4,376 | 7,319 | 26,113 | 562,166 | 599,974 | $0.3895 |
| skill-bpmn-timer-start | 4,381 | 10,582 | 28,152 | 788,151 | 831,266 | $0.5139 |
| skill-bpmn-timer-start | 4,382 | 9,080 | 27,156 | 831,273 | 871,891 | $0.5006 |
| skill-bpmn-queue-create-and-wait | 745 | 6,792 | 22,574 | 491,793 | 521,904 | $0.3363 |
| skill-bpmn-queue-create-and-wait | 4,406 | 10,515 | 28,514 | 787,034 | 830,469 | $0.5140 |
| skill-bpmn-queue-create-and-wait | 4,402 | 9,509 | 25,544 | 608,776 | 648,231 | $0.4343 |
| skill-bpmn-queue-create-and-wait | 749 | 12,371 | 25,517 | 654,999 | 693,636 | $0.4800 |
| skill-bpmn-queue-create-and-wait | 4,404 | 12,200 | 27,959 | 702,112 | 746,675 | $0.5117 |
| skill-bpmn-e2e-invoice-exception-triage | 4,232 | 13,465 | 35,152 | 834,192 | 887,041 | $0.5967 |
| skill-bpmn-e2e-invoice-exception-triage | 580 | 17,171 | 32,149 | 857,094 | 906,994 | $0.6370 |
| skill-bpmn-e2e-invoice-exception-triage | 586 | 19,855 | 51,460 | 1,145,339 | 1,217,240 | $0.8362 |
| skill-bpmn-e2e-invoice-exception-triage | 4,236 | 11,918 | 33,646 | 941,597 | 991,397 | $0.6001 |
| skill-bpmn-e2e-invoice-exception-triage | 585 | 9,029 | 34,674 | 1,080,629 | 1,124,917 | $0.5914 |
| skill-bpmn-debug-instance-inspect | 566 | 2,197 | 12,148 | 211,824 | 226,735 | $0.1438 |
| skill-bpmn-debug-instance-inspect | 566 | 2,048 | 14,945 | 218,432 | 235,991 | $0.1540 |
| skill-bpmn-debug-instance-inspect | 566 | 2,085 | 14,821 | 248,405 | 265,877 | $0.1631 |
| skill-bpmn-debug-instance-inspect | 566 | 2,161 | 14,755 | 248,414 | 265,896 | $0.1640 |
| skill-bpmn-debug-instance-inspect | 569 | 2,096 | 11,672 | 297,795 | 312,132 | $0.1663 |
| skill-bpmn-hitl-result-downstream | 690 | 14,253 | 46,973 | 566,454 | 628,370 | $0.5619 |
| skill-bpmn-hitl-result-downstream | 4,345 | 11,790 | 29,937 | 641,971 | 688,043 | $0.4947 |
| skill-bpmn-hitl-result-downstream | 4,351 | 11,778 | 29,413 | 855,148 | 900,690 | $0.5566 |
| skill-bpmn-hitl-result-downstream | 4,349 | 14,143 | 30,317 | 775,511 | 824,320 | $0.5715 |
| skill-bpmn-hitl-result-downstream | 689 | 13,599 | 26,960 | 568,945 | 610,193 | $0.4778 |
| skill-bpmn-hitl-multi-outcome-routing | 698 | 25,757 | 50,124 | 1,104,096 | 1,180,675 | $0.9076 |
| skill-bpmn-hitl-multi-outcome-routing | 4,344 | 25,459 | 30,509 | 777,546 | 837,858 | $0.7426 |
| skill-bpmn-hitl-multi-outcome-routing | 684 | 8,986 | 27,240 | 484,990 | 521,900 | $0.3845 |
| skill-bpmn-hitl-multi-outcome-routing | 4,342 | 13,401 | 30,945 | 645,172 | 693,860 | $0.5236 |
| skill-bpmn-hitl-multi-outcome-routing | 688 | 11,213 | 27,863 | 663,800 | 703,564 | $0.4739 |
| skill-bpmn-simple-approval-bpmn | 744 | 20,405 | 54,969 | 945,335 | 1,021,453 | $0.7980 |
| skill-bpmn-simple-approval-bpmn | 4,399 | 35,734 | 52,881 | 974,536 | 1,067,550 | $1.0399 |
| skill-bpmn-simple-approval-bpmn | 4,409 | 31,504 | 36,766 | 1,528,940 | 1,601,619 | $1.0823 |
| skill-bpmn-simple-approval-bpmn | 4,399 | 27,688 | 35,974 | 1,004,500 | 1,072,561 | $0.8648 |
| skill-bpmn-simple-approval-bpmn | 4,398 | 26,341 | 35,209 | 958,243 | 1,024,191 | $0.8278 |
| skill-bpmn-integration-service-boundary | 4,209 | 16,376 | 51,724 | 703,211 | 775,520 | $0.6632 |
| skill-bpmn-integration-service-boundary | 4,222 | 20,161 | 54,433 | 1,294,297 | 1,373,113 | $0.9075 |
| skill-bpmn-integration-service-boundary | 4,226 | 26,549 | 55,681 | 1,513,483 | 1,599,939 | $1.0738 |
| skill-bpmn-integration-service-boundary | 4,210 | 15,723 | 34,316 | 796,666 | 850,915 | $0.6162 |
| skill-bpmn-integration-service-boundary | 4,221 | 18,409 | 59,747 | 1,344,809 | 1,427,186 | $0.9163 |


## Command Telemetry

**Total Commands**: 6361
**Success Rate**: 5693/6361 (89.5%)

### Commands by Tool

| Tool | Count | % |
|------|-------|---|
| Bash | 4679 | 73.6% |
| Read | 788 | 12.4% |
| Skill | 350 | 5.5% |
| Write | 317 | 5.0% |
| Edit | 214 | 3.4% |
| Glob | 5 | 0.1% |
| TaskUpdate | 4 | 0.1% |
| TaskCreate | 2 | 0.0% |
| Grep | 1 | 0.0% |
| TaskStop | 1 | 0.0% |

### Performance

- **Average Command Time**: 807.9ms
- **Total Command Time**: 5139.36s

### Slowest Commands

| Tool | Duration | Parameters |
|------|----------|------------|
| Bash | 120047ms | {'command': '# There\'s a device_code grant type a... |
| Bash | 49487ms | {'command': 'uip maestro bpmn registry pull --outp... |
| Bash | 48842ms | {'command': 'uip maestro bpmn registry pull 2>&1 |... |
| Bash | 36493ms | {'command': 'grep -rn "\\.uipath\\|UIPATH_CLI_ENAB... |
| Bash | 34254ms | {'command': 'uip maestro bpmn registry pull --outp... |

**Most Common Pattern**: `Bash → Bash → Bash`

**Skill Tool Invoked**: 350 time(s)

## Agent Settings

- **Permission Mode**: acceptEdits
- **Allowed Tools**: Skill, Bash, Read, Write, Edit, Glob, Grep
- **Model**: us.anthropic.claude-sonnet-4-6
- **Max Turns**: 50
- **System Prompt**: You are a coding agent. Do not access files in sibling runs/* directories. Everywhere else is permitted. 
- **Plugins**: /home/azureuser/projects/skills/tmp

## Environment

- **git_commit**: unknown
- **skills_git_commit**: unknown
- **cli_version**: 1.197.0-alpha.20260626.7673
- **tool_plugins**: {'agent-tool': '1.197.0', 'agenthub-tool': '1.197.0', 'codedagent-tool': '1.197.0', 'data-fabric-tool': '1.197.0', 'functions-tool': '1.197.0', 'gov-tool': '1.197.0', 'insights-tool': '1.197.0', 'integrationservice-tool': '1.197.0', 'ixp-tool': '1.197.0', 'maestro-tool': '1.197.0', 'orchestrator-tool': '1.197.0', 'solution-tool': '1.197.0', 'tasks-tool': '1.197.0', 'test-manager-tool': '1.197.0'}
- **coder_eval**: 0.8.4
- **claude_code_cli**: 2.1.177 (Claude Code)
- **uv**: uv 0.11.28 (x86_64-unknown-linux-gnu)
- **anthropic**: 0.102.0
- **openai**: 2.46.0
- **pydantic**: 2.12.5
- **api_routing**: aws_bedrock
- **aws_region**: us-east-2
- **bedrock_model**: us.anthropic.claude-sonnet-4-6