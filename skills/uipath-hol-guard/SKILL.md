---
name: uipath-hol-guard
description: "UiPath development protection with HOL Guard for local coding-agent sessions that execute state-changing `uip` CLI commands. Installs and verifies the published `hol-guard` CLI, detects supported local harnesses, and launches protected sessions. For UiPath platform auth/operations→uipath-platform; for native agent guardrails→uipath-agents."
---

# UiPath HOL Guard

Use HOL Guard to supervise a supported local coding-agent session before that agent performs state-changing UiPath CLI work. HOL Guard protects the local agent execution boundary. UiPath authentication, tenant permissions, product guardrails, validation, and approvals remain authoritative.

## When to Use This Skill

- Before a local coding agent publishes, deploys, deletes, starts, or otherwise mutates UiPath resources through the `uip` CLI.
- When a user asks to put HOL Guard in front of a supported local Codex, Claude Code, Cursor, Gemini CLI, or other harness returned by Guard detection.
- When a user wants proof that Guard is active before allowing a high-impact UiPath action from an AI coding-agent session.

## Critical Rules

1. **Protect the local harness, not UiPath Cloud** - Never claim HOL Guard runs inside UiPath Cloud, intercepts server-side UiPath APIs, or replaces native UiPath agent guardrails.
2. **Keep UiPath controls authoritative** - Guard never replaces `uip` authentication, tenant permissions, product confirmations, validation, or review requirements.
3. **Use the published Guard package directly** - If `hol-guard` is missing, ask before installing `hol-guard` with `pipx`. Do not build a custom shell wrapper, approval layer, hook, or substitute security mechanism.
4. **Detect before wiring** - Run `hol-guard detect --json` and use only a harness Guard reports as supported. If no supported harness is detected, stop and explain the limitation.
5. **Verify wiring before mutation-bearing work** - After `hol-guard install <HARNESS>`, run `hol-guard status --json`. If Guard cannot be verified as active for the intended harness, stop. Do not bypass it by launching the harness directly.
6. **Run the mutation-bearing session through Guard** - Launch the next coding-agent session with `hol-guard run <HARNESS>` before that agent invokes state-changing `uip` commands. Do not treat an already-running unprotected session as retroactively protected.
7. **Honor deny, review, unavailable, and error states** - Never rerun the same UiPath mutation outside Guard to get around a Guard decision. Resolve approvals through Guard or stop.
8. **Treat dry-run as verification only** - `hol-guard run <HARNESS> --dry-run --default-action allow --json` checks the launch path; it is not a protected production session.
9. **Preserve evidence without secrets** - Use Guard status, approvals, and receipts for evidence. Do not copy credentials, tokens, or sensitive command payloads into reports.

## Quick Start

### 1. Check for HOL Guard

```bash
command -v hol-guard >/dev/null 2>&1 && hol-guard --version
```

If the command is missing, ask the user before installing:

```bash
pipx install hol-guard
hol-guard init
```

If `pipx` is unavailable, stop and report the prerequisite. Do not use an unreviewed bootstrap script as a fallback.

### 2. Detect the local harness

```bash
hol-guard detect --json
```

Choose only a harness reported by Guard. Do not guess a harness identifier.

### 3. Install and verify Guard for that harness

```bash
hol-guard install <HARNESS>
hol-guard status --json
```

If either step fails or status does not confirm the intended protection, stop before any state-changing UiPath command.

### 4. Verify the launch path

Before the first protected session, use a dry run:

```bash
hol-guard run <HARNESS> --dry-run --default-action allow --json
```

A successful dry run verifies wiring only. It does not authorize or execute UiPath mutations.

### 5. Launch the protected coding-agent session

```bash
hol-guard run <HARNESS>
```

Perform the requested `uip` work only from the protected session. Keep normal UiPath confirmation, validation, and permission checks in place.

### 6. Capture Guard evidence when needed

```bash
hol-guard status --json
hol-guard approvals
hol-guard receipts
```

Use the minimum evidence required for the task and redact secrets.

## What NOT to Do

- Do not write a custom `uip` wrapper or recreate Guard policy logic in the skill.
- Do not claim Guard protects an unsupported client merely because UiPath skills can run there.
- Do not run a denied or review-gated UiPath mutation directly from the native harness as a fallback.
- Do not imply that installing HOL Guard changes UiPath tenant-side security or permissions.
- Do not install software without user approval.
