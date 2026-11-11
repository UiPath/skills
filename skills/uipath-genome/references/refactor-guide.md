# Refactor Guide — rebuild a UiPath automation from its genome

A genome extracted from a UiPath source is built only to refactor that automation, and one extracted from another framework is refactored when the request asks for it instead of a migration that keeps the source's shape: every component is re-authored, never copied, on the UiPath product and project the genome's Components and Build With rows name, while the source keeps running until the switch. The genome is the behavioural contract; this guide adds to [execution-guide.md](execution-guide.md) the refactor questions, the refactor plan, the characterization tests, the run modes and the comparison, and the cutover.

## The contract

1. **Kept:** every rule, outcome, wait, retry and attempt count, every message, mail and log text word for word — a log line in the log the target keeps, wherever that is — the schedule and its time zone, and every output the source leaves — the records, files, mails, messages, tags and statuses it writes, with their names, fields, recipients and formats, the source's own run log aside, which the genome's Error Handling and Configuration Questions decide. Readers outside the export can depend on any output, so none is reshaped or dropped because nothing in the export reads it. A date the source takes from the clock keeps the source's clock: a rebuild that starts at another hour or in another time zone computes the date the source's run would have used.
2. **Changed only with a reason**, and each change is a row of the refactor plan (§ Refactor plan) or of the correspondence table:
   - a source defect, as the genome's defect index says the rebuild follows ([genome-reading-guide.md § Source Defects](genome-reading-guide.md));
   - a user ruling written in the genome;
   - a refactor answer (§ Refactor questions);
   - a platform limit the build meets, recorded with the finding;
   - a change of how that leaves every output the same: one read where the source read once per item, a check the source repeated now made once, duplicated branches merged, a hand-written guard replaced by the platform's own (a lock on running jobs by a queue's unique reference), dead code, unused dependencies and the source's workarounds for its own platform dropped.
3. **A behaviour the genome leaves to the user** — an evident intent only the step's purpose shows, an open question — keeps the source's behaviour until the user rules ([genome-reading-guide.md § Source Defects](genome-reading-guide.md)).
4. **Retries and re-runs are safe.** A write the rebuild retries, or that a second run of the same inputs would make again, first checks whether it already went through, so a retry never repeats it; where the source repeated it, that is a plan difference with this reason. The reads and checks a run's writes depend on run before its first write, so a failed read stops the run with nothing half done. Where that puts time between the read that decides a write and the write — reads batched at the start, items queued for later — the item is read again just before its write, and one changed meanwhile is left alone and reported.
5. **Carried over from a UiPath source, not re-derived:** the Object Repository and inline targets ([source-migration-guide.md § UI Target Locators](source-migration-guide.md)), the data files and test variations, the project's activity defaults as the new project's settings when the target is an RPA project, the libraries the source consumes, installed as packages, and the configuration of each connector activity — connector, object, operation, fields — from which the rebuild authors the same call where the build cannot resolve it from a live connection. From another framework's source, the UI targets, test data and credentials migrate, and each kind of source step is built, as [source-migration-guide.md](source-migration-guide.md) states; its rule that the rebuild keeps the source's names and shape gives way to § Refactor plan.

## Refactor questions

Asked after the genome questions and before the split questions ([configuration-questions-guide.md](configuration-questions-guide.md)). The targets are the genome's: each component is built on the product and project its Components and Build With rows name, and those targets decide which split and scaffolding questions apply. Options are prepared from the genome — its steps, Transactional Shape and Handoffs — and from the Source Map's deployed-state rows (§ Provenance):

