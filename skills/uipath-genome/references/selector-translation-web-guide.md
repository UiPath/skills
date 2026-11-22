# Selector Translation — the web

The web's side of [selector-translation-guide.md](selector-translation-guide.md): what each rule adds for pages driven through the browser driver — browsers, SAP Fiori, Web GUI and Ariba, web views. Read whole with that guide when the target catalog holds web controls, together with the `html` and `webctrl` attribute references and reliability rankings of the UI Automation package's Selector Reference (that guide names where it is read): what each attribute holds, how the web extension computes it, how a search visits the page, and which values to keep, wildcard or drop. Rule numbers are that guide's.

## Rule 1 — web

**The browser's `app`.** A source recording only "Chrome", "Edge" or "IE" as browser choice maps to the executable the `html` attribute reference lists for it; a source recording nothing gets a Configuration Question ("Which browser runs the automation?", default Chrome → `chrome.exe`). Never leave `app` for the run time to default.

**A container without a tag of its own.** `parentid`, `parentname` and `parentclass` say "inside that container" on the element's own tag (`parentclass='*infobox*'`, `parentid='p-search'`), where the container's tag would be needed only for scoping.

## Rule 2 — web

Which `webctrl` attributes hold their text padded, or with tabs and line breaks, is the `webctrl` attribute reference's. Two take rule 2's whitespace row even for an exact caption: a table row's `visibleinnertext`, which carries the tabs of its empty cells, for a caption not seen live; and `rowName` / `colName`, which indented markup pads, with `\s*` at both ends. A recorded text that holds line breaks keeps them, each written `&#10;`: an equals stays an equals (rule 2), never a prefix with a wildcard in their place.

## Rule 4 — web

`aaname` on a form-ish element that has a programmatic label (`<label for>`, `title`, `alt`) is the *label* — an identity, and it stays: the driver's own default Type Into target avoids `aaname` (for most inputs it is content) and, on a form with several fields of one widget type, falls back to structural fragments (`id='*input*'`, a label-id fragment) that match every input of that type, so a migrated target keeps `aaname='<label>'` where the label is programmatic: it is unique where the driver's default is not. Live, the test is one read of the attribute list: `aaname` equal to the label text is identity; an element with no label falls back to its value or own text, and then `aaname` is content. Offline, keep `aaname` on a typed-into control only when the source recorded a label for it (the value is then the label), never when the source recorded only its text.

A source predicate on the `value` attribute (XPath `@value`, CSS `[value=…]`) carries over as `value` with its criteria — the same attribute — never as `aaname`, which on a button with a `title` is that title. On a typed-into field `value` is the data the page was served with, and the current content is `text`.

## Rule 5 — web

**The mechanical test for `aaname`.** Before writing `aaname` on a `webctrl`, decide which of the three cases of the `webctrl` attribute reference (which nodes carry `aaname`) the node is in — the answer is forced, not a judgement call:

| Node | `aaname` on its tag |
|---|---|
| Form-ish tag | Yes: the name the driver synthesises, which on a labelled `INPUT` is its label text — a labelled field is targetable by its caption while its wrapper is not |
| Leaf that owns its text | Yes, an exact, non-inherited pin. Pair it with `isleaf='1'` so the match cannot drift to an ancestor, and with its `tag`: a labelled form control carries its label's text as its own `aaname`, so `aaname` + `isleaf` alone also matches the input a `LABEL` names (a hidden radio beside its caption) |
| Container wrapping other elements | **No.** `aaname` written on a wrapper was observed on one of its descendants and belongs on that descendant (rule 14); the wrapper's own identity is `aria-label` or `aria-labelledby` when it has any |

`aaname` is neither over- nor under-used as a category — it is *node-dependent*. `<webctrl tag='DIV' data-automation-id='promptOption' aaname='My Organizations' />` is correct, because that option label is a leaf owning its text. `<webctrl tag='DIV' aaname='Save' />` for a command button is not: the button is a `BUTTON`, and the `DIV` that wraps it has no name. Neither the caption nor the tag can be chosen without knowing which node is which.

## Rule 7 — web

