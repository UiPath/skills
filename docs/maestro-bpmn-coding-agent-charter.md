# Maestro BPMN Coding-Agent Charter

Status: planning charter for the `maestro-bpmn-coding-agent-skill` quest.

## Purpose

Build `uipath-maestro-bpmn`, a coding-agent skill for authoring, inspecting, validating, packaging, operating, and diagnosing UiPath Maestro BPMN process-orchestration projects. The skill should be analogous to `uipath-maestro-flow` in structure, but it must treat BPMN XML as the project source instead of `.flow` JSON.

This charter is intentionally source inventory and boundary setting only. It does not define public API changes by itself.

## Skill Name and Shape

- Skill folder: `skills/uipath-maestro-bpmn`.
- Frontmatter identity: Maestro BPMN / Process Orchestration project authoring with `.bpmn`, `project.uiproj`, `entry-points.json`, `operate.json`, `bindings_v2.json`, and `package-descriptor.json`.
- Router shape: reuse the Flow skill pattern:
  - `SKILL.md` as a capability router with universal critical rules.
  - `references/shared/` for CLI conventions, project layout, BPMN XML contract, variables/bindings, expression rules, and source inventory.
  - `references/author/CAPABILITY.md` for local authoring, skeleton design, element plugins, validation, and edit strategy.
  - `references/operate/CAPABILITY.md` for packaging, Studio Web upload, Orchestrator deployment/run/debug, and instance lifecycle.
  - `references/diagnose/CAPABILITY.md` for incidents, element executions, variables, deployed asset correlation, and known runtime failure modes.
  - `.maintenance/` checks adapted from `uipath-maestro-flow`.

## Public and Internal Boundaries

Public skill repository content may include:

- Generic BPMN authoring guidance and execution-safe workflow rules.
- Sanitized BPMN fixtures with no customer, tenant, connection, folder, process, URL, or user-identifying data.
- Public CLI command references for `uip maestro ...` once commands exist or are already published.
- Contract summaries derived from public or sanitized source excerpts.
- Review rules: all public source-changing PRs must be draft until human review completes.

Do not commit:

- Operator-supplied exported BPMN examples, screenshots, tenant data, private process names, connection IDs, folder keys, URLs, or raw customer XML.
- Temporary mission notes from Rookery tasks.
- Direct local absolute paths from developer machines.
- Internal-only repository implementation details unless the destination repository is explicitly internal and the PR is scoped as such.

Internal research sources can inform the public docs, but the public skill should describe stable behavior and tooling contracts rather than requiring agents to read internal source repos at runtime.

## Capability Boundaries

Author owns local, reviewable source work:

- Create or edit Maestro BPMN project files.
- Draft standard BPMN structure: process, events, gateways, tasks, sequence flows, subprocesses, boundary events, and diagram layout.
- Add non-Integration-Service UiPath extension XML when the contract is documented and fixture-backed.
- Run local validation and packaging checks.
- Stop before any cloud-side debug/run without explicit user consent.

Operate owns cloud-side side effects:

- Upload or publish solutions.
- Run or debug process instances.
- Pause, resume, cancel, retry, migrate, or move cursors.
- Read jobs, processes, process versions, traces, and instance state.

Diagnose owns post-run investigation:

- Fetch deployed BPMN assets when local files may differ.
- Correlate incidents, element executions, variables, traces, child Orchestrator jobs, and BPMN element IDs.
- Identify runtime-only failure modes and hand the underlying file fix back to Author.

The skill must not automatically invoke RPA, Agent, Apps, or Platform specialist skills. It should identify missing dependent resources and provide handoff instructions.

## Generation Boundary

The model should own:

- First-pass BPMN skeleton generation for common BPMN structure.
- Human-readable process-shape discussion before deep bindings are filled.
- Non-Integration-Service UiPath extension XML after the relevant contract is documented.
- Diagram coordinates when a deterministic layout rule is enough.
- Review explanations and diffs.

The CLI should own or validate:

- Integration Service activity and trigger enrichment from registry-backed schemas.
- Connector metadata, connection/folder/resource binding shapes, and generated output schemas.
- Package/project scaffolding and pack output.
- Structural validation, BPMN parse validation, and Studio Web/debug upload plumbing.
- Registry search/list/get/pull and resource discovery.

Open generation decision:

- Prefer model-authored BPMN plus CLI enrichment/validation for the first implementation. Full CLI emission of complete BPMN files should wait until the XML contract, registry generation, and layout expectations are stable.

## CLI Deliverables

