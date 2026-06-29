# Logon Failure — Password Mismatch (Stale Orchestrator Credential)

This scenario reproduces the **"Could Not Start Executor — Logon
Failed for User"** playbook's **branch 3**: the AD password was
rotated for the unattended robot user, but the credential stored in
Orchestrator was not updated to match. Every job since the rotation
faults with:

```
Could not start executor. Logon failed for user UIPATH\USER1.
The user name or password is incorrect. (0x0000052E).
Last error: 131092. RDP connection failed.
```

## What this scenario uncovers

**Root Cause:** Three identical `InvoiceIngestor` runs (keys
`aabb1099-...`, `aabb1100-...`, `aabb1122-...`) faulted within
~25 minutes for service account `UIPATH\USER1` on `MOCK-HOST`. AD
`PasswordLastSet = 2026-05-11T07:14:00Z`, but Orchestrator's stored
credential record reports `PasswordLastSet = 2026-05-04T09:00:00Z` —
the platform is still sending the pre-rotation password. A sibling
unattended job (`OrderExporter` running as `UIPATH\USER2`) succeeded
on the same machine at `11:20Z`, so the host, RDP path, and network
are fine; the fault is scoped to the `USER1` credential.

This maps to:
`references/products/orchestrator/playbooks/job-faulted-logon-failure.md`
(branch 3 — password mismatch / stale Orchestrator credential).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `process/` | minimal background-unattended UiPath project (no UI activities — LogMessage + Delay only) |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

> **Note on fixtures.** Like sibling synthetic scenarios, the
> fixtures here were authored from the documented playbook
> signature rather than captured from a real `.investigation/`
> session. Regenerate via
> `_shared/scripts/generate_scenario.py` from a real failed-job
> session before treating this test's score as a regression
> signal.

## How this differs from sibling cause-branches of the same playbook

The `job-faulted-logon-failure` playbook covers six cause-branches.
The agent must select the right one — matching the **playbook** is
not enough. Distinguishing fingerprints:

| Branch | Fingerprint distinguishing it from branch 3 |
|---|---|
| **1 — Session-config mismatch** | `RequiresUserInteraction: true` AND `LoginToConsole: false`. Our scenario has `false` / `true` respectively. |
| **2 — Account locked in AD** | LSA returns `STATUS_ACCOUNT_LOCKED_OUT` (`0xC0000234`); Windows code `0x00000775`; Robot log says `Account is locked`. Our log explicitly says `Account is NOT locked` and code is `0x0000052E`. |
| **3 — Password mismatch** *(this scenario)* | LSA returns `STATUS_LOGON_FAILURE` (`0xC000006D`) with sub-status `0xC000006A` (wrong password); Windows code `0x0000052E`; account NOT locked; AD `PasswordLastSet` recent AND Orchestrator `PasswordLastSet` stale. |
| **4 — Lockout loop (3 → 2 chained)** | Same as branch 3 PLUS account is currently locked AND `badPwdCount` climbing rapidly. Our account is not yet locked — agent should flag this as a *risk* (H5), not as the current state. |
| **5 — MFA / Conditional Access** | LSA / Entra returns interactive-auth-required; Robot log mentions MFA / Conditional Access. Absent in our fixtures. |
| **6 — RDP slot conflict** | Other users also fail on the same machine; `query session` would show a disconnected RDP session. Our sibling user `USER2` *succeeds* on the same machine → branch 6 ruled out. |

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-diagnostics` skill
- Agent matched
  `orchestrator/playbooks/job-faulted-logon-failure.md` AND
  selected **branch 3 (password mismatch / stale Orchestrator
  credential)** as the root cause
- Conclusion must explicitly name the stale Orchestrator
  credential and propose the playbook's resolution sequence
  (pause triggers → update stored credential → verify → unlock
  if needed → re-enable triggers)
- Bonus (not required for pass): agent flags branch-4 lockout-loop
  risk while triggers remain active

## Regenerating from a real session

```bash
python tests/tasks/uipath-diagnostics/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.investigation> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name logon-failure-password-mismatch --apply
```
