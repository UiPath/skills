# API Workflow File Format

JSON files conforming to **CNCF Serverless Workflow DSL 1.0.0** with UiPath task-type extensions. Executed by `@uipath/api-workflow-executor` via `uip api-workflow run`.

## Top-Level Structure

```json
{
  "document": {
    "dsl": "1.0.0",
    "name": "Workflow",
    "version": "0.0.1",
    "namespace": "default",
    "metadata": {
      "variables": {
        "schema": {
          "format": "json",
          "document": {
            "type": "object",
            "properties": {
              "myVar": { "type": "string", "default": "" }
            },
            "title": "Variables"
          }
        }
      }
    }
  },
  "input": {
    "schema": {
      "format": "json",
      "document": {
        "type": "object",
        "properties": {
          "inputField": { "type": "string" }
        },
        "title": "Inputs"
      }
    }
  },
  "output": {
    "schema": {
      "format": "json",
      "document": {
        "type": "object",
        "properties": {
          "outputField": { "type": "string" }
        },
        "title": "Outputs"
      }
    }
  },
  "do": [
    {
      "Sequence_1": {
        "do": [
          {
            "WorkflowStart": {
              "set": "${Object.entries($workflow.definition?.document?.metadata?.variables?.schema?.document?.properties || {}).reduce((acc, [name, def]) => ({ ...acc, [name]: def?.default }), {}) }",
              "output": { "as": "${$input}" },
              "export": { "as": "{ ...$context, variables: { ...$context.variables, ...$output } }" },
              "metadata": { "activityType": "Assign", "displayName": "Workflow start", "fullName": "Assign", "isTransparent": true }
            }
          }
        ],
        "metadata": { "activityType": "Sequence", "displayName": "Sequence", "fullName": "Sequence" }
      }
    }
  ],
  "evaluate": { "mode": "strict", "language": "javascript" }
}
```

## Required Top-Level Keys

| Key | Type | Required | Notes |
|-----|------|----------|-------|
| `document.dsl` | string | yes | MUST be `"1.0.0"`. |
| `document.name` | string | yes | Workflow display name. |
| `document.version` | string | yes | SemVer. Independent of solution version. |
| `document.namespace` | string | yes | Logical grouping. `"default"` is fine. |
| `document.metadata.variables` | object | yes | Variables JSON Schema. See **Variables** below. |
| `input.schema` | object | optional | JSON Schema for workflow inputs. |
| `output.schema` | object | optional | JSON Schema for workflow outputs. |
| `evaluate.language` | string | yes | MUST be `"javascript"`. |
| `evaluate.mode` | string | yes | `"strict"`. |
| `do` | array | yes | Ordered tasks. Each entry is `{ "<TaskName>": { ... } }`. Root is conventionally a single `Sequence_1`. |
| `httpRetryConfig` | object | optional | Workflow-level retry policy for HTTP **GET** calls (`UiPath.Http` GET + `UiPath.IntSvc` list/get). Absent → no retry. See [http-retry-config.md](http-retry-config.md). |

## Variables

Variables live at `document.metadata.variables.schema.document` as a JSON Schema:

```json
"variables": {
  "schema": {
    "format": "json",
    "document": {
      "type": "object",
      "properties": {
        "counter":  { "type": "number",  "default": 0 },
        "userName": { "type": "string",  "default": "" },
        "results":  { "type": "array",   "default": [] }
      },
      "title": "Variables"
    }
  }
}
```

`WorkflowStart` (see below) hydrates `$context.variables` from these defaults at run start.

## Inputs and Outputs

Workflow-level I/O is declared at the root via JSON Schema:

```json
"input": {
  "schema": {
    "format": "json",
    "document": {
      "type": "object",
      "properties": { "userId": { "type": "string" } },
      "title": "Inputs"
    }
  }
}
```

Inputs come from `--input-arguments` JSON or the calling workflow. Read them as `$workflow.input.<name>` from any task. (Reading as `$input.<name>` only works on the very first task — see [expressions-and-context.md](expressions-and-context.md).)

Outputs are read from the final `Response` task's `response` value.

## WorkflowStart — System Activity

`WorkflowStart` is **always the first activity** inside the root sequence's `do` array (`Sequence_1.do` in the template skeleton; the actual key may differ in existing workflows). It hydrates variable defaults into `$context.variables` and forwards inputs to `$input`. Treat it as system-generated:

```json
{
  "WorkflowStart": {
    "set": "${Object.entries($workflow.definition?.document?.metadata?.variables?.schema?.document?.properties || {}).reduce((acc, [name, def]) => ({ ...acc, [name]: def?.default }), {}) }",
    "output": { "as": "${$input}" },
    "export": { "as": "{ ...$context, variables: { ...$context.variables, ...$output } }" },
    "metadata": { "activityType": "Assign", "displayName": "Workflow start", "fullName": "Assign", "isTransparent": true }
  }
}
```

Rules:
- Always present, always first inside the root sequence's `do` array
- `isTransparent: true` (only `WorkflowStart` uses `true` — user-created Assign uses `false`)
- Do not rename, remove, or modify the `set` expression

