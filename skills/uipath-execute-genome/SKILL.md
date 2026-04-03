---
name: uipath-execute-genome
description: "Orchestrate end-to-end execution of a UiPath automation genome file — configure, build across multiple skills, and validate acceptance criteria. TRIGGER when: user says 'build this genome', 'execute this genome', 'implement this genome', 'follow this genome'; user provides or references a *-genome.md file and wants to create the UiPath automation project from it; user opens a genome file and asks to build the automation it describes; user mentions a genome and wants to implement it. DO NOT TRIGGER when: user wants to CREATE a genome from a description (use uipath-genome-authoring); user wants to EXTRACT a genome from an existing UiPath project (use uipath-genome-extraction); user wants to build a specific automation type without a genome file (use the specific skill directly — uipath-coded-workflows, uipath-rpa-workflows, etc.)."
---

# Genome Executor

Orchestrate end-to-end execution of a UiPath automation genome. The genome is the spec — this skill is the conductor that turns it into a working automation project.

A genome file describes *what* to build. The build skills (coded-workflows, rpa-workflows, maestro-flow, etc.) know *how* to build. This skill bridges the two: it reads the genome, asks configuration questions, sequences through build steps skill by skill, and validates the result against acceptance criteria.

## When to Use This Skill

- User provides a `*-genome.md` file and wants to build the automation
- User says "build this genome", "execute this genome", "implement this genome"
- User opens a genome and asks to create the UiPath project from it
- User references a genome file by name and wants it implemented

## Critical Rules

1. **Always ask Configuration Questions before building.** If the genome has a Configuration Questions section that is not a stub (i.e., not "Description covers the scope" or similar), present every question as a structured multi-choice prompt with auto-generated options, grouped by topic area. Collect all answers before writing any code. These answers are context for every subsequent build step.
2. **Follow the Build With table order.** The genome's Build With table defines the execution sequence. Implement steps in that order — do not reorder, skip, or parallelize steps across different skills.
3. **Group consecutive same-skill steps.** When multiple consecutive Build With rows reference the same skill, combine them into a single skill invocation. Pass all relevant workflow steps, business rules, and error handling for the group together.
4. **Auto-advance between skill groups.** After completing one skill group, immediately proceed to the next. Never stop and ask the user to manually trigger the next skill. Report progress and continue.
5. **Pass genome context to each skill group.** When building, provide the target skill with: (a) the specific workflow steps being implemented, (b) business rules that reference those steps, (c) error handling for those steps, (d) configuration question answers that affect those steps.
6. **Validate every acceptance criterion after building.** After all Build With steps are complete, walk through each acceptance criterion and assess whether the built code addresses it. Do not skip this phase.
7. **One project for the whole genome.** Create or reuse a single UiPath project for all Build With steps, regardless of how many different skills are involved. A UiPath project can contain both coded (.cs) and XAML (.xaml) files.
8. **Do not modify the genome file.** The genome is a read-only spec. Never edit, update, or mark checkboxes in the genome during execution.

## Workflow

### Phase 1: Parse & Configure

#### Step 1 — Read the genome file

Read the entire genome markdown file. Extract these sections:

| Section | Required | What to extract |
|---------|----------|----------------|
| Overview | Yes | Automation purpose and context |
| Target Applications | Yes | Systems involved and their roles |
| Build With | Yes | Ordered list of (step, skill, rationale) |
| Configuration Questions | No | Questions to ask before building (may be a stub) |
| Workflow | Yes | Detailed step-by-step instructions |
| Business Rules | No | Constraints and decision logic (may be a stub) |
| Error Handling | No | Failure modes and recovery (may be a stub) |
| Acceptance Criteria | Yes | Checkboxes for post-build validation |
| Complexity | Yes | simple / medium / complex |

#### Step 2 — Present Configuration Questions

Check the Configuration Questions section:

- **If it is a stub** ("Description covers the scope", "No additional configuration needed", or similar one-liner): Skip to Phase 2. No questions needed.
- **If it contains actual questions** (numbered list): Present them as structured multi-choice questions using the process below.

**2a. Group questions by topic area.**

Scan the configuration questions and group related ones. Common areas: Notifications (email, Slack, messaging), Data Sources (APIs, files, databases), Behavior (thresholds, timing, retry logic), Environment (servers, connections, credentials). Use whatever grouping fits the genome — not all areas will appear in every genome.

**2b. Generate options for each question.**

For each configuration question, generate 3 concrete answer options. The user always gets a 4th freeform option ("Other") automatically — do not add it yourself. Option generation rules:

- **If the genome mentions a default** (e.g., "source project used: 50%"): Make the genome's default the first option with "(Recommended)" appended. Generate 2 alternative options that represent common variations.
- **If no default exists**: Generate 3 sensible options based on the question's domain. Put the most common/safest choice first with "(Recommended)".
- **Keep option labels concise** (1-5 words). Use the description field for details.
- **Headers must be 12 characters or fewer.** Use the topic keyword (e.g., "Recipients", "SMTP", "Lookback", "State", "Format").

