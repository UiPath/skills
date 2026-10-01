# Offline Target Definition Workarounds — TEMPORARY

**Delete this file when the UIA CLI gains a `create-definition` command and registers a number attribute bound to a selector variable.** It records shapes and workarounds the CLI would otherwise own, so a migration need not rediscover them.

Scope: a migration whose only input is the target catalog derived from the source export, with **no reachable application**. `target-anchorable resolve-defaults` takes live snapshot refs (`e*`/`w*`) and there is no `create-definition`, so no first definition can be produced through the CLI there. An offline definition carries no anchor: a caption the source recorded beside a control becomes a `<nav>` path in the strict selector ([selector-translation-guide.md](selector-translation-guide.md) rules 6 and 12). One section applies whether the application is reachable or not: § Selector variables in number attributes, a defect no CLI path avoids.

**Precedence: whenever the application is reachable, the CLI path wins and the offline sections do not apply.** The UIA package guide's rule stands — definitions are CLI-owned, never hand-edited. What follows is the documented exception for the offline case and for that defect, not general licence.

## Starting-point definition file

There is no `create-definition`. Two ways to obtain a first file:

1. **Preferred — export a seed** from any activity that already carries a target, then copy it per element and mutate only through `update-definition`:

   ```bash
   uip rpa uia target-anchorable get-definition \
     --definition-file-path "$DEFS/element-seed.xaml" \
     --activity-id "$ACT" --workflow-file-path "$XAML_REL"
   ```

   Copy the `.xaml` **and its `.xaml.metadata` sibling** per element. An empty placeholder target cannot be exported (`Could not find target`), so one activity in the project must hold a real target first.

2. **No seed available** — author the minimal shape below, then mutate via `update-definition`.

```xml
<uix:TargetAnchorable DesignTimeRectangle="0, 0, 0, 0"
                      ScopeSelectorArgument="&lt;html app='chrome.exe' title='*App*' /&gt;"
                      SearchSteps="Selector" Version="V6">
  <uix:TargetAnchorable.Anchors>
    <scg:List x:TypeArguments="uix:ITarget" Capacity="0" />
  </uix:TargetAnchorable.Anchors>
</uix:TargetAnchorable>
```

Sibling `.xaml.metadata`: `{"ActivityType": "Click", "Anchor0": null, "Anchor1": null, "Anchor2": null, "Anchor3": null, "Name": "", "Description": ""}`.

No `xmlns` declarations needed — the undeclared `uix:`, `scg:` and `x:` prefixes are what the CLI itself writes. Set `ActivityType` through `--activity-type`, not by hand: a hand-written value does not persist, the option accepts only its own enum values, and it drives the selector reliability rules (a `GetText` target avoids content-reflecting attributes, a `Check` target avoids state attributes). A definition can only be updated once it exists — hence the seed.

Field semantics deciding whether an offline file behaves:

| Field | What to write |
|---|---|
| `Version` | `V6`. Not decorative: **at V6 the runtime no longer expands a fuzzy selector itself**, so `FuzzySelectorArgument` must already carry its `matching:`/`fuzzylevel:` prefixes. Omitting `Version` falls back to legacy semantics (no anchor-alignment factor, no image scale factor) |
| `SearchSteps` | `Selector`, `FuzzySelector`, `SemanticSelector`, `CV`, `Image`, `TextNative` — combinable, but set only the step whose argument is filled |
| `FullSelectorArgument` | the **partial** strict selector, relative to the scope. Full selector is scope + partial, computed at runtime, never written |
| `ScopeSelectorArgument` | the window selector. Only the main target carries one; anchors inherit it |
| `DesignTimeRectangle` | **load-bearing wherever anchors, CV or Image are used**: the reference geometry anchor scoring measures against, so zeros silently degrade an anchored fuzzy target. Zeros are fine only for a strict, unanchored target |
| `Guid` | No author-supplied value needed. `update-definition` or Object Repository registration generates it when absent; registration may preserve a value already present |
| `ElementType` | cosmetic — logging and design-time hints only; `None` is harmless |

