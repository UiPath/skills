# CredProvider Path — Known Robot Defect (ROBO-4022)

Reproduces the `known-issue-robot-defect` playbook: a `Could not
start executor` fault whose signature matches a documented,
already-fixed Robot defect.

```
Could not start executor. Could not find a part of the path
'C:\Windows\TEMP\UiPath\CredProvider'.
```

## What this scenario uncovers

**Root Cause:** A known Robot defect (ROBO-4022) fixed in Robot
23.10.9. The host runs 23.10.4 (predates the fix). The correct fix
is to **upgrade the Robot to ≥ 23.10.9** — not to hand-create the
missing folder or change TEMP permissions.

Maps to:
`references/products/orchestrator/playbooks/known-issue-robot-defect.md`.

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` + `m/uip.cmd` | shared from `../../../_shared/mock_template/` |
| `process/` | minimal unattended UiPath project |
| `data/m/r/*.json` | **synthetic** canned `uip` responses — jobs get/list/logs plus `machines list` showing Robot 23.10.4 |
| `data/m/r/manifest.json` | dispatch table |

> Fixtures authored from the playbook signature (and the OR backlog's
> ROBO-4022 / 23.10.9 fact), not captured from a real session.

## Distinguishing fingerprint / common wrong turn

The Info names a missing TEMP path, which tempts a naive "create the
folder / fix TEMP permissions" answer. The playbook-driven diagnosis
recognizes the signature as a **known Robot defect** and checks the
host Robot version (23.10.4 < 23.10.9) — the correct fix is a Robot
upgrade. An agent that suggests recreating the directory scores low;
one that identifies the known issue and recommends the upgrade scores
full.

## Success criteria

Scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent identified the CredProvider-path fault as a known Robot
  defect (fixed in 23.10.9) given the host's older 23.10.4 build, and
  recommended upgrading the Robot to ≥ 23.10.9 rather than
  hand-creating the folder or editing TEMP permissions.
