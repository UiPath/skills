# Diagnosis: OrderRouting drift

DRIFTED_ELEMENT: Flow_HighValue
DRIFT: deployed-differs-from-local

## Notes

Fetched the deployed BPMN asset for instance `inst-triage-001` in folder
`folder-public` via `uip maestro bpmn instance asset inst-triage-001 -f
folder-public --output json` (deployedVersion 3) and compared it
element-by-element against the local `OrderRouting.bpmn`.

All other elements (start event `Start_Order`, exclusive gateway `Gw_Value`,
tasks `Task_HighValue`/`Task_Standard`, and the other sequence flows) match
between deployed and local.

The sequence flow `Flow_HighValue` (Gw_Value → Task_HighValue) has a different
`conditionExpression` on each side:

- **Local:** `=vars.amount &gt; 5000`
- **Deployed:** `=vars.amount &gt; 500`

The deployed process routes orders over 500 into the high-value handling path,
while the local source only routes orders over 5000 that way — an order-of-
magnitude difference in the routing threshold that explains why the deployed
instance behaved differently from what the local file implies.
