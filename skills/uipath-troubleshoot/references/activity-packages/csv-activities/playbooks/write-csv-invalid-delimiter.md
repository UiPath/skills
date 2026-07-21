---
confidence: high
---

# Write CSV — "Failed to create a 'Delimitator' from the text '...'"

## Context

What this looks like:
- `Write CSV` (or another CSV activity) faults with `Failed to create a 'Delimitator' from the text '<value>'` — e.g. `... from the text 'Tab'`.

What can cause it:
- **The `Delimiter` property is set from a string / localized name** instead of the activity's delimiter value. Passing the **word** `"Tab"`, `"Comma"`, or `"Pipe"` (or a localized label) into the `Delimiter` field gives the activity a value it cannot map to a real delimiter — it expects the enum selection or the actual character.

What to look for:
- The `Delimiter` property expression in the `.xaml`: is it a word like `"Tab"` / `"Comma"` / a `String` variable holding such a word, rather than the dropdown enum value or a character literal?

## Investigation

1. Read the error from job evidence; confirm it is `Failed to create a 'Delimitator' from the text '...'` at the CSV activity.
2. Read the activity's `Delimiter` property from the `.xaml`. Check whether it is bound to a string/word (`"Tab"`, `"Comma"`, `"Pipe"`) or a variable holding one, rather than the enum value.

## Resolution

- **Use the Properties-panel dropdown:** select the delimiter (`Tab` / `Comma` / `Semicolon` / `Space`) from the activity's `Delimiter` drop-down rather than typing a string. This sets the correct enum value.
- **If configuring via an expression:** pass the **actual character literal**, not the name — e.g. `vbTab` (or `"\t"`), `","`, `"|"`, `";"` — not `"Tab"` / `"Comma"` / `"Pipe"`.
- **If the delimiter is data-driven:** map the incoming string to the correct enum/character in code before assigning it, so the activity never receives a localized word.
