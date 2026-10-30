# Offline Target Definition Workarounds

Scope: accepted targets supplied for offline registration/linking. The
execution contract is [offline-object-repository-guide.md](offline-object-repository-guide.md).
These are measured definition/transport workarounds, reconciled with the
installed UIA documentation before use. They do not authorize selector
derivation, capture or healing.

**Precedence.** Definitions remain CLI-owned except for the minimal offline
seed and the number-attribute expression restoration below. Preserve the
caller's accepted target configuration; no general hand-edit permission.

## Starting-point definition file

There is no `create-definition`. A first file comes from one of three places, in this order; it is then copied per element — the `.xaml` **and its `.xaml.metadata` sibling** — and each copy mutated only through the definition commands (`update-definition`, `enable-steps`, `disable-steps`):

1. **Resolved during exploration**, where the application was reachable: reuse a supplied screen/element seed only when it came from an authorized capture. Offline registration does not start exploration to obtain one.
2. **Exported** from any activity that already carries a target:

   ```bash
   uip rpa uia target-anchorable get-definition \
     --definition-file-path "$DEFS/element-seed.xaml" \
     --activity-id "$ACT" --workflow-file-path "$XAML_REL"
   ```

   An empty placeholder target cannot be exported (`Could not find target`), so one activity in the project must hold a real target first.

3. **No seed available** — author the minimal shape below.

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

**Seed leakage.** The definition commands write only the options passed and leave everything else untouched, so fields the seed carried can survive into each copy. Set every element's strict selector (§ Order of commands, offline): a copy otherwise keeps the seed's. A seed resolved or exported from a live target can carry anchors, since the driver's default often has one: run `target-anchorable remove-anchor` on the seed until none is left before copying it. Removing the last anchor turns the seed strict (`SearchSteps="Selector"`, with a strict selector written from the fuzzy one). A seed resolved from a live target also names its capture's screenshot (`InformativeScreenshot`), which lies in the scratch project's `.screenshots/` folder: Object Repository registration keeps that name for every element and screen copied from the seed, and the build project holds no such file, so delete the attribute from both seeds before copying them. A screen seed resolved live also carries the launch settings of the application explored (§ Screens). No `Guid` step is needed: Object Repository uses its `referenceId` for element identity, and `create-elements` accepts definitions with or without a `Guid`.

**Search steps.** `update-definition --search-steps` sets values only on steps already enabled: a strict selector given to a fuzzy-only definition fails with `Cannot set values for search steps that are not enabled: Strict selector.` `target-anchorable enable-steps` turns a step on with the value it is given, offline included; a strict selector it gives a fuzzy definition replaces the fuzzy step, since only one of the two is ever enabled. `target-anchorable disable-steps` turns a step off. A copy whose `SearchSteps` holds a step the user did not ask for, a semantic step among them, has it disabled before registration.

**Write-back** to an existing Object Repository element is `object-repository replace-elements` (keeps the `referenceId`, so workflow links survive). Never `create-elements` on an element that already exists — that adds a duplicate and orphans the link.

## Screens — `TargetApp` definitions offline

A screen's definition is a `uix:TargetApp`. Take the screen seed exploration resolved, or write the seed below; mutate it only through `uip rpa uia target-app update-definition`, then register and link it (§ Order of commands, offline). The command also writes the `.metadata` sibling (§ CLI behaviour observed offline).

The seed `create-screen` accepts:

```xml
<uix:TargetApp Area="0, 0, 0, 0" Url="https://host.example.com/start" Selector="&lt;html app='chrome.exe' url='https://host.example.com/*' /&gt;" Version="V3" />
```

