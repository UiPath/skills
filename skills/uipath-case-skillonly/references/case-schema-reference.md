# Case Management JSON Schema Reference (v16)

Structural skeleton reference for `caseplan.json`. For feature-specific configuration, load the relevant plugin from the navigation table below.

---

## Top-Level Structure

```json
{
  "root":  { ... },
  "nodes": [ ... ],
  "edges": [ ... ]
}
```

- **`root`** — case metadata, SLA rules, global variables, bindings, case exit conditions
- **`nodes`** — all trigger, stage, and exception stage nodes
- **`edges`** — connections between nodes

---

## ID Generation Conventions

All IDs use cryptographically random alphanumeric characters (`A-Za-z0-9`).

| Element | Prefix | Char count | Example |
|---|---|---|---|
| Root | `"root"` | fixed | `root` |
| Stage / ExceptionStage | `Stage_` | 6 | `Stage_zlZulP` |
| Trigger | `trigger_` | 6 | `trigger_aB3cD4` |
| Task | `t` | **8** | `t9nayawCu` |
| Edge | `edge_` | 6 | `edge_9bzKc2` |
| Condition | `Condition_` | 6 | `Condition_SqgWT0` |
| Rule | `Rule_` | 6 | `Rule_iQF8aX` |
| Escalation | `esc_` | 6 | `esc_FIWwCn` |
| Binding | `b` | **8** | `bCiT7IgAE` |
| elementId | `<stageId>-<taskId>` | — | `Stage_f95rff-t9nayawCu` |

---

## Root Node

```json
{
  "id": "root",
  "name": "<Case Name>",
  "type": "case-management:root",
  "caseIdentifier": "<identifier>",
  "caseIdentifierType": "constant",
  "caseAppEnabled": false,
  "version": "v16",
  "description": "<optional>",
  "data": {
    "uipath": {
      "bindings": [],
      "variables": {}
    },
    "slaRules": []
  },
  "caseExitConditions": []
}
```

| Field | Notes |
|---|---|
| `caseIdentifierType` | `"constant"` (fixed string) or `"external"` (resolved at runtime) |
| `data.uipath.bindings` | See → [plugins/variables/bindings](plugins/variables/bindings/impl.md) |
| `data.uipath.variables` | See → [plugins/variables/global-vars](plugins/variables/global-vars/impl.md) |
| `data.slaRules` | See → [plugins/sla/setup](plugins/sla/setup/impl.md) |
| `caseExitConditions` | See → [plugins/conditions/case-exit](plugins/conditions/case-exit/impl.md) |

---

## Stage / ExceptionStage Node Skeleton

```json
{
  "id": "Stage_<6chars>",
  "type": "case-management:Stage",
  "position": { "x": 100, "y": 200 },
  "style": { "width": 304, "opacity": 0.8 },
  "measured": { "width": 304, "height": 128 },
  "width": 304,
  "zIndex": 1001,
  "data": {
    "label": "<Stage Name>",
    "parentElement": { "id": "root", "type": "case-management:root" },
    "isInvalidDropTarget": false,
    "isPendingParent": false,
    "description": "<optional>",
    "isRequired": true,
    "tasks": [],
    "entryConditions": [],
    "exitConditions": [],
    "slaRules": []
  }
}
```

**Position layout:** start first stage at `x: 100`, increment `x` by ~500 per stage. Keep `y: 200` for all main-flow stages.

For `ExceptionStage`: change `type` to `"case-management:ExceptionStage"`. See → [plugins/stage-types/exception-stage](plugins/stage-types/exception-stage/impl.md).

---

## Trigger Node Skeleton

```json
{
  "id": "trigger_<6chars>",
  "type": "case-management:Trigger",
  "position": { "x": 0, "y": 0 },
  "data": { "label": "Trigger 1" }
}
```

For timer or event triggers, see → [plugins/triggers/timer](plugins/triggers/timer/impl.md).

---

## Edges

| Edge type | When to use |
|---|---|
| `case-management:TriggerEdge` | Source is a Trigger node |
| `case-management:Edge` | Source is a Stage node |

**Handle format:** `<nodeId>____source____<direction>` / `<nodeId>____target____<direction>`

Directions: `right`, `left`, `top`, `bottom`. Standard layout uses `right` → `left`. Exception stages branch vertically using `bottom` → `top`.

```json
{
  "id": "edge_<6chars>",
  "source": "<sourceNodeId>",
  "target": "<targetNodeId>",
  "sourceHandle": "<sourceNodeId>____source____right",
  "targetHandle": "<targetNodeId>____target____left",
  "data": {},
  "type": "case-management:TriggerEdge"
}
```

---

## Plugin Navigation

Load plugins on demand as you build each feature. Do not load all plugins upfront.

### Tasks
| What you are building | Plugin |
|---|---|
| Automation task (process / agent / rpa / api-workflow / case-management) | [plugins/tasks/standard-io](plugins/tasks/standard-io/planning.md) |
| Human-in-the-loop action task | [plugins/tasks/action](plugins/tasks/action/planning.md) |
| Timer / delay task | [plugins/tasks/timer](plugins/tasks/timer/planning.md) |
| Connector task (wait-for-connector / execute-connector-activity / external-agent) | [plugins/tasks/connector-activity](plugins/tasks/connector-activity/planning.md) |

### Triggers
| What you are building | Plugin |
|---|---|
| Manual case trigger | [plugins/triggers/manual](plugins/triggers/manual/impl.md) |
| Scheduled timer trigger | [plugins/triggers/timer](plugins/triggers/timer/planning.md) |
| Connector event trigger | [plugins/triggers/connector-trigger](plugins/triggers/connector-trigger/planning.md) |

### Stage Types
| What you are building | Plugin |
|---|---|
| Exception / error handler stage | [plugins/stage-types/exception-stage](plugins/stage-types/exception-stage/planning.md) |

### Conditions
| What you are building | Plugin |
|---|---|
| When a stage becomes active | [plugins/conditions/stage-entry](plugins/conditions/stage-entry/planning.md) |
| When a stage completes | [plugins/conditions/stage-exit](plugins/conditions/stage-exit/planning.md) |
| When a task within a stage triggers | [plugins/conditions/task-entry](plugins/conditions/task-entry/planning.md) |
| When the case ends | [plugins/conditions/case-exit](plugins/conditions/case-exit/impl.md) |

### SLA
| What you are building | Plugin |
|---|---|
| Deadlines and escalation notifications | [plugins/sla/setup](plugins/sla/setup/planning.md) |

### Variables
| What you are building | Plugin |
|---|---|
| Process / app resource references in tasks | [plugins/variables/bindings](plugins/variables/bindings/impl.md) |
| Case-level input / output variables | [plugins/variables/global-vars](plugins/variables/global-vars/planning.md) |
