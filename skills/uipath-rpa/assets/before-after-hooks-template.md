# Before/After Hooks Template

Two patterns for adding setup/teardown logic to coded workflows and test cases.

## Pattern 1: IBeforeAfterRun on Individual Workflows/Test Cases

Any workflow or test case can implement `IBeforeAfterRun` directly. The hooks run only for that specific file.

**File: `TestLoginFlow.cs`**

```csharp
using UiPath.CodedWorkflows;

namespace {{PROJECT_NAME}}
{
    public class TestLoginFlow : CodedWorkflow, IBeforeAfterRun
    {
        public void Before(BeforeRunContext context)
        {
            Log($"[BEFORE] Starting {context.RelativeFilePath}");
            // Open browser, navigate to login page
        }

        public void After(AfterRunContext context)
        {
            Log($"[AFTER] Finished {context.RelativeFilePath}");
            // Close browser, clean up
        }

        [TestCase]
        public void Execute()
        {
            // Before() has already run

            // Arrange
            string username = "testuser";

            // Act
            var result = workflows.Login(username: username, password: "pass123");

            // Assert
            testing.VerifyExpression(result.success, "Login should succeed");

            // After() will run automatically
        }
    }
}
```

Use this when only one or a few files need setup/teardown.

## Pattern 2: Partial Class CodedWorkflow — Hooks for ALL Files

Extend the auto-generated `CodedWorkflow` partial class with `IBeforeAfterRun`. The hooks apply to **every** workflow and test case in the project automatically.

**File: `CodedWorkflowHooks.cs`** (Coded Source File — NOT a workflow, no entry point)

```csharp
using UiPath.CodedWorkflows;

namespace {{PROJECT_NAME}}
{
    public partial class CodedWorkflow : IBeforeAfterRun
    {
        public void Before(BeforeRunContext context)
        {
            Log($"[BEFORE] Execution started for {context.RelativeFilePath}");

            // Example: Open application
            // var app = uiAutomation.Open("myApp");

            // Example: Log in
            // Login("testuser", "password");
        }

        public void After(AfterRunContext context)
        {
            Log($"[AFTER] Execution finished for {context.RelativeFilePath}");

            // Example: Close application
            // uiAutomation.Close(app);

            // Example: Clean up test data
            // DeleteTestData();
        }
    }
}
```

The auto-generated `CodedWorkflow` in `.local/.codedworkflows/CodedWorkflow.cs` is already a `partial class`. By adding another partial definition, the compiler merges them — every workflow and test case inherits the hooks with no code changes.

## Pattern 3: Partial Class CodedWorkflow — Shared Logic (Without Hooks)

The partial class pattern is useful beyond hooks. You can add shared methods, properties, or constants available to all workflows and test cases:

**File: `CodedWorkflowExtensions.cs`** (Coded Source File)

```csharp
using UiPath.CodedWorkflows;

namespace {{PROJECT_NAME}}
{
    public partial class CodedWorkflow
    {
        // Shared helper available in all workflows and test cases
        protected string GetEnvironmentUrl()
        {
            var env = system.GetAsset("Environment").ToString();
            return env == "prod" ? "https://app.example.com" : "https://staging.example.com";
        }

        // Shared constant
        protected const int MaxRetries = 3;
    }
}
```

Then in any workflow:
```csharp
[Workflow]
public void Execute()
{
    string url = GetEnvironmentUrl();  // available via partial class
    Log($"Using environment: {url}");
}
```

## Key Points

- **`IBeforeAfterRun`** is an interface — any `CodedWorkflow`-derived class can implement it
- **`partial class CodedWorkflow`** is a C# feature — extends the auto-generated class for all files in the project
- **They combine:** use `partial class CodedWorkflow : IBeforeAfterRun` when you want hooks on every file
- **Use `IBeforeAfterRun` on individual files** when only specific workflows/test cases need setup/teardown
- **Use `partial class CodedWorkflow`** (without hooks) to add shared methods, properties, or constants
- **Context objects** (`BeforeRunContext`, `AfterRunContext`) provide `RelativeFilePath`, `WorkflowFilePath`, etc.
- **After() runs even on failure** — guaranteed cleanup

## When to Use Which

| Scenario | Pattern |
|----------|---------|
| One test case needs its own setup/teardown | Pattern 1: `IBeforeAfterRun` on the class |
| All test cases share the same setup/teardown | Pattern 2: `partial class CodedWorkflow : IBeforeAfterRun` |
| Shared helper methods for all workflows | Pattern 3: `partial class CodedWorkflow` (no hooks) |
| All of the above | Combine patterns 2 + 3 in one or more partial files |
