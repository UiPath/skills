# <Process name> — BPMN Solution Design Document

## 1. Process identity

| Field | Value |
| --- | --- |
| Process name | <Human-readable name> |
| Logical process ID | `<stable-kebab-id>` |
| Business objective | <Outcome the process delivers> |
| Scope | <Included and excluded work> |
| Implementation readiness | `Reviewable` \| `Executable` \| `Blocked` |

## 2. Participants and triggers

| Logical ID | Participant or trigger | Role in the process | Input or event |
| --- | --- | --- | --- |
| `<participant-id>` | <person, system, or lane> | <responsibility> | <what starts or informs work> |

State the start trigger, its payload, and whether the process is manually,
message, timer, or event initiated.

## 3. Process graph

### Nodes

Use stable logical IDs. A logical ID is the future BPMN element identity, not a
display label or registry key.

| Logical ID | BPMN kind | Name | Inputs | Outputs | Resource intent |
| --- | --- | --- | --- | --- | --- |
| `<node-id>` | <start event, task, gateway, event, subprocess, end event> | <display name> | <variables or event payload> | <variables or event payload> | <none or resource-intent-id> |

### Sequence flows

| Logical flow ID | From node | To node | Condition | Default path |
| --- | --- | --- | --- | --- |
| `<flow-id>` | `<source-node-id>` | `<target-node-id>` | <condition or `Always`> | `Yes` \| `No` |

Every gateway outgoing flow has either a condition or an explicit default path.
A default flow is unconditional (`Always`); it never also carries a condition.

## 4. Data and variables

| Variable ID | Type | Scope | Source | Consumers | Purpose |
| --- | --- | --- | --- | --- | --- |
| `<variable-id>` | <string, number, boolean, object, array> | <process or subprocess ID> | <trigger or node ID> | <node, event, or condition-flow IDs> | <meaning> |

Record event payloads, error data, and any variable whose producer or consumer
is outside the main sequence flow.

## 5. Events, subprocesses, and loops

| Logical ID | Structure | Attachment or parent | Trigger or iteration rule | Exit behavior |
| --- | --- | --- | --- | --- |
| `<structure-id>` | <boundary event, event subprocess, embedded subprocess, loop> | <node or process ID> | <event or collection rule> | <continue, interrupt, retry, terminate> |

Write `None` when this process has no exception event, subprocess, or loop.

## 6. Resource intent

Describe only the business intent needed for later registry discovery. Do not
place registry payloads, candidate lists, or diagram coordinates in this SDD.

| Resource intent ID | Used by node | Intended capability | Intended resource name | Connection or folder intent | Required | Resolution |
| --- | --- | --- | --- | --- | --- | --- |
| `<resource-intent-id>` | `<node-id>` | <human review, API, RPA, agent, connector> | <known name or `UNRESOLVED`> | <known path/name or `UNRESOLVED`> | `Yes` \| `No` | `Resolved` \| `UNRESOLVED` |

## 7. Exception and event behavior

For every exception, describe its source, event or condition, affected node,
and recovery or terminal path. Include explicit business error outcomes that
must be visible to a caller.

## 8. Implementation readiness

| Check | Status | Evidence or blocker |
| --- | --- | --- |
| Graph is complete | <Ready or blocker> | <start/end, flow, and gateway review> |
| Variable lineage is complete | <Ready or blocker> | <producer and consumer review> |
| Required resources are resolved | <Ready or blocker> | <resource intent IDs> |
| Executable BPMN may be authored | <Yes or No> | <reason> |

Required unresolved resources may remain in a reviewable SDD. They make the
implementation readiness `Blocked` and prevent executable BPMN authoring until
the registry resolves them.
