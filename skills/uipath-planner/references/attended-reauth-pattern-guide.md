# Attended Re-authentication / Hardware-token Handoff Pattern

Use when authentication requires human attendance, including a hardware 2FA token, smart card, biometric, OTP device, or other unscriptable interactive sign-in. Cite this pattern in the SDD and route the build to `uipath-rpa`. This is the design contract, not the build.

## Authentication choice and design shape

Apply when the PDD identifies human attendance or a modality such as `hardware token`, `smart card`, `physical 2FA`, `OTP device`, `biometric`, or `human present for login`.

MFA handling is a security-policy decision, not a convenience default. Prefer:

1. **Approved application / certificate identity** — service principal, app registration, or certificate/token authentication against the target API; confirm with the customer's security team first.
2. **Interactive attended handoff (this pattern)** — the human completes MFA and the robot uses the authenticated session when no approved application identity exists. This applies to hardware and soft factors.
3. **Scripted soft factor** — a TOTP secret, SMS, or email code read by the robot. Use only with documented security-team approval; flag `[SME REVIEW]`, store the secret in the Orchestrator credential store, and record approval in §16 Security & Data Handling. Never use it by default because it collapses MFA to one factor.

Physical factors—hardware tokens, smart cards, and biometrics—cannot be scripted; use option 1 or 2 only.

Choose the design shape:

- **A — Login-before-handoff:** When login is first, the human completes token login, then starts or hands off to the attended robot. Do not pause in-process.
- **B — Mid-run pause + resume:** When authentication recurs or the session may expire, run to the authentication gate, pause, prompt the human, and verify the post-login state before continuing.

## Handoff contract for shape B

Complete §9 *Interactive Authentication / Re-auth Handoff* with:

1. **Handoff point** — the step where the robot pauses.
2. **Human action** — exactly what the person does, such as inserting the token and completing portal login.
3. **Resume condition / state anchor** — the observable authenticated state, such as the expected URL or dashboard element.
4. **No-completion behavior** — timeout, then abort with notification (`[DEFAULT]` 5 min).
5. **Attendance** — Attended; record it in §16 Robot type.

## Rules

1. Verify the authenticated state before resuming; never resume on a fixed delay.
2. Make work after the gate idempotent. If handoff fails, abort and rerun from the last committed item without duplicates.
3. State the contract once per process; reference it for additional re-authentication gates.
4. Never design around reading the hardware-token value; the factor is the human's.

## SDD placement and build routing

Specify the gate as a §2 process-map node, the handoff contract in §9, Attended in §16, and a §17 re-auth scenario covering successful handoff/resumption and timeout/clean abort.

Route to `uipath-rpa` the pause mechanism, state-anchor check, retry/timeout, and session handling. Do not name activities or describe implementation.

## Product reference

Attended robots run in the user's session with a person present. The supported path is the human completing the interactive/MFA login and handing off to the attended robot. See UiPath docs: [attended automations](https://docs.uipath.com/robot/standalone/2024.10/admin-guide/attended-automations), [interactive sign-in](https://docs.uipath.com/robot/standalone/2023.4/admin-guide/setting-up-interactive-sign-in). A physical token cannot be automated; the handoff is required.