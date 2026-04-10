# Validation Guide

Validate `.flow` files after every structural change. This guide covers the full 17-item manual checklist, CLI validation, and common failure patterns.

## 1. Validation Checklist

Walk through every item after editing a `.flow` file. Each check can be performed by inspecting the JSON.

1. **Unique node IDs** -- No two entries in `workflow.nodes` share the same `id`. IDs must match `/^[a-zA-Z_][a-zA-Z0-9_]*$/`.

2. **Unique edge IDs** -- No two entries in `workflow.edges` share the same `id`.

3. **Edge source references exist** -- Every `edge.sourceNodeId` must match an `id` in `workflow.nodes`.

4. **Edge target references exist** -- Every `edge.targetNodeId` must match an `id` in `workflow.nodes`.

5. **Every edge has `targetPort`** -- All edges must have a non-empty `targetPort` field. This is the #1 validation failure.

6. **Every edge has `sourcePort`** -- All edges must have a non-empty `sourcePort` field.

7. **Port IDs match node type** -- The `sourcePort` must be a valid source handle ID for the source node's type. The `targetPort` must be a valid target handle ID for the target node's type. Check the node reference docs in `references/nodes/` for valid ports.

8. **Definition coverage** -- Every unique `type:typeVersion` pair in `workflow.nodes` must have a matching entry in `workflow.definitions` (by `nodeType:version`). Missing definitions cause a warning.

9. **Definition deduplication** -- No two entries in `workflow.definitions` share the same `nodeType:version` pair.

10. **`variables.nodes` regenerated** -- `workflow.variables.nodes` must contain one entry per output of every node. Regenerate from scratch after any node add/remove.

11. **`out` variables mapped on End nodes** -- Every variable in `variables.globals` with `direction: "out"` or `"inout"` must have a corresponding output mapping on every reachable End (`core.control.end`) node. Missing mappings cause silent runtime failures.

12. **Expression prefix** -- All JavaScript expressions must start with `=js:`. Missing prefix causes runtime evaluation failure.

13. **Script nodes return objects** -- Script node `inputs.script` must contain a `return { ... }` statement returning an object, not a bare scalar.

14. **No orphaned nodes** -- Every non-trigger node should have at least one incoming edge. Every non-end node should have at least one outgoing edge. (Warning, not error.)

15. **Trigger node exists** -- The flow must have exactly one trigger node (`core.trigger.manual` or `core.trigger.scheduled`). The trigger's `model.entryPointId` must be a UUID.

16. **`parentId` for subflow children** -- Nodes inside a loop/subflow must have `parentId` set to the parent node's ID.

17. **Metadata timestamps** -- `metadata.createdAt` and `metadata.updatedAt` should be valid ISO 8601 strings. Update `updatedAt` on every edit.

## 2. Common Failure Table

| Error | Cause | Fix |
|---|---|---|
| Missing `targetPort` | Edge created without specifying target handle | Add `targetPort` -- check the node's port table |
| Missing `sourcePort` | Edge created without specifying source handle | Add `sourcePort` -- check the node's port table |
| Duplicate node ID | Copy-pasted node without changing ID | Rename to a unique ID, update all edge references |
| Duplicate edge ID | Copy-pasted edge without changing ID | Rename to a unique ID |
| Missing definition | Added node but forgot to add its type to `definitions` | Copy the definition block from `uip flow registry get <nodeType>` output |
| Invalid node/edge references | `sourceNodeId` or `targetNodeId` does not match any node `id` | Correct the reference to an existing node ID, or add the missing node |
| Stale `variables.nodes` | Added/removed node without regenerating the variables | Regenerate `variables.nodes` from scratch |
| Invalid expression | Missing `=js:` prefix on a JavaScript expression | Prepend `=js:` to all expressions |
| Unmapped `out` variable | End node missing output mapping for a global `out` var | Add the output mapping on every reachable End node |

## 3. CLI Validation

If `uip` is available, use the CLI validator as a final check. It runs full semantic validation (Zod schema + built-in cross-reference rules) that cannot be replicated by manual inspection alone.

```bash
uip flow validate <FILE_PATH> --output json
```

### Success response

```json
{ "Result": "Success", "Code": "FlowValidate", "Data": { ... } }
```

### Failure response

```json
{ "Result": "Failure", "Message": "...", "Instructions": "Found N error(s): ..." }
```

The `Instructions` field contains the individual error messages. Parse these to identify which checklist items failed.

### What CLI validation catches

- All structural checks from the checklist above (items 1-9, 12, 15)
- Zod schema violations (missing required fields, wrong types)
- Cross-reference integrity (edges pointing to nonexistent nodes)
- Port existence validation
- Definition coverage

### What CLI validation misses

CLI validation is a local JSON schema and cross-reference check. It does **not** catch:

- **Connector-specific issues** -- wrong connection IDs, expired tokens, misconfigured enriched metadata fields. These require `uip flow registry get` and connection binding validation during the planning phase.
- **Runtime errors** -- API failures, timeout issues, external service unavailability. These only surface during `uip flow debug` (cloud execution).
- **Missing output mappings at execution time** -- an End node that lacks a `source` expression for an `out` variable will pass validation but silently produce `null` at runtime.
- **Script logic errors** -- a script node with valid syntax but wrong business logic passes validation.
- **Resource availability** -- RPA processes, agents, or apps referenced by resource nodes may not be published or may have been deleted. Validation does not check Orchestrator state.
- **Expression correctness** -- `=js:` expressions with valid syntax but incorrect variable references or logic errors pass validation.

## 4. Validation Loop Pattern

Run validation after **every** structural change to the `.flow` file. Do not batch multiple edits before validating -- catch errors early.

```
1. Edit the .flow file (add node, add edge, change input, etc.)
2. Run: uip flow validate <FILE_PATH> --output json
3. If Result is "Success" --> done, proceed to next edit or next workflow step
4. If Result is "Failure":
   a. Read the error messages in "Instructions"
   b. Fix the .flow file based on the error
   c. Go to step 2
```

Repeat until validation passes. There is no maximum retry count for validation -- every error has a deterministic fix. If the same error persists after a fix attempt, re-read the relevant checklist item above and verify the JSON structure matches the expected format.

> **validate vs debug:** `uip flow validate` is instant and local -- use it freely after every edit. `uip flow debug` uploads and executes the flow in the cloud with real side effects. Never use `debug` as a validation step.

## 5. What Validation Does NOT Catch

Even when `uip flow validate` returns `Success`, the flow may still fail at runtime. These categories require testing via `uip flow debug` or manual review:

| Category | Example | How to catch |
|---|---|---|
| Connector configuration | Wrong connection ID, expired auth token, incorrect enriched metadata fields | Validate connections during Phase 2 planning with `uip flow registry get` and connection binding |
| Runtime service errors | External API returns 500, timeout on HTTP call, Orchestrator queue unavailable | Run `uip flow debug` with explicit user consent |
| Missing output mappings | End node lacks `source` for an `out` variable -- produces `null` silently | Manual review: check every End node's `outputs` against `variables.globals` (checklist item 11) |
| Script logic errors | Script has valid syntax but computes the wrong value | Manual review of script logic or debug execution |
| Resource availability | Referenced RPA process was deleted or never published | Check resource status via `uip flow registry search` or Orchestrator |
| Expression logic | `=js:$vars.data.count + 1` when `count` is a string -- no type error, wrong result | Manual review or debug execution |
| Subflow scope leaks | Script references `$vars.parentVar` inside a subflow -- undefined at runtime | Manual review: subflows have isolated scope, pass values via inputs |
