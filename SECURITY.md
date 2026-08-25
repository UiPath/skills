# Security Policy

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues,
discussions, or pull requests.**

Instead, use one of the following private channels:

1. **GitHub private vulnerability reporting (preferred for this repo).** Go to the
   [**Security** tab](https://github.com/UiPath/skills/security/advisories/new)
   of this repository and click **"Report a vulnerability"**. This opens a private
   advisory visible only to you and the maintainers.
2. **UiPath Bug Bounty / HackerOne.** For UiPath's coordinated disclosure program,
   report through [HackerOne](https://hackerone.com/uipath) or email
   **hackerone@uipath.com**.
3. **UiPath Trust.** For other security or trust queries, use
   [trust.uipath.com](https://trust.uipath.com/) or email **trust@uipath.com**.

Please include as much of the following as you can:

- A description of the vulnerability and its impact.
- Steps to reproduce (proof-of-concept, affected skill/hook, agent and version,
  configuration).
- The component involved (e.g. a skill's instructions or bundled scripts, the
  lifecycle hooks, the install/update flow, telemetry).
- Any suggested remediation.

## What to Expect

- We will acknowledge your report within **5 business days**.
- We will provide an assessment and expected timeline for a fix, and keep you
  informed of progress.
- We will credit you in the advisory once a fix is released, unless you prefer
  to remain anonymous.

Please give us a reasonable opportunity to remediate before any public
disclosure (coordinated disclosure).

## Scope Notes

This repository ships **instructions and scripts that AI coding agents execute
on developers' machines**, with the developer's local privileges and UiPath
credentials. A few areas are security-sensitive by design and are the most
valuable to review:

- **Skill content** — skills are instruction packages that coding agents
  (Claude Code, Cursor, Codex, Gemini, and others) follow autonomously.
  Content that could steer an agent into unsafe actions — exfiltrating
  credentials, running destructive commands, or acting on injected
  instructions from untrusted external data — is in scope, as is any way for a
  third party to influence what an installed skill tells the agent to do.
- **Lifecycle hooks (`hooks/`)** — shell/PowerShell scripts registered on
  agent events (`SessionStart`, `PostToolUse`, `Stop`, …) that run
  automatically, without per-invocation user confirmation. Command injection,
  unsafe handling of untrusted input (file paths, tool output, environment),
  or privilege issues here are high-impact.
- **Install and update flow** — skills are distributed via
  `uip skills install` (the [`@uipath/cli`](https://www.npmjs.com/package/@uipath/cli)
  npm package) and written into each agent's configuration directory.
- **`uip` CLI invocations** — skills instruct agents to run `uip` commands
  that operate against UiPath Orchestrator / Cloud with the developer's
  authenticated identity.

## Supported Versions

Security fixes are applied to the latest release on the `main` branch; there
is no long-term support for older versions. Re-run `uip skills install` (after
updating `@uipath/cli`) to pick up the latest skills and fixes.
