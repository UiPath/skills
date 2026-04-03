# Phase 2: Genome Extraction Skill - Research

**Researched:** 2026-04-02
**Domain:** UiPath project analysis and genome specification generation
**Confidence:** HIGH

## Summary

This phase creates a new skill (`uipath-genome-extraction`) that reads an existing UiPath Studio project and produces a genome markdown file following TEMPLATE.md format. The skill is structurally parallel to the authoring skill (Phase 1), but instead of interviewing a user, it analyzes source files: `project.json`, `.xaml`, `.cs`, `.cs.json`, and `.flow` files. The extraction skill must produce output indistinguishable from one created by the authoring skill.

The domain is well-understood. The genome template, population matrix, skill mapping rules, and UiPath project file formats are all documented in existing references. The primary challenge is designing the extraction logic: mapping UiPath file-format signals (package dependencies, activity namespaces, XAML control flow, coded workflow patterns, error handling blocks) to genome sections. This is a knowledge-mapping problem, not a technology problem. The skill is pure markdown (SKILL.md + references), no code to build.

**Primary recommendation:** Structure the extraction skill as SKILL.md (workflow + critical rules) plus two reference files: an extraction-mapping guide (signal-to-genome-section mapping tables) and a project-analysis guide (what to read from each file type and how to interpret it). Mirror the authoring skill's patterns exactly: same population matrix, same section ordering, same critical rules about acceptance criteria format and blueprint preamble.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Interaction model**: Fully autonomous — agent reads the project, produces a complete genome, then offers edits. Mirrors authoring skill's "write immediately, offer edits after" pattern
- **Ambiguity handling**: When the agent encounters ambiguity (unclear business logic, multiple entry points), it flags low-confidence sections in the genome with a visible marker (e.g., "Inferred") rather than asking the user upfront
- **Complexity inference**: Agent infers project complexity (simple/medium/complex) from project signals (file count, dependency count, entry points, orchestration patterns) and adjusts section depth per the same population matrix as the authoring skill
- **File naming**: Derived from project.json `name` field, slugified (e.g., "InvoiceProcessing" -> `invoice-processing-genome.md`)
- **Extraction depth**: Structural + obvious logic: extract what's structurally visible (workflow steps, target apps, error handling patterns, conditional branches) and infer business rules from if/switch conditions and validation logic, but don't speculate on business intent beyond what the code expresses
- **Generalization**: Hardcoded values AND application choices become Configuration Questions with original values as defaults. Applications become configurable (e.g., "Outlook" becomes "Which email provider? (source project used: Outlook)")
- **Platform feature detection**: Detect from dependencies and activity usage; map to Target Applications (Document Understanding, Integration Service) and note Orchestrator dependencies in Configuration Questions
- **Acceptance criteria**: Describe functional outcomes, not code-level assertions ("Given an invoice PDF, extracts vendor and amount" not "Uses ReadPDF activity")
- **Project scope**: User specifies a directory; agent scans for project.json, falls back to .xaml/.cs files. Read all relevant files (project.json, all .xaml, all .cs excluding .local/.objects/auto-generated, .cs.json metadata, .flow files). No file count limit.
- **Mixed projects**: Handle mixed XAML + coded workflow projects as a unified genome — Build With maps each step to the appropriate skill
- **Error handling extraction**: Pattern detection: identify TryCatch blocks, retry loops, GlobalHandler, exception types caught; map to genome Error Handling section as behavioral descriptions
- **Output fidelity**: Overview section contains generalized purpose and context. Output genome is indistinguishable from one created by the authoring skill — no extraction markers or provenance notes. Blueprint preamble required.

