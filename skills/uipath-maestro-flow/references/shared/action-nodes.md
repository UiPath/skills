# Action Node Structure

Reference for the boilerplate shared by every action-node `impl.md` in this skill. Plugin docs should link here for the standard parts and only spell out what is plugin-specific: the registry type string, plugin-specific input fields, plugin-specific rules, debug entries, and node-type configuration workflows.

## Registry validation

Every action node should validate its registry contract before authoring:

```bash
uip maestro flow registry get <node-type> --output json
```

`registry get` returns the manifest at `Data.Node`. Do **not** inspect `Data` directly as if it were the node manifest.

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

Inspect:

- `Data.Node.handleConfiguration` — input port name and output port name(s). Array of position groups, not a map with a top-level `handles` field.
- `Data.Node.inputDefinition` — required inputs.
- `Data.Node.outputDefinition` — downstream payloads.
- `Data.Node.model.serviceType` — where applicable.

Plugin `impl.md` records what to confirm for that specific node type.

## Standard JSON skeleton

All action nodes share this base shape on the node instance:

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
      "source": "=result.Error",
      "var": "error"
    }
  }
}
```

`outputs.output` documents the success payload referenced downstream as `=js:$vars.{nodeId}.output`. `outputs.error` documents the failure shape; the runtime routes to the implicit `error` port when the action faults. See [Implicit error port on action nodes](file-format.md#implicit-error-port-on-action-nodes).

> **Do not omit the instance `outputs` block when the plugin skeleton includes it.** The manifest's `outputDefinition` drives activity-side output mapping, but current validators also require instance `outputs.output` / `outputs.error` for some action families (IxP is strict here). The instance block still does not expose the value to downstream nodes by itself: what exposes `$vars.{nodeId}.output` as a process-level variable is the matching `variables.nodes[]` entry — see [file-format.md — Node outputs](file-format.md#node-outputs). End / terminate nodes are different: their instance `outputs` block is consumed to map workflow-level `out` variables. `uip maestro flow format` regenerates `variables.nodes[]` from the current node graph (MST-9972), so running format after structural edits self-heals an omitted entry.

## Standard ports

| Direction | Common name(s) | Notes |
| --- | --- | --- |
| Input (target) | `input` | Every action node accepts a single input edge on `input`. |
| Output (success, source) | `output`, `default`, or `success` | Name varies by plugin — `registry get` is authoritative. |
| Output (error, source) | `error` | Implicit on every action node via `outputs.error`. |

Some plugins add dynamic source ports (e.g., HTTP `branch-{id}` from `inputs.branches`); those are documented in the plugin's own `impl.md`.

## Adding and editing procedures

For step-by-step add, delete, and wiring instructions, see [editing-operations.md](../author/references/editing-operations.md) and the JSON recipes in [editing-operations-json.md](../author/references/editing-operations-json.md). Plugin `impl.md` files describe only the inputs and wiring patterns that are specific to the node type.

## Migrating a plugin to reference this template

When converting an existing plugin `impl.md` to use this template:

- **Keep in the plugin:** registry type string, `typeVersion`, plugin-specific input fields, plugin-specific configuration workflow (e.g., `node configure` for HTTP/connector nodes), plugin-specific rules, common patterns, debug table.
- **Replace with a link here:** generic JSON skeleton, generic `outputs` block (`=result.response` / `=result.Error`), generic registry-validation prose, generic "Adding / Editing" cross-reference.
