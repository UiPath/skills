# Experiment Report: skill-tests-smoke

**Description**: Linux PR-gate smoke tests — docker isolation, fast turn budget
**Variants**: default
**Total Duration**: 2630.7s

## Aggregate Metrics

| Metric | default |
|--------|--------|
| Tasks Run | 70 |
| Succeeded | 60 |
| Failed | 7 |
| Errors | 3 |
| Pass Rate | 85.7% |
| Score | 0.885 ± 0.299 |
| Avg Duration (s) | 273.6 ± 318.4 |
| Assistant Turns | 52.2 ± 36.1 |
| Tokens | 2,161,387 ± 1,941,535 |

## Win Rates

- **default**: 70/70 tasks (100%)

## Per-Task Comparison

| Task | default | Best | Spread |
|------|------|------|--------|
| skill-bpmn-e2e-customer-escalation | 1.000 (+) | default | 0.000 |
| skill-bpmn-hitl-brownfield-insert | 1.000 (+) | default | 0.000 |
| skill-bpmn-multi-city-weather | 1.000 (+) | default | 0.000 |
| skill-bpmn-feet-inches | 1.000 (+) | default | 0.000 |
| skill-bpmn-script-jint-guidance | 1.000 (+) | default | 0.000 |
| skill-bpmn-agent-job | 1.000 (+) | default | 0.000 |
| skill-bpmn-diagnose-scoped-variables | 1.000 (+) | default | 0.000 |
| skill-bpmn-message-catch | 1.000 (+) | default | 0.000 |
| skill-bpmn-hitl-result-downstream | 1.000 (+) | default | 0.000 |
| skill-bpmn-integration-service-boundary | 0.167 (-) | default | 0.000 |
| skill-bpmn-subprocess | 1.000 (+) | default | 0.000 |
| skill-bpmn-operate-diagnose-minimal-fault-triage | 1.000 (+) | default | 0.000 |
| skill-bpmn-safety-sanitize | 1.000 (+) | default | 0.000 |
| skill-bpmn-author-validate | 1.000 (+) | default | 0.000 |
| skill-bpmn-dice-roller | 1.000 (+) | default | 0.000 |
| skill-bpmn-event-based-gateway | 1.000 (+) | default | 0.000 |
| skill-bpmn-edit-move-node | 1.000 (+) | default | 0.000 |
| skill-bpmn-reading-list | 1.000 (+) | default | 0.000 |
| skill-bpmn-gateway-sequence-flows | 1.000 (+) | default | 0.000 |
| skill-bpmn-hitl-completed-wired | 1.000 (+) | default | 0.000 |
| skill-bpmn-error-event-subprocess | 1.000 (+) | default | 0.000 |
| skill-bpmn-expr-multiinstance-iterator | 1.000 (+) | default | 0.000 |
| skill-bpmn-e2e-invoice-exception-triage | 1.000 (+) | default | 0.000 |
| skill-bpmn-registry-discovery | 1.000 (+) | default | 0.000 |
| skill-bpmn-hitl-schema-design | 0.000 (!) | default | 0.000 |
| skill-bpmn-switch | 1.000 (+) | default | 0.000 |
| skill-bpmn-timer-boundary-noninterrupting | 1.000 (+) | default | 0.000 |
| skill-bpmn-debug-workflow-mocked | 1.000 (+) | default | 0.000 |
| skill-bpmn-script-task-group-by | 1.000 (+) | default | 0.000 |
| skill-bpmn-timer | 1.000 (+) | default | 0.000 |
| skill-bpmn-business-rule-task | 0.200 (M) | default | 0.000 |
| skill-bpmn-calculator | 1.000 (+) | default | 0.000 |
| skill-bpmn-callactivity-agentic-process | 1.000 (+) | default | 0.000 |
| skill-bpmn-inclusive-gateway-forkjoin | 1.000 (+) | default | 0.000 |
| skill-bpmn-loop-multiply | 1.000 (+) | default | 0.000 |
| skill-bpmn-rpa-job | 1.000 (+) | default | 0.000 |
| skill-bpmn-hitl-multi-outcome-routing | 1.000 (+) | default | 0.000 |
| skill-bpmn-diagnose-stuck-gateway | 1.000 (+) | default | 0.000 |
| skill-bpmn-timer-start | 1.000 (+) | default | 0.000 |
| skill-bpmn-queue-create-and-wait | 1.000 (+) | default | 0.000 |
| skill-bpmn-edit-update-node | 1.000 (+) | default | 0.000 |
| skill-bpmn-debug-not-validation | 0.882 (-) | default | 0.000 |
| skill-bpmn-diagnose-job-traces | 1.000 (+) | default | 0.000 |
| skill-bpmn-diagnose-incident-root-cause | 1.000 (+) | default | 0.000 |
| skill-bpmn-script-task-map | 0.000 (M) | default | 0.000 |
| skill-bpmn-diagnose-deployed-drift | 1.000 (+) | default | 0.000 |
| skill-bpmn-contract-variant-wrappers | 1.000 (+) | default | 0.000 |
| skill-bpmn-edit-group-to-subflow | 1.000 (+) | default | 0.000 |
| skill-bpmn-e2e-live-debug | 1.000 (+) | default | 0.000 |
| skill-bpmn-script-jint-lifecycle | 0.200 (-) | default | 0.000 |
| skill-bpmn-terminate | 1.000 (+) | default | 0.000 |
| skill-bpmn-http-weather | 1.000 (+) | default | 0.000 |
| skill-bpmn-event-trigger-start | 1.000 (+) | default | 0.000 |
| skill-bpmn-hitl-boolean-decision | 1.000 (+) | default | 0.000 |
| skill-bpmn-simple-approval-bpmn | 0.000 (!) | default | 0.000 |
| skill-bpmn-api-workflow-task | 0.200 (M) | default | 0.000 |
| skill-bpmn-edit-remove-node | 0.333 (-) | default | 0.000 |
| skill-bpmn-diagnose-validate-fix-loop | 1.000 (+) | default | 0.000 |
| skill-bpmn-debug-instance-inspect | 1.000 (+) | default | 0.000 |
| skill-bpmn-edit-add-output | 1.000 (+) | default | 0.000 |
| skill-bpmn-smoke-registry-discovery | 1.000 (+) | default | 0.000 |
| skill-bpmn-hitl-rpa-wrappers | 1.000 (+) | default | 0.000 |
| skill-bpmn-edit-add-node | 1.000 (+) | default | 0.000 |
| skill-bpmn-expr-error-mapping | 1.000 (+) | default | 0.000 |
| skill-bpmn-script-task-filter | 1.000 (+) | default | 0.000 |
| skill-bpmn-error-boundary-handler | 1.000 (+) | default | 0.000 |
| skill-bpmn-e2e-wiki-pageviews | 1.000 (+) | default | 0.000 |
| skill-bpmn-message-send-receive-pair | 0.000 (!) | default | 0.000 |
| skill-bpmn-parallel-fork-join | 1.000 (+) | default | 0.000 |
| skill-bpmn-expr-computed-js | 1.000 (+) | default | 0.000 |