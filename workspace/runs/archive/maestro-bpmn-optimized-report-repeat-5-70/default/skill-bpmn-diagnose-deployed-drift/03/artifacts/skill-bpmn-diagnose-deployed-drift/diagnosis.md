# Drift Diagnosis: OrderRouting

DRIFTED_ELEMENT: Flow_HighValue
DRIFT: deployed-differs-from-local

## Details

The sequence flow `Flow_HighValue` carries the condition that routes orders to
the high-value handling task (`Task_HighValue`). Its `conditionExpression`
differs between the deployed asset (version 3, fetched via
`uip maestro bpmn instance asset inst-triage-001 -f folder-public`) and the
local `OrderRouting.bpmn`:

| Side     | conditionExpression value          |
|----------|------------------------------------|
| Deployed | `=vars.amount > 500`               |
| Local    | `=vars.amount > 5000`              |

The deployed threshold is **500**, while the local source sets it at **5000**.
Any order with an amount between 501 and 5000 would therefore be routed to
`Task_HighValue` at runtime, even though the local model intends those orders
to fall through to `Task_Standard` via the default flow. This off-by-10×
threshold is the root cause of the observed behavioral difference.
