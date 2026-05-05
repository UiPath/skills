"""Static checks for committed Flow examples.

These tests keep copy-pasteable example flows aligned with the skill rules
without requiring a tenant, debug run, or network access.
"""

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
EXAMPLES_DIR = REPO_ROOT / "skills" / "uipath-maestro-flow" / "references" / "examples"


def _load_example(name):
    return json.loads((EXAMPLES_DIR / name).read_text())


def test_decision_branch_example_has_expected_topology():
    flow = _load_example("decision-branch.flow")

    nodes = {node["id"]: node for node in flow["nodes"]}
    assert set(nodes) == {
        "start",
        "rollDice",
        "checkHighRoll",
        "formatHigh",
        "formatLow",
        "endHigh",
        "endLow",
    }

    assert nodes["start"]["type"] == "core.trigger.manual"
    assert nodes["rollDice"]["type"] == "core.action.script"
    assert nodes["checkHighRoll"]["type"] == "core.logic.decision"
    assert nodes["formatHigh"]["type"] == "core.action.script"
    assert nodes["formatLow"]["type"] == "core.action.script"
    assert nodes["endHigh"]["type"] == "core.control.end"
    assert nodes["endLow"]["type"] == "core.control.end"

    edge_tuples = {
        (
            edge["sourceNodeId"],
            edge["sourcePort"],
            edge["targetNodeId"],
            edge["targetPort"],
        )
        for edge in flow["edges"]
    }
    assert edge_tuples == {
        ("start", "output", "rollDice", "input"),
        ("rollDice", "success", "checkHighRoll", "input"),
        ("checkHighRoll", "true", "formatHigh", "input"),
        ("checkHighRoll", "false", "formatLow", "input"),
        ("formatHigh", "success", "endHigh", "input"),
        ("formatLow", "success", "endLow", "input"),
    }


def test_decision_branch_example_has_agent_safe_runtime_metadata():
    flow = _load_example("decision-branch.flow")
    nodes = {node["id"]: node for node in flow["nodes"]}

    assert "return { roll, isHigh: roll >= 4 };" in nodes["rollDice"]["inputs"]["script"]
    assert nodes["checkHighRoll"]["inputs"]["expression"] == (
        "$vars.rollDice.output.isHigh === true"
    )

    for node_id in ("start", "rollDice", "formatHigh", "formatLow"):
        assert nodes[node_id]["outputs"], f"{node_id} must define node outputs"

    assert nodes["endHigh"]["outputs"] == {
        "resultMessage": {"source": "=js:$vars.formatHigh.output.message"},
        "roll": {"source": "=js:$vars.rollDice.output.roll"},
    }
    assert nodes["endLow"]["outputs"] == {
        "resultMessage": {"source": "=js:$vars.formatLow.output.message"},
        "roll": {"source": "=js:$vars.rollDice.output.roll"},
    }

    definition_types = {definition["nodeType"] for definition in flow["definitions"]}
    assert definition_types == {
        "core.trigger.manual",
        "core.action.script",
        "core.logic.decision",
        "core.control.end",
    }

    assert set(flow["layout"]["nodes"]) == set(nodes)
    xs = {
        node_id: layout["position"]["x"]
        for node_id, layout in flow["layout"]["nodes"].items()
    }
    assert xs["start"] < xs["rollDice"] < xs["checkHighRoll"]
    assert xs["checkHighRoll"] < xs["formatHigh"] < xs["endHigh"]
    assert xs["checkHighRoll"] < xs["formatLow"] < xs["endLow"]
