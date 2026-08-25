---
confidence: medium
---

# Replace Text in Document — Headers, Footers, and Text Boxes Not Replaced

## Context

What this looks like:
- Activity `Replace Text in Document` / `Replace Text` finishes **without error**, but text inside **headers, footers, or floating text boxes / shapes** is left unchanged — only the main body got the substitution
- Placeholders in the body are replaced correctly; the same placeholder in a header or text box survives

What can cause it:
- **Older versions of `UiPath.Word.Activities`** scan only the primary body text. Content stored in header/footer story ranges or in floating shapes (text boxes) is outside the scanned range, so those placeholders are never matched.

What to look for:
- Where the surviving placeholder lives (header / footer / text box vs body).
- The `UiPath.Word.Activities` version in `project.json`.

## Investigation

1. Confirm the unreplaced placeholder is in a **header, footer, or text box / shape**, while body placeholders did replace — that locates the gap to non-body story ranges.
2. Check the `UiPath.Word.Activities` version in `project.json` against the latest release.

## Resolution

- **Update the package** — open `Manage Packages` in Studio and update `UiPath.Word.Activities` to the latest version, then rebuild. Newer versions natively replace inside headers, footers, and text shapes.
- **If you cannot upgrade** — substitute the header/footer/text-box content explicitly (e.g. address the header story range directly, or move the placeholder into the body), or do the replacement in code over the document XML, which covers all story ranges.

> This is a silent miss — the activity throws nothing. Trace the **output document content** (including headers/footers/text boxes), not just the absence of an exception. For a body-text silent miss caused by run-splitting rather than the package version, see [replace-text-silent-no-substitution.md](./replace-text-silent-no-substitution.md).
