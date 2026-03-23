---
name: uipath-project-discovery
description: "Generate project context documentation for UiPath automation projects. Discovers project structure, dependencies, naming conventions, code patterns, and entry points, then writes context files for Claude Code and UiPath Autopilot. TRIGGER when: UiPath project detected (project.json with UiPath dependencies exists in or near the working directory) AND the file .claude/rules/project-context.md does NOT exist; User explicitly asks to generate project context, analyze project structure, or create AGENTS.md; User invokes /uipath:project-context. DO NOT TRIGGER when: .claude/rules/project-context.md already exists (context was already generated) unless the user explicitly asks to regenerate or refresh; User is asking to create, edit, or run workflows (use uipath-coded-workflows or uipath-rpa-workflows instead); User is asking about Orchestrator, deployment, or CLI setup (use uipath-development instead)."
metadata:
  allowed-tools: Bash, Read, Write, Glob, Grep, Edit
---

# UiPath Project Context Generator

Discover and document a UiPath automation project's structure, conventions, and architecture. Generates context files consumed by Claude Code (`.claude/rules/project-context.md`) and UiPath Autopilot in Studio Desktop (`AGENTS.md`).

## When to Use This Skill

- A UiPath project exists (project.json with UiPath dependencies) and `.claude/rules/project-context.md` does not exist yet
- User asks to "generate project context", "analyze this project", "create AGENTS.md", or "regenerate context"
- User invokes `/uipath:project-context` manually to force regeneration

## Auto-Trigger Conditions

This skill auto-triggers when ALL of the following are true:
1. A `project.json` exists at or near the current working directory
2. That `project.json` contains UiPath dependencies (any key matching `UiPath.*` in the `dependencies` object)
3. The file `.claude/rules/project-context.md` does NOT exist relative to the project root

If `.claude/rules/project-context.md` already exists, do NOT auto-trigger. The user must explicitly invoke `/uipath:project-context` to regenerate.

## Workflow

### Phase 1: Locate the Project

Resolve the project directory:
1. If the user provided an explicit path, use it
2. Try `uip rpa list-instances --format json` to find an open Studio Desktop project
3. Fall back to current working directory
4. Verify `project.json` exists at the resolved path
5. Confirm it contains UiPath dependencies before proceeding

### Phase 2: Discovery

Follow the discovery procedure in [references/discovery-guide.md](references/discovery-guide.md). Gather:

1. **Project identity** — name, description, type, target framework, expression language
2. **Dependencies** — all UiPath packages with versions, any third-party NuGet packages
3. **Project structure** — directory layout, file counts by type (.cs, .xaml)
4. **Entry points** — list of entry point workflows with their arguments (inputs/outputs)
5. **Code patterns** — namespace convention, base classes used, coding style
6. **Naming conventions** — file naming patterns, class naming, variable conventions
7. **Key workflows** — what each major workflow does (from file names, class names, comments)
8. **Shared resources** — helper classes, models, Object Repository, connections

### Phase 3: Generate Context

Using the template in [assets/context-template.md](assets/context-template.md), produce the context document:

- **Maximum 200 lines**
- Structured with clear sections
- Factual only — include only what was actually discovered, never assume
- Actionable — tells an AI assistant or developer what they need to know to work in this project
- Omit any section where no relevant data was found

### Phase 4: Write Output Files

**File 1: `.claude/rules/project-context.md`**
1. Create the `.claude/rules/` directory if it does not exist
2. Write the generated context document to `.claude/rules/project-context.md`
3. This file is fully owned by the skill — overwrite on regeneration
4. This file is auto-loaded by Claude Code as a project rule

**File 2: `AGENTS.md` at project root**
1. If `AGENTS.md` does NOT exist: write the full context document
2. If `AGENTS.md` ALREADY exists:
   a. Read the existing content
   b. Look for fenced markers `<!-- PROJECT-CONTEXT:START -->` and `<!-- PROJECT-CONTEXT:END -->`
   c. If markers exist: replace ONLY the content between them with the new context
   d. If markers do NOT exist: append the fenced block at the end of the file:
      ```
      <!-- PROJECT-CONTEXT:START -->
      [generated context]
      <!-- PROJECT-CONTEXT:END -->
      ```
   This preserves any user-written content in AGENTS.md

### Phase 5: Report

After writing files, inform the user:
1. Files created/updated (with absolute paths)
2. Brief summary of what was discovered (project type, file counts, key entry points)
3. Note that `.claude/rules/project-context.md` is auto-loaded by Claude Code in every conversation
4. Note that `AGENTS.md` is read by UiPath Autopilot in Studio Desktop
5. Suggest running `/uipath:project-context` again after significant project changes

## Critical Rules

1. **NEVER fabricate project information.** Only include facts discovered by reading actual files. If something cannot be determined, omit it entirely.
2. **Keep output under 200 lines.** Prefer tables and lists over prose. Every line must earn its place.
3. **Preserve user content in AGENTS.md.** Always use the fenced marker pattern when AGENTS.md already exists. Never modify content outside the markers.
4. **Do not modify any project source files.** This skill only reads the project and writes context documentation files.
5. **Sample intelligently, do not read exhaustively.** For large projects, read a representative sample (up to 20 source files). Prioritize entry points, Main.cs/Main.xaml, and files from different directories.
6. **Handle both project types.** Support coded workflow projects (.cs files), RPA projects (.xaml files), and mixed projects containing both.
7. **Never leave placeholders in output.** Every `{{PLACEHOLDER}}` from the template must be replaced with actual values or the section must be omitted.
8. **Identical content in both output files.** The context written to `.claude/rules/project-context.md` and `AGENTS.md` must be the same (except for AGENTS.md fencing markers when appending to an existing file).

## Anti-Patterns

- Do NOT read every file in a large project — sample up to 20 representative files
- Do NOT include raw file contents in the output — summarize and extract patterns
- Do NOT guess what workflows do if unclear — describe only what is observable
- Do NOT overwrite user content in AGENTS.md outside the fenced markers
- Do NOT trigger when `.claude/rules/project-context.md` already exists unless user explicitly requests regeneration
- Do NOT add commentary or recommendations — this is a factual context document, not a code review
