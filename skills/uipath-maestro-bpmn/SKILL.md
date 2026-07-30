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

Work the four steps quickly, but keep the path matched to the user's ask.

**An explicit approval gate overrides both "create evidence immediately" and
"author early."** Until the requested approval arrives, run only read-only
discovery CLI commands and leave their results on stdout. Apart from the CLI's
own registry/activity cache, do not create a project or evidence directory,
write a file, use shell redirection or `tee`, or invoke a helper that writes.
After approval, create the requested artifacts and rerun each exact successful
JSON discovery command except `registry pull` into its evidence file. Preserve
the first pull result from stdout rather than invoking it again: the session
gets one pull, and all later discovery uses that cache.

Choose one evidence location from the requested deliverable before writing:

- If the user names an exact evidence path, use that path.
- When the task names or creates a project directory, write evidence under
  `<project>/registry-evidence/`.
- Use workspace-root `registry-evidence/` only for an evidence-only task that
  has no project deliverable.

Do not create a second evidence directory at workspace root while authoring a
named project.

Treat requests to discover before authoring, save raw registry JSON/evidence,
or "do not author yet" as discovery-only even if they describe an eventual
BPMN. In that mode, immediately create the evidence directory selected above,
run and save `registry pull --output json`, `registry list --output json` or
`registry search ... --output json`, and `registry get <type> --output json` for
each requested type; do not read deep authoring references or scaffold a
project. For authoring asks, author early: do not pre-read every reference
before writing. Read a reference only when you reach the structure it covers,
get the needed templates, then write the first complete draft before further
spelunking. If
[references/structural-bpmn.md](references/structural-bpmn.md) or
[references/expression-authoring.md](references/expression-authoring.md)
directly covers the requested construct, write a first complete draft before
further spelunking. If the user explicitly says requirements are incomplete,
or a missing decision would materially change routing or outputs, ask focused
questions and confirm the design before authoring rather than guessing.
Do not enumerate tenant connections, folders, processes, or connector schemas
during requirements discovery. First learn whether the design will use live
tenant resources or portable intent-only placeholders. If it is intent-only,
skip tenant inventory entirely. If it needs live resources, discover only the
resource kinds the approved design actually uses.

For registry-evidence-only tasks, be command-first and time-boxed:

- Create the evidence directory selected above before anything else.
- Run the registry command forms the user asked for. For RPA job + internal
  message discovery, use `uip maestro bpmn registry list --limit -1 --output
  json`, `uip maestro bpmn registry get Orchestrator.StartJob --output json`,
  and `uip maestro bpmn registry get Maestro.ReceiveMessageEvent --output json`.
- If a discovery-only request is limited to login-free, non-live built-in
  templates and `uip` is unavailable in a temp/smoke sandbox (or returns a
  valid `"Result": "Failure"` envelope), do not search the repo for another CLI
  or inspect test fixtures. Still issue the required `list` and `get` command
  forms once each with output redirected to their evidence files (allowing
  failure with `|| true`), so the transcript shows the discovery loop:
  `uip maestro bpmn registry list --limit -1 --output json` and
  `uip maestro bpmn registry get <type> --output json`. Record the failed CLI
  attempts in `<evidence-directory>/cli-error.txt`, then overwrite any failure
  JSON in the expected `<evidence-directory>/*.json` files with valid JSON
  evidence from `skills/uipath-maestro-bpmn/validator/bpmn-spec.json`
  containing the same extension types and stop. The final evidence files must
  literally contain the discovered type names, for example
  `Orchestrator.StartJob` and `Maestro.ReceiveMessageEvent`. Never use this
  fallback for `Intsvc.*`, connector or connection discovery, activity/object
  selection, enrichment, or any node claimed to be live/runnable; stop those
  tasks as blocked.

1. **Discover.** `uip maestro bpmn registry pull` **once** (cached for the
   session — do not re-pull), then `list` / `search` to map intent to extension
   types. Only after the user confirms the design needs a live Integration
   Service resource, use `uip is connections list --all-folders` for that
   resource (always `--all-folders` — a folder-scoped list silently misses
   connections). Do not list connections for portable or intent-only designs.
   Confirm every live selection with the user (use AskUserQuestion). Never
   fabricate an identifier.
   See [references/registry-workflow.md](references/registry-workflow.md).
