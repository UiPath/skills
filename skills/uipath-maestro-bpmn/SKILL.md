---
name: uipath-maestro-bpmn
description: "UiPath Maestro BPMN / Process Orchestration (`.bpmn`, `.bpmn.ts`): author, validate, package, operate, diagnose, evaluate, or sketch a process before it is built. Author `.bpmn.ts` with `@uipath/maestro-builder-sdk/bpmn` and the `uip maestro bpmn` check/compile/format/validate loop; edit an existing `.bpmn` via decompile. Operate: refresh package metadata, pack, upload to Studio Web, publish, debug, run, inspect jobs/instances, pause/resume/cancel/retry/migrate. Diagnose failed or stuck runs: incidents, runtime variables, deployed asset, element executions, traces. Evaluate: eval sets, evaluators, simulations, eval runs. Covers events, gateways, tasks, sub-processes, sequence flows, diagram, bindings, boundary handlers, event sub-processes, human tasks, Integration Service connectors, Data Fabric records/files, registry extension types. .flow→uipath-maestro-flow; case plans→uipath-maestro-case."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

<!-- CANONICAL — edit here, not in UiPath/flow-builder-sdk. Why: docs/SKILLS_PROMOTION_PLAN.md in that repo. -->

# UiPath Maestro BPMN — TypeScript Builder SDK

Author typed BPMN graphs in TypeScript and compile them to `.bpmn` XML. Read only needed references; let TypeScript and `bpmn check` provide the contract.

## Critical Rules

