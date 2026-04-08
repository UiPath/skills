# Validation Plan: `uipath-lattice-flow` Skill

## Context

The `uipath-lattice-flow` skill was built in Phase 1 (OOTB nodes) and Phase 2 (dynamic resource nodes). Before shipping to users, we need to validate that the skill actually works — that an agent using it can produce correct `.flow` files from natural-language prompts.

This plan focuses on **validation only** (does the skill work?), not comparative evaluation against maestro-flow (which is a separate effort).

## Evaluation Infrastructure

The `coder_eval` framework at `/home/tmatup/root/coder_eval/` provides:

- **Task YAMLs**: Pydantic-validated `TaskDefinition` with agent config, sandbox setup, and success criteria
- **Sandbox**: `tempdir` driver with template overlays (`template_dir`, `starter_files`, `repo`)
- **13 criterion types**: `file_exists`, `file_contains`, `file_check`, `json_check`, `run_command` (with `score_from_stdout`), `pytest`, `file_matches_regex`, `pylint_score`, `reference_comparison`, `command_executed`, `commands_efficiency`, `import_check`, `uipath_eval`
- **Experiment layer**: 5-layer config merge (default → experiment → task → variant → CLI)
- **CLI**: `coder-eval run`, `coder-eval plan` (dry run), `coder-eval evaluate` (criteria against existing dir)
- **`uipcli`**: Installed via `@uipath/cli@0.1.21` into `node_modules/.bin/` (auto-added to PATH)
- **`$TASK_DIR`**: Env var pointing to task YAML's parent directory in `run_command` criteria

### Key Conventions from Updated Docs

- `python: {}` means "create venv, no extra packages" (required, empty braces)
- `template_sources` paths are **relative to the task YAML file**
- `uipcli` (from npm) vs `uip` (global) — existing tasks use `uipcli`; we'll use `uipcli` for consistency
- Tags must be lowercase kebab-case
- Experiment variants can inject additional `template_sources` (appended after task sources, last-wins)

## Skill Injection Strategy

The lattice-flow skill must be available for the agent to Read within the sandbox. Two approaches:

### Approach A: `template_dir` overlay (recommended)

Copy the entire skill directory into the sandbox so files are locally readable:

```yaml
template_sources:
  - type: template_dir
    path: "../../../../skills/skills/uipath-lattice-flow"
```

This copies SKILL.md, all references, and all templates into the sandbox root. The agent can then `Read` any skill file.

### Approach B: Custom CLAUDE.md with inline guidance

Use `starter_files` to write a CLAUDE.md that contains the essential instructions:

```yaml
template_sources:
  - type: starter_files
    files:
      - path: "CLAUDE.md"
        content: |
          Read SKILL.md for complete instructions on building .flow files.
          Reference docs are in references/. Templates are in assets/templates/.
```

**Decision: Use Approach A** — it's simpler and tests the actual skill files as-shipped.

## Validation Scope

### Tier 1: OOTB Flows (no CLI needed)

These test the core value proposition — building flows from bundled schemas without CLI dependency.

| # | Task | Reference Flow | Complexity | What It Tests |
|---|---|---|---|---|
| 1 | Create dice-roller flow | `dice-roller` | Simple | Trigger + script, minimal flow |
| 2 | Create calculator flow | `calculator-multiply` | Simple | Trigger + script + input variables |
| 3 | Add a decision branch | (edit task) | Simple | Edit existing flow, add node + edges |
| 4 | Remove a node and rewire | (edit task) | Simple | Edit existing flow, remove node |

### Tier 2: Mixed Flows (OOTB + mock placeholders)

These test whether the agent can build flow topology using OOTB nodes and mocks for dynamic nodes.

| # | Task | Reference Flow | Complexity | What It Tests |
|---|---|---|---|---|
| 5 | Create decision/branching flow | `devconnect-email` | Medium | Switch node, multiple branches |
| 6 | Create loop flow | `sales-pipeline-cleanup` | Simple | Loop pattern with mock data source |
| 7 | Create scheduled trigger flow | `sales-pipeline-hygiene` | Complex | Scheduled trigger + loop + switch |

### Tier 3: Dynamic Nodes (requires CLI + auth)

These test the full dynamic resource node workflow. Only runnable with `uip login`.

| # | Task | Reference Flow | Complexity | What It Tests |
|---|---|---|---|---|
| 8 | Create flow with RPA node | `hr-onboarding` subset | Medium | Registry + resource node construction |

## Task YAML Design

### Tier 1: New Flow Task (OOTB, no Bash)

