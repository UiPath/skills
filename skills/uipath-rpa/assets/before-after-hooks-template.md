# Before/After Hooks Template

## IBeforeAfterRun on Individual Workflow/Test Case

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

## Partial Class CodedWorkflow — Hooks for ALL Files

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

## Partial Class CodedWorkflow — Shared Logic (Without Hooks)

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

## Usage in Any Workflow

```csharp
[Workflow]
public void Execute()
{
    string url = GetEnvironmentUrl();  // available via partial class
    Log($"Using environment: {url}");
}
```
