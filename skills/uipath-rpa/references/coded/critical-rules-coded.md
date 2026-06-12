# Coded Critical Rules Companion & Quick Reference

Coded-mode companion to SKILL.md. Read before authoring `.cs` workflow files. Coded Critical Rules 13–19 and the service-API doc resolution order live in SKILL.md (§ Coded-Specific Rules, § Coded Workflows Quick Reference); this file carries the supporting detail those rules depend on.

## Three Types of .cs Files

| Type | Base Class | Attribute | Entry Point | Purpose |
|------|-----------|-----------|-------------|---------|
| **Coded Workflow** | `CodedWorkflow` | `[Workflow]` | Process only | Executable automation logic |
| **Coded Test Case** | `CodedWorkflow` | `[TestCase]` | Process only | Automated test with assertions |
| **Coded Source File** | None (plain C#) | None | No | Reusable models, helpers, utilities, hooks |

## Service-to-Package Mapping

Each service on `CodedWorkflow` requires its NuGet package in `project.json`. Without it: `CS0103`.

| Service Property | Required Package |
|-----------------|------------------|
| `system` | `UiPath.System.Activities` |
| `testing` | `UiPath.Testing.Activities` |
| `uiAutomation` | `UiPath.UIAutomation.Activities` |
| `excel` | `UiPath.Excel.Activities` |
| `word` | `UiPath.Word.Activities` |
| `powerpoint` | `UiPath.Presentations.Activities` |
| `mail` | `UiPath.Mail.Activities` |
| `office365` | `UiPath.MicrosoftOffice365.Activities` |
| `google` | `UiPath.GSuite.Activities` |

For infrastructure/cloud packages (azure, gcp, aws, azureAD, citrix, hyperv, etc.), resolve the service's package and API surface via the coded-api resolution order in SKILL.md § Coded Workflows Quick Reference.

For IS connectors from coded workflows via `ConnectorConnection.ExecuteAsync`: `UiPath.IntegrationService.Activities` — see [integration-service-guide.md](integration-service-guide.md).

## CodedWorkflow Base Class

All workflow/test case files inherit from `CodedWorkflow`, providing built-in methods, service properties, and the `workflows` property for strongly-typed invocation. Extendable with Before/After hooks via `IBeforeAfterRun`. Integration Service connections (`connections` property), the `services` property, job context (`IRunningJobInformation`), and hooks: [codedworkflow-reference.md](codedworkflow-reference.md).

### Built-in Methods (available in any workflow/test case via `this`)

| Method | Description |
|--------|-------------|
| `Log(string message, LogLevel level = LogLevel.Info, IDictionary<string, object> additionalLogFields = null)` | Output log messages with optional level and custom fields. Valid `LogLevel` values: `Trace`, `Verbose`, `Info`, `Warn`, `Error`, `Fatal`. Note: `LogLevel.Warning` does not exist — use `LogLevel.Warn` |
| `Delay(TimeSpan time)` / `Delay(int delayMs)` | Pause execution synchronously |
| `DelayAsync(TimeSpan time)` / `DelayAsync(int delayMs)` | Pause execution asynchronously |
| `BuildClient(string scope = "Orchestrator", bool force = true)` | Build an authenticated `HttpClient` for Orchestrator or custom scopes |
| `GetRunningJobInformation()` | Returns `IRunningJobInformation` with current job context: job ID, process name/version, tenant, folder, organization, robot name, and more — see [codedworkflow-reference.md § IRunningJobInformation Properties](codedworkflow-reference.md#irunningjobinformation-properties) |
| `RunWorkflow(string workflowFilePath, IDictionary<string, object> inputArguments = null, TimeSpan? timeout = null, bool isolated = false, InvokeTargetSession targetSession = InvokeTargetSession.Current)` | **Fallback method:** Invoke workflow by string path. Use `workflows.MyWorkflow()` instead when possible |
| `RunWorkflowAsync(...)` | Async version of `RunWorkflow` (same limitations apply) |

### Invoking Other Workflows

- **Recommended:** `workflows.MyWorkflow(invoiceId: "INV-001", amount: 1500.00m)` — strongly-typed, compile-checked workflow names and parameters, refactor-friendly, returns the declared return type directly. Parameters with C# default values may be omitted — defaults apply.
- **Fallback:** `RunWorkflow(path, new Dictionary<string, object> { { "invoiceId", "INV-001" } })` — only when the workflow name is determined at runtime. Returns `IDictionary<string, object>`: a single return value lands under key `"Output"`; tuple returns produce one key per element; a name shared between an input parameter and the return tuple is an InOut argument. Full argument-direction table: [operations-guide.md § Add a Workflow File](operations-guide.md).

## Templates

- [../../assets/codedworkflow-template.md](../../assets/codedworkflow-template.md) — Workflow boilerplate
- [../../assets/testcase-template.md](../../assets/testcase-template.md) — Test case boilerplate
- [../../assets/helper-utility-template.md](../../assets/helper-utility-template.md) — Helper class boilerplate
- [../../assets/json-template.md](../../assets/json-template.md) — `entryPoints` and `fileInfoCollection` snippets
- [../../assets/before-after-hooks-template.md](../../assets/before-after-hooks-template.md) — Before/After hooks
- [../project-structure-guide.md](../project-structure-guide.md) — Project structure design guidelines (mode-agnostic)
