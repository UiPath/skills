---
confidence: high
---

# Write CSV — "Unsupported encoding name"

## Context

What this looks like:
- `Write CSV` faults with `'<value>' is not a supported encoding name` / `Unsupported encoding name '<value>'` (`System.ArgumentException`) from the `Encoding` property.

What can cause it:
- **The `Encoding` property is set to a string .NET does not recognize** — a typo, a made-up name, or a label that isn't a valid .NET encoding (e.g. `UTF8` written in a way the framework rejects, or `Unicode (UTF-8)` instead of the canonical name).

What to look for:
- The `Encoding` property value in the `.xaml`: is it a valid .NET encoding name?

## Investigation

1. Read the error from job evidence; confirm it is an unsupported-encoding `ArgumentException` at `Write CSV` (from the `Encoding` property), not a delimiter, access, or version error.
2. Read the `Write CSV` `Encoding` property from the `.xaml` and check it against valid .NET encoding names.

## Resolution

- **Use a valid .NET encoding name** in the `Encoding` property: e.g. `"UTF-8"`, `"utf-8"`, `"Windows-1252"`, `"us-ascii"`, `"utf-16"`. Match the name .NET's `Encoding.GetEncoding(name)` accepts.
- **If you don't need a specific encoding:** leave `Encoding` empty to use the activity default.
- **Bulletproof alternative:** if encoding handling on the activity keeps failing, convert the data yourself — **Output Data Table** (DataTable → string) then **Write Text File** (which lets you control encoding cleanly) to a `.csv` path.
