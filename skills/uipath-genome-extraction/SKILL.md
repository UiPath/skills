---
name: uipath-genome-extraction
description: "Analyze existing UiPath Studio projects and produce genome markdown specifications. TRIGGER when: user wants to extract a genome from an existing UiPath project, reverse-engineer an automation spec from source files, analyze a UiPath solution to create a blueprint, or says 'extract genome from this project'. DO NOT TRIGGER when: user wants to create a genome from a description (use uipath-genome-authoring), user wants to build/code an automation (use uipath-rpa-workflows, uipath-coded-workflows, uipath-coded-agents, uipath-coded-apps, or uipath-maestro-flow), or user is asking about UiPath platform/CLI setup (use uipath-platform)."
---

# Genome Extraction

Analyze existing UiPath Studio projects and produce genome markdown specifications. The agent reads the project files, extracts what the solution does, generalizes business-specific details into reusable configuration questions, and writes a genome that reads as if it were authored from scratch.

## When to Use This Skill

- User points to a UiPath project directory ("extract a genome from this project")
- User wants to reverse-engineer an automation spec from existing source files
- User wants to document what an existing UiPath solution does as a reusable blueprint
- User wants to create a genome from a .xaml, .cs, or .flow project (not from a description)

## Critical Rules

1. **Agent reads, never asks first.** Read the entire project directory before producing any output. Do not ask the user to describe what the project does -- the code tells you. Analyze all files: project.json, all .xaml, all .cs (excluding auto-generated directories), .cs.json metadata, and .flow files. See [project-analysis-guide.md](./references/project-analysis-guide.md) for file-by-file extraction instructions.

2. **Generalize, don't transcribe.** Every hardcoded value (file paths, URLs, email addresses, server names, credential names, queue names, threshold values, column names) becomes a Configuration Question with the original value as the default. Application choices become configurable too (e.g., "Which email provider? (source project used: Outlook)"). The genome is a reusable blueprint, not a transcript of one specific project.

3. **Complexity inferred from project signals.** Count workflow files, package dependencies, entry points, Integration Service connections, error handling patterns, and Orchestrator features. Map to simple/medium/complex using the complexity table in [extraction-mapping-guide.md](./references/extraction-mapping-guide.md). Never ask the user to declare complexity. When ambiguous, default to the lower level.

4. **Replication-grade detail, not code transcription.** The genome must contain enough detail that an agent can rebuild the solution without seeing the original project. Ban UiPath activity names, variable names, and API calls (`Uses ReadPDF activity`, `Calls ProcessInvoice.xaml`). But DO include: field names and mappings (`extracts vendor_name, invoice_number, line_items from the PDF`), data transformations (`sums line_item amounts and compares to invoice total`), specific conditions in plain language (`if amount exceeds $10,000 and category is Premium, route to manager approval`), and step-by-step substeps for any non-trivial operation. Err on the side of too much domain detail, not too little.

5. **Every section present, always.** The genome must include all template sections. For simple genomes, sections that do not apply get a stub with guidance (same stubs as the authoring skill). Never omit a section entirely.

6. **Flag ambiguity, don't leave gaps.** When the code is ambiguous (unclear business logic, multiple possible interpretations, no clear entry point), write your best interpretation and append `*[Inferred from project signals]*` after the uncertain content. Never leave a section empty because you are unsure -- always write something and flag it.

7. **Write immediately, offer edits after.** Write the genome file to the user's CWD as `{slug}-genome.md` immediately after generating. Derive the slug from project.json `name` field, slugified (e.g., "InvoiceProcessing" -> `invoice-processing-genome.md`). Then ask "Want to adjust anything?" Do not show a preview or ask for confirmation before writing.

8. **One skill per workflow step in Build With.** Map each major workflow step to exactly one skill using the [skill-mapping-guide.md](../shared/genome/skill-mapping-guide.md) decision tree. For mixed XAML + coded workflow projects, map XAML-based steps to `uipath-rpa-workflows` and coded steps to `uipath-coded-workflows`. Each step gets one skill, never both.

