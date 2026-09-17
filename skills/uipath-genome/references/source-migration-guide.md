# Source Migration Guide — UI targets and test data at execution

Execution of an extracted genome migrates two things the genome body deliberately leaves out: the **UI targets** (selectors) and the **test data** of the source automation. Both live in the source artifacts folder the extraction writes next to the genome ([genome-format-guide.md § Source Artifacts](genome-format-guide.md)). This guide is framework-agnostic; each source guide's *UI Target Locators* and *Test Data* sections say what the source provides and how its attributes translate.

## Rules

1. **Migrate targets from the catalog before anything else.** When `source/targets.json` exists, every UI activity of the built project receives an Object Repository (OR) target derived from the catalog. The placeholder-selector stub pattern is the fallback only when no catalog exists AND no live application is reachable; a live application is captured with the owning skill's target-capture procedure instead.
2. **Every migrated target is inferred and says so.** Its OR element description starts with `INFERRED (<confidence>)` and names the source control. The first run against the real application is a healing pass; accepted fixes go into the OR element in place so every consumer inherits them.
3. **Migrate test data from the data catalog by default.** When `source/test-data.json` exists, the test projects' data files are filled from it by a scripted, reviewable mapping from source variables to test-case arguments, never by hand. Generated placeholder rows are a temporary state, not a deliverable.
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

Mapping rules: every UI activity mapped once, activity ids file-unique; `source/step-map.json` names the source processes of each workflow step, and their dumped steps name the controls; shared widgets (search box, OK, Submit, comment box, menus) reuse one control so the OR holds one element each; literals that the workflow receives as arguments (a person name, a placeholder the source rewrote at run time) become selector variables (`{{Argument}}`) bound to the workflow argument; steps the built workflow has but the source had not (optional pop-up checks, verifications) get no source control, a precise semantic description and low confidence.

Confidence: **high** = developer identifier present (automation id, id, aria-label, name); **medium** = only label, inner text, title or class (fuzzy selector + label anchor); **low** = only XPath/outerHTML, or no control (semantic only). Targeting-method policy: label → fuzzy main selector with a label anchor; no label and high → strict; no label and medium → fuzzy; position index present → strict with index (never anchored); semantic selector always added as runtime fallback.

Creating and linking mechanics are the owning skill's Object Repository CLI, target-configuration and target-attachment guidance; follow them. Offline specifics the guidance does not cover: a definition can only be updated once it exists (export one from an activity that already carries a target, then mutate it only through the CLI); the activity-type option accepts only its own enum values; a single link call with more than about a dozen entries can exceed the shell command-line length — batch; the designer leaves `~<Workflow>.xaml` recovery copies in the project after linking — delete them before packing; analyzer rules such as SecureString public arguments or large position indexes fail `build` and `pack` but not `validate` — decide with the user whether to lower them or pack with the analyzer skipped.

## Test data — pipeline

| Step | Output |
|---|---|
| 1. Decode the data catalog | recordsets as named rows (schema = layout variables, in column order); process → recordset links |
| 2. Per test project, decide the mapping | per data file: its source recordset(s) and rows; per argument: the source variable (with a transform when needed), a join, a constant, a lookup into another recordset, or keep the default |
| 3. Check coverage, then migrate | every argument has a rule, credentials refused, rows rewritten, coverage report per file (migrated / kept / missing) |
| 4. Rebuild the project | data files are not compiled, but rebuild once to catch argument drift |

Transforms that recur: organisation-with-manager strings (`Org (Manager)` → org, manager), On/Off → boolean, country → region code, dates normalised, placeholder markers (`^`) → empty, user name → credential asset name and tenant URL.

Report per project: rows and cells migrated, values kept at defaults and why, values the source had but the test case has no argument for (and where they went), source quirks carried over (typos, wrong-field values, historical worker names, stale run dates). Historical run dates and worker names must be refreshed before a run on a live tenant; say so in the report.

## What the executor records (no prescribed file formats)

Mechanics — creating screens and elements, updating definitions, fuzzifying, linking — are the owning skill's Object Repository CLI and target-configuration guidance; read them and use them as they are. The genome skill only requires that, at the end, these facts are recorded and reviewable:

- per UI activity: the source window and control it was derived from (or "none"), the resulting strict/fuzzy selector, anchor and semantic description, the confidence tier, and the OR element it links to — one OR element per distinct source control, reused across workflows;
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
