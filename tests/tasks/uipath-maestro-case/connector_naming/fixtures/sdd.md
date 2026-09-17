# SDD — ConnectorNaming

## Table of Contents

- [Section 1: Case Definition](#section-1-case-definition)
- [Section 2: Stages & Tasks](#section-2-stages--tasks)
- [Section 3: Personas & App Views](#section-3-personas--app-views)
- [Section 4: Integrations](#section-4-integrations)

---

## Section 1: Case Definition

### Case Metadata

| Property | Value |
|----------|-------|
| Case Name | ConnectorNaming |
| Case Description | Posts a build notice to Slack, then waits for a matching Outlook calendar event. Exercises connector request and response field handling across two connectors. |
| Case Identifier | Type: constant. Constant → Prefix: CN |
| Priority | Choiceset: Low, Medium, High — Default: Medium |
| Case-Level SLA | — |
| SLA Type | time-based |
| Case App | Disabled |
| Task-output passing | Direct |
| Case Identifier source | =metadata.ExternalId |

### Case Triggers

| T# | Type | Detail |
|----|------|--------|
| T01 | manual | Manual start. No trigger parameters. |

### Case Exit Conditions

| WHEN | IF | Marks Case Complete | Display Name |
|------|-----|---------------------|--------------|
| `selected-stage-completed("Naming")` | — | Yes | Case exit rule 1 |

### Case Variables

| Name | Category | Type | sourceTriggers | sourceFields | Default | Description |
|------|----------|------|----------------|--------------|---------|-------------|
| postAppId | Variable | string | | | | Slack app id returned by the post. |
| postTs | Variable | string | | | | Slack message timestamp returned by the post. |
| postThreadTs | Variable | string | | | | Slack thread timestamp returned by the post. |
| postChannel | Variable | string | | | | Slack channel returned by the post. |
| eventId | Variable | string | | | | Identifier of the calendar event that fired the trigger. |
| eventTitle | Variable | string | | | | Subject of the calendar event. |
| eventCalendarName | Variable | string | | | | Calendar the event belongs to. |
| eventHasAttachments | Variable | string | | | | Whether the calendar event carries attachments. |

---

## Section 2: Stages & Tasks

### Stage 1: Naming (`stage_naming`)

#### Stage Entry Conditions

| WHEN | IF | Display Name |
|------|-----|--------------|
| `current-stage-entered` | — | Entry rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Completion | Display Name |
|------|-----|------------|--------------|
| `selected-tasks-completed("Await Calendar Event")` | — | Yes | Exit rule 1 |

#### Stage SLA

—

#### Tasks

| # | Task Name | Type | Activation Mode | Starts When | Required | Run Only Once | Persona | SLA |
|---|-----------|------|-----------------|-------------|----------|---------------|---------|-----|
| 1 | Post Naming Notice | execute-connector-activity | sequential | stage enters | Yes | No | system | — |
| 2 | Await Calendar Event | wait-for-connector | sequential | after Post Naming Notice | Yes | No | system | — |

##### Task 1.1: Post Naming Notice

**Type:** execute-connector-activity
**Activation Mode:** sequential
**Design Rationale:** A connector activity is the only task type that issues an outbound Slack call; sequential because it must complete before the case waits on the calendar event.
**Description:** Posts a build notice to the team Slack channel and captures the message identifiers.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `current-stage-entered` | — | Entry rule 1 |

**Task envelope**

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

**Connector:** Slack · **Connector Key:** `uipath-salesforce-slack`
**Connection:** is-sandboxes · **Connection ID:** `e03f734e-0f80-4e8a-a7c1-0ece309b0ca4`
**Activity Type ID:** `37a305b2-89b1-315d-b73f-1778839a6c47` · **Service Type:** `Intsvc.ActivityExecution`
**Auth Method:** OAuth2
**Account / Endpoint:** —
**Operation:** Send Message to Channel (objectName `send_message_to_channel_v2`)
**Trigger / Event:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| send_as | string | `"bot"` |
| channel | string | `"#general"` |
| messageToSend | string | `"Naming contract check"` |
| link_names | boolean | `"true"` |
| image | string | `"https://example.invalid/build.png"` |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| app_id | -> postAppId |
| ts | -> postTs |
| thread_ts | -> postThreadTs |
| channel | -> postChannel |

##### Task 1.2: Await Calendar Event

**Type:** wait-for-connector
**Activation Mode:** sequential
**Design Rationale:** The case must pause until a matching calendar event arrives; a connector wait is the only task type that suspends on an inbound Integration Service event.
**Description:** Waits for an Outlook calendar event whose subject matches the posted notice, then captures the event identifiers.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `runs-sequentially` | — | Entry rule 1 |

**Task envelope**

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

**Connector:** Microsoft Outlook 365 · **Connector Key:** `uipath-microsoft-outlook365`
**Connection:** is-sandboxes-test@uipathsandboxes.onmicrosoft.com · **Connection ID:** `dd657127-91f5-4568-a3a3-c024bc03fb0f`
**Activity Type ID:** `32b856f3-e7ba-3cb3-9f4b-4c85280315be` · **Service Type:** `Intsvc.WaitForEvent`
**Auth Method:** OAuth2
**Account / Endpoint:** —
**Operation:** Calendar Event Created (objectName `Calendar`, event `CALENDAR_CREATED`)
**Trigger / Event:** Calendar Event Created

**Inputs:** — no event parameters.

**Trigger Filter:**

| Field | Operator | Value |
|-------|----------|-------|
| Title | contains | `Naming contract` |
| HasAttachments | not equals | `true` |
| Attachments[*].MIMEType | contains | `text/` |

Group operator: And.

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| ID | -> eventId |
| Title | -> eventTitle |
| CalendarName | -> eventCalendarName |
| HasAttachments | -> eventHasAttachments |

---

## Section 3: Personas & App Views

### Personas

None — every task is system-executed.

### Process App Views

None — Case App is Disabled.

---

## Section 4: Integrations

### Integration Service Connectors

#### Slack

**Connector Key:** `uipath-salesforce-slack`
**Connection:** is-sandboxes · **Connection ID:** `e03f734e-0f80-4e8a-a7c1-0ece309b0ca4`
**Auth Method:** OAuth2
**Operations used:** Send Message to Channel (Task 1.1)

#### Microsoft Outlook 365

**Connector Key:** `uipath-microsoft-outlook365`
**Connection:** is-sandboxes-test@uipathsandboxes.onmicrosoft.com · **Connection ID:** `dd657127-91f5-4568-a3a3-c024bc03fb0f`
**Auth Method:** OAuth2
**Operations used:** Calendar Event Created trigger (Task 1.2)

### API Workflows

None.

### Agents

None.

### Processes & RPA

None.

### Child Cases

None.

### External Agents

None.

### IXP / Document Understanding Models

None.

### Coded Functions

None.

### Reusable Components

None.
