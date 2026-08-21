# Experiment Report: skill-tests-smoke

**Description**: Linux PR-gate smoke tests — docker isolation, fast turn budget
**Variants**: default
**Total Duration**: 545.3s

## Aggregate Metrics

| Metric | default |
|--------|--------|
| Tasks Run | 70 |
| Succeeded | 64 |
| Failed | 5 |
| Errors | 1 |
| Success Rate | 92.8% |
| Score | 0.975 ± 0.119 |
| Avg Duration (s) | 193.0 ± 125.8 |
| Assistant Turns | 28.7 ± 17.5 |
| Tokens | 3,858,568 ± 4,935,325 |
| Replicates/task | 5 |

## Win Rates

- **default**: 70/70 tasks (100%)

## Per-Task Comparison

| Task | default | Best | Spread | Reps |
|------|------|------|--------|------|
| skill-bpmn-timer | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-callactivity-agentic-process | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-diagnose-job-traces | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-script-jint-lifecycle | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-script-task-map | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-expr-multiinstance-iterator | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-message-send-receive-pair | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-script-jint-guidance | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-switch | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-error-event-subprocess | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-script-task-filter | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-hitl-brownfield-insert | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-diagnose-scoped-variables | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-gateway-sequence-flows | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-hitl-completed-wired | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-edit-update-node | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-business-rule-task | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-script-task-group-by | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-loop-multiply | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-parallel-fork-join | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-feet-inches | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-e2e-customer-escalation | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-message-catch | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-reading-list | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-event-based-gateway | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-agent-job | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-dice-roller | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-expr-computed-js | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-operate-diagnose-minimal-fault-triage | 0.980 (-) | default | 0.000 | 5 |
| skill-bpmn-edit-move-node | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-debug-not-validation | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-debug-workflow-mocked | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-diagnose-validate-fix-loop | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-http-weather | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-api-workflow-task | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-multi-city-weather | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-expr-error-mapping | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-rpa-job | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-diagnose-incident-root-cause | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-diagnose-deployed-drift | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-terminate | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-inclusive-gateway-forkjoin | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-contract-variant-wrappers | 0.833 (-) | default | 0.000 | 5 |
| skill-bpmn-timer-boundary-noninterrupting | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-hitl-schema-design | 0.800 (!) | default | 0.000 | 5 |
| skill-bpmn-diagnose-stuck-gateway | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-smoke-registry-discovery | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-hitl-boolean-decision | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-edit-group-to-subflow | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-edit-remove-node | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-error-boundary-handler | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-hitl-rpa-wrappers | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-author-validate | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-event-trigger-start | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-calculator | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-edit-add-output | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-e2e-wiki-pageviews | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-safety-sanitize | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-edit-add-node | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-e2e-live-debug | 0.167 (M) | default | 0.000 | 5 |
| skill-bpmn-registry-discovery | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-subprocess | 0.978 (-) | default | 0.000 | 5 |
| skill-bpmn-timer-start | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-queue-create-and-wait | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-e2e-invoice-exception-triage | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-debug-instance-inspect | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-hitl-result-downstream | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-hitl-multi-outcome-routing | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-simple-approval-bpmn | 1.000 (+) | default | 0.000 | 5 |
| skill-bpmn-integration-service-boundary | 0.500 (-) | default | 0.000 | 5 |

## Replicate Statistics

| Variant | Replicates/task | Mean score | 95% CI | Pass-rate (Wilson 95%) |
|---------|-----------------|------------|--------|------------------------|
| default | 5 | 0.975 | [0.960, 0.990] | 339/350 [0.94, 0.98] |