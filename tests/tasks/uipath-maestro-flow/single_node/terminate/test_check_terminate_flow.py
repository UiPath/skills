import importlib.util
import json
from pathlib import Path

import pytest


CHECKER_PATH = Path(__file__).with_name("check_terminate_flow.py")
SPEC = importlib.util.spec_from_file_location("check_terminate_flow", CHECKER_PATH)
assert SPEC and SPEC.loader
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)

DIRECT = [("start", "stop"), ("start", "wait")]
FORK = [("start", "fork"), ("fork", "stop"), ("fork", "wait")]
SEQUENTIAL = [("start", "wait"), ("wait", "stop")]
ONE_ARM_FORK = [("start", "fork"), ("fork", "wait"), ("wait", "stop")]
JOIN = [("start", "fork"), ("other", "fork"), ("fork", "stop"), ("fork", "wait")]


def _write_flow(tmp_path, edges):
    flow = {
        "nodes": [
            {"id": "start", "type": "core.trigger.manual"},
            {"id": "fork", "type": "core.logic.merge"},
            {"id": "stop", "type": "core.logic.terminate"},
            {"id": "wait", "type": "core.logic.delay"},
            {"id": "other", "type": "core.logic.script"},
        ],
        "edges": [{"sourceNodeId": s, "targetNodeId": t} for s, t in edges],
    }
    (tmp_path / "TerminateParallel.flow").write_text(json.dumps(flow))


@pytest.mark.parametrize("edges", [DIRECT, FORK], ids=["direct", "fork"])
def test_accepts_parallel_branches(tmp_path, edges):
    _write_flow(tmp_path, edges)

    CHECKER._check_parallel_branches(str(tmp_path))


@pytest.mark.parametrize("edges", [SEQUENTIAL, ONE_ARM_FORK, JOIN], ids=["sequential", "one-arm-fork", "join"])
def test_rejects_single_branch(tmp_path, edges):
    _write_flow(tmp_path, edges)

    with pytest.raises(SystemExit, match="Expected 2\\+ parallel branches from trigger"):
        CHECKER._check_parallel_branches(str(tmp_path))
