# Worksoft Certify Selectors Guide — locator formats and attribute translation

Companion to [worksoft-certify-source-guide.md § UI Target Locators](worksoft-certify-source-guide.md): how each Certify interface stores a control's recognition data and which UiPath attribute each recorded field becomes. The UiPath vocabulary, reliability tiers, criteria mapping, anchor policy and confidence tiers are in [selector-translation-guide.md](../selector-translation-guide.md) and are not repeated here — read it first. Observations below come from twenty-one production exports (Workday, SAP GUI, SAP Fiori/Web GUI, Coupa, NetSuite, Jira, LabVantage LIMS, ENOVIA PLM, Kinaxis, WinSCP, Windows dialogs).

The recognition data is `MapObjects.json` → windows (`ObjectIdParmValues[].CertifyValue`) and `ChildTrackObjects[].ObjectIdParmValues[].CertifyValue`; one locator per object (a handful have none). The `targets` command parses every format below into one normalized shape (`technology`, `class`, `instance`, `findby[]`, `parentpath[]`, `anchor`, `volatile[]`) — work from `certify-targets.json`, never from the raw XML.

## Locator formats

The **shape of the value**, not the interface library of the application, tells the technology — one application routinely mixes formats (a web app with Windows file dialogs, SAP GUI next to Fiori).

| # | Shape | Certify interface | `technology` | UiPath chain |
|---|---|---|---|---|
| 1 | `<version>3.0</version><frame>…</frame><tagname>…</tagname><instance>n</instance><findby><n>attr</n><v criteria="…">value</v>…</findby>` + optional `<anchor>…</anchor>`, `<RAFAUM>attr,attr</RAFAUM>` | Web (HTML, SAP web, Salesforce Lightning, any browser page) | `web` | `<html>` + `<webctrl>` |
| 2 | `v1.0IC!~TYPE=OBJECT!~CLASS=GuiButton!~SAPNAME=btn[7]!~[ID=wnd[0]/…!~][COORDINATES~Row=…~Column=…~Length=…~Height=…!~]PARENT~TYPE=…~CLASS=…~SAPNAME=…`; older `v8.x!~OBJECT!~GuiButton~wnd[0]/tbar[0]/btn[11]!~PARENT~GuiToolbar~…` and `v2.x!~BODY!~GuiMainWindow~wnd[0]!~Text=*~Wildcard` | SAP (GUI scripting) | `sapgui` | `<wnd>` + `<sap>` |
| 3 | `<certifyobject interface="Silverlight" frameworkid="Win32|WPF|DirectUI|Chrome|GenericApplicationSupport|ImageObjects|" windowflag="Yes|No" certifyclass="…"><findby instance="n"><n>controltype</n>…</findby>` with nested `<parentpath>` (ancestor `certifyobject`s) and `<anchor>` | "Silverlight" — Certify's UI Automation desktop engine, **not** the Silverlight plug-in | `uia` | `<wnd>` + `<uia>` |
| 4 | `<certifyobject interface="UIA" technology="uia" certifyclass="…" instance="n" iswindow="false"><properties><property name="NativeType|NetName|AutomationId|ClassName" criterion="…" value="…" ignorecase="true" /></properties><parentpath>…</parentpath>` | UIA | `uia` | `<wnd>` + `<uia>` |
| 5 | `<object platform="Java" [type="window"]><parent>…</parent><learnname>…</learnname><physicalname id="n">…</physicalname><path id="n">wNPP1B1</path><logicalname>…</logicalname><certifyclass>javaButton</certifyclass><class>javax.swing.JButton</class><caption>…</caption></object>` | Java | `java` | `<wnd>` + `<java>` |
| 6 | `GuiCTextField.(GuiCTextField)`, `Dynamic`, `Dynamic_DataGrid`, `Scripting.(Scripting)`, or format 1 with `<instance>0</instance>` and no `<findby>` | any — class-only **template objects** whose identity Certify sets at run time (`Set Attributes`) or takes from step parameters | `none` | no selector: semantic description, **low**, live capture |
| 7 | `Excel_Automation_Object`, `Word_…`, `Outlook_…`, `PowerPoint_…` | Office | `office` | not a UI target — the steps are Excel/Word/Outlook activities; record under Component Detection, not in the Object Repository |
| 8 | format 3 with `frameworkid="ImageObjects"` and `ImageObjectAttributeString`, or `frameworkid="GenericApplicationSupport"` with `patternname` | image / pattern recognition | `image` | no selector — Computer Vision or image target, **low** |