**2c. Present questions in batches using AskUserQuestion.**

Present up to 4 questions per batch, grouped by topic area. If there are more than 4 questions, use multiple batches — present one batch, collect answers, then present the next.

**Example** — for the artemis-2 genome's 5 configuration questions:

Batch 1 (Notification settings — 3 questions):

```
Question 1:
  header: "Recipients"
  question: "Which email address(es) should receive mission alerts?"
  options:
    - label: "Team DL"
      description: "Use a team distribution list — enter the address in Other if selected"
    - label: "Single email"
      description: "Send to one personal email address"
    - label: "Multiple"
      description: "Comma-separated list of individual addresses"

Question 2:
  header: "SMTP"
  question: "Which SMTP server should send the alert emails?"
  options:
    - label: "Orchestrator (Recommended)"
      description: "Use the default Orchestrator email configuration"
    - label: "Custom SMTP"
      description: "Specify a custom SMTP server (host, port, credentials)"
    - label: "SendGrid/SES"
      description: "Use a cloud email service via API"

Question 3:
  header: "Format"
  question: "What email format for mission alerts?"
  options:
    - label: "HTML (Recommended)"
      description: "HTML with mission phase icons and formatted layout"
    - label: "Plain text"
      description: "Simple text summary, works in all email clients"
    - label: "Both"
      description: "HTML with plain text fallback"
```

Batch 2 (Behavior settings — 2 questions):

```
Question 4:
  header: "Lookback"
  question: "How far back should the initial poll look for events?"
  options:
    - label: "1 hour (Recommended)"
      description: "Default from genome — avoids inbox flood on first run"
    - label: "30 minutes"
      description: "Shorter window, fewer initial notifications"
    - label: "6 hours"
      description: "Catch up on recent mission activity"

Question 5:
  header: "State"
  question: "Should the state file persist across Orchestrator restarts?"
  options:
    - label: "Persist (Recommended)"
      description: "Keep state file — avoids duplicate notifications after restart"
    - label: "Reset on restart"
      description: "Fresh state each time — may re-send recent alerts once"
```

**2d. Record all answers.**

After all batches are answered, compile the configuration answers into a structured record:

```
Configuration Answers:
  Recipients: [user's answer]
  SMTP: Orchestrator default
  Format: HTML with phase icons
  Lookback: 1 hour
  State persistence: Yes, persist across restarts
```

These answers are referenced in Phase 2 when assembling build context for each skill group.

#### Step 3 — Resolve project

Before building, establish the target UiPath project:

1. Check if a UiPath project is already open by running:
   ```bash
   uip rpa list-instances --output json --use-studio
   ```
2. If a project is open, confirm with the user: "Use [project name] at [path] for this genome?"
3. If no project is open, create one using the genome's name as the project name.

Record the `PROJECT_DIR` — all subsequent skill work targets this project.

### Phase 2: Build

#### Step 4 — Plan skill groups

Parse the Build With table into an ordered list. Group consecutive rows that reference the same skill into a single "skill group."

Example for the artemis-2 genome:

| Group | Steps | Skill |
|-------|-------|-------|
| 1 | Poll NASA APIs, Detect transitions, Compose email, Update state | `uipath-coded-workflows` |
| 2 | Scrape NASA status page (fallback) | `uipath-rpa-workflows` |

Report the plan to the user:

```
Genome build plan:
  Group 1: Steps 1, 3, 4, 5 → uipath-coded-workflows (4 steps)
  Group 2: Step 2 → uipath-rpa-workflows (1 step)
  Total: 2 skill groups, 5 steps
```

#### Step 5 — Execute each skill group

For each skill group, in order:

**5a. Report start:**
```
Building group [N]/[total]: [skill-name] ([count] steps)
Steps: [list of step names from Build With]
```

**5b. Assemble the build context for this group:**

Extract from the genome only the sections relevant to this group's steps:

- **Workflow steps:** The numbered steps from the Workflow section that correspond to this group's Build With rows. Include substeps.
- **Business rules:** Any rules from the Business Rules section that reference this group's workflow steps. If rules are organized by step, include only the matching ones. If rules are general, include all.
- **Error handling:** Any error handling from the Error Handling section that references this group's steps. If general, include all.
- **Configuration answers:** All answers from Phase 1 that are relevant (when in doubt, include them — the build skill will use what it needs).
- **Target applications:** The entries from Target Applications that this group interacts with.

**5c. Build:**

Follow the target skill's workflow to implement the steps. The agent already has the target skill loaded — apply its Critical Rules, discovery flow, project resolution, and validation loop as you normally would.

Key context to carry into the skill:
- `PROJECT_DIR` from Step 3 (do NOT create a new project — reuse the one from Step 3)
- The assembled build context from 5b
- The genome's Overview for high-level understanding

**5d. Verify the group completed:**

