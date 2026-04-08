# Validation Checklist

Walk through this checklist after every `.flow` file edit. Each item is a structural check you can perform by inspecting the JSON.

## Checklist

1. **Unique node IDs** -- No two entries in `workflow.nodes` share the same `id`. IDs must match `/^[a-zA-Z_][a-zA-Z0-9_]*$/`.

2. **Unique edge IDs** -- No two entries in `workflow.edges` share the same `id`.

3. **Edge source references exist** -- Every `edge.sourceNodeId` must match an `id` in `workflow.nodes`.

4. **Edge target references exist** -- Every `edge.targetNodeId` must match an `id` in `workflow.nodes`.

5. **Every edge has `targetPort`** -- All edges must have a non-empty `targetPort` field. This is the #1 validation failure.

6. **Every edge has `sourcePort`** -- All edges must have a non-empty `sourcePort` field.

7. **Port IDs match node type** -- The `sourcePort` must be a valid source handle ID for the source node's type. The `targetPort` must be a valid target handle ID for the target node's type. Check the node reference docs in `references/nodes/` for valid ports.

8. **Definition coverage** -- Every unique `type:typeVersion` pair in `workflow.nodes` must have a matching entry in `workflow.definitions` (by `nodeType:version`). Missing definitions cause a warning.

9. **Definition deduplication** -- No two entries in `workflow.definitions` share the same `nodeType:version` pair.

10. **`variables.nodes` regenerated** -- `workflow.variables.nodes` must contain one entry per output of every node. Regenerate from scratch after any node add/remove. See [project-scaffolding-guide.md](project-scaffolding-guide.md) Section 3.

11. **`out` variables mapped on End nodes** -- Every variable in `variables.globals` with `direction: "out"` or `"inout"` must have a corresponding output mapping on every reachable End (`core.control.end`) node. Missing mappings cause silent runtime failures.

12. **Expression prefix** -- All JavaScript expressions must start with `=js:`. Missing prefix causes runtime evaluation failure.

13. **Script nodes return objects** -- Script node `inputs.script` must contain a `return { ... }` statement returning an object, not a bare scalar.

14. **No orphaned nodes** -- Every non-trigger node should have at least one incoming edge. Every non-end node should have at least one outgoing edge. (Warning, not error.)

15. **Trigger node exists** -- The flow must have exactly one trigger node (`core.trigger.manual` or `core.trigger.scheduled`). The trigger's `model.entryPointId` must be a UUID.

16. **`parentId` for subflow children** -- Nodes inside a loop/subflow must have `parentId` set to the parent node's ID.

17. **Metadata timestamps** -- `metadata.createdAt` and `metadata.updatedAt` should be valid ISO 8601 strings. Update `updatedAt` on every edit.

## Optional: CLI Validation

If `uip` is available:

```bash
uip flow validate <FILE_PATH> --output json
```

This runs full semantic validation (Zod schema + built-in rules) that cannot be replicated manually. Use it as a final check.

## Common Validation Failures

| Error | Cause | Fix |
|---|---|---|
| Missing `targetPort` | Edge created without specifying target handle | Add `targetPort` -- check node's port table |
| Duplicate node ID | Copy-pasted node without changing ID | Rename to unique ID, update all edge references |
| Missing definition | Added node but forgot to add its type to `definitions` | Copy definition block from node reference doc |
| Stale `variables.nodes` | Added/removed node without regenerating | Regenerate per scaffolding guide Section 3 |
| Invalid expression | Missing `=js:` prefix | Prepend `=js:` to all expressions |
| Unmapped `out` variable | End node missing output for a global `out` var | Add output mapping on End node |
