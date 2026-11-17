<!--skill-flavor:multi-workflow-layout:start-->
## Layout in Studio Web

Studio Web shows an API workflow project's folders and workflow files in the project explorer, with "Create folder" and a new API workflow file on the project and on each folder. Each file in the explorer is a complete workflow (rule 1 of SKILL.md: `document`, `evaluate`, one root sequence starting with `WorkflowStart`).

- Create folders and workflow files through the explorer, then edit them through the Studio Web VFS. Keep the host-generated project metadata as Studio Web wrote it.
- File and folder names follow file-name rules: no leading or trailing `.` or whitespace, none of `< > : " \ | ? *`, and none of the Windows device names (`con`, `nul`, `com1`, ...).
- Keep workflows out of the root `content/` and `evals/` folders and out of dot-folders, and give them names other than the project's metadata file names.
- Two files with the same name in different folders are different workflows.
- Studio Web records the entry points (the workflows that start on their own) when it publishes. A workflow that is only invoked by another needs none.
<!--skill-flavor:multi-workflow-layout:end-->

<!--skill-flavor:multi-workflow-package-contents:start-->
## What a Package Ships

Publishing packs the whole project and keeps what the runtime reads:

| Ships | Left out |
|---|---|
| the project's metadata files at the root | dot-folders and dot-files |
| every other `.json` file, at any depth (workflows and the JSON data they read) | `~` temp files and `node_modules/` |
| everything under the root `evals/`, any file type | every non-JSON file outside `evals/` (`README.md`, images, `.txt`/`.csv` data) |

Packing then checks the package against itself. An invoke the package cannot resolve, or two paths that collide, fail the publish (the message starts with "The package is inconsistent"):

| Problem | Fix |
|---|---|
| `'content/A.json' invokes 'content/B.json', which the package does not contain` | A `run.workflow` `name` points at no packaged workflow. Fix the name (project-root path, no `.json`) or add the file. |
| `... which the package holds only as 'content/B.json' (names are case-sensitive)` | The name differs from the file only in case. Use the file's exact case. |
| `... invokes a workflow by a name the runtime refuses: <reason>` | Rename the invoke to a project-root path that follows the naming rules above. |
| `... which is not a workflow definition` | The target is data JSON; invoke the workflow file. |
| `'content/a.json' and 'content/A.json' differ only in letter case or Unicode form` | Two files whose paths collide. Rename one. |

An entry point or the main workflow that names a file the package lacks is reported as a warning, and the publish goes ahead. Fix the file's location or name so the entry point finds it; a job started from that entry point fails.

A file the project needs at run time is `.json`, or lives under `evals/`.
<!--skill-flavor:multi-workflow-package-contents:end-->

<!--skill-flavor:multi-workflow-local-checks:start-->
## Checking a Multi-Workflow Project in Studio Web

1. **Validate every workflow file**, including `Workflow.json`: from the project root, run `uip api-workflow validate Shared/Validate.json --output json` for each one. `validate` checks each `run.workflow` name against the rules above; it reads one file at a time, so publishing is where a missing invoked file shows up.
   - An older embedded CLI reports the activity itself (`Unknown activityType 'RunWorkflow'`, `Unknown property 'workflow' is not allowed`). Those two errors on an invoke task are a CLI gap, not a workflow error: keep the invoke as written, and say in your report which errors were the gap.
2. **Run with consent** through the host's `RunProject` capability (see the Studio Web capability map). If it reports that it cannot run the invoke, run each invoked workflow on its own with the `input` the caller would pass.
3. **Publish** through the host bridge. Packaging runs in the background with the rules and checks above; a failed check appears in Studio Web's Publish history with the messages in the table. Fix the reported path or name and publish again.

## Publishing

A standalone project (outside a solution) and a project in a solution both publish through the host bridge; Studio Web packs them with the same packager.

**Runtime support for folders.** A published job resolves `name` from the package's content root. Sub-folder names (`Shared/Validate`) need a runtime with folder support, which is rolling out. If a job reports a workflow-not-found error for a nested name, move the invoked workflow to the root and invoke it by bare name.
<!--skill-flavor:multi-workflow-local-checks:end-->
