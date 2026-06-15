---
confidence: high
---

# Replace Text in Document — Input String Length Limit (256 Characters)

## Context

What this looks like:
- Activity `Replace Text in Document` / `Replace Text` faults or silently truncates when the `Search` or `Replace` value is long
- Error message is an `ArgumentException`, or there is no error but the written value is **cut off** at 256 characters

What can cause it:
- Classic versions of the activity enforce a **hard 256-character limit** on both the `Search for` and `Replace with` input fields. A value over 256 characters raises `ArgumentException` or is truncated.

What to look for:
- The length of the `Replace` (and `Search`) expressions at runtime — over 256 characters is the trigger.
- The `UiPath.Word.Activities` package version (the limit is a classic-version constraint).

## Investigation

1. Read the `Replace Text in Document` node and evaluate the actual length of the `Search` and `Replace` values for the failing run. Confirm one exceeds 256 characters.
2. Check the `UiPath.Word.Activities` version in `project.json` — the 256-char limit is present in classic/older versions and relaxed in current ones.

## Resolution

- **If the replacement text exceeds 256 characters** — update the `UiPath.Word.Activities` dependency to the latest version (the limit is relaxed in current releases), then rebuild.
- **If you cannot upgrade the package** — do the substitution in code instead: read the document text into a `String`, replace with `myString.Replace(...)` / regex in an `Assign`, and write the result back, which has no 256-character cap.
- **If the value is being truncated silently** — same fix; verify the output document content after the write rather than trusting a no-error run.
