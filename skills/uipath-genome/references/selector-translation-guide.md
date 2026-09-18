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
| last resort | `action`, `alt`, `href`, `src`, `tabindex`, `placeholder`, `title`, `uipath-html-title`, `css-selector`, `class`, `parentclass`, `aria-pressed` |
| last resort — framework-generated | `ng-reflect-*`, `ng-version`, `_ngcontent-*`, `_nghost-*`, `data-reactid`, `__reactProps$*`, `v-*`, `data-v-*` |
| SAP Fiori / UI5 | very reliable `ui5-label`, `ui5-tooltip`, `ui5-role`, `ui5-type`, `ui5-view-local-id`; alright `ui5-class`; tables `ui5-tableCol`, `ui5-tableRow`, `ui5-colLabel`, `ui5-isEmpty`; trees `ui5-path` |
| SAP Web GUI | very reliable `sapweb-id` (scripting id), `sapweb-type`; alright `sapweb-lsclass`, `sapweb-text`, `sapweb-itemid`; tables `sapweb-tablerow`, `sapweb-tablecol`, `sapweb-colname`, `sapweb-coltooltip`; trees `sapweb-path`; avoid `sapweb-lsid` |
| SAP Ariba | very reliable `aw-name`, `aw-label`, `aw-type`; tables `aw-tablerow`, `aw-tabledetailrow`, `aw-tablerowtype`, `aw-tablecol`, `aw-collabel`; avoid `id` (session hash) |

Hard rules for `webctrl`: a tag whose node sits inside a shadow DOM must carry `shadowhostid` (even empty); `frame`/`iframe` tags are never removed; `class` keeps only the semantic core (`class='*search-input*'`), never utility tokens or build hashes; ids with three or more dot-separated structural segments are wildcarded to the last semantic segments; hash-suffixed custom tag names are wildcarded (`tag='MACROPONENT-*'`); a `DIV`/`SPAN` without a semantic attribute is not a target on its own.

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
| `id` | scripting id relative to the session window — `usr/ctxtRF02D-KUNNR`, `tbar[1]/btn[8]`, `usr/cntlGRID1/shellcont/shell`; the `wnd[n]/` prefix is never part of it (the window is the `<wnd>`) | very reliable — *derived*; wildcards work inside (`id='*ctxtRF02D-KUNNR'`) when the subscreen path is unknown |
| `type` | GUI component type (`GuiCTextField`, `GuiButton`) | structure — *derived* |
| `text`, `tooltip` | field text, tooltip (the field label in SAP) | semantic/text — *derived*; `tooltip` is the label, `text` is content |
| `tableRow`, `tableCol`, `colName`, `colTooltip` | table cell position and header | table — prefer `colName`/`colTooltip` over numbers |
| `relpath` | tree node path (`Root/Child/Leaf`) | semantic — trees |
| `itemId` | tree/list item id | identity — *derived* |
| `idx` | | position |

Positional ids (`tbar[0]/btn[11]`, `mbar/menu[4]/menu[2]`) shift between screens: toolbar buttons, menu paths and transactions are driven with the SAP activities (Click Toolbar Button, Select Menu Item, Call Transaction), not with selectors on the button.

### Other tags

| Tag | Attributes | Note |
|---|---|---|
| `wpf` | `type`, `name`, `uid`, `header`, `automationid`, `content`, `text`, `tooltip`, `labeledby`, `groupname`, `row`, `col`, `rowName`, `colName`, `checked`, `isexpanded`, `idx` (and driver internals `command`, `datastr`, `dotnethash`, `persistid`, `band*`, `auto*`) | UiPath normally surfaces WPF through `uia`; translate WPF recordings to `uia` unless the source recorded WPF-only properties (`x:Type`, `Uid`, `Header`, `Content`) |
| `silverlight` | `role`, `name`, `text`, `idx` | Silverlight plug-in content only; a source *engine* named Silverlight is not this |
| `qt` | `name`, `role`, `tooltip`, `accessibleName`, `statusTip`, `text`, `rawtext`, `idx` | |
| `curl` | `cls`, `role`, `name`, `text`, `tableRow`, `tableCol`, `colName`, `idx` | Curl applets |
| `ax` | `role`, `subrole`, `name`, `title`, `identifier`, `filename`, `url`, `help`, `value`, `rowCount`, `columnCount`, `tableRow`, `tableCol`, `rowName`, `colName`, states, `idx` | macOS accessibility |
| `rdp`, `rdpapp` | `<wnd>` attribute set | remote runtime |

