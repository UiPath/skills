# Phase 2 — Skeleton

Author blank boxes, arrows, and labels; show them to the user and stop for approval. Make no new registry calls (`list` already ran in 1a).

**Draft mode only.** Draft mode asks the user to agree the shape (phase 3); phase 4 pastes real payloads into the boxes. Auto mode skips 2b–2f and phase 3 and authors real nodes directly in phase 4. Brownfield edits (shape already exists) and discovery-only tasks (nothing is authored) skip this phase.

## What a skeleton is

A skeleton is an approval-ready phase-4 shape, never a working process.

1. Make every activity a bare `<bpmn:task>` with only `id` and `name`; omit `uipath:activity`, `uipath:event`, payloads, resource identities, and connections.
2. Do not use `serviceTask` or `sendTask`; their icons (gear, envelope) imply a decided product choice. Keep every box blank.
3. Make no new registry calls: do not run `registry pull`, `search`, or `get`; `list` already ran in 1a. Do not choose element types yet. Box kinds come from the list 1a already read.
4. Use genuine `bpmn:startEvent` (with plain `bpmn:timerEventDefinition` or `bpmn:messageEventDefinition` when applicable), `bpmn:exclusiveGateway`, `bpmn:parallelGateway`, `bpmn:sequenceFlow`s, and end events. These need no registry call; phase 4 wires the trigger. Converge every branch on one end event unless the request names separate outcomes. Branches converge through a join gateway, never as two flows into the end event (`FAKE_JOIN`, see [structural-bpmn.md](structural-bpmn.md#gateways)). A skeleton returns no public result, so the shared-result end-event exception in that file's validation checklist does not apply here. Do not simplify the branch structure.
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
6. Name each branch flow with its outcome (`approve`, `reject`, `escalate`) in its `name` attribute. Leave the name off the flows leaving a parallel gateway: every branch runs, so a name would read as a choice.
7. Declare variables and gateway conditions for real; routing basis is part of approval. See [Gateways cost more than boxes](#gateways-cost-more-than-boxes).

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

A gateway requires:

1. An exclusive gateway needs `default="<flow id>"` on the gateway and `conditionExpression` on **every other** outgoing flow, or validation fails `MISSING_CONDITION_EXPRESSION`.
2. Declare each condition variable in the process's `<uipath:variables>` block, or validation fails `VARIABLE_DOES_NOT_EXIST`:
   `<uipath:inputOutput id="Classification" name="Classification" type="string" elementId="Process_1" />`
3. A `conditionExpression` uses `xsi:type="bpmn:tFormalExpression"`. If an older `init` scaffold omits that namespace, add `xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"` to `bpmn:definitions` before writing any `xsi:type`, or parsing fails with `XML_NOT_WELL_FORMED: Unbound namespace prefix: "xsi"`.

A skeleton may express reads, not writes. Conditions read the variable structurally; assignment requires a `uipath:output` mapping inside a registry payload, which the skeleton lacks. The upstream box therefore implies the producer; naming it helps, e.g. `Classify ticket [Agent] → Classification`.

## Expected findings — do not chase them

A skeleton validates as **Valid** with these expected warnings; fix none:

- `Variable "vars.<id>" is read but never assigned; it will be empty at run time` — one at process level.
- `VARIABLE_NOT_SET: Variable '<name>' is not set at this point in the flow` — one per conditioned branch flow. These read like errors and are not.

Treat validation as clean when there are zero errors. Act only on error-severity findings that block import.

## Steps

Run phases 0 and 1 first; 2a creates or adopts the project (see [SKILL.md](../SKILL.md#workflow)). Then:

- **2b Author the skeleton** by writing the `.bpmn` that `init` generated in this run (`<Name>.bpmn` at 2a's `Data.Path`) whole, in one Write, instead of patching it with a series of edits. Only that fresh starter is written whole; a downloaded or brownfield `.bpmn` is edited in place. Preserve the generated start event's `id`, its `<uipath:entryPointId>`, and the four generated JSON files. **Do not rename the start event**: its name feeds the entry-point schema, and renaming it makes `refresh` rewrite `entry-points.json` for no benefit.
- **2c** Run `uip maestro bpmn format <file>.bpmn` to generate the diagram; without it no box renders (Rule 5).
- **2d** Run `uip maestro bpmn validate <file>.bpmn --output json`; it must reach `Status: Valid`. This checks import readiness, not design; act on errors and ignore expected warnings. Write no file for the result: no notes, log, or memory file (Rule 20). The reply carries it.
- **2e** From the solution directory, run `uip maestro bpmn refresh <project-path> --output json`. `refresh` validates internally and writes nothing while validation fails, so 2d must pass first. With the preserved start event it reports `WrittenFiles: []`, the drift check passing rather than a no-op to skip. Skip 2e for a trigger-start skeleton (timer or message start): `refresh` fails without a manual start, as in 4c.
- **2f Make the shape visible.**
<!--skill-flavor:make-shape-visible:start-->
  When upload is allowed, run `uip solution upload <SolutionDir> --output json`; 3c shows the returned `Data.DesignerUrl`. Do not ask first: a build request authorizes this upload, and per-iteration consent defeats the mode. Confirm only when adopting a solution the agent did not create, because `upload` overwrites the cloud solution matching the local `.uipx` SolutionId; confirm at 2a. Skip upload when forbidden.
<!--skill-flavor:make-shape-visible:end-->

## Iterating

- **3a Edit the skeleton** from user feedback, then re-`format`. If uploaded, download it first (as in 1c); if its `.bpmn` differs from local, the user edited it online, so edit the downloaded `.bpmn` (3c says so).
- **3b Show the change** as in 2f.
<!--skill-flavor:show-change:start-->
  Each later upload reports `Data.Action: "Overwritten"` and reuses the same `SolutionId` and `DesignerUrl`, because `upload` writes the cloud solution id into local `.uipx`. If a later upload reports `"Imported"`, that id was lost and a second cloud solution was created: stop and fix it.
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
    Fabric entity box, including when the user named no provider. Skip it
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

To remove a box, delete the task and its two sequence flows, add one replacement flow, then `format`. Entry points remain untouched, so `refresh` stays a no-op.

Only *Build it* authorizes phase 4: registry pull, element disambiguation, binding live connections and resources, and payloads pasted into existing boxes. Until then, report the skeleton only as an outline, never a finished process.