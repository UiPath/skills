# Final Resolution

**Fault:** The `MonthlyReporting` job (folder Shared, host MOCK-HOST) ended **Faulted**. The fault is raised by a **`UiPath.PDF.Activities` Extract PDF Page Range** activity ("Extract document pages") and surfaces as `UiPath.DocumentProcessing.Contracts.Extensions.InvalidPageRangeException`.

**Root cause:** The PDF opened successfully, but the activity's **`Range` argument is malformed** and could not be parsed into a page range. The actionable signature is `The input string 'abc' was not in a correct format.`, thrown from `PageRange.ParsePageRangePart` via `ValidationHelper.ParseRange`. The configured `Range` (`abc`) is not a valid page-range expression (valid forms are like `2-4`, `1,3,5`, or a single page number) — most often an upstream variable produced a non-numeric value.

**Fix:** Correct the **`Range`** argument on the Extract PDF Page Range activity to a valid page-range expression (e.g. `2-4` or `1,3,5`). If the value comes from an upstream variable (e.g. a config cell or a prior read), fix the expression that produced the non-numeric string.

**Must NOT attribute the root cause to:**
- A **missing or wrong input file** — that would be `System.IO.FileNotFoundException: Could not find file ...`; here the file opened and only the `Range` failed to parse.
- The **PDF content / encryption / corruption** — the exception is `InvalidPageRangeException` (an argument-parse failure), not a `UiPath.PDF.PdfException`.
- An **out-of-bounds page** — that would surface as `Page range is incorrect.`; this message is specifically the format-parse failure (`The input string 'abc' was not in a correct format.`).
- A **missing OCR engine**, a **connection/Orchestrator** problem, or a **workflow-logic / null-variable** bug unrelated to the `Range` argument.

A correct answer identifies that **Extract PDF Page Range could not parse its `Range` argument (`InvalidPageRangeException: The input string 'abc' was not in a correct format.`)**, and recommends correcting the `Range` to a valid page-range expression. It must read the invalid-page-range signature rather than blaming the file, the PDF content, or the workflow logic.