1. Edit `<Name>.bpmn.ts`, never compiled `.bpmn`; compilation overwrites hand edits.
2. Seed an existing process or `bpmn init` stub with `bpmn decompile`; never hand-write its skeleton (Workflow step 4).
3. Leave decompile-written `.preserve({ … })` calls unchanged; they carry state nothing else derives (Workflow step 4).
4. Run `uip maestro bpmn check <Name>.bpmn.ts --source` before every compile and fix every printed error first (Workflow step 5). `check` lints SDK source and never replaces `validate`. Author every expression as `=js:` ([exceptions](references/bpmn-runtime.md#variables-and-the-process-contract)).
5. For a new process run `format`, then `refresh`, then `validate` after every compile (Workflow steps 6–7). After merging an existing process run only `refresh` and `validate`. Run `format` without `--relayout` only when `refresh` or `validate` reports `BPMN_PARSE_ERROR` with `No diagrams found`, `MISSING_DI_SHAPE`, or `MISSING_DI_EDGE`, then repeat `refresh` and `validate`. If `format --help` has no `--relayout`, plain `format` lays out the whole diagram again and drops pools, lanes, colors, and placement; unless the report was `No diagrams found`, tell the user the canvas layout was reset ([Brownfield](references/bpmn-runtime.md#brownfield-editing)).
6. A different target system (Document Understanding → agent, Outlook → Gmail) changes a node's type and binding, not the graph; reshape only when the process differs.
7. Author the process, never participate in it. Where a step reasons, classifies or extracts at run time, place and bind the node that does it (a UiPath agent, Document Understanding, a business rule); never do that work while authoring or hardcode its result. A bare "agent" means a UiPath agent, never you.
8. Build a design you are given (an approved SDD, a BPMN diagram, an image) 1:1: every item is a node, every connector a flow, each rule belongs on its named element, and every stated default remains unchanged (including unknown until assessed, never `false` or available). Never merge, drop, or collapse nodes, for example into one script task, without asking. A node the design draws once, reached from more than one route, is built once: after the `choose` by fall-through, or behind a named join when fall-through can't reach it ([Shared joins](references/patterns/composing-guide.md#shared-joins-the-mechanism-nesting-hides)), never copied into each arm. A design gap is a user question, not an invented step. Add only compile/validation necessities (start/end events or a join). Convert drawn retry loops to activity `retry` (rule 9). In a draft, ask at the gate and name each addition in its reply; in a build, name each on the final report's `Assumed:` line. When the request says nobody will answer, use the most literal reading and name each choice likewise. Confirm an image inventory first; read [Authoring from an image](references/image-transcription-guide.md).
9. Retry failing activities with `retry` ([Retry](references/bpmn-runtime.md#events-and-timers)), never a drawn loop of gateways, timers or `.goto()`.
10. Choose an Orchestrator node by target `ProcessType`, never its label ([Orchestrator work](references/bpmn-runtime.md#http-and-orchestrator-work)).
11. A process returns only what its end event maps: compute into `.var()` and map it onto each `.output()` in the `BPMN.Variables` payload of every end event that finishes the process (root scope, never a sub-process body). A task writing `.output()` directly returns `null` to the caller although checks pass. A step reads `.input()` only through the start event: read the `.var()` mapped by that start event's `BPMN.Variables`; if absent, add the row and a start-event-scoped `.var()`. Later `vars.<inputId>` reads produce "A variable is unresolved" on the canvas and at most a `VARIABLE_NOT_SET` validation warning ([Process contract](references/bpmn-runtime.md#variables-and-the-process-contract)).
12. Fix every process-caused `validate` warning in the same edit as errors; never add a step or change an input, default, or path merely to silence one. Fix each warning once: if the next `validate` still prints it, keep it and never edit or rerun for it. Ignore and do not report `[(xml)] unknown attribute` on compiled output. Report every other kept warning as required by the [final report](references/final-report-template.md#the-reply); call none non-blocking or optional. A draft skeleton follows [its own rule](references/draft-skeleton.md#expected-findings--do-not-chase-them) until *Build it*.
<!--skill-flavor:critical-rules-extra:start-->
<!--skill-flavor:critical-rules-extra:end-->

<!--skill-flavor:host-setup:start-->

<!--skill-flavor:host-setup:end-->
## Workflow

Discovery-only requests (discover types or save registry evidence, no authoring) skip this workflow and follow [Discovery only](references/bpmn-runtime.md#registry-extension-types). Draft, outline, and sketch requests stop at the [draft gate](#draft-first), which says which requests gate and which build.

<!--skill-flavor:workflow-scaffold:start-->
1. **Before the first `init`, ask which solution to use when one already exists.**
   Search up to two levels below the working directory and every directory above it:

   ```bash
   find . -maxdepth 2 -type f -name '*.uipx' -print
   d="$PWD"; while [ "$d" != / ]; do d=$(dirname "$d"); find "$d" -maxdepth 1 -type f -name '*.uipx' -print; done
   ```

   Ask this for a draft and for a plain build alike; an edit of an existing `.bpmn` runs no `init` and skips the scan.
   - When the scan finds nothing, or only a solution this run created, run `init` without asking.
   - When the request names the solution to use (an existing one, or a new one by name), use it without asking.
   - When the request names no solution and says nobody will answer questions, do not ask: put the project in a new solution, never an existing one, and say so in the draft gate sentence or build final report `Assumed:` line.
   - Otherwise stop and ask the user which to use, as a pick list if the host has one: one option per found solution (folder name) plus "Create a new solution".
     Do not run `init` until the user answers, and never silently adopt an existing solution: `init` registers the project in a solution above it without asking.
     Unless upload is forbidden, say in the question that adopting a solution means a later upload overwrites its cloud copy.
     For an unnamed new solution ask only for its name, offering `<Name>Solution` as the default, or a free name by the numbering rule below when that one is taken.

   For an existing solution, from its directory run `init`; project is `<SolutionDir>/<Name>/`. If selected after warning about cloud overwrite, upload without asking again; if named in the request, confirm before the first upload as [Operate](references/operate.md#studio-web-upload) requires, while a draft holds upload as [Draft skeleton](references/draft-skeleton.md#steps) says. Check its cloud copy before overwriting.

   For a new solution use the name the user gave, else `<Name>Solution`; its creation directory must not contain that name. Run the guard in the same command, never `uip solution init` alone: `test ! -e <SolutionName> && uip solution init <SolutionName> --output json`, because `uip solution init` on an existing solution succeeds but replaces its `SolutionId` and empties its `Projects`, unregistering every project in it. If occupied, ask for another name; when nobody will answer, try `<SolutionName>2`, `<SolutionName>3`, etc., and state the choice in the draft gate sentence or build `Assumed:` line. If `uip solution init` fails, stop and report its error; do not retry under another name. Then `cd <SolutionName>` and run `init` there; this works even inside another solution, which stays untouched. This run created it, so upload without confirmation.

   If the user names the `.bpmn` path, use the table command from the workspace root. Ask only if a directory above it contains `.uipx`; offer that solution or "No solution", since a new solution cannot hold a project outside its folder. On "No solution", or when nobody will answer, add `--skip-solution-registration`.

   `init` is `uip maestro bpmn init <Name> --output json`; take the project directory from `Data.Path` and verify it is the requested project directory before writing anything. `<Project>` is that directory. It contains `<Name>.bpmn`, `project.uiproj`, `operate.json`, `entry-points.json`, `bindings_v2.json`, and `package-descriptor.json`, required by `bpmn pack` and product tooling. Without `--path`, it writes `./<Name>/` inside a solution (a `.uipx` here or in a parent), registered in it; `./<Name>Solution/<Name>/` outside one; or `./<Name>/` with `--skip-solution-registration`.

   When the path is named, its containing directory is the project directory and `init --path <dir>` writes directly there. Match the path to one row and run that row's command from the workspace root, with the user's names in place of `X`, `A`, `B` and `C`:

   | Path named | Project directory | Command |
   |---|---|---|
   | `X.bpmn` (workspace root) | `.` | `uip maestro bpmn init X --path . --output json` |
   | `A/A.bpmn` | `A` | `uip maestro bpmn init A --path A --output json` |
   | `A/B/B.bpmn` (also `A/A/A.bpmn`, or deeper) | `A/B` | `uip maestro bpmn init B --path A/B --output json` |
   | `A/B/C.bpmn` (file name differs from directory) | `A/B` | `uip maestro bpmn init C --path A/B --output json` |
   | nothing named | `Data.Path` | `uip maestro bpmn init <Name> --output json` |

   If `init` returns `error: unknown option '--path'`, run the row command without `--path` in a new empty directory, move its project files into the project directory, and, when a solution holds it, run `uip solution projects add <PROJECT_DIR> --output json`. Never copy beside an existing user `<Name>.bpmn`; it remains the source to edit. `--path` accepts the given directory, creates missing parents, writes `<Name>.bpmn` named after the project, and scaffolds no `<Name>Solution`. Registration occurs only when a parent contains `.uipx`, unless `--skip-solution-registration` prevents it. The directory may contain unrelated files but not a project file (`project.uiproj`, `project.json`, `operate.json`, `entry-points.json`, `bindings_v2.json`, `package-descriptor.json`, or `<Name>.bpmn`, case-insensitive). Refusal means a project exists: edit it if it is the requested process (step 8), and ask before `--force`, which overwrites those files. `init` refuses a `.uipx` directory even with `--force`. Compile only to `<Project>/<Name>.bpmn`, never elsewhere. A project without a solution can validate, refresh, and pack; see [Operate](references/operate.md#studio-web-upload) for later upload/deploy.
2. Install once per machine: `npm install -g @uipath/maestro-builder-sdk` (6.88.1 or later); verify with `npm ls -g @uipath/maestro-builder-sdk`. Connector-definition fetching through `uip` requires 6.97.0 or later, via `uip` or SDK `flow-sdk`. Write `<Name>.bpmn.ts` in the starting workspace root, never solution/project folders, even when `init` ran from the solution folder. Do not add `package.json`; with one, `check` may fail with `Cannot use import statement outside a module`. If `uip` says the SDK cannot fetch definitions, run its named upgrade (`npm install -g @uipath/maestro-builder-sdk@latest`, or `--save-dev` for a workspace copy); cloud also supports `uip maestro registry pull`.
<!--skill-flavor:workflow-scaffold:end-->
3. Import from `@uipath/maestro-builder-sdk/bpmn` and default-export a chain ending in `.build()`.
<!--skill-flavor:workflow-seed:start-->
4. Seed with `uip maestro bpmn decompile <Project>/<Name>.bpmn -o <Name>.bpmn.ts --style nested`, not a handwritten skeleton.
<!--skill-flavor:workflow-seed:end-->
   `--style nested` lifts boundary events, gateways, and event sub-processes into nesting constructs, writes the top level in `flowMode('sequence')`, leaves unprovable structures flat with a printed reason, and verifies the compiled graph is identical first. It pins imported `edge_…` ids with `.flowIds([…])` at the top of the chain, because `bpmn merge` keys elements and flows by id: a renamed flow becomes a new one, its old diagram edge is deleted, and a gateway `default` naming the old id makes `validate` reject the file. `--keep-flow-ids` instead writes no pin table and lifts only regions whose ids already match, so it lifts less. Without `--style nested`, output is flat. Decompile carries the process id and product-assigned `entryPointId` UUID. Existing projects need no `init`; seed from their `.bpmn`. For shape, copy the closest staged `examples/*.bpmn.ts`. It reports and drops unused bindings unless `--keep-unused-bindings` is used, and writes `.preserve({ … })` (Critical Rule 3; [Process contract](references/bpmn-runtime.md#variables-and-the-process-contract)).
<!--skill-flavor:workflow-compile:start-->
5. Run `uip maestro bpmn check <Name>.bpmn.ts --source` before every compile; fix every error (non-zero exit) first. `compile` writes the `.bpmn` the source describes; `check` catches probable errors such as `EXPR_UNDECLARED_REF` for undeclared `vars.<id>` and `EXPR_BARE_VAR_REF` for declared reads without `vars.` (fix with `=js:vars.<id>`). `check` is the only offline gate for reads in `errorMapping` conditions and bare `=amount`; `validate` accepts both. It needs SDK 6.86.0 or later; older `compile` rejects the read. If installed packages contain `dist/bpmn-api.md` (see [API index](#api-index)), `check` also type-checks source; a `TS<code>` at `file:line:col` is a wrong option name or value type; fix it like any other error. Node runtime globals, top-level `await`, and ES2024 APIs are accepted.
6. Compile **into the scaffolded project**, then `format`, `refresh`, and product `validate`, in that order for every new process. Existing processes use step 8 `merge`; format only for the specified missing-diagram/shape reports. `validate` rejects no diagram (`BPMN_PARSE_ERROR` with `No diagrams found`), while `compile` adds none and `format` does. Exactly one emitted `<Name>.bpmn` may exist: `<Project>/<Name>.bpmn`; do not leave a second copy at the workspace root, and do not leave the init template instead of compiled output.
<!--skill-flavor:workflow-compile:end-->
7. **`refresh` is part of the loop, not part of packaging.** `init` creates `entry-points.json` and `operate.json` once for template start id `Event_start`; a start event with any other id (your own chain always has one) fails `validate` with `entry-points.json references start event "Event_start" via filePath, but no <bpmn:startEvent id="Event_start"> exists`. Run `uip maestro bpmn refresh <project-path>` after any start-id or entry-point change; it regenerates both from BPMN and validates before writing. It fails on no diagram (`BPMN_PARSE_ERROR` with `No diagrams found`) or missing shape (`MISSING_DI_SHAPE` / `MISSING_DI_EDGE`); format a new compile first (a merged file: Critical Rule 5). It requires an init-generated project with `project.uiproj`.
<!--skill-flavor:workflow-merge:start-->
8. Edit existing processes with `merge`, using edited source and original ([Brownfield](references/bpmn-runtime.md#brownfield-editing)). Keep no other `.bpmn` in the workspace: no intermediate, probe, or second scaffold. If the project is in a solution not created this run, check its Studio Web copy before editing ([Operate](references/operate.md#check-the-cloud-copy-before-editing)).
<!--skill-flavor:workflow-merge:end-->
9. **End every build with the final report.** Plain build/edit requests (`(auto mode)`) and *Build it* after [draft gate](#draft-first) (`(draft mode)`) end with **[`references/final-report-template.md`](references/final-report-template.md)**, even when validation fails only for missing tenant resources: read it in full once `validate` passes or fails only that way, before upload or another closing tool call. Resume only: with no new instruction after a report or gate reply, resend that message unchanged and whole and do nothing else; a new message (*Build it*, *Change it: …*, or a question) is normal.

## Draft first

For draft/shape requests—*create a draft*, *outline it*, *show me the shape*, *sketch it*, *what would it look like*, *before you build it*, or plan mode—read **[`references/draft-skeleton.md`](references/draft-skeleton.md)**, build a bare-task skeleton, and stop at approval. These cues gate even complete specifications. Wording leaning draft (*rough version*, *first pass*, *quick mock-up*) also drafts unless it explicitly asks to build or deploy the whole process; that exception never overrides draft/outline/sketch. A request with none of these cues is a build, and so are a brownfield edit and a "draft project" asking for source files to import later, with no upload or run.
<!--skill-flavor:draft-upload-summary:start-->
Outside plan mode, chat mermaid/outline is not the deliverable; deliver the validated `<Name>.bpmn` in the initialized project. The skeleton retains `Event_start`, so it skips `refresh` (step 7) and makes no `registry` calls. Unless upload is forbidden or the project has no solution, upload the validated skeleton to Studio Web and put its link in the gate reply; *Build it* ends with the final report and uploads again when [its rules](references/final-report-template.md#upload-the-built-process) allow.
<!--skill-flavor:draft-upload-summary:end-->

## API index

<!--skill-flavor:api-index-location:start-->
Indexed in the INSTALLED PACKAGE, not here; `.d.ts` spans vary by build.

If `node_modules/@uipath/maestro-builder-sdk/dist/bpmn-api.md` exists, search the needed field, method, or shape (`outputVar`, `humanTask`, `HttpOpts`) and read only its row. Do not read `dist/**/*.d.ts` with that package; `check --source` reports wrong option names/types with line numbers. Use `dist/api-index.md` by exported symbol (`BpmnBuilder`) only when long-form `@remarks` or `@example` is needed.

Without `bpmn-api.md`, use `dist/api-members.md` by field/method and `dist/api-index.md` by exported symbol; match one name and read its complete declaration and doc comment, not either file end to end.
<!--skill-flavor:api-index-location:end-->

## Capability router

| Surface | Builder/API | Reference | Example |
|---|---|---|---|
| Draft or pre-build shape | bare `task`, `choose` | [Draft first](references/draft-skeleton.md) | — |
| Discovery only | `registry` pull, list, search, get | [Discovery only](references/bpmn-runtime.md#registry-extension-types) | — |
| Build or draft from a given design: approved SDD, BPMN diagram, sketch, whiteboard photo, diagram screenshot | built 1:1 | [Critical Rule 8](#critical-rules); image: [Authoring from an image](references/image-transcription-guide.md) | — |
| Process/nested scopes | `bpmn`, `subProcess` | [Builders](#api-index) | `examples/NotifyChannel.bpmn.ts` |
| Variables/inputs/outputs | `vars`, `var`, `input`, `output`, `schemas`, `schema` | [Process contract](references/bpmn-runtime.md#variables-and-the-process-contract) | `examples/NotifyChannel.bpmn.ts` |
| Node output | `outputs` (job builders) or `outputRows` (`.activity()`, `.scriptTask()`), not adjacent `.var()` | [Process contract](references/bpmn-runtime.md#variables-and-the-process-contract) | `examples/InvoiceApproval.bpmn.ts` |
| Imported state | `preserve` | [Process contract](references/bpmn-runtime.md#variables-and-the-process-contract) | `examples/InvoiceApproval.bpmn.ts` |
| Events | event methods | [Events](references/bpmn-runtime.md#events-and-timers) | `examples/NotifyChannel.bpmn.ts` |
| Activity error/timer/message | activity body `onError`, `onTimer`, `onMessage` | [ActivityBuilder](#api-index) | `examples/InvoiceEscalation.bpmn.ts` |
| Gateways | gateway methods | [GatewayOpts](#api-index) | `examples/NotifyChannel.bpmn.ts` |
| In-place decision/split/wait | `choose`, `fork`, `race`, `goto` | [ChooseArm](#api-index) | `examples/InvoiceEscalation.bpmn.ts` |
| Whole-scope safety net | `eventSubProcess` | [Event sub-process scope](references/bpmn-runtime.md#events-and-timers) | `examples/InvoiceEscalation.bpmn.ts` |
| Script/assignment (`scriptTask` computes: totals, counts, decisions; `task` only assigns) | `scriptTask`, `task` | [Script tasks](references/bpmn-runtime.md#script-tasks) | `examples/ContractRegistry.bpmn.ts` |
| HTTP | `http` | [HTTP](references/bpmn-runtime.md#http-and-orchestrator-work) | `examples/InvoiceEscalation.bpmn.ts` |
| Orchestrator jobs/queues | start/execute/queue methods | [Work dispatch](references/bpmn-runtime.md#http-and-orchestrator-work) | `examples/InvoiceApproval.bpmn.ts` |
| Business rule | `businessRule` | [Work dispatch](references/bpmn-runtime.md#http-and-orchestrator-work) | — |
| Human work; always inline form | `humanTask` | [Human tasks](references/bpmn-runtime.md#human-task-outcomes) | `examples/InvoiceEscalation.bpmn.ts` |
| Connectors/external work | `connector`, `externalAgent`, `externalWorkflow` | [Connectors](references/connectors.md) | `examples/NotifyChannel.bpmn.ts` |
| Connector event start/wait | `eventTrigger`, `waitForEvent` | [Connector events](references/connectors.md#6-connector-events) | — |
| A connector step in a draft with no connection (offline, or no real ids allowed) | symbolic `connector` bindings or bare `task` | [Unresolved connector draft](references/connectors.md#7-draft-with-an-unresolved-connector) | — |
| Data Fabric | `dataService` | [Connections](references/bpmn-runtime.md#connectors-and-bindings) | `examples/ContractRegistry.bpmn.ts` |
| Any registry type, typed method or not | `activity` | [Registry extension types](references/bpmn-runtime.md#registry-extension-types) | `examples/InvoiceApproval.bpmn.ts` |
| Existing BPMN | `bpmn decompile`, `check`, `merge` | [Brownfield](references/bpmn-runtime.md#brownfield-editing) | `examples/NotifyChannel.bpmn.ts` |
| Metadata/package/layout | `metadata`, project metadata, `bpmn format` | [Contract metadata](references/bpmn-runtime.md#contract-metadata) | `examples/NotifyChannel.bpmn.ts` |
| Package/upload/publish/debug/run/manage | `uip maestro bpmn refresh` / `pack` / `debug` / `process run` / `instance …` | [Operate](references/operate.md) | — |
<!--skill-flavor:evaluate-row:start-->
| Evaluate a process: evaluators, eval sets, data points, simulations, eval runs | `uip maestro bpmn eval` | [Evaluate](references/evaluate.md) | — |
<!--skill-flavor:evaluate-row:end-->
| Diagnose | `uip maestro bpmn job status` / `instance incidents` / `instance variables` / `instance asset` | [Diagnose](references/diagnose.md) | — |
| Sanitize a file to share or commit; what notes and examples may contain | placeholders in the `.bpmn.ts`, then `decompile` / `merge` for an export | [Public safety](references/public-safety.md) | — |
| Recurring shapes | `choose`, `race`, `subProcess` with `loop`, `eventSubProcess` | [Patterns](#patterns) | — |

## Minimal shape

**MUST read [references/minimal-shape.md](references/minimal-shape.md) before writing a new process chain from scratch without a decompiled seed or staged example.**

## Structure by nesting

Use nesting wherever it expresses a relationship; it lowers to the same elements/flows as explicit methods, and `.sequenceFlow()` may be mixed freely. `examples/InvoiceEscalation.bpmn.ts` is a complete nested process; `examples/InvoiceApproval.bpmn.ts` is a 71-element import lifted by `bpmn decompile --style nested`, retaining seven explicit merge/fan-out flows. A short chain with a boundary timer and error, a `choose` and an error net: [Nested shape](references/minimal-shape.md#nested-shape).

- Declare a boundary event on its guarded activity in that activity's body; never write `attachedTo`. Interrupting paths rejoin after the activity; non-interrupting paths run beside it and must end with an end event, `.goto()`, or explicit flow. On a `.fork()` branch's last activity, the statement is the fork join; a failure handler must end with `.endEvent(<id>, { terminate: true })` or an error end, or add another branch statement; a plain end stalls the join ([draft-skeleton](references/draft-skeleton.md#what-a-skeleton-is) rule 9). On the activity written directly before a `.fork()`, a handler that does not end stalls the fork itself, so put a plain box between.
- `choose` arms require `when` or `otherwise: true`; fallback is the default flow; name no flow id, the SDK assigns one. Arms rejoin at the next statement, using `<id>_join` only when multiple arms reach it. Inside a `.fork()` branch, a `choose` or `race` arm that ends in a plain `.endEvent()`, or that jumps out with `.goto()` into a sibling branch, past the join, or into the join while the branch's own path also reaches it, stalls the fork's join; terminate/error-end it or rejoin ([draft-skeleton](references/draft-skeleton.md#what-a-skeleton-is) rule 9). Retry a whole fork by `.goto()`ing the box before it, never the fork.
- Consecutive elements in arms/handlers wire in order; branch with `choose`/`fork`/`race`, not a bare gateway, and jump with `.goto(id)`.
- An event sub-process guards its containing scope and catches what closer handlers did not; a boundary handler guards one activity. Put it inside a multi-instance sub-process to fail one iteration rather than the whole run. An error net's start captures the caught error by default into `vars.<net>_Error` (for `eventSubProcess('failures', { error: true }, …)`, `vars.failures_Error`), a JSON string read with `JSON.parse(vars.failures_Error)` ([Events and timers](references/bpmn-runtime.md#events-and-timers)). Each net id is unique; display names may be `Error`, but the default capture is never bare `vars.Error`. The `Error` spelling that IS fixed is the capture row's `source="=Error"`, the key the engine seeds the payload under, which the SDK writes for you. `errorVar` names the variable something else; `errorVar: false` omits the capture. Boundary handlers capture nothing by default; `errorVar` makes it readable as `=js:vars.<errorVar>.code`.
- `check` warns `NO_DEFAULT_FLOW` for an exclusive gateway whose flows are all conditioned; add `otherwise` or a default.
- Call `.flowMode('sequence')` before the first element to wire consecutive elements in scope; sub-processes inherit it and may override it. Explicit outgoing flow suppresses next-element wiring; a bare gateway is wired into but implies no outgoing flows. Elements with no incoming flow or unfinished paths are refused at build.
- Write shared downstream steps once after `choose`; let reaching arms fall through; never repeat the step, or a downstream gate, inside each arm. The repeated form passes `check`, `compile` and `validate`; it is the most common pattern error. If fall-through cannot reach it, name the join: `.exclusiveGateway(id)`, `.goto(id)` from every route, and `.sequenceFlow(id, next)`. See [Shared joins](references/patterns/composing-guide.md#shared-joins-the-mechanism-nesting-hides).
- After structural edits in a sequence scope, read `uip maestro bpmn check <Name>.bpmn.ts --graph` (inserting a line there rewires the graph): `~>` means implied, `->` explicit, and `[NO INCOMING]`/`[NO OUTGOING]` mark gaps.

## Patterns

Read only the guide for patterns actually used. Its node table marks **Entry** (omit when inserting into a running process), **Mechanism** (changing it changes the pattern), and **Placeholder** (bind it or skip if already present).

| Pattern | Use when | Guide |
|---|---|---|
| `ai-decision-review` | AI makes one call and acts or gets human review | [ai-decision-review-guide.md](references/patterns/ai-decision-review-guide.md) |
| `approval-chain` | Several sign-offs are needed | [approval-chain-guide.md](references/patterns/approval-chain-guide.md) |
| `smart-triage` | Inbound work is categorized and handled elsewhere | [smart-triage-guide.md](references/patterns/smart-triage-guide.md) |
| `external-wait` | Waiting on an outside party under an SLA | [external-wait-guide.md](references/patterns/external-wait-guide.md) |
| `high-volume-batch` | Many independent items run in one process | [high-volume-batch-guide.md](references/patterns/high-volume-batch-guide.md) |
| `failure-escalation` | Unhandled failures must not disappear | [failure-escalation-guide.md](references/patterns/failure-escalation-guide.md) |
| `queue-distribution` | An Orchestrator queue distributes work across runtimes | [queue-distribution-guide.md](references/patterns/queue-distribution-guide.md) |

**Do not reach for a pattern** for a short linear process, single node, or change introducing none of these shapes; it is never a wrapper for unnecessary work. For multiple patterns first read [references/patterns/composing-guide.md](references/patterns/composing-guide.md): retained start event, four joining methods, variable crossing of nesting boundaries, and two engine-constrained placements.

## Validation loop

<!--skill-flavor:validation-loop:start-->
```bash
uip maestro bpmn init <Name> --output json    # once; <Project> is Data.Path (see step 1)
uip maestro bpmn check <Name>.bpmn.ts --source
uip maestro bpmn check <Name>.bpmn.ts --graph   # resolved wiring; ~> means implied
uip maestro bpmn compile <Name>.bpmn.ts -o <Project>/<Name>.bpmn
uip maestro bpmn format <Project>/<Name>.bpmn
uip maestro bpmn refresh <Project> --output json   # entry-points.json + operate.json
uip maestro bpmn validate <Project>/<Name>.bpmn --output json
```

For an existing process, decompile first ([Brownfield](references/bpmn-runtime.md#brownfield-editing)), edit, run both `check` commands, then `merge` instead of `compile`/`format`, followed by `refresh` and `validate`. Format without `--relayout` only for `BPMN_PARSE_ERROR` with `No diagrams found`, `MISSING_DI_SHAPE`, or `MISSING_DI_EDGE`; then repeat refresh/validate. If `format --help` lacks `--relayout`, report layout reset unless the report was `No diagrams found`.

For connector nodes, run `check` and `compile` from the directory where `prepare` ran ([Connectors §3](references/connectors.md#3-the-loop-author--check--prepare--check--compile)).
<!--skill-flavor:validation-loop:end-->

`check` owns source/graph invariants; product validation owns compiled BPMN. Skipping `refresh` commonly breaks otherwise-correct validation.

Connector checks read the connector library and prepared overlay, reporting missing required input, unresolved `lookup()`, unprepared object, or self-naming binding before compile, each with its closing command. `--library <dir>` and `--connectors-local <dir>` select them; `--connectors-local` defaults to `.flow-sdk/connectors-local/` under the current directory, where `prepare` writes. `--library` defaults to `$FLOW_SDK_LIBRARY_JSON`, otherwise the `uip maestro registry pull` cache—not `uip maestro bpmn registry pull`. `check` reads bindings only with `--bindings`; `compile` reads them by default ([Connectors §3](references/connectors.md#3-the-loop-author--check--prepare--check--compile)).

## Operating a process

<!--skill-flavor:operating:start-->
Refresh package metadata, pack, upload to Studio Web (the meaning of "publish" unless Orchestrator is named), debug a real run, run a deployed process, inspect a job, and drive an instance lifecycle. All require `uip login`; run `uip maestro bpmn refresh <project-path>` before every cloud action. `bpmn debug` is a REAL run, not validation. Every mutation needs the user's decision for that action, except Studio Web upload of a project created this run, authorized by a build/draft request. Read **[`references/operate.md`](references/operate.md)**.
<!--skill-flavor:operating:end-->

## Evaluating a process

<!--skill-flavor:evaluating:start-->
Evaluators, eval sets, data points, and simulations are project files written by `uip maestro bpmn eval`; `<Name>.bpmn.ts` cannot create them. Add/list locally without login. Every `eval run` verb needs `uip login`; `eval run start` packages the solution and **uploads it to Studio Web** before running, so it needs the user's upload decision. Read **[`references/evaluate.md`](references/evaluate.md)**.
<!--skill-flavor:evaluating:end-->

## Diagnosing a failed run

Triage in order: job status, incidents, runtime variables, deployed BPMN asset, element executions/cursors, generated package files, then traces. Use exact CLI verbs from the reference, one literal command per read and never a loop, and include `-f <FOLDER_KEY>` on every `instance` read. Never mutate while diagnosing or guess command shapes. Read **[`references/diagnose.md`](references/diagnose.md)**.

## Evidence boundary

Static success does not prove tenant resource resolution, human outcomes, or
runtime-only values. Read [BPMN runtime decisions](references/bpmn-runtime.md)
when the requested outcome depends on those behaviors.
