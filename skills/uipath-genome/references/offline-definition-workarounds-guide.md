# Offline Target Definition Workarounds — TEMPORARY

**Delete this file when the UIA CLI gains a `create-definition` command and an offline `add-anchor`.** It records shapes the CLI would otherwise own, so a catalog-only migration need not rediscover them.

Scope: a migration whose only input is the target catalog derived from the source export, with **no reachable application**. `target-anchorable resolve-defaults` and `add-anchor` both take live snapshot refs (`e*`/`w*`), and there is no `create-definition`, so neither a first definition nor an anchor can be produced through the CLI there.

**Precedence: whenever the application is reachable, the CLI path wins and this file does not apply.** The UIA package guide's rule stands — definitions are CLI-owned, never hand-edited. What follows is the documented exception for the offline case, not general licence.

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
<uix:TargetAnchorable DesignTimeRectangle="0, 0, 0, 0" Guid="<fresh-guid>"
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
| `Guid` | one per element, never shared (also the id sent with a semantic request) |
| `ElementType` | cosmetic — logging and design-time hints only; `None` is harmless |

**Seed leakage.** `update-definition` writes only the options passed and leaves everything else untouched, so every field the seed carried survives into each copy — its `FullSelectorArgument` and its `Guid`. Pass `--full-selector` on every element (a fuzzy-only element otherwise keeps the seed's strict selector), and give each element its own `Guid`. `update-definition` exposes no `--guid`, so a shared `Guid` can only be changed by writing the file; Object Repository identity is the `referenceId`, so it appears cosmetic.

**Kind conversion.** `--full-selector` on a definition whose search step is `FuzzySelector` also flips `SearchSteps` to `Selector, SemanticSelector`. The old `FuzzySelectorArgument` stays as inert, disabled residue; no command clears it — re-copy the seed and re-apply to purge it. `fuzzify` is one-way (strict → fuzzy); there is no de-fuzzify.

**Write-back** to an existing Object Repository element is `object-repository replace-elements` (keeps the `referenceId`, so workflow links survive). Never `create-elements` on an element that already exists — that adds a duplicate and orphans the link.

## Anchors without `add-anchor`

Semantics first — they constrain when an anchor is worth authoring at all (package docs, `activities/common/Target.md` § Anchors):

| Supports anchors | Ignores anchors |
|---|---|
| `FuzzySelector`, `CV`, `TextNative`, `Image` | `Selector`, `SemanticSelector` |

- An anchor is a plain `uix:Target`, never a `TargetAnchorable` — anchors cannot have anchors. **Up to four**, slots `0..3`; a fifth is rejected.
- An anchor has no scope of its own: it inherits the main target's `ScopeSelectorArgument`. Never give an anchor one.
- A **strict** target ignores any anchor present. `add-anchor` on a strict target atomically converts the main target to `FuzzySelector` first; removing its last anchor reverses the conversion. So offline, adding an anchor means also moving the main target to `FuzzySelector`.
- `idx` is **stripped when a selector is fuzzified** (with `tableRow`, `tableCol` and `css-selector`). A target that needs a positional index must stay strict, and so can never be anchored.
- **An anchor that matches nothing at run time fails the whole search**, not just that candidate. Anchor only on something reliably present; a caption that appears conditionally is worse than no anchor.
- Anchor scoring is geometric, relative to `DesignTimeRectangle`: direction (which side the anchor sits on), edge-to-edge distance, angle and overlap. The score peaks at the design-time distance and falls off in **both** directions, so a candidate much closer than at capture is penalised as much as one much further. `fuzzylevel` plays no part in it.
- Fuzzifying a selector leaves `cls`/`class`, `app`, `role`, `tag`, `type`, `css-selector` and `hasTableAncestor` as exact ("hard") attributes and fuzzifies the rest (`id`, `name`, `aaname`, `automationid`, title and text attributes), each written as the triple `name='value'`, `matching:name='fuzzy'`, `fuzzylevel:name='0.0'`. An attribute whose value already holds a `*`, or that is matched by regex, gets only `fuzzylevel:name='0.0'` and keeps its own matching.
- Mechanical reason for the targeting-method policy in [selector-translation-guide.md](selector-translation-guide.md) rule 12: fuzzy without an anchor has nothing to disambiguate with, and an anchor on a strict target is dead weight.

Shape of a populated anchor list (one anchor). Working examples in this repo: `tests/tasks/uipath-review/rpa/selector-brittle/fixture/BrittleBot/Main.xaml`, `tests/tasks/uipath-troubleshoot/activity-packages/uia-application-open-failed/process/EditorLink.xaml`.

```xml
<uix:TargetAnchorable … FuzzySelectorArgument="&lt;…target…&gt;" SearchSteps="FuzzySelector" Version="V6">
  <uix:TargetAnchorable.Anchors>
    <scg:List x:TypeArguments="uix:ITarget" Capacity="1">
      <uix:Target DesignTimeRectangle="0, 0, 0, 0" ElementType="Text"
                  FullSelectorArgument="&lt;webctrl aaname='First Name' tag='LABEL' /&gt;"
                  FuzzySelectorArgument="&lt;webctrl aaname='First Name' tag='LABEL' matching:aaname='fuzzy' fuzzylevel:aaname='0.0' /&gt;"
                  SearchSteps="FuzzySelector" />
    </scg:List>
  </uix:TargetAnchorable.Anchors>
</uix:TargetAnchorable>
```

Checklist when authoring one offline:

- **`Capacity` is not load-bearing — don't compute it.** The CLI normalizes whatever you write to `Capacity="4"`.
- **Anchor `Guid` is optional** — omit it and `create-elements` assigns one.
- **Anchor `SearchSteps`: set exactly one step** and fill the argument that matches it (`FuzzySelector` → `FuzzySelectorArgument`). Only one targeting method is used at runtime, so a second step or a second populated argument is never evaluated — files carrying both exist, but the extra one is dead weight, not a fallback.
- **The main target's `SearchSteps` must include `FuzzySelector`**, or the anchor is ignored. `Selector, FuzzySelector` together is valid — the strict step runs first and the anchor serves the fuzzy step.
- `DesignTimeRectangle` / `ElementType` are design-time only; zeros are fine offline.

When the source's selectors guide sends a recorded caption to an anchor ([selector-translation-guide.md](selector-translation-guide.md) rule 6), the catalog gives that caption's **text**, never a selector for the caption element. That is enough: put the caption text on the attribute that table names for the criteria that recorded it, under that criteria's own matching, and add nothing else — inventing the caption's tag or class is exactly the fabrication the derivation rule forbids. Where the chosen attribute is an inner-text one, keep the match exact: inner text is inherited by every ancestor, so a wildcarded caption matches the container chain. The target then keeps only its non-caption attributes; where the caption was the *only* thing the source recorded, the target is tag-only and the anchor carries the identification. Parametrised captions need the stored expression form (`[string.Format("…{0}…", arg)]`): `{{var}}` is CLI input sugar a hand-injected anchor never passes through.

Leave `.metadata`'s `Anchor0`–`Anchor3` as `null` — an anchor persists and round-trips without them; they hold only the `--name`/`--description` labels `add-anchor` attaches.

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

Shared failure mode: all these wrong answers *look* like finished work and pass every structural check, while a tag-only target with a good semantic description looks unfinished and actually resolves. Prefer the honest shape. Two fields the driver writes on every live definition and the minimal shape omits — `ElementVisibilityArgument="Interactive"` and `WaitForReadyArgument="Interactive"` — are project-setting defaults, not requirements; a live pass restores them when it replaces the definition.

## Before shipping

An offline-authored definition is structurally valid but functionally unproven: `target-anchorable validate` (`--step Fuzzy` isolates the fuzzy step) probes a live application, so the definition stays owed a live pass and its element description says `offline-unverified`. Before that pass is possible, read the definitions back against this guide's own checks — search steps disagreeing with their arguments, an anchor on a strict target, an anchor carrying a scope, a fuzzy match with no `fuzzylevel` — and [selector-translation-guide.md § Checking a definition](selector-translation-guide.md). Everything a structural check cannot see is what the live pass is for ([source-migration-guide.md § Verifying targets](source-migration-guide.md)).
