# Worksoft Certify Selectors Guide — locator formats and attribute translation

Companion to [worksoft-certify-source-guide.md § UI Target Locators](worksoft-certify-source-guide.md): how each Certify interface stores a control's recognition data and which UiPath attribute each recorded field becomes. The UiPath vocabulary, reliability tiers, criteria mapping, anchor policy and confidence tiers are in [selector-translation-guide.md](../selector-translation-guide.md) and are not repeated here — read it first. Observations below come from twenty-one production exports (Workday, SAP GUI, SAP Fiori/Web GUI, Coupa, NetSuite, Jira, LabVantage LIMS, ENOVIA PLM, Kinaxis, WinSCP, Windows dialogs).

The recognition data is `MapObjects.json` → windows (`ObjectIdParmValues[].CertifyValue`) and `ChildTrackObjects[].ObjectIdParmValues[].CertifyValue`; one locator per object (a handful have none). The `targets` command parses every format below into one normalized shape (`technology`, `class`, `instance`, `findby[]`, `parentpath[]`, `anchor`, `volatile[]`) — work from the `certify-targets.json` execution derives from the export, never from the raw XML.

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
| `tagname` | `tag` — **of the node Certify learned, which for composite widgets is the wrapper, not the leaf that takes the action** | — | upper-case; matched case-insensitively; `*`-suffixed hash tag names wildcarded. Measured on a Workday export of 673 web controls: `PushButton` objects recorded `tagname` DIV 102× against BUTTON 71×, `EditBox` DIV 92× against INPUT 57×, `CheckBox` DIV 9× against INPUT 3×, `Link` DIV/SPAN 62× against A 26× — the recorder attaches to the container it resolved and collects `label` and text from descendants. The recorded tag is usable for a scope or anchor tag; the *acting* tag is the one the control type implies ([selector-translation-guide.md](../selector-translation-guide.md) § Web widget anatomy) or is left out when unknown (pitfall 11) |
| `instance` > 1 | `idx` | — | strict, never anchored; Certify counts within its findby set, UiPath counts same-tag matches in document order under the parent tag's element — the number carries over only as a hint to re-derive live |
| `data-automation-id`, `data-testid`, `data-*` | same attribute | high **only when the value names an instance** | author-controlled identifiers (Workday's `data-automation-id`). Most such values in a component framework are **component types** repeated once per instance on the page (`responsiveMonikerInput`, `menuItem`, `promptOption`, `selectedItem`, `cell`, `sidebarL1`): a type id identifies the widget family, and the instance is identified by its label or text (`aaname` on the leaf, `aria-label` on the container) or by a per-instance id (`data-metadata-id`, a stable `id`) — never by `idx` ([selector-translation-guide.md](../selector-translation-guide.md) rule 14). Confidence **medium** for a type id alone |
| `id`, `name`, `aria-label`, `type`, `href`, `alt`, `placeholder`, `src`, `operationid`, `aria-haspopup` | same attribute | high (`id`, `name`, `aria-label`) / last resort (others) | an `id` with a letter after a digit (`input-45f6g7h8`, `wd-FieldSet-56$1234`) is auto-generated by the driver's own rule — wildcard the semantic part or drop; `href` and `src` are volatile URLs — wildcard the host |
| `title` (element attribute: `Edit Company`) | `uipath-html-title` | last resort | `title` on `webctrl` is the **document** title, not the element's |
| `role` | `aria-role` | high | `role` on `webctrl` is a constant — never emit it |
| `classname`, `xclassname` | `class` | medium | one semantic token only, wildcarded both sides — a multi-token class value is never usable; `xclassname` (`Dropdown`, `Listbox`, `Element`) is Certify's own classification, not a DOM class — drop |
| `parentelement.<attr>`, `parentelement.parentelement.<attr>`, `parentelement.tagname` | a preceding `<webctrl>` tag carrying that attribute | as the attribute | one ancestor level per `parentelement.`; `parentid`/`parentclass` on the leaf are the *nearest* ancestor's values, not the direct parent's |
| `innertext`, `normalizedinnertext`, `text`, `normalizedtext`, `alltext`, `normalizedalltext`, `outertext`, `normalizedoutertext` | `visibleinnertext` (or `aaname` when the text is the element's own direct content) | medium | never the primary identifier of an input; `visibleinnertext` is inherited by every ancestor — exact match, leaf pinned by `tag` (+`class` or `isleaf`); `aaname` on a `div`/`span`/`li` is only its own direct text and is not inherited; Certify's `normalized*` variants collapse whitespace, UiPath does not — match the visible spelling; on a container a wildcarded text is the row/card pillar |
| `label` | the **acting leaf's** `aaname` when that leaf is form-ish and programmatically labelled (`INPUT`/`TEXTAREA`/`SELECT`/`BUTTON` with `<label for>`, `aria-labelledby`, `title` — the driver synthesises `aaname` from the label, and its own default target keeps it); otherwise an anchor on the `LABEL`/caption element (the driver's default anchor). Never on the recorded wrapper tag | medium | Certify's `label` is the associated caption; `label` + `data-automation-id` on one object (55 of 673 Workday controls) come from two nodes — the caption from the leaf or its `LABEL`, the id from the wrapper (pitfall 10). A control with both `label` and a text anchor recorded takes `label` |
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

Workday specifics, verified live against a tenant (2026-09-20) — the generic anatomy they instantiate is [selector-translation-guide.md § Web widget anatomy](../selector-translation-guide.md):

- A prompt (`responsiveMonikerInput` / `promptInput`) is a nest: form item `LI` (`formLabelRequired` when required) › `LABEL[formLabel, for=…-input]` + wrapper `DIV[responsiveMonikerInput, data-metadata-id=<field id>]` › … › `INPUT` (`aaname` = the label, `placeholder='Search'`, `aria-labelledby`) with siblings `UL[selectedItemList]` › `DIV[selectedItem, aria-role=option, aria-label='<value>, Press delete…']` › `P[promptOption, aaname=<value>]`. Its suggestion popup is `DIV[activeListContainer, aria-role=menu, aria-label='<Field label>, Options Expanded']` › `DIV[menuItem, aria-label=<option>]` › … › `DIV[promptOption, aaname=<option>, isleaf=1]`. **`promptOption` names both the selected chip and every popup entry**: the accepted value is the `selectedItem` under the field, the pick is the `promptOption` under the popup labelled with the field.
- A custom list (`selectWidget`, Certify `DropDown`/`ListBox`) is `DIV[aria-role=combobox, aria-haspopup=listbox, aria-labelledby=…-formLabel]` showing `selectSelectedOption`; it exposes `selecteditem` but **no `items`**, so Select Item cannot drive it. Its popup is `UL[menuList, aria-role=listbox, aria-label='<Field label>']` › `LI` › `DIV[aria-role=option, id='…-entry-<n>']` › text leaf with `aaname` = option.
- Date fields (`dateTimeWidget`) are three `INPUT type='number'` segments `dateSectionMonth-input` / `dateSectionDay-input` / `dateSectionYear-input` (`placeholder` MM/DD/YYYY, `aria-label` Month/Day/Year; the month segment carries the field label as `aaname`) plus a `datePickerButton`; a hidden leaf `hiddenDateValueId-…` reads `current value is 9/20/2026`. The Certify `Hor=10` click was the month segment.
- Command buttons are `BUTTON[wd-CommandButton_uic_okButton | …cancelButton]` with `aaname` = caption; icon buttons (`closeButton`, `inbox_preview`, `Current_User`, `datePickerButton`) carry `aria-label` and no `aaname`. Related Actions: `relatedActionsList` (aria-role=menu) with `relatedActionsItemLabel` leaf labels; each hovered level opens a second `relatedActionsList` popup of the same shape, and a label can repeat across groups. Error banner: `bannerContainer` › `bannerLabel` (`aaname='Errors: 1    '`, padded) + `bannerButton` "View All".
- Grids of the `tables20` generation are **real `TABLE` markup**: `TABLE[data-automation-id='table']` › `TR[row, data-row-id]` › `TD[cell, tableRow, tableCol, colName, rowName]`; `colName` is the header cell's full text including the sr-only sort caption (`'Document Category*'`), `rowName` the row's first cell text. Older GWT grids may be div-based. Probe one cell live before choosing between table attributes and a text-pinned row (translation guide rule 8).

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
10. **One Certify object is not necessarily one DOM node.** Certify records a control as a single object with a flat `findby` attribute set, but its recorder collects those attributes by walking the element's ancestry until each one is satisfied, and its `tagname` is the wrapper it attached to (the `tagname` row above has the counts). A `data-automation-id` and a `label` on the same Certify object routinely come from a wrapper and from an inner input respectively. Translating the object into one tag reproduces a node that does not exist ([selector-translation-guide.md](../selector-translation-guide.md) rule 14) — live, `evaluate` rejects it with *the attribute 'aaname' does not exist on this element*. Translate by role instead: the caption goes to the acting leaf's `aaname` (or to a `LABEL` anchor), the wrapper's type id is at most a scope tag, and the instance is told apart by the caption, never by `idx`. When the export gives no way to tell which node is which, ship tag-only plus the semantic description and flag `offline-unverified`.
11. **`xclassname` and `controltype` decide the activity, never the tag.** Certify's `Dropdown`, `Listbox`, `Element`, `Textbox` are its own classification (pitfall 7). They tell you which interaction pattern to build; they do not tell you the HTML tag, and `tag='DIV'` is not a safe default for an unknown one — a command button Certify called `Element` is a `BUTTON`, and a `tag='DIV'` on it is a hard mismatch. Map the control type to the tag it implies, or omit `tag` entirely: an absent `tag` widens the search, a wrong one eliminates the only correct candidate.
12. **A Certify verification step is usually not a UiPath activity.** Certify expresses "the value was accepted", "the page arrived", "the field now reads X" as its own check steps, and the natural-looking translation is one Check Element per check. That is almost always wrong: those checks are post-conditions of the step before them and belong in that activity's `VerifyOptions` ([source-migration-guide.md § Verification](../source-migration-guide.md)). Translate a Certify check into a separate activity only when a later Certify step branches on its result. A migrated project whose Check-activity count approaches its Click count has taken the wrong route everywhere.
