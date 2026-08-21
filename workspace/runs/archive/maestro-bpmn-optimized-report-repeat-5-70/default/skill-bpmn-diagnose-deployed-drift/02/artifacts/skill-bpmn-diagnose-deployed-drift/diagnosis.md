# Drift Diagnosis: OrderRouting — inst-triage-001

## Summary

The deployed BPMN asset (version 3, fetched via `uip maestro bpmn instance asset inst-triage-001 -f folder-public`) differs from the local `OrderRouting.bpmn` in exactly one element.

DRIFTED_ELEMENT: Flow_HighValue
DRIFT: deployed-differs-from-local

## How the deployed definition differs from local

**Element:** `<bpmn:sequenceFlow id="Flow_HighValue">` — the condition expression on the high-value routing branch.

| Side | `conditionExpression` value |
|---|---|
| **Local** (`OrderRouting.bpmn`) | `=vars.amount > 5000` |
| **Deployed** (instance asset v3) | `=vars.amount > 500` |

The deployed asset has a threshold of **500**, while the local source has **5000**. As a result, when the process ran, any order with `amount > 500` was routed to `Task_HighValue` (high-value handling) — a pool ten times broader than what the local definition intends. Orders in the 501–5000 range were incorrectly treated as high-value during that run.