```yaml
task_id: lattice-flow-dice-roller
description: "Create a dice-roller .flow using lattice-flow skill (no CLI)"
tags: [flow, lattice-flow, generate, no-cli]

agent:
  type: claude-code
  permission_mode: acceptEdits
  allowed_tools: ["Read", "Write", "Edit", "Glob", "Grep"]
  max_turns: 30

sandbox:
  driver: tempdir
  python: {}
  template_sources:
    - type: template_dir
      path: "../../../../skills/skills/uipath-lattice-flow"

initial_prompt: |
  You have the uipath-lattice-flow skill available in the current directory.
  Read SKILL.md for instructions.

  Create a UiPath Flow project named "DiceRoller" that simulates rolling a
  six-sided die and outputs the result (a random integer 1-6).

  Follow the skill's Quick Start workflow. Use the minimal-flow-template.json
  as your starting point. Save the flow as DiceRoller/flow_files/DiceRoller.flow
  and create DiceRoller/project.uiproj.

success_criteria:
  - type: file_exists
    description: "project.uiproj exists"
    path: "DiceRoller/project.uiproj"
    weight: 1.0
    pass_threshold: 1.0

  - type: json_check
    description: "Flow file is valid JSON with required top-level fields"
    path: "DiceRoller/flow_files/DiceRoller.flow"
    assertions:
      - expression: "nodes"
        operator: "type_is"
        expected: "array"
      - expression: "edges"
        operator: "type_is"
        expected: "array"
      - expression: "definitions"
        operator: "type_is"
        expected: "array"
    weight: 2.0
    pass_threshold: 1.0

  - type: run_command
    description: "Structural comparison against reference flow"
    command: "python3 $TASK_DIR/../shared/check_flow_structure.py DiceRoller/flow_files/DiceRoller.flow $TASK_DIR/../shared/references/dice-roller.flow"
    timeout: 10
    score_from_stdout: true
    weight: 5.0
    pass_threshold: 0.7

  - type: run_command
    description: "uipcli flow validate passes"
    command: "npx --yes @uipath/cli@0.1.21 flow validate DiceRoller/flow_files/DiceRoller.flow"
    timeout: 60
    expected_exit_code: 0
    weight: 3.0
    pass_threshold: 1.0

  - type: command_executed
    description: "Agent did NOT use Bash (CLI-free validation)"
    tool_name: "Bash"
    command_pattern: ".*"
    min_count: 0
    max_count: 0
    weight: 2.0
    pass_threshold: 1.0

max_iterations: 1
```

### Tier 1: Edit Flow Task

```yaml
task_id: lattice-flow-add-decision
description: "Add a decision branch to an existing dice-roller flow"
tags: [flow, lattice-flow, modify, no-cli]

agent:
  type: claude-code
  permission_mode: acceptEdits
  allowed_tools: ["Read", "Write", "Edit", "Glob", "Grep"]
  max_turns: 30

sandbox:
  driver: tempdir
  python: {}
  template_sources:
    - type: template_dir
      path: "../../../../skills/skills/uipath-lattice-flow"
    - type: template_dir
      path: "./artifacts"

initial_prompt: |
  You have the uipath-lattice-flow skill available in the current directory.
  Read SKILL.md for instructions.

  Read the flow at baseline.flow. Add a Decision node after the script node
  that checks if the dice result is greater than 3. Wire the "true" branch
  to a new End node and the "false" branch to another End node.

  Save the result as result.flow. Follow the skill's validation checklist.

success_criteria:
  - type: run_command
    description: "Decision node added and wired correctly"
    command: "python3 $TASK_DIR/check_edit.py"
    timeout: 10
    score_from_stdout: true
    weight: 5.0
    pass_threshold: 0.8

max_iterations: 2
```

### Tier 2: Mixed Flow Task

```yaml
task_id: lattice-flow-loop
description: "Create a loop-based flow with mock data source"
tags: [flow, lattice-flow, generate, no-cli, tier-2]

# Same structure as Tier 1 but prompt asks for loop + mock pattern
# Success criteria compare against OOTB-only subset of reference
```

### Tier 3: Dynamic Node Task

```yaml
task_id: lattice-flow-rpa-node
description: "Create a flow with an RPA workflow resource node via registry"
tags: [flow, lattice-flow, generate, dynamic, tier-3]

agent:
  type: claude-code
  permission_mode: acceptEdits
  allowed_tools: ["Bash", "Read", "Write", "Edit", "Glob", "Grep"]  # Bash needed for uipcli
  max_turns: 50

sandbox:
  driver: tempdir
  python: {}
  node:
    env_packages:
      - "@uipath/cli@0.1.21"
  template_sources:
    - type: template_dir
      path: "../../../../skills/skills/uipath-lattice-flow"
    - type: template_dir
      path: "../../../templates/uipath-flow-starter"
```

