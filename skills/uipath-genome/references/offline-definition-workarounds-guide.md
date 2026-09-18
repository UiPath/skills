# Offline Target Definition Workarounds — TEMPORARY

**Delete this file when the UIA CLI gains a `create-definition` command and an offline `add-anchor`.** It records shapes that the CLI would otherwise own, so a catalog-only migration does not have to rediscover them.

Scope: a migration whose only input is a source target catalog (`source/targets.json`), with **no reachable application**. `target-anchorable resolve-defaults` and `add-anchor` both take live snapshot refs (`e*`/`w*`), and there is no `create-definition`, so neither a first definition nor an anchor can be produced through the CLI in that situation.

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

No `xmlns` declarations are needed — the undeclared `uix:`, `scg:` and `x:` prefixes are what the CLI itself writes. Set `ActivityType` through `--activity-type`, not by hand: a hand-written value does not persist, and it drives the selector reliability rules (a `GetText` target avoids content-reflecting attributes, a `Check` target avoids state attributes).

**Seed leakage.** `update-definition` writes only the options passed and leaves everything else untouched, so every field the seed carried survives into each copy — its `FullSelectorArgument` and its `Guid`. Pass `--full-selector` on every element (a fuzzy-only element otherwise keeps the seed's strict selector), and give each element its own `Guid`. `update-definition` exposes no `--guid`, so a shared `Guid` can only be changed by writing the file; Object Repository identity is the `referenceId`, so it appears cosmetic.

**Kind conversion.** `--full-selector` on a definition whose search step is `FuzzySelector` also flips `SearchSteps` to `Selector, SemanticSelector`. The old `FuzzySelectorArgument` stays as inert, disabled residue; no command clears it — re-copy the seed and re-apply to purge it. `fuzzify` is one-way (strict → fuzzy); there is no de-fuzzify.

**Write-back** to an existing Object Repository element is `object-repository replace-elements` (keeps the `referenceId`, so workflow links survive). Never `create-elements` on an element that already exists — that adds a duplicate and orphans the link.

## Anchors without `add-anchor`

Semantics first, because they constrain when an anchor is worth authoring at all (package docs, `activities/common/Target.md` § Anchors):

| Supports anchors | Ignores anchors |
|---|---|
| `FuzzySelector`, `CV`, `TextNative`, `Image` | `Selector`, `SemanticSelector` |

- An anchor is a plain `uix:Target`, never a `TargetAnchorable` — anchors cannot have anchors. Up to four, slots `0..3`.
- A **strict** target ignores any anchor present. `add-anchor` on a strict target atomically converts the main target to `FuzzySelector` first; removing its last anchor reverses the conversion. So offline, adding an anchor means also moving the main target to `FuzzySelector`.
- `idx` is **not supported** on `FuzzySelector`. A target that needs a positional index must stay strict, and therefore can never be anchored.
- This is the mechanical reason for the targeting-method policy in [source-migration-guide.md](source-migration-guide.md): fuzzy without an anchor has nothing to disambiguate with, and an anchor on a strict target is dead weight.

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
- **Anchor `SearchSteps`** follows the same model as a target: `FuzzySelector` alone or `Selector, FuzzySelector`, carrying `FullSelectorArgument`, `FuzzySelectorArgument`, or both.
- **The main target's `SearchSteps` must include `FuzzySelector`**, or the anchor is ignored. `Selector, FuzzySelector` together is valid — the strict step runs first and the anchor serves the fuzzy step.
- `DesignTimeRectangle` / `ElementType` are design-time only; zeros are fine offline.

Source-catalog input: a framework whose recognition data records an associated caption (Certify's `label` / `LeftTextAnchor` / `RightTextAnchor`) is describing an anchor, not an attribute of the target — see the Certify guide's translation table. Folding that caption into the target's own `aaname` instead asserts the caption's text is the target's accessible name; true for a button whose text *is* its name, unreliable for a caption that is merely positioned nearby.

Leave `.metadata`'s `Anchor0`–`Anchor3` as `null` — an anchor persists and round-trips without them; they hold only the `--name`/`--description` labels `add-anchor` attaches.

An offline-authored definition is structurally valid but functionally unproven: `target-anchorable validate` (`--step Fuzzy` isolates the fuzzy step) probes a live application, so the definition stays owed a live pass.
