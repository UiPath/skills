import contextlib
import datetime
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_contracts as cc  # noqa: E402

fx = cc.fixture
TODAY = datetime.date(2026, 10, 8)


def contract(days, cid, number=None, today=TODAY):
    return {"id": cid, "label": f"{fx.ACCOUNT_PREFIX} t0k3n {days:+d}d", "days": days, "number": number,
            "end_date": (today + datetime.timedelta(days=days)).isoformat()}


CONTRACTS = [contract(5, "800AAAAAAAAAAA1", "00000101"), contract(25, "800AAAAAAAAAAA2", "00000102"),
             contract(45, "800AAAAAAAAAAA3", "00000103"), contract(-3, "800AAAAAAAAAAA4", "00000104"),
             contract(12, "800AAAAAAAAAAA5", "00000105")]


def workflow_declaring(inputs=None, outputs=None, required=None):
    workflow = {}
    if inputs is not None:
        document = {"type": "object", "properties": inputs}
        if required is not None:
            document["required"] = required
        workflow["input"] = {"schema": {"document": document}}
    if outputs is not None:
        workflow["output"] = {"schema": {"document": {"type": "object", "properties": outputs}}}
    return json.dumps(workflow)


FIELD_LISTER = workflow_declaring(outputs={"fields": {"type": "array"}})
REMINDER_SENDER = workflow_declaring({"contracts": {"type": "array"}}, {"sent": {"type": "integer"}},
                                     required=["contracts"])
EXPIRING_CONTRACTS = workflow_declaring({"daysAhead": {"type": "integer"}}, {"contracts": {"type": "array"}},
                                        required=["daysAhead"])


@contextlib.contextmanager
def sandbox(workflow_text=None):
    if isinstance(workflow_text, dict):
        projects = workflow_text
    else:
        projects = {} if workflow_text is None else {"Reminders": workflow_text}
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
