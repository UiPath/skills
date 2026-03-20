# UiPath Coded Helper/Utility Classes Templates

Ready-to-use templates for UiPath coded class files. Replace placeholders in `{{PLACEHOLDER}}` format.

---

## Helper/Utility Class (.cs) — No Attribute

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

IMPORTANT!: Helper classes do NOT inherit from `CodedWorkflow`, do NOT have `[Workflow]` or `[TestCase]` attributes, and do NOT have a companion `.cs.json` file. They are NOT entry points and do not appear in the fileInfoCollection attribute from `project.json`.
