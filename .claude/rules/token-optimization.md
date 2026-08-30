---
paths:
  - "**/*.md"
---

# Token Optimization — Terse Documentation Mode

All skill documentation and agent-facing prose in this repo MUST follow these rules. Technical accuracy stays. Fluff dies.

## 0. Compression Boundary — what may be compressed

Compression is NOT uniform. A/B evidence (internal July 2026 rollback; external compliance testing where merging 8 safety bullets into 3 equivalent sentences dropped rule-following from 3/3 to 1/3, and shorthand like `python=venv` was ignored outright): compressing RULES breaks compliance; compressing enumerations does not.

| Compress aggressively (60–70%) | Keep full sentences (trim 10–20% max) |
|---|---|
| Enumerations, file-path lists, link lists | Critical Rules and any numbered rule text |
| Tool/feature/keyword tables | Action patterns ("do X, then Y, never Z") |
| Section intros, table surrounds | Scope qualifiers ("only when…", "except…") |
| Repeated statements → state once fully + pointers | Rationale/example blocks inside rules — redundancy in safety rules is reinforcement, not waste |

Duplication is the preferred target over wording: the same fact stated in N places compresses to ONE full statement + N pointers — never to N terse paraphrases.

## 1. Prose Compression

Strip every word that does not carry information — within the § 0 boundary: rules and action patterns keep full sentences. Drop articles. Fragments OK. Short synonyms. Technical terms exact.

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

## 3. Boilerplate Deduplication

Code examples in a skill often repeat the same structural boilerplate — namespace declarations, import blocks, wrapper envelopes, schema headers. Agent only needs to see them once per file.

### General Rule

1. **First code block in file** for a given format: include full boilerplate
2. **Subsequent code blocks in same file** of the same format: replace standard boilerplate with a single-line placeholder comment in that format's comment syntax (e.g., `<!-- standard xmlns omitted -->`, `// standard imports omitted`, `# standard header omitted`)
3. Only omit **standard** boilerplate — keep any non-standard, example-specific, or differing lines that carry information for the current example
4. Never omit boilerplate in `assets/templates/` — templates are copy-paste scaffolding and must be complete

### Per-Format Boilerplate Registries

Each skill that introduces a new file format adds its standard boilerplate list to the skill's own references (e.g., `references/<format>-boilerplate.md`) so agents editing that skill know what is safe to omit. When extending this rule to a new format, add the registry in the owning skill and link it from here.

Known registries:

- **XAML (uipath-rpa)**: standard UiPath `xmlns` declarations — see the RPA skill's XAML reference for the full list.

### Example — XAML

Standard UiPath `xmlns` declarations (`xmlns:ui`, `xmlns:sap`, `xmlns:x`, etc.) appear in every workflow. After the first block in a file, replace them with `<!-- standard xmlns omitted -->`. Package-specific or example-specific `xmlns` stay.

## Scope

- Applies to: SKILL.md files, reference docs, asset templates, PR descriptions, review comments
- Does NOT apply to: code in user projects, CLI commands, YAML frontmatter, commit messages
- Safety override: use full clarity for security warnings, irreversible actions, and multi-step sequences where brevity risks misreading
