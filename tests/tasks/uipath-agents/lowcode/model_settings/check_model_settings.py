#!/usr/bin/env python3
"""Model-specific settings check (agent-definition.md § Model-Specific Settings).

The runtime forwards `settings.modelSettings` to the model unchanged. On a
Claude 4.6 model, effort is `output_config.effort`, thinking is
`thinking.type: "adaptive"`, and Anthropic rejects any temperature other than
1 while thinking is on.

PASS requires ALL of:
  1. `settings.model` is the requested Claude Sonnet 4.6 model
  2. `settings.modelSettings["output_config.effort"]` == "high"
  3. `thinking.type`, when present, is "adaptive", and `temperature` is then 1
  4. no other `modelSettings` keys (e.g. `reasoning_effort`, `thinking_level`)
"""

import json
import os
import sys
from pathlib import Path

AGENT = Path(os.getcwd()) / "ResearchSol" / "ResearchAgent" / "agent.json"

ALLOWED_KEYS = {"output_config.effort", "thinking.type"}


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def main() -> None:
    settings = load(AGENT).get("settings") or {}

    model = settings.get("model")
    if not isinstance(model, str) or "claude-sonnet-4-6" not in model:
        sys.exit(f"FAIL: settings.model must be the Claude Sonnet 4.6 model, got {model!r}")
    print("OK: model is Claude Sonnet 4.6")

    model_settings = settings.get("modelSettings")
    if not isinstance(model_settings, dict):
        sys.exit(f"FAIL: settings.modelSettings must be an object, got {model_settings!r}")

    if model_settings.get("output_config.effort") != "high":
        sys.exit(f"FAIL: output_config.effort must be \"high\", got {model_settings.get('output_config.effort')!r}")
    print("OK: output_config.effort is high")

    extra = set(model_settings) - ALLOWED_KEYS
    if extra:
        sys.exit(f"FAIL: modelSettings has keys another model family uses: {sorted(extra)}")
    print("OK: only Claude 4.6 keys")

    if "thinking.type" in model_settings:
        if model_settings["thinking.type"] != "adaptive":
            sys.exit(f"FAIL: thinking.type must be \"adaptive\" on Claude 4.6, got {model_settings['thinking.type']!r}")
        if settings.get("temperature") != 1:
            sys.exit(f"FAIL: temperature must be 1 while thinking is on, got {settings.get('temperature')!r}")
        print("OK: adaptive thinking with temperature 1")

    print("PASS")


if __name__ == "__main__":
    main()