Before advancing, confirm:
- All files for this group were created/modified
- All files pass validation (the target skill's validation loop should handle this)
- No unresolved errors remain

**5e. Report progress and advance:**
```
Group [N]/[total] complete ✓
  Files: [list of files created/modified]
  Validation: passed
  
Advancing to group [N+1]...
```

Repeat 5a-5e for every skill group. Do not stop between groups.

#### Step 6 — Wire cross-group dependencies

After all groups finish, check if any workflow steps reference outputs from steps built by a different skill group. Common cases:

- A coded workflow calls an RPA workflow (or vice versa)
- A workflow reads a file or state produced by another workflow
- A main entry point orchestrates calls to other workflows

If cross-group wiring is needed:
1. Identify the connection points (method calls, file references, workflow invocations)
2. Edit the relevant files to wire them together
3. Validate the modified files

### Phase 3: Validate

#### Step 7 — Assess acceptance criteria

Read the Acceptance Criteria section from the genome. For each criterion:

1. **Identify coverage:** Which file(s) and code section(s) address this criterion?
2. **Assess:** Does the implementation satisfy the criterion as written?
3. **Classify:** Mark each as one of:
   - **Met** — The code directly implements this behavior
   - **Partial** — The code handles part of it but has gaps
   - **Not Met** — No code addresses this criterion
   - **Not Verifiable** — Cannot be verified without runtime execution (e.g., depends on live API responses)

#### Step 8 — Report results

Present the validation summary:

```
Acceptance Criteria Validation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ [criterion 1 summary] — Met (file.cs:method)
✓ [criterion 2 summary] — Met (file.xaml)
⚠ [criterion 3 summary] — Partial: [what's missing]
✗ [criterion 4 summary] — Not Met: [why]
○ [criterion 5 summary] — Not Verifiable: [requires runtime]

Result: [N]/[total] met, [N] partial, [N] not met, [N] not verifiable
```

If there are gaps (Partial or Not Met):
1. Explain what's missing for each gap
2. Suggest specific code changes to close the gap
3. Ask the user if they want to fix the gaps now

#### Step 9 — Completion report

After validation (and optional gap fixes):

```
Genome execution complete.

Project: [project name] at [PROJECT_DIR]
Genome: [genome file name]
Skills used: [list of skills invoked]
Files created: [count]
Acceptance criteria: [N]/[total] met

To run: uip rpa run-file --file-path "[entry point]" --project-dir "[PROJECT_DIR]" --output json --use-studio
```

## Genome Format Reference

The genome file follows this structure (from `skills/shared/genome/genome-template.md`):

```markdown
<!-- UIPATH-AUTOMATION-GENOME: build specification -->
# Genome: {Name}
> {One-line description}
> **This is a UiPath automation blueprint.** ...

## Overview
## Target Applications       (table: Application | Role | Notes)
## Build With                (table: Step | Skill | Rationale)
## Configuration Questions   (numbered list or stub)
## Workflow                  (numbered steps with optional substeps)
## Business Rules            (per-step or general, or stub)
## Error Handling            (per-step or general, or stub)
## Acceptance Criteria       (checkbox list: - [ ] Given X, then Y)
## Complexity                (simple | medium | complex)
## Tags                      (comma-separated)
```

### Valid skill names in Build With

| Skill | What it builds |
|-------|---------------|
| `uipath-coded-workflows` | C# coded automations — API calls, data processing, business logic |
| `uipath-rpa-workflows` | XAML workflows — UI automation, Document Understanding, activity-based RPA |
| `uipath-maestro-flow` | Flow orchestration — multi-step flows, queue management, scheduling |
| `uipath-coded-agents` | Python AI agents — LLM integration, AI-powered decisions |
| `uipath-coded-apps` | Web applications — user-facing forms, dashboards |

## Anti-patterns

1. **Skipping Configuration Questions.** The most common failure mode. If the genome has questions, they exist for a reason — the answers affect how code is written. Building without them produces placeholder values that the user must manually replace.
2. **Stopping between skill groups.** The agent must auto-advance. "I've finished the coded parts, want me to continue with the RPA steps?" is wrong. Just continue.
3. **Creating a new project per skill group.** One project holds everything. Coded and XAML files coexist in a single UiPath project.
4. **Skipping acceptance criteria validation.** The genome's acceptance criteria are the definition of done. Building without validating against them leaves the user guessing whether the automation works.
5. **Reordering Build With steps.** The genome author ordered the steps deliberately. The fallback scrape in artemis-2 is step 2 in Build With because it logically comes after the API poll. Build in order, group by skill, but preserve the logical sequence.
6. **Treating the genome as a suggestion.** The genome is the spec. Implement what it says — don't add features it doesn't mention, don't skip steps it includes, don't change the skill assignments.
7. **Editing the genome file.** The genome is read-only during execution. Don't mark checkboxes, add notes, or modify it. If the user wants changes, they should edit the genome separately and re-execute.
