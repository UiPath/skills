---
confidence: medium
---

# File & Folder Operation Failed — Modern File Activities (Copy / Move / Rename / Delete Folder, Delete File, Create Folder)

## Context

A modern StudioX file-system activity (`Copy Folder`, `Move Folder`, `Rename Folder`, `Copy File`, `Rename File`, `Delete File`, `Delete Folder`, `Create Folder`) from `UiPath.System.Activities` faulted. **Folder** activities throw a `FileSystemException` with the messages below; **file** activities (`Copy File`, `Rename File`) are thin wrappers that surface the raw `System.IO` exception (`IOException`, `DirectoryNotFoundException`); an unresolved path throws `ArgumentNullException`. These run on the robot machine's filesystem and route on the message text below.

> For the **classic** `Rename File` / `Move File` / `Append Line` activities (`UiPath.Core.Activities`, different message wording), use [classic-activities/file-operation-failed.md](../../classic-activities/playbooks/file-operation-failed.md). This playbook covers the modern StudioX File/Folder activities only.

What this looks like:
- `File path is missing. Provide either a file path or a file resource.` / `Folder path is missing. Provide either a folder path or a folder resource.` / `No file path could be resolved. ...` / `No folder path could be resolved. ...` / `File cannot be null` / `ArgumentNullException` on `FilePath` — the path input is empty/unresolved.
- `Source file does not exist` / `Source folder is missing.` / `Source or destination folder missing.` / `The file was not found at the provided path. Verify that the path is correct.` / `The folder was not found at the provided path. Verify that the path is correct.` — the source path does not exist on the robot machine.
- `The provided path points to a file, not a folder. Provide a valid folder path.` / `File resource should not be a folder` — the path exists but is the wrong type for the activity.
- `System.IO.IOException: The file '<path>' already exists.` — a `Copy File` target already exists and Overwrite is off (the raw .NET message from `System.IO.FileSystem.CopyFile`, not a UiPath-wrapped one). A missing destination directory surfaces as `System.IO.DirectoryNotFoundException`.
- `Destination folder should not be the parent of source folder.` / `To directory is a child of From directory` — an illegal Copy/Move Folder nesting (destination inside source, or vice-versa).
- `Cannot create a file with the same name as an existing directory` (`UnauthorizedAccessException`, from Write/Read Text File) — a file write targets a path already used by a folder.
- `Failed to copy folder from path <a> to path <b>.` / `Move folder exception` / `Rename folder exception` — a generic wrapper around an inner .NET IO error (access denied, file locked, path too long).

What can cause it:
- A path variable resolved to empty/null because an upstream assignment or input was missing.
- The path is valid on the developer machine but absent on the robot (different drives, user folders, unmapped network shares).
- The activity was pointed at a file where a folder is expected (or vice-versa), or at a Copy/Move Folder target nested inside the source.
- A same-named target already exists and Overwrite is off; or the robot account lacks permission / the file is locked (surfaced through the generic wrappers).

What to look for:
- The exact message and the source + destination paths the activity resolved at run time (from logs/variables).
- Whether those paths exist, are the right type (file vs folder), and are reachable with the right permissions on the robot machine.
- For the generic `Failed to ... / ... exception` wrappers, the inner exception in the trace — that carries the real IO cause.

## Investigation

1. Capture the message and classify it: missing/null path, source-not-found, wrong-type, destination-exists, illegal-nesting, name-clashes-with-directory, or generic-wrapper.
2. Resolve the actual source/destination paths at run time from logs, and confirm each exists and is the expected type on the robot machine.
3. For a generic `Failed to copy folder` / `Move folder exception` / `Rename folder exception`, open the inner exception in the trace to get the underlying IO cause (permission, lock, path length).
4. If a path was empty/null, trace back to the upstream step or input that should have set it.

## Resolution

### Missing / null path
Set the path input, and ensure the upstream assignment/argument that feeds it is populated before the activity runs.

### Source not found
Fix the source path, or fix the upstream step that should have produced it; do not point the activity at a path absent on the robot. Confirm network shares are mapped and reachable under the robot account.

### Wrong path type (file vs folder)
Give the activity the correct kind of path — a folder path for the folder activities, a file path for the file activities.

### Destination already exists (`IOException: The file '<path>' already exists.`)
Enable the activity's Overwrite option if replacing is intended, or change the destination name/folder so it does not collide.

### Illegal Copy/Move Folder nesting
Choose a destination that is not the parent of, or a child of, the source folder.

### `Cannot create a file with the same name as an existing directory`
A folder already occupies the target path — write to a different file path, or remove/rename the conflicting directory.

### Generic wrapper (`Failed to copy folder` / `Move folder exception` / `Rename folder exception`)
Read the inner exception and fix the underlying IO cause: grant the robot account read/write on the path, release the process holding the file open, or shorten an over-long path.
