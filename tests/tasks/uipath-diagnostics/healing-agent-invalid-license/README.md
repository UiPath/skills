# Healing Agent Invalid License — Faithful Replay

This scenario replays a real UiPath diagnostic investigation where the
agent reached a verified resolution. The fixtures are the verbatim
`uip` CLI responses captured from that session.

## What the original session uncovered

A Faulted Orchestrator job for process **ERN** in folder **Shared** (job key `d2c90d73-bcee-4f9d-b9fc-d37146b7f6ff`) failed with `UiPath.UIAutomationNext.Exceptions.NodeNotFoundException` at the **Click 'Simt că am noroc'** activity in `Google.xaml` — an authoring-time selector typo (`aria-label='Simt că am noroccccccccccc'` with nine extra trailing `c` characters vs. the live `aria-label='Simt că am noroc'` at 94% match).

`AutopilotForRobots.Enabled=true` and `HealingEnabled=true` on the job, so Healing Agent was invoked — but it refused to run. The robot Error log at `2026-05-15T17:10:18.218Z` contains the deterministic line *"'Click 'Simt că am noroc'' activity recovery failed. No available license / Agentic units to perform healing analysis and recovery."*, `uip or jobs healing-data` returned a 22-byte empty ZIP, and `uip or licenses info` confirmed `Allowed.AgentService=0` with `LicensedFeatures=[]` despite `SubscriptionPlan='ENTERPRISE'`.

The match is **cause #1** in `healing-agent-no-license.md` — *No Healing Agent entitlement on the tenant*. RuntimeType=`StudioPro` (Non-Test set) means the requested pool is regular **Heals** (operation code `HealingAgent`), not Test Heals. Fix: acquire the Healing Agent Add-On for the tenant, or move to Flex Advanced / Unified Enterprise.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `process/` | frozen snapshot of the failing UiPath project |
| `fixtures/mocks/responses/*.json` | real stdout extracted verbatim from the session transcript |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its recorded fixture |

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-diagnostics` skill
- Agent matched the correct playbook AND reached the same root cause as `RESOLUTION.md`

## Re-running the extraction

If the source transcript or project changes, regenerate the scenario:

```bash
python tests/tasks/uipath-diagnostics/_shared/scripts/generate_scenario.py \
    --investigation <path> --project <path> --transcript <path> \
    --scenario-name healing-agent-invalid-license --apply
```
