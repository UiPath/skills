# UiPath Coded Workflow Templates

Ready-to-use templates for all UiPath coded automation project files. Replace placeholders in `{{PLACEHOLDER}}` format.

> **IMPORTANT: Do NOT use these `project.json` / `project.uiproj` templates to create new projects.** Always use `rpa-tool create-project` which generates correct defaults, metadata directories, and version-matched configuration. These templates are **reference-only** — use them to understand the file structure, or to manually add entry points, dependencies, and fileInfoCollection entries to an existing `project.json` that was scaffolded by `create-project`.

---

## project.json — Process Project (Reference Only)

```json
{
  "name": "{{PROJECT_NAME}}",
  "projectId": "{{UUID_V4}}",
  "description": "{{DESCRIPTION}}",
  "main": "Main.cs",
  "dependencies": {
    "UiPath.System.Activities": "[25.12.2]",
    "UiPath.Testing.Activities": "[25.10.0]",
    "UiPath.UIAutomation.Activities": "[25.10.21]"
  },
  "webServices": [],
  "entitiesStores": [],
  "schemaVersion": "4.0",
  "studioVersion": "{{STUDIO_VERSION}}",
  "projectVersion": "1.0.0",
  "runtimeOptions": {
    "autoDispose": false,
    "netFrameworkLazyLoading": false,
    "isPausable": true,
    "isAttended": false,
    "requiresUserInteraction": false,
    "supportsPersistence": false,
    "workflowSerialization": "NewtonsoftJson",
    "excludedLoggedData": [
      "Private:*",
      "*password*"
    ],
    "executionType": "Workflow",
    "readyForPiP": false,
    "startsInPiP": false,
    "mustRestoreAllDependencies": true,
    "pipType": "ChildSession"
  },
  "designOptions": {
    "projectProfile": "Developement",
    "outputType": "Process",
    "libraryOptions": {
      "privateWorkflows": []
    },
    "processOptions": {
      "ignoredFiles": []
    },
    "fileInfoCollection": [],
    "saveToCloud": false
  },
  "expressionLanguage": "CSharp",
  "entryPoints": [
    {
      "filePath": "Main.cs",
      "uniqueId": "{{UUID_V4}}",
      "input": [],
      "output": []
    }
  ],
  "isTemplate": false,
  "templateProjectData": {},
  "publishData": {},
  "targetFramework": "Windows"
}
```

### Variant: Tests Project (Reference Only)

Replace the `designOptions` block and `targetFramework` as shown. Key differences from the Process template:
- `outputType` → `"Tests"`
- `fileInfoCollection` → one entry per test case file (add more entries as you add test cases)
- No `processOptions` block
- **No `main`** — Tests projects do not have a main entry point file
- **No `entryPoints`** — Tests projects do not use entry points

```json
{
  "name": "{{PROJECT_NAME}}",
  "projectId": "{{UUID_V4}}",
  "description": "{{DESCRIPTION}}",
  "dependencies": {
    "UiPath.System.Activities": "[25.12.2]",
    "UiPath.Testing.Activities": "[25.10.0]",
    "UiPath.UIAutomation.Activities": "[25.10.21]"
  },
  "webServices": [],
  "entitiesStores": [],
  "schemaVersion": "4.0",
  "studioVersion": "{{STUDIO_VERSION}}",
  "projectVersion": "1.0.0",
  "runtimeOptions": {
    "autoDispose": false,
    "netFrameworkLazyLoading": false,
    "isPausable": true,
    "isAttended": false,
    "requiresUserInteraction": false,
    "supportsPersistence": false,
    "workflowSerialization": "NewtonsoftJson",
    "excludedLoggedData": [
      "Private:*",
      "*password*"
    ],
    "executionType": "Workflow",
    "readyForPiP": false,
    "startsInPiP": false,
    "mustRestoreAllDependencies": true,
    "pipType": "ChildSession"
  },
  "designOptions": {
    "projectProfile": "Developement",
    "outputType": "Tests",
    "libraryOptions": {
      "privateWorkflows": []
    },
    "fileInfoCollection": [
      {
        "editingStatus": "InProgress",
        "testCaseId": "{{UUID_V4}}",
        "testCaseType": "TestCase",
        "fileName": "{{TestCase}}.cs",
        "publishAsTestCase": true
      }
    ],
    "saveToCloud": false
  },
  "expressionLanguage": "CSharp",
  "entryPoints": [],
  "isTemplate": false,
  "templateProjectData": {},
  "publishData": {},
  "targetFramework": "Windows"
}
```

