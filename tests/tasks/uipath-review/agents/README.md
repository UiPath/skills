# Agent review evals (`uipath-review`)

## Low-code scenarios (`e2e`, weekly)

Each scenario plants a group of related rules and some decoys. `_shared/check_scenario_findings.py` grades the report against the task's `scenario.json` and prints one HIT/MISS line per planted rule.

| Dir | Agent type | Planted groups |
|---|---|---|
| `lowcode_scenario_clean_control/` | IT ticket triage, no defects | precision only |
| `lowcode_scenario_classifier/` | Email router | schema, settings, evals |
| `lowcode_scenario_rag_assistant/` | HR knowledge assistant | grounding, retrieval, evals |
| `lowcode_scenario_ops_actions/` | Order status with write tools | authority, irreversible actions, escalation |
| `lowcode_scenario_public_chat/` | Website chat | prompt injection, content safety |
| `lowcode_scenario_extractor_prompt/` | Invoice extractor | prompt quality, schema |
| `lowcode_scenario_eval_suite/` | Clean agent, bad evals | evals |
| `lowcode_scenario_orchestrator/` | Research orchestrator | delegation, tool selection, settings |
| `lowcode_scenario_guardrails/` | Balance notifications | guardrail audit and recommend |
| `lowcode_scenario_kitchen_sink/` | Refund triage | all groups |

## Single-rule tests (`smoke`, PR gate)

The remaining `lowcode_review_*` and `coded_review_*` tasks check one pipeline mechanism each (CLI pass-through, refresh of generated files, guardrail catalog fetch).

## Fixture self-test

`python3 -m pytest tasks/uipath-review/_shared/test_scenario_fixtures.py -v` builds every scenario fixture and checks the CLI rules it must trigger. Run it after a `uip` CLI upgrade.
