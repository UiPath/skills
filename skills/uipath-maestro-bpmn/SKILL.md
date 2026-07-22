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

Work the four steps quickly, but keep the path matched to the user's ask. Treat
requests to discover before authoring, save raw registry JSON/evidence, or "do
not author yet" as discovery-only even if they describe an eventual BPMN. In
that mode, immediately create `registry-evidence/`, run and save `registry pull
--output json`, `registry list --output json` or `registry search ... --output
json`, and `registry get <type> --output json` for each requested type; do not
read deep authoring references or scaffold a project. For authoring asks, author
early: do not pre-read every reference before writing. Read a reference only
when you reach the structure it covers, get the needed templates, then write the
first complete draft before further spelunking. If
[references/structural-bpmn.md](references/structural-bpmn.md) or
[references/expression-authoring.md](references/expression-authoring.md)
directly covers the requested construct, write a first complete draft before
further spelunking.

For registry-evidence-only tasks, be command-first and time-boxed:

- Create `registry-evidence/` before anything else.
- Run the registry command forms the user asked for. For RPA job + internal
  message discovery, use `uip maestro bpmn registry list --limit -1 --output
  json`, `uip maestro bpmn registry get Orchestrator.StartJob --output json`,
  and `uip maestro bpmn registry get Maestro.ReceiveMessageEvent --output json`.
- If `uip` is unavailable in a temp/smoke sandbox, do not search the repo for a
  replacement CLI or inspect test fixtures. Still issue the required `list` and
  `get` command forms once each with output redirected to their evidence files
  (allowing failure with `|| true`), so the transcript shows the discovery loop:
  `uip maestro bpmn registry list --limit -1 --output json` and
  `uip maestro bpmn registry get <type> --output json`. Record the failed CLI
  attempts in `registry-evidence/cli-error.txt`, then overwrite the expected
  `registry-evidence/*.json` files with valid JSON evidence from
  `skills/uipath-maestro-bpmn/validator/bpmn-spec.json` containing the same
  extension types and stop.

1. **Discover.** `uip maestro bpmn registry pull` **once** (cached for the
   session — do not re-pull), then `list` / `search` to map intent to extension
   types; `uip is connections list --all-folders` for live connections (always
   `--all-folders` — a folder-scoped list silently misses connections). Confirm
   every selection with the user (use AskUserQuestion). Never fabricate an identifier.
   See [references/registry-workflow.md](references/registry-workflow.md).
2. **Get templates.** `uip maestro bpmn registry get <type> --output json` for
   each chosen registry-owned node only. Enrich `Intsvc.*` connector nodes with
   `--connection-id`/`--object-name`. Do not call `registry get` for structural
   gaps the registry never owns: sequence flows, gateways, events, boundary
   events, multi-instance/loop markers, `errorMapping`/retry structure, or
   diagrams.
3. **Assemble.** Author directly from the complete minimal file in
   [references/structural-bpmn.md](references/structural-bpmn.md#a-complete-minimal-file-author-from-this-not-from-fixtures)
   plus each node's `xmlTemplate` (fill placeholders only). That skeleton already
   shows variables, the entry point, a branch, and the diagram. **Do not read the
   validator's `test/fixtures/`, task fixtures, or generated package files to
   infer authoring patterns** — fixture spelunking is the top reason authoring
   runs out of time. Add only the structural pieces your process needs (extra
   gateways, events, boundary events, containers, multi-instance markers,
   expression/error mappings, retry attributes), then generate one
   `BPMNShape`/`BPMNEdge` per node and flow. For local authoring prompts, use the
   plain project layout `<ProjectName>/<ProjectName>.bpmn` with
   `<ProjectName>/project.uiproj`; do not create `*Solution/`, package files, or
   `.uipx` artifacts unless the user explicitly asks to package or operate the
   project.
   When routing on an Actions.HITL user task's outcome, the sequence-flow
   conditions from the exclusive gateway must reference the exact variable bound
   by the HITL template's `<uipath:output ... var="...">` (for example
   `=vars.Var_HitlResult == "approve"`), not only a copied or derived script
   variable.
   If a local-only prompt asks for `operate.json`, `entry-points.json`,
   `bindings_v2.json`, or `package-descriptor.json`, follow the minimal local
   metadata shape in
   [references/shared/local-metadata-regeneration-guide.md](references/shared/local-metadata-regeneration-guide.md#minimal-local-metadata-shape).
   Do not copy CLI scaffold metadata shapes into a synthetic local project.
4. **Validate.** There is **no** `uip maestro bpmn validate` CLI command. Run the
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
| CLI conventions and the side-effect boundary | [references/cli-conventions.md](references/cli-conventions.md) |
| Keeping content public-safe | [references/public-safety.md](references/public-safety.md) |
| Bundled offline validator (every PO.Frontend rule) | [validator/README.md](validator/README.md) |
| Package, upload, publish, run, or manage instances | [references/operate/CAPABILITY.md](references/operate/CAPABILITY.md) |
| Diagnose a failed or misbehaving run | [references/diagnose/CAPABILITY.md](references/diagnose/CAPABILITY.md) |
| Project layout and generated package files | [references/shared/project-layout.md](references/shared/project-layout.md) |
