# SDD — Connector Field-Naming Contract Case

> Purpose: one stage, two connector tasks, whose only job is to exercise
> connector request / response **field-name** fidelity. The activity's contract
> is snake_case; the trigger's contract is PascalCase (capital-first). Every
> field name below is the connector's own, taken verbatim from
> `uip maestro case spec`. The build must reproduce them byte-for-byte.

## Table of Contents

- Section 1: Case Definition
- Section 2: Stages & Tasks
- Section 3: Personas & App Views
- Section 4: Integrations

---

## Section 1: Case Definition

### Case Metadata

| Field | Value |
|---|---|
| Case name | ConnectorNaming |
| Project name | ConnectorNaming |
| Solution name | ConnectorNaming |
| Description | Single-stage connector field-naming contract case. |
| Case identifier type | auto |
| Folder Path | Shared/uipath-maestro-case |

### Case Triggers

| T# | Type | Detail |
|---|---|---|
| T01 | manual | Manual start. No trigger parameters. |

### Case Exit Conditions

| Rule | Marks case complete |
|---|---|
| selected-stage-completed → Stage 1 | true |

### Case Variables

| Name | Category | Type | Default | Source |
|---|---|---|---|---|
| postAppId | Variable | string | — | T02 output `app_id` |
| postTs | Variable | string | — | T02 output `ts` |
| postThreadTs | Variable | string | — | T02 output `thread_ts` |
| postChannel | Variable | string | — | T02 output `channel` |
| eventId | Variable | string | — | T03 output `ID` |
| eventTitle | Variable | string | — | T03 output `Title` |
| eventCalendarName | Variable | string | — | T03 output `CalendarName` |
| eventHasAttachments | Variable | string | — | T03 output `HasAttachments` |

---

## Section 2: Stages & Tasks

### Stage 1: Naming — both contracts in one stage

Entry: case started. Exit: both tasks complete.

#### T02: Add connector-activity task "Post Naming Notice"

**Connector:** Slack · **Connector Key:** `uipath-salesforce-slack`
**Connection:** is-sandboxes · **Connection ID:** `e03f734e-0f80-4e8a-a7c1-0ece309b0ca4`
**Activity Type ID:** `37a305b2-89b1-315d-b73f-1778839a6c47` · **Service Type:** `Intsvc.ActivityExecution`
**Object:** Send Message to Channel
**Folder Path:** Shared/uipath-maestro-case

- activation-mode: sequential
- entry-rule: current-stage-entered
- isRequired: true
- runOnlyOnce: false

**Inputs — pass exactly these, with these values.** Three are required; the
rest are chosen to cover flat snake_case, a boolean, and two- and three-level
dotted paths. Pass `channel` as the literal channel name — do not resolve it
to an ID.

| Sink | Field name | Value | Naming case covered |
|---|---|---|---|
| queryParameters | `send_as` | `bot` | flat snake_case, REQUIRED |
| bodyParameters | `channel` | `C01G1P7CU58` | single word, REQUIRED |
| bodyParameters | `messageToSend` | `Naming contract check` | lowerCamelCase, REQUIRED |
| bodyParameters | `link_names` | `true` | flat snake_case, native boolean |
| bodyParameters | `image` | `https://example.invalid/build.png` | single word, optional |

> `send_as` and `channel` are the connector's only reference-typed inputs, and
> both take literal values here — `bot` is the field's own default, and
> `channel` is the resolved channel id. Do NOT run a resource lookup.
>
> This input set is deliberately limited to the fields Studio Web's Slack form
> exposes, so a canvas-built solution stays a valid cross-check of the shape.
> The connector's dotted body fields (`attachment.image_url`,
> `metadata.event_type`, `metadata.event_payload.id`) and `icon_emoji` are real
> contract fields but have no form control, so they are out of scope here;
> dotted-input coverage lives in the cm_golden Outlook task
> (`message.toRecipients`).

**Outputs.** The connector returns **102 leaf paths that collapse to 13
top-level properties** — the harshest available test of the dotted-path
derivation. Bind four:

| Field path | → Case variable | Naming case covered |
|---|---|---|
| `app_id` | postAppId | flat snake_case output |
| `ts` | postTs | two-letter lowercase name |
| `thread_ts` | postThreadTs | flat snake_case, also an input field name |
| `channel` | postChannel | same name on input and output |

