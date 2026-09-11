# HITL Node — Planning

The flow needs to pause for a human to review, approve, or fill in data. Two node types serve this need — choose based on form complexity and whether an app already exists.

---

## Which HITL Node to Use

| Use case | Node type | Form source |
| --- | --- | --- |
| Inline form designed right now (fields + outcomes defined in the flow) | `uipath.human-in-the-loop.quick-form` | Schema embedded in node inputs — no app needed |
| Existing coded app or Action Center app | `uipath.human-in-the-loop.coded-action-app` | Deployed app from Orchestrator |

**Prefer `uipath.human-in-the-loop.quick-form`** for new flows. It is an OOTB node — no registry discovery, no app publishing, no tenant dependency.

---

## Option 1 — `uipath.human-in-the-loop.quick-form` (Inline Schema — OOTB)

Node type: `uipath.human-in-the-loop.quick-form`
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
| The user wants to **see** a value the flow produced | Only if a human will open the task — see below |

**A HITL node blocks until a human completes its task, so place one only where a human actually will.** The task appears in Action Center; if it has no assignee, or the run is unattended (a schedule, a `flow debug`, an eval), nobody opens it and the flow never reaches its End node. The instance stays `Running` until the caller's timeout, with no output. Every outcome port can be wired correctly and this still happens, so it does not present as the unwired-port failure below.

**"Show me the result" does not by itself mean a form.** The mechanisms differ in who can consume them, so ask what *seeing it* means before choosing:

| Mechanism | Reaches | Completes unattended |
| --- | --- | --- |
| HITL form | a person who opens Action Center | No — blocks until submitted |
| Message to a channel or mailbox (connector node) | a person wherever they already are | Yes |
| `out` variable mapped on the End node | whoever or whatever invoked the flow | Yes |

With no user to ask, pick one that terminates unattended and record which you chose and why. Do not reach for a form because the request said "display" — that word describes the goal, not the node.

### Ports

| Input port | Output port(s) |
| --- | --- |
| `input` | one per outcome — `outcome-<outcome.id>`, derived verbatim from `inputs.schema.outcomes[].id` |

**Every outcome gets its own port — wire one edge per outcome, not a single shared port.** A schema with `outcomes: [Approve, Reject]` (ids `approve`, `reject`) produces two ports, `outcome-approve` and `outcome-reject`; each needs its own edge. Every outcome needs a non-empty string `id` — one without gets no handle at all, so an edge drawn to a guessed port name is a no-op, not a working branch. A node with any outcome port left unwired blocks the flow indefinitely on that branch.

> **`outcome-completed` is the port for a zero-outcome node, or for a real outcome whose `id` is literally `completed`.** It is an ordinary string, not a reserved one, so it can be a genuine outcome port. The instant `inputs.schema.outcomes` has one or more entries with a different `id` — including the shipped default `Submit` (id `submit`) — its port becomes `outcome-submit`, not `outcome-completed`. Never wire `outcome-completed` standing in for several different outcomes.

### Output Variables

- `$vars.{nodeId}.output` — object containing all output and inOut fields the human filled in
- `$vars.{nodeId}.output.{fieldName}` — individual field value
- `$vars.{nodeId}.status` — selected outcome's action value (`"Continue"` or `"End"`)

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
priority: Low
```

Full JSON format and conversion examples: see [`uipath-human-in-the-loop` skill](../../../../../uipath-human-in-the-loop/references/hitl-node-quickform.md).

> **Note:** Skills are self-contained — cross-skill references are for documentation context only. The agent uses the `uipath-human-in-the-loop` skill to implement HITL nodes; this planning guide is for topology selection only.

### Wiring Pattern

```
[Upstream] -> [HITL] ->|outcome-approve| [Continue]
                ->|outcome-reject| [End]
```

Each outcome branches directly off its own handle — no separate Decision node needed to re-derive the branch from `$vars.{nodeId}.status`.

### Common Topology Patterns

**Approval gate:**
```
Trigger -> Fetch Data -> HITL (review, outcomes: Approve/Reject) ->
  outcome-approve: Script (process) -> End
  outcome-reject: Script (log rejection) -> End
```

**Exception escalation:**
```
Trigger -> Process -> Decision (confidence ok?) ->
  true: Continue -> End
  false: HITL (exception review, outcomes: Retry/Escalate) ->
    outcome-retry: Script (retry with human input) -> End
    outcome-escalate: End
```

**Do not insert a Decision node after a HITL node to re-branch on outcome.** Each outcome already has its own wired handle — that handle IS the branch point. Reach for a Decision node only where the branch is on something other than the HITL outcome itself (e.g., the confidence check above, which runs before any HITL node).

### Planning Annotation

In the node table:
```
| hitlReview | Invoice Review | human-task | uipath.human-in-the-loop.quick-form | inputs: [invoiceId, amount] outputs: [decision] outcomes: [Approve, Reject] | output, status |
```

---

## Option 2 — `uipath.core.human-task.{key}` (App-Based)

Node type: `uipath.core.human-task.{key}`
Available: tenant-specific resource — requires `uip login` + `uip maestro flow registry pull`.

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
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.core.human-task" --output json
```

**In-solution (local, no login required):**

```bash
uip maestro flow registry list --local --output json
uip maestro flow registry get "<node-type>" --local --output json
```

Run from inside the flow project directory. Discovers sibling projects in the same `.uipx` solution.

### Planning Annotation

- If the app exists: note as `resource: <name> (human-task)`
- If it does not exist: note as `[CREATE NEW] <description>` with skill `uipath-coded-apps`, use `core.logic.mock` placeholder