## Validation Scripts

### `check_flow_structure.py` — Reusable structural checker

Compares a generated `.flow` against a reference `.flow`, ignoring non-deterministic fields.

**Fields to ignore:** `id`, `nodes[*].id`, `edges[*].id`, `nodes[*].ui`, `metadata`, `model.entryPointId`, `model.projectId`, `bindings[*].id`, `solutionId`, `projectId`

**Fields that MUST match:**
- Node types: sorted list of `nodes[*].type`
- Edge topology: sorted list of `(sourcePort, targetPort)` pairs
- Definitions: sorted list of `definitions[*].nodeType`
- Variables: `variables.globals` declarations (id, direction, type)
- Node count and edge count

**Scoring (0.0-1.0):**

| Component | Weight | Check |
|---|---|---|
| Node types match | 0.30 | Sorted type lists are identical |
| Edge count matches | 0.20 | Same number of edges |
| Definitions cover all types | 0.20 | Every used nodeType has a definition |
| variables.globals match | 0.15 | Same variable declarations |
| variables.nodes present | 0.15 | Correct count of node output variables |

Invocation: `python3 check_flow_structure.py <generated.flow> <reference.flow>` — prints float score to stdout.

### `check_edit.py` — Per-task edit verification

Each edit task gets a custom checker verifying the specific edit (node added, edges wired, definitions present). Pattern follows existing `add_terminate_node` inline Python checks.

## File Manifest

```
coder_eval/tasks/uipath_flow/
├── lattice_shared/
│   ├── check_flow_structure.py              # Reusable structural comparison
│   └── references/                          # Reference .flow files for comparison
│       ├── dice-roller.flow
│       └── calculator-multiply.flow
├── lattice_dice_roller/
│   └── dice_roller.yaml                     # Task 1
├── lattice_calculator/
│   └── calculator.yaml                      # Task 2
├── lattice_add_decision/
│   ├── add_decision.yaml                    # Task 3
│   ├── artifacts/baseline.flow
│   └── check_edit.py
├── lattice_remove_node/
│   ├── remove_node.yaml                     # Task 4
│   ├── artifacts/baseline.flow
│   └── check_edit.py
├── lattice_decision_flow/
│   └── decision_flow.yaml                   # Task 5 (Tier 2)
├── lattice_loop_flow/
│   └── loop_flow.yaml                       # Task 6 (Tier 2)
├── lattice_scheduled_flow/
│   └── scheduled_flow.yaml                  # Task 7 (Tier 2)
└── lattice_rpa_node/
    └── rpa_node.yaml                        # Task 8 (Tier 3)
```

**Total: ~15 files** (8 task YAMLs + 1 shared checker + 2 reference flows + 2 edit checkers + 2 baseline artifacts)

## Execution

The coder_eval venv is at `/home/tmatup/root/coder_eval/.coder_eval`. Activate it before running:

```bash
cd /home/tmatup/root/coder_eval
source .coder_eval/bin/activate

# Dry run — validate task definitions
coder-eval plan tasks/uipath_flow/lattice_flow/

# Run Tier 1 only
coder-eval run tasks/uipath_flow/lattice_flow/ --tags no-cli

# Run all tiers
coder-eval run tasks/uipath_flow/lattice_flow/

# Run specific task
coder-eval run tasks/uipath_flow/lattice_flow/dice_roller/dice_roller.yaml
```

## Resolved Questions

1. **Skill injection**: Use `template_dir` pointing to the lattice-flow skill directory. This copies all skill files into the sandbox root, making them readable by the agent.

2. **Tier 2 reference comparison**: Use the skill's own distilled templates (`assets/templates/*.json`) as OOTB-only reference points. Check structural properties (correct OOTB node types present, proper loop/switch/trigger wiring) rather than exact match against full reference flows that contain dynamic nodes.

3. **CLI for validation**: Use `npx --yes @uipath/cli@0.1.21 flow validate` as a run_command criterion even for OOTB tasks — the agent doesn't call CLI, but we use it to verify the output. This avoids needing `node.env_packages` in the sandbox config.

4. **No-Bash enforcement**: Use `command_executed` criterion with `max_count: 0` on Bash tool to verify the agent didn't fall back to CLI. This is the key differentiator from maestro-flow.
