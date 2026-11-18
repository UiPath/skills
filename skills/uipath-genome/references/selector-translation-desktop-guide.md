# Selector Translation — desktop

The desktop technologies' side of [selector-translation-guide.md](selector-translation-guide.md): what the rules add for UI Automation, Active Accessibility, Java, and the other desktop and remote tags. Read whole with that guide when the target catalog holds controls of these technologies, together with the attribute reference and reliability ranking of each of their tags in the UI Automation package's Selector Reference (that guide names where it is read): `uia` with its control types, `ctrl`, `java`, and the remaining tags. Rule numbers are that guide's.

## Rule 1 — desktop

**Chromium content through UI Automation carries no DOM attribute.** An Electron renderer window, browser chrome or a web view without the browser driver exposes the page's accessibility tree (the `uia` attribute reference): a locator built on DOM `class`, `data-*`, `name` or `type` attributes translates to role plus accessible name or to a no-selector outcome (rule 13), and whether `automationid` mirrors the DOM `id` is settled by the live attribute listing (rule 15), never assumed. Framework side: the framework pack's selectors guide, section for renderer windows reached through UI Automation.

**WPF and Silverlight.** A WPF recording translates to `uia`, through which UiPath normally surfaces WPF, unless the source recorded WPF-only properties (`x:Type`, `Uid`, `Header`, `Content`), which take `wpf`. `silverlight` is Silverlight plug-in content only: a source *engine* named Silverlight is not this.

## Rule 7 — desktop

On `java`, `virtualname` holds one of three things (the `java` attribute reference): a component name, which is identity (an application's own item identifiers); a neighbouring label's text, which is semantic and repeats across fields labelled alike; or a check box value, which is state and never in a target. The driver's default never uses it, so a default that ends in `idx` says nothing about it: read it in the attribute listing (rule 15), and where it holds a component name it replaces the index.

## Rule 8 — desktop

A cell of a Windows Forms list view (`SysListView32`) found by row content and column caption is `<uia role='text' rowName='{{Key}}' colName='<header caption>' />` under the list; what the list view exposes: the `uia` attribute reference. Under the list, the Find Elements filter `<uia role='text' />` in Find Descendants mode takes only the cells; searched from the window, it also takes the window's captions and those of the windows it owns (§ Rule 9), so a source that reads the cells in groups by position reads the wrong cell of every row, or overruns the collection.

## Rule 9 — desktop

**A window's UI Automation tree holds the windows it owns** (the `uia` attribute reference, owned windows), so a `uia` search from the owner's scope also matches in every open window it owns, and there first: a Find Elements with no Target in the owner's card returns the owned windows' matches ahead of the owner's, and a target under the owner's window selector resolves a control of an owned window, whatever the card's attach mode.
