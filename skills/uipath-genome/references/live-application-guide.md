# Live Application Guide — exploration and the live healing pass

The two live phases of a migration's UI targets ([ui-target-migration-guide.md](ui-target-migration-guide.md) rule 4) run when the Live application answer names a reachable application — the target application or a comparable instance of it ([execution-guide.md § 1.3](execution-guide.md)): exploration, which walks the application before the targets are derived and ends with a contract probe before the first part that authors, and the live healing pass once every workflow is linked. What each kind of instance lets a verdict say, and the live checks every UI migration writes: [ui-target-migration-guide.md § Verifying targets](ui-target-migration-guide.md).

## Driving the application

1. **Drive it yourself, read-only, outside the healing pass's runs.** Open pages, menus and lists, type into a field to make a popup appear, and cancel out; never submit, save or confirm. Where a step the run does not take blocks the way — a sign-in, since the run never types a password, or a page reached only through a step that writes — ask the user to get past that step, then carry on.
2. **Leave the machine as it was.** Record the window baseline before driving and close only the windows the build opened, as the owning skill's run procedure prescribes; never close what the Live application answer says must stay open.
3. **Use the UIA package's live capabilities** — driver default, attribute listing, selector evaluator, target validation, snapshot reload, element-interaction probes ([selector-translation-guide.md](selector-translation-guide.md) rule 15) — with their syntax routed from the package guide. Stale refs are normal: every capture re-mints them, a driver-default call can invalidate the refs of the capture it read from, and a click that re-renders a widget (a search box or prompt moving into a popup) invalidates its refs too; re-capture rather than retry.
4. **A comparable instance is checked through copies.** Copy the definition to a scratch file, substitute the selector variables with values present on that screen and the scope with that instance's, and run the validator against the copy — the project's own definitions and scope are never pointed at the other instance.
5. **Captures and probes work in a scratch project in the working folder**, on the build's package versions, never in a project of the build — exploration's, the contract probe's and the healing pass's recaptures alike: every live command that captures names the scratch project, because a definition generated from a capture stores the capture's screenshot, whatever the screen showed, in that project's `.screenshots/` folder, and the owning skill's target-capture procedure registers what it finds in that project's Object Repository. Probe workflows are written there too; what a probe settles goes into the notes, so no part of the offline migration runs one.

## Exploring — before the targets are derived

Explore once the migration preflight has derived the catalogs and before the target spec is written ([source-migration-guide.md § Migration preflight](source-migration-guide.md) step 3a): walk the screens the genome's UI steps reach, in the order the steps reach them, and write one **application notes** file per application, `applications/<application-slug>.md` in the hand-off folder ([execution-guide.md § 3.3](execution-guide.md)). The target spec is derived with the notes, every UI part reads its applications' notes ([execution-parts-guide.md](execution-parts-guide.md) item 6), and so does the engineer who heals the targets later. The notes answer what the offline migration would otherwise go back to the application for; a question they leave open becomes a live-checks row, not a probe. Five sections, the last written by the contract probe:

1. **Windows and navigation.** Every window, tab and dialog the steps reach: how it is reached (a menu path, a URL, a button), the window selector the driver reports for it, the part of its title that stays the same while the automation works in it and the part that varies ([selector-translation-guide.md](selector-translation-guide.md) rule 9), the windows it owns, the pop-ups that can interrupt it, and the card that reaches it ([ui-target-migration-guide.md § Object Repository identity](ui-target-migration-guide.md) rule 2). Also how the automation starts the application clean: the browser profile or session the card opens it in, the sign-in, and what an earlier session leaves behind for the next one (a cart, a saved filter, a remembered user).
2. **Input method.** The method each application takes, proven while driving it as the UIA package's input-methods guidance prescribes, and the interactions that need another (special keys, date inputs). Each screen of the application carries the proven method, so every card linked to it runs with it; an application where no method was proven keeps the default.
3. **Structures.** Per table, tree and list the steps act on: what the driver exposes — one grid cell's table attributes, whether a list or tree exposes `items` and takes Select Item, rows that render only once scrolled into view, how a type-ahead's popup and value display render — and the row of [ui-target-migration-guide.md § Composite interactions](ui-target-migration-guide.md) this settles.
4. **Selectors.** Per interaction family, the verdict of the procedure below, with what the package's selector-improvement guidance changed in the derived shape: the attributes that hold across instances, the generated ones to drop, and the collisions found.
5. **Contracts.** Each shape the build repeats across files, how it is built, and what its probe showed (§ Contract probe).

