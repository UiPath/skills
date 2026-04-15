# Implementation Mode Guide

Guidelines for recommending XAML, Coded C#, or Hybrid implementation mode in the SDD. The skill that builds the workflows owns the final, detailed decision — this guide produces a directional recommendation so the project structure and data model sections are coherent.

## Decision Summary

| Process Characteristic | Recommended Mode |
|---|---|
| Primarily UI automation (clicking, typing, reading screens) | **XAML** |
| Simple linear or transactional flow (REFramework) | **XAML** |
| Heavy use of pre-built activity packages (SAP, Salesforce, Excel) | **XAML** |
| Significant data transformation (parsing, regex, hashing, aggregation) | **Coded C#** |
| REST API integrations (HTTP calls, pagination, auth tokens) | **Coded C#** |
| Complex branching logic (5+ decision paths) | **Coded C#** |
| Custom data models needed (typed DTOs, enums) | **Coded C#** |
| UI automation AND complex data logic | **Hybrid** |
| Multiple applications with different interaction patterns | **Hybrid** |

## When to Recommend Each Mode

### XAML (Default)

Recommend XAML when:
- The process is primarily about interacting with application UIs
- Steps map directly to UiPath activities (Open Browser, Type Into, Click, Get Text, etc.)
- The process fits the REFramework pattern (queue/transaction-based with retry)
- Data transformations between steps are simple (assignments, string concatenation, basic formatting)
- The team is expected to maintain the automation using Studio's visual designer

XAML is the safest default. Most PDD-described processes are UI-heavy and transactional.

### Coded C#

Recommend Coded C# when:
- The process involves significant non-UI logic (data parsing, calculations, API calls)
- Business rules are complex enough to benefit from unit testing
- The process manipulates structured data that benefits from typed models (classes, enums)
- There is minimal UI interaction, or the UI interaction is secondary to the data processing

### Hybrid

Recommend Hybrid when:
- The process has both heavy UI automation AND complex data logic
- UI orchestration is best done in XAML (visual, activity-based), but business logic is best done in C# (testable, type-safe)
- Pattern: XAML workflows for UI steps, Coded Source Files for data models and helpers, optionally Coded Workflows for pure logic steps

## How to Write the Recommendation

In the SDD's "Implementation Mode" section, write:

1. **Recommendation** — one of: XAML, Coded C#, Hybrid
2. **Justification** — 2-3 sentences explaining why, referencing specific process characteristics
3. **Note** — "This is a preliminary recommendation. Detailed decision criteria will be applied during implementation and may adjust this choice."

### Example Recommendations

**XAML example:**
> **Recommendation:** XAML with REFramework
>
> The process is primarily UI-driven, interacting with two web applications through form fills, button clicks, and text reads. Data transformations are limited to simple value mappings between the two systems. REFramework fits because the process is transactional — each claim is an independent work item with defined retry logic.

**Hybrid example:**
> **Recommendation:** Hybrid (XAML orchestration + Coded C# data models and logic)
>
> The process combines heavy UI automation (two web portals) with non-trivial data processing (SHA1 hashing, multi-field validation, regex matching). XAML handles the UI interaction sequences and REFramework transaction loop. Coded Source Files define typed data models (ClientData, SecurityHash) and implement the hashing logic that would be cumbersome in XAML's Invoke Code activities.

## Impact on SDD Sections

The implementation mode affects how other SDD sections are written:

| SDD Section | XAML | Coded C# | Hybrid |
|---|---|---|---|
| Data Definitions | Dictionary keys, DataTable columns | C# classes, structs, enums | C# types (shared by both XAML and coded) |
| Workflow Inventory | `.xaml` file extensions | `.cs` file extensions | Mix of `.xaml` and `.cs` |
| Project Structure | Standard XAML folders | Coded project layout | XAML structure + source files |
| Testing Strategy | XAML test workflows | `[TestCase]` coded test cases | Coded tests for logic, manual/XAML tests for UI |
