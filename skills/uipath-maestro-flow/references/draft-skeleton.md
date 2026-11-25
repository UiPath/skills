# Draft first — the skeleton

Author a skeleton of labelled placeholder boxes with real control flow. Compile and validate it, show it to the user, and stop for their approval.
It makes no registry calls.

**When.** The user asks for a draft or wants to see the shape before the flow is built: *draft*, *outline it*, *sketch it*, *show me the shape*, *what would it look like*, *before you build it*, or a session in host plan mode.
Judge intent, not the word: a step or value named "draft" inside the flow (*draft a reply email* as a step) is not draft mode.
A request for a draft, an outline or a sketch always gates, even when it describes the whole flow.
Wording that only leans toward a draft (*a rough version*, *a first pass*, *a quick mock-up*) gates unless the request also says outright to build the whole flow.
A request with none of these cues is a build. So is a brownfield edit, and so is a "draft project" that asks for source files to hand off later, with no upload or run.
Never ask the user whether to draft or build. Default to build.
Plan mode is the host's state: never enter it yourself to satisfy "show me first".

**The deliverable is a file.**
A mermaid or ASCII diagram in chat is not a draft, and neither is a prose outline. The draft is the compiled, validated `<Project>/<Name>.flow`.
Write the source, run the loop below, and only then reply.

**In plan mode, writes wait for plan approval.**
Put the outline in the plan: each box's label in order, the decisions with their conditions, the trigger.
Build the file with the steps below once the host approves the plan. The gate reply then comes after the file validates, as outside plan mode.

## What a skeleton is

A skeleton is not a working flow. Never report it as one.

