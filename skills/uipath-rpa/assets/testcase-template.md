# UiPath Coded Test Cases Templates

Ready-to-use templates for UiPath coded test cases files. Replace placeholders in `{{PLACEHOLDER}}` format.

> **Using statements:** These templates include only the minimal required usings. Add service-specific usings based on actual usage — see [coding-guidelines.md](../references/coded/coding-guidelines.md) for the full mapping.

---

## Coded Test Case (.cs) — Basic

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

## Coded Test Case (.cs) — Data-Driven with Default Parameters

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

## Coded Test Case (.cs) — Data-Driven with Test Data Queue

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
