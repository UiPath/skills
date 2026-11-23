# Offline Target Definition Workarounds — TEMPORARY

Scope: the offline migration ([ui-target-migration-guide.md](ui-target-migration-guide.md) rule 4), which builds every definition from the target spec, whether or not the application is reachable. The CLI resolves a first definition only from a live snapshot (`resolve-defaults`) and creates no definition file, so the offline migration writes a one-line seed per screen and per element and fills it through the definition commands. An offline definition carries no anchor: a caption the source recorded beside a control becomes a `<nav>` path in the strict selector ([selector-translation-guide.md](selector-translation-guide.md) rules 6 and 12).

**Precedence.** The UIA package guide's rule stands — definitions are CLI-owned, never hand-edited. The seeds below are the documented exception for definitions built from the target spec, not general licence. An application automated without an export is captured with the owning skill's target-capture procedure instead, and the live healing pass captures a target live where its derived selector fails ([live-application-guide.md § Live healing pass](live-application-guide.md)).

## Starting-point definition file

Each screen and each element starts from a seed file of its own in the working folder, outside every project: a project's build compiles every `.xaml` under it.

| Definition | Seed |
|---|---|
| element | `<uix:TargetAnchorable SearchSteps="Selector" Version="V6" />` |
| screen | `<uix:TargetApp Version="V3" />` |

The definition commands write every other field and the `.xaml.metadata` sibling (§ Order of commands, offline); the undeclared `uix:` prefix is what the CLI itself writes. The CLI never adds `Version`, and it is not decorative: at V6 the runtime no longer expands a fuzzy selector itself, and without it a target falls back to legacy semantics (no anchor-alignment factor, no image scale factor). An element's strict selector is the **partial** selector, relative to its scope selector; the full selector is scope + partial, computed at run time.

A definition resolved from a live capture is never a seed: a definition built from it keeps the capture's anchors, the launch settings of the application captured and the capture's screenshot, which registration stores with the screen or element.

## Screens — `TargetApp` definitions offline

A screen's definition is a `uix:TargetApp`, filled from its seed by `uip rpa uia target-app update-definition`, then registered and linked (§ Order of commands, offline).

- `--selector` sets the window selector; a literal selector also sets `BrowserType`.
- Launch settings, which the card opens the application with: `--url` on a browser screen; `--file-path` and `--working-directory` on a desktop one. `Arguments` has no option: it is written in the seed, a variable in the form `link-screen` writes ([package-doc-errata-guide.md](package-doc-errata-guide.md) § Tools). After `create-screen`, read the screen back with `object-repository get-screen-xaml` to check that it holds them.
- A variable launch setting must be in scope in every workflow with a card linked to the screen; where it is not, `link-screen` fails with `Failed to save the workflow after updating the activity.` and the file stays as it was.
- The input method the application notes record for the application ([live-application-guide.md § Exploring](live-application-guide.md)) is `--input-mode`, which `link-screen` applies to the card.
- `link-screen` writes the screen's launch settings into the card it links. A card linked before the screen changed keeps its copy until it is linked again.

## Order of commands, offline

The run's target tool ([ui-target-migration-guide.md § UI targets](ui-target-migration-guide.md)) runs these steps. A success line is not proof: a batch past the shell's length limit reports success for the part that arrived. After each `create-*` and `link-*`, count the `TargetApp` / `TargetAnchorable` entries in the file it wrote to (the Object Repository file, the workflow) and stop when the count did not move.

1. A seed per screen → `target-app update-definition --name --description --selector`, with the launch options and `--input-mode` § Screens names.
2. A seed per element → one `target-anchorable update-definition --name --description --scope-selector --activity-type --search-steps "{'strictSelector':{'value':'<selector>'}}"`. Where the user asked for the semantic step ([selector-translation-guide.md](selector-translation-guide.md) rule 12), `target-anchorable enable-steps --search-steps "{'semantic':{'value':'<semantic description>'}}"` adds it beside the strict one. A registered element changes the same way on its exported definition (`object-repository get-element-definition`), then `replace-elements`.
3. `object-repository create-app` → `create-screen` with the screen definition → `create-elements` with every new element definition of that screen in one call (`--definition-file-paths`, comma-separated). The ids the registry keeps come from what they print:
   - `create-app` prints the application's `referenceId`.
   - `create-screen` and `create-elements` print a `Name:` / `DefinitionFilePath:` / `ReferenceId:` block per definition; an entry `create-elements` refuses prints `Error:` in place of its `ReferenceId:`.
   - `get-screens` and `get-elements` print one `ReferenceId:` / `Name:` / `Description:` block per entry — the store lookup that find-before-create makes.
   - `update-definition` prints `Message: Target anchorable definition updated.` (`Target application definition updated.` for a screen); `replace-elements` prints one `Successfully replaced Object Repository element '<referenceId>' from definition file '<path>'.` line per entry.
4. `link-screen` links one card per call. `link-elements` takes entries for several workflows in one call (`workflowFilePath` per entry) and prints one `Successfully linked … to activity '<id>' in workflow '<file>'` line per entry. After a `replace-elements` that changes an expression in an element — a selector variable, or a semantic description holding one — every activity linked to that element is linked again ([package-doc-errata-guide.md](package-doc-errata-guide.md) § Tools).

## CLI behaviour observed offline

