import contextlib
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_vat  # noqa: E402,F401

REGISTERED = {"RO34737997"}


def workflow_with_inputs(*names, outputs=()):
    properties = {name: {"type": "string"} for name in names}
    workflow = {"input": {"schema": {"format": "json", "document": {"type": "object", "properties": properties}}}}
    if outputs:
        declared = {name: {"type": "boolean"} for name in outputs}
        workflow["output"] = {"schema": {"format": "json", "document": {"type": "object", "properties": declared}}}
    return workflow


@contextlib.contextmanager
def sandbox(workflow_text):
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp) / "VatCheck"
        project.mkdir()
        (project / "Workflow.json").write_text(workflow_text)
        cwd = os.getcwd()
        os.chdir(tmp)
        try:
            yield
        finally:
            os.chdir(cwd)


class Runner:

    def __init__(self, answer):
        self.answer = answer
        self.calls = []

    def __call__(self, _workflow_path, inputs, timeout=90):
        self.calls.append(inputs)
        return True, self.answer(inputs, len(self.calls)), None


def prefixed(inputs, _call):
    return {"isValid": next(iter(inputs.values())) in REGISTERED}
