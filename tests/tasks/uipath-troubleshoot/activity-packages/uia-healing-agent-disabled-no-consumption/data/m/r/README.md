# Healing Agent Disabled / No Consumption — Faithful Replay

Replays a real `uipath-troubleshoot` investigation against a `uip` CLI mock. The fixtures are the verbatim sub-agent CLI responses captured from that session (PII scrubbed).

## What the original session uncovered

A user asked whether the Healing Agent ran on their **last job in folder `Shared`**, whether it consumed any AI units/credits, and what the `healing-agent` log line meant. The most-recent job (`BlankProcess2`, Attended/StudioPro) had **Faulted** on an unrelated UI Automation `NodeNotFoundException`. Healing Agent was **disabled** for the run (`AutopilotForRobots.Enabled=false`, `HealingEnabled=false`); the `"Healing agent is disabled for the current job."` Info log is a benign config-read; the healing-data archive is an empty 22-byte ZIP. Conclusion: **HA did not run and consumed nothing** — this is Surface 2 (the config-read log line) of the `healing-agent-orch-issues` playbook.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `fixtures/mocks/responses/*.json` | real stdout from the session (`jobs get` / `jobs list` / `jobs logs` repopulated from the recorded raw responses — the generator's compound-command backfill produced stubs) |
| `fixtures/mocks/responses/manifest.json` | substring dispatch table (unquoted keys) → recorded fixtures |

No `process/` snapshot — the source project was not part of the session (the investigation was CLI-driven).

## Success criteria

Scores the **conclusion**, not the trajectory (per `../CLAUDE.md`):

- Agent invoked the `uipath-troubleshoot` skill.
- LLM judge (vs `RESOLUTION.md`): HA did not run, zero consumption, the log line is informational.

## Re-running the extraction

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <.local/investigations dir> --transcript <session dir> \
    --scenario-name healing-agent-disabled-no-consumption --apply
```

Then repopulate any stub fixtures from the investigation's `raw/` responses and rewrite the manifest matches as unquoted substrings.
