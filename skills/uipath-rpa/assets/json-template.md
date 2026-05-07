# project.json Snippets

Hand-editable snippets for the sections of `project.json` the agent legitimately modifies after `uip rpa create-project` has scaffolded the project.

> **DO NOT use these snippets to write `project.json` from scratch.** Always run `uip rpa create-project` first — it generates correct schema versions, metadata directories, default dependencies, and version-matched configuration. Use these snippets only to add entries to an existing scaffolded `project.json`.

> **Sections NOT shown here** (`runtimeOptions`, `designOptions.processOptions`, `schemaVersion`, `studioVersion`, `expressionLanguage`, `targetFramework`, etc.) are written by `create-project` and should not be hand-edited unless the user explicitly asks.

---

## `entryPoints` entry (Process projects only)

For each `.cs` workflow file added to a Process project, append one entry to the `entryPoints` array. Tests and Library projects do NOT use `entryPoints`.

```json
{
  "filePath": "{{FILE_NAME}}.cs",
  "uniqueId": "{{UUID_V4}}",
  "input": [],
  "output": []
}
```

### Entry point with parameters

When the workflow's `Execute` method has parameters or a return value, populate `input` / `output`:

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

Common `type` values: `System.String`, `System.Int32`, `System.Boolean`, `System.Double`, `System.DateTime`, `System.Data.DataTable`, `System.Collections.Generic.Dictionary<System.String,System.Object>`

---

## `fileInfoCollection` entry (test cases)

For each `.cs` test case file (in any project type — Process, Tests, or Library), append one entry to `designOptions.fileInfoCollection`. Test cases do NOT go in `entryPoints`.

```json
{
  "editingStatus": "InProgress",
  "testCaseId": "{{UUID_V4}}",
  "testCaseType": "TestCase",
  "fileName": "{{TestCase}}.cs",
  "publishAsTestCase": true
}
```

> **`editingStatus` lifecycle:** Set `"InProgress"` when creating a new test case. Update to `"Publishable"` only when the user explicitly asks to mark the test case as ready.

### Data-driven test case (with variations file)

When a test case uses parameter variations, add `dataVariationFilePath` to its `fileInfoCollection` entry:

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

The variations file lives at `.variations/{{variationName}}_Sheet1.json` with shape:

```json
[
  { "{{paramName}}": "value1" },
  { "{{paramName}}": "value2" },
  { "{{paramName}}": "value3" }
]
```
