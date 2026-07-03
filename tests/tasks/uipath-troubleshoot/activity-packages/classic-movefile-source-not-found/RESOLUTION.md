# Final Resolution

Investigation complete. Here is the resolution:

---

**Root Cause:** The classic **Move File** activity in the **Legacy** process points at a hardcoded source path that does not exist on the robot machine, so the job faulted the moment that activity ran.

**What went wrong:** Job `f32f9829-4465-49a2-8e3e-0cc182a020c4` (process **Legacy**, folder **Shared**) faulted with `System.IO.FileNotFoundException` because **Move File** was told to move `C:\UiPathDemo\DoesNotExist\source.txt`, which is absent on machine **MOCK-HOST**.

**Why:** `move.xaml` (the job's entry point) is a single `move` sequence whose only activity is **Move File** (line 61), with two hardcoded string literals: `Path="C:\UiPathDemo\DoesNotExist\source.txt"` and `Destination="C:\UiPathDemo\Destination\source.txt"`, `Overwrite="False"`. The path is a literal — no variable resolves it — so the run-time source path equals the design-time value. On the robot machine the source file, its parent folder `C:\UiPathDemo\DoesNotExist\`, the destination folder `C:\UiPathDemo\Destination\`, and even the base `C:\UiPathDemo\` tree are all absent. No earlier activity in the workflow creates or downloads the source file (the sequence has no upstream producer). `System.IO.File.Move` therefore could not find the source and raised `FileNotFoundException`, faulting the job about 1.3 seconds after it started (Running 12:57:51.810Z → Faulted 12:57:53.120Z). This is the file-operation-failed playbook's "source file does not exist" cause — the source path is simply wrong/non-existent on the robot, not a transient lock, permission, or destination issue.

**Evidence:**

### Classic Activities (Root Cause)
- Faulting activity: **Move File** (`UiPath.Core.Activities.MoveFile`), `IdRef` MoveFile_1, in `move.xaml` line 61, inside the `move` sequence.
- Exact attributes (verbatim from source): `Path="C:\UiPathDemo\DoesNotExist\source.txt"`, `Destination="C:\UiPathDemo\Destination\source.txt"`, `Overwrite="False"`, `ContinueOnError="False"`.
- Exception (from job Info and Error log): `System.IO.FileNotFoundException: Could not find file 'C:\UiPathDemo\DoesNotExist\source.txt'.` Stack: `UiPath.Core.Activities.MoveFile.ExecuteAsync` → `System.IO.File.Move` → `File.InternalMove` → `WinIOError`.
- Filesystem check on robot machine **MOCK-HOST** (same host as the job's `HostMachineName`, same account `UIPATH\user1`, incident today so the snapshot is causally relevant): source file ABSENT, `C:\UiPathDemo\DoesNotExist\` ABSENT, `C:\UiPathDemo\Destination\` ABSENT, base `C:\UiPathDemo\` ABSENT.
- Path is a hardcoded literal — no variable, no `Assign`, and no upstream `InvokeWorkflowFile`/`Write`/`Create`/`Copy`/`Download` activity that could have produced `source.txt`. The Move File is the first and only child of the sequence.
- Job identity (`raw/triage-job-get.json`): Key `f32f9829-4465-49a2-8e3e-0cc182a020c4` (Id 66080537), `ReleaseName` **Legacy**, `EntryPointPath` move.xaml, `FolderKey` defb8e05-e36b-4c36-bf11-0b4d08ce6cd1 (folder **Shared**), `State` Faulted, `ErrorCode` Robot.

**Immediate fix:**

### Classic Activities (Root Cause)
1. Correct the **Move File** source `Path` to a file that actually exists on robot machine **MOCK-HOST** at run time (or ensure the source file is placed/created there before the job runs). Do not point the activity at a path that is not present on the robot.
  - Why: `System.IO.File.Move` raised `FileNotFoundException` because `C:\UiPathDemo\DoesNotExist\source.txt` — and the entire `C:\UiPathDemo\` tree — does not exist on the robot; the path is a literal, so it is wrong as authored.
  - Where: `move.xaml`, line 61, `uca:MoveFile` `Path` attribute (currently `C:\UiPathDemo\DoesNotExist\source.txt`).
  - Who: RPA developer.
  - Source: `references/activity-packages/classic-activities/playbooks/file-operation-failed.md` § Resolution ("If the source file does not exist: fix the source path, or fix the upstream step that should have created it").
2. Confirm the destination is correct. The `Destination` is `C:\UiPathDemo\Destination\source.txt` and that folder is also absent on the robot; ensure the destination folder exists (or will exist) before the activity runs, so the move does not fault on the destination once the source is fixed.
  - Why: The filesystem check shows `C:\UiPathDemo\Destination\` is absent; with a valid source the move would then fail on a missing destination directory.
  - Where: `move.xaml` line 61, `uca:MoveFile` `Destination` attribute; create the target folder on **MOCK-HOST** or repoint to an existing folder.
  - Who: RPA developer.
  - Source: `references/activity-packages/classic-activities/playbooks/file-operation-failed.md` § Investigation step 4 / § Resolution.

**Preventive fix:**

1. Classic Activities -- Replace hardcoded file-system literals with project/orchestrator-driven values (arguments, assets, or environment-relative paths) and validate path existence before the move.
  - Why: The fault was caused entirely by a literal path baked into the workflow that exists on no machine; a configurable, validated path would have failed safely or been correct per environment. The `move` sequence had no guard and `ContinueOnError="False"`, so the first bad path faulted the whole job.
  - Where: `move.xaml` — parameterize the `Path`/`Destination` of **Move File**; optionally add an existence check (e.g., a Path Exists / If guard) before the Move File so a missing source is handled deliberately rather than faulting.
  - Who: RPA developer.
  - Source: `references/activity-packages/classic-activities/playbooks/file-operation-failed.md` § Resolution + § What can cause it ("The path is valid on the developer machine but does not exist on the robot machine").

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Move File faulted because its hardcoded source path `C:\UiPathDemo\DoesNotExist\source.txt` does not exist on robot **MOCK-HOST**; literal path in `move.xaml` line 61, so `System.IO.File.Move` raised `FileNotFoundException`, faulting the job ~1.3s after start. | medium | confirmed | Yes (depth-check VERIFIED) | `FileNotFoundException` at `UiPath.Core.Activities.MoveFile.ExecuteAsync` → `File.Move`; `move.xaml` line 61 literal `Path`/`Destination`; FS check shows source, parent, destination, and base `C:\UiPathDemo\` all ABSENT; single-activity sequence with no upstream producer. | Fix the Move File source path (and destination folder) to point at locations that exist on the robot, or create/place them before the activity runs. |
| H2 | Path is correct as authored but `source.txt` was never deployed to **MOCK-HOST** — a developer-machine-vs-robot environment gap. | medium | eliminated by H1 evidence | No | The base `C:\UiPathDemo\` does not exist at all on the robot, and no upstream step was ever meant to create the file, so the path is wholly wrong rather than an unsynced-but-valid location. | N/A — collapses into H1; no separate deployment fix applies. |

---

Now I'll execute the post-presentation action the playbook prescribes.

```
Process:        Legacy   (folder "Shared", job f32f9829-4465-49a2-8e3e-0cc182a020c4)
Robot machine:  MOCK-HOST
File to edit:   move.xaml  (line 61)

Current Move File attributes:
  Path        = C:\UiPathDemo\DoesNotExist\source.txt   <- does NOT exist on the robot
  Destination = C:\UiPathDemo\Destination\source.txt     <- folder does NOT exist on the robot
  Overwrite   = False

On the robot machine MOCK-HOST the entire C:\UiPathDemo\ tree is absent
(source file, its parent folder, the destination folder, and the base folder).
```

The source path is a hardcoded literal — there is no upstream step that creates the file. Editing the XAML only fixes the path; the source file must actually exist on the robot at run time (and the destination folder must exist) for the job to succeed.
