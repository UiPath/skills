# UiPath Automation Genomes — Discussion Notes

## Context

UiPath is integrating workflows with Claude Code so the AI agent can create automations autonomously. We want a way for people to share reusable "genomes" — specifications that an AI agent consumes to build automations.

Inspired by the [AI Analyst Genome](https://github.com/ai-analyst-lab/ai-analyst-genome), which is a self-contained markdown blueprint that Claude Code reads and bootstraps into a full data analyst product.

## Key Decisions

### The UiPath Marketplace is not the right venue

The Marketplace hosts finished artifacts (NuGet packages, pre-built workflows). Genomes are fundamentally different:

- Generative specifications, not deliverables
- Produce different output depending on user context
- Consumed by an AI agent, not by Studio's package manager
- Plain text (markdown), no binary format

### Distribution strategy (phased)

1. **GitHub org** (start here) — e.g. `github.com/uipath-genomes/`. Each genome is a repo or folder. Topic tag `uipath-genome` for discovery. Zero infrastructure, ships immediately.
2. **CLI-integrated registry** (next) — `uipath genome list`, `uipath genome init <name>`. Backs onto GitHub or a JSON index.
3. **Dedicated portal** (if traction warrants) — lightweight web app indexing genome repos. Search, tags, ratings. Only after 20+ genomes exist.

### Genome complexity is a spectrum

| Level | Format | Example |
|-------|--------|---------|
| Simple | A paragraph | "Monitor mailbox, download PDF attachments, extract invoice fields with DU, post to SAP" |
| Medium | Single markdown file with field mappings, business rules, error handling | Invoice processing with specific ERP field mappings and validation rules |
| Complex | Multi-file spec with questionnaire, phased build, architecture decisions | End-to-end order-to-cash automation across multiple systems |

The format should accommodate all three without forcing everything into the heavy end.

### The agent carries the weight, not the genome

Genomes stay thin because Claude Code has deep knowledge of UiPath's activity model, selector system, Object Repository, Document Understanding, etc. The genome describes *what* to build; the agent knows *how*.

### Verification matters

Each genome should include acceptance criteria or expected test outcomes so the agent can self-verify the built automation works. Curation (proven to work, edge cases handled, ratings) is where the shared registry adds real value beyond just hosting specs.
