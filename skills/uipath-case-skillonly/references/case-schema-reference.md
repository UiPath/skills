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

## Task Output Fields

```json
{
  "name": "AnomalyCheck",
  "displayName": "AnomalyCheck",
  "value": "anomalyCheck",
  "type": "string",
  "source": "=AnomalyCheck",
  "var": "anomalyCheck",
  "id": "anomalyCheck",
  "target": "=anomalyCheck",
  "elementId": "Stage_intake-tAnomalyXX"
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `name` | ✓ | Output field name from the task/process |
| `displayName` | ✓ | Display label (usually same as `name`) |
| `value` | ✓ | Variable ID to store the value |
| `type` | ✓ | Data type: `string`, `number`, `boolean`, `jsonSchema`, `file`, `json`, `any` |
| `source` | ✓ | Expression reading from task response: `=<fieldName>` |
| `var` | ✓ | Global variable ID (must be unique across case) |
| `id` | ✓ | Same as `var` |
| `target` | optional | Expression for write target: `=<varId>` |
| `elementId` | ✓ | `<stageId>-<taskId>` |
| `_jsonSchema` | optional | JSON schema body (for `type: "jsonSchema"`) |
| `body` | optional | Alias for `_jsonSchema` — FE emits both |
| `custom` | optional | `true` if this is a user-defined constant output (not from task response) |
| `canonicalId` | optional | FE-generated disambiguation ID — omit when writing |
| `description` | optional | Human-readable description |

### FE-Generated Fields (Omit When Writing)

These fields are added by the FE but not required for validation or execution:

| Field | Purpose |
|-------|---------|
| `canonicalId` | Disambiguates outputs when the same `name` appears multiple times across tasks |
| `body` | Duplicate of `_jsonSchema` — FE emits both for compat |

---

## Plugin Navigation

Load plugins on demand as you build each feature. Do not load all plugins upfront.

### Setup (load these first)
| What you are building | Plugin |
|---|---|
| New case project + root JSON skeleton | [plugins/setup/case-skeleton](plugins/setup/case-skeleton/impl.md) |
| Any stage node | [plugins/setup/stage](plugins/setup/stage/impl.md) |
| Any task (common fields, lane convention) | [plugins/setup/task](plugins/setup/task/impl.md) |
| Any edge | [plugins/setup/edge](plugins/setup/edge/impl.md) |

### Tasks
| Task type | Plugin |
|---|---|
| `process` | [plugins/tasks/process](plugins/tasks/process/planning.md) |
| `agent` | [plugins/tasks/agent](plugins/tasks/agent/planning.md) |
| `rpa` | [plugins/tasks/rpa](plugins/tasks/rpa/planning.md) |
| `api-workflow` | [plugins/tasks/api-workflow](plugins/tasks/api-workflow/planning.md) |
| `case-management` | [plugins/tasks/case-management](plugins/tasks/case-management/planning.md) |
| `action` | [plugins/tasks/action](plugins/tasks/action/planning.md) |
| `wait-for-timer` | [plugins/tasks/timer](plugins/tasks/timer/planning.md) |
| `execute-connector-activity` | [plugins/tasks/execute-connector-activity](plugins/tasks/execute-connector-activity/planning.md) |
| `wait-for-connector` | [plugins/tasks/wait-for-connector](plugins/tasks/wait-for-connector/planning.md) |
| `external-agent` | [plugins/tasks/external-agent](plugins/tasks/external-agent/planning.md) |

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
| Wait for connector event | [plugins/conditions/wait-for-connector](plugins/conditions/wait-for-connector/planning.md) |

### SLA
| What you are building | Plugin |
|---|---|
| Deadlines and escalation notifications | [plugins/sla/setup](plugins/sla/setup/planning.md) |

### Variables
| What you are building | Plugin |
|---|---|
| Process / app resource references in tasks | [plugins/variables/bindings](plugins/variables/bindings/impl.md) |
| Case-level input / output variables | [plugins/variables/global-vars](plugins/variables/global-vars/planning.md) |
