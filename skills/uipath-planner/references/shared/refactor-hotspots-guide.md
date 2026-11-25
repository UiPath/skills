# Refactor Hot Spots Guide — places where a better shape may exist

Where to look in an extracted genome and its source for a place the rebuild may be better shaped than the source, read at [extract-guide.md](../extract/extract-guide.md) Step 6c and by a redesign edit ([edit-guide.md](../edit/edit-guide.md)). A hot spot is a question for the user, never a rule: the source's shape is always one of its options, and none is applied unless the user chooses it.

## Asking

1. **Look for every spot below where its Look for line points**, after Step 6c's Retire, Fold and Target topics, and ask one question per spot found. A component the Fold topic already asked about is not asked again as spot 1.
2. **The options are the entry's, plus the source's shape**, each naming what it changes and what it requires; none is marked Recommended. The same question asks the facts its Keep as is when line turns on — another caller, the owners, release cycles, the business cadence — that the genome, the deployed state and Step 1 leave open.
3. **A pattern the catalogue does not list** — the source building by hand a component, a call or a trigger the target platform offers — is asked the same way. How a step is built is no hot spot: the technology of each capability (mail, spreadsheets, documents), where the run logs, how closely the steps follow the source and a library's layout are `uipath-genome`'s build questions, and a flow's unit of work, split, item store and coordination are the Transactional Shape's ([transactional-shape-guide.md](transactional-shape-guide.md); [skill-mapping-guide.md § Refactor Targets](skill-mapping-guide.md) rule 3).
4. **An answer is a refactor answer, written as Step 6c writes Fold:**
   - a folded component keeps its row, its Rationale opening `Folded into <component>:`; a component rebuilt as a library keeps its row and genome, typed as a library; a library made of shared steps is a new row and component genome, and each component that shared the steps calls it there;
   - a Handoffs row to a folded component from any component but the one it is folded into names that one instead, and a row to a library names a library workflow call;
   - the `Requested change` row records a fold as `Fold: <component> into <component>`, and any other answer in the user's words, naming each component it touches and what changes for it.
5. **Unattended runs ask none.** Each spot found is an Open Decisions entry of the business-outcome tier, since it decides what is built, as a `Not covered` object does: in the process genome when it spans components, else in its component genome, `Builds now:` the source's shape, one `instead:` per other option, and named `(D<n>)` in each Components, Handoffs or Triggers row it concerns ([genome-questions-guide.md § Open Decisions](genome-questions-guide.md)).
6. **An option that changes an input or output another party reads says so in its text**, since it changes only on the user's word ([extract-guide.md](../extract/extract-guide.md) Step 6c).

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

### 3. Near-identical components that differ only by their data

- **Look for:** components whose Workflow steps match step for step and differ only in their Configuration Questions' defaults or the names in Platform Dependencies — folders, sheets, queues.
- **Why reconsider:** every fix is made twice and the copies drift apart.
- **Options:** the shared steps as a library component, each component keeping only what differs and its own trigger and queue; keep them apart.
- **Keep as is when:** their owners or release cycles differ.

### 4. Polling where a trigger would do

- **Look for:** a Triggers row whose schedule runs far more often than the business cadence; the Source Map's runtime row showing most jobs ending with no item worked; steps that count empty runs or wait for a file to appear.
- **Why reconsider:** most jobs take a robot for nothing, and an item still waits up to a full interval.
- **Options:** a time trigger at the business cadence, its outputs arriving at that cadence; an event trigger on the arrival the polling waits for — a queue item, a file, a mail — where the target can start on it; keep the source's schedule.
- **Keep as is when:** the cadence is the business's own, as when items arrive all day and are due within minutes.

### 5. One application's screens spread over several UI libraries

- **Look for:** UI library components whose Target Applications name the same application, each with its own copy of the main window and the sign-in. Asked for a UiPath source only: a migration's build offers that merge among its own questions.
- **Why reconsider:** one Object Repository per application keeps one definition of each screen.
- **Options:** one UI library for the application, the others folded into it; keep the source's libraries.
- **Keep as is when:** other automations consume the libraries as they are, or different teams own the screens.
