---
confidence: medium
---

# Read CSV — "The CSV file format for [Path] is invalid"

## Context

What this looks like:
- `Read CSV` faults with `The CSV file format for <Path> is invalid` (or a similar "invalid format" message naming the file).
- The file opens fine in a text editor / Excel, so "the file is right, why is it invalid?"

What can cause it:
- **Blank initial lines.** One or more empty rows at the very top of the file shift the header detection — `Read CSV` expects the header (or first data row) at the top, and leading blank lines break the tabular structure.
- **`Has headers` mismatch.** `Add headers` / `Has headers` is checked but the file has **no** title row, so the first **data** row is consumed as the header definition — later rows then don't match the inferred schema. (Or the inverse: the file has a header row but `Has headers` is unchecked, so the titles are read as data.)
- **Not a tabular CSV.** The file is empty, a single blob, or otherwise lacks consistent rows/columns.

What to look for:
- Leading empty lines at the top of the file (open in a plain text editor — Notepad — not Excel, which hides them).
- Whether the file actually has a header/title row, and whether the activity's `Has headers` / `Add headers` setting agrees with it.

## Investigation

1. Read the error from job evidence; confirm it is `The CSV file format ... is invalid` at `Read CSV` (not a parse "more values than header" or a file-not-found error).
2. Open the file in a plain text editor and check the **first few lines**: leading blank lines? a real header row, or data straight away?
3. Read the `Read CSV` activity's `Has headers` (a.k.a. `Add headers`) property and compare it to the file's actual first row.

## Resolution

- **If there are blank initial lines:** strip the leading empty rows from the file (e.g. open in Notepad, delete the blank lines at the top) so the header/first row is at line 1. If the source produces them, trim them up front — read with **Read Text File**, remove leading newlines with string activities, write back (or feed to **Generate Data Table**).
- **If the file has no header row but `Has headers` is checked:** uncheck `Has headers` so the first data row is not consumed as column titles.
- **If the file has a header row but `Has headers` is unchecked:** check `Has headers` so the titles are treated as the header, not data.
- **If the file is empty / non-tabular:** validate it exists with content and a consistent structure before reading (guard with a `File Exists` + size/row check).
