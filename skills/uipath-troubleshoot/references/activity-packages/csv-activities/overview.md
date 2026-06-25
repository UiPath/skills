# CSV Activities

The CSV file activities — **Read CSV** (`ReadCsvFile`), **Write CSV** (`WriteCsvFile`), and **Append To CSV** (`AppendToCsvFile`), all under the `UiPath.Core.Activities` namespace and shipped in the **`UiPath.System.Activities`** package — read and write delimited text files to/from a `DataTable`. They run in-process against a **local file path** (no COM, no Office); the underlying (de)serialization is done by the bundled **`CsvHelper`** library.

## How CSV Activities Execute

1. Resolve the file `Path` (a local filesystem path) and open it for read / write / append.
2. Use `CsvHelper` to map between CSV rows and a `DataTable`: `Read CSV` returns a `DataTable`; `Write CSV` overwrites the file from a `DataTable`; `Append To CSV` adds the `DataTable`'s rows to the end of an existing file.
3. Honor options: `Delimiter`, `IncludeColumnNames` / `AddHeaders`, `Encoding`.

Failures originate at distinct layers — **package/dependency load** (the bundled `CsvHelper` version, before any row is written), **file access** (path resolution, locks, cloud paths), or **data shape** (the `DataTable` passed in vs the file's columns). Knowing which layer produced the error narrows the investigation.

## Key Activities

- **Read CSV** (`UiPath.Core.Activities.ReadCsvFile`, "Read CSV") — read a delimited file into a `DataTable` (`Path` in, `DataTable` out).
- **Write CSV** (`UiPath.Core.Activities.WriteCsvFile`, "Write CSV") — overwrite a file from a `DataTable` (`Path`, `DataTable`).
- **Append To CSV** (`UiPath.Core.Activities.AppendToCsvFile`, "Append To CSV") — append a `DataTable`'s rows to an existing file (`Path`, `DataTable`). **Local files only.**

## Common Failure Patterns

- **`Method not found: 'Void CsvHelper.CsvWriter..ctor(...)'` (or similar `CsvHelper...` member)** — a **`CsvHelper` version conflict**. `CsvHelper.dll` is bundled in **both** `UiPath.System.Activities` and `UiPath.Excel.Activities`; when those two packages are at versions that bundle incompatible `CsvHelper` builds, the CSV activity binds the wrong assembly at runtime/compile and throws `Method not found`. Fix by aligning the two packages (upgrade both to current stable). See `csv-helper-method-not-found.md`.
- **`The process cannot access the file because it is being used by another process` / `The filename, directory name, or volume label syntax is incorrect`** — file **locked** (the CSV is open in Microsoft Excel or held by another session/job) or an **invalid / cloud path** (CSV activities operate on local files; a raw `https://...` SharePoint/OneDrive URL is not a valid local path). See `csv-file-locked-or-invalid-path.md`.
- **Mismatched columns / rows fail to write** — a **`DataTable` shape problem**: an uninitialized `DataTable` variable, a column **count/header mismatch** between the incoming `DataTable` and the existing CSV, or mapping out-of-scope fields. See `csv-datatable-structure-mismatch.md`.

## Package

NuGet: `UiPath.System.Activities` (CSV file activities; underlying library: `CsvHelper`)

Namespaces: `UiPath.Core.Activities`

> The `CsvHelper` dependency is shared with `UiPath.Excel.Activities` — keep the two packages on aligned versions. Version-specific behavior is documented in the relevant playbooks.
