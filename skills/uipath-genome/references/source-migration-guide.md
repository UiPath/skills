# Source Migration Guide — UI targets and test data at execution

Execution of an extracted genome migrates two things the genome body deliberately leaves out: the **UI targets** (selectors) and the **test data** of the source automation. Both live in the source artifacts folder the extraction writes next to the genome ([genome-format-guide.md § Source Artifacts](genome-format-guide.md)). This guide is framework-agnostic; each source guide's *UI Target Locators* and *Test Data* sections say what the source provides and how its attributes translate.

## Rules

1. **Migrate targets from the catalog before anything else.** When `source/targets.json` exists, every UI activity of the built project receives an Object Repository (OR) target derived from the catalog. The placeholder-selector stub pattern is the fallback only when no catalog exists AND no live application is reachable; a live application is captured with the owning skill's target-capture procedure instead.
2. **Every migrated target is inferred and says so.** Its OR element description starts with `INFERRED (<confidence>)` and names the source control. The first run against the real application is a healing pass; accepted fixes go into the OR element in place so every consumer inherits them.
3. **Migrate test data from the data catalog by default.** When `source/test-data.json` exists, the test project's data files (one per test-component folder) are filled from it by a scripted, reviewable mapping from source variables to test-case arguments, never by hand. Generated placeholder rows are a temporary state, not a deliverable.
4. **Account identity migrates, secrets never.** A login user name becomes the name of a credential asset (`<App>_Login_<USER>`) plus the tenant/environment URL recorded for that account; passwords, tokens and secrets are refused by the migration engine and are entered in Orchestrator. One credential asset per source account is declared as a solution resource.
5. **The argument set is frozen during data migration.** Mappings place source values onto the test cases' existing arguments; a value with no argument goes to the project's configuration workflow or argument defaults and is listed as `unmapped`. Source row counts and execution flags replace generated ones.
6. **Build through the owning skill's contract.** Invoke the owning skill for each build group and perform its mandatory reads (its authoring rules, the installed activity package's core guide and per-activity docs). Activity XAML comes from the skill's discovery commands and per-activity docs, never from memory and never from a bespoke template generator whose templates were not derived from those commands. Validate per file and build per project exactly as the skill prescribes; a generator is acceptable only for repetition of activity fragments already confirmed that way.

## UI targets — pipeline

| Step | Output |
|---|---|
| 1. Load the target catalog and the built workflows | list of UI activities per workflow (activity id, type, display name, arguments and variables) |
| 2. Map every UI activity to a catalog control (or to *none*) | for each application card its source window; for each UI activity its source control (or none), activity type, argument substitutions, semantic text, confidence |
| 3. Derive targets | per element: strict selector from the control's attributes (source guide table), optional label anchor, semantic description, confidence; per window: application/browser selector |
| 4. Create OR screens and elements through the owning skill's Object Repository CLI and target-configuration guidance | one screen per source window, one element per distinct source control (plus substitutions), reused across workflows |
| 5. Link screens then elements into each workflow per the owning skill's target-attachment guidance | linked XAML, placeholder prefixes removed from linked activities |
| 6. Validate every workflow; build; pack | per-workflow report: linked count, created vs reused, confidence, remaining errors |

Mapping rules: every UI activity mapped once, activity ids file-unique; `source/step-map.json` names the source processes of each workflow step, and their dumped steps name the controls; shared widgets (search box, OK, Submit, comment box, menus) reuse one control so the OR holds one element each; literals that the workflow receives as arguments (a person name, a placeholder the source rewrote at run time) become selector variables (`{{Argument}}`) bound to the workflow argument; steps the built workflow has but the source had not (optional pop-up checks, verifications) get no source control, a precise semantic description and low confidence. A **composite source step** (§ Composite interactions) maps to several activities and several elements: the anchor control from the catalog plus the derived elements the source never learned.

## Composite interactions — one source step, several UiPath activities

Test frameworks package multi-step interactions into one parameterised step: type-ahead pick, menu path, option list, find-row-then-act, keystrokes to the focused element. The source guide's composite-actions section names them and dictates the substep wording; this section fixes how execution builds them. **Rule: build the pattern, never the nearest single activity.** The first Certify migration did the latter and shipped workflows that validated and failed: the first popup entry clicked regardless of caption, custom lists driven with a native select action, a two-level menu collapsed into one click.

