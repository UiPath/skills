# BPMN Drift Diagnosis

**Instance:** inst-triage-001  
**Folder:** folder-public  
**Deployed Version:** 3

## Result

DRIFTED_ELEMENT: Flow_HighValue
DRIFT: deployed-differs-from-local

## How the Deployed Definition Differs from Local

The sequence flow `Flow_HighValue` carries a `conditionExpression` that routes orders to the high-value handling task. The two sides disagree on the numeric threshold:

- **Local** (`OrderRouting.bpmn`): `=vars.amount > 5000`
- **Deployed** (version 3, fetched via `uip maestro bpmn instance asset`): `=vars.amount > 500`

The deployed asset uses a threshold of **500** instead of the locally-authored **5000**. As a result, any order with an `amount` between 501 and 5000 (inclusive) was routed to the high-value handling path during execution, whereas the local definition would have sent those same orders down the standard handling path. This single digit difference (one fewer zero) is the root cause of the behavioral drift observed in the instance.
