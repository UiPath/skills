import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_task_dependency_chain import _task_is_non_required  # noqa: E402


def test_non_required_accepts_the_sdk_default_or_explicit_false():
    assert _task_is_non_required({})
    assert _task_is_non_required({"isRequired": False})


def test_non_required_rejects_required_or_invalid_values():
    assert not _task_is_non_required({"isRequired": True})
    assert not _task_is_non_required({"isRequired": "false"})
