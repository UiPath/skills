---
confidence: medium
---

# Download File from URL — Downloaded File Stuck as .tmp

## Context

What this looks like:
- `Download File from URL` reports success, but a **downstream step fails** because the saved file is a temporary file — e.g. `document.xlsx.tmp` instead of `document.xlsx` — so `Read Range` / `Read CSV` / a path check on the real name can't find it.

What can cause it:
- **The download/finalize raced.** The activity streams the body to a `*.tmp` file and then renames it to the final name; when downstream activities run before the network stream is fully flushed and the file is finalized, the path is still the `.tmp`. A slow/large transfer or an eager next step makes the workflow "move too fast" for the file system.

What to look for:
- Whether the immediate next step references the **final** file name/extension, and whether it intermittently finds a `*.tmp` instead.
- Whether the failure is intermittent (timing-dependent) rather than every run.

## Investigation

1. Read the error from job evidence; confirm the download "succeeded" but a later step fails resolving the target file, and that a `*.tmp` artifact is involved.
2. Read the `.xaml`: what consumes the downloaded file immediately after, and does it expect the final extension?
3. Confirm the failure is timing-dependent (intermittent), the signature of a finalize race rather than a wrong path.

## Resolution

- **Wrap the download in a Retry Scope (preferred):** put `Download File from URL` (or the consuming step) in a **Retry Scope** whose condition is a `File Exists` / `Path Exists` check on the **final** target path — i.e. validate the real extension is present and there is **no** `.tmp` — with a retry interval of ~5 seconds. This waits for the stream to finalize before proceeding.
- **Gate downstream steps on the final file:** before reading the file, poll `File Exists` for the exact target name (not `*.tmp`); only continue once the finalized file is present.
- **General:** never assume the file is ready the instant the activity returns — validate the finalized path/extension before consuming it.