- `Area`: zeros are fine offline.
- `Selector`: set with `--selector`. A literal selector also sets `BrowserType`, so the seed carries none.
- Launch settings, which the card opens the application with: `Url` on a browser screen; `FilePath`, `Arguments` and `WorkingDirectory` on a desktop one. Set them with `update-definition`'s `--url`, `--file-path` and `--working-directory`; an empty value clears one, such as a launch setting a seed resolved live brought from the application explored. `Arguments`, which has no option, is written in the seed. `create-screen` stores them. After `create-screen`, read the screen back with `object-repository get-screen-xaml` to check that it holds them.
- A launch setting is a literal or one variable. The options take a variable as a `{{variable}}` token and store it as `string.Format("{0}", <variable>)` (`[string.Format("{0}", BaseUrl)]` in a VB project), the text `link-screen` writes into the card, so the card and the screen hold the same expression; after the first link, compare the card's text with the screen's (read back both the stored screen and the linked card). The variable must be in scope in every workflow with a card linked to the screen; where it is not, `link-screen` fails with `Failed to save the workflow after updating the activity.` and the file stays as it was.
- The input method the caller supplied is `--input-mode` on the screen's definition: `create-screen` stores it, and `link-screen` applies it to the card and reports a change (`The activity's input mode changed from 'HardwareEvents' to 'Simulate'.`).
- `link-screen` writes the screen's launch settings into the card it links. A card linked before the screen changed keeps its copy until it is linked again.

## Order of commands, offline

The chosen OR implementation ([offline-object-repository-guide.md](offline-object-repository-guide.md)) runs these steps. A success line is not proof: a batch past the shell's length limit reports success for the part that arrived. After each `create-*` and `link-*`, verify each requested reference/slot in the store and workflow. Counts alone cannot detect a wrong target, and unchanged counts are normal for replacement or relinking.

1. Screen seed, one copy per screen → `target-app update-definition --name --description --selector`, with the launch options and `--input-mode` § Screens names.
2. Element seeds, one copy per element → `target-anchorable update-definition --name --description --scope-selector --activity-type --search-steps "{'strictSelector':{'value':'<selector>'}}"` per element, on a strict seed (§ Starting-point definition file, Seed leakage). `--description` is accepted and lands in the `.xaml.metadata` sibling. Where the user asked for the semantic step (only when the caller requests it), `target-anchorable enable-steps --search-steps "{'semantic':{'value':'<semantic description>'}}"` adds it beside the strict one (`SearchSteps="Selector, SemanticSelector"`) and leaves the strict selector as it is, a `string.Format` expression included. On a registered element, the same calls on its exported definition (`object-repository get-element-definition`) followed by `replace-elements` carry the semantic step and the description into the store and keep the `referenceId` (checked).
3. `object-repository create-app` → `create-screen` with the screen definition → `create-elements` with every new element definition of that screen in one call (`--definition-file-paths`, comma-separated). The ids the registry keeps come from what they print:
   - `create-app` prints the application's `referenceId`.
   - `create-screen` prints `Name:`, `DefinitionFilePath:` and `ReferenceId: <app id>/<screen id>`.
   - `create-elements` prints one `DefinitionFilePath:` / `ReferenceId:` pair per definition and writes the `Reference` into each definition file.
   - `get-screens` and `get-elements` print one `ReferenceId:` / `Name:` / `Description:` block per entry — the store lookup that find-before-create makes.
   - `target-anchorable update-definition` prints `Message: Target anchorable definition updated.`; `replace-elements` prints one `Successfully replaced Object Repository element '<referenceId>' from definition file '<path>'.` line per entry.
4. `link-screen` links one card per call. `link-elements` takes entries for several workflows in one call (`workflowFilePath` per entry) and prints one `Successfully linked … to activity '<id>' in workflow '<file>'` line per entry. Never run two link commands on one file at once.
5. An element whose selector binds a number attribute to a selector variable takes steps 2–4 as § Selector variables in number attributes changes them.

## Selector variables in number attributes

A number attribute bound to a selector variable (`tableRow='{{Row}}'`) cannot be registered through the CLI. That holds for `tableRow` and `tableCol` on a `sap`, `uia` or `java` target, and for the `nav` counts `up`, `next` and `prev`; `idx` bound to a variable registers (table below).

| Command | Result |
|---|---|
| `target-anchorable update-definition --full-selector` with the variable | stores the `string.Format` form, reports success |
| any later command reading that definition — `update-definition` without `--full-selector` (`--name`, `--description`, `--activity-type`), `create-elements`, `replace-elements` | `Invalid configuration for Target '<name>': The attribute '<attribute>' is not supported.` |
| same selector, literal value | passes every command |
| `idx` bound to a variable — any tag, in element, fuzzy, scope and screen selectors; `webctrl` table attributes bound to a variable | pass every command and resolve at run time |
| definition's `string.Format` rewritten as an interpolated string or a concatenation | registers; `link-elements` then writes the activity's target without a strict selector and still reports success |
| `target-anchorable link` with that registered definition file | links with the `Reference` and drops the expression the same way |

The error names the attribute, but the attribute is valid: keep it, because the selector without it no longer names the row, column or relative node it acts on. A run evaluates the Object Repository element's selector, not the activity's copy in the workflow, and an expression selector runs only when the build compiled the same expression text from the workflow; otherwise the activity fails with `Expression Activity type 'CSharpValue`1 (…)' requires compilation in order to run`. Workaround, per element:

1. Run one `target-anchorable update-definition` on the element's definition with the variable selector in `--full-selector`, and with `--name`, `--description` and `--activity-type` in the same call: every later call without `--full-selector` rejects the file. It writes the `string.Format` expression in the project's expression language.
2. In the definition file, rewrite that expression (or that literal) as an interpolated string: `string.Format("…tableRow='{0}'…", Row)` becomes `$"…tableRow='{Row}'…"`. In a C# project that is the text of the `CSharpValue`; in a VB project it is the attribute value `[$"…"]` (both checked).
3. Register the definition with `create-elements` (`replace-elements` for an existing element), then link as usual.
4. After the link pass, every target linked to that element in one workflow file is the same tag, without the selector. Restore them with one Edit per file and element, `replace_all` on that tag: add the definition's `FullSelectorArgument`, text unchanged, and keep `Reference`. It is a child element in a C# project and an attribute in a VB project. Validate the file. The build compiles the expression, and per-file `validate`, `build` and the run accept the target.
5. A re-link writes the target without the expression again, and no link command keeps it. Re-apply step 4 after every re-link and after every `replace-elements` that changes the expression text. The chosen OR implementation does it ([offline-object-repository-guide.md](offline-object-repository-guide.md)). The link table marks these rows, and the report lists them.

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
- On Windows a script that starts `uip.cmd`, the shim other languages' process calls resolve `uip` to, passes its arguments through `cmd.exe`, which expands `%VAR%` and splits unquoted free text at `|`, `&`, `<` and `>`. A description quoting a source path (`1|1|$vRow$`) then fails with `'1' is not recognized as an internal or external command` and nothing is written. A script passes free text to the CLI from PowerShell 7 (`pwsh`), calling `uip` by name: the `uip.ps1` shim PowerShell resolves it to passes each argument byte for byte, double quotes included (checked). Windows PowerShell 5.1 drops embedded double quotes, and Git Bash rewrites an argument starting with `/` into a Windows path.
- `object-repository get-element-definition` takes about ten seconds per element. To check what the store holds, read each element's `.metadata` under `.objects` (JSON: `Name`, `Description`, `Type`, `Reference`) instead of exporting it again; the definition in its `.data` folder declares `utf-16` but is UTF-8.
- `target-app update-definition` prints `Target application definition updated.`; confirm the write by reading the definition file back (`--name`, `--description` and `--input-mode` land in its `.metadata` sibling).
- `object-repository link-screen` / `link-elements` resolve `--workflow-file-path` against the shell's working directory, not `--project-dir`: pass an absolute path inside the project, or every entry fails with "not inside the project directory".
- Per-file `validate` accepts a definition whose strict selector carries a literal `idx` above 2; `build` rejects it (`UI-REL-001`, an Error under the default analyzer configuration). The caller decides whether any selector change is authorized; an authorized change is written back with `target-anchorable update-definition` → `object-repository replace-elements`.
- `replace-elements` keeps the `referenceId`, so the links of already-linked workflows survive a selector change. The run uses the replaced selector at once; the activity's copy in the workflow stays as it was until Studio syncs it or the activity is re-linked, and that stale copy is not an error.
- A strict selector with a `<nav>` path passes `update-definition`, `create-elements`, `link-elements`, per-file `validate` and `build`, and resolves at run time. `selector-intelligence evaluate` rejects it (one ref and the attributes per tag), so `target-anchorable validate --step Strict` checks it against the live application, and its screenshot shows the node the path landed on. `fuzzify` keeps the `<nav>` tag and writes `matching:` / `fuzzylevel:` on its count.
- Element metadata `ActivityType` may stay `None` on elements registered before their acting activity was known: it only tunes selector generation, which offline has already happened.


## Version-specific observations

These observations were captured in Genome builds using uip 1.204; they
are moved here with their version scope. Check the installed documentation
and a bounded offline case before applying a workaround. They override the
older examples above only where the pinned surface exhibits the defect.

| Tool | Observed defect | Response |
|---|---|---|
| `uip rpa uia target-anchorable update-definition`, `UiPath.UIAutomation.Activities` 26.10.3 | Rejects `idx` bound to a selector variable at the first call, on every tag (checked on `java` and `webctrl`); 26.10.4 registers it | Probes once per run, before the first element is defined: one `update-definition` with `idx='{{Row}}'` on a seed copy, against the project, the answer recorded in the brief. Where it is rejected, every positional selector variable takes § Selector variables in number attributes above, with a literal in the variable's place at its first step |
| `uip rpa uia object-repository link-elements`, `UiPath.UIAutomation.Activities` 26.10.5 (its CLI reference and target-attachment guide) | The documented `--elements` form quotes every JSON string with `'`, so an apostrophe in a workflow path ends the string: `After parsing a value an unexpected character was encountered` | Escapes `'` as `\'` in every path it passes |
| UI Automation screen link, `UiPath.UIAutomation.Activities` 26.10.6 and earlier (its target-attachment guide is silent) | Linking a screen into an application card sets the card's input mode to the mode stored on the Object Repository screen, which registration takes from the project's input-mode setting, not from the card: an authored mode is replaced with no message, and the attribute disappears when the stored mode is the default. `target-app update-definition` has no `--input-mode` | Sets the card's input mode after the card's last screen link, and re-reads it after any later one |
| UI Automation screen link with a variable launch setting, `UiPath.UIAutomation.Activities` 26.10.6 and 26.10.7 | `link-screen` writes a variable launch setting into the card as `string.Format("{0}", <variable>)`, while a screen that stores the plain variable keeps it, and a run evaluates the screen's copy, which the build never compiled: the card validates and builds, then fails at run time with ``Url Expression Activity type 'VisualBasicValue`1 (BaseUrl)' requires compilation in order to run`` (``CSharpValue`1`` in a C# project). On 26.10.6 and earlier `target-app update-definition` has no launch options, so a variable reaches the screen only as written in the seed | Writes a variable launch setting in the seed as `link-screen` writes it, `[string.Format("{0}", BaseUrl)]` in a VB project and the `CSharpValue` text `string.Format("{0}", BaseUrl)` in a C# one, or sets it with the launch options where the CLI has them, which store that form; after the first link, compares the card's text with the screen's |
| `uip rpa uia target-anchorable update-definition`, `UiPath.UIAutomation.Activities` 26.10.6 and earlier | No `--search-steps`, `enable-steps` or `disable-steps`: the strict selector is set with `--full-selector` and the semantic step added with `--semantic-selector`. `--full-selector` on a fuzzy-only definition makes it strict and leaves the fuzzy selector in the file as residue, as removing a seed's last anchor does | Uses those two options in the calls of § Order of commands, offline above step 2, and drops a residue, or a step the user did not ask for, by applying the call again to a fresh copy of the strict seed |