Exports whose `InterfaceLibraries.json` lists `Mainframe` carried no map objects for it; terminal steps address the screen by row and column and are not selector targets. `Utilities`, `Postman`, `System` are engine libraries, never targets.

### Format-wide conventions

- Attribute names occur in any case (`normalizedinnertext`, `NormalizedInnerText`, `INNERTEXT`); compare case-insensitively. Criteria too (`isequalto`, `IsEqualTo`).
- Criteria observed: `isequalto`, `contains`, `startswith`, `endswith`, `isnotempty`, `doesnotcontain`, `doesnotstartwith`, `isnotequalto`. The last four have no UiPath equivalent — drop the attribute and say so (translation guide rule 2).
- Values in formats 3 and 4 are XML-name encoded: `_x0020_` space, `_x0023_` `#`, `_x002B_` `+`, `_x003A_` `:`, `_x0021_` `!`, `_x0028_`/`_x0029_` parentheses, `_x0031_` a leading digit. Decode before matching (`Internet_x0020_Properties` → `Internet Properties`, `_x0023_32770` → `#32770`).
- `DynamicValue` in formats 3 and 4 marks a property Certify found volatile at learn time (`automationid`, `helptext`, `name`, `text`). Drop the attribute; the `targets` output lists such names under `volatile`.
- `<instance>n</instance>` (format 1) and `findby instance="n"` (format 3) / `instance="n"` (format 4) count matches of the *same* findby set; `n > 1` → `idx`. Format 5 has no instance — its `path` is positional.
- `<anchor>` (formats 1 and 3) is a second object Certify used to disambiguate the first — a UiPath anchor candidate in its own right, translated with the same tables.
- `<RAFAUM>` (format 1) lists the attribute names of the findby; it carries no extra information.
- Certify never records the executable in a locator. `<html app>` comes from the process's `Browser.Load Browser` step, whose `Browser` parameter is `Chrome` → `chrome.exe`, `Edge` → `msedge.exe`, `Internet Explorer` → `iexplore.exe` (Configuration Question with that default; no Load Browser step → default Chrome). `<wnd app>` is `saplogon.exe` for windows reached through `Window.Launch SAP`, `java*.exe` for Java objects, and otherwise the executable behind `Applications[].Name` — a Configuration Question when the export does not say.
- `Browser.Load XF Definitions` names the web framework definition set Certify learned with (`SAP UI5 Definitions`, `Workday Definitions`, `LIMS Definitions`, `<Auto-Detect>`); it confirms which attribute family (`ui5-*`, `data-automation-id`) the web controls of that process carry.

## Web interface → `html` + `webctrl`

Window locators (`title`, `caption`, `url`, occasionally `sapprogram`) describe the browser tab; control locators carry `<frame>`, `<tagname>`, `<instance>` and the findby.

