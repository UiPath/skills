---
confidence: high
---

# PDF — Invalid page range or page number

## Context

A page-oriented PDF activity (`Extract PDF Page Range`, `Export PDF Page As Image`) faults because the requested `Range` / page number is malformed or outside the document's page count. The file is fine; the page argument is the problem.

What this looks like — `Extract PDF Page Range` raises `UiPath.DocumentProcessing.Contracts.Extensions.InvalidPageRangeException` (from `PageRange.ParsePageRangePart` → `ValidationHelper.ParseRange`):

- `The input string '<value>' was not in a correct format.` — the `Range` string contains a non-numeric / unparseable part (e.g. `abc`, stray letters, wrong separators). Valid form is like `2-4`, `1,3,5`, or a single page.
- `Page range is incorrect.` — the `Range` is syntactically numeric but refers to pages outside the document (e.g. page `9` of a 1-page PDF, or a reversed/empty range).

Related signatures:
- `The provided page number is invalid` (`System.ArgumentException`, resx `InvalidPageNumberException`) — `Export PDF Page As Image` given an empty, non-numeric, or ≤ 0 page number.
- `The Range argument does not have a valid format` (resx `RangeFormatException`) — the activity-level / design-time range-format check (the runtime extraction path throws `InvalidPageRangeException` above; treat both as the same failure class).

What can cause it:
- **Malformed range string** — letters, wrong separators, spaces in unexpected places, or an upstream variable that produced garbage → `The input string '<value>' was not in a correct format.`
- **Out-of-bounds page** — the range is numeric but larger than the document's actual page count → `Page range is incorrect.`
- **Empty / non-numeric page number** (`Export PDF Page As Image`) → `The provided page number is invalid`.

What to look for:
- The exception **type is `InvalidPageRangeException`** for `Extract PDF Page Range`. `...not in a correct format` = the string is unparseable (fix the `Range` string). `Page range is incorrect.` = syntax is fine but the page doesn't exist in this document (fix the number or check the page count). The file opened successfully — this is not a missing/corrupt-file problem.

> **Different cause — do not apply this playbook:**
> - `Could not find file` / `does not have a .PDF extension` → the input path is wrong, use [pdf-file-not-found-or-not-pdf.md](./pdf-file-not-found-or-not-pdf.md).
> - `PdfException` → the file is encrypted/corrupt, use [pdf-encrypted-or-wrong-password.md](./pdf-encrypted-or-wrong-password.md) or [pdf-corrupt-or-image-input.md](./pdf-corrupt-or-image-input.md).

## Investigation

1. **Capture the `Range` / page-number argument value** at runtime and the exact message (`...not in a correct format` vs `Page range is incorrect.` vs `The provided page number is invalid`).
2. **For `...not in a correct format`**, check the string against the valid form (`2-4`, `1,3,5`, single page). Identify whether an upstream variable produced an unexpected value.
3. **For `Page range is incorrect.`**, get the document's actual page count (e.g. `Get PDF Page Count`) and compare to the requested range.

## Resolution

- **If `The input string '<value>' was not in a correct format.`:** correct the `Range` to a valid expression (e.g. `2-4` or `1,3,5`); with explicit user approval, fix the upstream expression that built it.
- **If `Page range is incorrect.`:** clamp the requested range to the document's page count; read the page count first (`Get PDF Page Count`) and bound the range against it.
- **If `The provided page number is invalid`:** set a positive integer page number on `Export PDF Page As Image`.
