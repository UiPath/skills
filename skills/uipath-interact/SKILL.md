---
name: uipath-interact
description: "[PREVIEW] Read and drive any open desktop window or browser tab — inspect UI, screenshot, extract text/tables, click, type, fill forms, verify behavior. Authoring workflows or selectors→uipath-rpa."
allowed-tools: Bash, Read, Glob, Grep, AskUserQuestion
---

# UI Interaction via "uip rpa uia"

Drive live desktop applications and browser tabs via the `uip rpa uia` CLI: discover applications and interact with elements using stable refs.

## When to use

- Probing a running application -- read values, inspect state, explore a UI tree.
- Driving a UI end-to-end (click, type, fill form, extract table).
- Verifying behavior after a change.

## When NOT to use

For anything else (building workflows, configuring Object Repository targets, creating or fixing selectors, etc.) -- use the `uipath-rpa` skill. It is the entry point for all non-interactive UIA work and routes to the appropriate sub-skills.

## Critical Rules

Complete these steps in order before proceeding to the Entry Procedure. Do not skip, reorder, or improvise.

**1. Ensure a UiPath project exists.** Look for `project.json` in or under the working directory. If found, set `$PROJECT_DIR` to its containing directory (if multiple are found, ask the user which to use). If none, prompt the user via `AskUserQuestion` to either create a new project via the `uipath-rpa` skill (set `$PROJECT_DIR` to the new project's path) or use an existing one (set `$PROJECT_DIR` to the path they provide).

**2. Execute the preflight.** Open [uia-prerequisites.md](references/uia-prerequisites.md) and follow it exactly against `$PROJECT_DIR`. Do not summarize, paraphrase, or improvise — that file is the source of truth.

**3. Proceed to the Entry Procedure** only after the preflight passes.

## Entry Procedure

**You MUST read and follow** the implementation at `$PROJECT_DIR/.local/docs/packages/UiPath.UIAutomation.Activities/skills/uia-interact/SKILL.md` **inline** in the main conversation. Do NOT delegate to a subagent -- the skill drives the live CLI and needs the main conversation's feedback loop (screenshots, captured output, user replies).

> **Trouble?** If something didn't work as expected, use `/uipath-feedback` to send a report.
