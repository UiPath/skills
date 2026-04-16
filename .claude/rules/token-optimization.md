# Token Optimization — Terse Documentation Mode

All skill documentation and agent-facing prose in this repo MUST follow these rules. Technical accuracy stays. Fluff dies.

## 1. Prose Compression

Strip every word that does not carry information. Drop articles. Fragments OK. Short synonyms. Technical terms exact.

Pattern: `[thing] [action] [reason]. [next step].`

### What to Drop

| Category | Examples | Instead |
|----------|----------|---------|
| **Articles** | a, an, the | Delete — LLM readers parse without them |
| **Filler** | just, really, basically, actually, simply, essentially, quite, very, pretty much | Delete |
| **Hedging** | I think, might, should consider, could potentially, it seems like, perhaps | State fact directly |
| **Pleasantries** | Sure!, Certainly, Of course, Happy to help, Great question | Start with answer |
| **Preamble** | "The reason this works is because...", "What this means is that...", "It's important to note that..." | State fact |
| **Redundant context** | "as mentioned above", "as we discussed", "note that" | Delete |
| **Weak verbs** | "perform a validation" → "validate", "make a determination" → "determine", "do an installation" → "install" | Use direct verb |
| **Subject padding** | "You should run", "You need to check", "You can use", "You'll want to" | Lead with verb: "Run", "Check", "Use" |

### What to Keep

- Technical terms — exact, never abbreviated (no "DB" for "database", no "auth" for "authentication")
- Tables and structured data — unchanged
- Numbered rules and ordered steps — keep numbering
- Section headers — keep for navigation
- Links and references — keep all
- Conditional logic (if/then/else), causal chains

### Examples

**Before:** "When you need to validate a workflow, you should run the following command to check for errors:"
**After:** "Validate with:"

**Before:** "The agent returns the generated context document as its response."
**After:** "Agent returns generated context document."

**Before:** "Each service on `CodedWorkflow` requires its NuGet package in `project.json`. Without it, you will get a `CS0103` error."
**After:** "Each service on `CodedWorkflow` requires its NuGet package in `project.json`. Without it: `CS0103`."

## 2. Code Block Comment Stripping

Strip comments from code examples when surrounding prose already explains intent. Comments help the reader — if prose already does that, comment is duplicate tokens.

### Strip when

- Comment restates what next line of code does: `// Create client` above `var client = new Client()`
- Comment restates section heading or surrounding bullet point
- Comment is placeholder like `// TODO` or `// Add your logic here` in non-template files

### Keep when

- Comment annotates non-obvious behavior (e.g., `// Must be called before Dispose`)
- Comment is inside **template** file (`assets/templates/`) — templates are scaffolding, comments are part of deliverable
- Comment explains workaround or UiPath-specific quirk not covered by surrounding prose
- Comment marks section boundary in long code block (e.g., `// --- Phase 2: Validation ---`)

## 3. XAML Namespace Deduplication

XAML code examples repeat standard `xmlns` declarations in every block. Agent only needs to see them once.

### Rule

1. **First XAML code block in file**: include full `xmlns` declarations
2. **Subsequent XAML code blocks in same file**: replace standard UiPath xmlns lines with `<!-- standard xmlns omitted -->`
3. Only omit **standard** xmlns — keep any non-standard or example-specific xmlns that differs from first block

### Standard UiPath xmlns (safe to omit after first occurrence)

```
xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
xmlns:sap="http://schemas.microsoft.com/netfx/2009/xaml/activities/presentation"
xmlns:sap2010="http://schemas.microsoft.com/netfx/2010/xaml/activities/presentation"
xmlns:scg="clr-namespace:System.Collections.Generic;assembly=..."
xmlns:sco="clr-namespace:System.Collections.ObjectModel;assembly=..."
xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
xmlns:ui="http://schemas.uipath.com/workflow/activities"
xmlns:upa="http://schemas.uipath.com/workflow/activities"
xmlns:upas="http://schemas.uipath.com/workflow/activities/start"
```

### NOT standard (never omit)

- Package-specific xmlns added for particular activity (e.g., connector-specific namespaces)
- xmlns that only appear in one example and are specific to that example's point

## Scope

- Applies to: SKILL.md files, reference docs, asset templates, PR descriptions, review comments
- Does NOT apply to: code in user projects, CLI commands, YAML frontmatter, commit messages
- Safety override: use full clarity for security warnings, irreversible actions, and multi-step sequences where brevity risks misreading
