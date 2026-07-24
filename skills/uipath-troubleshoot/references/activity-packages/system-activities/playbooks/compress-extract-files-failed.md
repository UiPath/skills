---
confidence: medium
---

# Compress / Extract Files Failed — Archive Operation Errors

## Context

A `Compress/Zip Files` or `Extract/Unzip Files` activity (`UiPath.System.Activities`) faulted with a `CompressionException` while building or reading a `.zip` archive. Every branch below shares that one exception type — route on the message text, not the activity name alone.

> In a faulted Orchestrator job, an extract failure surfaces as the header `Extraction Failed` / `Check if the archive is corrupted or if you have write permissions to the destination` with `ErrorCode: System.Compression.Sys.ExtractFailed`; the underlying `CompressionException: Cannot extract data from archive "<path>"` is in the exception detail (a corrupt/truncated zip shows an inner `ICSharpCode.SharpZipLib.Zip.ZipException: Cannot find central directory`).

What this looks like — match on message text:
- `No files to compress.` — Compress: the input file/folder set resolved to nothing.
- `The file <path> exists but the override flag is set to false. Delete the file or set override flag to true to update archive.` — Compress: the output archive already exists and Overwrite is off.
- `<name> already exists in the compressed file.` — Compress: the same entry name was added twice.
- `The filename is required.` — Extract: the archive path input is empty/unresolved.
- `Cannot extract data from archive <path>.` — Compress or Extract: the archive is corrupt, truncated, password-protected, or not a real zip.
- `File <name> is compressed in an unsupported format. To extract all support files, set the Skip unsupported files setting to true.` — Extract: an entry uses a compression method the activity cannot read.
- `File <name> already exists in the output folder.` — Extract: an entry collides with an existing file and Overwrite is off.
- `Cannot extract file <name> because a folder with the same name already exists.` — Extract: an entry name collides with an existing folder in the output path.

What can cause it:
- Input path/glob resolves empty, or an upstream step that should have produced the files failed (empty compress).
- Output archive or extracted file already exists and the activity's Overwrite option is off.
- The archive is partially downloaded, renamed from a non-zip, encrypted, or written by a tool using an unsupported method.
- A duplicate entry name, or an output name that clashes with an existing file/folder on the robot filesystem.

What to look for:
- The exact `CompressionException` message and the archive + output paths the activity resolved at run time (from logs/variables).
- Which activity faulted (Compress vs Extract) and its Overwrite / "Skip unsupported files" settings.
- Whether the archive opens in a normal zip tool and its on-disk size is plausible (a few bytes / HTML body = a failed download, not a zip).

## Investigation

1. Capture the exact message and classify it against the list above; note the resolved archive and output paths.
2. Confirm the faulted activity (Compress vs Extract) and read its Overwrite and "Skip unsupported files" settings.
3. For any `Cannot extract data from archive` case, verify the file is a valid, complete zip — open it manually and check its size and true type; a truncated download or a renamed non-zip presents identically.
4. Trace an empty-input or null-path failure back to the upstream step/variable that should have supplied the files or the archive path.

## Resolution

Match the surfaced message to a branch.

### `No files to compress.`
The input collection/glob matched zero files. Fix the source path or the upstream step that should have produced the files; confirm the folder/filter resolves to at least one file at run time before the Compress step.

### `The file ... exists ... override flag is set to false` / `File ... already exists in the output folder.`
The target (archive on Compress, or an entry on Extract) already exists and Overwrite is off. Enable the activity's Overwrite option if replacing is intended, or delete/rename the existing target (or point at a clean output folder) before the operation.

### `... already exists in the compressed file.`
The same entry name was added twice to one archive. De-duplicate the input set so each entry name appears once.

### `The filename is required.`
The archive path input is empty. Set the archive/file path (ensure the upstream variable/argument that feeds it is populated).

### `Cannot extract data from archive ...`
The archive is unreadable — corrupt, truncated, encrypted, or not a real zip. Verify the file is a complete, valid, unencrypted zip; if it came from a download, re-fetch it and confirm the byte size matches the source before extracting. Do not raise timeouts or toggle Overwrite for this case — neither addresses a bad archive.

### `File ... is compressed in an unsupported format ...`
An entry uses a compression method the activity cannot decode. Set "Skip unsupported files" to true to extract the readable entries, or re-create the archive with a standard method (Deflate). Note this skips the offending entries — confirm the workflow does not require them.

### `Cannot extract file ... because a folder with the same name already exists.`
An entry name clashes with an existing folder in the output path. Remove or rename the conflicting folder, or extract to a clean output directory.
