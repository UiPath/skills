# Selector Translation Guide — source locators → UiPath targets

UiPath side of UI target migration, shared by every source framework. A framework pack's selectors guide (`<PACK_DIR>/<framework>/selectors-guide.md`, [SKILL.md § Source Frameworks](../SKILL.md)) says what *its* framework recorded and which UiPath attribute each recorded field becomes; this guide says what UiPath can match on, per technology, and the rules every translation obeys. Vocabulary: UiPath driver's selector schema (tag names, attribute names) and UI Automation package's selector references (reliability tiers). Execution mechanics — Object Repository elements, linking, reporting: [source-migration-guide.md](source-migration-guide.md); no-application shapes: [offline-definition-workarounds-guide.md](offline-definition-workarounds-guide.md).

## Technology → tag chain

UiPath selector = chain of tags: one top-level tag for window or browser tab, then one tag per ancestry level needed to identify the element. Source control's technology decides the tags; a chain never mixes tags of two technologies below the same window unless the technology genuinely changes (browser chrome UI vs page content, Java applet inside browser).

| Source technology | Top-level tag | Element tag | Notes |
|---|---|---|---|
| Browser page (Chrome, Edge, Firefox) | `<html app='chrome.exe' title='…' url='…' />` | `<webctrl … />` | `app` = browser executable; sources rarely record it → Configuration Question (browser choice), default `chrome.exe` |
| SAP web (Fiori/UI5, Web GUI, Web Dynpro, Ariba) | `<html … />` | `<webctrl … />` with `ui5-*`, `sapweb-*`, `aw-*` attributes | Prefer SAP attributes over generic HTML ones on same element |
| SAP GUI for Windows | `<wnd app='saplogon.exe' cls='SAP_FRONTEND_SESSION' title='…' />` | `<sap id='…' />` | Modal dialogs are own windows: `cls='#32770'`, title = dialog caption |
| SAP GUI for Java | `<wnd app='java*.exe' cls='SunAwtFrame' title='…' />` | `<sap id='…' />` | Dialogs `cls='SunAwtDialog'`; custom Java classes surface as `<java>` |
| Windows desktop recorded through UI Automation (WPF, WinForms, Win32, UWP, Electron shells, browser chrome UI) | `<wnd app='<exe>' cls='…' title='…' />` | `<uia … />` | Default for any control recorded with UI Automation properties (control type, name, automation id, class name) |
| Windows desktop recorded through Active Accessibility (MSAA) | `<wnd … />` | `<ctrl … />` | When source recorded MSAA role/name/state, or as alternative framework when UIA does not surface the element |
| Classic Win32 child windows (HWND controls) | `<wnd … />` | nested `<wnd cls='…' ctrlid='…' ctrlname='…' />` | Dialog controls that own a window handle |
| Java Swing/AWT | `<wnd app='java*.exe' cls='SunAwtFrame' title='…' />` | `<java … />` | Java Access Bridge required at run time |
| Qt | `<wnd … />` | `<qt … />` | |
| Remote desktop with the UiPath remote runtime (Citrix, RDP, VMware) | `<rdpapp … />` / `<rdp … />` | native tags of the remote application | `<rdp>` carries the `<wnd>` attribute set |
| macOS | `<wnd app='…' title='…' />` | `<ax … />` | |
| Terminal / mainframe (3270, 5250) | none | none | Not a selector technology: UiPath Terminal activities address the screen by row and column. Source screen map translates to terminal field positions, not selectors |
| Image / pattern / coordinate recognition | window tag | none | No selector. Computer Vision or image target; confidence **low**; live capture owed |
| Relative navigation between tags | | `<nav up='n' />`, `<nav next='n' />`, `<nav prev='n' />` | Anchoring to related element; never `up='0'` |

`<wnd>` needs `app` (executable name); `<html>` needs `app` (browser). No test framework records the executable: take it from the source's application record or the step that launches the application, else a Configuration Question with the technology default.

## Tag attribute catalog

**This section is a catalog — read it by tag.** List its `###` headings; read the sections for the tags § Technology → tag chain gives the source's technologies (plus `webctrl`'s attribute-getter table whenever the web is involved); § Matching semantics and § Rules are read in full.

Attribute names are the driver's; tag schema is closed for every tag except `webctrl` (any HTML attribute) — a translation may not invent an attribute not listed here. Reliability tiers **very reliable**, **alright**, **table**, **last resort** follow the UI Automation package's per-tag references; rows marked *derived* apply the general rule (developer identifier > semantic name > text > structure > state/position) where the package documents nothing. Roles: **identity** (developer identifier), **semantic** (name, label, role), **text** (content — purpose-constrained, § Rules 4–5), **structure** (never alone), **table**, **position** (strict only), **state** (never in a target), **session** (top-level discriminators), **runtime** (readable through Get Attribute, never matched).

### `wnd` — window

| Attribute | Meaning | Tier / role |
|---|---|---|
| `app` | executable name (`saplogon.exe`) | very reliable — mandatory |
| `cls` | window class (`SAP_FRONTEND_SESSION`, `#32770`, `Chrome_WidgetWin_1`) | very reliable |
| `title` | window caption | alright — keep at least part, wildcard volatile part |
| `aaname` | accessible name | alright |
| `ctrlname` | WinForms control name | identity — reliable when present |
| `ctrlid` | Win32 control id | identity for fixed dialogs; positional in dynamic UIs |
| `automationid` | UI Automation id on the window | identity |
| `idx` | position among matches | position — strict only |
| `aastate` | accessibility state | state — never |
| `sapSysSessionId` | server-side SAP session id, carried by the session window **and** by every SAP modal dialog of that session; absent on the SAP Logon pad | session — the one matchable SAP attribute on a window; its value is runtime, so a selector uses it only as "present" (`sapSysSessionId='?*'`), which separates SAP dialogs from other `#32770` windows of `saplogon.exe` |
| `sapSysName`, `sapClient`, `sapUser`, `sapLanguage`, `sapTransaction`, `sapProgram`, `sapScreen`, `sapWindowName` (`wnd[0]`, `wnd[1]`), `sapGuiSessionId` (`/app/con[0]/ses[0]`), `sapSession`, `sapSysNumber`, `sapReadyState` | SAP GUI session context | runtime — readable through Get Attribute, **not matchable** (the selector evaluator rejects them as attributes the window does not have) |
| `pid`, `tid`, `gid`, `appid`, `isremoteapp`, `hwnd` | runtime identities | runtime — never |