### Claude's Discretion
- Specific complexity inference heuristics and thresholds for extracted projects
- How to order workflow steps when the call graph has parallel branches
- Exact format of the ambiguity flag markers
- How to handle projects with no clear entry point (no `main` in project.json)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| EXTR-01 | Agent reads UiPath project structure (project.json, .xaml, .cs, .flow files) to understand the solution | Project file format analysis: project.json schema, XAML anatomy, coded workflow patterns, .flow JSON format. All documented in existing references (project-structure.md, xaml-basics-and-rules.md, codedworkflow-reference.md, flow-file-format.md). |
| EXTR-02 | Agent identifies target applications, workflow steps, and business rules from project files | Signal extraction mapping: package dependencies -> target apps, XAML activity sequences -> workflow steps, If/Switch/condition expressions -> business rules. Detailed mapping tables in Architecture Patterns. |
| EXTR-03 | Agent produces genome markdown following TEMPLATE.md format from analyzed solution | Same genome template (skills/shared/genome/genome-template.md), same population matrix from authoring skill, same section ordering (Build With before Workflow). |
| EXTR-04 | Agent detects platform features in use (Document Understanding, Integration Service, Orchestrator queues, etc.) | Package dependency fingerprinting: specific package IDs map to platform features. XAML namespace patterns reveal Integration Service connectors. See Platform Feature Detection section below. |
| EXTR-05 | Agent extracts error handling patterns and maps them to genome error handling section | TryCatch blocks in XAML, try/catch in .cs, GlobalHandler references, Retry Scope activities, exception type analysis. Mapped to behavioral descriptions in the genome. |

</phase_requirements>

## Standard Stack

This phase produces only markdown documentation (SKILL.md and reference files). No libraries, packages, or build tools are involved.

| Artifact | Purpose | Convention |
|----------|---------|------------|
| `skills/uipath-genome-extraction/SKILL.md` | Skill definition with workflow and critical rules | YAML frontmatter + markdown body per skill-structure.md |
| `skills/uipath-genome-extraction/references/extraction-mapping-guide.md` | Signal-to-genome-section mapping tables | kebab-case `-guide.md` suffix |
| `skills/uipath-genome-extraction/references/project-analysis-guide.md` | File-by-file extraction instructions | kebab-case `-guide.md` suffix |
| `skills/shared/genome/genome-template.md` | Shared genome template (already exists) | Read-only reference, not duplicated |
| `CODEOWNERS` | Add entry for new skill path | Append line |

## Architecture Patterns

### Recommended Skill Structure

```
skills/uipath-genome-extraction/
  SKILL.md                                # Skill definition
  references/
    extraction-mapping-guide.md           # Signal -> genome section mapping
    project-analysis-guide.md             # File-by-file extraction instructions
```

### Pattern 1: Project Signal Extraction Pipeline

The agent follows a fixed sequence to analyze a UiPath project. Each step feeds the next.

**Step 1 - Locate and read project.json:**
- Extract `name` (genome file name), `main` (entry point), `dependencies` (package list), `designOptions.outputType`, `expressionLanguage`, `targetFramework`, `entryPoints`
- If project.json not found, fall back to scanning for .xaml/.cs files directly

**Step 2 - Classify file types and build inventory:**
- `.xaml` files -> XAML workflows (analyze with Step 3a)
- `.cs` files (excluding `.local/`, `.objects/`, `.codedworkflows/` auto-generated) -> Coded workflows (analyze with Step 3b)
- `.cs.json` files -> Metadata for coded workflows (arguments, display name)
- `.flow` files -> Maestro flow definitions (analyze with Step 3c)

**Step 3a - XAML analysis:**
- Root element and workflow type: `Sequence`, `Flowchart`, `StateMachine`
- `xmlns` declarations -> which activity packages are used
- Activity elements -> workflow steps (e.g., `ui:LogMessage`, `umam:GetNewestEmail`)
- `x:Members` -> arguments (In/Out/InOut)
- `If`, `Switch`, `FlowDecision` -> business rules / conditional logic
- `TryCatch`, `Retry Scope` -> error handling patterns
- `ConnectionId` attributes -> Integration Service connections
- `isactr:ConnectorActivity` -> Integration Service connector usage
- Variable names and expressions -> data flow understanding

**Step 3b - Coded workflow analysis (.cs files):**
- Service property usage (`system.`, `excel.`, `office365.`, `testing.`) -> target applications
- `connections.*` usage -> Integration Service connections
- `workflows.*` calls -> workflow invocation graph
- `try/catch` blocks, exception types -> error handling
- Method signatures and attributes (`[Workflow]`, `[TestCase]`) -> entry points
- C# control flow (if/switch/loops) -> business rules

