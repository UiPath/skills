# UiPath Coded Templates (Workflows, Test Cases, Helpers, Hooks)

Ready-to-use templates for UiPath coded files — workflows, test cases, helper/utility classes, and Before/After hooks. Replace placeholders in `{{PLACEHOLDER}}` format.

> **Using statements:** These templates include only the minimal required usings. Add service-specific usings based on actual usage — see [operations-guide.md § Coding Guidelines](../references/coded/operations-guide.md#coding-guidelines) for the full mapping.

---

## Coded Workflow (.cs) — Void

```csharp
using System;
using System.Collections.Generic;
using UiPath.CodedWorkflows;
// Add service-specific usings as needed — see references/coding-guidelines.md

namespace {{PROJECT_NAME}}
{
    public class {{CLASS_NAME}} : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            {{IMPLEMENTATION}}
        }
    }
}
```

## Coded Workflow (.cs) — With Return Value

```csharp
using System;
using System.Collections.Generic;
using UiPath.CodedWorkflows;
// Add service-specific usings as needed — see references/coding-guidelines.md

namespace {{PROJECT_NAME}}
{
    public class {{CLASS_NAME}} : CodedWorkflow
    {
        [Workflow]
        public {{RETURN_TYPE}} Execute({{PARAMETERS}})
        {
            {{IMPLEMENTATION}}
            return {{RETURN_TYPE}};
        }
    }
}
```

## Coded Workflow (.cs) — With Tuple Return (Multiple Outputs)

```csharp
using System;
using System.Collections.Generic;
using UiPath.CodedWorkflows;
// Add service-specific usings as needed — see references/coding-guidelines.md

namespace {{PROJECT_NAME}}
{
    public class {{CLASS_NAME}} : CodedWorkflow
    {
        [Workflow]
        public ({{TYPE1}} {{name1}}, {{TYPE2}} {{name2}}) Execute({{PARAMETERS}})
        {
            {{IMPLEMENTATION}}
            return ({{name1}}: value1, {{name2}}: value2);
        }
    }
}
```

## Coded Workflow (.cs) — With Single InOut Argument

A single input argument named `Output` with the same type as the return value becomes an InOut argument.

```csharp
using System;
using System.Collections.Generic;
using UiPath.CodedWorkflows;
// Add service-specific usings as needed — see references/coding-guidelines.md

namespace {{PROJECT_NAME}}
{
    public class {{CLASS_NAME}} : CodedWorkflow
    {
        [Workflow]
        public {{RETURN_TYPE}} Execute({{RETURN_TYPE}} Output)
        {
            {{IMPLEMENTATION}}
            return Output;
        }
    }
}
```

## Coded Workflow (.cs) — With Multiple InOut Arguments (Tuple Return)

When multiple arguments are both input and output, the return type must be a tuple whose names and types match the input parameters.

```csharp
using System;
using System.Collections.Generic;
using UiPath.CodedWorkflows;
// Add service-specific usings as needed — see references/coding-guidelines.md

namespace {{PROJECT_NAME}}
{
    public class {{CLASS_NAME}} : CodedWorkflow
    {
        [Workflow]
        public ({{TYPE1}} {{name1}}, {{TYPE2}} {{name2}}) Execute({{TYPE1}} {{name1}}, {{TYPE2}} {{name2}})
        {
            {{IMPLEMENTATION}}
            return ({{name1}}: value1, {{name2}}: value2);
        }
    }
}
```

## Coded Workflow (.cs) — Async

```csharp
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using UiPath.CodedWorkflows;
// Add service-specific usings as needed — see references/coding-guidelines.md

namespace {{PROJECT_NAME}}
{
    public class {{CLASS_NAME}} : CodedWorkflow
    {
        [Workflow]
        public async Task Execute()
        {
            {{IMPLEMENTATION}}
        }
    }
}
```

## Coded Workflow (.cs) — With Default Parameters

Parameters with default values become **optional** when the workflow is invoked via `workflows.MyWorkflow()` — callers can omit them to use the defaults, or pass explicit values to override.

```csharp
using System;
using System.Collections.Generic;
using UiPath.CodedWorkflows;
// Add service-specific usings as needed — see references/coding-guidelines.md

namespace {{PROJECT_NAME}}
{
    public class {{CLASS_NAME}} : CodedWorkflow
    {
        [Workflow]
        public void Execute({{TYPE}} {{paramName}} = {{defaultValue}})
        {
            {{IMPLEMENTATION}}
        }
    }
}
```

**Example:**
```csharp
[Workflow]
public void Execute(string browser = "chrome.exe", int retryCount = 3)
{
    Log($"Using browser: {browser}, retries: {retryCount}");
}
```

**Calling from another workflow:**
```csharp
// All defaults — browser="chrome.exe", retryCount=3
workflows.LaunchApp();

// Override one, keep the other default
workflows.LaunchApp(browser: "msedge.exe");

// Override both
workflows.LaunchApp(browser: "msedge.exe", retryCount: 5);
```

---

## Coded Test Case Templates


### Coded Test Case (.cs) — Basic

```csharp
using System;
using System.Collections.Generic;
using UiPath.CodedWorkflows;
// Add service-specific usings as needed — see references/coding-guidelines.md

namespace {{PROJECT_NAME}}
{
    public class {{CLASS_NAME}} : CodedWorkflow
    {
        [TestCase]
        public void Execute()
        {
            // Arrange
            {{ARRANGE}}

            // Act
            {{ACT}}

            // Assert
            testing.VerifyExpression({{ASSERTION}});
        }
    }
}
```

### Coded Test Case (.cs) — Data-Driven with Default Parameters

```csharp
using System;
using System.Collections.Generic;
using UiPath.CodedWorkflows;
// Add service-specific usings as needed — see references/coding-guidelines.md

namespace {{PROJECT_NAME}}
{
    public class {{CLASS_NAME}} : CodedWorkflow
    {
        [TestCase]
        public void Execute(System.String {{paramName}} = "{{defaultValue}}")
        {
            // Arrange
            {{ARRANGE}}

            // Act
            {{ACT}}

            // Assert
            testing.VerifyExpression({{ASSERTION}});
        }
    }
}
```

### Coded Test Case (.cs) — Data-Driven with Test Data Queue

```csharp
using System;
using System.Collections.Generic;
using UiPath.CodedWorkflows;
// Add service-specific usings as needed — see references/coding-guidelines.md

namespace {{PROJECT_NAME}}
{
    public class {{CLASS_NAME}} : CodedWorkflow
    {
        [TestCase]
        public void Execute()
        {
            // Arrange — get test data from queue
            var item = testing.GetTestDataQueueItem("{{QUEUE_NAME}}");
            {{EXTRACT_FIELDS}}

            // Act
            {{ACT}}

            // Assert
            testing.VerifyExpression({{ASSERTION}});
        }
    }
}
```

---

## Helper/Utility Class Templates

### Helper/Utility Class (.cs) — No Attribute

```csharp
using System;
using System.Collections.Generic;

namespace {{PROJECT_NAME}}
{
    public class {{CLASS_NAME}}
    {
        {{IMPLEMENTATION}}
    }
}
```

IMPORTANT!: Helper classes do NOT inherit from `CodedWorkflow`, do NOT have `[Workflow]` or `[TestCase]` attributes. They are NOT entry points and do not appear in the fileInfoCollection attribute from `project.json`.

---

## Before/After Hooks Templates

### IBeforeAfterRun on Individual Workflow/Test Case

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

### Partial Class CodedWorkflow — Hooks for ALL Files

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

### Partial Class CodedWorkflow — Shared Logic (Without Hooks)

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

### Usage in Any Workflow

```csharp
[Workflow]
public void Execute()
{
    string url = GetEnvironmentUrl();  // available via partial class
    Log($"Using environment: {url}");
}
```
