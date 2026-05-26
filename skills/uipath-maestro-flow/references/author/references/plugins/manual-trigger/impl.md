# Manual Trigger — Implementation

## Node Type

`core.trigger.manual`

## Registry Validation

```bash
uip maestro flow registry get core.trigger.manual --output json
```

Confirm: no input port, output port `output`, no required inputs. Definition version `1.0`.

> **Usually already present.** `flow init` scaffolds this node (id `start`) and its `definitions[]` entry. You only author it from scratch when rebuilding or swapping a trigger — see [planning.md](planning.md).

## JSON Structure

```json
{
  "id": "start",
  "type": "core.trigger.manual",
  "typeVersion": "1.0",
  "display": { "label": "Manual Trigger" },
  "inputs": {
    "entryPointId": "<uuid>"
  },
  "outputs": {
    "output": {
      "type": "object",
      "description": "Data passed when manually triggering the workflow.",
      "source": "=result.response",
      "var": "output"
    }
  }
}
```

BPMN type (`bpmn:StartEvent`) comes from the `core.trigger.manual` entry in `definitions[]` — never on the instance. Instance-specific identity (`entryPointId`, and `isDefaultEntryPoint` for subflow triggers) lives under `inputs` — see [file-format.md — Instance-specific identity fields](../../../../shared/file-format.md#instance-specific-identity-fields).

## Replacing Manual Trigger with Scheduled

To switch a flow from manual to scheduled start, use the Edit/Write recipe [Replace manual trigger with scheduled trigger](../../editing-operations-json.md#replace-manual-trigger-with-scheduled-trigger). The scheduled-trigger node-specific `inputs` are in [scheduled-trigger/impl.md](../scheduled-trigger/impl.md).

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Two triggers in flow | Both manual and scheduled (or a connector) trigger exist | Remove one — flows must have exactly one trigger |
| Missing `entryPointId` | Trigger instance has no `inputs.entryPointId` | Add a stable UUID at `inputs.entryPointId` |
| Trigger not first | Manual trigger wired downstream of another node | The trigger must be the topology's first node |

<!-- PHASE 1: append `## Definition — core.trigger.manual v1.0 (copy verbatim)` section here -->
