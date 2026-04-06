# UI Automation

Activities for interacting with desktop and web application UIs. Robots use selectors (XML descriptors of UI elements) to find and interact with buttons, text fields, tables, and other controls.

## How Selectors Work

A selector is an XML string that describes the path from the application window to the target UI element:

```xml
<html app='chrome.exe' title='Invoice Portal' />
<webctrl tag='BUTTON' aaname='Submit Invoice' />
```

When a robot executes a UI activity (Click, Type Into, Get Text, etc.), it uses the selector to locate the element in the live UI tree. If the element can't be found — because the UI changed, the element was renamed, or the layout shifted — the activity throws a `SelectorNotFoundException`.

## Key Activity Types

- **Click / NClick** — click a UI element
- **Type Into / NTypeInto** — type text into an input field
- **Get Text / NGetText** — extract text from a UI element
- **Set Text** — set the value of an input field
- **Check App State** — wait for a UI element to appear or disappear
- **Element Exists** — check if a UI element exists without interacting
- **Take Screenshot** — capture a screenshot of the application

## Exception Types

- **SelectorNotFoundException** — the selector didn't match any element in the UI tree. Most common failure.
- **UiElementNotFoundException** — UI element lookup failed (similar to selector not found, different internal path)
- **ElementNotInteractableException** — element was found but can't be clicked/typed into (hidden, disabled, covered by overlay)
- **NodeNotFoundException** — DOM or UI tree node missing
- **TimeoutException** — activity exceeded its wait time (ambiguous — could be UI or non-UI)
- **ImageOperationException** — image-based UI automation failure
- **ScreenScrapingException** — screen scraping activity failure

## Features

- **Healing Agent Data** — recovery data captured when HA is enabled and activities fail → [interpretations/healing-agent-data.md](./interpretations/healing-agent-data.md)
