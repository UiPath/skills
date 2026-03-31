# Phase 3 Verification Checklist -- Zero Logic Loss

**Date:** 2026-03-31
**Purpose:** Section-level audit proving that every instruction, example, and edge case from the original 8 domain files is present in either the trimmed domain file or a shared file.
**Method:** Compare pre-edit content (commit `c528417`) against current state (post `39dd98f`).

---

## skills/uipath-coded-workflows/references/ui-automation-guide.md

| Section | Location | Status |
|---------|----------|--------|
| `# UI Automation Guide for Coded Workflows` | stays (domain) | OK |
| `### Prerequisites` | pointer to `shared/uia-prerequisites.md` | OK |
| `## Workflow Pattern` | stays (C#-specific) | OK |
| `## Screen Handle Affinity (Critical)` | stays (C#-specific) | OK |
| `## Target Resolution` | stays (C#-specific) | OK |
| `## Finding Descriptors (Mandatory)` | stays (C#-specific) | OK |
| `### Step 1 -- Check the project's Object Repository` | stays (C#-specific) | OK |
| `### Step 2 -- Check UILibrary NuGet packages` | stays (C#-specific) | OK |
| `### Step 3 -- Configure the target via uia-configure-target skill` | stays (C#-specific details); shared content via pointer | OK |
| `#### Multi-Step UI Flows (Advancing Application State)` | pointer to `shared/uia-multi-step-flows.md` | OK |
| `#### Fallback: Raw Indication Commands` | pointer to `shared/uia-configure-target-workflows.md` | OK |
| `### Step 4 -- UITask / ScreenPlay (last resort only)` | stays (domain) | OK |
| `## Common Pitfalls` | stays (C#-specific) | OK |
| `### Web Dropdowns and SelectItem` | stays (C#-specific code example) | OK |
| `### Screen Handle Mismatch` | stays (C#-specific) | OK |
| `## Running UI Automation Workflows` | pointer to `shared/uia-debug-workflow.md` | OK |
| `## Runtime Selector Failures` | pointer to `shared/uia-selector-recovery.md` | OK |
| `## More Information` | stays (domain) | OK |

**Sections in original:** 18
**Stays in domain:** 13 | **Pointer to shared:** 5 | **Issues:** 0

---

## skills/uipath-rpa-workflows/references/ui-automation-guide.md

| Section | Location | Status |
|---------|----------|--------|
| `# UI Automation Guide for RPA Workflows` | stays (domain) | OK |
| `### Prerequisites` | pointer to `shared/uia-prerequisites.md` | OK |
| `## Key Concepts` | stays (XAML-specific) | OK |
| `### Application Card (Use Application/Browser)` | stays (XAML-specific) | OK |
| `### Target Configuration` | stays (XAML-specific) | OK |
| `### Object Repository` | stays (XAML-specific) | OK |
| `## Configuring Targets (Primary Approach)` | stays (XAML-specific) | OK |
| `### Applying Targets to XAML` | stays (XAML-specific) | OK |
| `### Multi-Step UI Flows (Advancing Application State)` | pointer to `shared/uia-multi-step-flows.md` | OK |
| `## Low-Level Indication Tools (Alternative)` | pointer to `shared/uia-configure-target-workflows.md` | OK |
| `## Capturing New UI Targets` | merged into Low-Level Indication Tools pointer (content covered by `shared/uia-configure-target-workflows.md`) | OK |
| `## Common Activities` | stays (XAML-specific table) | OK |
| `## Common Pitfalls` | stays (XAML-specific) | OK |
| `## More Information` | stays (domain) | OK |

**Sections in original:** 14
**Stays in domain:** 10 | **Pointer to shared:** 3 | **Merged into pointer:** 1 | **Issues:** 0

Note: "Capturing New UI Targets" was merged into the Low-Level Indication Tools pointer. Its content (indicate-application, indicate-element commands) is fully present in `shared/uia-configure-target-workflows.md` under the "Indication Fallback Commands" section.

---

## skills/uipath-coded-workflows/references/coding-guidelines.md

| Section | Location | Status |
|---------|----------|--------|
| `# Coding Guidelines Reference` | stays (domain) | OK |
| `## Using Statements Rules` | stays (C#-specific) | OK |
| `## Best Practices` | stays (C#-specific) | OK |
| `### API Discovery` | stays (C#-specific) | OK |
| `### Code Quality` | stays (C#-specific) | OK |
| `### Validation Loop (Critical Rule #14)` | pointer to `shared/validation-loop.md` (heading kept, body replaced with pointer) | OK |
| `### Error Handling` | stays (C#-specific) | OK |
| `### File Operations` | stays (C#-specific) | OK |
| `## Anti-Patterns (What NOT to Do)` | stays (C#-specific) | OK |
| `### Project & Code Structure` | stays (C#-specific) | OK |
| `### UI Automation` | stays (C#-specific) | OK |
| `### Object Repository / Indicate Commands` | stays (C#-specific) | OK |
| `### Validation & Execution` | stays (C#-specific) | OK |
| `### Shell & Environment` | stays (C#-specific) | OK |
| `## Common Issues and Fixes` | stays (C#-specific) | OK |

**Sections in original:** 15
**Stays in domain:** 14 | **Pointer to shared:** 1 | **Issues:** 0

---

## skills/uipath-rpa-workflows/references/validation-and-fixing.md

| Section | Location | Status |
|---------|----------|--------|
| `# Validation & Fixing (Phase 3 Details)` | stays (domain) | OK |
| `## Package Error Resolution` | stays (domain) | OK |
| `## Resolving Dynamic Activity Custom Types` | stays (domain) | OK |
| `## Focus Activity for Debugging` | stays (domain) | OK |
| `## Iteration Loop` | pointer to `shared/validation-loop.md` | OK |
| `## Smoke Test (Optional but Recommended)` | pointer to `shared/validation-loop.md` (smoke test section) | OK |
| `## Running UI Automation Workflows` | pointer to `shared/uia-debug-workflow.md` | OK |
| `## Runtime Selector Failures (UI Automation)` | pointer to `shared/uia-selector-recovery.md` | OK |

**Sections in original:** 8
**Stays in domain:** 4 | **Pointer to shared:** 4 | **Issues:** 0

---

## skills/uipath-coded-workflows/references/uip-guide.md

| Section | Location | Status |
|---------|----------|--------|
| `# UiPath CLI (uip) RPA Commands Guide` | stays (domain) | OK |
| `## Global Options` | pointer to `shared/cli-reference.md` | OK |
| `### STUDIO_DIR Resolution` | moved to `shared/cli-reference.md` | OK |
| `### PROJECT_DIR Resolution` | moved to `shared/cli-reference.md` | OK |
| `## Commands Reference` | stays (domain heading) | OK |
| `### list-instances` | pointer to `shared/cli-reference.md` (grouped as "Common Commands") | OK |
| `### start-studio` | pointer to `shared/cli-reference.md` (grouped as "Common Commands") | OK |
| `### create-project` | pointer to `shared/cli-reference.md` (grouped as "Common Commands") | OK |
| `### open-project` | pointer to `shared/cli-reference.md` (grouped as "Common Commands") | OK |
| `### validate` | pointer to `shared/cli-reference.md` | OK |
| `### run-file` | pointer to `shared/cli-reference.md` | OK |
| `### get-manual-test-cases` | stays (domain) | OK |
| `### get-manual-test-steps` | stays (domain) | OK |
| `### indicate-application` | stays (domain) | OK |
| `### indicate-element` | stays (domain) | OK |

**Sections in original:** 15
**Stays in domain:** 6 | **Pointer to shared:** 9 | **Issues:** 0

---

## skills/uipath-rpa-workflows/references/cli-reference.md

| Section | Location | Status |
|---------|----------|--------|
| `# CLI Tool Reference` | stays (domain) | OK |
| `## Installed Package Activity Documentation (Primary Discovery)` | stays (domain) | OK |
| `## Core RPA Workflow Tools` | stays (domain) | OK |
| `## Project Lifecycle Tools` | stays (domain) | OK |
| `## Studio Management Tools` | stays (domain) | OK |
| `## UI Automation Indication Tools` | stays (domain) | OK |
| `## Test Manager Tools` | stays (domain) | OK |
| `## Integration Service (IS) Tools` | stays (domain) | OK |
| `## CLI Error Recovery` | stays (domain) | OK |

**Sections in original:** 9
**Stays in domain:** 9 | **Pointer to shared:** 0 (pointer line added at top of file for detailed docs) | **Issues:** 0

Note: This file retained all its summary tables (quick-reference index format). A single pointer line to `shared/cli-reference.md` was added for detailed command documentation. No sections were removed.

---

## skills/uipath-coded-workflows/SKILL.md

| Section | Location | Status |
|---------|----------|--------|
| `# UiPath Coded Workflows Assistant` | stays | OK |
| `## When to Use This Skill` | stays | OK |
| `## Quick Start` | stays | OK |
| `## Critical Rules` | stays (rule 14 now points to shared/validation-loop.md; rule 15 simplified with pointer to ui-automation-guide.md) | OK |
| `### UI Automation References` | stays (expanded with explicit shared/ file links) | OK |
| `## Task Navigation` | stays (CLI row updated with shared/ link) | OK |
| `## Three Types of .cs Files` | stays | OK |
| `## Service-to-Package Dependency Mapping` | stays | OK |
| `### Commonly used packages` | stays | OK |
| `### Integration Service package` | stays | OK |
| `### Domain-specific packages` | stays | OK |
| `### Infrastructure & Cloud packages` | stays | OK |
| `### Resolving Packages & Activity Docs` | stays | OK |
| `## CodedWorkflow Base Class` | stays | OK |
| `## Project Structure Reference` | stays | OK |
| `## Templates` | stays | OK |
| `## Activity Examples & References` | stays | OK |
| `## Completion Output` | stays | OK |

**Sections in original:** 18
**Stays in domain:** 18 | **Pointer additions:** 3 (validation-loop, UIA shared files list, CLI shared) | **Issues:** 0

---

## skills/uipath-rpa-workflows/SKILL.md

| Section | Location | Status |
|---------|----------|--------|
| `# RPA Workflow Architect` | stays | OK |
| `## Core Principles` | stays | OK |
| `## CLI Output Format` | stays | OK |
| `## Tool Quick Reference` | stays (added shared/cli-reference.md pointer) | OK |
| `## Supporting References` | stays | OK |
| `### Resolving Packages & Activity Docs` | stays | OK |
| `### Procedural Reference Files` | stays (added shared/validation-loop.md entry) | OK |
| `### Domain Reference Files` | stays | OK |
| `#### UI Automation References` | stays (expanded with shared/ file links) | OK |
| `## Core Workflow: Classify Request` | stays | OK |
| `## Phase 0: Environment Readiness` | stays | OK |
| `## Phase 1: Discovery` (all sub-steps 1.1-1.9) | stays | OK |
| `## Phase 2: Generate or Edit` | stays | OK |
| `### Guidelines for both CREATE and EDIT:` | stays | OK |
| `### UI Automation Workflows -- Target Configuration Gate` | stays (condensed; points to shared/uia-configure-target-workflows.md and shared/uia-multi-step-flows.md) | OK |
| `### For CREATE Requests` | stays | OK |
| `### For EDIT Requests` | stays | OK |
| `## Phase 3: Validate & Fix Loop` | stays | OK |
| `## Phase 4: Response` | stays | OK |
| `## CLI Error Recovery` | stays | OK |
| `## Anti-Patterns` | stays | OK |
| `## Quality Checklist` | stays | OK |

**Sections in original:** 22 (counting Phase 1 sub-steps as one group)
**Stays in domain:** 22 | **Pointer additions:** 4 (cli-reference, validation-loop, UIA shared files, target config gate) | **Issues:** 0

---

## Summary

| Metric | Count |
|--------|-------|
| **Files audited** | 8 |
| **Total sections audited** | 119 |
| **Sections staying in domain file (paradigm-specific)** | 96 |
| **Sections pointed to shared files** | 22 |
| **Sections merged into existing pointer** | 1 |
| **Sections with issues** | 0 |

### Shared File Coverage

All pointers reference these 7 shared files. Each shared file was verified to contain the expected content:

| Shared File | Content Verified | Referenced By |
|-------------|-----------------|---------------|
| `shared/uia-prerequisites.md` | Package version check, upgrade flow | coded/ui-automation-guide, rpa/ui-automation-guide |
| `shared/uia-configure-target-workflows.md` | Indication fallback commands (indicate-application, indicate-element, get XAML) | coded/ui-automation-guide, rpa/ui-automation-guide |
| `shared/uia-debug-workflow.md` | Running UI automation workflows procedure | coded/ui-automation-guide, rpa/validation-and-fixing |
| `shared/uia-selector-recovery.md` | Runtime selector failure recovery | coded/ui-automation-guide, rpa/validation-and-fixing |
| `shared/uia-multi-step-flows.md` | Multi-step UI flows (advancing application state) | coded/ui-automation-guide, rpa/ui-automation-guide |
| `shared/validation-loop.md` | Fix-one-thing rule, iteration loop, smoke test | coded/coding-guidelines, rpa/validation-and-fixing |
| `shared/cli-reference.md` | Global options, STUDIO_DIR/PROJECT_DIR resolution, common commands, validate, run-file | coded/uip-guide, rpa/cli-reference |

### Merged Section Detail

**"Capturing New UI Targets" (rpa/ui-automation-guide.md):** This section contained `indicate-application`, `indicate-element` commands for screen and element indication. All three command examples from this section are present in `shared/uia-configure-target-workflows.md` under "Indication Fallback Commands". The merge is correct -- no content lost.

### Verdict

**PASS** -- All 119 sections from the 8 original files are accounted for. Every section either remains in its domain file (paradigm-specific content) or is correctly pointed to the appropriate shared file. The one merged section ("Capturing New UI Targets") was verified to have its full content present in the target shared file. Zero content loss confirmed.
