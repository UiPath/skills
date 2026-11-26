"""check_deployed_discovery.py passes the described contract and fails a wrong folder or an invented schema."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

CHECKER = Path(__file__).with_name("check_deployed_discovery.py")
sys.path.insert(0, str(CHECKER.parent))

from check_deployed_discovery import FOLDER, INPUT, OUTPUT  # noqa: E402

RIGHT = {"folderPath": FOLDER, "input": INPUT, "output": OUTPUT}


def run(tmp_path: Path, contract: object) -> subprocess.CompletedProcess[str]:
    if contract is not None:
        (tmp_path / "contract.json").write_text(json.dumps(contract), encoding="utf-8")
    return subprocess.run([sys.executable, str(CHECKER)], cwd=tmp_path, capture_output=True, text=True, check=False)


@pytest.mark.parametrize("contract", [RIGHT, {**RIGHT, "input": json.dumps(INPUT), "output": json.dumps(OUTPUT)}])
def test_described_contract_passes(tmp_path: Path, contract: dict) -> None:
    result = run(tmp_path, contract)
    assert result.returncode == 0, result.stdout


@pytest.mark.parametrize("contract, message", [
    (None, "contract.json is missing"),
    ({**RIGHT, "folderPath": "Shared"}, "folderPath is 'Shared'"),
    # Written from the prompt's wording, not read from describe.
    ({**RIGHT, "output": {"type": "object", "properties": {"rate": {"type": "number"}}}}, "`output` is not"),
    ({**RIGHT, "input": {}}, "`input` is not"),
])
def test_wrong_contract_fails(tmp_path: Path, contract: object, message: str) -> None:
    result = run(tmp_path, contract)
    assert result.returncode != 0 and message in result.stdout, result.stdout
