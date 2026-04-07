# Before/After Hooks Template

Use this pattern when you need shared setup and teardown logic that runs before and after ALL test cases (or workflows) in a project.

## CodedWorkflowBase.cs — Base Class Template

This is a **Coded Source File** (NOT a workflow — no `.cs.json`, no entry point).

```csharp
using UiPath.CodedWorkflows;

namespace {{PROJECT_NAME}}
{
    /// <summary>
    /// Base class for all workflows/test cases in this project.
    /// Implements IBeforeAfterRun to provide shared setup/teardown logic.
    /// </summary>
    public class CodedWorkflowBase : CodedWorkflow, IBeforeAfterRun
    {
        /// <summary>
        /// Runs BEFORE each workflow/test case Execute method.
        /// Use for: opening apps, logging in, navigating to start state, setting up test data.
        /// </summary>
        public void Before(BeforeRunContext context)
        {
            Log($"[BEFORE] Execution started for {context.RelativeFilePath}");

            // Example: Open application
            // var app = uiAutomation.Open("myApp");

            // Example: Log in
            // Login("testuser", "password");

            // Example: Navigate to starting state
            // NavigateToHomePage();
        }

        /// <summary>
        /// Runs AFTER each workflow/test case Execute method (even if it fails).
        /// Use for: closing apps, cleaning up test data, logging out, teardown.
        /// </summary>
        public void After(AfterRunContext context)
        {
            Log($"[AFTER] Execution finished for {context.RelativeFilePath}");

            // Example: Close application
            // uiAutomation.Close(app);

            // Example: Clean up test data
            // DeleteTestData();

            // Example: Log out
            // Logout();
        }
    }
}
```

## Using the Base Class in Workflows

Once `CodedWorkflowBase.cs` exists, change your workflows/test cases to inherit from `CodedWorkflowBase` instead of `CodedWorkflow`:

### Example Test Case Inheriting from CodedWorkflowBase

```csharp
using System;
using UiPath.CodedWorkflows;
using UiPath.UIAutomationNext.API.Contracts;
using {{PROJECT_NAME}}.ObjectRepository;  // for Descriptors.*

namespace {{PROJECT_NAME}}
{
    public class TestInvoiceCreation : CodedWorkflowBase  // ← Inherit from CodedWorkflowBase
    {
        [TestCase]
        public void Execute()
        {
            // Before() has already run automatically at this point

            // GIVEN (Arrange) — prepare the test scenario
            Log("Creating new invoice");

            // WHEN (Act) — perform the action under test
            // Use Object Repository descriptors (Descriptors.App.Screen.Element) — never hardcode selectors
            var formScreen = uiAutomation.Open(Descriptors.InvoiceApp.InvoiceForm);
            formScreen.TypeInto(Descriptors.InvoiceApp.InvoiceForm.InvoiceNumber, "INV-001");
            formScreen.TypeInto(Descriptors.InvoiceApp.InvoiceForm.Amount, "1500.00");
            formScreen.Click(Descriptors.InvoiceApp.InvoiceForm.SubmitButton);

            // THEN (Assert) — verify expected results
            var confirmScreen = uiAutomation.Attach(Descriptors.InvoiceApp.Confirmation);
            var confirmation = confirmScreen.GetText(Descriptors.InvoiceApp.Confirmation.Message);
            testing.VerifyExpression(confirmation.Contains("successfully"), "Invoice should be created successfully");

            // After() will run automatically after this method completes
        }
    }
}
```

### Example Workflow Inheriting from CodedWorkflowBase

```csharp
using System;
using UiPath.CodedWorkflows;

namespace {{PROJECT_NAME}}
{
    public class ProcessInvoices : CodedWorkflowBase  // ← Inherit from CodedWorkflowBase
    {
        [Workflow]
        public void Execute(string folderPath)
        {
            // Before() has already run automatically at this point

            Log($"Processing invoices from {folderPath}");

            // ... workflow logic ...

            // After() will run automatically after this method completes
        }
    }
}
```

## Key Points

- **CodedWorkflowBase.cs is a Coded Source File** — no `.cs.json`, no entry point, not listed in `project.json`
- **Before() runs automatically** before EVERY workflow/test case that inherits from `CodedWorkflowBase`
- **After() runs automatically** after EVERY workflow/test case (even if it throws an exception)
- **Context objects provide metadata** — `RelativeFilePath`, `WorkflowFilePath`, etc.
- **All workflows/test cases must inherit** from `CodedWorkflowBase` to get the hooks
- **Perfect for test projects** — shared app setup/teardown, login/logout, test data management

## When to Use This Pattern

✅ **Use when:**
- Multiple test cases need the same setup/teardown (open app, login, etc.)
- You want consistent logging for all workflow executions
- You need guaranteed cleanup even if a workflow fails
- You're building a test suite with shared preconditions

❌ **Don't use when:**
- Each workflow has unique setup requirements
- Setup is lightweight and can be done inline
- You only have one or two workflows/test cases
