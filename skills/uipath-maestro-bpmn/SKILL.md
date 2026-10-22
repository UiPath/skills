---
name: uipath-maestro-bpmn
description: "UiPath Maestro BPMN / Process Orchestration: author, validate, package, operate, and diagnose .bpmn projects. For .flow use uipath-maestro-flow; for case plans use uipath-maestro-case."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# Reasoning budget
Match reasoning to difficulty: use scripts for mechanical, IO, and format work — if a provided script already covers the task, run it — don't re-derive it; reserve deep reasoning for judgments they cannot make.

# Working style
Read this SKILL.md and its scripts first. Plan from their behavior; outline the full sequence of steps before running anything; choose unchanged, modified, or complementary scripts; batch independent work and pipeline calls. Inspect each input once, preferably dumping it to a file for grep; reread a source image whenever it leaves context (see [Authoring from an image](#authoring-from-an-image)). Do not reread unchanged files/scripts/SKILL.md or rerun commands with unchanged inputs/state. Reread content after a tool changes it. Write needed code once as a terse reusable script with CLI path/parameter arguments; keep large results in files, inspect them, and filter CLI JSON by field (`jq select`), never truncate it (`head`, `sed -n`). Do nothing unnecessary.

# UiPath Maestro BPMN
Work with UiPath Maestro Process Orchestration `.bpmn` projects: author, validate, package, operate, and diagnose. Registry templates own registered-node execution payloads; the documented spec/canvas contract owns structural BPMN and serializer scaffold metadata: process scaffold, variables, bindings, entry points, flows, gateways, events, boundary events, containers, multi-instance markers, and diagram. Packaging and operation use the UiPath CLI and capability references.

## When to use
Use for creating/editing Maestro `.bpmn` projects, including text/image processes; gateways, events, boundary events, subprocesses, call activities, loops, conditions, variables; RPA, agent, HITL, queue, business-rule, API-workflow, Integration Service, internal-message, and timer nodes; and validation, packaging, upload, publishing, running, management, or diagnosis.

### Editing an existing `.bpmn` (preserve what you did not author)
Use [Patterns](#patterns), including for running processes. Make surgical edits: preserve unknown `uipath:*`, `uipath:migrationVersion`, tags, imported Integration Service payloads, stable IDs, and preserve-only structures in [references/structural-bpmn.md](references/structural-bpmn.md#do-not-generate-for-new-authoring-preserve-on-round-trip-only). Do not regenerate, discard extension data, normalize untouched nodes to canonical templates, or alter untouched attributes; only `bpmn:incoming`/`bpmn:outgoing` wiring may change on untouched neighbors. Do not add `type="json" target="bodyField"` to existing untouched `uipath:input` elements.

If `validate` finds a payload with a `type` attribute or outside `<bpmn:extensionElements>`, or an `Orchestrator.StartAgentJob` whose type version is not `v2` and whose `releaseKey` or `folderId` lacks a value, rewrite under rule 6 and name every rewrite in the summary. For existing ScriptTask preserve its mapping discriminator and `uipath:scriptVersion`; do not migrate a working brownfield node without explicit confirmation; see [references/structural-bpmn.md](references/structural-bpmn.md#script-tasks--jint-authoring-contract). Use `uipath-maestro-flow` for `.flow` JSON, `uipath-rpa` for XAML/coded workflows, `uipath-agents` for Python agents, and `uipath-maestro-case` for Case plans.

## Critical Rules
1. **Registry owns registry-listed node payloads.** Build execution extensions from `registry get` templates and serializer-owned scaffold only from the structural/canvas contract; never invent either from prose.
2. **Never fabricate an identifier.** Connection IDs, process/queue/connector keys, app IDs, and folder IDs/paths come from discovery or the user. A connector field whose `describe` entry has `Reference` takes the live lookup's `LookupValue`, never its display name. See [references/registry-workflow.md](references/registry-workflow.md#a-reference-entry-takes-a-looked-up-value-never-the-display-name).
3. **Structural BPMN is authored, not invented.** Follow [references/structural-bpmn.md](references/structural-bpmn.md) and state honestly what the registry does not expose.
4. **One clarifying round, then author.** Use AskUserQuestion only for an undecidable choice whose wrong answer is unrecoverable or would invent an identifier; batch those into one round before authoring and never open a second. If approval/confirmation is forbidden, ask nothing. Decide all else and name assumptions/evidence in the summary. For images confirm the full inventory, not a summary (see [Authoring from an image](#authoring-from-an-image)); in draft mode defer structure questions to the 3c gate.
5. **The diagram is mandatory.** Every node needs `BPMNShape` and every flow `BPMNEdge`. Run `uip maestro bpmn format <file.bpmn>` last among BPMN writes and before `validate` or `refresh`; both error on missing shapes.
6. **Declare node type as a `<uipath:type>` child.** Every `uipath:activity`, `uipath:event`, and `uipath:mapping` is inside `<bpmn:extensionElements>` and carries `<uipath:type value="<Type>" version="<version>" />`. If a template puts `type` on the wrapper, remove it, add the child, retain the wrapper's own `version`, and add `<bpmn:extensionElements>` if absent; this overrides 4b/4c paste-as-is. Take the version from the template's `uipath:type`, otherwise `uip maestro bpmn registry get <Type>`. `Orchestrator.StartAgentJob` uses `v2`, binds `name`/`folderPath`, and drops `releaseKey`/`folderId`. `Intsvc.WaitForEvent`, `Intsvc.EventTrigger`, `Maestro.ReceiveMessageEvent`, and `Maestro.SendMessageEvent` use `<uipath:event>`, including task-like hosts such as `<bpmn:receiveTask>`.
7. **No `--` in XML comments.** Never put commands or flags such as `--output`, `--connection-id`, or `--object-name` in `<!-- ... -->` comments.
8. **Use `--output json` for parsed CLI calls.**
9. **Public-safe always.** Do not expose customer XML, tenant URLs, real IDs, or private names; see [references/public-safety.md](references/public-safety.md). Exception: in the user's local project (the `.bpmn` and the CLI-generated `bindings_v2.json`), a connection binding and its folder key take the real IDs 4a bound (4a names when placeholders apply); repository notes, examples, and fixtures remain sanitized.
10. **Confirm before cloud changes.** Publish, deploy, run, pause, resume, cancel, retry, and migrate require explicit user consent; validate locally first. `solution upload` is the exception: unless the request forbids it, a request to build the process authorizes the upload that shows it, so upload without asking; confirm only when the project was not created this run (adopted at 2a or brownfield), because upload overwrites the cloud solution matching local `.uipx` SolutionId. Confirm at solution choice in 2a, or before 4g upload when 2a did not run.
11. **Retry is node configuration, never canvas.** Use `uipath:retry`; never draw retry loops with gateways/timers. See [references/structural-bpmn.md](references/structural-bpmn.md#choosing-an-error-handling-construct).
12. **Task SLA is task configuration, never canvas.** Put approval timers, reassignment, and escalation-on-breach on the user task, not boundary timers.
13. **An error event subprocess is interrupting and terminal.** It stops the normal path and records **Completed**, not Faulted. Every path through it must end in an explicitly named outcome, or a handled failure is indistinguishable from success. For recover-and-continue, attach an error boundary event instead.
14. **A different target system is not, by itself, a different shape.** Swapping Document Understanding for a UiPath agent, or Outlook for Gmail, changes a binding; change bindings rather than reshape unless the process genuinely differs.
15. **You author the process, never participate in it.** Runtime reasoning, classification, and extraction belong to a bound UiPath agent, Document Understanding, business-rule task, etc.; never perform them at authoring time or hardcode results. Bare “agent” means UiPath agent, never you.
16. **Generated package files are CLI-owned.** Never hand-author `bindings_v2.json`, `entry-points.json`, `operate.json`, or `package-descriptor.json`; run `uip maestro bpmn refresh <project-path>`, never deprecated `update-metadata`. An Integration Service draft or boundary handoff the user asked for (4c) emits only `.bpmn` and `.md` notes naming CLI-owned blockers.
17. **Delegated resources require five ordered steps. Stopping after the owning skill hands the resource back is not done.** A business rule skips step 4 and uses `name`/`folderPath`, keyed `<folderPath>.<name>`, with no release/folder keys; see [references/registry-workflow.md](references/registry-workflow.md) § Business rule bindings.
<!--skill-flavor:delegated-resource-solution-first:start-->
(1) Create/open the solution first (`uip solution init`; on `unknown command`, older `uip solution new`), then author the resource project inside it. Run the resource `init` and `uip maestro bpmn init` from the directory containing `.uipx`, as in **Assemble**; a project created outside any solution has no path to deployment.
<!--skill-flavor:delegated-resource-solution-first:end-->
<!--skill-flavor:delegated-resource-author-deploy:start-->
(2) Delegate authoring to the owning skill (for example `uipath-api-workflow`, `uipath-rpa`) with declared inputs/outputs, not an unauthored scaffold. (3) Pack, publish, and `solution deploy run` before binding; release and folder keys exist only after deployment. Redeploy via `uipath-solution`'s upgrade path.
<!--skill-flavor:delegated-resource-author-deploy:end-->
(4) Select the wrapper by `ProcessType` from `uip or processes list --folder-path <path> --all-fields --output json` ([registry-workflow.md](references/registry-workflow.md#agent-wrapper-selection--pick-by-processtype-not-the-label)). Low-code agents use `Orchestrator.StartAgentJob` type `v2`, binding `name` and `folderPath`, not rule 18. Otherwise read `Key` and `FolderKey` (PascalCase; default list omits `ProcessType`) and bind per rule 18, never with fabricated/placeholders. Re-read both after every deploy because `deploy run` creates a new folder. (5) Unless live runs are forbidden or a draft/handoff is requested, run `uip maestro bpmn debug`, read the node output in `debug-instance variables-all`, and map `=result.<key>` to the actual output key; scalars may use a generic key. Without a run use the schema name and report it unverified. A business rule maps its whole result as one `output` from `=result`, never one output per decision/column.
18. **Job-wrapper templates** `Orchestrator.StartJob`, `ExecuteApiWorkflowAsync`, `StartAgenticProcess[Async]`, and `StartCaseMgmtProcess[Async]` serve an unresolved `releaseKey` that validates but faults at runtime. Bind `releaseKey` as `=bindings.<id>` to the resource `Key`. For `ExecuteApiWorkflowAsync` also add literal `folderKey`=`FolderKey` and drop `folderId`, `folderPath`, and `name`. For the others retain remaining template fields and make the swap only after a live `key:FolderKey` fault; without a run report the node unverified. See [references/registry-workflow.md](references/registry-workflow.md#job-wrapper-v1-trap--releasekey-templates-are-unrunnable).

## The model
1. **Registry-listed payloads:** `uipath:activity`/`event`/`mapping`, `context`, `input`, `output`, and `bindingInfo` come from `uip maestro bpmn registry get <type>` `xmlTemplate`; never author them from prose.
2. **Spec/canvas scaffold:** the registry emits no definitions/process, flows, gateway conditions/defaults, event definitions, boundary attributes, subprocess/loop structure, or diagram. `uipath:variables`, `uipath:bindings`, `uipath:entryPointId`, and `uipath:migrationVersion` come from the structural contract. Use [references/structural-bpmn.md](references/structural-bpmn.md).

## Patterns
Seven recurring shapes apply to new and running processes. Read each guide actually used, and none unused; adapt known-good topologies: add steps, drop branches, and change counts as the process needs. Each guide's "Why it works" names the parts that carry the shape — change those and you are building something else, so say so. Shape tables mark each node **Entry** (omit when inserting into a process that already runs), **Mechanism** (changing it changes the pattern), or **Placeholder** (bind it, or skip it if the process already does this); author named elements. An unresolved Placeholder still gets its registry payload and public identity placeholders, never a bare task. Phase 2 is the exception: every activity is deliberately a bare `bpmn:task`; see [references/phase-2-skeleton-guide.md](references/phase-2-skeleton-guide.md).

| Pattern | Use | Guide |
|---|---|---|
| `ai-decision-review` | One AI call, acted on or human-reviewed | [ai-decision-review-guide.md](references/patterns/ai-decision-review-guide.md) |
| `approval-chain` | Multiple sign-offs | [approval-chain-guide.md](references/patterns/approval-chain-guide.md) |
| `smart-triage` | Sort inbound work into separately handled categories | [smart-triage-guide.md](references/patterns/smart-triage-guide.md) |
| `external-wait` | Outside-party wait under SLA | [external-wait-guide.md](references/patterns/external-wait-guide.md) |
| `high-volume-batch` | Many independent items | [high-volume-batch-guide.md](references/patterns/high-volume-batch-guide.md) |
| `failure-escalation` | Never silently lose failures | [failure-escalation-guide.md](references/patterns/failure-escalation-guide.md) |
| `queue-distribution` | Queue work across runtimes | [queue-distribution-guide.md](references/patterns/queue-distribution-guide.md) |

Do not use patterns for short linear work, a single node, or edits introducing none; patterns are not wrappers. For multiple patterns first read [references/patterns/composing-guide.md](references/patterns/composing-guide.md) for start-event ownership, four joining methods, variable boundaries, and constrained placements.

## Authoring from an image
**MUST read [references/image-transcription.md](references/image-transcription.md) § Authoring from an image before authoring or checking a process taken from an image (sketch, whiteboard, sticky notes, screenshot).**

## Workflow
Author in five ordered phases; mode selects steps but never changes behavior:

| Phase | Steps | Function | Reference |
|---|---|---|---|
| **0 — Surface** | — | No work; detection is future work | Below |
| **1 — Preflight** | 1a–1c | Login, scan solution/project, start from cloud copy; no project changes; every mode | Below |
| **2 — Skeleton** | 2a–2f | Scaffold, blank control-flow boxes, `format`, `validate`, show shape; no registry calls; draft only except 2a | [references/phase-2-skeleton-guide.md](references/phase-2-skeleton-guide.md) |
| **3 — Iterate** | 3a–3c | Adjust, re-`format`, show, hold approval gate; draft only | [references/phase-2-skeleton-guide.md](references/phase-2-skeleton-guide.md#iterating) |
| **4 — Wire it up** | 4a–4g | Discover, fetch templates, fill boxes, layout, validate, refresh, show | Below |

The skeleton and iteration show shape before wiring. **Auto** runs 2a then phase 4; all other steps remain identical.

### Modes
Choose the first match; never ask which mode:

| Mode | Condition | Phases |
|---|---|---|
| **Brownfield** | Target `.bpmn` exists; do not `init`; if bare, use 4c's two-key `project.uiproj` + refresh path | 0–1, 4 |
| **Discovery-only** | Asked to discover/save evidence or not author yet, even if it describes an eventual BPMN; immediately create `registry-evidence/` and save `registry pull --output json`, `registry list --output json` or `registry search ... --output json`, and each `registry get <type> --output json`; no scaffold/deep references. Recipe: [references/registry-workflow.md](references/registry-workflow.md#registry-evidence-only-tasks) | 0–1, terminate |
| **Draft** | Plan mode or user asks to draft/plan/sketch/design/*what would it look like*/show first. Judge the intent, not the word: a source-only draft/handoff under rule 16 is auto | 0–3, stop at gate |
| **Auto** | Default | 0–1, 2a, 4, no stop |

Report the chosen mode. In plan mode put boxes, gateways, and conditions in the plan; writes wait for approval, then build 2a–2f once the plan is approved. Only *Build it* at 3c authorizes phase 4. Keeping or not answering the outline means report an outline, not a finished process. Draft mode uploads the shape when allowed; otherwise show the laid-out local `.bpmn` and short outline.

Read references only when their covered structure is reached, and only that section; [references/structural-bpmn.md](references/structural-bpmn.md) begins with an anchor index. Get templates, write the first complete version, then investigate further.

### Phase 0 — Surface
Nothing to do yet.

### Phase 1 — Preflight
- **1a Check login:** chain `uip login status --output json` with 1b in the same Bash call, not a separate turn. Without login, `registry pull` exposes only built-in OOTB types: warn rather than discover against a partial registry; local authoring/`validate` still work offline. See [references/cli-conventions.md](references/cli-conventions.md#login-boundary).
- **1b Scan:** search for `*.uipx` no deeper than two levels, e.g. `find . -maxdepth 2 -type f -name '*.uipx' -print`; record the result and do not rescan in phase 2.
- **1c Cloud copy:** if 1b found a solution (not discovery-only), download by `.uipx` `SolutionId` into a separate directory: `uip solution download <SOLUTION_ID> --extract -d <DOWNLOAD_DIR> --output json`. `init` writes `SolutionId`; an `Instructions` “Studio Web API returned 404” means no cloud copy, so skip the rest. Other failures (offline/not logged in) also skip and report. Compare downloaded/local project `.bpmn` files only: Studio Web reformats `.uipx`/`project.uiproj` and adds `SolutionStorage.json`. If they differ, ask which copy to keep before authoring; later upload replaces cloud with local.

### Phase 2 — Skeleton
2b–2f are in [references/phase-2-skeleton-guide.md](references/phase-2-skeleton-guide.md); only 2a is below.

- **2a Create or adopt (greenfield only):** skip for discovery-only, brownfield/bare edits, and requested Integration Service draft/boundary handoff. Chain after 1b in the same turn; adopt its result without rescanning. If the user names `A/B/B.bpmn`, project directory is `A/B`: `mkdir -p` the parent, `cd` there, and run `uip maestro bpmn init <B> --skip-solution-registration --output json`; omit the flag only if the parent is already a solution. Author only at returned `Data.Path`.
  If a solution was found, stop and ask which one, as a pick list if the host has one: one option per solution found, plus “Create a new solution”; never silently adopt/init/repair. Explain that adoption lets later upload overwrite its cloud copy. If none was found, run `init` according to **Assemble**; 2b or 4c writes its generated `.bpmn`.

### Phase 3 — Iterate
Adjust shape, re-`format`, show it, and hold approval until agreement; see [references/phase-2-skeleton-guide.md](references/phase-2-skeleton-guide.md#iterating). Draft only.

### Phase 4 — Wire it up
- **4a Discover:** run `uip maestro bpmn registry pull` once and cache it for the session; use `list`/`search` to map intent. Run `uip is connections list --all-folders` (always `--all-folders`), never fabricate IDs, and ask only under rule 4. Bind each connector to an `Enabled` connection for its connector: named folder first, otherwise `IsDefault` `Yes`, otherwise first. Confirm with `uip is connections ping <id> --output json`; `Data.Status` must be `Enabled` (`State` is cached); try the next candidate otherwise. Another owner is not a reason to skip. In the summary name each bound connection's Name, Owner, and Folder, never Id, as a rule-4 assumption. Use placeholders only for requested source-only draft/handoff/placeholder/synthetic/public-safe/sanitized values or when no candidate pings `Enabled`. See [references/registry-workflow.md](references/registry-workflow.md).
- **4b Get templates:** fetch each chosen node with `uip maestro bpmn registry get <type> --output json`, all in one Bash call, e.g. `for t in TypeA TypeB TypeC; do uip maestro bpmn registry get "$t" --output json; done`. For `Intsvc.*`, add `--connection-id`/`--object-name`; choose the object from [registry-workflow.md](references/registry-workflow.md#picking-the-object-the-table-first-then-the-parameters), not `describe` ranking. Do not fetch structural gaps (flows, gateways, events, boundary events, loops, `errorMapping`/retry, diagrams). Lowercase the first character after `bpmn:` in every pasted opening/closing tag. Preserve `uipath:*` exactly except rules 6/18. `BPMN.ScriptTask` is the lookup key, but new nodes serialize `<uipath:type value="BPMN.Variables" version="v1" />` — never the lookup key. Local validation accepts the older discriminator, so a clean `validate` does not prove that mapping is right. Use the compatibility fallback only as scoped in [references/structural-bpmn.md#script-tasks--jint-authoring-contract](references/structural-bpmn.md#script-tasks--jint-authoring-contract).
- **4c Assemble:** if this run uploaded the shape, download first as 1c and build on the downloaded `.bpmn` when it differs. For greenfield edit 2a's file in place; never replace it, preserving generated JSON, `Event_start`, and `uipath:entryPointId`. Use the complete minimal file in [references/structural-bpmn.md](references/structural-bpmn.md#a-complete-minimal-file-author-from-this-not-from-examples) plus templates; **do not reverse-engineer authoring patterns from task fixtures, generated package files, or any installed package bundle under `node_modules`** — such spelunking is the top reason authoring runs out of time. Add only needed structural pieces. Leave the diagram to 4d; do not hand-author `bpmndi:*` while the source is still moving. For new local projects run `uip maestro bpmn init <ProjectName> --output json`, edit returned `Data.Path`, and preserve metadata. For a source-only draft the user has not asked to package or operate, pass `--skip-solution-registration` so no `*Solution/` wrapper or `.uipx` is created. `init` takes a project name, not a path, and writes under the current directory: `./<ProjectName>/` with that flag or inside an existing solution, `./<ProjectName>Solution/<ProjectName>/` otherwise.
<!--skill-flavor:named-solution-init:start-->
When the user names a solution, “same name” means `<ProjectName>`, not `<ProjectName>Solution`:
```bash
uip solution init <SolutionName> --output json
cd <SolutionName> && uip maestro bpmn init <ProjectName> --output json
```
If response has `Data.AutoCreatedSolution`, rerun inside the solution and report the stray directory.
<!--skill-flavor:named-solution-init:end-->
  For a requested path, `mkdir -p` its parent and initialize there with the leaf name plus `--skip-solution-registration`, or make that parent a solution; check `Data.Path`. If an older scaffold lacks it, add `xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"` to `bpmn:definitions` before writing any `xsi:type` attribute; see [references/shared/local-metadata-regeneration-guide.md](references/shared/local-metadata-regeneration-guide.md). Runnable BPMN/start-event path is lowercase `operate.json.main`, never `project.uiproj.main`. Preserve requested case-management variants with real lowercase `<uipath:caseManagement version="v1">...</uipath:caseManagement>` synthetic preserve-only payloads, not a typed `Orchestrator.StartCaseMgmtProcess*` shell. Preserve generic unsupported `uipath:Activity` as `<uipath:Activity version="v1">...</uipath:Activity>`, never a lowercase typed shell. XML-escape attribute placeholders as `&lt;TENANT_URL&gt;`, `&lt;FOLDER_KEY&gt;`, `&lt;CONNECTION_NAME&gt;`; raw angle brackets are allowed only in element text/CDATA. HITL gateway conditions must reference the exact variable in the template's `<uipath:output ... var="...">`, e.g. `=vars.Var_HitlResult == "approve"`, not a copied variable.
  Every new connector, including `Intsvc.UnifiedHttpRequest` and external agents, is V2: use `registry get --input-details` and paste `Data.V2`. In an existing workflow lacking `<uipath:intsvcActivityConfig version="v2" />`, never add it, and do not alter V1 nodes unless requested; rebuild a touched V1 trigger/wait because it faults. If `--input-details` is unknown, stop on trigger/wait/HTTP/external-agent and request a `uip` update; only a plain activity falls back to V1. See [references/v2-connector-nodes.md](references/v2-connector-nodes.md).
<!--skill-flavor:v2-solution-resources-refresh:start-->
After `bpmn refresh`, run `uip solution resources refresh` so connections become solution resources.
<!--skill-flavor:v2-solution-resources-refresh:end-->
  For V1 `Intsvc.*` activities whose `inputTarget` is `body` (`Intsvc.ActivityExecution` and async/agent/workflow variants), override the template's `InputNotes`, `DiscoveryNotes`, and `ContextFieldNotes`:
  - Emit exactly one `<uipath:input name="body" type="json" target="body">` containing the whole request object in CDATA, not a field-per-input or bare array. Dotted names nest (`fields.project.key` → `{"fields":{"project":{"key":…}}}`); `users[*]` becomes `{"users":["U1","U2"]}`. Put it and every `Parameters` input inside `<uipath:activity>`, after `</uipath:context>` and before template output; an input after `</uipath:activity>` is not sent and `validate` misses it. See [Body shape](references/registry-workflow.md#body-shape-hand-authored-files-need-one-targetbody-input).
  - Emit every `Required: true` parameter (Slack `send_as`) as its own `uipath:input` after context, inside activity, with `target` equal to its `Type`, using request value or `DefaultValue`. See [Parameters](references/registry-workflow.md#required-parameters-are-separate-from-the-body--emit-every-one).
  - For `Intsvc.ActivityExecution`, `operation` is the described `Operation.Name` (`Create`, `List`, `Retrieve`, `Update`, `Delete`, `Replace`), never activity `Name`.
  - Data Service files use `UploadFileToRecordField`, `DownloadFileFromRecordField`, and `DeleteFileFromRecordField`, never V2 objects from `uip is resources list`. See [Picking the object](references/registry-workflow.md#picking-the-object-the-table-first-then-the-parameters).
  - For every connection-bound `Intsvc.ActivityExecution`, retain context `folderKey` as `=bindings.<folderBindingId>` and its folder binding; omission faults `102010` `Value cannot be null (Parameter 'Folder')`. See [Bindings](references/registry-workflow.md#4-bindings--from-bindinginfo-never-invented).
  - A `Reference` uses the looked-up ID (Rule 2). A body value without a leading `=` is a literal: write `"=vars.<id>"`, and make text mixed with variables one `=js:` expression (`"=js:'Severity: ' + vars.Var_Severity"`).

  For an Integration Service draft or boundary handoff the user asked for (a request that only says to validate is not one), emit **only** the `.bpmn` plus the notes file — do NOT create the four generated package files (Rule 16); authoring them fails the boundary the task tests. The node itself is still authored: paste the registry's `Intsvc.*` template and keep the shell that template declares — `uipath:activity` for activities, `uipath:event` for `Intsvc.WaitForEvent` and `Intsvc.EventTrigger` (Rule 6) — plus its context and output, filling the resource identity slots with the escaped public placeholders. Event context references the connection as `connectionId`, activities as `connection`. A host element carrying neither shell, such as a bare `bpmn:sendTask` with no `uipath:activity`, is a missing node, not a draft. Only the resolved values are CLI-owned — see [references/registry-workflow.md](references/registry-workflow.md#2-get-the-template-for-each-chosen-type).
  For Integration Service draft notes, name every CLI-owned blocker literally, including the exact phrase `connection binding`, plus dynamic schemas, generated outputs, `bindings_v2.json`, and package metadata. Avoid softer wording such as "connection and process binding" because it hides the concrete artifact the CLI must supply.

  Run `uip maestro bpmn refresh <project-path>` after any edit that changes a start event id or adds or removes an entry point — **not only when packaging or operating**; a trigger-start draft (below) is the exception. Lay the diagram out first (4d): `refresh` validates before it writes, so a node you just added fails it with `MISSING_DI_SHAPE`. `operate.json` and `entry-points.json` are generated once and do not follow source edits, so 4e's validator fails on the mismatch: `entry-points.json references start event "Event_start" via filePath, but no <bpmn:startEvent id="Event_start"> exists`. Writing a full-file replacement from the minimal file above renames the initializer's `Event_start`, so a source-only draft needs this too; editing in place avoids it. Keep the output as written — that shape is the contract `pack` consumes.
  `refresh` requires an init-generated project: with no `project.uiproj` it fails `Required file is missing` / `RetryWillNotFix`. For a bare `.bpmn` (the shape of this repo's edit fixtures), write the two-key `project.uiproj` first — `{ "Name": "<ProjectName>", "ProjectType": "ProcessOrchestration" }` — then refresh, which writes the rest. Only fall back to the equivalent hand-authored shape in [references/shared/local-metadata-regeneration-guide.md](references/shared/local-metadata-regeneration-guide.md#source-only-fallback) when the CLI is unavailable. Do not copy CLI scaffold metadata shapes into a synthetic local project. Every root **manual** start event needs a `<uipath:entryPointId value="<uuid>" />` child in its `extensionElements`; without one `refresh` fails the whole project `RetryWillNotFix` instead of writing an empty entry-point list.
  When the request names a trigger as the start and asks for no package-ready, upload, debug, publish, or deploy deliverable, it is a trigger-start draft. For a timer or V1 connector start, turn the initializer's `Event_start` into the trigger in place, keeping its id and its `uipath:entryPointId` child, add no second start, and skip `refresh` (a timer or V1 start alone has no entry point, so it fails), even after binding a connection; `entry-points.json` stays valid. Any of those deliverables, including a later one on such a draft, keeps the manual `Event_start`, gives the trigger its own start id, joins the two per [Gateways](references/structural-bpmn.md#gateways), and runs `refresh`. A V2 connector trigger start is the exception, and the usual case, since every new trigger is V2: it carries its own `uipath:entryPointId` and is an entry point. In a draft, paste its `Data.V2` element with `{{ID}}` = `Event_start` in place of the manual start, add no second start, and run `refresh`; skipping it leaves `entry-points.json` on the old id and `validate` fails. A deliverable may do the same, or keep the manual `Event_start` beside it, joined as above, to debug from either start.
  A recurring timer is a `timeCycle` with an `R/` repeat (`R/P1D`), not the template's `timeDuration`. Clearing a stale-entry error by editing or deleting `entry-points.json` instead of running `refresh` passes `validate` and `pack` while shipping an empty `bindings_v2.json`.
  Give public inputs and outputs explicit runtime bridges, and converge routes returning one result on a single completion EndEvent — for the two-layer contract see [references/structural-bpmn.md](references/structural-bpmn.md#variables).
- **4d Lay out the diagram.** After the last source edit, and before any `validate`, `refresh`, or `pack` — including the `refresh` 4c calls for:

  ```bash
  uip maestro bpmn format <file.bpmn>
  ```

  It overwrites the file's `bpmndi:BPMNDiagram` in place, so the canvas renders the process arranged instead of stacked at the origin. Every deliverable gets this, source-only drafts included. It is also a hard precondition for the next two steps, not a cosmetic pass: a node with no `BPMNShape` or a flow with no `BPMNEdge` fails `validate` with `MISSING_DI_SHAPE` / `MISSING_DI_EDGE`, no diagram at all fails it with `BPMN_PARSE_ERROR`, and `refresh` validates before it writes, so it fails the same way. Edit the source again and the layout is stale — re-run this step before re-validating. If `format` reports `unknown command`, update the CLI (see [references/cli-conventions.md](references/cli-conventions.md)); if upgrading is unavailable, hand-author the fallback DI structure in [references/structural-bpmn.md](references/structural-bpmn.md).
- **4e Validate.** Check well-formedness first. `validate` tokenizes with a tolerant parser and reports `Valid` on XML with an unbound namespace prefix, so a `ParseError` here is a source defect to fix before anything else. Then run the CLI validator, which runs the full PO.Frontend canvas rule set (structural rules plus variable, method-call, input-type, and event-object checks) offline, plus deploy-readiness checks:

  ```bash
  python3 -c "import sys, xml.etree.ElementTree as ET; ET.parse(sys.argv[1])" <file.bpmn> &&
    ! grep -nE '</?bpmn:[A-Z]' <file.bpmn> &&
    uip maestro bpmn validate <file.bpmn> --output json
  ```

  `validate` ignores tag case; a line the `grep` prints is a tag to lowercase (4b).

  Exit 0 = valid. Exit 1 = a parse error, a `grep` hit, or a `validate` failure. Read severity from each issue's `[error]`/`[warning]` tag, not from the `Found N error(s)` header, which counts errors while the list under it prints warnings too. Fix only error-severity findings, then re-run 4d and validate again; stop re-validating once every remaining finding is a warning or the placeholder pair below. `read but never assigned` is a defect no error covers: nothing writes a value the process reads, so a step that should produce it does not. `MISSING_RESOURCE` (warning) and `MISSING_BINDING` (error) are one finding about one unresolved node, and the binding half is a live tenant lookup. Bind the node to a deployed resource. When the user asked for a placeholder, a source-only draft (Rule 16), or a boundary handoff, or 4a found no `Enabled` candidate, no invented identifier can clear `MISSING_BINDING` (Rule 2): exit 1 / `RetryWillNotFix` is the expected result. Report the pair once and continue; `refresh` (4f) succeeds with it unresolved. Fix every `VARIABLE_DOES_NOT_EXIST` warning: it names a reference with no declaration. A `VARIABLE_NOT_SET` warning on the node reading a start-event-scoped caller input is expected; see [references/structural-bpmn.md#validation](references/structural-bpmn.md#validation).

  `[warning] [(xml)] unknown attribute <type>` is expected noise from the script-task template's `<uipath:inputSchema type="jsonSchema">`. Leave it. `type` is required on `uipath:input`, `uipath:output`, and `uipath:inputOutput`; removing it there fails the load with `BPMN_PARSE_ERROR ... to be a string`. Do not bisect the file and do not read package bundles under `node_modules` to find the rule.

  Validation is structural preflight, not runtime proof — see [references/cli-conventions.md](references/cli-conventions.md). When execution is authorized, inspect runtime variables, element executions, and incidents before reporting behavioral success.

  If `validate` reports "unknown command" or clearly skips the structural rules, the installed CLI predates them — update it (see [references/cli-conventions.md](references/cli-conventions.md)). See [references/structural-bpmn.md#validation](references/structural-bpmn.md#validation).
- **4f Refresh derived metadata.** Once 4e leaves no fixable error, regenerate the four CLI-owned package files:

  ```bash
  uip maestro bpmn refresh <project-path> --output json
  ```

  Treat a nonzero result as a source/precondition failure: fix the BPMN or `project.uiproj`, re-run 4d and 4e, and refresh again — never repair the generated JSON by hand. Refresh after binding a connection (4a) and for a package-ready, upload, debug, publish, or deploy deliverable; a source-only draft needs it only for 4c's start-event edits, and a trigger-start draft (4c) skips it. For the full contract (scope, idempotency, binding rules) see [references/shared/local-metadata-regeneration-guide.md](references/shared/local-metadata-regeneration-guide.md).
- **4g Show the finished process.** When the request allows an upload and the project has a solution (`.uipx`), `uip solution upload <SolutionDir> --output json` returns the `Data.DesignerUrl`. When the project was not created in this run (brownfield, or adopted at 2a without a confirmation), confirm before uploading (Rule 10). When the request forbids upload, or there is no solution, skip it. Then reply in this shape, dropping lines that do not apply:

  ```text
  <Name>: built, validated<, uploaded><, run>. <One sentence if you kept the user's online changes.>
  <DesignerUrl as a link on its own line, or the local .bpmn path>

  - <what changed, one line each, up to 5>

  Assumed: <...>  Unverified: <...>
  ```

## Operate and diagnose
This skill also packages, ships, runs, and diagnoses Maestro projects through the UiPath CLI.

- **Package and operate** (package a project, upload to Studio Web, publish or deploy, run or debug instances, and manage jobs, instances, incidents, and lifecycle actions): see [references/operate/CAPABILITY.md](references/operate/CAPABILITY.md).
- **Diagnose** (fetch incidents, variables, and element executions, and trace a failed run back to its BPMN element): see [references/diagnose/CAPABILITY.md](references/diagnose/CAPABILITY.md). Runtime evidence — incidents, variables, element executions, cursors, the deployed asset — comes only from a `uip maestro bpmn ... --output json` read, one literal command per read, never a loop (rule 9 there); local `.bpmn` source and generated package files are read from disk as usual. Never substitute the files backing that CLI for the CLI itself — see rule 3 in that reference.

Any cloud-side change (publish, deploy, run, pause, resume, cancel, retry, migrate) requires explicit user consent, and local validation should pass first. `solution upload` is the exception — see Rule 10.

## Structural coverage
What the registry serves a template for vs. what you author by hand:

| Structure | Source |
|---|---|
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

Flagged registry gaps are authored from [references/structural-bpmn.md](references/structural-bpmn.md) and honestly surfaced to the user as gaps when asked.

## References

| Topic | Read |
|---|---|
| Phase 2 skeleton — blank boxes, real control flow, no registry calls | [references/phase-2-skeleton-guide.md](references/phase-2-skeleton-guide.md) |
| Discover → template → bind → assemble loop | [references/registry-workflow.md](references/registry-workflow.md) |
| Structural BPMN, event matrix, boundary events, containers, multi-instance, diagram, validation | [references/structural-bpmn.md](references/structural-bpmn.md) |
| Worked-out topology for a recurring process shape, and how shapes compose | Patterns table above → `references/patterns/*-guide.md` |
| Authoring from an image | [references/image-transcription.md](references/image-transcription.md) |
| Runtime expressions, `vars.`/`bindings.`/`iterator.`, `=js:` (Jint) syntax | [references/expression-authoring.md](references/expression-authoring.md) |
| CLI conventions and the side-effect boundary | [references/cli-conventions.md](references/cli-conventions.md) |
| Keeping content public-safe | [references/public-safety.md](references/public-safety.md) |
| Package, upload, publish, run, or manage instances | [references/operate/CAPABILITY.md](references/operate/CAPABILITY.md) |
| Diagnose a failed or misbehaving run | [references/diagnose/CAPABILITY.md](references/diagnose/CAPABILITY.md) |
| Project layout and generated package files | [references/shared/project-layout.md](references/shared/project-layout.md) |