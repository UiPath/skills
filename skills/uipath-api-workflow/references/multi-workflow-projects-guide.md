# Multi-Workflow Projects: Sub-Folders, Invoke API Workflow, and Packaging

An API workflow project can hold more than one workflow file, in sub-folders, and one workflow can run another with the **Invoke API Workflow** activity. This guide covers the layout, the invoke shape and its naming rules, what a package ships, and the errors packing reports.

<!--skill-flavor:multi-workflow-layout:start-->
## Layout

```
<projectFolder>/
├── project.uiproj              # MainFile: "Workflow.json"
├── Workflow.json               # the main workflow
├── Shared/
│   └── Validate.json           # a workflow in a sub-folder
├── Invoices/
│   └── Validate.json           # same file name, different folder: a different workflow
├── entry-points.json           # one entry per workflow that is started on its own
├── bindings_v2.json
└── evals/                      # eval sets (see testing-and-evals.md); never workflows
```

- Every workflow file is a complete workflow (rule 1 of SKILL.md: `document`, `evaluate`, one root sequence starting with `WorkflowStart`). Start a new file from [../assets/templates/api-workflow-template.json](../assets/templates/api-workflow-template.json) and give `document.name` the file's base name.
- File and folder names follow file-name rules: no leading or trailing `.` or whitespace, none of `< > : " \ | ? *`, no Windows device names (`con`, `nul`, `com1`, ...).
- Never put a workflow under the root `content/` or `evals/` folder, in a dot-folder (`.local`, `.cache`), or in `node_modules/`; never name one like a project file (`operate.json`, `entry-points.json`, `bindings_v2.json`, `bindings.json`, `package-descriptor.json`, `project.json`, `webappmanifest.json`, `apps.json`) in any folder.
- **Entry points.** `entry-points.json` lists the workflows that are started on their own (as a process or job). A workflow that is only invoked by another needs no entry. To make a nested workflow startable on its own, add an entry with `filePath: "content/Shared/Validate.json"` (forward slashes, no leading slash) and a new `uniqueId` GUID.
<!--skill-flavor:multi-workflow-layout:end-->

## Invoke API Workflow (`RunWorkflow`)

The activity is a `run.workflow` task. Copy this shape; only the key, `name`, `input` and `displayName` change. A complete caller and child: [invoke-workflow-caller-example.json](../assets/templates/invoke-workflow-caller-example.json), [invoke-workflow-child-example.json](../assets/templates/invoke-workflow-child-example.json).

```json
{
  "RunWorkflow_1": {
    "run": {
      "workflow": {
        "namespace": "default",
        "name": "Shared/Validate",
        "version": "0.0.1",
        "input": "${ { invoiceId: $context.variables.invoiceId } }"
      }
    },
    "export": {
      "as": "{ ...$context, outputs: { ...$context?.outputs, \"RunWorkflow_1\": $output } }"
    },
    "metadata": { "activityType": "RunWorkflow", "displayName": "Invoke Validate", "fullName": "RunWorkflow" }
  }
}
```

**Naming the workflow.** `name` is the invoked file's path **from the project root**, without `.json`, with `/` between folders:

| File | `name` |
|---|---|
| `Child.json` (root) | `Child` |
| `Shared/Validate.json` | `Shared/Validate` |
| `Invoices/2024/Validate.json` | `Invoices/2024/Validate` |

