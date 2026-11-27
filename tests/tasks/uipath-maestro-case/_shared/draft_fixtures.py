"""Hand-built case plans for the draft-mode grader tests, in the shape `uip maestro case compile` writes."""

from __future__ import annotations

import copy
import json


def box(task_id: str, label: str, task_type: str = "process") -> dict:
    return {"id": task_id, "displayName": label, "type": task_type, "data": {}, "isRequired": True}


def stage(stage_id: str, label: str, lanes: list[list[dict]], entry: list[dict], secondary: bool = False) -> dict:
    data = {"label": label, "tasks": lanes, "isRequired": not secondary, "entryConditions": entry, "exitConditions": []}
    if secondary:
        data["stageType"] = "secondary"
    return {"id": stage_id, "type": "case-management:Stage", "data": data}


def entry(name: str, rule: str, expression: str | None = None) -> dict:
    body = {"rule": rule, "id": f"Rule_{name}"}
    if expression:
        body["conditionExpression"] = expression
    return {"id": f"Condition_{name}", "displayName": name, "rules": [[body]]}


def trigger(service: str = "None") -> dict:
    return {"id": "trigger_1", "type": "uipath.case.trigger", "data": {"inputs": {"serviceType": service}}}


SKELETON = {
    "nodes": [
        trigger(),
        stage("Stage_a", "Intake", [[box("t1", "Extract claim data [Agent]", "agent")],
                                    [box("t2", "Record the claim [Data Fabric]", "execute-connector-activity")]],
              [entry("Claim arrives", "case-entered")]),
        stage("Stage_b", "Review", [[box("t3", "Adjuster review [Human task] → decision", "action")]],
              [entry("Ready for review", "selected-stage-completed")]),
        stage("Stage_c", "Payout", [[box("t4", "Pay the claim [RPA workflow]", "rpa")]],
              [entry("Approved", "selected-stage-completed", '=js:vars.decision === "Approve"')]),
        stage("Stage_d", "Rejection", [[box("t5", "Send rejection letter [Outlook]", "execute-connector-activity")]],
              [entry("Rejected", "selected-stage-completed", '=js:vars.decision === "Reject"')], secondary=True),
    ],
}

TIMER_SKELETON = {
    "nodes": [
        trigger("timer"),
        stage("Stage_a", "Sweep", [[box("t1", "Score the account [Function] → tier", "function")],
                                   [box("t2", "Work out the fee [Script]")]],
              [entry("Sweep starts", "case-entered")]),
        stage("Stage_b", "Escalate", [[box("t3", "Run collections [Maestro process]")]],
              [entry("High tier", "selected-stage-completed", '=js:vars.tier === "high"')]),
    ],
}


def built(doc: dict) -> dict:
    """The skeleton after Build it: every box gets a `data` block and loses its label suffix."""
    out = copy.deepcopy(doc)
    for node in out["nodes"]:
        for lane in (node.get("data") or {}).get("tasks") or []:
            for task in lane:
                task["data"] = {"name": "=bindings.b1", "folderPath": "=bindings.b2"}
                task["displayName"] = task["displayName"].rsplit(" [", 1)[0]
    return out


def write_project(root, doc: dict, plan_file: str = "caseplan.case") -> str:
    proj = root / "Sol" / "Sketch"
    proj.mkdir(parents=True, exist_ok=True)
    (proj / "project.uiproj").write_text(json.dumps({"ProjectType": "CaseManagement", "Name": "Sketch"}))
    (proj / plan_file).write_text(json.dumps(doc))
    return str(proj / plan_file)
