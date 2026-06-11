---
confidence: medium
---

# File Operation Failed — Rename / Move / Append

## Context

A classic file-system activity (`Rename File`, `Move File`, or `Append Line`) faulted while acting on
a path. These activities run on the robot machine's file system and surface a file-system error.

What this looks like:
- "The source file does not exist." (`Rename File` / `Move File` — the source path is wrong or gone)
- "Destination should be a folder." (`Move File` — the destination must be a folder, but a file path
  was given)
- "File cannot be null" (an empty/unresolved path argument)
- Standard .NET I/O errors: file already exists at the destination, access denied
  (`UnauthorizedAccessException`), the path is a directory, the file is locked by another process, or
  the path is too long

What can cause it:
- The path is valid on the developer machine but does not exist on the robot machine (different
  drives, user folders, or mapped network drives)
- The source file was never created, or a previous step that should have produced it failed
- A path variable resolved to empty/null because an upstream assignment or input was missing
- The destination already contains a file with the same name and overwrite is not enabled
- The robot account lacks read/write permission on the folder, or the file is open/locked by another
  application
- For `Append Line`: an invalid encoding name, or the target file/folder is not writable

What to look for:
- The exact source and destination paths the activity resolved at run time (from logs/variables)
- Whether those paths exist and are reachable on the robot machine, with the right permissions
- Whether the destination is a folder (for `Move File`) vs a file path
- Whether the file is held open by another process

## Investigation

1. Identify the failing file activity and the exact paths it used at run time (resolve any variables
   from logs).
2. Check the error text to classify it: source missing, destination-not-a-folder, null path, already
   exists, access denied, or locked.
3. Verify the source path exists on the robot machine and the robot account can read it.
4. Verify the destination: for `Move File`, confirm it is a folder; check whether a same-named file
   already exists there.
5. Confirm the robot account has write permission to the destination folder and that the file is not
   open in another process.
6. If a path variable was empty, trace back to the upstream step/input that should have set it.

## Resolution

- **If the source file does not exist:** fix the source path, or fix the upstream step that should
  have created it; do not point the activity at a path that isn't there on the robot.
- **If the destination should be a folder:** give `Move File` a destination folder, not a file path.
- **If a path is null/empty:** ensure the upstream assignment/input that feeds the path is set.
- **If the destination already has the file:** enable overwrite if that is intended, or change the
  destination/name.
- **If access is denied:** grant the robot account read/write permission on the path.
- **If the file is locked:** ensure no other process (or earlier step) is holding it open before the
  operation.