Before building any UI group of an extracted genome, read the per-control `actions` in `source/targets.json` and the substep wording, classify every UI step against this table, and read the owning skill's control-interaction guidance for the classified controls (option lists, date inputs, tables) as it mandates.

| Pattern | Naive mapping that fails | Build | Derived elements |
|---|---|---|---|
| **Type-ahead pick** — type text, a suggestion list appears, pick the entry matching a caption rule, optional confirm key | type + click "first item" (positional container element); or type + Enter without checking what was accepted | 1. Type the value into the anchor input with key-event input (never set-value: the list only opens on key events). 2. Wait for the suggestion list. 3. Click the entry whose visible text matches the caption rule (contains / equals / nth match) — the caption is a selector variable bound to the typed or matched text. 4. Send the follow-up key if the source had one. 5. Verify the input now shows the accepted value (Verify execution / check element) — the source's `Is Equal To` becomes the acceptance check. Keyboard-confirm variant (type + Enter on a prompt): type, Enter, then verify the accepted value; fall back to the click variant when the verify fails | suggestion entry (text-matched, from the anchor's popup container), accepted-value indicator; low confidence, `derived from <anchor control>` |
| **Option list** — choose an item by caption rule from a list, dropdown or combo | `SelectItem` on a custom (div/li/span) widget; positional `idx` on the item | Probe the anchor control's `items` per the owning skill's select-item guidance. Items present → `SelectItem` with the listed value verbatim. Items absent → click-to-open the anchor, then click the option whose text matches the rule (selector variable), then verify the displayed selection. A numeric index in the source is positional: keep it as an index on the option element and flag it | option entry (text-matched) or option list container; medium when the source caption is literal, low when variable-bound |
| **Menu / tree path** — `A|B|C` from a menu root, levels revealed by hover or click | one click on the root, or a click on the leaf caption anywhere on the page | One click (or hover, per the live probe) per level, each re-resolving its target after the previous level rendered; levels are separate activities, never one target with the leaf text. The last level gets a verify (the page or dialog the leaf opens). Menu roots that appear in several source windows reuse one element | one element per level (text-matched under the menu container); medium for the root (mapped), low for levels |
| **Table row by content** — find the row whose cell(s) match, then click, read, type or verify in that row | store a row number and index into the table with it | Never carry a row integer. Either a row-anchored target (the cell whose text matches becomes the anchor of the row/target cell, selector variables for the matched values) or extract the table, filter in code for the row, then act through a row selector pinned by the matched value. `Last` = last matching row. Multi-criteria finds and-combine the cell matches. Source "popup rendered as table" (suggestion popups) is an option pick, not a table op | matched cell (anchor), target cell in the same row; medium |
| **Table cell** — act on the cell at (row rule, column caption or number) | absolute `tableRow`/`tableCol` | Column by header caption (column caption → header-anchored cell), row by content rule from the preceding find; a literal row number in the source is positional and stays flagged; double-click and follow-up keystroke preserved. A prompt inside a cell (typed value + Enter) is a type-ahead pick inside the cell | header cell, target cell; medium |
| **Read cell / row count / control text** | Get Text on the table element | Get Text or Get Attribute on the row-anchored cell after previewing what it extracts (owning skill's get-text guidance); row count via table extraction or a rows attribute, verified live | as table cell |
| **Keystrokes** — keys sent to the window or the focused element | Keyboard Shortcuts to the browser window / page body; a Delay | Determine the target from the preceding step: the keys go to that element (Type Into text with special-key tokens when they follow typing; Keyboard Shortcuts targeted at the element otherwise). Page scrolling keys are dropped (UiPath scrolls the target into view). A browser refresh becomes the browser navigation activity. Invented shortcuts are forbidden; only keys the source actually sent | none; the target is the preceding step's element |
| **Coordinate click** — click at pointer position or screen x/y | Click with an offset on the page | Identify the intended element from surrounding steps (dismiss a popup, focus the page, an unmapped button) and target it; semantic description; flag `*[Inferred]*` in the report | derived element; low |
| **Set state** — ensure checkbox/radio state | Click | Check/Uncheck with the state (idempotent); radio click plus verify selected | none |
| **Input-method hint** — source switched to key-event input for the fields that follow | ignored | Carry into the affected activities' input mode (key events / hardware, per the owning skill's input-methods guidance); the type-ahead pattern needs it | none |

