# CSV Activities

The CSV file activities — **Read CSV** (`ReadCsvFile`), **Write CSV** (`AppendWriteCsvFile`), and **Append To CSV** (`AppendCsvFile`), all under the `UiPath.CSV.Activities` namespace and shipped in the **`UiPath.Excel.Activities`** package — read and write delimited text files to/from a `DataTable`. They run in-process against a **local file path** (no COM, no Office); the underlying (de)serialization is done by the bundled **`CsvHelper`** library.

## How CSV Activities Execute

1. Resolve the file `Path` (a local filesystem path) and open it for read / write / append.
2. Use `CsvHelper` to map between CSV rows and a `DataTable`: `Read CSV` returns a `DataTable`; `Write CSV` writes (replaces) or appends to the file from a `DataTable` per its `CsvAction`; `Append To CSV` adds the `DataTable`'s rows to the end of an existing file.
3. Honor options: `Delimiter`, `IncludeColumnNames` / `AddHeaders`, `Encoding`.

Failures originate at distinct layers — **package/dependency load** (the bundled `CsvHelper` version, before any row is written), **file access** (path resolution, locks, cloud paths), or **data shape** (the `DataTable` passed in vs the file's columns). Knowing which layer produced the error narrows the investigation.

## Key Activities

- **Read CSV** (`UiPath.CSV.Activities.ReadCsvFile`, "Read CSV") — read a delimited file into a `DataTable` (`FilePath` in, `DataTable` out).
- **Write CSV** (`UiPath.CSV.Activities.AppendWriteCsvFile` and `UiPath.CSV.Activities.WriteCsvFile`, both "Write CSV") — write a `DataTable` to a file (`FilePath`, `DataTable`); `AppendWriteCsvFile` writes or appends per its `CsvAction`.
- **Append To CSV** (`UiPath.CSV.Activities.AppendCsvFile`, "Append To CSV") — append a `DataTable`'s rows to an existing file (`FilePath`, `DataTable`). **Local files only.**

## Common Failure Patterns

- **`Method not found: 'Void CsvHelper.CsvWriter..ctor(...)'` (or similar `CsvHelper...` member)** — a **`CsvHelper` version conflict**. `CsvHelper.dll` is bundled in **both** `UiPath.System.Activities` and `UiPath.Excel.Activities`; when those two packages are at versions that bundle incompatible `CsvHelper` builds, the CSV activity binds the wrong assembly at runtime/compile and throws `Method not found`. Fix by aligning the two packages (upgrade both to current stable). See `csv-helper-method-not-found.md`.
- **`The process cannot access the file because it is being used by another process` / `The filename, directory name, or volume label syntax is incorrect`** — file **locked** (the CSV is open in Microsoft Excel or held by another session/job) or an **invalid / cloud path** (CSV activities operate on local files; a raw `https://...` SharePoint/OneDrive URL is not a valid local path). See `csv-file-locked-or-invalid-path.md`.
- **Mismatched columns / rows fail to write** — a **`DataTable` shape problem**: an uninitialized `DataTable` variable, a column **count/header mismatch** between the incoming `DataTable` and the existing CSV, or mapping out-of-scope fields. See `csv-datatable-structure-mismatch.md`.
- **`Read CSV`: `Line X contains more values than the header line`** — a **parse mismatch**: the `Delimiter` property doesn't match the file, or a field contains the delimiter unquoted. See `read-csv-more-values-than-header.md`.
- **`Read CSV`: `The CSV file format for <Path> is invalid`** — **leading blank lines** at the top of the file, or a `Has headers` setting that disagrees with the file's first row. See `read-csv-invalid-format.md`.
- **`Read CSV`: `Could not find file` / `Could not find a part of the path`** — the path is broken or **evaluated too early** (async download not yet written), a path variable quoted as a literal, or a relative path resolving wrong. See `read-csv-file-not-found.md`.
- **`Write CSV`: `Cannot set unknown member`** — **package version skew** between the build machine and the robot/runtime; a property in the XAML doesn't exist in the runtime activity's version. See `write-csv-cannot-set-unknown-member.md`.
- **`Write CSV`: `Failed to create a 'Delimitator' from the text '...'`** — the `Delimiter` is a **string/localized name** (`"Tab"`) instead of the enum value or character literal. See `write-csv-invalid-delimiter.md`.
- **`Write CSV`: `Access to the path is denied`** — **permissions / read-only / open-in-Excel** on the output (`UnauthorizedAccessException`). See `write-csv-access-denied.md`.
- **`Write CSV`: `Unsupported encoding name`** — the `Encoding` property is an invalid .NET encoding name. See `write-csv-unsupported-encoding.md`.

## Package

NuGet: `UiPath.Excel.Activities` (CSV file activities; underlying library: `CsvHelper`)

Namespaces: `UiPath.CSV.Activities`

> The `CsvHelper` dependency is shared with `UiPath.System.Activities` — keep the two packages on aligned versions. Version-specific behavior is documented in the relevant playbooks.
