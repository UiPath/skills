# Credential Store Unavailable

Reproduces the `credential-store-unavailable` playbook (Orchestrator
Database store branch): Orchestrator cannot retrieve the robot
credential because the store backend is unreachable, so jobs fail to
start.

```
Unable to retrieve credentials from Orchestrator Database credential
store. Please check your connection settings and ensure the
Orchestrator Database service is running.
```

## What this scenario uncovers

**Root Cause:** The Orchestrator SQL database backing the
"Orchestrator Database" credential store is unreachable (connection
timeout). The credential is never retrieved, so no logon is
attempted. Two unrelated processes (`SecurePortalBot`,
`VendorSyncBot`) on different machines fail identically — store-wide.
Fix: restore Orchestrator DB / credential-store connectivity, then
rerun.

Maps to:
`references/products/orchestrator/playbooks/credential-store-unavailable.md`.

## How this test reproduces it

| Layer | Source |
|---|---|
| `process/` | minimal unattended UiPath project |

> Fixtures authored from the playbook signature, not captured from a
> real session.

## Distinguishing fingerprint

The error is a credential **retrieval** failure (no logon code, no
`0x0000052E`), and it is **store-wide** (two unrelated processes on
different machines). That rules out a wrong/expired password
(robot-credentials / logon-failure) and points at the store backend.

## Success criteria

Scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent identified the credential-store backend (Orchestrator SQL
  database) as unreachable — not a wrong password — and recommended
  restoring store/DB connectivity (and testing the store) before
  rerunning.

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's UID/GID-isolated mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
