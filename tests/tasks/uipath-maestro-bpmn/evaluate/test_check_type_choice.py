from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


CHECKER = Path(__file__).with_name("check_type_choice.py")


def _run(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _write(tmp_path: Path, name: str, doc: dict) -> None:
    (tmp_path / name).write_text(json.dumps(doc), encoding="utf-8")


def test_matches_evaluator_by_config_name(tmp_path: Path) -> None:
    # The persisted evaluator schema keys the display name under
    # ``evaluatorConfig.name`` with no top-level ``name`` — the exact shape the
    # `_evaluator_name` fix targets. A pre-fix checker read top-level ``name``
    # and missed it.
    _write(
        tmp_path,
        "goal-a.json",
        {
            "id": "goal-a-evaluator",
            "evaluatorTypeId": "uipath-llm-judge-output-semantic-similarity",
            "evaluatorConfig": {"name": "goal-a-evaluator"},
        },
    )

    result = _run(tmp_path, "--artifact", "goal-a")

    assert result.returncode == 0, result.stdout + result.stderr


def test_falls_back_to_top_level_id(tmp_path: Path) -> None:
    # No evaluatorConfig and no top-level ``name`` — identity only in ``id``.
    _write(
        tmp_path,
        "goal-b.json",
        {"id": "goal-b-evaluator", "evaluatorTypeId": "uipath-json-similarity"},
    )

    assert _run(tmp_path, "--artifact", "goal-b").returncode == 0


def test_rejects_wrong_type_id(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "goal-c.json",
        {
            "evaluatorConfig": {"name": "goal-c-evaluator"},
            "evaluatorTypeId": "uipath-json-similarity",
        },
    )

    assert _run(tmp_path, "--artifact", "goal-c").returncode == 1