**Step 3c - Flow file analysis (.flow JSON):**
- Node types (`core.action.script`, `core.action.invoke`, etc.) -> workflow steps
- Edge connections -> step ordering
- Script content in `inputs.script` -> business logic
- Variable definitions -> data flow

**Step 4 - Map signals to genome sections** (see Extraction Mapping below)

**Step 5 - Infer complexity and populate per population matrix**

**Step 6 - Write genome file and offer edits**

### Pattern 2: Dependency-to-Target-Application Mapping

The `dependencies` field in project.json is the single most reliable signal for Target Applications.

| Package ID | Target Application | Role |
|------------|-------------------|------|
| `UiPath.UIAutomation.Activities` | Desktop/Browser apps | UI interaction |
| `UiPath.Excel.Activities` | Excel | Data source/target |
| `UiPath.Mail.Activities` | Email (generic) | Input/output |
| `UiPath.MicrosoftOffice365.Activities` | Outlook/Office 365 | Email, Calendar, OneDrive |
| `UiPath.GSuite.Activities` | Gmail/Google Workspace | Email, Drive, Sheets |
| `UiPath.Database.Activities` | Database (SQL) | Data source/target |
| `UiPath.WebAPI.Activities` | REST APIs | Integration |
| `UiPath.PDF.Activities` | PDF files | Document processing |
| `UiPath.Word.Activities` | Microsoft Word | Document generation |
| `UiPath.Presentations.Activities` | PowerPoint | Presentation generation |
| `UiPath.IntegrationService.Activities` | Integration Service | Connector runtime |
| `UiPath.IntelligentOCR.Activities` | Document Understanding | Document AI extraction |
| `UiPath.DocumentUnderstanding.ML.Activities` | Document Understanding | ML models |
| `UiPath.Cryptography.Activities` | Encryption/Security | Data protection |
| `UiPath.Testing.Activities` | Testing framework | Validation |
| `UiPath.Persistence.Activities` | Orchestrator queues/assets | Queue management |

### Pattern 3: Platform Feature Detection (EXTR-04)

Beyond package dependencies, detect platform features from usage patterns:

| Signal | Platform Feature | Where to Check |
|--------|-----------------|----------------|
| `UiPath.IntelligentOCR.Activities` or `UiPath.DocumentUnderstanding.*` in dependencies | Document Understanding | project.json |
| `UiPath.IntegrationService.Activities` in dependencies OR `ConnectionId` attributes in XAML OR `connections.*` in .cs | Integration Service | project.json, .xaml, .cs |
| `UiPath.Persistence.Activities` in dependencies OR queue-related activities | Orchestrator Queues | project.json, .xaml |
| `BuildClient("Orchestrator")` in .cs | Orchestrator API | .cs files |
| `UiPath.MicrosoftOffice365.Activities` or `UiPath.GSuite.Activities` | Cloud email/productivity | project.json |
| `GlobalHandler` referenced in project.json or separate GlobalHandler.xaml | Global error handling | project.json, file listing |
| `entryPoints` array with multiple entries | Multi-entry-point project | project.json |
| `.flow` files present | Maestro orchestration | file listing |
| `isAttended: true` or `requiresUserInteraction: true` in runtimeOptions | Attended automation | project.json |

### Pattern 4: Error Handling Extraction (EXTR-05)

Map source-code error patterns to behavioral descriptions in the genome:

| Source Pattern | XAML Signal | .cs Signal | Genome Description |
|----------------|------------|------------|-------------------|
| Retry on failure | `<RetryScope>` with `NumberOfRetries` attribute | `for` loop wrapping try/catch | "Retries Nx on [exception type]" |
| Catch and log | `<TryCatch>` with `<Catch>` containing `LogMessage` | `catch` with `Log()` call | "Logs [error type] and continues" |
| Catch and rethrow | `<TryCatch>` with `<Catch>` containing `Rethrow` | `catch` with `throw` | "Escalates [error type] to caller" |
| Global handler | `GlobalHandler.xaml` or project.json `globalHandler` field | N/A (XAML only) | "Global error handler catches unhandled exceptions" |
| Catch specific types | `<Catch x:TypeArguments="s:TimeoutException">` | `catch (TimeoutException)` | "Handles timeout exceptions separately" |
| Queue exception | Activities writing to Orchestrator exception queue | `system.AddQueueItem` with exception data | "Routes failed items to exception queue" |

