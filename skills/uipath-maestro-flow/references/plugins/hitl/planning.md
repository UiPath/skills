# HITL Node — Planning

The flow needs to pause for a human to review, approve, or fill in data. Two node types serve this need — choose based on form complexity and whether an app already exists.

---

## Which HITL Node to Use

| Use case | Node type | Form source |
| --- | --- | --- |
| Inline form designed right now (fields + outcomes defined in the flow) | `uipath.human-in-the-loop` | Schema embedded in node inputs — no app needed |
| Existing coded app or Action Center app | `uipath.core.human-task.{key}` | Deployed app from Orchestrator |

**Prefer `uipath.human-in-the-loop`** for new flows. It is an OOTB node — no registry discovery, no app publishing, no tenant dependency.

---

## Option 1 — `uipath.human-in-the-loop` (Inline Schema — OOTB)

Node type: `uipath.human-in-the-loop`
Available: always — no `uip login` or registry pull required.

### When to Select

| Situation | Select? |
| --- | --- |
| Manager approval before processing | Yes |
| Human reviews extracted data before submission | Yes |
| Human resolves exceptions the automation cannot handle | Yes |
| Need a quick form with specific fields and outcomes | Yes |
| Existing coded/Action Center app should be used | No — use Option 2 |
| Fully automated processing, no human involvement | No |

### Ports

| Input port | Output port |
| --- | --- |
| `input` | `completed` |

**The output port must be wired.** A node with no edge on `completed` blocks the flow indefinitely.

### Output Variables

- `$vars.{nodeId}.result` — object containing all output and inOut fields the human filled in
- `$vars.{nodeId}.result.{fieldName}` — individual field value
- `$vars.{nodeId}.status` — `"completed"`

### Schema Design

The schema defines what the human sees and provides. Three field categories:

| Category | Human can… | Use for |
| --- | --- | --- |
| `inputs` | Read only | Context the human needs to decide |
| `outputs` | Write | Data the automation needs back |
| `inOuts` | Read + modify | Fields the human can see and optionally correct |

Outcomes are the action buttons (e.g., Approve/Reject). First outcome is primary.

**In the architectural plan**, describe the schema:
```
inputs:   [invoiceId (string), amount (number)]
outputs:  [decision (string, required)]
outcomes: [Approve, Reject]
priority: normal
```

Full JSON format and conversion examples: see [`uipath-human-in-the-loop` skill](../../../../uipath-human-in-the-loop/references/hitl-node-quickform.md).

> **Note:** Skills are self-contained — cross-skill references are for documentation context only. The agent uses the `uipath-human-in-the-loop` skill to implement HITL nodes; this planning guide is for topology selection only.

### Wiring Pattern

```
[Upstream] -> [HITL] ->|completed| [Continue]
```

### Common Topology Patterns

**Approval gate:**
```
Trigger -> Fetch Data -> HITL (review) ->|completed| Decision (approved?) ->
  true: Script (process) -> End
  false: Script (log rejection) -> End
```

**Exception escalation:**
```
Trigger -> Process -> Decision (confidence ok?) ->
  true: Continue -> End
  false: HITL (exception review) ->|completed| Script (retry with human input) -> End
```

### Planning Annotation

In the node table:
```
| hitlReview | Invoice Review | human-task | uipath.human-in-the-loop | inputs: [invoiceId, amount] outputs: [decision] outcomes: [Approve, Reject] | result, status |
```

---

## Option 2 — `uipath.core.human-task.{key}` (App-Based)

Node type: `uipath.core.human-task.{key}`
Available: tenant-specific resource — requires `uip login` + `uip flow registry pull`.

### When to Select

Use when there is an existing coded app or Action Center app that should be the task form.

### Ports

| Input port | Output port |
| --- | --- |
| `input` | `output` |

### Output Variables

- `$vars.{nodeId}.output` — form data submitted by the user
- `$vars.{nodeId}.error` — error details if execution fails

### Discovery

**Published (tenant registry):**

```bash
uip flow registry pull --force
uip flow registry search "uipath.core.human-task" --output json
```

**In-solution (local, no login required):**

```bash
uip flow registry list --local --output json
uip flow registry get "<nodeType>" --local --output json
```

Run from inside the flow project directory. Discovers sibling projects in the same `.uipx` solution.

### Planning Annotation

- If the app exists: note as `resource: <name> (human-task)`
- If it does not exist: note as `[CREATE NEW] <description>` with skill `uipath-coded-apps`, use `core.logic.mock` placeholder