The unbound remainder MUST still appear with contract names, in particular:

- `blocks[*]` — array marker must survive; its leaves include
  `blocks[*].block_id` (snake under an array) and `blocks[*].text.type`
- `response_metadata` — snake, two segments
- `message` — nested object three levels deep, e.g. `message.bot_profile.app_id`
  and `message.attachments[*].callback_id`
- `icons`, `metadata`, `ok`, `root`, `subtype`, `username`

#### T03: Add wait-for-connector task "Await Calendar Event"

**Connector:** Microsoft Outlook 365 · **Connector Key:** `uipath-microsoft-outlook365`
**Connection:** is-sandboxes-test@uipathsandboxes.onmicrosoft.com · **Connection ID:** `dd657127-91f5-4568-a3a3-c024bc03fb0f`
**Activity Type ID:** `32b856f3-e7ba-3cb3-9f4b-4c85280315be` · **Service Type:** `Intsvc.WaitForEvent`
**Object / Event:** Calendar Event Created
**Folder Path:** Shared/uipath-maestro-case

- activation-mode: sequential
- entry-rule: runs-sequentially
- isRequired: true
- runOnlyOnce: false

**Event parameters — none.** This trigger declares no inputs, so author no
`eventParameters`.

**Filter — author exactly this.** The trigger declares a `jmes` filter builder
over 18 fields; `Title` is the one the UI labels "Subject". The filter is a
third place field names must survive byte-exact, because they compile into a
JMESPath expression:

| Filter field | Operator | Value | Naming case covered |
|---|---|---|---|
| `Title` | contains | `Naming contract` | capital-first, collides with the `title` schema keyword |
| `HasAttachments` | not equals | `true` | capital-first boolean |
| `Attachments[*].MIMEType` | contains | `text/` | array-marked, dotted, three-capital run |

Join the three clauses with `And`. Do not hand-write the JMESPath — pass the
structured tree and let the CLI compile it. For reference, Studio Web compiles
this exact filter to:

```
((contains(Title,'Naming contract'))&&(HasAttachments!=`true`)&&(Attachments[?contains(MIMEType,'text/')]))
```

Note the array clause becomes a JMESPath filter projection
(`Attachments[?contains(MIMEType,…)]`), not a `[*]` path — the field names
still appear verbatim, which is what the grader checks.

**Outputs.** 20 leaf paths collapse to 14 top-level properties, **every one
capital-first**. This is the half of the contract that a "no capital-first key
may remain" scan destroys. Bind four:

| Field path | → Case variable | Naming case covered |
|---|---|---|
| `ID` | eventId | all-caps contract name |
| `Title` | eventTitle | **collides with the JSON-Schema `title` keyword** |
| `CalendarName` | eventCalendarName | capital-first with internal capital |
| `HasAttachments` | eventHasAttachments | capital-first boolean |

The unbound remainder MUST still appear with contract names:

- `Attachments[*]`, `Attendees[*]`, `Categories[*]` — capital-first **and**
  array-marked
- `Attachments[*].MIMEType`, `Attachments[*].ID`, `Attachments[*].Name`,
  `Attachments[*].Size` — nested under an array; `MIMEType` carries a
  three-capital run
- `Attendees[*].Type`, `Attendees[*].Response`, `Attendees[*].Name`,
  `Attendees[*].Email` — `Type` and `Name` collide with schema keywords
- `Categories[*].Name`
- `CalendarID` — capital-first with a trailing all-caps segment
- `Description`, `Importance`, `Sensitivity`, `AllDay`, `Location`, `ShowAs`

---

## Section 3: Personas & App Views

### Personas

None. This case has no human tasks.

### Process App Views

None.

---

## Section 4: Integrations

### Integration Service Connectors

| Connector | Connector Key | Connection | Connection ID | Used by |
|---|---|---|---|---|
| Slack | `uipath-salesforce-slack` | is-sandboxes | `e03f734e-0f80-4e8a-a7c1-0ece309b0ca4` | T02 |
| Microsoft Outlook 365 | `uipath-microsoft-outlook365` | is-sandboxes-test@uipathsandboxes.onmicrosoft.com | `dd657127-91f5-4568-a3a3-c024bc03fb0f` | T03 |

### API Workflows

None.

### Agents

None.

### Processes & RPA

None.

### Child Cases

None.
