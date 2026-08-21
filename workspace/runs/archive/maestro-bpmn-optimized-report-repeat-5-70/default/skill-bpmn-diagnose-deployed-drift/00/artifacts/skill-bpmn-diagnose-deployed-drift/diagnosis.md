# BPMN Deployed-vs-Local Drift Diagnosis

**Instance:** inst-triage-001  
**Folder:** folder-public  
**Deployed version:** 3  

## Finding

DRIFTED_ELEMENT: Flow_HighValue
DRIFT: deployed-differs-from-local

## Details

The sequence flow `Flow_HighValue` (gateway `Gw_Value` → task `Task_HighValue`) carries a
`conditionExpression` that determines when an order is routed to high-value handling.

| Side | Condition |
|------|-----------|
| **Deployed (ran)** | `=vars.amount > 500` |
| **Local source** | `=vars.amount > 5000` |

The deployed asset used a threshold of **500**, while the local file specifies **5000**.
As a result, any order with an `amount` between 501 and 5000 was incorrectly routed to
the high-value handling path during the run, instead of following the standard handling
path as the local definition intends.
