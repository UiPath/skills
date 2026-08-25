# File Operations Activities

Modern **System > File** activities under the `UiPath.Activities.System.FileOperations` namespace, shipped in the **`UiPath.System.Activities`** package. This package currently documents **Download File from URL** (`DownloadFileFromUrl`) — an activity that downloads a file from an HTTP(S) URL to the robot's local file system.

## Download File from URL — execution model

`DownloadFileFromUrl` (`UiPath.Activities.System.FileOperations.DownloadFileFromUrl`, display "Download File from URL", category **System > File**):

1. Opens an HTTP(S) connection to `Url` and waits up to `Timeout` seconds (default **600**) for the server to **begin** streaming the response (the timeout covers the start of the response, not the total transfer).
2. Streams the body to a temporary file on disk, then finalizes it to the target name (`FileName`, or the URL's original file name) in the robot's working directory by default.
3. Applies `ConflictResolution` (`FileConflictBehavior` — `Rename` (default) / `Replace` / `Skip`) when a file of that name already exists.
4. Returns the saved file as `ResponseAttachment` (`ILocalResource`).

It performs a **native HTTP download** — it does **not** carry cookies, a browser session, or interactive authentication state. Key properties: `Url`, `FileName` ("Save file as"), `ConflictResolution`, `Timeout`, `UserAgentHeader`.

Failures originate at distinct layers — **HTTP/auth** (server rejects the request: 401/403), **DNS/network** (host can't be resolved / blocked by firewall or SSL inspection), **client lifecycle** (reusing the activity's HTTP client across a loop), or **file finalization** (the download races and the file is left as a `.tmp`). Knowing which layer produced the error narrows the investigation.

## Common Failure Patterns

- **`This instance has already started one or more requests ...`** — the activity's internal HTTP client is reused/disposed improperly when `DownloadFileFromUrl` runs **inside a `For Each` loop** downloading multiple files. See `download-file-httpclient-reused-in-loop.md`.
- **HTTP `403 (Forbidden)` / `401 (Unauthorized)`** — the server rejects the native download because it requires authentication / cookies / a browser session that the activity does not carry (or a missing/!blocked `User-Agent`). See `download-file-403-401-auth.md`.
- **Downloaded file stuck as `.tmp`** — the activity finishes but downstream steps fail because the saved file is left as a temporary `*.tmp` (the stream/finalize raced). See `download-file-stuck-tmp.md`.
- **`Don't know about such a host` / name resolution failure** — DNS cannot resolve the host, or an enterprise firewall / SSL-inspection proxy blocks the automated outbound connection. See `download-file-host-not-found.md`.

## Package

NuGet: `UiPath.System.Activities`

Namespaces: `UiPath.Activities.System.FileOperations`

Version-specific behavior is documented in the relevant playbooks.
