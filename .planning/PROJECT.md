# UiPath Agent Skills

## What This Is

A repository of self-contained AI agent skills for UiPath automation development, installed as Claude Code plugins. Each skill teaches an AI agent how to build, run, test, and deploy a specific type of UiPath automation — coded workflows, XAML/RPA workflows, Maestro flows, coded agents, coded apps, platform management, and genome blueprints.

## Core Value

AI agents can autonomously build production-quality UiPath automations by following skill instructions — no human hand-holding required.

## Current State

v1.0 Genome Skills shipped 2026-04-02. Two new skills added:
- **uipath-genome-authoring** — interview users about automation ideas, produce genome markdown specs
- **uipath-genome-extraction** — analyze existing UiPath Studio projects, produce genome markdown specs

Shared genome assets live in `skills/shared/genome/` (template, skill-mapping guide).

Total skills: 10 (8 pre-existing + 2 genome skills)
Genome content: 719 lines across 6 markdown files

## Requirements

### Validated

- ✓ uipath-coded-workflows — full coded automation lifecycle
- ✓ uipath-rpa-workflows — XAML workflow generation via discovery-first approach
- ✓ uipath-maestro-flow — flow authoring and orchestration
- ✓ uipath-coded-agents — Python agent lifecycle
- ✓ uipath-coded-apps — coded web application lifecycle
- ✓ uipath-platform — environment and Orchestrator management
- ✓ uipath-servo — desktop/browser UI automation via CLI
- ✓ uipath-report-issue — structured GitHub issue filing
- ✓ Genome creation from user descriptions — v1.0
- ✓ Genome creation from existing UiPath Studio solutions — v1.0

### Active

(No active milestone)

### Out of Scope

- Genome execution skill — genomes are self-contained; existing skills handle the build
- Genome distribution/registry — infrastructure beyond the repo (GitHub org, CLI registry, portal)
- Genome marketplace or rating system — premature without 20+ genomes

## Context

- Genome concept documented in `.genome_spec/` with template, discussion notes, and 3 examples
- Genomes span a complexity spectrum: simple (paragraph), medium (single file with rules), complex (multi-file spec)
- The agent carries the weight — genomes describe *what* to build; skills know *how*
- Shared genome assets avoid cross-skill references: `skills/shared/genome/` contains genome-template.md and skill-mapping-guide.md
- Extraction skill generalizes business-specific values into Configuration Questions for genome reusability

## Constraints

- **Self-containment**: Each skill must be fully independent (no cross-skill imports); shared assets go in `skills/shared/`
- **Repo conventions**: SKILL.md with YAML frontmatter, kebab-case references, no build system
- **Reference reuse**: Skills leverage existing deep reference material rather than duplicating it

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| No execution skill | Genomes are self-contained specs; existing skills handle building | ✓ Good — keeps scope focused |
| Shared genome assets in skills/shared/genome/ | Avoids cross-skill references while enabling reuse | ✓ Good — resolved cross-skill violation |
| Follow .genome_spec/TEMPLATE.md | Established format with examples already validated | ✓ Good — both skills produce consistent output |
| Authoring before extraction | Establishes genome format handling pattern extraction needs | ✓ Good — extraction reused population matrix, critical rules patterns |
| Generalize hardcoded values + app choices | Makes extracted genomes reusable beyond the original project | ✓ Good — config questions with defaults |
| Autonomous extraction (no interview) | Mirrors authoring's "write immediately, offer edits" pattern | ✓ Good — consistent UX across skills |

---
*Last updated: 2026-04-02 after v1.0 milestone*
