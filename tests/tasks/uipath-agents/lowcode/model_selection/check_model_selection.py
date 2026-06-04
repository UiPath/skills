#!/usr/bin/env python3
"""Model-selection check.

Validates the final state of ModelAgent after the agent has
scaffolded it and selected a model via `uip agent model list`:

  1. agent.json exists and is valid JSON.
  2. settings.model is a non-empty string.
  3. settings.model contains 'gpt-5.4' — proves the agent
     selected the requested model.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "ModelSol" / "ModelAgent"
AGENT = ROOT / "agent.json"

EXPECTED_MODEL_SUBSTRING = "gpt-5.4"


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def assert_model_selected(agent: dict) -> None:
    settings = agent.get("settings")
    if not isinstance(settings, dict):
        sys.exit(f"FAIL: agent.json.settings is not an object: {settings!r}")

    model = settings.get("model")
    if not model or not isinstance(model, str) or not model.strip():
        sys.exit(
            f"FAIL: settings.model is missing or empty: {model!r} "
            "— agent did not set a model"
        )

    if EXPECTED_MODEL_SUBSTRING not in model:
        sys.exit(
            f"FAIL: settings.model is '{model}' — expected it to contain "
            f"'{EXPECTED_MODEL_SUBSTRING}'"
        )

    print(f"OK: settings.model is '{model}' (contains '{EXPECTED_MODEL_SUBSTRING}')")


def main() -> None:
    agent = load(AGENT)
    assert_model_selected(agent)


if __name__ == "__main__":
    main()
