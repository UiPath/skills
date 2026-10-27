"""Each edit task's merged and preserved criteria pass its edit and fail what they exist to catch."""

from __future__ import annotations

import copy
import importlib.util
import json
import re
import shlex
import shutil
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
REFERENCE_DIR = HERE.parent
FIXTURE = HERE / "templates" / "initial_flow" / "BellevueWeather" / "BellevueWeather"
FLOW = "BellevueWeather/BellevueWeather/BellevueWeather.flow"
TASKS = ("add_node", "add_output", "update_node", "remove_node", "move_node", "group_to_subflow")

spec = importlib.util.spec_from_file_location("check_brownfield_preserved", REFERENCE_DIR / "_shared" / "check_brownfield_preserved.py")
preserved = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preserved)


def criteria(task: str) -> dict[str, list[str]]:
    text = (HERE / task / f"{task}.yaml").read_text()
    found = {}
    for command in re.findall(r'command: "python3 \$REFERENCE_DIR/_shared/check_brownfield_preserved\.py ([^"]*)"', text):
        # run_command hands the string to a shell, so an unquoted '>' in an edge spec is a redirect.
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        assert not any(set(token) <= set("();<>|&") for token in lexer), f"{task}: unquoted shell operator in {command}"
        argv = shlex.split(command.replace("$REFERENCE_DIR", str(REFERENCE_DIR)))
        found["merged" if "merged" in argv else "graph"] = argv
    assert set(found) == {"merged", "graph"}, task
    return found


def node(flow: dict, node_id: str) -> dict:
    return next(n for n in flow["nodes"] if n["id"] == node_id)


def end_expression(flow: dict, node_id: str) -> dict:
    return node(flow, node_id)["outputs"]["summary"]["source"]


def rewrite_ends(flow: dict, old: str, new: str, ends=("endNiceDay", "endBringJacket")) -> None:
    for end in ends:
        source = end_expression(flow, end)
        source["expression"] = source["expression"].replace(old, new)


def edge(source: str, port: str, target: str) -> dict:
    return {"id": f"{source}-{target}", "sourceNodeId": source, "sourcePort": port, "targetNodeId": target, "targetPort": "input"}


def drop(flow: dict, node_id: str) -> dict:
    gone = node(flow, node_id)
    flow["nodes"].remove(gone)
    flow["edges"] = [e for e in flow["edges"] if node_id not in (e["sourceNodeId"], e["targetNodeId"])]
    flow["variables"]["nodes"] = [v for v in flow["variables"]["nodes"] if v["binding"]["nodeId"] != node_id]
    flow["layout"]["nodes"].pop(node_id, None)
    return gone


def add_node(flow: dict) -> None:
    convert = copy.deepcopy(node(flow, "formatSummary"))
    convert["id"] = "convertToCelsius"
    convert["inputs"]["script"] = "const f = $vars.getWeather.output.body.current.temperature_2m;\nreturn { temperatureF: f, temperatureC: (f - 32) * 5 / 9 };"
    flow["nodes"].append(convert)
    node(flow, "formatSummary")["inputs"]["script"] += "\n// adds $vars.convertToCelsius.output.temperatureC"
    flow["edges"] = [e for e in flow["edges"] if e["id"] != "edge-getWeather-formatSummary"]
    flow["edges"] += [edge("getWeather", "default", "convertToCelsius"), edge("convertToCelsius", "success", "formatSummary")]


def add_output(flow: dict) -> None:
    rewrite_ends(flow, "({ ", "({ location: 'Bellevue, WA', ")


def update_node(flow: dict) -> None:
    rewrite_ends(flow, "'nice day'", "'amazing day'", ends=("endNiceDay",))
    rewrite_ends(flow, "'bring a jacket'", "'go home'", ends=("endBringJacket",))


def remove_node(flow: dict) -> None:
    drop(flow, "formatSummary")
    flow["edges"].append(edge("getWeather", "default", "checkTemperature"))
    reading = "$vars.getWeather.output.body.current.temperature_2m"
    node(flow, "checkTemperature")["inputs"]["expression"] = f"{reading} > 60"
    rewrite_ends(flow, "$vars.formatSummary.output.temperatureF", reading)


def move_node(flow: dict) -> None:
    drop(flow, "endBringJacket")
    flow["edges"] = [e for e in flow["edges"] if e["id"] == "edge-start-getWeather"]
    flow["edges"] += [
        edge("getWeather", "default", "checkTemperature"),
        {**edge("checkTemperature", "true", "formatSummary"), "id": "t"},
        {**edge("checkTemperature", "false", "formatSummary"), "id": "f"},
        edge("formatSummary", "success", "endNiceDay"),
    ]
    node(flow, "checkTemperature")["inputs"]["expression"] = "$vars.getWeather.output.body.current.temperature_2m > 60"
    node(flow, "formatSummary")["inputs"]["script"] += "\n// message from $vars.checkTemperature.output"
    rewrite_ends(flow, "'nice day'", "$vars.formatSummary.output.message", ends=("endNiceDay",))


