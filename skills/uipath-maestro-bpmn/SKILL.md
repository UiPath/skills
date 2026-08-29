---
name: uipath-maestro-bpmn
description: "UiPath Maestro BPMN / Process Orchestration: author (registry-driven), validate, package, operate, and diagnose .bpmn projects. For .flow use uipath-maestro-flow; for case plans use uipath-maestro-case."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# Reasoning budget
- Match reasoning to step difficulty and bias toward acting; for mechanical / IO / format steps, if a
  provided script already covers the task, run it — don't re-derive it.
- Save deep, extended reasoning for the one genuinely hard judgment a script can't make for you.

# Working style
- **Understand first, then decide.** Read this skill's SKILL.md and understand the scripts it ships before you act. Then plan accordingly, such as run a script as-is when it fits, change a script when it's close, or write extra scripts to complement — based on what the scripts actually do, not a guess.
- **Plan the whole path up front, then chain.** Outline the full sequence of steps before running anything, batch independent steps into one turn, and pipeline the whole plan in as few turns as possible. Don't do things that can be pipelined into one call turn-by-turn.
- **Inspect an input ONCE.** To learn a file's structure (sheets/columns, pages, form fields, keys), dump it once — ideally to a file you then grep — never re-open the same file field-by-field or retry it with several libraries.
- **Don't repeat work.** Do not rerun a command when its inputs and relevant state are unchanged, and do not reread an unchanged file, script, or SKILL.md already in context. After a tool or command may modify a file, reread the affected content before relying on it.
- **Write code once and reuse.** If a step needs code, write it once as a small script (paths/params as CLI args) and call it; don't paste near-duplicate inline python across turns. Keep it terse — no comment banners or narration in inline scripts.
- **Keep outputs small.** Don't put large tool results and outputs into the context, instead write them into a file and use tools to inspect them. If there is no tool available, you should write your own scripts to inspect the file.
- **Don't do anything unnecessary.** Don't call tools, read files, or put results into context unless they're immediately needed.

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

The skill can edit an existing file. If the edit introduces one of the shapes in
[Patterns](#patterns), use that guide — inserting a pattern into a running
process is a normal edit, not a reason to skip the shape. Make **surgical**
edits and preserve content you did not author: unknown `uipath:*` elements, `uipath:migrationVersion`,
tags, imported Integration Service payloads, and stable element IDs. Do not
regenerate the whole file or drop extension data the skill does not recognize —
preserve-only structures (see the blocklist in
[references/structural-bpmn.md](references/structural-bpmn.md)) round-trip
untouched. Never normalize existing nodes to this skill's canonical templates:
do not add missing attributes (e.g. `type="json" target="bodyField"` on an
existing `uipath:input`) to elements the edit does not target — on untouched
neighbors only wiring (`bpmn:incoming`/`bpmn:outgoing`) may change.

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

## Patterns

Seven recurring process shapes, for building a new process and for extending
one that already runs. Each guide gives a worked-out topology — nodes, wiring,
gateway conditions, variables — and the reasoning behind it. Many topologies
pass validation for the same request; these are known-good shapes, not
specifications. Adapt them: add steps, drop branches, and change
counts as the process needs. Each guide's "Why it works" names the parts that
carry the shape — change those and you are building something else, so say so.
Read the guide for each pattern the process actually uses — one for a simple
process, several for a composed one — and none for a pattern you are not
building.

Every guide's shape table marks each node **Entry** (omit when inserting into a
process that already runs), **Mechanism** (changing it changes the pattern), or
**Placeholder** (bind it, or skip it if the process already does this).

