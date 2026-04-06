# Skill E2E Tests

End-to-end tests that verify AI agents can correctly use skills from this repository. Tests are defined as [coder_eval](https://github.com/UiPath/coder_eval) task YAML files.

## Prerequisites

1. **coder-eval** — install from GitHub:
   ```bash
   uv pip install "coder-eval @ git+https://github.com/UiPath/coder_eval.git"
   ```

2. **uip CLI** — the UiPath CLI must be available:
   ```bash
   npm install -g @uipath/cli
   ```

3. **ANTHROPIC_API_KEY** — set in your environment for the agent to run.

## Running Tests

```bash
cd tests

# Run all smoke tests
make e2e

# Run maestro-flow skill tests only
make e2e-flow

# Run a single task
SKILLS_REPO_PATH=$(cd .. && pwd) \
  coder-eval run tasks/uipath-maestro-flow/init_validate.yaml \
  -e experiments/default.yaml --proxy
```

The `SKILLS_REPO_PATH` environment variable defaults to the parent directory (repo root) when using `make`.

## Directory Structure

```
tests/
├── README.md
├── Makefile
├── experiments/
│   └── default.yaml              # Shared agent config (plugin, model, tools)
└── tasks/
    └── <skill-name>/             # One folder per skill
        └── <capability>.yaml     # One task per capability tested
```

## Adding Tests for a New Skill

1. Create `tests/tasks/<skill-name>/` matching the skill folder name under `skills/`.
2. Write one YAML file per capability you want to test.
3. Use minimal prompts — the goal is to test whether the skill guides the agent correctly.
4. Tag every task with `smoke` and the skill domain (e.g., `flow`, `platform`, `rpa`).

### Task ID Convention

```
skill-<domain>-<capability>
```

Examples: `skill-flow-init-validate`, `skill-platform-queue-operations`

### Task YAML Template

```yaml
task_id: skill-<domain>-<capability>
description: >
  Skill-guided evaluation: agent uses the <skill-name> skill to <what it does>.
tags: [skill, <domain>, <capability>, smoke]

agent:
  type: claude-code
  permission_mode: acceptEdits
  allowed_tools: ["Skill", "Bash", "Read", "Write", "Edit", "Glob", "Grep"]
  max_turns: 20

sandbox:
  driver: tempdir
  python: {}

initial_prompt: |
  <Minimal prompt — describe the goal, not the steps.>

success_criteria:
  - type: command_executed
    description: "Agent used the expected CLI command"
    tool_name: "Bash"
    command_pattern: '<regex matching the key command>'
    min_count: 1
    weight: 1.0
    pass_threshold: 1.0

  # Add file_exists, file_contains, run_command criteria as needed

max_iterations: 2

llm_reviewer:
  enabled: true
```
