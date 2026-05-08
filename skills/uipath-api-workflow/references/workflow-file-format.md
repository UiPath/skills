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

`WorkflowStart` is **always the first activity** inside `Sequence_1.do`. It hydrates variable defaults into `$context.variables` and forwards inputs to `$input`. Treat it as system-generated:

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
- Always present, always first inside `Sequence_1.do`
- `isTransparent: true` (only `WorkflowStart` uses `true` — user-created Assign uses `false`)
- Do not rename, remove, or modify the `set` expression

User activities go AFTER `WorkflowStart` inside `Sequence_1.do`.

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

## Project Structure (Packaging Context)

When part of a UiPath solution, the workflow JSON sits in a project folder with `Type: "Api"` declared in the solution `.uipx`:

```
<solutionDir>/
├── <solution>.uipx          # Lists all projects with their Type
└── <projectFolder>/
    ├── project.json         # Project metadata
    ├── <main-workflow>.json # Your API workflow
    └── <other-workflow>.json
```

`uip solution pack` auto-generates `operate.json` and `package-descriptor.json` during build — do NOT commit these.

## Sources

- CNCF Serverless Workflow Specification: https://github.com/serverlessworkflow/specification
- UiPath executor: `@uipath/api-workflow-executor` (bundled with `@uipath/cli`)