| Topic | Question | Options (first = Recommended) |
|---|---|---|
| Rulings *(each source defect whose Rebuild follows cell leaves the choice to the user, and each evident intent the genome marks `*[Inferred]*`; code that can never run is dropped by the contract, never put to a ruling)* | `<the defect in a few words>`: keep the source's behaviour, or `<the evident intent>`? | The intent (Recommended when it changes only how a run counts, logs, retries or recovers — a wrong count, a retry that repeats a write, a fault that hides what the run did or stops the other items); the source's behaviour (Recommended when the intent would change a business outcome — what is written, to whom, for which item — or would send a mail or message the source never sent: that is the owner's to decide) |
| Run modes | Build a shadow mode and a write-test mode (§ Run modes)? | Both (Recommended when the automation writes to a system of record or reaches people, and no test environment holds data like production's); a dry-run switch only, which reads and writes nothing; neither |
| Run record | How does a run report what it did? | A run record and a failure alert (Recommended when the source's runs can skip items or fail without notice): each run's start, end, status and counts, and each item skipped or failed with its business key and reason, in a store the owner reads, plus a mail to the owner when a run fails; the logs only |
| Connections *(a connection the deployed state shows signed in as a person)* | Which identity does `<connection>` sign in as in the rebuild? | A service account of the same connector that the deployed state shows the source already using elsewhere (Recommended when there is one: a person's account makes every write look like that person's and stops the run when the person leaves); the source's identity; a service account the user names. The identity decides who appears as the author of every write and which fields and records the run can read, so a changed identity's access is checked before the first live run (§ Cutover) |

Rules:

1. The answers are recorded under `Refactor` in the Configuration Answers, one line per component: `<component> — modes <both | dry run | none> — run record <yes | no> — connections <kept | <service account>> — rulings <defect: intent | source>, …`. A ruling becomes a plan difference (§ Refactor plan) and is offered in the completion report as a genome edit for `uipath-planner`, so the genome states the contract the rebuild follows.
2. Unattended runs take the Recommended option of every refactor question, as [configuration-questions-guide.md](configuration-questions-guide.md) takes every default. The Source Map's `Requested change` row is the user's own answer to the topics it names: each is answered, never asked again, and recorded `(from the request)` in the Configuration Answers and the completion report.
3. A component the Source Map's `Requested change` row records as retired or folded into another gets no project; every output a folded component left is still written, by the component it is folded into.
4. The split questions are asked only for the components whose target is an RPA process: any other target works its items in its own loop, and every outcome the Transactional Shape lists is still owed — each item retried and reported on its own, one item's failure never ending the others.

## Refactor plan

Written to `refactor-plan.md` in the hand-off folder ([completion-report-guide.md](completion-report-guide.md)) once the questions are answered and before any project is created, and read by every group:

1. **Decisions:** the refactor answer line of each component (§ Refactor questions rule 1), then the projects the genome's Components and Build With rows name, each with its product; projects are created ([execution-guide.md § 1.4](execution-guide.md)), groups planned (§ 2.1), built through the target's owning skill (§ 2.2) and wired (§ 2.3) from those rows and the genome's Handoffs.
2. **Differences:** one row per output the rebuild produces differently from the source — `# | Source | Rebuild | Reason` — the reason one of the contract's (a defect with its index row, a ruling with its date, an answer, a platform limit with its finding, a retry made safe). A change of how that leaves every output the same is a row of the correspondence table, not of this table.
3. **Kept outputs:** each store, file, mail, message and tag the source writes and the rebuild writes the same way, with its name and fields or recipients: the list the comparison and the characterization tests check.
4. **Not proven until it runs:** each assumption the offline build cannot prove — a connector's answer shape, a trigger's input, a limit, an identity's access — with the run that first shows it (the first shadow run, the write test, the first live run) and what the rebuild does when it is wrong. Groups add the assumptions they meet.

The build names its own steps and groups them for the target — a refactor, not a migration — each display name saying what the step does in the business's words, and keeps every text a person or another system reads as the source spells it. The correspondence table of [source-migration-guide.md § What the executor records](source-migration-guide.md) is written per component, with every source workflow and step the rebuild does not keep under its own name and place; its Reason cell cites a plan row, a fold, a retirement or the kind of how-change.

## Characterization

The source's behaviour is pinned in tests before the rebuild's logic exists, so the rebuild proves that it changed the internals and kept the outcomes:

1. **Before a group builds a step's logic, it builds that step's characterization tests:** fixed inputs and the outcome the source produces from them, for every rule and branch of the step and every acceptance criterion it serves. They are written in the owning skill's test facility — test cases an RPA project runs locally, the evaluation rows of an API workflow or a flow — under that skill's rules for when they run (a run that needs the user's consent or a tenant waits for it), and the logic the target runs as code (a script step, a coded workflow) is also checked offline by the run's own check, so a build with no tenant still runs its characterization.
2. **Texts are compared with the source's own.** Each mail, message and log line the rebuild writes is checked against its text in the source workflow, spacing and punctuation included, with the values the test supplies.
3. **A plan difference is a test of the rebuild's behaviour** that names its row; every other test expects the source's outcome.
4. **Recorded runs are replayed when the user has them** — job logs with the items each run handled and what it did, the records a run wrote: the rebuild's decisions on those inputs equal the source's, except the plan's differences.
5. **The source is not run to make expectations** against production systems; its outcomes come from its workflows, the genome and the recorded runs.

The results — tests per step, passed, and the plan rows they cover — go in the completion report.

## Run modes

Built when the Run modes answer asks for them, in every component that writes:

1. **One required setting, `mode`:** `shadow`, `write-test` or `live`, with no default; a missing or unknown value stops the run before its first read, naming the setting.
2. **Reads run in every mode; writes run only in live mode** — every record, file, mail, message, tag and status the run writes, in the source's systems and in its own stores — except in write-test mode, which writes for one item only: one the source would write the same way in the same run, its mails only to the test recipient the configuration names.
3. **In shadow mode each write a live run would make is recorded instead**, as a would-do record in a store the rebuild owns: the run, the item's key, the action and what it would write — fields, recipients, subject, text. The run writes nothing else.
4. **The shadow keeps its own done-marks** where the source marks its work done in a system both read (a tag, a status, a record) and the shadow cannot run before every source run that writes the mark — a source started on events, many times a day. It records its marks in its store and reads each item as it would be had the source not run, so the source's marks do not hide the work the shadow must decide. A shadow that runs before each source run reads the systems as they stand.
5. **The shadow sees the source's inputs:** it runs just before the source's run, with the date and time window the source's run uses.
6. **The comparison is a read-only check built and tested with the rebuild:** given one source run — its job logs, the records and mails it left — and the shadow's would-do records for the same inputs, it lists each item as the same, different as expected (citing the plan row), or to look at, and prints the counts per run.

The stores the run record, the would-do records and the shadow's marks need are platform resources the rebuild adds: Platform Dependencies of the plan's Decisions, created per the Data Fabric answer ([configuration-questions-guide.md](configuration-questions-guide.md)) or listed in the open items.

## Cutover

The refactor's open-items file for the solution ([open-items-guide.md](open-items-guide.md)) ends with a `## Cutover` section, after Triggers, in the same voice — one step per checkbox, for the engineer:

1. **Shadow run** — when modes were built: deploy in shadow mode into a folder of its own, its trigger before the source's; run the comparison after each run until a set number of runs (the user's, five by default) shows nothing to look at.
2. **Write test** — when write-test mode was built: one run in write-test mode; read back every write, including the identity it was written as. A second item the run must fail or skip proves the failure path's writes too — a failed status, an error mail.
3. **Access check** — when a connection changes identity: one read of every field and record the steps read and write, on that connection, before the first live run.
4. **Switch,** in one change window: the source's triggers disabled and its pending, running and suspended jobs finished or stopped before the rebuild's triggers are enabled — a disabled trigger starts no new job but leaves those running, and two implementations writing at once can repeat or interleave each other's writes; `mode` set to `live` when modes were built; after every deploy or upgrade, every trigger (enabled or not, its input, the identity it runs as) and every connection binding read back.
5. **Rollback:** the criteria (a failed run, a difference to look at, an outcome missing) and the steps — the rebuild's triggers off and its jobs finished or stopped, then the source's back on; the source's processes stay deployed until retirement.
6. **Hypercare:** the first live runs compared with the runtime baseline of the Source Map.
7. **Retirement:** the source's processes and triggers, the retired and folded components, and each queue, asset and connection that neither the rebuild nor another automation uses (for a UiPath source, the deployed state's other processes); a queue once it holds no open item.

## Done

Beyond [execution-guide.md](execution-guide.md)'s list, a refactor is done when the refactor plan is written, every step's characterization tests run with their results in the report, the run modes and the comparison are built where the answer asked for them, and the Cutover section is written. The completion report adds one line: `Refactor: <component → target | folded into X | retired>, …; plan refactor-plan.md (<n> differences, <m> unproven); characterization <passed>/<total>; modes <both | dry run | none>; comparison <built | not built>`.

## Deployed State

What runs is the Orchestrator process, not the package: each process binds one package version, can override any binding of the package, and owns its triggers, so the binding a process overrides is the value that runs — the genome's Configuration Question default is the override, and the package's value is in the Source Map. An event trigger is the one the deployed state records, read from the genome's Deployment, never inferred from the entry point's event arguments.

## Provenance

How the build reads a UiPath source's Source Map rows ([genome-reading-guide.md § Source Map](genome-reading-guide.md)):

| Row | The build reads it for |
|---|---|
| The source | the project or solution the carry-over (§ The contract rule 5) reads, and the one the cutover retires |
| A workflow step | the source workflow whose rules and texts the step's characterization tests check (§ Characterization), and the source side of the correspondence table |
| A test case | the test case and its checkpoints, migrated and kept |
| A step's data set | the data variation file carried over (§ The contract rule 5) and used as characterization inputs |
| Inventory | what the carry-over covers |
| Deployed state | the bindings that run (§ Deployed State), the event triggers, the Connections question's identities, and the Retirement step (§ Cutover) |
| Runtime | the hypercare baseline (§ Cutover) |

A UiPath source has no inventory script, so its Source Map gets no mechanical export check at preflight.

## Anti-patterns

1. **Copying a source workflow into the rebuild**, or porting it activity by activity: a refactor re-authors each component from the genome.
2. **Building on a target the genome's Components and Build With rows do not name** — a flow or an agent because it is newer, a queue because the source had one. Another target is a `uipath-planner` edit.
3. **A changed output with no plan row**, an output dropped because nothing in the export reads it, or a defect fixed that the genome says the rebuild keeps (§ The contract).
4. **A shadow that writes, or that decides from the source's done-marks** (§ Run modes).
5. **Logic built before its characterization tests**, or tests whose expected values come from the rebuild instead of the source (§ Characterization).
