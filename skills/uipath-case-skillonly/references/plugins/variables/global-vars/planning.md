# Global Variables — Planning

Global variables store data that is passed into the case, shared between stages, or returned as case output.

## When to Use Global Variables

| Situation | Use global var? |
|---|---|
| Pass input data to the case at start (e.g., claim ID, customer ID) | Yes — `inputs` |
| Share data produced by one stage with a later stage (e.g., risk score) | Yes — `inputOutputs` |
| Return case results to the caller when the case ends | Yes — `outputs` |
| Task needs data only from its own execution | No — keep in task outputs only |

## Variable Category Selection

| Category | `variables` key | Use when |
|---|---|---|
| Data provided **to** the case from outside | `inputs` | Initialised externally before the case starts |
| Data **produced** by the case for external consumption | `outputs` | Read by the caller after the case ends |
| Data shared **within** the case between stages | `inputOutputs` | Read and written by multiple stages |

## Variable Type Values

| Type | When |
|---|---|
| `"string"` | Text values |
| `"number"` | Numeric values |
| `"boolean"` | True/false flags |
| `"object"` | Structured data (no schema) |
| `"jsonSchema"` | Structured data with defined schema |

## Naming Convention

Use camelCase for variable IDs. The `id` is the reference key used in expressions (`=vars.claimId`). `name` should match `id`.
