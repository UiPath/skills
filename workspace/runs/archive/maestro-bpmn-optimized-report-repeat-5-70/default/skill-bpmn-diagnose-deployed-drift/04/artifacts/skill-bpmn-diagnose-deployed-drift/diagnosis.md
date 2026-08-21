# Diagnosis: OrderRouting Deployed vs Local BPMN Drift

DRIFTED_ELEMENT: Flow_HighValue
DRIFT: deployed-differs-from-local

## Description

The sequence flow `Flow_HighValue` (from `Gw_Value` to `Task_HighValue`) carries a
`conditionExpression` that differs between the two versions:

- **Local (`OrderRouting.bpmn`):** `=vars.amount > 5000`
- **Deployed (instance `inst-triage-001`, version 3):** `=vars.amount > 500`

The deployed version has a threshold of **500**, while the local source has **5000**.
This means the deployed process routes any order above 500 to the high-value handling
path, whereas the local definition only routes orders above 5000 there. Any order
with an amount between 501 and 5000 would be treated as high-value at runtime but
as standard in the local source, explaining the behavioral mismatch.
