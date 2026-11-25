# Draft first — the skeleton

Author a skeleton of real stages and rules whose tasks are labelled blank boxes. Compile and validate it, show it to the user, and stop for their approval.
It makes no registry calls and needs no `sdd.md`.

**When.** The user asks for a draft or wants to see the shape before the case is built: *draft*, *outline it*, *sketch it*, *show me the shape*, *what would it look like*, *before you build it*, or a session in host plan mode.
Judge intent, not the word: a task or value named "draft" inside the case (*draft a reply email* as a task) is not draft mode.
A request for a draft, an outline or a sketch always gates, even when it describes the whole case. When nobody can answer (CI, headless), still stop at the gate: the outline is the result.
Wording that only leans toward a draft (*a rough version*, *a first pass*, *a quick mock-up*) gates unless the request also says outright to build the whole case.
A request with none of these cues is a build. So is an edit of a plan that already has stages, and so is a "draft project" that asks for source files to hand off later, with no upload or run.
The [Stop rule](../SKILL.md#workflow) wins over a draft: a request that says design-only, Phase 1 only, review first, not to build, or not to create the case plan gets no skeleton.
Never ask the user whether to draft or build. Default to build.
Plan mode is the host's state: never enter it yourself to satisfy "show me first".

**A draft skips Design first.**
Do not invoke the planner and write no `sdd.md`: the skeleton is the design the user reviews.
When an approved `sdd.md` exists, take the stages, tasks, rules and task types from it, and leave step 0 of the [Workflow](../SKILL.md#workflow) to *Build it*.

**The deliverable is a file.**
A mermaid or ASCII diagram in chat is not a draft, and neither is a prose outline. The draft is the compiled, validated plan file of the Case project.
Write the source, run the loop below, and only then reply.

**In plan mode, writes wait for plan approval.**
Put the outline in the plan: the trigger, each stage in order with its entry condition, and each box's label.
Build the file with the steps below once the host approves the plan. The gate reply then comes after the file validates, as outside plan mode.

## What a skeleton is

A skeleton is not a working case. Never report it as one.

1. **Every task is a labelled blank box**: `.task('<Action> [<Kind>]', (t) => t.unresolved('<kind>'))`.
   `unresolved` compiles to a task of that type with an empty `data` block.
   Take `<Kind>` and `<kind>` from [Box kinds](#box-kinds).
   Several kinds share one blank task type, so the label suffix is the only place every kind shows. Keep it.
2. **Use no other task builder** (`process`, `agent`, `rpa`, `apiWorkflow`, `function`, `action`, `connector`, `waitForConnector`, `waitForTimer`, `script`, `httpRequest`, `documentExtraction`, `businessRule`, `caseManagement`, `flowProcess`, `externalAgent`, `externalWorkflow`).
   A blank box takes no `outputs`, and no `sla`, `escalation` or `caseApp` goes in a skeleton: each needs a recipient or a resource. *Build it* adds them.
3. **Make no registry calls.** No `uip maestro case registry pull`, no `uip maestro case sdd resolve`, no `uip maestro registry`, no `prepare`.
   Resources come after the user approves the shape.
   The lookups in [Find the resources](#find-the-resources) read the tenant and are not registry calls.
4. **Structure is real.** The trigger, the stages and their order, each entry and exit rule, each required flag and the case's completion are what the user approves.
   - Keep the manual trigger the plan was seeded with. A case that starts on a schedule uses `timerTrigger({ every: '<ISO_8601_CYCLE>', name: '<NAME>' })`.
     A case that starts on an outside event uses the placeholder `eventTrigger({ name, object, description })` ([Triggers](case-runtime.md#triggers-and-live-payloads)). Never pick a connector for it.
   - Write each stage as the [Minimal shape](../SKILL.md#minimal-shape) shows: an entry rule, an exit rule with `marksStageComplete: true`, and `.required()` or `.required(false)`.
     A stage for a rejection, a withdrawal or another side path is `.exceptionStage(...)` with `.required(false)`.
   - A stage that follows several alternative stages takes one `entryWhen` call per stage it follows.
   - Order the tasks inside a stage with real rules: `current-stage-entered`, then `selected-tasks-completed` naming the task before it.
   - End with `.completeWhen(rule('required-stages-completed'), { displayName: '<OUTCOME>' })`.
     When the last required stage also opens an optional stage, `validate` warns `CASE_MGMT_STAGE_ENTRY_CONDITION_MATCHES_CASE_EXIT_CONDITION`: the case closes before that stage starts. Add a required closing stage after the alternatives.
5. **Name every condition with the outcome it carries**: `{ displayName: 'Approved' }` on the `entryWhen` or `exitWhen` call.
   Each name is unique in the case: `check` warns `DUP_RULE_NAME` on a repeat and `compile` renames it.
6. **Route on a case variable or an input, never on a box.**
   A blank box has no output, so `taskOutput(...)` on it fails `check` with `TASK_OUTPUT_REF_UNRESOLVED`.
   Declare the value a rule reads with `.var('<name>', '<type>')`, and read it as `vars.<name>` in the rule's `expression`.
   Name the box that produces a routing value in its label: `Adjuster review [Human task] → decision`.
7. **Declare the inputs the request names**, with `.input({ <name>: '<type>' }, { from: <trigger> })`. Never draw a box whose only job is to receive or read an input.
8. **Ask nothing about the case before the outline.**
   A structure question (a threshold, an unnamed outcome) waits for the gate.

### Box kinds

Write each kind exactly as this table shows.
A connector box names its app as the user names it (`Slack`, `Outlook`, `Jira`). Write `Connector` only when the request names no app.

| Task | Kind | `unresolved(...)` |
|---|---|---|
| A person reviews, approves, or fills a form | Human task | `'action'` |
| An unattended robot job | RPA workflow | `'rpa'` |
| An AI agent decides or extracts | Agent | `'agent'` |
| An API workflow | API workflow | `'api-workflow'` |
| A coded function | Function | `'function'` |
| A Maestro process or flow | Maestro process | `'process'` |
| Another case | Case | `'case-management'` |
| A call to an outside app | `<App>` | `'connector'` |
| A wait for an event in an outside app | `<App>` | `'wait-for-connector'` |
| A Data Fabric read or write | Data Fabric | `'connector'` |
| Document extraction | Document extraction | `'process'` |
| A business rule decision | Business rule | `'process'` |
| An inline calculation | Script | `'process'` |
| An HTTP call with no connector | HTTP request | `'process'` |
| A wait for a time | Timer | `'process'` |

The last five kinds have no blank task of their own, so they take `'process'`. The label carries the kind, and *Build it* writes the real builder.
When several kinds fit, pick the one a Studio Web user would most likely choose. The user changes it at the gate.

## A worked skeleton

"When a claim arrives, an agent extracts the claim data and we record it. An adjuster reviews it. Approved claims are paid by a robot, rejected claims get a rejection letter. Then archive the claim."

```ts
import { casePlan, rule, manualTrigger, preserveCaseJson } from "@uipath/maestro-builder-sdk/case";

const trigger1 = manualTrigger();

const caseDefinition = casePlan("<CASE_ID_FROM_SEED>")
  .schemaVersion("<SCHEMA_VERSION_FROM_SEED>")
  .name("ClaimIntake")
  .identifier("ClaimIntake")
  .trigger(trigger1)
  .var("decision", "string")
  .stage("Intake", (s) => s
    .required()
    .entryWhen(rule("case-entered"), { displayName: "Claim arrives" })
    .exitWhen(rule("required-tasks-completed"), { displayName: "Claim recorded", marksStageComplete: true })
    .task("Extract claim data [Agent]", (t) => t.unresolved("agent").required()
      .entryWhen(rule("current-stage-entered")))
    .task("Record the claim [Data Fabric]", (t) => t.unresolved("connector").required()
      .entryWhen(rule("selected-tasks-completed", { tasks: ["Extract claim data [Agent]"] }))))
  .stage("Review", (s) => s
    .required()
    .entryWhen(rule("selected-stage-completed", { stage: "Intake" }), { displayName: "Ready for review" })
    .exitWhen(rule("required-tasks-completed"), { displayName: "Reviewed", marksStageComplete: true })
    .task("Adjuster review [Human task] → decision", (t) => t.unresolved("action").required()
      .entryWhen(rule("current-stage-entered"))))
  .stage("Payout", (s) => s
    .required(false)
    .entryWhen(rule("selected-stage-completed", { stage: "Review", expression: '=js:vars.decision === "Approve"' }), { displayName: "Approved" })
    .exitWhen(rule("required-tasks-completed"), { displayName: "Paid", marksStageComplete: true })
    .task("Pay the claim [RPA workflow]", (t) => t.unresolved("rpa").required()
      .entryWhen(rule("current-stage-entered"))))
  .exceptionStage("Rejection", (s) => s
    .required(false)
    .entryWhen(rule("selected-stage-completed", { stage: "Review", expression: '=js:vars.decision === "Reject"' }), { displayName: "Rejected" })
    .exitWhen(rule("required-tasks-completed"), { displayName: "Letter sent", marksStageComplete: true })
    .task("Send rejection letter [Outlook]", (t) => t.unresolved("connector").required()
      .entryWhen(rule("current-stage-entered"))))
  .stage("Close", (s) => s
    .required()
    .entryWhen(rule("selected-stage-completed", { stage: "Payout" }), { displayName: "After payout" })
    .entryWhen(rule("selected-stage-completed", { stage: "Rejection" }), { displayName: "After rejection" })
    .exitWhen(rule("required-tasks-completed"), { displayName: "Archived", marksStageComplete: true })
    .task("Archive the claim [API workflow]", (t) => t.unresolved("api-workflow").required()
      .entryWhen(rule("current-stage-entered"))))
  .completeWhen(rule("required-stages-completed"), { displayName: "Claim closed" })
  .build();

export default preserveCaseJson(caseDefinition, <OPTIONS_FROM_SEED>);
```

The header lines, the trigger and the last line are the ones the decompiled seed carries. It checks clean, compiles, and validates with one `TASK_NOT_CONFIGURED` warning per box: a trigger, five stages, six blank boxes, two routed outcomes and a closing stage.

## Steps

<!--skill-flavor:draft-steps:start-->
1. Scaffold as steps 1 and 2 of the [Workflow](../SKILL.md#workflow) say: `uip solution init`, then `uip maestro case init` from inside the solution dir, and the SDK.
   `<project>/<plan>` below is the plan `case init` seeded.
2. Seed `<Name>.case.ts` by decompiling that plan, as step 5 of the Workflow says. Then rewrite the chain between `.trigger(...)` and `.build()` as the skeleton, in one write.
   Keep the first comment line, the case id, `.schemaVersion(...)`, `.name(...)`, `.identifier(...)`, the trigger and the trailing `preserveCaseJson(...)`.
   Replace the trigger only for a schedule or an outside event.
3. Run the loop from the solution dir.

   ```bash
   uip maestro case check <Name>.case.ts --source
   uip maestro case compile <Name>.case.ts -o <project>/<plan>
   uip maestro case validate <project>/<plan> --strict --output json
   ```

   `validate` must report `Data.Status: "Valid"`.
<!--skill-flavor:draft-steps:end-->
   `validate` lists one `TASK_NOT_CONFIGURED` warning per box. That is the skeleton, not a defect: do not fix it and do not report it.
   Treat any other warning or error as real and fix it without adding a real task.
   Pass no `--sdd`, even when an `sdd.md` exists: its audit compares resources a skeleton does not have.
   Do not reply after `validate`. Steps 4 and 5 come first: the gate reply needs the lookups.
<!--skill-flavor:draft-upload:start-->
4. **Upload it, so the user sees it on the canvas**, unless the request forbids upload:

   ```bash
   uip solution resources refresh --solution-folder "<SolutionDir>" --output json
   uip solution upload "<SolutionDir>" --output json
   ```

   `<SolutionDir>` is the solution `uip solution init` made. The gate reply carries the returned `Data.DesignerUrl`.
   Studio Web may rename a new solution whose name is taken. When the returned name differs from `<Solution>`, say the returned name in the reply's one sentence.
   Do not ask first when this run created the solution: a draft request authorizes the upload that shows it. A skeleton names no assignee, so the [recipient list](case-runtime.md#action-recipients-and-the-go-live-trap) is empty.
   For any other solution, do not upload. The gate asks no other question, so its one sentence says the upload waits for the user's go-ahead.
   When the request forbids upload, do not upload and do not create a solution to show a draft: the gate reply carries the local path.
   When the upload fails, do not retry: say so in the one sentence, and use the local path.
   Do not publish, debug or run anything. Those are separate decisions, and the user has not approved the shape yet.
<!--skill-flavor:draft-upload:end-->
5. **Find each box's resource**, as [Find the resources](#find-the-resources) says. Then reply as [Show the shape and stop](#show-the-shape-and-stop) says.

## Find the resources

A box whose kind runs a deployed resource needs one: every kind in [Box kinds](#box-kinds) except `Script`, `HTTP request` and `Timer`.
<!--skill-flavor:lookup-no-login:start-->
When this run already found no `uip login` (the upload failed for it), skip the lookup and mark each such box `not checked`.
Otherwise run every lookup in **one** Bash call.
<!--skill-flavor:lookup-no-login:end-->
The lookups only read the tenant, so a request that forbids upload or run does not forbid them.
The lookup call is the turn's last tool call. Before it, read [gate-reply-template.md](gate-reply-template.md), search the target for each box's label as its [End the turn](gate-reply-template.md#end-the-turn) says, and send any progress note.
When it returns, send the gate reply as your next and final message, starting with its first line.

- **Processes and apps:** `uip solution resources list --kind <Process|App> --search "<TERM>" --output json`.
  It lists what the solution holds (`Source: Local`) and what the tenant has (`Source: Remote`).
  `--kind Process` returns every process type. Match the box's kind on `Type`, ignoring case: RPA workflow `process`, API workflow `api`, Agent `agent`, Function `function`, Maestro process `processOrchestration` or `flow`, Case `caseManagement`.
  A Human task box needs an Action App: search `--kind App`. A Business rule box has no lookup: unless the user named the rule, mark it `none yet`.
  Never match the Case project's own row.
- **Connections:** run this once when any box is a connector box or a Data Fabric box, including when the user named no provider.
  Skip it when no box is either. The command has no `--limit`, so the `--output-filter` row filter keeps the output to the boxes' connectors:

  ```bash
  uip is connections list --all-folders --output-filter "[?contains(ConnectorName,'<WORD>')].{Connector:ConnectorName,Connection:Name,State:State,IsDefault:IsDefault,Folder:Folder}" --output json
  ```

  Replace the `contains(...)` test with one per service the boxes use, joined with `||`.
  `<WORD>` is one distinctive word of the app the user named, in the app's usual capitalization (`Slack`, `Outlook`, `SharePoint`, `Jira`). `contains` is case-sensitive and the exact display name is unknown, so never pass a full name for a named app.
  For a box that names no provider, such as "send an email", use exact names, never `contains(...,'Mail')` (it also matches Mailchimp and Mailgun): `ConnectorName=='Gmail'`, `ConnectorName=='Microsoft Outlook 365'`, `ConnectorName=='Mail'`, `ConnectorName=='Exchange Server'`.
  For a Data Fabric box, add `ConnectorName=='UiPath Data Fabric'`.
  Match each connector box on `Connector` only, since a connector's key can contain another service's name.
  Prefer `State: Enabled`; among those, the folder the task names, then `IsDefault: Yes`.
  An empty result for a box's service marks the box `none yet`. Never say the tenant has no such connection.
- **Data Fabric entities:** `uip df entities list --include-folders --output-filter "[?contains(Name,'<KEYWORD>') || contains(Name,'<keyword>')].{Name:Name,FolderId:FolderId}" --output json`, matched on `Name` alone. The row carries a folder id, not a folder name, so name no folder on the box's line.
  A tenant holds hundreds of entities, so never list them unfiltered. `contains` is case-sensitive: test each keyword from the box's label as written, capitalized and lowercase, and a plural by its stem (`Compan` for `companies`), all joined with `||`.
- **Document extraction:** `uip ixp projects list -l 10000 --output-filter "Projects[?contains(Name,'<KEYWORD>') || contains(Name,'<keyword>') || contains(Title,'<KEYWORD>') || contains(Title,'<keyword>')].{Name:Name,Title:Title}" --output json`, matched on `Title`, else `Name`.
  It reads IXP projects and is not a registry call. Name the project; do not claim it is deployed.

Run each lookup as written and add no flag: `uip` rejects `--output-filter` on `uip solution resources list` without `--limit`, and rejects `--limit` on every `uip is` and `uip df` list.
`--search` matches names only, and tenants hold thousands of processes, so never list a kind unfiltered, not even after a search came back empty.
Put every search in the one lookup call: the user's own words for the resource, and one or two keywords from the box's label (`invoice`, `extract` for `Extract invoice data [RPA workflow]`).
When a lookup fails, mark its boxes `not checked`, say why in the first line's one sentence, and do not retry.
<!--skill-flavor:lookup-not-checked-rule:start-->
Mark a box `not checked` only when its lookup ran and exited non-zero, or when this run already found no `uip login`. Never write it for a lookup you did not run.
<!--skill-flavor:lookup-not-checked-rule:end-->
A failed lookup proves nothing is missing: say "Couldn't check your Slack connections", never "No Slack connection in this tenant". Never name a connector key, a task type or a CLI term.

Give each box one status:

- When the user named the resource, or exactly one row fits the box, use it and name it, with its folder when the row has one.
- When several fit, name the best two and ask which one.
- When none fits, write `none yet, create it or name one`.
- `Script`, `HTTP request` and `Timer` boxes need no resource: write `no resource needed` and look nothing up for them.

A row fits only when both hold: its kind is the box's kind, and its name and folder show it does the task the box describes.
A name that merely shares a keyword does not fit: a process called `invoice-cleanup` in an unrelated folder is not the invoice-recording task.
When you cannot tell that a row serves the task, treat the box as having none. Never bind to that row.
Run the lookup again at every gate, so a resource the user created since the last gate shows up.
<!--skill-flavor:gate-one-round:start-->
This gate is the one round for structure and resource questions.
<!--skill-flavor:gate-one-round:end-->

## Show the shape and stop

Read [gate-reply-template.md](gate-reply-template.md) in full before you write the gate reply. End the turn with the reply exactly as it shows.
The reply is the template and nothing else: no line before it, between its parts or after it.

## After the answer

<!--skill-flavor:draft-cloud-copy:start-->
When you uploaded the skeleton, the user may have changed it on the canvas before answering. Studio Web can add project files when the page opens, so compare the plan files only.
Before you edit again, download the cloud copy and compare its plan with `<project>/<plan>`:

```bash
uip solution download "<SOLUTION_ID>" --extract -d "$(mktemp -d)" --output json
```

`<SOLUTION_ID>` is the `SolutionId` in the solution's `.uipx`.
- A failure that says "Studio Web API returned 404" means no cloud copy exists yet: carry on.
- Any other failure (offline, not logged in, a timeout): retry once. When it still fails, do not upload again until the user says to replace the unchecked copy.
- When the two plans match, carry on.
- When they differ, build on the user's copy without asking, and say so in the reply's one sentence: copy the downloaded plan over `<project>/<plan>`, then decompile it afresh into `<Name>.case.ts` and edit that source.
<!--skill-flavor:draft-cloud-copy:end-->

<!--skill-flavor:draft-change-it:start-->
- **Change it**: edit the skeleton source, run the loop again, and show it again as steps 4 and 5 do.
<!--skill-flavor:draft-change-it:end-->
  Look the resources up again at every gate.
- **Build it** asks nothing and overrides [Design first](../SKILL.md#workflow): invoke no planner and write no `sdd.md`. Replace each `unresolved('<kind>')` with the real builder its label names, as the rest of this skill describes.
  Drop the ` [<Kind>]` suffix and any ` → <variable>` hint from each task name, and write the new name in every rule that names the task (`selected-tasks-completed`, `task-exited`). Where a label named a producer, write the `outputs` that set its variable.
  Bind each box that needs a resource to the resource the gate named, by name and folder. Ask nothing more about structure or resources.
  With an approved `sdd.md`, run step 0 of the Workflow now, and answer step 5 of [Registry resolution](registry-resolution.md) from the gate without asking: a task whose box the gate named a resource for is that pick, and every other unresolved task is a placeholder.
  A value the request leaves open (a deadline, a threshold, a text) is not a question: pick a plausible value, build with it, and name it under `Assumed:`. Never invent an identifier, a URL or an assignee.
  A Human task with no assignee in the request takes its recipient from a case input, as [Action recipients](case-runtime.md#action-recipients-and-the-go-live-trap) says. Name the input under `Needs:`.
  An unanswered which-of-two takes the first resource named. Report it under `Assumed:`.
  A box the gate marked `none yet` stays `unresolved('<kind>')` under its new name, and the final report lists it under `Needs:`. The first line says `not runnable yet`.
  A `not checked` box is looked up now, with `uip maestro case registry pull` and its index files ([Registry resolution](registry-resolution.md#index-files-by-task-type)).
<!--skill-flavor:draft-build-loop:start-->
  Finish with the [Validation loop](../SKILL.md#validation-loop): `check`, `compile` into the same `<project>/<plan>`, then `validate --strict`, with `--sdd` when an `sdd.md` exists.
<!--skill-flavor:draft-build-loop:end-->
  End the turn with the [final report](final-report-template.md). Its first line says `(draft mode)`, because this run stopped at a gate.
- **Keep it**: stop, and report the file as an outline, not a working case.

Only *Build it* authorizes the build.
Until then the skeleton is an outline. Calling it a finished case misreports it.
