---
name: uipath-maestro-bpmn
description: "UiPath Maestro BPMN / Process Orchestration: author (registry-driven), validate, package, operate, and diagnose .bpmn projects; consume BPMN SDD sdd.md input or run Phase 0 when a new BPMN request has no SDD. For .flow use uipath-maestro-flow; for case plans use uipath-maestro-case."
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

### Editing an existing `.bpmn` (preserve what you did not author)

The skill can edit an existing file. Make **surgical** edits and preserve
content you did not author: unknown `uipath:*` elements, `uipath:migrationVersion`,
tags, imported Integration Service payloads, and stable element IDs. Do not
regenerate the whole file or drop extension data the skill does not recognize —
preserve-only structures (see the blocklist in
[references/structural-bpmn.md](references/structural-bpmn.md)) round-trip
untouched.

For `.flow` JSON use `uipath-maestro-flow`; for XAML/coded workflows use
`uipath-rpa`; for Python agents use `uipath-agents`; for Case plans use
`uipath-maestro-case`.

### SDD input routing

Choose one authoring route before registry discovery. These routes preserve the
existing direct-prose and existing-file behavior while adding an SDD handoff.
Resolve the SDD location before choosing the route: search the caller's explicit
SDD path first, then `./sdd.md`. Treat the SDD as absent only when neither path
exists.

| Resolved input | Route |
| --- | --- |
| Existing `.bpmn` | Use the surgical edit flow above. Preserve unknown payloads and stable IDs; do not run Phase 0. |
| Supplied `sdd.md` | Read [SDD semantic intake](references/sdd-input.md), skip Phase 0, refresh connection inventory exactly once with `uip is connections list --all-folders`, then take its complete semantic model through the existing registry, structural BPMN, BPMNDI, and validator workflow. |
| Prose with an explicit direct-authoring request | Keep the direct prose-to-BPMN route: clarify the process shape, then use the existing registry-driven workflow below without creating an SDD. |
| No `sdd.md` and no existing `.bpmn` | Run [BPMN Phase 0](references/phase-0-interview.md) to create `sdd.draft.md`; wait for explicit approval before creating `sdd.md` or beginning registry authoring. |

The BPMN SDD is a portable semantic handoff, not a serialized BPMN artifact.
Use this skill's own [SDD template](assets/templates/sdd-template.md) and
[SDD generation rules](references/sdd-generation-rules.md). It contains no
registry XML or BPMNDI. A required unresolved resource blocks executable BPMN,
but does not block SDD review: retain its intent and unresolved marker until a
later registry discovery can resolve it. SDD approval confirms business shape;
it does not silently confirm a different discovered technical resource.

When an approved SDD advances to executable authoring, create a complete local
project as defined in [project layout](references/shared/project-layout.md):
the BPMN source and
`project.uiproj`, plus the required package metadata files `bindings_v2.json`,
`entry-points.json`, `operate.json`, and `package-descriptor.json`. Keep the
metadata references aligned with the BPMN file and its actual start event.

Every supplied-SDD executable path refreshes the connection inventory exactly
once with `uip is connections list --all-folders`, before choosing registry
resources. Do this even when the SDD says the resource is resolved or appears
not to use a connection: a stale inventory must never silently validate a
technical binding. Discovery does not authorize usage: add a connection binding
only when the selected registry template contract requires that connection and
the discovered candidate matches the SDD intent.

## The model

Two halves make a valid Maestro `.bpmn`:

1. **`uipath:*` payloads — registry-owned.** Each node's extension XML
   (`uipath:activity` / `uipath:event` / `uipath:mapping`, its `context`,
   `input`, `output`, and `bindingInfo`) comes from
   `uip maestro bpmn registry get <extensionType>`'s `xmlTemplate`. **Never hand-author a
   `uipath:*` element from prose.**
2. **Structural BPMN — spec/canvas-owned.** The registry emits no
   `<bpmn:definitions>`/`<bpmn:process>`, no sequence flows, no gateway
   conditions/defaults, no event-definition payloads, no boundary-event
   attributes, no subprocess/loop structure, and no diagram. Author all of these
   from [references/structural-bpmn.md](references/structural-bpmn.md), which is
   grounded in the registry spec and the Studio Web canvas serializer.

## Workflow

Work the five steps quickly and author early — do not pre-read every reference
before writing. Read a reference only when you reach the structure it covers.

