---
name: uipath-maestro-bpmn
description: "Always invoke for `.bpmn`, `project.uiproj`, `entry-points.json`, `operate.json`, `bindings_v2.json`, or `package-descriptor.json` files. UiPath Maestro BPMN / Process Orchestration — author, inspect, validate, package, operate, diagnose. Model writes BPMN skeleton + non-IS UiPath XML; CLI owns Integration Service nodes/templates and generated package files. For .flow JSON→uipath-maestro-flow. For XAML/coded workflows→uipath-rpa. For Python agents→uipath-agents. For Case plans→uipath-maestro-case."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Maestro BPMN Skill

Guide for authoring, inspecting, validating, packaging, operating, and diagnosing UiPath Maestro BPMN Process Orchestration projects. BPMN XML is the source of record. Generated JSON package files and Integration Service details are owned by CLI tooling.

## When to use this skill

**Author** - creating or editing local BPMN project source. Read [references/author/CAPABILITY.md](references/author/CAPABILITY.md).

- Create a Maestro BPMN project skeleton
- Edit `.bpmn` XML for process structure, variables, mappings, timers, messages, gateways, subprocesses, script tasks, and documented non-Integration-Service UiPath extensions
- Plan where Integration Service activities/triggers require CLI enrichment instead of model-authored XML
- Validate XML, diagrams, entry points, bindings, and generated package metadata locally

**Operate** - packaging, uploading, publishing, running, or managing cloud lifecycle. Read [references/operate/CAPABILITY.md](references/operate/CAPABILITY.md).

- Package a BPMN Process Orchestration project
- Upload to Studio Web or publish/deploy when explicitly requested
- Run/debug a process instance only after explicit user consent
- Manage jobs, instances, incidents, variables, and lifecycle actions

**Diagnose** - investigating failed or misbehaving runs. Read [references/diagnose/CAPABILITY.md](references/diagnose/CAPABILITY.md).

- Fetch incidents, variables, element executions, and deployed BPMN assets
- Correlate runtime failures back to BPMN element IDs and local XML
- Identify authoring, packaging, binding, and Integration Service enrichment failures

## Capability router

| I want to... | Read |
| --- | --- |
| Create or edit BPMN source | [references/author/CAPABILITY.md](references/author/CAPABILITY.md) |
| Package, upload, publish, run, or manage lifecycle | [references/operate/CAPABILITY.md](references/operate/CAPABILITY.md) |
| Diagnose a failed or misbehaving run | [references/diagnose/CAPABILITY.md](references/diagnose/CAPABILITY.md) |
| Understand project layout and package files | [references/shared/project-layout.md](references/shared/project-layout.md) |
| Regenerate or verify local package metadata | [references/shared/local-metadata-regeneration-guide.md](references/shared/local-metadata-regeneration-guide.md) |
| Understand BPMN XML authoring boundaries | [references/shared/bpmn-xml-contract.md](references/shared/bpmn-xml-contract.md) |
| Copy minimal XML shells per supported wrapper | [references/shared/wrapper-shells.md](references/shared/wrapper-shells.md) |
| Understand variables, bindings, entry points, and expressions | [references/shared/variables-bindings-expressions.md](references/shared/variables-bindings-expressions.md) |
| Author lint-compatible runtime expressions | [references/shared/expression-authoring.md](references/shared/expression-authoring.md) |
| Map Studio Web palette buttons to BPMN XML | [references/shared/studio-web-palette-mapping.md](references/shared/studio-web-palette-mapping.md) |
| Author Maestro retry and error handling | [references/shared/error-handling.md](references/shared/error-handling.md) |
| Understand CLI conventions and side-effect boundaries | [references/shared/cli-conventions.md](references/shared/cli-conventions.md) |
| Keep examples and commits public-safe | [references/shared/public-safety.md](references/shared/public-safety.md) |

## Critical rules (universal)

1. **BPMN XML is the source of record** - edit `.bpmn` for process structure; treat generated package JSON as derived unless a CLI contract explicitly says otherwise.
2. **Model owns skeleton and documented non-IS XML only** - generate BPMN control flow, diagram coordinates, root variables, mappings, entry point IDs, script tasks, retry/error metadata, and documented non-Integration-Service UiPath extensions. Do not invent undocumented UiPath extension payloads.
3. **Use two-pass authoring for substantial changes** - write the standard BPMN skeleton first, get operator confirmation of the process shape, then fill model-owned UiPath extension XML.
4. **CLI owns Integration Service enrichment** - Integration Service activities/triggers, connection bindings, connector metadata, dynamic schemas, trigger properties, and generated output templates must come from registry-backed CLI enrichment or validation.
5. **Never use private source material in skill content** - no exported customer BPMN, tenant URLs, folder keys, connection IDs, user names, process names, local paths, screenshots, or temporary mission notes. Examples must be synthetic.
6. **Use JSON output for parsed CLI calls** - whenever CLI output is parsed programmatically, request JSON output from the CLI and preserve the raw command result in the local transcript or a sanitized report.
7. **Do not run debug or deployed process execution without explicit user consent** - debug/run can trigger real side effects in external systems.
8. **Ask before cloud-side mutations** - upload, publish, deploy, run, pause, resume, cancel, retry, migrate, and move-cursor operations require a clear user decision.
9. **Do not automatically invoke sibling skills** - when BPMN references an RPA process, agent, app, API workflow, or case asset that is missing, identify the dependency and provide handoff instructions.
10. **Validate before operate** - run local XML/project/package validation before upload, publish, or debug. Treat validation warnings about CLI-owned enrichment as blockers for real runs when the target element can execute.
11. **Preserve unknown extension payloads unless normalizing explicitly** - do not delete or rewrite user-authored or imported UiPath extension XML just because the skill cannot fully interpret it.

## Anti-patterns (universal)

- **Do not hand-author Integration Service connection details** - connection IDs, resource keys, connector labels, trigger property bindings, and generated schemas are CLI-owned.
- **Do not rely on BPMN without diagrams for Studio Web import** - a valid diagram and plane are required, and visible elements need shapes or waypoints.
- **Do not edit derived package files as the primary fix** - fix the BPMN source or rerun the CLI generator/enricher unless the package file itself is the documented source for that field.
- **Do not include real exported XML snippets in docs or examples** - summarize patterns using public-safe synthetic IDs and placeholder values.
- **Do not use validation fixtures as greenfield templates** - fixtures are
  coverage examples, not the authoring source of truth. Use capability docs,
  shared contracts, wrapper shells, and the specific plugin or task recipe
  instead.

> Trouble? Send public-safe product feedback through the repository's normal feedback path.
