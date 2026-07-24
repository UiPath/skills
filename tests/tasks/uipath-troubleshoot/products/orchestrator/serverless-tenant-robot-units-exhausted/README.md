# Serverless — Tenant Robot Units Exhausted

Reproduces branch 3 of the **Automation Cannot Be Started —
Serverless Licensing / Robot Units** playbook: the tenant-wide Robot
Unit pool is fully consumed, so serverless (runtimetype 9) jobs are
refused at the licensing layer before any session is created:

```
Automation cannot be started. Your tenant's assigned Robot Units
have been exceeded. Allocate more Robot Units to your tenant to
continue.
```

## What this scenario uncovers

**Root Cause:** The `AcmeProd` tenant Robot Unit pool is at 25/25
used, 0 available. Two different serverless processes owned by two
different users (`LedgerSyncService`/alice, `ExpenseImporter`/bob)
fault identically overnight — the tenant-wide fingerprint. The
reporting user's Personal Automation quota (166/200) and per-user
Robot Units (0/5) both have headroom, so the constraint is the
shared tenant pool, not any per-user limit.

Maps to:
`references/products/orchestrator/playbooks/serverless-cannot-start-licensing.md`
(branch 3 — tenant Robot Units exhausted).

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` + `m/uip.cmd` | shared from `../../../_shared/mock_template/` |
| `process/` | minimal serverless UiPath project (LogMessage + Delay) |
| `data/m/r/*.json` | **synthetic** canned `uip` responses (jobs get/list/logs, `licenses info`) |
| `data/m/r/manifest.json` | dispatch table mapping each command to its fixture |

> Fixtures are authored from the playbook signature, not captured
> from a real session. Regenerate via
> `_shared/scripts/generate_scenario.py` before treating the score
> as a strict regression signal.

## Distinguishing fingerprints

| Branch | Fingerprint that rules it out here |
|---|---|
| Personal Automation quota (branch 1) | User quota 166/200 remaining; message names the tenant, not the user. |
| Per-user Robot Units (branch 2) | User has 0/5 units used — headroom, not the blocker. |
| **Tenant Robot Units (branch 3)** *(this scenario)* | `licenses info` tenant pool 0 of 25; two users fail identically; log says tenant-scoped reservation denied. |
| Time-limit cancellation (branch 4) | Jobs faulted ~0.8s after start — never executed. |

## Success criteria

Scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent identified tenant-wide Robot Unit pool exhaustion (0 of 25
  available) as the root cause — explicitly tenant scope, not
  per-user quota — and recommended allocating more Robot Units to
  the tenant (or freeing in-use units), then rerunning.
