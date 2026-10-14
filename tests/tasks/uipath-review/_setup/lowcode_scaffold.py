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
import shutil
import uuid
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


def stable_id(*parts: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "uipath-review-fixture/" + "/".join(parts)))


def string_props(fields: dict[str, str]) -> dict:
    return {
        name: {"type": "string", **({"description": desc} if desc else {})}
        for name, desc in fields.items()
    }


def apply_agent(
    project_dir: Path,
    *,
    system: str,
    user: str,
    input_schema: dict,
    output_schema: dict,
    settings: dict | None = None,
    guardrails: list[dict] | None = None,
) -> None:
    project_dir = Path(project_dir)
    for base in (project_dir, project_dir / ".agent-builder"):
        agent_path = base / "agent.json"
        data = json.loads(agent_path.read_text(encoding="utf-8"))
        data["inputSchema"] = json.loads(json.dumps(input_schema))
        data["outputSchema"] = json.loads(json.dumps(output_schema))
        data["settings"] = {**data["settings"], **(settings or {})}
        data["guardrails"] = json.loads(json.dumps(guardrails or []))
        set_message(data, "system", system)
        set_message(data, "user", user)
        _write_json(agent_path, data)
        ep_path = base / "entry-points.json"
        ep = json.loads(ep_path.read_text(encoding="utf-8"))
        ep["entryPoints"][0]["input"] = json.loads(json.dumps(input_schema))
        ep["entryPoints"][0]["output"] = json.loads(json.dumps(output_schema))
        _write_json(ep_path, ep)


def write_tool(
    project_dir: Path,
    name: str,
    description: str,
    inputs: dict[str, str],
    *,
    required: list[str] | None = None,
    outputs: dict | None = None,
    tool_type: str = "process",
) -> dict:
    if outputs is None or "type" not in outputs:
        output_schema = {"type": "object", "properties": string_props(outputs or {})}
    else:
        output_schema = outputs
    d = Path(project_dir) / "resources" / name
    d.mkdir(parents=True, exist_ok=True)
    _write_json(
        d / "resource.json",
        {
            "$resourceType": "tool",
            "id": stable_id("tool", name),
            "type": tool_type,
            "location": "external",
            "name": name,
            "description": description,
            "isEnabled": True,
            "inputSchema": {
                "type": "object",
                "properties": string_props(inputs),
                "required": list(required or []),
            },
            "outputSchema": output_schema,
            "settings": {},
            "guardrail": {"policies": []},
            "properties": {"processName": name, "folderPath": "Shared", "exampleCalls": []},
            "referenceKey": stable_id("tool-ref", name),
            "argumentProperties": {},
        },
    )
    return process_binding(name)


def write_context_index(
    project_dir: Path,
    name: str,
    description: str,
    index_name: str,
    query_description: str,
    *,
    threshold: float,
    result_count: int,
) -> None:
    d = Path(project_dir) / "resources" / name
    d.mkdir(parents=True, exist_ok=True)
    _write_json(
        d / "resource.json",
        {
            "$resourceType": "context",
            "id": stable_id("context", name),
            "referenceKey": None,
            "name": name,
            "description": description,
            "contextType": "index",
            "folderPath": "Shared",
            "indexName": index_name,
            "settings": {
                "retrievalMode": "semantic",
                "query": {"variant": "dynamic", "description": query_description},
                "folderPathPrefix": {"variant": "static"},
                "fileExtension": {"value": "All"},
                "threshold": threshold,
                "resultCount": result_count,
            },
        },
    )


