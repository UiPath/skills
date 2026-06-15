---
confidence: medium
---

# Word Application Scope — Workflow Hangs / Freezes on a Background Dialog

## Context

What this looks like:
- The job reaches the `Word Application Scope` (`UiPath.Word.Activities.WordApplicationScope`) and then hangs indefinitely — no error, no progress, until the job times out
- WINWORD.EXE is running but unresponsive to the robot's COM calls

What can cause it:
- Word opened a **modal prompt in the background** that requires user interaction and blocks all COM calls until dismissed. Common prompts: a "Password Protected" / "Enter password" dialog, a document-recovery sidebar, a "Safe Mode" message after a prior crash, an activation/license prompt, or a "trust this file" / Protected View bar
- When the scope runs unattended (no visible Word window), the dialog is invisible to anyone watching the robot but still wedges the process

What to look for:
- One or more hidden `WINWORD.EXE` instances stuck in Task Manager during the freeze.
- Whether the document is password-protected, was recovered from a prior crash, or last closed uncleanly.

## Investigation

1. Reproduce with Word **visible**: ask the user (or someone with desktop access on the robot host, signed in as the robot's Windows user) to run the workflow and watch WINWORD.EXE. Note any dialog, banner, recovery sidebar, or Safe Mode prompt that appears.
2. Open the target document manually once on the robot host to surface and clear any startup alert (recovery pane, activation, trust prompt).
3. During the freeze, open Task Manager and check for multiple hidden `WINWORD.EXE` processes stuck with no window.
4. Confirm whether the document is password-protected and whether the scope supplies the password.

## Resolution

- **If a recovery sidebar / Safe Mode prompt appears** — open the document interactively on the robot host, dismiss the recovery/Safe Mode prompt, then save and close cleanly so the startup state is cleared before the next run.
- **If a password prompt blocks it** — supply the password in the `Word Application Scope` properties, or remove protection from the source document if it does not need to be encrypted.
- **If an activation / "trust this file" prompt blocks it** — complete Office activation under the robot's Windows user, and add the document folder to Word Trusted Locations (`File > Options > Trust Center > Trust Center Settings > Trusted Locations`).
- **If WINWORD.EXE was left orphaned and wedged** — add a `Kill Process` for `WINWORD` before the scope, and ensure the scope disposes on every path so Word always closes cleanly.
- **As a guard against silent hangs** — wrap the scope so the job fails fast rather than hanging forever (set a finite timeout on the surrounding sequence / job), and prefer the modern `Use Word File` surface where it avoids the interactive-prompt failure mode.
