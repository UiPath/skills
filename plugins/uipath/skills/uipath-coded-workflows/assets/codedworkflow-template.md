# UiPath Coded Workflow Templates

Ready-to-use templates for UiPath coded workflow files. Replace placeholders in `{{PLACEHOLDER}}` format.

> **Using statements:** These templates include only the minimal required usings. Add service-specific usings based on actual usage — see [coding-guidelines.md](../references/coding-guidelines.md) for the full mapping.

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

Parameters with default values become **optional** when the workflow is invoked via `workflows.MyWorkflow()` — callers can omit them to use the defaults, or pass explicit values to override. In the companion `.cs.json`, default-valued parameters should still be listed as `ArgumentType: 0` (Input) but with `"IsRequired": false`.

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