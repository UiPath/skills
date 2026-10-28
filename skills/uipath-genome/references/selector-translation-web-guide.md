# Selector Translation — the web

The web's side of [selector-translation-guide.md](selector-translation-guide.md): the `html` and `webctrl` tags, and what each rule adds for pages driven through the browser driver — browsers, SAP Fiori, Web GUI and Ariba, web views. Read whole with that guide when the target catalog holds web controls; its tiers, roles and matching semantics hold here, and rule numbers are its own.

## `html` — browser tab

| Attribute | Meaning | Tier / role |
|---|---|---|
| `app` | browser executable — selects browser driver at run time | critical — never drop: empty or missing `app` is treated as Internet Explorer |
| `url` | page URL | very reliable — wildcard path, keep host: `url='https://host/*'` |
| `title` | page title | alright — wildcard; prefer `url` to tell tabs apart |
| `htmlwindowname` | `window.name` | alright |
| `mobiledata` | mobile device binding | critical when present — never drop |
| `sapweb-ses-screen`, `sapweb-ses-transaction`, `sapweb-ses-client`, `sapweb-ses-user`, `sapweb-ses-program` | SAP Web GUI session context | session |
| `ui5-ses-technicalName`, `ui5-ses-appId` | UI5 application context | session |
| `idx` | | position |
| `pid`, `tid`, `gid`, `bsid`, `excludehwnd`, `isremoteapp`, `useBrowserExtension` | runtime | never |

`app` values the driver recognises (anything else is treated as a custom Chromium browser only when it equals `custom_browser`):

| Browser | `app` |
|---|---|
| Google Chrome | `chrome.exe` |
| Microsoft Edge (Chromium) | `msedge.exe` |
| Microsoft Edge WebView2 (embedded in desktop app) | `msedgewebview2.exe` |
| Microsoft Edge (legacy, UWP) | `ApplicationFrameHost.exe` |
| Mozilla Firefox | `firefox.exe` |
| Internet Explorer | `iexplore.exe` — also default when `app` is empty or missing |
| Brave, Vivaldi | `brave.exe`, `vivaldi.exe` |
| Custom Chromium-based browser (with UiPath extension) | `custom_browser` |
| Safari (macOS) | `Safari` |

A source recording only "Chrome", "Edge" or "IE" as browser choice maps to these executables; a source recording nothing gets a Configuration Question ("Which browser runs the automation?", default Chrome → `chrome.exe`). Never leave `app` for the run time to default.

## `webctrl` — HTML element (open schema)

