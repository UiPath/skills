# Refactor Hot Spots Guide — places where a better shape may exist

A catalogue of places in an extracted genome where the rebuild may be better shaped than the source, read at [extract-guide.md](../extract/extract-guide.md) Step 6c and by a redesign edit ([edit-guide.md](../edit/edit-guide.md)). A hot spot is a question for the user, never a rule: the source's shape is always one of its options, and none is applied unless the user chooses it.

## Asking

1. **Ask the design inputs first, once.** The answers rest on facts a genome rarely holds: volumes and cadence, the robots available to the process, whether a failed item is retried, where logs go, when outputs are due, which channels a mail may use. Ask those the genome and Step 1 leave open, in the same message as the first hot spot; one left unanswered is a reading entry of the process genome, or of the component genome when one component uses it ([genome-questions-guide.md § Open Decisions](genome-questions-guide.md)).
2. **Look for every spot below** in the steps, Handoffs, Transactional Shape, Platform Dependencies and Source Map, and ask one question per spot found, after Step 6c's Retire, Fold and Target topics. The options are the entry's, each naming what it changes and what it requires, plus the source's shape; none is marked Recommended over the source's shape. A component Step 6c's Fold topic already asked about is not asked again as spot 1.
3. **A pattern the catalogue does not list** — the source doing by hand what the target platform offers — is asked the same way, with the source's shape as an option.
4. **An answer is a refactor answer.** It is recorded in the `Requested change` row as `Hot spot: <spot> → <choice>` and applied as the edit request it is ([edit-guide.md](../edit/edit-guide.md)): a component folded, merged, retargeted or added; a unit of work or a split decided (the flow's `Decided:` line); a store, an asset or a trigger changed.
5. **A spot left unanswered keeps the source's shape.** Unattended runs ask nothing: each spot found is an Open Decisions entry at the section or component it concerns with one `instead:` per other option: `business outcome` with `Builds now:` the source's shape when an option changes an input or output, otherwise `run behaviour` with `Recommended:` the source's shape.
6. **An input or output changes only on the user's word** ([extract-guide.md](../extract/extract-guide.md) Step 6c). An option that would change one — a file, mail, recipient, report, log, store or queue another party reads — says so in its text.

## Hot spots

### 1. A sub-process run once per unit of work by one caller

- **Look for:** a process with no trigger of its own that one caller starts inside its per-item work, passing the item and using the result.
- **Why reconsider:** a second package, a contract between two projects and often a second sign-in for what is one transaction.
- **Options:** fold it into the caller as workflows of the caller's project, sharing its sign-in and transaction; keep it a process.
- **Keep as is when:** another caller exists or is planned, it runs on other machines or credentials, another team owns it, or people start it on its own for re-runs.

### 2. A helper process several components start

- **Look for:** a process with no trigger or queue of its own that several components start for the same service — a notification, a lookup, a file conversion.
- **Why reconsider:** a job start per call and a process contract for what a library workflow does in the caller's own run.
- **Options:** a public workflow of a shared library each caller installs; keep it a process.
- **Keep as is when:** it needs an identity, machine or isolation of its own, or something outside the automation also starts it.

### 3. Near-identical components that differ only by their data

- **Look for:** two or more components with the same steps over different folders, sheets, queues or applications' data — two intake processes, two report writers.
- **Why reconsider:** every fix is made twice and the copies drift apart.
- **Options:** one component with the differences as configuration; the shared steps in a library, each component keeping only what differs — the choice when each should stay bound to its own queue or schedule for visibility; keep them apart.
- **Keep as is when:** their owners, release cycles or schedules differ.

### 4. Fine-grained items joined by hand-made coordination

- **Look for:** an item per row or record whose items the consumer joins back into their parent by tags or naming, claims through a "first" or "master" item, excludes what other robots hold by listing locked items, or cleans up items left locked ([transactional-shape-guide.md](transactional-shape-guide.md), the As-is Coordination row).
- **Why reconsider:** the joins, claims and clean-ups are the source's own locking, which the target's transaction lock and references can carry.
- **Options:** the parent as the unit of work, its children worked inside its transaction and their outcomes kept per child; the same items with the joins carried by the reference (the parent key leading it) or a record store; keep the source's coordination. Each option keeps the protection the coordination gave ([skill-mapping-guide.md § Refactor Targets](skill-mapping-guide.md) rule 3).
- **Keep as is when:** children are retried, reported or worked by several robots on their own.

### 5. Per-item state a queue cannot hold

- **Look for:** the per-item state [transactional-shape-guide.md](transactional-shape-guide.md) rule 3 names as one a queue cannot hold — values written to an item after it is added that a later step, attempt, run or person reads.
- **Why reconsider:** that rule decides when the split needs a record store beside the queue; the store itself is a choice the user may want to make now, with the design.
- **Options:** name the record store now — a Data Fabric entity, or a database the process owns; leave it to the build's store question.
- **Keep as is when:** the user has no preference; the build asks it.

### 6. An output whose only reader is outside the automation

- **Look for:** a file, log, report or status the run writes and nothing in the source reads — a summary appended to a shared file, the source's own run log, a status file.
- **Why reconsider:** a shared file written by several robots can collide, and a platform store is queryable and kept with the run.
- **Options:** keep writing it as the source does; write it to a platform store (an entity, the queue item's output, the job's log) as well; replace it (Asking item 6).
- **Keep as is when:** its readers are unknown or depend on its format.

### 7. An office application driven for plain data

- **Look for:** steps that open a workbook or document in its desktop application only to read or write values.
- **Why reconsider:** the application adds a machine prerequisite and leaves lock files behind when a run is killed.
- **Options:** file-level workbook or document work with no application; keep the application.
- **Keep as is when:** the step needs the application itself — a template whose exact layout must survive, formulas recalculated, macros, conversion to another format.

### 8. A desktop mail client

- **Look for:** mail sent or read through the mail application of the robot's session.
- **Why reconsider:** a client installed and signed in on every robot, and a profile tied to the robot's session.
- **Options:** a mail service reached through an app registration on a service mailbox; an Integration Service connection; keep the client.
- **Keep as is when:** policy forbids both alternatives, or the mail must leave from the robot user's own mailbox.

### 9. A credential name built from the robot's identity

- **Look for:** a credential read by a name built from the machine or user the robot runs as.
- **Why reconsider:** the name is computed in code, and a new robot needs a new asset.
- **Options:** one credential asset per application with one value per robot account; keep one asset per name.
- **Keep as is when:** robots of one environment must not share an asset.

### 10. Polling and hand-made run control

- **Look for:** a schedule far finer than the business cadence, counters of empty runs, stop flags the run reads, waits for a file to appear.
- **Why reconsider:** triggers, the platform's stop request and a schedule matching the business cadence do the same with less code.
- **Options:** a time trigger at the business cadence, a queue trigger for the consumer, the platform's stop request checked between items; keep the source's run control.
- **Keep as is when:** the cadence is the business's own, as when items arrive all day and are due within minutes.

### 11. One application's screens spread over several libraries

- **Look for:** several UI libraries for one application, each with its own copy of the main window and the sign-in.
- **Why reconsider:** one Object Repository per application keeps one definition of each screen.
- **Options:** one UI library per application; keep the source's libraries.
- **Keep as is when:** other automations consume the libraries as they are, or different teams own the screens.
