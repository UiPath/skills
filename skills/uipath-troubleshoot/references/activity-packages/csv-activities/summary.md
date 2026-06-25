# CSV Activities Playbooks

**Overview:** [overview.md](./overview.md) — CSV file activities (`Read CSV` / `Write CSV` / `Append To CSV`) in `UiPath.System.Activities`, the bundled `CsvHelper` dependency, and common failure patterns

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Append/Write CSV — "Method not found: 'CsvHelper...'" | High | `CsvHelper` version conflict: the library is bundled in **both** `UiPath.System.Activities` and `UiPath.Excel.Activities`; mismatched package versions bind an incompatible `CsvHelper` and the activity throws `Method not found`. Fix: align both packages (upgrade to current stable) | [csv-helper-method-not-found.md](./playbooks/csv-helper-method-not-found.md) |
| Append/Write CSV — file locked or invalid / cloud path | Medium | `The process cannot access the file because it is being used by another process` (CSV open in Excel / held by another job) or `The filename, directory name, or volume label syntax is incorrect` (a raw `https://` SharePoint/OneDrive path — CSV activities are local-file only). Fix: close/kill the lock holder; for cloud, download local → append → upload via Microsoft 365 activities | [csv-file-locked-or-invalid-path.md](./playbooks/csv-file-locked-or-invalid-path.md) |
| Append/Write CSV — DataTable structure / null mismatch | Medium | Mismatched columns or rows fail to write: an uninitialized `DataTable`, a column count/header mismatch vs the existing CSV, or mapping out-of-scope fields. Fix: instantiate the `DataTable` (Build Data Table with matching headers) before the Add Data Row loop; align column structure | [csv-datatable-structure-mismatch.md](./playbooks/csv-datatable-structure-mismatch.md) |
