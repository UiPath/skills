"""Regression guard for the subflow task's debug-criterion timeout budget.

Context (RCA 2026-05-29, run 2026-05-29_04-04-25): skill-flow-subflow failed
because its ``check_subflow_flow.py`` criterion was killed by the sandbox after
exceeding the criterion ``timeout`` while ``uip maestro flow debug`` (a live
cloud round-trip) was still running. The criterion budget (120s) was *below*
``flow_check.run_debug``'s own ``subprocess.run`` timeout (240s default, since
the checker calls ``run_debug(inputs=...)`` with no explicit timeout). That
inversion means the checker can NEVER surface the underlying CLI error: the
sandbox kills the whole process first, yielding exit ``-1`` with empty output
("Command ... timed out after N seconds") instead of the informative exit ``1``
+ traceback that the inner ``subprocess.TimeoutExpired`` would produce.

This test locks the ordering for the subflow task: the debug criterion's
``timeout`` must be strictly greater than the subprocess timeout the checker
hands to ``run_debug``. It FAILS on the pre-fix value (120 <= 240) and PASSES
on the fixed value (300 > 240).

Run with ``pytest tests/tasks/uipath-maestro-flow/single_node/subflow``.
"""

from __future__ import annotations

import importlib.util
import inspect
import re
from pathlib import Path

import yaml

TASK_DIR = Path(__file__).resolve().parent
TASK_YAML = TASK_DIR / "subflow.yaml"
CHECKER = TASK_DIR / "check_subflow_flow.py"
SHARED = TASK_DIR.parents[1] / "_shared" / "flow_check.py"


def _debug_criterion_timeout() -> int:
    """The ``timeout`` of the run_command criterion that runs check_subflow_flow.py."""
    config = yaml.safe_load(TASK_YAML.read_text())
    matches = [
        c
        for c in config.get("success_criteria", [])
        if c.get("type") == "run_command"
        and CHECKER.name in str(c.get("command", ""))
    ]
    assert len(matches) == 1, (
        f"Expected exactly one criterion invoking {CHECKER.name}, found {len(matches)}"
    )
    timeout = matches[0].get("timeout")
    assert isinstance(timeout, int), f"criterion timeout must be an int, got {timeout!r}"
    return timeout


def _run_debug_subprocess_timeout() -> int:
    """The subprocess timeout check_subflow_flow.py effectively gives run_debug.

    The checker calls ``run_debug(inputs=...)`` with no explicit ``timeout``, so
    the value that governs ``subprocess.run`` is ``run_debug``'s signature
    default. If the checker is ever changed to pass ``timeout=N`` explicitly,
    prefer that literal so this guard tracks the real budget.
    """
    explicit = re.findall(r"run_debug\([^)]*timeout\s*=\s*(\d+)", CHECKER.read_text())
    if explicit:
        return max(int(n) for n in explicit)

    spec = importlib.util.spec_from_file_location("flow_check", SHARED)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    default = inspect.signature(module.run_debug).parameters["timeout"].default
    assert isinstance(default, int), "run_debug.timeout default must be an int"
    return default


def test_debug_criterion_timeout_exceeds_run_debug_subprocess_timeout():
    criterion = _debug_criterion_timeout()
    subprocess_timeout = _run_debug_subprocess_timeout()
    assert criterion > subprocess_timeout, (
        f"subflow debug criterion timeout ({criterion}s) must be greater than "
        f"flow_check.run_debug's subprocess timeout ({subprocess_timeout}s); "
        "otherwise the sandbox kills the checker first (exit -1, empty output) "
        "and the real `uip maestro flow debug` error never surfaces. "
        "See the RCA: docs/uipath-skills/2026-05-29-skill-flow-subflow-root-cause.md."
    )
