# Offline target derivation — limits

Registration, definition construction, CLI defects and selector-variable
workarounds belong to the invoked `uipath-rpa` owner. Delegate the target spec
and link table under [ui-target-migration-guide.md § UI targets — pipeline](ui-target-migration-guide.md#ui-targets--pipeline).
Do not generate a second target tool or read the sibling skill's files.
If the owner is unavailable, retain the spec, link table and unsatisfied work
with the missing-owner remedy; no registration or linking is claimed.

The following are Genome's derivation limits, not registration mechanics.

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

Shared failure mode: all these wrong answers *look* like finished work and pass every structural check, while a tag-only target with a good semantic description looks unfinished and tells the live pass what to capture. Prefer the honest shape. Two fields the driver writes on every live definition and the minimal shape omits — `ElementVisibilityArgument="Interactive"` and `WaitForReadyArgument="Interactive"` — are project-setting defaults, not requirements; a live pass restores them when it replaces the definition.

## Before shipping

An offline-authored definition is structurally valid but functionally unproven: `target-anchorable validate` (`--step Strict` isolates the strict step) probes a live application, so the definition stays owed a live pass and its element description says `offline-unverified`. Before that pass is possible, read the definitions back against this guide's own checks — search steps disagreeing with their arguments, a `FuzzySelector` step or an anchor on an offline definition — and [selector-translation-guide.md § Checking a definition](selector-translation-guide.md). Everything a structural check cannot see is what the live pass is for ([ui-target-migration-guide.md § Verifying targets](ui-target-migration-guide.md)).
