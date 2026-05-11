# Author - Create and edit BPMN Process Orchestration projects

Capability index for local BPMN project authoring. Author owns source edits, local inspection, validation, and CLI enrichment planning. It does not upload, publish, debug, or run cloud instances.

> Inherits universal rules from [SKILL.md](../../SKILL.md). Read [shared/bpmn-xml-contract.md](../shared/bpmn-xml-contract.md) before changing XML boundaries.

## When to use this capability

- Create a Maestro BPMN project scaffold.
- Edit `.bpmn` XML for process structure, diagrams, variables, bindings, entry points, scripts, timers, messages, gateways, subprocesses, boundary errors, and documented non-Integration-Service UiPath extensions.
- Inspect an existing BPMN project and identify source versus generated files.
- Run the two-pass authoring workflow: standard BPMN skeleton first, operator shape confirmation second, UiPath extension fill last.
- Plan Integration Service nodes/triggers that must be CLI-enriched.
- Run local validation before handing off to Operate.

## Critical rules

1. **Use the two-pass workflow for non-trivial authoring** - first generate or edit a pure BPMN skeleton with readable IDs and diagram geometry, then ask the operator to confirm the process shape, then add UiPath variables, bindings, mappings, entry points, and documented non-Integration-Service extensions.
2. **Keep pass 1 standard BPMN-first** - pass 1 may include placeholders and annotations for resource intent, but it must not invent `uipath:activity`, `uipath:event`, connector bindings, generated schemas, or package metadata.
3. **Read the BPMN XML contract before editing** - the Maestro BPMN contract defines which XML the model may author and which pieces require CLI generation or enrichment.
4. **Default to reviewable file edits for BPMN source** - edit `.bpmn` directly for model-owned XML so diffs stay inspectable.
5. **Choose BPMN element class before resource recipe** - RPA, agents, and API workflows are service tasks; queue create is a send task; business rules are business rule tasks; HITL is a user task. See [supported-elements.md](references/supported-elements.md).
6. **Do not hand-author Integration Service details** - use [plugins/integration-service/](references/plugins/integration-service/) for the planning and implementation boundary.
7. **Keep generated package files derived** - if `bindings_v2.json`, `entry-points.json`, `operate.json`, or `package-descriptor.json` is stale, prefer regeneration or validation over manual patching.
8. **Every Studio Web-visible element needs diagram geometry** - ensure diagrams, planes, shapes, bounds, edges, and waypoints exist for rendered nodes and flows.
9. **Validate once the full local edit is coherent** - intermediate BPMN edits may be invalid while IDs, flows, and diagrams are being reconciled.
10. **Preserve unknown imported extensions** - do not delete extension elements the skill cannot interpret unless the user explicitly asks for normalization.
11. **Use synthetic examples only** - never copy private exported BPMN into local fixtures, docs, or comments.

## Two-pass workflow

Use this workflow for greenfield projects and for brownfield edits that change topology, entry points, service calls, subprocess boundaries, or variable contracts.

1. **Plan the process shape** - identify starts, human/system steps, gateways, subprocesses, timers/messages, error paths, end states, variables, resources, and Integration Service enrichment needs. See [planning-arch.md](references/planning-arch.md).
2. **Pass 1: author the BPMN skeleton** - create or edit standard BPMN elements, sequence flows, event definitions, diagram planes, shapes, edges, and placeholder labels. Keep this pass mostly free of UiPath extension XML except preserving existing extensions in brownfield files.
3. **Operator shape confirmation** - summarize the skeleton in process terms and explicitly confirm starts, branches, joins, subprocess boundaries, error paths, and external-system placeholders before filling execution metadata.
4. **Pass 2: fill model-owned UiPath XML** - add root variables, entry point IDs, mappings, bindings, scripts, retry/error metadata, and documented non-Integration-Service `uipath:activity` or `uipath:event` shells. See [planning-impl.md](references/planning-impl.md).
5. **CLI enrichment handoff** - run or request registry-backed enrichment for Integration Service activities/triggers and generated package metadata. If tooling is unavailable, leave draft intent documented and keep the project in Author state.
6. **Validate and summarize** - run local validation after the source is coherent, then report validation status, generated-file status, and unresolved enrichment blockers.

## Workflow

| Journey | Read |
| --- | --- |
| Create a new BPMN project | [references/greenfield.md](references/greenfield.md) |
| Edit an existing BPMN project | [references/brownfield.md](references/brownfield.md) |
| Plan the process topology and enrichment boundary | [references/planning-arch.md](references/planning-arch.md) |
| Fill variables, bindings, expressions, and UiPath extensions | [references/planning-impl.md](references/planning-impl.md) |
| Choose an editing operation | [references/editing-operations.md](references/editing-operations.md) |
| Choose what the model may write | [shared/bpmn-xml-contract.md](../shared/bpmn-xml-contract.md) |
| Choose supported BPMN elements and extension wrappers | [references/supported-elements.md](references/supported-elements.md) |
| Copy a minimal XML shell for a wrapper | [shared/wrapper-shells.md](../shared/wrapper-shells.md) |
| Add resource-backed task recipes | [references/task-recipes/](references/task-recipes/) |
| Work with Integration Service nodes/triggers | [references/plugins/integration-service/](references/plugins/integration-service/) |