### `html` — browser tab

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

### `webctrl` — HTML element (open schema)

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
| `css-selector` | tag-name-only chain from `body` (`body>div>span>a`), no ids or classes | weak; last resort |
| `shadowhostid` | `id` of the shadow host of the element's root; host also gets its own tag in the chain | mandatory, even empty, on every tag whose node lives in a shadow root — without it the matcher never descends into shadow roots |
| frames | one `<webctrl tag='IFRAME' … />` (`FRAME`, `EMBED`) per frame level, carrying `id`, `name`, `src` (never `class`); nested frames give one tag per level | there is **no** `frame` attribute; SAP web frames are the exception and get no frame tag |
| `idx` | 1-based, document order, counted over all same-tag elements **in the subtree of the parent tag's element** that match the tag's other attributes — not siblings | omitted when match is unique |

Driver's own attribute preference when generating a selector, in order (stage one always emitted, later stages added only while they lower the index): `shadowhostid` (shadow DOM), `tag`, `tableRow`, `id`; `type`; `aria-role`; `aria-label`; `aria-labelledby`; Salesforce `sfl-*`; Ariba `aw-*`; Oracle ADF `adf-*`; `name`; `src` (frames); `parentid`; `parentname`; `class`; `aaname`; `isleaf`; `tabindex`; `tableCol`; `href`; `src`; `css-selector`. Volatility filters: an `id`, `parentid` or `aria-labelledby` containing a letter after a digit (`_oj146_smart-filter`, `input-45f6g7h8`) is rejected as auto-generated; a `class` with several tokens is never used at all (take one semantic token, wildcarded); `aaname` is offered only for `a`, `label`, `img`, `input`, `button`, `textarea`, `area`, `select`, `table`, `th`, for a `div`/`span` whose text is 32 characters or shorter, or under such an ancestor — and the offer depends on the activity type as well: a Click default may prefer a positional index over a multi-word caption that a `None` default keeps. SAP Fiori and Web GUI elements bypass this table and use their own families.

### `uia` — UI Automation element

| Attribute | Meaning | Tier / role |
|---|---|---|
| `automationid` | AutomationId | very reliable |
| `role` | language-agnostic control type, lower-case (`button`, `combo box`, `edit`) | very reliable — the role value does not change with the UI language |
| `cls`, `name`, `helpText`, `legacyAccHelp`, `legacyAccDescription` | class name, Name, help text | alright |
| `tableCol`, `tableRow`, `rowName`, `colName` | grid position and headers | table |
| `roleint`, `enabled`, `ispwd`, `kbfocus`, `itemstatus`, `itemtype`, `accelkey`, `acskey` | control type id, state, keys | last resort — only to make the selector unique |
| `rtid`, `pid` | runtime id, process | runtime — never |
| `idx` | | position |

UI Automation control type → `role` (same values across UI languages):

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

Chromium-rendered content reached through UI Automation (an Electron renderer window, browser chrome, a web view without the browser driver) exposes the page's **accessibility tree**, not its DOM: `role` is the control type Chromium derives from the element's implicit or explicit ARIA role, `name` its accessible name (associated label, `aria-label`, own text, placeholder as the last fallback). DOM `class`, `data-*`, `name` and `type` attributes are not accessibility properties and never reach the element; whether `automationid` mirrors the DOM `id` is settled by the live attribute listing (rule 15), never assumed. A locator built on such attributes translates to role plus accessible name or to a no-selector outcome (rule 13). Framework side: the framework pack's selectors guide, section for renderer windows reached through UI Automation.

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
| `id` | normalized scripting id: everything after `wnd[n]/` — `usr/ctxtRF02D-KUNNR`, `tbar[1]/btn[8]`, `usr/cntlGRID1/shellcont/shell`. `/app/con[0]/ses[0]/` and the `wnd[n]/` segment are stripped, so a control in a modal dialog has the same `id` as its main-window twin; the window element tells them apart. `usr/` stays: an id with `wnd[n]/` left on, with `usr/` cut, or reduced to the control's own last segment matches nothing. The driver's default target for any activity type is this `id` alone, strict | very reliable — plain, case-sensitive text resolves in one scripting call (`FindById`); a wildcard, a regex/fuzzy matching mode or `casesensitive:id='false'` moves the search onto a per-node tree walk with no node cap and no timeout of its own (`id='*<prefix><FIELD>' type='Gui…'` is the tail match that finds a field by its technical name) |
| `type` | SAP component type name (`GuiCTextField`, `GuiButton`, `GuiCtrlGridView`); synthetic cells and nodes report `GuiGridViewCell`, `GuiGridViewRow`, `GuiTreeNode`, `GuiTreeItem` | structure — narrows a walk cheaply |
| `text` | the `Text` property, untrimmed (SAP pads some captions with spaces — match with trailing `*`); a grid cell reports its cell value | text — purpose-constrained |
| `tooltip` | `Tooltip`, falling back to accessibility tooltip, then default quick-info; untrimmed. On input fields the quick-info usually carries the field label | semantic |
| `tableRow` | 0-based **absolute** row of a table control or ALV grid (not visible-relative; addressing may scroll) | table |
| `tableCol` | 0-based column index — **classic `GuiTableControl` only**; on an ALV grid legal only as `-1` (all-items element) | table |
| `colName` | ALV grid **technical** column name (`MATNR`), language-stable — **rejected on a classic `GuiTableControl`** | table — ALV cells are `id` of the grid + `tableRow` + `colName` |
| `colTooltip` | column header tooltip, trimmed; on a classic table control this is the header **title** | table — classic cells are `id` of the table + `tableRow` + `colTooltip` (or `tableCol`); the cell's own scripting id (`…/tbl<TABLE>/<prefix><FIELD>[c,r]`) does not match, exact or wildcarded — `[c,r]` becomes `tableCol='c' tableRow='r'`. The driver's default takes `colTooltip`, a caption in the logon language; `tableCol` is the language-independent form |
| `relpath` | tree node path of node **display texts**, root-relative, slash-separated, literal `/` escaped as `\/` (`Root/Child/Leaf`) — tree nodes only | semantic — the value the Expand Tree activity takes |
| `itemId` | tree item inside a node: index (`0`…`n`) for list trees, column name for column trees; requires a tree-node parent | identity — trees only |
| `idx` | | position |

