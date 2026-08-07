#!/usr/bin/env python3
"""Require the generated ScriptNormalizer BPMN to pass offline validation."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


path = Path("ScriptNormalizer/ScriptNormalizer/ScriptNormalizer.bpmn")
if not path.is_file():
    sys.exit(f"FAIL: missing BPMN file: {path}")
result = subprocess.run(
    ["uip", "maestro", "bpmn", "validate", str(path), "--output", "json"],
    capture_output=True,
    text=True,
    timeout=45,
)
if result.returncode:
    sys.exit(f"FAIL: BPMN validation failed (exit {result.returncode}): {result.stdout[:2000]}{result.stderr[:1000]}")
print("OK: offline BPMN validation passed")