## Common tasks

| I need to... | Read these |
| --- | --- |
| Understand project files | [shared/project-layout.md](../shared/project-layout.md) |
| Create a confirmed BPMN skeleton | [references/planning-arch.md](references/planning-arch.md) + [references/greenfield.md](references/greenfield.md) |
| Add or revise BPMN structure | [references/brownfield.md](references/brownfield.md) + [references/editing-operations.md](references/editing-operations.md) + [shared/bpmn-xml-contract.md](../shared/bpmn-xml-contract.md) |
| Add variables, mappings, bindings, or expressions | [references/planning-impl.md](references/planning-impl.md) + [shared/variables-bindings-expressions.md](../shared/variables-bindings-expressions.md) |
| Select the right BPMN wrapper for RPA, agent, API workflow, queue, HITL, business rule, or call activity work | [references/supported-elements.md](references/supported-elements.md) + [references/task-recipes/](references/task-recipes/) |
| Add an Integration Service activity or trigger | [references/plugins/integration-service/](references/plugins/integration-service/) |
| Add a specific BPMN or UiPath extension element | [Plugin references](#plugin-references) |
| Prepare for upload or run | [references/validation.md](references/validation.md) then [operate/CAPABILITY.md](../operate/CAPABILITY.md) |
| Keep authored content public-safe | [shared/public-safety.md](../shared/public-safety.md) |

## Anti-patterns

- **Never omit BPMN DI for a process intended for Studio Web.**
- **Never skip operator shape confirmation for a substantial topology change.**
- **Never mix skeleton design and executable connector enrichment in one opaque rewrite.**
- **Never patch generated JSON to hide a BPMN source problem.**
- **Never paste a real connection ID, folder key, tenant URL, or exported XML snippet into the project.**
- **Never downgrade an Integration Service node to a generic task just because enrichment is unavailable** - keep the node as a draft intent and report the blocker.
- **Never assume imported extension XML is disposable** - preserve first, normalize only on explicit request.

## References

### Author-scoped

- [greenfield.md](references/greenfield.md) - create-new-project journey
- [brownfield.md](references/brownfield.md) - edit-existing-project journey
- [planning-arch.md](references/planning-arch.md) - pass 1 BPMN skeleton planning
- [planning-impl.md](references/planning-impl.md) - pass 2 UiPath extension fill
- [editing-operations.md](references/editing-operations.md) - safe edit operations for BPMN XML
- [supported-elements.md](references/supported-elements.md) - supported BPMN elements and UiPath extension wrappers
- [task-recipes/](references/task-recipes/) - BPMN-first recipes for resource-backed tasks
- [validation.md](references/validation.md) - local validation checklist
- [plugins/integration-service/](references/plugins/integration-service/) - Integration Service planning and CLI enrichment boundary

### Plugin references

Each plugin reference has a `planning.md` for pass 1 shape/resource decisions and an `impl.md` for pass 2 XML ownership and validation boundaries.

- [plugins/start-end-events/](references/plugins/start-end-events/) - start events, end events, intermediate events, and boundary events
- [plugins/gateways/](references/plugins/gateways/) - exclusive, inclusive, parallel, event-based, and complex gateways
- [plugins/sequence-flows/](references/plugins/sequence-flows/) - control-flow edges, conditions, defaults, and diagram waypoints
- [plugins/service-tasks/](references/plugins/service-tasks/) - base service task boundary; use [task-recipes/](references/task-recipes/) for concrete resource-backed tasks
- [plugins/connectors/](references/plugins/connectors/) - connector-backed activities, triggers, waits, and dynamic schemas
- [plugins/waits-triggers/](references/plugins/waits-triggers/) - timers, waits, triggers, receives, and timeout behavior
- [plugins/script/](references/plugins/script/) - script tasks, script metadata, inputs, outputs, and error paths
- [plugins/hitl/](references/plugins/hitl/) - user task representation for Action Center work
- [plugins/queues/](references/plugins/queues/) - send task or service task representation for queue work
- [plugins/call-activity-subprocess/](references/plugins/call-activity-subprocess/) - call activities, subprocesses, event subprocesses, and scoped mappings
- [plugins/multi-instance/](references/plugins/multi-instance/) - sequential or parallel collection processing
- [plugins/agents/](references/plugins/agents/) - service task recipes for agent job and A2A execution shells
- [plugins/rpa-jobs/](references/plugins/rpa-jobs/) - service task recipe for Orchestrator RPA process execution
- [plugins/api-workflows/](references/plugins/api-workflows/) - service task recipe for API workflow invocation
- [plugins/signals/](references/plugins/signals/) - signal definitions, throws, catches, waits, and broadcast semantics
- [plugins/business-rules/](references/plugins/business-rules/) - business rule task invocation and result routing

### Cross-capability

- [shared/bpmn-xml-contract.md](../shared/bpmn-xml-contract.md) - model-owned versus CLI-owned XML
- [shared/project-layout.md](../shared/project-layout.md) - source and generated files
- [shared/variables-bindings-expressions.md](../shared/variables-bindings-expressions.md) - variables, bindings, mappings, expressions
- [shared/cli-conventions.md](../shared/cli-conventions.md) - CLI and side-effect conventions
- [shared/public-safety.md](../shared/public-safety.md) - sanitization rules
