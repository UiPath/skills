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
registry-driven for registered nodes**: their execution payloads come from
templates the registry serves. The structural BPMN and serializer-owned scaffold
metadata that hold those nodes together (process scaffold, variables, bindings,
entry points, sequence flows, gateways, events, boundary events, containers,
multi-instance markers, and the diagram) are authored from the documented spec
and canvas contract. Packaging, operating (upload, publish, run, manage), and
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

For an existing ScriptTask, preserve its mapping discriminator and
`uipath:scriptVersion`, and do not normalize a working brownfield node merely
because the new-node authoring contract differs. Migration requires explicit
confirmation — see
[references/structural-bpmn.md](references/structural-bpmn.md#script-tasks--jint-authoring-contract).

For `.flow` JSON use `uipath-maestro-flow`; for XAML/coded workflows use
`uipath-rpa`; for Python agents use `uipath-agents`; for Case plans use
`uipath-maestro-case`.

## The model

Two halves make a valid Maestro `.bpmn`:

1. **Registry-listed node payloads — registry-owned.** Each listed node's
   execution XML (`uipath:activity` / `uipath:event` / `uipath:mapping`, its
   `context`, `input`, `output`, and `bindingInfo`) comes from
   `uip maestro bpmn registry get <type>`'s `xmlTemplate`. **Never hand-author a
   registry-owned node payload from prose.**
2. **Structural BPMN and scaffold metadata — spec/canvas-owned.** The registry emits no
   `<bpmn:definitions>`/`<bpmn:process>`, no sequence flows, no gateway
   conditions/defaults, no event-definition payloads, no boundary-event
   attributes, no subprocess/loop structure, and no diagram. Serializer-owned
   scaffold extensions such as `uipath:variables`, `uipath:bindings`,
   `uipath:entryPointId`, and `uipath:migrationVersion` also come from this
   contract rather than a node template. Author these from
   [references/structural-bpmn.md](references/structural-bpmn.md), which is
   grounded in the registry spec, the CLI scaffold, and the canvas serializer.

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
**Placeholder** (bind it, or skip it if the process already does this). Author
the element the table names. A **Placeholder** whose target is still undecided
is that element with its registry payload and the identity slots left as
public placeholders, never a bare `bpmn:task` standing in for the work. That
applies to phase 4, where nodes are real. In a phase 2 skeleton every activity
is deliberately a bare `bpmn:task` — see
[references/phase-2-skeleton.md](references/phase-2-skeleton.md).

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

Authoring runs four phases in order. The **mode** decides how far you go and
whether you stop to ask; it never changes what a phase does.

| Phase | What happens | Reference |
| --- | --- | --- |
| **1 — Preflight** | Check login, scan the open directory for an existing solution and project, resolve the mode. Writes nothing, so it runs in every mode. | Steps 0–1 below |
| **2 — Skeleton** | Scaffold the project, author blank boxes with real control flow, `format`, `validate`, `refresh`, upload. Makes **no registry calls**. | [references/phase-2-skeleton.md](references/phase-2-skeleton.md) |
| **3 — Iterate** | Adjust the shape, re-`format`, re-upload, repeat until the user agrees it. | [references/phase-2-skeleton.md](references/phase-2-skeleton.md#iterating) |
| **4 — Wire it up** | Registry discovery, template fetch, real payloads pasted into the existing boxes, revalidate, refresh. | Steps 1–5 below |

Phase 2 is not a draft-only step. **Auto mode builds the same skeleton**, then
continues into phase 4 without stopping — so a template error is never tangled
up with a structural one.

### Modes

Two modes are detected, never asked:

| Mode | Detect it when | Phases |
| --- | --- | --- |
| **Brownfield** | A `.bpmn` the request targets already exists. Do not run `init`; if the file is bare (no `project.uiproj`), bootstrap it with the two-key `project.uiproj` + `refresh` path in step 3. Pre-empts the question below — the shape is already on disk. | 1, then 3–4 |
| **Discovery-only** | The request asks to discover before authoring, save raw registry JSON/evidence, or explicitly "do not author yet", even if it describes an eventual BPMN. Create `registry-evidence/`, save `registry pull --output json`, `registry list --output json` or `registry search ... --output json`, and `registry get <type> --output json` for each requested type. Do not scaffold a project and do not read deep authoring references. Recipe: [references/registry-workflow.md](references/registry-workflow.md#registry-evidence-only-tasks). | 1, then terminate |

Otherwise ask the user before scaffolding (AskUserQuestion), offering
**"Something else"** last so they can describe a different path:

| Mode | Choose it when | Phases |
| --- | --- | --- |
| **Draft** (recommend this) | The default for a new process. Also whenever the user wants to see the shape first, requirements are vague, the process branches or runs to roughly five or more steps, or the wording is *design* / *what would it look like* / *show me*. | 1–3, stop at the approval gate |
| **Auto** | The user gave the exact topology, the process is short and linear, or the wording is *just build it*. | 1–4, no stop |

Resolve it in this order. An explicit instruction from the user ("just build
it", "show me the shape first") decides it — obey it and never ask. Otherwise
ask. When nobody is available to answer (non-interactive or headless), take
**Auto** and record that choice prominently in the final report: draft mode's
approval gate cannot be satisfied with no user to approve it, so drafting would
stall.

**Draft mode is never the deliverable on its own.** The user's approval of the
shape is what authorizes phase 4. Without it, report the skeleton as an
unapproved draft rather than as a finished process.

### Deliverable scope

An independent dial: *package-ready* when pack, upload, publish, deploy, debug,
or run is asked for, *source-only* when none of those is. A source-only
deliverable skips `init` entirely — every `init` variant, including
`--skip-solution-registration`, writes the four generated package files, and
Rule 16 requires source-only output to be the `.bpmn` plus its notes file and
nothing else. Scope is independent of whether the process uses an Integration
Service connector: a plain three-node RPA process can be source-only too.
Draft mode needs package-ready scope, because the user sees the shape by
opening an uploaded solution.

Author early: do not pre-read every reference before writing. Read a reference
only when you reach the structure it covers, get the needed templates, then
write the first complete version before further spelunking. If
[references/structural-bpmn.md](references/structural-bpmn.md) or
[references/expression-authoring.md](references/expression-authoring.md)
directly covers the requested construct, write it before further spelunking.

0. **Check login.** `uip login status --output json`, chained in the same Bash
   call as step 1's `registry pull` — not a turn of its own. Without login,
   `registry pull` returns only the built-in (OOTB) extension types, so
   connector and process discovery comes back silently incomplete: tell the
   user rather than discovering against a half-registry. Local authoring and
   `validate` still work offline — see
   [references/cli-conventions.md](references/cli-conventions.md#login-boundary).
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
   `BPMN.ScriptTask` is the registry lookup key, but a new node serializes
   `<uipath:type value="BPMN.Variables" version="v1" />` — never the lookup
   key. Local validation accepts the older discriminator, so a clean
   `validate` does not prove that mapping is right. For the compatibility
   fallback and its scope, see
   [references/structural-bpmn.md#script-tasks--jint-authoring-contract](references/structural-bpmn.md#script-tasks--jint-authoring-contract).

**2b. Create or adopt the project (greenfield, package-ready only).** Skip this
step for discovery-only, for brownfield/bare-`.bpmn` edits, and for any
source-only deliverable. Otherwise chain it after Discover in the same turn.
Phase 1's scan already answered whether a solution exists; adopt what it found
rather than scanning again. If it found nothing:

```bash
find . -maxdepth 2 -type f -name '*.uipx' -print
```

If one is found, stop and ask the user which to use (AskUserQuestion: one
option per solution found, plus "Create a new solution"). Never silently
adopt, initialize, or repair an existing solution. Say in that question that
adopting one means a later `upload` overwrites its cloud copy, because this is
the only point where that is still the user's choice to make. Otherwise initialize the
project with `uip maestro bpmn init <ProjectName> --output json` and author at
the returned `Data.Path`. `init` is idempotent — re-running reports
`AlreadyRegistered` — and outside a solution it auto-scaffolds
`<ProjectName>Solution/`, nesting the project at
`<ProjectName>Solution/<ProjectName>/`; a non-empty target directory is left
untouched and the project still lands there. `--skip-solution-registration`
suppresses the `*Solution/` wrapper and its `.uipx`, but still writes the four
generated JSON files, so it does not produce a source-only deliverable — skip
`init` for that instead. `init` writes six files — the
`.bpmn`, `project.uiproj`, and the four generated JSON files
(`bindings_v2.json`, `entry-points.json`, `operate.json`,
`package-descriptor.json`) — preserve the four generated ones as written.
`init` takes a project name, not a path, and writes under the current
directory: `./<ProjectName>/` with `--skip-solution-registration` or inside an
existing solution, `./<ProjectName>Solution/<ProjectName>/` otherwise. To land a
project at a path the user named, `mkdir -p` its parent and run `init` there
with the leaf as the name — and either pass `--skip-solution-registration` or
make that parent a solution first, because default `init` inserts a
`<ProjectName>Solution/` level the requested path does not have. Check
`Data.Path` against the requested path before editing. The init scaffold
declares no `xsi` namespace: add
`xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"` to `bpmn:definitions`
before writing any `xsi:type` attribute. See
[references/shared/local-metadata-regeneration-guide.md](references/shared/local-metadata-regeneration-guide.md).

3. **Assemble.** For greenfield, author into the `.bpmn` that step 2b's `init`
   already generated, using `Edit` — never `Write` a full-file replacement over
   it. Editing in place preserves the four generated JSON files, the
   initializer's `Event_start` id, and its `uipath:entryPointId`; keep them, and
   the "renamed start event ⇒ `refresh` fails on the mismatch" failure
   described below no longer applies — `refresh` is then needed only for
   genuine entry-point drift (an entry point added or removed) or a
   package-ready deliverable (step 5). For brownfield and hand-authored files,
   the failure mode and its fix still apply as written below.
   Use the complete minimal file in
   [references/structural-bpmn.md](references/structural-bpmn.md#a-complete-minimal-file-author-from-this-not-from-examples)
   as the shape to insert, plus each node's `xmlTemplate` (fill placeholders
   only). That skeleton shows a stable manual entry point, one structural task,
   and complete DI. **Do not reverse-engineer authoring patterns from task
   fixtures, generated package files, or the CLI's compiled bundle
   (`@uipath/cli/dist/*.js`)** — such spelunking is the top reason authoring
   runs out of time.
   Add only the structural pieces your process needs (extra
   gateways, events, boundary events, containers, multi-instance markers,
   expression/error mappings, retry attributes), then run
   `uip maestro bpmn format <file.bpmn>` to generate the diagram. Run it after
   each meaningful batch of edits, not only once at the end, when the user is
   watching the canvas — without a diagram, nodes do not render (Rule 5). If
   `format` reports `unknown command`, update the CLI (see
   [references/cli-conventions.md](references/cli-conventions.md)); if
   upgrading is unavailable, use the fallback DI structure in
   [references/structural-bpmn.md](references/structural-bpmn.md).
   The runnable BPMN/start-event path belongs in lowercase `operate.json.main`,
   never `project.uiproj.main`.
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
   Author an Integration Service connector node (`Intsvc.*`) by pasting the
   registry's template and keeping the shell it declares — `uipath:activity`
   for activities, `uipath:event` for `Intsvc.WaitForEvent` and
   `Intsvc.EventTrigger` (Rule 6) — plus its context and output, filling the
   resource identity slots with the escaped public placeholders. Event context
   references the connection as `connectionId`, activities as `connection`. A
   host element carrying neither shell, such as a bare `bpmn:sendTask` with no
   `uipath:activity`, is a missing node, not a draft.
   An unresolved node's resource — one that cannot be resolved right now
   (login, tenant, or connection availability) — is an element-level condition,
   independent of deliverable scope: follow the canonical rule in
   [references/registry-workflow.md](references/registry-workflow.md#2-get-the-template-for-each-chosen-type),
   which reports the node as **draft** and names the CLI-owned blocker
   literally, including the exact phrase `connection binding`. That rule holds
   regardless of whether the deliverable is source-only, so it does not by
   itself restrict which files may exist.
   For a source-only deliverable, emit **only** the `.bpmn` plus the notes file — do
   NOT create the four generated package files (Rule 16); authoring them fails
   the boundary the task tests. Name every CLI-owned blocker literally in the
   notes file, including the exact phrase `connection binding`, plus dynamic
   schemas, generated outputs, `bindings_v2.json`, and package metadata. Avoid
   softer wording such as "connection and process binding" because it hides the
   concrete artifact the CLI must supply.
   For brownfield edits, hand-authored bare `.bpmn` files, and any edit that
   changes a start event id or adds or removes an entry point, run
   `uip maestro bpmn refresh <project-path>` — **not only when packaging or
   operating**. `operate.json` and `entry-points.json` are generated once and
   do not follow source edits, so step 4's validator fails on the mismatch:
   `entry-points.json references start event "Event_start" via filePath, but no
   <bpmn:startEvent id="Event_start"> exists`. Writing a full-file replacement
   from the skeleton above renames the initializer's `Event_start` — exactly
   the drift this checks for; editing in place, as greenfield does above,
   avoids it. Keep the output as written — that shape is the contract `pack`
   consumes.
   `refresh` requires an init-generated project: with no
   `project.uiproj` it fails `Required file is missing` / `RetryWillNotFix`.
   For a bare `.bpmn` (the shape of this repo's edit fixtures, and the
   brownfield mode above), write the two-key `project.uiproj` first — `{
   "Name": "<ProjectName>", "ProjectType": "ProcessOrchestration" }` — then
   refresh, which writes the rest. Only fall back to the equivalent
   hand-authored shape in
   [references/shared/local-metadata-regeneration-guide.md](references/shared/local-metadata-regeneration-guide.md#source-only-fallback)
   when the CLI is unavailable. Do not copy CLI scaffold metadata shapes into a
   synthetic local project. Every root start event needs a
   `<uipath:entryPointId value="<uuid>" />` child in its `extensionElements`;
   without one `refresh` fails the whole project `RetryWillNotFix` instead of
   writing an empty entry-point list.
   Give public inputs and outputs explicit runtime bridges, and converge routes
   returning one result on a single completion EndEvent — for the two-layer
   contract see
   [references/structural-bpmn.md](references/structural-bpmn.md#variables-bpmnvariables).
4. **Validate.** Check well-formedness first. `validate` tokenizes with a
   tolerant parser and reports `Valid` on XML with an unbound namespace
   prefix, so a `ParseError` here is a source defect to fix before anything
   else. Then run the CLI validator, which runs the full PO.Frontend canvas
   rule set (structural rules plus variable, method-call, input-type, and
   event-object checks) offline, plus deploy-readiness checks:

   ```bash
   python3 -c "import sys, xml.etree.ElementTree as ET; ET.parse(sys.argv[1])" <file.bpmn>
   uip maestro bpmn validate <file.bpmn> --output json
   ```

   Exit 0 = valid; exit 1 = validation failed (the envelope lists each issue
   with its rule code). Warnings do not fail the run: validate once, fix only
   error-severity findings, and do not re-validate in a loop chasing warnings.
   Two warnings are defects rather than noise, because no error covers them.
   `read but never assigned` says nothing writes a value the process reads, so
   a step that should produce it does not. `MISSING_RESOURCE` says a node has
   no target selected; in a runnable deliverable, bind it. For a draft or
   boundary handoff the user asked for, an unresolved node warns
   `MISSING_RESOURCE` by design: keep its public placeholder, never invent an
   identifier (Rule 2), and report the warning rather than clearing it.

   Validation is structural preflight, not runtime proof — see
   [references/cli-conventions.md](references/cli-conventions.md). When
   execution is authorized, inspect runtime variables, element executions, and
   incidents before reporting behavioral success.

   If `validate` reports "unknown command" or clearly skips the
   structural rules, the installed CLI predates them — update it (see
   [references/cli-conventions.md](references/cli-conventions.md)). See
   [references/structural-bpmn.md#validation](references/structural-bpmn.md#validation).
5. **Refresh derived metadata when package-ready output is required.** After
   source validation passes, regenerate the four CLI-owned package files:

   ```bash
   uip maestro bpmn refresh <project-path> --output json
   ```

   Treat a nonzero result as a source/precondition failure: fix the BPMN or
   `project.uiproj`, revalidate, and refresh again — never repair the generated
   JSON by hand. Refresh is needed only for a package-ready, upload, debug,
   publish, or deploy deliverable, not for a source-only deliverable. For the full
   contract (scope, idempotency, binding rules) see
   [references/shared/local-metadata-regeneration-guide.md](references/shared/local-metadata-regeneration-guide.md).

## Operate and diagnose

Beyond authoring, this skill packages, ships, runs, and diagnoses Maestro
projects through the UiPath CLI.

- **Package and operate** (package a project, upload to Studio Web, publish or
  deploy, run or debug instances, and manage jobs, instances, incidents, and
  lifecycle actions): see [references/operate/CAPABILITY.md](references/operate/CAPABILITY.md).
- **Diagnose** (fetch incidents, variables, and element executions, and trace a
  failed run back to its BPMN element): see [references/diagnose/CAPABILITY.md](references/diagnose/CAPABILITY.md).
  Runtime evidence — incidents, variables, element executions, cursors, the
  deployed asset — comes only from a `uip maestro bpmn ... --output json` read;
  local `.bpmn` source and generated package files are read from disk as usual.
  Never substitute the files backing that CLI for the CLI itself — see rule 3
  in that reference.

Any cloud-side change (publish, deploy, run, pause, resume, cancel, retry,
migrate) requires explicit user consent, and local validation should pass
first. `solution upload` is the exception — see Rule 10.

## Structural coverage

This skill teaches authoring of the full surface the canvas supports. What the
registry serves a template for vs. what you author by hand:

| Structure | Source |
| --- | --- |
| Node `uipath:*` payloads (RPA, agent, HITL, queue, business rule, API workflow, IS connector, internal message, timer, script) | **Registry** `xmlTemplate` |
| `<uipath:variables>` declarations (each with an `elementId`) | Authored (registry gap) |
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

1. **Registry owns registry-listed node payloads.** Author their execution
   extensions from `registry get` templates; author serializer-owned scaffold
   metadata only from the structural/canvas contract. Never invent either from
   prose.
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
   `Orchestrator.StartAgentJob` is a direct child of `bpmn:ServiceTask` with
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
10. **Confirm before any cloud change.** Publish, deploy, run, pause, resume,
   cancel, retry, and migrate require explicit user consent; validate locally
   first. `solution upload` is the exception: a request to build the process
   authorizes the upload that shows it, so upload without asking. Confirm only
   when the project was adopted from a solution the agent did not create,
   because upload overwrites the cloud solution matching the local `.uipx`
   SolutionId — and confirm it where that solution is chosen, not at upload
   time.
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
16. **Generated package files are CLI-owned.** Never hand-author
   `bindings_v2.json`, `entry-points.json`, `operate.json`, or
   `package-descriptor.json`. Run `uip maestro bpmn refresh <project-path>` to
   generate them — never the deprecated `update-metadata`. A source-only
   draft asks for none of those — emit only the `.bpmn` plus a `.md` notes
   file naming the CLI-owned blockers.

## References

| Topic | Read |
| --- | --- |
| Phase 2 skeleton — blank boxes, real control flow, no registry calls | [references/phase-2-skeleton.md](references/phase-2-skeleton.md) |
| Discover → template → bind → assemble loop | [references/registry-workflow.md](references/registry-workflow.md) |
| Structural BPMN, event matrix, boundary events, containers, multi-instance, diagram, validation | [references/structural-bpmn.md](references/structural-bpmn.md) |
| Worked-out topology for a recurring process shape, and how shapes compose | Patterns table above → `references/patterns/*-guide.md` |
| Runtime expressions, `vars.`/`bindings.`/`iterator.`, `=js:` (Jint) syntax | [references/expression-authoring.md](references/expression-authoring.md) |
| CLI conventions and the side-effect boundary | [references/cli-conventions.md](references/cli-conventions.md) |
| Keeping content public-safe | [references/public-safety.md](references/public-safety.md) |
| Package, upload, publish, run, or manage instances | [references/operate/CAPABILITY.md](references/operate/CAPABILITY.md) |
| Diagnose a failed or misbehaving run | [references/diagnose/CAPABILITY.md](references/diagnose/CAPABILITY.md) |
| Project layout and generated package files | [references/shared/project-layout.md](references/shared/project-layout.md) |