**A positional web path is one `css-selector`.** A source that located a web element by a path of tag positions (`/HTML[1]/BODY[1]/DIV[3]/INPUT[1]`) or of child positions (`3|-3`, the element's place among its parent's element children at each level, `-k` counted from the last) and recorded no identifier or name for it carries the path as one `css-selector` on the element's `webctrl`, step for step: `tag[n]` is `tag:nth-of-type(n)` (both count the parent's children of that tag), a step with no index is its tag, a child position `k` is `:nth-child(k)` and `-k` is `:nth-last-child(k)` (both count every element child), and each level is `>` — `<webctrl tag='INPUT' css-selector='html>body>div:nth-of-type(3)>input:nth-of-type(1)' />`, `<webctrl tag='SPAN' css-selector='body>:nth-child(3)>:nth-last-child(3)' />`. The element's tag goes on the `webctrl` beside a child-position path, so a path that ends on another node matches nothing. Strict, flagged `positional`, in place of `idx` and rule 7's `<nav>` replay: `idx` counts every match in the document, and `tag` with `parentid` or ancestor tags takes the first element that fits — another element, or none, when the element has an earlier sibling of its tag, sits in a nested table or under a wrapper with its own id. An element in a frame keeps its frame tag before the `webctrl`; its path counts from the frame's document. A step with no CSS form (an axis, a function, a selection counted across the page) and a path the source sets at run time are the framework pack's to rule.

## Rule 8 — web

The column comes from the header caption: `colName` on web (`ui5-colLabel`, `sapweb-colname`, `aw-collabel` for the SAP web families). Whether a web grid exposes the table attributes at all is a property of its markup, not of the application: read one cell's attribute list live before choosing. When they are present, what `colName` and `rowName` hold is the `webctrl` attribute reference's, and the row-by-content cell is `<webctrl tag='TD' rowName='<key text>' colName='<caption>*' />`. The trailing wildcard on `colName` is load-bearing, not tidiness: a sortable header's full text usually carries a screen-reader caption after the visible one, so the bare caption matches nothing while `'Placement*'` matches. A source key that equals the visible caption is carried as `rowName='<key text>'` when the header is one line, as `rowName='*<key text>*'` when the source matched by containment or the header may carry more than the key; when the key text is not unique in its column, pin the row container by the discriminating value instead. When they are absent, the row is a container pinned by exact text and the cell is its descendant. A row found by a descendant filter takes its key as `rowName` on the cell, or is pinned by `visibleinnertext`, which includes the descendant's text.

## Rule 9 — web

`url` keeps the host and wildcards the path — a host the source reads from configuration (an environment switch) is a selector variable in the screen's scope, never the value the setting held at build, which stops every attach once the setting points elsewhere. A workflow whose card opens the application, or attaches by the screen's selector, binds the variable to that setting's scheme, host and port through an argument. A workflow given the application's handle takes no argument for the host and binds the variable to the scheme, host and port of the handle's `url` attribute.

