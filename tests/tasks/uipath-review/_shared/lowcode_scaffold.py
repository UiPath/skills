#!/usr/bin/env python3
"""Shared scaffold helpers for uipath-review low-code agent tests.

Writes a minimal-but-valid low-code agent-builder project directly (no
`uip solution init` / `uip agent init`). The reviewer does read-only
static analysis, so a statically-written project is enough to exercise
the agents-lowcode-rules.md catalog deterministically and fast — and
without requiring the `uip` CLI to be on PATH (it isn't on the Linux
GitHub runner used in CI for tempdir-driver tasks).

The baseline layout mirrors what `uip agent init` produces for an
agent-builder low-code agent inside a solution:

  ReviewSol/
    ReviewSol.uipx
    AGENTS.md
    CLAUDE.md
    SampleAgent/
      agent.json
      entry-points.json
      project.uiproj
      flow-layout.json
      .agent-builder/
        agent.json
        bindings.json
        entry-points.json
      evals/
        eval-sets/
          evaluation-set-default.json
        evaluators/
          evaluator-default.json
          evaluator-default-trajectory.json
"""

import json
from pathlib import Path

SOLUTION_ID = "11111111-1111-4111-1111-111111111111"
PROJECT_ID = "22222222-2222-4222-2222-222222222222"
ENTRY_POINT_UID = "33333333-3333-4333-3333-333333333333"
EVAL_SET_ID = "44444444-4444-4444-4444-444444444444"
EVALUATOR_DEFAULT_ID = "55555555-5555-5555-5555-555555555555"
EVALUATOR_TRAJ_ID = "66666666-6666-6666-6666-666666666666"

BASELINE_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "input": {"type": "string", "description": "User input"},
    },
    "required": ["input"],
}

BASELINE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "content": {"type": "string", "description": "Agent response"},
    },
}

BASELINE_MESSAGES = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "{{input.input}}"},
]

BASELINE_SETTINGS = {
    "model": "gpt-4o-2024-11-20",
    "maxTokens": 16384,
    "temperature": 0,
    "engine": "basic-v2",
    "maxIterations": 25,
    "mode": "standard",
}


def _agent_json() -> dict:
    return {
        "version": "1.1.0",
        "settings": dict(BASELINE_SETTINGS),
        "inputSchema": json.loads(json.dumps(BASELINE_INPUT_SCHEMA)),
        "outputSchema": json.loads(json.dumps(BASELINE_OUTPUT_SCHEMA)),
        "messages": json.loads(json.dumps(BASELINE_MESSAGES)),
    }


def _entry_points_json() -> dict:
    return {
        "$schema": "https://cloud.uipath.com/draft/2024-12/entry-point",
        "$id": "entry-points.json",
        "entryPoints": [
            {
                "filePath": "/content/agent.json",
                "uniqueId": ENTRY_POINT_UID,
                "type": "agent",
                "input": json.loads(json.dumps(BASELINE_INPUT_SCHEMA)),
                "output": json.loads(json.dumps(BASELINE_OUTPUT_SCHEMA)),
            }
        ],
    }


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def write_baseline_lowcode_agent(
    solution_root: Path,
    *,
    project_name: str = "SampleAgent",
) -> Path:
    """Write a clean agent-builder low-code agent at
    ``<solution_root>/<project_name>/`` plus a solution wrapper. Returns
    the project directory path so callers can chain edits.
    """
    solution_root = Path(solution_root)
    project_dir = solution_root / project_name

    # --- solution-level files
    solution_root.mkdir(parents=True, exist_ok=True)
    _write_json(
        solution_root / f"{solution_root.name}.uipx",
        {
            "DocVersion": "1.0.0",
            "StudioMinVersion": "2025.10.0",
            "SolutionId": SOLUTION_ID,
            "Projects": [
                {
                    "Type": "Agent",
                    "ProjectRelativePath": f"{project_name}/project.uiproj",
                    "Id": PROJECT_ID,
                }
            ],
        },
    )
    (solution_root / "AGENTS.md").write_text(
        f"# {solution_root.name} solution\n\nTest fixture.\n",
        encoding="utf-8",
    )
    (solution_root / "CLAUDE.md").write_text(
        f"# {solution_root.name} solution\n\nTest fixture.\n",
        encoding="utf-8",
    )

    # --- project-level files
    project_dir.mkdir(parents=True, exist_ok=True)
    _write_json(project_dir / "agent.json", _agent_json())
    _write_json(project_dir / "entry-points.json", _entry_points_json())
    _write_json(
        project_dir / "project.uiproj",
        {
            "ProjectType": "Agent",
            "Name": project_name,
            "Description": None,
            "MainFile": None,
        },
    )
    _write_json(project_dir / "flow-layout.json", {"zoom": 1.0})

    # --- .agent-builder/ regenerated artifacts (same logical content)
    agent_builder = project_dir / ".agent-builder"
    agent_builder.mkdir(exist_ok=True)
    _write_json(agent_builder / "agent.json", _agent_json())
    _write_json(agent_builder / "entry-points.json", _entry_points_json())
    _write_json(
        agent_builder / "bindings.json",
        {"version": "2.0", "resources": []},
    )

    # --- evals (one eval set, two evaluators — same shape uip agent init emits)
    eval_sets = project_dir / "evals" / "eval-sets"
    evaluators = project_dir / "evals" / "evaluators"
    eval_sets.mkdir(parents=True, exist_ok=True)
    evaluators.mkdir(parents=True, exist_ok=True)
    _write_json(
        eval_sets / "evaluation-set-default.json",
        {
            "fileName": "evaluation-set-default.json",
            "id": EVAL_SET_ID,
            "name": "Default Evaluation Set",
            "batchSize": 10,
            "evaluatorRefs": [EVALUATOR_DEFAULT_ID, EVALUATOR_TRAJ_ID],
            "evaluations": [],
            "modelSettings": [],
            "agentMemoryEnabled": False,
            "agentMemorySettings": [],
            "lineByLineEvaluation": False,
            "createdAt": "2026-01-01T00:00:00.000Z",
            "updatedAt": "2026-01-01T00:00:00.000Z",
        },
    )
    _write_json(
        evaluators / "evaluator-default.json",
        {
            "fileName": "evaluator-default.json",
            "id": EVALUATOR_DEFAULT_ID,
            "name": "Default Evaluator",
            "description": "Semantic similarity LLM judge over agent output.",
            "type": 5,
            "category": 1,
            "prompt": "Score 0-100 by semantic similarity.",
        },
    )
    _write_json(
        evaluators / "evaluator-default-trajectory.json",
        {
            "fileName": "evaluator-default-trajectory.json",
            "id": EVALUATOR_TRAJ_ID,
            "name": "Default Trajectory Evaluator",
            "description": "Trajectory-based LLM judge.",
            "type": 7,
            "category": 3,
            "prompt": "Score 0-100 by trajectory adherence.",
        },
    )

    return project_dir
