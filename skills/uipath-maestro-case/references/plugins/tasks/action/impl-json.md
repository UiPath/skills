# action task — Delegated HITL Implementation

Case does not author action-specific JSON. For every approved, non-placeholder action T-entry, spawn a sub-agent that follows the `uipath-human-in-the-loop` skill and edits the existing Case project.

The delegate owns both QuickForm and App-based implementation details. This plugin owns only the handoff, target placement, failure fallback, and Case-level verification.

## Phase and Concurrency

Run action delegation during Phase 2 after the Case root, variables, stages, and target lanes exist.

- Delegate action tasks **sequentially**. Multiple sub-agents must never edit the same `caseplan.json` concurrently.
- Re-read `caseplan.json` after every delegate returns and before starting the next action.
- Phase 3 still applies shared task-entry conditions and binds downstream consumers. It does not rebuild or repair the delegated action's own data.

## Step 1 — Prepare a Self-Contained Brief

Read the approved action T-entry and the current `caseplan.json`. Supply only:

- absolute `caseplan.json` path and project directory;
- target stage ID/display name and lane;
- action display name and required/run-once settings;
- exact `hitl-implementation` preference;
- task title, priority, recipient, labels, action type, and assignment note;
- exact Input Schema, Output Schema, Case-normalized `outputs`, and outcomes from `tasks.md`; resolve any upstream Case cross-task reference through the normal Case resolver before handoff and include the resolved binding alongside the approved row;
- relevant declared Case variables and types;
- selected Action App registry object and persisted I/O contract for an App-based task.

Do not send unrelated stages/tasks or files from this skill. Do not read or quote the sibling skill's files; invoking it in the sub-agent is the runtime boundary.

## Step 2 — Invoke the HITL Delegate

Use this brief shape:

```text
Add one Human-in-the-Loop action task to an existing UiPath Case project by
following the uipath-human-in-the-loop skill.

The Case plan and HITL schema were already reviewed and approved by the user.
Treat the supplied declaration as confirmed; do not ask the Case caller to
redesign it. Do not debug, upload, publish, or deploy anything.

Caseplan:           <absolute path to caseplan.json>
Project directory:  <absolute path containing caseplan.json>
Target stage:       <stage display name> (id: <stage id>)
Target lane:        <lane index>
Task display name:  <display name>
Required:           <true|false>
Run only once:      <true|false>

HITL implementation: <QuickForm | Action App: deploymentTitle>
Task title:          <title>
Priority:            <level>
Recipient:           <typed recipient or omitted>
Labels:              <labels or omitted>
Action type:         <resolved app selector or N/A>
Assignment note:     <note or omitted>
Input Schema:
  <exact approved rows>
Output Schema:
  <exact approved rows>
Case output contract:
  <exact outputs rows used by Case lineage/xrefs>
Outcomes:
  <exact approved rows>
Relevant Case variables:
  <name + Case type>
Resolved Action App:
  <selected registry object + persisted tasks-describe I/O contract, or N/A>

Preserve all unrelated Case content. Add exactly one action task to the target
lane and create/update only HITL-owned artifacts required by your skill.
If you cannot locate/load uipath-human-in-the-loop, do not improvise the action
JSON. Return:
  {"built":false,"error":"skill uipath-human-in-the-loop not installed"}

Return JSON:
  {
    "built": true|false,
    "taskId": "<id or empty>",
    "elementId": "<elementId or empty>",
    "hitlKind": "<quick|app|empty>",
    "artifacts": ["<paths written>"],
    "error": "<message when built=false>"
  }
```

The delegate may determine the action-specific identifiers and artifacts required by its own contract. Case must not prescribe or reconstruct those shapes.

## Step 3 — Verify the Handoff

After the delegate returns:

1. Re-read `caseplan.json`.
2. Find exactly one `type: "action"` task with the requested display name in the requested stage/lane.
3. Confirm its `data` object is non-empty.
4. Confirm the returned `taskId` and `elementId` match the written task.
5. Confirm every returned artifact path exists inside the Case project.
6. Capture the task ID in `id-map.json`.
7. Continue the normal Case phase. The shared Phase-2 validation remains informational; Phase 4 is authoritative.

These are boundary checks, not permission to inspect or reproduce the delegate's schema algorithm.

If a prior interrupted run already contains exactly one matching non-placeholder action in the target lane, adopt it and capture its ID instead of delegating a duplicate.

## Failure — Placeholder, Never Local HITL Authoring

Treat any of these as delegation failure:

- the HITL skill is unavailable;
- the sub-agent returns `built:false`, dies, or returns malformed output;
- no matching action task was written;
- multiple matching tasks were written;
- the task landed in the wrong stage/lane;
- the task has empty `data`;
- a returned artifact is missing.

Surface the error, then write the standard structural placeholder in the target lane. The booleans below are examples; copy their exact values from `tasks.md`.

```json
{
  "id": "t<8 alphanumeric chars>",
  "type": "action",
  "displayName": "<display name>",
  "elementId": "<stageId>-<taskId>",
  "isRequired": true,
  "shouldRunOnlyOnce": false,
  "data": {}
}
```

Capture its ID, keep structural task conditions, add the delegation failure to `build-issues.md`, and continue. Do not leave partial HITL sidecars or a partially populated action marked as resolved; report partial artifacts for manual cleanup rather than guessing which are safe to delete.

## Post-Delegation Case Responsibilities

- Apply the approved task-entry conditions through the shared condition plugin.
- Bind downstream consumers to the delegated task's exposed outputs using the normal Case cross-task reference workflow.
- Regenerate `bindings_v2.json` from the final top-level bindings after all tasks are present.
- Run Case validation and solution packing through the normal Phase 4/6 workflow.
- Report whether each action was delegated successfully or remained a placeholder.

## Anti-Patterns

- **Do not write QuickForm sidecars, action context, resource bindings, recipients, or runtime I/O in Case.**
- **Do not copy a HITL JSON example or mapping table into this skill.**
- **Do not read files from the sibling HITL skill.** Runtime invocation is allowed; structural dependency is not.
- **Do not run two action delegates against one `caseplan.json` concurrently.**
- **Do not convert a delegation failure into a locally improvised action.** Use `data: {}`.
- **Do not report a placeholder as a completed HITL task.**