**A browser card works in one tab** (the UI Automation package's Target System doc, § Window Selector), so each tab the automation works in takes a card of its own: attached by the tab's screen selector once the tab is open, or given that tab's handle. A source that switches tabs, or acts in a tab a click opened, switches cards there.

On a single-page web application, one scope for its tab (rule 9) is the difference between one scope and thirty: the page title changes with every task, so titles derived per screen fragment into `'*App*'`, `'*App *'`, `'*App_Common*'`, `'Create Thing - App'` … each a separate object with its own failure mode, while the host never changed. The title's stable part there is the application's word, which every page's title shows, so the tab's one scope carries it. `html`'s `title` is the tab's page title, not the browser window's caption: a window caption the source recorded ends with the browser's name (` - Google Chrome`), which the scope drops.

| Technology | Scope on | Shape |
|---|---|---|
| Web | `url` — host kept, path wildcarded — plus the title's stable part | `<html app='chrome.exe' title='*App*' url='https://host.example.com/*' />` |
| Web, two tabs of the **same** host open at once | the same, with the title fragment that tells the tabs apart | `title='*Fragment*'` in place of the application's word |

**`url` values are case-sensitive** (the `html` attribute reference), so `url='*Site*'` and `url='*site*'` are different selectors and at most one of them matches. The driver's own default for a browser tab is `<html app='chrome.exe' title='*<App>*' url='https://<host>/<tenant path>*' />` — host plus the first path segment, title reduced to the application's word; take that shape.

**One browser window can hold two scopes.** A page's scope is the tab's `html` tag alone, whatever the source attached by — a window title, a window class: a `wnd` tag before an `html` narrows nothing (the Selector Reference's tags per technology). An element the source recorded through UI Automation in the same browser window — the tab strip, a toolbar button, a dialog the browser draws, page content read through UI Automation — is a `uia` target under the browser's `wnd` scope, on a screen of the browser's own application, not the page host's ([ui-target-migration-guide.md § Object Repository identity](ui-target-migration-guide.md) rule 2).

## Rule 10 — web

SAP's web frameworks build their ids from the screen, not from a hash, so rule 10 keeps more of them than their look suggests. What each id encodes: the `webctrl` attribute reference, SAP web identifiers.

| Id | On `webctrl` |
|---|---|
| SAP Web GUI DOM `id` (`M0:46:::1:34`, `M0:50::btn[8]`), which `sapweb-lsid` repeats | a field's: `id` as recorded, medium confidence, when nothing better was recorded; the live pass replaces it with `sapweb-id`. A toolbar button's: `sapweb-id='wnd[0]/tbar[*]/btn[8]'` — the window and the function code carry over, the toolbar number does not |
| SAP Web GUI `sapweb-id` (`wnd[0]/usr/ctxtMS_MATNR-LOW`) | taken whenever seen; a field's is not derivable from its DOM id |
| SAP Fiori DOM `id`, `<view id>--<local id>` | `ui5-view-local-id` with the part after the view's `--`; an id ending `-inner` is the `INPUT` inside the control whose id precedes it, and the control and that `INPUT` are two nodes (rule 14) |

A recorded text or name that is one character from U+E000–U+F8FF is an icon font's glyph, not a name: a button that shows only an icon holds it as its inner text, and its name is in `aria-label`, else in `uipath-html-title`.

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

Three traps follow from the cast. **The value display and the popup entry often share a component-type id and the same text** (`promptOption` names both the selected chip and every list entry — and the two can even differ only by tag, the chip a `P` and the list row a `DIV`, which is no help offline): a verify on the bare text leaf passes while the list is still open, before anything was accepted, so the verify target is the value display *scoped to the field*, and the pick target is the entry *scoped to the popup labelled with the field* — `<webctrl tag='LI' visibleinnertext='Location*' /><webctrl data-automation-id='selectedItem' aria-label='{0}*' />` against `<webctrl data-automation-id='activeListContainer' aria-label='Location*' /><webctrl data-automation-id='promptOption' aaname='{0}' />`. **The wrapper's inner text is the field's current value**, so a wrapper pinned by `visibleinnertext` (which the driver's default for the wrapper does) is volatile and never survives a data change. Whether a custom list exposes `items` is a property of the widget and its version — one exposes only `selecteditem`, another lists every caption — so probe the control's `items` live (the package's element-interaction commands) before choosing Select Item over open-and-click ([composite-interactions-guide.md](composite-interactions-guide.md)). Segmented inputs (date month/day/year) are three acting leaves under one form item; only the first carries the field label, and a later segment is reached from it by a climb to the widget that names the segment (rule 6). **A popup list is not always a flat list of values**: the same widget may open a *hierarchy* whose first level is categories that drill down, so the entries on screen before anything is typed are not the values the step picks from — the leaf values appear only once the typed text filters, which is why the pattern types first and picks second, and why a pick that "found" an entry without typing has probably picked a category.

**A value display may render the value inside a sentence** rather than as the bare value — a hidden read-back leaf whose text reads `current value is <the value>`, for the benefit of screen readers. Read one before choosing the compare: a verify written as equality against such a leaf can never pass, and the correct check is `contains` on the value.

## Rule 17 — web

How a `webctrl` search visits the page — its order, shadow roots, frames, hidden elements — is the `webctrl` attribute reference's. What each decision of the source's finder becomes:

| The finder | On `webctrl` |
|---|---|
| enters shadow roots (an engine that pierces open shadow roots, a script that walks `shadowRoot`) | `shadowhostid='*'` on every tag translated without seeing the page: such a locator does not record which controls sit in one |
| enters frames | one frame tag per level, as the `webctrl` attribute reference gives it |
| considers visible elements only | `uipath-visible='1'` on the tag. Without it a hidden copy earlier in the page is the match — a closed menu's entry, a collapsed header's caption |
| compares the element's own text | `aaname` on the node that owns the text, with its `tag` (§ Rule 5); on a `BUTTON`, whose `aaname` is its `title` first, `visibleinnertext` |
| compares text with the descendants' included | `visibleinnertext`, or `innertext` where hidden text counts, on a tag with a criterion of its own (rule 5) |
| compares the accessible name | the name on `visibleinnertext` where the node shows it as text — a button, a link, a tab, a menu entry; on an `INPUT` button, `value`, which holds its caption; on a field, `labeledby`; on a node named by its `aria-label` alone (an icon button, a link around an image), `aria-label`. A button or link translated without seeing the page takes `visibleinnertext`, with `aria-label` as the live check's alternative; for a field whose name `labeledby` does not hold (the `webctrl` attribute reference), the live check names `uipath-html-title`, the label as the field's scope, or a path from the naming element (rule 6). Each compared as rule 2 gives for whitespace |
| selects by role, whichever element carries it | the role's native elements and the written role as one `css-selector`: `button` → `'button, input[type=button], input[type=submit], input[type=reset], input[type=image], [role=button]'`, `link` → `'a[href], area[href], [role=link]'`, `textbox` → `'input:not([type]), input[type=text], input[type=email], input[type=tel], input[type=url], textarea, [role=textbox]'`, `searchbox` → `'input[type=search], [role=searchbox]'`, `combobox` → `'select:not([multiple]), [role=combobox]'`, `checkbox` → `'input[type=checkbox], [role=checkbox]'`, `radio` → `'input[type=radio], [role=radio]'`, `heading` → `'h1, h2, h3, h4, h5, h6, [role=heading]'`, `option` → `'option, [role=option]'`, `dialog` → `'dialog, [role=dialog]'`, `img` → `'img, [role=img]'`, `listitem` → `'li, [role=listitem]'`; a role no element carries natively (`tab`, `menuitem`) → `aria-role`. Neither `tag` nor `aria-role` alone covers both. The name goes where the accessible-name row says |
| returns the innermost match | `isleaf='1'` |
| returns an ancestor of its match — the link or button that takes the click | the text on the ancestor's `visibleinnertext`, which holds its descendants' text |

With no `tag`, the text goes on `visibleinnertext` with `isleaf='1'`: the match is the element that shows the text, never a wrapper or a form control, and a click on it reaches the control around it.

On a live pass a tag drops `uipath-visible` only where the page, in every state the step meets, holds no hidden copy of its node; a role's `css-selector` becomes the `tag` or `aria-role` the node has, and `shadowhostid` stays on a node inside a shadow root: `'*'`, or the host's `id` only where that id is authored (not a counter) and tells two matches apart.

## Checks

| Check | Decide by | Rule |
|---|---|---|
| Text on `aaname` with no `tag`; a tag translated without seeing the page with no `shadowhostid` where the finder enters shadow roots, or no `uipath-visible` where it skips hidden elements | attributes + the finder | 17 |
| `aaname` on a container tag (`DIV`, `SPAN`, `LI`, `UL`, `TR`, `SECTION`, …) with no `isleaf='1'` | attributes | 5, 14 |
| A `data-*` type identifier is the only discriminator and the selector carries `idx` | attributes | 7, 14 |
| `tag='DIV'` that no source recording and no known role vouches for, on a control the source typed as a button, input, checkbox or link — and the mirror case, a type-implied `tag` that contradicts the tag the source recorded | attributes + source control type + the recorded tag | 14 |
| A caption-only target on a control whose source row also carried a role identifier (the id was dropped as a wrapper's when the role is a leaf's) | attributes + the source row's identifiers | 14 |
| More than one distinct `html` scope (`ScopeSelectorArgument`) per host across the project, unless a second tab of the host tells them apart; `url` values differing only by case; a web scope with `title` and no `url`, or with no title fragment where every page's title shares one | all definitions + the titles the source recorded | 9 |
| `colName` written as the bare caption on a grid whose headers carry hidden suffixes | live attribute listing on one cell | 8 |
| A control the source located by a positional web path, carried as `idx`, as ancestor tags or with the path's indexes dropped | attributes + the source's path | 7 |
