# action task — Planning

A human-in-the-loop (HITL) action task for manual review, approval, sign-off, correction, or data entry.

## Ownership Boundary

Case owns the task's orchestration intent: target stage/lane, entry conditions, required/run-once flags, approved business I/O and outcomes, declared Case variables, and any resolved Action App metadata. It does **not** translate that intent into an HITL resource.

At execution, delegate every non-placeholder action T-entry to a sub-agent that follows the `uipath-human-in-the-loop` skill. That skill owns the QuickForm/App-specific schema representation, action-specific JSON, resource bindings, sidecars, runtime I/O, and HITL validation. Never read, import, quote, or reproduce files from the sibling skill.

The approved `sdd.md` and `tasks.md` are the user's schema confirmation for this delegated build. Pass only the relevant action declaration and Case context in the delegation brief.

## Path Selection

Record the user's approved intent; do not implement either path here:

1. **App named + resolves** — `HITL Implementation: Action App: <deploymentTitle>` resolves in `action-apps-index.json`. Record the canonical deployment metadata and delegate an App-based action.
2. **No app named** — `HITL Implementation: QuickForm` or silent. Record QuickForm as the preferred implementation and delegate it.
3. **App named + missing** — ask `Use QuickForm` / `Placeholder (deploy the app later)`. Record the selected intent. This is action-specific and outside the Rule-17 agent/API sibling-create gate.
4. **No usable HITL intent** — no declared inputs, outputs, decision, or outcomes. Plan a placeholder.

A deployed Action App is never created by Case. QuickForm is an inline HITL artifact, not a sibling project.

## Required Fields from sdd.md

| Field | Source | Notes |
|---|---|---|
| `display-name` | sdd.md task name | Required |
| `hitl-implementation` | `QuickForm` or `Action App: <deploymentTitle>` | Required, never `<UNRESOLVED>` |
| `resource-name` | App title from `HITL Implementation` | App-based only |
| `name` | selected `deploymentTitle` | App-based only |
| `folder-path` | selected `deploymentFolder.fullyQualifiedName` | App-based only |
| `task-type-id` | selected Action App `id` | App-based only |
| `task-title` | explicit title, description summary, or display name | Required for delegation |
| `priority` | sdd.md, default `Medium` | `Low` / `Medium` / `High` / `Critical` |
| `recipient` | typed sdd.md assignee | Prompt if silent |
| `labels` | sdd.md labels | Preserve as declared |
| `action-type` | sdd.md `actionType` | App-based only; preserve the resolved app selector |
| `input-schema` | exact approved Input Schema rows | Preserve field, type, binding, required |
| `output-schema` | exact approved Output Schema rows | Preserve field and binding/value |
| `outputs` | Case-normalized producer rows derived from Output Schema | Preserve `<field> -> <case-variable>` for Case lineage/xrefs |
| `outcomes` | approved Actions/Buttons rows | Preserve business names and behavior |
| `isRequired` | sdd.md, default `true` | Case structural setting |
| `runOnlyOnce` | sdd.md, default `true` | Case structural setting |

Do not translate these rows into HITL field directions, native types, sidecar properties, context entries, or runtime arrays. The delegate performs that translation.

## Registry Resolution (App-based only)

1. Read `action-apps-index.json` directly.
2. Match the exact intended `deploymentTitle`.
3. Record selected `id`, `deploymentTitle`, and `deploymentFolder.fullyQualifiedName`.
4. During Phase 0/1 planning, use `tasks describe` only when needed to verify that the approved I/O is supported by the selected app; persist that contract with the registry resolution.
5. Pass the selected registry object, persisted `tasks describe` I/O contract, and approved declared I/O to the HITL delegate.

Do not use planning metadata to construct Action App bindings or action JSON. Those are HITL build details. A QuickForm performs no registry lookup and has no `registry-resolved.json` entry.

## Recipient Handling

For a non-placeholder action:

- Specific user email → record the typed value.
- User/group UUID or runtime expression → preserve it verbatim.
- Group/role without an ID → omit the recipient and record an assignment note.
- Silent assignee → ask who should receive the task; accept email, group/role, runtime expression, or `Skip`.

Do not encode the recipient into an action-task JSON shape. Pass the approved value to the HITL delegate.

## tasks.md Entry Format

The entry is a self-contained delegation request, not an implementation recipe.

### QuickForm

```markdown
## T<n>: Add HITL action task "<display-name>" to "<stage>"
- hitl-implementation: QuickForm
- task-title: "<title-shown-to-user>"
- priority: Medium
- recipient: Email:user@company.com
- labels: finance, review
- input-schema:
  - <field> | <case-type> | <binding> | <required>
- output-schema:
  - <field> | <binding-or-value>
- outputs:
  - <field> -> <case-variable>
- outcomes:
  - <button> | <maps-to> | <behavior>
- runOnlyOnce: false
- isRequired: true
- order: after T<m>
- lane: <n>
- verify: delegated HITL action exists in the target lane; Case validation passes
```

### App-based

```markdown
## T<n>: Add HITL action task "<display-name>" to "<stage>"
- hitl-implementation: Action App: <deploymentTitle>
- taskTypeId: <action-app-id>
- name: "<selected-deployment-title>"
- folder-path: "<selected-deployment-folder>"
- task-title: "<title-shown-to-user>"
- priority: Medium
- recipient: Email:user@company.com
- labels: finance, review
- action-type: InvoiceReview
- input-schema:
  - <field> | <case-type> | <binding> | <required>
- output-schema:
  - <field> | <binding-or-value>
- outputs:
  - <field> -> <case-variable>
- runOnlyOnce: false
- isRequired: true
- order: after T<m>
- lane: <n>
- verify: delegated HITL action exists in the target lane; Case validation passes
```

## Placeholder

Plan a placeholder when the user explicitly chooses it or no usable HITL intent exists:

`<UNRESOLVED: HITL task "<display-name>" — no delegated implementation selected>`

At execution, delegation can also degrade to a placeholder when the `uipath-human-in-the-loop` skill is unavailable, the sub-agent fails, or the returned task cannot be verified. Preserve all structural fields, use `data: {}`, and report the delegation error. Never compensate by authoring HITL JSON inside Case.
