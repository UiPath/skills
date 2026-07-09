---
confidence: medium
---

# Replace Text in Document — Multi-line Replacement Loses Formatting / Collapses to One Line

## Context

What this looks like:
- Activity `Replace Text in Document` / `Replace Text` completes, but the replacement text **loses its formatting** or **wraps into a single line** instead of preserving the intended paragraph breaks
- The `Search` placeholder is replaced, but the multi-line/styled result does not render as expected

What can cause it:
- The `Replace` value is a **raw string containing standard environment line breaks** (`Environment.NewLine` / `\r\n`). The activity inserts the text as a flat run, so OS line breaks do not become proper Word paragraph breaks and any intended formatting is dropped.

What to look for:
- Whether the `Replace` expression embeds `Environment.NewLine` / `vbCrLf` / `\n` to build multi-line content.
- Whether the expected output is rich/multi-paragraph (styled) rather than a simple token swap.

## Investigation

1. Read the `Replace` expression. Confirm it carries line breaks or formatting intent (multi-paragraph text), not a simple single-line value.
2. Confirm the symptom is layout/formatting (collapsed lines, lost styling), not a missing replacement.

## Resolution

- **Keep replacement strings simple** — use `Replace Text` only for plain, single-line token swaps. Avoid passing `Environment.NewLine`-laden strings and expecting Word paragraph formatting.
- **For complex multi-line / styled content** — do not use `Replace Text`. Use **Bookmarks or Form Fields** with the `Set Bookmark Text` activity (preserves the bookmark's formatting), or a copy-paste simulation approach when preserving nested multi-line paragraphs is mandatory.
- **If you must inject paragraphs via Replace** — split the content and insert paragraph breaks through the Word object model rather than relying on raw `Environment.NewLine` in the `Replace` field.

> For long replacement text that hits the 256-character input cap (a different failure), see [replace-text-length-limit.md](./replace-text-length-limit.md) — the Bookmarks / Form Fields path applies there too.
