# Drift Diagnosis: OrderRouting.bpmn

## Summary

The deployed BPMN asset (instance `inst-triage-001`, deployed version 3) was
compared element-by-element against the local `OrderRouting.bpmn`. One element
has a differing definition.

DRIFTED_ELEMENT: Flow_HighValue
DRIFT: deployed-differs-from-local

## Detail

The sequence flow `Flow_HighValue` carries the condition that routes high-value
orders to the `Task_HighValue` branch of the exclusive gateway `Gw_Value`.

| Side     | `conditionExpression` value              |
|----------|------------------------------------------|
| Local    | `=vars.amount > 5000`                    |
| Deployed | `=vars.amount > 500`                     |

The deployed asset uses a threshold of **500**, while the local source file
specifies **5000**. Any order with an `amount` between 501 and 5000 (inclusive)
would be routed to the high-value handler in the deployed run, whereas the local
definition would route those same orders through the standard handler. This
explains why the instance behaved differently from what the local file implies.
