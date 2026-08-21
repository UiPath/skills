# BPMN Drift Diagnosis

**Instance:** inst-triage-001  
**Folder:** folder-public  
**Deployed version:** 3

## Result

DRIFTED_ELEMENT: Flow_HighValue
DRIFT: deployed-differs-from-local

## Details

The sequence flow `Flow_HighValue` carries the condition expression that routes
orders to the high-value handling task. Its threshold differs between the two
versions:

| Side     | `conditionExpression`                             |
|----------|---------------------------------------------------|
| Local    | `=vars.amount > 5000`                             |
| Deployed | `=vars.amount > 500`                              |

The deployed version uses a threshold of **500**, whereas the local source
defines a threshold of **5000**. As a result, the deployed process routes any
order above 500 to the high-value path instead of only those above 5000,
causing significantly more orders to be handled as "high-value" than the local
definition intends.
