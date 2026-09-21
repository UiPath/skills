# Automation Anywhere Selectors Guide — recorder formats and property translation

Companion to [automation-anywhere-source-guide.md § UI Target Locators](automation-anywhere-source-guide.md): how an Automation 360 recorder capture stores a control's recognition data and which UiPath attribute each recorded property becomes. UiPath vocabulary, reliability tiers, criteria mapping, anchor policy, node identity and confidence tiers: [selector-translation-guide.md](../selector-translation-guide.md) — read it first. Observations come from one production export (nineteen bots migrated from Enterprise 11: an Oracle Forms 11g application delivered as a Java Web Start applet, its browser launch page in Internet Explorer and Microsoft Edge, Microsoft 365 and corporate identity-provider sign-in pages, Java runtime and Windows credential dialogs). Work from the normalized `a360-targets.json` the source guide's `targets` command derives, never from the base64 blob. Read § Capture format, § Format-wide conventions and § Pitfalls in full; the per-technology tables are a catalog — read the sections for the `technology` values the catalog contains.

## Capture format

One `Recorder.capture` node = one control. Its `uiObject` attribute carries:

| Field | Content | Use |
|---|---|---|
| `uiObject.technologyType` | `JAVA`, `HTML`, `MS_ACTIVE_ACCESSIBILITY`, `MS_UI_AUTOMATION` | Decides the UiPath tag chain (§ Technology → chain) |
| `uiObject.controlType` | `TEXTBOX`, `PASSWORD_TEXT`, `BUTTON`, `LABEL`, `CLIENT` | Decides the acting tag / role and the activity ([selector-translation-guide.md](../selector-translation-guide.md) rule 14) |
| `uiObject.criteria` | map `property → {enabled, value}`; only `enabled: true` entries were used for matching; a value may be a variable expression (`$intStatusIndex$`, `$strMenuItemName$`) | The recorded match set — the left side of the tables below |
| `uiObject.blob` (base64 JSON) → `objNode` | the object as captured: `name`, numeric `role`, `description`, `className`, `id`, `value`, `windowTitle`, `path.objPath[].index` (accessibility tree path), bounds and click point, `technology.techType` / `platformType`, `attributes[]` (every property the recorder read, enabled or not) | Disabled properties still carry information (an accessible name the author did not match on); the `path` is the positional identity |
| `uiObjectWindow.expression` | `$window-N$` → a WINDOW variable of the bot: `window.name` (title with `*`), `window.class`, `window.path` (executable) | The window tag (`<wnd>` / `<html>`) |
| action attribute + `value` / `valueCV` | what was done (§ source guide, Signals) | The activity and, for a SETTEXT with tokens, the composite pattern |
| `screenshotMetadataPath` / `thumbnailMetadataPath` | PNG names under `<Bot>Metadata/` | A picture of the control and its screen at capture time — the executor's aid when deriving a target offline |
| `blob.browserFramework`, `blob.captureVersion` | present on captures made with the Automation 360 recorder (`captureVersion` 2400 / 2900); absent on captures converted from Enterprise 11 | Which recorder produced the properties; v11 conversions carry `uniqueID` / `class` keys, native captures `uniqueId` / `className` |

The same control recorded twice (a live capture and its disabled twin, or the same field in several bots) differs in `Path` (`-1|1|2|…` vs `1|1|2|…`), sometimes in the enabled criteria set, never in `Name` / `Role`: collapse on window + `Name` + `Role` (+ `Index` when it is a literal).

## Technology → chain

| `technologyType` | Window | Element | Notes |
|---|---|---|---|
| `JAVA` | `<wnd app='<window.path exe>' cls='SunAwtFrame' title='<window.name>' />`; a `SunAwtDialog` class is a Java dialog and gets its own `<wnd>` | `<java … />` | Java Access Bridge at run time; the executable is the Java launcher (`jp2launcher.exe` for Web Start, `java.exe` / `javaw.exe` for a desktop launch) — one application, several launchers across bots → one scope per launcher variant, chosen by Configuration Question |
| `HTML` in an `IEFrame` window | `<html app='iexplore.exe' url='…' />` | `<webctrl … />` | Internet Explorer pages; frames per § HTML |
| `HTML` in a `Chrome_WidgetWin_1` window of `msedge.exe` | `<html app='msedge.exe' url='…' />` | `<webctrl … />` | Edge; the recorded title (`LARA*- Microsoft Edge`, `Sign On*Microsoft Edge`) is the tab title — scope on `url`, keep a title fragment only when two tabs of one host are open ([selector-translation-guide.md](../selector-translation-guide.md) rule 9) |
| `MS_ACTIVE_ACCESSIBILITY` | `<wnd app='<exe>' cls='#32770' title='<window.name>' />` (`javaw.exe` Security Warning, `jp2launcher.exe` Java Update Needed, `explorer.exe` Run) or `cls='Credential Dialog Xaml Host'` (`CredentialUIBroker.exe` Windows Security) | `<ctrl … />`; a `Class` of `Button` / `Edit` may instead be a child `<wnd cls='Button' aaname='…' />` | Win32 dialogs; both shapes are legal, the driver default decides ([selector-translation-guide.md](../selector-translation-guide.md) rule 15) |
| `MS_UI_AUTOMATION` | `<wnd app='msedge.exe' cls='Chrome_WidgetWin_1' />` | `<uia … />` | Browser chrome (toolbar buttons), never page content |

