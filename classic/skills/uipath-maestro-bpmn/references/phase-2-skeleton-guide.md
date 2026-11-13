# Phase 2 — Skeleton

Author a skeleton of blank boxes, arrows and labels, show it to the user, and
stop for their approval. It makes no new registry calls (`list` already ran in 1a).

**Draft mode only.** Draft mode stops afterwards and asks the user to agree
the shape (phase 3); phase 4 then pastes real payloads into these same boxes.
Auto mode skips 2b–2f and phase 3 and authors real nodes directly in phase 4.
Brownfield edits (the shape already exists) and discovery-only tasks (nothing
is authored) skip this phase too.

## What a skeleton is

A skeleton exists so the shape can be read end to end — so a user can say "yes,
that's it" or "drop that step", and so phase 4 has a validated structure to fill
in. It is not a working process and must never be reported as one.

1. **Every activity is a bare `<bpmn:task>`** carrying only an `id`, a
   `name`, and, for a step that runs once per item, its multi-instance marker
   (Rule 8). No `uipath:activity`, no `uipath:event`, no payloads, no resource
   identities, no connections.
2. **Do not use `serviceTask` or `sendTask`.** Their icons (a gear, an
   envelope) make a box look like a decided product choice. Keep every box
   blank.
3. **Make no new registry calls.** No `registry pull`, `search`, or `get`; `list` already ran in 1a.
   Element types are not being chosen yet. Box kinds come from the list 1a
   already read.