9. **Always include the blueprint preamble.** Every genome must start with the HTML comment `<!-- UIPATH-AUTOMATION-GENOME: ... -->` and the visible blockquote "This is a UiPath automation blueprint..." immediately after the one-liner. Build With must appear before Workflow. This prevents AI agents from executing the workflow steps directly instead of building a UiPath project.

## Workflow

### Step 1 -- Receive Project Path

User specifies a directory. Scan for project.json. If found, read it first to get the project name, entry point, dependencies, and configuration. If not found, scan for .xaml/.cs files directly and proceed with reduced metadata (flag missing metadata with ambiguity markers).

### Step 2 -- Analyze Project Files

Follow [project-analysis-guide.md](./references/project-analysis-guide.md):

1. Read project.json for metadata and dependencies
2. Build file inventory (classify .xaml, .cs, .cs.json, .flow files; exclude auto-generated directories)
3. Analyze each XAML file for activities, control flow, error handling, arguments
4. Analyze each coded workflow for service usage, connections, control flow, error handling
5. Analyze any .flow files for node types, edges, scripts
6. Build the call graph from entry point(s)

Read every relevant file -- no file count limit, no summarization of helpers.

### Step 3 -- Infer Complexity

Count project signals and map to simple/medium/complex using the complexity table in [extraction-mapping-guide.md](./references/extraction-mapping-guide.md). This determines section depth in Step 4.

### Step 4 -- Map Signals to Genome Sections

Use [extraction-mapping-guide.md](./references/extraction-mapping-guide.md) to translate extracted signals into genome content:

- **Overview**: Synthesize business purpose from project name, file names, variable names, target applications, and data flow. Write as if authoring the genome, not describing what you found. If business intent is genuinely unclear, write best interpretation and flag.
- **Target Applications**: Map package dependencies to applications using the package table. Each application gets a Role and Notes.
- **Build With**: Map each workflow step to a skill using [skill-mapping-guide.md](../shared/genome/skill-mapping-guide.md). For mixed projects, attribute each step to the file type it originates from.
- **Configuration Questions**: Generalize all hardcoded values and application choices. Format: "N. {Question}? (source project used: {original value})". Minimum questions for medium/complex: 3-5 / 5+.
- **Workflow**: Order steps from the call graph (Step 2, item 6). Each step describes the business action, not the code. Use substeps for any step that involves multiple fields, conditional logic, or data transformation. Include what data enters and leaves each step. See [extraction-mapping-guide.md](./references/extraction-mapping-guide.md) §Workflow Depth Rules for format and examples.
- **Business Rules**: Translate conditions and decision logic to natural language. Associate each rule with the workflow step where it applies. No programming syntax, but include specific field names, threshold values, and conditions. See [extraction-mapping-guide.md](./references/extraction-mapping-guide.md) §Business Rule Extraction for step-associated format.
- **Error Handling**: Map patterns using the error handling table. Associate each handler with the workflow step it protects. See [extraction-mapping-guide.md](./references/extraction-mapping-guide.md) §Error Handling Pattern Mapping.
- **Acceptance Criteria**: Derive from workflow steps, error handling, and business rules. Include criteria that verify data transformations and field mappings, not just happy-path outcomes. Pattern: "Given [input], [outcome]." One criterion per major step/rule minimum, plus one per data transformation.
- **Complexity**: State the inferred level.
- **Tags**: Derive from target applications, business domain, and platform features.

Populate per this matrix:

| Section | Simple | Medium | Complex |
|---------|--------|--------|---------|
| Overview | Full (1 paragraph) | Full (2-3 paragraphs) | Full (2-3 paragraphs) |
| Target Applications | Full | Full | Full |
| Build With | Full | Full | Full |
| Configuration Questions | Stub | Full (3-5 questions minimum) | Full (5+ questions minimum) |
| Workflow | Full (3-5 steps minimum) | Full (5+ steps with substeps) | Full (8+ steps with substeps) |
| Business Rules | Stub | Full (step-associated) | Full (step-associated) |
| Error Handling | Stub | Full (per-step where applicable) | Full (per-step where applicable) |
| Acceptance Criteria | Full (3-4 criteria minimum) | Full (5+ criteria including data checks) | Full (7+ criteria including data checks) |
| Complexity | Full | Full | Full |
| Tags | Full | Full | Full |