Every derived element is named `derived from <anchor control> — <pattern>` in its description, labelled `INFERRED (low)` unless the table says medium, and listed in the report under the healing-pass note as the first targets to verify live. The first live run must exercise every type-ahead and menu-path step; a step that "passes" by clicking the wrong entry is the failure mode this section exists to prevent, so the verify sub-step of each pattern is mandatory, not optional.

Confidence: **high** = developer identifier present (automation id, id, aria-label, name); **medium** = only label, inner text, title or class (fuzzy selector + label anchor); **low** = only XPath/outerHTML, or no control (semantic only). Targeting-method policy: label → fuzzy main selector with a label anchor; no label and high → strict; no label and medium → fuzzy; position index present → strict with index (never anchored); semantic selector always added as runtime fallback.

Creating and linking mechanics are the owning skill's Object Repository CLI, target-configuration and target-attachment guidance; follow them. Offline specifics the guidance does not cover: a definition can only be updated once it exists (export one from an activity that already carries a target, then mutate it only through the CLI); the activity-type option accepts only its own enum values; a single link call with more than about a dozen entries can exceed the shell command-line length — batch; the designer leaves `~<Workflow>.xaml` recovery copies in the project after linking — delete them before packing; analyzer rules such as SecureString public arguments or large position indexes fail `build` and `pack` but not `validate` — decide with the user whether to lower them or pack with the analyzer skipped.

## Test data — pipeline

| Step | Output |
|---|---|
| 1. Decode the data catalog | recordsets as named rows (schema = layout variables, in column order); process → recordset links |
| 2. Per test-component folder of the test project, decide the mapping | per data file: its source recordset(s) and rows; per argument: the source variable (with a transform when needed), a join, a constant, a lookup into another recordset, or keep the default |
| 3. Check coverage, then migrate | every argument has a rule, credentials refused, rows rewritten, coverage report per file (migrated / kept / missing) |
| 4. Rebuild the project | data files are not compiled, but rebuild once to catch argument drift |

Transforms that recur: organisation-with-manager strings (`Org (Manager)` → org, manager), On/Off → boolean, country → region code, dates normalised, placeholder markers (`^`) → empty, user name → credential asset name and tenant URL.

Report per project: rows and cells migrated, values kept at defaults and why, values the source had but the test case has no argument for (and where they went), source quirks carried over (typos, wrong-field values, historical worker names, stale run dates). Historical run dates and worker names must be refreshed before a run on a live tenant; say so in the report.

## What the executor records (no prescribed file formats)

Mechanics — creating screens and elements, updating definitions, fuzzifying, linking — are the owning skill's Object Repository CLI and target-configuration guidance; read them and use them as they are. The genome skill only requires that, at the end, these facts are recorded and reviewable:

- per UI activity: the source window and control it was derived from (or "none"), the resulting strict/fuzzy selector, anchor and semantic description, the confidence tier, and the OR element it links to — one OR element per distinct source control, reused across workflows;
- per composite source step: the pattern applied (§ Composite interactions), the activities it expanded into, the derived elements created, and the verify sub-step;
- per data file: the source recordset(s) it was filled from and, per argument, whether the value came from the source, stayed at its default, or had no source counterpart; credentials appear as asset names and environments only;
- per workflow: validate result after linking, and any activity still without a target.

How that is scripted (mapping files, registries, validators) is the executor's choice for the run; the reports are the deliverable.

## Anti-patterns

1. Shipping placeholder targets when the source export carries locators.
2. Hand-typing selectors into XAML or definition files; the OR CLI and the derivation rules are the only path.
3. Copying passwords, or dropping the account identity along with them (which loses which role each scenario ran as).
4. Authoring test rows from the genome's defaults when the source has recordsets.
5. Widening a test case's argument set to fit the source layout instead of mapping onto the existing arguments and configuration defaults.
6. Declaring a target "done" without the confidence label and the healing-pass note.
7. Mapping a composite source step to the nearest single activity: type-ahead as type + click-first-entry, a custom list as `SelectItem`, a menu path as one click, a found row as a stored row number.
8. Building a type-ahead or option pick without the verify sub-step; the wrong entry accepted silently is the costliest failure of a migration.
9. Sending keystrokes to the window instead of the element that has focus, or keeping the source's page-scrolling keys.
