"""Unit tests for check_dice_runs_simulated's roll-value rule."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _load():
    path = Path(__file__).parent / "check_dice_runs_simulated.py"
    spec = importlib.util.spec_from_file_location("_check_dice_runs_simulated", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_find_int_in_range_accepts_a_whole_valued_float() -> None:
    """Jint serialises numbers as doubles, so a correct roll can read back as
    5.0; 7.5, 0, 7 and booleans still fail, and int / digit-string pass."""
    grader = _load()
    f = grader.find_int_in_range
    assert f([5.0], 1, 6) == 5
    assert f([5], 1, 6) == 5
    assert f(["5"], 1, 6) == 5
    assert f([7.5], 1, 6) is None
    assert f([0, 7, 6.5], 1, 6) is None
    assert f([True], 1, 6) is None
    assert f([True, 6.0], 1, 6) == 6
