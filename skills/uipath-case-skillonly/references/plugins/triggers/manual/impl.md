# Manual Trigger — Implementation

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

Connect it to the first stage with a `TriggerEdge`:

```json
{
  "id": "edge_<6chars>",
  "source": "trigger_<6chars>",
  "target": "Stage_<6chars>",
  "sourceHandle": "trigger_<6chars>____source____right",
  "targetHandle": "Stage_<6chars>____target____left",
  "data": {},
  "type": "case-management:TriggerEdge"
}
```

> For multiple entry points, add additional trigger nodes with separate TriggerEdge connections to their respective first stages.
