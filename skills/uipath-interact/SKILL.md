---
name: uipath-interact
description: "[PREVIEW] Read and drive a running desktop window or browser tab — inspect, screenshot, extract, click, type, fill forms, verify. NOT for authoring UiPath projects. Workflows, activities, selectors, Object
  Repository, project.json→uipath-rpa."
allowed-tools: Bash, Read, Glob, Grep, AskUserQuestion
---

# UI Interaction via "uip rpa uia"

Drive live desktop applications and browser tabs via the `uip rpa uia` CLI: discover applications and interact with elements using stable refs.

## When NOT to use — STOP and switch to `uipath-rpa`

This skill drives a **live, running** application. It does **NOT** author or modify UiPath projects. If the task is to **create, edit, build, or run a workflow**, **configure Object Repository targets**, **create or fix selectors**, or **modify `project.json`**, STOP — switch to the `uipath-rpa` skill. Do not improvise here. `uipath-rpa` is the entry point for all workflow-authoring work and routes to the appropriate sub-skills.

## When to use

- Probing a running application -- read values, inspect state, explore a UI tree.
- Driving a UI end-to-end (click, type, fill form, extract table).
- Verifying behavior after a change.

## Critical Rules

Complete these steps in order before proceeding to the Entry Procedure. Do not skip, reorder, or improvise.

**1. Ensure a UiPath project exists.** Search for `project.json` files in or under the working directory and select one as `$PROJECT_DIR`:

- **One found** — set `$PROJECT_DIR` to its containing directory.
- **Multiple found** — `AskUserQuestion` which one to use; set `$PROJECT_DIR` to their selection.
- **None found** — `AskUserQuestion` whether to create a new project here or use an existing project elsewhere.
  - **Create new** — run `uip rpa create-project --name "<NAME>" --output json` with the user's chosen `<NAME>`, then set `$PROJECT_DIR` from the returned project directory.
  - **Use existing** — set `$PROJECT_DIR` to the path they provide.

**2. Execute the preflight.** Open [uia-prerequisites.md](references/uia-prerequisites.md) and follow it exactly against `$PROJECT_DIR` — **regardless of whether you just created the project or it already existed**. Do not summarize, paraphrase, or improvise — that file is the source of truth.

**3. Proceed to the Entry Procedure** only after the preflight passes.

## Entry Procedure

**You MUST read and follow** the implementation at `$PROJECT_DIR/.local/docs/packages/UiPath.UIAutomation.Activities/skills/uia-interact/SKILL.md` **inline** in the main conversation. Do NOT delegate to a subagent -- the skill drives the live CLI and needs the main conversation's feedback loop (screenshots, captured output, user replies).

> **Trouble?** If something didn't work as expected, use `/uipath-feedback` to send a report.