User activities go AFTER `WorkflowStart` inside the root sequence.

## Task Naming

- Each task wraps in a single-key object: `{ "<TaskName>": { ... } }`
- Names must be **globally unique** across the whole workflow (including `#Wrapper`, `#Then`, `#Else`, `#Body` suffixes)
- Names become keys in `$context.outputs` for downstream reads
- Convention: `<ActivityType>_<index>` — e.g., `Assign_1`, `Javascript_1`, `If_2#Wrapper`, `For_Each_1`

## Common Task Body Fields

| Field | Purpose |
|-------|---------|
| `call` / `run` / `do` / `for` / `try` / `switch` / `wait` / `response` / `set` / `break` | Action selector — varies per task type |
| `with` | Inputs to the action (less common — most activities in this skill use `set` / `do` / `for` / `try` / `run.script`) |
| `export` | How to merge this task's output into context. See [expressions-and-context.md](expressions-and-context.md) |
| `metadata` | StudioWeb editor metadata (`activityType`, `displayName`, `fullName`). Required for designer roundtrip. Runtime mostly ignores it. |

## Sequence

A `Sequence` task groups child tasks. Most workflows have a single root `Sequence_1`:

```json
{
  "Sequence_1": {
    "do": [ /* WorkflowStart, then user tasks */ ],
    "metadata": { "activityType": "Sequence", "displayName": "Sequence", "fullName": "Sequence" }
  }
}
```

Child tasks execute in order. `$context` flows from one to the next via `export.as`.

## Project Structure (Studio Web editable contract)

An API workflow project that must open and edit in **Studio Web** ships a specific on-disk shape. **`uip api-workflow init <name>` generates this shape for you** (and registers the project in the solution `.uipx`) — use it for new projects instead of writing these files by hand. The layout below is the contract `init` produces and what `uip solution pack` reads via `project.uiproj`; it also documents what to recreate when converting a legacy `project.json` project:

```
<solutionDir>/
├── <solution>.uipx                 # Projects[].Type "Api", ProjectRelativePath "<projectFolder>/project.uiproj"
└── <projectFolder>/                # created by `uip api-workflow init <projectFolder>`
    ├── project.uiproj              # { "ProjectType": "Api", "Name": "...", "Description": null, "MainFile": "Workflow.json" }
    ├── Workflow.json               # the API workflow — canonical fixed name, project root
    ├── entry-points.json           # entryPoints[0]: filePath "content/Workflow.json", type "Api"
    ├── bindings_v2.json            # IntSvc connector bindings ({"version":"2.0","resources":[]} when none)
    └── .local/ProjectSettings.json # NOT written by init — Studio Web creates it on first open. Do not author by hand.
```

`uip solution pack` auto-generates `operate.json` and `package-descriptor.json` during build — do NOT commit these.

### Field rules (what Studio Web enforces)

| File | Field | Rule |
|------|-------|------|
| `.uipx` | `Projects[].ProjectRelativePath` | MUST end with `/project.uiproj`. Pointing at `project.json` → folder isn't recognized as a project. |
| `.uipx` | `Projects[].Type` | `"Api"`. |
| `project.uiproj` | `ProjectType` | Exactly `"Api"` (capital A). Studio Web parses this with a strict enum — `"api"` is rejected with `InvalidUiprojFileError`. |
| `project.uiproj` | `MainFile` | `"Workflow.json"`. Studio Web technically accepts any name, but the CLI packager + solution reconcile assume `Workflow.json`. |
| `Workflow.json` | — | Must exist at project root (the file `MainFile` points to). |
| `entry-points.json` | `entryPoints[0].filePath` | `"content/Workflow.json"` — relative, **no leading slash**. (`/content/...` is non-canonical.) |
| `entry-points.json` | `entryPoints[0].type` | `"Api"`. (Studio Web's schema accepts any string here, but stay consistent.) `input`/`output` may be `null` or mirror the workflow's input/output JSON schema so the designer shows parameters. |

> **Why this matters — the runtime shape is a trap.** A `project.json` + `workflows/WF_*.json` layout (no `.uiproj`) runs under `uip api-workflow run`, and packs/publishes/deploys as an API process — every runtime gate passes. But Studio Web's import only recognizes a folder as a project if it contains a `.uiproj` file (`isProjectFolder`); a `project.json`-only project is rejected as `invalid_project_folder` and never appears in Studio Web. Runtime success is NOT proof of Studio Web editability. Scaffold with `uip api-workflow init` — it can't produce the wrong shape (SKILL.md rule 19a).

> **Standalone (CLI-only) projects** that never open in Studio Web — run purely via `uip api-workflow run` — don't need solution registration; `uip api-workflow init <name> --skip-solution-registration` still emits the same files but skips the `.uipx` wiring. The `.uiproj` contract is required the moment the project must be editable in Studio Web or shipped in a solution uploaded to Studio Web.

## Sources

- CNCF Serverless Workflow Specification: https://github.com/serverlessworkflow/specification
- UiPath executor: `@uipath/api-workflow-executor` (bundled with `@uipath/cli`)
