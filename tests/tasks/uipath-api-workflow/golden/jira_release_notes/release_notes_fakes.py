"""Fixtures and stubs shared by the check_release_notes.py test files: the committed
fixture with made-up keys, notes for given tickets, a sandbox holding one project or
several, and a stand-in for golden_connectors.run_workflow."""
import contextlib
import copy
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_release_notes as crn  # noqa: E402

COMMITTED = json.loads((Path(__file__).resolve().parent / "fixture.json").read_text())


def with_keys(key_for):
    """fixture.json with every epic and child key replaced by `key_for(epic number, child
    number)`, the child number being 0 for the epic itself."""
    fixture = copy.deepcopy(COMMITTED)
    for e, epic in enumerate(fixture["epics"], start=1):
        epic["key"] = key_for(e, 0)
        for c, child in enumerate(epic["children"], start=1):
            child["key"] = key_for(e, c)
    return fixture


def seeded():
    """fixture.json with keys A-1.. for epics and A-11.. for children."""
    return with_keys(lambda e, c: f"A-{e}{c}" if c else f"A-{e}")


def unseeded():
    """fixture.json as it is before seed_jira_fixture.py runs: no keys."""
    return with_keys(lambda e, c: None)


FIXTURE = seeded()
CLOSED = [child for child in crn.children(FIXTURE) if child["status"] == "done"]


def notes_for(tickets):
    return [{"summary": t["summary"], "description": t["description"]} for t in tickets]


def closed_notes(epic_keys):
    """Notes for the closed tickets under `epic_keys`, as a workflow that follows its input
    returns them."""
    return notes_for([child for epic in FIXTURE["epics"] if epic["key"] in epic_keys
                      for child in epic["children"] if child["status"] == "done"])


@contextlib.contextmanager
def sandbox(workflow_text):
    """A working directory holding the ReleaseNotes project, or one project per
    {folder: Workflow.json text} when given a dict."""
    projects = workflow_text if isinstance(workflow_text, dict) else {"ReleaseNotes": workflow_text}
    with tempfile.TemporaryDirectory() as tmp:
        for folder, text in projects.items():
            (Path(tmp) / folder).mkdir()
            (Path(tmp) / folder / "Workflow.json").write_text(text)
        cwd = os.getcwd()
        os.chdir(tmp)
        try:
            yield Path(tmp)
        finally:
            os.chdir(cwd)


def workflow_with_inputs(**properties):
    return json.dumps({"input": {"schema": {"document": {"type": "object", "properties": properties}}}})


def workflow_declaring(inputs=None, outputs=None):
    """Workflow.json text declaring the {name: schema} inputs and outputs."""
    workflow = {}
    if inputs is not None:
        workflow["input"] = {"schema": {"document": {"type": "object", "properties": inputs}}}
    if outputs is not None:
        workflow["output"] = {"schema": {"document": {"type": "object", "properties": outputs}}}
    return json.dumps(workflow)


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
    return True, closed_notes([inputs["epicKey"]]), None


def per_epic_list(inputs):
    """A workflow that takes a list of epic keys and returns the notes for those epics."""
    return True, closed_notes(inputs["epicKeys"]), None
