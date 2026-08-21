# Diagnosis: OrderRouting BPMN Deployed vs Local Drift

## Method

- Local source reviewed: `OrderRouting.bpmn` (working directory).
- Deployed asset fetched via CLI (not read from any mock/fixture file):
  `uip maestro bpmn instance asset inst-triage-001 -f folder-public --output json`
  → reports `deployedVersion: 3`.
- Compared the two `<bpmn:definitions>` trees element-by-element (start event,
  gateway, tasks, end event, and all sequence flows including condition
  expressions).

## Result

DRIFTED_ELEMENT: Flow_HighValue
DRIFT: deployed-differs-from-local

## Details

The sequence flow `Flow_HighValue` (the `Gw_Value` → `Task_HighValue` branch,
guarding the "high-value" routing path) carries a different
`conditionExpression` on each side:

- **Local** (`OrderRouting.bpmn`): `=vars.amount &gt; 5000`
- **Deployed** (instance `inst-triage-001`, folder `folder-public`, version 3):
  `=vars.amount &gt; 500`

Everything else that is present in both definitions (start event `Start_Order`,
gateway `Gw_Value` with its `default="Flow_Standard"`, task ids/names
`Task_HighValue`/`Task_Standard`, and the `Flow_Standard` flow) matches
between local and deployed.

## Impact

Because the deployed threshold is `500` instead of the intended `5000`, orders
with an amount between 500 and 5000 are routed to the high-value handling path
in production even though the local source says they should be treated as
standard orders. This one-digit threshold drift (missing a trailing zero)
explains the instance behaving differently from what the local source
suggests.