1. **Route.** Use [SDD input routing](#sdd-input-routing). A supplied approved
   `sdd.md` is parsed by [SDD semantic intake](references/sdd-input.md) before
   discovery; no-SDD Phase 0 stops at the approved `sdd.md`. The direct prose
   route starts at discovery.
2. **Discover.** `uip maestro bpmn registry pull` **once** (cached for the
   session — do not re-pull), then `list` / `search` to map intent to extension
   types. On every supplied-SDD executable path, refresh live connections
   **exactly once** with `uip is connections list --all-folders`, even when the
   resource looks resolved; a folder-scoped list silently misses connections.
   Do not bind an inventory result unless the selected registry template
   requires it and the connection matches the declared resource intent.
   Confirm every selection with the user (use AskUserQuestion). Never fabricate
   an identifier. See [references/registry-workflow.md](references/registry-workflow.md).
3. **Get templates.** `uip maestro bpmn registry get <extensionType> --output json` for
   each chosen node. Enrich `Intsvc.*` connector nodes with
   `--connection-id`/`--object-name`.
4. **Assemble.** Author directly from the complete minimal file in
   [references/structural-bpmn.md](references/structural-bpmn.md#a-complete-minimal-file-author-from-this-not-from-fixtures)
   plus each node's `xmlTemplate` (fill placeholders only). That skeleton already
   shows variables, the entry point, a branch, and the diagram. **Do not read the
   validator's `test/fixtures/` to infer the pattern** — it is the top reason
   authoring runs out of time. Add only the structural pieces your process needs
   (extra gateways, events, boundary events, containers, multi-instance markers),
   then generate one `BPMNShape`/`BPMNEdge` per node and flow. For a new project,
   also produce the five local package files named in the greenfield SDD contract
   above.
5. **Validate.** There is **no** `uip maestro bpmn validate` CLI command. Run the
   bundled validator — it reconstructs the canvas model and runs every
   PO.Frontend rule:

   ```bash
   cd skills/uipath-maestro-bpmn/validator && npm install --silent
   node validate-bpmn.mjs <file.bpmn>   # prints VALID (exit 0) or the errors (exit 1)
   ```

   A well-formed-XML parse is the secondary fallback if Node is unavailable. See
   [references/structural-bpmn.md#validation](references/structural-bpmn.md#validation).
   Validate once; fix only ERROR-severity findings (warnings do not block import).
   Do not re-validate in a loop chasing warnings.

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
| Gateways: exclusive, parallel, inclusive, event-based (complex is preserve-only) | Authored (registry gap) |
| Events + event-definition matrix: message, timer, error, terminate (end-only). Signal/escalation/conditional/link/compensate/cancel/multiple are preserve-only | Authored (registry gap); payload per canvas serializer |
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
6. **Node type is a child element, never an attribute.** Every `uipath:activity`
   / `uipath:event` / `uipath:mapping` declares its type as
   `<uipath:type value="<Type>" version="v1" />` inside the wrapper. Never write
   `<uipath:activity type="…">` — the canvas will not recognize the node.
7. **No `--` in XML comments.** XML forbids `--` (double-hyphen) inside
   `<!-- … -->`, so never paste CLI commands or flags (`--output`,
   `--connection-id`, `--object-name`) into a comment — it makes the file
   unparseable. Keep comments minimal.
8. **Use `--output json` for parsed CLI calls.**
9. **Public-safe always.** No customer XML, tenant URLs, real IDs, or private
   names — see [references/public-safety.md](references/public-safety.md).
10. **Confirm before any cloud change.** Upload, publish, deploy, run, pause,
   resume, cancel, retry, and migrate require explicit user consent; validate
   locally first.

## References

| Topic | Read |
| --- | --- |
| Discover → template → bind → assemble loop | [references/registry-workflow.md](references/registry-workflow.md) |
| Structural BPMN, event matrix, boundary events, containers, multi-instance, diagram, validation | [references/structural-bpmn.md](references/structural-bpmn.md) |
| Runtime expressions, `vars.`/`bindings.`/`iterator.`, `=js:` (Jint) syntax | [references/expression-authoring.md](references/expression-authoring.md) |
| Generate an SDD when none was supplied | [references/phase-0-interview.md](references/phase-0-interview.md) |
| Consume a supplied SDD as BPMN semantics | [references/sdd-input.md](references/sdd-input.md) |
| BPMN SDD semantic constraints | [references/sdd-generation-rules.md](references/sdd-generation-rules.md) |
| BPMN SDD document shape | [assets/templates/sdd-template.md](assets/templates/sdd-template.md) |
| CLI conventions and the side-effect boundary | [references/cli-conventions.md](references/cli-conventions.md) |
| Keeping content public-safe | [references/public-safety.md](references/public-safety.md) |
| Bundled offline validator (every PO.Frontend rule) | [validator/README.md](validator/README.md) |
| Package, upload, publish, run, or manage instances | [references/operate/CAPABILITY.md](references/operate/CAPABILITY.md) |
| Diagnose a failed or misbehaving run | [references/diagnose/CAPABILITY.md](references/diagnose/CAPABILITY.md) |
| Project layout and generated package files | [references/shared/project-layout.md](references/shared/project-layout.md) |