| Certify (any case) | UiPath | Confidence | Notes |
|---|---|---|---|
| window `title` / `caption` | `<html title='…' />` with the criteria's wildcards | — | `caption` is the browser window caption, `title` the document title; the common window's caption is rewritten at run time by `Page.Set Attributes` (`Workday_Common` → `Workday`) |
| window `url` | `<html url='…' />` | — | `contains` → `*value*`; `isnotempty` → drop |
| `frame` = `body` / `Body` | none | — | top document |
| `frame` = index path (`0`, `0.2`, `do0.0`, `dodo1`) | one `<webctrl tag='IFRAME' id='…' name='…' src='…' />` ancestor per level (`do…` segments are nested documents) | — | UiPath emits one frame tag per level carrying `id`/`name`/`src`, never `class`; Certify recorded only the position, so the frame attributes must be captured live — flag `frame-unresolved`. SAP web frames are the exception: no frame tag |
| `tagname` | `tag` | — | upper-case; matched case-insensitively; `*`-suffixed hash tag names wildcarded |
| `instance` > 1 | `idx` | — | strict, never anchored; Certify counts within its findby set, UiPath counts same-tag matches in document order under the parent tag's element — the number carries over only as a hint to re-derive live |
| `data-automation-id`, `data-testid`, `data-*` | same attribute | high | author-controlled identifiers (Workday's `data-automation-id`) |
| `id`, `name`, `aria-label`, `type`, `href`, `alt`, `placeholder`, `src`, `operationid`, `aria-haspopup` | same attribute | high (`id`, `name`, `aria-label`) / last resort (others) | an `id` with a letter after a digit (`input-45f6g7h8`, `wd-FieldSet-56$1234`) is auto-generated by the driver's own rule — wildcard the semantic part or drop; `href` and `src` are volatile URLs — wildcard the host |
| `title` (element attribute: `Edit Company`) | `uipath-html-title` | last resort | `title` on `webctrl` is the **document** title, not the element's |
| `role` | `aria-role` | high | `role` on `webctrl` is a constant — never emit it |
| `classname`, `xclassname` | `class` | medium | one semantic token only, wildcarded both sides — a multi-token class value is never usable; `xclassname` (`Dropdown`, `Listbox`, `Element`) is Certify's own classification, not a DOM class — drop |
| `parentelement.<attr>`, `parentelement.parentelement.<attr>`, `parentelement.tagname` | a preceding `<webctrl>` tag carrying that attribute | as the attribute | one ancestor level per `parentelement.`; `parentid`/`parentclass` on the leaf are the *nearest* ancestor's values, not the direct parent's |
| `innertext`, `normalizedinnertext`, `text`, `normalizedtext`, `alltext`, `normalizedalltext`, `outertext`, `normalizedoutertext` | `visibleinnertext` (or `aaname` when the text is the element's own direct content) | medium | never the primary identifier of an input; `visibleinnertext` is inherited by every ancestor — exact match, leaf pinned by `tag` (+`class` or `isleaf`); `aaname` on a `div`/`span`/`li` is only its own direct text and is not inherited; Certify's `normalized*` variants collapse whitespace, UiPath does not — match the visible spelling; on a container a wildcarded text is the row/card pillar |
| `label` | anchor — `aaname` of the caption element; on an `INPUT`/`TEXTAREA`/`SELECT` that has an `id` and a `<label for>`, the target's own `aaname` also equals it | medium | Certify's `label` is the associated caption; a control with both `label` and a text anchor recorded takes `label` |
| `lefttextanchor`, `righttextanchor` | anchor — `aaname` of the caption element when its text is direct content (a bare `div`/`span`/`label`), `visibleinnertext` + `tag` when nested; exact | medium | positional text next to the control; skip numeric or one-character captions |
| `isdisplayed`, `isvisible`, `ishidden`, `inmodal`, `controltype`, `checked`, `disabled`, `value` | none | — | state and Certify classifications; `value` is content (purpose rule) |
| `innerhtml`, `outerhtml` | none | — | `innerhtml startswith <button` means the real control is a child `BUTTON`; a class or id fragment inside `outerhtml` may be recovered into `class`/`id`; otherwise semantic text only |
| `xpath` | none | low | positional path; description only |
| `sapapplicationtype` (`UI5`, `GUI`, `TR`) | selects the SAP attribute family: `UI5` → `ui5-*`, `GUI`/`TR` → `sapweb-*` | — | absent → decide by `sapclass` (`sap.m.*` = UI5, `UCF_*` = Web GUI) |
| `sapclass` | `ui5-class` (UI5) / `sapweb-lsclass` (Web GUI) | medium | `sap.m.Button`, `sap.ui.comp.smarttable.SmartTable` / `UCF_InputField`, `UCF_Button` |
| `sapsid` | `sapweb-id` | high | scripting id fragment (`ctxtBKPF-BUKRS`, `wnd[0]/sbar_msg`); Certify's `contains`/`endswith` criteria carry over as wildcards |
| `saptooltip` | `ui5-tooltip` (UI5) / `title` (Web GUI) | medium | tooltip is the field label in SAP |
| `saplabel`, `saplayoutlabel` | `ui5-label` (UI5) / anchor on the label text (Web GUI) | medium | |
| `saptext` | `sapweb-text` (Web GUI) / `visibleinnertext` (UI5) | medium | purpose rule applies |
| `saptype` (`GuiButton`, `MESSAGEBAR`) | `sapweb-type` | medium | |
| `ct` (`MB`, `STCS`) | `sapweb-lsclass` | low | LightSpeed control-type code; verify live |
| `sapheader` | anchor on the page header text, or `<html title>` | — | the Fiori page title |
| `saptcode`, `sapprogram`, `sapapplication`, `sapservicename`, `sapbindingtext`, `lsdata` | `<html sapweb-ses-transaction>`, `<html sapweb-ses-program>`, `<html url='*<sapapplication>*'>`, none, none, none | — | session context belongs on the `<html>` tag; OData service and binding paths have no selector equivalent (description only) |
| `auratype`, `auralabel`, `auraid`, `auraplaceholder` | none / anchor on `auralabel` text / none / `placeholder` | low | Salesforce Lightning component properties computed by Certify, not DOM attributes; `aria-label` from a live capture replaces them |

Workday specifics: `responsiveMonikerInput` / `promptInput` are type-ahead prompts; `relatedActionsList` the Related Actions menu; `activeListContainer*` the suggestion popup rendered as a table — their interaction contract is the source guide's § Composite actions. Certify `Table` objects on Workday and most modern web apps are `div`-based ARIA grids: UiPath's `tableRow`/`tableCol`/`colName` exist only for real `TABLE` markup, so cells there are text-pinned row containers plus a column header caption, never table attributes.

## SAP GUI interface → `wnd` + `sap`

| Certify field | UiPath | Confidence | Notes |
|---|---|---|---|
| `TYPE=BODY CLASS=GuiMainWindow SAPNAME=<PROGRAM>:<DYNPRO>` (window) | `<wnd app='saplogon.exe' cls='SAP_FRONTEND_SESSION' title='<window name>*' />` | — | the map window's `Name` is the screen title; the program:dynpro pair is description only; `v2.x … GuiMainWindow~wnd[0]!~Text=*~Wildcard` is the same window with no title |
| `TYPE=MODAL CLASS=GuiModalWindow` | own `<wnd app='saplogon.exe' cls='#32770' title='<dialog caption>' />` | — | popups are separate OS windows; controls inside carry `wnd[1]/…` ids |
| `TYPE=CONTAINER CLASS=GuiSimpleContainer SAPNAME=<PROGRAM>:<DYNPRO>` | none | — | a subscreen; only says the control's id sits under `usr/sub…/` — wildcard the prefix |
| `ID=wnd[n]/<path>` | `<sap id='<path>' />` — plain text, case-sensitive | high | strip `wnd[n]/`; `wnd[1]` → the modal window's chain (the `id` inside a modal is identical to a main-window id; only the `<wnd>` differs). Plain text keeps the one-call `FindById` path |
| `SAPNAME` only, `PARENT~TYPE=BODY` (field directly in the user area) | `<sap id='usr/<prefix><SAPNAME>' type='<CLASS>' />` with the prefix from `CLASS` | high | the field sits directly under `usr/`; flag when the same field name occurs on several dynpros |
| `SAPNAME` only, `PARENT~TYPE=CONTAINER` (field inside a subscreen) | `<sap id='usr/.*<prefix><SAPNAME>' matching:id='regex' type='<CLASS>' />` | medium | the subscreen segments (`subSUB:SAPLXXX:0100/`) are not recorded; a Normal-matching `*` is compared per path level and cannot span them, so the whole-id regex is the only offline form — it forces a per-node walk of the window, so `type` narrows it; prefer a live capture of the full id when the application is reachable |
| `SAPNAME=shell` / `shell[n]` without `ID` | none | low | GuiShell controls (grid, tree, toolbar, text edit) need the full scripting id — live capture |
| `SAPNAME` with `[col,row]` suffix (`RF05A-XPOS1[2,0]`) | keep in `id` | medium | a cell of a step-loop table — positional, flag |
| `COORDINATES~Row=…~Column=…~Length=…~Height=…` | none | — | screen character coordinates |
| `PARENT~…` | none | — | program:dynpro of the container, see BODY/CONTAINER rows |
| older `v8.x!~OBJECT!~<CLASS>~wnd[0]/<path>!~PARENT~…` | `<sap id='<path>' />` | high | the path after `~` is the scripting id |
| `CLASS` | `type` | — | the component type name; add it whenever the `id` is not plain text, it prunes the walk |
| Table step parameters `Column Caption` / `Row Number` on a `Table` (`GuiTableControl`) | `<sap id='<table id>' tableRow='<row-1>' colTooltip='<caption>' />` | medium | rows are 0-based and absolute; the caption is the column **title**, which the driver exposes as `colTooltip`; `colName` is rejected on a classic table control |
| Table step parameters on a `GridView` (ALV) | `<sap id='<grid id>' tableRow='<row-1>' colName='<technical name>' />` | medium | ALV columns are addressed by technical field name (`MATNR`), which Certify does not record — take it from the caption via a live probe, or use `colTooltip='<caption>'` and flag; ALV grid ids are unreliable across sessions |
| `Tree.Select Node` `NodePath` `A|B|C` on a `Tree` (`GuiCtrlTree`) | Expand Tree / `<sap id='<tree id>' relpath='A/B/C' />` | medium | `relpath` is root-relative, slash-separated node display text; escape a literal `/` in a node text as `\/` |

Scripting-id prefix by `CLASS`: `GuiTextField` → `txt`, `GuiCTextField` → `ctxt`, `GuiPasswordField` → `pwd`, `GuiButton` → `btn`, `GuiCheckBox` → `chk`, `GuiRadioButton` → `rad`, `GuiComboBox` → `cmb`, `GuiLabel` → `lbl`, `GuiTab` → `tabp`, `GuiTabStrip` → `tabs`, `GuiTableControl` → `tbl`, `GuiOkCodeField` → `tbar[0]/okcd`, `GuiTitlebar` → `titl`, `GuiStatusbar` → `sbar`, `GuiStatusPane` → `sbar/pane[n]`, `GuiToolbar` → `tbar[n]`, `GuiSimpleContainer` → `sub`, `GuiScrollContainer` → `ssub`, `GuiCustomControl` → `cntl`, `GuiContainerShell` → `shellcont`, any `GuiCtrl*` → `shell`.

Component → activity, so the substep wording and the build agree: `CTextField`/`TextField`/`Password` → type into (Simulate input); `Button` → click; `OkCodeField` (typing a transaction code) → Call Transaction, not a selector; toolbar `btn[n]` → Click Toolbar Button; menu paths → Select Menu Item; `Tab` → click; `Table` (classic) → table cell scope or Extract Table, cells by `tableRow` + `colTooltip`; `GridView` (ALV) → cells by `tableRow` + `colName`; `Tree` → Expand Tree with `relpath`; `StatusBar` → Read Statusbar (the verification channel); `ComboBox` → Select Item; `CheckBox` → Check; `RadioButton` → click plus verify; `TitleBar` → get text for verification; `HTMLViewer` → an embedded browser: switch to `webctrl` inside it. SAP `text` values are untrimmed and often space-padded: verify a caption with a trailing `*`.

## Desktop interfaces ("Silverlight", UIA, NetUI) → `wnd` + `uia`

Format 3 (`<findby>` of UI Automation properties) and format 4 (`<properties>`) record the same information under different names.

| Certify (format 3 `<n>` / format 4 `property name`) | UiPath | Confidence | Notes |
|---|---|---|---|
| `windowflag="Yes"` / `iswindow="true"` object: `controltype`=`Window`/`Pane`, `name`, `classname` | `<wnd app='?' cls='<classname>' title='<name>' />` | — | `app` from the application record or launch step; `Chrome_WidgetWin_1`/`RootView` windows are browser chrome UI (dialogs, find bar), not page content |
| `controltype` / `NativeType` | `role` (localized control type table in the translation guide) | medium | `Primitive` (pattern objects) → none |
| `name` / `NetName` | `name` | medium (high when it is the accessible name of a button or field) | decode `_x…_`; `contains` → wildcard; empty → drop |
| `automationid` / `AutomationId` | `automationid` | high | empty or `DynamicValue` → drop |
| `classname` / `ClassName` | `cls` | medium | `#32770`, `Button`, `TextBlock`, `RadTabControl`, `SysTreeView32` |
| `labeledby` | anchor — `name` of the label element | medium | `uia` has no `labeledby`; the caption is a programmatic association, so the anchor may match the label's accessible name |
| `helptext` | `helpText` | last resort | usually `DynamicValue` |
| `accesskey`, `acceleratorkey` | `acskey`, `accelkey` | last resort | `Alt+O`, `Ctrl+L` |
| `ispassword` | `ispwd` | last resort | |
| `iscontentelement`, `iscontrolelement` | none | — | constant flags |
| `findby instance="n"` / `instance="n"` | `idx` when `n > 1` | — | strict, never anchored |
| `<parentpath>` | ancestor `<uia>` tags | — | keep only ancestors that carry an `automationid`, a `name` or a distinctive `cls` and are needed for uniqueness; `Unknown`/`Pane` containers with empty properties are dropped |
| `ignorecase="true"` (format 4) | `casesensitive:<attr>='false'` | — | only when the value's case could vary |
| `frameworkid="WPF"` | `uia` | — | translate to `uia`; the `wpf` tag only when WPF-only properties were recorded |
| `frameworkid="DirectUI"` (Windows shell dialogs) | `uia` | — | |
| `frameworkid="GenericApplicationSupport"`, `patternname`, `objectidentifier*` | none | low | Certify's pattern/image engine — semantic description, live capture |
| `frameworkid="ImageObjects"`, `ImageObjectAttributeString` | none | low | image target |
| `<anchor>` | UiPath anchor from the nested object | — | |

## Java interface → `wnd` + `java`

| Certify element | UiPath | Confidence | Notes |
|---|---|---|---|
| `type="window"` object: `caption`/`logicalname`, `class` (`javax.swing.JDialog`, `…JFrame`) | `<wnd app='java*.exe' cls='SunAwtDialog|SunAwtFrame' title='<caption>' />` | — | `JDialog` → `SunAwtDialog`, `JFrame` → `SunAwtFrame`; internal frames are `<java role='internal frame' name='…' />` under the main window |
| `class` (full Java class) | `cls` = last dotted segment (`JButton`, `BusyComboBox`, `JideChart$1`) | high | |
| `caption` | `name` | medium | the accessible name; absent on custom components |
| `certifyclass` | `role` hint: `javaButton` → `push button`, `javaToggleBtn` → `toggle button`, `javaRadioBtn` → `radio button`, `javaCombo` → `combo box`, `javaEdit` → `text`, `javaList` → `list`, `javaCustom` → unknown (live) | medium | role is matched case-insensitively |
| `logicalname`, `learnname`, `physicalname` | description only | — | Certify-generated names (`Cmbo-11_1_2`, `Text-28_1`); `logicalname` sometimes carries the caption (`RButton-24_1: Substance`) |
| `path` (`wNPP1B1`) | none | low | encoded positional tree path; `idx` only if the leaf is otherwise ambiguous |
| `parent` | ancestor `<java>` by its caption | — | only when needed |
| several `physicalname id="n"` / `path id="n"` | one element | — | variants learned against several application versions; keep the attributes they share |

## Certify-specific pitfalls

1. The interface named **Silverlight is the UI Automation desktop engine** (`frameworkid` Win32/WPF/DirectUI/Chrome). Nothing in these exports is Silverlight plug-in content; never emit a `<silverlight>` tag for it.
2. `DynamicValue` is a marker, not a value. An `automationid='DynamicValue'` in a selector matches nothing.
3. Encoded names (`_x0020_`) pass silently into a selector as literal text and match nothing — decode.
4. Web `<frame>` values are index paths; UiPath needs the iframe's own attributes. Every control under a non-`body` frame is `frame-unresolved` until captured live.
5. Class-only template objects (`GuiCTextField.(GuiCTextField)`, `Dynamic_*`) and `<instance>0</instance>` objects have no identity of their own; the steps that use them pass the identity in parameters or set it with `Set Attributes` — read those steps for the semantic description.
6. SAP GUI positional ids (`tbar[0]/btn[11]`, `menu[4]`) and `COORDINATES` are not identity; the SAP activities own toolbar, menu and transaction navigation.
7. `xclassname`, `controltype`, `isdisplayed` and friends are Certify's classification of the element, not properties of it.
8. Windows exist under duplicate names (two `View Worker`, two `Sign in to your account` for different applications); resolve a control's window through its own parent object, never by name.
9. `Set Attributes` with `REPLACEME`/`replaceme` parameterises a locator at run time → selector variable `{{Argument}}` bound to the workflow argument.