### Pattern 5: Complexity Inference from Project Signals

The authoring skill uses description-based signals. Extraction uses project-based signals. Map to the same three levels:

| Signal | Simple | Medium | Complex |
|--------|--------|--------|---------|
| Total workflow files (.xaml + .cs) | 1-3 | 4-8 | 9+ |
| Unique package dependencies | 1-3 | 4-6 | 7+ |
| Entry points | 1 | 1-2 | 3+ |
| Integration Service connections | 0 | 0-1 | 2+ |
| Error handling patterns found | 0-1 | 2-3 | 4+ |
| Orchestrator features (queues, assets) | None | Optional | Present |
| Flow files present | No | No | Yes |
| Document Understanding packages | No | Optional | Often |

When ambiguous, default to the lower level (same rule as authoring skill).

### Pattern 6: Workflow Step Ordering from Call Graph

Build a call graph from entry point(s):
1. Start from `main` entry point in project.json
2. Follow `Invoke Workflow` activities in XAML (reads `FileName` attribute)
3. Follow `workflows.*` calls in .cs files
4. Order steps by their position in the call chain (depth-first from entry point)
5. For parallel branches (multiple Invoke calls at the same level), order by file position in the calling workflow
6. For projects with no clear entry point, order alphabetically and flag with ambiguity marker

### Anti-Patterns to Avoid

- **Duplicating reference material.** The extraction skill must NOT copy XAML rules, project structure docs, or coded workflow references. It references the fact that the agent should read `.xaml` and `.cs` files, but the deep format knowledge lives in the existing skills' references. The extraction skill's references cover only the mapping logic (signals -> genome sections).
- **Extraction provenance in output.** The genome must not contain phrases like "Extracted from project X" or "Source: Main.xaml". The genome reads as if authored from scratch.
- **Code-level acceptance criteria.** "Uses ReadPDF activity" is banned. "Given an invoice PDF, extracts vendor name and amount" is correct.
- **Speculating beyond code.** If the code has a `ReadRange` from Excel and a `TypeInto` on a web form, the genome says "Reads data from a spreadsheet and enters records into a web form." It does NOT say "Automates the monthly reporting process" unless comments or variable names clearly indicate this.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Genome template format | Custom section structure | `skills/shared/genome/genome-template.md` | Must match authoring skill output exactly |
| Skill mapping for Build With | Ad-hoc skill selection | `skills/uipath-genome-authoring/references/skill-mapping-guide.md` | Same 7-rule decision tree; ensures consistency |
| Population matrix | Custom depth rules | Authoring skill Step 6 population matrix | Extraction and authoring must produce identical section depth for same complexity level |
| Blueprint preamble | Writing it inline | Copy from genome template | HTML comment + blockquote must be exact |

## Common Pitfalls

### Pitfall 1: Confusing Auto-Generated Files with User Code
**What goes wrong:** Agent reads files in `.local/`, `.objects/`, or `.codedworkflows/` and tries to extract workflow logic from auto-generated boilerplate.
**Why it happens:** These directories contain .cs files that look like real code but are generated by Studio.
**How to avoid:** Exclude `.local/`, `.objects/`, and `.codedworkflows/` directories from analysis. Only read .cs files in the project root or user-created subdirectories. The `.cs.json` metadata files are safe to read (they contain argument definitions).
**Warning signs:** Seeing files like `CodedWorkflow.cs`, `ConnectionsManager.cs`, `ObjectRepository.cs`, `WorkflowRunnerService.cs`.

