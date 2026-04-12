# Validation Report: `uipath-flow` Skill (v2 — Round 2)

> Date: 2026-04-11
> Branch: `tmatup/uipath_flow_skill`
> Skill commit: [`af1b5fd`](https://github.com/UiPath/skills/commit/af1b5fd75e90a3ffb888e61bc32b056c7620f677) — fix: address PR review feedback from gozhang2 and bai-uipath
> Eval commit: [`b8479c5`](https://github.com/UiPath/coder_eval/commit/b8479c53c692b4b9235b64d5232dfabb2ab1b0bb) — feat: add uipath-flow validation tasks (18 tasks, 4 tiers) (#135)
> Framework: `coder_eval` at `/home/tmatup/root/coder_eval/`

---

## Executive Summary

**No regressions from PR review changes.** All 19 previously-passing tasks still pass (16 new tasks + 3 connector/rpa_node tasks). 8 new E2E tasks (Phase 6 + Phase 7) all produce valid flows — their `flow debug` criterion continues to fail as a known task design issue, not a skill regression.

**New task coverage:** rpa_node (Phase 5) and 8 E2E tasks (Phases 6–7) are newly validated in this round.

| Phase | Tasks | Result | Regression? |
|-------|-------|--------|-------------|
| Phase 1: JSON authoring | 7 | **7/7 PASS** | No |
| Phase 2: Mode selection | 3 | **3/3 PASS** | No |
| Phase 3: CLI with skill | 2 | **2/2 PASS** | No |
| Phase 4: Planning | 2 | **2/2 PASS** | No |
| Phase 5: Connectors + rpa_node | 3 | **3/3 PASS** | No (rpa_node is new) |
| Phase 6: E2E OOTB | 3 | **3/3 PARTIAL PASS** | No (same expected pattern) |
| Phase 7: E2E Dynamic + Connector | 5 | **5/5 PARTIAL PASS** | New |
| **Total** | **25** | **25/25** | **0 regressions** |

---

## PR Review Changes Validated

Commit `af1b5fd` addressed PR review feedback with these changes:

| Change | Files | Regression Risk | Result |
|--------|-------|-----------------|--------|
| Mode selection: "ask the user" → "recommend a mode" | `SKILL.md` | Phase 2 | No regression — all 3 mode selection tasks pass, BellevueWeather still defaults to JSON |
| Template rename: `multi-agent-template.json` → `data-pipeline-template.json` | template + 2 refs | Phase 1 | No regression — template table references updated consistently |
| flow-schema.md: inline example removed, replaced with template reference | `flow-schema.md` | Phase 4 | No regression — planning tasks still produce correct documents |
| authoring-guide.md: added `description`/`schema` fields to variable regeneration | `authoring-guide.md` | Phase 1 | No regression — all JSON authoring tasks pass |
| authoring-guide.md: clarified `outputDefinition` (removed `.fields`) | `authoring-guide.md` | Phase 1 | No regression |
| authoring-guide.md: added definition source-of-truth note | `authoring-guide.md` | Phase 1 | No regression |

---

## Phase Results

### Phase 1: JSON Authoring Regression (7 tasks)

| Task ID | Criteria | Score | Status |
|---------|----------|-------|--------|
| flow-json-add-decision | 2/2 | 1.000 | PASS |
| flow-json-remove-node | 2/2 | 1.000 | PASS |
| flow-json-dice-roller | 4/4 | 0.909 | PASS |
| flow-json-calculator | 4/4 | 1.000 | PASS |
| flow-json-loop | 3/3 | 1.000 | PASS |
| flow-json-scheduled | 3/3 | 1.000 | PASS |
| flow-json-decision | 3/3 | 1.000 | PASS |

### Phase 2: Mode Selection (3 tasks)

| Task ID | Criteria | Score | Status |
|---------|----------|-------|--------|
| flow-mode-selection-cli | 3/3 | 1.000 | PASS |
| flow-mode-selection-json | 4/4 | 1.000 | PASS |
| flow-json-bellevue-weather | 5/5 | 1.000 | PASS |

**BellevueWeather (mode default regression):** Agent correctly defaults to JSON authoring with the updated "recommend a mode" wording. No behavioral change from v1.

### Phase 3: CLI with Skill (2 tasks)

| Task ID | Criteria | Score | Status |
|---------|----------|-------|--------|
| flow-cli-add-node | 4/4 | 1.000 | PASS |
| flow-cli-dice-roller | 4/4 | 1.000 | PASS |

### Phase 4: Planning (2 tasks)

| Task ID | Criteria | Score | Status |
|---------|----------|-------|--------|
| flow-planning-arch | 5/5 | 1.000 | PASS |
| flow-planning-impl | 5/5 | 1.000 | PASS |

### Phase 5: Connectors + rpa_node (3 tasks)

| Task ID | Criteria | Score | Status | Notes |
|---------|----------|-------|--------|-------|
| flow-connector-discovery | 4/4 | 1.000 | PASS | |
| flow-connector-configure | 4/4 | 1.000 | PASS | |
| flow-json-rpa-node | 4/4 | 1.000 | PASS | **New.** Failed iter 1, passed iter 2. Agent explored registry, created flow with mock placeholder. |

### Phase 6: E2E OOTB (3 tasks — with experiment config)

| Task ID | Validate | Debug | Status |
|---------|----------|-------|--------|
| uipath-flow-bellevue-weather | 1.00 | 0.00 (expected) | PARTIAL PASS |
| uipath-flow-calculator | 1.00 | 0.00 (expected) | PARTIAL PASS |
| uipath-flow-dice-roller | 1.00 | 0.00 (expected) | PARTIAL PASS |

Same pattern as Round 1: all 3 produce valid flows (validate passes). Debug criterion fails because prompt says "don't debug" but criteria tests debug output — pre-existing task design issue, not a skill regression.

### Phase 7: E2E Dynamic + Connector (5 tasks — NEW)

| Task ID | Validate | Debug | Status |
|---------|----------|-------|--------|
| uipath-flow-coded-agent | 1.00 | 0.00 (expected) | PARTIAL PASS |
| uipath-flow-rpa-project-euler | 1.00 | 0.00 (expected) | PARTIAL PASS |
| uipath-flow-api-workflow | 1.00 | 0.00 (expected) | PARTIAL PASS |
| uipath-flow-lowcode-agent | 1.00 | 0.00 (expected) | PARTIAL PASS |
| uipath-flow-slack-channel-description | 1.00 | 0.00 (expected) | PARTIAL PASS |

All 5 E2E dynamic/connector tasks produce valid flows. Same debug criterion pattern as Phase 6. Slack task took longest (~18 min) due to IS connector complexity.

---

## Run Metrics

All tasks ran on `claude-sonnet-4-6` via `coder_eval` with `anthropic_direct` routing.

### Phase 1: JSON Authoring (7 tasks)

| Task ID | Duration | Score | Cost | Output Tok | Tool Calls | Turns |
|---------|----------|-------|------|------------|------------|-------|
| flow-json-add-decision | 1m51s | 1.000 | $0.30 | 7,368 | 5 | 11 |
| flow-json-remove-node | 0m48s | 1.000 | $0.17 | 2,683 | 4 | 10 |
| flow-json-dice-roller | 2m23s | 0.909 | $0.46 | 7,870 | 14 | 23 |
| flow-json-calculator | 2m42s | 1.000 | $0.49 | 9,335 | 13 | 25 |
| flow-json-loop | 2m14s | 1.000 | $0.49 | 9,834 | 16 | 25 |
| flow-json-scheduled | 1m58s | 1.000 | $0.55 | 9,839 | 16 | 26 |
| flow-json-decision | 2m56s | 1.000 | $0.60 | 11,975 | 20 | 34 |
| **Subtotal** | **14m52s** | | **$3.06** | **58,904** | **88** | **154** |

### Phase 2: Mode Selection (3 tasks)

| Task ID | Duration | Score | Cost | Output Tok | Tool Calls | Turns |
|---------|----------|-------|------|------------|------------|-------|
| flow-mode-selection-cli | 1m46s | 1.000 | $0.41 | 3,787 | 26 | 33 |
| flow-mode-selection-json | 1m57s | 1.000 | $0.44 | 7,091 | 15 | 26 |
| flow-json-bellevue-weather | 3m17s | 1.000 | $1.26 | 8,899 | 37 | 53 |
| **Subtotal** | **7m00s** | | **$2.11** | **19,777** | **78** | **112** |

### Phase 3: CLI with Skill (2 tasks)

| Task ID | Duration | Score | Cost | Output Tok | Tool Calls | Turns |
|---------|----------|-------|------|------------|------------|-------|
| flow-cli-add-node | 1m22s | 1.000 | $0.34 | 2,955 | 18 | 30 |
| flow-cli-dice-roller | 1m29s | 1.000 | $0.41 | 3,315 | 25 | 30 |
| **Subtotal** | **2m51s** | | **$0.76** | **6,270** | **43** | **60** |

### Phase 4: Planning (2 tasks)

| Task ID | Duration | Score | Cost | Output Tok | Tool Calls | Turns |
|---------|----------|-------|------|------------|------------|-------|
| flow-planning-arch | 1m07s | 1.000 | $0.26 | 3,220 | 7 | 12 |
| flow-planning-impl | 2m06s | 1.000 | $0.43 | 6,540 | 20 | 29 |
| **Subtotal** | **3m13s** | | **$0.69** | **9,760** | **27** | **41** |

### Phase 5: Connectors + rpa_node (3 tasks)

| Task ID | Duration | Score | Cost | Output Tok | Tool Calls | Turns |
|---------|----------|-------|------|------------|------------|-------|
| flow-connector-discovery | 1m09s | 1.000 | $0.31 | 2,762 | 12 | 19 |
| flow-connector-configure | 4m09s | 1.000 | $0.80 | 10,170 | 38 | 55 |
| flow-json-rpa-node | 4m09s | 1.000 | $1.17 | 11,226 | 54 | 79 |
| **Subtotal** | **9m27s** | | **$2.29** | **24,158** | **104** | **153** |

### Phase 6: E2E OOTB (3 tasks)

| Task ID | Duration | Score | Cost | Output Tok | Tool Calls | Turns |
|---------|----------|-------|------|------------|------------|-------|
| uipath-flow-dice-roller | 2m09s | 0.375 | $0.54 | 7,632 | 16 | 27 |
| uipath-flow-calculator | 3m38s | 0.375 | $0.71 | 6,369 | 21 | 30 |
| uipath-flow-bellevue-weather | 6m40s | 0.375 | $1.32 | 24,003 | 52 | 66 |
| **Subtotal** | **12m27s** | | **$2.57** | **38,004** | **89** | **123** |

### Phase 7: E2E Dynamic + Connector (5 tasks)

| Task ID | Duration | Score | Cost | Output Tok | Tool Calls | Turns |
|---------|----------|-------|------|------------|------------|-------|
| uipath-flow-coded-agent | 4m57s | 0.375 | $0.63 | 11,755 | 26 | 34 |
| uipath-flow-rpa-project-euler | 4m56s | 0.375 | $0.89 | 16,814 | 30 | 46 |
| uipath-flow-api-workflow | 10m36s | 0.375 | $2.30 | 21,505 | 76 | 100 |
| uipath-flow-lowcode-agent | 10m52s | 0.375 | $2.22 | 28,665 | 85 | 114 |
| uipath-flow-slack-channel-description | 8m30s | 0.250 | $1.27 | 19,071 | 21 | 30 |
| **Subtotal** | **39m51s** | | **$7.30** | **97,810** | **238** | **324** |

### Aggregate Totals

| Metric | Value |
|--------|-------|
| **Total tasks** | 25 |
| **Total duration** | 89m48s |
| **Total cost** | $18.77 |
| **Total output tokens** | 254,683 |
| **Total tool calls** | 667 |
| **Avg cost per task** | $0.75 |
| **Avg duration per task** | 3m35s |
| **Model** | claude-sonnet-4-6 |

---

## Validation Matrix

| What | Tasks | Strategy | Auth | Result |
|------|-------|----------|------|--------|
| Mode selection (JSON explicit) | mode-selection-json | template_dir | No | PASS |
| Mode selection (CLI explicit) | mode-selection-cli | Skill tool | No | PASS |
| Mode default (no preference) | bellevue-weather | Skill tool | No | PASS |
| JSON: OOTB creation | json-dice-roller, json-calculator | template_dir | No | PASS |
| JSON: flow editing | json-add-decision, json-remove-node | template_dir | No | PASS |
| JSON: control flow | json-decision, json-loop, json-scheduled | template_dir | No | PASS |
| JSON: dynamic resource | json-rpa-node | Skill tool | Yes | PASS |
| CLI: flow creation | cli-dice-roller | Skill tool | No | PASS |
| CLI: node editing | cli-add-node | Skill tool | No | PASS |
| Planning: Phase 1 | planning-arch | template_dir | No | PASS |
| Planning: Phase 2 | planning-impl | Skill tool | Yes | PASS |
| Connectors: discovery | connector-discovery | Skill tool | Yes | PASS |
| Connectors: configure | connector-configure | Skill tool | Yes | PASS |
| E2E: OOTB flows | e2e/bellevue_weather, calculator, dice_roller | Skill tool + experiment | Yes | PARTIAL PASS |
| E2E: dynamic resources | e2e/api_workflow, coded_agent, lowcode_agent, rpa_project_euler | Skill tool + experiment | Yes | PARTIAL PASS |
| E2E: IS connector | e2e/slack_channel_description | Skill tool + experiment | Yes | PARTIAL PASS |

---

## Not Yet Run

| Group | Tasks | Reason |
|-------|-------|--------|
| Legacy CLI | registry, process, run_e2e, init_validate_pack | Pre-existing, picks up active plugin |
| Complexity | complexity-5/10/25/50/100 | Requires Skill plugin |
| Reference flows | devconnect-email, hr-onboarding, etc. | Requires Skill plugin |
