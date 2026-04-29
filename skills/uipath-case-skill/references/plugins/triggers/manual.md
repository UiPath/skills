# Manual Trigger

A manual trigger is the default case entry point — created for every case. No planning needed.

## JSON

```json
{
  "id": "trigger_<6chars>",
  "type": "case-management:Trigger",
  "position": { "x": 0, "y": 0 },
  "data": {
    "label": "Trigger 1"
  }
}
```

Wire to the first stage with a `TriggerEdge` — see [edge reference](../skeleton/edge.md).

## Multiple Triggers

A case can have any number of trigger nodes. Each connects to exactly one stage, but multiple triggers may **converge on the same stage** (e.g., manual + webhook + scheduled all start the same workflow).

```json
// Manual trigger
{ "id": "trigger_aaa111", "type": "case-management:Trigger",
  "position": {"x": 0, "y": 0},
  "data": {"label": "Started manually"} },

// Webhook trigger
{ "id": "StartEvent_Trigger_bbb222", "type": "case-management:Trigger",
  "position": {"x": 0, "y": 200},
  "data": {"label": "Started by webhook"} }
```

Both edges target the same stage — whichever trigger fires first starts the case. See [edge reference](../skeleton/edge.md) for the `TriggerEdge` format.

**Layout:** stack triggers vertically on the left. Manual at `y: 0`, second at `y: 200`, third at `y: 400`. All trigger edges enter target on `left` handle.

For non-manual triggers, see [timer](timer.md) and [connector trigger](connector-trigger.md).
