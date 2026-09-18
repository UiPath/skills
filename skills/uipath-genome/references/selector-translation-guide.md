# Selector Translation Guide — source locators → UiPath targets

The UiPath side of UI target migration, shared by every source framework. A source guide's selectors companion (e.g. [sources/worksoft-certify-selectors-guide.md](sources/worksoft-certify-selectors-guide.md)) says what *its* framework recorded and which UiPath attribute each recorded field becomes; this guide says what UiPath can match on, per technology, and the rules every translation obeys. Vocabulary comes from the UiPath driver's selector schema (tag names, attribute names) and the UI Automation package's selector references (reliability tiers). Execution mechanics — creating Object Repository elements, linking, reporting — stay in [source-migration-guide.md](source-migration-guide.md); shapes for the no-application case in [offline-definition-workarounds-guide.md](offline-definition-workarounds-guide.md).

## Technology → tag chain

A UiPath selector is a chain of tags: one top-level tag for the window or browser tab, then one tag per level of the element's ancestry that is needed to identify it. The technology of the source control decides the tags; a chain never mixes tags of two technologies below the same window unless the technology genuinely changes (browser chrome UI vs page content, a Java applet inside a browser).

| Source technology | Top-level tag | Element tag | Notes |
|---|---|---|---|
| Browser page (Chrome, Edge, Firefox) | `<html app='chrome.exe' title='…' url='…' />` | `<webctrl … />` | `app` is the browser executable; sources rarely record it → Configuration Question (browser choice), default `chrome.exe` |
| SAP web (Fiori/UI5, Web GUI, Web Dynpro, Ariba) | `<html … />` | `<webctrl … />` with `ui5-*`, `sapweb-*`, `aw-*` attributes | Prefer the SAP attributes over generic HTML ones on the same element |
| SAP GUI for Windows | `<wnd app='saplogon.exe' cls='SAP_FRONTEND_SESSION' title='…' />` | `<sap id='…' />` | Modal dialogs are own windows: `cls='#32770'`, title = dialog caption |
| SAP GUI for Java | `<wnd app='java*.exe' cls='SunAwtFrame' title='…' />` | `<sap id='…' />` | Dialogs `cls='SunAwtDialog'`; custom Java classes surface as `<java>` |
| Windows desktop recorded through UI Automation (WPF, WinForms, Win32, UWP, Electron shells, browser chrome UI) | `<wnd app='<exe>' cls='…' title='…' />` | `<uia … />` | Default for any control recorded with UI Automation properties (control type, name, automation id, class name) |
| Windows desktop recorded through Active Accessibility (MSAA) | `<wnd … />` | `<ctrl … />` | When the source recorded MSAA role/name/state, or as the alternative framework when UIA does not surface the element |
| Classic Win32 child windows (HWND controls) | `<wnd … />` | nested `<wnd cls='…' ctrlid='…' ctrlname='…' />` | Dialog controls that own a window handle |
| Java Swing/AWT | `<wnd app='java*.exe' cls='SunAwtFrame' title='…' />` | `<java … />` | Java Access Bridge required at run time |
| Qt | `<wnd … />` | `<qt … />` | |
| Remote desktop with the UiPath remote runtime (Citrix, RDP, VMware) | `<rdpapp … />` / `<rdp … />` | native tags of the remote application | `<rdp>` carries the `<wnd>` attribute set |
| macOS | `<wnd app='…' title='…' />` | `<ax … />` | |
| Terminal / mainframe (3270, 5250) | none | none | Not a selector technology: UiPath Terminal activities address the screen by row and column. A source screen map translates to terminal field positions, not selectors |
| Image / pattern / coordinate recognition | window tag | none | No selector. Computer Vision or image target; confidence **low**; live capture owed |
| Relative navigation between tags | | `<nav up='n' />`, `<nav next='n' />`, `<nav prev='n' />` | Anchoring to a related element; never `up='0'` |

