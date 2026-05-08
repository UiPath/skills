# Diagnose - Investigate failed BPMN runs

Capability index for post-run investigation.
Diagnose owns the diagnostic priority ladder for BPMN Process Orchestration runs: incidents, runtime variables,
deployed BPMN asset correlation, element executions, cursors, generated package metadata, and traces.

> **Where you came from / where to go next.** Diagnose is downstream of Operate (a debug or deployed run failed, hung,
> or behaved unexpectedly) and points back to Author for source fixes.
> Running and lifecycle live in [operate/CAPABILITY.md](../operate/CAPABILITY.md);
> source fixes live in [author/CAPABILITY.md](../author/CAPABILITY.md).
>
> **Inherits universal rules from [SKILL.md](../../SKILL.md).** BPMN source is model-authored; generated package files
> and Integration Service enrichment are CLI-owned.
> Use `uip maestro bpmn ... --output json` for diagnostic reads and redact private runtime data in summaries.

## When to use this capability

- Triage a failed debug or deployed process run.
- Read incidents and faulting element IDs.
- Inspect runtime variables and element executions.
- Fetch the deployed BPMN asset when local files may differ.
- Map runtime failures back to BPMN source and generated package metadata.
- Identify failures caused by unresolved Integration Service enrichment, bad bindings, missing diagrams, invalid mappings,
  or stale package files.
- Decide whether the safe next action is retry, cancel, migrate, cursor movement, re-authoring, package regeneration,
  or cloud configuration repair.

## Critical rules

1. **Investigate in priority order** - context, incidents, runtime variables, deployed BPMN asset,
   element executions/cursors, generated package files, then traces.
2. **Always include folder context on instance and incident reads** - `instance` commands require `--folder-key` or `-f`,
   and `incident get` requires `--folder-key`.
3. **Fetch deployed BPMN when local source may differ** - do not assume the working tree matches what ran.
4. **Map failures to BPMN element IDs** - use IDs to identify the source node, gateway, event, sequence flow,
   or extension that needs Author work.
5. **Separate runtime symptoms from ownership of the fix** - BPMN structure and mappings belong in Author;
   Integration Service enrichment and generated JSON come from CLI generation;
   folder/process/release choices belong to cloud configuration.
6. **Do not expose private runtime data** - redact tenant, user, connection, folder, URL, payload,
   and secret values in summaries.
7. **Do not mutate while diagnosing** - retry, cancel, migrate, and cursor movement are Operate actions and require
   explicit user consent after root cause analysis.

## Workflow

| Journey | Read |
| --- | --- |
| Triage a failed run | [references/troubleshooting-guide.md](references/troubleshooting-guide.md) |
| Recognize recurring failure patterns | [references/failure-modes.md](references/failure-modes.md) |

## Common tasks

| I need to... | Read these |
| --- | --- |
| Find the faulting element | [references/troubleshooting-guide.md](references/troubleshooting-guide.md) |
| Compare local and deployed BPMN | [references/troubleshooting-guide.md](references/troubleshooting-guide.md) |
| Inspect runtime variables, cursors, or element executions | [references/troubleshooting-guide.md](references/troubleshooting-guide.md) |
| Diagnose binding or generated JSON issues | [failure modes](references/failure-modes.md), [project layout](../shared/project-layout.md) |
| Diagnose Integration Service runtime issues | [failure modes](references/failure-modes.md) |
| Decide whether retry is safe | [troubleshooting guide](references/troubleshooting-guide.md), [manage guide](../operate/references/manage.md) |
| Fix the source | [author/CAPABILITY.md](../author/CAPABILITY.md) |

For Integration Service enrichment details, read
[author/references/plugins/integration-service/impl.md](../author/references/plugins/integration-service/impl.md).

## Anti-patterns

- **Never start with verbose traces when incidents are available.**
- **Never call runtime lifecycle commands while diagnosing.** Diagnose reads; Operate mutates after explicit consent.
- **Never assume local BPMN is the deployed asset.**
- **Never retry before root cause is known.**
- **Never paste private incident payloads or connection details into docs, commits, or issue comments.**
- **Never patch generated package files as the only fix for a BPMN source defect.**

## References

### Diagnose-scoped

- [troubleshooting-guide.md](references/troubleshooting-guide.md) - diagnostic priority ladder
- [failure-modes.md](references/failure-modes.md) - recurring failure patterns

### Cross-capability

- [shared/bpmn-xml-contract.md](../shared/bpmn-xml-contract.md) - XML authoring and validation boundaries
- [shared/project-layout.md](../shared/project-layout.md) - generated files and package shape
- [shared/variables-bindings-expressions.md](../shared/variables-bindings-expressions.md) - mappings and binding expressions
- [shared/public-safety.md](../shared/public-safety.md) - redaction and sanitization