| Tier | Attributes |
|---|---|
| very reliable | `tag`, `aria-label`, `aria-labelledby`, `aria-role`, `aria-describedby`, `shadowhostid`; author-controlled `data-*` identifiers (`data-testid`, `data-automation-id`, `data-cy`) |
| alright | `id`, `parentid`, `name`, `parentname`, `type`, `isleaf`, `aaname`, `visibleinnertext`, `innertext` |
| table | `tableCol`, `tableRow`, `colName`, `rowName` |
| last resort | `action`, `alt`, `href`, `src`, `tabindex`, `placeholder`, `uipath-html-title` (element's `title` attribute), `css-selector`, `class`, `parentclass`, `aria-pressed` |
| last resort — framework-generated | `ng-reflect-*`, `ng-version`, `_ngcontent-*`, `_nghost-*`, `data-reactid`, `__reactProps$*`, `v-*`, `data-v-*` |
| SAP Fiori / UI5 | very reliable `ui5-label`, `ui5-tooltip`, `ui5-role`, `ui5-type`, `ui5-view-local-id`; alright `ui5-class`; tables `ui5-tableCol`, `ui5-tableRow`, `ui5-colLabel`, `ui5-isEmpty`; trees `ui5-path` |
| SAP Web GUI | very reliable `sapweb-id` (scripting id), `sapweb-type`; alright `sapweb-lsclass`, `sapweb-text`, `sapweb-itemid`; tables `sapweb-tablerow`, `sapweb-tablecol`, `sapweb-colname`, `sapweb-coltooltip`; trees `sapweb-path`; avoid `sapweb-lsid` |
| SAP Ariba | very reliable `aw-name`, `aw-label`, `aw-type`; tables `aw-tablerow`, `aw-tabledetailrow`, `aw-tablerowtype`, `aw-tablecol`, `aw-collabel`; avoid `id` (session hash) |

Hard rules for `webctrl`: a tag whose node sits inside a shadow DOM must carry `shadowhostid` (even empty); `frame`/`iframe` tags are never removed; `class` keeps only the semantic core (`class='*search-input*'`), never utility tokens or build hashes; ids with three or more dot-separated structural segments are wildcarded to the last semantic segments; hash-suffixed custom tag names are wildcarded (`tag='MACROPONENT-*'`); a `DIV`/`SPAN` without a semantic attribute is not a target on its own.

How the browser driver computes the attributes a translation leans on (web extension's attribute getters):

| Attribute | Computed as | Consequence for translation |
|---|---|---|
| `tag` | DOM tag name, upper-case for HTML elements | matched case-insensitively |
| `aaname` | legacy MSAA-style name, **not** the ARIA accessible name. For `A`, `INPUT`, `IMG`, `BUTTON`, `TEXTAREA`, `AREA`, `SELECT`, `TABLE`: buttons `title` → text/value; images `title` → `alt` → `<label for>` (→ enclosing `A`); tables `title` → caption → header cells; other form elements and links `<label for>` text → own text/value → `title` → `alt`. For **every other element**: element's **own direct text nodes only**. Text is taken as the node holds it — not trimmed, inner whitespace kept (a link indented in the markup reads `'      Travel      '`), while `visibleinnertext` of the same node is trimmed but keeps its line breaks | never reads `aria-label`, `aria-labelledby`, `placeholder` or a wrapping `<label>`; a container's `aaname` is not inherited from descendants, so `aaname` on a bare `DIV`/`SPAN`/`LABEL` caption is an exact, non-inherited pin; an input's `aaname` is its `<label for>` text when the input has an `id` |
| `value` | the HTML `value` **attribute**, read raw — not the live `.value` property: typing into a field or assigning `.value` from script leaves it as the page served it (empty when the markup has none), only `setAttribute` changes it; on an `INPUT` of type submit, button or reset, assigning `.value` writes the attribute, so it always holds the caption; on a `SELECT` it is empty unless the markup sets it, and never holds the selection | a source predicate on the `value` attribute (XPath `@value`, CSS `[value=…]`) carries over as `value` with its criteria — the same attribute — never as `aaname`, which on a button with a `title` is that title; on a typed-into field `value` is the data the page was served with, and the current content is `text` (rule 4) |
| `innertext` | `textContent` — all descendants, hidden ones included; newlines become spaces; no trim, no whitespace collapsing | inherited by every ancestor (rule 5) |
| `visibleinnertext` | rendered `innerText` — hidden descendants excluded; no driver-side trim | inherited by every ancestor; the one to use for visible captions |
| `outertext` | identical to `innertext` | never adds information |
| long text values | truncated at 512 characters with trailing `*` | translation of a long caption must do the same |
| `title` | the **document** title | element's `title` attribute is `uipath-html-title` |
| `aria-role`, `aria-label`, `aria-labelledby`, `type`, `placeholder`, `href`, `src`, `alt`, `data-*` | raw DOM attribute | `role` on `webctrl` is a constant `element` — never use it, use `aria-role` |
| `labeledby` | label text the driver resolves for the element | separate attribute, not part of `aaname`; verify live before relying on it |
| `parentid`, `parentname`, `parentclass` | **nearest ancestor** with non-empty `id`/`name`/`class` (crosses shadow roots) | not the direct parent; the one-tag way to say "inside {container}" (`parentclass='*infobox*'`, `parentid='p-search'`) when the container's own tag would otherwise be needed only for scoping |
| `isleaf` | `1` when element has no element children (text-only counts as leaf) | pins innermost node of a text |
| `tableRow`, `tableCol`, `colName`, `rowName` | real `TABLE`/`TR`/`TD`/`TH` markup only, 1-based, header rows counted (under one header row the first data row is `tableRow` 2); `colName` is the **full text** of the header cell at the same column position — including visually hidden text the header carries, such as a sort caption (`Document CategorySort and filter column`); `rowName` is the text of the row's header cell as the driver reports it — a multi-line header concatenates without separators (`Capitaland largest city`), so a source rule of "header contains X" is carried as `rowName='*X*'`, never as the exact caption | absent on div-based grids (`role='grid'`), present on the many enterprise grids that still render `TABLE` (Workday's current grids do); choosing and cell shapes: rule 8 |
| `css-selector` | generated as a tag-name-only chain from `body` (`body>div>span>a`), no ids or classes; matched as a CSS selector on the candidate element (the browser's `Element.matches`), so any selector the browser accepts is a criterion, positions included | weak as generated — it names a depth, not an element; last resort; a source's positional path: § Rule 7 — web |
| `shadowhostid` | `id` of the shadow host of the element's root; host also gets its own tag in the chain | mandatory, even empty, on every tag whose node lives in a shadow root — without it the matcher never descends into shadow roots |
| frames | one `<webctrl tag='IFRAME' … />` (`FRAME`, `EMBED`) per frame level, carrying `id`, `name`, `src` (never `class`); nested frames give one tag per level | there is **no** `frame` attribute; SAP web frames are the exception and get no frame tag |
| `idx` | 1-based, document order, counted over all same-tag elements **in the subtree of the parent tag's element** that match the tag's other attributes — not siblings | omitted when match is unique |

Driver's own attribute preference when generating a selector, in order (stage one always emitted, later stages added only while they lower the index): `shadowhostid` (shadow DOM), `tag`, `tableRow`, `id`; `type`; `aria-role`; `aria-label`; `aria-labelledby`; Salesforce `sfl-*`; Ariba `aw-*`; Oracle ADF `adf-*`; `name`; `src` (frames); `parentid`; `parentname`; `class`; `aaname`; `isleaf`; `tabindex`; `tableCol`; `href`; `src`; `css-selector`. Volatility filters: an `id`, `parentid` or `aria-labelledby` containing a letter after a digit (`_oj146_smart-filter`, `input-45f6g7h8`) is rejected as auto-generated; a `class` with several tokens is never used at all (take one semantic token, wildcarded); `aaname` is offered only for `a`, `label`, `img`, `input`, `button`, `textarea`, `area`, `select`, `table`, `th`, for a `div`/`span` whose text is 32 characters or shorter, or under such an ancestor — and the offer depends on the activity type as well: a Click default may prefer a positional index over a multi-word caption that a `None` default keeps. SAP Fiori and Web GUI elements bypass this table and use their own families.

## Rule 4 — web

`aaname` on a form-ish element that has a programmatic label (`<label for>`, `aria-labelledby`, `title`, `alt`) is the *label* — an identity, and it stays: the driver's own default Type Into target avoids `aaname` (for most inputs it is content) and, on a form with several fields of one widget type, falls back to structural fragments (`id='*input*'`, a label-id fragment) that match every input of that type, so a migrated target keeps `aaname='<label>'` where the label is programmatic: it is unique where the driver's default is not. Live, the test is one read of the attribute list: `aaname` equal to the label text is identity; an element with no label falls back to its value or own text, and then `aaname` is content. Offline, keep `aaname` on a typed-into control only when the source recorded a label for it (the value is then the label), never when the source recorded only its text.

## Rule 5 — web

**The mechanical test for `aaname`.** Before writing `aaname` on a `webctrl`, decide which of three cases the node is in — the answer is forced, not a judgement call:

| Node | Does it carry `aaname`? |
|---|---|
| Form-ish tag — `A`, `INPUT`, `BUTTON`, `TEXTAREA`, `SELECT`, `IMG`, `AREA`, `TABLE` | Yes, **synthesised**: the driver builds it from `<label for>`, `title`, `alt`, text or value (§ attribute-getter table). An `INPUT`'s `aaname` is its label text — which is why a labelled field is targetable by its caption while its wrapper is not |
| Leaf that owns its text — a `DIV`/`SPAN`/`LI`/`LABEL`/`TH` with `isleaf='1'` and its own text node | Yes, an exact, non-inherited pin. Pair it with `isleaf='1'` so the match cannot drift to an ancestor, and with its `tag`: a labelled form control carries its label's text as its own `aaname`, so `aaname` + `isleaf` alone also matches the input a `LABEL` names (a hidden radio beside its caption) |
| Container — a `DIV`/`SPAN`/`SECTION`/`LI`/`UL`/`TR`… wrapping other elements (`isleaf='0'`) | **No** — the split is near-total, not a tendency: on enterprise SPA pages essentially no visible interactive container carries a non-blank `aaname` (whitespace-only values occur and are not names) while almost every text leaf does. `aaname` written on a wrapper was observed on one of its descendants and belongs on that descendant (rule 14); the wrapper's own identity is `aria-label` or `aria-labelledby` when it has any |

`aaname` is neither over- nor under-used as a category — it is *node-dependent*. `<webctrl tag='DIV' data-automation-id='promptOption' aaname='My Organizations' />` is correct, because that option label is a leaf owning its text. `<webctrl tag='DIV' aaname='Save' />` for a command button is not: the button is a `BUTTON`, and the `DIV` that wraps it has no name. Neither the caption nor the tag can be chosen without knowing which node is which.

## Rule 7 — web

**A positional web path is one `css-selector`.** A source that located a web element by a path of tag positions (`/HTML[1]/BODY[1]/DIV[3]/INPUT[1]`) and recorded no identifier or name for it carries the path as one `css-selector` on the element's `webctrl`, step for step: `tag[n]` is `tag:nth-of-type(n)` (both count the parent's children of that tag), a step with no index is its tag, `/` is `>` — `<webctrl tag='INPUT' css-selector='html>body>div:nth-of-type(3)>input:nth-of-type(1)' />`. Strict, flagged `positional`, in place of `idx` and rule 7's `<nav>` replay: `idx` counts every match in the document, and `tag` with `parentid` or ancestor tags takes the first element that fits — another element, or none, when the element has an earlier sibling of its tag, sits in a nested table or under a wrapper with its own id. An element in a frame keeps its frame tag before the `webctrl`; its path counts from the frame's document. A step with no CSS form (an axis, a function, a selection counted across the page) and a path the source sets at run time are the framework pack's to rule.

## Rule 8 — web

The column comes from the header caption: `colName` on web (`ui5-colLabel`, `sapweb-colname`, `aw-collabel` for the SAP web families). Whether a web grid exposes the table attributes at all is a property of its markup, not of the application: read one cell's attribute list live before choosing. When they are present, `colName` is the header's *full* text (wildcard the tail: `colName='Status*'`), `rowName` is the row's first cell text, and the row-by-content cell is `<webctrl tag='TD' rowName='<key text>' colName='<caption>*' />`. The trailing wildcard is load-bearing, not tidiness: a sortable header's full text usually carries a screen-reader caption after the visible one (`colName='PlacementSort and filter column'`), so the bare caption matches nothing while `'Placement*'` matches — confirmed on a live grid, both ways round. `rowName` is the row header cell's text as the driver reports it, which concatenates a multi-line header without separators (`Capitaland largest city`): a source key that equals the visible caption is carried as `rowName='<key text>'` when the header is one line, as `rowName='*<key text>*'` when the source matched by containment or the header may carry more than the key; when the key text is not unique in its column, pin the row container by the discriminating value instead. When they are absent, the row is a container pinned by exact text and the cell is its descendant. A row found by a descendant filter takes its key as `rowName` on the cell, or is pinned by `visibleinnertext`, which includes the descendant's text.

## Rule 9 — web

`url` keeps the host and wildcards the path — a host the source reads from configuration (an environment switch) is a selector variable in the screen's scope, bound to that setting's scheme, host and port by an argument of every workflow whose card attaches to the screen, never the value the setting held at build, which stops every attach once the setting points elsewhere.

On a single-page web application, one scope for its tab (rule 9) is the difference between one scope and thirty: the page title changes with every task, so title-derived scopes fragment into `'*App*'`, `'*App *'`, `'*App_Common*'`, `'Create Thing - App'` … each a separate object with its own failure mode, while the host never changed.

| Technology | Scope on | Shape |
|---|---|---|
| Web | `url` — host kept, path wildcarded | `<html app='chrome.exe' url='https://host.example.com/*' />` |
| Web, two tabs of the **same** host open at once | `url` **plus** a title fragment | add `title='*Fragment*'` to the shared url scope |

**`url` values are case-sensitive** (only `app`, and `tag` on `webctrl`, are not), so `url='*Site*'` and `url='*site*'` are different selectors and at most one of them matches. The driver's own default for a browser tab is `<html app='chrome.exe' title='*<App>*' url='https://<host>/<tenant path>*' />` — host plus the first path segment, title reduced to the application's word; take that shape, and drop `title` when a second tab of the same host is never open.

## Rule 14 — web

The merge rule 14 forbids, on a Workday prompt:

```
<webctrl tag='DIV' data-automation-id='responsiveMonikerInput' aaname='Supervisory Organization' />
```

The container does carry that `data-automation-id`, and the field is labelled that way — but the container has no `aaname` at all (its own text is `"Select multiple." 0 items selected`), so the whole selector fails. The element that takes the typing is an `INPUT` several levels down, whose `aaname` *is* the label (the driver resolves `<label for>`) and which carries no `data-automation-id`. Either node is targetable; the merge of the two is not.

Provenance and uniqueness on a repeated web widget:

| Shape | Provenance | Unique? |
|---|---|---|
| `<webctrl tag='DIV' data-automation-id='monikerInput' aaname='Location' />` | ✗ merged from two nodes | never matches |
| `<webctrl tag='DIV' data-automation-id='monikerInput' /><webctrl tag='INPUT' />` | ✓ two nodes, two tags | ✗ — matches every instance of the widget; the engine resolves it only by adding `idx`, which rule 7 puts last |
| `<webctrl tag='INPUT' aaname='Location' />` | ✓ one node | ✓ — the driver synthesises the input's `aaname` from its `<label for>` |

**Where the tag comes from, in order.** An absent `tag` only widens the search; a wrong one eliminates the only correct candidate. So take the tag from the strongest evidence available and never from habit:

1. **A tag the source read out of markup** — a recorded `tagname`, an `innerhtml` fragment beginning `<button`. This is an observation of the node the recorder attached to, and it outranks everything below.
2. **The node's role, when a known role identifier names it.** A component framework's `data-*` role ids have fixed node types (an icon-action `DIV`, a text-area field, a page-title `SPAN`, an option row `DIV`). Once one instance has been seen — live, or in the framework's own documentation — that role's tag is known for every instance of it, and it outranks the control type.
3. **The tag the control type implies** — a command button is a `BUTTON`, a text field an `INPUT`, a link an `A`. This is the weakest of the three, because a source's control *type* is its own abstraction over the widget, not a reading of the DOM: component frameworks render buttons as `DIV`s, "text boxes" as `TEXTAREA`s and page titles as `SPAN`s, and a recorder that classified the widget will still have recorded the real tag.
4. **Omit `tag`** when none of the above applies.

**`DIV` is never a *default* — but a recorded `DIV` is evidence.** Writing `tag='DIV'` because the node "looks like a container" is the same fabrication as guessing an identifier, and `tag='BUTTON'` on a control the source recorded as a `DIV` is the same mistake in the other direction: both replace an observation with a habit. When 1 and 3 disagree, 1 is right, and the disagreement is worth counting across the export before deriving anything: a source whose control types and recorded tags disagree for a large share of its controls is telling you its type vocabulary is a classification of widgets, not a reading of the DOM, and that every tag derived from a type alone is a guess.

## Rule 16 — web

The roles of rule 16 on a web widget, with Workday's identifiers as one worked example:

| Role | What it is | Identity it exposes | Which step uses it |
|---|---|---|---|
| wrapper | outermost `DIV` of the widget, carrying the component-type id (`data-automation-id='responsiveMonikerInput'`, `'selectWidget'`, `'dateTimeWidget'`) and sometimes a per-instance id | type id (repeated per instance), instance id when present, inner text (volatile: it contains the current value) | scope only, and only with an instance id |
| label | `LABEL for=…` or a caption leaf beside the widget | its own text as `aaname` | the start of a `<nav>` path to the acting leaf (rule 6), or the text that pins the form item |
| form item | the `LI`/`DIV` that holds label and widget | inner text starting with the label | scope for children with no name of their own (rule 14 step 2) |
| acting leaf | the `INPUT`/`TEXTAREA`/`BUTTON`/combobox `DIV` that takes the keystrokes or the click | `aaname` = label on form-ish tags; `aria-role`/`aria-labelledby` on a div-based control; no `aaname` on icon buttons (`aria-label` instead) | Type Into, Click, Check |
| value display | the chip, pill or selected-option text that shows what the field now holds (`selectedItem` + `promptOption`, `selectSelectedOption`, a hidden "current value is …" leaf) | `aria-label`/`aaname` = the value | the **verify** of a pick, scoped to the field |
| popup list | the suggestion or option list the widget opens (`activeListContainer`, `menuList`), usually **labelled with the field's name** (`aria-label='Position Status, Options Expanded'`, `'Column'`) | `aria-label` = field name; `aria-role` menu/listbox | scope for the entry |
| popup entry | one option: a container (`menuItem`, `aria-role='option'`, `aria-label` = option) around a text leaf (`promptOption`, `aaname` = option) | the option text | the **pick** click |

Three traps follow from the cast. **The value display and the popup entry often share a component-type id and the same text** (`promptOption` names both the selected chip and every list entry — and the two can even differ only by tag, the chip a `P` and the list row a `DIV`, which is no help offline): a verify on the bare text leaf passes while the list is still open, before anything was accepted, so the verify target is the value display *scoped to the field*, and the pick target is the entry *scoped to the popup labelled with the field* — `<webctrl tag='LI' visibleinnertext='Location*' /><webctrl data-automation-id='selectedItem' aria-label='{0}*' />` against `<webctrl data-automation-id='activeListContainer' aria-label='Location*' /><webctrl data-automation-id='promptOption' aaname='{0}' />`. **The wrapper's inner text is the field's current value**, so a wrapper pinned by `visibleinnertext` (which the driver's default for the wrapper does) is volatile and never survives a data change. Whether a custom list exposes `items` is a property of the widget and its version — one exposes only `selecteditem`, another lists every caption — so probe the control's `items` live (the package's element-interaction commands) before choosing Select Item over open-and-click ([ui-target-migration-guide.md § Composite interactions](ui-target-migration-guide.md)). Segmented inputs (date month/day/year) are three acting leaves under one form item; only the first carries the field label, and a later segment is reached from it by a climb to the widget that names the segment (rule 6). **A popup list is not always a flat list of values**: the same widget may open a *hierarchy* whose first level is categories that drill down, so the entries on screen before anything is typed are not the values the step picks from — the leaf values appear only once the typed text filters, which is why the pattern types first and picks second, and why a pick that "found" an entry without typing has probably picked a category.

**A value display may render the value inside a sentence** rather than as the bare value — a hidden read-back leaf whose text reads `current value is <the value>`, for the benefit of screen readers. Read one before choosing the compare: a verify written as equality against such a leaf can never pass, and the correct check is `contains` on the value.

## Checks

| Check | Decide by | Rule |
|---|---|---|
| `aaname` on a container tag (`DIV`, `SPAN`, `LI`, `UL`, `TR`, `SECTION`, …) with no `isleaf='1'` | attributes | 5, 14 |
| A `data-*` type identifier is the only discriminator and the selector carries `idx` | attributes | 7, 14 |
| `tag='DIV'` that no source recording and no known role vouches for, on a control the source typed as a button, input, checkbox or link — and the mirror case, a type-implied `tag` that contradicts the tag the source recorded | attributes + source control type + the recorded tag | 14 |
| A caption-only target on a control whose source row also carried a role identifier (the id was dropped as a wrapper's when the role is a leaf's) | attributes + the source row's identifiers | 14 |
| More than one distinct `ScopeSelectorArgument` per host across the project; `url` values differing only by case; a web scope with `title` and no `url` | all definitions | 9 |
| `colName` written as the bare caption on a grid whose headers carry hidden suffixes | live attribute listing on one cell | 8 |
| A control the source located by a positional web path, carried as `idx`, as ancestor tags or with the path's indexes dropped | attributes + the source's path | 7 |