The window class and executable come from the WINDOW variable, not from the capture; a variable with empty `class` / `path` (title-only) yields `<wnd title='…' />` with `app` from a Configuration Question.

### Format-wide conventions

- Only **enabled** criteria were matched at run time; disabled properties in `objNode.attributes` are context (the accessible name of a positional control, the class of a button) and may supply the semantic description and, when the enabled set is positional only, a candidate identity to verify live — never a matched attribute without live confirmation.
- Criteria values are exact matches with `*` wildcards allowed (window titles use them; control names rarely). A variable expression as a value (`Name="$strMenuItemName$"`, `Index="$intStatusIndex$"`) becomes a selector variable `{{Argument}}` bound to the workflow argument.
- `Path` is the accessibility tree path from the window (child indexes separated by `|`; `-1` = the window itself); `Index` is the control's position among the window's controls of that role as the recorder counted them. Both are **position** ([selector-translation-guide.md](../selector-translation-guide.md) rule 7): never an attribute, `idx` only when nothing else identifies the control, flagged.
- `States` (`enabled,focusable,visible,showing,editable,single line`) is state — never in a target.
- Numeric `objNode.role`: 1 = push button, 5 = text, 66 = static text / label, 0 = client area, 25 = HTML client (`DIV`); the string `Role` criterion (`PushButton`, `TextBox`, `StaticText`, `Client`) is the readable form.
- No capture records the executable of the browser or the URL of the page; `url` comes from the `openbrowser` / `runApp` command that opened the page or from the `HTML FrameSrc` host, `app` from the WINDOW variable's executable.
- Passwords typed by a `PASSWORD_TEXT` capture are CREDENTIAL references or redacted literals; the target is the field, the value is the credential asset.

## Java (Oracle Forms applet through Java Access Bridge) → `wnd` + `java`

Criteria observed: `Name`, `Role`, `Path`, `Index`, `States`, `Description`, `Parent`, `Class`.

| Criterion | UiPath | Confidence | Notes |
|---|---|---|---|
| `Role` `TextBox` | `<java role='text' />`; the acting activity is Type Into / Get Text | — | Forms text items and grid cells are both `text` |
| `Role` `PushButton` | `<java role='push button' />` | — | Forms buttons carry their caption plus the mnemonic in the name (`OK ALT O`, `Search alt S`, `Connect As alt C`, `No ALT N`, `Yes ALT Y`) — keep the full recorded name, wildcard the mnemonic (`name='OK*'`) only when the caption alone is unique |
| `Role` `StaticText` | `<java role='label' />` | — | Status bar messages (`FRM-40301: …`) and menu-tree captions |
| `Role` `Client` | `<java role='panel' />` or the internal frame / dialog itself | low until seen live | The Forms canvas or an alert; its accessible `Name` is the window title (`Consignment Booking`) or the alert text (`Error LARA-012695: Query caused no records to be retrieved.`). Which node carries the name is a live question ([selector-translation-guide.md](../selector-translation-guide.md) rule 15) |
| `Name` (literal) | `name` | medium (high when the name is a unique field label) | Field labels end in a colon (`Order No: Required`, `Haulier:`, `Username:`, `Dept : `) — keep the spelling including trailing spaces and colon |
| `Name` = variable expression | `name='{{Argument}}'` | medium | Menu nodes clicked by caption (`$strMenuItemName$`) |
| `Description` | none; semantic description text | — | Same as `Name` on Forms controls |
| `Parent` (`Change Department`, `User Login`, `Menu Search`) | ancestor `<java role='internal frame' name='<Parent>' />` (or `role='dialog'`) | medium | The enclosing Forms window; the one attribute that scopes a repeated alert text to its dialog |
| `Class` | `cls` | medium | Rare on Forms (Swing class names like `JButton`) |
| `Path` | none | low | Positional; keep as description only; two captures of one control disagree on its first segment (`-1` vs `1`) |
| `Index` literal (`Index="30"`, `"77"`, `"82"`) | `idx` on a strict selector, **flagged** | low | Toolbar buttons and unlabeled fields have no name — the log line beside the capture names the function; live capture must find a real identity or the target stays positional |
| `Index` = variable (`$intStatusIndex$`) with a `Name` shared by every row (`Status`) | the **row rule** of a table pattern ([source-migration-guide.md § Composite interactions](../source-migration-guide.md)): row pinned by the key column's value, cell by the column name; `idx='{{Row}}'` only as the flagged fallback | low | Forms grids expose each visible row's cell as a same-named `text`; the recorder counted them top to bottom (`134` = the first Status cell in the reference export) |
| `States` | none | — | state |