| Pattern | Reach for it when | Guide |
| --- | --- | --- |
| `ai-decision-review` | AI makes one call; act on it, or a human reviews it | [ai-decision-review-guide.md](references/patterns/ai-decision-review-guide.md) |
| `approval-chain` | A request needs sign-off from several people | [approval-chain-guide.md](references/patterns/approval-chain-guide.md) |
| `smart-triage` | Inbound work sorted into categories, each handled elsewhere | [smart-triage-guide.md](references/patterns/smart-triage-guide.md) |
| `external-wait` | The process waits on an outside party under an SLA | [external-wait-guide.md](references/patterns/external-wait-guide.md) |
| `high-volume-batch` | Many independent items processed in one run | [high-volume-batch-guide.md](references/patterns/high-volume-batch-guide.md) |
| `failure-escalation` | Unhandled failures must never disappear silently | [failure-escalation-guide.md](references/patterns/failure-escalation-guide.md) |
| `queue-distribution` | An Orchestrator queue hands work across runtimes | [queue-distribution-guide.md](references/patterns/queue-distribution-guide.md) |

**Do not reach for a pattern** when the ask is a short linear process, a single
node, or a change that does not introduce one of these shapes. A pattern is
never a wrapper to retrofit onto work that does not need one.

Using more than one pattern in one process? Read
[references/patterns/composing-guide.md](references/patterns/composing-guide.md)
first — which pattern keeps its start event, the four ways the rest join it, how
variables cross a nesting boundary, and the two placements the engine
constrains. A single pattern needs only its own guide.

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
- If `uip` is unavailable in a temp/smoke sandbox, or if it writes a valid JSON
  failure object such as `"Result": "Failure"` instead of registry content, do
  not search the repo for a replacement CLI or inspect test fixtures. Still
  issue the required `list` and `get` command forms once each with output
  redirected to their evidence files (allowing failure with `|| true`), so the
  transcript shows the discovery loop:
  `uip maestro bpmn registry list --limit -1 --output json` and
  `uip maestro bpmn registry get <type> --output json`. Record the failed CLI
  attempts in `registry-evidence/cli-error.txt`, then overwrite any failure JSON
  in the expected `registry-evidence/*.json` files with valid JSON evidence from
  `skills/uipath-maestro-bpmn/validator/bpmn-spec.json` containing the same
  extension types and stop. The final evidence files must literally contain the
  discovered type names, for example `Orchestrator.StartJob` and
  `Maestro.ReceiveMessageEvent`.

1. **Discover.** `uip maestro bpmn registry pull` **once** (cached for the
   session — do not re-pull), then `list` / `search` to map intent to extension
   types; `uip is connections list --all-folders` for live connections (always
   `--all-folders` — a folder-scoped list silently misses connections). Confirm
   every selection with the user (use AskUserQuestion). Never fabricate an identifier.
   See [references/registry-workflow.md](references/registry-workflow.md).
2. **Get templates.** `uip maestro bpmn registry get <type> --output json` for
   each chosen registry-owned node only. Fetch every chosen template in **one**
   Bash call, not one command per turn — each shell round-trip is a model turn
   and dozens of them exhaust the run's time budget before authoring finishes:
   `for t in TypeA TypeB TypeC; do uip maestro bpmn registry get "$t" --output json; done`.
   Enrich `Intsvc.*` connector nodes with `--connection-id`/`--object-name`. Do not call `registry get` for structural
   gaps the registry never owns: sequence flows, gateways, events, boundary
   events, multi-instance/loop markers, `errorMapping`/retry structure, or
   diagrams. If a registry template's BPMN host tag is PascalCase (for example
   `<bpmn:SendTask>` or `<bpmn:ReceiveTask>`), normalize the host tag to the
   serializer's lower-camel BPMN element (`<bpmn:sendTask>`,
   `<bpmn:receiveTask>`) while preserving the `uipath:*` payload exactly.
