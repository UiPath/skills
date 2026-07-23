# Guardrail Skills Green Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every task in the `guardrail` evaluation slice pass without weakening the product-safety contracts those tasks protect.

**Architecture:** Align evaluator prompts and tool availability with the skills' declared contracts, then harden the skill guidance at the exact decision points that failed. Add deterministic repository-level contract tests for the non-probabilistic portions and use the coder-eval guardrail slice for end-to-end behavioral verification.

**Tech Stack:** Markdown skills, coder_eval YAML tasks, Python `unittest`, PyYAML, regular expressions, GitHub CLI.

## Global Constraints

- Preserve each skill's Critical Rules and self-contained operation.
- The review skill may write only an explicitly requested report outside the reviewed project; reviewed artifacts remain strictly read-only.
- Guardrail tests must grade observable behavior and must not weaken artifact-safety checks.
- All parsed UiPath CLI commands use `--output json`.

---

### Task 1: Repository Contract Regression Tests

**Files:**
- Create: `tests/scripts/test_guardrail_skill_contracts.py`

- [x] Write static tests for review report scope, prompt activation, WebSearch restrictions, coded/low-code guidance, and the Maestro regex boundary.
- [x] Run the test and confirm it fails against the current contracts.

### Task 2: Review Contract and Activation

**Files:**
- Modify: `skills/uipath-review/SKILL.md`
- Modify: ten guardrail task YAMLs under `tests/tasks/uipath-review/agents/`

- [x] Permit `Write` only for an explicit report path outside reviewed roots.
- [x] Keep all files inside reviewed projects immutable.
- [x] Make unattended no-PDD behavior non-blocking and require the report artifact when requested.
- [x] Keep guardrail review prompts user-realistic and rely on skill activation plus explicit report paths for unattended no-PDD behavior.

### Task 3: Agent Guardrail Authoring and Evaluation Alignment

**Files:**
- Modify: `skills/uipath-agents/references/coded/capabilities/guardrails/guardrails.md`
- Modify: `skills/uipath-agents/references/coded/capabilities/guardrails/guardrails-recommend.md`
- Modify: `skills/uipath-agents/references/lowcode/capabilities/guardrails/guardrails-recommend.md`
- Modify: affected coded/conversational guardrail task YAMLs
- Modify: `tests/tasks/uipath-agents/coded/guardrails/deterministic/check_deterministic.py`

- [x] Add concrete callable deterministic examples and AST-based verification.
- [x] Add a mandatory post-edit middleware-spread check and LLM-as-judge model discovery step.
- [x] Require validate-mode fixes to preserve and relocate validators.
- [x] Require semantic re-reading after low-code refresh/validate.
- [x] Disallow WebSearch in tasks that require direct SDK WebFetch while keeping the conversational scaffold prompt user-realistic.

### Task 4: Maestro Artifact-Safety Boundary

**Files:**
- Modify: `tests/tasks/uipath-maestro-case/guardrails/artifact_safety_guard.yaml`

- [x] Restrict Node/Python filesystem detection to commands that target enumerated skill artifacts.
- [x] Keep redirection, stream-editor, and helper-assembler protections intact.
- [x] Verify registry-cache reads remain allowed while artifact writes remain rejected.

### Task 5: Verification and Pull Request

- [x] Run the repository contract tests and Python checker tests.
- [x] Validate changed YAML/frontmatter and run focused task lint checks.
- [ ] Run all previously failing guardrail tasks, then the full `guardrail` slice. Blocked locally: the Claude runner is not authenticated, and the Codex fallback cannot access its state database under the managed sandbox policy.
- [ ] Review the diff, commit once, push the feature branch, and create one PR with exact test evidence.
