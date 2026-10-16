"""Fixtures and stubs shared by the check_release_notes.py test files: the committed
fixture with made-up keys, notes for given tickets, a sandbox holding one project, and a
stand-in for golden_connectors.run_workflow."""
import contextlib
import copy
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_release_notes as crn  # noqa: E402

UNSEEDED = json.loads((Path(__file__).resolve().parent / "fixture.json").read_text())


def seeded():
    """fixture.json with keys A-1.. for epics and A-11.. for children."""
    fixture = copy.deepcopy(UNSEEDED)
    for e, epic in enumerate(fixture["epics"], start=1):
        epic["key"] = f"A-{e}"
        for c, child in enumerate(epic["children"], start=1):
            child["key"] = f"A-{e}{c}"
    return fixture


FIXTURE = seeded()
CLOSED = [child for child in crn.children(FIXTURE) if child["status"] == "done"]
GRADING = {**crn.GRADING_TICKET, "key": "A-19"}


def notes_for(tickets):
    return [{"summary": t["summary"], "description": t["description"]} for t in tickets]


@contextlib.contextmanager
def sandbox(workflow_text):
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp) / "ReleaseNotes"
        project.mkdir()
        (project / "Workflow.json").write_text(workflow_text)
        cwd = os.getcwd()
        os.chdir(tmp)
        try:
            yield Path(tmp)
        finally:
            os.chdir(cwd)


def workflow_with_inputs(**properties):
    return json.dumps({"input": {"schema": {"document": {"type": "object", "properties": properties}}}})


class Runner:
    """Stand-in for golden_connectors.run_workflow; `answer(inputs)` returns (ok, raw, error)."""

    def __init__(self, answer):
        self.answer = answer
        self.calls = []

    def __call__(self, _workflow_path, inputs, timeout):
        self.calls.append(inputs)
        return self.answer(inputs)


def per_epic(inputs):
    """A workflow that takes one epic key and returns the notes for that epic."""
    epic = next(e for e in FIXTURE["epics"] if e["key"] == inputs["epicKey"])
    return True, notes_for([c for c in epic["children"] if c["status"] == "done"]), None