Base command namespace: `uip maestro bpmn ...` is the proposed public surface for coding-agent authoring commands. Existing `uip maestro ...` commands should remain the lifecycle surface unless the CLI maintainers choose to nest them.

Minimum authoring deliverables:

- `uip maestro bpmn init <name>`: create the canonical project layout, or alias/document existing `uip maestro init` if that remains the supported command.
- `uip maestro bpmn validate <project-or-bpmn>`: parse BPMN with UiPath moddle, check required project files, validate entry point references, validate bindings, and produce machine-readable output.
- `uip maestro bpmn pack <project> <output>`: package a project, or document existing `uip maestro pack` if no nested command is added.
- `uip maestro bpmn registry pull|list|search|get`: shared registry-backed resource discovery for RPA, agents, API workflows, Integration Service activities/triggers, HITL, queues, business rules, and related Maestro nodes.
- `uip maestro bpmn connector enrich`: convert a draft connector node intent plus selected registry/template data into UiPath extension XML and `bindings_v2.json` updates.

Lifecycle deliverables can reuse existing `uip maestro` commands:

- `init`, `pack`, `debug`.
- `process list|get|run`.
- `processes list|incidents`.
- `job traces|status`.
- `instances list|get|pause|resume|cancel|variables|incidents|asset|retry|migrate|goto|cursors|element-executions`.
- `incidents list`.

Known current CLI gaps:

- `maestro-tool` has `init`, `pack`, `debug`, process/job/instance/incidents commands.
- `flow-tool` has `validate`, `registry`, `node`, and `edge` commands that Maestro BPMN does not yet mirror.
- `maestro-sdk` already hosts shared debug/PIMS utilities used by Flow, Case, and Maestro tools. New shared behavior should land there or in another shared package rather than being duplicated.

## BPMN XML Contract Inventory

Frontend source of truth:

- `PO.FrontEnd/src/services/serialization/bpmn-moddle.ts`: UiPath moddle descriptor registration and extension element construction.
- `PO.FrontEnd/src/services/serialization/bpmn-from-xml.ts`: XML import, diagram validation, object extraction, migration, and warning behavior.
- `PO.FrontEnd/src/services/serialization/bpmn-to-xml.ts`: XML export, diagram filtering, geometry merge, definitions construction, exporter metadata, and CDATA fixup.
- `PO.FrontEnd/src/services/serialization/uipath-moddle.v1.json`: current UiPath extension namespace descriptor.
- `PO.FrontEnd/src/services/serialization/design-schema/*.json`: design-time schema contracts for Orchestrator, Integration Service, Maestro message/timer/event, and business-rule activities.
- `PO.FrontEnd/src/services/serialization/converters/bpmn-converter-utils/*.ts`: conversion utilities for root, nodes, edges, tasks, events, gateways, boundary events, subprocesses, and scripts.
- `PO.FrontEnd/mocks/files/*.bpmn` and `PO.FrontEnd/cli/test-resources/**`: fixture corpus for valid exported XML shapes.

Key frontend contract notes:

- Uses `bpmn-moddle` with the UiPath moddle descriptor.
- Import expects BPMN diagrams to exist and filters orphan diagrams.
- Export writes `UiPath Studio Web (https://uipath.com)` or standalone exporter metadata.
- UiPath extension areas include variables, bindings, entry point IDs, activity/event type metadata, context inputs, outputs, retry, error mapping, script version, case management, and design-schema-driven metadata.
- Supported canvas node/event families include tasks, service tasks, user tasks, business rule tasks, send tasks, call activities, intermediate catch/throw events, receive tasks, start/end events, and boundary events.

Runtime source of truth:

- `PO.BpmnEngine/src/BpmnEngine/UiPath.PO.BpmnParser/Parser.cs`: runtime parser and supported BPMN element builder map.
- `PO.BpmnEngine/src/BpmnEngine/UiPath.PO.BpmnParser/Models/Enums/BpmnElementType.cs`: runtime element type enum.
- `PO.BpmnEngine/src/BpmnEngine/UiPath.PO.BpmnParser/ExtensionsProviders/UiPathExtensionsProvider.cs`: UiPath extension reader.
- `PO.BpmnEngine/src/BpmnEngine/UiPath.PO.BpmnEngine/**`: execution state, data scopes, lifecycle manager, and result handling.
- `PO.BpmnEngine/src/BpmnEngine/UiPath.PO.Worker/**`: activity pre/postprocessing, incidents, observability, and Temporal execution bridge.
- `PO.BpmnEngine/tests/BpmnEngine/UiPath.PO.BpmnParser.Tests/TestData/*.bpmn`: runtime parser fixtures and negative cases.

