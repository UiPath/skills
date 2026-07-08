# Scenario: uia-healing-agent-pool-exhausted

A Faulted Orchestrator job for process **ERN** in folder **Shared** (job key `d2c90d73-bcee-4f9d-b9fc-d37146b7f6ff`) failed with `UiPath.UIAutomationNext.Exceptions.NodeNotFoundException` at the **Click 'Simt că am noroc'** activity in `Google.xaml` — an authoring-time selector typo (`aria-label='Simt că am noroccccccccccc'` vs. the live `aria-label='Simt că am noroc'`, 94% match).

`AutopilotForRobots.Enabled=true` and `HealingEnabled=true`, so Healing Agent was invoked — but it refused to run. The robot Error log carries *"…recovery failed. No available license / Agentic units to perform healing analysis and recovery."*, `uip or jobs healing-data` returned a 22-byte empty ZIP, and `uip or licenses info` shows **`Allowed.AgentService=5000` with `Used.AgentService=5000` (`Used >= Allowed`) and `LicensedFeatures=["HealingAgent"]`**.

Maps to **cause #7 (pool exhausted)** of `ui-automation/playbooks/healing-agent-no-license.md`: the tenant IS entitled to Healing Agent, but the Heals allocation is fully consumed for the billing period, so HA had no unit to spend. Release `ProcessType=Process` → regular Heals pool (`HealingAgent`). **Fix:** replenish the Heals pool (Admin → Licenses → Consumables) or wait for the billing reset — **not** acquire the Add-On.

This is distinct from `uia-healing-agent-no-license` (cause #1, `Allowed.AgentService=0`, fix = acquire the entitlement). The discriminator is the `licenses info` reading: entitlement present + pool spent vs. no entitlement at all.

`process/` holds the failing project snapshot; `data/m/r/` holds the mocked `uip` responses. Grading: `skill_triggered` + `llm_judge` vs `RESOLUTION.md` (final response only).
