"""Stubs shared by the check_vat.py test files: a workflow with given inputs, a sandbox
holding one project, and a stand-in for eval_scoring.run_row."""
import contextlib
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_vat  # noqa: E402,F401

REGISTERED = {"RO34737997"}


def workflow_with_inputs(*names):
    properties = {name: {"type": "string"} for name in names}
    return {"input": {"schema": {"format": "json", "document": {"type": "object", "properties": properties}}}}


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
    """Stand-in for eval_scoring.run_row; `answer(inputs, call_number)` returns the raw output."""

    def __init__(self, answer):
        self.answer = answer
        self.calls = []

    def __call__(self, _workflow_path, inputs, timeout=90):
        self.calls.append(inputs)
        return True, self.answer(inputs, len(self.calls)), None


def prefixed(inputs, _call):
    """A correct workflow with one input that takes the prefixed VAT id."""
    return {"isValid": next(iter(inputs.values())) in REGISTERED}
