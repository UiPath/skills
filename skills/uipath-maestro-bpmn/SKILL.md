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

Work the five steps quickly and author early — do not pre-read every reference
before writing. Read a reference only when you reach the structure it covers.

1. **Clarify behavior (hard gate).** Before discovery, shell commands, or file
   writes, identify missing business semantics that affect routing, output
   values, handoffs, waits, or approvals. If any are missing, ask concise,
   decision-oriented questions with AskUserQuestion and stop that turn. Never
   scaffold guessed policy for later correction. If AskUserQuestion is not
   exposed, ask the same questions in plain text and wait. If the user already
   supplied the semantics, proceed.

   For an interactive or underspecified request, do not claim the contract is
   complete until every applicable row in this checklist is explicit:

   - exact input and output variable names, primitive types, and entry-point
     direction;
   - allowed values, normalization rules for each compared input (including
     exactly which string operands are case-insensitive), exact output
     literals, and any byte-for-byte correlation/key requirement;
   - decision truth table and precedence when more than one rule applies;
   - failure, ambiguity, unavailable-system, and human-review behavior;
   - required ordering, which business decisions must be visible as control
     flow rather than hidden in a calculation, parallel workstreams, joins,
     waits, and completion semantics;
   - local-versus-live execution boundary, validation, packaging, and whether
     cloud execution is authorized.

   In the first clarification turn, explicitly ask all of the following when
   they are not already stated:

   - for every string input used by a rule, whether comparison is
     case-sensitive and whether whitespace or empty-string normalization is
     required;
   - which validation and success-routing decisions the user expects to see as
     explicit diagram branches rather than hidden in expressions;
   - which workstreams may run concurrently, their exact branch grouping, and
     where they must synchronize;
   - whether named external systems are live connectors or
     simulated/intent-only work, and whether upload, debug, or run is
     authorized.

   These are mandatory business-contract questions, not optional BPMN
   implementation details. Do not infer normalization from example casing,
   diagram visibility from the existence of routing rules, branch grouping
   from a generic request for concurrency, or the execution boundary from a
   scenario that mentions CRM, Jira, email, or Slack. A question about allowed
   values does not by itself ask about normalization, and asking whether two
   steps can overlap does not establish the complete parallel topology. Before
   sending the first clarification response, verify it contains explicit
   questions covering **Typed inputs/outputs**, **Normalization**, **Diagram
   visibility**, **Parallel topology**, and **Execution boundary**. Before
   discovery, scan the actual questions you asked—not merely facts the user
   volunteered—and close any missing category in a focused follow-up turn.

   A user response may answer only part of the checklist. Ask a focused second
   round for every material gap and stop again. Registry discovery is authoring
   work: do not start it while a checklist row is still unknown. Once the hard
   gate is satisfied, make registry discovery the next action. Do not spend an
   uninterrupted reasoning pass solving the complete node graph, expressions,
   and diagram coordinates before the first tool call; those decisions belong
   in the bounded assembly checkpoints below.
2. **Discover.** `uip maestro bpmn registry pull` **once** (cached for the
   session — do not re-pull), then `list` / `search` to map intent to extension
   types; `uip is connections list --all-folders` for live connections (always
   `--all-folders` — a folder-scoped list silently misses connections). Confirm
   every selection with the user (use AskUserQuestion). Never fabricate an identifier.
   See [references/registry-workflow.md](references/registry-workflow.md).
3. **Get templates.** `uip maestro bpmn registry get <type> --output json` for
   each chosen node. Enrich `Intsvc.*` connector nodes with
   `--connection-id`/`--object-name`.