> **`editingStatus` lifecycle:** Set `"InProgress"` when creating a new test case. Update to `"Publishable"` only when the user explicitly asks to mark the test case as ready.

### Variant: Library Project (Reference Only)

Replace the `designOptions` block. Key differences from the Process template:
- `outputType` → `"Library"`
- `libraryOptions.privateWorkflows` lists any workflows that should NOT be exposed as activities
- **No `entryPoints`** — Library projects do not use entry points

```json
{
  "name": "{{PROJECT_NAME}}",
  "projectId": "{{UUID_V4}}",
  "description": "{{DESCRIPTION}}",
  "main": "Main.cs",
  "dependencies": {
    "UiPath.System.Activities": "[25.12.2]"
  },
  "webServices": [],
  "entitiesStores": [],
  "schemaVersion": "4.0",
  "studioVersion": "{{STUDIO_VERSION}}",
  "projectVersion": "1.0.0",
  "runtimeOptions": {
    "autoDispose": false,
    "netFrameworkLazyLoading": false,
    "isPausable": true,
    "isAttended": false,
    "requiresUserInteraction": false,
    "supportsPersistence": false,
    "workflowSerialization": "NewtonsoftJson",
    "excludedLoggedData": [
      "Private:*",
      "*password*"
    ],
    "executionType": "Workflow",
    "readyForPiP": false,
    "startsInPiP": false,
    "mustRestoreAllDependencies": true,
    "pipType": "ChildSession"
  },
  "designOptions": {
    "projectProfile": "Developement",
    "outputType": "Library",
    "libraryOptions": {
      "privateWorkflows": []
    },
    "processOptions": {
      "ignoredFiles": []
    },
    "fileInfoCollection": [],
    "saveToCloud": false
  },
  "expressionLanguage": "CSharp",
  "entryPoints": [],
  "isTemplate": false,
  "templateProjectData": {},
  "publishData": {},
  "targetFramework": "Windows"
}
```

### Variant: Cross-Platform (Portable)

Set `targetFramework` to `"Portable"` in any of the above templates:
```json
{
  "targetFramework": "Portable"
}
```

### Entry Point with Parameters
```json
{
  "filePath": "{{FILE_NAME}}.cs",
  "uniqueId": "{{UUID_V4}}",
  "input": [
    {
      "name": "{{PARAM_NAME}}",
      "type": "{{DOTNET_TYPE}}",
      "required": true
    }
  ],
  "output": [
    {
      "name": "{{OUTPUT_NAME}}",
      "type": "{{DOTNET_TYPE}}"
    }
  ]
}
```

Common `type` values: `System.String`, `System.Int32`, `System.Boolean`, `System.Double`, `System.DateTime`, `System.Data.DataTable`, `System.Collections.Generic.Dictionary\u003cSystem.String,System.Object\u003e`

---

## project.uiproj

```json
{
  "Name": "{{PROJECT_NAME}}",
  "ProjectType": "{{Process|Tests|Library}}",
  "Description": "{{DESCRIPTION}}",
  "MainFile": "Main.cs"
}
```

## Data-Driven Test Variations File

**Path:** `.variations/{{variationName}}_Sheet1.json`

```json
[
  {
    "{{paramName}}": "value1"
  },
  {
    "{{paramName}}": "value2"
  },
  {
    "{{paramName}}": "value3"
  }
]
```

When using variations, also add to project.json fileInfoCollection:
```json
{
  "editingStatus": "InProgress",
  "testCaseId": "{{UUID_V4}}",
  "testCaseType": "TestCase",
  "fileName": "{{TestCase}}.cs",
  "publishAsTestCase": true,
  "dataVariationFilePath": ".variations\\{{variationName}}_Sheet1.json"
}
```