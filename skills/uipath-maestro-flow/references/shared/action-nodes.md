# Action Node Structure

Reference boilerplate shared by every action-node `impl.md`. Plugin docs should link here and specify only the registry type string, plugin-specific inputs and rules, debug entries, and node-type configuration workflows.

## Registry validation

Before authoring, run:

```bash
uip maestro flow registry get <node-type> --output json
```

`registry get` returns the manifest at `Data.Node`; do not inspect `Data` directly as the node manifest.

```json
{
  "Data": {
    "Node": {
      "nodeType": "core.action.script",
      "version": "1.0",
      "handleConfiguration": [
        { "position": "left", "handles": [{ "id": "input", "type": "target" }] },
        { "position": "right", "handles": [{ "id": "success", "type": "source" }] }
      ],
      "inputDefinition": {},
      "outputDefinition": {}
    }
  }
}
```

Inspect `Data.Node.handleConfiguration` for input and output port names; it is an array of position groups, not a map with a top-level `handles` field. Inspect `Data.Node.inputDefinition` for required inputs, `Data.Node.outputDefinition` for downstream payloads, and `Data.Node.model.serviceType` where applicable. Each plugin `impl.md` records what to confirm for its node type.

## Standard JSON skeleton

Every action-node instance uses this base shape:

```json
{
  "id": "<nodeId>",
  "type": "<node-type>",
  "typeVersion": "<version>",
  "display": { "label": "<Label>" },
  "inputs": { /* plugin-specific — see plugin impl.md */ },
  "outputs": {
    "output": {
      "type": "object",
      "description": "<plugin-specific description>",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the action fails.",
      "source": "=Error",
      "var": "error"
    }
  }
}
```

`outputs.output` documents the success payload referenced downstream as `=js:$vars.{nodeId}.output`; `outputs.error` documents the failure shape. Runtime faults route to the implicit `error` port. See [Implicit error port on action nodes](file-format.md#implicit-error-port-on-action-nodes).

For action nodes, the instance `outputs` block is documentation, not the runtime contract. The matching `variables.nodes[]` entry exposes process-level `$vars.{nodeId}.output`; see [file-format.md — Node outputs](file-format.md#node-outputs). The BPMN emitter ignores the instance `outputs` block at serialization because the manifest's `outputDefinition` drives activity-side mapping.

**Exceptions:** Orchestrator-job nodes (api-workflow, rpa-workflow, agent, agentic-process, function) have their instance `outputs` read by the converter, which copies each `source` verbatim. A wrong `source` (for example, `=result.response`) breaks `$vars.{nodeId}.output`; declare `error` only there. End / terminate nodes also have their instance `outputs` consumed to map workflow-level `out` variables.

`uip maestro flow format` regenerates `variables.nodes[]` from the current node graph (MST-9972), so running format after structural edits self-heals an omitted entry.

## Standard ports

| Direction | Common name(s) | Notes |
| --- | --- | --- |
| Input (target) | `input` | Every action node accepts one input edge on `input`. |
| Output (success, source) | `output`, `default`, or `success` | The name varies by plugin; `registry get` is authoritative. |
| Output (error, source) | `error` | Implicit on every action node via `outputs.error`. |

Plugins may add dynamic source ports, such as HTTP `branch-{id}` from `inputs.branches`; document these in the plugin's `impl.md`.

## Adding and editing procedures

Use [editing-operations.md](../author/references/editing-operations.md) and [editing-operations-json.md](../author/references/editing-operations-json.md) for step-by-step add, delete, and wiring instructions. Plugin `impl.md` files should describe only node-type-specific inputs and wiring patterns.

## Migrating a plugin to reference this template

Keep in the plugin:

- registry type string and `typeVersion`;
- plugin-specific input fields;
- plugin-specific configuration workflows, such as `node configure` for HTTP/connector nodes;
- plugin-specific rules, common patterns, and debug table.

Replace with a link here:

- generic JSON skeleton;
- generic `outputs` block (`=result.response` / `=result.Error`);
- generic registry-validation prose;
- generic "Adding / Editing" cross-reference.