---
confidence: medium
---

# GSuite — Invalid or null activity input (client-side validation)

## Context

This playbook covers errors thrown **inside the activity, before any Google API call is made**, because an input property is null, empty, out of range, or otherwise invalid. The root cause is always in the workflow itself — a variable that wasn't populated, an upstream activity that returned nothing, a hard-coded address that's wrong, or a property combination the activity rejects. The connection and the Google resource are irrelevant; do not investigate them.

What this looks like — any of the following messages:

- `Value cannot be null. (Parameter '<name>')` — a required input (`<name>` names it, e.g. `EmailId`, `range`, `spreadsheetId`, `SheetName`, `DataRow`) was null at runtime. (`Value cannot be null` with no parameter is the same error without a captured name.)
- `The object used in the activity does not exist.` — a `NullReferenceException` was mapped to this message: a `DataTable`, email object, range handle, or other object the activity dereferences was null. Commonly the output of a previous activity (a search that found nothing, a read that returned null) fed straight into this one.
- `Column not found: <name>` — a row/column operation referenced a column by name that doesn't exist in the range (header typo, or the read range didn't include that column).
- `Column index <i> is outside of the selected range <range>` — a column index is beyond the bounds of the range being iterated.
- `RelativeRowIndex <i> outside the range: 0 to <n>.` — `Write Row` (WriteMode = Overwrite) targeted a row position past the end of the range (range has rows `0..n`, position `<i>` exceeds it).
- `RelativeColumnIndex <i> outside the range: 0 to <n>.` — same, for column width: the data is wider than the overwrite range allows.
- `Named ranges with cell value are invalid. Named ranges require no cell input.` — `Write Cell` was given **both** a named range *and* a `Cell` value; a named range already defines the target, so `Cell` must be empty.
- `The provided data table does not have any columns.` — an empty `DataTable` (zero columns) was passed to a write activity.
- `<property> must be a positive number` — a count property (e.g. `MaxResults` on legacy `GetMailMessages`) was set to 0 or negative.
- `You do not have the following labels` — a Gmail activity referenced one or more label names that don't exist in the account (followed by the offending label names).
- `Cannot iterate over the QuickHandle item.` — the result of a `For Each Row` was used in an operation that needs a valid current-row handle but received an incompatible object.
- `The selected folder does not exist.` — legacy local-OAuth datastore: the configured credential-storage `Folder` path is missing on the robot machine.

The job faults synchronously the instant the activity validates the input; there is no API round-trip, no retry.

What activities can produce these errors:
Any activity with the relevant input. Null/`Value cannot be null` and `The object used in the activity does not exist.` are universal (every activity has required inputs). The range/row/column messages come from Sheets activities (`WriteRangeConnections`, `WriteCellConnections`, `WriteRowConnections`, `WriteColumnConnections`, `ReadRange(Connections)`, `ForEachRowConnections`, and their legacy equivalents). `<property> must be a positive number` and `You do not have the following labels` come from Gmail retrieval activities such as legacy `GetMailMessages`.

What can cause it:
- A workflow variable bound to the property was never assigned, or an expression evaluated to null/empty at runtime.
- The output of an upstream activity (a search with no match, a read that returned an empty result) was passed directly in without a null check.
- A hard-coded address is wrong: an out-of-bounds row/column position, a misspelled column name, a named range combined with a cell value.
- An empty or zero-column `DataTable` was built and passed to a write.
- A configuration value (`MaxResults`, a label name, a local datastore folder) is invalid for the environment.

> **Different cause — do not apply this playbook:**
> - **`Invalid data[0]: Unable to parse range: <Sheet>!<Cell>`** is a **server-side** Google 400 (the range reached Google and Google rejected its A1 syntax) — use [sheets-invalid-range.md](./sheets-invalid-range.md). The errors in *this* playbook are thrown before the call leaves the robot.
> - **`This action would increase the number of cells ...`** → [sheets-cell-limit-exceeded.md](./sheets-cell-limit-exceeded.md).
> - **`The resource was not found.`** / **`Cannot find item configured with connection ...`** (a target that doesn't resolve) → [drive-file-not-found.md](./drive-file-not-found.md).
> - 401/403/auth-timeout → [connection-and-auth-failures.md](./connection-and-auth-failures.md).

## Investigation

1. **Read the parameter name or value out of the message** — it names the offending input directly (`Parameter '<name>'`, the index in `outside the range`, the column in `Column not found`).
2. **Trace that input back to its source in the workflow** — is it a literal, a variable, or the output of a previous activity? Capture how it's assigned.
3. **If the input comes from an upstream activity,** check whether that activity could legitimately have returned null/empty (e.g. a search with no results) — that's the real fault to handle.
4. **For range/row/column bounds,** compare the configured index/position/width against the actual dimensions of the target range.

## Resolution

- **If a required input was null (`Value cannot be null` / `The object used in the activity does not exist.`):** Ensure the property is assigned before the activity runs. If it comes from an upstream activity that can return nothing, add a null/empty guard (If, or Try/Catch) and handle the empty case explicitly rather than feeding it forward.
- **If a row/column position or width is out of range (`RelativeRowIndex` / `RelativeColumnIndex` / `Column index ... outside`):** Correct the position/index to fall within the target range, or size the write data to the range. For `Write Row` Overwrite, the position must be `0..(range rows − 1)`.
- **If a column name is wrong (`Column not found`):** Fix the column name to match the read range's header, or widen the read range to include it.
- **If a named range was combined with a cell (`Named ranges with cell value are invalid`):** Clear the `Cell` input when using a named range.
- **If an empty DataTable was passed (`does not have any columns`):** Build the DataTable with its columns defined before writing.
- **If a count is non-positive (`must be a positive number`):** Set `MaxResults` (or the named property) to a value ≥ 1.
- **If labels don't exist (`You do not have the following labels`):** Correct the label names to match labels that exist in the Gmail account (labels are case-sensitive and user-defined).
- **If the local datastore folder is missing (`The selected folder does not exist.`):** Create the configured credential-storage folder on the robot machine or point the legacy scope at an existing path.
