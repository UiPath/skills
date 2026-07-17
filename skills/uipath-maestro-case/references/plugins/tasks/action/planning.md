# action task — Planning

A human-in-the-loop (HITL) action task. Assigns a task to a user or group for manual review, approval, sign-off, correction, or data entry. Two authoring paths: **QuickForm** (inline form, no deployed app — the default) and **App-based** (a deployed Action Center app).

## When to Use

Pick this plugin when the sdd.md describes a `HITL` task, or any task requiring manual user interaction: approval, review, sign-off, correction, classification by a person.

## Path Selection

Choose by whether a deployed Action Center app backs the task:

1. **App named + resolves** — sdd.md `HITL Implementation` = `Action App: <deploymentTitle>` AND it resolves in `action-apps-index.json` → **App-based** (§ Registry Resolution). Bind to the deployed app.
2. **No app named** — sdd.md `HITL Implementation` = `QuickForm` or silent → **QuickForm** (§ QuickForm), the default. Author an inline form — no app, no registry, no bindings.
3. **App named + missing** — named app absent from `action-apps-index.json` → a Rule 17 empty-lookup confirm, **action-specific** (NOT the agent/api sibling-create gate in [registry-discovery.md § Create-on-Missing](../../../registry-discovery.md#create-on-missing-build-and-rediscovery) — QuickForm builds no sibling project): `AskUserQuestion` **Author QuickForm inline** / **Placeholder (deploy the app later)**. Create → QuickForm; Skip → placeholder. Report the swap in the completion report (`named app "<x>" not found — authored QuickForm`).
4. **Not derivable** — QuickForm chosen but no wired I/O and no described decision/outcomes → placeholder (§ Unresolved Fallback).

This plugin owns a self-contained Case QuickForm contract and must remain usable without any sibling skill. Other authoring surfaces should mirror this public contract independently. Reach for App-based only when the SDD names a specific deployed app.

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `display-name` | sdd.md task name |  |
| `resource-name` | `Action App: <deploymentTitle>` in sdd.md `HITL Implementation` | Concrete registry query; REQUIRED and never `<UNRESOLVED>`. Do not substitute `display-name`. |
| `name` | Selected registry `deploymentTitle` | Runtime resource binding consumed by Phase 2; use the selected app's canonical title. |
| `folder-path` | Selected registry `deploymentFolder.fullyQualifiedName` | Runtime folder binding consumed by Phase 2; use the selected app's exact deployment folder. |
| `task-type-id` | Registry resolution (below) | Action-app ID |
| `task-title` | sdd.md task title or description (see fallback below) | Required for `action` type. |
| `priority` | sdd.md (default `Medium`) | `Low` / `Medium` / `High` / `Critical`.  |
| `recipient` | sdd.md assignee email; **prompt the user if silent** | See Recipient Handling below. |
| `inputs` | sdd.md task data mapping | See [bindings-and-expressions.md](../../../bindings-and-expressions.md) |
| `outputs` | Discovered via `tasks describe` | Decision, comments, structured form fields |
| `isRequired` | sdd.md (default `true`) |  |

> **Path-scoped:** `resource-name`, `name`, `folder-path`, `task-type-id` apply to **App-based** only. QuickForm omits them — its form fields come from wired I/O (§ QuickForm), not `tasks describe`. `display-name`, `task-title`, `priority`, `recipient`, `isRequired` are shared by both paths.

## Task Title Fallback

`task-title` is what the user sees in the Actions app. Required on resolved action tasks (placeholders skip — see § Unresolved Fallback). Derive in this order:

1. SDD has an explicit title or question field → use it
2. SDD has a Description → summarize into a short, concise title
3. Neither → use the `display-name`

## Registry Resolution (App-based)

1. **Primary cache file:** `action-apps-index.json`.
2. **Identifier field:** `id` (NOT `entityKey` — action-apps use a different field).
3. **Name field:** `deploymentTitle` (not `name`).
4. **Folder field:** `deploymentFolder.fullyQualifiedName`.
5. **CLI search known to fail** for action-apps — always use direct cache-file inspection.
6. Set `name` to the selected entry's canonical `deploymentTitle` and `folder-path` to its exact `deploymentFolder.fullyQualifiedName`. Never substitute the task display name or a parent/truncated folder.
7. Discover form fields / inputs / outputs via `tasks describe` — see [bindings-and-expressions.md § Discovering output names](../../../bindings-and-expressions.md).

Query by the exact concrete `resource-name` from the SDD. `Action App ID` determines whether the prior phase resolved the app; an unresolved ID does not erase or replace the intended title. Action lookups stay in `action-apps-index.json` — never adopt a same-named resource from another cache type. A name absent from the index is **not** an automatic placeholder — it routes to the missing-app gate (§ Path Selection step 3).

See [registry-discovery.md](../../../registry-discovery.md#cli-search-gaps) for the fallback rationale.

## QuickForm (default — no deployed app)

Author an inline form; no deployed app, no registry lookup, no root bindings, and no `registry-resolved.json` entry. The authoring schema lives in a sibling `<TaskLabel>.hitl.json`; the task carries `data.context[hitlType]="quick"` **and** mirrors the form's runtime I/O into `data.inputs[]` / `data.outputs[]`. The sidecar alone does not deliver bindings to the packed HITL task. Full task + file shapes: [impl-json.md § QuickForm](impl-json.md).

Derive the form ONLY from the SDD's wired I/O + described decision — the pinned-I/O contract, [create-inline-common.md § Step 1](../create-inline-common.md#step-1--compute-the-pinned-io-contract). No field-name guessing, no silent `string` default.

| Form element | One per… | `.hitl.json` field shape | Required Case runtime bridge |
|---|---|---|---|
| **Input field** (reviewer reads) | wired input the reviewer must see | `direction:"input"`, `binding:"=vars.<v>"`; type pinned from the SDD Case Variables table | one `data.inputs[]` entry whose `name` is the field `id` and whose `value` is the same binding |
| **Output field** (reviewer enters) | wired output the case consumes downstream | `direction:"output"`, `variable:"<name>"`, `required:true` if mandatory; downstream reads `=vars.<name>` | one `data.outputs[]` entry that extracts `=<field.id>` and targets `=<field.variable>` |
| **inOut field** (reviewer edits a prefilled value) | wired value the human may correct | `direction:"inOut"`, both `binding` and `variable` | both an input entry and an output entry |
| **Outcomes** | the SDD's described decision | domain-specific buttons (Approve/Reject…), never a bare Submit | no task I/O entry; outcomes remain in the sidecar |

`task-title`, `priority`, `recipient` — derived exactly as App-based (§ Task Title Fallback, § Recipient Handling).

## Unresolved Fallback (placeholder)

A HITL task placeholders ONLY when no path yields a real task: no deployed app resolves **and** no QuickForm is derivable (no wired I/O, no described decision/outcomes), OR the user picks **Placeholder** at the missing-app gate (§ Path Selection step 3). A named-but-missing app does NOT auto-placeholder — it offers QuickForm first.

Mark `<UNRESOLVED: HITL task "<display-name>" — no deployed app and no derivable form>`. Emit only structural fields — drop every action-specific line (`task-title`, `priority`, `recipient`, `inputs`, `outputs`, `name`, `folder-path`, `task-type-id`). See [placeholder-tasks.md](../../../placeholder-tasks.md) for the full placeholder entry shape and wiring-block convention.

## Recipient Handling

> Resolved action tasks only (both paths) — placeholders skip this entire section (see § Unresolved Fallback).

- If sdd.md **names a specific user email**, record it in `tasks.md`. Sets `assignmentCriteria: "user"` at execution time.
- If sdd.md **names a group or role**, do **not** record a recipient — group assignment is configured separately via Actions app rules. Record a note in `tasks.md` so the user remembers to configure group assignment externally.
- If sdd.md is **silent on assignee**, **prompt the user** using **AskUserQuestion** with a direct open-ended prompt:
  > "The action task '<display-name>' has no assignee specified in sdd.md. Who should receive it? Enter an email, a group/role name, or 'Skip' to leave it unassigned for now."

  Parse the user's response:
  - Looks like an email → record as `recipient: <email>`.
  - Group / role name → omit recipient; record a note in `tasks.md` reminding the user to configure group assignment externally.
  - `Skip` or empty → omit recipient.

For open-ended inputs like an email address, use a direct prompt rather than AskUserQuestion with a finite option list.

## tasks.md Entry Format

Two variants by path. For the unresolved placeholder shape, see [placeholder-tasks.md § `tasks.md` Planning-Entry Shape](../../../placeholder-tasks.md#tasksmd-planning-entry-shape).

### App-based

```markdown
## T<n>: Add action task "<display-name>" to "<stage>"
- hitl-kind: app
- taskTypeId: <action-app-id>
- name: "<selected-deployment-title>"
- folder-path: "<selected-deployment-folder>"
- task-title: "<title-shown-to-user>"
- priority: Medium
- recipient: user@company.com   # omit when group-assigned or when user chose Skip
- assignment-note: "<free-form note if group-assigned>"   # optional
- runOnlyOnce: false   # from sdd.md "Run Only Once" column
- inputs:
  - <input_name> <- "<Stage>"."<Task>".<output>
  - <input_name> = "<literal-or-expression>"
- outputs: decision, comments
- isRequired: true
- order: after T<m>
- lane: <n>  # FE layout; increment per task. Within `runs-sequentially` group, parallel members share a lane (semantic).
- verify: Confirm Result: Success, capture TaskId
```

### QuickForm

```markdown
## T<n>: Add QuickForm action task "<display-name>" to "<stage>"
- hitl-kind: quick
- task-title: "<title-shown-to-user>"
- priority: Medium
- recipient: user@company.com   # omit when group-assigned or when user chose Skip
- assignment-note: "<free-form note if group-assigned>"   # optional
- fields:
  - <name> input  = "=vars.<v>"         # reviewer reads; bound to case var <v>
  - <name> output -> <var> [required]   # reviewer enters; downstream reads =vars.<var>
  - <name> inout  = "=vars.<v>" -> <var># reviewer edits a prefilled value
- outputs: <var1>, <var2>   # the output/inOut field vars — REQUIRED: declares the producer contract (the Out-arg producer scan reads `outputs:`, not `fields:`). The action recipe derives both runtime arrays from `fields:`: input/inOut -> data.inputs[], output/inOut -> data.outputs[].
- outcomes: Approve, Reject
- runOnlyOnce: false   # from sdd.md "Run Only Once" column
- isRequired: true
- order: after T<m>
- lane: <n>  # FE layout; increment per task. Within `runs-sequentially` group, parallel members share a lane (semantic).
- verify: uip maestro case validate passes; <TaskLabel>.hitl.json present alongside caseplan.json
```
