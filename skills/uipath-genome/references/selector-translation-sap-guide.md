# Selector Translation — SAP GUI

SAP GUI's side of [selector-translation-guide.md](selector-translation-guide.md): what the rules add for SAP GUI for Windows and SAP GUI for Java, and how the SAP activities act on what a selector finds. Read whole with that guide when the target catalog holds SAP GUI controls, together with the SAP GUI attribute reference of the UI Automation package's Selector Reference (that guide names where it is read): the SAP session attributes of `wnd`, the `<sap>` schema with each attribute's matching behaviour, the attributes each kind of element takes, and the ids that hold or shift between screens. Rule numbers are that guide's.

## Rule 1 — SAP GUI

`<sap>` ids are the same on both front ends, so a SAP GUI for Windows session is a comparable instance for the targets of SAP GUI for Java ([ui-target-migration-guide.md § Verifying targets](ui-target-migration-guide.md)), except for what the attribute reference says differs between them: the case of `type` values and the inactive system-toolbar buttons.

## Rule 2 — SAP GUI

`text` holds a caption with SAP's padding: match it with a trailing `*`.

## Rule 3 — SAP GUI

A scripting id the source recorded, normalised as the attribute reference gives, is the whole target: the driver's own default is the `id` alone, strict. `type` adds nothing beside a plain `id`; beside a wildcard or regex `id` it narrows the tree walk, on the elements that take it.

## Rule 8 — SAP GUI

The column comes from the header caption: on a SAP GUI table control the recorded title itself as `colName`, and on an ALV grid `colTooltip` — the column's tooltip, not the title its header displays, so a recorded title is checked against a live listing before it becomes one (the grid's `colName` is the technical field name). A title or tooltip two columns of one table share identifies neither, since the match takes the first: that column is its other attribute or its `tableCol`, which the driver itself writes for a shared tooltip, read from a live listing. SAP GUI rows are 0-based and absolute, so a source's 1-based visible row number is neither; a SAP GUI row found by content is `text` beside the column attribute.

A grid cell target is `<sap id='<grid id>' tableRow='…' colName='…' />` and stays **medium** until seen live: ALV grid ids are unreliable across sessions. A classic table cell is the table's `id` with `tableRow` and a column attribute, never the cell's own scripting id, whose `[c,r]` count only the displayed rows and columns.

A **classic list** (an ALV list, a report's output) has no table element and takes no table attribute. A row found by content is the column's label pinned by its value, `<sap id='usr/lbl[<column>,*]' text='<value>' />`, the `*` staying inside its segment. Only the displayed page is in the tree, so a label searched for over the whole list is looked for from the first page (`tbar[0]/btn[80]`), then on each next page (`tbar[0]/btn[82]`). The driver's own default for a list label is its `text` plus `type`, which rule 4 excludes on a read target.

## Rule 9 — SAP GUI

A SAP session window is identified by `app`, `cls` and its title, which is the current screen's (`SAP Easy Access`, a transaction screen's own caption): each screen the automation works on is a scope of its own that keeps its title, and the controls every screen holds (the command field, the system toolbar, the status bar) sit on one shared screen whose scope is `app` and `cls` alone, so they resolve on whichever screen is up, under a `ByInstance` card, where the title only ranks the session's windows, or under one card per screen. The system name, session number and client a title can also show (`<SID> (<session>) (<client>)`) change with the logon and are wildcarded. A SAP modal dialog is identified by `cls='#32770'`, the presence of `sapSysSessionId` (which the SAP Logon pad and the process's other `#32770` windows lack) and its caption — without a recorded caption, by the first two alone, which match whichever SAP dialog of the session is open, and its own `sapProgram` and `sapScreen` (the popup's program and screen number, which a source recording `<PROGRAM>:<DYNPRO>` names) tell one popup from another. The class is what keeps a dialog's targets out of the session window, whose controls carry the same ids (`tbar[0]/btn[0]`, `usr/…`): under a `ByInstance` card the caption only ranks the session's windows (the Selector Reference's `wnd` attribute reference), so a dialog's window selector always keeps its `cls` — on SAP GUI for Java its own, `SunAwtDialog`. The other `sap*` session attributes: the SAP GUI attribute reference.

| Technology | Scope on | Shape |
|---|---|---|
| SAP GUI session / SAP modal dialog | `app` + `cls` + the screen's title / `app` + `cls` + `sapSysSessionId` present + caption, or the popup's program and screen in its place | `<wnd app='saplogon.exe' cls='SAP_FRONTEND_SESSION' title='SAP Easy Access' />` / `<wnd app='saplogon.exe' cls='#32770' sapSysSessionId='?*' title='Information' />`, `<wnd app='saplogon.exe' cls='#32770' sapSysSessionId='?*' sapProgram='SAPLSHSY' sapScreen='0700' />` |

## Acting on SAP GUI controls

**Toolbars and menus.** Application-toolbar buttons and menu positions shift between screens (the SAP GUI attribute reference): drive them with the SAP activities (Click Toolbar Button, Select Menu Item, Call Transaction), not with selectors, when the tooltip or menu text is known, and otherwise target the id on the screen the source pressed it on, flagged `positional`.

**Call Transaction** waits until the session reports the transaction it names, failing early only on a status-bar error it lists, so `/n` alone never succeeds: it lands on a start screen reporting `SESSION_MANAGER`, `SMEN` or `S000`, and the activity times out. A call of `SESSION_MANAGER` is no stand-in: from inside a transaction SAP answers it with a "Cannot start transaction SESSION_MANAGER" dialog, and the activity then succeeds where the start screen reports `SESSION_MANAGER` and times out where it reports `SMEN`. A transaction is left by typing `/n` into `tbar[0]/okcd` and pressing Enter with hardware events, as Simulate types no special keys.

**Select Menu Item**'s item is the menu path in captions, as the session window's `items` list it (`System/Status...`); each level is matched exactly, case included, and a `*` or `?` matches within its own level only.

**Tabs.** A tab (`tabp…`) is selected by a single click, which under Simulate needs no on-screen rectangle; under Simulate a double click on a tab fails. A tab found by its caption is Select Item on its tab strip (`tabs…`), which matches the caption exactly, case included.

**Rows by content.** A row found by content in a table control or ALV grid is the SAP Table Cell Scope activity, whose row filter is a cell selector of the `<sap>` schema (`text` beside a column attribute); its row modes and limits are the package's own (its activity doc and SAP guide).

**Row selection.** A row is selected through its row element (`tableRow` alone), whose `checked` attribute is the row's selection: Check on it sets the selection whatever it was (`Action` Check selects, Uncheck deselects), while a click toggles it — a click on a table control's row element selects the row on either front end and under either input method, and a second Simulate click deselects it. A click on one of its cells selects nothing; its row-selector cell (`tableCol='-1'`) selects the row except under Simulate on SAP GUI for Windows.

**Combo boxes.** A combo box's `items` and `selecteditem` are the entries' captions, never their keys. Select Item takes an entry's caption or its key, exact — case and spaces included — or as a `*` pattern, so an entry a source chose by key is selected by that key, and a caption copied with padding or a key in front matches nothing. The blank entry is one space on SAP GUI for Windows and the empty text on SAP GUI for Java, whose `items` leave it out.

## Checks

| Check | Decide by | Rule |
|---|---|---|
| A `<sap>` attribute the element does not take: `type` or `tooltip` beside the `id` of a table control, ALV grid or tree, or on its rows, columns, cells and nodes | attributes + the control's kind | the SAP GUI attribute reference |
