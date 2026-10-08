"""Contracts and a sandbox shared by the expiring-contracts test files: five fixture
contracts around a fixed TODAY, and a temporary working directory with an optional
project."""
import contextlib
import datetime
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


@contextlib.contextmanager
def sandbox(workflow_text=None):
    with tempfile.TemporaryDirectory() as tmp:
        if workflow_text is not None:
            (Path(tmp) / "Reminders").mkdir()
            (Path(tmp) / "Reminders" / "Workflow.json").write_text(workflow_text)
        cwd = os.getcwd()
        os.chdir(tmp)
        try:
            yield Path(tmp)
        finally:
            os.chdir(cwd)
