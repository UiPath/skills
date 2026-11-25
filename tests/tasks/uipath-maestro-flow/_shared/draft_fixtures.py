"""Hand-built `.flow` documents for the draft-mode grader tests, in the shape `uip maestro flow compile` writes."""

from __future__ import annotations

import copy
import json


def box(node_id: str, label: str) -> dict:
    return {"id": node_id, "type": "core.logic.mock", "inputs": {}, "display": {"label": label}}


def edge(src: str, port: str, dst: str) -> dict:
    return {"id": f"{src}-{port}-{dst}", "sourceNodeId": src, "sourcePort": port, "targetNodeId": dst, "targetPort": "input"}


SKELETON = {
    "nodes": [
        {"id": "start", "type": "core.trigger.manual", "inputs": {}},
        box("record", "Record invoice [Data Fabric]"),
        {"id": "large", "type": "core.logic.decision",
         "inputs": {"trueLabel": "Review", "falseLabel": "Auto", "expression": "$vars.start.output.amount >= 1000"}},
        box("review", "Manager review [HITL]"),
        box("approve", "Approve invoice [Script]"),
        {"id": "each", "type": "core.logic.loop",
         "inputs": {"collection": {"type": "jsExpression", "expression": "$vars.start.output.items"}}},
        box("line", "Check line [Agent]"),
        box("notify", "Notify finance [Connector]"),
        {"id": "end", "type": "core.control.end", "inputs": {}},
    ],
    "edges": [
        edge("start", "output", "record"), edge("record", "output", "large"),
        edge("large", "true", "review"), edge("large", "false", "approve"),
        edge("review", "output", "each"), edge("approve", "output", "each"),
        edge("each", "start", "line"), edge("line", "output", "each"),
        edge("each", "success", "notify"), edge("notify", "output", "end"),
    ],
}

SCHEDULED_SWITCH = {
    "nodes": [
        {"id": "start", "type": "core.trigger.scheduled", "inputs": {"timerType": "timeCycle", "timerValue": "R/P1D"}},
        box("pull", "Pull items [Connector]"),
        {"id": "route", "type": "core.logic.switch", "inputs": {
            "hasDefault": True,
            "cases": [
                {"id": "case_1", "label": "Urgent", "expression": "$vars.tier === \"a\""},
                {"id": "case_2", "label": "Normal", "expression": "$vars.tier === \"b\""},
                {"id": "case_3", "label": "Low", "expression": "$vars.tier === \"c\""},
            ]}},
        box("ha", "Escalate [Agent]"), box("hb", "Queue [Connector]"), box("hc", "Log [Connector]"),
        {"id": "end", "type": "core.control.end", "inputs": {}},
    ],
    "edges": [
        edge("start", "output", "pull"), edge("pull", "output", "route"),
        edge("route", "case-case_1", "ha"), edge("route", "case-case_2", "hb"), edge("route", "case-case_3", "hc"),
        edge("ha", "output", "end"), edge("hb", "output", "end"), edge("hc", "output", "end"),
    ],
}


def place(doc: dict) -> dict:
    for i, n in enumerate(doc["nodes"]):
        n["ui"] = {"position": {"x": 200 * i, "y": 100}}
    return doc


place(SKELETON)
place(SCHEDULED_SWITCH)


def built(doc: dict) -> dict:
    """The skeleton after Build it: every mock becomes a script node, labels lose their suffix."""
    out = copy.deepcopy(doc)
    for n in out["nodes"]:
        if n["type"] == "core.logic.mock":
            n["type"] = "core.action.script"
            n["display"]["label"] = n["display"]["label"].rsplit(" [", 1)[0]
    return out


def write_project(root, doc: dict, flow_file: str = "Sketch.flow") -> str:
    proj = root / "Sol" / "Sketch"
    proj.mkdir(parents=True, exist_ok=True)
    (proj / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow", "Name": "Sketch"}))
    (proj / flow_file).write_text(json.dumps(doc))
    return str(proj / flow_file)