Component → activity, so substep wording and build agree: `TextBox` → Type Into (with the confirm key when the source typed `[TAB]`) / Get Text (`GETPROPERTY Value`); `PushButton` → Click; `StaticText` → Get Text or an anchor; `Client` → Get Text of the alert / title, or Check App State when the read only decides a branch; `Keystrokes` `F5` / `F11` / `Ctrl+F11` / `Ctrl+S` / `F4` → Keyboard Shortcuts targeted at the Forms frame (the shortcut is the application's function); `Security Warning` `Alt+I` / `Alt+R` → Click on the dialog's `Run` button (`<java role='push button' name='Run' />` under the `SunAwtDialog`) with the shortcut as fallback.

## HTML (Internet Explorer and Edge pages) → `html` + `webctrl`

Criteria observed: `DOMXPath`, `HTML Tag`, `HTML ID`, `HTML Name`, `HTML Type`, `HTML HasFrame`, `HTML FrameName`, `HTML FrameSrc`, `HTML FramePath`, `HTML TagIndex`, `innerHTML`, `outerHTML`, `Path`.

| Criterion | UiPath | Confidence | Notes |
|---|---|---|---|
| `HTML Tag` | `tag` | — | `INPUT`, `BUTTON`, `DIV`, `B`; a `LABEL` / `CLIENT` control type recorded on a `B` or `DIV` is the text leaf the author clicked — the acting node is the enclosing button or link when one exists ([selector-translation-guide.md](../selector-translation-guide.md) rule 14) |
| `HTML ID` | `id` | high when stable (`username`, `password`, `i0116`, `idSIButton9`, `btnLara`), dropped when hash-like | Microsoft sign-in ids (`i0116`, `idSIButton9`) are stable across tenants |
| `HTML Name` | `name` | high | `loginfmt`, `pf.username`, `pf.pass` |
| `HTML Type` | `type` | alright | `email`, `text`, `password`, `submit`, `button` |
| `DOMXPath` `//tag[@attr='value']` | the predicate's attribute (`name`, `id`) | as that attribute | The recorder builds the XPath from the strongest attribute it found — read it as a hint, translate the attribute, never the path |
| `DOMXPath` `…/div[text()='Use another account']` | `aaname` or `visibleinnertext` of the text leaf (rule 5 three-case test) | medium | Text-pinned leaf |
| `DOMXPath` positional (`//div[@id='lightbox']/div[3]/div[1]/…/input[1]`) | none | low | Use `HTML ID` / `HTML Name` / `HTML Type` from the same capture; the path is description only |
| `HTML HasFrame` = `True`, `HTML FrameName`, `HTML FrameSrc`, `HTML FramePath` (`IFRAME[1]/FRAME[1]`) | one `<webctrl tag='IFRAME' name='<FrameName>' src='*<FrameSrc file>' />` per `FramePath` level (`FRAME` for a `FRAME` level) | — | `FrameSrc` may be a full URL in one capture and a file name in another (`http://lara-11g.<host>/LHP_appli.html` vs `LHP_appli.html`) — wildcard the host; the frame's `id` / `name` must be confirmed live (`frame-unresolved`) |
| `HTML HasFrame` = `false` | no frame tag | — | |
| `HTML TagIndex` | `idx` | low | Position among same-tag elements |
| `innerHTML`, `outerHTML` | none | — | Content; a `class` or `id` inside may be recovered into `class` / `id` |
| `Path` (MSAA-style index path recorded beside the HTML criteria) | none | — | Position |

Sign-in pages seen in the reference export (Microsoft 365 `login.microsoftonline.com`, a PingFederate corporate IdP `auth.<tenant>/idp/…`) are third-party applications: one Target Applications row each, one `<html>` scope per host, and the whole login is an **interactive OAuth priming** step the UiPath build replaces by a mailbox connection (Integration Service / Exchange activities) — keep the page targets only when the customer insists on browser login.

## Active Accessibility (Win32 dialogs) → `wnd` + `ctrl`

Criteria observed: `Name`, `Role`, `Class`, `Path`.

| Criterion | UiPath | Confidence | Notes |
|---|---|---|---|
| window (`#32770`, `Credential Dialog Xaml Host`) | `<wnd app='<exe>' cls='<class>' title='<window.name>' />` | — | `Security Warning` (Java, `javaw.exe`), `Java Update Needed` (`jp2launcher.exe`), `Run` (`explorer.exe`), `Windows Security` (`CredentialUIBroker.exe`) |
| `Name` | `name` (or `aaname` on a child `<wnd>`) | medium (high for a dialog button caption: `Don't Block`, `Later`, `Cancel`) | Apostrophes must be escaped in the selector |
| `Role` `PushButton` | `role='push button'` | medium | |
| `Class` `Button` / `Edit` | alternative child window `<wnd cls='Button' aaname='<Name>' />` | medium | The driver default decides between `<ctrl>` and a child `<wnd>` |
| `Path` (`4|1|4|-2|4`) | none | — | Position |

## UI Automation (browser chrome) → `wnd` + `uia`

Criteria observed: `Name`, `ID`, `Path`.

| Criterion | UiPath | Confidence | Notes |
|---|---|---|---|
| `ID` (`view_1003`) | `automationid` | high | Edge toolbar ids are stable per build; verify live |
| `Name` (`Refresh`) | `name` | medium | Localized |
| `objNode.className` (`ReloadButton`) | `cls` | alright | From the blob, not an enabled criterion |
| `Path` | none | — | Position |

A browser-chrome click (refresh) has an activity counterpart (browser navigation / refresh) that needs no target; prefer it.

## Keystroke tokens

Automation 360 key syntax → the key names the genome states (execution encodes them in the owning skill's key syntax): `[ENTER]` Enter; `[TAB]` Tab; `[F4]`…`[F11]` function keys; `[DOWN-ARROW]` / `[UP-ARROW]` arrows; `[CTRL DOWN]x[CTRL UP]` Ctrl+x; `[ALT DOWN]x[ALT UP]` Alt+x; `[WIN DOWN]r[WIN UP]` Win+R; plain characters are typed. A `Keystrokes` command addresses a **window**; the control that receives the keys is the one the previous capture clicked or typed into ([source-migration-guide.md § Composite interactions](../source-migration-guide.md), keystrokes row).

## Pitfalls

1. **Enabled criteria are the only ones the bot matched on.** A capture with `Name` recorded but disabled and `Path` enabled ran positionally; translating the disabled `Name` into the selector changes the behaviour (usually for the better) but must be confirmed live before it counts as identity.
2. **`Path` first segments disagree between twins of one control** (`-1|1|2|…` from the Enterprise 11 recorder, `1|1|2|…` from the Automation 360 one). Neither is identity.
3. **Grid rows are same-named text fields.** `Name="Status"` with `Index=$var$` is not one control; it is the Status column. A UiPath target for "the Status cell of the current row" is a table pattern, not `idx`.
4. **Forms button names carry the mnemonic** (`OK ALT O`). The visible caption is `OK`; the accessible name is what the recorder saw. Match the recorded name; do not shorten it without a live check.
5. **Java dialogs are not Java.** The `Security Warning` shown by the Java runtime is a Win32 dialog (`#32770`) recorded with MSAA in some bots and a `SunAwtDialog` recorded with Java Access Bridge in others — two different windows in two technologies for the same user-visible prompt. Check both shapes live; scope each by its own class.
6. **Window titles change with the launcher.** The applet frame is `LARA*` under `jp2launcher.exe` in one bot and `java.exe` in another, `fulfillmentSCE` for the login frame, `*LARA1*` for a desktop launch; a title-only window variable (`path` empty) says nothing about the executable.
7. **WINDOW variables named `window-N-1-1-1-1` are migration-generated**; the suffix encodes the nesting of the v11 command, not an identity. Several variables with identical title / class / executable in one bot are one window.
8. **HTML captures of the launch page were made in three browsers** (IE `IEFrame`, Edge tab titles with and without ` - Microsoft Edge`). One page, one scope on `url`; the browser is a Configuration Question.
9. **A `LABEL` control type on the launch button** (`HTML Tag` `B` inside `div#btnLara/span/b`) is the caption leaf; the click belongs on the enclosing clickable element — take the tag from the live DOM ([selector-translation-guide.md](../selector-translation-guide.md) rule 14).
10. **Credential dialogs and identity-provider pages are login plumbing.** In a UiPath rebuild the mailbox is reached through a mail connection, not by typing into `login.microsoftonline.com`; carry these targets only when the genome keeps a browser login step.