4. **Assemble.** Author directly from the complete minimal file in
   [references/structural-bpmn.md](references/structural-bpmn.md#a-complete-minimal-file-author-from-this-not-from-fixtures)
   plus each node's `xmlTemplate` (fill placeholders only). That skeleton already
   shows variables, the entry point, a branch, and the diagram. **Do not read the
   validator's `test/fixtures/` to infer the pattern** — it is the top reason
   authoring runs out of time. Add only the structural pieces your process needs
   (extra gateways, events, boundary events, containers, multi-instance markers),
   then generate one `BPMNShape`/`BPMNEdge` per node and flow.

   For a large process (roughly more than ten variables or twelve visible flow
   elements), a single full-file `Write` is forbidden: streaming one giant XML
   tool argument can consume the whole turn without creating a file. Do not
   mentally draft the entire XML before the first write and do not paste BPMN
   into the chat response. Keep a compact node/flow/variable table with stable
   IDs. Immediately after registry `get`, run
   `scripts/scaffold-project.py` with the project name and repeated
   `--input name:type` / `--output-variable name:type` arguments. This creates
   the complete local metadata set and a small, well-formed start-to-end BPMN
   with the typed contract; do not retype that scaffold. Then expand it with
   bounded `Edit` calls in this order: at most four executable nodes and their
   flows per edit; remaining nodes/flows; then diagram shapes and edges in small
   groups. Validate XML well-formedness between phases. The final artifact must
   still be one coherent registry-derived BPMN file; the helper owns only the
   generic project shell, not business nodes, routing, expressions, or layout.
   Copy every elicited type token exactly into the scaffold command:
   `integer` and `number` are distinct contracts and must never be widened or
   substituted. Before the first graph edit, compare the generated BPMN
   variables and `entry-points.json` schemas back to the user's typed contract.

   The first positional argument is the project directory and also supplies the
   project name by default; use `--name` only when those differ:

   ```bash
   python3 scripts/scaffold-project.py <ProjectName> \
     --input requestId:string \
     --output-variable status:string
   ```

   For a large **deterministic variable process** whose activities are all the
   registry-confirmed `BPMN.Variables` type, do not serialize the expanded BPMN
   XML through `Write` or `Edit`. That can exceed the model/tool-call limit even
   when attempted in phases. Express the complete business graph in a compact
   `process-plan.json`, then run the generic assembler:

   ```bash
   python3 scripts/assemble-variable-process.py <ProjectName> process-plan.json
   ```

   The plan is the authored source of truth: it must still specify every task,
   output mapping, gateway, default, guarded flow, and exact branch topology.
   The assembler only expands that plan into the already-retrieved
   `BPMN.Variables` mapping shape, incoming/outgoing references, and one
   BPMN-DI shape/edge per element. It derives variable ids and types from the
   typed scaffold. Use `{{variableName}}` in expressions; the assembler expands
   it to the declared `vars.<id>` reference and rejects unknown variables or
   JavaScript-only operators without `=js:`.

   Minimal plan shape:

   ```json
   {
     "nodes": [
       {"id":"Task_Set","kind":"task","name":"Set status",
        "outputs":{"status":"Approved"}},
       {"id":"GW_Decide","kind":"exclusiveGateway","name":"Approved?",
        "default":"Flow_No"},
       {"id":"GW_Merge","kind":"exclusiveGateway","name":"Merge"}
     ],
     "flows": [
       {"id":"Flow_Start","source":"Start_1","target":"GW_Decide"},
       {"id":"Flow_Yes","source":"GW_Decide","target":"Task_Set",
        "condition":"={{approved}} == true"},
       {"id":"Flow_No","source":"GW_Decide","target":"GW_Merge"},
       {"id":"Flow_Done","source":"Task_Set","target":"GW_Merge"},
       {"id":"Flow_End","source":"GW_Merge","target":"End_1"}
     ]
   }
   ```

   Gateways must still satisfy the normal BPMN rules, and all paths must form an
   acyclic graph for automatic layout. If review reveals a graph defect, edit
   the plan and rerun with `--replace`; never fall back to a giant XML edit.
   Before assembly, audit the plan itself against the full decision table,
   including overlap/adversarial rows. Preserve every qualifier on a later
   failure rule: an unavailable-system branch that applies only to particular
   severities or tiers must test that eligibility explicitly. A route label is
   not a safe proxy unless the elicited truth table proves the equivalence for
   every route, including duplicate/existing-item cases.
   Processes containing connector, agent, RPA, HITL, event, or other registry
   node types are outside this assembler's scope and continue to use bounded
   direct assembly from their exact registry templates.

   Preserve the requested process semantics in the diagram. When a business
   route or validation decision must be visible, model it with a genuine
   diverging gateway, guarded non-default flows, and an explicit default flow;
   do not collapse the whole decision tree into one deeply nested mapping
   expression. `BPMN.Variables` tasks remain appropriate for deterministic
   value assignment before or within those paths. Conversely, do not add a
   decorative gateway whose branches perform indistinguishable work.
   Sequence-flow conditions are read-only: they select a path but cannot assign
   outputs. Put branch-specific output mappings in registry-backed
   `BPMN.Variables` tasks on those paths before convergence.
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

   If the requested stopping point includes a local package, use the positional
   `pack` syntax after validation (there is no `package` subcommand and no
   `--project-dir` option):

   ```bash
   uip maestro bpmn pack <project-path> <output-path> --output json
   ```

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
4. **Confirm before authoring.** Confirm the chosen connector/connection/process,
   process structure, and any missing business rules with the user
   (AskUserQuestion). Never guess policy that determines routing or outputs.
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
