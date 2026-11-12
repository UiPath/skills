# Selector Translation — desktop

The desktop tags beside `wnd` ([selector-translation-guide.md](selector-translation-guide.md)): UI Automation, Active Accessibility, Java Access Bridge, and the other desktop and remote tags. Read whole with that guide when the target catalog holds controls of these technologies; rule numbers are its own.

## `uia` — UI Automation element

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

## `ctrl` — Active Accessibility element

| Attribute | Tier / role |
|---|---|
| `automationid`, `role` | very reliable |
| `labeledby`, `name`, `rowName` | alright |
| `aastate`, `virtualname`, `helpText`, `accessibleDescription` | less reliable (`aastate` is state — never on Check targets) |
| `text` | highly unreliable |
| `idx` | position |

## `java` — Java Access Bridge element

| Attribute | Meaning | Tier / role |
|---|---|---|
| `role` | accessible role (`push button`, `text`, `combo box`, `check box`, `radio button`, `toggle button`, `list`, `list item`, `table`, `tree`, `label`, `menu item`, `page tab`, `frame`, `dialog`, `panel`) | very reliable — matched case-insensitively |
| `cls` | simple class name (`JButton`, `BusyComboBox`, `JideChart$1`) | very reliable |
| `accessibleClass`, `hasTableAncestor` | | very reliable |
| `name` | accessible name (caption) | alright |
| `rowName`, `colName`, `tableRow`, `tableCol` | | table |
| `virtualname` | the Swing component name (`Component.getName()`) when the component has one and its accessible name is set or nothing else names it; otherwise the virtual accessible name — accessible name, else description, else, for a text, password text, combo box, list, table, spin box, slider or date editor not directly under a table or tool bar, the label that labels it, a label left of or above it in the same parent, or (text, combo box) a button left of it; a label's own text; a check box's value `true` / `false`; empty on a check box or combo box cell of a table | identity when it holds a component name (an application's own item identifiers); semantic when it holds a neighbouring label's text, which repeats across fields labelled alike; state when it holds a check box value — never then |
| `javastate`, `backgroundColor`, `foregroundColor` | | last resort |
| `idx` | | position |

The driver's default `java` selector is built from `role`, `name`, `cls`, the table attributes and `idx`, never from `virtualname`, which it lists only among the element's other attributes. A driver default that ends in `idx` therefore says nothing about `virtualname`: read it in the attribute listing (rule 15), and where it holds a component name it replaces the index (rule 7).

## Other tags

| Tag | Attributes | Note |
|---|---|---|
| `wpf` | `type`, `name`, `uid`, `header`, `automationid`, `content`, `text`, `tooltip`, `labeledby`, `groupname`, `row`, `col`, `rowName`, `colName`, `checked`, `isexpanded`, `idx` (and driver internals `command`, `datastr`, `dotnethash`, `persistid`, `band*`, `auto*`) | UiPath normally surfaces WPF through `uia`; translate WPF recordings to `uia` unless the source recorded WPF-only properties (`x:Type`, `Uid`, `Header`, `Content`) |
| `silverlight` | `role`, `name`, `text`, `idx` | Silverlight plug-in content only; a source *engine* named Silverlight is not this |
| `qt` | `name`, `role`, `tooltip`, `accessibleName`, `statusTip`, `text`, `rawtext`, `idx` | |
| `curl` | `cls`, `role`, `name`, `text`, `tableRow`, `tableCol`, `colName`, `idx` | Curl applets |
| `ax` | `role`, `subrole`, `name`, `title`, `identifier`, `filename`, `url`, `help`, `value`, `rowCount`, `columnCount`, `tableRow`, `tableCol`, `rowName`, `colName`, states, `idx` | macOS accessibility |
| `rdp`, `rdpapp` | `<wnd>` attribute set | remote runtime |

## Rule 8 — desktop

A Windows Forms list view (`SysListView32`) reached through UI Automation exposes each row as a `list item` whose cells are `text` children, and its column headers as `header item`s under a `header`, outside the rows. Each cell carries `colName`, its column's header caption, and `rowName`, the text of its row's first cell, so a cell found by row content and column caption is `<uia role='text' rowName='{{Key}}' colName='<header caption>' />` under the list. Under the list, the Find Elements filter `<uia role='text' />` in Find Descendants mode takes only the cells; searched from the window, it also takes the window's captions and those of the windows it owns (§ Rule 9), so a source that reads the cells in groups by position reads the wrong cell of every row, or overruns the collection.

## Rule 9 — desktop

**A window's UI Automation tree holds the windows it owns.** A modal dialog, a form the window opened and the windows those own in turn sit under their owner, topmost first and ahead of the owner's own elements. A `uia` search from the owner's scope therefore also matches in every open window it owns, and there first: a Find Elements with no Target in the owner's card returns the owned windows' matches ahead of the owner's, and a target under the owner's window selector resolves a control of an owned window, whatever the card's attach mode.