`<wnd>` needs `app` (executable name) and `<html>` needs `app` (browser). No test framework records the executable; take it from the source's application record or the step that launches the application, else a Configuration Question with the technology default.

## Tag attribute catalog

Attribute names are the driver's; the tag schema is closed for every tag except `webctrl` (any HTML attribute) — a translation may not invent an attribute that is not listed here. Reliability tiers: **very reliable**, **alright**, **table**, **last resort** follow the UI Automation package's per-tag references; rows marked *derived* apply the general rule (developer identifier > semantic name > text > structure > state/position) where the package documents nothing. Roles: **identity** (developer identifier), **semantic** (name, label, role), **text** (content — purpose-constrained, § Rules 4–5), **structure** (never alone), **table**, **position** (strict only), **state** (never in a target), **session** (top-level discriminators), **runtime** (readable through Get Attribute, never matched).

### `wnd` — window

| Attribute | Meaning | Tier / role |
|---|---|---|
| `app` | executable name (`saplogon.exe`) | very reliable — mandatory |
| `cls` | window class (`SAP_FRONTEND_SESSION`, `#32770`, `Chrome_WidgetWin_1`) | very reliable |
| `title` | window caption | alright — keep at least part, wildcard the volatile part |
| `aaname` | accessible name | alright |
| `ctrlname` | WinForms control name | identity — reliable when present |
| `ctrlid` | Win32 control id | identity for fixed dialogs; positional in dynamic UIs |
| `automationid` | UI Automation id on the window | identity |
| `idx` | position among matches | position — strict only |
| `aastate` | accessibility state | state — never |
| `sapSysName`, `sapClient`, `sapUser`, `sapLanguage`, `sapTransaction`, `sapWindowName` | SAP GUI session context on the session window | session — `sapSysName`/`sapClient` discriminate systems when several are in play |
| `sapSession`, `sapGuiSessionId`, `sapSysSessionId`, `sapSysNumber`, `pid`, `tid`, `gid`, `appid`, `isremoteapp`, `hwnd` | runtime identities | runtime — never |

### `html` — browser tab

| Attribute | Meaning | Tier / role |
|---|---|---|
| `app` | browser executable — selects the browser driver at run time | critical — never drop: an empty or missing `app` is treated as Internet Explorer |
| `url` | page URL | very reliable — wildcard the path, keep the host: `url='https://host/*'` |
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
| Microsoft Edge WebView2 (embedded in a desktop app) | `msedgewebview2.exe` |
| Microsoft Edge (legacy, UWP) | `ApplicationFrameHost.exe` |
| Mozilla Firefox | `firefox.exe` |
| Internet Explorer | `iexplore.exe` — also the default when `app` is empty or missing |
| Brave, Vivaldi | `brave.exe`, `vivaldi.exe` |
| Custom Chromium-based browser (with the UiPath extension) | `custom_browser` |
| Safari (macOS) | `Safari` |

A source that records only "Chrome", "Edge" or "IE" as a browser choice maps to these executables; a source that records nothing gets a Configuration Question ("Which browser runs the automation?", default Chrome → `chrome.exe`). Never leave `app` for the run time to default.

### `webctrl` — HTML element (open schema)

