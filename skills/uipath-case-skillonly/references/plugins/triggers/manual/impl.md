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

## Multiple Triggers — Same or Different First Stage

A case can have any number of trigger nodes. Each is connected to *exactly one* stage via a TriggerEdge, but multiple TriggerEdges may **converge on the same stage**. This represents distinct entry points (e.g., manual + webhook + scheduled) that all start the same workflow.

```json
// Manual trigger
{ "id": "trigger_aaa111", "type": "case-management:Trigger",
  "position": {"x": 0, "y": 0},
  "data": {"label": "Started manually"} },

// Webhook trigger (start event from connector trigger or external system)
{ "id": "StartEvent_Trigger_bbb222", "type": "case-management:Trigger",
  "position": {"x": 0, "y": 200},
  "data": {"label": "Started by webhook"} }
```

```json
// Both edges target the SAME stage — case-1 runs whichever trigger fires first
{ "id": "edge_xxxxxx", "source": "trigger_aaa111", "target": "Stage_intake",
  "sourceHandle": "trigger_aaa111____source____right",
  "targetHandle": "Stage_intake____target____left",
  "data": {}, "type": "case-management:TriggerEdge" },
{ "id": "edge_yyyyyy", "source": "StartEvent_Trigger_bbb222", "target": "Stage_intake",
  "sourceHandle": "StartEvent_Trigger_bbb222____source____right",
  "targetHandle": "Stage_intake____target____left",
  "data": {}, "type": "case-management:TriggerEdge" }
```

**Layout convention:** stack triggers vertically on the left. Manual trigger at `y: 0`, second trigger at `y: 200`, third at `y: 400`, etc. All trigger edges enter their target stage on its `left` handle (regardless of source trigger position).

For non-manual triggers (timer, connector event), see `plugins/triggers/timer` and `plugins/triggers/connector-trigger`.
