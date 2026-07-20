# Attended Re-authentication / Hardware-token Handoff Pattern

Use this when a step needs a login the robot cannot perform — a physical hardware 2FA token, smart card, biometric, or any interactive sign-in that cannot be scripted. Cite this pattern in the SDD and route the build to `uipath-rpa`. This guide is the design contract, not the build.

## When to apply

Apply when the PDD's robot-attendance or signing-modality signals show a human must complete authentication: `hardware token`, `smart card`, `physical 2FA`, `OTP device`, `biometric`, `human present for login`.

**MFA factor handling is a security-policy decision, never a convenience default.** Preference order for any MFA-protected login:

1. **Approved application / certificate identity** — service principal, app registration, certificate/token auth against the target's API. No interactive factor to handle; confirm with the customer's security team first.
2. **Interactive attended handoff (this pattern)** — the human completes the MFA login, the robot uses the authenticated session. The default whenever no approved application identity exists — for hardware AND soft factors alike.
3. **Scripted soft factor** (TOTP secret / SMS / email code the robot reads) — **never by default**: a second factor the robot can read collapses MFA to one factor. Design it only with the security team's documented approval — flag `[SME REVIEW]`, store the secret in the Orchestrator credential store, record the approval in §16 Security & Data Handling.

Physical factors (hardware token, smart card, biometric) can never be scripted — options 1 or 2 only.

## Choose the design shape

Pick **A** when the login is the first step; pick **B** when authentication recurs or the session expires mid-run.

- **A — Login-before-handoff.** The human completes the token login, then starts or hands off to the attended robot, which uses the authenticated session. No in-process pause.
- **B — Mid-run pause + resume.** The robot runs to the auth gate, pauses, prompts the human to complete the token login, then verifies the post-login state before continuing.

## Specify the handoff contract (shape B)

Fill the §9 *Interactive Authentication / Re-auth Handoff* subsection with:

1. **Handoff point** — the step where the robot pauses.
2. **Human action** — exactly what the person does (insert token, complete portal login).
3. **Resume condition / state anchor** — the observable post-login state the robot checks before continuing (authenticated URL reached, dashboard element present).
4. **No-completion behavior** — timeout, then abort with notification (`[DEFAULT]` 5 min).
5. **Attendance** — Attended; record it in §16 Robot type.

## Rules

1. Verify the authenticated state before resuming. Never resume on a fixed delay.
2. Make the work after the gate idempotent — a failed handoff aborts and reruns; resume from the last committed item, not duplicates.
3. State the contract once per process. If it re-authenticates at several gates, reference the one contract.
4. Never design around reading the hardware token value — it cannot be done. The factor is the human's.

## What goes where

Specify in the SDD: the gate as a §2 process-map node; the handoff contract in §9; Attended in §16; a re-auth scenario in §17 (handoff completes → resumes; handoff times out → aborts cleanly).

Route to `uipath-rpa`: the pause mechanism, the state-anchor check, retry/timeout, session handling. Do not name activities or describe the implementation.

## Product reference

Attended robots run in the user's session with a person present; the supported path is the human completing the interactive / MFA login and handing off to the attended robot. See UiPath docs: [attended automations](https://docs.uipath.com/robot/standalone/2024.10/admin-guide/attended-automations), [interactive sign-in](https://docs.uipath.com/robot/standalone/2023.4/admin-guide/setting-up-interactive-sign-in). A physical token cannot be automated — the handoff is required.
