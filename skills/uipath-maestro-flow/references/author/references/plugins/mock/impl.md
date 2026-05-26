# Mock — Implementation

## Node Type

`core.logic.mock`

## Registry Validation

```bash
uip maestro flow registry get core.logic.mock --output json
```

Confirm: input port `input`, output port `output`, no required inputs. Definition version `1.0`.

## JSON Structure

```json
{
  "id": "<nodeId>",
  "type": "core.logic.mock",
  "typeVersion": "1.0",
  "display": { "label": "<Placeholder Label>" },
  "inputs": {},
  "outputs": {
    "output": {
      "type": "object",
      "description": "Mock output value",
      "source": "=result.response",
      "var": "output"
    }
  }
}
```

BPMN type (`bpmn:Task`) comes from the `core.logic.mock` entry in `definitions[]` — never on the instance.

## Adding and Editing

A mock uses the standard `input` port and `output` port; no plugin-specific wiring. For add / delete / wire procedures see [editing-operations.md](../../editing-operations.md) and the JSON recipes in [editing-operations-json.md](../../editing-operations-json.md).

## Replacing a Mock with a Real Node

When the resource becomes available, swap the mock for the real resource node: [Replace a mock with a real resource node](../../editing-operations-json.md#replace-a-mock-with-a-real-resource-node). Discovery and decision steps are in [planning.md](planning.md).

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Mock left at publish | Placeholder never resolved | Replace with the real resource node, or confirm with the user it is intentional and note it in Open Questions |
| `$vars.<mockId>.output` is empty downstream | Mock emits only a placeholder object | Expected — wire real logic once the mock is replaced |
| Mock used where a sibling resource exists | Should have used `--local` discovery | Replace with the in-solution resource node ([planning.md](planning.md)) |

<!-- PHASE 1: append `## Definition — core.logic.mock v1.0 (copy verbatim)` section here -->
