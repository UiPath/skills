---
confidence: medium
---

# Read CSV — "Could not find file" / "Could not find a part of the path"

## Context

What this looks like:
- `Read CSV` faults with `Could not find file '<path>'` (`System.IO.FileNotFoundException`) or `Could not find a part of the path '<path>'` (`System.IO.DirectoryNotFoundException`).
- The path *looks* right, and the file may even exist when you check manually afterward.

What can cause it:
- **Asynchronous download timing.** A preceding step downloads / generates the CSV (HTTP download, an export, a cloud sync), and `Read CSV` runs before the file is fully written to disk — so at read time the file isn't there yet.
- **Path variable wrapped in quotes.** The `FilePath` expression quotes the variable *name* (e.g. `"MyPathVar"`) instead of using the variable, so the literal string `MyPathVar` is treated as the path — which doesn't exist. Or a hard-coded path has a typo / wrong folder.
- **Relative path / working-directory drift.** A relative path resolves against the robot's working directory, not where the file actually is, so a part of the path is missing.

What to look for:
- Whether a download/export/sync step runs immediately before `Read CSV` (timing/race).
- The `FilePath` expression in the `.xaml`: is the variable quoted as a literal string? Is the path relative? Does the folder portion exist?
- Whether the failure is intermittent (points at a timing race) or every run (points at a wrong/quoted path).

## Investigation

1. Read the error and the resolved path from job evidence; confirm it is `Could not find file` / `Could not find a part of the path` at `Read CSV`.
2. Read the `Read CSV` `FilePath` expression from the `.xaml`: is it a bare variable, a quoted literal, a relative path? Does the directory portion exist on the host?
3. Check what runs immediately before the read — a download/export/sync — and whether failures are intermittent (race) vs every run (bad path).

## Resolution

- **If the file is produced just before the read (race):** insert a wait before `Read CSV` — a `File Exists` retry loop (poll until the file is present, with a timeout), or a brief `Delay`. Prefer the retry loop over a fixed delay so it is robust to variable download times.
- **If the path variable is quoted as a literal:** pass the variable itself, not its name in quotes — use `MyPathVar`, not `"MyPathVar"`, in the `FilePath` expression.
- **If the path is wrong / relative:** use a correct absolute path (or build it explicitly, e.g. with `Path.Combine`) so the directory portion resolves on the robot host.
- **General:** guard the read with a `File Exists` check and fail with a clear message when the file is genuinely absent, so a timing race is distinguishable from a wrong path.