3. **Assemble.** Author directly from the complete minimal file in
   [references/structural-bpmn.md](references/structural-bpmn.md#a-complete-minimal-file-author-from-this-not-from-examples)
   plus each node's `xmlTemplate` (fill placeholders only). That skeleton already
   shows variables, the entry point, a branch, and the diagram. **Do not
   reverse-engineer authoring patterns from task fixtures, generated package
   files, or the CLI's compiled bundle (`@uipath/cli/dist/*.js`)** — such
   spelunking is the top reason authoring runs out of time.
   Add only the structural pieces your process needs (extra
   gateways, events, boundary events, containers, multi-instance markers,
   expression/error mappings, retry attributes), then run
   `uip maestro bpmn format <file.bpmn>` to generate the diagram. If `format` reports `unknown command`, update the CLI (see [references/cli-conventions.md](references/cli-conventions.md)); if upgrading is unavailable, use the fallback DI structure in [references/structural-bpmn.md](references/structural-bpmn.md). For local authoring prompts, use the
   plain project layout `<ProjectName>/<ProjectName>.bpmn` with
   `<ProjectName>/project.uiproj`; do not create `*Solution/`, package files, or
   `.uipx` artifacts unless the user explicitly asks to package or operate the
   project.
   When adding draft or preserve-only case-management variants, include a real
   lowercase `<uipath:caseManagement version="v1">...</uipath:caseManagement>`
   payload with synthetic content as a separate preserve-only extension. Do not
   treat an `Orchestrator.StartCaseMgmtProcess*` typed activity shell as a
   substitute for that payload when the user asks to preserve case-management
   contract variants.
   When asked to preserve a generic unsupported `uipath:Activity`, write the
   actual capitalized element `<uipath:Activity version="v1">...</uipath:Activity>`.
   Do not write `<uipath:activity><uipath:type value="uipath:Activity" ... />`;
   that is a lowercase typed shell, not the preserve-only generic payload.
   When writing public-safe placeholders into XML attribute values, XML-escape
   angle brackets: use `&lt;TENANT_URL&gt;`, `&lt;FOLDER_KEY&gt;`, and
   `&lt;CONNECTION_NAME&gt;` in attributes. Raw `<PLACEHOLDER>` text is only safe
   in element text or CDATA; unescaped angle brackets inside attributes make the
   BPMN not well-formed.
   When routing on an Actions.HITL user task's outcome, the sequence-flow
   conditions from the exclusive gateway must reference the exact variable bound
   by the HITL template's `<uipath:output ... var="...">` (for example
   `=vars.Var_HitlResult == "approve"`), not only a copied or derived script
   variable.
   For Integration Service draft notes, name every CLI-owned blocker literally,
   including the exact phrase `connection binding`, plus dynamic schemas,
   generated outputs, `bindings_v2.json`, and package metadata. Avoid softer
   wording such as "connection and process binding" because it hides the concrete
   artifact the CLI must supply.
   If the user asks for the package metadata files, or to package or operate,
   run `uip maestro bpmn update-metadata <file.bpmn>` to generate the five
   files, and keep its output as written — that shape is the contract `pack`
   consumes. Only fall back to the equivalent hand-authored shape in
   [references/shared/local-metadata-regeneration-guide.md](references/shared/local-metadata-regeneration-guide.md#minimal-local-metadata-shape)
   when the CLI is unavailable. Every root start event needs a
   `<uipath:entryPointId value="<uuid>" />` child in its `extensionElements` or
   the project generates zero entry points.
4. **Validate.** Run the CLI validator — it runs the full PO.Frontend canvas
   rule set (structural rules plus variable, method-call, input-type, and
   event-object checks) offline, plus deploy-readiness checks:

   ```bash
   uip maestro bpmn validate <file.bpmn> --output json
   ```

   Exit 0 = valid; exit 1 = validation failed (the envelope lists each issue
   with its rule code). Warnings are reported but do not fail the run. Validate
   once; fix only error-severity findings. Do not re-validate in a loop chasing
   warnings. If `validate` reports "unknown command" or clearly skips the
   structural rules, the installed CLI predates them — update it (see
   [references/cli-conventions.md](references/cli-conventions.md)). See
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
| Gateways: exclusive, parallel, inclusive, event-based (complex is preserve-only) | Authored (registry gap) |
| Events + event-definition matrix: message, timer, error, terminate (end-only). Signal/escalation/conditional/link/compensate/cancel/multiple are preserve-only | Authored (registry gap); payload per canvas serializer |
| Boundary events: `attachedToRef`, interrupting/non-interrupting (`cancelActivity`) | Authored (registry gap) |
| Subprocess, event subprocess (`triggeredByEvent`), call activity | Authored (registry gap); call-activity payloads from registry |
| Multi-instance / loop characteristics | Authored from canvas contract — **registry exposes no template (registry gap)** |
| `bpmndi:BPMNDiagram` (shape per node, edge per flow) | Generated via `uip maestro bpmn format <file.bpmn>` — **registry emits none (registry gap)** |

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
   BPMN XML element names are case-sensitive: use exact lower-camel tags such
   as `<bpmn:startEvent>`, `<bpmn:intermediateCatchEvent>`,
   `<bpmn:scriptTask>`, and `<bpmn:endEvent>`. Do not write PascalCase tags
   like `<bpmn:IntermediateCatchEvent>`.
4. **Confirm before authoring.** Confirm the chosen connector/connection/process
   and the process structure with the user (AskUserQuestion).
5. **The diagram is mandatory.** Import is diagram-driven — every node needs a
   `BPMNShape`, every flow a `BPMNEdge`, or it will not appear on the canvas.
6. **Preserve the registry's node-type shape.** Most `uipath:activity` /
   `uipath:event` / `uipath:mapping` templates declare their type as a nested
   `<uipath:type value="<Type>" version="v1" />`. Some runtime-authored
   templates use the payload's `type` attribute instead; notably,
   `Orchestrator.StartAgentJob` is a direct child of `bpmn:serviceTask` with
   `<uipath:activity type="Orchestrator.StartAgentJob" version="v1">`. Both
   declarations are supported. Paste the selected registry template literally
   and do not normalize one form into the other.
   Event extension types (`Intsvc.WaitForEvent`, `Intsvc.EventTrigger`,
   `Maestro.ReceiveMessageEvent`, `Maestro.SendMessageEvent`) must use
   `<uipath:event>`, including when the BPMN host is task-like such as
   `<bpmn:receiveTask>`.
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
11. **Retry is node configuration, never canvas.** Handle transient failures
   with `uipath:retry` on the activity. Never draw a retry loop from gateways
   and timer events. See
   [references/structural-bpmn.md](references/structural-bpmn.md#choosing-an-error-handling-construct).
12. **Task SLA is task configuration, never canvas.** Approval timers,
   reassignment, and escalation-on-breach live on the user task. Do not model
   them as boundary timers around it.
13. **An error event subprocess is interrupting and terminal.** When it fires,
   the normal path stops and the instance records **Completed**, not Faulted.
   Every path through it must end in an explicitly named outcome, or a handled
   failure is indistinguishable from success. For recover-and-continue, attach
   an error boundary event instead.
14. **A different target system is not, by itself, a different shape.** Swapping
   Document Understanding for a UiPath agent, or Outlook for Gmail, changes a
   binding. Reshape when the process genuinely differs — not merely because the
   target system did.
15. **You author the process; you are never a participant in it.** Where a shape
   calls for reasoning, classification, or extraction at runtime, place and bind
   the node that will perform it — a UiPath agent, Document Understanding, a
   business rule task. Never do that work at authoring time or hardcode its
   result. Bare "agent" in any process description means a UiPath agent, never
   you.

## References

| Topic | Read |
| --- | --- |
| Discover → template → bind → assemble loop | [references/registry-workflow.md](references/registry-workflow.md) |
| Structural BPMN, event matrix, boundary events, containers, multi-instance, diagram, validation | [references/structural-bpmn.md](references/structural-bpmn.md) |
| Worked-out topology for a recurring process shape, and how shapes compose | Patterns table above → `references/patterns/*-guide.md` |
| Runtime expressions, `vars.`/`bindings.`/`iterator.`, `=js:` (Jint) syntax | [references/expression-authoring.md](references/expression-authoring.md) |
| CLI conventions and the side-effect boundary | [references/cli-conventions.md](references/cli-conventions.md) |
| Keeping content public-safe | [references/public-safety.md](references/public-safety.md) |
| Package, upload, publish, run, or manage instances | [references/operate/CAPABILITY.md](references/operate/CAPABILITY.md) |
| Diagnose a failed or misbehaving run | [references/diagnose/CAPABILITY.md](references/diagnose/CAPABILITY.md) |
| Project layout and generated package files | [references/shared/project-layout.md](references/shared/project-layout.md) |
