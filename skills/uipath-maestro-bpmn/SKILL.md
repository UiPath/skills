---
name: uipath-maestro-bpmn
description: "UiPath Maestro BPMN / Process Orchestration: author (registry-driven), validate, package, operate, diagnose, and evaluate .bpmn projects, including a BPMN process the user wants to see or sketch before it is built. Evaluate: eval sets, evaluators, simulations, eval runs. For .flow→uipath-maestro-flow; for case plans→uipath-maestro-case."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# Reasoning budget
- Match reasoning to difficulty; for mechanical, IO, and format steps, run a provided script instead of re-deriving it. Reserve extended reasoning for the one judgment a script cannot make.

# Working style
- Read this SKILL.md and its scripts first; act from what they do: run, modify, or complement them.
- Plan the whole path; batch independent work and pipeline calls. Inspect each input once (dump to a file and grep it). After a tool or command may modify a file, reread the affected content before relying on it. Revisit a source image whenever it is no longer visible (see [Authoring from an image](#authoring-from-an-image)).
- Write each script once with CLI parameters and reuse it. Keep output small; write large results to files. Filter JSON with `jq select`, never truncate with `head` or `sed`. Do only immediately needed work; do not rerun unchanged work or reread an unchanged file already in context. No comment banners or narration in inline scripts.
- **Talk to the user in plain words.** Every line the user sees, including the short progress note you write while working, is one plain sentence about what is happening for them ("Sketching your process", "Checking what your tenant already has"). Never put an element, gateway, variable, validator, or file term in it, and never name a phase or step ("2f", "1a", "phase 4"): those labels are this skill's, not the user's.

# UiPath Maestro BPMN
Work with UiPath Maestro `.bpmn` projects: author, validate, package, operate, and diagnose. Registered-node execution payloads are registry templates; structural BPMN and serializer-owned scaffold metadata (process, variables, bindings, entry points, flows, gateways, events, boundary events, containers, multi-instance markers, and diagram) come from the documented spec/canvas contract. Packaging and operation use the UiPath CLI and capability references.

## When to use
Use for text/image creation; structural edits (gateways, events, boundary events, subprocesses, call activities, loops, conditions, variables); RPA, agent, HITL, queue, business-rule, API-workflow, Integration Service, internal-message, or timer nodes; validation; packaging/upload/publish/run; and diagnosis.

### Editing an existing `.bpmn` (preserve what you did not author)
For an existing file, use [Patterns](#patterns) when adding a listed shape, but make surgical edits. Preserve unknown `uipath:*`, `uipath:migrationVersion`, tags, imported Integration Service payloads, stable IDs, and all preserve-only structures in [references/structural-bpmn.md](references/structural-bpmn.md#do-not-generate-for-new-authoring-preserve-on-round-trip-only). Never regenerate or normalize untouched nodes; only their `bpmn:incoming`/`bpmn:outgoing` may change. Do not add canonical attributes to untouched neighbors.

If `validate` finds a payload with a `type` attribute or outside `<bpmn:extensionElements>`, or an `Orchestrator.StartAgentJob` whose type version is not `v2` and whose `releaseKey` or `folderId` lacks a value, rewrite it under rule 6 and name each rewrite in the summary. For existing ScriptTask, preserve its mapping discriminator and `uipath:scriptVersion`; explicit confirmation is required for migration: [references/structural-bpmn.md](references/structural-bpmn.md#script-tasks--jint-authoring-contract).

#### Keep the user's diagram
If the file already had a `bpmndi:BPMNDiagram` when this task started, preserve its pools, lanes, colors, sizes, placement, routing, every existing `BPMNShape`, `BPMNEdge`, and `BPMNLabel`, including bounds, waypoints, colors, `isHorizontal`, and each plane `bpmnElement`. **Do NOT run `uip maestro bpmn format`** on it: it may redraw the diagram and drop all of it while `validate` still passes. Exception: the user explicitly asks to re-layout or tidy the diagram. Then run `uip maestro bpmn format <file.bpmn> --relayout` only if `uip maestro bpmn format --help` lists `--relayout`; otherwise explain that format drops pools, lanes, and colors and run only after confirmation.

<!--skill-flavor:diagram-snapshot:start-->
1. Before the first write, copy the file outside the project folder and print its path: `SNAP="$(mktemp -d)/before.bpmn" && cp "<FILE>" "$SNAP" && echo "$SNAP"`. Record the printed path as `<SNAPSHOT_PATH>`; shell variables do not persist between tool calls.
<!--skill-flavor:diagram-snapshot:end-->
2. For each added node, add one `BPMNShape` sized like same-kind existing nodes, place it in its predecessor's lane, add its `bpmn:flowNodeRef`, and use free space in that lane that overlaps no other shape. If needed, shift every shape, label, and waypoint right of the insertion together and widen the pool, lanes, and any expanded subprocess around the insertion point by the same distance; never move individually.
3. For each added or retargeted flow, write only that flow's `BPMNEdge`, with orthogonal source-edge-to-target-edge waypoints.
4. For each deleted node or flow, delete its shape or edge and remove the node's `bpmn:flowNodeRef` from its lane.
<!--skill-flavor:diagram-preserved-check:start-->
5. After the last write and before `validate`, run [scripts/check-diagram-preserved.py](scripts/check-diagram-preserved.py) from `<SKILL_DIR>` (the directory containing SKILL.md): `python3 "<SKILL_DIR>/scripts/check-diagram-preserved.py" "<SNAPSHOT_PATH>" <file.bpmn> --removed <REMOVED_IDS>`. `<REMOVED_IDS>` is comma-separated deleted IDs; omit `--removed` if none. Use `python` or `py -3` if `python3` is unavailable; with no Python, compare manually using the script docstring's list. For each loss, retain and name it if user-requested (color, move, relayout); otherwise restore it from the snapshot. Recheck after restoration, at most twice; report remaining losses.
<!--skill-flavor:diagram-preserved-check:end-->

An `init` scaffold or greenfield draft has no user layout; run `format` as rule 5 requires. For `.flow` JSON use `uipath-maestro-flow`; XAML/coded workflows `uipath-rpa`; Python agents `uipath-agents`; Case plans `uipath-maestro-case`.

## Critical Rules
1. **Registry owns registry-listed node payloads.** Author execution extensions from `registry get` templates; author only serializer-owned structural metadata from the structural/canvas contract. Never invent either from prose.
2. **Never fabricate an identifier.** Connection IDs, process/queue/connector keys, app IDs, and folder IDs/paths come from discovery or the user. A connector field whose `describe` entry has `Reference` takes the live lookup's `LookupValue`, never the user's display name. See [references/registry-workflow.md](references/registry-workflow.md#a-reference-entry-takes-a-looked-up-value-never-the-display-name).
3. **Structural BPMN is authored, not invented.** Follow [references/structural-bpmn.md](references/structural-bpmn.md); state honestly what the registry does not expose.
4. **One clarifying round, then author.** Ask with AskUserQuestion (except at the 3c gate, which is a plain message) only for an undecidable choice whose wrong answer is unrecoverable or would invent an identifier; batch one round and never ask a second. Decide everything else and name each assumption and what tied in the summary. If the user says not to pause, ask nothing. For images, confirm the full inventory, not a summary. In draft mode, structure and resource questions wait for the 3c gate, and phase 4 asks nothing further about them. Rule 10 consent still applies.
5. **The diagram is mandatory.** Every node needs `BPMNShape`, every flow `BPMNEdge`. For a new/no-layout file, run `uip maestro bpmn format <file.bpmn>` as the last source write and before `validate` or `refresh`; a file that already had a diagram when the task started follows [Keep the user's diagram](#keep-the-users-diagram). Both `validate` and `refresh` error on missing shapes.
6. **Declare node type as a `<uipath:type>` child.** Every `uipath:activity`, `uipath:event`, and `uipath:mapping` is inside `<bpmn:extensionElements>` and contains `<uipath:type value="<Type>" version="<version>" />`. If a template puts `type` on the wrapper, remove it, add the child, retain wrapper `version`, and add missing `<bpmn:extensionElements>`; this overrides 4b/4c paste-as-is. Take version from the template, else `uip maestro bpmn registry get <Type>`. `Orchestrator.StartAgentJob` uses `v2`, binds `name`/`folderPath`, and drops `releaseKey`/`folderId`. `Intsvc.WaitForEvent`, `Intsvc.EventTrigger`, `Maestro.ReceiveMessageEvent`, and `Maestro.SendMessageEvent` use `<uipath:event>` even in task-like hosts such as `<bpmn:receiveTask>`.
7. **No `--` in XML comments.** Never put CLI commands or flags (`--output`, `--connection-id`, `--object-name`) in `<!-- … -->`; keep comments minimal.
8. **Use `--output json` for parsed CLI calls.**
9. **Public-safe always.** Do not expose customer XML, tenant URLs, real IDs, or private names; see [references/public-safety.md](references/public-safety.md). In the user's local `.bpmn` and CLI-generated `bindings_v2.json`, connection binding and folder key take the real IDs 4a bound (4a names when placeholders apply). Notes, repository examples, and fixtures remain sanitized.
10. **Confirm before cloud changes.** Publish, deploy, run, pause, resume, cancel, retry, and migrate require explicit consent after local validation.
<!--skill-flavor:rule-10-upload:start-->
   `solution upload` is authorized by a build request unless forbidden, so upload without asking. Confirm upload only for a project not created this run (adopted at 2a or brownfield). Confirm at the 2a solution choice; when 2a did not run, confirm before the 4g upload; upload overwrites the matching cloud `SolutionId`.
<!--skill-flavor:rule-10-upload:end-->
11. **Retry is node configuration, never canvas.** Use `uipath:retry`; never draw gateway/timer retry loops. See [references/structural-bpmn.md](references/structural-bpmn.md#choosing-an-error-handling-construct).
12. **Task SLA is task configuration, never canvas.** Approval timers, reassignment, and escalation-on-breach belong on the user task, not boundary timers.
13. **An error event subprocess is interrupting and terminal.** Normal flow stops and the instance is **Completed**, not Faulted. Every path must end in an explicitly named outcome; use an error boundary event for recover-and-continue.
14. **A different target system alone is not a different shape;** change bindings unless the process genuinely differs.
15. **You author the process and are never its runtime participant.** Place/bind the runtime agent, Document Understanding, business rule, or other node; never perform the work or hardcode its result. Bare “agent” means a UiPath agent, never you.
16. **Generated package files are CLI-owned.** Never hand-author `bindings_v2.json`, `entry-points.json`, `operate.json`, or `package-descriptor.json`; run `uip maestro bpmn refresh <project-path>`, never deprecated `update-metadata`. For a requested Integration Service draft or boundary handoff (4c), emit only `.bpmn` and `.md` notes naming CLI-owned blockers.
17. **Delegated resources (RPA workflow, API workflow, agent, business rule) require five ordered steps. Stopping after the owning skill hands the resource back is not done.** A business rule skips step 4; its release/folder keys do not apply, and it binds by `name` and `folderPath`, keyed `<folderPath>.<name>`, per [references/registry-workflow.md](references/registry-workflow.md) § Business rule bindings.
<!--skill-flavor:delegated-resource-solution-first:start-->
(1) Create/open the solution **first** (`uip solution init`; on `unknown command`, older `uip solution new`), then author the resource project inside it: run its `init` and `uip maestro bpmn init` from the directory containing `.uipx`, as in **Assemble**. A project outside a solution cannot be deployed.
<!--skill-flavor:delegated-resource-solution-first:end-->
<!--skill-flavor:delegated-resource-author-deploy:start-->
(2) Delegate authoring to the owning skill (for example `uipath-api-workflow`, `uipath-rpa`) with explicit declared inputs and outputs, not an unauthored scaffold. (3) Deploy it (pack, publish, `solution deploy run`) before binding; release and folder keys exist only after deployment. Redeploy through `uipath-solution`'s upgrade path.
<!--skill-flavor:delegated-resource-author-deploy:end-->
(4) Choose the wrapper by `ProcessType` from `uip or processes list --folder-path <path> --all-fields --output json` ([registry-workflow.md](references/registry-workflow.md#agent-wrapper-selection--pick-by-processtype-not-the-label)). A low-code agent uses `Orchestrator.StartAgentJob`, type `v2`, binding `name` and `folderPath`, not rule 18. Otherwise read `Key` and `FolderKey` (PascalCase; default list omits `ProcessType`) and bind per rule 18, never a placeholder/fabricated key. Re-read both after every deploy because `deploy run` creates a new folder.
<!--skill-flavor:debug-node-output:start-->
(5) Unless live runs are forbidden or a draft/handoff is requested, run with `uip maestro bpmn debug`, read the node output in `debug-instance variables-all`, and map `=result.<key>` to the actual key; scalars may use a generic key. Without a run, use the schema name and report the mapping unverified. A business rule maps its entire result as one `output` from `=result`, never one output per decision/column.
<!--skill-flavor:debug-node-output:end-->
18. **Job-wrapper registry templates** (`Orchestrator.StartJob`, `ExecuteApiWorkflowAsync`, `StartAgenticProcess[Async]`, `StartCaseMgmtProcess[Async]`) expose unresolved `releaseKey`: validation may pass but runtime faults. Override paste-as-is in 4b/4c. Bind `releaseKey` as `=bindings.<id>` to the resource `Key`. For `ExecuteApiWorkflowAsync`, also add literal `folderKey` from `FolderKey` and drop `folderId`, `folderPath`, and `name`. For others, retain remaining fields and make the swap only after a live `key:FolderKey` fault; without a run report unverified. See [references/registry-workflow.md](references/registry-workflow.md#job-wrapper-v1-trap--releasekey-templates-are-unrunnable).
19. **Fill every `{name}`/`<name>` placeholder in an HTTP request `url` before `registry get`** with a discovered/given value or `=js:` expression; never invent it. To change it, rerun `registry get`, never edit the element ([how](references/v2-connector-nodes.md#http-requests)).
20. **Write no extra files.** Write no notes, memory, summary, or
   validation-log file, and no scratch copy of the project, inside it or
   outside it. Report findings in the reply. The files a step or the user asks
   for are not extra: the project's own files (the `.bpmn` and what `init` and
   `refresh` generate), the 1c download directory, Discovery-only evidence
   (`registry-evidence/`, `cli-error.txt`), Rule 16 notes, Rule 17 resource
   projects, the image inventory, and helper scripts.

## The model
A valid file has two halves:
1. Registry-owned payloads: each listed node's `uipath:activity`/`event`/`mapping`, `context`, `input`, `output`, and `bindingInfo` comes from `uip maestro bpmn registry get <type>`'s `xmlTemplate`; never hand-author from prose.
2. Spec/canvas-owned structure: registry emits no definitions/process, flows, gateway conditions/defaults, event definitions, boundary attributes, subprocess/loop structure, or diagram; serializer-owned `uipath:variables`, `uipath:bindings`, `uipath:entryPointId`, and `uipath:migrationVersion` also come from [references/structural-bpmn.md](references/structural-bpmn.md).

## Patterns
Use the guide for each shape actually built; do not use patterns for a short linear process, one node, or unrelated edits. Guides are known-good adaptable topologies, not specifications; shape tables classify nodes as **Entry**, **Mechanism**, or **Placeholder**. Mechanism nodes carry the shape; if you change one, say so in the summary. Author the element the table names. Omit Entry when inserting into a running process; bind Placeholder, or skip it only if the process already does this. An unresolved 4a Placeholder still gets its registry payload and public identity placeholders, never a bare task. Phase 2 deliberately uses bare `bpmn:task` boxes: [references/phase-2-skeleton-guide.md](references/phase-2-skeleton-guide.md).

| Pattern | Use | Guide |
| --- | --- | --- |
| `ai-decision-review` | One AI call followed by action or human review | [ai-decision-review-guide.md](references/patterns/ai-decision-review-guide.md) |
| `approval-chain` | Several sign-offs | [approval-chain-guide.md](references/patterns/approval-chain-guide.md) |
| `smart-triage` | Categorize inbound work and route it | [smart-triage-guide.md](references/patterns/smart-triage-guide.md) |
| `external-wait` | Wait for an outside party under SLA | [external-wait-guide.md](references/patterns/external-wait-guide.md) |
| `high-volume-batch` | Process many independent items | [high-volume-batch-guide.md](references/patterns/high-volume-batch-guide.md) |
| `failure-escalation` | Prevent unhandled failures disappearing | [failure-escalation-guide.md](references/patterns/failure-escalation-guide.md) |
| `queue-distribution` | Distribute queue work across runtimes | [queue-distribution-guide.md](references/patterns/queue-distribution-guide.md) |

For multiple patterns, first read [references/patterns/composing-guide.md](references/patterns/composing-guide.md): start-event ownership, four join methods, variable scope across nesting, and two constrained placements. A single pattern needs only its guide.

## Authoring from an image
**MUST read [references/image-transcription.md](references/image-transcription.md) § Authoring from an image before authoring or checking a process taken from an image (sketch, whiteboard, screenshot).**

## Workflow
Author in phases 0–4 in order; mode selects phases, never behavior.

| Phase | Steps | Role | Reference |
| --- | --- | --- | --- |
| **0 — Surface** | — | Future surface detection; no action | Below |
<!--skill-flavor:phase-table-preflight:start-->
| **1 — Preflight** | 1a–1c | Login, scan solution/project, use cloud copy | Below |
<!--skill-flavor:phase-table-preflight:end-->
| **2 — Skeleton** | 2a–2f | Blank boxes/control flow, format, validate, refresh, show; no new registry calls (`list` ran in 1a) | [references/phase-2-skeleton-guide.md](references/phase-2-skeleton-guide.md) |
| **3 — Iterate** | 3a–3c | Adjust, re-format, show, name each box's resource, hold approval gate | [references/phase-2-skeleton-guide.md](references/phase-2-skeleton-guide.md#iterating) |
| **4 — Wire it up** | 4a–4g | Discover, template, paste, lay out, validate, refresh, show | Below |

Skeleton 2b–2f and phase 3 precede wiring only in draft mode; auto runs 2a then phase 4. Author early: read only the relevant reference section when reached. Get the needed templates, then write the first complete version before further spelunking. In plan mode put the skeleton outline in the plan and wait for approval before 2a–2f.

### Modes
Take the first match; never ask which mode.
- **Brownfield:** targeted `.bpmn` exists; no `init`; if bare, use the two-key `project.uiproj` plus 4c `refresh` path. Phases 0–1, 4.
- **Discovery-only:** request asks to discover before authoring, save raw registry JSON/evidence, or explicitly “do not author yet”, even if it describes an eventual BPMN. Immediately create `registry-evidence/` and save `registry pull --output json`, `registry list --output json` or `registry search ... --output json`, and each `registry get <type> --output json`; no scaffold or deep authoring references. See [references/registry-workflow.md](references/registry-workflow.md#registry-evidence-only-tasks). Phases 0–1 then stop.
- **Draft:** plan mode, or the user wants to see or approve the shape before it is built: *draft it first*, *plan it*, *sketch*, *design*, *what would it look like*, *show me first*. Judge the intent, not the word. A source-only “draft project/handoff” (Rule 16) is auto. Phases 0–3, stop at gate.
- **Auto:** default; phases 0–1, 2a, 4, no stop.

Say which mode was taken in the final report: in 4g's first line, or in the
3c reply when the run stops at the gate. 4g's first line carries the mode
as literal text, in place of `<draft|auto>` in the 4g template: write `(draft mode)` for any run that stopped at the 3c
gate, including after *Build it*, and write `(auto mode)` only in a run that
never stopped at a gate. Never write `(auto mode)` after a draft gate.

**Only *Build it* at 3c authorizes phase 4.** Outside plan mode, draft writes a real validated skeleton; do not report a chat outline as a skeleton. If the user keeps the outline or has not answered, report the skeleton as an outline, not a finished process.
<!--skill-flavor:draft-shape-display:start-->
If upload is allowed, show by upload; otherwise show local `.bpmn` and a short outline.
<!--skill-flavor:draft-shape-display:end-->
Plan mode is host state; never enter it yourself.

### Phase 0 — Surface
Nothing to do.

### Phase 1 — Preflight
<!--skill-flavor:login-status-check:start-->
- **1a:** In the same Bash call as 1b, run `uip login status --output json`. Without login, `registry pull` is OOTB-only and discovery is silently incomplete; tell the user. Local authoring/`validate` work offline; see [references/cli-conventions.md](references/cli-conventions.md#login-boundary).
<!--skill-flavor:login-status-check:end-->
  In the same call, read the element kinds Studio Web's toolbox shows; phase
  2 labels boxes with them. It reads the CLI's built-in list, so it needs no
  login and no `registry pull`:

  ```bash
  uip maestro bpmn registry list --limit -1 --output json --output-filter "ExtensionTypes[?!starts_with(ExtensionType,'Maestro.Case') && !contains(['Maestro.UpdateCaseState','Maestro.RetrieveCaseState','Maestro.NotificationService','Maestro.AcquireLock','Maestro.ReleaseLock','BPMN.Variables','uipath:Activity','A2A.AgentExecution','Intsvc.HttpExecution','Intsvc.SyncAgentExecution','Intsvc.AsyncAgentExecution','Intsvc.SyncWorkflowExecution'],ExtensionType) && (ends_with(BpmnElement,'Task') || BpmnElement=='bpmn:CallActivity')].[ExtensionType,Label]"
  ```

  The filter keeps the task types Studio Web's toolbox offers for new boxes
  (`BpmnElement` ending in `Task`, or `CallActivity`). It drops events, case
  management, A2A, the legacy HTTP request, the older external agent
  variants, and the sync external workflow variant (`Intsvc.AsyncAgentExecution`
  is dropped, `Intsvc.AsyncExecution` and `Intsvc.AsyncWorkflowExecution` stay).

- **1b:** Search up to two levels for `*.uipx` (for example `find . -maxdepth 2 -type f -name '*.uipx' -print`), record once, and use it to decide create/adopt.
<!--skill-flavor:cloud-copy-download:start-->
- **1c:** If found (not discovery-only), download by `.uipx` `SolutionId` into a separate directory: `uip solution download <SOLUTION_ID> --extract -d <DOWNLOAD_DIR> --output json`. A `Studio Web API returned 404` in `Instructions` means no cloud copy; skip. Other failures skip and report. Compare downloaded/local `.bpmn` only; Studio Web reformats `.uipx`/`project.uiproj` and adds `SolutionStorage.json`. If they differ, ask which copy to retain before authoring.
<!--skill-flavor:cloud-copy-download:end-->

### Phase 2 — Skeleton
2b–2f are specified in [references/phase-2-skeleton-guide.md](references/phase-2-skeleton-guide.md); only 2a is local.
- **2a:** For greenfield, chain after 1b, never rescan. Skip for discovery-only, brownfield/bare edits, or requested Integration Service draft/boundary handoff. If the user named `A/B/B.bpmn`, project directory is `A/B`: `mkdir -p` its parent, `cd` there, and run `uip maestro bpmn init <B> --skip-solution-registration --output json`; omit the flag only when parent is already a solution. Author only at returned `Data.Path`; never write a second `.bpmn` elsewhere.
<!--skill-flavor:adopt-solution-question:start-->
If a solution is found, stop and ask the user which to use, as a pick list if the host has one: one option per solution found, plus “Create a new solution”; never silently adopt/init/repair. Explain adoption means later upload overwrites its cloud copy.
<!--skill-flavor:adopt-solution-question:end-->
If none, run `init` per **Assemble**; draft uses 2b, auto 4c.

### Phase 3 — Iterate
Adjust, re-`format`, show, and hold approval until accepted: [references/phase-2-skeleton-guide.md](references/phase-2-skeleton-guide.md#iterating). Draft mode only. Before you write the 3c reply, read [references/gate-reply-template.md](references/gate-reply-template.md) in full, then end the turn with the reply exactly as it shows.

### Phase 4 — Wire it up
- **4a Discover:** Run `uip maestro bpmn registry pull` once per session; use list/search to map intent. For live connections run `uip is connections list --all-folders`. Bind a box only to a resource that fits its step (kind and purpose, not a similar name); when unsure, report it as none yet. In draft mode, bind each box to the resource the 3c gate named; when a connection it named does not ping `Enabled`, fall to the next candidate below and name the swap under `Assumed` in 4g. Bind each connector to an `Enabled` connection in the named folder, else `IsDefault` `Yes`, else first. Confirm with `uip is connections ping <id> --output json` (`Data.Status` must be `Enabled`; the list's `State` is cached); try the next candidate otherwise. Another owner is not a reason to skip. Report each bound connection's Name, Owner, Folder, never Id, as a rule-4 assumption. Use placeholders only for requested source-only draft/handoff/placeholder/synthetic/public-safe values or when none pings `Enabled`, or when the 3c gate reported the box's resource as *none yet*. See [references/registry-workflow.md](references/registry-workflow.md).
- **4b Get templates:** In **one** Bash call, never one per turn, fetch each selected registry node: `uip maestro bpmn registry get <type> --output json`, for example `for t in TypeA TypeB TypeC; do uip maestro bpmn registry get "$t" --output json --output-filter "ExtensionType.XmlTemplate"; done`.
   That filter returns only the template, as `Data.Value`; do not retry
   `registry get` with other filters or flags to find it. Use it for non-connector
   types only. Drop the filter when you need the full spec (`ContextFields`,
   bindings) of a type. Never put the filter on an `Intsvc.*` connector node: it
   projects away `Data.V2` and `Data.ISEnrichment`, which a connector node needs.
   Fetch each connector node without a filter, outside that loop:
   `uip maestro bpmn registry get <type> --connection-id <CONNECTION_ID> --object-name <OBJECT> --input-details '<JSON>' --output json`.
   For `Intsvc.*`, add `--connection-id`/`--object-name`; choose object from [registry-workflow.md](references/registry-workflow.md#picking-the-object-the-table-first-then-the-parameters), not `describe` ranking. Do not fetch structural gaps (flows, gateways, events, boundaries, loops, `errorMapping`/retry, diagrams). Lowercase the first character after `bpmn:` on every pasted opening/closing tag: `<bpmn:UserTask>` → `<bpmn:userTask>`. Preserve `uipath:*` exactly except rules 6/18. `BPMN.ScriptTask` is lookup key, but a new node uses `<uipath:type value="BPMN.Variables" version="v1" />`. Local validation accepts the older discriminator, so a clean `validate` does not prove that mapping is right; see [references/structural-bpmn.md#script-tasks--jint-authoring-contract](references/structural-bpmn.md#script-tasks--jint-authoring-contract).
- **4c Assemble:** If this run uploaded a shape, download it as 1c and use the downloaded `.bpmn` when it differs. For greenfield, write the `.bpmn` that 2a's `init` generated in this run (`<Name>.bpmn` at `Data.Path`; `init` never names it `Process.bpmn`) whole, in one Write, instead of patching it with a series of edits. That whole-file write is only for a file this run alone has touched. A downloaded copy or any brownfield `.bpmn` is edited in place, per Editing an existing `.bpmn`; never rewrite it from the minimal file. Never write a second `.bpmn`. Keep the initializer's `Event_start` id and its `uipath:entryPointId` in what you write, and never touch the four generated JSON files. Use the complete minimal file in [references/structural-bpmn.md](references/structural-bpmn.md#a-complete-minimal-file-author-from-this-not-from-examples) plus templates, filling placeholders only; **do not reverse-engineer authoring patterns from task fixtures, generated package files, or any installed package bundle under `node_modules`** — such spelunking is the top reason authoring runs out of time. Add only needed structural pieces; leave DI to 4d. New local projects use `uip maestro bpmn init <ProjectName> --output json`, edit `Data.Path`; `init` takes a name and writes `./<ProjectName>/` with `--skip-solution-registration` or inside an existing solution, `./<ProjectName>Solution/<ProjectName>/` otherwise. For a source-only draft the user has not asked to package or operate, pass `--skip-solution-registration` so no `*Solution/` wrapper or `.uipx` is created.
<!--skill-flavor:named-solution-init:start-->
When the user names a solution ("a solution of the same name" is `<ProjectName>`, not `<ProjectName>Solution`), create it and run `init` from inside it:
```bash
uip solution init <SolutionName> --output json
cd <SolutionName> && uip maestro bpmn init <ProjectName> --output json
```
If `Data.AutoCreatedSolution` appears, `init` ran outside; rerun inside and report the stray directory.
<!--skill-flavor:named-solution-init:end-->
For a requested path, `mkdir -p` its parent, run `init` there with the leaf name, and either use `--skip-solution-registration` or make the parent a solution; check `Data.Path`. Add `xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"` to older scaffolds before `xsi:type`. See [references/shared/local-metadata-regeneration-guide.md](references/shared/local-metadata-regeneration-guide.md). Put runnable BPMN/start-event path in lowercase `operate.json.main`, never `project.uiproj.main`.

For draft/preserve-only case variants, use real lowercase `<uipath:caseManagement version="v1">...</uipath:caseManagement>` with synthetic content; a typed `Orchestrator.StartCaseMgmtProcess*` shell is not a substitute. Preserve generic unsupported `uipath:Activity` as capitalized `<uipath:Activity version="v1">...</uipath:Activity>`, never `<uipath:activity><uipath:type value="uipath:Activity" ... />`, a lowercase typed shell. Escape XML attribute placeholders as `&lt;TENANT_URL&gt;`, `&lt;FOLDER_KEY&gt;`, `&lt;CONNECTION_NAME&gt;`; raw `<PLACEHOLDER>` is safe only in element text/CDATA. HITL outcome flows must reference the exact variable in the template's `<uipath:output ... var="...">`, e.g. `=vars.Var_HitlResult == "approve"`, not only a copied or derived script variable.

Every new connector, including HTTP (`Intsvc.UnifiedHttpRequest`) and external agents, is V2: run `registry get --input-details` and paste `Data.V2` unchanged. In an existing workflow without `<uipath:intsvcActivityConfig version="v2" />`, do not add it and leave V1 nodes unless requested; rebuild a touched V1 trigger/wait as V2 because it faults. If `unknown option '--input-details'`, the CLI predates V2 nodes: stop on a trigger, wait, HTTP request or external agent and tell the user to update `uip`; only a plain activity may use V1 fallback. See [references/v2-connector-nodes.md](references/v2-connector-nodes.md).
<!--skill-flavor:v2-solution-resources-refresh:start-->
After `bpmn refresh`, run `uip solution resources refresh` so connections become solution resources.
<!--skill-flavor:v2-solution-resources-refresh:end-->

For older/V1 `Intsvc.*` activities with `inputTarget` `body` (`Intsvc.ActivityExecution` and async, agent, workflow variants), these rules override the template's `InputNotes`, `DiscoveryNotes`, and `ContextFieldNotes`:
- Exactly one `<uipath:input name="body" type="json" target="body">` containing the whole request object in CDATA, never a per-field input or bare array. Dotted names nest (`fields.project.key` → `{"fields":{"project":{"key":…}}}`); `users[*]` is an array under `users` (`{"users":["U1","U2"]}`). Put it and all `Parameters` inputs inside `<uipath:activity>`, between `</uipath:context>` and template output; outside is not sent and `validate` misses it. See [Body shape](references/registry-workflow.md#body-shape-hand-authored-files-need-one-targetbody-input).
- Emit every `Required: true` parameter (including Slack `send_as`) as its own input with `target` equal to its `Type`, using request value or `DefaultValue` ([Parameters](references/registry-workflow.md#required-parameters-are-separate-from-the-body--emit-every-one)).
- `Intsvc.ActivityExecution` `operation` is the described `Operation.Name` (`Create`, `List`, `Retrieve`, `Update`, `Delete`, `Replace`), never activity `Name`.
- Data Service files use `UploadFileToRecordField`, `DownloadFileFromRecordField`, `DeleteFileFromRecordField`, never V2 objects shown by `uip is resources list`. See [Picking the object](references/registry-workflow.md#picking-the-object-the-table-first-then-the-parameters).
- `Intsvc.ActivityExecution` retains `folderKey` context input `=bindings.<folderBindingId>` and its folder binding on every connection-bound node; without it runtime faults `102010` `Value cannot be null (Parameter 'Folder')`. See [Bindings](references/registry-workflow.md#4-bindings--from-bindinginfo-never-invented).
- **Values.** A `Reference` field takes the looked-up id (Rule 2). A body value without a leading `=` is a literal: write `"=vars.<id>"`, and make text mixed with variables one `=js:` expression (`"=js:'Severity: ' + vars.Var_Severity"`).

For an Integration Service draft or boundary handoff the user asked for (a request that only says to validate is not one), emit **only** the `.bpmn` plus the notes file — do NOT create the four generated package files (Rule 16); authoring them fails the boundary the task tests. The node itself is still authored: paste the registry's `Intsvc.*` template and keep the shell that template declares — `uipath:activity` for activities, `uipath:event` for `Intsvc.WaitForEvent` and `Intsvc.EventTrigger` (Rule 6) — plus its context and output, filling the resource identity slots with the escaped public placeholders. Event context references the connection as `connectionId`, activities as `connection`. A host element carrying neither shell, such as a bare `bpmn:sendTask` with no `uipath:activity`, is a missing node, not a draft. Only the resolved values are CLI-owned — see [references/registry-workflow.md](references/registry-workflow.md#2-get-the-template-for-each-chosen-type).
For Integration Service draft notes, name every CLI-owned blocker literally, including the exact phrase `connection binding`, plus dynamic schemas, generated outputs, `bindings_v2.json`, and package metadata. Avoid softer wording such as "connection and process binding" because it hides the concrete artifact the CLI must supply.

Run `uip maestro bpmn refresh <project-path>` after any edit that changes a start event id or adds or removes an entry point — **not only when packaging or operating**; a trigger-start draft (below) is the exception. Lay the diagram out first (4d): `refresh` validates before it writes, so a node you just added fails it with `MISSING_DI_SHAPE`. `operate.json` and `entry-points.json` are generated once and do not follow source edits, so 4e's validator fails on the mismatch: `entry-points.json references start event "Event_start" via filePath, but no <bpmn:startEvent id="Event_start"> exists`. A whole-file write that keeps the initializer's `Event_start` and `uipath:entryPointId` (4c) needs no refresh; one that renames or drops them does, so a source-only draft that changed them needs this too. Keep the output as written — that shape is the contract `pack` consumes.
`refresh` requires an init-generated project: with no `project.uiproj` it fails `Required file is missing` / `RetryWillNotFix`. For a bare `.bpmn` (the shape of this repo's edit fixtures), write the two-key `project.uiproj` first — `{ "Name": "<ProjectName>", "ProjectType": "ProcessOrchestration" }` — then refresh, which writes the rest. Only fall back to the equivalent hand-authored shape in [references/shared/local-metadata-regeneration-guide.md](references/shared/local-metadata-regeneration-guide.md#source-only-fallback) when the CLI is unavailable. Do not copy CLI scaffold metadata shapes into a synthetic local project. Every root **manual** start event needs a `<uipath:entryPointId value="<uuid>" />` child in its `extensionElements`; without one `refresh` fails the whole project `RetryWillNotFix` instead of writing an empty entry-point list.

When the request names a trigger as the start and asks for no package-ready, upload, debug, publish, or deploy deliverable, it is a trigger-start draft. For a timer or V1 connector start, turn the initializer's `Event_start` into the trigger in place, keeping its id and its `uipath:entryPointId` child, add no second start, and skip `refresh` (a timer or V1 start alone has no entry point, so it fails), even after binding a connection; `entry-points.json` stays valid. Any of those deliverables, including a later one on such a draft, keeps the manual `Event_start`, gives the trigger its own start id, joins the two per [Gateways](references/structural-bpmn.md#gateways), and runs `refresh`. A V2 connector trigger start is the exception, and the usual case, since every new trigger is V2: it carries its own `uipath:entryPointId` and is an entry point. In a draft, paste its `Data.V2` element with `{{ID}}` = `Event_start` in place of the manual start, add no second start, and run `refresh`; skipping it leaves `entry-points.json` on the old id and `validate` fails. A deliverable may do the same, or keep the manual `Event_start` beside it, joined as above, to debug from either start.
A recurring timer is a `timeCycle` with an `R/` repeat (`R/P1D`), not the template's `timeDuration`. Clearing a stale-entry error by editing or deleting `entry-points.json` instead of running `refresh` passes `validate` and `pack` while shipping an empty `bindings_v2.json`.
Give public inputs and outputs explicit runtime bridges, and converge routes returning one result on a single completion EndEvent — for the two-layer contract see [references/structural-bpmn.md](references/structural-bpmn.md#variables).

- **4d Lay out the diagram.** After the last source edit, and before any `validate`, `refresh`, or `pack` — including the `refresh` 4c calls for:

  ```bash
  uip maestro bpmn format <file.bpmn>
  ```

  It overwrites the file's `bpmndi:BPMNDiagram` in place, so the canvas renders the process arranged instead of stacked at the origin. Every deliverable this task created gets this, source-only drafts included. A brownfield file that already had a diagram does NOT: follow [Keep the user's diagram](#keep-the-users-diagram) and run its check instead. It is also a hard precondition for the next two steps, not a cosmetic pass: a node with no `BPMNShape` or a flow with no `BPMNEdge` fails `validate` with `MISSING_DI_SHAPE` / `MISSING_DI_EDGE`, no diagram at all fails it with `BPMN_PARSE_ERROR`, and `refresh` validates before it writes, so it fails the same way. Edit the source again and the layout is stale — re-run this step before re-validating. If `format` reports `unknown command`, update the CLI (see [references/cli-conventions.md](references/cli-conventions.md)); if upgrading is unavailable, hand-author the fallback DI structure in [references/structural-bpmn.md](references/structural-bpmn.md).
- **4e Validate.**
<!--skill-flavor:wellformed-check:start-->
  Check well-formedness first. `validate` tokenizes with a tolerant parser and reports `Valid` on XML with an unbound namespace prefix, so a `ParseError` here is a source defect to fix before anything else. Then run the CLI validator, which runs the full PO.Frontend canvas rule set (structural rules plus variable, method-call, input-type, and event-object checks) offline, plus deploy-readiness checks:

  ```bash
  python3 -c "import sys, xml.etree.ElementTree as ET; ET.parse(sys.argv[1])" <file.bpmn> &&
    ! grep -nE '</?bpmn:[A-Z]' <file.bpmn> &&
    uip maestro bpmn validate <file.bpmn> --output json
  ```
<!--skill-flavor:wellformed-check:end-->

  `validate` ignores tag case; a line the `grep` prints is a tag to lowercase (4b).

  Exit 0 = valid. Exit 1 = a parse error, a `grep` hit, or a `validate` failure. Read severity from each issue's `[error]`/`[warning]` tag, not from the `Found N error(s)` header, which counts errors while the list under it prints warnings too. Fix error-severity findings and the warnings named below, then re-run 4d and validate again; stop re-validating once every remaining finding is another warning or the placeholder pair below. `read but never assigned` is a defect no error covers: nothing writes a value the process reads, so a step that should produce it does not. `MISSING_RESOURCE` (warning) and `MISSING_BINDING` (error) are one finding about one unresolved node, and the binding half is a live tenant lookup. Bind the node to a deployed resource. When the user asked for a placeholder, a source-only draft (Rule 16), or a boundary handoff, or 4a found no `Enabled` candidate, or the 3c gate reported *none yet*, no invented identifier can clear `MISSING_BINDING` (Rule 2): exit 1 / `RetryWillNotFix` is the expected result. Report the pair once and continue. A connection binding whose `default` is a placeholder fails `refresh` (4f) with "default must be a GUID", so that draft skips 4f; refresh needs a real connection id from `uip is connections list`. Fix every `VARIABLE_DOES_NOT_EXIST` warning: it names a reference with no declaration. Fix every `VARIABLE_NOT_SET` and `read but never assigned` on a variable a node or a flow condition reads; neither is expected. A declared start-event input reaches a process variable only through the start event's `BPMN.Variables` mapping, see [references/structural-bpmn.md#variables](references/structural-bpmn.md#variables).

  `[warning] [(xml)] unknown attribute <type>` is expected noise from the script-task template's `<uipath:inputSchema type="jsonSchema">`. Leave it. `type` is required on `uipath:input`, `uipath:output`, and `uipath:inputOutput`; removing it there fails the load with `BPMN_PARSE_ERROR ... to be a string`. Do not bisect the file and do not read package bundles under `node_modules` to find the rule.

  Validation is structural preflight, not runtime proof — see [references/cli-conventions.md](references/cli-conventions.md). When execution is authorized, inspect runtime variables, element executions, and incidents before reporting behavioral success.

  If `validate` reports "unknown command" or clearly skips the structural rules, the installed CLI predates them — update it (see [references/cli-conventions.md](references/cli-conventions.md)). See [references/structural-bpmn.md#validation](references/structural-bpmn.md#validation).
- **4f Refresh derived metadata.** Once 4e leaves no fixable error, regenerate the four CLI-owned package files:

  ```bash
  uip maestro bpmn refresh <project-path> --output json
  ```

  Treat a nonzero result as a source/precondition failure: fix the BPMN or `project.uiproj`, re-run 4d and 4e, and refresh again — never repair the generated JSON by hand. Refresh after binding a connection (4a) and for a package-ready, upload, debug, publish, or deploy deliverable; a source-only draft needs it only for 4c's start-event edits, and a trigger-start draft (4c) or a draft with a placeholder connection binding skips it; a placeholder-binding draft keeps the initializer's `Event_start` id and its `uipath:entryPointId`, because a renamed start event leaves `entry-points.json` stale and 4e fails. Such a draft is never a package-ready, upload, debug, publish, or deploy deliverable: stop and ask for a real connection, or report it blocked; never skip `refresh` and ship. For the full contract (scope, idempotency, binding rules) see [references/shared/local-metadata-regeneration-guide.md](references/shared/local-metadata-regeneration-guide.md).
- **4g Show the finished process.**
<!--skill-flavor:final-upload:start-->
  When the request allows an upload and the
  project has a solution (`.uipx`), `uip solution upload <SolutionDir> --output json`
  returns the `Data.DesignerUrl`. When the project was not created in
  this run (brownfield, or adopted at 2a without a confirmation), confirm before
  uploading (Rule 10). When the request forbids upload, or there is no
  solution, skip it.
<!--skill-flavor:final-upload:end-->
  Then reply in this shape, dropping lines that do not apply:

  ```text
<!--skill-flavor:final-first-line:start-->
  <Name>: built, validated<, uploaded><, run> (<draft|auto> mode). <One sentence if you kept the user's online changes.>
<!--skill-flavor:final-first-line:end-->
<!--skill-flavor:final-path-line:start-->
  <DesignerUrl as a link on its own line, or the local .bpmn path>
<!--skill-flavor:final-path-line:end-->

  - <what changed, one line each, at most 5 lines in all>

  Needs: <...>
  Assumed: <...>  Unverified: <...>
  ```

  When validation fails only because tenant resources are missing (no
  connection, agent, process, or queue to bind), the first line reads
  `<Name>: built, not runnable yet (<draft|auto> mode).` and `Needs:` names
  each missing resource in the user's words, such as `a Slack connection`
  or `the ticket triage agent`. Drop `Needs:` when nothing is missing.

  Write every line in the user's words: say what each step now does. No
  element type ids (`Orchestrator.StartAgentJob`), connector keys, object
  or operation names, payload, binding, or placeholder terms, and no file
  names other than the path line.

  This reply is your whole final message, and its first characters are the
  process name: write no status sentence or introduction before the
  `<Name>:` line. Send nothing beyond these lines: no extra sections,
  headings, tables, numbered lists, questions, or suggested next steps.
  **Write at most five change lines. A sixth line is a defect, not a
  judgment call.** Count the `-` change lines before you send:
  when there are more than five, merge related steps into one line each, and
  fold anything else the user must act on into `Needs`, `Assumed` or `Unverified`.
  Before sending, check the message against the template line by line and delete every line the template does not have.

## Operate, evaluate, and diagnose

Beyond authoring, this skill packages, ships, runs, evaluates, and diagnoses Maestro projects through the UiPath CLI.

- **Package and operate** (package a project, upload to Studio Web, publish or deploy, run or debug instances, and manage jobs, instances, incidents, and lifecycle actions): see [references/operate/CAPABILITY.md](references/operate/CAPABILITY.md).
- **Evaluate** (design evaluators and eval sets, add data points and simulations, and start/monitor/compare Studio Web evaluation runs for a BPMN project): see [references/evaluate.md](references/evaluate.md). `eval run start` deploys and overwrites the matching Studio Web solution (never auto-run a separate `uip solution upload`); read evaluate.md before running it.
- **Diagnose** (fetch incidents, variables, and element executions, and trace a failed run back to its BPMN element): see [references/diagnose/CAPABILITY.md](references/diagnose/CAPABILITY.md). Runtime evidence — incidents, variables, element executions, cursors, the deployed asset — comes only from a `uip maestro bpmn ... --output json` read, one literal command per read, never a loop (rule 9 there); local `.bpmn` source and generated package files are read from disk as usual. Never substitute the files backing that CLI for the CLI itself — see rule 3 in that reference.

Any cloud-side change (publish, deploy, run, pause, resume, cancel, retry, migrate) requires explicit user consent, and local validation should pass first. `solution upload` is the exception — see Rule 10.

## Structural coverage

This skill teaches authoring of the full surface the canvas supports. What the registry serves a template for vs. what you author by hand:

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

Flagged registry gaps: the registry serves no template for structural BPMN, sequence-flow conditions, event-definition payloads, boundary-event attributes, multi-instance markers, or the diagram. These are authored from the spec + canvas contract in [references/structural-bpmn.md](references/structural-bpmn.md) and honestly surfaced to the user as gaps when asked.

## References

| Topic | Read |
| --- | --- |
| Phase 2 skeleton — blank boxes, real control flow, no new registry calls | [references/phase-2-skeleton-guide.md](references/phase-2-skeleton-guide.md) |
| 3c gate reply — the fixed message that ends a draft-mode run | [references/gate-reply-template.md](references/gate-reply-template.md) |
| Discover → template → bind → assemble loop | [references/registry-workflow.md](references/registry-workflow.md) |
| Structural BPMN, event matrix, boundary events, containers, multi-instance, diagram, validation | [references/structural-bpmn.md](references/structural-bpmn.md) |
| Authoring a process from an image | [references/image-transcription.md](references/image-transcription.md) |
| Worked-out topology for a recurring process shape, and how shapes compose | Patterns table above → `references/patterns/*-guide.md` |
| Runtime expressions, `vars.`/`bindings.`/`iterator.`, `=js:` (Jint) syntax | [references/expression-authoring.md](references/expression-authoring.md) |
| CLI conventions and the side-effect boundary | [references/cli-conventions.md](references/cli-conventions.md) |
| Keeping content public-safe | [references/public-safety.md](references/public-safety.md) |
| Package, upload, publish, run, or manage instances | [references/operate/CAPABILITY.md](references/operate/CAPABILITY.md) |
| Design and run BPMN evaluations (evaluators, eval sets, data points, simulations, runs) | [references/evaluate.md](references/evaluate.md) |
| Diagnose a failed or misbehaving run | [references/diagnose/CAPABILITY.md](references/diagnose/CAPABILITY.md) |
| Project layout and generated package files | [references/shared/project-layout.md](references/shared/project-layout.md) |