- `uip rpa uia …` relay commands (`object-repository *`, `target-anchorable *`, `target-app *`) reject `--output`; read what they print.
- On Windows a script that starts `uip.cmd`, the shim other languages' process calls resolve `uip` to, passes its arguments through `cmd.exe`, which expands `%VAR%` and splits unquoted free text at `|`, `&`, `<` and `>`. A description quoting a source path (`1|1|$vRow$`) then fails with `'1' is not recognized as an internal or external command` and nothing is written. A script passes free text to the CLI from PowerShell 7 (`pwsh`), calling `uip` by name: the `uip.ps1` shim PowerShell resolves it to passes each argument byte for byte, double quotes included (checked). Windows PowerShell 5.1 drops embedded double quotes, and Git Bash rewrites an argument starting with `/` into a Windows path.
- To check what the store holds, read each element's `.metadata` under `.objects` (JSON: `Name`, `Description`, `Type`, `Reference`) instead of exporting each definition; the definition in its `.data` folder declares `utf-16` but is UTF-8.
- Per-file `validate` accepts a definition whose strict selector carries a literal `idx` above 2; `build` rejects it (`UI-REL-001`, an Error under the default analyzer configuration). What replaces the index, and how an index that stays is decided: [selector-translation-guide.md](selector-translation-guide.md) rule 7; a selector changed that way is written back with `target-anchorable update-definition` → `object-repository replace-elements`.
- A strict selector with a `<nav>` path passes `update-definition`, `create-elements`, `link-elements`, per-file `validate` and `build`, and resolves at run time. `selector-intelligence evaluate` rejects it (one ref and the attributes per tag), so `target-anchorable validate --step Strict` checks it against the live application, and its screenshot shows the node the path landed on. `fuzzify` keeps the `<nav>` tag and writes `matching:` / `fuzzylevel:` on its count.
- Element metadata `ActivityType` may stay `None` on elements registered before their acting activity was known: it only tunes selector generation, which offline has already happened.

## What offline authoring cannot know

Structural validity is the easy half. A catalog cannot tell you these, and each has a correct offline answer that is *not* a guess:

| Unknown | Wrong answer | Right answer |
|---|---|---|
| Which node in the widget takes the action — the container carrying the developer identifier, or the focusable leaf carrying the caption | flatten both into one tag | two tags (container then leaf), or tag-only plus semantic description when the nesting is unknown ([selector-translation-guide.md](selector-translation-guide.md) rule 14) |
| Whether the element exposes `aaname` at all | write the caption onto `aaname` because the catalog recorded a label | apply the three-case test of [selector-translation-web-guide.md § Rule 5](selector-translation-web-guide.md); a container gets `visibleinnertext` matched exactly, or nothing |
| The element's real HTML tag | `tag='DIV'` as a neutral-looking default — or the tag the control *type* implies, overriding a tag the source actually recorded | strongest evidence first: a tag read out of recorded markup, then the node's role when a known role identifier names it, then the control type, then omit `tag` ([selector-translation-web-guide.md § Rule 14](selector-translation-web-guide.md), "Where the tag comes from"). A source's control type is a classification of the widget; a recorded tag is an observation of the node |
| Whether an attribute value is stable or generated | keep any id the catalog held | drop ids failing the volatility filters (a letter after a digit, hashes, GUIDs) |
| The window's identity on the web | derive a title wildcard per screen | one `url` scope per host with the title's stable part, authored once and reused by every target on that application (rule 9) |
| Which node shows the accepted value of a pick, and whether it shares attributes with the popup entry | verify on a text leaf matched page-wide by the value | verify on the field's value display scoped to the field; the entry is scoped to the popup labelled with the field (rule 16) |
| Whether `aaname` on the acting input is its label or its current value | drop it on every Type Into, or keep it on every one | keep it only when the catalog recorded a `label` for that control (the value is then the label); omit it otherwise (rule 4) |
| Whether the grid exposes `tableRow`/`colName`/`rowName` | assume div-based (text-pinned rows) or assume `TABLE` | tag-only cell plus a description naming row rule and column; live, read one cell's attribute list (rule 8) |
| Where a caption recorded beside a control sits in the tree relative to it | an anchor with zero design-time rectangles, or the caption written onto the control | the caption leaf and the `<nav>` path the source recorded or the framework pack's widget anatomy documents, else a tag-only target (rule 13); live, target validation shows the node a path lands on (rule 6) |

Shared failure mode: all these wrong answers *look* like finished work and pass every structural check, while a tag-only target with a good semantic description looks unfinished and tells the live pass what to capture. Use the honest shape. Two fields the driver writes on every live definition and the seed leaves out — `ElementVisibilityArgument="Interactive"` and `WaitForReadyArgument="Interactive"` — are project-setting defaults, not requirements; a live pass restores them when it replaces the definition.

## Before shipping

An offline-authored definition is structurally valid but functionally unproven: `target-anchorable validate` (`--step Strict` isolates the strict step) probes a live application, so the definition stays owed a live pass and its element description says `offline-unverified`. Before that pass is possible, read the definitions back against [selector-translation-guide.md § Checking a definition](selector-translation-guide.md). Everything a structural check cannot see is what the live pass is for ([ui-target-migration-guide.md § Verifying targets](ui-target-migration-guide.md)).
