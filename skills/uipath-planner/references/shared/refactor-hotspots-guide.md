# Refactor Hot Spots Guide — the refactor review

The refactor review of an extracted genome, run only when the user asks for it ("check the refactoring opportunities", "analyze the process and suggest refactors"): where to look for a place the rebuild may be better shaped than the source, how to discuss each one with the user, and how the design agreed goes into the genome. Read by `edit`'s refactor review ([edit-guide.md](../edit/edit-guide.md)). A hot spot is a suggestion for the user to weigh, never a rule: the source's shape is always one of its options, and none is applied unless the user chooses it.

## The review

1. **Only on request.** Extraction never runs it unasked; a request to analyze the process starts it once the genome is written, and any other refactor or migration request is told of it once ([extract-guide.md](../extract/extract-guide.md) Step 7).
2. **Look for every spot below where its Look for line points.** The review may also revisit a Retire, Fold or Target answer the extraction recorded ([extract-guide.md](../extract/extract-guide.md) Step 6c), when the user asks for it or a spot found changes it.
3. **Discuss the spots found with the user, in the session.** Present them in one message, each with where it is, why it may be worth reconsidering, and the options with what each changes and requires, the source's shape among them. Ask the facts each Keep as is when line turns on — another caller, the owners, release cycles, the business cadence — that the genome and its Source Map leave open. Once they are known, say which option the facts point to and why; the user decides each spot, and a spot left open keeps the source's shape.
4. **A pattern the catalogue does not list** — the source building by hand a component, a call, a trigger or a wait the target platform offers — is raised the same way. How a step is built is no hot spot: the technology of each capability (mail, spreadsheets, documents), where the run logs, how closely the steps follow the source and a library's layout are `uipath-genome`'s build questions, and a flow's unit of work, split, item store and coordination are the Transactional Shape's ([transactional-shape-guide.md](transactional-shape-guide.md); [skill-mapping-guide.md § Refactor Targets](skill-mapping-guide.md) rule 3).
5. **Propose the new architecture, then apply it.** Once each spot is decided, show the design the decisions make in one message — the components with each one's target, the folds and libraries, the handoffs and triggers that change, and what keeps the source's shape — and apply it on the user's yes, written as Step 6c writes a refactor answer:
   - a folded component keeps its row, its Rationale opening `Folded into <component>:`; a step given to another skill is its Build With row;
   - a component rebuilt as a library is rewritten in the library form of [genome-format-guide.md](genome-format-guide.md) — its Interface one table per public workflow, no trigger, delivered as § Two Levels rule 6 states — its Source Map step table kept current with it ([extract-guide.md](../extract/extract-guide.md) Step 6b);
   - a Handoffs row to a folded component from any component but the one it is folded into names that one instead, and a row to a library names a library workflow call;
   - the `Requested change` row records a fold as `Fold: <component> into <component>`, with the caller's step it runs at when the caller started it mid-run, and every other decision — a changed trigger, a changed output, a step given to another skill — in the user's words, naming each component it touches and what changes for it; Platform Dependencies, Workflow and handlers keep the source's, as for every refactor answer.
6. **An option that changes an input or output another party reads says so in its text**, since it changes only on the user's word ([extract-guide.md](../extract/extract-guide.md) Step 6c).
7. **A request that leaves no one to discuss with** (an unattended run) gets the spots found and the design they suggest in the closing message, and the genome stays as it is.

## Hot spots

### 1. A sub-process run once per unit of work by one caller

- **Look for:** a Handoffs row whose mechanism starts a process from inside the caller's per-item steps, passing the item and using the result, where the callee has no Triggers row and no other caller.
- **Why reconsider:** a second package, a contract between two projects and often a second sign-in for what is one transaction.
- **Options:** fold it into the caller, its workflows in the caller's project, sharing the caller's sign-in and transaction; keep it a process.
- **Keep as is when:** another caller exists or is planned, it runs on other machines or credentials, another team owns it, or people start it on its own for re-runs.

### 2. A helper process several components start

- **Look for:** Handoffs rows from several components to one process with no Triggers row or queue of its own, each start asking for the same service — a notification, a lookup, a file conversion.
- **Why reconsider:** a job start per call and a process contract for what a library workflow does in the caller's own run.
- **Options:** a library whose public workflows each caller invokes in its own run; keep it a process.
- **Keep as is when:** it needs an identity, machine or isolation of its own, or something outside the automation also starts it.

### 3. Polling where a trigger would do

- **Look for:** a Triggers row whose schedule runs far more often than the business cadence; the Source Map's runtime row showing most jobs ending with no item worked; steps that count empty runs or wait for a file to appear.
- **Why reconsider:** most jobs take a robot for nothing, and an item still waits up to a full interval.
- **Options:** a time trigger at the business cadence, its outputs arriving at that cadence; a queue trigger, when the polling waits for queue items; an event trigger on the file or mail the polling waits for, where the target can start on it; keep the source's schedule.
- **Keep as is when:** the cadence is the business's own, as when items arrive all day and are due within minutes.

### 4. One application's screens spread over several UI libraries

- **Look for:** UI library components whose Target Applications name the same application, each with its own copy of the main window and the sign-in. Raised for a UiPath source only: a migration's build offers that merge among its own questions.
- **Why reconsider:** one Object Repository per application keeps one definition of each screen.
- **Options:** one UI library for the application, the others folded into it; keep the source's libraries.
- **Keep as is when:** other automations consume the libraries as they are, or different teams own the screens.

### 5. An output file several jobs write at once

- **Look for:** a file the run appends to or rewrites in a shared location — a summary, a status list, a report — where the Transactional Shape's As-is or the Triggers rows let several jobs run at once: several robots, overlapping schedules, a queue worked in parallel. The source's own run log is the evidence policy's ([extract-guide.md](../extract/extract-guide.md) Step 3), never this spot.
- **Why reconsider:** two jobs writing at once can interleave or lose each other's lines, and a job that finds the file held by another fails.
- **Options:** one file per job, named by its run, merged where the readers need one; a platform store each job writes — an entity, the queue item's output — with the file written from it once the work is done; keep the shared file as the source writes it.
- **Keep as is when:** the jobs that write it never overlap in practice, as the schedules or the job history show.

### 6. A person's decision waited for by hand

- **Look for:** steps that send a person a mail or a file and then poll a mailbox, a folder or a sheet for the reply; a status column a person edits that a later run reads; a run kept waiting for an approval.
- **Why reconsider:** the polling costs runs or holds a robot, a free-text reply is parsed by hand, and nothing shows who holds the decision or for how long.
- **Options:** a task in Action Center that the run waits on, the job suspended meanwhile so it holds no robot, the person answering in a form with the fields the process reads — the person then works the task instead of a mail; keep the source's message and polling.
- **Keep as is when:** the people who decide have no access to Action Center, or the reply comes from outside the organisation.