**Verdict per family.** Families to walk for a typical form-driven application: window scope; labelled text input; prompt / type-ahead (leaf, popup entry, value display); custom list (combobox, option, displayed selection); checkbox / radio; segmented date; command button and icon button; menu root and revealed level; grid header and cell; search box and result link; dialog close and error banner. Expect to reach only some of them: a family needs a page that shows it in the state the step needs, and reaching such a page read-only is the binding constraint, not the probing. For each family reached:

1. **Capture the screen** that holds the family (a snapshot of the window), with the widget in the state the step needs (list open, value accepted).
2. **Ask the driver for its own shape**: the driver default for the acting node with the family's activity type. Compare tag and attributes with the shape the translation rules derive from the catalog, and the driver's anchor, when it has one, with the caption a derived `<nav>` path starts from; a derivation that disagrees with the driver on which node is acted on is wrong, not "different".
3. **Read the acting node's attribute listing** and strike every attribute the derived selector names that the node does not carry. Read the label's, the value display's and the popup entry's listings the same way ([selector-translation-guide.md](selector-translation-guide.md) rule 16).
4. **Evaluate uniqueness** (the selector evaluator, one ref per tag) for the derived selector and for the fixed one — with the popup open for a pick, after the pick for the value display, so the shared-text trap shows. A selector with a `<nav>` path goes to target validation instead, and its screenshot shows the node the path landed on.
5. **Probe capability where the pattern depends on it**: the control's `items` for a list (Select Item or open-and-click), one grid cell's attribute listing for `tableRow`/`colName`/`rowName` (table attributes or text-pinned rows).
6. **Fix the rule before the family is derived**, then re-run steps 2–4 on a second instance of the family.
7. **Record in the notes**: the driver's default, the shape the family ships with, the collisions found, and the label the family carries — `verified` or `shape-verified` — and why. A family left unexercised is recorded as such, and a *partly* exercised one says which part — an editable grid cell whose row and column matched but whose input was never reached is not the same as a cell that was never seen.

**Seeds.** During the walk, exploration resolves the seed definitions the contract probe and the offline migration copy — a screen seed from the first page's window and an element seed from one element on it, with the driver's defaults and before any sign-in — into the working folder ([offline-definition-workarounds-guide.md § Starting-point definition file](offline-definition-workarounds-guide.md)).

### Contract probe — before the first part that authors

A contract is a shape the build repeats across files: the card that attaches to a window and the scope its targets carry, how a dialog is checked for and how it is acted on, how a table cell is read, a pattern helper with its verify, the input method on a card. Per-file validate and build check that each copy is well-formed, not that the shape acts on the application, so a wrong contract validates and builds in every file it reaches and shows only in the healing pass. Once the target spec is written and the shared decisions fix the build's contracts, and before the first part that authors:

1. **One probe per contract, not per element.** In exploration's scratch project (§ Driving the application, item 5), author one workflow per contract exactly as the build will write it — the same activities, card and window scope, verify options and input method, with its targets built from the target spec the way the offline migration builds them — then link and validate it.
2. **Run it read-only** against the live application through the owning skill's debug-run procedure, on an instance of the shape that changes nothing: a dialog opened and cancelled, a cell read, a window checked for. On a comparable instance its definitions take that instance's scope and values (§ Driving the application, item 4).
3. **A probe that fails fixes the contract** — the rule, the shape or the helper it comes from — before any part writes it, and runs again.
4. **Record each contract** in the notes with how it is built and what its probe showed; a contract no read-only instance reaches is a `run` row of the live checks.

