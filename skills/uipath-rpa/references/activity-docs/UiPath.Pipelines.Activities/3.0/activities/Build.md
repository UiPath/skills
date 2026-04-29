# Build

`UiPath.Pipelines.Activities.Build`

Packages an automation project into a NuGet package (`.nupkg`).

Delegates to the `PipelinesWrapper` child process which calls `uipcli` internally. Before packing, it optionally validates the project against the configured Orchestrator library feeds. The resulting package path is written to the `PackagePath` output argument.

**Package:** `UiPath.Pipelines.Activities`
**Category:** Pipelines

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `RepositoryPath` | Repository path | `InArgument` | `string` | Yes | — | — | Absolute path to the cloned repository. |
| `ProjectPath` | Project path | `InArgument` | `string` | No | `project.json` | — | Relative path to the `project.json` file. Defaults to `project.json` in the repository root. |
| `Author` | Author | `InArgument` | `string` | No | Current user | — | Author to be set on the package. |
| `Version` | Version | `InArgument` | `string` | No | From `project.json` | — | Version of the package. If not provided, defaults to the version in `project.json`. |
| `IncludeSources` | Include sources | `InArgument` | `bool` | No | `false` | — | Sets whether the automation source code shall be packed as well. |
| `SeparateRuntimeDependencies` | Separate runtime dependencies | `InArgument` | `bool` | No | `true` | — | Enables the output split to runtime and design libraries. |
| `SkipValidate` | Skip validation | `InArgument` | `bool` | No | `false` | — | Skips project validation. |
| `RepositoryType` | Repository type | `InArgument` | `string` | No | — | — | The used source control type (e.g. `git`, `svn`, `uip`). |
| `RepositoryUrl` | Repository URL | `InArgument` | `string` | No | — | — | Remote repository URL of the `project.json` file. |
| `RepositoryBranch` | Repository branch | `InArgument` | `string` | No | — | — | Source branch for the package. |
| `RepositoryCommit` | Repository commit | `InArgument` | `string` | No | — | — | Commit ID (the commit SHA for git repositories). |
| `ReleaseNotes` | Release notes | `InArgument` | `string` | No | — | — | Release notes for the package. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `PackagePath` | NuGet Package path | `string` | Absolute path to the built NuGet package (`.nupkg`). |

### Common

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `ContinueOnError` | Continue on error | `InArgument` | `bool` | `false` | If set, continues executing even if this activity fails. |

## XAML Example

```xml
<pip:Build
    RepositoryPath="[repoPath]"
    ProjectPath="src/project.json"
    Version="1.0.0"
    PackagePath="[packagePath]"
    DisplayName="Build" />
```

## Notes

- `RepositoryPath` is the only required property; all others are optional.
- When `SkipValidate` is `false` (the default), the activity first validates the project using `uipcli` before packing. Validation checks library feed compatibility.
- The `SeparateRuntimeDependencies` property defaults to `true`, which splits the output package into runtime and design-time libraries.
- Repository metadata properties (`RepositoryType`, `RepositoryUrl`, `RepositoryBranch`, `RepositoryCommit`) are embedded in the package manifest and used by Orchestrator for source-tracking.
- The `Build` activity does **not** require an Orchestrator connection (no `Tenant` argument). It inherits directly from `ContinuableAsyncCodeActivity`.