| Tier | Attributes |
|---|---|
| very reliable | `tag`, `aria-label`, `aria-labelledby`, `aria-role`, `aria-describedby`, `shadowhostid`; author-controlled `data-*` identifiers (`data-testid`, `data-automation-id`, `data-cy`) |
| alright | `id`, `parentid`, `name`, `parentname`, `type`, `isleaf`, `aaname`, `visibleinnertext`, `innertext` |
| table | `tableCol`, `tableRow`, `colName`, `rowName` |
| last resort | `action`, `alt`, `href`, `src`, `tabindex`, `placeholder`, `uipath-html-title` (the element's `title` attribute), `css-selector`, `class`, `parentclass`, `aria-pressed` |
| last resort — framework-generated | `ng-reflect-*`, `ng-version`, `_ngcontent-*`, `_nghost-*`, `data-reactid`, `__reactProps$*`, `v-*`, `data-v-*` |
| SAP Fiori / UI5 | very reliable `ui5-label`, `ui5-tooltip`, `ui5-role`, `ui5-type`, `ui5-view-local-id`; alright `ui5-class`; tables `ui5-tableCol`, `ui5-tableRow`, `ui5-colLabel`, `ui5-isEmpty`; trees `ui5-path` |
| SAP Web GUI | very reliable `sapweb-id` (scripting id), `sapweb-type`; alright `sapweb-lsclass`, `sapweb-text`, `sapweb-itemid`; tables `sapweb-tablerow`, `sapweb-tablecol`, `sapweb-colname`, `sapweb-coltooltip`; trees `sapweb-path`; avoid `sapweb-lsid` |
| SAP Ariba | very reliable `aw-name`, `aw-label`, `aw-type`; tables `aw-tablerow`, `aw-tabledetailrow`, `aw-tablerowtype`, `aw-tablecol`, `aw-collabel`; avoid `id` (session hash) |

Hard rules for `webctrl`: a tag whose node sits inside a shadow DOM must carry `shadowhostid` (even empty); `frame`/`iframe` tags are never removed; `class` keeps only the semantic core (`class='*search-input*'`), never utility tokens or build hashes; ids with three or more dot-separated structural segments are wildcarded to the last semantic segments; hash-suffixed custom tag names are wildcarded (`tag='MACROPONENT-*'`); a `DIV`/`SPAN` without a semantic attribute is not a target on its own.

How the browser driver computes the attributes a translation leans on (the web extension's attribute getters):

| Attribute | Computed as | Consequence for translation |
|---|---|---|
| `tag` | the DOM tag name, upper-case for HTML elements | matched case-insensitively |
| `aaname` | a legacy MSAA-style name, **not** the ARIA accessible name. For `A`, `INPUT`, `IMG`, `BUTTON`, `TEXTAREA`, `AREA`, `SELECT`, `TABLE`: buttons `title` → text/value; images `title` → `alt` → `<label for>` (→ the enclosing `A`); tables `title` → caption → header cells; other form elements and links `<label for>` text → own text/value → `title` → `alt`. For **every other element**: the element's **own direct text nodes only** | never reads `aria-label`, `aria-labelledby`, `placeholder` or a wrapping `<label>`; a container's `aaname` is not inherited from descendants, so `aaname` on a bare `DIV`/`SPAN`/`LABEL` caption is an exact, non-inherited pin; an input's `aaname` is its `<label for>` text when the input has an `id` |
| `innertext` | `textContent` — all descendants, hidden ones included; newlines become spaces; no trim, no whitespace collapsing | inherited by every ancestor (rule 5) |
| `visibleinnertext` | rendered `innerText` — hidden descendants excluded; no driver-side trim | inherited by every ancestor; the one to use for visible captions |
| `outertext` | identical to `innertext` | never adds information |
| long text values | truncated at 512 characters with a trailing `*` | a translation of a long caption must do the same |
| `title` | the **document** title | the element's `title` attribute is `uipath-html-title` |
| `aria-role`, `aria-label`, `aria-labelledby`, `type`, `placeholder`, `href`, `src`, `alt`, `data-*` | the raw DOM attribute | `role` on `webctrl` is a constant `element` — never use it, use `aria-role` |
| `labeledby` | the label text the driver resolves for the element | a separate attribute, not part of `aaname`; verify live before relying on it |
| `parentid`, `parentname`, `parentclass` | the **nearest ancestor** with a non-empty `id`/`name`/`class` (crosses shadow roots) | not the direct parent |
| `isleaf` | `1` when the element has no element children (text-only counts as leaf) | pins the innermost node of a text |
| `tableRow`, `tableCol`, `colName`, `rowName` | real `TABLE`/`TR`/`TD`/`TH` markup only, 1-based; `colName` is the header cell at the same column position, `rowName` the first header cell of the row | **absent on ARIA grids** (`role='grid'`, div-based tables); those use the framework families (`ui5-*`, `sapweb-*`, `aw-*`) or a text-pinned row container |
| `css-selector` | tag-name-only chain from `body` (`body>div>span>a`), no ids or classes | weak; last resort |
| `shadowhostid` | the `id` of the shadow host of the element's root; the host also gets its own tag in the chain | mandatory, even empty, on every tag whose node lives in a shadow root — without it the matcher never descends into shadow roots |
| frames | one `<webctrl tag='IFRAME' … />` (`FRAME`, `EMBED`) per frame level, carrying `id`, `name`, `src` (never `class`); nested frames give one tag per level | there is **no** `frame` attribute; SAP web frames are the exception and get no frame tag |
| `idx` | 1-based, document order, counted over all same-tag elements **in the subtree of the parent tag's element** that match the tag's other attributes — not siblings | omitted when the match is unique |

The driver's own attribute preference when it generates a selector, in order (stage one is always emitted, later stages are added only while they lower the index): `shadowhostid` (shadow DOM), `tag`, `tableRow`, `id`; `type`; `aria-role`; `aria-label`; `aria-labelledby`; Salesforce `sfl-*`; Ariba `aw-*`; Oracle ADF `adf-*`; `name`; `src` (frames); `parentid`; `parentname`; `class`; `aaname`; `isleaf`; `tabindex`; `tableCol`; `href`; `src`; `css-selector`. Its volatility filters: an `id`, `parentid` or `aria-labelledby` containing a letter after a digit (`_oj146_smart-filter`, `input-45f6g7h8`) is rejected as auto-generated; a `class` with several tokens is never used at all (take one semantic token, wildcarded); `aaname` is offered only for `a`, `label`, `img`, `input`, `button`, `textarea`, `area`, `select`, `table`, `th`, for a `div`/`span` whose text is 32 characters or shorter, or under such an ancestor. SAP Fiori and Web GUI elements bypass this table and use their own families.

### `uia` — UI Automation element

| Attribute | Meaning | Tier / role |
|---|---|---|
| `automationid` | AutomationId | very reliable |
| `role` | localized control type, lower-case (`button`, `combo box`, `edit`) | very reliable — language-dependent: on a non-English runtime keep it only as captured live |
| `cls`, `name`, `helpText`, `legacyAccHelp`, `legacyAccDescription` | class name, Name, help text | alright |
| `tableCol`, `tableRow`, `rowName`, `colName` | grid position and headers | table |
| `roleint`, `enabled`, `ispwd`, `kbfocus`, `itemstatus`, `itemtype`, `accelkey`, `acskey` | control type id, state, keys | last resort — only to make the selector unique |
| `rtid`, `pid` | runtime id, process | runtime — never |
| `idx` | | position |

UI Automation control type → `role` (English runtime):

| Control type | `role` | Control type | `role` |
|---|---|---|---|
| Button | `button` | Edit | `edit` |
| CheckBox | `check box` | Text | `text` |
| RadioButton | `radio button` | Hyperlink | `hyperlink` |
| ComboBox | `combo box` | Image | `image` |
| List / ListItem | `list` / `list item` | Tree / TreeItem | `tree` / `tree item` |
| Tab / TabItem | `tab` / `tab item` | Menu / MenuBar / MenuItem | `menu` / `menu bar` / `menu item` |
| DataGrid / DataItem | `data grid` / `data item` | Table / Header / HeaderItem | `table` / `header` / `header item` |
| ToolBar / StatusBar / ProgressBar / ScrollBar | `tool bar` / `status bar` / `progress bar` / `scroll bar` | TitleBar / Window / Pane / Group / Document / Custom | `title bar` / `window` / `pane` / `group` / `document` / `custom` |
| Slider / Spinner / SplitButton / Thumb / ToolTip / Separator | `slider` / `spinner` / `split button` / `thumb` / `tool tip` / `separator` | | |

### `ctrl` — Active Accessibility element

| Attribute | Tier / role |
|---|---|
| `automationid`, `role` | very reliable |
| `labeledby`, `name`, `rowName` | alright |
| `aastate`, `virtualname`, `helpText`, `accessibleDescription` | less reliable (`aastate` is state — never on Check targets) |
| `text` | highly unreliable |
| `idx` | position |

### `java` — Java Access Bridge element

| Attribute | Meaning | Tier / role |
|---|---|---|
| `role` | accessible role (`push button`, `text`, `combo box`, `check box`, `radio button`, `toggle button`, `list`, `list item`, `table`, `tree`, `label`, `menu item`, `page tab`, `frame`, `dialog`, `panel`) | very reliable — matched case-insensitively |
| `cls` | simple class name (`JButton`, `BusyComboBox`, `JideChart$1`) | very reliable |
| `accessibleClass`, `hasTableAncestor` | | very reliable |
| `name` | accessible name (caption) | alright |
| `rowName`, `colName`, `tableRow`, `tableCol` | | table |
| `virtualname`, `javastate`, `backgroundColor`, `foregroundColor` | | last resort |
| `idx` | | position |

### `sap` — SAP GUI scripting element

| Attribute | Meaning | Tier / role |
|---|---|---|
| `id` | normalized scripting id: everything after `wnd[n]/` — `usr/ctxtRF02D-KUNNR`, `tbar[1]/btn[8]`, `usr/cntlGRID1/shellcont/shell`. `/app/con[0]/ses[0]/` and the `wnd[n]/` segment are stripped, so a control in a modal dialog has the same `id` as its main-window twin; the window element tells them apart | very reliable — plain, case-sensitive text resolves in one scripting call (`FindById`); a wildcard, a regex/fuzzy matching mode or `casesensitive:id='false'` moves the search onto a per-node tree walk with no node cap and no timeout of its own |
| `type` | SAP component type name (`GuiCTextField`, `GuiButton`, `GuiCtrlGridView`); synthetic cells and nodes report `GuiGridViewCell`, `GuiGridViewRow`, `GuiTreeNode`, `GuiTreeItem` | structure — narrows a walk cheaply |
| `text` | the `Text` property, untrimmed (SAP pads some captions with spaces — match with a trailing `*`); a grid cell reports its cell value | text — purpose-constrained |
| `tooltip` | `Tooltip`, falling back to the accessibility tooltip, then the default quick-info; untrimmed. On input fields the quick-info usually carries the field label | semantic |
| `tableRow` | 0-based **absolute** row of a table control or ALV grid (not visible-relative; addressing may scroll) | table |
| `tableCol` | 0-based column index — **classic `GuiTableControl` only**; on an ALV grid it is legal only as `-1` (all-items element) | table |
| `colName` | ALV grid **technical** column name (`MATNR`), language-stable — **rejected on a classic `GuiTableControl`** | table — ALV cells are `id` of the grid + `tableRow` + `colName` |
| `colTooltip` | column header tooltip, trimmed; on a classic table control this is the header **title** | table — classic cells are `id` of the table + `tableRow` + `colTooltip` (or `tableCol`) |
| `relpath` | tree node path of node **display texts**, root-relative, slash-separated, a literal `/` escaped as `\/` (`Root/Child/Leaf`) — tree nodes only | semantic — the value the Expand Tree activity takes |
| `itemId` | tree item inside a node: an index (`0`…`n`) for list trees, a column name for column trees; requires a tree-node parent | identity — trees only |
| `idx` | | position |

Not matchable on `<sap>`: `name`, `label`, `iconName`, status and scroll attributes — readable through Get Attribute only. The full matchable set is exactly the eleven attributes above plus `idx`. A matching `id` requires the search to start from the right window: modal dialogs are their own `<wnd>` (`cls='#32770'`), and `usr/…` resolves inside whichever window the chain names. Positional ids (`tbar[0]/btn[11]`, `mbar/menu[4]/menu[2]`) shift between screens: toolbar buttons, menu paths and transactions are driven with the SAP activities (Click Toolbar Button, Select Menu Item, Call Transaction), not with selectors on the button. ALV grid ids are unreliable across sessions; the driver itself prefers the grid's technical column names — a grid cell target is `<sap id='<grid id>' tableRow='…' colName='…' />` and stays **medium** until seen live.

### Other tags

| Tag | Attributes | Note |
|---|---|---|
| `wpf` | `type`, `name`, `uid`, `header`, `automationid`, `content`, `text`, `tooltip`, `labeledby`, `groupname`, `row`, `col`, `rowName`, `colName`, `checked`, `isexpanded`, `idx` (and driver internals `command`, `datastr`, `dotnethash`, `persistid`, `band*`, `auto*`) | UiPath normally surfaces WPF through `uia`; translate WPF recordings to `uia` unless the source recorded WPF-only properties (`x:Type`, `Uid`, `Header`, `Content`) |
| `silverlight` | `role`, `name`, `text`, `idx` | Silverlight plug-in content only; a source *engine* named Silverlight is not this |
| `qt` | `name`, `role`, `tooltip`, `accessibleName`, `statusTip`, `text`, `rawtext`, `idx` | |
| `curl` | `cls`, `role`, `name`, `text`, `tableRow`, `tableCol`, `colName`, `idx` | Curl applets |
| `ax` | `role`, `subrole`, `name`, `title`, `identifier`, `filename`, `url`, `help`, `value`, `rowCount`, `columnCount`, `tableRow`, `tableCol`, `rowName`, `colName`, states, `idx` | macOS accessibility |
| `rdp`, `rdpapp` | `<wnd>` attribute set | remote runtime |

## Matching semantics

How the selector engine reads what a translation writes. These are properties of the engine, not style preferences.

**Values match whole.** A value with no wildcard must equal the element's value exactly; there is no implied `*` at either end. `*` matches zero or more characters, `?` exactly one (never zero). **There is no escape character**, so a literal `*` or `?` in a value cannot be expressed — use `matching:<attr>='regex'` for those. Carriage returns and newlines are normalised on both sides before comparison.

**Case.** Attribute *values* are case-sensitive by default, except `app` on every tag, `tag` on `webctrl`, `role` on `java`, and the macOS state attributes. `casesensitive:<attr>='false'` lifts it per attribute. Attribute *names* are case-sensitive and must be spelled exactly as this catalog spells them — `tableRow`, `colName`, `colTooltip`, `rowName`, `labeledby`, `htmlwindowname`, `css-selector`; a misspelled case is a parse error, not a silent miss. Tag names are case-insensitive.

**Matching modes**, set per attribute with `matching:<attr>`:

| Mode | Behaviour |
|---|---|
| (absent) | wildcard matching as above |
| `regex` | ECMAScript, matched against the **whole** value (anchored); an invalid pattern is a parse error |
| `fuzzy` | similarity score; an imperfect match never exceeds 0.999, so only an exact match scores 1.0 |

`fuzzylevel:<attr>` is the **threshold the score must reach**, from `0.0` to `1.0`, defaulting to `1.0`. Two consequences: `fuzzylevel:<attr>='0.0'` always matches on that attribute (which is exactly what UiPath emits when it fuzzifies), and `matching:<attr>='fuzzy'` **without** a `fuzzylevel` is *stricter* than plain equality — never write one without the other.

**`idx` is positional and 1-based**, counted in document order over the elements that already match every other attribute of that tag, within the scope of the preceding tag — not among siblings. It is omitted when the match is unique. UiPath strips `idx` (with `tableRow`, `tableCol` and `css-selector`) when it fuzzifies a selector, so an indexed target stays strict.

**Number attributes** (`idx`, `tableRow`, `tableCol`, `rowCount`, `pid`, the `nav` counts) take a plain integer only: no wildcard, no range, no comparison operator. An empty value on a number attribute means zero, not "any".

**The selector is XML.** Values are single-quoted, `&apos;` `&amp;` `&lt;` escape the characters that need it, and a repeated attribute on one tag rejects the entire selector. An empty value (`attr=''`) is an active criterion matching only an empty value — to carry an attribute without matching on it, prefix it `omit:`. Beyond `omit:`, `matching:`, `fuzzylevel:` and `casesensitive:` there are no other modifiers, and there is no cap on attributes per tag.

**`<nav>`** carries exactly one of `up`, `next`, `prev`, with a count of at least 1, and never comes first in a chain.

## Rules

1. **Tag chain by technology.** Choose the window tag and element tag from § Technology → tag chain according to the technology the source recorded for the control, not according to the application's name. Add intermediate tags only from the control's own ancestry, only when the leaf is not unique without them, and prefer the ancestors closest to the leaf. Never change a tag's type to make attributes fit.
2. **Criteria carry over unchanged.** Translate the source's match criteria to UiPath matching and nothing else — never tighten a `contains` into an exact match and never loosen an exact match into a wildcard:

   | Source criteria | UiPath |
   |---|---|
   | equals | verbatim |
   | starts with | `value*` |
   | ends with | `*value` |
   | contains | `*value*` |
   | regular expression | `matching:<attr>='regex'` with the pattern as the value |
   | case-insensitive | `casesensitive:<attr>='false'` |
   | not equal, does not contain, does not start with, is not empty | no equivalent — drop the attribute and name it in the element description |

   `*` also matches the empty string; an "is not empty" check cannot be expressed.
3. **Keep two or three attributes per tag, from the top tiers.** Take identity first (developer identifier), then semantic (name, label, role), then structure to pin the leaf (`tag`, `cls`). Drop state, runtime and volatile-marked values. When several text-carrying attributes hold the same string, keep only the highest-priority one (`aria-label`, `ctrlname`, `name`, `title`, `aaname`, `text`, `visibleinnertext`, `innertext`, in that order).
4. **Element purpose constrains the target tag.** A target that is read or typed into (Get Text, Type Into, Extract Data) carries no content attribute (`text`, `aaname`, `visibleinnertext`, `innertext`, `value`) — matching the target by the text about to be read or replaced is circular. A Check/Uncheck target carries no state attribute (`checked`, `aastate`). A Select Item target carries no attribute reflecting the current selection. Ancestor tags may carry text: a row or card pinned by its text is different content from the target's.
5. **Inner text is inherited; `aaname` is not.** `innertext` and `visibleinnertext` on a container concatenate the text of every descendant, so a text match on a broad tag also matches the whole ancestor chain, outermost first. On the web `aaname` of a non-form element is only its **own direct text**, so it pins the exact node that carries the caption and is empty on wrappers; on desktop technologies `name`/`aaname` is the accessible name and behaves likewise. Match a control's *own* text exactly and pin the leaf by `tag` (plus `cls` or `isleaf` when needed); wildcard only the volatile part of the text (`aaname='$*%*'`). On a *container* (row, card, list item) a wildcarded `visibleinnertext='*ETH*'` is a reliable pillar and is the preferred replacement for a row index. Text values longer than 512 characters are truncated by the driver with a trailing `*`.
6. **A recorded caption is an anchor, not an attribute of the control.** Sources record the visible label next to a field. When the association is programmatic (a `<label for>` on an input that has an `id`, `aria-labelledby`, `labeledby`, a button or link whose text *is* its name), the caption is part of the control's own accessible name and may go on the target's `aaname`/`name`/`labeledby`. When the association is positional (text to the left or right, a heading above), the caption lives in a separate element — the anchor is that element, matched on `aaname` when the text is its own direct content (the usual case for a `LABEL`, `SPAN` or `DIV` caption), on `visibleinnertext` with the leaf pinned by `tag` when the text sits in nested children; exact, never wildcarded. The target keeps only its non-caption attributes; a target whose only recorded attribute was the caption is tag-only and the anchor identifies it. A control with a positional index cannot be anchored (rule 7).
7. **Position is strict and last.** A source instance or index greater than one becomes `idx` on a strict selector; `idx` is not supported on fuzzy targets, so an indexed target is never anchored. Prefer a text-pinned container or a table header over an index; when an index stays, flag it (the workflow analyzer reports large indexes).
8. **Tables: never a numeric row.** A row found by content becomes a container pinned by text or a row-anchored cell; the column comes from the header caption — `colName` on web (`ui5-colLabel`, `sapweb-colname`, `aw-collabel` for the SAP web families), `colTooltip` on SAP GUI (its `colName` is the technical field name, ALV only; § `sap`); `tableRow`/`tableCol` survive only when the source itself was positional, and stay flagged. SAP GUI rows are 0-based and absolute, so a source's 1-based visible row number is neither.
9. **Window level discriminates, it does not identify.** `title` keeps a stable fragment with wildcards; `url` keeps the host and wildcards the path; before wildcarding, consider the other windows and tabs the automation opens — a wildcard that also matches another open tab is wrong. SAP session windows discriminate by `cls` and title; system and client through the `sap*` session attributes when several systems are in play.
10. **Identifier hygiene.** Purely numeric or hash-like ids (`89763184740`, `css-1wq41pf`, `container-45f6g7h8`) are dropped; partially semantic ids keep the semantic part (`id='*startDate*'`); framework-generated attributes are the last resort even when their value looks semantic.
11. **Write the semantic description for the screen, not for the capture.** Every migrated element carries one, and it is the fallback the runtime resolves with a model against a live screenshot. Name what the element *is* and where it sits: its control type, its own static caption, label or placeholder, the label it belongs to, and its section, dialog, tab or column header. Never name anything the application or a user can change — current field contents, the selected option, a checkbox state, dates, counters, totals, IDs, user names, row values. "The username text box under the Sign in heading" resolves; "the text box containing john_doe" does not. The description is the only text the model receives, so the element's name in the Object Repository does not substitute for it.
12. **Confidence and targeting method.** **high** = a developer identifier is present (automation id, id, name, `aria-label`, `data-*` identifier, SAP scripting id, `sapweb-id`, `ui5-view-local-id`); **medium** = only a label, inner text, title, tooltip, role or class; **low** = only an XPath, outer HTML, a positional path, an image, or no control at all (semantic description only). The tier is read off the control the element *is*: a neighbouring control's identifier raises nothing. Targeting method: a caption anchor exists → fuzzy main selector plus that anchor; no anchor → strict, whatever the tier; positional index → strict with `idx`, never anchored; the semantic (description-based) fallback is always added. A fuzzy selector without an anchor has nothing to disambiguate with and is never shipped.
13. **No selector is a valid outcome.** Image-only, coordinate, pattern and class-only template objects, and terminal screens get a precise semantic description, confidence **low**, and a note that the first live pass must capture them. Inventing attributes for them — or lifting an identifier from a control that merely looks related — is fabrication ([source-migration-guide.md § Composite interactions](source-migration-guide.md)).

## What a translation produces per element

The source guide's row supplies the left side; this guide fixes the right side. Each translated control yields: the strict selector (tag chain), the optional fuzzy selector and anchor, the semantic description (what the control is, from the source's names), the confidence tier, the list of dropped attributes with the reason (state, runtime, volatile, negative criteria, positional, no equivalent), and the flags `positional`, `volatile`, `frame-unresolved`, `offline-unverified`. The execution guide says where these land ([source-migration-guide.md § What the executor records](source-migration-guide.md)).

## Adding a technology or a framework

- A new **source framework** adds `sources/<framework>-selectors-guide.md` with one table per technology it records: `source field (any case) | UiPath tag.attribute | criteria/value transform | confidence | notes`. Every right-hand side is an attribute listed in this catalog; the driver schema is closed except for `webctrl`.
- A new **UiPath technology** (a new driver tag or a new SAP/UI5 attribute family) is added here first, with its tier source (package reference, or *derived*), and only then referenced from a source guide.
