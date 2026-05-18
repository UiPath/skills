# Maestro Playbooks

**Investigation guide:** [investigation_guide.md](./investigation_guide.md) — data correlation rules and testing prerequisites for Maestro investigations

**Top-20 production errors (telemetry-ranked, last 7 days as of 2026-03-19):** the table below covers the highest-volume Maestro errors first, with a generic table after for additional symptoms. Source: [PO.BpmnEngine PR #3092](https://github.com/UiPath/PO.BpmnEngine/pull/3092).

## Top 20 Production Errors

| # | Error | Status | Error Code | Playbook |
|---|-------|:------:|------------|----------|
| 1 | Personal Automation quota exceeded | 502 | — | [personal-automation-quota.md](./playbooks/personal-automation-quota.md) |
| 2 | Job's associated process could not be found | 404 | 170007 | [process-not-found-404.md](./playbooks/process-not-found-404.md) |
| 3 | No unattended robot permissions in folder | 409 | #1671 | [unattended-robot-permissions.md](./playbooks/unattended-robot-permissions.md) |
| 4 | Job Operation Timeout | 502 | — | [job-operation-timeout.md](./playbooks/job-operation-timeout.md) |
| 5 | Input does not conform to schema | 400 | — | [input-schema-mismatch.md](./playbooks/input-schema-mismatch.md) |
| 6 | Missing value for required parameter | 400 | — | [missing-required-parameter.md](./playbooks/missing-required-parameter.md) |
| 7 | Generic Error_400 | 400 | — | [generic-error-400.md](./playbooks/generic-error-400.md) |
| 8 | Expression evaluation — property not found | 400 | 400300–400302 | [expression-evaluation-errors.md](./playbooks/expression-evaluation-errors.md) |
| 9 | No outgoing flow condition met | 400 | 400001 | [gateway-no-outgoing-flow.md](./playbooks/gateway-no-outgoing-flow.md) |
| 10 | Loop detected (>100 executions) | 400 | 400009 | [loop-detected.md](./playbooks/loop-detected.md) |
| 11 | 'File' field required (DAP-RT-1003) | 502 | DAP-RT-1003 | [file-field-required.md](./playbooks/file-field-required.md) |
| 12 | Integration Services 404 | 404 | 102001 | [integration-service-404.md](./playbooks/integration-service-404.md) |
| 13 | Insufficient funds / credits | 400 | — | [insufficient-funds.md](./playbooks/insufficient-funds.md) |
| 14 | Marker element input collection is null | 400 | 400007 | [marker-input-null.md](./playbooks/marker-input-null.md) |
| 15 | Integration Services 400 | 400 | 102003 | [integration-service-400.md](./playbooks/integration-service-400.md) |
| 16 | Folder does not exist or no access | 400 | #1100 | [folder-not-accessible.md](./playbooks/folder-not-accessible.md) |
| 17 | No machine with Unattended/NonProduction runtimes | 409 | #2818 | [no-suitable-runtime-machine.md](./playbooks/no-suitable-runtime-machine.md) |
| 18 | No Message events found | 400 | — | [no-message-events.md](./playbooks/no-message-events.md) |
| 19 | Foreground job requires unattended robot | 409 | #1230 | [foreground-unattended-robot.md](./playbooks/foreground-unattended-robot.md) |
| 20 | Index outside bounds of array | 502 | — | [index-out-of-bounds.md](./playbooks/index-out-of-bounds.md) |

> **API debuggability:** errors #1, #3, #5, #6, #8, #11, #13, #16, #19 are **Fully Troubleshootable** from PIMS API alone. Errors #2, #4, #10, #14, #17 are **Partially Troubleshootable** — incident gives a starting point but needs Orchestrator or BPMN inspection. Errors #7, #9, #12, #15, #18, #20 are **Not Troubleshootable** from API alone today; ask the user for additional artifacts (`.bpmn`, bindings, full stack trace).
>
> Error #9 (`NoOutgoingFlow`) becomes Fully Troubleshootable once [PR #3092](https://github.com/UiPath/PO.BpmnEngine/pull/3092) lands and the `IncludeGatewayDebugInfoInIncidents` targeted feature flag is enabled.

## Additional Symptoms (Lower Volume)

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Maestro Service Disabled | High | Designer pane blank or errors after license change — service silently disabled | [maestro-service-disabled.md](./playbooks/maestro-service-disabled.md) |
| Deployment Error — EMAIL_RECEIVED | High | Error code 4006, IS/packaging sync issue with Outlook email trigger | [deployment-email-received.md](./playbooks/deployment-email-received.md) |
| Deployment Error — DateTime Input | High | "Package entry points definition is invalid" due to DateTime BPMN input parameters | [deployment-datetime-input.md](./playbooks/deployment-datetime-input.md) |
| JS Runtime Discrepancy | High | JS expression passes in editor but fails at runtime — Jint lacks browser APIs | [js-runtime-discrepancy.md](./playbooks/js-runtime-discrepancy.md) |
| Agent Traces Disappearing | High | Traces missing due to AI Trust Layer Trace TTL policy | [agent-traces-disappearing.md](./playbooks/agent-traces-disappearing.md) |
| Autopilot 429 Too Many Requests | High | HTTP 429 rate limiting on Autopilot features | [autopilot-429.md](./playbooks/autopilot-429.md) |
| Multi-Instance Marker InvalidCastException | High | JS array cannot be cast to ExpressionList — switch to C# expressions | [marker-invalid-cast.md](./playbooks/marker-invalid-cast.md) |
| Attachment Not Found After Retention | High | Files disappear when job retention deletes the owning job | [attachment-not-found.md](./playbooks/attachment-not-found.md) |
| Argument Mismatch (400) — Generic | Medium | Generic 400 argument mismatch; route to #5 or #6 for specifics | [argument-mismatch-400.md](./playbooks/argument-mismatch-400.md) |
| Service Task Child Job Faulted (170002) | High | Error 170002, child job faulted — chase child error as root cause, add boundary error event | [service-task-child-job-faulted.md](./playbooks/service-task-child-job-faulted.md) |
| Debug vs Deploy Mismatch | Medium | Process works in debug but fails after deploy — identity, permissions, or bindings | [debug-vs-deploy.md](./playbooks/debug-vs-deploy.md) |
| Deployment Failure | Medium | Solution deployment fails — duplicate entry points, trigger conflicts, or stale references | [deployment-failure.md](./playbooks/deployment-failure.md) |
| Variable and Expression Errors | Medium | Missing output variables, assignment errors, case sensitivity in gateway conditions | [variable-expression-errors.md](./playbooks/variable-expression-errors.md) |
| Boundary Event / Duplicate Task | Medium | Task running twice, boundary events firing unexpectedly, missing incident logging | [boundary-event-duplicate-task.md](./playbooks/boundary-event-duplicate-task.md) |
| File Handling Issues | Medium | Files not passed correctly, attachment not found, file type incompatibility | [file-handling.md](./playbooks/file-handling.md) |
| Multi-Instance Parallel Marker | Medium | Parallel marker failures, collection size limits, NoneType errors | [multi-instance-parallel.md](./playbooks/multi-instance-parallel.md) |
| BPMN Job Stuck | Low | Instance stuck with no progress or error — disconnected connection, child job not created, or backend delay | [bpmn-job-stuck.md](./playbooks/bpmn-job-stuck.md) |