Runtime-supported BPMN families observed in parser source:

- Events: start, end, boundary, intermediate catch, intermediate throw, signal, message-derived event props, timer props, error props.
- Gateways: exclusive, inclusive, parallel, event-based, complex.
- Tasks/activities: task, service task, send task, receive task, user task, manual task, business rule task, script task, call activity.
- Containers and flow: subprocess, ad-hoc subprocess, sequence flow.
- Markers: multi-instance loop characteristics on valid BPMN activities only.

Prior generate/analyze work:

- `Maestro-BPMN-Analyzer` contains a static parser/analyzer that extracts tasks, gateways, events, boundary events, Integration Service usage, complexity signals, and uses PO.FrontEnd for viewer styling.
- Useful lessons: strip diagram data for analysis when appropriate, never persist/log raw BPMN XML from private pipelines, and require `BPMNDiagram` data when the viewer must render.
- This repo is an internal analytics/reference source, not the public authoring contract.

## Exported Example Inventory

Three operator-supplied exported BPMN XML files were reviewed as private inputs and must not be committed raw.

Observed structural coverage:

- Example 1: large process with boundary error events, exclusive/parallel gateways, intermediate catch/throw events, send tasks, service tasks, script tasks, generic tasks, groups, annotations, multi-instance marker, timer, message, and terminate end behavior.
- Example 2: large process with many exclusive gateways, service tasks, subprocesses, user tasks, receive task, multiple start/end events, message event, and terminate end behavior.
- Example 3: medium process with service tasks, script tasks, send task, boundary error events, timer catch events, exclusive/parallel gateways, and documentation-heavy nodes.

Fixture policy:

- Derive sanitized fixtures from these examples only after removing names, IDs, customer/process text, URLs, bindings, connection/folder data, and any payloads.
- Keep the first public fixture set small and purposeful: one minimal linear process, one gateway/boundary-error process, one Integration Service activity/trigger process, and one subprocess/multi-instance process.

## Source Inventory for Next Tasks

Public skill repo:

- `skills/uipath-maestro-flow/SKILL.md`: router, universal rules, and Flow capability pattern.
- `skills/uipath-maestro-flow/references/{author,operate,diagnose,shared}/`: split to mirror for BPMN.
- `skills/uipath-maestro-flow/.maintenance/`: structure, link, anchor, depth, orphan, plugin-pair, and command checks to adapt.
- `tests/tasks/uipath-maestro-flow/`: evaluation layout and Flow fixtures to mirror.

CLI repo:

- `packages/maestro-tool/src/tool.ts`: current command registration.
- `packages/maestro-tool/src/commands/{init,pack,debug,process,processes,job,instances,incidents}.ts`: existing Maestro lifecycle surface.
- `packages/maestro-tool/src/services/{maestro-pack-service,maestro-debug-service,maestro-api}.ts`: project packaging, Studio Web debug, PIMS/Orchestrator calls.
- `packages/maestro-sdk/src/**`: shared PIMS/debug helpers and types.
- `packages/flow-tool/src/commands/{validate,registry,node,edge}.ts`: candidate patterns for missing BPMN authoring support.
- `packages/flow-tool/src/utils/integration-service-fetcher.ts` and node services: candidate Integration Service enrichment patterns.

Frontend repo:

- Serialization, moddle, design-schema, converter, mock, and CLI test-resource files listed in the BPMN XML contract inventory.

Runtime repo:

- Parser, models, extension provider, engine, worker, and parser fixture files listed in the runtime inventory.

Private local inputs:

- Three exported BPMN examples from the operator. Treat as private source material only.

## PR and Review Rules

- Public repo changes must be on feature branches.
- CLI branch suggestion: `feature/maestro-bpmn-agent-cli`.
- Skills branch suggestion: `feature/maestro-bpmn-skill`.
- Open draft PRs early for source-changing work.
- Do not merge public PRs without human review.
- Later implementation tasks should wait for prerequisite PRs to close when they depend on merged CLI or skill surfaces.

## Open Decisions

- Whether the public command namespace is nested `uip maestro bpmn ...` or existing top-level `uip maestro ...` plus documented BPMN authoring commands.
- Exact shared CLI package boundary between Flow, Case, and Maestro BPMN for registry, Integration Service enrichment, packaging metadata, and validation.
- Which Canvas-supported elements are public agent-authoring targets now versus inspect/diagnose-only.
- Whether CLI should eventually emit complete BPMN XML or remain an enrichment/validation layer around model-authored BPMN.
- Where the durable public design document should live after review: skills repo docs, CLI repo docs, or both with a short cross-link.
