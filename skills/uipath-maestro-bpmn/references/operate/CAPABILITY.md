# Operate - Package, ship, run, and manage BPMN processes

Capability index for BPMN Process Orchestration lifecycle work. Operate owns the steps that prepare a BPMN project
for the cloud and the steps that touch the cloud: package generation, Studio Web upload, Orchestrator publish/deploy,
debug/run, job inspection, and instance lifecycle.
These actions may contact UiPath services or external systems.

> **Where you came from / where to go next.** Operate is downstream of Author (model-authored BPMN plus CLI
> validation/enrichment) and upstream of Diagnose (runtime faults and state inspection).
> BPMN source work lives in [author/CAPABILITY.md](../author/CAPABILITY.md);
> post-run investigation lives in [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md).
>
> **Inherits universal rules from [SKILL.md](../../SKILL.md).** In particular: BPMN XML is source, generated package
> files and Integration Service enrichment are CLI-owned, parsed CLI output uses `--output json`, and
> upload/publish/deploy/debug/run/lifecycle actions require explicit user consent.

## When to use this capability

- Package a Maestro BPMN Process Orchestration project.
- Upload a solution containing the BPMN project to Studio Web.
- Publish or deploy a packaged process when explicitly requested.
- Debug or run a process instance after explicit consent.
- Inspect jobs, processes, process versions, instances, variables, incidents, and traces.
- Pause, resume, cancel, retry, migrate, or move a running instance when explicitly requested.
- Refresh or regenerate CLI-owned package metadata before a cloud action.

## Critical rules

1. **Never debug or run without explicit consent** - execution can call connectors, start child processes, create Action
   Center work, mutate queues, send messages, or update external systems.
2. **Ask before every cloud-side mutation** - upload, publish, deploy, debug, process run, pause, resume, cancel, retry,
   migrate, and cursor movement require a clear user decision for that action.
3. **Validate before operate** - do not upload, publish, debug, or run until Author validation is complete or the user
   explicitly accepts known draft warnings.
4. **Refresh or regenerate package metadata before cloud actions** - stale `bindings_v2.json`, `entry-points.json`,
   `operate.json`, or `package-descriptor.json` can break import or runtime even when the BPMN source is correct.
5. **Keep source and package ownership clear** - fix process structure, variables, mappings, events, and documented non-IS
   extensions in `.bpmn`; rerun CLI generation/enrichment for generated package JSON and Integration Service metadata.
6. **Default publish wording to Studio Web upload unless the user explicitly asks for Orchestrator deployment** - keep deploy semantics explicit.
7. **Always include folder context on runtime commands that require it** - `process run` takes `<FOLDER_KEY>` and
   `instance`/`incident get` commands require `--folder-key` or `-f`.
8. **Report identifiers plainly** - summarize returned Studio Web URLs, package paths, solution IDs, process keys,
   job keys, instance IDs, run IDs, final status, and folder context when available.
9. **Do not retry before diagnosis** - identify root cause first, then decide whether retry, cancel, migrate,
   cursor movement, or source repair is appropriate.

## Workflow

| Journey | Read |
| --- | --- |
| Package and upload or publish | [references/ship.md](references/ship.md) |
| Debug/run and inspect execution | [references/run.md](references/run.md) |
| Manage a running instance | [references/manage.md](references/manage.md) |

## Common tasks

| I need to... | Read these |
| --- | --- |
| Prepare for Studio Web upload | [references/ship.md](references/ship.md), [shared/project-layout.md](../shared/project-layout.md) |
| Deploy to Orchestrator | [references/ship.md](references/ship.md) |
| Run/debug a BPMN process | [references/run.md](references/run.md) |
| Inspect job or instance status | [references/run.md](references/run.md) |
| Pause/resume/cancel/retry | [references/manage.md](references/manage.md) |
| Migrate or move an instance cursor | [references/manage.md](references/manage.md) |
| Correlate a running instance to deployed BPMN | [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md) |
| Diagnose a failed run | [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md) |

## Anti-patterns

- **Never treat package generation as source authoring** - generated files reflect BPMN plus enrichment.
- **Never upload a draft with unresolved Integration Service enrichment unless the user explicitly wants a non-executable
  draft review.**
- **Never run lifecycle commands just to validate XML.**
- **Never default to Orchestrator deploy when the user says "publish."** Use Studio Web upload unless the target is explicit.
- **Never use `debug` as a substitute for validation.** Debug executes the process against real services.
- **Never retry a faulted instance without checking incidents and deployed asset correlation.**

## References

### Operate-scoped

- [ship.md](references/ship.md) - package, upload, publish, deploy
- [run.md](references/run.md) - debug, run, status, traces
- [manage.md](references/manage.md) - pause, resume, cancel, retry, migrate, cursor movement

### Cross-capability

- [shared/project-layout.md](../shared/project-layout.md) - package files and content
- [shared/cli-conventions.md](../shared/cli-conventions.md) - side effects, login, JSON output
- [author/validation.md](../author/references/validation.md) - pre-operate validation
- [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md) - failure investigation