Not matchable on `<sap>`: `name` (the technical field name), `labeledby` (the field's label), `leafid`, `label`, `iconName`, status and scroll attributes — readable through Get Attribute only. A combo box's `items` and `selecteditem` are the entries' captions; no key is exposed, so a source that chose an entry by key needs the caption in the logon language. Full matchable set is exactly the eleven attributes above plus `idx`. A matching `id` requires the search to start from the right window: modal dialogs are their own `<wnd>` (`cls='#32770'`), and `usr/…` resolves inside whichever window the chain names. Positional ids (`tbar[0]/btn[11]`, `mbar/menu[4]/menu[2]`) shift between screens: drive toolbar buttons, menu paths and transactions with the SAP activities (Click Toolbar Button, Select Menu Item, Call Transaction), not with selectors on the button. ALV grid ids are unreliable across sessions; the driver itself prefers the grid's technical column names — a grid cell target is `<sap id='<grid id>' tableRow='…' colName='…' />` and stays **medium** until seen live.

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

How the selector engine reads what a translation writes — properties of the engine, not style preferences.

**Values match whole.** A value with no wildcard must equal the element's value exactly; there is no implied `*` at either end. `*` matches zero or more characters, `?` exactly one (never zero). **There is no escape character**, so a literal `*` or `?` in a value cannot be expressed — use `matching:<attr>='regex'` for those. Carriage returns and newlines are normalised on both sides before comparison.

**Case.** Attribute *values* are case-sensitive by default, except `app` on every tag, `tag` on `webctrl`, `role` on `java`, and the macOS state attributes. `casesensitive:<attr>='false'` lifts it per attribute. Attribute *names* are case-sensitive and must be spelled exactly as this catalog spells them — `tableRow`, `colName`, `colTooltip`, `rowName`, `labeledby`, `htmlwindowname`, `css-selector`; a misspelled case is a parse error, not a silent miss. Tag names are case-insensitive.

**Matching modes**, set per attribute with `matching:<attr>`:

| Mode | Behaviour |
|---|---|
| (absent) | wildcard matching as above |
| `regex` | ECMAScript, matched against the **whole** value (anchored); an invalid pattern is a parse error |
| `fuzzy` | similarity score; an imperfect match never exceeds 0.999, so only an exact match scores 1.0 |

`casesensitive:<attr>='false'` applies in `regex` mode as well. In a pattern `.` does not cross a line break — `[\s\S]` does — while a wildcard `*` crosses line breaks; a multi-line value (a table header, a cell with two lines) needs the former in a regex.

`fuzzylevel:<attr>` is the **threshold the score must reach**, from `0.0` to `1.0`, defaulting to `1.0`. Two consequences: `fuzzylevel:<attr>='0.0'` always matches on that attribute (exactly what UiPath emits when it fuzzifies), and `matching:<attr>='fuzzy'` **without** a `fuzzylevel` is *stricter* than plain equality — never write one without the other.

**`idx` is positional and 1-based**, counted in document order over the elements that already match every other attribute of that tag, within the scope of the preceding tag — not among siblings. It is omitted when the match is unique. UiPath strips `idx` (with `tableRow`, `tableCol` and `css-selector`) when it fuzzifies a selector, so an indexed target stays strict.

**Number attributes** (`idx`, `tableRow`, `tableCol`, `rowCount`, `pid`, the `nav` counts) take a plain integer only: no wildcard, no range, no comparison operator. An empty value on a number attribute means zero, not "any".

**The selector is XML.** Values are single-quoted, `&apos;` `&amp;` `&lt;` escape the characters that need it, and a repeated attribute on one tag rejects the entire selector. An empty value (`attr=''`) is an active criterion matching only an empty value — to carry an attribute without matching on it, prefix it `omit:`. Beyond `omit:`, `matching:`, `fuzzylevel:` and `casesensitive:` the driver accepts no other modifier, and there is no cap on attributes per tag. The UI Automation activities layer adds one of its own on **fuzzy** selectors and anchors: `check:<attr>='<value>'` (in practice `check:text`), a post-match verification that the resolved element's text equals the value. The fuzzy generator emits it on labels, buttons and anchors and strips it for activities whose text changes at run time (Type Into, Get Text). Preserve it when copying a driver-generated selector; never author it by hand, and never on a Type Into target.

**`<nav>`** carries exactly one of `up`, `next`, `prev`, with a count of at least 1, and never comes first in a chain.

## Rules

1. **Tag chain by technology.** Choose the window tag and element tag from § Technology → tag chain according to the technology the source recorded for the control, not according to the application's name, and never by pattern-matching attribute names across technologies. Add intermediate tags only from the control's own ancestry, only when the leaf is not unique without them, and prefer the ancestors closest to the leaf. Never change a tag's type to make attributes fit.
2. **Criteria carry over unchanged.** Translate the source's match criteria to UiPath matching and nothing else — never tighten a `contains` into an exact match and never loosen an exact match into a wildcard:

   | Source criteria | UiPath |
   |---|---|
   | equals | verbatim |
   | starts with | `value*` |
   | ends with | `*value` |
   | contains | `*value*` |
   | regular expression that must match the whole value | `matching:<attr>='regex'` with the pattern as the value |
   | regular expression that searches the text (matches anywhere in it — what most frameworks' "matches" does) | `matching:<attr>='regex'` with `[\s\S]*(?:<pattern>)[\s\S]*` — the engine anchors, so the bare pattern would have to equal the whole value; `^…$` anchors the source wrote stay as written |
   | case-insensitive | `casesensitive:<attr>='false'` (also in regex mode) |
   | equals after whitespace normalisation (the source collapses runs of spaces, turns line breaks into spaces, trims the ends before comparing) | verbatim only on an attribute whose live value holds the text without padding or line breaks; otherwise `matching:<attr>='regex'` with `\s*` at both ends and `\s+` for each inner space — never `*value*`, which turns equals into contains |
   | not equal, does not contain, does not start with, is not empty | no equivalent — drop the attribute and name it in the element description |

   `*` also matches the empty string; an "is not empty" check cannot be expressed.
3. **Keep two or three attributes per tag, from the top tiers.** Take identity first (developer identifier), then semantic (name, label, role), then structure to pin the leaf (`tag`, `cls`). Drop state, runtime and volatile-marked values. When several text-carrying attributes hold the same string, keep only the highest-priority one (`aria-label`, `ctrlname`, `name`, `title`, `aaname`, `text`, `visibleinnertext`, `innertext`, in that order).
4. **Element purpose constrains the target tag.** A target that is read or typed into (Get Text, Type Into, Extract Data) carries no attribute whose value *is* the content about to be read or replaced: `value`, `text`, `visibleinnertext`, `innertext`, and `aaname` **when the driver derived it from the element's content**. `aaname` on a form-ish element that has a programmatic label (`<label for>`, `aria-labelledby`, `title`, `alt`) is the *label* — an identity, and it stays: the driver's own default Type Into target avoids `aaname` (for most inputs it is content) and, on a form with several fields of one widget type, falls back to structural fragments (`id='*input*'`, a label-id fragment) that match every input of that type, so a migrated target keeps `aaname='<label>'` where the label is programmatic: it is unique where the driver's default is not. Live, the test is one read of the attribute list: `aaname` equal to the label text is identity; an element with no label falls back to its value or own text, and then `aaname` is content. Offline, keep `aaname` on a typed-into control only when the source recorded a label for it (the value is then the label), never when the source recorded only its text. A Check/Uncheck target carries no state attribute (`checked`, `aastate`, `aria-checked`, `data-*checked*`). A Select Item target carries no attribute reflecting the current selection (`selecteditem`, `value`). Ancestor tags may carry text: a row or card pinned by its text is different content from the target's.
5. **Inner text is inherited; `aaname` is not.** `innertext` and `visibleinnertext` on a container concatenate the text of every descendant, so a text match on a broad tag also matches the whole ancestor chain, outermost first. On the web `aaname` of a non-form element is only its **own direct text**, so it pins the exact node that carries the caption and is empty on wrappers; on desktop technologies `name`/`aaname` is the accessible name and behaves likewise. Match a control's *own* text exactly and pin the leaf by `tag` (plus `cls` or `isleaf` when needed); wildcard only the volatile part of the text (`aaname='$*%*'`). On a *container* (row, card, list item) a wildcarded `visibleinnertext='*ETH*'` is a reliable pillar and the preferred replacement for a row index. Text values longer than 512 characters are truncated by the driver with a trailing `*`.

   **The mechanical test for `aaname`.** Before writing `aaname` on a `webctrl`, decide which of three cases the node is in — the answer is forced, not a judgement call:

   | Node | Does it carry `aaname`? |
   |---|---|
   | Form-ish tag — `A`, `INPUT`, `BUTTON`, `TEXTAREA`, `SELECT`, `IMG`, `AREA`, `LABEL`, `TH`, `TABLE` | Yes, **synthesised**: the driver builds it from `<label for>`, `title`, `alt`, text or value (§ attribute-getter table). An `INPUT`'s `aaname` is its label text — which is why a labelled field is targetable by its caption while its wrapper is not |
   | Leaf that owns its text — a `DIV`/`SPAN`/`LI` with `isleaf='1'` and its own text node | Yes, an exact, non-inherited pin. Pair it with `isleaf='1'` so the match cannot drift to an ancestor, and with its `tag`: a labelled form control carries its label's text as its own `aaname`, so `aaname` + `isleaf` alone also matches the input a `LABEL` names (a hidden radio beside its caption) |
   | Container — a `DIV`/`SPAN`/`SECTION`/`LI`/`UL`/`TR`… wrapping other elements (`isleaf='0'`) | **No** — the split is near-total, not a tendency: on enterprise SPA pages essentially no visible interactive container carries a non-blank `aaname` (whitespace-only values occur and are not names) while almost every text leaf does. `aaname` written on a wrapper was observed on one of its descendants and belongs on that descendant (rule 14); the wrapper's own identity is `aria-label` or `aria-labelledby` when it has any |

   `aaname` is neither over- nor under-used as a category — it is *node-dependent*. `<webctrl tag='DIV' data-automation-id='promptOption' aaname='My Organizations' />` is correct, because that option label is a leaf owning its text. `<webctrl tag='DIV' aaname='Save' />` for a command button is not: the button is a `BUTTON`, and the `DIV` that wraps it has no name. Neither the caption nor the tag can be chosen without knowing which node is which.
6. **A recorded caption is an anchor, not an attribute of the control.** Sources record the visible label next to a field. When the association is programmatic (a `<label for>` on an input that has an `id`, `aria-labelledby`, `labeledby`, a button or link whose text *is* its name), the caption is part of the control's own accessible name and may go on the target's `aaname`/`name`/`labeledby`. When the association is positional (text to the left or right, a heading above), the caption lives in a separate element — the anchor is that element, matched on `aaname` when the text is its own direct content (the usual case for a `LABEL`, `SPAN` or `DIV` caption), on `visibleinnertext` with the leaf pinned by `tag` when the text sits in nested children; exact, never wildcarded. The target keeps only its non-caption attributes; a target whose only recorded attribute was the caption is tag-only and the anchor identifies it. A control with a positional index cannot be anchored (rule 7).
7. **Position is strict and last.** A source instance or index greater than one becomes `idx` on a strict selector; `idx` is not supported on fuzzy targets, so an indexed target is never anchored. Prefer a text-pinned container or a table header over an index; when an index stays, flag it and carry it as a selector variable bound to an annotated workflow constant (`idx='{{ToolbarCloseIndex}}'`): the default workflow analyzer rejects a literal `idx` above 2 as an Error at build (`UI-REL-001`, while per-file validation passes), and a recorder's index is a per-deployment constant rather than identity, so it belongs in configuration. The element stays strict and positional, its description still says so, and the analyzer still warns about the `idx` attribute — the parametrisation raises no confidence.
8. **Tables: never a numeric row, and never an assumed markup.** A row found by content becomes a row-anchored cell or a container pinned by text; the column comes from the header caption — `colName` on web (`ui5-colLabel`, `sapweb-colname`, `aw-collabel` for the SAP web families), `colTooltip` on SAP GUI (its `colName` is the technical field name, ALV only; § `sap`); `tableRow`/`tableCol` survive only when the source itself was positional, and stay flagged. Whether a web grid exposes the table attributes at all is a property of its markup, not of the application: read one cell's attribute list live before choosing. When they are present, `colName` is the header's *full* text (wildcard the tail: `colName='Status*'`), `rowName` is the row's first cell text, and the row-by-content cell is `<webctrl tag='TD' rowName='<key text>' colName='<caption>*' />`. The trailing wildcard is load-bearing, not tidiness: a sortable header's full text usually carries a screen-reader caption after the visible one (`colName='PlacementSort and filter column'`), so the bare caption matches nothing while `'Placement*'` matches — confirmed on a live grid, both ways round. `rowName` is the row header cell's text as the driver reports it, which concatenates a multi-line header without separators (`Capitaland largest city`): a source key that equals the visible caption is carried as `rowName='<key text>'` when the header is one line, as `rowName='*<key text>*'` when the source matched by containment or the header may carry more than the key; when the key text is not unique in its column, pin the row container by the discriminating value instead. When they are absent, the row is a container pinned by exact text and the cell is its descendant. A source that finds the row as "the row that has a header or cell containing X" (a descendant filter) is finding it by content: X is the row's key — `rowName` on the cell, or the row pinned by `visibleinnertext` (which includes the descendant's text) — never a part to drop. SAP GUI rows are 0-based and absolute, so a source's 1-based visible row number is neither.
9. **Window level discriminates, it does not identify.** `title` keeps a stable fragment with wildcards; `url` keeps the host and wildcards the path; before wildcarding, consider the other windows and tabs the automation opens — a wildcard that also matches another open tab is wrong. A SAP session window is identified by `app` and `cls` alone — its title is the current screen's and changes with every transaction; a SAP modal dialog by `cls='#32770'`, the presence of `sapSysSessionId` (which the SAP Logon pad, another `#32770` window of the same process, lacks) and its caption. The other `sap*` session attributes are readable, not matchable (§ `wnd`).

   **One application, one scope.** The scope selector belongs to the *application*, not to the screen. Every target on the same application carries the identical scope string, authored once and reused verbatim; a migration that derives the scope per screen from that screen's name produces one wildcard per screen and never converges. On a single-page web application this is the difference between one scope and thirty: the page title changes with every task, so title-derived scopes fragment into `'*App*'`, `'*App *'`, `'*App_Common*'`, `'Create Thing - App'` … each a separate object with its own failure mode, while the host never changed.

   | Technology | Scope on | Shape |
   |---|---|---|
   | Web | `url` — host kept, path wildcarded | `<html app='chrome.exe' url='https://host.example.com/*' />` |
   | Web, two tabs of the **same** host open at once | `url` **plus** a title fragment | add `title='*Fragment*'` to the shared url scope |
   | Desktop | `app` + `cls` | `<wnd app='x.exe' cls='…' />` |
   | Modal dialog that is its own window | `app` + `cls` + caption | `<wnd app='x.exe' cls='#32770' title='Open' />` |
   | SAP GUI session / SAP modal dialog | `app` + `cls` / `app` + `cls` + `sapSysSessionId` present + caption | `<wnd app='saplogon.exe' cls='SAP_FRONTEND_SESSION' />` / `<wnd app='saplogon.exe' cls='#32770' sapSysSessionId='?*' title='Information' />` |

   `title` is a discriminator *within* an application, never the application's identity: reach for it only once `url` (web) or `cls` (desktop) has been fixed and two windows still collide. Two applications are two scopes — a tenant and its public careers site are different hosts and get one scope each. **`url` values are case-sensitive** (only `app`, and `tag` on `webctrl`, are not), so `url='*Site*'` and `url='*site*'` are different selectors and at most one of them matches. The driver's own default for a browser tab is `<html app='chrome.exe' title='*<App>*' url='https://<host>/<tenant path>*' />` — host plus the first path segment, title reduced to the application's word; take that shape, and drop `title` when a second tab of the same host is never open.
10. **Identifier hygiene.** Purely numeric or hash-like ids (`89763184740`, `css-1wq41pf`, `container-45f6g7h8`) are dropped; partially semantic ids keep the semantic part (`id='*startDate*'`); framework-generated attributes are the last resort even when their value looks semantic.
11. **Write the semantic description for the screen, not for the capture.** Every migrated element carries one, and it is the fallback the runtime resolves with a model against a live screenshot. Name what the element *is* and where it sits: its control type, its own static caption, label or placeholder, the label it belongs to, and its section, dialog, tab or column header. Never name anything the application or a user can change — current field contents, the selected option, a checkbox state, dates, counters, totals, IDs, user names, row values. "The username text box under the Sign in heading" resolves; "the text box containing john_doe" does not. The description is the only text the model receives, so the element's name in the Object Repository does not substitute for it.
12. **Confidence and targeting method.** **high** = a developer identifier that names the *instance* is present (automation id, a stable id, name, `aria-label`, an instance-level `data-*` identifier, SAP scripting id, `sapweb-id`, `ui5-view-local-id`); **medium** = only a label, inner text, title, tooltip, role or class, or a `data-*` identifier that names a component *type* repeated per instance (rule 14); **low** = only an XPath, outer HTML, a positional path, an image, or no control at all (semantic description only). The tier is read off the control the element *is*: a neighbouring control's identifier raises nothing. Targeting method: a caption anchor exists → fuzzy main selector plus that anchor; no anchor → strict, whatever the tier; positional index → strict with `idx`, never anchored; the semantic (description-based) fallback is always added. A fuzzy selector without an anchor has nothing to disambiguate with and is never shipped. The driver's default resolution returns a strict selector with no anchor for every activity type, acting and observed alike: fuzzy-plus-anchor is the migration's choice under this rule, so a driver default is compared with a derivation for the node and the attributes it picks, not for its search steps.
13. **No selector is a valid outcome.** Image-only, coordinate, pattern and class-only template objects, and terminal screens get a precise semantic description, confidence **low**, and a note that the first live pass must capture them. Inventing attributes for them — or lifting an identifier (`id`, `data-automation-id`, `name`, `aria-label`) from a catalog control that merely looks related because its *name* resembles the element's — is fabrication, not derivation: nothing ties a neighbour's attribute to the element, and a wrong identifier is worse than none because it suppresses the text match and the semantic fallback instead of deferring to them. An element the source never learned (a popup entry, a menu level, an option row, a matched cell) carries only its tag, the matched text and a semantic description; how execution builds such derived elements is [source-migration-guide.md § Composite interactions](source-migration-guide.md). **This extends to the ordinary case**: a control for which the source recorded only a caption, with no developer identifier and no anchorable caption element, is a *no-selector* outcome too. It ships tag-only with the semantic description and `offline-unverified`, not with the caption promoted onto an attribute to make the target look finished. A target that names an attribute the element does not carry is worse than a tag-only target, because the strict step fails outright instead of falling through to the semantic step.

14. **One tag is one node.** Every attribute on a tag must have been observed on *the same element*. A selector is a description of one node, not a summary of a widget. This is the rule most easily broken offline, because a source catalog lists a control as a single row while the live DOM renders it as a nest — an outer container carrying the developer identifier, and an inner leaf carrying the caption and taking the keystrokes. Merging the two produces a selector that looks strong and matches nothing:

    ```
    <webctrl tag='DIV' data-automation-id='responsiveMonikerInput' aaname='Supervisory Organization' />
    ```

    The container does carry that `data-automation-id`, and the field is labelled that way — but the container has no `aaname` at all (its own text is `"Select multiple." 0 items selected`), so the whole selector fails. The element that takes the typing is an `INPUT` several levels down, whose `aaname` *is* the label (the driver resolves `<label for>`) and which carries no `data-automation-id`. Either node is targetable; the merge of the two is not.

    **Decide which node you act on, then take every attribute from that node.** The node you act on is the one that receives the click or the keystrokes — the focusable leaf, not the widget wrapper.

    **An identifier and a caption on one source row are not automatically two nodes.** The split above is the *wrapper* case, and it is the one that bites, but the opposite case is just as common and splitting it is equally wrong: a role id that names a **leaf** role — an option row, an icon action, a page title, a tab, a cell — sits on the *same* node as the caption, and dropping it "because the id belongs to the wrapper" throws away the only attribute that says what the node is, leaving a caption-only target. Which case a row is in follows from the role the id names, and the cast in rule 16 is the list: wrapper roles (the widget container, the popup list, the date widget) split; leaf roles (acting leaf, value display, popup entry, cell) do not. When the source's own recorded tag agrees with the leaf reading — a caption and a role id on a node the recorder read as a `DIV` text leaf — there is nothing to split.

    Provenance and uniqueness are two separate problems, and fixing the first does not fix the second. A widget identifier is usually a **component type**, repeated once per instance on the page, so it cannot tell two instances apart:

    | Shape | Provenance | Unique? |
    |---|---|---|
    | `<webctrl tag='DIV' data-automation-id='monikerInput' aaname='Location' />` | ✗ merged from two nodes | never matches |
    | `<webctrl tag='DIV' data-automation-id='monikerInput' /><webctrl tag='INPUT' />` | ✓ two nodes, two tags | ✗ — matches every instance of the widget; the engine resolves it only by adding `idx`, which rule 7 forbids |
    | `<webctrl tag='INPUT' aaname='Location' />` | ✓ one node | ✓ — the driver synthesises the input's `aaname` from its `<label for>` |

    Order to try, for a labelled field inside a repeated widget — each shape below resolves to exactly one node where the ones above it in the table do not:

    1. **The focusable leaf, named by its own label.** `<webctrl tag='INPUT' aaname='Location' />`, `<webctrl tag='INPUT' type='checkbox' aaname='Include Subordinate Organizations' />`, `<webctrl tag='BUTTON' aaname='OK' />`. On a form-ish tag the driver already resolves `<label for>`, `aria-labelledby`, `title` or `alt` into `aaname` (rule 5) — one tag, no index, and it distinguishes instances because the label does. Reach for this first; it is the shape that makes the widget's repetition irrelevant.
    2. **A per-instance scope, when the leaf has no name of its own** — a div-based combobox, the day and year segments of a segmented date input (only the first segment carries the label), a cell inside a repeated row. Put the node that carries the **instance's** identity in scope and keep the child target local: the form item pinned by its label text (`<webctrl tag='LI' visibleinnertext='Location*' /><webctrl tag='INPUT' />` — starts-with, because the label is the first text inside it), a per-instance id when the framework has one (`<webctrl data-automation-id='responsiveMonikerInput' data-metadata-id='15$4377' /><webctrl tag='INPUT' />`), or the list labelled with the field (`<webctrl data-automation-id='menuList' aria-label='Column' /><webctrl tag='DIV' aaname='Position Status' />`). Never the component-type wrapper shared by every instance: `<webctrl data-automation-id='responsiveMonikerInput' /><webctrl tag='INPUT' />` matched every prompt on the page. The Element Scope activity is the same idea at activity level: attach once to the instance container, and every child activity inside it needs only a locally-unique target ([source-migration-guide.md § Element Scope](source-migration-guide.md)).
    3. **Tag-only plus an anchor on the caption element**, per rule 6, when neither of the above is available. This is the driver's own default for every labelled control, so it is never wrong — only heavier than 1.

    Offline, when the catalog cannot tell you which node owns which attribute, you do not know the node: emit the tag-only target under rule 13 and owe it a live pass. Guessing the nesting is fabrication — and a component-type identifier looks like a strong developer identifier while carrying no instance information at all, so its presence must never raise the confidence tier on its own (rule 12).

    **Where the tag comes from, in order.** An absent `tag` only widens the search; a wrong one eliminates the only correct candidate. So take the tag from the strongest evidence available and never from habit:

    1. **A tag the source read out of markup** — a recorded `tagname`, an `innerhtml` fragment beginning `<button`. This is an observation of the node the recorder attached to, and it outranks everything below.
    2. **The node's role, when a known role identifier names it.** A component framework's `data-*` role ids have fixed node types (an icon-action `DIV`, a text-area field, a page-title `SPAN`, an option row `DIV`). Once one instance has been seen — live, or in the framework's own documentation — that role's tag is known for every instance of it, and it outranks the control type.
    3. **The tag the control type implies** — a command button is a `BUTTON`, a text field an `INPUT`, a link an `A`. This is the weakest of the three, because a source's control *type* is its own abstraction over the widget, not a reading of the DOM: component frameworks render buttons as `DIV`s, "text boxes" as `TEXTAREA`s and page titles as `SPAN`s, and a recorder that classified the widget will still have recorded the real tag.
    4. **Omit `tag`** when none of the above applies.

    **`DIV` is never a *default* — but a recorded `DIV` is evidence.** Writing `tag='DIV'` because the node "looks like a container" is the same fabrication as guessing an identifier, and `tag='BUTTON'` on a control the source recorded as a `DIV` is the same mistake in the other direction: both replace an observation with a habit. When 1 and 3 disagree, 1 is right, and the disagreement is worth counting across the export before deriving anything: a source whose control types and recorded tags disagree for a large share of its controls is telling you its type vocabulary is a classification of widgets, not a reading of the DOM, and that every tag derived from a type alone is a guess.

15. **Verify the node with the driver, not by eye.** The UI Automation package's live selector tools settle what no catalog can; their syntax is the package's own and is routed from the UIA package guide (`{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/ui-automation-guide.md` § Documentation), never copied into this skill. Four capabilities, named here by what they settle: the **driver default** — the selector the driver itself generates for a given node and activity type — is the strongest evidence for a family's shape, and the thing every offline derivation rule is compared against on one instance before it is applied to the family; the **attribute listing** prints exactly the attributes the driver exposes for one element; the **selector evaluator** (one ref per tag, ancestors first) reports whether the selector matches that element and every other node it matches, and rejects an attribute the node does not carry (*the attribute 'aaname' does not exist on this element*); a **snapshot reload** re-seeds an earlier capture so the evaluator can run against a page that is no longer open. An attribute absent from the listing does not exist for matching, whatever the accessibility tree's display name suggests: a tree that renders a node as `DropDown "Search"` is showing a *computed* name (its `aria-label`), and the node may expose no `aaname` at all. Never translate a tree's display label into an attribute value — read the attribute list. Collisions hide: a selector unique among visible elements can still match an invisible twin (a second `Close` button in a collapsed menu), which is why the evaluator, not the eye, decides uniqueness.

16. **A web widget is a nest with fixed roles, and each role is targeted by a different pattern step.** Component frameworks render one *field* as several nodes, and every enterprise SPA seen so far has the same cast:

    | Role | What it is | Identity it exposes | Which step uses it |
    |---|---|---|---|
    | wrapper | outermost `DIV` of the widget, carrying the component-type id (`data-automation-id='responsiveMonikerInput'`, `'selectWidget'`, `'dateTimeWidget'`) and sometimes a per-instance id | type id (repeated per instance), instance id when present, inner text (volatile: it contains the current value) | scope only, and only with an instance id |
    | label | `LABEL for=…` or a caption leaf beside the widget | its own text as `aaname` | anchor, or the text that pins the form item |
    | form item | the `LI`/`DIV` that holds label and widget | inner text starting with the label | scope for children with no name of their own (rule 14 step 2) |
    | acting leaf | the `INPUT`/`TEXTAREA`/`BUTTON`/combobox `DIV` that takes the keystrokes or the click | `aaname` = label on form-ish tags; `aria-role`/`aria-labelledby` on a div-based control; no `aaname` on icon buttons (`aria-label` instead) | Type Into, Click, Check |
    | value display | the chip, pill or selected-option text that shows what the field now holds (`selectedItem` + `promptOption`, `selectSelectedOption`, a hidden "current value is …" leaf) | `aria-label`/`aaname` = the value | the **verify** of a pick, scoped to the field |
    | popup list | the suggestion or option list the widget opens (`activeListContainer`, `menuList`), usually **labelled with the field's name** (`aria-label='Position Status, Options Expanded'`, `'Column'`) | `aria-label` = field name; `aria-role` menu/listbox | scope for the entry |
    | popup entry | one option: a container (`menuItem`, `aria-role='option'`, `aria-label` = option) around a text leaf (`promptOption`, `aaname` = option) | the option text | the **pick** click |

    Three traps follow from the cast. **The value display and the popup entry often share a component-type id and the same text** (`promptOption` names both the selected chip and every list entry — and the two can even differ only by tag, the chip a `P` and the list row a `DIV`, which is no help offline): a verify on the bare text leaf passes while the list is still open, before anything was accepted, so the verify target is the value display *scoped to the field*, and the pick target is the entry *scoped to the popup labelled with the field* — `<webctrl tag='LI' visibleinnertext='Location*' /><webctrl data-automation-id='selectedItem' aria-label='{0}*' />` against `<webctrl data-automation-id='activeListContainer' aria-label='Location*' /><webctrl data-automation-id='promptOption' aaname='{0}' />`. **The wrapper's inner text is the field's current value**, so a wrapper pinned by `visibleinnertext` (which the driver's default for the wrapper does) is volatile and never survives a data change. Whether a custom list exposes `items` is a property of the widget and its version — one exposes only `selecteditem`, another lists every caption — so probe the control's `items` live (the package's element-interaction commands) before choosing Select Item over open-and-click ([source-migration-guide.md § Composite interactions](source-migration-guide.md)). Segmented inputs (date month/day/year) are three acting leaves under one form item; only the first carries the field label. **A popup list is not always a flat list of values**: the same widget may open a *hierarchy* whose first level is categories that drill down, so the entries on screen before anything is typed are not the values the step picks from — the leaf values appear only once the typed text filters, which is why the pattern types first and picks second, and why a pick that "found" an entry without typing has probably picked a category.

    **A value display may render the value inside a sentence** rather than as the bare value — a hidden read-back leaf whose text reads `current value is <the value>`, for the benefit of screen readers. Read one before choosing the compare: a verify written as equality against such a leaf can never pass, and the correct check is `contains` on the value.

## Checking a definition

Most of these rules are decidable from a definition file alone; the rest need one live command. The list exists so an executor can read a batch of definitions back — by hand, or with a throwaway script written for the run when there are hundreds; the skill deliberately ships no checker, because a passing structural check proves shape, not that anything matches the screen, and a maintained checker's rule set drifts from this guide.

A throwaway checker has to encode each rule's **scope**, or it reports this guide's own prescribed shapes as violations and the executor "fixes" correct selectors. The two that bite: the content-attribute ban is on the **acting leaf** — an ancestor that scopes by a stable field label or row key is the prescribed shape (rule 4, last sentence) — and the `DIV` ban is on an **assumed** tag, not on one the source recorded or a known node role vouches for (rule 14). A finding count that jumps into the hundreds is the checker being wrong, not the batch.

| Check | Decide by | Rule |
|---|---|---|
| Content attribute on a Type Into / Get Text target — `value`, `text`, `visibleinnertext`, `innertext`; `aaname` unless the source recorded a label for that control | `.xaml.metadata` `ActivityType` + the tag's attributes | 4 |
| State attribute on a Check target; selection attribute on a Select Item target | same | 4 |
| `aaname` on a container tag (`DIV`, `SPAN`, `LI`, `UL`, `TR`, `SECTION`, …) with no `isleaf='1'` | attributes | 5, 14 |
| A caption (`aaname`, `visibleinnertext`, `aria-label`) is the tag's only identifier and there is no anchor | attributes + `Anchors` | 6 |
| A `data-*` type identifier is the only discriminator and the selector carries `idx` | attributes | 7, 14 |
| `tag='DIV'` that no source recording and no known role vouches for, on a control the source typed as a button, input, checkbox or link — and the mirror case, a type-implied `tag` that contradicts the tag the source recorded | attributes + source control type + the recorded tag | 14 |
| A caption-only target on a control whose source row also carried a role identifier (the id was dropped as a wrapper's when the role is a leaf's) | attributes + the source row's identifiers | 14 |
| `SearchSteps` has `FuzzySelector` and `Anchors` is empty; or `Anchors` is non-empty and `SearchSteps` lacks `FuzzySelector`; an anchor carries a `ScopeSelectorArgument` | definition | 12, offline guide |
| `matching:<a>='fuzzy'` without `fuzzylevel:<a>` | attributes | § Matching semantics |
| A `matching:<a>='regex'` pattern carried from a source regex that searched, without the `[\s\S]*…[\s\S]*` wrap; an exact caption the source compared whitespace-normalised, written verbatim on `aaname` | attributes + the source criterion + one live attribute listing | 2 |
| More than one distinct `ScopeSelectorArgument` per host across the project; `url` values differing only by case; a web scope with `title` and no `url` | all definitions | 9 |
| `colName` written as the bare caption on a grid whose headers carry hidden suffixes | live attribute listing on one cell | 8 |
| Any attribute the node does not expose | live selector evaluator (rejects the selector outright) | 15 |
| Uniqueness, including invisible twins | live selector evaluator | 15 |
| The shape the driver would have chosen | live driver default on one instance per family | 15 |

## What a translation produces per element

Source guide's row supplies the left side; this guide fixes the right side. Each translated control yields: strict selector (tag chain), optional fuzzy selector and anchor, semantic description (what the control is, from the source's names), confidence tier, list of dropped attributes with reason (state, runtime, volatile, negative criteria, positional, no equivalent), and flags `positional`, `volatile`, `frame-unresolved`, `offline-unverified`. Where these land: [source-migration-guide.md § What the executor records](source-migration-guide.md).

## Adding a technology or a framework

- New **source framework**: add `<framework>/selectors-guide.md` to the framework migration pack ([SKILL.md § Source Frameworks](../SKILL.md)) with one table per technology it records: `source field (any case) | UiPath tag.attribute | criteria/value transform | confidence | notes`. Every right-hand side is an attribute listed in this catalog; driver schema is closed except for `webctrl`.
- New **UiPath technology** (new driver tag or new SAP/UI5 attribute family): add here first, with its tier source (package reference, or *derived*), then reference it from a source guide.
