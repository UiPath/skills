#!/usr/bin/env python3
"""Runs `uip rules debug` on the agent's RiskRules project and checks the engine's riskBand for each policy case."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from rules_check import POLICY, fail, find_project  # noqa: E402


def engine_band(project: Path, inputs: dict) -> object:
    completed = subprocess.run(
        ["uip", "rules", "debug", str(project), "--inputs", json.dumps(inputs), "--output", "json"],
        capture_output=True, text=True, timeout=180,
    )
    if completed.returncode != 0:
        fail(f"rules debug exited {completed.returncode} for {inputs}: {completed.stdout or completed.stderr}")
    data = json.loads(completed.stdout).get("Data") or {}
    # ponytail: old `results[]` shape kept until rules debug single-input ships in @latest; drop after
    for result in [data["result"]] if "result" in data else data.get("results") or []:
        for decision in result.get("decisions") or []:
            outputs = decision.get("outputs")
            if isinstance(outputs, dict) and "riskBand" in outputs:
                return outputs["riskBand"]
            if isinstance(outputs, str):
                return outputs
    fail(f"rules debug returned no riskBand for {inputs}: {completed.stdout}")
    raise AssertionError


if __name__ == "__main__":
    project_dir = find_project()
    for case_inputs, expected in POLICY:
        actual = engine_band(project_dir, case_inputs)
        if actual != expected:
            fail(f"the engine returned {actual!r} for {case_inputs}, expected {expected!r}")
    print(f"OK: the engine returns the expected band for all {len(POLICY)} cases")
