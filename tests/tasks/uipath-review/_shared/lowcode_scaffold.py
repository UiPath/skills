#!/usr/bin/env python3
"""Shared scaffold helpers for uipath-review low-code agent tests.

Writes a minimal-but-valid low-code agent-builder project directly (no
`uip solution init` / `uip agent init`). The reviewer does read-only
static analysis, so a statically-written project is enough to exercise
the uipath-review pipeline (the `uip agent review` CLI plus the judgment
`agents-lowcode-rules.md` catalog) fast — and without requiring the `uip`
CLI to *scaffold* the fixture (it isn't on the Linux GitHub runner used in
CI for tempdir-driver tasks; the runner installs it for the task itself).

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
import re
from pathlib import Path

SOLUTION_ID = "11111111-1111-4111-8111-111111111111"
PROJECT_ID = "22222222-2222-4222-8222-222222222222"
ENTRY_POINT_UID = "33333333-3333-4333-8333-333333333333"
EVAL_SET_ID = "44444444-4444-4444-8444-444444444444"
EVALUATOR_DEFAULT_ID = "55555555-5555-4555-8555-555555555555"
EVALUATOR_TRAJ_ID = "66666666-6666-4666-8666-666666666666"

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
    {
        "role": "system",
        "content": "You are a helpful assistant.",
        "contentTokens": [
            {"type": "simpleText", "rawString": "You are a helpful assistant."},
        ],
    },
    {
        "role": "user",
        "content": "{{input.input}}",
        "contentTokens": [
            {"type": "variable", "rawString": "input.input"},
        ],
    },
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
        "metadata": {
            "storageVersion": "50.0.0",
            "isConversational": False,
            "showProjectCreationExperience": False,
            "targetRuntime": "pythonAgent",
        },
        "type": "lowCode",
        "messages": json.loads(json.dumps(BASELINE_MESSAGES)),
        "guardrails": [],
        "projectId": PROJECT_ID,
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


_TOKEN_RE = re.compile(r"\{\{\s*([^}]+?)\s*\}\}")


def content_tokens(content: str) -> list[dict]:
    """Build the ``contentTokens`` array matching a message ``content`` string.

    `uip agent validate` requires contentTokens to mirror content segment by
    segment: plain text becomes ``simpleText`` entries and each ``{{expr}}``
    becomes a ``variable`` entry. Inject scripts that patch a message's
    ``content`` MUST also set ``contentTokens = content_tokens(content)`` or
    the fixture fails schema validation before the reviewer ever sees the
    intended defect signal.
    """
    tokens: list[dict] = []
    pos = 0
    for m in _TOKEN_RE.finditer(content):
        if m.start() > pos:
            tokens.append({"type": "simpleText", "rawString": content[pos : m.start()]})
        tokens.append({"type": "variable", "rawString": m.group(1)})
        pos = m.end()
    if pos < len(content):
        tokens.append({"type": "simpleText", "rawString": content[pos:]})
    return tokens


def set_message(agent_data: dict, role: str, content: str) -> None:
    """Set a message's content AND its matching contentTokens in one step."""
    for msg in agent_data.get("messages", []):
        if msg.get("role") == role:
            msg["content"] = content
            msg["contentTokens"] = content_tokens(content)


def connection_binding(connection_id: str, connector_key: str) -> dict:
    """One bindings_v2 entry for an integration tool's connection.

    Mirrors the packager's generateBindings() output — `uip agent validate`
    derives the expected entries from the tool resources and fails with
    "expected binding entry ... is not present on disk" when they're absent.
    """
    return {
        "resource": "connection",
        "key": connection_id,
        "value": {
            "connectionId": {
                "defaultValue": connection_id,
                "isExpression": False,
                "displayName": "Connection ID",
            }
        },
        "metadata": {
            "connector": connector_key,
            "useConnectionService": "true",
            "bindingsVersion": "2.2",
            "solutionsSupport": "true",
        },
    }


def process_binding(process_name: str, folder_path: str = "Shared") -> dict:
    """One bindings_v2 entry for a process tool (see connection_binding)."""
    return {
        "resource": "process",
        "key": process_name,
        "value": {
            "name": {
                "defaultValue": process_name,
                "isExpression": False,
                "displayName": "Process name",
            },
            "folderPath": {
                "defaultValue": folder_path,
                "isExpression": False,
                "displayName": "Folder path",
            },
        },
        "metadata": {
            "subType": "process",
            "bindingsVersion": "2.2",
            "solutionsSupport": "true",
        },
    }


def write_bindings(project_dir: Path, entries: list[dict]) -> None:
    """Write bindings_v2.json (root) + .agent-builder/bindings.json with the
    given entries, matching what `uip agent refresh` would generate."""
    data = {"version": "2.0", "resources": entries}
    _write_json(Path(project_dir) / "bindings_v2.json", data)
    _write_json(Path(project_dir) / ".agent-builder" / "bindings.json", data)


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
    # Root-level bindings_v2.json — real `uip agent init` projects carry it,
    # and `uip agent validate` requires it as soon as resources/ exists.
    _write_json(project_dir / "bindings_v2.json", {"version": "2.0", "resources": []})

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
            "model": "same-as-agent",
            "targetOutputKey": "*",
            "createdAt": "2026-01-01T00:00:00.000Z",
            "updatedAt": "2026-01-01T00:00:00.000Z",
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
            "model": "same-as-agent",
            "targetOutputKey": "*",
            "createdAt": "2026-01-01T00:00:00.000Z",
            "updatedAt": "2026-01-01T00:00:00.000Z",
        },
    )

    return project_dir