2. **Get templates.** `uip maestro bpmn registry get <type> --output json` for
   each chosen registry-owned node only. Enrich `Intsvc.*` connector nodes with
   `--connection-id` and the exact `ObjectName` selected from `uip is activities
   list <connector-key> --output json`; accept it only when the enriched
   response identifies that same object and connector. Do not call `registry
   get` for structural gaps the registry never owns: sequence flows, gateways,
   events, boundary events, multi-instance/loop markers, `errorMapping`/retry
   structure, or diagrams. If a registry template's BPMN host tag is PascalCase
   (for example `<bpmn:SendTask>` or `<bpmn:ReceiveTask>`), normalize the host
   tag to the serializer's lower-camel BPMN element (`<bpmn:sendTask>`,
   `<bpmn:receiveTask>`) while preserving the `uipath:*` payload exactly.
   For the accepted connector operation, identify its selected method key under
   `Data.IsEnrichment.Metadata.Method`. Serialize only enrichment `Fields`
   whose `Method.<same-key>.Request` is true. `RequestCurated` is presentation
   metadata and never makes a non-request field legal by itself. Use each
   field's exact `Name`, not the `Fields` dictionary key or display name;
   include every request field whose same method entry marks `Required`, omit
   optional request fields the business contract does not need, exclude
   response-only fields, and reconstruct dotted names as nested JSON.

   **Small local fast path (overrides the generic Discover and Assemble
   guidance).** Use this path only for a new intent-only graph with at most
   twelve visible nodes and no connector, subprocess, loop, or boundary event.
   Pull the registry once. If the request names the exact registry-owned types,
   do not run `registry list` or `registry search`; otherwise stop listing or
   searching as soon as those types are resolved. Run `registry get` exactly
   once per **distinct** registry-owned type and reuse its template for every
   node of that type.

   Read only the
   [complete minimal file](references/structural-bpmn.md#a-complete-minimal-file-author-from-this-not-from-examples)
   and the directly relevant subsection for each requested node. Then write
   exactly `<Project>/<Project>.bpmn` and `<Project>/project.uiproj`; the latter
   is exactly:

   ```json
   {"projectVersion":"1.0.0","ProjectType":"ProcessOrchestration","Name":"<Project>","main":"<Project>.bpmn"}
   ```

   Author the XML directly from that minimal structure plus the retrieved
   templates and validate exactly once. Do not run `uip maestro bpmn init`, the
   declarative renderer, `pack`, or any solution scaffold/package command. Do
   not create a solution, `.uipx`, metadata, renderer spec, evidence directory,
   fixture, implementation source, or test. Manual start/end events, exclusive
   or parallel gateways, sequence flows, conditions, defaults, and DI are
   structural: do not search the registry or validator spec for them. A graph
   using only those elements plus `BPMN.Variables` tasks needs only one
   `registry get BPMN.Variables`. Copy the minimal file's namespace declarations
   verbatim; every `di:waypoint` requires the `xmlns:di` declaration. The first
   post-template action must write the requested project.

   **Intent-only `Actions.HITL`.** Use its retrieved registry template; `.flow`
   QuickForm JSON does not apply. Without a confirmed live app, use visibly
   synthetic literals for `appId`, `key`, and `taskTitle`; keep `appVersion`
   numeric; serialize the requested outcome labels in the template's string
   `actions` field (for example `Approve,Reject`); and put the fields the
   reviewer must see in the `HitlTaskArguments` JSON body. Declare the
   template's output variable with type `Actions.HITL`. If the process only
   records completion, wire the user task directly to a registry-derived
   `BPMN.Variables` task and then to the end event—do not introduce a gateway or
   ScriptTask. Report the result as a portable, non-runnable draft until a real
   app identity replaces the synthetic values.
3. **Assemble.** Author directly from the complete minimal file in
   [references/structural-bpmn.md](references/structural-bpmn.md#a-complete-minimal-file-author-from-this-not-from-examples)
   plus each node's `xmlTemplate` (fill placeholders only). That skeleton already
   shows variables, the entry point, a branch, and the diagram. **Do not
   reverse-engineer authoring patterns from task fixtures or generated package
   files, and do not read `scripts/build-bpmn.py` or its test source to learn the
   renderer contract.** The declarative-builder guide plus `--example` is the
   public contract; treat the renderer as a tool, not as source to
   reverse-engineer. Fixture and implementation spelunking is the top reason
   authoring runs out of time.
   Add only the structural pieces your process needs (extra
   gateways, events, boundary events, containers, multi-instance markers,
   expression/error mappings, retry attributes), then generate one
   `BPMNShape`/`BPMNEdge` per node and flow. For local authoring prompts, use the
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
   If a local-only prompt asks for `operate.json`, `entry-points.json`,
   `bindings_v2.json`, or `package-descriptor.json`, follow the minimal local
   metadata shape in
   [references/shared/local-metadata-regeneration-guide.md](references/shared/local-metadata-regeneration-guide.md#minimal-local-metadata-shape).
   Do not copy CLI scaffold metadata shapes into a synthetic local project.

   Preserve every declared contract type exactly: `integer` and `number` are
   distinct, as are `array`, `object`, and `json`. For a large new graph whose
   executable work uses only the renderer's documented Variables, ScriptTask,
   and Integration Service activity mapping forms, use the generic structural
   renderer described in
   [references/declarative-builder.md](references/declarative-builder.md).
   Use its Integration Service path only after authenticated discovery and only
   for the documented `sendTask` / `uipath:activity` / process-binding contract.
   Do not use this path for HITL, RPA, agents, receive tasks, or another registry
   payload the renderer contract does not explicitly cover; assemble those
   payloads from their registry XML templates.
   Author its JSON spec instead of precomposing repetitive XML. The spec must
   still state every variable, node, visible condition, Variables assignment,
   scope, loop, error, and flow; the renderer derives references, DI, and local
   metadata. It does not generate business policy.

   After discovery, create the project and requested evidence files, then run
   `python3 scripts/build-bpmn.py --example` (resolve `scripts/` relative to
   this SKILL.md). Set the spec's mandatory constraints first: exact public
   inputs/outputs, exact ScriptTask count/ids, and guarded error-end policy.
   Build in bounded contract, root-topology, embedded-scope, and workstream
   checkpoints. For a small graph, direct XML editing remains acceptable. For
   an existing/imported BPMN, do not use the renderer; preserve unknown content
   and make surgical edits.

   When a ScriptTask normalizes entry-point inputs for later gateways, map its
   results to dedicated, unbound mutable working variables. Do not transform
   start-bound inputs in place. Keep route, severity, failure, and downstream
   actions out of a normalization script; assign them visibly with
   registry-derived `BPMN.Variables` tasks.

   For a new v3 ScriptTask, follow the current Studio serializer contract even
   if an installed CLI registry still returns the older empty-args
   `BPMN.ScriptTask` template: use a `BPMN.Variables` mapping, pass `vars` and
   `metadata` through the `args` JSON (`iterator` as well for a
   multi-instance script), map the standard response and Error variables, and
   read stable ids as `vars.<id>` inside the script. Declare each Error target
   with `name="Error"`, `type="jsonSchema"`, and
   `elementId="<that-script-id>"`; when several scripts exist, give those
   same-named scoped variables distinct ids and map each Error output by its
   explicit id. Serialize `args` as CDATA or the engine-equivalent `value`
   attribute; ordinary XML text is ignored at runtime. Return the intended
   value directly and map it from `=result.response`.
   For every typed object argument or response, declare each property that
   downstream code dereferences and list every guaranteed property in the
   schema's `required` array; a property name without `required` is nullable
   to Studio and runtime validation.

   Give public inputs and outputs explicit runtime bridges. Bind a public input
   declaration to the root StartEvent, map it there to a mutable internal
   variable, then route on the internal id. Map each mutable result to a public
   output declaration on the single root completion EndEvent. Values produced
   in an embedded subprocess also need an explicit output mapping on the
   subprocess before parent/root work can depend on them.

   Before validation, audit the source against the approved design:

   - Count ScriptTasks and diverging gateways and confirm their responsibilities
     and named policy predicates match the design.
   - Keep business decisions in visible gateways and their assignments in the
     applicable Variables tasks.
   - Trace every output across every terminal route. Assign required empty,
     false, or other concrete values explicitly; unset/null is not equivalent.
   - Give an error end one visibly guarded incoming flow containing the complete
     qualification. Use errors only for technical exceptions the user classified
     as errors, and require a matching typed boundary on its subprocess.
   - Treat an error end as abnormal subprocess termination: the subprocess's
     normal output mapping is not applied, and the parent boundary cannot read
     terminated child-local variables. If later work needs business values
     computed in that subprocess, explicitly re-establish them on the parent
     boundary path from parent-visible state, using gateways and Variables
     tasks so the recovery policy remains visible.
   - Trace every ordinary completion and boundary path to the required
     downstream work and end state, and confirm every node and flow has DI.
   - Give every root and embedded-subprocess StartEvent exactly one outgoing
     flow. Keep sequence flows inside their owning scope and make every node
     reachable from a start, boundary, or event-subprocess entry. Alpha can
     otherwise complete a disconnected subprocess without an incident while
     returning unset outputs.
   - For a parallel region whose workstreams contain internal exclusive
     alternatives, merge those alternatives inside each workstream first.
     Feed exactly one path per workstream into the parallel join. Connecting
     mutually exclusive alternatives directly to an AND join makes it wait for
     tokens that can never all arrive.
   - When the approved design assigns an output to a downstream workstream, do
     not precompute it upstream and insert a self-assignment such as
     `action <- vars.action` merely to make the branch appear to own it. The
     workstream must materially derive or assign every outcome it owns through
     its visible gateways and Variables tasks.
4. **Validate.** Run the CLI validator — it runs the PO.Frontend canvas
   rule set (structural rules plus variable, method-call, input-type, and
   event-object checks) offline, plus deploy-readiness checks:

   ```bash
   uip maestro bpmn validate <file.bpmn> --output json
   ```

   Exit 0 = valid; exit 1 = validation failed (the envelope lists each issue
   with its rule code). Warnings are reported but do not fail the run. Validate
   once; fix only error-severity findings. Do not re-validate in a loop chasing
   warnings.

   Validation is a structural preflight, not runtime proof. It does not prove
   that entry inputs reach mutable variables, subprocess results reach the root,
   mapping bodies are consumed by the engine, ScriptTask globals exist, a
   multi-instance output is reduced correctly, or public outputs contain the
   intended business values. When the user authorizes execution, use a
   controlled debug/run and inspect `variables-all`, element executions, and
   incidents before reporting behavioral success.

   If `validate` reports "unknown command" or clearly skips the
   structural rules, the installed CLI predates them — update it (see
   [references/cli-conventions.md](references/cli-conventions.md)). See
   [references/structural-bpmn.md#validation](references/structural-bpmn.md#validation).

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
2. **Never fabricate a live identifier.** Connection IDs,
   process/queue/connector keys, app IDs, and folder ids/paths selected for live
   use come from discovery or the user. Use visibly synthetic intent-only
   placeholders only where this skill explicitly allows them, and report the
   resulting draft as non-runnable.
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
6. **Node type is a child element, never an attribute.** Every `uipath:activity`
   / `uipath:event` / `uipath:mapping` declares its type as
   `<uipath:type value="<Type>" version="v1" />` inside the wrapper. Never write
   `<uipath:activity type="…">` — the canvas will not recognize the node.
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

## References

| Topic | Read |
| --- | --- |
| Discover → template → bind → assemble loop | [references/registry-workflow.md](references/registry-workflow.md) |
| Structural BPMN, event matrix, boundary events, containers, multi-instance, diagram, validation | [references/structural-bpmn.md](references/structural-bpmn.md) |
| Runtime expressions, `vars.`/`bindings.`/`iterator.`, `=js:` (Jint) syntax | [references/expression-authoring.md](references/expression-authoring.md) |
| Declarative renderer for large new BPMN graphs | [references/declarative-builder.md](references/declarative-builder.md) |
| CLI conventions and the side-effect boundary | [references/cli-conventions.md](references/cli-conventions.md) |
| Keeping content public-safe | [references/public-safety.md](references/public-safety.md) |
| Package, upload, publish, run, or manage instances | [references/operate/CAPABILITY.md](references/operate/CAPABILITY.md) |
| Diagnose a failed or misbehaving run | [references/diagnose/CAPABILITY.md](references/diagnose/CAPABILITY.md) |
| Project layout and generated package files | [references/shared/project-layout.md](references/shared/project-layout.md) |