- Always from the project root, never relative to the calling file. A workflow in `Invoices/` that invokes its neighbour still writes `Invoices/Validate`; a bare `Validate` means the **root** `Validate.json`.
- Matched **exactly, including case**: `shared/validate` does not find `Shared/Validate.json`.
- Never `.json` at the end (`Child.json` looks for `Child.json.json`), never `\`, `./`, `../` or a leading `/`, never an expression (`${...}`): the name must be a literal.

**Input and output.**
- `input` is an object, or an expression that returns one. The invoked workflow reads it as `$workflow.input.<name>`, so declare those names in its `input.schema`.
- The task's output is what the invoked workflow's Response returns (a non-object value arrives as `{ "result": <value> }`; no Response gives `null`). Read it as `$context.outputs.RunWorkflow_1.<field>`.
- If the invoked workflow ends with `markJobAsFailed: true`, the invoking task fails; wrap it in a Try/Catch to handle that.
- The invoked workflow gets its own `$context` and variables; it cannot change the caller's.
- Omit `run.await` (the runtime only runs an invoked workflow to completion; `await: false` is refused).

<!--skill-flavor:multi-workflow-package-contents:start-->
## What a Package Ships

Packing walks the whole project and keeps only what the runtime reads:

| Ships | Left out |
|---|---|
| the root metadata files (`entry-points.json`, `bindings_v2.json`, `operate.json`, ...) and the root `project.uiproj` | anything under a dot-folder or dot-file (`.local/`, `.gitignore`) |
| every other `.json` file, at any depth (workflows and the JSON data they read) | `~` temp files and `node_modules/` |
| everything under the root `evals/`, any file type | every non-JSON file outside `evals/` (`README.md`, images, `.txt`/`.csv` data) |
| | project-file names below the root (a nested `project.json` or `project.uiproj`) |

`operate.json` and `package-descriptor.json` are generated; `operate.json`'s `main` is the entry point for `project.uiproj`'s `MainFile`.

Packing then checks the package against itself and **fails** (`Message` starts with "The package is inconsistent") when:

| Problem | Fix |
|---|---|
| `'entry-points.json' names 'content/X.json', which the package does not contain` | The entry's `filePath` points at a missing, renamed or left-out file. Fix the path, or move the file out of the left-out locations above. |
| `'operate.json' main names ...` | Same, for `MainFile` / a hand-written `operate.json`. Delete a stale `operate.json`; the packager generates it. |
| `'content/A.json' invokes 'content/B.json', which the package does not contain` | A `run.workflow` `name` points at no packaged workflow. Fix the name (project-root path, no `.json`) or add the file. |
| `... which the package holds only as 'content/Shared/Validate.json' (names are case-sensitive)` | The name differs from the file only in case. Use the file's exact case. |
| `'content/a.json' and 'content/A.json' differ only in case` | Two files whose paths differ only in case; one is lost on Windows and macOS. Rename one. |

A warning (not a failure) lists files left out of the package, with a count and the first five names. Read it: a file the project needs at run time must be `.json` (or live under `evals/`).
<!--skill-flavor:multi-workflow-package-contents:end-->

<!--skill-flavor:multi-workflow-local-checks:start-->
## Checking a Multi-Workflow Project Locally

1. **Validate every workflow file**, not only `Workflow.json`: `uip api-workflow validate <project>/Shared/Validate.json --output json` for each one (rule 20). `validate` checks each `run.workflow` name against the rules above, but it reads one file and cannot tell whether the invoked file exists — packing checks that.
   - An older CLI rejects the activity itself (`Unknown activityType 'RunWorkflow'`, `Unknown property 'workflow' is not allowed`). Those two errors on an invoke task are a CLI gap, not a workflow error: do not remove or rewrite the invoke to silence them. Keep validating everything else, and say in your report which errors were the gap.
2. **Run what can run.** `uip api-workflow run` cannot execute an Invoke API Workflow task yet: it fails with `No code found for script task: <key>`. Run each invoked workflow on its own with the `input` the caller would pass (`--input-arguments`), with the rule-21 consent; the invoking workflow is proven once published.
3. **Pack the project and read the result**: `uip api-workflow pack <project> <outDir> --output json` checks the invokes and entry points across files (table above). Then list the package and confirm every workflow is there:

   ```bash
   unzip -l <outDir>/<id>.<version>.nupkg | grep content/
   ```

   An older CLI packs only root files (and `evals/`) and does not check invokes: if `content/Shared/Validate.json` is missing from the listing, the CLI predates sub-folder packaging; keep invoked workflows at the project root (invoke them by bare name) until it is updated.
4. **Pack warnings about workflows.** A CLI that validates while packing prints each `validate` problem as a warning and still packs. Treat those warnings as `validate` errors and fix them; a package with them may fail at run time.

## Publishing

A project inside a solution publishes with `uip solution pack` + `uip solution publish` (SKILL.md Phase 4); the same packaging rules and checks apply to each API project in the solution. There is no CLI command that uploads a single project's `.nupkg`: `uip api-workflow pack` is for checking one project. A standalone project (not in a solution) is published from Studio Web, which packs it with the same packager in the browser and uploads it to the chosen Orchestrator feed.

**Runtime support for folders.** A published job resolves `name` from the package's content root. Sub-folder names (`Shared/Validate`) need a runtime with folder support, which is rolling out. If a job fails with a workflow-not-found error for a nested name while the package listing shows the file, the tenant's runtime predates it: move the invoked workflow to the root and invoke it by bare name.
<!--skill-flavor:multi-workflow-local-checks:end-->
