---
name: uipath-maestro-bpmn
description: "UiPath Maestro BPMN / Process Orchestration: author (registry-driven), validate, package, operate, and diagnose .bpmn projects. For .flow use uipath-maestro-flow; for case plans use uipath-maestro-case."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Maestro BPMN

Work with UiPath Maestro (Process Orchestration) `.bpmn` projects across their
lifecycle: author, validate, package, operate, and diagnose. **Authoring is
registry-driven**: every `uipath:*` extension payload comes from a template the
registry serves; the structural BPMN that holds those nodes together (process
scaffold, sequence flows, gateways, events, boundary events, containers,
multi-instance markers, and the diagram) is authored from the documented spec +
canvas contract. Packaging, operating (upload, publish, run, manage), and
diagnosing are driven through the UiPath CLI, covered in the capability
references below.

## When to use

- Create a Maestro `.bpmn` from a description.
- Edit `.bpmn` structure: gateways, events, boundary events, subprocesses, call
  activities, multi-instance loops, sequence-flow conditions, variables.
- Add a UiPath extension node (RPA job, agent, HITL, queue, business rule, API
  workflow, Integration Service connector, internal message, timer).
- Validate a `.bpmn` against the canvas rules before import.
- Package, upload, publish, or run a project, and manage its jobs and instances.
- Diagnose a failed or misbehaving run.

For `.flow` JSON use `uipath-maestro-flow`; for XAML/coded workflows use
`uipath-rpa`; for Python agents use `uipath-agents`; for Case plans use
`uipath-maestro-case`.

## The model

Two halves make a valid Maestro `.bpmn`:

1. **`uipath:*` payloads — registry-owned.** Each node's extension XML
   (`uipath:activity` / `uipath:event` / `uipath:mapping`, its `context`,
   `input`, `output`, and `bindingInfo`) comes from
   `uip maestro bpmn registry get <type>`'s `xmlTemplate`. **Never hand-author a
   `uipath:*` element from prose.**
2. **Structural BPMN — spec/canvas-owned.** The registry emits no
   `<bpmn:definitions>`/`<bpmn:process>`, no sequence flows, no gateway
   conditions/defaults, no event-definition payloads, no boundary-event
   attributes, no subprocess/loop structure, and no diagram. Author all of these
   from [references/structural-bpmn.md](references/structural-bpmn.md), which is
   grounded in the registry spec and the Studio Web canvas serializer.

## Workflow

1. **Discover.** `uip maestro bpmn registry pull`, then `list` / `search` to map
   intent to extension types; `uip is connections list` for live connections.
   Confirm every selection with the user (use AskUserQuestion). Never fabricate
   an identifier. See [references/registry-workflow.md](references/registry-workflow.md).
2. **Get templates.** `uip maestro bpmn registry get <type> --output json` for
   each chosen node. Enrich `Intsvc.*` connector nodes with
   `--connection-id`/`--object-name`.
3. **Assemble.** Build the document scaffold, declare variables and bindings,
   paste each node's `xmlTemplate` (fill placeholders only), then author the
   structural BPMN the registry does not emit — sequence flows, gateways,
   events, boundary events, containers, multi-instance markers — and generate
   the `bpmndi:BPMNDiagram`.