Matching modifiers on any string attribute: `*` (0+ characters), `?` (exactly one), `matching:<attr>='regex'`, `casesensitive:<attr>='false'`, `matching:<attr>='fuzzy'` + `fuzzylevel:<attr>` (fuzzy targets only).

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
5. **Inner text is inherited.** `innertext`, `visibleinnertext`, `aaname` on a container concatenate the text of every descendant, so a text match on a broad tag also matches the whole ancestor chain, outermost first. Match a control's *own* text exactly and pin the leaf by `tag` (plus `cls` when needed); wildcard only the volatile part of the text (`aaname='$*%*'`). On a *container* (row, card, list item) a wildcarded text (`visibleinnertext='*ETH*'`) is a reliable pillar and is the preferred replacement for a row index.
6. **A recorded caption is an anchor, not an attribute of the control.** Sources record the visible label next to a field. When the association is programmatic (a `label for`, `aria-labelledby`, `labeledby`, an accessible name that *is* the caption), the caption is the control's accessible name and may go on the target's `aaname`/`name`/`labeledby`. When the association is positional (text to the left or right, a heading above), the caption element is a bare text node with no accessible name — the anchor matches its inner text exactly, never wildcarded, and the target keeps only its non-caption attributes; a target whose only recorded attribute was the caption is tag-only and the anchor identifies it. A control with a positional index cannot be anchored (rule 7).
7. **Position is strict and last.** A source instance or index greater than one becomes `idx` on a strict selector; `idx` is not supported on fuzzy targets, so an indexed target is never anchored. Prefer a text-pinned container or a table header over an index; when an index stays, flag it (the workflow analyzer reports large indexes).
8. **Tables: never a numeric row.** A row found by content becomes a container pinned by text or a row-anchored cell; the column becomes `colName` (`colTooltip`, `ui5-colLabel`, `sapweb-colname`, `aw-collabel` per technology) from the header caption; `tableRow`/`tableCol` survive only when the source itself was positional, and stay flagged.
9. **Window level discriminates, it does not identify.** `title` keeps a stable fragment with wildcards; `url` keeps the host and wildcards the path; before wildcarding, consider the other windows and tabs the automation opens — a wildcard that also matches another open tab is wrong. SAP session windows discriminate by `cls` and title; system and client through the `sap*` session attributes when several systems are in play.
10. **Identifier hygiene.** Purely numeric or hash-like ids (`89763184740`, `css-1wq41pf`, `container-45f6g7h8`) are dropped; partially semantic ids keep the semantic part (`id='*startDate*'`); framework-generated attributes are the last resort even when their value looks semantic.
11. **Confidence and targeting method.** **high** = a developer identifier is present (automation id, id, name, `aria-label`, `data-*` identifier, SAP scripting id, `sapweb-id`, `ui5-view-local-id`); **medium** = only a label, inner text, title, tooltip, role or class; **low** = only an XPath, outer HTML, a positional path, an image, or no control at all (semantic description only). The tier is read off the control the element *is*: a neighbouring control's identifier raises nothing. Targeting method: a caption anchor exists → fuzzy main selector plus that anchor; no anchor → strict, whatever the tier; positional index → strict with `idx`, never anchored; the semantic (description-based) fallback is always added. A fuzzy selector without an anchor has nothing to disambiguate with and is never shipped.
12. **No selector is a valid outcome.** Image-only, coordinate, pattern and class-only template objects, and terminal screens get a precise semantic description, confidence **low**, and a note that the first live pass must capture them. Inventing attributes for them — or lifting an identifier from a control that merely looks related — is fabrication ([source-migration-guide.md § Composite interactions](source-migration-guide.md)).

## What a translation produces per element

The source guide's row supplies the left side; this guide fixes the right side. Each translated control yields: the strict selector (tag chain), the optional fuzzy selector and anchor, the semantic description (what the control is, from the source's names), the confidence tier, the list of dropped attributes with the reason (state, runtime, volatile, negative criteria, positional, no equivalent), and the flags `positional`, `volatile`, `frame-unresolved`, `offline-unverified`. The execution guide says where these land ([source-migration-guide.md § What the executor records](source-migration-guide.md)).

## Adding a technology or a framework

- A new **source framework** adds `sources/<framework>-selectors-guide.md` with one table per technology it records: `source field (any case) | UiPath tag.attribute | criteria/value transform | confidence | notes`. Every right-hand side is an attribute listed in this catalog; the driver schema is closed except for `webctrl`.
- A new **UiPath technology** (a new driver tag or a new SAP/UI5 attribute family) is added here first, with its tier source (package reference, or *derived*), and only then referenced from a source guide.