### Pitfall 2: Missing the Entry Point
**What goes wrong:** Agent analyzes all workflows as peers without understanding which is the entry point, producing a flat genome with no clear trigger or starting step.
**Why it happens:** Not reading `project.json` `main` or `entryPoints` fields first.
**How to avoid:** Always read project.json first. Use `main` field to identify the entry point. If `main` is missing, check `entryPoints` array. If both are missing, look for `Main.xaml` or `Main.cs` by convention. Flag as ambiguous if none found.
**Warning signs:** Genome workflow section starts with a helper/utility step rather than the trigger.

### Pitfall 3: Overly Specific Genome (Not Generalizing)
**What goes wrong:** Genome references specific file paths, server URLs, credential names, or email addresses from the source project, making it non-reusable.
**Why it happens:** Extracting literal values instead of generalizing to Configuration Questions.
**How to avoid:** Every hardcoded value (paths, URLs, email addresses, server names, credential names, queue names, threshold values, column names) becomes a Configuration Question with the original value as the default. Application choices also become configurable.
**Warning signs:** Configuration Questions section is empty or has only 1-2 items for a medium/complex project.

### Pitfall 4: Ignoring XAML ViewState and Namespace Noise
**What goes wrong:** Agent tries to extract meaningful logic from ViewState sections or xmlns declarations, producing nonsensical workflow steps.
**Why it happens:** ViewState is XML that looks structural but is designer layout metadata. xmlns declarations are plumbing.
**How to avoid:** Skip `<sap2010:WorkflowViewState.ViewStateManager>` entirely. Use xmlns only to identify which packages are in use (for target app detection), not as workflow steps.
**Warning signs:** Genome contains steps like "Configure designer layout" or references to ViewState elements.

### Pitfall 5: Expression Language Confusion in Business Rules
**What goes wrong:** Business rules extracted from VB expressions use VB syntax in the genome ("OrElse", "&" for concat), or C# expressions leak raw code.
**Why it happens:** Extracting expressions verbatim instead of translating to natural language.
**How to avoid:** Translate conditions to plain English. `[Amount > 10000 AndAlso Category = "Premium"]` becomes "If amount exceeds $10,000 and category is Premium." Check `expressionLanguage` in project.json to know which syntax you're reading.
**Warning signs:** Genome business rules contain programming syntax or operators.

### Pitfall 6: Integration Service Without Connection Context
**What goes wrong:** Agent detects IS connector activities but doesn't capture which services they connect to, producing a genome that says "uses Integration Service" without specifying the target application.
**Why it happens:** `ConnectionId` is a GUID that doesn't reveal the service name. The agent needs to look at the xmlns namespaces (e.g., `UiPath.MicrosoftOffice365`) or the activity class names to determine the actual service.
**How to avoid:** Map activity namespaces and package names to service names. `umam:GetNewestEmail` with `UiPath.MicrosoftOffice365.Activities` -> "Outlook/Office 365 email". `isactr:ConnectorActivity` with specific `UiPathActivityTypeId` -> look up in namespace imports.
**Warning signs:** Target Applications table has "Integration Service" as an app name rather than the actual service (e.g., "Salesforce", "ServiceNow").

### Pitfall 7: Producing a Genome That Reads Like a Code Summary
**What goes wrong:** Overview reads like "This project contains 5 XAML files and 3 coded workflows that process data" instead of describing the business purpose.
**Why it happens:** Agent describes what it found structurally rather than synthesizing the business intent.
**How to avoid:** Derive business purpose from: project name, file names, variable names, target applications involved, and the overall data flow. "InvoiceProcessor" project with PDF + Email + ERP packages -> "Processes incoming invoices from email, extracts data, and posts to ERP." When business intent is genuinely unclear, write the best interpretation and flag as "Inferred."
**Warning signs:** Overview mentions file counts, XAML types, or code structure instead of business outcomes.

## Code Examples

Not applicable -- this phase produces markdown skill documentation, not executable code. The skill's reference files will contain structured mapping tables and analysis instructions for the AI agent to follow.

## State of the Art