4. **Control flow is real.** Genuine `bpmn:startEvent` (see
   [Draw the trigger the user named](#draw-the-trigger-the-user-named)),
   `bpmn:exclusiveGateway` and `bpmn:parallelGateway`, `bpmn:sequenceFlow`s,
   boundary events (`errorEventDefinition`, `timerEventDefinition`) when the
   request names a failure or a deadline on a step (a deadline that escalates
   while the step keeps running is `cancelActivity="false"`), and end events: one that every branch converges on, unless the request
   names separate outcomes. Branches converge through a join gateway, never
   as two flows into the end event (`FAKE_JOIN`, see
   [structural-bpmn.md](structural-bpmn.md#gateways)). A skeleton returns no
   public result, so the shared-result end-event exception in that file's
   validation checklist does not apply here. Do not simplify the branch
   structure.
5. **Label each box with the action first and the element's toolbox kind last,
   in brackets** — `Extract invoice data [RPA workflow]`, `Manager review
   [Action app]`, `Classify ticket [Agent]`, `Notify the team [Slack]`. Pick the box's type from the 1a
   list, then take its kind verbatim from [Toolbox kinds](#toolbox-kinds) (for a
   connector box, substitute the app per the rule above the table);
   a type not in that table takes its `Label` from the 1a list (`Execute
   script`, `Execute HTTP request`). Never write a type that is not in
   the 1a list. When several types could fit, pick the one
   a Studio Web user would most likely choose for that step and label the box
   with it; the user changes it at the gate if they disagree. The label
   carries the meaning a blank box cannot.
6. **Name each branch flow** with the outcome it carries (`approve`, `reject`,
   `escalate`) via the flow's `name` attribute, so the routing reads off the
   picture. Leave the name off the flows leaving a parallel gateway: every
   branch runs, so a name would read as a choice.
7. **Declare variables and gateway conditions for real.** The basis a gateway
   routes on is part of what the user is approving — three branches out of a
   diamond with no stated basis could mean anything. See
   [Gateways cost more than boxes](#gateways-cost-more-than-boxes).
8. **Mark a step that runs once per item.** When the request says a step
   runs for each item ("for every line item", "notify each supplier"), put a
   multi-instance marker on its box. Do not draw a loop from gateways and
   boxes instead, and do not leave the marker to phase 4: it is structure,
   and the user is approving it. See
   [Multi-instance boxes](#multi-instance-boxes).
9. **Every error path out of a parallel branch must end the process or
   rejoin.** A parallel join waits for every branch it forked. When an error
   boundary or a gateway exit leaves one branch for a plain end event, the
   join never fires and the instance never completes. End that path in a
   terminate end event (`<bpmn:terminateEventDefinition />`) when it stops
   the process. When the process carries on, merge the path back onto its own
   branch through an exclusive gateway placed before the join, so the join
   keeps exactly one incoming flow per forked branch; a flow from the error
   path straight into the join adds an input the join waits for forever.
   This applies to interrupting boundaries only: a non-interrupting one
   leaves the step running on its branch.

The kind is enough for a label; the type's template is resolved in phase 4.
The resource each box will use is looked up at 3c.

### Toolbox kinds

The short names Studio Web's BPMN toolbox shows (PO.Frontend
`toolbox/types.ts` `enum Category`). The registry's `Label` is the longer
element name, so copy these instead when the type is listed.
A connector box (`Intsvc.ActivityExecution`) names its app as the user names
it (`Slack`, `Outlook`, `Jira`), not the generic category: a box labeled
`[Connector]` does not tell the user which system the step talks to. Write
`Connector` only when the request names no app. If the user picks a different
app at the gate, relabel the box with it.

| Type | Kind |
|---|---|
| `Actions.HITL` | Action app |
| `Orchestrator.StartJob` | RPA workflow |
| `Orchestrator.StartAgentJob` | Agent |
| `Orchestrator.ExecuteApiWorkflowAsync` | API workflow |
| `Orchestrator.ExecuteFunctionAsync` | Function |
| `Orchestrator.BusinessRules` | Business rule |
| `Intsvc.ActivityExecution` | `<App>` (see the connector rule above) |
| `Orchestrator.StartAgenticProcess`, `Orchestrator.StartAgenticProcessAsync` | Maestro BPMN |
| `Orchestrator.StartCaseMgmtProcess`, `Orchestrator.StartCaseMgmtProcessAsync` | Maestro Case |
| `Orchestrator.StartFlowProcess`, `Orchestrator.StartFlowProcessAsync` | Maestro Flow |

## Gateways cost more than boxes

Boxes are free. A gateway is not, and the three costs always arrive together:

1. An exclusive gateway needs `default="<flow id>"` on the gateway and a
   `conditionExpression` on **every other** outgoing flow, or validation fails
   `MISSING_CONDITION_EXPRESSION`.
2. A condition referencing a variable needs that variable declared in the
   process's `<uipath:variables>` block, or validation fails
   `VARIABLE_DOES_NOT_EXIST`:
   `<uipath:inputOutput id="Classification" name="Classification" type="string" elementId="Process_1" />`
3. A `conditionExpression` uses `xsi:type="bpmn:tFormalExpression"`, and older
   `init` scaffolds do not declare that namespace. Add
   `xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"` to
   `bpmn:definitions` before writing any `xsi:type`, or the file is not
   well-formed XML and fails at parse with
   `XML_NOT_WELL_FORMED: Unbound namespace prefix: "xsi"`.

A skeleton can express **reads but not writes**. The gateway reads the variable
through its conditions, which is plain structural BPMN. What *assigns* the
variable is a `uipath:output` mapping inside a node's registry payload, which a
skeleton deliberately does not have. So the producer is implied by position — the
box upstream of the gateway is understood to be what will assign it. Naming it
in the label helps: `Classify ticket [Agent] → Classification`.

## Expected findings — do not chase them

A skeleton validates as **Valid** with warnings, and those warnings are correct
for a skeleton. Fix nothing that appears here:

- `Variable "vars.<id>" is read but never assigned; it will be empty at run
  time` — one per declared variable, at process level.
- `VARIABLE_NOT_SET: Variable '<name>' is not set at this point in the flow` —
  one per conditioned branch flow. These read like errors and are not.

Treat a skeleton as validating cleanly when there are **zero errors**. Act only on
error-severity findings, and only when they block import.

## Steps

Phases 0 and 1 run first, and 2a has created or adopted the project — see
[SKILL.md](../SKILL.md#workflow). Then:

- **2b Author the skeleton** by writing the `.bpmn` that `init`
  generated in this run (`<Name>.bpmn` at 2a's `Data.Path`) whole, in one Write, instead of patching it with a series of edits. Only that fresh starter is written whole; a downloaded or brownfield `.bpmn` is edited in place. Preserve the generated start event's `id`, its
  `<uipath:entryPointId>`, and the four generated JSON files. **Do not rename
  a manual start event**: its name feeds the entry-point schema, so renaming
  it makes `refresh` rewrite `entry-points.json` for no benefit. A trigger
  start takes its trigger's name
  ([Draw the trigger the user named](#draw-the-trigger-the-user-named)).
- **2c `uip maestro bpmn format <file>.bpmn`** — generates the diagram. Without
  it no box renders on the canvas (Rule 5).
- **2d `uip maestro bpmn validate <file>.bpmn --output json`** — must reach
  `Status: Valid`. This is an import-readiness check, not a design review:
  act on errors, ignore the expected warnings above. Write no file for the
  result: no notes, log, or memory file (Rule 20). The reply carries it.
- **2e `uip maestro bpmn refresh <project-path> --output json`** — run it from the
  solution directory. `refresh` validates internally and refuses to write
  anything while validation fails, so 2d must pass first. On a skeleton that
  preserved the start event it reports `WrittenFiles: []`, which is the
  drift check passing rather than a no-op to skip. Skip 2e for a
  trigger-start skeleton (timer or message start): `refresh` fails with no
  manual start, as in 4c.
- **2f Make the shape visible.**
<!--skill-flavor:make-shape-visible:start-->
  When the request allows an upload, run
  `uip solution upload <SolutionDir> --output json`; 3c shows the returned
  `Data.DesignerUrl`. Do not ask first: a request to build the
  process authorizes the upload that shows it, and a consent gate per
  iteration would defeat the mode. The one case that still needs confirmation
  is adopting a solution the agent did not create, because `upload` overwrites
  the cloud solution matching the local `.uipx` SolutionId. Confirm that at
  2a, not here. When the request forbids upload, skip it.
<!--skill-flavor:make-shape-visible:end-->
- **Then go straight to 3c.** 3a–3b run only after the user asks for a
  change. A first pass ends with the 3c lookup and the 3c reply, never with a
  description of the shape or a request to approve it in your own words.

## Iterating

- **3a Edit the skeleton** from the user's feedback, then re-`format`. If you
  uploaded it, download it first (as in 1c); when its `.bpmn` differs from
  the local one, the user edited it online: edit the downloaded `.bpmn` (3c
  says so).
- **3b Show the change** the same way as 2f.
<!--skill-flavor:show-change:start-->
  Each upload after the first
  reports `Data.Action: "Overwritten"` and reuses the same `SolutionId` and
  `DesignerUrl`, because `upload` writes the cloud solution id back into the
  local `.uipx`. `"Imported"` on a later upload means that id was lost and a
  second cloud solution was just created — stop and fix that before
  continuing.
<!--skill-flavor:show-change:end-->
  Repeat 3a–3b.
- **3c Ask before building.** Find each box's resource, then reply.

  **Find the resources.** A box whose kind runs a deployed resource (any
  kind in [Toolbox kinds](#toolbox-kinds), including Business rule, plus an
  app, queue, entity, or a connector's connection) cannot be built without one. When 1a reported no
  login, skip the lookup and mark each such box *not checked*. Otherwise run
  every lookup in **one** Bash call. It is the turn's last tool call: send
  any progress note before it, and when it returns, send the 3c reply
  as your next and final message, starting with its first line.

  - **Processes, queues, apps:** `uip solution resources list --kind
    <Process|Queue|App> --search "<term>" --output json`. It lists what the
    solution already holds (`Source: Local`) and what the tenant has
    (`Source: Remote`). `--kind Process` returns every process type; match
    the box's kind on `Type`: RPA workflow `process`, API workflow `api`,
    Agent `agent`, Maestro BPMN `processOrchestration`, Maestro Case
    `CaseManagement`, Maestro Flow `Flow`, Function `function`.
  - **Connections:** run this once when any box is a connector box or a Data
    Fabric entity box, including when the user named no provider. A
    connector trigger start (`Invoice updated [Data Fabric]`) counts as a
    connector box: give it its own line, labelled with its start event's
    `name`. Skip it
    when no box is either, since the filter has no service to test. No
    connector key is needed, and the command has no `--limit`, so the
    `--output-filter` row filter keeps the output to the boxes' connectors:

    ```bash
    uip is connections list --all-folders --output-filter "[?contains(ConnectorName,'<WORD>')].{Connector:ConnectorName,Connection:Name,State:State,IsDefault:IsDefault,Folder:Folder}" --output json
    ```

    Replace the `contains(...)` test with one per service the boxes use, joined
    with `||`. `<WORD>` is one distinctive word of the app the user named, in
    the app's usual capitalization (`Slack`, `Outlook`, `SharePoint`, `Jira`,
    `Salesforce`); `contains` is case-sensitive and the exact display name is
    unknown, so never pass a full name for a named app. For a box that names no
    provider, such as "send an email", use exact names, never `contains(...,'Mail')`
    (it also matches Mailchimp and Mailgun): `ConnectorName=='Gmail'`,
    `ConnectorName=='Microsoft Outlook 365'`, `ConnectorName=='Mail'`,
    `ConnectorName=='Exchange Server'`. When any box is a Data Fabric entity,
    add `ConnectorName=='UiPath Data Fabric'`.

    Match each connector box to the rows whose `Connector` is the service the
    box uses. Match on `Connector` only: a connector's key can contain another
    service's name (the Slack connector's key contains `salesforce`). A box
    that names no provider takes any row from the exact-name list. Prefer
    `State: Enabled`; among those, the folder the step names, then
    `IsDefault: Yes`. An empty result for a box's service marks the box *none
    yet*, whose line asks the user to create one or name one, so a filter that
    missed through a wrong word is corrected by the user's reply. Never say
    the tenant has no such connection. Mark the box *not checked* only when
    this command exited non-zero.
  - **Business rules:** `uip rules list --all-folders --limit 10000
    --output-filter "[].{Name:Name,FolderPath:FolderPath}" --output json`, matched on name and folder path. A business rule binds by name and folder
    path (Rule 17).
  - **Data Fabric entities:** `uip df entities list --include-folders
    --output-filter "[].{Name:Name,FolderId:FolderId}" --output json`, matched
    on `Name`; the row carries a folder id, not a folder name, so judge an
    entity on its name alone and name no folder on its box line. (True as of `uip` 1.207.0: `solution resources list --kind Entity` returns no rows even
    when the entity exists.) A Data Fabric box
    also needs a Data Fabric connection: match `Connector` `UiPath Data
    Fabric` in the connections list above (its filter clause is required).

  Run each lookup exactly as written, adding no flag. `uip` rejects
  `--output-filter` on `uip solution resources list` unless `--limit` comes
  with it, and rejects `--limit` on every `uip is` and `uip df` list. Where a
  lookup above shows no `--output-filter`, leave it off. When you do narrow a
  `solution resources list` output, pass `--limit 50`.

  `--search` matches names only, and tenants hold thousands of processes, so
  never list a kind unfiltered, not even after a search came back empty.
  Put every search in the one lookup call: the user's own words for the
  resource, and one or two keywords from the box's label (`review`,
  `approval` for `Manager review [Action app]`). Say a resource does not
  exist only after every search found no fit. When a
  lookup fails, mark its boxes *not checked*, say why in the one sentence
  the reply's first line allows, and do not retry. A failed lookup proves
  nothing is missing, so state it as what could not be checked ("Couldn't
  check your Slack connections"), never as "No Slack connection in this
  tenant", and never as a connector key, kind, or CLI term; never write
  "connector key" in the reply. Then, for each box:

  - When the user named the resource, or exactly one row fits the box, use
    it and name it on the box's line, with its folder when the row has one.
  - When several fit, name the best two on the box's line and ask which one.
  - When none fits, say on the box's line that it does not exist yet: the
    user creates it or names one, or picks *Change it* to have it authored
    (Rule 17).

  A row fits only when both hold: its kind is the box's kind (match `Type`
  as above, and an Action app box takes an action app, never a web or other
  app), and its name and folder show it does the step the box describes. A
  name that merely shares a keyword does not fit: an app called `review-app`
  in an unrelated project's folder is not the approval step of an
  accounts-payable process. When you cannot tell that a row serves the step,
  treat the box as having none: write "none yet, create it or name one" and
  never bind to the row. Phase 4 binds only the resource this gate named, except the 4a swap when that connection does not ping `Enabled`.

  Script steps need no resource: write `no resource needed` and skip the lookup. Every `[Action app]` box needs the lookup. Run the lookup
  again at every 3c, so a resource the user created since the last gate
  shows up. These lookups read only; none is a registry call. In draft mode
  this gate is the one round for structure and resource questions that Rule 4 allows. The 2a solution pick list and the image-inventory confirmation still come before it.

  Reply exactly as [gate-reply-template.md](gate-reply-template.md) shows,
  and read that file in full before you write the reply.

  *Build it* goes to phase 4, which binds each box to the resource named here
  and asks nothing more about structure or resources. A box still marked
  *none yet* gets a placeholder binding (4a) and is listed under
  `Needs:` in 4g (`Unverified` is for mappings and nodes that could not be checked); a *not checked* box is looked up in 4a; an unanswered *which of two* takes the first named, reported under `Assumed`. *Change it* goes back to 3a. *Keep it* ends the run
  with the skeleton reported as an outline.

Removing a box is the common edit: delete the task, delete its two sequence
flows, add one replacement flow, then `format`. Since entry points are
untouched, `refresh` stays a no-op.

Only *Build it* authorizes phase 4 — registry pull, element disambiguation,
binding live connections and resources, and payloads pasted into the existing
boxes. Until then the skeleton is an outline, and calling it a finished
process misreports it.

## Draw the trigger the user named

When the request names the trigger, turn the generated start event into
that trigger in place. Keep its `id` and its `<uipath:entryPointId>`, add no
second start, and add one plain event definition:

| The request says | Event definition | Start event `name` |
|---|---|---|
| A schedule ("every night", "each Monday at 9") | `<bpmn:timerEventDefinition />` | `Every night [Schedule]` |
| An event in another system ("when an invoice is updated in Data Fabric", "when an email arrives") | `<bpmn:messageEventDefinition />` | `Invoice updated [Data Fabric]`, `Email received [Outlook]` |
| A message from another process | `<bpmn:messageEventDefinition />` | `Order message received [Message]` |

Name the start the same way as a box: the event first, then its kind in
brackets, with a connector event naming its app. Keep the generated manual
start only when the request names no trigger, or says someone starts it.
The event definition carries no payload and needs no registry call; phase 4
wires the trigger.

## Multi-instance boxes

Add `bpmn:multiInstanceLoopCharacteristics` to the bare `bpmn:task`, and
declare the collection it iterates as a process variable:
`<uipath:inputOutput id="LineItems" name="LineItems" type="array" elementId="Process_1" />`

```xml
<bpmn:task id="Task_CheckStock" name="Check stock [RPA workflow]">
  <bpmn:incoming>Flow_1</bpmn:incoming>
  <bpmn:outgoing>Flow_2</bpmn:outgoing>
  <bpmn:multiInstanceLoopCharacteristics isSequential="true">
    <bpmn:completionCondition xsi:type="bpmn:tFormalExpression">=vars.OutOfStock</bpmn:completionCondition>
    <bpmn:extensionElements>
      <uipath:loopCharacteristics inputCollection="=vars.LineItems" inputElement="item" />
    </bpmn:extensionElements>
  </bpmn:multiInstanceLoopCharacteristics>
</bpmn:task>
```

- "One at a time" or "in order" is `isSequential="true"`. "All at once",
  "at the same time" or "in parallel" is `isSequential="false"`. When the
  request does not say, use parallel.
- "Stop as soon as …" is a `completionCondition` on the boolean variable the
  box would set. Declare that variable too. With no stop rule, omit
  `completionCondition`.
- The `xsi` namespace rule in
  [Gateways cost more than boxes](#gateways-cost-more-than-boxes) applies to
  `completionCondition` too.

The full contract is in
[structural-bpmn.md](structural-bpmn.md#multi-instance--loop-characteristics-registry-gap--canvas-supports-it).
