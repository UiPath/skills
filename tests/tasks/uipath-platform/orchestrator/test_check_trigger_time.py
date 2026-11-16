"""Unit tests for check_trigger_time.py — no tenant or CLI required.

Run with ``pytest tests/tasks/uipath-platform/orchestrator/test_check_trigger_time.py``.
"""

import importlib.util
import json
from pathlib import Path

import pytest

CHECKER = Path(__file__).resolve().parent / "check_trigger_time.py"

_spec = importlib.util.spec_from_file_location("_check_trigger_time", CHECKER)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)


@pytest.mark.parametrize("cron", [
    "0 30 4 * * ?",
    "0 30 4 ? * *",
    "0 30 4 * * ? *",
    "0 30 4 ? * * *",
    "  0\t30  4 ? * *\n",
])
def test_daily_at_0430_passes(cron):
    assert _mod.matches_expected_cron(cron)


@pytest.mark.parametrize("cron", [
    "0 30 4 * * *",  # Quartz requires one unspecified day field.
    "30 4 * * *",  # Unix cron has no seconds field.
    "0 30 5 * * ?",
    "1 30 4 * * ?",
    "0 31 4 * * ?",
    "0 30 4 * 1 ?",
    "0 30 4 1 * ?",
    "0 30 4 ? * MON",
    "0 30 4 ? * ?",
    "0 30 4 * * ? 2026",
    "0 30 4 ? * * 2026",
    "0 30 4 * * ? * *",
    "",
    "   ",
    None,
])
def test_other_schedules_fail(cron):
    assert not _mod.matches_expected_cron(cron)


@pytest.mark.parametrize("cron, passes", [
    ("0 30 4 * * ?", True),
    ("0 30 4 ? * *", True),
    ("0 30 5 * * ?", False),
])
def test_checker_uses_semantic_matcher(tmp_path, monkeypatch, capsys, cron, passes):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "seed.json").write_text(json.dumps({"uuid8": "test", "folder_path": "Test"}))
    monkeypatch.setattr(_mod, "uip_json", lambda *args, **kwargs: {
        "Result": "Success",
        "Data": [{"Name": "e2e-trigger-time-test", "Enabled": True, "StartProcessCron": cron}],
    })
    if passes:
        _mod.main()
        assert "OK:" in capsys.readouterr().out
    else:
        with pytest.raises(SystemExit) as exc:
            _mod.main()
        message = str(exc.value)
        assert f"cron={cron!r}" in message
        assert "'0 30 4 * * ?' or '0 30 4 ? * *'" in message