**These are minimums, not ceilings.** If the project has 15 meaningful workflow steps, write 15 steps. If it has 12 business rules, write 12 business rules. The genome must capture every step and rule needed to replicate the solution. Never compress detail to fit a target count.

**"Full"** means populated with specific content derived from the project analysis, including substeps with data flow for any non-trivial operation. **"Stub"** means the section heading is present with a one-line guidance note. Example stubs:
- Configuration Questions: "Description covers the scope -- no additional configuration needed."
- Business Rules: "No explicit business rules -- agent applies standard validation patterns."
- Error Handling: "Standard error handling -- retry on transient failures, log and skip on permanent errors."

### Step 5 -- Write Genome File

Read the genome template from [genome-template.md](../shared/genome/genome-template.md). Write the populated genome to the user's CWD.

File naming: slugify the project.json `name` field. "InvoiceProcessing" -> `invoice-processing-genome.md`. If no project.json, derive from the directory name.

The output genome must be indistinguishable from one created by the authoring skill. No extraction markers, no provenance notes, no references to source files.

### Step 6 -- Offer Edits

Tell the user the file has been created and ask: "Want to adjust anything?" If they request changes, edit in place.

Common edit requests:
- "This step is wrong / missing": Update the Workflow section and adjust Build With and Acceptance Criteria to match.
- "The complexity should be higher/lower": Update Complexity, then adjust section depth per the population matrix.
- "Remove the inferred flags": Remove all `*[Inferred from project signals]*` markers -- user has confirmed the content.
- "Add a target application": Update Target Applications, Workflow, Build With, and Acceptance Criteria.

## Reference Navigation

- **[genome-template.md](../shared/genome/genome-template.md)** -- Full genome template with all sections. Read when writing genome output.
- **[project-analysis-guide.md](./references/project-analysis-guide.md)** -- File-by-file extraction instructions. Read when analyzing project files (Step 2).
- **[extraction-mapping-guide.md](./references/extraction-mapping-guide.md)** -- Signal-to-genome-section mapping tables. Read when mapping signals to genome content (Step 4).
- **[skill-mapping-guide.md](../shared/genome/skill-mapping-guide.md)** -- Which UiPath skill handles which automation type. Consult when populating Build With section.

## Anti-patterns

1. **Asking the user what the project does.** The agent reads the project files. Never ask "What does this automation do?" or "Can you describe the workflow?"
2. **Showing a preview before writing.** Write the genome first, then offer edits. No "Here's what I'll generate -- look good?" step.
3. **Code-level acceptance criteria.** "Uses ReadPDF activity" and "Calls Main.xaml" are banned. Every criterion must describe a functional outcome.
4. **Omitting sections.** Even if a section does not apply, include it with a stub. The genome template must be complete.
5. **Leaving extraction markers in the genome.** The genome must not contain "Extracted from project X", "Source: Main.xaml", file paths from the source project, or any provenance notes. It reads as if authored from scratch. (Exception: `*[Inferred from project signals]*` markers are allowed -- they flag ambiguity, not provenance, and the user can remove them.)
6. **Including programming syntax in business rules.** "Amount > 10000 AndAlso Category = Premium" is banned. Translate to "If amount exceeds $10,000 and category is Premium."
7. **Treating Integration Service as a target application.** "Integration Service" is infrastructure, not an app. Resolve to the actual service: "Salesforce", "ServiceNow", "SAP". Use xmlns namespaces and activity class names to determine the specific service.
8. **Compressing workflow steps to fit a target count.** The population matrix is a minimum. If the project has 20 steps, write 20 steps. Never summarize "steps 5-10 process the data" when each step does something distinct.
9. **Flat workflow steps for non-trivial operations.** "Validate invoice" as a single line is too shallow to replicate. Break it into substeps: what fields are checked, what rules apply, what happens on failure. If an agent cannot rebuild the step from the genome text alone, add more detail.
10. **Disconnected business rules.** A flat list of rules forces the rebuilding agent to guess which step each rule belongs to. Associate every rule with its workflow step.