1. **Every activity is a labelled `mock()` box**: `.step("<id>", mock(), { label: "<Action> [<Kind>]" })`.
   `mock()` takes no arguments and compiles to `core.logic.mock`.
   Take `<Kind>` from [Box kinds](#box-kinds).
   On the canvas every mock box looks the same, so the label suffix is the only place the kind shows. Keep it.
2. **Use no typed node factory** (`script`, `http`, `connector`, `agent`, `inlineAgent`, `rpaWorkflow`, `apiWorkflow`, `hitl`, `subflow`, `rawNode`, and the like).
3. **Make no registry calls.** No `uip maestro registry`, no `uip maestro flow registry`, no `prepare`.
   Node types come after the user approves the shape.
   The lookups in [Find the resources](#find-the-resources) read the tenant and are not registry calls.
4. **Control flow is real.** The trigger, `.branch`, `.switch`, `.parallel`, `.loop` and the end are what the user approves.
   - Keep the manual trigger the stub wrote. A flow that runs on a schedule uses `.trigger(scheduled({ every: "<CRON_OR_INTERVAL>" }))` ([scheduled-trigger.md](scheduled-trigger.md)).
     A scheduled trigger has no inputs: declare the values a decision reads with `.var(<name>, types.*, <default>)`.
     For any other start (a connector event, a form, a chat), keep the manual trigger and make the first box `<Event> [Trigger]`.
   - Arms that finish the same way fall through to one shared next step. Do not copy it into each arm unless the request names separate outcomes.
   - End with `.return({})`. Declare no flow output: a mock produces nothing to bind.
   - Give each decision and loop an id that reads as its label (`isUrgent`, `eachAttachment`). The canvas shows the id.
   - Write each construct as its reference shows: [branch.md](branch.md), [switch.md](switch.md), [parallel-merge.md](parallel-merge.md), [loops.md](loops.md). Only the step bodies are `mock()`.
5. **Label every arm with the outcome it carries**: `.label("Approved")` on a `.branch` arm, `label: "Billing"` on a `.switch` case.
   Give `.switch` a default arm when the request leaves other values open.
6. **Route on an input or a `.var()`, never on a box.**
   A condition that reads `out(<mock step>)` fails `check` with `MOCK_HAS_NO_OUTPUT`, but `compile` still exits 0 and writes the file. So run `check` before `compile` and fix it first.
   In emit-only mode `check` refuses: keep this rule by hand.
   Name the box that produces a routing value in its label: `Classify request [Agent] → category`.
7. **Declare the inputs the request names**, with `.input({ <name>: types.* })`. Never draw a box whose only job is to receive or read an input.
8. **Mark a step that runs once per item with `.loop(<id>, <collection>, body)`**, and put the box inside it.
   Read the collection from `input(<name>)` or a `.var(<name>, types.array)`, never from a box.
   Do not leave the loop to Build it: it is structure, and the user approves it.
9. **Ask nothing about the flow before the outline.**
   A structure question (a threshold, an unnamed branch) waits for the gate.
   The solution question in [SKILL.md — Project layout](../SKILL.md#project-layout) still comes first.

### Box kinds

Write each kind exactly as this table shows.
A connector box names its app as the user names it (`Slack`, `Outlook`, `Jira`). Write `Connector` only when the request names no app.

| Step | Kind |
|---|---|
| A person reviews, approves, or fills a form | Human task |
| An unattended robot job | RPA workflow |
| An AI agent decides or extracts | Agent |
| An API workflow | API workflow |
| A coded function | Function |
| A call to an outside app | `<App>` |
| Another Maestro process, case, or flow | Maestro process |
| Document extraction | Document extraction |
| A Data Fabric read or write | Data Fabric |
| A queue item | Queue |
| An inline calculation | Script |
| Reshape or filter list data | Transform |
| An HTTP call with no connector | HTTP request |
| A wait | Delay |

When several kinds fit, pick the one a Studio Web user would most likely choose. The user changes it at the gate.

## A worked skeleton

"When a support request arrives, an agent classifies it. Billing requests go to the finance queue, outages page the on-call engineer, all others get a reply. Then scan every attachment and log the request."

```ts
import { flow, manual, mock, input, types } from "@uipath/maestro-builder-sdk";

export default flow("<FLOW_ID_FROM_STUB>")
  .schemaVersion("1.9")
  .name("SupportRequestRouter")
  .openTails()
  .trigger(manual(), { version: "1.0" })
  .input({ category: types.string, attachments: types.array })
  .step("classify", mock(), { label: "Classify request [Agent] → category" })
  .switch("route", input("category"), [
    { value: "billing", label: "Billing", body: (b) => b.step("queueBilling", mock(), { label: "Add to finance queue [Queue]" }) },
    { value: "outage", label: "Outage", body: (b) => b.step("pageOnCall", mock(), { label: "Page on-call [Slack]" }) },
  ], (other) => other.step("reply", mock(), { label: "Send reply [Outlook]" }))
  .loop("eachAttachment", input("attachments"), (body) => body
    .step("scan", mock(), { label: "Scan attachment [RPA workflow]" }))
  .step("log", mock(), { label: "Log the request [Script]" })
  .return({})
  .build();
```

The header lines are the ones `init` seeds. It checks, compiles and validates with 0 warnings: a trigger, six mock boxes, a switch with a default arm, a loop, and an end.

## Steps

<!--skill-flavor:draft-steps:start-->
1. Run the solution scan and `init` of [SKILL.md — Project layout](../SKILL.md#project-layout), and ask which solution to use when it says to.
   Run `init` only once the solution is settled.
   The project is `<Solution>/<Name>/`; the commands below write it as `<Project>`.
2. Rewrite `<Project>/.flow-sdk/<Name>.flow.ts` as the skeleton, in one write.
   `init` seeds `.schemaVersion("1.9")`, `.name(...)`, `.openTails()`, `.trigger(manual(), { version: "1.0" })` and a `.layout()` call. Keep the seeded flow id, the first four, and the imports you still use. Delete the `.layout()` call: `compile` lays out every box.
   Replace the trigger only for a schedule.
3. Run the loop. Skip `format`: `compile` lays out the skeleton. In emit-only mode `check` refuses: skip it, and keep rule 6 by hand.

   ```bash
   ( cd "<Project>" && uip maestro flow check .flow-sdk/<Name>.flow.ts --source )
   ( cd "<Project>" && uip maestro flow compile .flow-sdk/<Name>.flow.ts -o <Name>.flow )
   uip maestro flow validate "<Project>/<Name>.flow" --output json
   ```

   `validate` must report `Data.Status: "Valid"`.
<!--skill-flavor:draft-steps:end-->
   A skeleton checks, compiles and validates with no warning. Treat any warning or error as real and fix it without adding a real node.
   `check` prints `HANDLE_NOT_IN_CURRENT_MANIFEST did not run` when no tenant is logged in. That is not a failure.
   Do not reply after `validate`. Steps 4 and 5 come first: the gate reply needs the lookups.
<!--skill-flavor:draft-upload:start-->
4. **Upload it, so the user sees it on the canvas**, unless the request forbids upload:

   ```bash
   uip solution resources refresh --solution-folder "<SolutionDir>" --output json
   uip solution upload "<SolutionDir>" --output json
   ```

   `<SolutionDir>` is the solution `uip solution init` made. The gate reply carries the returned `Data.DesignerUrl`.
   Studio Web may rename a new solution whose name is taken. When the returned name differs from `<Solution>`, say the returned name in the reply's one sentence.
   Do not ask first when this run created the solution: a draft request authorizes the upload that shows it ([author.md](author.md) rule 9).
   For any other solution, do not upload. The gate asks no other question, so its one sentence says the upload waits for the user's go-ahead.
   When the request forbids upload, do not upload and do not create a solution to show a draft: the gate reply carries the local path.
   When the upload fails, do not retry: say so in the one sentence, and use the local path.
   Do not publish, debug or run anything. Those are separate decisions, and the user has not approved the shape yet.
<!--skill-flavor:draft-upload:end-->
5. **Find each box's resource**, as [Find the resources](#find-the-resources) says. Then reply as [Show the shape and stop](#show-the-shape-and-stop) says.

## Find the resources

A box whose kind runs a deployed resource needs one: every kind in [Box kinds](#box-kinds) except `Human task`, `Script`, `Transform`, `HTTP request` and `Delay`.
<!--skill-flavor:lookup-no-login:start-->
When this run already found no `uip login` (the upload failed for it), skip the lookup and mark each such box `not checked`.
Otherwise run every lookup in **one** Bash call.
<!--skill-flavor:lookup-no-login:end-->
The lookups only read the tenant, so a request that forbids upload or run does not forbid them.
The lookup call is the turn's last tool call. Before it, read [gate-reply-template.md](gate-reply-template.md), search the target for each box's step id as its [End the turn](gate-reply-template.md#end-the-turn) says, and send any progress note.
When it returns, send the gate reply as your next and final message, starting with its first line.

- **Processes and queues:** `uip solution resources list --kind <Process|Queue> --search "<TERM>" --output json`.
  It lists what the solution holds (`Source: Local`) and what the tenant has (`Source: Remote`).
  `--kind Process` returns every process type. Match the box's kind on `Type`: RPA workflow `process`, API workflow `api`, Agent `agent`, Function `function`, Maestro process `processOrchestration`, `CaseManagement` or `Flow`.
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
  Prefer `State: Enabled`; among those, the folder the step names, then `IsDefault: Yes`.
  An empty result for a box's service marks the box `none yet`. Never say the tenant has no such connection.
- **Data Fabric entities:** `uip df entities list --include-folders --output-filter "[?contains(Name,'<KEYWORD>') || contains(Name,'<keyword>')].{Name:Name,FolderId:FolderId}" --output json`, matched on `Name` alone. The row carries a folder id, not a folder name, so name no folder on the box's line.
  A tenant holds hundreds of entities, so never list them unfiltered. `contains` is case-sensitive: test each keyword from the box's label as written, capitalized and lowercase, and a plural by its stem (`Compan` for `companies`), all joined with `||`.
- **Document extraction:** `uip ixp projects list -l 10000 --output-filter "Projects[?contains(Name,'<KEYWORD>') || contains(Name,'<keyword>') || contains(Title,'<KEYWORD>') || contains(Title,'<keyword>')].{Name:Name,Title:Title}" --output json`, matched on `Title`, else `Name`.
  It reads IXP projects, not flow nodes, and is not a registry call. Name the project; do not claim it is deployed.

Run each lookup as written and add no flag: `uip` rejects `--output-filter` on `uip solution resources list` without `--limit`, and rejects `--limit` on every `uip is` and `uip df` list.
`--search` matches names only, and tenants hold thousands of processes, so never list a kind unfiltered, not even after a search came back empty.
Put every search in the one lookup call: the user's own words for the resource, and one or two keywords from the box's label (`invoice`, `extract` for `Extract invoice data [RPA workflow]`).
When a lookup fails, mark its boxes `not checked`, say why in the first line's one sentence, and do not retry.
<!--skill-flavor:lookup-not-checked-rule:start-->
Mark a box `not checked` only when its lookup ran and exited non-zero, or when this run already found no `uip login`. Never write it for a lookup you did not run.
<!--skill-flavor:lookup-not-checked-rule:end-->
A failed lookup proves nothing is missing: say "Couldn't check your Slack connections", never "No Slack connection in this tenant". Never name a connector key, a node type or a CLI term.

Give each box one status:

- When the user named the resource, or exactly one row fits the box, use it and name it, with its folder when the row has one.
- When several fit, name the best two and ask which one.
- When none fits, write `none yet, create it or name one`.
- `Human task`, `Script`, `Transform`, `HTTP request` and `Delay` boxes need no resource: write `no resource needed` and look nothing up for them.

A row fits only when both hold: its kind is the box's kind, and its name and folder show it does the step the box describes.
A name that merely shares a keyword does not fit: a process called `invoice-cleanup` in an unrelated folder is not the invoice-recording step.
When you cannot tell that a row serves the step, treat the box as having none. Never bind to that row.
Run the lookup again at every gate, so a resource the user created since the last gate shows up.
<!--skill-flavor:gate-one-round:start-->
This gate is the one round for structure and resource questions. A question asked before the skeleton exists, such as which solution to use, still comes before it.
<!--skill-flavor:gate-one-round:end-->

## Show the shape and stop

Read [gate-reply-template.md](gate-reply-template.md) in full before you write the gate reply. End the turn with the reply exactly as it shows.
The reply is the template and nothing else: no line before it, between its parts or after it.

## After the answer

<!--skill-flavor:draft-cloud-copy:start-->
When you uploaded the skeleton, the user may have changed it on the canvas before answering. Studio Web also adds `evals/`, `entry-points.json` and `simulations.json` to the project when the page opens, so compare the `.flow` files only.
Before you edit again, download the cloud copy and compare its `.flow` with `<Project>/<Name>.flow`:

```bash
uip solution download "<SOLUTION_ID>" --extract -d "$(mktemp -d)" --output json
```

`<SOLUTION_ID>` is the `SolutionId` in the solution's `.uipx`.
- A failure that says "Studio Web API returned 404" means no cloud copy exists yet: carry on.
- Any other failure (offline, not logged in, a timeout): retry once. When it still fails, do not upload again until the user says to replace the unchecked copy.
- When the two `.flow` files match, carry on.
- When they differ, build on the user's copy without asking, and say so in the reply's one sentence: copy the downloaded `.flow` over `<Project>/<Name>.flow`. Then take the decompile-and-merge loop below, never `compile`, so their layout survives.
<!--skill-flavor:draft-cloud-copy:end-->

<!--skill-flavor:draft-change-it:start-->
- **Change it**: edit the skeleton source, run the loop again, and show it again as steps 4 and 5 do. When you built on their copy, use the merge loop of [Editing an existing flow](../SKILL.md#editing-an-existing-flow) in place of the loop's `compile`.
<!--skill-flavor:draft-change-it:end-->
  Look the resources up again at every gate.
- **Build it** asks nothing and overrides [SKILL.md](../SKILL.md#critical-rules) rule 4 and [author.md](author.md) rule 8: replace each `mock()` with the real node its label names, keeping its step id. Author the real nodes as the rest of this skill describes: node search, connectors, `prepare`, bindings.
  Drop the ` [<Kind>]` suffix and any ` → <variable>` hint from each label. Where a label named a producer, write the `{ updates }` that sets its variable. Declare and bind the flow's outputs now ([author.md](author.md) rule 6).
  Bind each box that needs a resource to the resource the gate named, by name and folder. Ask nothing more about structure or resources.
  A value the request leaves open (a rate, a threshold, a text) is not a question: pick a plausible value, build with it, and name it under `Assumed:`. Never invent an identifier or a URL.
  An unanswered which-of-two takes the first resource named. Report it under `Assumed:`.
  A box the gate marked `none yet` stays a `mock()`, and the final report lists it under `Needs:`. The first line says `not runnable yet`.
  A `not checked` box is looked up now, with the search commands of [author.md](author.md) rule 1.
<!--skill-flavor:draft-build-merge:start-->
  Finish through the merge loop of [Editing an existing flow](../SKILL.md#editing-an-existing-flow), never through `compile`. `decompile` the target afresh: the source from the draft turn carries a stamp of the file `compile` has since overwritten, so `merge` refuses it (`MERGE_ORIGINAL_CHANGED`).
  `merge` of an unchanged source writes nothing and prints no error. Confirm the source changed before you merge.
<!--skill-flavor:draft-build-merge:end-->
  End the turn with the [final report](final-report-template.md). Its first line says `(draft mode)`, because this run stopped at a gate.
- **Keep it**: stop, and report the file as an outline, not a working flow.

Only *Build it* authorizes the build.
Until then the skeleton is an outline. Calling it a finished flow misreports it.