**Seed leakage.** `update-definition` writes only the options passed and leaves everything else untouched, so fields the seed carried can survive into each copy. Pass `--full-selector` on every element (a fuzzy-only element otherwise keeps the seed's strict selector). A seed exported from a live target can carry anchors, since the driver's default often has one: run `target-anchorable remove-anchor` on the seed until none is left before copying it. Removing the last anchor turns the seed strict (`SearchSteps="Selector"`, with a strict selector written from the fuzzy one) and leaves the fuzzy selector as residue (§ Kind conversion). No `Guid` step is needed: Object Repository uses its `referenceId` for element identity, and `create-elements` accepts definitions with or without a `Guid`.

**Kind conversion.** `--full-selector` on a definition whose search step is `FuzzySelector` also flips `SearchSteps` to `Selector, SemanticSelector`. The old `FuzzySelectorArgument` stays as inert, disabled residue; no command clears it — re-copy the seed and re-apply to purge it. `fuzzify` is one-way (strict → fuzzy); there is no de-fuzzify.

**Write-back** to an existing Object Repository element is `object-repository replace-elements` (keeps the `referenceId`, so workflow links survive). Never `create-elements` on an element that already exists — that adds a duplicate and orphans the link.

## Screens — `TargetApp` definitions offline

A screen's definition is a `uix:TargetApp`, obtained like an element's: write the seed below, mutate it only through `uip rpa uia target-app update-definition` (`--name`, `--description`, `--selector` — it also writes the `.metadata` sibling in the CLI's own shape, and prints nothing on success, § CLI behaviour observed offline), then register and link it in the order of § Order of commands, offline. The command exposes no launch URL or file path, so an application card linked to an offline screen can only *attach*: the launch itself is a Start Process ([source-migration-guide.md § Composite interactions](source-migration-guide.md), "actions without a control") and the live pass may move the open into the card. A window-level screen with no elements is the legitimate shape for maximise, close and "window exists" steps, and for the scope a Start Process-launched application is attached through.

The whole seed `create-screen` accepts — `Area` zeros are fine offline, `Selector` is what `update-definition --selector` fills:

```xml
<uix:TargetApp Area="0, 0, 0, 0" Selector="&lt;html app='chrome.exe' url='https://host.example.com/*' /&gt;" Version="V3" />
```

## Order of commands, offline

The run's target tool ([source-migration-guide.md § UI targets](source-migration-guide.md)) runs these steps. A success line is not proof: a batch past the shell's length limit reports success for the part that arrived. After each `create-*` and `link-*`, count the `TargetApp` / `TargetAnchorable` entries in the file it wrote to (the Object Repository file, the workflow) and stop when the count did not move.

1. Screen seed → `target-app update-definition --name --description --selector`.
2. Element seeds, one copy per element → `target-anchorable update-definition --name --description --full-selector --scope-selector --semantic-selector --activity-type` per element; `--full-selector` on every element (§ Starting-point definition file, Seed leakage). `--description` is accepted and lands in the `.xaml.metadata` sibling. `--semantic-selector` adds the semantic step beside the strict one (`SearchSteps="Selector, SemanticSelector"`) and leaves the strict selector as it is, an interpolated expression included. On a registered element, the same call on its exported definition (`object-repository get-element-definition`) followed by `replace-elements` carries the semantic step and the description into the store and keeps the `referenceId` (checked).
3. `object-repository create-app` → `create-screen` with the screen definition → `create-elements` with every new element definition of that screen in one call (`--definition-file-paths`, comma-separated). The ids the registry keeps come from what they print:
   - `create-app` prints the application's `referenceId`.
   - `create-screen` prints `Name:`, `DefinitionFilePath:` and `ReferenceId: <app id>/<screen id>`.
   - `create-elements` prints one `DefinitionFilePath:` / `ReferenceId:` pair per definition and writes the `Reference` into each definition file.
   - `get-screens` and `get-elements` print one `ReferenceId:` / `Name:` / `Description:` block per entry — the store lookup that find-before-create makes.
   - `target-anchorable update-definition` prints `Message: Target anchorable definition updated.`; `replace-elements` prints one `Successfully replaced Object Repository element '<referenceId>' from definition file '<path>'.` line per entry.
4. `link-screen` links one card per call. `link-elements` takes entries for several workflows in one call (`workflowFilePath` per entry) and prints one `Successfully linked … to activity '<id>' in workflow '<file>'` line per entry. Never run two link commands on one file at once.
5. An element whose selector binds a number attribute to a selector variable takes steps 2–4 as § Selector variables in number attributes changes them.

## Selector variables in number attributes

A number attribute bound to a selector variable (`tableRow='{{Row}}'`) cannot be registered through the CLI. That holds for `tableRow` and `tableCol` on a `sap`, `uia` or `java` target, and for the `nav` counts `up`, `next` and `prev`. For `idx` it depends on the installed UI Automation package:
- **26.10.3:** `update-definition` rejects `idx` bound to a variable at the first call, on every tag (checked on `java` and `webctrl`).
- **26.10.4:** it stores the `string.Format` form and passes every command.

**Probe once per run, before the first element is defined:** run one `update-definition` with `idx='{{Row}}'` on a seed copy, against the project, and record the answer in the brief. If it is rejected, every positional selector variable takes the workaround below.

| Command | Result |
|---|---|
| `target-anchorable update-definition --full-selector` with the variable | stores the `string.Format` form, reports success; `idx` under 26.10.3: rejected at once with the error below |
| any later command reading that definition — `update-definition` without `--full-selector` (`--name`, `--description`, `--activity-type`), `create-elements`, `replace-elements` | `Invalid configuration for Target '<name>': The attribute '<attribute>' is not supported.` |
| same selector, literal value | passes every command |
| `idx` bound to a variable (26.10.4) — any tag, in element, fuzzy, scope and screen selectors; `webctrl` table attributes bound to a variable | pass every command and resolve at run time |
| definition's `string.Format` rewritten as an interpolated string or a concatenation | registers; `link-elements` then writes the activity's target without a strict selector and still reports success |
| `target-anchorable link` with that registered definition file | links with the `Reference` and drops the expression the same way |

The error names the attribute, but the attribute is valid: keep it, because the selector without it no longer names the row, column or relative node it acts on. A run evaluates the Object Repository element's selector, not the activity's copy in the workflow, and an expression selector runs only when the build compiled the same expression text from the workflow; otherwise the activity fails with `Expression Activity type 'CSharpValue`1 (…)' requires compilation in order to run`. Workaround, per element:

1. Run one `target-anchorable update-definition` on the element's definition with the variable selector in `--full-selector`, and with `--name`, `--description` and `--activity-type` in the same call: every later call without `--full-selector` rejects the file. It writes the `string.Format` expression in the project's expression language. Where the variable is rejected at once (`idx` under 26.10.3), pass the selector with a literal in the variable's place instead.
2. In the definition file, rewrite that expression (or that literal) as an interpolated string: `string.Format("…tableRow='{0}'…", Row)` becomes `$"…tableRow='{Row}'…"`. In a C# project that is the text of the `CSharpValue`; in a VB project it is the attribute value `[$"…"]` (both checked).
3. Register the definition with `create-elements` (`replace-elements` for an existing element), then link as usual.
4. After the link pass, every target linked to that element in one workflow file is the same tag, without the selector. Restore them with one Edit per file and element, `replace_all` on that tag: add the definition's `FullSelectorArgument`, text unchanged, and keep `Reference`. It is a child element in a C# project and an attribute in a VB project. Validate the file. The build compiles the expression, and per-file `validate`, `build` and the run accept the target.
5. A re-link writes the target without the expression again, and no link command keeps it. Re-apply step 4 after every re-link and after every `replace-elements` that changes the expression text. The link table marks these rows, and the report lists them.

Linked target after step 4 (C# project):

```xml
<uix:TargetAnchorable … Reference="<ELEMENT_REFERENCE_ID>" ScopeSelectorArgument="&lt;wnd app='saplogon.exe' cls='SAP_FRONTEND_SESSION' /&gt;" SearchSteps="Selector" Version="V6">
  <uix:TargetAnchorable.FullSelectorArgument>
    <InArgument x:TypeArguments="x:String">
      <CSharpValue x:TypeArguments="x:String">$"&lt;sap id='usr/…/tbl…' tableRow='{Row}' tableCol='1' /&gt;"</CSharpValue>
    </InArgument>
  </uix:TargetAnchorable.FullSelectorArgument>
</uix:TargetAnchorable>
```

## CLI behaviour observed offline

- `uip rpa uia …` relay commands (`object-repository *`, `target-anchorable *`, `target-app *`) reject `--output`; read what they print.
- On Windows `uip` resolves to a `.cmd` shim, so arguments a script passes to it go through `cmd.exe`, which splits free text at `|`, `&`, `<` and `>` and expands `%VAR%`. A description quoting a source path (`1|1|$vRow$`) then fails with `'1' is not recognized as an internal or external command` and nothing is written. A script calls the CLI's node entry point instead (`node <npm prefix>/node_modules/@uipath/cli/dist/index.js rpa uia …`) with an argument list; that stores the text byte for byte (both checked).
- `object-repository get-element-definition` takes about ten seconds per element. To check what the store holds, read each element's `.metadata` under `.objects` (JSON: `Name`, `Description`, `Type`, `Reference`) instead of exporting it again; the definition in its `.data` folder declares `utf-16` but is UTF-8.
- `target-app update-definition` prints nothing on success; confirm the write by reading the definition file back (`--name` / `--description` land in its `.metadata` sibling).
- `object-repository link-screen` / `link-elements` resolve `--workflow-file-path` against the shell's working directory, not `--project-dir`: pass an absolute path inside the project, or every entry fails with "not inside the project directory".
- Per-file `validate` accepts a definition whose strict selector carries a literal `idx` above 2; `build` rejects it (`UI-REL-001`, an Error under the default analyzer configuration). What replaces the index, and how an index that stays is decided: [selector-translation-guide.md](selector-translation-guide.md) rule 7; a selector changed that way is written back with `target-anchorable update-definition` → `object-repository replace-elements`.
- `replace-elements` keeps the `referenceId`, so the links of already-linked workflows survive a selector change. The run uses the replaced selector at once; the activity's copy in the workflow stays as it was until Studio syncs it or the activity is re-linked, and that stale copy is not an error.
- A strict selector with a `<nav>` path passes `update-definition`, `create-elements`, `link-elements`, per-file `validate` and `build`, and resolves at run time. `selector-intelligence evaluate` rejects it (one ref and the attributes per tag), so `target-anchorable validate --step Strict` checks it against the live application, and its screenshot shows the node the path landed on. `fuzzify` keeps the `<nav>` tag and writes `matching:` / `fuzzylevel:` on its count.
- Element metadata `ActivityType` may stay `None` on elements registered before their acting activity was known: it only tunes selector generation, which offline has already happened; the live pass replaces the definitions anyway.

## What offline authoring cannot know

Structural validity is the easy half. A catalog cannot tell you these, and each has a correct offline answer that is *not* a guess:

| Unknown | Wrong answer | Right answer |
|---|---|---|
| Which node in the widget takes the action — the container carrying the developer identifier, or the focusable leaf carrying the caption | flatten both into one tag | two tags (container then leaf), or tag-only plus semantic description when the nesting is unknown ([selector-translation-guide.md](selector-translation-guide.md) rule 14) |
| Whether the element exposes `aaname` at all | write the caption onto `aaname` because the catalog recorded a label | apply rule 5's three-case test; a container gets `visibleinnertext` matched exactly, or nothing |
| The element's real HTML tag | `tag='DIV'` as a neutral-looking default — or the tag the control *type* implies, overriding a tag the source actually recorded | strongest evidence first: a tag read out of recorded markup, then the node's role when a known role identifier names it, then the control type, then omit `tag` (rule 14, "Where the tag comes from"). A source's control type is a classification of the widget; a recorded tag is an observation of the node |
| Whether an attribute value is stable or generated | keep any id the catalog held | drop ids failing the volatility filters (a letter after a digit, hashes, GUIDs) |
| The window's identity on the web | derive a title wildcard per screen | one `url` scope per host, authored once and reused by every target on that application (rule 9) |
| Which node shows the accepted value of a pick, and whether it shares attributes with the popup entry | verify on a text leaf matched page-wide by the value | verify on the field's value display scoped to the field; the entry is scoped to the popup labelled with the field (rule 16) |
| Whether `aaname` on the acting input is its label or its current value | drop it on every Type Into, or keep it on every one | keep it only when the catalog recorded a `label` for that control (the value is then the label); omit it otherwise (rule 4) |
| Whether the grid exposes `tableRow`/`colName`/`rowName` | assume div-based (text-pinned rows) or assume `TABLE` | tag-only cell plus a description naming row rule and column; live, read one cell's attribute list (rule 8) |
| Where a caption recorded beside a control sits in the tree relative to it | an anchor with zero design-time rectangles, or the caption written onto the control | the caption leaf and the `<nav>` path the source recorded or the framework pack's widget anatomy documents, else a tag-only target (rule 13); live, target validation shows the node a path lands on (rule 6) |

Shared failure mode: all these wrong answers *look* like finished work and pass every structural check, while a tag-only target with a good semantic description looks unfinished and actually resolves. Prefer the honest shape. Two fields the driver writes on every live definition and the minimal shape omits — `ElementVisibilityArgument="Interactive"` and `WaitForReadyArgument="Interactive"` — are project-setting defaults, not requirements; a live pass restores them when it replaces the definition.

## Before shipping

An offline-authored definition is structurally valid but functionally unproven: `target-anchorable validate` (`--step Strict` isolates the strict step) probes a live application, so the definition stays owed a live pass and its element description says `offline-unverified`. Before that pass is possible, read the definitions back against this guide's own checks — search steps disagreeing with their arguments, a `FuzzySelector` step or an anchor on an offline definition — and [selector-translation-guide.md § Checking a definition](selector-translation-guide.md). Everything a structural check cannot see is what the live pass is for ([source-migration-guide.md § Verifying targets](source-migration-guide.md)).
