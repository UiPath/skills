# Maestro Playbooks

**Investigation guide:** [investigation_guide.md](./investigation_guide.md) — data correlation rules and testing prerequisites for Maestro investigations

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
| No Suitable Runtime Machine (409) | High | HTTP 409, no Unattended/NonProduction robots available in folder | [no-suitable-runtime-machine.md](./playbooks/no-suitable-runtime-machine.md) |
| Argument Mismatch (400) | High | HTTP 400, argument values did not match definitions | [argument-mismatch-400.md](./playbooks/argument-mismatch-400.md) |
| Integration Service Failure (404) | High | HTTP 404 during IS call, resource or endpoint not found | [integration-service-404.md](./playbooks/integration-service-404.md) |
| Debug vs Deploy Mismatch | Medium | Process works in debug but fails after deploy — identity, permissions, or bindings | [debug-vs-deploy.md](./playbooks/debug-vs-deploy.md) |
| Deployment Failure | Medium | Solution deployment fails — duplicate entry points, trigger conflicts, or stale references | [deployment-failure.md](./playbooks/deployment-failure.md) |
| Variable and Expression Errors | Medium | Missing output variables, assignment errors, case sensitivity in gateway conditions | [variable-expression-errors.md](./playbooks/variable-expression-errors.md) |
| Boundary Event / Duplicate Task | Medium | Task running twice, boundary events firing unexpectedly, missing incident logging | [boundary-event-duplicate-task.md](./playbooks/boundary-event-duplicate-task.md) |
| File Handling Issues | Medium | Files not passed correctly, attachment not found, file type incompatibility | [file-handling.md](./playbooks/file-handling.md) |
| Multi-Instance Parallel Marker | Medium | Parallel marker failures, collection size limits, NoneType errors | [multi-instance-parallel.md](./playbooks/multi-instance-parallel.md) |
| Expression Evaluation and Input Errors | Medium | Null inputs, missing parameters, GUID parse errors | [expression-evaluation-errors.md](./playbooks/expression-evaluation-errors.md) |
| BPMN Job Stuck | Low | Instance stuck with no progress or error — disconnected connection, child job not created, or backend delay | [bpmn-job-stuck.md](./playbooks/bpmn-job-stuck.md) |
