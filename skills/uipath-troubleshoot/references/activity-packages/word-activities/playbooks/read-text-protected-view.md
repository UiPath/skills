---
confidence: medium
---

# Read Text — Protected View Blocks Reading a File From an Untrusted Source

## Context

What this looks like:
- Reading a Word document (via `Read Text` inside `Use Word File` / `Word Application Scope`) **faults trying to open/access the file**, or hangs, when the file came from **email, the internet, or an external/network server**
- The same file opens and reads fine when it originated locally; only externally-sourced copies fail

What can cause it:
- Word opens files carrying a **Mark-of-the-Web** (downloaded / received from outside the machine) in **Protected View** — a read-only sandbox. The Interop read against a Protected-View document is blocked, surfacing as an access exception (or, unattended, a hang on the Protected View bar that nobody can dismiss).

What to look for:
- The file's origin — downloaded, email attachment, copied from a network/external share (carries Mark-of-the-Web) vs created locally.
- Whether the failure is specific to externally-sourced files.

## Investigation

1. Confirm the failing document came from an external source (email/internet/remote share) and that locally-created files read fine — that isolates Protected View / Mark-of-the-Web.
2. Ask the user (or someone with desktop access on the robot host, as the robot's Windows user) whether the file opens in Protected View when double-clicked.

## Resolution

- **Unblock the file (preferred, per-file)** — clear the Mark-of-the-Web before reading: `Right-click > Properties > Unblock`, or `Unblock-File <path>` in PowerShell as a workflow pre-step.
- **Add the folder to Trusted Locations** — `File > Options > Trust Center > Trust Center Settings > Trusted Locations` on the execution machine (as the robot's Windows user), so files in that folder skip Protected View.
- **Disable Protected View on the execution machine** — `File > Options > Trust Center > Trust Center Settings > Protected View` and uncheck the relevant rules (files from internet / Outlook / unsafe locations). Apply only on a controlled robot host, since it lowers a safety control.
- **If unattended and hanging rather than erroring** — the Protected View bar is an invisible blocking dialog; see [word-scope-hangs-background-prompt.md](./word-scope-hangs-background-prompt.md).

> Related: [word-scope-file-corrupted.md](./word-scope-file-corrupted.md) covers Protected View / Mark-of-the-Web blocking a *write/save*; this playbook covers it blocking a *read*.