def write_escalation(project_dir: Path, name: str, description: str, recipient_email: str) -> None:
    d = Path(project_dir) / "resources" / name
    d.mkdir(parents=True, exist_ok=True)
    _write_json(
        d / "resource.json",
        {
            "$resourceType": "escalation",
            "id": stable_id("escalation", name),
            "name": name,
            "description": description,
            "escalationType": 0,
            "isAgentMemoryEnabled": False,
            "ixpToolId": None,
            "storageBucketName": None,
            "properties": {},
            "governanceProperties": {"isEscalatedAtRuntime": False},
            "isEnabled": True,
            "channels": [
                {
                    "id": stable_id("escalation-channel", name),
                    "name": "Channel",
                    "description": description,
                    "type": "actionCenter",
                    "inputSchema": {"type": "object", "properties": string_props({"Content": "Agent output to review"})},
                    "inputSchemaDotnetTypeMapping": {"Content": "System.String"},
                    "outputSchema": {"type": "object", "properties": string_props({"Comment": "Reviewer comment"})},
                    "outputSchemaDotnetTypeMapping": {"Comment": "System.String"},
                    "outcomeMapping": {"approve": "continue", "reject": "end"},
                    "properties": {
                        "resourceKey": stable_id("escalation-app", name),
                        "appName": f"{name}App",
                        "folderName": "Shared",
                        "appVersion": 1,
                        "isActionableMessageEnabled": False,
                        "actionableMessageMetaData": None,
                    },
                    "recipients": [{"type": 3, "value": recipient_email}],
                    "taskTitle": f"{name} request",
                    "taskTitleV2": {
                        "type": "textBuilder",
                        "tokens": [{"type": "simpleText", "rawString": f"{name} request"}],
                    },
                    "labels": [],
                }
            ],
        },
    )


def _evaluator(name: str, type_: int, category: int, **extra) -> dict:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return {
        "fileName": f"evaluator-{slug}.json",
        "id": stable_id("evaluator", name),
        "name": name,
        "description": name,
        "type": type_,
        "category": category,
        "targetOutputKey": "*",
        "createdAt": "2026-01-01T00:00:00.000Z",
        "updatedAt": "2026-01-01T00:00:00.000Z",
        **extra,
    }


def equality_evaluator(name: str) -> dict:
    return _evaluator(name, 1, 0)


def llm_judge_evaluator(name: str, prompt: str) -> dict:
    return _evaluator(name, 5, 1, prompt=prompt, model="same-as-agent")


def trajectory_evaluator(name: str, prompt: str) -> dict:
    return _evaluator(name, 7, 3, prompt=prompt, model="same-as-agent")


def write_evals(project_dir: Path, evaluators: list[dict], datapoints: list[dict]) -> None:
    evals = Path(project_dir) / "evals"
    ev_dir = evals / "evaluators"
    shutil.rmtree(ev_dir, ignore_errors=True)
    ev_dir.mkdir(parents=True)
    for ev in evaluators:
        _write_json(ev_dir / ev["fileName"], ev)
    set_path = evals / "eval-sets" / "evaluation-set-default.json"
    eval_set = json.loads(set_path.read_text(encoding="utf-8"))
    eval_set["evaluatorRefs"] = [ev["id"] for ev in evaluators]
    eval_set["evaluations"] = [
        {
            "id": dp.get("id", stable_id("datapoint", dp["name"])),
            "name": dp["name"],
            "inputs": dp["inputs"],
            "expectedOutput": dp["expectedOutput"],
            "expectedAgentBehavior": dp.get("expectedAgentBehavior", ""),
            "simulationInstructions": dp.get("simulationInstructions", ""),
            "simulateInput": False,
            "simulateTools": dp.get("simulateTools", False),
            "inputGenerationInstructions": "",
            "evalSetId": EVAL_SET_ID,
            "source": "manual",
            "createdAt": "2026-01-01T00:00:00.000Z",
            "updatedAt": "2026-01-01T00:00:00.000Z",
        }
        for dp in datapoints
    ]
    _write_json(set_path, eval_set)


def builtin_guardrail(
    name: str,
    validator: str,
    scopes: list[str],
    action: dict,
    parameters: list[dict] | None = None,
    match_names: list[str] | None = None,
) -> dict:
    selector: dict = {"scopes": list(scopes)}
    if match_names is not None:
        selector["matchNames"] = list(match_names)
    return {
        "$guardrailType": "builtInValidator",
        "id": stable_id("guardrail", name),
        "name": name,
        "description": name,
        "validatorType": validator,
        "validatorParameters": list(parameters or []),
        "action": action,
        "enabledForEvals": True,
        "selector": selector,
    }