## Live healing pass — once every workflow is linked

The live healing pass meets the finished build: every UI workflow of the run is linked and validated, and the acceptance verdicts are still to come ([execution-guide.md § 3.1](execution-guide.md)). It starts from the live checks and closes their rows as it goes.

### Checking every target read-only

Walk the read-only rows of the live checks screen by screen:

1. **Validate each element's strict step** with target validation, the screen in the state the element needs; a parametrised element at two values of each selector variable (two rows, two captions).
2. **An element that does not resolve, or resolves another node, is captured again** with the owning skill's target-capture procedure, in the scratch project (§ Driving the application, item 5), given its semantic description as the element to find. Take the selector the driver gives for the node found, and put each selector variable of the spec entry back in the attribute that carries the varying part; keep the window's scope unless the live window proves it wrong. Edit the spec entry and let the run's target tool replace the element, then validate again. A fix that shows the family's rule was wrong is applied to the family's other elements, each validated.
3. **On a comparable instance only the family samples are checked** (§ Driving the application, item 4), and the family's elements take its label.
4. **Close each row** with its state, and change the element's label in its description in place ([ui-target-migration-guide.md](ui-target-migration-guide.md) rule 2). The `run` rows, and the elements of a screen only a run reaches, stay open for the runs.

### Runs — only on the user's yes

Where the Healing pass answer allows it, after the read-only check, on the instance and the data the answer named — the runs enter and change data in the systems the automation drives:

1. **Run the workflows and test cases the answer covers,** those the `run` rows name first, through the owning skill's debug-run procedure, with the run's settings pointing at the named instance.
2. **A target that fails** takes the owning skill's runtime selector-failure recovery; its accepted selector is folded into the spec entry as a recaptured one is (§ Checking every target read-only), and written back through the run's target tool.
3. **A step that went through can still be a miss**, and a miss is fixed like a failure:
   - a target found only through a semantic step or another fallback, which a target carries only where the user or the owning skill's recovery added one: the run log warns `<target> was found using fallback method '<method>'.`, every lookup first waits out the strict step's timeout, on every item of a loop, and nothing confirms the fallback reached the intended control — a target is healed when its strict selector resolves it;
   - a read or a collection that came back empty while the screen showed something to find;
   - a pick whose verify passed on another entry than the step asked for.
4. **A fix re-runs every workflow and test that uses what it changed**, as [execution-guide.md § 3.2](execution-guide.md) states for acceptance fixes.
5. **Every data change the runs made** goes into the completion report's section for it ([execution-guide.md § 3.3](execution-guide.md)).

The runs are the local runs the acceptance verdicts cite ([execution-guide.md § 3.1](execution-guide.md)), and each `run` row closes with what its run showed.

## Anti-patterns

1. **Deriving the target spec before exploring a reachable application, or exploring it without writing the notes and the seeds.** The offline migration then goes back to the application for the windows, the clean start, the input method and the grid shapes, and the spec ships the rules the driver would have corrected (§ Exploring).
2. **Starting the offline migration on a reachable application without a contract probe.** A wrong contract then validates and builds in every file it reaches, and only the healing pass finds it (§ Contract probe).
3. **Submitting, saving or confirming outside the runs, or running them when the user did not allow it or on data the user did not name** (§ Driving the application, § Runs).
4. **Taking a step's success for a healed target** — a fallback, an empty read, a wrong pick — **or a family sample on a comparable instance for a check of every target** (§ Live healing pass).
5. **Fixing a failing element in the workflow by hand, or with the create command**, instead of in its spec entry through the run's target tool, whose replace keeps the links ([ui-target-migration-guide.md § Object Repository identity](ui-target-migration-guide.md) rule 4).