4. **Validate.** There is **no** `uip maestro bpmn validate` CLI command. Run the
   bundled validator — it reconstructs the canvas model and runs every
   PO.Frontend rule:

   ```bash
   cd skills/uipath-maestro-bpmn/validator && npm install --silent
   node validate-bpmn.mjs <file.bpmn>   # prints VALID (exit 0) or the errors (exit 1)
   ```

   A well-formed-XML parse is the secondary fallback if Node is unavailable. See
   [references/structural-bpmn.md#validation](references/structural-bpmn.md#validation).

## Operate and diagnose

Beyond authoring, this skill packages, ships, runs, and diagnoses Maestro
projects through the UiPath CLI.

- **Package and operate** (package a project, upload to Studio Web, publish or
  deploy, run or debug instances, and manage jobs, instances, incidents, and
  lifecycle actions): see [references/operate/CAPABILITY.md](references/operate/CAPABILITY.md).
- **Diagnose** (fetch incidents, variables, and element executions, and trace a
  failed run back to its BPMN element): see [references/diagnose/CAPABILITY.md](references/diagnose/CAPABILITY.md).

Any cloud-side change (upload, publish, deploy, run, pause, resume, cancel,
retry, migrate) requires explicit user consent, and local validation should pass
first.

## Structural coverage

This skill teaches authoring of the full surface the canvas supports. What the
registry serves a template for vs. what you author by hand:

| Structure | Source |
| --- | --- |
| Node `uipath:*` payloads (RPA, agent, HITL, queue, business rule, API workflow, IS connector, internal message, timer, script, variables) | **Registry** `xmlTemplate` |
| `<bpmn:definitions>`/`<bpmn:process>` scaffold + namespaces | Authored (registry gap) |
| Sequence flows, `conditionExpression`, gateway `default` | Authored (registry gap) |
| Gateways: exclusive, parallel, inclusive, event-based, complex | Authored (registry gap) |
| Events + event-definition matrix: message, timer, signal, error, escalation, conditional, link, compensate, terminate | Authored (registry gap); payload per canvas serializer |
| Boundary events: `attachedToRef`, interrupting/non-interrupting (`cancelActivity`) | Authored (registry gap) |
| Subprocess, event subprocess (`triggeredByEvent`), call activity | Authored (registry gap); call-activity payloads from registry |
| Multi-instance / loop characteristics | Authored from canvas contract — **registry exposes no template (registry gap)** |
| `bpmndi:BPMNDiagram` (shape per node, edge per flow) | Always generated — **registry emits none (registry gap)** |

Flagged registry gaps: the registry serves no template for structural BPMN,
sequence-flow conditions, event-definition payloads, boundary-event attributes,
multi-instance markers, or the diagram. These are authored from the spec +
canvas contract in [references/structural-bpmn.md](references/structural-bpmn.md)
and honestly surfaced to the user as gaps when asked.

## Rules

1. **Registry owns every `uipath:*` payload.** Author from
   `registry get` templates; never hand-write `uipath:` XML from prose.
2. **Never fabricate an identifier.** Connection IDs, process/queue/connector
   keys, app IDs, folder ids/paths come from discovery or the user.
3. **Structural BPMN is authored, not invented.** Follow the spec/canvas
   contract in [references/structural-bpmn.md](references/structural-bpmn.md);
   flag honestly what the registry does not expose.
4. **Confirm before authoring.** Confirm the chosen connector/connection/process
   and the process structure with the user (AskUserQuestion).
5. **The diagram is mandatory.** Import is diagram-driven — every node needs a
   `BPMNShape`, every flow a `BPMNEdge`, or it will not appear on the canvas.
6. **Use `--output json` for parsed CLI calls.**
7. **Public-safe always.** No customer XML, tenant URLs, real IDs, or private
   names — see [references/public-safety.md](references/public-safety.md).
8. **Confirm before any cloud change.** Upload, publish, deploy, run, pause,
   resume, cancel, retry, and migrate require explicit user consent; validate
   locally first.

## References

| Topic | Read |
| --- | --- |
| Discover → template → bind → assemble loop | [references/registry-workflow.md](references/registry-workflow.md) |
| Structural BPMN, event matrix, boundary events, containers, multi-instance, diagram, validation | [references/structural-bpmn.md](references/structural-bpmn.md) |
| Runtime expressions, `vars.`/`bindings.`/`iterator.`, `=js:` (Jint) syntax | [references/expression-authoring.md](references/expression-authoring.md) |
| CLI conventions and the side-effect boundary | [references/cli-conventions.md](references/cli-conventions.md) |
| Keeping content public-safe | [references/public-safety.md](references/public-safety.md) |
| Bundled offline validator (every PO.Frontend rule) | [validator/README.md](validator/README.md) |
| Package, upload, publish, run, or manage instances | [references/operate/CAPABILITY.md](references/operate/CAPABILITY.md) |
| Diagnose a failed or misbehaving run | [references/diagnose/CAPABILITY.md](references/diagnose/CAPABILITY.md) |
| Project layout and generated package files | [references/shared/project-layout.md](references/shared/project-layout.md) |
