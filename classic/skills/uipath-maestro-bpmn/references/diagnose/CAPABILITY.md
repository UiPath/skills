# Diagnose - Investigate failed BPMN runs

Post-run investigation for BPMN Process Orchestration runs. Diagnose owns the priority ladder: incidents, runtime variables, deployed BPMN assets, element executions, cursors, generated package metadata, and traces.

> Diagnose follows Operate when a debug or deployed run failed, hung, or behaved unexpectedly, and points source fixes to Author. Running and lifecycle live in [operate/CAPABILITY.md](../operate/CAPABILITY.md); source fixes live in [registry-workflow.md](../registry-workflow.md).
>
> Inherit universal rules from [SKILL.md](../../SKILL.md). BPMN source is model-authored; generated package files and Integration Service enrichment are CLI-owned. Use `uip maestro bpmn ... --output json` for diagnostic reads and redact private runtime data in summaries.

## When to use this capability

- Triage failed debug or deployed runs with incidents, faulting element IDs, runtime variables, and element executions.
- Fetch deployed BPMN when local files may differ; map failures to source and generated package metadata.
- Diagnose unresolved Integration Service enrichment, bad bindings, missing diagrams, invalid mappings, and stale package files.
- Identify repair ownership and the read-only check required before Operate follow-up.

## Critical rules

1. **Investigate in priority order** - context, incidents, runtime variables, deployed BPMN asset, element executions/cursors, generated package files, then traces. For failed BPMN run triage, always run `uip maestro bpmn instance asset <INSTANCE_ID> -f <FOLDER_KEY> --output json` before writing the diagnosis, even when incidents and variables reveal the likely root cause.
2. **Always include folder context on instance and incident reads** - instance commands require `--folder-key` or `-f`, and `incident get` requires `--folder-key`.
3. **Use the CLI as the diagnostic interface** - run `uip maestro bpmn ... --output json` reads. If mock or fixture files exist in a test harness, do not read them by any means—including `cat`, `less`, `head`, `tail`, `grep`, `jq`, `sed`, file-read tools, or editor tools—on a `mocks/`, `fixtures/`, or response-cache path unless explicitly debugging the mock harness. Capturing a CLI response to your own file and reading it back is allowed; it is the CLI's own output.
4. **Fetch deployed BPMN when local source may differ** - never assume the working tree matches what ran.
5. **Map failures to BPMN element IDs** - use IDs to identify the source node, gateway, event, sequence flow, or extension needing Author work.
6. **Separate runtime symptoms from ownership of the fix** - BPMN structure and mappings belong in Author; Integration Service enrichment and generated JSON come from CLI generation; folder/process/release choices belong to cloud configuration.
7. **Do not expose private runtime data** - redact tenant, user, connection, folder, URL, payload, and secret values from summaries.
8. **Do not mutate while diagnosing** - retry, cancel, migrate, and cursor movement are Operate actions requiring explicit user consent after root cause analysis. Diagnose reads; Operate mutates after consent.
9. **One literal command per diagnostic read, never a loop** - write each read in full, e.g. `uip maestro bpmn instance cursors <INSTANCE_ID> -f <FOLDER_KEY> --output json`. No loop, function, alias, or variable may replace the verb, ID, or folder key: the command log records what was read. To batch, chain literal reads in one Bash call, one per line.

## Workflow

| Journey | Read |
| --- | --- |
| Triage a failed run | [troubleshooting-guide.md](troubleshooting-guide.md) |
| Recognize recurring failure patterns | [failure-modes.md](failure-modes.md) |

## Common tasks

| I need to... | Read these |
| --- | --- |
| Find the faulting element; compare local and deployed BPMN; inspect runtime variables, cursors, or element executions | [troubleshooting-guide.md](troubleshooting-guide.md) |
| Diagnose binding or generated JSON issues | [failure modes](failure-modes.md), [project layout](../shared/project-layout.md) |
| Diagnose Integration Service runtime issues | [failure modes](failure-modes.md) |
| Decide whether retry is safe | [troubleshooting guide](troubleshooting-guide.md), [manage guide](../operate/manage.md) |
| Fix the source | [registry-workflow.md](../registry-workflow.md) |

For Integration Service enrichment details, read [registry-workflow.md](../registry-workflow.md).

## Anti-patterns

- Never start with verbose traces when incidents are available.
- Never call runtime lifecycle commands, retry, or mutate while diagnosing; establish root cause and obtain explicit consent before Operate follow-up.
- Never assume local BPMN is the deployed asset.
- Never paste private incident payloads or connection details into docs, commits, or issue comments.
- Never patch generated package files as the only fix for a BPMN source defect.

## References

### Diagnose-scoped

- [troubleshooting-guide.md](troubleshooting-guide.md) - diagnostic priority ladder
- [failure-modes.md](failure-modes.md) - recurring failure patterns

### Cross-capability

- [structural-bpmn.md](../structural-bpmn.md) - XML authoring and validation boundaries
- [shared/project-layout.md](../shared/project-layout.md) - generated files and package shape
- [expression-authoring.md](../expression-authoring.md) - mappings and binding expressions
- [public-safety.md](../public-safety.md) - redaction and sanitization
