# UiPath.Pipelines.Activities

**Assembly:** `UiPath.Pipelines.Activities.dll`
**Category:** Pipelines

The `UiPath.Pipelines.Activities` package provides activities for building CI/CD pipelines in UiPath Studio. It covers the full automation lifecycle: cloning source repositories, analyzing workflow quality, packaging, publishing to Orchestrator, running tests, and managing Solutions deployments.

---

## CI/CD Activities

| Activity | Class | Description |
|----------|-------|-------------|
| [Build](activities/Build.md) | `UiPath.Pipelines.Activities.Build` | Packages an automation project into a NuGet package. |
| [Analyze](activities/Analyze.md) | `UiPath.Pipelines.Activities.Analyze` | Analyzes a project against workflow analysis rules. |
| [Clone](activities/Clone.md) | `UiPath.Pipelines.Activities.Clone` | Clones a git repository. |
| [Download Package](activities/DownloadPackage.md) | `UiPath.Pipelines.Activities.DownloadPackage` | Downloads a package from Orchestrator. |
| [Publish Package](activities/PublishPackage.md) | `UiPath.Pipelines.Activities.PublishPackage` | Publishes a package to Orchestrator. |
| [Stage](activities/Stage.md) | `UiPath.Pipelines.Activities.Stage` | Container activity for reporting pipeline stage status to Automation Ops. |
| [Update Process](activities/UpdateProcess.md) | `UiPath.Pipelines.Activities.UpdateProcess` | Updates an Orchestrator process to a new package version. |
| [Run Tests](activities/RunTests.md) | `UiPath.Pipelines.Activities.RunTests` | Builds, uploads, and runs a test project against Orchestrator. |
| [Run Existing Test Set](activities/RunExistingTestSet.md) | `UiPath.Pipelines.Activities.RunExistingTestSet` | Runs a pre-existing test set defined in Orchestrator. |

## Solutions Activities

| Activity | Class | Description |
|----------|-------|-------------|
| [Activate Solution Deployment](activities/ActivateSolutionDeployment.md) | `UiPath.Pipelines.Activities.ActivateSolutionDeployment` | Activates a solution deployment. |
| [Delete Solution Package](activities/DeleteSolutionPackage.md) | `UiPath.Pipelines.Activities.DeleteSolutionPackage` | Deletes a solution package. |
| [Deploy Solution](activities/DeploySolution.md) | `UiPath.Pipelines.Activities.DeploySolution` | Deploys a solution. |
| [Download Solution Package](activities/DownloadSolutionPackage.md) | `UiPath.Pipelines.Activities.DownloadSolutionPackage` | Downloads a solution package. |
| [Download Solution Package Configuration](activities/DownloadSolutionPackageConfiguration.md) | `UiPath.Pipelines.Activities.DownloadSolutionPackageConfiguration` | Downloads a solution package configuration file. |
| [Publish Solution Package](activities/PublishSolutionPackage.md) | `UiPath.Pipelines.Activities.PublishSolutionPackage` | Publishes a solution package. |
| [Re-sync Solution Project](activities/ResyncSolutionProject.md) | `UiPath.Pipelines.Activities.ResyncSolutionProject` | Re-syncs a solution project with Orchestrator. |
| [Uninstall Solution](activities/UninstallSolution.md) | `UiPath.Pipelines.Activities.UninstallSolution` | Uninstalls a deployed solution. |
| [Upload Solution Package](activities/UploadSolutionPackage.md) | `UiPath.Pipelines.Activities.UploadSolutionPackage` | Uploads a solution package zip archive to Orchestrator. |

---

## Architecture Notes

### CI/CD Activity Hierarchy

```
ContinuableAsyncCodeActivity
└── CicdBaseActivity                          # ContinueOnError + TimeoutMS (60 s default)
    ├── Clone, Analyze, Build                 # No Orchestrator client; delegate to PipelinesWrapper
    └── CicdBaseOrchestratorPackageActivity   # Adds Tenant + OrchestratorClient
        ├── PublishPackage, UpdateProcess, DownloadPackage
        └── BaseTestingActivity (persistent)
            ├── RunTests
            └── RunExistingTestSet
```

### Solutions Activity Hierarchy

```
ContinuableAsyncCodeActivity
└── BaseSolutionsActivity                     # Tenant (required), ContinueOnError, TimeoutMS (120 s default)
    └── All 9 Solutions activities
```

### Key Custom Types

| Type | Description |
|------|-------------|
| `OrchestratorTenant` | Wraps a tenant name string; has implicit conversion from/to `string`. |
| `OrchestratorFolder` | Wraps a folder path string; has implicit conversion from/to `string`. |
| `AnalyzePolicy` | Governance policy identifier; has implicit conversion from `string`. |
| `UiPathTestReport` | Aggregated test set execution results object. |
| `ConfigurationFormat` | Enum: `Json` (0), `Yaml` (1). |
| `SolutionProjectSyncOption` | Enum: `Sync` (0) — read-only properties, `Reset` (1) — all properties. |