def group_to_subflow(flow: dict) -> None:
    moved = [drop(flow, "getWeather"), drop(flow, "formatSummary")]
    flow["nodes"].insert(1, {"id": "fetchAndFormat", "type": "core.subflow", "typeVersion": "1.0.0", "display": {"label": "fetchAndFormat"}, "inputs": {}})
    flow["subflows"] = {"fetchAndFormat": {"nodes": moved, "edges": [edge("getWeather", "default", "formatSummary")], "variables": {}}}
    flow["edges"] += [edge("start", "output", "fetchAndFormat"), edge("fetchAndFormat", "output", "checkTemperature")]
    node(flow, "checkTemperature")["inputs"]["expression"] = "$vars.fetchAndFormat.output.temperatureF > 60"
    rewrite_ends(flow, "$vars.formatSummary.output", "$vars.fetchAndFormat.output")


EDITS = {f.__name__: f for f in (add_node, add_output, update_node, remove_node, move_node, group_to_subflow)}


def renumber_edges(flow: dict) -> None:
    edges = flow["edges"] + [e for sf in flow.get("subflows", {}).values() for e in sf["edges"]]
    for i, e in enumerate(edges):
        e["id"] = f"edge_{i}"


@pytest.fixture
def sandbox(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    shutil.copytree(FIXTURE, tmp_path / "BellevueWeather" / "BellevueWeather")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def mutate(sandbox: Path, *changes) -> None:
    path = sandbox / FLOW
    flow = json.loads(path.read_text())
    for change in changes:
        change(flow)
    path.write_text(json.dumps(flow, indent=2))


def test_fixture_http_is_managed_v2() -> None:
    flow = json.loads((FIXTURE / "BellevueWeather.flow").read_text())
    assert node(flow, "getWeather")["type"] == "core.action.http.v2"


@pytest.mark.parametrize("task", TASKS)
def test_merged_edit_passes_both(sandbox: Path, task: str) -> None:
    mutate(sandbox, EDITS[task], renumber_edges)
    argv = criteria(task)
    assert preserved.main(argv["merged"]) == 0
    assert preserved.main(argv["graph"]) == 0


@pytest.mark.parametrize("task", TASKS)
def test_hand_edit_fails_merged(sandbox: Path, task: str) -> None:
    mutate(sandbox, EDITS[task])
    argv = criteria(task)
    assert preserved.main(argv["merged"]) == 1
    assert preserved.main(argv["graph"]) == 0


@pytest.mark.parametrize("task", TASKS)
def test_unedited_fixture_fails_merged(sandbox: Path, task: str) -> None:
    assert preserved.main(criteria(task)["merged"]) == 1


@pytest.mark.parametrize("task", TASKS)
def test_touching_the_trigger_fails_preserved(sandbox: Path, task: str) -> None:
    mutate(sandbox, EDITS[task], renumber_edges, lambda f: node(f, "start")["display"].update(label="Start"))
    assert preserved.main(criteria(task)["graph"]) == 1


@pytest.mark.parametrize("task", TASKS)
def test_rewritten_flow_variable_fails_preserved(sandbox: Path, task: str) -> None:
    def add_name(flow: dict) -> None:
        flow["variables"]["globals"][0]["name"] = "summary"

    mutate(sandbox, EDITS[task], renumber_edges, add_name)
    assert preserved.main(criteria(task)["graph"]) == 1


def test_update_node_fails_preserved_when_the_script_changes(sandbox: Path) -> None:
    mutate(sandbox, update_node, renumber_edges, lambda f: node(f, "formatSummary")["inputs"].update(script="return {};"))
    assert preserved.main(criteria("update_node")["graph"]) == 1


def test_remove_node_may_drop_the_definition_no_node_uses(sandbox: Path) -> None:
    def drop_definition(node_type: str):
        return lambda f: f.update(definitions=[d for d in f["definitions"] if d["nodeType"] != node_type])

    mutate(sandbox, remove_node, renumber_edges, drop_definition("core.action.script"))
    assert preserved.main(criteria("remove_node")["graph"]) == 0
    mutate(sandbox, drop_definition("core.logic.decision"))
    assert preserved.main(criteria("remove_node")["graph"]) == 1


def test_move_node_fails_preserved_when_a_branch_still_ends_directly(sandbox: Path) -> None:
    mutate(sandbox, move_node, lambda f: f["edges"].append(edge("checkTemperature", "true", "endNiceDay")), renumber_edges)
    assert preserved.main(criteria("move_node")["graph"]) == 1