| Aspect | Current State | Impact |
|--------|--------------|--------|
| Genome template location | `skills/shared/genome/genome-template.md` (consolidated in Phase 1) | Extraction skill reads from same shared location |
| Blueprint preamble | Required on all genomes (added in Phase 1, commit 075705b) | Extraction must include the HTML comment and blockquote |
| Build With placement | Before Workflow section (Phase 1 decision) | Same ordering in extraction output |
| Skill mapping | 7-rule decision tree in `skill-mapping-guide.md` | Extraction uses same rules for Build With |
| Population matrix | In authoring SKILL.md Step 6 | Extraction follows same depth rules per complexity |

## Open Questions

1. **Ambiguity marker format**
   - What we know: The agent should flag low-confidence sections with a visible marker (e.g., "Inferred")
   - What's unclear: Exact syntax. Options: inline text "(Inferred)", italicized note, blockquote callout
   - Recommendation: Use italicized inline note: `*[Inferred from project signals]*` after the uncertain content. Lightweight, visible, easy to search and remove during editing.

2. **Projects with no entry point**
   - What we know: Some projects may not have `main` in project.json (libraries, test projects)
   - What's unclear: Whether to treat every workflow as a potential entry point or pick one heuristically
   - Recommendation: For `outputType: Library`, treat all public workflows as independent capabilities and list each in the Workflow section. For `outputType: Process` without a `main`, look for `Main.xaml`/`Main.cs` by convention, then fall back to alphabetical ordering with an ambiguity flag.

3. **Parallel branch ordering**
   - What we know: Some workflows invoke multiple sub-workflows at the same level
   - What's unclear: Whether to order by file position, alphabetically, or by importance
   - Recommendation: Order by file position in the calling workflow (top-to-bottom for Sequence, left-to-right for Flowchart). This matches visual reading order.

4. **Mixed XAML + coded workflow step attribution**
   - What we know: Projects can mix .xaml and .cs files. Build With maps to appropriate skill per step.
   - What's unclear: Whether a single workflow step in the genome can span both file types
   - Recommendation: No. Each genome workflow step maps to one file type and therefore one skill. If a .xaml workflow calls a .cs helper, the calling step uses the caller's skill and the helper becomes its own step if it represents a distinct business action.

## Sources

### Primary (HIGH confidence)
- `skills/shared/genome/genome-template.md` -- canonical genome template with all sections
- `skills/uipath-genome-authoring/SKILL.md` -- authoring workflow, population matrix, critical rules, anti-patterns
- `skills/uipath-genome-authoring/references/skill-mapping-guide.md` -- skill mapping table and 7-rule decision tree
- `skills/uipath-rpa-workflows/references/project-structure.md` -- project.json schema, directory layout, common packages
- `skills/uipath-rpa-workflows/references/xaml-basics-and-rules.md` -- XAML anatomy, workflow types, activity structure, expressions
- `skills/uipath-coded-workflows/references/codedworkflow-reference.md` -- service properties, connections, workflow invocation
- `skills/uipath-maestro-flow/references/flow-file-format.md` -- .flow JSON structure, nodes, edges
- `.genome_spec/examples/invoice-processing.md` -- medium complexity genome example
- `.genome_spec/examples/simple-data-transfer.md` -- simple genome example
- `.genome_spec/examples/email-triage.md` -- email/classification genome example
- `.genome_spec/DISCUSSION.md` -- genome design philosophy
- `CLAUDE.md`, `CONTRIBUTING.md`, `CODEOWNERS` -- repo conventions

### Secondary (MEDIUM confidence)
- `skills/uipath-coded-workflows/references/integration-service.md` -- Integration Service coded workflow patterns
- `skills/uipath-rpa-workflows/references/connector-capabilities.md` -- IS connector discovery commands

### Tertiary (LOW confidence)
- None. All findings are based on primary sources within the repository.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- this is a markdown-only skill, no libraries involved
- Architecture: HIGH -- all extraction signals documented in existing reference files; genome format established
- Pitfalls: HIGH -- derived from actual file format documentation and Phase 1 patterns

**Research date:** 2026-04-02
**Valid until:** 2026-05-02 (stable domain, no external dependencies)
